"""M3 — métricas @K, desempate al azar y valores esperados del recomendador aleatorio (JJ-4; D10, D12).

Notación. Para el usuario u: C_u = candidatos (D10: catálogo menos el historial conocido), R_u ⊂ C_u = relevantes (en prueba
y validación |R_u| = 1, D3), L_u^K = top-K recomendado (lista ordenada, sin repetidos, L_u^K ⊂ C_u), r = posición 1-indexada
en la lista, N_u = |C_u| y n = tamaño del catálogo.

Con |R_u| = 1 (D12): Recall@K = acierto@K y Precision@K = acierto@K / K. Siguen siendo tres métricas porque las fórmulas
generales (con |R_u| >= 1) son las del enunciado y así el módulo no cambia si algún día hay más de un relevante.

Todas las funciones son puras. Toda aleatoriedad llega por un ``np.random.Generator`` recibido (``make_rng`` en el arnés);
nunca se usa ``np.random.seed``. Este módulo no lee archivos ni estadísticas de las interacciones.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np

from src.comun.seeds import validar_entero
from src.m3_recomendacion.eda_estadistica import gini, hhi


# --------------------------------------------------------------------------- validaciones
def _k(k) -> int:
    return validar_entero(k, "K", minimo=1)


def _lista(top, k: int) -> list[int]:
    """Los primeros K elementos de la lista como enteros (si hay menos de K, los que haya)."""
    return [int(x) for x in list(top)[:k]]


def _ids(top, k: int) -> list[int]:
    """Los primeros K ids de una lista de ids o de un par (ids, puntajes) como el de ``rankear_usuarios``."""
    return _lista(top[0] if isinstance(top, tuple) else top, k)


def _posiciones(cat: np.ndarray, sorter: np.ndarray, ids, que: str) -> np.ndarray:
    """Posición en ``cat`` de cada id (``sorter`` = ``np.argsort(cat)``); ValueError si alguno no está en el catálogo."""
    ids = np.asarray(ids, dtype="int64")
    pos = sorter[np.minimum(np.searchsorted(cat, ids, sorter=sorter), len(cat) - 1)]
    if not np.array_equal(cat[pos], ids):
        raise ValueError(f"{que}: hay destinos que no están en el catálogo")
    return pos


# --------------------------------------------------------------------------- desempate al azar y orden
def _orden(puntajes: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Posiciones ordenadas por puntaje descendente; los empates se rompen al azar con ``rng``.

    Se permuta uniformemente 0…N−1 y luego se ordena de forma estable por −puntaje: entre los empatados queda primero el que
    la permutación puso antes, y la permutación es uniforme, así que cada orden entre empatados es igualmente probable.
    Misma semilla → mismo orden; ningún candidato se pierde ni se repite.
    """
    p = np.asarray(puntajes, dtype=float)
    if p.ndim != 1:
        raise ValueError(f"los puntajes de un usuario deben ser un vector; forma {p.shape}")
    if not np.isfinite(p).all():
        raise ValueError("los puntajes deben ser finitos (sin NaN ni inf)")
    perm = rng.permutation(len(p))
    return perm[np.argsort(-p[perm], kind="stable")]


def ordenar_candidatos_con_puntajes(puntajes, candidatos, k: int, rng: np.random.Generator):
    """(ids, puntajes) de los k candidatos de mayor puntaje, en orden descendente, con desempate al azar (ver ``_orden``).

    ``puntajes[j]`` es el puntaje de ``candidatos[j]``. Si k > N_u se devuelven los N_u candidatos.
    """
    k = _k(k)
    p = np.asarray(puntajes, dtype=float)
    c = np.asarray(candidatos, dtype="int64")
    if p.shape != c.shape:
        raise ValueError(f"puntajes {p.shape} y candidatos {c.shape} deben tener la misma longitud")
    idx = _orden(p, rng)[:k]
    return c[idx], p[idx]


def ordenar_candidatos(puntajes, candidatos, k: int, rng: np.random.Generator) -> np.ndarray:
    """Top-k de ``candidatos`` por puntaje descendente; los empates se rompen al azar con ``rng``. Común a todos los modelos."""
    return ordenar_candidatos_con_puntajes(puntajes, candidatos, k, rng)[0]


