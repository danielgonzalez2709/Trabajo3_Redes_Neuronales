"""M3 — red neuronal de dos torres (JJ-5; D15–D19 de docs/spec/partes/juanjose.md §3.2). Estilo de los notebooks del curso:
módulos ``nn.Module`` con ``__init__`` y ``forward``, y funciones explícitas ``train_loop`` y ``val_loop``.

Formulación (la que se explica en la sustentación)
--------------------------------------------------
Entradas (``contenido.py``): x_u ∈ {0,1}^{p_u} = las 5 preferencias one-hot (+ demografía si ``modelo.usar_demografia``);
x_i ∈ {0,1}^5 = ``tipo`` one-hot. Índices de id k(u), k(i) ∈ {0, 1, …, n}: 1..n para usuarios/destinos con al menos una
interacción en TRAIN (orden ascendente de id), 0 = «sin id» para el resto (fríos, perfiles nuevos). La fila 0 de cada tabla
de embeddings es un vector nulo FIJO (``padding_idx = 0``: su gradiente es 0 y no se cuenta como parámetro).

  Torre de usuario:  h_0 = x_u;   h_l = Dropout(ReLU(W_l h_{l−1} + c_l)),  l = 1..L_u
                     u = A h_{L_u} + a + E_U[k(u)]                               ∈ R^d
  Torre de destino:  g_0 = x_i;   g_l = Dropout(ReLU(W'_l g_{l−1} + c'_l)),  l = 1..L_i
                     [v_i ; b_i] = A' g_{L_i} + a' + E_I[k(i)]                   ∈ R^{d+1}   (d componentes de v_i y el sesgo b_i)
  Puntaje (logit):   s_ui = ⟨u, v_i⟩ + b_i

Con k(u) = 0 la torre de usuario es una MLP de las preferencias: es la ``torre_usuario`` que se exporta a la app (núcleo
§5.8, capas «W·h + b» con ReLU). Un destino frío (k(i) = 0) recibe puntaje solo por su tipo.

Pérdidas (D16), sobre un minilote de B positivos (u, i) ∈ train con m negativos j ~ U(C − T_u) por positivo:
  BCE  (modelo: y_ui ~ Bernoulli(σ(s_ui)) independientes, y = 1 en el positivo y 0 en los negativos muestreados;
        −log verosimilitud media):  L = −1/(B(1+m)) [Σ_b log σ(s⁺_b) + Σ_{b,j} log(1 − σ(s⁻_bj))]
  BPR  (modelo: P(i ≻_u j) = σ(s_ui − s_uj), pares independientes; −log verosimilitud media):
        L = −1/(B·m) Σ_{b,j} log σ(s⁺_b − s⁻_bj)
  Ambas sobre logits y estables: −log σ(x) = softplus(−x) y −log(1 − σ(x)) = softplus(x).
  BPR: Rendle, Freudenthaler, Gantner y Schmidt-Thieme (2009) [VERIFICAR en JJ-9; sin DOI hasta entonces].

Optimizador (D19): Adam con ``weight_decay`` λ (L2 acoplado al gradiente: g ← ∇L + λθ, luego los momentos de Adam), dropout
en las capas ocultas y «dropout de id»: en entrenamiento, cada índice de id (de usuario y de destino, por separado) se
reemplaza por 0 con probabilidad ``modelo.dropout_id``; así la parte de contenido aprende a puntuar sola (fríos y perfiles
nuevos). Parada temprana por NDCG@5 de VALIDACIÓN (candidatos = catálogo − train, D10) con ``entrenamiento.paciencia``; se
restauran los pesos de la mejor época.

Uso de los conjuntos (D9): ``ajustar`` descarta PRUEBA al entrar; validación entra solo a la parada temprana (y a la pérdida
de validación que se registra en la curva). Negativos, índices de id y gradiente salen solo de train. Toda aleatoriedad sale
del ``np.random.Generator`` recibido (semillas hijas) y torch corre dentro de ``torch.random.fork_rng``: el estado global no
cambia. Misma semilla → mismos pesos y mismos puntajes.
"""

from __future__ import annotations

import copy
import warnings
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

from src.comun.results import save_json
from src.comun.seeds import validar_entero
from src.comun.torch_utils import activar_determinismo, resolver_device
from src.m3_recomendacion import contenido as contenido_m3
from src.m3_recomendacion import metricas, particion

K_PARADA = 5                       # D19: la parada temprana mira NDCG@5 de validación
BLOQUES = ("modelo", "perdida", "entrenamiento", "regularizacion")
PERDIDAS_VALIDAS = ("bce", "bpr")
CLAVES = ("modelo.dim_embedding", "modelo.capas_usuario", "modelo.unidades_usuario", "modelo.capas_destino",
          "modelo.unidades_destino", "modelo.usar_id_usuario", "modelo.usar_id_destino", "modelo.dropout_id",
          "modelo.negativos_por_positivo", "modelo.usar_demografia", "perdida.tipo", "entrenamiento.lr",
          "entrenamiento.max_epocas", "entrenamiento.paciencia", "entrenamiento.tam_lote", "regularizacion.weight_decay",
          "regularizacion.dropout")
N_SEMILLAS_HIJAS = 6               # torch, lotes, negativos, dropout de id, negativos de validación, desempate de validación


# =========================================================================== pérdidas (D16)
def perdida_bce(s_pos: torch.Tensor, s_neg: torch.Tensor) -> torch.Tensor:
    """Entropía cruzada binaria con negativos muestreados, sobre logits.

    Modelo probabilístico: y_ui ~ Bernoulli(p_ui) con p_ui = σ(s_ui), independientes; y = 1 en los positivos ``s_pos`` (B,) y
    y = 0 en los negativos ``s_neg`` (B, m). −log verosimilitud media sobre los B(1+m) términos:
        L = −1/(B(1+m)) [Σ_b log σ(s⁺_b) + Σ_{b,j} log(1 − σ(s⁻_bj))]
    ``BCEWithLogitsLoss`` la calcula de forma estable (softplus)."""
    logits = torch.cat([s_pos.reshape(-1), s_neg.reshape(-1)])
    etiquetas = torch.cat([torch.ones_like(s_pos.reshape(-1)), torch.zeros_like(s_neg.reshape(-1))])
    return nn.functional.binary_cross_entropy_with_logits(logits, etiquetas)


