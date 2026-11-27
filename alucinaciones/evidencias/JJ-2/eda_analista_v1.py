"""M3 — análisis descriptivo (JJ-2): secciones 3–7 de la plantilla común (núcleo §5.12). Sin red; solo lee ``data/processed/m3/``.

Entrada: ``destinos.parquet``, ``usuarios.parquet`` e ``interacciones.parquet`` de ``m3-datos`` (núcleo §5.7).
Salida (``results/data/m3/eda/``; no se tocan ``ficha.json``, ``calidad.csv`` ni ``diccionario.json``):
  interacciones_por_{usuario,destino,lugar}.csv   conteo por entidad (incluidas las de 0)
  distribucion_actividad.json                     histograma de usuarios y de destinos vs. reparto uniforme al azar
  calificaciones.csv                              distribución 1–5 por origen, media y desviación
  concentracion.json                              Gini, HHI, cuota top, Lorenz (observado y azar) por nivel
  actividad_usuarios.json                         grupos «pocas» / «muchas», cuenta de la partición D3 y sensibilidad
  coincidencia_preferencias.json, matriz_preferencias_tipo.csv, demografia_tipo.csv
  pruebas_hipotesis.json                          pruebas confirmatorias (ajuste de Holm) y complementarias
  hipotesis.json                                  contrato de §5.12

Definiciones (las fijan las pruebas de ``tests/test_eda_m3.py``):
  Gini            2·Σ i·x_(i) / (n·Σx) − (n+1)/n  (x ascendente, i = 1…n); máximo (n−1)/n; «corregido» = Gini·n/(n−1)
  HHI             Σ s_i² con cuotas s_i en [0, 1]; normalizado (HHI − 1/n)/(1 − 1/n)
  cuota top f     suma de los ceil(f·n) mayores sobre el total
  p permutación   (1 + #{T* >= T_obs}) / (1 + B)
  Holm            p_(j) ajustado = max_{i<=j} min(1, (m − i + 1)·p_(i))

Toda aleatoriedad sale de ``make_rng(base_seed, run_id)`` con un ``run_id`` propio por uso (ver ``configs/m3/eda.yaml``).
Los datos son generados (D4): ningún resultado se atribuye a comportamiento real de turistas.
"""

from __future__ import annotations

import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from src.comun.eda import escribir_hipotesis
from src.comun.results import load_json, save_json
from src.comun.seeds import make_rng
from src.m3_recomendacion.datos import chi2_y_v, separar_opciones, usuarios_por_numero

ORIGENES = ("resena", "historial")
TOLERANCIA = 1e-12
COLUMNAS = {
    "destinos": ["destino_id", "lugar", "tipo", "popularidad"],
    "usuarios": ["usuario_id", "preferencias", "genero", "n_adultos", "n_ninos"],
    "interacciones": ["usuario_id", "destino_id", "origen", "calificacion"],
}
VARIABLES_DEMOGRAFICAS = (("genero", "H4_genero", "genero", "genero"),
                          ("n_adultos", "H4_n_adultos", "n_adultos", "numero de adultos"),
                          ("n_ninos", "H4_n_ninos", "n_ninos", "numero de ninos"))


# =========================================================================== medidas de concentración
def _positivo(x) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    if (a.sum(axis=-1) <= 0).any():
        raise ValueError("la suma de los conteos debe ser positiva para medir la concentración")
    return a


def gini(x):
    """Gini sin corrección: 2·Σ i·x_(i) / (n·Σx) − (n+1)/n (en [0, (n−1)/n]). Acepta una fila o una matriz (por filas)."""
    a = np.sort(_positivo(x), axis=-1)
    n = a.shape[-1]
    return 2.0 * (a * np.arange(1, n + 1)).sum(axis=-1) / (n * a.sum(axis=-1)) - (n + 1) / n


def gini_corregido(x):
    """Gini·n/(n−1), en [0, 1]."""
    n = np.asarray(x).shape[-1]
    if n < 2:
        raise ValueError("el Gini corregido necesita al menos 2 entidades")
    return gini(x) * n / (n - 1)


def hhi(x):
    """Σ s_i² con las cuotas s_i = x_i/Σx en [0, 1] (mínimo 1/n, máximo 1)."""
    a = _positivo(x)
    return ((a / a.sum(axis=-1, keepdims=True)) ** 2).sum(axis=-1)


def hhi_normalizado(x):
    """(HHI − 1/n)/(1 − 1/n), en [0, 1]."""
    n = np.asarray(x).shape[-1]
    if n < 2:
        raise ValueError("el HHI normalizado necesita al menos 2 entidades")
    return (hhi(x) - 1.0 / n) / (1.0 - 1.0 / n)


def n_top(n: int, fraccion: float) -> int:
    """k = ceil(fracción·n), al menos 1 y a lo sumo n (el redondeo a 9 decimales evita 100,00000000000001 → 101)."""
    return int(min(n, max(1, math.ceil(round(fraccion * n, 9)))))


def cuota_top(x, fraccion: float):
    """Cuota de las interacciones que acumulan las ceil(fracción·n) entidades con más interacciones."""
    a = _positivo(x)
    k = n_top(a.shape[-1], fraccion)
    mayores = np.sort(a, axis=-1)[..., ::-1][..., :k]
    return mayores.sum(axis=-1) / a.sum(axis=-1)


def lorenz(x):
    """Vértices de la curva de Lorenz (x_j = j/n, y_j = suma de los j menores / total), j = 0…n; ``x`` por filas admite matriz."""
    a = np.sort(_positivo(x), axis=-1)
    n = a.shape[-1]
    ys = np.concatenate([np.zeros(a.shape[:-1] + (1,)), np.cumsum(a, axis=-1) / a.sum(axis=-1, keepdims=True)], axis=-1)
    return np.arange(n + 1) / n, ys


# =========================================================================== estadística auxiliar
def holm(p) -> list[float]:
    """Ajuste de Holm (escalonado descendente, monótono) de la familia ``p``; devuelve p ajustados en el orden original."""
    p = np.asarray(p, dtype=float)
    m = len(p)
    ajustado = np.empty(m)
    previo = 0.0
    for rango, i in enumerate(np.argsort(p, kind="stable")):
        previo = max(previo, min(1.0, (m - rango) * p[i]))
        ajustado[i] = previo
    return ajustado.tolist()


def p_permutacion(obs: float, nulos, alternativa: str = "mayor") -> float:
    """(1 + #{T* >= T_obs}) / (1 + B); ``dos_colas`` compara |T*| con |T_obs|. Tolerancia de 1e-12 para empates numéricos."""
    nulos = np.asarray(nulos, dtype=float)
    tol = TOLERANCIA * max(1.0, abs(obs))
    if alternativa == "mayor":
        k = int((nulos >= obs - tol).sum())
    elif alternativa == "dos_colas":
        k = int((np.abs(nulos) >= abs(obs) - tol).sum())
    else:
        raise ValueError(f"alternativa desconocida: {alternativa!r}")
    return (1 + k) / (1 + len(nulos))