def rankear_usuarios(puntajes: np.ndarray, usuario_ids, catalogo, cands: Mapping[int, np.ndarray], k: int,
                     rng: np.random.Generator) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Top-k de cada usuario: {usuario_id: (ids, puntajes)}.

    ``puntajes`` es (n_usuarios, n_catalogo) con la fila i ↔ ``usuario_ids[i]`` y las columnas en el orden de ``catalogo``;
    ``cands[u]`` son los candidatos del usuario (D10). Los usuarios se recorren en el orden recibido (el consumo del azar es
    determinista).
    """
    puntajes = np.asarray(puntajes, dtype=float)
    cat = np.asarray(catalogo, dtype="int64")
    usuarios = [int(u) for u in usuario_ids]
    if puntajes.shape != (len(usuarios), len(cat)):
        raise ValueError(f"puntajes {puntajes.shape} ≠ (n_usuarios, n_catalogo) = {(len(usuarios), len(cat))}")
    sorter = np.argsort(cat)
    out = {}
    for i, u in enumerate(usuarios):
        c = np.asarray(cands[u], dtype="int64")
        pos = _posiciones(cat, sorter, c, f"candidatos del usuario {u}")
        out[u] = ordenar_candidatos_con_puntajes(puntajes[i, pos], c, k, rng)
    return out


def normalizar_k(valor, nombre: str = "evaluacion.k") -> list[int]:
    """Lista ascendente y sin repetidos de K a partir de un entero o una lista de enteros >= 1 (``--set evaluacion.k=3`` o
    ``--set "evaluacion.k=[1, 3]"``). Error claro si está vacía o algún valor no es un entero >= 1."""
    valores = [valor] if isinstance(valor, (int, np.integer)) and not isinstance(valor, bool) else valor
    if not isinstance(valores, (list, tuple)) or len(valores) == 0:
        raise ValueError(f"{nombre} debe ser un entero >= 1 o una lista no vacía de enteros >= 1; se recibió {valor!r}")
    return sorted({validar_entero(v, nombre, minimo=1) for v in valores})


# --------------------------------------------------------------------------- métricas por usuario
def acierto_en_k(top, relevantes, k: int) -> int:
    """acierto@K = 1[|L ∩ R| > 0] (1 si algún relevante está en los K primeros, si no 0)."""
    k = _k(k)
    return int(len(set(_lista(top, k)) & {int(r) for r in relevantes}) > 0)


def precision_en_k(top, relevantes, k: int) -> float:
    """Precision@K = |L ∩ R| / K (K nominal, aunque la lista tenga menos de K elementos). Con |R| = 1: acierto@K / K."""
    k = _k(k)
    return len(set(_lista(top, k)) & {int(r) for r in relevantes}) / k


def recall_en_k(top, relevantes, k: int) -> float:
    """Recall@K = |L ∩ R| / |R|. Con |R| = 1: igual a acierto@K (D12)."""
    k = _k(k)
    rel = {int(r) for r in relevantes}
    if not rel:
        raise ValueError("Recall@K no está definido sin relevantes (|R| = 0)")
    return len(set(_lista(top, k)) & rel) / len(rel)


def ndcg_en_k(top, relevantes, k: int) -> float:
    """NDCG@K binario = DCG / IDCG, con DCG = Σ_{r=1}^{K} 1[L(r) ∈ R] / log2(r + 1) e IDCG = Σ_{r=1}^{min(|R|,K)} 1/log2(r + 1).

    Con un relevante: 1/log2(r + 1) si su rango r ≤ K, si no 0 (IDCG = 1)."""
    k = _k(k)
    rel = {int(r) for r in relevantes}
    if not rel:
        raise ValueError("NDCG@K no está definido sin relevantes (|R| = 0)")
    dcg = sum(1.0 / math.log2(r + 1) for r, d in enumerate(_lista(top, k), start=1) if d in rel)
    idcg = sum(1.0 / math.log2(r + 1) for r in range(1, min(len(rel), k) + 1))
    return dcg / idcg


def acierto_por_lugar_en_k(top, objetivo, lugar_de: Mapping[int, str], k: int) -> int:
    """1[∃ i ∈ L^K : lugar(i) = lugar(objetivo)] (con varios objetivos: el lugar de cualquiera de ellos).

    Solo para K ∈ ``evaluacion.k_lugar`` y siempre junto a su línea base del azar (``esperado_acierto_lugar``)."""
    k = _k(k)
    lugares_objetivo = np.array([lugar_de[int(r)] for r in objetivo], dtype=str)
    lugares_lista = np.array([lugar_de[d] for d in _lista(top, k)], dtype=str)
    return int(np.isin(lugares_lista, lugares_objetivo).any())


def metricas_por_usuario(tops: Mapping[int, tuple], relevantes: Mapping[int, set], lugar_de: Mapping[int, str],
                         ks: Sequence[int], k_lugar: Sequence[int]) -> dict:
    """Métricas de cada usuario de ``tops`` ({u: (ids, puntajes)}), en el orden ascendente de ``usuarios``.

    Devuelve ``{"usuarios": array, "acierto"|"precision"|"recall"|"ndcg": {K: array}, "lugar": {K: array}}`` (``lugar`` solo
    para K ∈ ``k_lugar`` que también estén en ``ks``)."""
    usuarios = np.array(sorted(tops), dtype="int64")
    out: dict = {"usuarios": usuarios, "acierto": {}, "precision": {}, "recall": {}, "ndcg": {}, "lugar": {}}
    funciones = {"acierto": acierto_en_k, "precision": precision_en_k, "recall": recall_en_k, "ndcg": ndcg_en_k}
    for k in ks:
        for nombre, f in funciones.items():
            out[nombre][k] = np.array([f(tops[int(u)][0], relevantes[int(u)], k) for u in usuarios], dtype=float)
    for k in k_lugar:
        if k in ks:
            out["lugar"][k] = np.array([acierto_por_lugar_en_k(tops[int(u)][0], relevantes[int(u)], lugar_de, k)
                                        for u in usuarios], dtype=float)
    return out


# --------------------------------------------------------------------------- cobertura y concentración
def exposiciones(tops: Mapping[int, Sequence[int]], catalogo, k: int) -> np.ndarray:
    """e_i = #{u : i ∈ L_u^K} para cada destino del catálogo, en el orden de ``catalogo`` (0 si nunca aparece).

    Acepta listas de ids o pares (ids, puntajes) como los de ``rankear_usuarios``."""
    k = _k(k)
    cat = np.asarray(catalogo, dtype="int64")
    pos = {int(d): j for j, d in enumerate(cat)}
    e = np.zeros(len(cat), dtype="int64")
    for u, top in tops.items():
        ids = _ids(top, k)
        if len(set(ids)) != len(ids):
            raise ValueError(f"la lista del usuario {u} repite destinos: {ids}")
        for d in ids:
            if d not in pos:
                raise ValueError(f"el destino {d} (usuario {u}) no está en el catálogo")
            e[pos[d]] += 1
    return e


def cobertura(tops: Mapping[int, Sequence[int]], n_catalogo: int, k: int) -> float:
    """cobertura@K = |∪_u L_u^K| / |catálogo| (D12: / 1 000 en los datos reales)."""
    k = _k(k)
    visto: set[int] = set()
    for top in tops.values():
        visto.update(_ids(top, k))
    return len(visto) / validar_entero(n_catalogo, "n_catalogo", minimo=1)


def gini_exposiciones(e) -> float:
    """Gini sin corrección de las exposiciones: 2·Σ i·e_(i) / (n·Σe) − (n+1)/n (misma definición que el descriptivo de JJ-2,
    ``eda_estadistica.gini``), sobre los n destinos del catálogo, incluidos los de exposición 0."""
    return float(gini(np.asarray(e, dtype=float)))


def hhi_exposiciones(e) -> float:
    """HHI de las exposiciones: Σ s_i², s_i = e_i/Σe (``eda_estadistica.hhi``), sobre los n destinos del catálogo."""
    return float(hhi(np.asarray(e, dtype=float)))


# --------------------------------------------------------------------------- resúmenes entre semillas
def resumir_semillas(valores) -> dict:
    """{media, desviacion, mejor, peor, n} de una métrica sobre las semillas.

    La desviación es muestral (ddof = 1; ``None`` si hay una sola semilla). Todas las métricas de acierto son «mayor es
    mejor»: mejor = máximo y peor = mínimo."""
    v = np.asarray(valores, dtype=float)
    if v.ndim != 1 or len(v) == 0:
        raise ValueError("resumir_semillas necesita un vector no vacío")
    return {"media": float(v.mean()), "desviacion": float(v.std(ddof=1)) if len(v) > 1 else None,
            "mejor": float(v.max()), "peor": float(v.min()), "n": int(len(v))}


def resumir_concentracion(valores) -> dict:
    """{media, desviacion, minimo, maximo, n} para Gini y HHI, que no tienen una dirección de «mejor» (desviación ddof = 1)."""
    r = resumir_semillas(valores)
    return {"media": r["media"], "desviacion": r["desviacion"], "minimo": r["peor"], "maximo": r["mejor"], "n": r["n"]}


# --------------------------------------------------------------------------- esperados del recomendador aleatorio
# El aleatorio recomienda un subconjunto uniforme de min(K, N_u) candidatos, ordenado al azar. Sea K' = min(K, N_u).
def _n_candidatos(n_cand) -> int:
    """N_u >= 1: sin candidatos no hay esperado (dividiría por 0)."""
    return validar_entero(n_cand, "N_u (número de candidatos)", minimo=1)


def esperado_acierto(n_cand: int, k: int, n_rel: int = 1) -> float:
    """E[acierto@K] = 1 − C(N − |R|, K') / C(N, K'); con |R| = 1 es K'/N con K' = min(K, N). Exige 1 <= |R| <= N."""
    n_cand = _n_candidatos(n_cand)
    if not 1 <= n_rel <= n_cand:
        raise ValueError(f"|R| debe estar entre 1 y N_u = {n_cand}; se recibió {n_rel}")
    k = min(_k(k), n_cand)
    return 1.0 - math.comb(n_cand - n_rel, k) / math.comb(n_cand, k)


def esperado_precision(n_cand: int, k: int, n_rel: int = 1) -> float:
    """E[Precision@K] = |R|·K'/(N·K); con |R| = 1 es E[acierto@K]/K."""
    n_cand, k_nominal = _n_candidatos(n_cand), _k(k)
    return n_rel * min(k_nominal, n_cand) / n_cand / k_nominal


