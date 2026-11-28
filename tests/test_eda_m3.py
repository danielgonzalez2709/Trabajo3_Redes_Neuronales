"""Pruebas sin red de src/m3_recomendacion/eda.py y src/viz/figs_m3.py (JJ-2): análisis descriptivo de M3 (núcleo §5.12).

Todo con un conjunto de juguete construido aquí (ficticio, semilla fija) escrito como parquet en ``tmp_path``; ninguna
prueba lee ``data/raw`` ni usa datos reales, salvo la prueba final, que compara con ``ficha.json`` si existen.

Definiciones que estas pruebas FIJAN (las usa eda.py):
  Gini (sin corrección)   G = 2·Σ_i i·x_(i) / (n·Σx) − (n+1)/n, con x ordenado ascendente e i = 1…n; máximo (n−1)/n.
  Gini reescalado         G·n/(n−1), en [0, 1] (reescalado, NO una corrección de sesgo).
  HHI                     Σ s_i², con las cuotas s_i = x_i/Σx en [0, 1]; mínimo 1/n, máximo 1.
  HHI normalizado         (HHI − 1/n)/(1 − 1/n), en [0, 1].
  cuota del top f         suma de los k = ceil(f·n) mayores (al menos 1) sobre la suma total.
  Lorenz                  vértices (j/n, suma de los j menores / suma total), j = 0…n.
  Holm                    p_(j) ajustado = max_{i<=j} min(1, (m − i + 1)·p_(i)), con p ordenados ascendente.
  p de permutación        (1 + #{T* >= T_obs}) / (1 + B).

Cálculo a mano con los conteos [0, 1, 1, 2, 6] (n = 5, suma = 10):
  Σ i·x_(i) = 1·0 + 2·1 + 3·1 + 4·2 + 5·6 = 43  →  G = 2·43/(5·10) − 6/5 = 1,72 − 1,2 = 0,52 (reescalado 0,52·5/4 = 0,65)
  comprobación por diferencias medias: Σ_{i,j} |x_i − x_j| = 2·26 = 52 → G = 52/(2·5²·2) = 0,52
  cuotas 0; 0,1; 0,1; 0,2; 0,6 → HHI = 0,01 + 0,01 + 0,04 + 0,36 = 0,42; normalizado (0,42 − 0,2)/0,8 = 0,275
  top 10 % → k = ceil(0,5) = 1 → 0,6; top 20 % → k = 1 → 0,6; top 40 % → k = 2 → 0,8; top 60 % → k = 3 → 0,9
  Lorenz: x = 0; 0,2; 0,4; 0,6; 0,8; 1 → y = 0; 0; 0,1; 0,2; 0,4; 1

Línea base de la tasa de coincidencia, catálogo de 6 ids con tipos A, A, A, A, B, C:
  usuario 1 prefiere {A, B}, usuario 2 prefiere {B, C}; interacciones: u1→A, u1→C, u2→A
  coincide: sí, no, no → tasa = 1/3
  línea base exacta (destino uniforme en el catálogo): u1 → (4 + 1)/6 = 5/6 (dos interacciones), u2 → (1 + 1)/6 = 1/3
  → (5/6 + 5/6 + 1/3)/3 = 2/3
  línea base marginal (tipos de las interacciones: A 2/3, C 1/3, B 0): u1 → 2/3, u2 → 1/3 → (2/3 + 2/3 + 1/3)/3 = 5/9
  diferencia = 1/3 − 2/3 = −1/3
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.comun.config import load_config
from src.comun.eda import validar_hipotesis
from src.comun.seeds import make_rng
from src.m3_recomendacion import datos as dm
from src.m3_recomendacion import eda
from src.viz import figs_m3

RAIZ = Path(__file__).resolve().parents[1]
CONFIG = RAIZ / "configs" / "m3" / "eda.yaml"
COMBOS = ["Beaches, Historical", "Adventure, Nature", "City, Historical"]
TIPOS_JUGUETE = ["Adventure"] * 5 + ["Beach"] * 10 + ["City"] * 5 + ["Historical"] * 5 + ["Nature"] * 5


# --------------------------------------------------------------------------- conjunto de juguete
def montar(tmp_path: Path, n_perm: int = 200, n_boot: int = 100, n_sim: int = 100) -> dict:
    """Escribe parquet ficticios (30 destinos de tipos desiguales, 60 usuarios) y devuelve la config apuntándolos."""
    rng = np.random.default_rng(123)
    proc = tmp_path / "proc"
    proc.mkdir(parents=True)
    tipos = TIPOS_JUGUETE
    nombres = {"Adventure": "adventure_land", "Beach": "beach_town", "City": "city_town", "Historical": "old_fort",
               "Nature": "green_park"}
    destinos = pd.DataFrame({
        "destino_id": np.arange(1, 31), "nombre": [nombres[t] for t in tipos], "lugar": [nombres[t] for t in tipos],
        "estado": "Estado", "tipo": tipos, "mejor_epoca": "Nov-Feb", "popularidad": rng.uniform(7.5, 9.5, 30)})
    n_u = 60
    usuarios = pd.DataFrame({
        "usuario_id": np.arange(1, n_u + 1), "preferencias": [COMBOS[i % 3] for i in range(n_u)],
        "pref_adventure": False, "pref_beaches": False, "pref_city": False, "pref_historical": False, "pref_nature": False,
        "genero": ["Male" if i % 2 else "Female" for i in range(n_u)],
        "n_adultos": [1 + (i % 2) for i in range(n_u)], "n_ninos": [i % 3 for i in range(n_u)]})
    filas = []
    for u in range(1, n_u + 1):
        for k in range(int(rng.integers(0, 5))):   # 0 a 4 interacciones por usuario
            filas.append((u, int(rng.choice(np.arange(1, 31), replace=False)), "resena" if k % 2 == 0 else "historial",
                          len(filas) + 1, int(rng.integers(1, 6)), "2024-01-01"))
    inter = pd.DataFrame(filas, columns=dm.COLUMNAS_INTERACCIONES)
    inter = inter.drop_duplicates(["usuario_id", "destino_id"]).reset_index(drop=True)
    inter["fecha_visita"] = pd.to_datetime(inter["fecha_visita"])
    destinos.to_parquet(proc / "destinos.parquet", index=False)
    usuarios.to_parquet(proc / "usuarios.parquet", index=False)
    inter.to_parquet(proc / "interacciones.parquet", index=False)
    cfg = load_config(CONFIG)
    cfg["entrada"]["carpeta"] = str(proc)
    cfg["salida"]["carpeta"] = str(tmp_path / "eda")
    cfg["figuras"]["carpeta"] = str(tmp_path / "fig")
    cfg["n_permutaciones"], cfg["n_bootstrap"], cfg["n_simulaciones_azar"] = n_perm, n_boot, n_sim
    return cfg


@pytest.fixture(scope="module")
def corrida(tmp_path_factory):
    """Una sola corrida de ``main`` sobre el conjunto de juguete, compartida por las pruebas que solo leen sus salidas."""
    cfg = montar(tmp_path_factory.mktemp("eda_juguete"))
    assert eda.main(cfg) == 0
    return cfg, Path(cfg["salida"]["carpeta"])


# --------------------------------------------------------------------------- concentración (a mano)
X = [0, 1, 1, 2, 6]


def test_gini_a_mano():
    assert eda.gini(X) == pytest.approx(0.52)
    assert eda.gini_reescalado(X) == pytest.approx(0.65)
    assert eda.gini([6, 0, 2, 1, 1]) == pytest.approx(0.52)   # no depende del orden


def test_gini_casos_borde():
    assert eda.gini([3, 3, 3, 3]) == pytest.approx(0.0)
    assert eda.gini_reescalado([3, 3, 3, 3]) == pytest.approx(0.0)
    assert eda.gini([0, 0, 0, 10]) == pytest.approx(0.75)           # (n-1)/n
    assert eda.gini_reescalado([0, 0, 0, 10]) == pytest.approx(1.0)
    with pytest.raises(ValueError, match="suma"):
        eda.gini([0, 0, 0])


def test_gini_por_filas_coincide_con_cada_fila():
    m = np.array([X, [3, 3, 3, 3, 3], [0, 0, 0, 0, 10]])
    np.testing.assert_allclose(eda.gini(m), [0.52, 0.0, 0.8])


def test_hhi_a_mano_y_borde():
    assert eda.hhi(X) == pytest.approx(0.42)
    assert eda.hhi_normalizado(X) == pytest.approx(0.275)
    assert eda.hhi([3, 3, 3, 3]) == pytest.approx(0.25)             # 1/n
    assert eda.hhi_normalizado([3, 3, 3, 3]) == pytest.approx(0.0)
    assert eda.hhi([0, 0, 0, 10]) == pytest.approx(1.0)
    assert eda.hhi_normalizado([0, 0, 0, 10]) == pytest.approx(1.0)


def test_cuota_top_a_mano_y_borde():
    assert eda.cuota_top(X, 0.1) == pytest.approx(0.6)
    assert eda.cuota_top(X, 0.2) == pytest.approx(0.6)
    assert eda.cuota_top(X, 0.4) == pytest.approx(0.8)
    assert eda.cuota_top(X, 0.6) == pytest.approx(0.9)
    assert eda.cuota_top([0, 0, 0, 10], 0.1) == pytest.approx(1.0)
    assert eda.cuota_top([3, 3, 3, 3], 0.5) == pytest.approx(0.5)
    # 10 % de 1000 entidades = exactamente 100 (sin errores de redondeo flotante)
    assert eda.cuota_top(np.arange(1, 1001), 0.1) == pytest.approx(sum(range(901, 1001)) / sum(range(1, 1001)))


def test_lorenz_a_mano():
    xs, ys = eda.lorenz(X)
    np.testing.assert_allclose(xs, [0, 0.2, 0.4, 0.6, 0.8, 1.0])
    np.testing.assert_allclose(ys, [0, 0, 0.1, 0.2, 0.4, 1.0])
    _, ys_uno = eda.lorenz([0, 0, 0, 10])
    np.testing.assert_allclose(ys_uno, [0, 0, 0, 0, 1])
    _, ys_igual = eda.lorenz([3, 3, 3, 3])
    np.testing.assert_allclose(ys_igual, [0, 0.25, 0.5, 0.75, 1.0])


def test_gini_es_dos_veces_el_area_entre_la_diagonal_y_lorenz():
    """Con la corrección de n/(n-1) no hace falta: el área trapezoidal da exactamente el Gini sin corregir."""
    xs, ys = eda.lorenz(X)
    area = np.trapezoid(ys, xs)
    assert 1 - 2 * area == pytest.approx(eda.gini(X))


# --------------------------------------------------------------------------- estadística auxiliar
def test_holm_a_mano():
    # p = 0,01; 0,04; 0,03 (m = 3): ordenados 0,01; 0,03; 0,04 → 0,03; 0,06; 0,06 (monótonos)
    assert eda.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert eda.holm([0.5, 0.9]) == pytest.approx([1.0, 1.0])        # se recorta a 1
    assert eda.holm([0.001]) == pytest.approx([0.001])


def test_p_de_permutacion():
    nulos = [1, 2, 3, 4, 5]
    assert eda.p_permutacion(4, nulos, "mayor") == pytest.approx((1 + 2) / (1 + 5))
    assert eda.p_permutacion(100, nulos, "mayor") == pytest.approx(1 / 6)
    assert eda.p_permutacion(-2, [-3, -1, 1, 3], "dos_colas") == pytest.approx((1 + 2) / (1 + 4))


def test_delta_de_cliff_a_mano():
    # grupo 1: calificaciones {5, 3}; grupo 2: {1, 3, 4} → 4 victorias, 1 empate, 1 derrota de 6 pares
    d, ps = eda.delta_de_cliff([0, 0, 1, 0, 1], [1, 0, 1, 1, 0])
    assert d == pytest.approx((4 - 1) / 6)
    assert ps == pytest.approx((4 + 0.5) / 6)


def test_rho_de_spearman_a_mano():
    # 1 − 6·Σd²/(n(n²−1)) con d = 0, 1, 1, 0 → 1 − 6·2/(4·15) = 0,8
    assert eda.rho_de_spearman([1, 2, 3, 4], [1, 3, 2, 4]) == pytest.approx(0.8)


def test_histograma_de_actividad():
    h = eda.histograma_de_actividad([0, 1, 1, 2, 6], tope=5)
    assert list(h) == ["0", "1", "2", "3", "4", "5+"]
    assert list(h.values()) == [1, 2, 1, 0, 0, 1]


def test_simulacion_uniforme_conserva_el_total_y_es_determinista():
    a = eda.simular_uniforme(make_rng(0, 2), 100, 7, 50)
    b = eda.simular_uniforme(make_rng(0, 2), 100, 7, 50)
    assert a.shape == (50, 7) and (a.sum(axis=1) == 100).all()
    np.testing.assert_array_equal(a, b)
    assert not np.array_equal(a, eda.simular_uniforme(make_rng(0, 3), 100, 7, 50))


# --------------------------------------------------------------------------- coincidencia preferencia–tipo
EMPAREJ = {"Beaches": "Beach", "Historical": "Historical", "City": "City", "Adventure": "Adventure", "Nature": "Nature"}


def test_tipos_de_una_combinacion():
    assert eda.tipos_de_preferencias("Beaches, Historical", EMPAREJ) == frozenset({"Beach", "Historical"})
    with pytest.raises(ValueError, match="Surf"):
        eda.tipos_de_preferencias("Surf, City", EMPAREJ)


def test_tasa_y_lineas_base_a_mano():
    catalogo = pd.Series(["A", "A", "A", "A", "B", "C"])
    pref = {1: frozenset({"A", "B"}), 2: frozenset({"B", "C"})}
    r = eda.coincidencia(catalogo, usuarios=[1, 1, 2], tipos=["A", "C", "A"], preferidos_por_usuario=pref)
    assert r["n"] == 3 and r["n_coinciden"] == 1
    assert r["tasa"] == pytest.approx(1 / 3)
    assert r["linea_base_exacta"] == pytest.approx(2 / 3)
    assert r["linea_base_marginal"] == pytest.approx(5 / 9)
    assert r["diferencia_exacta"] == pytest.approx(-1 / 3)
    assert r["linea_base_exacta"] != pytest.approx(2 / 5)           # no es la 2/5 trivial: los tipos tienen distinto tamaño


def test_v_de_cramer_corregida_a_mano():
    """2×2 [[10, 20], [20, 10]]: n = 60, φ² = (20/3)/60 = 1/9; corrección (r−1)(c−1)/(n−1) = 1/59; r̃ = c̃ = 2 − 1/59 →
    V corregida = sqrt((1/9 − 1/59) / (1 − 1/59)) ≈ 0,3095 (frente a 0,3333 sin corregir)."""
    esperado = np.sqrt((1 / 9 - 1 / 59) / (1 - 1 / 59))
    t = np.array([[[10.0, 20.0], [20.0, 10.0]]])
    assert eda.v_corregida_por_lotes(t)[0] == pytest.approx(esperado)
    assert esperado == pytest.approx(0.3095, abs=5e-5)
    # sin asociación el valor ordinario es 0 y la corregida también (nunca negativa)
    assert eda.v_corregida_por_lotes(np.array([[[15.0, 15.0], [15.0, 15.0]]]))[0] == pytest.approx(0.0)


def test_v_corregida_queda_por_debajo_de_la_ordinaria_con_ruido():
    rng = np.random.default_rng(5)
    t = np.stack([np.bincount(rng.integers(0, 6, 300), minlength=6).reshape(2, 3).astype(float) for _ in range(20)])
    assert (eda.v_corregida_por_lotes(t) <= eda.v_de_cramer_por_lotes(t) + 1e-12).all()


def test_cramer_con_tabla_2x2_a_mano():
    # [[10, 20], [20, 10]]: esperado 15; χ² = 4·25/15 = 6,667; V = sqrt(6,667/60) = 1/3
    assert dm.chi2_y_v([[10, 20], [20, 10]])["v_de_cramer"] == pytest.approx(1 / 3)
    v = eda.v_de_cramer_por_lotes(np.array([[[10.0, 20.0], [20.0, 10.0]], [[15.0, 15.0], [15.0, 15.0]]]))
    np.testing.assert_allclose(v, [1 / 3, 0.0], atol=1e-12)


# --------------------------------------------------------------------------- criterio de veredicto
def test_veredicto_de_una_prueba():
    f = eda.veredicto_de_prueba
    assert f(0.001, 0.2, (0.15, 0.25), 0.1, 0.05, "dos_colas") == "cumple"
    assert f(0.001, 0.05, (0.03, 0.07), 0.1, 0.05, "dos_colas") == "indeterminada"   # detectable pero pequeño: no confirma
    assert f(0.5, 0.02, (-0.03, 0.07), 0.1, 0.05, "dos_colas") == "refuta"
    assert f(0.5, 0.02, (-0.15, 0.19), 0.1, 0.05, "dos_colas") == "indeterminada"     # IC ancho: no refuta
    # p ajustado >= alfa por el ajuste, pero el IC excluye el 0: efecto pequeño y detectable, no se refuta ni se confirma
    assert f(0.2, 0.0234, (0.0006, 0.0469), 0.05, 0.05, "mayor") == "indeterminada"
    assert f(0.2, 0.0234, (0.0006, 0.0469), 0.05, 0.05, "dos_colas") == "indeterminada"
    assert f(0.6, 0.0, (0.0, 0.08), 0.1, 0.05, "dos_colas") == "refuta"                 # el IC empieza en 0 (V no negativa)
    assert f(0.9, -0.1, (-0.15, -0.05), 0.2, 0.05, "mayor") == "refuta"                 # evidencia en contra
    assert f(0.001, -0.2, (-0.25, -0.15), 0.1, 0.05, "mayor") == "indeterminada"      # grande pero en sentido contrario
    assert f(0.001, -0.2, (-0.25, -0.15), 0.1, 0.05, "dos_colas") == "cumple"


def test_veredicto_de_una_hipotesis():
    g = eda.veredicto_de_hipotesis
    assert g(["indeterminada", "cumple"]) == "confirmada"
    assert g(["refuta", "refuta"]) == "refutada"
    assert g(["refuta", "indeterminada"]) == "no concluyente"
    assert g(["indeterminada"]) == "no concluyente"


# --------------------------------------------------------------------------- main
def test_hipotesis_json_valida_y_con_ids_correctos(corrida):
    _, out = corrida
    hip = json.loads((out / "hipotesis.json").read_text(encoding="utf-8"))
    validar_hipotesis(hip)
    assert [h["id"] for h in hip] == [f"H-M3-{i}" for i in range(1, len(hip) + 1)]
    assert len(hip) >= 7
    decididas = {h["id"]: h["veredicto"] for h in hip[:6]}
    assert all(v in {"confirmada", "refutada", "no concluyente"} for v in decididas.values()), decididas
    pendientes = [h for h in hip[6:]]
    assert pendientes and all(h["veredicto"] == "pendiente" for h in pendientes)
    assert any("JJ-10" in h["resultado"] for h in pendientes)
    assert "NDCG@5" in pendientes[0]["enunciado"]
    for h in hip:
        assert h["enunciado"] and h["justificacion"] and h["evidencia_esperada"] and h["figura_o_tabla"] and h["resultado"]


def test_el_veredicto_sigue_al_p_ajustado_y_al_efecto(corrida):
    """Cada veredicto de H-M3-1…6 se recalcula desde pruebas_hipotesis.json con el criterio de la config."""
    cfg, out = corrida
    pr = json.loads((out / "pruebas_hipotesis.json").read_text(encoding="utf-8"))
    hip = {h["id"]: h for h in json.loads((out / "hipotesis.json").read_text(encoding="utf-8"))}
    assert pr["ajuste"] == "holm" and pr["alfa"] == cfg["alfa"]
    conf = [p for p in pr["pruebas"] if p["familia"] == "confirmatoria"]
    assert pr["familia_confirmatoria"] == [p["id_prueba"] for p in conf]
    assert {p["hipotesis"] for p in conf} == {f"H-M3-{i}" for i in range(1, 7)}
    # Holm sobre las p crudas de la familia
    esperado = eda.holm([p["p_crudo"] for p in conf])
    assert [p["p_ajustado"] for p in conf] == pytest.approx(esperado)
    for h_id, h in hip.items():
        if h["veredicto"] == "pendiente":
            continue
        res = [eda.veredicto_de_prueba(p["p_ajustado"], p["efecto"]["valor"], tuple(p["efecto"]["ic95"]),
                                       cfg["efecto_minimo"][p["efecto"]["umbral"]], cfg["alfa"], p["alternativa"])
               for p in conf if p["hipotesis"] == h_id]
        assert eda.veredicto_de_hipotesis(res) == h["veredicto"], h_id
    for p in pr["pruebas"]:
        assert 0 < p["p_crudo"] <= 1 and p["n"] > 0
        if p["familia"] == "complementaria":
            assert p["p_ajustado"] is None


def test_p_minimo_de_permutacion_respeta_n_permutaciones(corrida):
    cfg, out = corrida
    pr = json.loads((out / "pruebas_hipotesis.json").read_text(encoding="utf-8"))
    minimo = 1 / (1 + cfg["n_permutaciones"])
    for p in pr["pruebas"]:
        if p["metodo_p"].startswith("permutación"):
            assert p["p_crudo"] >= minimo - 1e-15


def test_actividad_coincide_con_el_calculo_de_datos(corrida):
    """El histograma de usuarios debe ser el que usa ficha.json (``datos.usuarios_por_numero``)."""
    cfg, out = corrida
    proc = Path(cfg["entrada"]["carpeta"])
    inter = pd.read_parquet(proc / "interacciones.parquet")
    usr = pd.read_parquet(proc / "usuarios.parquet")
    esperado = dm.usuarios_por_numero(inter, usr["usuario_id"], cfg["tope_usuarios"])
    dist = json.loads((out / "distribucion_actividad.json").read_text(encoding="utf-8"))
    assert dist["usuarios"]["observado"] == esperado
    assert sum(dist["usuarios"]["observado"].values()) == len(usr)
    assert sum(dist["destinos"]["observado"].values()) == 30
    for nivel in ("usuarios", "destinos"):
        d = dist[nivel]
        assert list(d["azar_media"]) == list(d["observado"])
        # la media simulada suma el número de entidades; el IC tiene lo <= hi
        assert sum(d["azar_media"].values()) == pytest.approx(sum(d["observado"].values()))
        for lo, hi in d["azar_ic95"].values():
            assert lo <= hi


def test_main_compara_con_ficha_si_existe(tmp_path):
    cfg = montar(tmp_path)
    out = Path(cfg["salida"]["carpeta"])
    proc = Path(cfg["entrada"]["carpeta"])
    inter = pd.read_parquet(proc / "interacciones.parquet")
    usr = pd.read_parquet(proc / "usuarios.parquet")
    bueno = dm.usuarios_por_numero(inter, usr["usuario_id"], cfg["tope_usuarios"])
    from src.comun.results import save_json
    save_json(out / "ficha.json", {"conteos": {"usuarios_por_numero_de_interacciones": {"union": bueno}}})
    assert eda.main(cfg) == 0
    malo = {"union": {**bueno, "0": bueno["0"] + 1}}
    save_json(out / "ficha.json", {"conteos": {"usuarios_por_numero_de_interacciones": malo}})
    with pytest.raises(ValueError, match="ficha.json"):
        eda.main(cfg)


def test_concentracion_estructura(corrida):
    cfg, out = corrida
    c = json.loads((out / "concentracion.json").read_text(encoding="utf-8"))
    assert set(c["niveles"]) == {"destino_id", "lugar"}
    for nombre, n in (("destino_id", 30), ("lugar", 5)):
        nivel = c["niveles"][nombre]
        assert nivel["n_entidades"] == n
        obs = nivel["observado"]
        assert 0 <= obs["gini"] <= (n - 1) / n and 1 / n <= obs["hhi"] <= 1
        assert set(obs["cuota_top"]) == {"0.1", "0.2"}
        assert len(obs["lorenz"]["x"]) == len(obs["lorenz"]["y"]) == n + 1
        assert obs["lorenz"]["y"][0] == 0 and obs["lorenz"]["y"][-1] == pytest.approx(1.0)
        azar = nivel["azar_uniforme"]
        assert azar["n_simulaciones"] == cfg["n_simulaciones_azar"]
        lo, hi = azar["gini"]["ic95"]
        assert lo <= azar["gini"]["media"] <= hi
        assert 0 < azar["gini"]["p_observado_mayor_o_igual"] <= 1
        assert len(azar["lorenz"]["media"]) == n + 1


def test_actividad_de_usuarios_a_mano(corrida):
    cfg, out = corrida
    proc = Path(cfg["entrada"]["carpeta"])
    inter = pd.read_parquet(proc / "interacciones.parquet")
    por_u = inter.groupby("usuario_id").size().reindex(range(1, 61), fill_value=0)
    a = json.loads((out / "actividad_usuarios.json").read_text(encoding="utf-8"))
    g = a["grupos"]
    assert g["sin_interacciones"]["n_usuarios"] == int((por_u == 0).sum())
    assert g["pocas"]["n_usuarios"] == int(por_u.between(1, 2).sum())
    assert g["muchas"]["n_usuarios"] == int((por_u >= 3).sum())
    assert sum(x["n_usuarios"] for x in g.values()) == 60
    # D3: prueba = 1 si n >= 2; validación = 1 si n >= 3; el resto, entrenamiento
    d3 = a["particion_d3"]
    assert d3["total"]["prueba"] == int((por_u >= 2).sum())
    assert d3["total"]["validacion"] == int((por_u >= 3).sum())
    assert d3["total"]["entrenamiento"] == len(inter) - d3["total"]["prueba"] - d3["total"]["validacion"]
    assert d3["pocas"]["usuarios_con_prueba"] == int((por_u == 2).sum())
    assert a["proporcion_pocas"]["sobre_usuarios_que_aparecen"] == pytest.approx(
        int(por_u.between(1, 2).sum()) / int((por_u >= 1).sum()))
    assert [s["pocas_max"] for s in a["sensibilidad_umbral"]] == cfg["actividad"]["sensibilidad_pocas_max"]


def test_coincidencia_en_la_corrida_y_matriz(corrida):
    cfg, out = corrida
    c = json.loads((out / "coincidencia_preferencias.json").read_text(encoding="utf-8"))
    proc = Path(cfg["entrada"]["carpeta"])
    cat = pd.read_parquet(proc / "destinos.parquet")
    inter = pd.read_parquet(proc / "interacciones.parquet")
    usr = pd.read_parquet(proc / "usuarios.parquet").set_index("usuario_id")
    pref = {u: eda.tipos_de_preferencias(t, cfg["emparejamiento_preferencia_tipo"]) for u, t in usr["preferencias"].items()}
    tipo = cat.set_index("destino_id")["tipo"]
    tipos = [tipo[d] for d in inter["destino_id"]]
    r = eda.coincidencia(cat["tipo"], inter["usuario_id"].tolist(), tipos, pref)
    assert c["global"]["tasa"] == pytest.approx(r["tasa"])
    assert c["global"]["linea_base_exacta"] == pytest.approx(r["linea_base_exacta"])
    assert c["global"]["linea_base_marginal"] == pytest.approx(r["linea_base_marginal"])
    lo, hi = c["global"]["diferencia_exacta_ic95"]
    assert lo <= hi
    assert set(c["por_combinacion"]) == set(COMBOS)
    assert sum(v["n"] for v in c["por_combinacion"].values()) == len(inter)
    m = pd.read_csv(out / "matriz_preferencias_tipo.csv")
    assert set(m["combinacion"]) == set(COMBOS) and set(m["tipo"]) == set(cat["tipo"])
    assert m.groupby("combinacion")["proporcion_fila"].sum().tolist() == pytest.approx([1.0] * 3)
    por_celda = m.set_index(["combinacion", "tipo"])
    assert bool(por_celda.loc[("Beaches, Historical", "Beach"), "coincide"])
    assert not bool(por_celda.loc[("Beaches, Historical", "City"), "coincide"])
    # línea base exacta de la combinación = fracción del catálogo con los tipos de la combinación (Beach 10 + Historical 5)/30
    assert por_celda.loc[("Beaches, Historical", "Beach"), "linea_base_fila"] == pytest.approx(15 / 30)


def test_calificaciones_csv(corrida):
    _, out = corrida
    df = pd.read_csv(out / "calificaciones.csv")
    assert set(df["origen"]) == {"resena", "historial", "union"}
    for _, g in df.groupby("origen"):
        assert sorted(g["calificacion"]) == [1, 2, 3, 4, 5]
        assert g["proporcion"].sum() == pytest.approx(1.0)
        assert g["conteo"].sum() == g["n_origen"].iloc[0]
    u = df[df["origen"] == "union"]
    assert u["media_origen"].iloc[0] == pytest.approx((u["calificacion"] * u["conteo"]).sum() / u["conteo"].sum())


def test_csv_por_entidad_incluyen_los_de_cero(corrida):
    cfg, out = corrida
    pu = pd.read_csv(out / "interacciones_por_usuario.csv")
    pd_ = pd.read_csv(out / "interacciones_por_destino.csv")
    pl = pd.read_csv(out / "interacciones_por_lugar.csv")
    assert len(pu) == 60 and len(pd_) == 30 and len(pl) == 5
    assert pu["n_interacciones"].sum() == pd_["n_interacciones"].sum() == pl["n_interacciones"].sum()
    assert (pu["n_interacciones"] == 0).any()
    assert (pu["n_interacciones"] == pu["n_resenas"] + pu["n_historial"]).all()


def test_salidas_deterministas_con_la_misma_config(tmp_path):
    cfg = montar(tmp_path)
    out = Path(cfg["salida"]["carpeta"])
    eda.main(cfg)
    primera = {p.name: p.read_bytes() for p in sorted(out.iterdir())}
    eda.main(cfg)
    segunda = {p.name: p.read_bytes() for p in sorted(out.iterdir())}
    assert set(primera) == set(segunda) and len(primera) >= 12
    assert primera == segunda


def test_la_semilla_cambia_las_salidas_aleatorias(tmp_path):
    cfg = montar(tmp_path)
    out = Path(cfg["salida"]["carpeta"])
    eda.main(cfg)
    a = (out / "pruebas_hipotesis.json").read_bytes()
    cfg["base_seed"] = 1000
    eda.main(cfg)
    assert (out / "pruebas_hipotesis.json").read_bytes() != a


def test_main_no_toca_los_archivos_de_m3_datos_ni_lee_raw(tmp_path, monkeypatch):
    cfg = montar(tmp_path)
    out = Path(cfg["salida"]["carpeta"])
    out.mkdir(parents=True)
    for nombre in ("calidad.csv", "diccionario.json"):
        (out / nombre).write_text("intacto", encoding="utf-8")
    leidos = []
    real_parquet, real_csv = pd.read_parquet, pd.read_csv

    def espia_parquet(ruta, *a, **k):
        leidos.append(str(ruta))
        return real_parquet(ruta, *a, **k)

    def espia_csv(ruta, *a, **k):
        leidos.append(str(ruta))
        return real_csv(ruta, *a, **k)

    monkeypatch.setattr(pd, "read_parquet", espia_parquet)
    monkeypatch.setattr(pd, "read_csv", espia_csv)
    monkeypatch.chdir(tmp_path)               # aquí no existe data/raw
    eda.main(cfg)
    assert leidos and all("raw" not in Path(r).parts for r in leidos)
    assert all(Path(r).suffix == ".parquet" for r in leidos)
    assert (out / "calidad.csv").read_text(encoding="utf-8") == "intacto"
    assert (out / "diccionario.json").read_text(encoding="utf-8") == "intacto"


MODULOS_EDA = ("eda.py", "eda_estadistica.py", "eda_hipotesis.py")


def test_eda_no_menciona_data_raw_ni_siembra_global():
    for nombre in MODULOS_EDA:
        fuente = (RAIZ / "src" / "m3_recomendacion" / nombre).read_text(encoding="utf-8")
        for nodo in ast.walk(ast.parse(fuente)):
            if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
                assert "data/raw" not in nodo.value and "raw/" not in nodo.value
        assert "np.random.seed" not in fuente, nombre


def test_la_config_tiene_run_ids_distintos_y_emparejamiento_explicito():
    cfg = load_config(CONFIG)
    ids = list(cfg["run_id"].values())
    assert len(ids) == len(set(ids))
    assert cfg["ajuste_multiple"] == "holm" and cfg["alfa"] == 0.05
    assert cfg["emparejamiento_preferencia_tipo"]["Beaches"] == "Beach"
    assert cfg["actividad"]["pocas_max"] == 2


# --------------------------------------------------------------------------- figuras
def test_generar_figuras_desde_resultados(corrida, tmp_path):
    cfg, out = corrida
    destino = tmp_path / "figuras"
    rutas = figs_m3.generar(carpeta_resultados=out, carpeta_figuras=destino)
    nombres = {r.name for r in rutas}
    assert nombres == {"cola_larga.png", "lorenz.png", "preferencias_tipo.png", "calificaciones_origen.png"}
    for r in rutas:
        assert r.parent == destino and r.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n" and r.stat().st_size > 5000


def test_figuras_usan_coma_decimal_y_espacio_de_miles():
    assert figs_m3._miles(1998) == "1 998" and figs_m3._miles(2000) == "2 000" and figs_m3._miles(57) == "57"
    assert figs_m3._coma(0.2, None) == "0,20" and figs_m3._coma(0.05, None) == "0,05" and figs_m3._coma(1.0, None) == "1,00"


def _filas(*pares):
    """Filas de la matriz de preferencias: (combinación, n de celdas recuadradas, línea base exacta de la fila)."""
    return [{"combinacion": c, "n_recuadradas": n, "linea_base": b} for c, n, b in pares]


def test_pie_de_la_linea_base_sale_de_los_resultados():
    coin = {"tasa": 0.423, "linea_base_exacta": 0.4, "ids_por_tipo": {"A": 200, "B": 200, "C": 200, "D": 200, "E": 200}}
    t = figs_m3.texto_linea_base(coin, _filas(("X", 2, 0.4), ("Y", 2, 0.4), ("Z", 2, 0.4)))
    assert "cada celda tendría 0,20" in t and "las 2 recuadradas 0,40" in t and "0,423" in t
    # tipos de distinto tamaño pero la misma suma por fila: no se afirma una celda única
    desigual = {"tasa": 0.5, "linea_base_exacta": 0.5, "ids_por_tipo": {"A": 100, "B": 300}}
    t = figs_m3.texto_linea_base(desigual, _filas(("X", 1, 0.5)))
    assert "cada celda tendría la fracción de ids de su tipo" in t and "cada celda tendría 0," not in t


def test_pie_no_afirma_una_suma_unica_si_las_filas_cubren_fracciones_distintas():
    """R1: combinaciones de distinto tamaño (1 tipo de 4 vs 2 tipos de 4) tienen líneas base distintas."""
    coin = {"tasa": 0.6, "linea_base_exacta": 0.375, "ids_por_tipo": {"A": 25, "B": 25, "C": 25, "D": 25}}
    t = figs_m3.texto_linea_base(coin, _filas(("Una", 1, 0.25), ("Dos", 2, 0.5)))
    assert "cada celda tendría 0,25" in t                      # el catálogo es uniforme: cada celda vale 0,25
    assert "la suma de las 2 recuadradas 0,40" not in t and "las 2 recuadradas 0,50" not in t
    assert "Una: 0,25" in t and "Dos: 0,50" in t               # se da la suma de cada fila, no una sola
    assert "0,600" in t and "0,375" in t


def test_generar_figuras_sin_resultados_dice_que_comando_correr(tmp_path):
    with pytest.raises(FileNotFoundError, match="run.py m3-eda"):
        figs_m3.generar(carpeta_resultados=tmp_path / "no_existe", carpeta_figuras=tmp_path / "f")


def test_figs_m3_no_lee_datos_crudos_ni_procesados():
    fuente = (RAIZ / "src" / "viz" / "figs_m3.py").read_text(encoding="utf-8")
    assert "data/raw" not in fuente and "data/processed" not in fuente and "read_parquet" not in fuente


# --------------------------------------------------------------------------- datos reales (si están)
PROCESADOS = RAIZ / "data" / "processed" / "m3"
FICHA = RAIZ / "results" / "data" / "m3" / "eda" / "ficha.json"


@pytest.mark.skipif(not (PROCESADOS / "interacciones.parquet").exists() or not FICHA.exists(),
                    reason="faltan los datos procesados o la ficha de m3-datos")
def test_con_los_datos_reales_el_histograma_coincide_con_la_ficha(tmp_path):
    cfg = load_config(CONFIG)
    cfg["salida"]["carpeta"] = str(tmp_path / "eda")
    cfg["n_permutaciones"], cfg["n_bootstrap"], cfg["n_simulaciones_azar"] = 200, 100, 100
    # copia la ficha para que main la compare
    (tmp_path / "eda").mkdir()
    (tmp_path / "eda" / "ficha.json").write_bytes(FICHA.read_bytes())
    assert eda.main(cfg) == 0
    ficha = json.loads(FICHA.read_text(encoding="utf-8"))
    dist = json.loads((tmp_path / "eda" / "distribucion_actividad.json").read_text(encoding="utf-8"))
    assert dist["usuarios"]["observado"] == ficha["conteos"]["usuarios_por_numero_de_interacciones"]["union"]
    assert sum(dist["destinos"]["observado"].values()) == ficha["conteos"]["destinos_maestra"]


# --------------------------------------------------------------------------- 3.ª vuelta (R1 y R2)
def test_residuos_estandarizados_y_aporte_al_chi2_a_mano():
    """[[10, 20], [20, 10]]: esperado 15 en cada celda; aporte de cada celda 25/15 = 5/3; residuo ajustado
    (10 − 15)/sqrt(15·(1 − 1/2)·(1 − 1/2)) = −5/sqrt(3,75) ≈ −2,582 (+2,582 en las celdas de 20)."""
    t = np.array([[10.0, 20.0], [20.0, 10.0]])
    r = eda.residuos_estandarizados(t)
    esperado = 5 / np.sqrt(3.75)
    np.testing.assert_allclose(r, [[-esperado, esperado], [esperado, -esperado]])
    mascara = np.array([[True, False], [False, True]])
    si, no = eda.aporte_al_chi2(t, mascara)
    assert si == pytest.approx(10 / 3) and no == pytest.approx(10 / 3)
    assert si + no == pytest.approx(dm.chi2_y_v(t)["chi2"])
    assert eda.aporte_al_chi2(t, np.array([[True, True], [False, False]])) == pytest.approx((10 / 3, 10 / 3))


def test_residuos_de_pearson_a_mano():
    """[[10, 20], [20, 10]]: (10 − 15)/sqrt(15) = −1,291 (celdas de 10) y +1,291 (celdas de 20)."""
    r = eda.residuos_de_pearson(np.array([[10.0, 20.0], [20.0, 10.0]]))
    np.testing.assert_allclose(r, [[-5 / np.sqrt(15), 5 / np.sqrt(15)], [5 / np.sqrt(15), -5 / np.sqrt(15)]])
    # el ajustado es siempre mayor en valor absoluto que el de Pearson (divide por sqrt((1 − f/n)(1 − c/n)) < 1)
    t = np.array([[30.0, 10.0, 5.0], [10.0, 25.0, 20.0]])
    assert (np.abs(eda.residuos_estandarizados(t)) >= np.abs(eda.residuos_de_pearson(t)) - 1e-12).all()


def test_marca_en_el_limite():
    f = eda.en_el_limite
    assert f((0.0006, 0.0469), 0.05, 0.005, "mayor") is True          # |0,0469 − 0,05| = 0,0031 < 0,005 (caso H-M3-1)
    assert f((0.0, 0.1008), 0.10, 0.005, "dos_colas") is True         # caso H4_n_adultos
    assert f((0.0, 0.08), 0.10, 0.005, "dos_colas") is False
    assert f((-0.098, 0.02), 0.10, 0.005, "dos_colas") is True        # el límite inferior contra −mínimo
    assert f((-0.098, 0.02), 0.10, 0.005, "mayor") is False           # en «mayor» solo importa el superior
    assert f((0.0, 0.1049), 0.10, 0.005, "dos_colas") is True and f((0.0, 0.106), 0.10, 0.005, "dos_colas") is False


def test_la_regla_de_la_config_es_la_que_implementa_la_funcion():
    """B1: una sola fuente del texto (la config) y la función concuerdan, en particular en el caso de H-M3-1."""
    cfg = load_config(CONFIG)
    regla = cfg["regla_de_veredicto"]
    assert "contiene el 0" in regla and "empieza en 0 o antes" in regla and "indeterminada" in regla
    assert "alguna cumple" in regla and "todas refutan" in regla
    # H-M3-1: p ajustado ≈ 0,20, IC [0,0006; 0,047], mínimo 0,05, «mayor» → el IC excluye el 0: ni cumple ni refuta
    assert eda.veredicto_de_prueba(0.20, 0.0234, (0.0006, 0.047), 0.05, 0.05, "mayor") == "indeterminada"
    assert eda.veredicto_de_hipotesis(["indeterminada"]) == "no concluyente"
    # lo contrario sí refuta: el mismo IC empezando en 0
    assert eda.veredicto_de_prueba(0.20, 0.02, (0.0, 0.047), 0.05, 0.05, "mayor") == "refuta"


def test_pruebas_json_trae_la_regla_de_la_config_y_ic_ajustado(corrida):
    cfg, out = corrida
    pr = json.loads((out / "pruebas_hipotesis.json").read_text(encoding="utf-8"))
    assert pr["criterio_de_veredicto"]["regla"] == cfg["regla_de_veredicto"]
    assert pr["criterio_de_veredicto"]["tolerancia_limite"] == cfg["tolerancia_limite"]
    c = json.loads((out / "coincidencia_preferencias.json").read_text(encoding="utf-8"))
    aj = c["global"]["diferencia_exacta_ic_ajustado"]
    assert aj["m_familia"] == pr["m_familia"] == len(pr["familia_confirmatoria"])
    assert aj["nivel"] == pytest.approx(1 - cfg["alfa"] / pr["m_familia"])
    lo, hi = c["global"]["diferencia_exacta_ic95"]
    assert aj["ic"][0] <= lo and aj["ic"][1] >= hi
    h1 = next(p for p in pr["pruebas"] if p["id_prueba"] == "H1_permutacion_tasa")
    assert h1["efecto"]["ic_ajustado"] == aj["ic"]
    assert "_dif_boot" not in c


def test_chi2_son_de_cola_derecha_y_marcan_el_limite(corrida):
    cfg, out = corrida
    pr = json.loads((out / "pruebas_hipotesis.json").read_text(encoding="utf-8"))
    for p in pr["pruebas"]:
        if p["estadistico"]["nombre"] == "chi2":
            assert p["alternativa"] == "mayor", p["id_prueba"]
        if p["familia"] == "confirmatoria":
            assert isinstance(p["efecto"]["en_el_limite"], bool)
            esperado = eda.en_el_limite(tuple(p["efecto"]["ic95"]), cfg["efecto_minimo"][p["efecto"]["umbral"]],
                                        cfg["tolerancia_limite"], p["alternativa"])
            assert p["efecto"]["en_el_limite"] is esperado


def test_residuos_y_aporte_en_la_salida_de_h1(corrida):
    _, out = corrida
    c = json.loads((out / "coincidencia_preferencias.json").read_text(encoding="utf-8"))
    pr = json.loads((out / "pruebas_hipotesis.json").read_text(encoding="utf-8"))
    chi = next(p for p in pr["pruebas"] if p["id_prueba"] == "C_H1_chi2_combinacion_tipo")["estadistico"]["valor"]
    x = c["chi2_combinacion_tipo"]
    assert set(x["residuos_estandarizados"]) == set(COMBOS)
    assert x["aporte"]["celdas_coincidentes"] + x["aporte"]["celdas_no_coincidentes"] == pytest.approx(chi)
    assert x["aporte"]["n_celdas_coincidentes"] == 6 and x["aporte"]["n_celdas_no_coincidentes"] == 9
    mayor = max(abs(v) for f in x["residuos_estandarizados"].values() for v in f.values())
    m = x["residuo_maximo_absoluto"]
    assert abs(m["valor"]) == pytest.approx(mayor)
    assert x["residuos_estandarizados"][m["combinacion"]][m["tipo"]] == pytest.approx(m["valor"])
    hip = {h["id"]: h for h in json.loads((out / "hipotesis.json").read_text(encoding="utf-8"))}
    assert set(x["residuos_de_pearson"]) == set(COMBOS)
    pm = x["residuo_maximo_absoluto"]
    assert x["residuos_de_pearson"][pm["combinacion"]][pm["tipo"]] == pytest.approx(pm["valor_de_pearson"])
    assert "residuo" in hip["H-M3-1"]["resultado"] and "celdas coincidentes" in hip["H-M3-1"]["resultado"]
    assert "Pearson" in hip["H-M3-1"]["resultado"]
    assert "IC ajustado" in hip["H-M3-1"]["resultado"]


def test_textos_de_hipotesis_coherentes(corrida):
    _, out = corrida
    hip = {h["id"]: h for h in json.loads((out / "hipotesis.json").read_text(encoding="utf-8"))}
    # M-2: la figura sale de JJ-6 y la hipótesis se cierra en JJ-10, sin contradicción
    for i in ("H-M3-8", "H-M3-9"):
        assert "JJ-6" in hip[i]["figura_o_tabla"] and "JJ-10" in hip[i]["figura_o_tabla"]
        assert "JJ-10" in hip[i]["resultado"]
    # H-5: la regla confirma si alguna prueba cumple, así que el enunciado usa «o»
    assert "difieren en los tipos de destino o en la distribución" in hip["H-M3-6"]["enunciado"]
    assert "a nivel destino_id o lugar" in hip["H-M3-5"]["enunciado"]


def _prueba(id_, p_aj, valor, ic, umbral, alternativa, limite=True):
    return {"id_prueba": id_, "p_ajustado": p_aj, "alternativa": alternativa,
            "efecto": {"valor": valor, "ic95": list(ic), "umbral": umbral, "en_el_limite": limite}}


CFG_LIMITE = {"efecto_minimo": {"diferencia_tasa": 0.05, "v_de_cramer": 0.10}, "alfa": 0.05, "tolerancia_limite": 0.005}


def test_frase_de_limite_nombra_el_limite_que_decide():
    """M1 (R2): en H-M3-1 el que decide es el límite INFERIOR (0,0006, junto al 0), no el superior (0,0469 vs 0,05)."""
    h1 = _prueba("H1_permutacion_tasa", 0.20, 0.0234, (0.0006, 0.0469), "diferencia_tasa", "mayor")
    n_adultos = _prueba("H4_n_adultos", 1.0, 0.0361, (0.0, 0.1008), "v_de_cramer", "mayor")
    genero = _prueba("H4_genero", 1.0, 0.0, (0.0, 0.0645), "v_de_cramer", "mayor", limite=False)
    f1 = eda.frase_limite([h1], CFG_LIMITE)
    assert "el veredicto de H1_permutacion_tasa está en el límite del criterio y no debe leerse como hallazgo" in f1
    assert "límite inferior" in f1 and "0,0006" in f1 and "refutaría" in f1
    assert "límite superior" in f1 and "0,0469" in f1                     # también se dice qué pasa con el superior
    f4 = eda.frase_limite([n_adultos, genero], CFG_LIMITE)
    assert "el veredicto de H4_n_adultos está en el límite del criterio y no debe leerse como hallazgo" in f4
    assert "límite superior" in f4 and "0,1008" in f4 and "H4_genero" not in f4
    assert eda.frase_limite([genero], CFG_LIMITE) == ""


def test_metodo_ic_de_h5_dice_que_no_es_bootstrap_y_gini_reescalado(corrida):
    _, out = corrida
    pr = json.loads((out / "pruebas_hipotesis.json").read_text(encoding="utf-8"))
    h5 = [p for p in pr["pruebas"] if p["hipotesis"] == "H-M3-5"]
    assert h5 and all("no es un bootstrap" in p["efecto"]["metodo_ic"] and "desplazamiento" in p["efecto"]["metodo_ic"] for p in h5)
    conc = json.loads((out / "concentracion.json").read_text(encoding="utf-8"))
    assert "gini_reescalado" in conc["niveles"]["lugar"]["observado"] and "gini_corregido" not in conc["niveles"]["lugar"]["observado"]
    assert "NO es una corrección de sesgo" in conc["definiciones"]["gini_reescalado"]


def test_pie_de_lorenz_dice_que_la_banda_es_puntual():
    assert "puntual" in figs_m3.PIE_LORENZ and "no simultánea" in figs_m3.PIE_LORENZ


def test_todo_de_cita_de_la_v_corregida_nombra_a_bergsma():
    fuente = (RAIZ / "src" / "m3_recomendacion" / "eda_estadistica.py").read_text(encoding="utf-8")
    assert "TODO(cita): Bergsma (2013), doi 10.1016/j.jkss.2012.10.002 — verificar con la fuente primaria en JJ-9" in fuente


# --------------------------------------------------------------------------- 4.ª vuelta (R3 y M1 de R2)
def test_ajuste_multiple_despacha_por_la_clave_y_rechaza_valores_desconocidos(tmp_path):
    p = [0.01, 0.04, 0.03]
    assert eda.ajustar_multiplicidad(p, "holm") == eda.holm(p) == pytest.approx([0.03, 0.06, 0.06])
    with pytest.raises(ValueError, match="bonferroni.*holm"):
        eda.ajustar_multiplicidad(p, "bonferroni")
    cfg = montar(tmp_path)
    cfg["ajuste_multiple"] = "bonferroni"
    with pytest.raises(ValueError, match="ajuste_multiple"):
        eda.main(cfg)
    assert not Path(cfg["salida"]["carpeta"]).exists()          # falla antes de calcular o escribir nada


@pytest.mark.parametrize("clave", ["n_permutaciones", "n_bootstrap", "n_simulaciones_azar"])
def test_numero_de_remuestreos_menor_que_uno_falla_al_inicio(tmp_path, clave):
    cfg = montar(tmp_path)
    cfg[clave] = 0
    with pytest.raises(ValueError, match=clave):
        eda.main(cfg)
    assert not Path(cfg["salida"]["carpeta"]).exists()


def test_pie_no_confunde_lineas_base_que_solo_difieren_en_el_tercer_decimal():
    coin = {"tasa": 0.3, "linea_base_exacta": 0.2002, "ids_por_tipo": {"A": 1, "B": 1, "C": 1, "D": 1, "E": 1}}
    t = figs_m3.texto_linea_base(coin, _filas(("X", 1, 0.2000), ("Y", 1, 0.2004)))
    assert "por fila" in t and "la suma de las 1 recuadradas" not in t


def test_config_invalida_falla_al_inicio_con_mensaje_claro(tmp_path):
    for clave, valor, patron in (("niveles", ["destino_id", "pais"], "niveles"), ("niveles", [], "niveles"),
                                 ("fracciones_top", [], "fracciones_top"), ("fracciones_top", [1.5], "fracciones_top")):
        cfg = montar(tmp_path / f"{clave}_{len(str(valor))}")
        cfg[clave] = valor
        with pytest.raises(ValueError, match=patron):
            eda.main(cfg)
        assert not Path(cfg["salida"]["carpeta"]).exists()


def test_cambiar_fracciones_top_y_niveles_no_rompe_los_textos(tmp_path):
    cfg = montar(tmp_path / "a")
    cfg["fracciones_top"] = [0.2]
    cfg["niveles"] = ["destino_id"]
    assert eda.main(cfg) == 0
    out = Path(cfg["salida"]["carpeta"])
    conc = json.loads((out / "concentracion.json").read_text(encoding="utf-8"))
    assert list(conc["niveles"]) == ["destino_id"] and list(conc["niveles"]["destino_id"]["observado"]["cuota_top"]) == ["0.2"]
    hip = {h["id"]: h for h in json.loads((out / "hipotesis.json").read_text(encoding="utf-8"))}
    assert "20 %" in hip["H-M3-5"]["resultado"] and "lugar" not in hip["H-M3-5"]["resultado"].split("Criterio")[0]
    pr = json.loads((out / "pruebas_hipotesis.json").read_text(encoding="utf-8"))
    assert pr["m_familia"] == 9 and "H5_gini_lugar" not in pr["familia_confirmatoria"]
    cfg2 = montar(tmp_path / "b")
    cfg2["niveles"] = ["lugar"]
    cfg2["fracciones_top"] = [0.1, 0.5]
    assert eda.main(cfg2) == 0
    hip2 = {h["id"]: h for h in json.loads((Path(cfg2["salida"]["carpeta"]) / "hipotesis.json").read_text(encoding="utf-8"))}
    assert hip2["H-M3-5"]["veredicto"] in {"confirmada", "refutada", "no concluyente"}


def test_umbral_de_actividad_se_genera_desde_pocas_max(tmp_path):
    textos = {}
    for p_max in (1, 2, 3):
        cfg = montar(tmp_path / f"p{p_max}")
        cfg["actividad"]["pocas_max"] = p_max
        eda.main(cfg)
        out = Path(cfg["salida"]["carpeta"])
        act = json.loads((out / "actividad_usuarios.json").read_text(encoding="utf-8"))
        textos[p_max] = act["umbral"]["justificacion"]
        hip = {h["id"]: h for h in json.loads((out / "hipotesis.json").read_text(encoding="utf-8"))}
        assert f"(1 a {p_max})" in hip["H-M3-9"]["enunciado"] and f"({p_max + 1} o más)" in hip["H-M3-9"]["enunciado"]
    assert "con 1 o 2 interacciones aportan a lo sumo una interacción de prueba y ninguna de validación" in textos[2]
    assert "1 a 3 interacciones" in textos[3] and "ninguna de validación" not in textos[3]
    assert "con 1 interacción solo aportan entrenamiento" in textos[1] and "ninguna de validación" not in textos[1]


def test_combinacion_sin_interacciones_se_omite_con_aviso(tmp_path, capsys):
    cfg = montar(tmp_path)
    ruta = Path(cfg["entrada"]["carpeta"]) / "interacciones.parquet"
    usuarios = pd.read_parquet(Path(cfg["entrada"]["carpeta"]) / "usuarios.parquet")
    sin = set(usuarios.loc[usuarios["preferencias"] == "City, Historical", "usuario_id"])
    inter = pd.read_parquet(ruta)
    inter[~inter["usuario_id"].isin(sin)].to_parquet(ruta, index=False)
    assert eda.main(cfg) == 0                                   # antes: NaN → save_json fallaba al final
    out = Path(cfg["salida"]["carpeta"])
    c = json.loads((out / "coincidencia_preferencias.json").read_text(encoding="utf-8"))
    assert set(c["por_combinacion"]) == {"Beaches, Historical", "Adventure, Nature"}
    assert c["combinaciones_sin_interacciones"] == ["City, Historical"]
    salida = capsys.readouterr().out
    assert "sin interacciones" in salida and "City, Historical" in salida
    assert set(pd.read_csv(out / "matriz_preferencias_tipo.csv")["combinacion"]) == {"Beaches, Historical", "Adventure, Nature"}
    with pytest.raises(ValueError, match="sin interacciones"):
        eda.coincidencia(pd.Series(["A", "B"]), [], [], {})


def test_el_veredicto_de_cada_prueba_se_calcula_una_sola_vez(tmp_path, monkeypatch):
    from src.m3_recomendacion import eda_hipotesis
    llamadas = []
    original = eda_hipotesis.veredicto_de_prueba
    monkeypatch.setattr(eda_hipotesis, "veredicto_de_prueba", lambda *a, **k: llamadas.append(a) or original(*a, **k))
    cfg = montar(tmp_path)
    eda.main(cfg)
    pr = json.loads((Path(cfg["salida"]["carpeta"]) / "pruebas_hipotesis.json").read_text(encoding="utf-8"))
    assert len(llamadas) == pr["m_familia"]


def _funciones(nombre_modulo: str):
    fuente = (RAIZ / "src" / "m3_recomendacion" / nombre_modulo).read_text(encoding="utf-8")
    return [n for n in ast.walk(ast.parse(fuente)) if isinstance(n, ast.FunctionDef)]


def test_cada_hipotesis_tiene_su_funcion_corta():
    funciones = {f.name: f.end_lineno - f.lineno + 1 for f in _funciones("eda_hipotesis.py")}
    hipotesis = {n: k for n, k in funciones.items() if n.startswith("hipotesis_")}
    assert len(hipotesis) == 9 and max(hipotesis.values()) <= 45, hipotesis
    assert max(funciones.values()) <= 60, funciones


def test_datos_no_usa_nombres_de_una_letra_ni_guarda_la_config(tmp_path):
    cfg = montar(tmp_path)
    d = eda.Datos(*eda._leer(cfg), cfg["emparejamiento_preferencia_tipo"])
    cortos = [a for a in vars(d) if len(a) <= 3]
    assert not cortos, cortos
    assert "cfg" not in vars(d) and "inter" not in vars(d)
    assert d.__class__.__doc__ and "forma" in d.__class__.__doc__.lower()