def delta_de_cliff(a, b):
    """Delta de Cliff y probabilidad de superioridad de ``a`` sobre ``b`` desde los conteos por categoría ordenada.

    delta = (#{a > b} − #{a < b}) / (n_a·n_b); prob. de superioridad = (#{a > b} + ½·#{a = b}) / (n_a·n_b) = (delta + 1)/2.
    Acepta vectores o matrices (por filas)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    por_debajo = np.cumsum(b, axis=-1) - b            # Σ_{k<j} b_k
    por_encima = b.sum(axis=-1, keepdims=True) - np.cumsum(b, axis=-1)   # Σ_{k>j} b_k
    victorias = (a * por_debajo).sum(axis=-1)
    derrotas = (a * por_encima).sum(axis=-1)
    empates = (a * b).sum(axis=-1)
    total = a.sum(axis=-1) * b.sum(axis=-1)
    return (victorias - derrotas) / total, (victorias + 0.5 * empates) / total


def _rho_por_filas(rx, ry):
    """Correlación de Pearson por filas entre rangos ``rx`` (n o b×n) y ``ry`` (n o b×n)."""
    x = rx - rx.mean(axis=-1, keepdims=True)
    y = ry - ry.mean(axis=-1, keepdims=True)
    return (x * y).sum(axis=-1) / np.sqrt((x ** 2).sum(axis=-1) * (y ** 2).sum(axis=-1))


def rho_de_spearman(x, y) -> float:
    """Correlación de Spearman = Pearson de los rangos medios (los empates reciben su rango medio)."""
    return float(_rho_por_filas(stats.rankdata(x), stats.rankdata(y)))


def histograma_de_actividad(conteos, tope: int) -> dict[str, int]:
    """Entidades con 0, 1, …, tope−1 y «tope+» interacciones (mismas claves que ``ficha.json``)."""
    c = np.asarray(conteos)
    salida = {str(k): int((c == k).sum()) for k in range(tope)}
    salida[f"{tope}+"] = int((c >= tope).sum())
    return salida


def _histogramas_por_filas(conteos: np.ndarray, tope: int) -> np.ndarray:
    """Histograma (tope+1 columnas) de cada fila de una matriz de conteos."""
    cols = [(conteos == k).sum(axis=1) for k in range(tope)] + [(conteos >= tope).sum(axis=1)]
    return np.stack(cols, axis=1)


def simular_uniforme(rng: np.random.Generator, n_interacciones: int, n_entidades: int, n_sim: int) -> np.ndarray:
    """``n_sim`` repartos de ``n_interacciones`` entre ``n_entidades`` con probabilidad uniforme (multinomial): (n_sim, n_entidades)."""
    return rng.multinomial(n_interacciones, np.full(n_entidades, 1.0 / n_entidades), size=n_sim)


def _cuantiles(x, nivel: float, axis: int = 0):
    alfa = (1.0 - nivel) / 2.0
    return np.quantile(x, [alfa, 1.0 - alfa], axis=axis)


def chi2_por_lotes(tablas: np.ndarray) -> np.ndarray:
    """χ² de independencia de cada tabla (lote × filas × columnas); las celdas con esperado 0 no aportan."""
    t = np.asarray(tablas, dtype=float)
    n = t.sum(axis=(1, 2))
    esperado = t.sum(axis=2)[:, :, None] * t.sum(axis=1)[:, None, :] / n[:, None, None]
    with np.errstate(divide="ignore", invalid="ignore"):
        termino = np.where(esperado > 0, (t - esperado) ** 2 / esperado, 0.0)
    return termino.sum(axis=(1, 2))


def v_de_cramer_por_lotes(tablas: np.ndarray) -> np.ndarray:
    """V de Cramér = sqrt(χ² / (n·(min(filas, columnas) − 1))) de cada tabla del lote."""
    t = np.asarray(tablas, dtype=float)
    n = t.sum(axis=(1, 2))
    return np.sqrt(chi2_por_lotes(t) / (n * (min(t.shape[1:]) - 1)))


def veredicto_de_prueba(p_ajustado: float, efecto: float, ic: tuple[float, float], minimo: float, alfa: float,
                        alternativa: str) -> str:
    """«cumple» / «refuta» / «indeterminada» según el criterio de ``configs/m3/eda.yaml``.

    cumple: p ajustado < alfa y efecto >= mínimo (``mayor``) o |efecto| >= mínimo (``dos_colas``).
    refuta: p ajustado >= alfa y el IC 95 % queda dentro de (−mínimo, +mínimo) (``dos_colas``) o por debajo de +mínimo
    (``mayor``): efecto compatible con cero y lo bastante estrecho para excluir un efecto de la magnitud mínima.
    Un efecto detectable pero menor que el mínimo no cumple (queda «indeterminada»)."""
    lo, hi = ic
    grande = efecto >= minimo if alternativa == "mayor" else abs(efecto) >= minimo
    if p_ajustado < alfa and grande:
        return "cumple"
    estrecho = hi < minimo if alternativa == "mayor" else (lo > -minimo and hi < minimo)
    if p_ajustado >= alfa and estrecho:
        return "refuta"
    return "indeterminada"


def veredicto_de_hipotesis(resultados: list[str]) -> str:
    """confirmada si alguna prueba cumple; refutada si todas refutan; en otro caso, no concluyente."""
    if any(r == "cumple" for r in resultados):
        return "confirmada"
    if resultados and all(r == "refuta" for r in resultados):
        return "refutada"
    return "no concluyente"


# =========================================================================== preferencias y tipo
def tipos_de_preferencias(texto: str, emparejamiento: dict) -> frozenset:
    """Tipos de destino que cubre una combinación de preferencias («Beaches, Historical» → {Beach, Historical})."""
    tipos = set()
    for opcion in separar_opciones(texto):
        if opcion not in emparejamiento:
            raise ValueError(f"la opción de preferencia {opcion!r} no está en emparejamiento_preferencia_tipo de la config")
        tipos.add(emparejamiento[opcion])
    return frozenset(tipos)


def coincidencia(catalogo_tipos, usuarios, tipos, preferidos_por_usuario: dict, marginal: pd.Series | None = None) -> dict:
    """Tasa de coincidencia preferencia–tipo y sus dos líneas base.

    ``usuarios`` y ``tipos``: usuario y tipo del destino de cada interacción. Coincide si el tipo está entre los que cubren
    sus preferencias. Línea base EXACTA: por interacción, la fracción de ids del catálogo cuyo tipo está en las preferencias
    del usuario (destino uniforme en el catálogo), promediada sobre las interacciones. Línea base MARGINAL: igual, pero con
    la distribución de tipos de las interacciones (o ``marginal``, si se pasa) en lugar de la del catálogo."""
    cat = pd.Series(list(catalogo_tipos)).value_counts()
    fraccion = {u: float(sum(cat.get(t, 0) for t in p)) / float(cat.sum()) for u, p in preferidos_por_usuario.items()}
    q = pd.Series(list(tipos)).value_counts(normalize=True) if marginal is None else marginal
    coinciden = [t in preferidos_por_usuario[u] for u, t in zip(usuarios, tipos)]
    n = len(coinciden)
    tasa = float(np.mean(coinciden))
    exacta = float(np.mean([fraccion[u] for u in usuarios]))
    marg = float(np.mean([sum(q.get(t, 0.0) for t in preferidos_por_usuario[u]) for u in usuarios]))
    return {"n": n, "n_coinciden": int(sum(coinciden)), "tasa": tasa, "linea_base_exacta": exacta,
            "linea_base_marginal": marg, "diferencia_exacta": tasa - exacta, "diferencia_marginal": tasa - marg}


# =========================================================================== lectura y preparación
def _leer(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ent = cfg["entrada"]
    carpeta = Path(ent["carpeta"])
    tablas = {}
    for rol in ("destinos", "usuarios", "interacciones"):
        ruta = carpeta / ent[rol]
        if not ruta.is_file():
            raise FileNotFoundError(f"falta {ruta}: corre primero `python run.py m3-datos --config configs/m3/datos.yaml`")
        df = pd.read_parquet(ruta)
        faltan = [c for c in COLUMNAS[rol] if c not in df.columns]
        if faltan:
            raise ValueError(f"{ruta}: faltan las columnas {faltan}")
        tablas[rol] = df
    return tablas["destinos"], tablas["usuarios"], tablas["interacciones"]


def _validar(destinos: pd.DataFrame, usuarios: pd.DataFrame, inter: pd.DataFrame) -> None:
    if destinos["destino_id"].duplicated().any() or usuarios["usuario_id"].duplicated().any():
        raise ValueError("destino_id y usuario_id deben ser únicos")
    if inter.duplicated(["usuario_id", "destino_id"]).any():
        raise ValueError("hay pares (usuario, destino) repetidos en interacciones")
    if not inter["usuario_id"].isin(usuarios["usuario_id"]).all() or not inter["destino_id"].isin(destinos["destino_id"]).all():
        raise ValueError("hay interacciones con un usuario o destino que no está en los maestros")
    if not set(inter["origen"]) <= set(ORIGENES):
        raise ValueError(f"origen inesperado en interacciones: {sorted(set(inter['origen']) - set(ORIGENES))}")
    if not len(inter):
        raise ValueError("no hay interacciones")


class Datos:
    """Vistas numéricas de los parquet (todo derivado de ellos; sin aleatoriedad)."""

    def __init__(self, cfg: dict, destinos: pd.DataFrame, usuarios: pd.DataFrame, inter: pd.DataFrame):
        self.cfg, self.destinos, self.usuarios, self.inter = cfg, destinos, usuarios, inter
        emp = cfg["emparejamiento_preferencia_tipo"]
        self.tipos = sorted(destinos["tipo"].unique())
        sin_destinos = sorted(set(emp.values()) - set(self.tipos))
        if sin_destinos:
            raise ValueError(f"el emparejamiento menciona tipos que no existen en destinos: {sin_destinos}")
        usuarios = usuarios.copy()
        usuarios["combinacion"] = usuarios["preferencias"].map(lambda t: ", ".join(separar_opciones(t)))
        self.usuarios = usuarios
        self.combos = sorted(usuarios["combinacion"].unique())
        self.tipos_de_combo = {c: tipos_de_preferencias(c, emp) for c in self.combos}
        self.indicador = np.array([[t in self.tipos_de_combo[c] for t in self.tipos] for c in self.combos], dtype=np.int64)
        self.n_inter = len(inter)
        # por interacción
        m = inter.merge(usuarios[["usuario_id", "combinacion"]], on="usuario_id").merge(
            destinos[["destino_id", "lugar", "tipo"]], on="destino_id")
        self.m = m.sort_values(["usuario_id", "destino_id"]).reset_index(drop=True)
        self.escala = list(range(int(self.m["calificacion"].min()), int(self.m["calificacion"].max()) + 1))
        # por usuario que aparece (ordenados por id)
        self.ids_u = np.sort(self.m["usuario_id"].unique())
        self.n_u = len(self.ids_u)
        self.ui = np.searchsorted(self.ids_u, self.m["usuario_id"].to_numpy())
        self.ti = np.searchsorted(self.tipos, self.m["tipo"].to_numpy())
        self.ki = (self.m["calificacion"].to_numpy() - self.escala[0]).astype(int)
        self.oi = (self.m["origen"] != ORIGENES[0]).to_numpy().astype(int)
        u = usuarios.set_index("usuario_id").loc[self.ids_u]
        self.combo_u = np.searchsorted(self.combos, u["combinacion"].to_numpy())
        self.preferidos = {int(i): self.tipos_de_combo[c] for i, c in zip(usuarios["usuario_id"], usuarios["combinacion"])}
        self.usuarios_aparecen = u
        n_u, n_t, n_k = self.n_u, len(self.tipos), len(self.escala)
        self.C = np.zeros((n_u, n_t), dtype=np.int64)                         # interacciones del usuario por tipo
        np.add.at(self.C, (self.ui, self.ti), 1)
        self.Rt = np.zeros((n_u, n_t), dtype=np.int64)                        # suma de calificaciones del usuario por tipo
        np.add.at(self.Rt, (self.ui, self.ti), self.m["calificacion"].to_numpy())
        self.S = self.C @ self.indicador.T                                    # coincidencias si el usuario tuviera la combinación g
        self.R = self.Rt @ self.indicador.T                                   # suma de calificaciones de las coincidencias
        self.n_por_u = self.C.sum(axis=1)
        idx = np.arange(n_u)
        self.m_u = self.S[idx, self.combo_u]
        self.coincide = np.array([self.tipos[t] in self.preferidos[int(uid)] for t, uid in zip(self.ti, self.m["usuario_id"])])
        self.Um = np.zeros((n_u, n_k), dtype=np.int64)                        # calificaciones de las coincidencias, por usuario
        self.Un = np.zeros((n_u, n_k), dtype=np.int64)
        np.add.at(self.Um, (self.ui[self.coincide], self.ki[self.coincide]), 1)
        np.add.at(self.Un, (self.ui[~self.coincide], self.ki[~self.coincide]), 1)
        self.Co = np.zeros((n_u, 2, n_t), dtype=np.int64)                     # origen × tipo por usuario
        np.add.at(self.Co, (self.ui, self.oi, self.ti), 1)
        self.Cr = np.zeros((n_u, 2, n_k), dtype=np.int64)                     # origen × calificación por usuario
        np.add.at(self.Cr, (self.ui, self.oi, self.ki), 1)
        # líneas base por usuario (suma sobre sus interacciones)
        cat = destinos["tipo"].value_counts()
        self.frac_combo = np.array([sum(cat.get(t, 0) for t in self.tipos_de_combo[c]) / len(destinos) for c in self.combos])
        self.b_u = self.n_por_u * self.frac_combo[self.combo_u]
        q = pd.Series(self.m["tipo"]).value_counts(normalize=True)
        self.q_marg = q
        self.marg_combo = np.array([sum(q.get(t, 0.0) for t in self.tipos_de_combo[c]) for c in self.combos])
        self.b2_u = self.n_por_u * self.marg_combo[self.combo_u]
        # conteos por entidad (incluidas las de 0)
        self.n_por_usuario = self.m.groupby("usuario_id").size().reindex(usuarios["usuario_id"], fill_value=0).to_numpy()
        self.n_por_destino = self.m.groupby("destino_id").size().reindex(destinos["destino_id"], fill_value=0).to_numpy()
        self.lugares = sorted(destinos["lugar"].unique())
        self.lugar_de_destino = np.searchsorted(self.lugares, destinos["lugar"].to_numpy())
        self.n_por_lugar = np.bincount(self.lugar_de_destino, weights=self.n_por_destino, minlength=len(self.lugares))


# =========================================================================== remuestreos
def permutaciones(rng: np.random.Generator, etiquetas: np.ndarray, n: int, bloque: int = 2500):
    """Bloques (b, U) de permutaciones de ``etiquetas`` (cada fila es una permutación independiente)."""
    base = np.asarray(etiquetas)
    hecho = 0
    while hecho < n:
        b = min(bloque, n - hecho)
        yield rng.permuted(np.tile(base, (b, 1)), axis=1)
        hecho += b


def multiplicidades(rng: np.random.Generator, n_unidades: int, n_boot: int) -> np.ndarray:
    """Remuestreo con reposición de unidades: matriz (n_boot, n_unidades) con las veces que sale cada una."""
    idx = rng.integers(0, n_unidades, size=(n_boot, n_unidades))
    w = np.zeros((n_boot, n_unidades), dtype=np.int64)
    for b in range(n_boot):
        w[b] = np.bincount(idx[b], minlength=n_unidades)
    return w


def _tablas_de_grupos(pesos: np.ndarray, C: np.ndarray, grupos: np.ndarray, n_grupos: int) -> np.ndarray:
    """Tablas (lote, grupos, columnas): suma ponderada de C por grupo de usuarios (``grupos`` fijo; ``pesos`` por lote)."""
    return np.stack([pesos[:, grupos == g] @ C[grupos == g] for g in range(n_grupos)], axis=1)


def _tablas_permutadas(P: np.ndarray, C32: np.ndarray, n_grupos: int) -> np.ndarray:
    """Tablas (lote, grupos, columnas) cuando las etiquetas de grupo de los usuarios son las permutadas ``P``."""
    return np.stack([(P == g).astype(np.float32) @ C32 for g in range(n_grupos)], axis=1).astype(float)


def _ic(x: np.ndarray, nivel: float) -> list[float]:
    lo, hi = _cuantiles(x, nivel)
    return [float(lo), float(hi)]


# =========================================================================== análisis
def analizar_actividad(d: Datos, cfg: dict) -> tuple[dict, dict]:
    """Histogramas observados y de la referencia uniforme (usuarios y destinos); devuelve (json, simulación de destinos)."""
    nivel, n_sim = cfg["nivel_ic"], cfg["n_simulaciones_azar"]
    out = {"n_interacciones": d.n_inter, "n_simulaciones": n_sim, "nivel_ic": nivel,
           "referencia": ("reparto uniforme al azar de las interacciones entre las entidades maestras "
                          "(multinomial con probabilidad 1/n; cada interacción elige una entidad al azar, sin respetar los "
                          "pares únicos); media e IC por percentiles sobre las simulaciones")}
    sim_dest = None
    for nombre, conteos, tope, run in (("usuarios", d.n_por_usuario, cfg["tope_usuarios"], "simulacion_usuarios"),
                                       ("destinos", d.n_por_destino, cfg["tope_destinos"], "simulacion_destinos")):
        rng = make_rng(cfg["base_seed"], cfg["run_id"][run])
        sim = simular_uniforme(rng, d.n_inter, len(conteos), n_sim)
        if nombre == "destinos":
            sim_dest = sim
        h = _histogramas_por_filas(sim, tope)
        claves = list(histograma_de_actividad(conteos, tope))
        lo, hi = _cuantiles(h, nivel)
        out[nombre] = {"n_entidades": int(len(conteos)), "tope": tope,
                       "observado": histograma_de_actividad(conteos, tope),
                       "azar_media": {k: float(v) for k, v in zip(claves, h.mean(axis=0))},
                       "azar_ic95": {k: [float(a), float(b)] for k, a, b in zip(claves, lo, hi)},
                       "max_interacciones_observado": int(np.max(conteos)),
                       "max_interacciones_azar_media": float(sim.max(axis=1).mean())}
    return out, sim_dest


def verificar_contra_ficha(d: Datos, cfg: dict, observado: dict, carpeta_salida: Path) -> bool:
    """Si ``ficha.json`` existe y usa el mismo tope, el histograma de usuarios debe ser igual al de la ficha."""
    ruta = carpeta_salida / "ficha.json"
    if not ruta.is_file():
        return False
    ficha = load_json(ruta)
    union = ficha.get("conteos", {}).get("usuarios_por_numero_de_interacciones", {}).get("union")
    if not isinstance(union, dict) or list(union) != list(observado):
        return False
    if union != observado:
        raise ValueError(f"el histograma de usuarios por interacciones no coincide con {ruta.as_posix()}: "
                         f"ficha.json {union} frente a lo calculado aquí {observado}; corre `m3-datos` y `m3-eda` otra vez")
    return True


def analizar_concentracion(d: Datos, cfg: dict, sim_dest: np.ndarray) -> dict:
    """Gini, HHI, cuota top y Lorenz por nivel, observados y bajo reparto uniforme (media, IC y p del observado)."""
    nivel, fracs = cfg["nivel_ic"], cfg["fracciones_top"]
    sims = {"destino_id": sim_dest.astype(float),
            "lugar": np.stack([np.bincount(d.lugar_de_destino, weights=f, minlength=len(d.lugares)) for f in sim_dest])}
    obs_conteos = {"destino_id": d.n_por_destino.astype(float), "lugar": d.n_por_lugar.astype(float)}
    out = {"definiciones": {"gini": "2·Σ i·x_(i)/(n·Σx) − (n+1)/n, sin corrección (máximo (n−1)/n)",
                            "gini_corregido": "gini·n/(n−1), en [0, 1]",
                            "hhi": "Σ s_i² con cuotas en [0, 1]", "hhi_normalizado": "(HHI − 1/n)/(1 − 1/n)",
                            "cuota_top": "suma de las ceil(f·n) entidades con más interacciones sobre el total",
                            "lorenz": "vértices (j/n, suma de las j entidades con menos interacciones / total)",
                            "p_observado_mayor_o_igual": "(1 + #{simulaciones >= observado}) / (1 + simulaciones)"},
           "niveles": {}}

    def resumen(obs: float, sim: np.ndarray) -> dict:
        return {"observado": float(obs), "media": float(sim.mean()), "ic95": _ic(sim, nivel),
                "p_observado_mayor_o_igual": float((1 + (sim >= obs - TOLERANCIA).sum()) / (1 + len(sim))),
                "percentil_observado": float((sim <= obs + TOLERANCIA).mean())}

    for nombre in cfg["niveles"]:
        x, s = obs_conteos[nombre], sims[nombre]
        n = len(x)
        xs, ys = lorenz(x)
        _, ys_sim = lorenz(s)
        lo, hi = _cuantiles(ys_sim, nivel)
        medidas = {"gini": (gini, ()), "gini_corregido": (gini_corregido, ()), "hhi": (hhi, ()),
                   "hhi_normalizado": (hhi_normalizado, ())}
        azar = {"n_simulaciones": int(len(s))}
        for clave, (f, _) in medidas.items():
            azar[clave] = resumen(f(x), f(s))
        azar["cuota_top"] = {f"{f:g}": resumen(cuota_top(x, f), cuota_top(s, f)) for f in fracs}
        azar["lorenz"] = {"media": np.round(ys_sim.mean(axis=0), 6).tolist(), "ic95_inf": np.round(lo, 6).tolist(),
                          "ic95_sup": np.round(hi, 6).tolist()}
        out["niveles"][nombre] = {
            "n_entidades": n, "n_interacciones": int(x.sum()),
            "observado": {"gini": float(gini(x)), "gini_corregido": float(gini_corregido(x)), "hhi": float(hhi(x)),
                          "hhi_normalizado": float(hhi_normalizado(x)),
                          "cuota_top": {f"{f:g}": float(cuota_top(x, f)) for f in fracs},
                          "n_entidades_en_el_top": {f"{f:g}": n_top(n, f) for f in fracs},
                          "entidades_con_cero": int((x == 0).sum()),
                          "lorenz": {"x": np.round(xs, 6).tolist(), "y": np.round(ys, 6).tolist()}},
            "azar_uniforme": azar}
    return out


def analizar_actividad_usuarios(d: Datos, cfg: dict) -> dict:
    """Grupos «pocas» / «muchas», cuenta de la partición D3 (sin hacerla) y sensibilidad al umbral."""
    n = d.n_por_usuario
    p_max = cfg["actividad"]["pocas_max"]
    aparecen = int((n >= 1).sum())

    def d3(ns: np.ndarray) -> dict:
        prueba, valid = (ns >= 2).astype(int), (ns >= 3).astype(int)
        entren = np.where(ns >= 1, ns - prueba - valid, 0)
        return {"usuarios_con_prueba": int(prueba.sum()), "usuarios_con_validacion": int(valid.sum()),
                "usuarios_solo_entrenamiento": int(((ns >= 1) & (prueba == 0)).sum()),
                "interacciones": {"entrenamiento": int(entren.sum()), "validacion": int(valid.sum()),
                                  "prueba": int(prueba.sum())},
                "entrenamiento_por_usuario": {"min": int(entren.min()) if len(ns) else None,
                                              "media": float(entren.mean()) if len(ns) else None,
                                              "max": int(entren.max()) if len(ns) else None}}

    grupos = {"sin_interacciones": n == 0, "pocas": (n >= 1) & (n <= p_max), "muchas": n > p_max}
    out = {"umbral": {"pocas_max": p_max, "regla": f"pocas = 1 a {p_max} interacciones; muchas = {p_max + 1} o más; "
                                                    "sin_interacciones = 0 (no evaluable)",
                      "justificacion": ("Con la partición D3 (prueba = 1 interacción de cada usuario con >= 2; validación = 1 más "
                                        "con >= 3; el resto, entrenamiento) los usuarios con 1 o 2 interacciones aportan a lo sumo "
                                        "una interacción de prueba y ninguna de validación; los de 3 o más aportan además "
                                        "validación. Umbral PROPUESTO por esta tarea: Juan José debe confirmarlo. Los usuarios con "
                                        "exactamente 3 interacciones también quedan con una sola de entrenamiento: "
                                        "`sensibilidad_umbral` muestra qué pasa con otros umbrales.")},
           "grupos": {}, "particion_d3": {}}
    for g, mask in grupos.items():
        k = int(mask.sum())
        out["grupos"][g] = {"n_usuarios": k, "proporcion_de_maestros": float(k / len(n)),
                            "n_interacciones": int(n[mask].sum()),
                            "media_interacciones": float(n[mask].mean()) if k else None}
        if g != "sin_interacciones":
            out["particion_d3"][g] = d3(n[mask])
    out["particion_d3"]["regla"] = ("D3 (docs/spec/partes/juanjose.md §3.1): prueba = 1 interacción al azar de cada usuario con >= 2; "
                                    "validación = 1 más de cada usuario con >= 3; el resto, entrenamiento; con 1 solo entrenamiento. "
                                    "Esto solo CUENTA; la partición real es de JJ-3.")
    out["particion_d3"]["total"] = d3(n)["interacciones"]
    out["proporcion_pocas"] = {"sobre_usuarios_maestros": float(grupos["pocas"].sum() / len(n)),
                               "sobre_usuarios_que_aparecen": float(grupos["pocas"].sum() / aparecen)}
    out["sensibilidad_umbral"] = []
    for t in cfg["actividad"]["sensibilidad_pocas_max"]:
        k = int(((n >= 1) & (n <= t)).sum())
        out["sensibilidad_umbral"].append({"pocas_max": t, "n_pocas": k, "n_muchas": int((n > t).sum()),
                                           "proporcion_sobre_maestros": float(k / len(n)),
                                           "proporcion_sobre_los_que_aparecen": float(k / aparecen)})
    return out


def _entrada(nombre, hip, desc, estad, valor, p, alt, metodo, efecto, n, unidad, familia="confirmatoria", gl=None, **extra):
    return {"id_prueba": nombre, "hipotesis": hip, "familia": familia, "descripcion": desc,
            "estadistico": {"nombre": estad, "valor": valor}, "gl": gl, "alternativa": alt, "metodo_p": metodo,
            "p_crudo": float(p), "p_ajustado": None, "efecto": efecto, "n": int(n), "unidad_de_analisis": unidad, **extra}


def _efecto(nombre, valor, ic, metodo_ic, umbral):
    return {"nombre": nombre, "valor": float(valor), "ic95": [float(ic[0]), float(ic[1])], "metodo_ic": metodo_ic, "umbral": umbral}


def analizar_h1(d: Datos, cfg: dict) -> tuple[dict, dict, list[dict], pd.DataFrame]:
    """H-M3-1: coincidencia preferencia–tipo, líneas base, permutación, χ² y bootstrap por usuarios."""
    B, nboot, nivel, base = cfg["n_permutaciones"], cfg["n_bootstrap"], cfg["nivel_ic"], cfg["base_seed"]
    g = coincidencia(d.destinos["tipo"], d.m["usuario_id"].tolist(), d.m["tipo"].tolist(), d.preferidos)
    obs_count = int(d.m_u.sum())
    ar = np.arange(d.n_u)
    nulos = np.concatenate([d.S[ar[None, :], P].sum(axis=1) for P in
                            permutaciones(make_rng(base, cfg["run_id"]["permutacion_h1"]), d.combo_u, B)])
    p_perm = p_permutacion(obs_count, nulos, "mayor")
    w = multiplicidades(make_rng(base, cfg["run_id"]["bootstrap_h1"]), d.n_u, nboot)
    nb = w @ d.n_por_u
    tasa_b = (w @ d.m_u) / nb
    dif_b = (w @ d.m_u - w @ d.b_u) / nb
    dif_marg_b = (w @ d.m_u - w @ d.b2_u) / nb
    tabla = _tablas_de_grupos(np.ones((1, d.n_u), dtype=np.int64), d.C, d.combo_u, len(d.combos))[0]
    chi_v = chi2_y_v(tabla)
    v_b = v_de_cramer_por_lotes(_tablas_de_grupos(w, d.C, d.combo_u, len(d.combos)))
    por_combo = {}
    filas = []
    for gi, c in enumerate(d.combos):
        sel = d.m["combinacion"] == c
        r = coincidencia(d.destinos["tipo"], d.m.loc[sel, "usuario_id"].tolist(), d.m.loc[sel, "tipo"].tolist(), d.preferidos,
                         marginal=d.q_marg)
        por_combo[c] = {"n": r["n"], "n_usuarios": int((d.usuarios["combinacion"] == c).sum()),
                        "n_usuarios_con_interacciones": int((d.combo_u == gi).sum()),
                        "tipos_cubiertos": sorted(d.tipos_de_combo[c]), "tasa": r["tasa"],
                        "linea_base_exacta": r["linea_base_exacta"], "linea_base_marginal": r["linea_base_marginal"],
                        "diferencia_exacta": r["diferencia_exacta"]}
        for ti, t in enumerate(d.tipos):
            n_ct = int(tabla[gi, ti])
            filas.append({"combinacion": c, "tipo": t, "conteo": n_ct,
                          "proporcion_fila": n_ct / r["n"] if r["n"] else float("nan"), "n_interacciones_fila": r["n"],
                          "n_usuarios_fila": por_combo[c]["n_usuarios"], "coincide": bool(d.indicador[gi, ti]),
                          "linea_base_fila": float(d.frac_combo[gi])})
    resumen = {"emparejamiento_preferencia_tipo": cfg["emparejamiento_preferencia_tipo"],
               "nota_emparejamiento": ("Emparejamiento léxico NUESTRO (la fuente no documenta la correspondencia entre las opciones "
                                       "de Preferences y los valores de Type); ver configs/m3/eda.yaml."),
               "tipos_del_catalogo": d.tipos, "ids_por_tipo": {t: int(v) for t, v in d.destinos["tipo"].value_counts().sort_index().items()},
               "global": {**g, "tasa_ic95": _ic(tasa_b, nivel), "diferencia_exacta_ic95": _ic(dif_b, nivel),
                          "diferencia_marginal_ic95": _ic(dif_marg_b, nivel),
                          "metodo_ic": f"percentiles de {nboot} remuestreos de usuarios (con sus interacciones)"},
               "distribucion_marginal_de_tipos": {str(k): float(v) for k, v in d.q_marg.sort_index().items()},
               "nulo_permutacion": {"n_permutaciones": B, "tasa_media": float(nulos.mean() / d.n_inter),
                                    "tasa_ic95": [float(x / d.n_inter) for x in _cuantiles(nulos, nivel)]},
               "por_combinacion": por_combo}
    pruebas = [
        _entrada("H1_permutacion_tasa", "H-M3-1",
                 "Permutación de las combinaciones de preferencias entre usuarios con interacciones (se conserva cuántas interacciones "
                 "tiene cada uno y los tipos de sus destinos); estadístico = tasa de coincidencia",
                 "tasa_de_coincidencia", g["tasa"], p_perm, "mayor",
                 f"permutación (B={B}; p = (1 + #{{T* >= T_obs}}) / (1 + B))",
                 _efecto("tasa − línea base exacta (diferencia de proporciones)", g["diferencia_exacta"], _ic(dif_b, nivel),
                         f"percentiles de {nboot} remuestreos de usuarios", "diferencia_tasa"), d.n_inter, "interacciones",
                 n_permutaciones=B),
        _entrada("C_H1_chi2_combinacion_tipo", "H-M3-1",
                 "χ² de independencia en la tabla combinación de preferencias × tipo de destino (interacciones; supone "
                 "independencia entre interacciones, que no se cumple del todo: un usuario aporta varias)",
                 "chi2", chi_v["chi2"], chi_v["p"], "dos_colas", "asintótica (χ²)",
                 _efecto("V de Cramér", chi_v["v_de_cramer"], _ic(v_b, nivel), f"percentiles de {nboot} remuestreos de usuarios",
                         "v_de_cramer"), d.n_inter, "interacciones", familia="complementaria", gl=chi_v["gl"])]
    return resumen, {"tabla": tabla, "chi": chi_v}, pruebas, pd.DataFrame(filas)


def analizar_h2(d: Datos, cfg: dict) -> list[dict]:
    """H-M3-2: calificación según coincida o no el tipo con las preferencias."""
    B, nboot, nivel, base = cfg["n_permutaciones"], cfg["n_bootstrap"], cfg["nivel_ic"], cfg["base_seed"]
    cal = d.m["calificacion"].to_numpy()
    escala = np.array(d.escala, dtype=float)
    total_r, n_tot = int(cal.sum()), d.n_inter
    nm, rm = int(d.m_u.sum()), int(d.R[np.arange(d.n_u), d.combo_u].sum())
    if nm in (0, n_tot):
        raise ValueError("H-M3-2 necesita interacciones que coinciden y que no coinciden")
    dif_obs = rm / nm - (total_r - rm) / (n_tot - nm)
    ar = np.arange(d.n_u)
    nulos = []
    for P in permutaciones(make_rng(base, cfg["run_id"]["permutacion_h2"]), d.combo_u, B):
        r_p, n_p = d.R[ar[None, :], P].sum(axis=1), d.S[ar[None, :], P].sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            nulos.append(r_p / n_p - (total_r - r_p) / (n_tot - n_p))
    nulos = np.concatenate(nulos)
    p_perm = p_permutacion(dif_obs, nulos[np.isfinite(nulos)], "mayor")
    w = multiplicidades(make_rng(base, cfg["run_id"]["bootstrap_h2"]), d.n_u, nboot)
    um, un = w @ d.Um, w @ d.Un
    dif_b = (um @ escala) / um.sum(axis=1) - (un @ escala) / un.sum(axis=1)
    delta_b, _ = delta_de_cliff(um, un)
    delta, ps = delta_de_cliff(d.Um.sum(axis=0), d.Un.sum(axis=0))
    x_si, x_no = cal[d.coincide], cal[~d.coincide]
    mw = stats.mannwhitneyu(x_si, x_no, alternative="greater", method="asymptotic")
    conf = _entrada("H2_permutacion_calificacion", "H-M3-2",
                    "Permutación de las combinaciones de preferencias entre usuarios; estadístico = media de la calificación de "
                    "las interacciones que coinciden − media de las que no coinciden",
                    "diferencia_de_medias", dif_obs, p_perm, "mayor", f"permutación (B={B}; p = (1 + #{{T* >= T_obs}}) / (1 + B))",
                    _efecto("delta de Cliff (coincide vs. no coincide)", delta, _ic(delta_b, nivel),
                            f"percentiles de {nboot} remuestreos de usuarios", "delta_de_cliff"), d.n_inter, "interacciones",
                    n_permutaciones=B,
                    efectos_adicionales=[{**_efecto("diferencia de medias de calificación", dif_obs, _ic(dif_b, nivel),
                                                    f"percentiles de {nboot} remuestreos de usuarios", "delta_de_cliff"),
                                          "umbral": None},
                                         {"nombre": "probabilidad de superioridad", "valor": float(ps)}],
                    medias={"coincide": float(x_si.mean()), "no_coincide": float(x_no.mean())},
                    n_por_grupo={"coincide": int(len(x_si)), "no_coincide": int(len(x_no))})
    comp = _entrada("C_H2_mann_whitney_calificacion", "H-M3-2",
                    "Mann–Whitney (unilateral: coincide > no coincide; supone independencia entre interacciones, que no se cumple "
                    "del todo: un usuario aporta varias)",
                    "U", mw.statistic, mw.pvalue, "mayor", "asintótica con corrección por empates",
                    _efecto("delta de Cliff (coincide vs. no coincide)", delta, _ic(delta_b, nivel),
                            f"percentiles de {nboot} remuestreos de usuarios", "delta_de_cliff"), d.n_inter, "interacciones",
                    familia="complementaria")
    return [conf, comp]


def analizar_h3(d: Datos, cfg: dict) -> list[dict]:
    """H-M3-3: Spearman entre popularidad y número de interacciones de cada destino."""
    B, nboot, nivel, base = cfg["n_permutaciones"], cfg["n_bootstrap"], cfg["nivel_ic"], cfg["base_seed"]
    y = d.n_por_destino.astype(float)
    pop = d.destinos["popularidad"].to_numpy(dtype=float)
    ry, rp = stats.rankdata(y), stats.rankdata(pop)
    rho = float(_rho_por_filas(ry, rp))
    nulos = np.concatenate([_rho_por_filas(ry[None, :], P) for P in
                            permutaciones(make_rng(base, cfg["run_id"]["permutacion_h3"]), rp, B)])
    p_perm = p_permutacion(rho, nulos, "dos_colas")
    rng = make_rng(base, cfg["run_id"]["bootstrap_h3"])
    idx = rng.integers(0, len(y), size=(nboot, len(y)))
    boots = _rho_por_filas(stats.rankdata(y[idx], axis=1), stats.rankdata(pop[idx], axis=1))
    sp = stats.spearmanr(pop, y)
    return [
        _entrada("H3_spearman_popularidad", "H-M3-3",
                 "Permutación de la popularidad entre los destinos; estadístico = ρ de Spearman entre popularidad y número de "
                 "interacciones (con empates, rangos medios)", "rho_de_spearman", rho, p_perm, "dos_colas",
                 f"permutación (B={B}; p = (1 + #{{|T*| >= |T_obs|}}) / (1 + B))",
                 _efecto("ρ de Spearman", rho, _ic(boots, nivel), f"percentiles de {nboot} remuestreos de destinos",
                         "rho_de_spearman"), len(y), "destinos", n_permutaciones=B,
                 destinos_con_cero=int((y == 0).sum())),
        _entrada("C_H3_spearman_asintotico", "H-M3-3", "ρ de Spearman con el p asintótico de scipy (referencia; con empates es aproximado)",
                 "rho_de_spearman", float(sp.statistic), sp.pvalue, "dos_colas", "asintótica (t de Student)",
                 _efecto("ρ de Spearman", rho, _ic(boots, nivel), f"percentiles de {nboot} remuestreos de destinos",
                         "rho_de_spearman"), len(y), "destinos", familia="complementaria")]


def analizar_h4(d: Datos, cfg: dict) -> tuple[list[dict], pd.DataFrame]:
    """H-M3-4: demografía × tipo (permutación de las etiquetas entre usuarios; V con bootstrap por usuarios)."""
    B, nboot, nivel, base = cfg["n_permutaciones"], cfg["n_bootstrap"], cfg["nivel_ic"], cfg["base_seed"]
    w = multiplicidades(make_rng(base, cfg["run_id"]["bootstrap_h4"]), d.n_u, nboot)
    C32 = d.C.astype(np.float32)
    pruebas, filas = [], []
    for col, idp, run, etiqueta in VARIABLES_DEMOGRAFICAS:
        valores = d.usuarios_aparecen[col].to_numpy()
        niveles = sorted(pd.unique(valores))
        grupos = np.searchsorted(niveles, valores)
        k = len(niveles)
        obs = _tablas_de_grupos(np.ones((1, d.n_u), dtype=np.int64), d.C, grupos, k)
        chi_obs = float(chi2_por_lotes(obs)[0])
        nulos = np.concatenate([chi2_por_lotes(_tablas_permutadas(P, C32, k)) for P in
                                permutaciones(make_rng(base, cfg["run_id"][f"permutacion_h4_{run}"]), grupos, B)])
        p_perm = p_permutacion(chi_obs, nulos, "mayor")
        v_b = v_de_cramer_por_lotes(_tablas_de_grupos(w, d.C, grupos, k))
        asint = chi2_y_v(obs[0])
        pruebas.append(_entrada(
            idp, "H-M3-4", f"Permutación de {etiqueta} entre usuarios con interacciones (se conservan los tipos de cada usuario); "
                           "estadístico = χ² de la tabla variable × tipo (interacciones)",
            "chi2", chi_obs, p_perm, "mayor", f"permutación (B={B}; p = (1 + #{{T* >= T_obs}}) / (1 + B))",
            _efecto("V de Cramér", asint["v_de_cramer"], _ic(v_b, nivel), f"percentiles de {nboot} remuestreos de usuarios",
                    "v_de_cramer"), d.n_inter, "interacciones", gl=asint["gl"], n_permutaciones=B,
            p_chi2_asintotico=asint["p"], niveles=[str(x) for x in niveles]))
        for gi, nv in enumerate(niveles):
            tot = int(obs[0, gi].sum())
            for ti, t in enumerate(d.tipos):
                filas.append({"variable": col, "nivel": str(nv), "tipo": t, "conteo": int(obs[0, gi, ti]),
                              "proporcion_fila": float(obs[0, gi, ti] / tot) if tot else float("nan"),
                              "n_interacciones_fila": tot, "n_usuarios_fila": int((grupos == gi).sum())})
    return pruebas, pd.DataFrame(filas)


def analizar_h5(conc: dict, cfg: dict) -> list[dict]:
    """H-M3-5: Gini (confirmatoria) y HHI/cuota top (complementarias) frente al reparto uniforme simulado."""
    nivel = cfg["nivel_ic"]
    pruebas = []
    for nombre, info in conc["niveles"].items():
        az, obs = info["azar_uniforme"], info["observado"]
        g = az["gini"]
        pruebas.append(_entrada(
            f"H5_gini_{nombre}", "H-M3-5",
            f"Gini de las interacciones por {nombre} frente al reparto uniforme al azar de las mismas {info['n_interacciones']} "
            "interacciones (simulación multinomial)", "gini", obs["gini"], g["p_observado_mayor_o_igual"], "mayor",
            f"simulación uniforme (S={az['n_simulaciones']}; p = (1 + #{{sim >= obs}}) / (1 + S))",
            _efecto("Gini observado − media del Gini bajo azar", obs["gini"] - g["media"],
                    (obs["gini"] - g["ic95"][1], obs["gini"] - g["ic95"][0]),
                    f"observado menos los percentiles de {az['n_simulaciones']} simulaciones", "exceso_de_gini"),
            info["n_interacciones"], "interacciones", n_entidades=info["n_entidades"], referencia_azar_media=g["media"],
            referencia_azar_ic95=g["ic95"]))
        for clave in ("hhi", "hhi_normalizado"):
            r = az[clave]
            pruebas.append(_entrada(
                f"C_H5_{clave}_{nombre}", "H-M3-5", f"{clave} por {nombre} frente al reparto uniforme simulado", clave,
                obs[clave], r["p_observado_mayor_o_igual"], "mayor", f"simulación uniforme (S={az['n_simulaciones']})",
                _efecto(f"{clave} observado − media bajo azar", obs[clave] - r["media"],
                        (obs[clave] - r["ic95"][1], obs[clave] - r["ic95"][0]), "observado menos percentiles de la simulación", None),
                info["n_interacciones"], "interacciones", familia="complementaria"))
        for f, r in az["cuota_top"].items():
            pruebas.append(_entrada(
                f"C_H5_cuota_top_{f}_{nombre}", "H-M3-5",
                f"Cuota de interacciones del {float(f):.0%} de {nombre} más popular frente al reparto uniforme simulado",
                "cuota_top", obs["cuota_top"][f], r["p_observado_mayor_o_igual"], "mayor",
                f"simulación uniforme (S={az['n_simulaciones']})",
                _efecto("cuota observada − media bajo azar", obs["cuota_top"][f] - r["media"],
                        (obs["cuota_top"][f] - r["ic95"][1], obs["cuota_top"][f] - r["ic95"][0]),
                        "observado menos percentiles de la simulación", None),
                info["n_interacciones"], "interacciones", familia="complementaria"))
    return pruebas


def analizar_calificaciones(d: Datos) -> pd.DataFrame:
    filas = []
    for origen, mask in (("resena", d.m["origen"] == "resena"), ("historial", d.m["origen"] == "historial"),
                         ("union", np.ones(len(d.m), dtype=bool))):
        c = d.m.loc[mask, "calificacion"]
        for k in d.escala:
            n_k = int((c == k).sum())
            filas.append({"origen": origen, "calificacion": k, "conteo": n_k, "proporcion": n_k / len(c),
                          "n_origen": int(len(c)), "media_origen": float(c.mean()), "desviacion_origen": float(c.std(ddof=1))})
    return pd.DataFrame(filas)


def analizar_h6(d: Datos, cfg: dict) -> list[dict]:
    """H-M3-6: reseñas vs. historial en tipos (χ², V) y calificaciones (Mann–Whitney, delta de Cliff)."""
    nboot, nivel, base = cfg["n_bootstrap"], cfg["nivel_ic"], cfg["base_seed"]
    w = multiplicidades(make_rng(base, cfg["run_id"]["bootstrap_h6"]), d.n_u, nboot)
    n_t, n_k = len(d.tipos), len(d.escala)
    tabla = d.Co.sum(axis=0)
    chi_v = chi2_y_v(tabla)
    tablas_b = (w @ d.Co.reshape(d.n_u, 2 * n_t)).reshape(nboot, 2, n_t)
    v_b = v_de_cramer_por_lotes(tablas_b)
    cr_b = (w @ d.Cr.reshape(d.n_u, 2 * n_k)).reshape(nboot, 2, n_k)
    delta_b, _ = delta_de_cliff(cr_b[:, 0, :], cr_b[:, 1, :])
    delta, ps = delta_de_cliff(d.Cr.sum(axis=0)[0], d.Cr.sum(axis=0)[1])
    cal = d.m["calificacion"].to_numpy()
    res, his = cal[d.oi == 0], cal[d.oi == 1]
    mw = stats.mannwhitneyu(res, his, alternative="two-sided", method="asymptotic")
    chi_cal = chi2_y_v(d.Cr.sum(axis=0))
    return [
        _entrada("H6_chi2_origen_tipo", "H-M3-6",
                 "χ² de independencia en la tabla origen (reseña / historial) × tipo de destino (supone independencia entre "
                 "interacciones; la misma persona puede estar en ambos orígenes)", "chi2", chi_v["chi2"], chi_v["p"], "dos_colas",
                 "asintótica (χ²)", _efecto("V de Cramér", chi_v["v_de_cramer"], _ic(v_b, nivel),
                                            f"percentiles de {nboot} remuestreos de usuarios", "v_de_cramer"),
                 d.n_inter, "interacciones", gl=chi_v["gl"],
                 conteos={o: {t: int(tabla[i, j]) for j, t in enumerate(d.tipos)} for i, o in enumerate(ORIGENES)}),
        _entrada("H6_mann_whitney_calificacion", "H-M3-6",
                 "Mann–Whitney bilateral de la calificación de reseñas frente a la de historial (supone independencia entre "
                 "interacciones)", "U", mw.statistic, mw.pvalue, "dos_colas", "asintótica con corrección por empates",
                 _efecto("delta de Cliff (reseña vs. historial)", delta, _ic(delta_b, nivel),
                         f"percentiles de {nboot} remuestreos de usuarios", "delta_de_cliff"),
                 d.n_inter, "interacciones", probabilidad_de_superioridad=float(ps),
                 medias={"resena": float(res.mean()), "historial": float(his.mean())}),
        _entrada("C_H6_chi2_origen_calificacion", "H-M3-6", "χ² de independencia origen × calificación (referencia)",
                 "chi2", chi_cal["chi2"], chi_cal["p"], "dos_colas", "asintótica (χ²)",
                 _efecto("V de Cramér", chi_cal["v_de_cramer"], (float("nan"), float("nan")), "sin IC", "v_de_cramer"),
                 d.n_inter, "interacciones", familia="complementaria", gl=chi_cal["gl"])]


# =========================================================================== hipótesis
def _f(x, dec: int = 3) -> str:
    return f"{x:.{dec}f}".replace(".", ",")


def _fp(p: float) -> str:
    return _f(p, 4) if p < 0.001 else _f(p, 3)


def _ic_txt(ic) -> str:
    return f"[{_f(ic[0])}; {_f(ic[1])}]"


def _razon(veredicto: str, pruebas: list[dict], cfg: dict) -> str:
    """Frase que explica el veredicto con el criterio de la config (sin interpretar más allá de las cifras)."""
    alfa = _f(cfg["alfa"], 2)
    if veredicto == "confirmada":
        return (f"Veredicto «confirmada»: al menos una prueba tiene p ajustado < {alfa} y un efecto igual o mayor que el mínimo "
                "declarado en la config.")
    if veredicto == "refutada":
        return (f"Veredicto «refutada»: ninguna prueba tiene p ajustado < {alfa} y el IC 95 % del efecto de todas queda dentro de "
                "±el mínimo declarado, así que el efecto es compatible con cero y excluye un efecto de esa magnitud.")
    detectables = [p for p in pruebas if p["p_ajustado"] < cfg["alfa"]]
    if detectables:
        return (f"Veredicto «no concluyente»: hay efecto detectable (p ajustado < {alfa}) pero menor que el mínimo declarado "
                "en la config, de modo que no se declara «confirmada»; se describe su tamaño.")
    return (f"Veredicto «no concluyente»: ninguna prueba tiene p ajustado < {alfa}, pero el IC 95 % del efecto no queda dentro de "
            "±el mínimo declarado, así que no se descarta un efecto de esa magnitud.")


def construir_hipotesis(cfg: dict, d: Datos, pruebas: list[dict], h1: dict, actividad: dict, conc: dict) -> list[dict]:
    por_id = {p["id_prueba"]: p for p in pruebas}
    salida = cfg["salida"]["carpeta"].rstrip("/")
    conf = [p for p in pruebas if p["familia"] == "confirmatoria"]
    m = len(conf)
    minimo = cfg["efecto_minimo"]
    alfa_txt = _f(cfg["alfa"], 2)
    advertencia = " Datos generados (D4): el patrón, si lo hay, no se atribuye a comportamiento real de turistas."

    def verdicto(hid: str) -> tuple[str, list[dict]]:
        ps = [p for p in conf if p["hipotesis"] == hid]
        res = [veredicto_de_prueba(p["p_ajustado"], p["efecto"]["valor"], tuple(p["efecto"]["ic95"]), minimo[p["efecto"]["umbral"]],
                                   cfg["alfa"], p["alternativa"]) for p in ps]
        return veredicto_de_hipotesis(res), ps

    def criterio(ps: list[dict]) -> str:
        partes = []
        for p in ps:
            r = veredicto_de_prueba(p["p_ajustado"], p["efecto"]["valor"], tuple(p["efecto"]["ic95"]),
                                    minimo[p["efecto"]["umbral"]], cfg["alfa"], p["alternativa"])
            partes.append(f"{p['id_prueba']}: {r} (mínimo {p['efecto']['umbral']} = {_f(minimo[p['efecto']['umbral']])})")
        return "Criterio por prueba: " + "; ".join(partes) + "."

    def cifras(p: dict) -> str:
        e = p["efecto"]
        return (f"{p['id_prueba']}: estadístico {p['estadistico']['nombre']} = {_f(p['estadistico']['valor'], 4)}, p crudo "
                f"{_fp(p['p_crudo'])}, p ajustado (Holm, m = {m}) {_fp(p['p_ajustado'])}, {e['nombre']} {_f(e['valor'])} "
                f"(IC 95 % {_ic_txt(e['ic95'])})")

    hip = []
    g = h1["global"]
    # --- H-M3-1
    v, ps = verdicto("H-M3-1")
    c1 = por_id["C_H1_chi2_combinacion_tipo"]
    combos = "; ".join(f"«{c}»: tasa {_f(x['tasa'])} frente a {_f(x['linea_base_exacta'])} (n = {x['n']})"
                       for c, x in h1["por_combinacion"].items())
    hip.append({
        "id": "H-M3-1",
        "enunciado": ("Las preferencias declaradas de un usuario explican el TIPO de destino con el que interactúa: la proporción "
                      "de sus interacciones con destinos de un tipo que cubren sus preferencias supera lo esperado si eligiera "
                      "un destino al azar del catálogo."),
        "justificacion": ("Preferences (usuario) y Type (destino) son las variables de contenido de la fuente que podrían "
                          "relacionarse. Para compararlas se empareja cada opción con el tipo del mismo nombre (Beaches→Beach, "
                          "Historical→Historical, City→City, Adventure→Adventure, Nature→Nature): es un emparejamiento léxico "
                          "NUESTRO, la fuente no documenta esa correspondencia. Si las preferencias no importaran, la coincidencia "
                          "esperada sería la fracción del catálogo cuyo tipo está en las preferencias del usuario (línea base exacta)."),
        "evidencia_esperada": (f"Si es cierta: tasa de coincidencia mayor que la línea base exacta en al menos {_f(minimo['diferencia_tasa'])} "
                               f"(IC 95 % por usuarios por encima de 0) y p ajustado < {alfa_txt} en la permutación. Si es falsa: la tasa "
                               "cae dentro de la variación de la permutación y la diferencia es compatible con cero."),
        "figura_o_tabla": "preferencias_tipo.png; matriz_preferencias_tipo.csv; coincidencia_preferencias.json",
        "resultado": (f"Tasa de coincidencia {_f(g['tasa'])} ({g['n_coinciden']} de {g['n']} interacciones) frente a una línea base de "
                      f"azar exacta de {_f(g['linea_base_exacta'])} (diferencia {_f(g['diferencia_exacta'])}, IC 95 % "
                      f"{_ic_txt(g['diferencia_exacta_ic95'])}, bootstrap por usuarios) y de {_f(g['linea_base_marginal'])} con la "
                      f"distribución marginal de tipos observada. Por combinación: {combos}. "
                      f"{cifras(ps[0])}. χ² combinación × tipo: {_f(c1['estadistico']['valor'], 2)} (gl {c1['gl']}, p asintótico "
                      f"{_fp(c1['p_crudo'])}), V de Cramér {_f(c1['efecto']['valor'])} (IC 95 % {_ic_txt(c1['efecto']['ic95'])}). "
                      f"{criterio(ps)} {_razon(v, ps, cfg)} El emparejamiento preferencia→tipo es léxico y nuestro: con otro, "
                      "el resultado cambia. Los IC y la permutación son por usuario porque cada uno aporta varias interacciones."
                      + advertencia),
        "veredicto": v,
        "evidencia": (f"{salida}/pruebas_hipotesis.json (H1_permutacion_tasa, C_H1_chi2_combinacion_tipo); "
                      f"{salida}/coincidencia_preferencias.json; {salida}/matriz_preferencias_tipo.csv")})
    # --- H-M3-2
    v, ps = verdicto("H-M3-2")
    p2 = ps[0]
    c2 = por_id["C_H2_mann_whitney_calificacion"]
    hip.append({
        "id": "H-M3-2",
        "enunciado": "La calificación (1–5) de una interacción es mayor cuando el tipo del destino está cubierto por las preferencias del usuario.",
        "justificacion": ("Si las preferencias reflejaran gusto, una interacción con un destino del tipo preferido debería calificarse "
                          "mejor. Usa el mismo emparejamiento léxico nuestro de H-M3-1 (no documentado por la fuente). La calificación "
                          "es un atributo de la interacción, no el objetivo de los modelos (D1)."),
        "evidencia_esperada": (f"Si es cierta: diferencia de medias positiva, delta de Cliff >= {_f(minimo['delta_de_cliff'])} y p ajustado "
                               f"< {alfa_txt}. Si es falsa: la diferencia es compatible con cero con un IC estrecho."),
        "figura_o_tabla": "pruebas_hipotesis.json (H2_permutacion_calificacion); calificaciones.csv",
        "resultado": (f"Media de la calificación cuando el tipo coincide {_f(p2['medias']['coincide'])} (n = {p2['n_por_grupo']['coincide']}) "
                      f"frente a {_f(p2['medias']['no_coincide'])} cuando no coincide (n = {p2['n_por_grupo']['no_coincide']}); "
                      f"diferencia {_f(p2['estadistico']['valor'])} (IC 95 % {_ic_txt(p2['efectos_adicionales'][0]['ic95'])}). "
                      f"{cifras(p2)}. Mann–Whitney unilateral (complementaria): p asintótico {_fp(c2['p_crudo'])}. "
                      f"{criterio(ps)} {_razon(v, ps, cfg)} El p viene de permutar combinaciones entre usuarios (respeta que un usuario "
                      "aporta varias interacciones); Mann–Whitney supone independencia." + advertencia),
        "veredicto": v,
        "evidencia": f"{salida}/pruebas_hipotesis.json (H2_permutacion_calificacion, C_H2_mann_whitney_calificacion)"})
    # --- H-M3-3
    v, ps = verdicto("H-M3-3")
    p3 = ps[0]
    hip.append({
        "id": "H-M3-3",
        "enunciado": ("La popularidad del destino (Popularity de la fuente) se relaciona con su número de interacciones: ρ de Spearman "
                      "a nivel destino_id distinto de cero."),
        "justificacion": ("Popularity es la única variable de contenido del destino que cambia entre los 1 000 ids (nombre, estado, tipo y "
                          "temporada son constantes por lugar, D2); un puntaje de popularidad debería acompañar a la demanda. La fuente no "
                          "dice cómo se calculó."),
        "evidencia_esperada": (f"Si es cierta: |ρ| >= {_f(minimo['rho_de_spearman'])} y p ajustado < {alfa_txt}. Si es falsa: ρ compatible con 0 con IC estrecho."),
        "figura_o_tabla": "interacciones_por_destino.csv; pruebas_hipotesis.json (H3_spearman_popularidad)",
        "resultado": (f"{cifras(p3)}; {p3['destinos_con_cero']} de {p3['n']} destinos tienen 0 interacciones, por lo que hay muchos "
                      f"empates (rangos medios). {criterio(ps)} {_razon(v, ps, cfg)}" + advertencia),
        "veredicto": v,
        "evidencia": f"{salida}/pruebas_hipotesis.json (H3_spearman_popularidad); {salida}/interacciones_por_destino.csv"})
    # --- H-M3-4
    v, ps = verdicto("H-M3-4")
    detalle = "; ".join(f"{p['id_prueba']}: χ² {_f(p['estadistico']['valor'], 2)} (gl {p['gl']}), p crudo {_fp(p['p_crudo'])}, "
                        f"p ajustado {_fp(p['p_ajustado'])}, V {_f(p['efecto']['valor'])} (IC 95 % {_ic_txt(p['efecto']['ic95'])})"
                        for p in ps)
    hip.append({
        "id": "H-M3-4",
        "enunciado": ("La demografía del usuario (género, número de adultos, número de niños) se relaciona con el tipo de destino elegido "
                      "(p. ej. familias con niños eligen más playa)."),
        "justificacion": ("Es la hipótesis de sentido común sobre quién va adónde; el conjunto trae esas tres variables del usuario. "
                          "Tipo y lugar son la misma partición de los destinos (cada lugar tiene un solo tipo), así que una sola "
                          "prueba por variable cubre ambos. Un usuario aporta varias interacciones: el p sale de permutar la variable "
                          "ENTRE usuarios."),
        "evidencia_esperada": (f"Si es cierta: V de Cramér >= {_f(minimo['v_de_cramer'])} y p ajustado < {alfa_txt} en al menos una variable. "
                               "Si es falsa: V compatible con ruido (IC por debajo del mínimo) en las tres."),
        "figura_o_tabla": "demografia_tipo.csv; pruebas_hipotesis.json (H4_*)",
        "resultado": (f"{detalle}. {criterio(ps)} {_razon(v, ps, cfg)}" + advertencia),
        "veredicto": v,
        "evidencia": f"{salida}/pruebas_hipotesis.json (H4_genero, H4_n_adultos, H4_n_ninos); {salida}/demografia_tipo.csv"})
    # --- H-M3-5
    v, ps = verdicto("H-M3-5")
    cd, cl = conc["niveles"]["destino_id"], conc["niveles"]["lugar"]
    hip.append({
        "id": "H-M3-5",
        "enunciado": ("Las interacciones se concentran en pocos destinos más de lo esperado si las mismas interacciones se repartieran "
                      "uniformemente al azar (cola larga más allá del azar), a nivel destino_id y lugar."),
        "justificacion": ("El enunciado pide la concentración en populares. Un reparto uniforme ya produce desigualdad por azar "
                          "(unos destinos reciben 0 y otros varias); por eso se compara el Gini, el HHI y la cuota top con su "
                          "distribución bajo reparto uniforme simulado y no con 0."),
        "evidencia_esperada": (f"Si es cierta: Gini observado mayor que la media del azar en al menos {_f(minimo['exceso_de_gini'])} y fuera "
                               f"de su IC 95 %, p ajustado < {alfa_txt}. Si es falsa: el observado cae dentro de la banda del azar."),
        "figura_o_tabla": "cola_larga.png; lorenz.png; concentracion.json",
        "resultado": (f"destino_id: Gini {_f(cd['observado']['gini'])} (azar: media {_f(cd['azar_uniforme']['gini']['media'])}, IC 95 % "
                      f"{_ic_txt(cd['azar_uniforme']['gini']['ic95'])}), HHI {_f(cd['observado']['hhi'], 5)} (azar {_f(cd['azar_uniforme']['hhi']['media'], 5)}), "
                      f"cuota del 10 % más popular {_f(cd['observado']['cuota_top']['0.1'])} (azar {_f(cd['azar_uniforme']['cuota_top']['0.1']['media'])}). "
                      f"lugar ({cl['n_entidades']} lugares): Gini {_f(cl['observado']['gini'])} (azar: media {_f(cl['azar_uniforme']['gini']['media'])}, "
                      f"IC 95 % {_ic_txt(cl['azar_uniforme']['gini']['ic95'])}). "
                      + "; ".join(cifras(p) for p in ps) + f". {criterio(ps)} {_razon(v, ps, cfg)} La referencia es un reparto "
                      "multinomial uniforme (no impone pares usuario–destino únicos); con 5 lugares el IC del azar es ancho." + advertencia),
        "veredicto": v,
        "evidencia": f"{salida}/pruebas_hipotesis.json (H5_gini_destino_id, H5_gini_lugar); {salida}/concentracion.json"})
    # --- H-M3-6
    v, ps = verdicto("H-M3-6")
    hip.append({
        "id": "H-M3-6",
        "enunciado": "Las reseñas y el historial se comportan distinto: difieren en los tipos de destino y en la distribución de las calificaciones.",
        "justificacion": ("D1 unió los dos archivos como una sola interacción implícita. Esa unión solo es inocua si ambos orígenes se "
                          "parecen; si difirieran, habría que modelar el origen aparte."),
        "evidencia_esperada": (f"Si es cierta: V de Cramér >= {_f(minimo['v_de_cramer'])} (origen × tipo) o delta de Cliff >= "
                               f"{_f(minimo['delta_de_cliff'])} (calificación), con p ajustado < {alfa_txt}. Si es falsa: ambos efectos compatibles con cero."),
        "figura_o_tabla": "calificaciones_origen.png; calificaciones.csv; pruebas_hipotesis.json (H6_*)",
        "resultado": ("; ".join(cifras(p) for p in ps) + f". {criterio(ps)} {_razon(v, ps, cfg)} Los tests suponen independencia entre "
                      "interacciones y la misma persona puede aparecer en ambos orígenes." + advertencia),
        "veredicto": v,
        "evidencia": f"{salida}/pruebas_hipotesis.json (H6_chi2_origen_tipo, H6_mann_whitney_calificacion); {salida}/calificaciones.csv"})
    # --- pendientes: se cierran al modelar
    hip.append({
        "id": "H-M3-7",
        "enunciado": ("Una red con variables de contenido (preferencias del usuario, tipo del destino) no supera a la línea base de "
                      "popularidad por más que la variabilidad entre semillas (NDCG@5, 30 semillas)."),
        "justificacion": ("Con datos generados donde la relación preferencias–tipo es débil o nula, el contenido puede no aportar; el "
                          "enunciado pide comparar de forma justa y con 30 semillas."),
        "evidencia_esperada": ("Falsable: si la media de NDCG@5 de la red menos la de popularidad supera la desviación estándar entre las "
                               "30 semillas de la red, la hipótesis se refuta; si no, se confirma."),
        "figura_o_tabla": "Se cierra al modelar (JJ-10): results/data/m3/summary.json",
        "resultado": "Pendiente: se cierra en JJ-10, cuando existan la red, la línea base de popularidad y las 30 semillas.",
        "veredicto": "pendiente",
        "evidencia": "Aún no existe (results/data/m3/summary.json lo produce JJ-5)."})
    hip.append({
        "id": "H-M3-8",
        "enunciado": ("El acierto medido por lugar (5 lugares) es mucho mayor que el medido por destino_id (1 000 ids) en todos los modelos."),
        "justificacion": ("Los 1 000 ids son 5 lugares repetidos 200 veces (D2): acertar el lugar es un problema de 5 clases y acertar el "
                          "id exacto, de 1 000."),
        "evidencia_esperada": ("Falsable: Recall@K por lugar menor o igual que Recall@K por destino_id en algún modelo y algún K refuta la hipótesis."),
        "figura_o_tabla": "Se cierra al modelar (JJ-6)",
        "resultado": "Pendiente: se cierra en JJ-10, con las métricas por lugar y por destino_id de todos los modelos.",
        "veredicto": "pendiente",
        "evidencia": "Aún no existe."})
    p_max = cfg["actividad"]["pocas_max"]
    hip.append({
        "id": "H-M3-9",
        "enunciado": (f"Los usuarios con pocas interacciones (1 a {p_max}) obtienen un NDCG@5 menor que los de muchas ({p_max + 1} o más) "
                      "tanto en la popularidad como en la red."),
        "justificacion": ("Con D3 los usuarios con pocas interacciones tienen una sola interacción de entrenamiento, así que los modelos "
                          "colaborativos y de contenido tienen menos información sobre ellos."),
        "evidencia_esperada": ("Falsable: NDCG@5 de «pocas» mayor o igual que el de «muchas» en algún modelo refuta la hipótesis."),
        "figura_o_tabla": "Se cierra al modelar (JJ-6)",
        "resultado": "Pendiente: se cierra en JJ-10, con el desempeño separado por grupo de actividad.",
        "veredicto": "pendiente",
        "evidencia": "Aún no existe."})
    return hip


# =========================================================================== escritura
def _escribir_csv(df: pd.DataFrame, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    df.to_csv(tmp, index=False, encoding="utf-8", lineterminator="\n")
    tmp.replace(ruta)


def _tablas_por_entidad(d: Datos, grupo_de_usuario: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    m = d.m
    por_u = m.groupby(["usuario_id", "origen"]).size().unstack(fill_value=0).reindex(d.usuarios["usuario_id"], fill_value=0)
    pu = pd.DataFrame({"usuario_id": d.usuarios["usuario_id"].to_numpy(),
                       "n_interacciones": d.n_por_usuario,
                       "n_resenas": por_u.get("resena", pd.Series(0, index=por_u.index)).to_numpy(),
                       "n_historial": por_u.get("historial", pd.Series(0, index=por_u.index)).to_numpy(),
                       "grupo_actividad": grupo_de_usuario})
    por_d = m.groupby(["destino_id", "origen"]).size().unstack(fill_value=0).reindex(d.destinos["destino_id"], fill_value=0)
    pd_ = pd.DataFrame({"destino_id": d.destinos["destino_id"].to_numpy(), "lugar": d.destinos["lugar"].to_numpy(),
                        "tipo": d.destinos["tipo"].to_numpy(), "popularidad": d.destinos["popularidad"].to_numpy(),
                        "n_interacciones": d.n_por_destino,
                        "n_resenas": por_d.get("resena", pd.Series(0, index=por_d.index)).to_numpy(),
                        "n_historial": por_d.get("historial", pd.Series(0, index=por_d.index)).to_numpy()})
    por_l = pd.DataFrame({"lugar": d.lugares})
    tipo_de_lugar = d.destinos.drop_duplicates("lugar").set_index("lugar")["tipo"]
    por_l["tipo"] = [tipo_de_lugar[x] for x in d.lugares]
    por_l["n_destinos"] = np.bincount(d.lugar_de_destino, minlength=len(d.lugares))
    por_l["n_interacciones"] = d.n_por_lugar.astype(int)
    por_l["proporcion_interacciones"] = por_l["n_interacciones"] / por_l["n_interacciones"].sum()
    por_l["media_por_destino"] = por_l["n_interacciones"] / por_l["n_destinos"]
    return pu, pd_, por_l


def main(cfg: dict) -> int:
    t0 = time.perf_counter()
    destinos, usuarios, inter = _leer(cfg)
    _validar(destinos, usuarios, inter)
    d = Datos(cfg, destinos, usuarios, inter)
    out = Path(cfg["salida"]["carpeta"])

    # Todo se calcula antes de escribir: si algo falla, no queda nada a medias.
    dist, sim_dest = analizar_actividad(d, cfg)
    verificar_contra_ficha(d, cfg, dist["usuarios"]["observado"], out)
    conc = analizar_concentracion(d, cfg, sim_dest)
    act = analizar_actividad_usuarios(d, cfg)
    n = d.n_por_usuario
    p_max = cfg["actividad"]["pocas_max"]
    grupo = np.where(n == 0, "sin_interacciones", np.where(n <= p_max, "pocas", "muchas"))
    tab_u, tab_d, tab_l = _tablas_por_entidad(d, grupo)
    calif = analizar_calificaciones(d)
    h1, _, p_h1, matriz = analizar_h1(d, cfg)
    p_h2 = analizar_h2(d, cfg)
    p_h3 = analizar_h3(d, cfg)
    p_h4, demografia = analizar_h4(d, cfg)
    p_h5 = analizar_h5(conc, cfg)
    p_h6 = analizar_h6(d, cfg)

    todas = p_h1 + p_h2 + p_h3 + p_h4 + p_h5 + p_h6
    conf = [p for p in todas if p["familia"] == "confirmatoria"]
    for p, aj in zip(conf, holm([p["p_crudo"] for p in conf])):
        p["p_ajustado"] = float(aj)
    pruebas = conf + [p for p in todas if p["familia"] == "complementaria"]
    pr = {"alfa": cfg["alfa"], "ajuste": cfg["ajuste_multiple"], "m_familia": len(conf),
          "familia_confirmatoria": [p["id_prueba"] for p in conf],
          "criterio_de_veredicto": {"efecto_minimo": cfg["efecto_minimo"],
                                    "regla": ("la prueba cumple si p ajustado < alfa y |efecto| >= mínimo (en el sentido de la alternativa); "
                                              "refuta si p ajustado >= alfa y el IC 95 % del efecto queda dentro de ±mínimo; hipótesis "
                                              "con varias pruebas: confirmada si alguna cumple, refutada si todas refutan, si no, no "
                                              "concluyente; un efecto detectable pero menor que el mínimo nunca confirma")},
          "semillas": {"base_seed": cfg["base_seed"], "run_id": cfg["run_id"]},
          "n_permutaciones": cfg["n_permutaciones"], "n_bootstrap": cfg["n_bootstrap"],
          "n_simulaciones_azar": cfg["n_simulaciones_azar"], "nivel_ic": cfg["nivel_ic"],
          "pruebas": pruebas}
    hip = construir_hipotesis(cfg, d, pruebas, h1, act, conc)

    _escribir_csv(tab_u, out / "interacciones_por_usuario.csv")
    _escribir_csv(tab_d, out / "interacciones_por_destino.csv")
    _escribir_csv(tab_l, out / "interacciones_por_lugar.csv")
    save_json(out / "distribucion_actividad.json", dist)
    _escribir_csv(calif, out / "calificaciones.csv")
    save_json(out / "concentracion.json", conc)
    save_json(out / "actividad_usuarios.json", act)
    save_json(out / "coincidencia_preferencias.json", h1)
    _escribir_csv(matriz, out / "matriz_preferencias_tipo.csv")
    _escribir_csv(demografia, out / "demografia_tipo.csv")
    save_json(out / "pruebas_hipotesis.json", pr)
    escribir_hipotesis(out / "hipotesis.json", hip)
    _imprimir(cfg, d, dist, conc, act, h1, pruebas, hip, time.perf_counter() - t0)
    return 0


def _imprimir(cfg, d, dist, conc, act, h1, pruebas, hip, segundos) -> None:
    print(f"Usuarios: {len(d.usuarios)} (con interacciones: {d.n_u}) · destinos: {len(d.destinos)} · interacciones: {d.n_inter}")
    print("Usuarios por n.º de interacciones (observado | azar media): "
          + " · ".join(f"{k}: {v} | {dist['usuarios']['azar_media'][k]:.1f}" for k, v in dist["usuarios"]["observado"].items()))
    print("Destinos por n.º de interacciones (observado | azar media): "
          + " · ".join(f"{k}: {v} | {dist['destinos']['azar_media'][k]:.1f}" for k, v in dist["destinos"]["observado"].items()))
    for nombre, info in conc["niveles"].items():
        g = info["azar_uniforme"]["gini"]
        print(f"Gini {nombre}: {info['observado']['gini']:.4f} (azar {g['media']:.4f}, IC 95 % [{g['ic95'][0]:.4f}; {g['ic95'][1]:.4f}])")
    a = act["grupos"]
    print(f"Actividad: pocas (<= {act['umbral']['pocas_max']}) {a['pocas']['n_usuarios']} · muchas {a['muchas']['n_usuarios']} · "
          f"sin interacciones {a['sin_interacciones']['n_usuarios']}")
    g = h1["global"]
    print(f"H-M3-1: tasa {g['tasa']:.4f} · línea base exacta {g['linea_base_exacta']:.4f} · marginal {g['linea_base_marginal']:.4f}")
    for p in pruebas:
        if p["familia"] == "confirmatoria":
            print(f"  {p['id_prueba']}: p crudo {p['p_crudo']:.4g} · p ajustado {p['p_ajustado']:.4g} · "
                  f"efecto {p['efecto']['valor']:.4f} ({p['efecto']['nombre']})")
    print("Veredictos: " + " · ".join(f"{h['id']} {h['veredicto']}" for h in hip))
    print(f"Salida: {Path(cfg['salida']['carpeta']).as_posix()}")
    print(f"Tiempo de ejecución: {segundos:.1f} s")