def esperado_recall(n_cand: int, k: int, n_rel: int = 1) -> float:
    """E[Recall@K] = E|L ∩ R| / |R| = K'/N (con |R| = 1 coincide con E[acierto@K])."""
    n_cand = _n_candidatos(n_cand)
    return min(_k(k), n_cand) / n_cand


def esperado_ndcg(n_cand: int, k: int) -> float:
    """E[NDCG@K] = (1/N)·Σ_{r=1}^{K'} 1/log2(r + 1) (un relevante: está en cada rango con probabilidad 1/N)."""
    n_cand = _n_candidatos(n_cand)
    k = min(_k(k), n_cand)
    return sum(1.0 / math.log2(r + 1) for r in range(1, k + 1)) / n_cand


def esperado_acierto_lugar(n_cand: int, n_mismo_lugar: int, k: int) -> float:
    """E[acierto por lugar@K] = 1 − C(N − m, K')/C(N, K'), con m = #{i ∈ C_u : lugar(i) = lugar(objetivo)} (incluye al
    objetivo). Es la línea base del azar que se reporta junto a CADA modelo. Exige 0 <= m <= N."""
    n_cand = _n_candidatos(n_cand)
    if not 0 <= n_mismo_lugar <= n_cand:
        raise ValueError(f"m debe estar entre 0 y N_u = {n_cand}; se recibió {n_mismo_lugar}")
    k = min(_k(k), n_cand)
    return 1.0 - math.comb(n_cand - n_mismo_lugar, k) / math.comb(n_cand, k)


