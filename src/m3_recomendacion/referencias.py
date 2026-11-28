"""M3 — modelos de referencia (JJ-4; D9, D11): popularidad, factorización de matrices implícita por ALS y aleatorio.

Interfaz común (``Recomendador``). El arnés (``experimento.py``) solo conoce estos tres métodos y dos atributos, así que
**JJ-5 agrega su modelo en ``MODELOS`` (o en su propio módulo, registrándolo aquí) y lo nombra en ``cfg["modelos"]``, sin
reescribir el arnés**:

    ajustar(inter, catalogo, rng) -> self   ``inter`` TRAE la columna ``split``; el modelo usa SOLO ``split == "train"`` (D9)
    puntuar(usuario_ids) -> np.ndarray      (n_usuarios, n_catalogo), columnas en el orden de ``catalogo``
    n_parametros() -> int                   parámetros estimados (núcleo §6)
    diagnosticos() -> dict                  datos propios del modelo ajustado (``{}`` si no aplica). El arnés los resume entre
                                            semillas y, si trae ``degenerado`` verdadero, detiene el experimento con error claro
    guardar(carpeta, semilla, evidencia) -> list[Path]   escribe los artefactos del modelo (el arnés la llama solo con la
                                            primera semilla); ``[]`` si no hay nada que guardar
    nombre: str; hiperparametros: dict; descripcion_frios: str (cómo trata los destinos sin interacciones en train, D14)

Un modelo con búsqueda de hiperparámetros se registra además en ``hpo.BUSQUEDAS`` con el mismo nombre; el arnés le asigna sus
hiperparámetros, ``n_configuraciones_busqueda`` y ``tiempo_busqueda_s`` desde ``familias.<nombre>`` de ``hpo_ensayos.json``
(un modelo sin búsqueda tiene 1 y 0). Su fábrica lee los hiperparámetros de ``cfg[nombre]["hiperparametros"]``.

Ningún modelo lee validación ni prueba (lo comprueban ``AJUSTES_SOLO_TRAIN`` de ``tests/test_fuga_m3.py``) ni la columna
``popularidad`` de ``destinos.parquet`` (es un atributo de la fuente, no un conteo de interacciones; D11). Toda aleatoriedad
llega por el ``np.random.Generator`` recibido (``make_rng(base_seed, run_id)``); nunca se usa ``np.random.seed``.

Referencia de ALS: Hu, Koren y Volinsky (2008), «Collaborative filtering for implicit feedback datasets», ICDM
[VERIFICAR en JJ-9; sin DOI hasta entonces].
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds

from src.comun.results import save_json
from src.comun.seeds import validar_entero
from src.m3_recomendacion import particion


class Recomendador(Protocol):
    """Contrato que implementan los modelos de M3 (ver el docstring del módulo)."""

    nombre: str
    hiperparametros: dict
    descripcion_frios: str

    def ajustar(self, inter: pd.DataFrame | None, catalogo, rng: np.random.Generator) -> Recomendador: ...

    def puntuar(self, usuario_ids: Sequence[int]) -> np.ndarray: ...

    def n_parametros(self) -> int: ...

    def diagnosticos(self) -> dict: ...

    def guardar(self, carpeta: Path, semilla: int, evidencia: dict) -> list[Path]: ...


def _no_ajustado(nombre: str) -> RuntimeError:
    return RuntimeError(f"{nombre}: llama a ajustar() antes de puntuar() o n_parametros()")


# =========================================================================== popularidad
class Popularidad:
    """Puntaje(u, i) = conteo de interacciones de i en train, igual para todos los usuarios (D11 a).

    Un destino sin train queda con puntaje 0 (al final del orden); los empates los rompe al azar ``ordenar_candidatos`` con la
    semilla de la corrida. ``n_parametros()`` = n_catálogo: no tiene hiperparámetros, pero SÍ estima un conteo por destino
    (1 000 en los datos reales); se reporta ese número porque es lo que el modelo aprende de train (núcleo §6, «número de
    parámetros estimados»)."""

    nombre = "popularidad"
    descripcion_frios = ("Puntaje 0: quedan al final y nunca entran al top-K mientras el usuario tenga al menos K candidatos con "
                         "conteo >= 1 (se comprueba en `min_candidatos_no_frios`); su techo de acierto es la fracción de "
                         "usuarios con objetivo no frío.")

    def __init__(self) -> None:
        self.hiperparametros: dict = {}
        self._pop: np.ndarray | None = None

    def ajustar(self, inter, catalogo, rng) -> Popularidad:
        self._pop = particion.popularidad_train(inter, catalogo).to_numpy(dtype=float)
        return self

    def puntuar(self, usuario_ids) -> np.ndarray:
        if self._pop is None:
            raise _no_ajustado(self.nombre)
        return np.tile(self._pop, (len(usuario_ids), 1))

    def n_parametros(self) -> int:
        if self._pop is None:
            raise _no_ajustado(self.nombre)
        return int(len(self._pop))

    def diagnosticos(self) -> dict:
        return {}

    def guardar(self, carpeta, semilla, evidencia) -> list[Path]:
        return []


# =========================================================================== aleatorio
class Aleatorio:
    """Piso de referencia: puntaje(u, i) ~ U(0, 1) independiente. Con el desempate de ``ordenar_candidatos`` el top-K entre
    los candidatos es un subconjunto uniforme sin reemplazo; su valor esperado es analítico (``metricas.esperados_aleatorio``).
    No usa ``inter`` ni estima nada (``n_parametros()`` = 0). El generador recibido se conserva para ``puntuar``."""

    nombre = "aleatorio"
    descripcion_frios = "Todos son alcanzables: el azar no distingue destinos con y sin interacciones de train."

    def __init__(self) -> None:
        self.hiperparametros: dict = {}
        self._rng: np.random.Generator | None = None
        self._n_catalogo = 0

    def ajustar(self, inter, catalogo, rng) -> Aleatorio:
        self._rng, self._n_catalogo = rng, len(np.asarray(catalogo))
        return self

    def puntuar(self, usuario_ids) -> np.ndarray:
        if self._rng is None:
            raise _no_ajustado(self.nombre)
        return self._rng.random((len(usuario_ids), self._n_catalogo))

    def n_parametros(self) -> int:
        return 0

    def diagnosticos(self) -> dict:
        return {}

    def guardar(self, carpeta, semilla, evidencia) -> list[Path]:
        return []


# =========================================================================== ALS implícito
def _perdida_pares(X: np.ndarray, Y: np.ndarray, obs_u: Sequence[np.ndarray], alfa: float) -> float:
    """Σ_{u,i} c_ui (p_ui − x_u·y_i)² sobre TODOS los pares, sin armar la matriz densa.

    Con s_ui = x_u·y_i: los pares con p = 0 aportan s² (c = 1) y los observados (p = 1, c = 1 + α) aportan (1+α)(1−s)².
    Σ_todos s² = ‖X Yᵀ‖²_F = tr((XᵀX)(YᵀY)); a eso se le suma, solo en los observados, (1+α)(1−s)² − s²."""
    todos = float(((X.T @ X) * (Y.T @ Y)).sum())
    filas = np.concatenate([np.full(len(o), u) for u, o in enumerate(obs_u)]) if len(obs_u) else np.array([], dtype=int)
    cols = np.concatenate(list(obs_u)) if len(obs_u) else np.array([], dtype=int)
    s = np.einsum("nf,nf->n", X[filas], Y[cols])
    return todos + float(((1.0 + alfa) * (1.0 - s) ** 2 - s ** 2).sum())


def perdida_als(X: np.ndarray, Y: np.ndarray, obs_u: Sequence[np.ndarray], alfa: float, regularizacion: float) -> float:
    """L(X, Y) = Σ_{u,i} c_ui (p_ui − x_uᵀ y_i)² + λ (Σ_u ‖x_u‖² + Σ_i ‖y_i‖²), con p_ui = 1 si (u, i) ∈ train y 0 si no,
    c_ui = 1 + α·r_ui (r_ui = 1 en cada interacción: implícita binaria, D1). La suma es sobre TODOS los pares usuario × destino.

    ``obs_u[u]`` = posiciones (columnas de Y) de los destinos con interacción del usuario u (fila u de X)."""
    return _perdida_pares(X, Y, obs_u, alfa) + regularizacion * float((X ** 2).sum() + (Y ** 2).sum())


def actualizar_factores(F: np.ndarray, obs: Sequence[np.ndarray], alfa: float, regularizacion: float) -> np.ndarray:
    """Un medio paso de ALS: con los factores ``F`` (n_otros × f) FIJOS, resuelve en forma cerrada cada fila del otro lado:

        x_u = (Fᵀ C^u F + λI)⁻¹ Fᵀ C^u p(u),   con   Fᵀ C^u F = FᵀF + Fᵀ(C^u − I)F = FᵀF + α Σ_{i∈N(u)} f_i f_iᵀ
                                                   y   Fᵀ C^u p(u) = (1 + α) Σ_{i∈N(u)} f_i.

    (C^u es diagonal con c_ui; p_ui = 1 solo en N(u) = ``obs[u]``.) Así solo se suman los destinos de u y no se arma ninguna
    matriz usuarios × destinos por usuario. La matriz del sistema es simétrica definida positiva si λ > 0. Una fila sin
    observaciones es 0 exacto (su minimizador: con p = 0 en todos los pares y λ > 0, la solución es 0)."""
    f = F.shape[1]
    gram = F.T @ F + regularizacion * np.eye(f)
    out = np.zeros((len(obs), f))
    for r, idx in enumerate(obs):
        if len(idx) == 0:
            continue
        Fu = F[idx]
        out[r] = np.linalg.solve(gram + alfa * (Fu.T @ Fu), (1.0 + alfa) * Fu.sum(axis=0))
    return out


def ajustar_als(obs_u: Sequence[np.ndarray], obs_i: Sequence[np.ndarray], n_u: int, n_i: int, *, factores: int,
                regularizacion: float, alfa: float, iteraciones: int, escala_inicial: float, rng: np.random.Generator):
    """ALS implícito (Hu, Koren y Volinsky, 2008 [VERIFICAR]). Devuelve ``(X, Y, historial_perdida)``.

    Inicialización N(0, escala_inicial²) desde ``rng``; los destinos sin interacciones se inicializan en 0 (su minimizador
    exacto, y así quedan para siempre: y_i = 0). Luego ``iteraciones`` barridos: actualizar X con Y fija y después Y con X
    fija. ``historial_perdida`` guarda L tras la inicialización y tras CADA medio paso (1 + 2·iteraciones valores); como cada
    medio paso es un minimizador exacto, la pérdida no aumenta (salvo error de redondeo)."""
    f = validar_entero(factores, "factores", minimo=1)
    iteraciones = validar_entero(iteraciones, "iteraciones", minimo=1)
    if not regularizacion > 0:
        raise ValueError(f"regularizacion (λ) debe ser > 0 (sistema definido positivo); se recibió {regularizacion}")
    if not alfa >= 0:
        raise ValueError(f"alfa (α) debe ser >= 0; se recibió {alfa}")
    if not escala_inicial > 0:
        raise ValueError(f"escala_inicial debe ser > 0; se recibió {escala_inicial}")
    X = rng.normal(0.0, escala_inicial, size=(n_u, f))
    Y = rng.normal(0.0, escala_inicial, size=(n_i, f))
    for i, o in enumerate(obs_i):
        if len(o) == 0:
            Y[i] = 0.0
    historial = [perdida_als(X, Y, obs_u, alfa, regularizacion)]
    for _ in range(iteraciones):
        X = actualizar_factores(Y, obs_u, alfa, regularizacion)
        historial.append(perdida_als(X, Y, obs_u, alfa, regularizacion))
        Y = actualizar_factores(X, obs_i, alfa, regularizacion)
        historial.append(perdida_als(X, Y, obs_u, alfa, regularizacion))
    return X, Y, historial


def _listas_observadas(filas: np.ndarray, cols: np.ndarray, n_filas: int) -> list[np.ndarray]:
    """Por fila, las columnas observadas (lista de longitud ``n_filas``; vacía si no hay)."""
    orden = np.argsort(filas, kind="stable")
    cortes = np.searchsorted(filas[orden], np.arange(n_filas + 1))
    c = cols[orden]
    return [c[cortes[r]:cortes[r + 1]] for r in range(n_filas)]


def _indices_train(inter: pd.DataFrame, catalogo) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(usuarios con train ordenados, fila de cada interacción de train, columna de su destino en ``catalogo``). Solo train."""
    if "split" not in inter.columns:
        raise ValueError("``inter`` debe traer la columna split (solo se usa train)")
    cat = np.asarray(catalogo, dtype="int64")
    train = inter[inter["split"] == particion.TRAIN]
    usuarios = np.sort(train["usuario_id"].astype("int64").unique())
    filas = np.searchsorted(usuarios, train["usuario_id"].astype("int64").to_numpy())
    cols = pd.Index(cat).get_indexer(train["destino_id"].astype("int64"))
    if (cols < 0).any():
        raise ValueError("hay destino_id de train que no están en el catálogo")
    return usuarios, filas, cols


