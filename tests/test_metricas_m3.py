"""Pruebas sin red de las métricas @K, los modelos de referencia y el arnés de M3 (JJ-4; núcleo §5.9, §6, §8).

Todo con datos ficticios armados aquí (``tmp_path``); ninguna prueba lee ``data/raw`` ni usa los parquet reales.

Definiciones que estas pruebas FIJAN (D12, docs/spec/partes/juanjose.md §3.3). Para el usuario u: C_u = candidatos, R_u =
relevantes, L = top-K recomendado (lista ordenada sin repetidos), rango r = posición 1-indexada.
  acierto@K   = 1[|L ∩ R| > 0]          precision@K = |L ∩ R| / K          recall@K = |L ∩ R| / |R|
  NDCG@K      = DCG / IDCG, DCG = Σ_{r=1..K} 1[L(r) ∈ R] / log2(r+1), IDCG = Σ_{r=1..min(|R|,K)} 1 / log2(r+1)

Cálculos a mano con K = 3 y R = {7}:
  top [7, 1, 2]  → acierto 1, precision 1/3, recall 1, NDCG 1/log2(2) = 1
  top [1, 7, 2]  → NDCG 1/log2(3) = 0,63093
  top [1, 2, 7]  → NDCG 1/log2(4) = 0,5
  top [1, 2, 3]  → todo 0 (usuario sin acierto);  con K = 2 y top [1, 2, 7]: 7 queda fuera del top-2 → 0
Cálculo a mano con |R| = 2, R = {7, 9}, top [7, 1, 9, 2]:
  K = 4: DCG = 1 + 1/log2(4) = 1,5; IDCG = 1 + 1/log2(3) = 1,63093; NDCG = 0,91972; precision 2/4; recall 2/2
  K = 2: DCG = 1; IDCG = 1 + 1/log2(3); NDCG = 0,61315; precision 1/2; recall 1/2
  K = 1: DCG = 1; IDCG = 1 (min(|R|, K) = 1); NDCG = 1
Exposiciones: 3 usuarios, catálogo {1..5}, top-2 de a = [1, 2], de b = [2, 3], de c = [2, 1]:
  e = [2, 3, 1, 0, 0]; cobertura = 3/5; Σ i·e_(i) con e ordenado [0, 0, 1, 2, 3] = 3·1 + 4·2 + 5·3 = 26
  Gini = 2·26/(5·6) − 6/5 = 0,53333; HHI = (2² + 3² + 1²)/6² = 14/36 = 0,38889
  con K = 1: e = [1, 2, 0, 0, 0]
Esperados del aleatorio (top-K uniforme sin reemplazo en C_u, N = |C_u|):
  N = 10, K = 3: acierto 0,3; precision 0,1; NDCG = (1 + 1/log2(3) + 1/2)/10; por lugar con m = 4 → 1 − C(6,3)/C(10,3) = 5/6
  cobertura con catálogo {1..4}, C_1 = {1,2,3,4} (N = 4), C_2 = {1,2} (N = 2):
    K = 1: p1 = 1/4, p2 = 1/2: ítems 1 y 2 → 1 − (3/4)(1/2) = 5/8; ítems 3 y 4 → 1 − 3/4 = 1/4; (2·5/8 + 2·1/4)/4 = 0,4375
    K = 2: p2 = min(2, 2)/2 = 1: ítems 1 y 2 → 1; ítems 3 y 4 → 1 − 1/2 = 1/2; (2 + 1)/4 = 0,75
"""
from __future__ import annotations

import hashlib
import math
import socket
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.comun.config import apply_overrides, load_config
from src.comun.results import load_json
from src.comun.seeds import make_rng
from src.m3_recomendacion import experimento, hpo, metricas, particion, referencias
from test_fuga_m3 import _alterar_no_train, catalogo, tabla

RAIZ = Path(__file__).resolve().parents[1]
CFG_BASE = RAIZ / "configs" / "m3" / "base.yaml"
CFG_HPO = RAIZ / "configs" / "m3" / "hpo.yaml"
CFG_DEMO = RAIZ / "configs" / "m3" / "demo.yaml"
CFG_DATOS = RAIZ / "configs" / "m3" / "datos.yaml"
LOG2_3 = math.log2(3)


# =========================================================================== C1.1 métricas por usuario a mano
@pytest.mark.parametrize("top, k, acierto, ndcg", [
    ([7, 1, 2], 3, 1, 1.0),
    ([1, 7, 2], 3, 1, 1 / LOG2_3),
    ([1, 2, 7], 3, 1, 0.5),
    ([1, 2, 3], 3, 0, 0.0),          # usuario sin acierto
    ([1, 2, 7], 2, 0, 0.0),          # el relevante cae fuera del top-K
    ([7, 1, 2], 1, 1, 1.0),
])
def test_metricas_con_un_relevante_a_mano(top, k, acierto, ndcg):
    rel = {7}
    assert metricas.acierto_en_k(top, rel, k) == acierto
    assert metricas.precision_en_k(top, rel, k) == pytest.approx(acierto / k)
    assert metricas.recall_en_k(top, rel, k) == acierto        # con |R| = 1: Recall@K = acierto@K (D12)
    assert metricas.ndcg_en_k(top, rel, k) == pytest.approx(ndcg)


@pytest.mark.parametrize("k, precision, recall, ndcg", [
    (4, 2 / 4, 1.0, 1.5 / (1 + 1 / LOG2_3)),
    (2, 1 / 2, 1 / 2, 1.0 / (1 + 1 / LOG2_3)),
    (1, 1.0, 1 / 2, 1.0),
])
def test_ndcg_con_dos_relevantes_fija_el_idcg(k, precision, recall, ndcg):
    top, rel = [7, 1, 9, 2], {7, 9}
    assert metricas.precision_en_k(top, rel, k) == pytest.approx(precision)
    assert metricas.recall_en_k(top, rel, k) == pytest.approx(recall)
    assert metricas.ndcg_en_k(top, rel, k) == pytest.approx(ndcg)
    assert metricas.acierto_en_k(top, rel, k) == 1


def test_la_lista_mas_corta_que_k_no_rompe_y_precision_divide_por_k():
    assert metricas.precision_en_k([7], {7}, 5) == pytest.approx(1 / 5)
    assert metricas.ndcg_en_k([7], {7}, 5) == pytest.approx(1.0)
    assert metricas.acierto_en_k([], {7}, 3) == 0


def test_k_invalido_es_un_error_claro():
    for k in (0, -1, 2.5, True):
        with pytest.raises((TypeError, ValueError)):
            metricas.acierto_en_k([1], {1}, k)


# =========================================================================== empates (ordenar_candidatos)
def test_empates_se_rompen_al_azar_de_forma_determinista():
    cands = np.array([10, 11, 12, 13, 14])
    puntajes = np.array([1.0, 1.0, 1.0, 1.0, 0.0])
    mismo = [list(metricas.ordenar_candidatos(puntajes, cands, 2, make_rng(5, 0))) for _ in range(2)]
    assert mismo[0] == mismo[1]                                  # misma semilla → mismo desempate
    vistos = set()
    for s in range(40):
        top = list(metricas.ordenar_candidatos(puntajes, cands, 2, make_rng(5, s)))
        assert len(top) == len(set(top)) == 2 and set(top) <= {10, 11, 12, 13}
        vistos.add(tuple(top))
    assert len(vistos) > 1                                        # otra semilla cambia el desempate
    assert {x for t in vistos for x in t} == {10, 11, 12, 13}     # y los cuatro empatados pueden salir (azar, no sesgo)


def test_ningun_candidato_se_pierde_ni_se_repite_y_el_orden_respeta_el_puntaje():
    cands = np.array([10, 11, 12, 13, 14])
    puntajes = np.array([1.0, 1.0, 1.0, 1.0, 0.0])
    for s in range(20):
        todo = list(metricas.ordenar_candidatos(puntajes, cands, 5, make_rng(1, s)))
        assert sorted(todo) == [10, 11, 12, 13, 14] and todo[-1] == 14      # el de menor puntaje queda al final
    top, p = metricas.ordenar_candidatos_con_puntajes(np.array([0.2, 0.9, 0.5]), np.array([3, 4, 5]), 2, make_rng(0, 0))
    assert list(top) == [4, 5] and list(p) == [0.9, 0.5]
    # k mayor que el número de candidatos: se devuelven todos
    assert len(metricas.ordenar_candidatos(np.array([1.0, 2.0]), np.array([1, 2]), 10, make_rng(0, 0))) == 2


def test_ordenar_rechaza_puntajes_no_finitos_y_longitudes_distintas():
    with pytest.raises(ValueError):
        metricas.ordenar_candidatos(np.array([1.0, np.nan]), np.array([1, 2]), 1, make_rng(0, 0))
    with pytest.raises(ValueError):
        metricas.ordenar_candidatos(np.array([1.0]), np.array([1, 2]), 1, make_rng(0, 0))


# =========================================================================== C1.2 cobertura, exposiciones, Gini y HHI
TOPS = {1: [1, 2], 2: [2, 3], 3: [2, 1]}
CAT5 = [1, 2, 3, 4, 5]


def test_exposiciones_cobertura_gini_hhi_a_mano():
    e = metricas.exposiciones(TOPS, CAT5, 2)
    assert list(e) == [2, 3, 1, 0, 0]
    assert metricas.cobertura(TOPS, 5, 2) == pytest.approx(3 / 5)
    assert metricas.gini_exposiciones(e) == pytest.approx(2 * 26 / (5 * 6) - 6 / 5)
    assert metricas.hhi_exposiciones(e) == pytest.approx(14 / 36)
    e1 = metricas.exposiciones(TOPS, CAT5, 1)                   # solo el primero de cada lista
    assert list(e1) == [1, 2, 0, 0, 0]
    assert metricas.cobertura(TOPS, 5, 1) == pytest.approx(2 / 5)