def esperado_cobertura(cands: Sequence[np.ndarray], catalogo, k: int) -> float:
    """E[cobertura@K] = (1/n)·Σ_i [1 − Π_{u : i ∈ C_u} (1 − K'_u/N_u)], con K'_u = min(K, N_u) (independencia entre usuarios:
    exacta para el aleatorio, cuyos usuarios sortean por separado). Si K'_u = N_u todo el catálogo de u se recomienda."""
    k = _k(k)
    cat = np.asarray(catalogo, dtype="int64")
    sorter = np.argsort(cat)
    log_no = np.zeros(len(cat))          # Σ_u log(1 − p_u) sobre los usuarios que pueden recibir i (con p_u < 1)
    seguro = np.zeros(len(cat), dtype=bool)
    for c in cands:
        c = np.asarray(c, dtype="int64")
        p = min(k, _n_candidatos(len(c))) / len(c)
        pos = _posiciones(cat, sorter, c, "esperado_cobertura")
        if p >= 1.0:
            seguro[pos] = True
        else:
            log_no[pos] += math.log1p(-p)
    prob = np.where(seguro, 1.0, -np.expm1(log_no))
    return float(prob.mean())


def _candidatos_del_lugar_objetivo(cands, relevantes, lugar_de, catalogo, usuarios) -> dict[int, int]:
    """m_u = #{i ∈ C_u : lugar(i) = lugar(objetivo_u)} (incluye al objetivo), por usuario."""
    cat = np.asarray(catalogo, dtype="int64")
    sorter = np.argsort(cat)
    lugar_cat = np.array([lugar_de[int(i)] for i in cat], dtype=str)
    out = {}
    for u in usuarios:
        lugares_objetivo = lugar_cat[_posiciones(cat, sorter, sorted(relevantes[u]), f"relevantes del usuario {u}")]
        lugares_candidatos = lugar_cat[_posiciones(cat, sorter, cands[u], f"candidatos del usuario {u}")]
        out[u] = int(np.isin(lugares_candidatos, lugares_objetivo).sum())
    return out