def _sigma_max(filas: np.ndarray, cols: np.ndarray, n_filas: int, n_cols: int) -> float:
    """Mayor valor singular (norma espectral) de la matriz binaria con unos en (filas, cols). ARPACK (``svds``, k = 1) con
    arranque fijo (determinista); en matrices con una dimensión < 3, SVD densa."""
    if min(n_filas, n_cols) < 3:
        P = np.zeros((n_filas, n_cols))
        P[filas, cols] = 1.0
        return float(np.linalg.norm(P, 2))
    S = csr_matrix((np.ones(len(filas)), (filas, cols)), shape=(n_filas, n_cols))
    return float(svds(S, k=1, v0=np.ones(min(S.shape)), return_singular_vectors=False)[0])


def sigma_max_train(inter: pd.DataFrame, catalogo) -> float:
    """σ_max(P_train): mayor valor singular de la matriz binaria usuarios-con-train × catálogo, calculada SOLO con train.
    Es el σ de la condición exacta de degeneración de ``MFImplicitaALS`` y de la cota de ``hpo.cota_solucion_nula``."""
    usuarios, filas, cols = _indices_train(inter, catalogo)
    return _sigma_max(filas, cols, len(usuarios), len(np.asarray(catalogo)))


class MFImplicitaALS:
    """Factorización de matrices implícita por ALS (D11 b), con numpy.

    Con P ∈ {0,1}^{U×I} (p_ui = 1 si (u, i) ∈ train), confianza c_ui = 1 + α·p_ui y puntaje x_uᵀ y_i, minimiza

        L(X, Y) = Σ_{u,i} c_ui (p_ui − x_uᵀ y_i)² + λ (Σ_u ‖x_u‖² + Σ_i ‖y_i‖²)

    sobre TODOS los pares (ver ``perdida_als`` y ``actualizar_factores`` para las actualizaciones cerradas). Las filas de X
    son los usuarios con al menos una interacción en train (``usuario_ids``); las de Y, los destinos de ``catalogo``.
    Un destino sin ninguna interacción en train queda con y_i = 0 exacto, es decir puntaje 0 para todos los usuarios (la
    pérdida solo lo penaliza por su norma): el modelo no tiene información de él; su posición en el orden depende del signo
    de los demás puntajes del usuario. ``puntuar`` falla para un usuario sin interacciones en train.
    ``n_parametros()`` = (usuarios con train + destinos del catálogo) · f; como las filas de Y de los destinos sin train son 0
    por construcción, ``n_parametros_con_datos()`` = (usuarios con train + destinos con train) · f cuenta solo los que el
    modelo realmente estima a partir de datos. Determinista dada la semilla de inicialización.

    Guarda de degeneración. Con Z = X Yᵀ y σ = σ_max(P_train) (norma espectral de la matriz de train): ⟨P, Z⟩ ≤ σ‖Z‖_* y
    ‖Z‖_* ≤ ½(‖X‖² + ‖Y‖²), de modo que L(X, Y) − L(0, 0) ≥ (λ − (1 + α)σ)(‖X‖² + ‖Y‖²). La condición es EXACTA (si y solo
    si): si λ ≥ (1 + α)σ, X = Y = 0 es el único mínimo global; si λ < (1 + α)σ, el origen es un punto de silla (en la
    dirección t(u₁e₁ᵀ, v₁e₁ᵀ), L − L(0, 0) = 2t²(λ − (1 + α)σ) + O(t⁴) < 0) y existe un mínimo no nulo. Con σ calculada solo
    con train dentro de ``ajustar`` y L(0, 0) = (1 + α)·|train| (pares únicos, D1), la factorización es ``degenerada`` si se
    cumple alguna de:
      1. ``lambda_ge_cota``: λ ≥ (1 + α)σ (el óptimo es nulo; cualquier lista sale del residuo numérico);
      2. ``perdida_no_menor_que_nula``: L_final ≥ L(0, 0) (el ajuste no mejora a la solución nula);
      3. ``puntaje_bajo_tolerancia``: max |x_uᵀ y_i| < ``tolerancia_degenerado`` (puntajes numéricamente nulos).
    ``motivo_degenerado`` es la primera que se cumple (en ese orden) o ``None``; ``condiciones_degenerado`` trae las tres.
    El arnés y la búsqueda rechazan una factorización degenerada."""

    nombre = "mf_als"
    descripcion_frios = ("y_i = 0 exacto → puntaje 0 para todos; su posición depende del signo de los demás puntajes del "
                         "usuario, así que se MIDE cuántas veces entran al top-K (`frios_por_lista`).")

    def __init__(self, factores: int, regularizacion: float, alfa: float, iteraciones: int, escala_inicial: float = 0.01,
                 tolerancia_degenerado: float = 1e-8):
        self.factores = validar_entero(factores, "factores", minimo=1)
        self.iteraciones = validar_entero(iteraciones, "iteraciones", minimo=1)
        if not regularizacion > 0:
            raise ValueError(f"regularizacion (λ) debe ser > 0; se recibió {regularizacion}")
        if not alfa >= 0:
            raise ValueError(f"alfa (α) debe ser >= 0; se recibió {alfa}")
        if not escala_inicial > 0:
            raise ValueError(f"escala_inicial debe ser > 0; se recibió {escala_inicial}")
        if not tolerancia_degenerado > 0:
            raise ValueError(f"tolerancia_degenerado debe ser > 0; se recibió {tolerancia_degenerado}")
        self.regularizacion, self.alfa, self.escala_inicial = float(regularizacion), float(alfa), float(escala_inicial)
        self.tolerancia_degenerado = float(tolerancia_degenerado)
        self.degenerado: bool | None = None
        self.motivo_degenerado: str | None = None
        self.condiciones_degenerado: dict | None = None
        self.sigma_max_train: float | None = None
        self.perdida_nula: float | None = None
        self.max_abs_puntaje: float | None = None
        self._n_destinos_con_train = 0
        self.hiperparametros = {"factores": self.factores, "regularizacion": self.regularizacion, "alfa": self.alfa,
                                "iteraciones": self.iteraciones, "escala_inicial": self.escala_inicial}
        self.X = self.Y = self.usuario_ids = self.destino_ids = None
        self.historial_perdida: list[float] = []

    def ajustar(self, inter, catalogo, rng) -> MFImplicitaALS:
        if "split" not in inter.columns:
            raise ValueError("MFImplicitaALS.ajustar: ``inter`` debe traer la columna split (el modelo usa solo train)")
        cat = np.asarray(catalogo, dtype="int64")
        usuarios, filas, cols = _indices_train(inter, cat)                     # D9: solo train
        obs_u = _listas_observadas(filas, cols, len(usuarios))
        obs_i = _listas_observadas(cols, filas, len(cat))
        self.X, self.Y, self.historial_perdida = ajustar_als(
            obs_u, obs_i, len(usuarios), len(cat), factores=self.factores, regularizacion=self.regularizacion,
            alfa=self.alfa, iteraciones=self.iteraciones, escala_inicial=self.escala_inicial, rng=rng)
        self.usuario_ids, self.destino_ids = usuarios, cat
        self._n_destinos_con_train = int(sum(len(o) > 0 for o in obs_i))
        self.max_abs_puntaje = float(np.abs(self.X @ self.Y.T).max())
        self.sigma_max_train = _sigma_max(filas, cols, len(usuarios), len(cat))
        self.perdida_nula = (1.0 + self.alfa) * len(filas)                      # L(0, 0): pares (u, i) de train únicos
        self.condiciones_degenerado = {
            "lambda_ge_cota": bool(self.regularizacion >= (1.0 + self.alfa) * self.sigma_max_train),
            "perdida_no_menor_que_nula": bool(self.historial_perdida[-1] >= self.perdida_nula),
            "puntaje_bajo_tolerancia": bool(self.max_abs_puntaje < self.tolerancia_degenerado)}
        self.motivo_degenerado = next((k for k, v in self.condiciones_degenerado.items() if v), None)
        self.degenerado = self.motivo_degenerado is not None
        return self

    def puntuar(self, usuario_ids) -> np.ndarray:
        if self.X is None:
            raise _no_ajustado(self.nombre)
        u = np.asarray(usuario_ids, dtype="int64")
        pos = np.minimum(np.searchsorted(self.usuario_ids, u), len(self.usuario_ids) - 1)
        faltan = u[self.usuario_ids[pos] != u]
        if len(faltan):
            raise ValueError(f"{self.nombre}: usuarios sin interacciones en train (sin factor): {faltan[:10].tolist()}")
        return self.X[pos] @ self.Y.T

    def n_parametros(self) -> int:
        if self.X is None:
            raise _no_ajustado(self.nombre)
        return int((self.X.shape[0] + self.Y.shape[0]) * self.factores)

    def n_parametros_con_datos(self) -> int:
        """(usuarios con train + destinos con train) · f: excluye las filas de Y que son 0 por construcción."""
        if self.X is None:
            raise _no_ajustado(self.nombre)
        return int((self.X.shape[0] + self._n_destinos_con_train) * self.factores)

    def diagnosticos(self) -> dict:
        """Guarda de degeneración (ver el docstring de la clase) y parámetros con datos, del último ``ajustar``."""
        if self.X is None:
            raise _no_ajustado(self.nombre)
        return {"degenerado": self.degenerado, "motivo_degenerado": self.motivo_degenerado,
                "condiciones_degenerado": dict(self.condiciones_degenerado), "max_abs_puntaje": self.max_abs_puntaje,
                "sigma_max_train": self.sigma_max_train, "n_parametros_con_datos": self.n_parametros_con_datos()}

    def guardar(self, carpeta, semilla: int, evidencia: dict) -> list[Path]:
        """Escribe ``mf_als.npz`` (X, Y, usuario_ids, destino_ids) y ``mf_als.json`` (hiperparámetros, semilla, historial de la
        pérdida y evidencia) en ``carpeta``; devuelve las rutas."""
        if self.X is None:
            raise _no_ajustado(self.nombre)
        carpeta = Path(carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta_npz = carpeta / f"{self.nombre}.npz"
        np.savez_compressed(ruta_npz, X=self.X, Y=self.Y, usuario_ids=self.usuario_ids, destino_ids=self.destino_ids)
        ruta_json = save_json(carpeta / f"{self.nombre}.json", {
            "modelo": self.nombre, "semilla": semilla, "hiperparametros": self.hiperparametros,
            "forma_X": list(self.X.shape), "forma_Y": list(self.Y.shape),
            "nota": (f"{self.nombre}.npz: X (usuarios con train × f), Y (destinos del catálogo × f), usuario_ids y "
                     "destino_ids en el orden de las filas."),
            "historial_perdida": self.historial_perdida, "evidencia": evidencia})
        return [ruta_npz, ruta_json]


# =========================================================================== registro de modelos
def _fabrica_mf(cfg: dict) -> MFImplicitaALS:
    hp = cfg["mf_als"]["hiperparametros"]
    return MFImplicitaALS(factores=hp["factores"], regularizacion=hp["regularizacion"], alfa=hp["alfa"],
                          iteraciones=hp["iteraciones"], escala_inicial=cfg["mf_als"]["escala_inicial"],
                          tolerancia_degenerado=cfg["mf_als"]["tolerancia_degenerado"])


def _fabrica_red(cfg: dict) -> Recomendador:
    """JJ-5: la red de dos torres (``red.fabrica_red``). Import tardío: así las referencias no cargan torch."""
    from src.m3_recomendacion.red import fabrica_red

    return fabrica_red(cfg)


# nombre → fábrica(cfg). El arnés recorre ``cfg["modelos"]``.
MODELOS: dict[str, Callable[[dict], Recomendador]] = {
    "popularidad": lambda cfg: Popularidad(),
    "mf_als": _fabrica_mf,
    "aleatorio": lambda cfg: Aleatorio(),
    "red": _fabrica_red,
}