def test_exposiciones_respeta_el_orden_del_catalogo_y_valida_ids():
    assert list(metricas.exposiciones({1: [30]}, [30, 20, 10], 1)) == [1, 0, 0]
    with pytest.raises(ValueError):
        metricas.exposiciones({1: [99]}, CAT5, 1)               # destino fuera del catálogo
    with pytest.raises(ValueError):
        metricas.exposiciones({1: [1, 1]}, CAT5, 2)             # destino repetido en una lista


def test_acierto_por_lugar_a_mano():
    lugar = {1: "A", 2: "A", 3: "B", 4: "B", 5: "C"}
    top, objetivo = [1, 3, 2], {4}                              # el objetivo es de B
    assert metricas.acierto_por_lugar_en_k(top, objetivo, lugar, 1) == 0     # solo el 1 (lugar A)
    assert metricas.acierto_por_lugar_en_k(top, objetivo, lugar, 2) == 1     # el 3 es de B
    assert metricas.acierto_por_lugar_en_k(top, objetivo, lugar, 3) == 1


# =========================================================================== resúmenes entre semillas
def test_resumir_semillas_usa_desviacion_muestral():
    r = metricas.resumir_semillas([1.0, 2.0, 3.0, 4.0])
    assert r["media"] == pytest.approx(2.5) and r["desviacion"] == pytest.approx(math.sqrt(5 / 3))   # ddof = 1
    assert r["mejor"] == 4.0 and r["peor"] == 1.0 and r["n"] == 4
    assert metricas.resumir_semillas([0.5])["desviacion"] is None        # una sola semilla: sin desviación muestral
    c = metricas.resumir_concentracion([0.2, 0.4, 0.6])
    assert c["media"] == pytest.approx(0.4) and c["minimo"] == 0.2 and c["maximo"] == 0.6 and "mejor" not in c
    with pytest.raises(ValueError):
        metricas.resumir_semillas([])


# =========================================================================== C1.3 esperados analíticos del aleatorio
def test_esperados_analiticos_a_mano():
    assert metricas.esperado_acierto(10, 3) == pytest.approx(0.3)
    assert metricas.esperado_precision(10, 3) == pytest.approx(0.1)
    assert metricas.esperado_recall(10, 3) == pytest.approx(0.3)
    assert metricas.esperado_ndcg(10, 3) == pytest.approx((1 + 1 / LOG2_3 + 0.5) / 10)
    assert metricas.esperado_acierto_lugar(10, 4, 3) == pytest.approx(5 / 6)
    assert metricas.esperado_acierto(2, 5) == pytest.approx(1.0)                 # K > N: min(K, N)/N
    assert metricas.esperado_acierto_lugar(10, 10, 1) == pytest.approx(1.0)      # todos los candidatos son del lugar
    assert metricas.esperado_acierto_lugar(1000, 200, 10) == pytest.approx(
        1 - math.comb(800, 10) / math.comb(1000, 10))


def test_esperado_de_cobertura_a_mano():
    cands = [np.array([1, 2, 3, 4]), np.array([1, 2])]
    assert metricas.esperado_cobertura(cands, [1, 2, 3, 4], 1) == pytest.approx(0.4375)
    assert metricas.esperado_cobertura(cands, [1, 2, 3, 4], 2) == pytest.approx(0.75)    # rama p = 1


def _escenario_aleatorio():
    """12 usuarios con 30 destinos y historiales de tamaño distinto (candidatos de 24 a 30); lugar = id mod 5."""
    cat = np.arange(1, 31)
    cands, rel = {}, {}
    for j in range(12):
        u = 100 + j
        vistos = set(range(1, 1 + 2 * (j % 4) + (j % 3)))
        objetivo = 30 - j
        vistos.discard(objetivo)
        cands[u] = np.array([i for i in cat if i not in vistos])
        rel[u] = {objetivo}
    return cat, cands, rel, {int(i): f"L{i % 5}" for i in cat}


def test_aleatorio_simulado_coincide_con_su_esperado_analitico():
    """2 000 réplicas del Aleatorio completo (puntajes → desempate → métricas). Para cada métrica la media simulada difiere
    del esperado analítico en menos de 5 errores estándar (se = desviación de las réplicas / √2000, calculado de la propia
    simulación): con ≈ 10 comparaciones la probabilidad de un falso rechazo es ≈ 6e-6; una fórmula mal escrita (otro
    denominador, otro descuento) se desvía muchos errores estándar. Semilla fija."""
    cat, cands, rel, lugar = _escenario_aleatorio()
    usuarios = sorted(cands)
    ks, k_lugar, reps = [1, 3, 5], [1, 3], 2000
    esperado = metricas.esperados_aleatorio(cands, rel, lugar, cat, ks, k_lugar)
    sim = {n: [] for n in esperado}
    modelo = referencias.Aleatorio()
    rng = make_rng(11, 0)
    modelo.ajustar(None, cat, rng)
    kmax = max(ks + k_lugar)
    for _ in range(reps):
        tops = metricas.rankear_usuarios(modelo.puntuar(usuarios), usuarios, cat, cands, kmax, rng)
        pu = metricas.metricas_por_usuario(tops, rel, lugar, ks, k_lugar)
        for k in ks:
            for nombre in ("acierto", "precision", "recall", "ndcg"):
                sim[f"{nombre}@{k}"].append(pu[nombre][k].mean())
            sim[f"cobertura@{k}"].append(metricas.cobertura({u: tops[u][0] for u in usuarios}, len(cat), k))
        for k in k_lugar:
            sim[f"acierto_por_lugar@{k}"].append(pu["lugar"][k].mean())
    assert set(sim) == set(esperado)
    for nombre, valores in sim.items():
        v = np.asarray(valores)
        se = v.std(ddof=1) / math.sqrt(reps)
        assert se > 0
        assert abs(v.mean() - esperado[nombre]) < 5 * se, f"{nombre}: simulado {v.mean():.5f} vs analítico {esperado[nombre]:.5f}"


# =========================================================================== modelos de referencia
def _datos_chicos(n_usuarios: int = 40, n_destinos: int = 30, n_catalogo: int = 35, semilla: int = 3):
    inter = particion.asignar_split(tabla({u: 1 + u % 6 for u in range(1, n_usuarios + 1)}, n_destinos=n_destinos), semilla)
    return inter, catalogo(n_catalogo)


def test_popularidad_puntua_con_el_conteo_de_train_para_todos():
    inter, cat = _datos_chicos()
    m = referencias.Popularidad().ajustar(inter, cat["destino_id"], make_rng(0, 0))
    pop = particion.popularidad_train(inter, cat["destino_id"]).to_numpy()
    p = m.puntuar([1, 2, 3])
    assert p.shape == (3, len(cat)) and all(np.array_equal(f, pop) for f in p)
    assert m.n_parametros() == len(cat)           # conteos estimados (ver el docstring de Popularidad)
    assert m.nombre == "popularidad" and m.hiperparametros == {}


def test_aleatorio_puntua_con_el_rng_y_no_estima_nada():
    cat = np.arange(1, 11)
    m = referencias.Aleatorio().ajustar(None, cat, make_rng(2, 0))
    p = m.puntuar([1, 2, 3, 4])
    assert p.shape == (4, 10) and ((p >= 0) & (p < 1)).all() and m.n_parametros() == 0
    otro = referencias.Aleatorio().ajustar(None, cat, make_rng(2, 0)).puntuar([1, 2, 3, 4])
    assert np.array_equal(p, otro)                                   # misma semilla → mismos puntajes
    assert not np.array_equal(p, referencias.Aleatorio().ajustar(None, cat, make_rng(2, 1)).puntuar([1, 2, 3, 4]))


# =========================================================================== C1.5 ALS
def _problema_chico():
    """8 usuarios × 12 destinos; el destino 11 no tiene interacciones (frío) y todo usuario tiene al menos una."""
    rng = np.random.default_rng(5)
    P = (rng.random((8, 12)) < 0.3).astype(float)
    P[:, 11] = 0.0
    for u in range(8):
        P[u, u] = 1.0
    obs_u = [np.flatnonzero(P[u]) for u in range(8)]
    obs_i = [np.flatnonzero(P[:, i]) for i in range(12)]
    return P, obs_u, obs_i


def _perdida_densa(X, Y, P, alfa, lam):
    C = 1.0 + alfa * P
    return float((C * (P - X @ Y.T) ** 2).sum() + lam * ((X ** 2).sum() + (Y ** 2).sum()))


def test_perdida_eficiente_coincide_con_la_densa():
    P, obs_u, _ = _problema_chico()
    rng = np.random.default_rng(0)
    X, Y = rng.normal(size=(8, 3)), rng.normal(size=(12, 3))
    assert referencias.perdida_als(X, Y, obs_u, 7.0, 0.3) == pytest.approx(_perdida_densa(X, Y, P, 7.0, 0.3), rel=1e-12)