def esperados_aleatorio(cands: Mapping[int, np.ndarray], relevantes: Mapping[int, set], lugar_de: Mapping[int, str], catalogo,
                        ks: Sequence[int], k_lugar: Sequence[int], usuarios: Sequence[int] | None = None) -> dict[str, float]:
    """Esperados del aleatorio promediados sobre ``usuarios`` (por defecto todos los de ``cands``).

    Claves ``"acierto@K"``, ``"precision@K"``, ``"recall@K"``, ``"ndcg@K"``, ``"cobertura@K"`` y, para K ∈ ``k_lugar``
    que también estén en ``ks``, ``"acierto_por_lugar@K"``. NDCG y los demás suponen |R_u| = 1 (D3)."""
    us = sorted(cands) if usuarios is None else sorted(int(u) for u in usuarios)
    if not us:
        raise ValueError("esperados_aleatorio: no hay usuarios")
    for u in us:
        if len(relevantes[u]) != 1:
            raise ValueError(f"usuario {u}: los esperados analíticos suponen un relevante por usuario (D3)")
        if len(cands[u]) < 1:
            raise ValueError(f"usuario {u}: no tiene candidatos (N_u = 0); no hay esperado analítico")
    out: dict[str, float] = {}
    n = {u: len(cands[u]) for u in us}
    m = _candidatos_del_lugar_objetivo(cands, relevantes, lugar_de, catalogo, us)
    for k in ks:
        out[f"acierto@{k}"] = float(np.mean([esperado_acierto(n[u], k) for u in us]))
        out[f"precision@{k}"] = float(np.mean([esperado_precision(n[u], k) for u in us]))
        out[f"recall@{k}"] = float(np.mean([esperado_recall(n[u], k) for u in us]))
        out[f"ndcg@{k}"] = float(np.mean([esperado_ndcg(n[u], k) for u in us]))
        out[f"cobertura@{k}"] = esperado_cobertura([cands[u] for u in us], catalogo, k)
    for k in k_lugar:
        if k in ks:
            out[f"acierto_por_lugar@{k}"] = float(np.mean([esperado_acierto_lugar(n[u], m[u], k) for u in us]))
    return out