def perdida_bpr(s_pos: torch.Tensor, s_neg: torch.Tensor) -> torch.Tensor:
    """Bayesian Personalized Ranking sobre pares (positivo, negativo).

    Modelo probabilístico: P(i ≻_u j) = σ(s_ui − s_uj) para cada par (positivo i, negativo j) del usuario, independientes.
    −log verosimilitud media sobre los B·m pares (``s_pos`` (B,), ``s_neg`` (B, m)):
        L = −1/(B·m) Σ_{b,j} log σ(s⁺_b − s⁻_bj)
    El signo importa: subir s⁺ (o bajar s⁻) baja la pérdida. ``logsigmoid`` es estable para diferencias grandes."""
    return -nn.functional.logsigmoid(s_pos.reshape(-1, 1) - s_neg).mean()


PERDIDAS: dict[str, Callable[[torch.Tensor, torch.Tensor], torch.Tensor]] = {"bce": perdida_bce, "bpr": perdida_bpr}


# =========================================================================== torres (D15)
def _mlp(n_entradas: int, capas: int, unidades: int, n_salidas: int, dropout: float) -> nn.Sequential:
    """``capas`` bloques ocultos Linear → ReLU → Dropout de ``unidades`` y una Linear final a ``n_salidas`` sin activación."""
    bloques: list[nn.Module] = []
    entrada = n_entradas
    for _ in range(capas):
        bloques += [nn.Linear(entrada, unidades), nn.ReLU(), nn.Dropout(dropout)]
        entrada = unidades
    bloques.append(nn.Linear(entrada, n_salidas))
    return nn.Sequential(*bloques)


class TorreUsuario(nn.Module):
    """u = MLP_U(x_u) + E_U[k(u)] ∈ R^d. ``E_U`` (si ``usar_id``) tiene n_ids + 1 filas; la 0 es el vector nulo fijo."""

    def __init__(self, n_entradas: int, capas: int, unidades: int, dim: int, dropout: float, n_ids: int, usar_id: bool):
        super().__init__()
        self.mlp = _mlp(n_entradas, capas, unidades, dim, dropout)
        self.embedding = nn.Embedding(n_ids + 1, dim, padding_idx=0) if usar_id else None
        if self.embedding is not None:
            nn.init.zeros_(self.embedding.weight)          # arranca como la MLP de contenido sola

    def forward(self, x: torch.Tensor, idx: torch.Tensor) -> torch.Tensor:
        u = self.mlp(x)
        if self.embedding is not None:
            u = u + self.embedding(idx)
        return u