def test_als_no_aumenta_la_perdida_en_ningun_medio_paso():
    P, obs_u, obs_i = _problema_chico()
    X, Y, hist = referencias.ajustar_als(obs_u, obs_i, 8, 12, factores=3, regularizacion=0.1, alfa=20.0, iteraciones=15,
                                         escala_inicial=0.1, rng=make_rng(4, 0))
    assert len(hist) == 1 + 2 * 15                                    # pérdida inicial + 2 medios pasos por iteración
    for a, b in zip(hist[:-1], hist[1:]):
        assert b <= a * (1 + 1e-10), f"la pérdida subió de {a} a {b}"
    assert hist[-1] < hist[0]
    assert hist[-1] == pytest.approx(_perdida_densa(X, Y, P, 20.0, 0.1), rel=1e-10)   # el historial usa la pérdida densa
    assert np.all(Y[11] == 0.0)                                       # destino sin interacciones: y_i = 0 exacto


def test_als_misma_semilla_mismos_factores_otra_semilla_otros():
    _, obs_u, obs_i = _problema_chico()
    args = dict(factores=3, regularizacion=0.1, alfa=20.0, iteraciones=4, escala_inicial=0.1)
    a = referencias.ajustar_als(obs_u, obs_i, 8, 12, rng=make_rng(4, 0), **args)
    b = referencias.ajustar_als(obs_u, obs_i, 8, 12, rng=make_rng(4, 0), **args)
    c = referencias.ajustar_als(obs_u, obs_i, 8, 12, rng=make_rng(4, 1), **args)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1]) and a[2] == b[2]
    assert not np.array_equal(a[0], c[0])


def test_actualizacion_cerrada_coincide_con_minimos_cuadrados_ponderados():
    """x_u = (YᵀC^uY + λI)⁻¹ YᵀC^u p(u) es el minimizador de Σ_i c_ui (p_ui − x·y_i)² + λ‖x‖², que es el problema de
    mínimos cuadrados de la matriz aumentada [√c·Y; √λ·I] x ≈ [√c·p; 0] (np.linalg.lstsq)."""
    P, obs_u, obs_i = _problema_chico()
    rng = np.random.default_rng(8)
    Y, X = rng.normal(size=(12, 3)), rng.normal(size=(8, 3))
    alfa, lam = 15.0, 0.4
    nuevo_x = referencias.actualizar_factores(Y, obs_u, alfa, lam)
    for u in range(8):
        c = 1.0 + alfa * P[u]
        A = np.vstack([np.sqrt(c)[:, None] * Y, np.sqrt(lam) * np.eye(3)])
        b = np.concatenate([np.sqrt(c) * P[u], np.zeros(3)])
        assert np.allclose(nuevo_x[u], np.linalg.lstsq(A, b, rcond=None)[0], atol=1e-9)
    nuevo_y = referencias.actualizar_factores(X, obs_i, alfa, lam)        # mismo problema por destino
    for i in range(11):
        c = 1.0 + alfa * P[:, i]
        A = np.vstack([np.sqrt(c)[:, None] * X, np.sqrt(lam) * np.eye(3)])
        b = np.concatenate([np.sqrt(c) * P[:, i], np.zeros(3)])
        assert np.allclose(nuevo_y[i], np.linalg.lstsq(A, b, rcond=None)[0], atol=1e-9)
    assert np.all(nuevo_y[11] == 0.0)                                      # sin interacciones: 0 exacto


def test_mf_als_clase_usa_solo_train_y_valida_hiperparametros():
    inter, cat = _datos_chicos()
    ids = cat["destino_id"]
    hp = dict(factores=4, regularizacion=0.1, alfa=10.0, iteraciones=3, escala_inicial=0.01)
    m = referencias.MFImplicitaALS(**hp).ajustar(inter, ids, make_rng(1, 0))
    train = inter[inter["split"] == "train"]
    n_u = train["usuario_id"].nunique()
    assert m.X.shape == (n_u, 4) and m.Y.shape == (len(ids), 4) and m.n_parametros() == (n_u + len(ids)) * 4
    assert m.hiperparametros == hp
    frios = set(ids) - set(train["destino_id"])
    assert frios                                                           # el escenario tiene destinos fríos
    for j, d in enumerate(ids):
        if d in frios:
            assert np.all(m.Y[j] == 0.0)
    p = m.puntuar(list(m.usuario_ids[:3]))
    assert np.allclose(p, m.X[:3] @ m.Y.T) and p.shape == (3, len(ids))
    for malo in ({"regularizacion": 0.0}, {"regularizacion": -1.0}, {"alfa": -0.1}, {"factores": 0}, {"iteraciones": 0},
                 {"escala_inicial": 0.0}):
        with pytest.raises(ValueError):
            referencias.MFImplicitaALS(**{**hp, **malo})
    with pytest.raises(ValueError):
        m.puntuar([99999])                                                 # usuario sin interacciones en train


def test_registro_de_modelos_construye_las_tres_referencias():
    cfg = load_config(CFG_BASE)
    assert {"popularidad", "mf_als", "aleatorio"} <= set(referencias.MODELOS)
    for nombre in cfg["modelos"]:
        m = referencias.MODELOS[nombre](cfg)
        assert m.nombre == nombre and callable(m.ajustar) and callable(m.puntuar) and callable(m.n_parametros)


# =========================================================================== C1.4 la búsqueda no lee prueba
def test_objetivo_de_la_busqueda_no_cambia_si_se_altera_o_elimina_la_prueba():
    inter, cat = _datos_chicos(n_usuarios=50)
    ids = cat["destino_id"]
    cfg = load_config(CFG_DEMO)
    params = {"factores": 4, "regularizacion": 0.1, "alfa": 10.0, "iteraciones": 3}
    base = hpo.evaluar_configuracion(inter, ids, params, cfg)
    assert 0.0 <= base["valor"] <= 1.0 and base["valor"] == base[f"ndcg@{cfg['busqueda']['objetivo_k']}"]
    alterada = _alterar_no_train(inter, ids, "prueba")
    sin = inter[inter["split"] != "prueba"]
    assert hpo.evaluar_configuracion(alterada, ids, params, cfg) == base
    assert hpo.evaluar_configuracion(sin, ids, params, cfg) == base


# =========================================================================== C1.8 coherencia de configs
def test_configs_son_coherentes_con_las_decisiones():
    base, hp, datos = load_config(CFG_BASE), load_config(CFG_HPO), load_config(CFG_DATOS)
    assert base["evaluacion"]["umbral_pocas_max"] == datos["particion"]["umbral_pocas_max"]
    assert hp["busqueda"]["n_ensayos"] == 20                         # D13
    assert base["semillas"]["n"] == 30                               # D14
    assert base["evaluacion"]["k"] == [1, 3, 5, 10] and base["evaluacion"]["k_lugar"] == [1, 3]
    assert hp["busqueda"]["objetivo_k"] == 5 and hp["busqueda"]["objetivo"] == "ndcg"
    demo = load_config(CFG_DEMO)
    assert demo["busqueda"]["ejecutar_en_experimento"] is True and demo["salida"]["carpeta"] == "results/data/m3_demo"
    assert demo["salida"]["modelos"] == "models/m3_demo"
    ignorado = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    assert "results/data/*_demo/" in ignorado and "models/*_demo*" in ignorado       # las salidas del demo no se versionan


# =========================================================================== arnés sobre datos sintéticos
def sha_archivo(ruta: Path) -> str:
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def montar_sintetico(carpeta: Path, n_usuarios: int = 60, n_catalogo: int = 45) -> pd.DataFrame:
    """Escribe destinos, usuarios, interacciones (con ``split``) y un ``resumen.json`` mínimo (solo su bloque sha256)."""
    from src.comun.results import save_json
    carpeta.mkdir(parents=True, exist_ok=True)
    inter = particion.asignar_split(tabla({u: 1 + u % 7 for u in range(1, n_usuarios)}, n_destinos=40), 2)
    cat = catalogo(n_catalogo).assign(nombre=lambda d: "Destino " + d["destino_id"].astype(str))
    cat.to_parquet(carpeta / "destinos.parquet", index=False)
    pd.DataFrame({"usuario_id": np.arange(1, n_usuarios + 20)}).to_parquet(carpeta / "usuarios.parquet", index=False)
    inter.to_parquet(carpeta / "interacciones.parquet", index=False)
    leida = pd.read_parquet(carpeta / "interacciones.parquet")
    save_json(carpeta / "resumen.json", {"sha256": {"interacciones_parquet": sha_archivo(carpeta / "interacciones.parquet"),
                                                    "huella": particion.huella(leida), "huella_formato": "formato de prueba"}})
    return leida


def cfg_sintetica(tmp: Path, extra=(), base: Path = CFG_DEMO) -> dict:
    proc = (tmp / "proc").as_posix()
    sets = [f"datos.carpeta={proc}", f"datos.resumen_particion={proc}/resumen.json",
            f"salida.carpeta={(tmp / 'res').as_posix()}", f"salida.modelos={(tmp / 'mod').as_posix()}",
            "semillas.n=2", "busqueda.n_ensayos=2",
            "modelos=[popularidad, mf_als, aleatorio]"]      # JJ-5 agregó la red a las configs; estas pruebas son de JJ-4
    return apply_overrides(load_config(base), [*sets, *extra])


