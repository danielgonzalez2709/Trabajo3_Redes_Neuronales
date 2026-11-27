"""M3 — estadística del análisis descriptivo (JJ-2): funciones puras, sin lectura de datos ni textos de hipótesis.

Concentración (Gini, HHI, cuota top, Lorenz), ajuste por multiplicidad, p de permutación, delta de Cliff, ρ de Spearman,
tablas de contingencia (χ², V de Cramér, residuos), simulación del reparto uniforme y remuestreos (permutaciones y
bootstrap por unidades). Las definiciones las fijan las pruebas de ``tests/test_eda_m3.py`` y se resumen en
``eda.py``. Toda aleatoriedad llega por un ``np.random.Generator`` recibido (sembrado con ``make_rng`` en ``eda.py``).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

TOLERANCIA_NUMERICA = 1e-12   # empates numéricos al comparar un estadístico observado con sus réplicas


# =========================================================================== medidas de concentración
def _positivo(x) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    if (a.sum(axis=-1) <= 0).any():
        raise ValueError("la suma de los conteos debe ser positiva para medir la concentración")
    return a


def gini(x):
    """Gini sin corrección: 2·Σ i·x_(i) / (n·Σx) − (n+1)/n, en [0, (n−1)/n]. Admite una fila o una matriz."""
    a = np.sort(_positivo(x), axis=-1)
    n = a.shape[-1]
    return 2.0 * (a * np.arange(1, n + 1)).sum(axis=-1) / (n * a.sum(axis=-1)) - (n + 1) / n


def gini_reescalado(x):
    """Gini·n/(n−1), en [0, 1]. Es un reescalado del máximo (n−1)/n a 1, NO una corrección de sesgo."""
    n = np.asarray(x).shape[-1]
    if n < 2:
        raise ValueError("el Gini reescalado necesita al menos 2 entidades")
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
    """Vértices de la curva de Lorenz (x_j = j/n, y_j = suma de los j menores / total), j = 0…n; admite matriz."""
    a = np.sort(_positivo(x), axis=-1)
    n = a.shape[-1]
    ys = np.concatenate([np.zeros(a.shape[:-1] + (1,)), np.cumsum(a, axis=-1) / a.sum(axis=-1, keepdims=True)], axis=-1)
    return np.arange(n + 1) / n, ys


# =========================================================================== estadística auxiliar
def holm(p) -> list[float]:
    """Ajuste de Holm (escalonado, monótono) de la familia ``p``; devuelve los p ajustados en el orden original."""
    p = np.asarray(p, dtype=float)
    m = len(p)
    ajustado = np.empty(m)
    previo = 0.0
    for rango, i in enumerate(np.argsort(p, kind="stable")):
        previo = max(previo, min(1.0, (m - rango) * p[i]))
        ajustado[i] = previo
    return ajustado.tolist()


def p_permutacion(obs: float, nulos, alternativa: str = "mayor") -> float:
    """(1 + #{T* >= T_obs}) / (1 + B); ``dos_colas`` compara |T*| con |T_obs|; tolera 1e-12 en los empates numéricos."""
    nulos = np.asarray(nulos, dtype=float)
    tol = TOLERANCIA_NUMERICA * max(1.0, abs(obs))
    if alternativa == "mayor":
        k = int((nulos >= obs - tol).sum())
    elif alternativa == "dos_colas":
        k = int((np.abs(nulos) >= abs(obs) - tol).sum())
    else:
        raise ValueError(f"alternativa desconocida: {alternativa!r}")
    return (1 + k) / (1 + len(nulos))


def delta_de_cliff(a, b):
    """Delta de Cliff y probabilidad de superioridad de ``a`` sobre ``b`` desde los conteos por categoría ordenada.

    delta = (#{a > b} − #{a < b}) / (n_a·n_b);
    prob. de superioridad = (#{a > b} + ½·#{a = b}) / (n_a·n_b) = (delta + 1)/2.
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
    """``n_sim`` repartos multinomiales uniformes de ``n_interacciones`` entre ``n_entidades``: (n_sim, n_entidades)."""
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


def v_corregida_por_lotes(tablas: np.ndarray) -> np.ndarray:
    """V de Cramér con corrección de sesgo (la V ordinaria es positiva sin asociación y su bootstrap queda por encima).

    φ² = χ²/n;  φ̃² = max(0, φ² − (r−1)(c−1)/(n−1));  r̃ = r − (r−1)²/(n−1);  c̃ = c − (c−1)²/(n−1);
    V corregida = sqrt(φ̃² / min(r̃−1, c̃−1)).
    TODO(cita): Bergsma (2013), doi 10.1016/j.jkss.2012.10.002 — verificar con la fuente primaria en JJ-9"""
    t = np.asarray(tablas, dtype=float)
    n = t.sum(axis=(1, 2))
    r, c = t.shape[1:]
    phi2 = np.maximum(0.0, chi2_por_lotes(t) / n - (r - 1) * (c - 1) / (n - 1))
    r_c, c_c = r - (r - 1) ** 2 / (n - 1), c - (c - 1) ** 2 / (n - 1)
    return np.sqrt(phi2 / np.minimum(r_c - 1, c_c - 1))


def residuos_estandarizados(tabla) -> np.ndarray:
    """Residuos estandarizados ajustados de una tabla: (O − E) / sqrt(E·(1 − fila/n)·(1 − columna/n))."""
    t = np.asarray(tabla, dtype=float)
    n = t.sum()
    f, c = t.sum(axis=1, keepdims=True), t.sum(axis=0, keepdims=True)
    esperado = f * c / n
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(esperado > 0, (t - esperado) / np.sqrt(esperado * (1 - f / n) * (1 - c / n)), 0.0)


def residuos_de_pearson(tabla) -> np.ndarray:
    """Residuos de Pearson de una tabla de contingencia: (O − E) / sqrt(E) (su cuadrado suma el χ²)."""
    t = np.asarray(tabla, dtype=float)
    esperado = t.sum(axis=1, keepdims=True) * t.sum(axis=0, keepdims=True) / t.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(esperado > 0, (t - esperado) / np.sqrt(esperado), 0.0)


def aporte_al_chi2(tabla, mascara) -> tuple[float, float]:
    """Parte del χ² (suma de (O − E)²/E) que aportan las celdas de ``mascara`` y la que aportan las demás."""
    t = np.asarray(tabla, dtype=float)
    esperado = t.sum(axis=1, keepdims=True) * t.sum(axis=0, keepdims=True) / t.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        aporte = np.where(esperado > 0, (t - esperado) ** 2 / esperado, 0.0)
    m = np.asarray(mascara, dtype=bool)
    return float(aporte[m].sum()), float(aporte[~m].sum())


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


def _tablas_de_grupos(pesos: np.ndarray, conteos: np.ndarray, grupos: np.ndarray, n_grupos: int) -> np.ndarray:
    """Tablas (lote, grupos, columnas): suma ponderada de ``conteos`` (unidades × columnas) por grupo de unidades.

    ``grupos`` es fijo; ``pesos`` (lote × unidades) cambia por réplica."""
    return np.stack([pesos[:, grupos == g] @ conteos[grupos == g] for g in range(n_grupos)], axis=1)


def _tablas_permutadas(etiquetas: np.ndarray, conteos32: np.ndarray, n_grupos: int) -> np.ndarray:
    """Tablas (lote, grupos, columnas) si las etiquetas de grupo son las permutadas ``etiquetas``."""
    return np.stack([(etiquetas == g).astype(np.float32) @ conteos32 for g in range(n_grupos)], axis=1).astype(float)


def _ic(x: np.ndarray, nivel: float) -> list[float]:
    lo, hi = _cuantiles(x, nivel)
    return [float(lo), float(hi)]


# =========================================================================== ajuste por multiplicidad
AJUSTES_MULTIPLES = {"holm": holm}


def ajustar_multiplicidad(p, metodo: str) -> list[float]:
    """p ajustados de la familia ``p`` con el método de la config (hoy solo ``holm``); otro valor es un error claro."""
    if metodo not in AJUSTES_MULTIPLES:
        raise ValueError(f"ajuste_multiple {metodo!r} no está soportado; los posibles son {sorted(AJUSTES_MULTIPLES)}")
    return AJUSTES_MULTIPLES[metodo](p)