class TorreDestino(nn.Module):
    """[v_i ; b_i] = MLP_I(x_i) + E_I[k(i)] ∈ R^{d+1}: las primeras d salidas son v_i y la última el sesgo b_i."""

    def __init__(self, n_entradas: int, capas: int, unidades: int, dim: int, dropout: float, n_ids: int, usar_id: bool):
        super().__init__()
        self.dim = dim
        self.mlp = _mlp(n_entradas, capas, unidades, dim + 1, dropout)
        self.embedding = nn.Embedding(n_ids + 1, dim + 1, padding_idx=0) if usar_id else None
        if self.embedding is not None:
            nn.init.zeros_(self.embedding.weight)

    def forward(self, x: torch.Tensor, idx: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        salida = self.mlp(x)
        if self.embedding is not None:
            salida = salida + self.embedding(idx)
        return salida[..., :self.dim], salida[..., self.dim]


class DosTorres(nn.Module):
    """s_ui = ⟨u, v_i⟩ + b_i. ``forward`` puntúa, para cada usuario b del lote, sus J destinos (J = 1 positivo + m negativos)."""

    def __init__(self, torre_usuario: TorreUsuario, torre_destino: TorreDestino):
        super().__init__()
        self.torre_usuario = torre_usuario
        self.torre_destino = torre_destino

    def forward(self, x_u: torch.Tensor, idx_u: torch.Tensor, x_i: torch.Tensor, idx_i: torch.Tensor) -> torch.Tensor:
        """x_u (B, p_u), idx_u (B,), x_i (B, J, p_i), idx_i (B, J) → s (B, J)."""
        u = self.torre_usuario(x_u, idx_u)                                   # (B, d)
        v, b = self.torre_destino(x_i, idx_i)                                # (B, J, d), (B, J)
        return (u.unsqueeze(1) * v).sum(dim=-1) + b

    def puntuar_matriz(self, x_u, idx_u, x_cat, idx_cat) -> torch.Tensor:
        """Todos contra todos: (n_u, p_u) y (n_cat, p_i) → S (n_u, n_cat) con S = U Vᵀ + 1 bᵀ."""
        u = self.torre_usuario(x_u, idx_u)
        v, b = self.torre_destino(x_cat, idx_cat)
        return u @ v.T + b


def contar_parametros(modelo: nn.Module) -> int:
    """Parámetros entrenables = Σ numel de los que tienen ``requires_grad``, MENOS la fila ``padding_idx`` de cada embedding
    (es un vector nulo fijo: su gradiente es siempre 0 y el optimizador nunca la mueve)."""
    total = sum(p.numel() for p in modelo.parameters() if p.requires_grad)
    fijas = sum(m.embedding_dim for m in modelo.modules() if isinstance(m, nn.Embedding) and m.padding_idx is not None)
    return int(total - fijas)


# =========================================================================== índices de id y negativos (solo train)
def _train(inter: pd.DataFrame) -> pd.DataFrame:
    if "split" not in inter.columns:
        raise ValueError("``inter`` debe traer la columna split (la red usa train y, para la parada temprana, validación)")
    return inter[inter["split"] == particion.TRAIN]


def indices_de_id(inter: pd.DataFrame, catalogo) -> tuple[dict[int, int], np.ndarray]:
    """Índices de los embeddings, calculados SOLO con train (D15, D9).

    Devuelve ``(mapa_usuarios, indice_destinos)``: ``mapa_usuarios[usuario_id] = 1..n_u`` para los usuarios con train (en
    orden ascendente de id; cualquier otro usuario recibe 0) e ``indice_destinos[j]`` = 1..n_i para el destino ``catalogo[j]``
    si tiene train (orden ascendente de id) y 0 si no."""
    train = _train(inter)
    usuarios = np.sort(train["usuario_id"].astype("int64").unique())
    mapa = {int(u): k + 1 for k, u in enumerate(usuarios)}
    cat = np.asarray(catalogo, dtype="int64")
    con_train = np.sort(train["destino_id"].astype("int64").unique())
    indice = np.zeros(len(cat), dtype="int64")
    tiene = _en_ordenado(cat, con_train)                    # ¿el destino tiene alguna interacción en train?
    indice[tiene] = np.searchsorted(con_train, cat[tiene]) + 1  # 1..n_i en orden ascendente de id
    return mapa, indice


def aplicar_dropout_id(idx: np.ndarray, p: float, rng: np.random.Generator) -> np.ndarray:
    """«Dropout de id»: cada índice se reemplaza por 0 («sin id») con probabilidad ``p``, de forma independiente. Solo pone
    ceros: nunca crea un índice que no salió de train."""
    idx = np.asarray(idx, dtype="int64")
    if p <= 0:
        return idx.copy()
    return np.where(rng.random(idx.shape) < p, 0, idx)


def _en_ordenado(valores: np.ndarray, ordenado: np.ndarray) -> np.ndarray:
    """valores ∈ ordenado (``ordenado`` ascendente, sin repetidos), elemento a elemento."""
    if len(ordenado) == 0:
        return np.zeros(valores.shape, dtype=bool)
    pos = np.minimum(np.searchsorted(ordenado, valores), len(ordenado) - 1)
    return ordenado[pos] == valores


def muestrear_negativos(filas: np.ndarray, excluidos: np.ndarray, n_catalogo: int, m: int,
                        rng: np.random.Generator) -> np.ndarray:
    """m negativos por positivo, uniformes sobre las posiciones del catálogo NO excluidas para su usuario (D17).

    ``filas[b]`` = número de fila del usuario del positivo b; ``excluidos`` = códigos ``fila · n_catalogo + columna``
    prohibidos (ascendentes, sin repetidos: en train, el historial de train del usuario). Muestreo con rechazo: se sortea
    j ~ U{0..n−1} y se vuelve a sortear solo donde j está excluido; la distribución final es exactamente uniforme sobre los
    permitidos. Devuelve las columnas (B, m). Error claro si algún usuario no tiene ningún destino permitido."""
    filas = np.asarray(filas, dtype="int64")
    excluidos = np.asarray(excluidos, dtype="int64")
    m = validar_entero(m, "modelo.negativos_por_positivo", minimo=1)
    por_fila = np.bincount(excluidos // n_catalogo, minlength=int(filas.max(initial=0)) + 1) if len(excluidos) else None
    if por_fila is not None and len(filas) and (por_fila[np.unique(filas)] >= n_catalogo).any():
        raise ValueError("hay un usuario sin ningún destino permitido como negativo (todo el catálogo está excluido)")
    neg = rng.integers(0, n_catalogo, size=(len(filas), m))
    malos = _en_ordenado(filas[:, None] * n_catalogo + neg, excluidos)
    while malos.any():
        neg[malos] = rng.integers(0, n_catalogo, size=int(malos.sum()))
        malos = _en_ordenado(filas[:, None] * n_catalogo + neg, excluidos)
    return neg


def _posiciones_catalogo(cat: np.ndarray, ids) -> np.ndarray:
    orden = np.argsort(cat)
    ids = np.asarray(ids, dtype="int64")
    pos = orden[np.minimum(np.searchsorted(cat, ids, sorter=orden), len(cat) - 1)]
    if not np.array_equal(cat[pos], ids):
        raise ValueError("hay destinos que no están en el catálogo")
    return pos


def preparar_train(inter: pd.DataFrame, catalogo) -> dict:
    """Los positivos de TRAIN listos para muestrear negativos (lo usan ``RedDosTorres.ajustar`` y ``negativos_train``).

    Positivos en orden (usuario_id, destino_id). Devuelve ``usuarios`` (usuario de cada positivo), ``usuarios_train``
    (distintos, ascendentes), ``filas_u`` (fila de su usuario en ``usuarios_train``), ``cols`` (columna del destino en
    ``catalogo``), ``excluidos`` (códigos ``fila · n_catalogo + columna`` del historial de train: lo que nunca puede ser
    negativo, D17) y ``n_catalogo``. Validación y prueba no entran (D9)."""
    train = _train(inter).sort_values(["usuario_id", "destino_id"], kind="stable")
    cat = np.asarray(catalogo, dtype="int64")
    usuarios = train["usuario_id"].to_numpy(dtype="int64")
    usuarios_train = np.unique(usuarios)
    filas_u = np.searchsorted(usuarios_train, usuarios)
    cols = _posiciones_catalogo(cat, train["destino_id"].to_numpy(dtype="int64"))
    return {"usuarios": usuarios, "usuarios_train": usuarios_train, "filas_u": filas_u, "cols": cols,
            "excluidos": np.unique(filas_u * len(cat) + cols), "n_catalogo": len(cat)}


def sortear_epoca(prep: dict, m: int, rng_lotes: np.random.Generator,
                  rng_neg: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Una época del entrenamiento (D17): baraja los positivos y sortea m negativos NUEVOS por positivo, uniformes sobre
    catálogo − train de su usuario. Devuelve ``(perm, cols)``: ``perm`` = orden de los positivos y ``cols`` (n, 1 + m) =
    columna del positivo seguida de las de sus negativos. Consume ``rng_lotes`` (permutación) y luego ``rng_neg``."""
    perm = rng_lotes.permutation(len(prep["filas_u"]))
    neg = muestrear_negativos(prep["filas_u"][perm], prep["excluidos"], prep["n_catalogo"], m, rng_neg)
    return perm, np.concatenate([prep["cols"][perm][:, None], neg], axis=1)


def negativos_train(inter: pd.DataFrame, catalogo, m: int, rng: np.random.Generator):
    """(usuario_id, destino positivo, destinos negativos (n, m)) de cada interacción de TRAIN, en el orden barajado de una
    época. Es el MISMO camino que usa ``ajustar`` en cada época (``preparar_train`` + ``sortear_epoca``), con ``rng`` para
    barajar y para sortear. Los negativos son uniformes sobre catálogo − train del usuario: nunca un destino de su train; uno
    de validación sí puede salir (excluirlo usaría validación)."""
    prep = preparar_train(inter, catalogo)
    perm, cols = sortear_epoca(prep, m, rng, rng)
    cat = np.asarray(catalogo, dtype="int64")
    return prep["usuarios"][perm], cat[cols[:, 0]], cat[cols[:, 1:]]


# =========================================================================== bucles de entrenamiento y validación
def train_loop(modelo: DosTorres, optimizador: torch.optim.Optimizer, lotes, funcion_perdida) -> float:
    """Una época: para cada minilote (x_u, idx_u, x_i, idx_i), con la columna 0 de x_i el positivo y las demás los negativos,
    calcula la pérdida, retropropaga y da un paso de Adam. Devuelve la pérdida media de la época (ponderada por positivos)."""
    modelo.train()                                              # activa el dropout
    total, n = 0.0, 0
    for x_u, idx_u, x_i, idx_i in lotes:
        s = modelo(x_u, idx_u, x_i, idx_i)                      # (B, 1 + m)
        perdida = funcion_perdida(s[:, 0], s[:, 1:])
        optimizador.zero_grad()
        perdida.backward()                                     # backpropagation
        optimizador.step()                                     # actualización de Adam (con weight decay)
        total += float(perdida.item()) * len(x_u)
        n += len(x_u)
    return total / n


def val_loop(modelo: DosTorres, val: dict, funcion_perdida) -> tuple[float, float]:
    """Pérdida de validación (positivos de validación contra negativos fijos) y NDCG@5 de validación (candidatos =
    catálogo − train; mismo desempate en todas las épocas). Sin dropout ni gradiente."""
    modelo.eval()
    with torch.no_grad():
        s = modelo(val["x_u"], val["idx_u"], val["x_i"], val["idx_i"])
        perdida = float(funcion_perdida(s[:, 0], s[:, 1:]).item())
        S = modelo.puntuar_matriz(val["x_u_rank"], val["idx_u_rank"], val["x_cat"], val["idx_cat"]).double().numpy()
    tops = metricas.rankear_usuarios(S, val["usuarios"], val["catalogo"], val["cands"], K_PARADA,
                                     np.random.default_rng(val["semilla_desempate"]))
    return perdida, metricas.ndcg_medio(tops, val["rel"], val["usuarios"], K_PARADA)


# =========================================================================== diagnósticos
def diagnostico_degeneracion(S: np.ndarray, normas_u: np.ndarray, normas_v: np.ndarray, tolerancia: float) -> dict:
    """Guarda de degeneración de la red. Degenerada si se cumple alguna (en este orden; ``motivo_degenerado`` es la primera):
      1. ``puntajes_no_finitos``: algún s_ui es NaN o ±inf;
      2. ``puntajes_constantes_por_usuario``: max_u (max_i s_ui − min_i s_ui) < tolerancia (la lista sale solo del desempate);
      3. ``producto_de_normas_bajo_tolerancia``: max_u ‖u‖ · max_i ‖v_i‖ < tolerancia (la parte ⟨u, v_i⟩ es nula: el modelo
         solo puede ordenar por el sesgo b_i, igual para todos)."""
    finitos = bool(np.isfinite(S).all())
    rango = float(np.max(S.max(axis=1) - S.min(axis=1))) if finitos and S.size else float("nan")
    producto = float(np.max(normas_u) * np.max(normas_v)) if len(normas_u) and len(normas_v) else 0.0
    condiciones = {"puntajes_no_finitos": not finitos,
                   "puntajes_constantes_por_usuario": bool(finitos and rango < tolerancia),
                   "producto_de_normas_bajo_tolerancia": bool(producto < tolerancia)}
    motivo = next((k for k, v in condiciones.items() if v), None)
    return {"degenerado": motivo is not None, "motivo_degenerado": motivo, "condiciones_degenerado": condiciones,
            "rango_max_por_usuario": rango if finitos else None, "max_norma_u_por_norma_v": producto}


def medidas_personalizacion(S: np.ndarray, k: int = 10) -> dict:
    """Cuánto cambia el ORDEN de los destinos entre usuarios (diagnóstico que se reporta; no declara degenerada la corrida).

    Descomposición de dos vías de S (usuarios × destinos): S_ui = μ + α_u + β_i + E_ui, con α_u = media de la fila u − μ y
    β_i = media de la columna i − μ. El desplazamiento propio de cada usuario α_u (p. ej. ⟨u, v̄⟩) no cambia su orden, y β_i
    (incluye b_i) es común a todos y da el mismo orden a todos: la parte de s_ui que cambia el orden entre usuarios —sin b_i
    ni el desplazamiento propio de cada usuario— es la interacción doble centrada
        E = S − S.mean(1) − S.mean(0) + S.mean().
      personalizacion               = media sobre destinos de la desviación (ddof 0) entre usuarios de E_ui (depende de la
                                      escala de S: compararla entre semillas con cautela)
      fraccion_varianza_interaccion = ‖E‖² / ‖S − μ‖², con ‖S − μ‖² = n_destinos·‖α‖² + n_usuarios·‖β‖² + ‖E‖² (los tres
                                      términos son ortogonales). Se calcula con esa suma para que el redondeo no la saque
                                      de [0, 1]; 0 si S es constante. Con S casi constante (diferencias de pocos ulp) el
                                      valor es ruido de redondeo; esas corridas ya las marca `puntajes_constantes_por_usuario`.
                                      Con NaN sale NaN (ya lo marca `puntajes_no_finitos`). El denominador incluye α_u: no
                                      es «la fracción del orden que es personal»
      listas_top10_distintas        = número de listas top-k distintas (catálogo completo, orden estable)
      fraccion_mismo_top1           = fracción de usuarios cuyo top-1 es el top-1 más frecuente
    E ≠ 0 no garantiza que los órdenes difieran: las cuatro medidas juntas, no `personalizacion` sola, dicen cuánto cambia el
    orden."""
    S = np.asarray(S, dtype=float)
    mu = S.mean()
    alfa, beta = S.mean(axis=1) - mu, S.mean(axis=0) - mu                    # efecto de cada usuario y de cada destino
    E = S - S.mean(axis=1, keepdims=True) - S.mean(axis=0, keepdims=True) + mu
    e2 = float((E ** 2).sum())
    total = e2 + S.shape[1] * float((alfa ** 2).sum()) + S.shape[0] * float((beta ** 2).sum())   # = ‖S − μ‖²
    constante = bool(np.ptp(S) == 0)          # con S constante las medias redondeadas dejan ≈ 1e-30 a 1e-27, no 0 exacto
    orden = np.argsort(-S, axis=1, kind="stable")[:, :k]
    _, conteo_top1 = np.unique(orden[:, 0], return_counts=True)
    return {"personalizacion": float(E.std(axis=0).mean()),
            "fraccion_varianza_interaccion": 0.0 if constante or total == 0 else e2 / total,
            "listas_top10_distintas": int(len({tuple(f) for f in orden.tolist()})),
            "fraccion_mismo_top1": float(conteo_top1.max() / len(S))}


def capas_de_mlp(mlp: nn.Sequential) -> list[dict]:
    """Recorre una MLP de ``_mlp``: por cada ``Linear``, su posición, el módulo, si la sigue una ReLU y la probabilidad del
    Dropout que sigue a esa ReLU (``None`` si no hay). Lo usan ``capas_torre_usuario`` y ``arquitectura``."""
    mods = list(mlp)
    capas = []
    for j, mod in enumerate(mods):
        if not isinstance(mod, nn.Linear):
            continue
        relu = j + 1 < len(mods) and isinstance(mods[j + 1], nn.ReLU)
        dropout = mods[j + 2].p if relu and j + 2 < len(mods) and isinstance(mods[j + 2], nn.Dropout) else None
        capas.append({"posicion": j, "linear": mod, "activacion": "relu" if relu else "ninguna", "dropout": dropout})
    return capas


# =========================================================================== hiperparámetros y fábrica
def _validar_hiperparametros(hp: dict) -> dict:
    faltan = [c for c in CLAVES if c not in hp]
    if faltan:
        raise ValueError(f"faltan hiperparámetros de la red: {faltan}")
    for c in ("modelo.dim_embedding", "modelo.unidades_usuario", "modelo.unidades_destino", "modelo.negativos_por_positivo",
              "entrenamiento.max_epocas", "entrenamiento.paciencia", "entrenamiento.tam_lote"):
        validar_entero(hp[c], c, minimo=1)
    for c in ("modelo.capas_usuario", "modelo.capas_destino"):
        validar_entero(hp[c], c, minimo=0)
    for c in ("modelo.usar_id_usuario", "modelo.usar_id_destino", "modelo.usar_demografia"):
        if not isinstance(hp[c], bool):
            raise TypeError(f"{c} debe ser true o false; se recibió {hp[c]!r}")
    for c, lo, hi in (("modelo.dropout_id", 0.0, 1.0), ("regularizacion.dropout", 0.0, 1.0)):
        if not (isinstance(hp[c], (int, float)) and not isinstance(hp[c], bool) and lo <= hp[c] < hi):
            raise ValueError(f"{c} debe estar en [{lo}, {hi}); se recibió {hp[c]!r}")
    if not (isinstance(hp["entrenamiento.lr"], (int, float)) and hp["entrenamiento.lr"] > 0):
        raise ValueError(f"entrenamiento.lr debe ser > 0; se recibió {hp['entrenamiento.lr']!r}")
    if not (isinstance(hp["regularizacion.weight_decay"], (int, float)) and hp["regularizacion.weight_decay"] >= 0):
        raise ValueError(f"regularizacion.weight_decay debe ser >= 0; se recibió {hp['regularizacion.weight_decay']!r}")
    if hp["perdida.tipo"] not in PERDIDAS_VALIDAS:
        raise ValueError(f"perdida.tipo debe ser uno de {list(PERDIDAS_VALIDAS)}; se recibió {hp['perdida.tipo']!r}")
    return hp


def hiperparametros_efectivos(cfg: dict) -> dict:
    """Bloques de primer nivel ``modelo``, ``perdida``, ``entrenamiento`` y ``regularizacion`` (claves con punto) con
    ``cfg["red"]["hiperparametros"]`` encima (con ``red.hiperparametros_desde: hpo`` el arnés pone ahí el mejor ensayo; con
    ``config`` queda vacío y mandan los bloques, como con ``--set modelo.dim_embedding=8``). Una clave de encima que no esté
    en los bloques es error. Si el mejor ensayo reemplaza un valor distinto de los bloques se avisa (``UserWarning``)."""
    planos = {f"{b}.{k}": v for b in BLOQUES for k, v in cfg[b].items()}
    encima = dict(cfg.get("red", {}).get("hiperparametros") or {})
    desconocidas = sorted(set(encima) - set(planos))
    if desconocidas:
        raise ValueError(f"red.hiperparametros trae claves que no están en los bloques {list(BLOQUES)}: {desconocidas}")
    distintas = {k: (planos[k], v) for k, v in encima.items() if planos[k] != v}
    if distintas and cfg.get("red", {}).get("hiperparametros_desde") == "hpo":
        warnings.warn(f"red.hiperparametros_desde = hpo: el mejor ensayo reemplaza estos valores de la config "
                      f"(config → ensayo): {distintas}. Para que manden los bloques usa --set red.hiperparametros_desde=config",
                      UserWarning, stacklevel=2)
    return {**planos, **encima}


def fabrica_red(cfg: dict) -> RedDosTorres:
    """``referencias.MODELOS["red"]``: hiperparámetros efectivos + contenido de ``contenido.py`` (únicas lecturas)."""
    hp = hiperparametros_efectivos(cfg)
    usuarios, destinos = contenido_m3.cargar_contenido(cfg, usar_demografia=bool(hp["modelo.usar_demografia"]))
    return RedDosTorres(hp, usuarios, destinos, tolerancia_degenerado=cfg["red"]["tolerancia_degenerado"],
                        carpeta_resultados=cfg["salida"]["carpeta"], device=cfg.get("device", "cpu"))


# =========================================================================== el recomendador
class RedDosTorres:
    """Recomendador de dos torres con la interfaz ``referencias.Recomendador`` (ver el docstring del módulo).

    ``usar_validacion = False`` entrena ``entrenamiento.max_epocas`` épocas sin mirar validación (lo usa la guarda
    ``AJUSTES_SOLO_TRAIN`` de ``tests/test_fuga_m3.py``); el arnés y la búsqueda usan siempre la parada temprana."""

    nombre = "red"
    descripcion_frios = ("Índice de id 0 (sin id: embedding nulo fijo) → v_i y b_i salen solo de su tipo (torre de destino "
                         "sobre el one-hot de tipo): reciben puntaje solo por su tipo y todos los fríos del mismo tipo el mismo. "
                         "Pueden superar a destinos con train; si entran o no al top-K depende del entrenamiento, así que se "
                         "MIDE en `frios_por_lista`.")

    def __init__(self, hiperparametros: dict, contenido_usuarios: contenido_m3.Contenido,
                 contenido_destinos: contenido_m3.Contenido, tolerancia_degenerado: float = 1e-6,
                 carpeta_resultados: str | Path | None = None, device: str = "cpu", usar_validacion: bool = True):
        self.hiperparametros = _validar_hiperparametros(dict(hiperparametros))
        if not tolerancia_degenerado > 0:
            raise ValueError(f"red.tolerancia_degenerado debe ser > 0; se recibió {tolerancia_degenerado}")
        self.contenido_usuarios, self.contenido_destinos = contenido_usuarios, contenido_destinos
        self.tolerancia_degenerado = float(tolerancia_degenerado)
        self.carpeta_resultados = None if carpeta_resultados is None else Path(carpeta_resultados)
        self.device = resolver_device(device)
        self.usar_validacion = bool(usar_validacion)
        self.funcion_perdida = PERDIDAS[self.hiperparametros["perdida.tipo"]]
        self.red: DosTorres | None = None
        self.curvas: dict = {}
        self._diagnosticos: dict = {}
        self._val: dict | None = None                # datos de validación del último ajuste (None: sin validación)
        self._prep: dict | None = None               # positivos de train del último ajuste (preparar_train + filas de contenido)
        self.n_negativos_por_epoca: int | None = None

    # ----------------------------------------------------------------------- utilidades
    def _exigir_ajustado(self, metodo: str) -> None:
        if self.red is None:
            raise RuntimeError(f"red: llama a ajustar() antes de {metodo}()")

    def _t(self, x, dtype=torch.float32) -> torch.Tensor:
        return torch.as_tensor(np.asarray(x), dtype=dtype, device=self.device)

    def _indices_tensor(self, x) -> torch.Tensor:
        """Índices enteros (filas, columnas o ids) como tensor ``long`` para indexar tensores o embeddings."""
        return self._t(x, torch.long)

    def _construir(self, n_usuarios: int, n_destinos: int) -> DosTorres:
        hp = self.hiperparametros
        tu = TorreUsuario(self.contenido_usuarios.X.shape[1], hp["modelo.capas_usuario"], hp["modelo.unidades_usuario"],
                          hp["modelo.dim_embedding"], hp["regularizacion.dropout"], n_usuarios, hp["modelo.usar_id_usuario"])
        td = TorreDestino(self.contenido_destinos.X.shape[1], hp["modelo.capas_destino"], hp["modelo.unidades_destino"],
                          hp["modelo.dim_embedding"], hp["regularizacion.dropout"], n_destinos, hp["modelo.usar_id_destino"])
        return DosTorres(tu, td).to(self.device)

    def _indices_usuarios(self, ids) -> np.ndarray:
        return np.array([self.mapa_usuarios.get(int(u), 0) for u in ids], dtype="int64")

    def _lotes(self, rng_lotes, rng_neg, rng_id):
        """Minilotes de una época: positivos barajados y m negativos NUEVOS por positivo (``sortear_epoca``, D17); luego el
        dropout de id, primero de los usuarios y después de los destinos (mismo orden de consumo del azar)."""
        hp = self.hiperparametros
        perm, cols = sortear_epoca(self._prep, hp["modelo.negativos_por_positivo"], rng_lotes, rng_neg)   # (n, 1 + m)
        filas = self._prep["filas_contenido"][perm]
        idx_u = aplicar_dropout_id(self._idx_u_contenido[filas], hp["modelo.dropout_id"], rng_id)
        idx_i = aplicar_dropout_id(self.indice_destinos[cols], hp["modelo.dropout_id"], rng_id)
        tam = hp["entrenamiento.tam_lote"]
        for a in range(0, len(perm), tam):
            b = slice(a, a + tam)
            yield (self._Xu[self._indices_tensor(filas[b])], self._indices_tensor(idx_u[b]),
                   self._Xi[self._indices_tensor(cols[b])], self._indices_tensor(idx_i[b]))

    def _datos_validacion(self, inter, rng_val, semilla_desempate) -> dict | None:
        """Positivos de validación con m negativos fijos (catálogo − train − el propio positivo) y candidatos de NDCG@5."""
        val = inter[inter["split"] == particion.VALIDACION].sort_values(["usuario_id", "destino_id"], kind="stable")
        if not self.usar_validacion or val.empty:
            return None
        usuarios_train = self._prep["usuarios_train"]
        usuarios_val = val["usuario_id"].to_numpy(dtype="int64")
        if not _en_ordenado(usuarios_val, usuarios_train).all():  # D3 lo impide; se exige para que los códigos tengan sentido
            raise ValueError("hay usuarios de validación sin interacciones en train")
        filas_val = np.searchsorted(usuarios_train, usuarios_val)
        cols_val = _posiciones_catalogo(self.catalogo, val["destino_id"].to_numpy(dtype="int64"))
        excl = np.union1d(self._prep["excluidos"], filas_val * self.n_catalogo + cols_val)   # train y el propio positivo
        neg = muestrear_negativos(filas_val, excl, self.n_catalogo, self.hiperparametros["modelo.negativos_por_positivo"],
                                  rng_val)
        cols = np.concatenate([cols_val[:, None], neg], axis=1)
        fc = self.contenido_usuarios.filas(usuarios_val)
        cands = particion.candidatos(inter, self.catalogo, particion.VALIDACION)
        rel = particion.relevantes(inter, particion.VALIDACION)
        usuarios_rank = sorted(cands)
        fr = self.contenido_usuarios.filas(usuarios_rank)
        it = self._indices_tensor
        return {"x_u": self._Xu[it(fc)], "idx_u": it(self._idx_u_contenido[fc]), "x_i": self._Xi[it(cols)],
                "idx_i": it(self.indice_destinos[cols]), "x_u_rank": self._Xu[it(fr)],
                "idx_u_rank": it(self._idx_u_contenido[fr]), "x_cat": self._Xi, "idx_cat": it(self.indice_destinos),
                "usuarios": usuarios_rank, "catalogo": self.catalogo, "cands": cands, "rel": rel,
                "semilla_desempate": semilla_desempate}

    # ----------------------------------------------------------------------- interfaz Recomendador
    def _preparar_train(self, inter: pd.DataFrame, catalogo) -> None:
        """Índices de id, tensores de contenido en el orden del catálogo y positivos de train (``preparar_train``). Solo
        train; no consume azar."""
        self.catalogo = np.asarray(catalogo, dtype="int64")
        self.n_catalogo = len(self.catalogo)
        self.mapa_usuarios, self.indice_destinos = indices_de_id(inter, self.catalogo)       # solo train
        self._idx_u_contenido = self._indices_usuarios(self.contenido_usuarios.ids)
        self._Xu = self._t(self.contenido_usuarios.X)
        self._Xi = self._t(self.contenido_destinos.X[self.contenido_destinos.filas(self.catalogo)])
        prep = preparar_train(inter, self.catalogo)
        prep["filas_contenido"] = self.contenido_usuarios.filas(prep["usuarios"])
        self._prep = prep
        self.n_negativos_por_epoca = len(prep["filas_u"]) * self.hiperparametros["modelo.negativos_por_positivo"]

    def _entrenar_con_parada(self, opt: torch.optim.Optimizer, val: dict | None, rng_lotes, rng_neg, rng_id) -> dict:
        """El bucle de épocas y CUÁNDO PARA (D19). Cada época: ``train_loop`` y, si hay validación, ``val_loop``. La época
        mejora si su NDCG@5 de validación es ESTRICTAMENTE mayor que el mejor (en empate se queda la anterior); tras
        ``entrenamiento.paciencia`` épocas seguidas sin mejorar, para. Al final restaura los pesos de la mejor época. Sin
        validación entrena ``max_epocas`` épocas y se queda con la última. Devuelve el historial y la mejor época."""
        hp = self.hiperparametros
        historial = {"epoca": [], "perdida_train": [], "perdida_validacion": [], "ndcg5_validacion": []}
        mejor, mejor_epoca, sin_mejora, mejor_estado = -np.inf, 0, 0, None
        for epoca in range(1, hp["entrenamiento.max_epocas"] + 1):
            p_train = train_loop(self.red, opt, self._lotes(rng_lotes, rng_neg, rng_id), self.funcion_perdida)
            historial["epoca"].append(epoca)
            historial["perdida_train"].append(p_train)
            if val is None:
                historial["perdida_validacion"].append(None)
                historial["ndcg5_validacion"].append(None)
                mejor_epoca = epoca
                continue
            p_val, ndcg = val_loop(self.red, val, self.funcion_perdida)
            historial["perdida_validacion"].append(p_val)
            historial["ndcg5_validacion"].append(ndcg)
            if ndcg > mejor:                                        # mejora estricta
                mejor, mejor_epoca, sin_mejora = ndcg, epoca, 0
                mejor_estado = copy.deepcopy(self.red.state_dict())
            else:
                sin_mejora += 1
                if sin_mejora >= hp["entrenamiento.paciencia"]:     # parada temprana
                    break
        if mejor_estado is not None:
            self.red.load_state_dict(mejor_estado)                 # pesos de la mejor época
        return {**historial, "mejor_epoca": mejor_epoca, "epoca_parada": historial["epoca"][-1],
                "paciencia": hp["entrenamiento.paciencia"], "max_epocas": hp["entrenamiento.max_epocas"],
                "ndcg5_validacion_mejor": None if val is None else float(mejor)}

    def ajustar(self, inter: pd.DataFrame, catalogo, rng: np.random.Generator) -> RedDosTorres:
        """Entrena con train y para con validación (D9, D19). PRUEBA se descarta al entrar: la red no puede verla."""
        if "split" not in inter.columns:
            raise ValueError("RedDosTorres.ajustar: ``inter`` debe traer la columna split")
        inter = inter[inter["split"] != particion.PRUEBA]                                   # D9: nunca prueba
        activar_determinismo(self.device)
        # Todas las semillas hijas salen de UN sorteo del rng recibido (consumo fijo, sin importar los datos).
        s_torch, s_lotes, s_neg, s_id, s_val, s_desempate = (int(x) for x in rng.integers(0, 2**31 - 1, N_SEMILLAS_HIJAS))
        rng_lotes, rng_neg, rng_id, rng_val = (np.random.default_rng(s) for s in (s_lotes, s_neg, s_id, s_val))
        self._preparar_train(inter, catalogo)
        self._val = self._datos_validacion(inter, rng_val, s_desempate)
        hp = self.hiperparametros
        with torch.random.fork_rng(devices=[]):                     # el estado global de torch queda como estaba
            torch.manual_seed(s_torch)                              # inicialización y máscaras de dropout
            self.red = self._construir(len(self.mapa_usuarios), int(self.indice_destinos.max(initial=0)))
            opt = torch.optim.Adam(self.red.parameters(), lr=hp["entrenamiento.lr"],
                                   weight_decay=hp["regularizacion.weight_decay"])
            self.curvas = self._entrenar_con_parada(opt, self._val, rng_lotes, rng_neg, rng_id)
        self.red.eval()
        self._calcular_diagnosticos(self._val)
        return self

    def _matriz(self, filas_contenido: np.ndarray, idx_u: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            S = self.red.puntuar_matriz(self._Xu[self._indices_tensor(filas_contenido)], self._indices_tensor(idx_u),
                                        self._Xi, self._indices_tensor(self.indice_destinos))
        return S.double().numpy()

    def puntuar(self, usuario_ids: Sequence[int]) -> np.ndarray:
        """(n_usuarios, n_catálogo) en el orden de ``catalogo``. Un usuario sin train usa el índice 0 (solo preferencias)."""
        self._exigir_ajustado("puntuar")
        self.red.eval()
        filas = self.contenido_usuarios.filas(usuario_ids)
        return self._matriz(filas, self._idx_u_contenido[filas])

    def n_parametros(self) -> int:
        self._exigir_ajustado("n_parametros")
        return contar_parametros(self.red)

    def _calcular_diagnosticos(self, val: dict | None) -> None:
        usuarios = val["usuarios"] if val is not None else self._prep["usuarios_train"]
        filas = self.contenido_usuarios.filas(usuarios)
        S = self._matriz(filas, self._idx_u_contenido[filas])
        with torch.no_grad():
            U = self.red.torre_usuario(self._Xu[self._indices_tensor(filas)],
                                       self._indices_tensor(self._idx_u_contenido[filas]))
            V, _ = self.red.torre_destino(self._Xi, self._indices_tensor(self.indice_destinos))
        d = diagnostico_degeneracion(S, U.norm(dim=1).double().numpy(), V.norm(dim=1).double().numpy(),
                                     self.tolerancia_degenerado)
        # Personalización del ranking (se reporta; no declara degenerada la corrida): ver medidas_personalizacion.
        if np.isfinite(S).all():
            d.update(medidas_personalizacion(S))
        else:
            d.update(personalizacion=None, fraccion_varianza_interaccion=None, listas_top10_distintas=None,
                     fraccion_mismo_top1=None)
        d.update(mejor_epoca=self.curvas["mejor_epoca"], epoca_parada=self.curvas["epoca_parada"],
                 ndcg5_validacion_mejor=self.curvas["ndcg5_validacion_mejor"],
                 negativos_por_epoca=self.n_negativos_por_epoca,
                 usuarios_diagnostico="validacion" if val is not None else "train")
        self._diagnosticos = d

    def diagnosticos(self) -> dict:
        self._exigir_ajustado("diagnosticos")
        return dict(self._diagnosticos)

    def ndcg5_validacion_actual(self) -> float:
        """NDCG@5 de validación de los pesos actuales con el mismo desempate de la parada temprana (comprobación)."""
        self._exigir_ajustado("ndcg5_validacion_actual")
        if self._val is None:
            raise ValueError("el ajuste no usó validación")
        return val_loop(self.red, self._val, self.funcion_perdida)[1]

    # ----------------------------------------------------------------------- exportación
    def vector_usuario_sin_id(self, x_u) -> np.ndarray:
        """u de un perfil nuevo (índice 0): la torre de usuario sobre las preferencias, en modo evaluación."""
        self._exigir_ajustado("vector_usuario_sin_id")
        self.red.eval()
        with torch.no_grad():
            u = self.red.torre_usuario(self._t(np.asarray(x_u, dtype=np.float32).reshape(1, -1)),
                                       torch.zeros(1, dtype=torch.long))
        return u[0].double().numpy()

    def capas_torre_usuario(self) -> list[dict]:
        """La MLP de usuario como capas {W (salida × entrada, como ``nn.Linear.weight``), b, activacion} (núcleo §5.8)."""
        self._exigir_ajustado("capas_torre_usuario")
        return [{"W": c["linear"].weight.detach().double().numpy().tolist(),
                 "b": c["linear"].bias.detach().double().numpy().tolist(), "activacion": c["activacion"]}
                for c in capas_de_mlp(self.red.torre_usuario.mlp)]

    def arquitectura(self) -> dict:
        """Capas, formas de entrada y salida, activaciones y parámetros entrenables (núcleo §5.9); total = n_parametros()."""
        self._exigir_ajustado("arquitectura")
        capas = []
        for torre, mod_torre in (("usuario", self.red.torre_usuario), ("destino", self.red.torre_destino)):
            for c in capas_de_mlp(mod_torre.mlp):
                lin = c["linear"]
                capas.append({"torre": torre, "nombre": f"torre_{torre}.mlp.{c['posicion']}", "tipo": "Linear",
                              "entrada": lin.in_features, "salida": lin.out_features, "activacion": c["activacion"],
                              "dropout": c["dropout"], "parametros": int(lin.weight.numel() + lin.bias.numel())})
            emb = mod_torre.embedding
            if emb is not None:
                capas.append({"torre": torre, "nombre": f"torre_{torre}.embedding", "tipo": "Embedding",
                              "entrada": f"índice de id 0..{emb.num_embeddings - 1} (0 = sin id, fila fija)",
                              "salida": emb.embedding_dim, "activacion": "ninguna", "dropout": None,
                              "parametros": int((emb.num_embeddings - 1) * emb.embedding_dim),
                              "nota": "se suma a la salida de la MLP; la fila 0 (padding_idx) no cuenta"})
        d = self.hiperparametros["modelo.dim_embedding"]
        return {"modelo": self.nombre, "capas": capas, "total_parametros": self.n_parametros(),
                "entrada_usuario": list(self.contenido_usuarios.columnas), "entrada_destino": list(self.contenido_destinos.columnas),
                "salida_usuario": f"u ∈ R^{d}", "salida_destino": f"(v_i, b_i) ∈ R^{d} × R",
                "puntaje": "s_ui = ⟨u, v_i⟩ + b_i (logit)", "hiperparametros": dict(self.hiperparametros)}

    def guardar(self, carpeta, semilla: int, evidencia: dict) -> list[Path]:
        """``<carpeta>/red.pt`` (state_dict) y ``red.json``; además ``curvas/red.json`` y ``arquitectura/red.json`` en la carpeta
        de resultados (núcleo §5.9). El arnés la llama con la primera semilla."""
        self._exigir_ajustado("guardar")
        carpeta = Path(carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta_pt = carpeta / f"{self.nombre}.pt"
        torch.save(self.red.state_dict(), ruta_pt)
        destinos_con_id = {str(int(d)): int(k) for d, k in zip(self.catalogo, self.indice_destinos) if k > 0}
        rutas = [ruta_pt, save_json(carpeta / f"{self.nombre}.json", {
            "modelo": self.nombre, "semilla": semilla, "hiperparametros": dict(self.hiperparametros),
            "dim_embedding": self.hiperparametros["modelo.dim_embedding"], "n_parametros": self.n_parametros(),
            "columnas_usuario": list(self.contenido_usuarios.columnas),
            "columnas_destino": list(self.contenido_destinos.columnas),
            "mapa_ids": {"usuario": {str(u): k for u, k in self.mapa_usuarios.items()}, "destino": destinos_con_id},
            "exportacion": ("Perfil nuevo (app, núcleo §5.8): la MLP de usuario con índice 0 es la `torre_usuario` (capas "
                            "W·h + b con ReLU, sin el embedding de id); (v_i, b_i) de cada destino se precalculan con su torre "
                            "(MLP de tipo + embedding de id). Ids fuera de `mapa_ids` usan el índice 0."),
            "evidencia": evidencia})]
        if self.carpeta_resultados is not None:
            rutas.append(save_json(self.carpeta_resultados / "curvas" / f"{self.nombre}.json", {
                "modelo": self.nombre, "semilla": semilla, "perdida_tipo": self.hiperparametros["perdida.tipo"], **self.curvas,
                "nota": ("Por época: pérdida media de train (negativos nuevos), pérdida de validación (negativos fijos) y "
                         "NDCG@5 de validación; la red se queda con los pesos de `mejor_epoca` y se detuvo en "
                         "`epoca_parada` (paciencia épocas sin mejorar)."),
                "evidencia": evidencia}))
            rutas.append(save_json(self.carpeta_resultados / "arquitectura" / f"{self.nombre}.json",
                                   {**self.arquitectura(), "semilla": semilla, "evidencia": evidencia}))
        return rutas