@pytest.fixture(scope="module")
def corrida(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("m3_sintetico")
    inter = montar_sintetico(tmp / "proc")
    cfg = cfg_sintetica(tmp)
    assert experimento.main(cfg) == 0
    return {"tmp": tmp, "inter": inter, "cfg": cfg, "res": tmp / "res", "mod": tmp / "mod"}


def test_summary_cumple_el_contrato_5_9(corrida):
    s = load_json(corrida["res"] / "summary.json")
    inter = corrida["inter"]
    assert set(s["modelos"]) == {"popularidad", "mf_als", "aleatorio"}
    n_prueba = inter.loc[inter["split"] == "prueba", "usuario_id"].nunique()
    assert s["split_evaluado"] == "prueba" and s["n_usuarios_evaluados"] == n_prueba
    for nombre, m in s["modelos"].items():
        for k in s["k"]:
            for met in ("precision", "recall", "ndcg", "acierto", "cobertura"):
                r = m["metricas"][f"{met}@{k}"]
                assert set(r) >= {"media", "desviacion", "mejor", "peor"} and r["n"] == 2
                assert r["peor"] <= r["media"] <= r["mejor"]
            assert set(m["concentracion"][f"gini@{k}"]) >= {"media", "desviacion", "minimo", "maximo"}
            assert f"hhi@{k}" in m["concentracion"]
        assert isinstance(m["n_parametros"], int) and m["tiempo_total_s"] >= 0 and m["device"] == "cpu"
        assert m["semillas_efectivas"] == [0, 1]
        assert m["n_configuraciones_busqueda"] == (2 if nombre == "mf_als" else 1)
    assert s["modelos"]["aleatorio"]["n_parametros"] == 0
    ev = s["evidencia"]
    assert ev["particion_huella"] == particion.huella(inter) and ev["particion_huella_formato"]
    assert ev["sha256_parquet"] == {"interacciones": sha_archivo(corrida["tmp"] / "proc" / "interacciones.parquet"),
                                    "destinos": sha_archivo(corrida["tmp"] / "proc" / "destinos.parquet"),
                                    "usuarios": sha_archivo(corrida["tmp"] / "proc" / "usuarios.parquet")}
    assert "linea_base_aleatoria_analitica" in s and "destinos_frios" in s


def test_se_escriben_todos_los_archivos(corrida):
    res, mod = corrida["res"], corrida["mod"]
    for nombre in ("popularidad", "mf_als", "aleatorio"):
        for k in (0, 1):
            j = load_json(res / "semillas" / f"{nombre}_seed{k}.json")
            assert j["semilla"] == k and "metricas" in j and "evidencia" in j and "tiempo_s" in j
    assert not (res / "semillas" / "popularidad_seed2.json").exists()
    for archivo in ("metricas_por_k.json", "metricas_por_grupo.json", "hpo_ensayos.json"):
        assert (res / archivo).is_file()
    assert (res / "recomendaciones_prueba.parquet").is_file()
    assert (mod / "mf_als.npz").is_file() and (mod / "mf_als.json").is_file()
    z = np.load(mod / "mf_als.npz", allow_pickle=False)
    assert set(z.files) >= {"X", "Y", "usuario_ids", "destino_ids"}
    f = load_json(mod / "mf_als.json")
    assert f["semilla"] == 0 and f["historial_perdida"] and "hiperparametros" in f and "evidencia" in f
    h = load_json(res / "hpo_ensayos.json")["familias"]["mf_als"]
    assert h["n_ensayos"] == 2 and len(h["ensayos"]) == 2 and h["mejor"]["params"] and h["objetivo"]


def test_recomendaciones_permiten_recalcular_las_metricas(corrida):
    """El verificador recalcula desde el parquet: acierto@3 y NDCG@3 de cada modelo y semilla coinciden con el JSON."""
    rec = pd.read_parquet(corrida["res"] / "recomendaciones_prueba.parquet")
    assert list(rec.columns) == ["modelo", "semilla", "usuario_id", "rango", "destino_id", "puntaje"]
    inter = corrida["inter"]
    objetivo = inter[inter["split"] == "prueba"].set_index("usuario_id")["destino_id"]
    conocido = particion.historial_conocido(inter, "prueba")
    for (modelo, semilla), g in rec.groupby(["modelo", "semilla"]):
        assert set(g["usuario_id"]) == set(objetivo.index)
        aciertos, ndcg = [], []
        for u, gu in g.groupby("usuario_id"):
            gu = gu.sort_values("rango")
            assert list(gu["rango"]) == list(range(1, len(gu) + 1)) and not (set(gu["destino_id"]) & conocido[u])
            assert gu["destino_id"].is_unique
            r = list(gu["destino_id"][:3]).index(objetivo[u]) + 1 if objetivo[u] in list(gu["destino_id"][:3]) else None
            aciertos.append(r is not None)
            ndcg.append(0.0 if r is None else 1 / math.log2(r + 1))
        j = load_json(corrida["res"] / "semillas" / f"{modelo}_seed{semilla}.json")["metricas"]["global"]
        assert np.mean(aciertos) == pytest.approx(j["acierto@3"]) and np.mean(ndcg) == pytest.approx(j["ndcg@3"])
        assert np.mean(aciertos) == pytest.approx(j["recall@3"]) and np.mean(aciertos) / 3 == pytest.approx(j["precision@3"])


def test_destinos_frios_y_grupos(corrida):
    s = load_json(corrida["res"] / "summary.json")
    inter = corrida["inter"]
    pop = particion.popularidad_train(inter, np.arange(1, 46))
    rel = inter[inter["split"] == "prueba"]
    frios = int((pop.reindex(rel["destino_id"]).to_numpy() == 0).sum())
    fr = s["destinos_frios"]
    assert fr["usuarios_prueba_con_objetivo_frio"] == frios and fr["usuarios_prueba"] == len(rel)
    assert fr["techo_acierto_popularidad"] == pytest.approx((len(rel) - frios) / len(rel))
    assert frios > 0 and fr["popularidad_techo_valido"]              # el escenario sintético tiene fríos y candidatos de sobra
    for k in s["k"]:                                                  # la popularidad nunca acierta un destino frío
        assert fr["por_modelo"]["popularidad"][str(k)]["acierto_objetivo_frio"]["media"] == 0.0
    g = load_json(corrida["res"] / "metricas_por_grupo.json")
    assert g["umbral_pocas_max"] == 2 and set(g["modelos"]["mf_als"]) == {"pocas", "muchas"}
    total = inter.groupby("usuario_id").size()
    n_pocas = int((total.reindex(rel["usuario_id"]).le(2)).sum())
    assert g["modelos"]["mf_als"]["pocas"]["n_usuarios"] == n_pocas
    assert g["modelos"]["mf_als"]["muchas"]["n_usuarios"] == len(rel) - n_pocas
    assert "aleatorio_analitico" in g
    assert set(g["modelos"]["mf_als"]["pocas"]["ndcg@5"]) == {"media", "desviacion", "mejor", "peor", "n"}   # resumir_semillas
    pk = load_json(corrida["res"] / "metricas_por_k.json")
    assert "ndcg" in pk["modelos"]["popularidad"]["5"] and "aleatorio_analitico" in pk


def test_corrida_es_determinista(corrida, tmp_path):
    montar_sintetico(tmp_path / "proc")
    assert experimento.main(cfg_sintetica(tmp_path)) == 0
    a = load_json(corrida["res"] / "summary.json")["modelos"]
    b = load_json(tmp_path / "res" / "summary.json")["modelos"]
    for nombre in a:
        assert a[nombre]["metricas"] == b[nombre]["metricas"] and a[nombre]["hiperparametros"] == b[nombre]["hiperparametros"]
    ra = pd.read_parquet(corrida["res"] / "recomendaciones_prueba.parquet")
    rb = pd.read_parquet(tmp_path / "res" / "recomendaciones_prueba.parquet")
    pd.testing.assert_frame_equal(ra, rb)


# =========================================================================== C1.7 cambios en vivo
def test_cambios_en_vivo_evaluacion_k_y_semillas_n(tmp_path):
    montar_sintetico(tmp_path / "proc")
    cfg = cfg_sintetica(tmp_path, ["evaluacion.k=3", "semillas.n=2"])
    assert experimento.main(cfg) == 0
    s = load_json(tmp_path / "res" / "summary.json")
    assert s["k"] == [3]
    for m in s["modelos"].values():
        nombres = ("precision", "recall", "ndcg", "acierto", "cobertura", "acierto_por_lugar")
        assert set(m["metricas"]) == {f"{n}@3" for n in nombres}
        assert all(v["n"] == 2 for v in m["metricas"].values())
    # evaluacion.k también acepta una lista (con --set evaluacion.k=[1, 3])
    cfg2 = cfg_sintetica(tmp_path / "otra", ["evaluacion.k=[1, 3]", "semillas.n=1"])
    montar_sintetico(tmp_path / "otra" / "proc")
    assert experimento.main(cfg2) == 0
    s2 = load_json(tmp_path / "otra" / "res" / "summary.json")
    assert s2["k"] == [1, 3] and s2["modelos"]["mf_als"]["metricas"]["ndcg@1"]["n"] == 1




# =========================================================================== C1.9 evidencia verificada
def test_falla_con_error_claro_si_la_huella_no_coincide(tmp_path):
    from src.comun.results import save_json
    montar_sintetico(tmp_path / "proc")
    r = load_json(tmp_path / "proc" / "resumen.json")
    r["sha256"]["huella"] = "0" * 64
    save_json(tmp_path / "proc" / "resumen.json", r)
    with pytest.raises(ValueError, match="huella"):
        experimento.main(cfg_sintetica(tmp_path))
    assert not (tmp_path / "res" / "summary.json").exists()


def test_falla_con_error_claro_si_el_sha256_del_parquet_no_coincide(tmp_path):
    from src.comun.results import save_json
    montar_sintetico(tmp_path / "proc")
    r = load_json(tmp_path / "proc" / "resumen.json")
    r["sha256"]["interacciones_parquet"] = "f" * 64
    save_json(tmp_path / "proc" / "resumen.json", r)
    with pytest.raises(ValueError, match="SHA-256"):
        experimento.main(cfg_sintetica(tmp_path))


def test_hiperparametros_desde_hpo_sin_archivo_es_un_error_claro(tmp_path):
    montar_sintetico(tmp_path / "proc")
    cfg = cfg_sintetica(tmp_path, ["busqueda.ejecutar_en_experimento=false"])
    with pytest.raises(FileNotFoundError, match="hpo_ensayos"):
        experimento.main(cfg)


def test_hiperparametros_desde_config_no_necesita_busqueda(tmp_path):
    montar_sintetico(tmp_path / "proc")
    cfg = cfg_sintetica(tmp_path, ["mf_als.hiperparametros_desde=config", "busqueda.ejecutar_en_experimento=false"])
    assert experimento.main(cfg) == 0
    s = load_json(tmp_path / "res" / "summary.json")["modelos"]["mf_als"]
    assert s["n_configuraciones_busqueda"] == 1 and s["hiperparametros_origen"] == "config"


def test_hpo_conserva_familias_de_la_misma_huella_y_reemplaza_si_cambia(tmp_path):
    from src.comun.results import save_json
    montar_sintetico(tmp_path / "proc")
    cfg = cfg_sintetica(tmp_path, base=CFG_HPO)
    ruta = tmp_path / "res" / "hpo_ensayos.json"
    ev = {"particion_huella": particion.huella(pd.read_parquet(tmp_path / "proc" / "interacciones.parquet"))}
    save_json(ruta, {"evidencia": ev, "familias": {"red": {"n_ensayos": 20}}})
    assert hpo.main(cfg) == 0
    j = load_json(ruta)
    assert set(j["familias"]) == {"red", "mf_als"} and j["familias"]["mf_als"]["n_ensayos"] == 2   # la de JJ-5 se conserva
    save_json(ruta, {"evidencia": {"particion_huella": "otra"}, "familias": {"red": {"n_ensayos": 20}}})
    assert hpo.main(cfg) == 0
    assert set(load_json(ruta)["familias"]) == {"mf_als"}                                            # otra huella: se reemplaza


# =========================================================================== C1.10 sin red
def test_una_corrida_pequena_termina_con_la_red_bloqueada(tmp_path, monkeypatch):
    class RedBloqueada(RuntimeError):
        pass

    def bloqueado(*args, **kwargs):
        raise RedBloqueada("intento de usar la red durante un experimento")

    montar_sintetico(tmp_path / "proc")
    cfg = cfg_sintetica(tmp_path, ["semillas.n=1"])
    monkeypatch.setattr(socket, "socket", bloqueado)
    monkeypatch.setattr(socket, "create_connection", bloqueado)
    assert experimento.main(cfg) == 0
    assert (tmp_path / "res" / "summary.json").is_file()






# =========================================================================== guarda de degeneración de la MF (R1, H1)
# Con Z = X Yᵀ y σ = σ_max(P_train): ⟨P, Z⟩ ≤ σ‖Z‖_* y ‖Z‖_* ≤ ½(‖X‖² + ‖Y‖²), de modo que
#   L(X, Y) − L(0, 0) ≥ (λ − (1 + α)σ)(‖X‖² + ‖Y‖²)
# y si λ > (1 + α)σ el único mínimo global es X = Y = 0 (factorización nula: listas que salen del residuo numérico).
def _inter_desde_p(P: np.ndarray) -> tuple[pd.DataFrame, np.ndarray]:
    u, i = np.nonzero(P)
    inter = pd.DataFrame({"usuario_id": u + 1, "destino_id": i + 1, "split": "train"})
    return inter, np.arange(1, P.shape[1] + 1)


def test_la_mf_con_lambda_mayor_que_la_cota_queda_degenerada_y_el_detector_lo_marca():
    P, _, _ = _problema_chico()
    inter, cat = _inter_desde_p(P)
    sigma = np.linalg.norm(P, 2)
    alfa = 3.0
    umbral = (1 + alfa) * sigma
    sin = referencias.MFImplicitaALS(factores=3, regularizacion=umbral * 1.5, alfa=alfa, iteraciones=40,
                                     escala_inicial=0.1, tolerancia_degenerado=1e-8).ajustar(inter, cat, make_rng(0, 0))
    assert sin.degenerado and sin.max_abs_puntaje < 1e-8
    assert abs(sin.X).max() < 1e-6 and abs(sin.Y).max() < 1e-6                    # colapsa hacia X = Y = 0
    con = referencias.MFImplicitaALS(factores=3, regularizacion=0.05, alfa=alfa, iteraciones=15,
                                     escala_inicial=0.1, tolerancia_degenerado=1e-8).ajustar(inter, cat, make_rng(0, 0))
    assert not con.degenerado and con.max_abs_puntaje > 0.1
    assert con.max_abs_puntaje == pytest.approx(float(np.abs(con.X @ con.Y.T).max()))
    # la pérdida de la solución nula es (1 + α)·|train|; la de la MF sana es menor
    assert con.historial_perdida[-1] < (1 + alfa) * P.sum()
    assert sin.historial_perdida[-1] == pytest.approx((1 + alfa) * P.sum(), rel=1e-6)


def test_tolerancia_degenerado_se_valida():
    for malo in (0.0, -1e-8):
        with pytest.raises(ValueError):
            referencias.MFImplicitaALS(factores=2, regularizacion=0.1, alfa=1.0, iteraciones=1, tolerancia_degenerado=malo)


def _cfg_busqueda_mixta(tmp_path, lam_min, lam_max, n=12):
    montar_sintetico(tmp_path / "proc")
    cfg = cfg_sintetica(tmp_path, base=CFG_HPO, extra=[f"busqueda.n_ensayos={n}",
                                                       f"busqueda.espacio.regularizacion.min={lam_min}",
                                                       f"busqueda.espacio.regularizacion.max={lam_max}",
                                                       "busqueda.espacio.alfa.max=3.0", "busqueda.espacio.iteraciones.min=20"])
    return cfg


def test_la_busqueda_nunca_elige_un_ensayo_degenerado(tmp_path):
    cfg = _cfg_busqueda_mixta(tmp_path, 1.0e-3, 1.0e+4)          # incluye ambos regímenes (λ muy bajo y λ ≫ (1 + α)σ)
    assert hpo.main(cfg) == 0
    fam = load_json(tmp_path / "res" / "hpo_ensayos.json")["familias"]["mf_als"]
    flags = [e["degenerado"] for e in fam["ensayos"]]
    assert any(flags) and not all(flags)                          # el espacio forzado produjo de ambos
    assert fam["n_degenerados"] == sum(flags) and fam["n_ensayos"] == len(flags) == 12   # el presupuesto cuenta todos
    mejor = fam["mejor"]["numero"]
    assert not fam["ensayos"][mejor]["degenerado"]
    assert fam["mejor"]["valor"] == max(e["valor"] for e in fam["ensayos"] if not e["degenerado"])


def test_la_busqueda_falla_con_error_claro_si_todos_los_ensayos_son_degenerados(tmp_path):
    cfg = _cfg_busqueda_mixta(tmp_path, 1.0e+4, 1.0e+5, n=3)
    with pytest.raises(ValueError, match="degenerad"):
        hpo.main(cfg)
    assert not (tmp_path / "res" / "hpo_ensayos.json").exists()


def test_el_experimento_falla_si_la_mf_final_queda_degenerada(tmp_path):
    montar_sintetico(tmp_path / "proc")
    cfg = cfg_sintetica(tmp_path, ["mf_als.hiperparametros_desde=config", "busqueda.ejecutar_en_experimento=false",
                                   "mf_als.hiperparametros.regularizacion=100000.0", "mf_als.hiperparametros.iteraciones=30",
                                   "mf_als.hiperparametros.alfa=3.0"])
    with pytest.raises(ValueError, match="degenerad"):
        experimento.main(cfg)
    assert not (tmp_path / "res" / "summary.json").exists()


def test_n_parametros_con_datos_excluye_las_filas_de_destinos_sin_train(corrida):
    s = load_json(corrida["res"] / "summary.json")["modelos"]
    inter = corrida["inter"]
    train = inter[inter["split"] == "train"]
    f = s["mf_als"]["hiperparametros"]["factores"]
    n_u, n_d = train["usuario_id"].nunique(), train["destino_id"].nunique()
    assert s["mf_als"]["n_parametros"] == (n_u + 45) * f
    con_datos = s["mf_als"]["diagnosticos"]["n_parametros_con_datos"]
    assert con_datos["media"] == (n_u + n_d) * f < s["mf_als"]["n_parametros"] and con_datos["n"] == 2
    assert s["popularidad"]["diagnosticos"] == {}


def test_config_define_la_tolerancia_y_el_tope_de_lambda_es_seguro_para_alfa_minimo():
    base, hp = load_config(CFG_BASE), load_config(CFG_HPO)
    assert 0 < base["mf_als"]["tolerancia_degenerado"] <= 1e-6
    esp = hp["busqueda"]["espacio"]
    assert esp["regularizacion"]["max"] == 5.0 and esp["alfa"]["min"] >= 1.0


@pytest.mark.skipif(not (RAIZ / "data" / "processed" / "m3" / "interacciones.parquet").is_file(),
                    reason="faltan los datos reales")
def test_real_el_tope_de_lambda_esta_por_debajo_de_la_region_degenerada():
    """σ_max(P_train) calculado SOLO con las interacciones de train (matriz densa 858 × 1 000, norma espectral)."""
    inter = pd.read_parquet(RAIZ / "data" / "processed" / "m3" / "interacciones.parquet")
    cat = pd.read_parquet(RAIZ / "data" / "processed" / "m3" / "destinos.parquet")["destino_id"]
    t = inter[inter["split"] == "train"]
    us = np.sort(t["usuario_id"].unique())
    P = np.zeros((len(us), len(cat)))
    P[np.searchsorted(us, t["usuario_id"]), pd.Index(cat).get_indexer(t["destino_id"])] = 1.0
    sigma = float(np.linalg.norm(P, 2))
    hp = load_config(CFG_HPO)["busqueda"]["espacio"]
    assert hp["regularizacion"]["max"] < (1 + hp["alfa"]["min"]) * sigma
    r = load_config(CFG_BASE)["mf_als"]["hiperparametros"]
    assert r["regularizacion"] < (1 + r["alfa"]) * sigma


# =========================================================================== cota de la solución nula en hpo_ensayos.json
def _sigma_max_train(inter: pd.DataFrame, n_catalogo: int) -> float:
    t = inter[inter["split"] == "train"]
    us = np.sort(t["usuario_id"].unique())
    P = np.zeros((len(us), n_catalogo))
    P[np.searchsorted(us, t["usuario_id"]), t["destino_id"].to_numpy() - 1] = 1.0
    return float(np.linalg.norm(P, 2))


def test_hpo_ensayos_trae_la_cota_de_la_solucion_nula(corrida):
    fam = load_json(corrida["res"] / "hpo_ensayos.json")["familias"]["mf_als"]
    c = fam["cota_solucion_nula"]
    esp = corrida["cfg"]["busqueda"]["espacio"]
    sigma = _sigma_max_train(corrida["inter"], 45)
    assert c["sigma_max_train"] == pytest.approx(sigma, rel=1e-12)
    assert c["alfa_min"] == esp["alfa"]["min"] and c["lambda_max"] == esp["regularizacion"]["max"]
    assert c["cota"] == pytest.approx((1 + c["alfa_min"]) * sigma, rel=1e-12)
    assert c["lambda_max_bajo_la_cota"] is (c["lambda_max"] < c["cota"])
    assert "L(X, Y) − L(0, 0) ≥ (λ − (1 + α)σ_max)(‖X‖² + ‖Y‖²)" in c["nota"]


def test_la_cota_solo_usa_train(corrida):
    inter, ids = corrida["inter"], pd.Series(np.arange(1, 46))
    cfg = corrida["cfg"]
    base = hpo.cota_solucion_nula(inter, ids, cfg["busqueda"]["espacio"])
    for s in ("validacion", "prueba"):
        assert hpo.cota_solucion_nula(_alterar_no_train(inter, ids, s), ids, cfg["busqueda"]["espacio"]) == base
        assert hpo.cota_solucion_nula(inter[inter["split"] != s], ids, cfg["busqueda"]["espacio"]) == base


def test_advierte_en_consola_si_el_tope_de_lambda_supera_la_cota(tmp_path, capsys):
    cfg = _cfg_busqueda_mixta(tmp_path, 1.0e-3, 1.0e+4, n=2)
    hpo.main(cfg)
    salida = capsys.readouterr().out
    assert "ADVERTENCIA" in salida and "cota" in salida
    cota = load_json(tmp_path / "res" / "hpo_ensayos.json")["familias"]["mf_als"]["cota_solucion_nula"]
    assert cota["lambda_max_bajo_la_cota"] is False


def test_real_cota_de_hpo_yaml_queda_por_encima_del_tope():
    ruta = RAIZ / "results" / "data" / "m3" / "hpo_ensayos.json"
    if not ruta.is_file():
        pytest.skip("falta hpo_ensayos.json real")
    c = load_json(ruta)["familias"]["mf_als"]["cota_solucion_nula"]
    assert c["lambda_max_bajo_la_cota"] is True and c["cota"] > c["lambda_max"]
    inter = pd.read_parquet(RAIZ / "data" / "processed" / "m3" / "interacciones.parquet")
    cat = pd.read_parquet(RAIZ / "data" / "processed" / "m3" / "destinos.parquet")["destino_id"]
    t = inter[inter["split"] == "train"]
    us = np.sort(t["usuario_id"].unique())
    P = np.zeros((len(us), len(cat)))
    P[np.searchsorted(us, t["usuario_id"]), pd.Index(cat).get_indexer(t["destino_id"])] = 1.0
    assert c["sigma_max_train"] == pytest.approx(np.linalg.norm(P, 2), rel=1e-9)              # SVD densa de control


# =========================================================================== regla exacta de degeneración (R1 N1, N3)
def _mf_chica(P, **kw):
    inter, cat = _inter_desde_p(P)
    hp = dict(factores=3, regularizacion=0.05, alfa=3.0, iteraciones=15, escala_inicial=0.1, tolerancia_degenerado=1e-8)
    hp.update(kw)
    return referencias.MFImplicitaALS(**hp).ajustar(inter, cat, make_rng(0, 0))


def test_sigma_max_train_coincide_con_la_norma_espectral_y_solo_usa_train():
    inter, cat = _datos_chicos(n_usuarios=50)
    ids = cat["destino_id"]
    t = inter[inter["split"] == "train"]
    us = np.sort(t["usuario_id"].unique())
    P = np.zeros((len(us), len(ids)))
    P[np.searchsorted(us, t["usuario_id"]), pd.Index(ids).get_indexer(t["destino_id"])] = 1.0
    assert referencias.sigma_max_train(inter, ids) == pytest.approx(np.linalg.norm(P, 2), rel=1e-12)
    for s in ("validacion", "prueba"):
        assert referencias.sigma_max_train(_alterar_no_train(inter, ids, s), ids) == referencias.sigma_max_train(inter, ids)
        assert referencias.sigma_max_train(inter[inter["split"] != s], ids) == referencias.sigma_max_train(inter, ids)
    assert hpo.cota_solucion_nula(inter, ids, load_config(CFG_HPO)["busqueda"]["espacio"])["sigma_max_train"] == \
        referencias.sigma_max_train(inter, ids)                                  # la cota reutiliza el mismo cálculo


def test_motivo_lambda_ge_cota_con_lambda_apenas_encima_y_pocos_barridos():
    """λ = 1,05·(1 + α)σ_max y 5 barridos: los puntajes aún no son < tolerancia (colapso poco profundo) pero el modelo es
    degenerado por la condición exacta (el único mínimo global es 0)."""
    P, _, _ = _problema_chico()
    sigma, alfa = float(np.linalg.norm(P, 2)), 3.0
    m = _mf_chica(P, regularizacion=1.05 * (1 + alfa) * sigma, iteraciones=5)
    assert m.sigma_max_train == pytest.approx(sigma, rel=1e-12)
    assert m.max_abs_puntaje > m.tolerancia_degenerado                       # el detector por tolerancia no lo vería
    assert m.condiciones_degenerado["lambda_ge_cota"] and not m.condiciones_degenerado["puntaje_bajo_tolerancia"]
    assert m.degenerado and m.motivo_degenerado == "lambda_ge_cota"


def test_motivo_puntaje_bajo_tolerancia_por_separado():
    P, _, _ = _problema_chico()
    m = _mf_chica(P, regularizacion=0.05, tolerancia_degenerado=1e6)         # λ muy bajo la cota y pérdida sana
    c = m.condiciones_degenerado
    assert c == {"lambda_ge_cota": False, "perdida_no_menor_que_nula": False, "puntaje_bajo_tolerancia": True}
    assert m.degenerado and m.motivo_degenerado == "puntaje_bajo_tolerancia"


def test_una_mf_sana_no_es_degenerada_y_su_perdida_nula_es_a_mano():
    P, _, _ = _problema_chico()
    m = _mf_chica(P)
    assert m.condiciones_degenerado == {"lambda_ge_cota": False, "perdida_no_menor_que_nula": False,
                                        "puntaje_bajo_tolerancia": False}
    assert not m.degenerado and m.motivo_degenerado is None
    assert m.perdida_nula == pytest.approx((1 + 3.0) * P.sum())                # L(0,0) = (1 + α)·|train|
    assert m.historial_perdida[-1] < m.perdida_nula


def test_motivo_perdida_no_menor_que_nula_por_separado():
    """λ = 0,9·(1 + α)σ_max (bajo la cota), 1 barrido y una inicialización pequeña: ajustar desde cerca del punto de silla
    en 0 deja la pérdida por encima de L(0, 0) aunque los puntajes (≈ 2e-4) superan la tolerancia. Caso fijado con semilla 0."""
    P, _, _ = _problema_chico()
    sigma, alfa = float(np.linalg.norm(P, 2)), 3.0
    m = _mf_chica(P, regularizacion=0.9 * (1 + alfa) * sigma, alfa=alfa, iteraciones=1, escala_inicial=0.01)
    assert m.condiciones_degenerado == {"lambda_ge_cota": False, "perdida_no_menor_que_nula": True,
                                        "puntaje_bajo_tolerancia": False}
    assert m.historial_perdida[-1] >= m.perdida_nula and m.max_abs_puntaje > m.tolerancia_degenerado
    assert m.degenerado and m.motivo_degenerado == "perdida_no_menor_que_nula"


def test_el_motivo_queda_en_cada_ensayo_de_hpo_ensayos(tmp_path):
    cfg = _cfg_busqueda_mixta(tmp_path, 1.0e-3, 1.0e+4)
    assert hpo.main(cfg) == 0
    fam = load_json(tmp_path / "res" / "hpo_ensayos.json")["familias"]["mf_als"]
    for e in fam["ensayos"]:
        assert (e["motivo_degenerado"] is not None) == e["degenerado"]
        assert set(e["condiciones_degenerado"]) == {"lambda_ge_cota", "perdida_no_menor_que_nula", "puntaje_bajo_tolerancia"}
    assert any(e["motivo_degenerado"] == "lambda_ge_cota" for e in fam["ensayos"])
    assert "si y solo si" in fam["cota_solucion_nula"]["nota"] and "punto de silla" in fam["cota_solucion_nula"]["nota"]


# =========================================================================== auditoría de fugas del arnés (auditor-fugas, JJ-4)
class _Espia:
    """Modelo espía para el arnés: guarda la tabla que recibe en ``ajustar`` y puntúa 0 a todo (todo es empate), así la lista
    sale SOLO del desempate. No consume el ``rng``: el orden debe ser exactamente el de ``ordenar_candidatos`` con
    ``make_rng(base_seed, run_id)`` sobre los candidatos D10."""

    nombre = "espia"
    vistos: list = []

    def __init__(self) -> None:
        self.hiperparametros: dict = {}
        self._n = 0

    def ajustar(self, inter, catalogo, rng):
        _Espia.vistos.append(inter.copy())
        self._n = len(np.asarray(catalogo))
        return self

    def puntuar(self, usuario_ids):
        return np.zeros((len(usuario_ids), self._n))

    def n_parametros(self) -> int:
        return 0

    def diagnosticos(self) -> dict:
        return {}

    def guardar(self, carpeta, semilla, evidencia) -> list:
        return []

    descripcion_frios = "espía: puntaje constante"


@pytest.mark.parametrize("modelos", [["espia"], ["popularidad", "espia"]])
def test_el_arnes_entrega_la_particion_intacta_y_el_desempate_no_mira_el_objetivo(tmp_path, monkeypatch, modelos):
    """D9/D10 a nivel del arnés (no solo del modelo): (1) cada ``ajustar`` recibe la tabla con el ``split`` del parquet sin
    tocar (ni prueba ni validación reetiquetadas como train); (2) con puntajes constantes, la lista guardada es exactamente la
    del desempate al azar sobre C_u: el arnés no altera los puntajes ni el desempate con el objetivo de prueba."""
    inter = montar_sintetico(tmp_path / "proc")
    _Espia.vistos = []
    monkeypatch.setitem(referencias.MODELOS, "espia", lambda cfg: _Espia())
    cfg = cfg_sintetica(tmp_path, ["mf_als.hiperparametros_desde=config", "busqueda.ejecutar_en_experimento=false"])
    cfg["modelos"] = list(modelos)
    assert experimento.main(cfg) == 0
    assert len(_Espia.vistos) == cfg["semillas"]["n"]
    for visto in _Espia.vistos:
        pd.testing.assert_frame_equal(visto.reset_index(drop=True), inter.reset_index(drop=True))
    cat = pd.read_parquet(tmp_path / "proc" / "destinos.parquet")["destino_id"].to_numpy("int64")
    cands = particion.candidatos(inter, cat, "prueba")
    k_max = max(max(metricas.normalizar_k(cfg["evaluacion"]["k"])), cfg["evaluacion"]["top_guardar"])
    rec = pd.read_parquet(tmp_path / "res" / "recomendaciones_prueba.parquet")
    for run_id in range(cfg["semillas"]["n"]):
        rng = make_rng(cfg["semillas"]["base_seed"], run_id)
        g = rec[(rec["modelo"] == "espia") & (rec["semilla"] == cfg["semillas"]["base_seed"] + run_id)]
        for u in sorted(cands):
            lista = metricas.ordenar_candidatos(np.zeros(len(cands[u])), cands[u], k_max, rng)
            esperado = lista[:cfg["evaluacion"]["top_guardar"]]
            obtenido = g[g["usuario_id"] == u].sort_values("rango")["destino_id"].to_numpy()
            assert np.array_equal(obtenido, esperado), f"usuario {u}, run {run_id}: el arnés alteró la lista"
    if "popularidad" in modelos:                    # el puntaje guardado es el conteo de train del parquet (D9, D11)
        pop = particion.popularidad_train(inter, cat)
        rp = rec[rec["modelo"] == "popularidad"]
        assert np.array_equal(rp["puntaje"].to_numpy(), pop.reindex(rp["destino_id"]).to_numpy(dtype=float))


def test_la_mf_no_crea_factores_para_usuarios_sin_train():
    """El índice de X depende solo de train: usuarios con solo validación/prueba no cambian X, Y ni usuario_ids y no se
    pueden puntuar (en los datos reales no existen, porque n_u = 1 va a train, pero la MF no debe depender de eso)."""
    inter, cat = _datos_chicos()
    ids = cat["destino_id"]
    base_tabla = inter[["usuario_id", "destino_id", "split"]]
    extra = pd.DataFrame({"usuario_id": [9001, 9002], "destino_id": [int(ids.iloc[0]), int(ids.iloc[1])],
                          "split": ["prueba", "validacion"]})
    con_extra = pd.concat([base_tabla, extra], ignore_index=True)
    hp = dict(factores=4, regularizacion=0.1, alfa=10.0, iteraciones=3)
    a = referencias.MFImplicitaALS(**hp).ajustar(base_tabla, ids, make_rng(1, 0))
    b = referencias.MFImplicitaALS(**hp).ajustar(con_extra, ids, make_rng(1, 0))
    assert np.array_equal(a.usuario_ids, b.usuario_ids) and np.array_equal(a.X, b.X) and np.array_equal(a.Y, b.Y)
    with pytest.raises(ValueError):
        b.puntuar([9001])


# =========================================================================== arnés genérico: búsqueda, diagnósticos, guardado
class _EspiaConBusqueda:
    """Modelo espía CON búsqueda registrada (``hpo.BUSQUEDAS``): el arnés debe asignarle su presupuesto e hiperparámetros, pedirle
    ``diagnosticos()`` y ``guardar()`` y detener la corrida si se declara degenerado, SIN ningún caso especial por nombre."""

    nombre = "espia_busqueda"
    descripcion_frios = "espía: puntaje constante"

    def __init__(self, hiperparametros: dict, degenerado: bool = False) -> None:
        self.hiperparametros = dict(hiperparametros)
        self._degenerado, self._n = degenerado, 0

    def ajustar(self, inter, catalogo, rng):
        self._n = len(np.asarray(catalogo))
        return self

    def puntuar(self, usuario_ids):
        return np.zeros((len(usuario_ids), self._n))

    def n_parametros(self) -> int:
        return 5

    def diagnosticos(self) -> dict:
        return {"degenerado": self._degenerado, "motivo_degenerado": "espia" if self._degenerado else None,
                "n_parametros_con_datos": 7}

    def guardar(self, carpeta, semilla, evidencia) -> list:
        ruta = Path(carpeta) / "espia_busqueda.txt"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(f"semilla {semilla} a={self.hiperparametros['a']}", encoding="utf-8")
        return [ruta]


FAMILIA_ESPIA = {"n_ensayos": 7, "mejor": {"numero": 3, "params": {"a": 3}, "valor": 0.5}, "tiempo_total_s": 1.5,
                 "objetivo_nombre": "ndcg@5"}


def _cfg_espia(tmp_path, monkeypatch, ejecutar: bool, degenerado: bool = False) -> dict:
    montar_sintetico(tmp_path / "proc")
    monkeypatch.setitem(referencias.MODELOS, "espia_busqueda",
                        lambda cfg: _EspiaConBusqueda(cfg["espia_busqueda"]["hiperparametros"], degenerado))
    monkeypatch.setitem(hpo.BUSQUEDAS, "espia_busqueda", lambda cfg, inter, catalogo: dict(FAMILIA_ESPIA))
    cfg = cfg_sintetica(tmp_path, [f"busqueda.ejecutar_en_experimento={str(ejecutar).lower()}"])
    cfg["modelos"] = ["popularidad", "espia_busqueda"]
    cfg["espia_busqueda"] = {"hiperparametros_desde": "hpo", "hiperparametros": {"a": 1}}
    return cfg


@pytest.mark.parametrize("ejecutar", [True, False], ids=["busqueda_en_el_experimento", "busqueda_desde_el_archivo"])
def test_el_arnes_trata_igual_a_cualquier_modelo_con_busqueda_registrada(tmp_path, monkeypatch, ejecutar):
    cfg = _cfg_espia(tmp_path, monkeypatch, ejecutar)
    if not ejecutar:                                   # la familia ya está en hpo_ensayos.json (como la deja m3-hpo)
        huella = particion.huella(pd.read_parquet(tmp_path / "proc" / "interacciones.parquet"))
        hpo.escribir_familia(tmp_path / "res", {"particion_huella": huella}, "espia_busqueda", dict(FAMILIA_ESPIA))
    assert experimento.main(cfg) == 0
    resumen = load_json(tmp_path / "res" / "summary.json")
    s = resumen["modelos"]
    e = s["espia_busqueda"]
    assert e["hiperparametros"] == {"a": 3}                                          # el mejor de su familia, no el de respaldo
    assert e["n_configuraciones_busqueda"] == 7 and e["tiempo_busqueda_s"] == 1.5 and e["hiperparametros_origen"] == "hpo"
    assert e["tiempo_total_s"] == pytest.approx(1.5 + e["tiempo_corridas_finales_s"])
    assert e["diagnosticos"]["n_parametros_con_datos"]["media"] == 7 and e["diagnosticos"]["degenerado"] is False
    p = s["popularidad"]                                                             # sin búsqueda: presupuesto 1 y 0 s
    assert p["n_configuraciones_busqueda"] == 1 and p["tiempo_busqueda_s"] == 0.0 and p["hiperparametros_origen"] == "ninguno"
    assert (tmp_path / "mod" / "espia_busqueda.txt").read_text(encoding="utf-8") == "semilla 0 a=3"   # guardar() de la semilla 0
    j = load_json(tmp_path / "res" / "semillas" / "espia_busqueda_seed1.json")
    assert j["diagnosticos"]["n_parametros_con_datos"] == 7 and j["hiperparametros"] == {"a": 3}
    assert "espia_busqueda" in load_json(tmp_path / "res" / "hpo_ensayos.json")["familias"]
    assert resumen["destinos_frios"]["tratamiento"]["espia_busqueda"] == "espía: puntaje constante"


def test_el_arnes_detiene_cualquier_modelo_que_se_declare_degenerado(tmp_path, monkeypatch):
    cfg = _cfg_espia(tmp_path, monkeypatch, ejecutar=True, degenerado=True)
    with pytest.raises(ValueError, match="degenerad"):
        experimento.main(cfg)
    assert not (tmp_path / "res" / "summary.json").exists()


def test_un_modelo_con_busqueda_sin_su_familia_en_el_archivo_es_un_error_claro(tmp_path, monkeypatch):
    cfg = _cfg_espia(tmp_path, monkeypatch, ejecutar=False)
    huella = particion.huella(pd.read_parquet(tmp_path / "proc" / "interacciones.parquet"))
    hpo.escribir_familia(tmp_path / "res", {"particion_huella": huella}, "otra_familia", {"n_ensayos": 1})
    with pytest.raises(ValueError, match="espia_busqueda"):
        experimento.main(cfg)


# =========================================================================== semillas/, grupos vacíos y esperados válidos
def test_semillas_borra_solo_los_archivos_viejos_de_los_modelos_que_se_corren(tmp_path):
    montar_sintetico(tmp_path / "proc")
    sem = tmp_path / "res" / "semillas"
    sem.mkdir(parents=True)
    (sem / "otro_modelo_seed0.json").write_text("{}", encoding="utf-8")                  # de un modelo que NO se corre
    assert experimento.main(cfg_sintetica(tmp_path, ["semillas.n=3", "modelos=[popularidad]"])) == 0
    assert len(list(sem.glob("popularidad_seed*.json"))) == 3
    assert experimento.main(cfg_sintetica(tmp_path, ["semillas.n=2", "modelos=[popularidad]"])) == 0
    assert sorted(p.name for p in sem.glob("popularidad_seed*.json")) == ["popularidad_seed0.json", "popularidad_seed1.json"]
    assert (sem / "otro_modelo_seed0.json").is_file()


def test_un_grupo_sin_usuarios_se_reporta_con_cero_usuarios_y_sin_nan(tmp_path):
    """Con umbral_pocas_max = 1 nadie en prueba (todos tienen >= 2 interacciones) es «pocas»: el grupo aparece con
    n_usuarios = 0 y sin métricas, y no tiene esperado analítico (no hay usuarios que promediar)."""
    montar_sintetico(tmp_path / "proc")
    assert experimento.main(cfg_sintetica(tmp_path, ["evaluacion.umbral_pocas_max=1"])) == 0
    g = load_json(tmp_path / "res" / "metricas_por_grupo.json")          # save_json rechaza NaN: llegar aquí ya lo descarta
    assert g["modelos"]["mf_als"]["pocas"] == {"n_usuarios": 0}
    assert g["modelos"]["mf_als"]["muchas"]["n_usuarios"] > 0 and "pocas" not in g["aleatorio_analitico"]
    s = load_json(tmp_path / "res" / "semillas" / "mf_als_seed0.json")
    assert s["metricas"]["por_grupo"]["pocas"] == {"n_usuarios": 0}


@pytest.mark.parametrize("llamada", [
    lambda: metricas.esperado_acierto(0, 3),
    lambda: metricas.esperado_precision(0, 3),
    lambda: metricas.esperado_recall(0, 3),
    lambda: metricas.esperado_ndcg(0, 3),
    lambda: metricas.esperado_acierto(5, 3, n_rel=6),
    lambda: metricas.esperado_acierto_lugar(10, 11, 3),
    lambda: metricas.esperado_acierto_lugar(10, -1, 3),
    lambda: metricas.esperado_cobertura([np.array([], dtype=int)], [1, 2], 1),
    lambda: metricas.esperados_aleatorio({1: np.array([], dtype=int)}, {1: {1}}, {1: "A"}, [1], [1], [1]),
])
def test_esperados_analiticos_validan_los_tamanos(llamada):
    with pytest.raises(ValueError):
        llamada()


# =========================================================================== errores de configuración y entradas
@pytest.mark.parametrize("malo", [[], 0, "3", True, [1, 0], [1, 2.5], None])
def test_normalizar_k_rechaza_entradas_invalidas(malo):
    with pytest.raises((TypeError, ValueError)):
        metricas.normalizar_k(malo)


def test_normalizar_k_acepta_entero_o_lista_y_ordena():
    assert metricas.normalizar_k(3) == [3] and metricas.normalizar_k([10, 1, 3, 3]) == [1, 3, 10]


PARAMS_MINIMOS = {"factores": 2, "regularizacion": 0.1, "alfa": 1.0, "iteraciones": 1}


def _cfg_hpo_con(extra=()):
    return apply_overrides(load_config(CFG_HPO), list(extra))


def test_buscar_mf_rechaza_un_espacio_con_claves_faltantes_o_sobrantes():
    inter, cat = _datos_chicos()
    cfg = _cfg_hpo_con()
    faltante = {k: v for k, v in cfg["busqueda"]["espacio"].items() if k != "alfa"}
    sobrante = {**cfg["busqueda"]["espacio"], "extra": {"tipo": "real", "min": 0.1, "max": 1.0}}
    for espacio in (faltante, sobrante):
        malo = {**cfg, "busqueda": {**cfg["busqueda"], "espacio": espacio}}
        with pytest.raises(ValueError, match="espacio"):
            hpo.buscar_mf(malo, inter, cat["destino_id"])


def test_buscar_mf_rechaza_un_tipo_de_parametro_desconocido():
    inter, cat = _datos_chicos()
    cfg = _cfg_hpo_con(["busqueda.n_ensayos=1"])
    cfg["busqueda"]["espacio"]["alfa"]["tipo"] = "categorico"
    with pytest.raises(ValueError, match="tipo"):
        hpo.buscar_mf(cfg, inter, cat["destino_id"])


def test_objetivo_invalido_es_un_error_claro():
    inter, cat = _datos_chicos()
    cfg = _cfg_hpo_con(["busqueda.objetivo=precision"])
    with pytest.raises(ValueError, match="busqueda.objetivo"):
        hpo.evaluar_configuracion(inter, cat["destino_id"], PARAMS_MINIMOS, cfg)


def test_evaluar_configuracion_sin_columna_split_es_un_error_claro():
    inter, cat = _datos_chicos()
    with pytest.raises(ValueError, match="split"):
        hpo.evaluar_configuracion(inter.drop(columns="split"), cat["destino_id"], PARAMS_MINIMOS, _cfg_hpo_con())


def test_hiperparametros_desde_invalido_es_un_error_claro(tmp_path):
    montar_sintetico(tmp_path / "proc")
    cfg = cfg_sintetica(tmp_path, ["mf_als.hiperparametros_desde=archivo", "busqueda.ejecutar_en_experimento=false"])
    with pytest.raises(ValueError, match="hiperparametros_desde"):
        experimento.main(cfg)


def test_modelo_desconocido_es_un_error_claro(tmp_path):
    montar_sintetico(tmp_path / "proc")
    with pytest.raises(ValueError, match="desconocidos"):
        experimento.main(cfg_sintetica(tmp_path, ["modelos=[popularidad, no_registrado]"]))   # «red» existe desde JJ-5


def test_la_familia_trae_objetivo_nombre_y_la_consola_lo_usa(tmp_path, capsys):
    montar_sintetico(tmp_path / "proc")
    cfg = cfg_sintetica(tmp_path, base=CFG_HPO, extra=["busqueda.n_ensayos=2", "busqueda.objetivo_k=3"])
    assert hpo.main(cfg) == 0
    fam = load_json(tmp_path / "res" / "hpo_ensayos.json")["familias"]["mf_als"]
    assert fam["objetivo_nombre"] == "ndcg@3"
    assert f"{fam['objetivo_nombre']} = " in capsys.readouterr().out


def test_hpo_sin_ningun_modelo_con_busqueda_es_un_error_claro(tmp_path):
    montar_sintetico(tmp_path / "proc")
    with pytest.raises(ValueError, match="búsqueda"):
        hpo.main(cfg_sintetica(tmp_path, ["modelos=[popularidad]"], base=CFG_HPO))


def test_la_mf_expone_diagnosticos_y_guardar_escribe_sus_factores(tmp_path):
    P, _, _ = _problema_chico()
    m = _mf_chica(P)
    d = m.diagnosticos()
    assert d["degenerado"] is False and d["motivo_degenerado"] is None and d["max_abs_puntaje"] == m.max_abs_puntaje
    assert d["n_parametros_con_datos"] == m.n_parametros_con_datos()
    assert set(d["condiciones_degenerado"]) == set(m.condiciones_degenerado)
    archivos = m.guardar(tmp_path, 4, {"particion_huella": "h"})
    assert sorted(a.name for a in archivos) == ["mf_als.json", "mf_als.npz"] and all(a.is_file() for a in archivos)
    assert np.array_equal(np.load(tmp_path / "mf_als.npz")["X"], m.X)
    assert referencias.Popularidad().diagnosticos() == {} and referencias.Aleatorio().guardar(tmp_path, 0, {}) == []
