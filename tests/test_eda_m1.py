"""Pruebas del análisis descriptivo de M1 (CA-4): secciones 3-7 de la plantilla común (núcleo §5.12).

Todo con series construidas en `datos_eda_m1.py` (periodos y patrones conocidos); ninguna cifra real. El comportamiento con
los datos reales lo cubre la corrida de `run.py m1-eda`.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import datos_eda_m1 as d  # módulo de utilidades de pruebas (tests/ está en sys.path)
from src.comun.eda import VEREDICTOS, leer_hipotesis, validar_hipotesis
from src.m1_demanda import eda, eda_hipotesis

RUTAS = d.RUTAS
FACTOR_SEMANAL = d.FACTOR_SEMANAL
_diaria, _detalle, _marcas = d.diaria, d.detalle, d.marcas


@pytest.fixture(scope="module")
def diaria() -> pd.DataFrame:
    return d.diaria()


@pytest.fixture(scope="module")
def res_sin_calendario(diaria) -> dict:
    """Cálculo costoso (MSTL) hecho una sola vez por módulo, sin calendario."""
    return eda.calcular_resultados(diaria, _detalle(diaria), _marcas(diaria), None, eda.parametros({}))


@pytest.fixture(scope="module")
def res_con_calendario(diaria, res_sin_calendario) -> dict:
    """Mismos cálculos con un calendario (festivos y una vacación en Bogotá); reutiliza la descomposición ya hecha."""
    cal = d.calendario(["2022-08-15", "2022-10-17"])
    p = eda.parametros({})
    r = dict(res_sin_calendario)
    r["calendario"], r["efectos"], r["calendario_faltan"] = cal, {}, []
    eda.agregar_efectos_calendario(r, diaria, cal, p)
    return r


# ---------------------------------------------------------------- sección 3: variable objetivo
def test_tabla_objetivo_cuenta_ceros_sin_registro_y_anomalos(diaria):
    diaria = diaria.copy()  # la fixture es de módulo: no se muta
    marcas = _marcas(diaria)
    diaria.loc[(diaria["ruta_id"] == RUTAS[0]) & (diaria["fecha"] == "2022-03-15"), "anomalo"] = True
    t = eda.tabla_objetivo(diaria, marcas)
    assert list(t.columns) == eda.COLUMNAS_OBJETIVO
    assert set(t["ruta_id"]) == set(RUTAS)
    fila = t.set_index("ruta_id").loc[RUTAS[0]]
    assert fila["dias"] == len(d.fechas())
    assert fila["sin_registro"] == 30  # mayo de 2021 desde el 2
    assert fila["ceros"] == 30
    assert fila["anomalos"] == 1
    assert fila["anomalos_caida_robusta"] == 1
    assert fila["anomalos_pico_robusto"] == 0
    assert fila["pasajeros_total"] == diaria.loc[diaria["ruta_id"] == RUTAS[0], "pasajeros"].sum()


def test_tabla_objetivo_ruta_sin_dias_con_registro_da_minimo_y_maximo_nulos():
    x = d.diaria()
    x.loc[x["ruta_id"] == RUTAS[1], ["pasajeros", "despachos"]] = 0
    x.loc[x["ruta_id"] == RUTAS[1], "sin_registro"] = True
    t = eda.tabla_objetivo(x, _marcas(x)).set_index("ruta_id")
    assert pd.isna(t.loc[RUTAS[1], "minimo"]) and pd.isna(t.loc[RUTAS[1], "maximo"])
    assert t.loc[RUTAS[1], "pasajeros_total"] == 0
    assert t.loc[RUTAS[0], "minimo"] > 0  # la otra ruta no cambia


def test_proporcion_transito_por_ruta_y_anio(diaria):
    t = eda.proporcion_transito(_detalle(diaria))
    assert list(t.columns) == eda.COLUMNAS_TRANSITO
    assert set(t["anio"]) == {2021, 2022, 2023}
    assert np.allclose(t["pct_transito"], 40.0, atol=0.5)
    assert (t["pasajeros_origen"] + t["pasajeros_transito"] > 0).all()


def test_proporcion_transito_sin_filas_de_un_tipo_da_cero_no_nan():
    d = pd.DataFrame(
        {
            "ruta_id": ["A-B"] * 2,
            "fecha": pd.to_datetime(["2022-01-01", "2022-01-02"]),
            "tipo_despacho": ["ORIGEN", "ORIGEN"],
            "clase_vehiculo": ["BUS", "BUS"],
            "pasajeros": [10, 20],
            "despachos": [1, 2],
        }
    )
    t = eda.proporcion_transito(d)
    assert t.loc[0, "pasajeros_transito"] == 0 and t.loc[0, "pct_transito"] == 0.0


def test_composicion_clases_suma_100_y_detecta_microbus_que_desaparece(diaria):
    c = eda.composicion_clases(_detalle(diaria))
    assert list(c.columns) == eda.COLUMNAS_CLASES
    suma = c.groupby(["ruta_id", "anio"])["pct"].sum()
    assert np.allclose(suma, 100.0)
    micro23 = c[(c["anio"] == 2023) & (c["clase_vehiculo"] == "MICROBUS")]
    assert set(micro23["ruta_id"]) == set(RUTAS)  # aparece (no se omite) ...
    assert (micro23["pct"] == 0).all()  # ... con participación 0
    micro22 = c[(c["anio"] == 2022) & (c["clase_vehiculo"] == "MICROBUS")]
    assert (micro22["pct"] > 0).all()


def test_transito_mensual_tiene_un_mes_por_fila(diaria):
    t = eda.transito_mensual(_detalle(diaria))
    assert list(t.columns) == eda.COLUMNAS_TRANSITO_MENSUAL
    assert t.groupby("ruta_id")["mes"].nunique().iloc[0] == 36
    assert (t["pasajeros_dia_transito"] >= 0).all()


# ---------------------------------------------------------------- sección 4: estructura
def test_perfil_semanal_recupera_el_patron_conocido(diaria):
    p = eda.perfil_semanal(diaria, inicio="2021-06-01")
    assert list(p.columns) == eda.COLUMNAS_PERFIL_SEMANAL
    r = p[p["ruta_id"] == RUTAS[0]].sort_values("dia_semana")
    esperado = FACTOR_SEMANAL / FACTOR_SEMANAL.mean()
    assert np.allclose(r["razon_vs_media_semanal"].to_numpy(), esperado, atol=0.01)
    assert list(r["dia_semana"]) == list(range(7))  # 0 = lunes


def test_perfil_semanal_excluye_sin_registro():
    x = _diaria()
    # sin exclusión, mayo-2021 (ceros) rebajaría la media: con inicio anterior debe seguir siendo el patrón exacto
    p = eda.perfil_semanal(x, inicio="2021-01-01")
    r = p[p["ruta_id"] == RUTAS[0]].sort_values("dia_semana")
    assert np.allclose(r["razon_vs_media_semanal"].to_numpy(), FACTOR_SEMANAL / FACTOR_SEMANAL.mean(), atol=0.01)


def test_perfil_semanal_con_media_cero_da_nulo_no_infinito():
    x = d.diaria()
    x.loc[x["ruta_id"] == RUTAS[1], "pasajeros"] = 0  # ruta con registro pero sin pasajeros
    p = eda.perfil_semanal(x, inicio="2021-06-01")
    r = p[p["ruta_id"] == RUTAS[1]]
    assert r["razon_vs_media_semanal"].isna().all() and r["razon_mediana"].isna().all()
    assert not np.isinf(p[["razon_vs_media_semanal", "razon_mediana"]].to_numpy(dtype=float)).any()


def test_perfil_mensual_con_media_cero_da_nulo_no_infinito():
    x = d.diaria()
    x.loc[x["ruta_id"] == RUTAS[1], "pasajeros"] = 0
    p = eda.perfil_mensual(x, inicio="2021-06-01")
    assert p.loc[p["ruta_id"] == RUTAS[1], "razon_vs_media_anual"].isna().all()
    assert not np.isinf(p["razon_vs_media_anual"].to_numpy(dtype=float)).any()


def test_tendencia_con_anio_previo_en_cero_da_nulo_no_infinito():
    x = d.diaria()
    x.loc[(x["ruta_id"] == RUTAS[0]) & (x["fecha"].dt.year == 2022), "pasajeros"] = 0
    t = eda.tendencia_anual(x, inicio="2021-06-01").set_index(["ruta_id", "anio"])
    assert pd.isna(t.loc[(RUTAS[0], 2023), "variacion_pct_jun_dic"])
    assert pd.isna(t.loc[(RUTAS[0], 2023), "variacion_pct_ene_abr"])
    assert not np.isinf(t["variacion_pct_jun_dic"].to_numpy(dtype=float)).any()


def test_hallazgos_avisan_de_razones_sin_definir(diaria, res_sin_calendario):
    assert res_sin_calendario["hallazgos"]["avisos"] == []  # datos sanos: sin avisos
    x = d.diaria()
    x.loc[x["ruta_id"] == RUTAS[1], "pasajeros"] = 0
    r = dict(res_sin_calendario)
    r["perfil_semanal"] = eda.perfil_semanal(x, "2021-06-01")
    r["perfil_mensual"] = eda.perfil_mensual(x, "2021-06-01")
    r["tendencia"] = eda.tendencia_anual(x, "2021-06-01")
    avisos = eda.calcular_hallazgos(r, eda.parametros({}))["avisos"]
    assert any(RUTAS[1] in a and "perfil_semanal" in a for a in avisos)
    assert any(RUTAS[1] in a and "perfil_mensual" in a for a in avisos)
    assert any(RUTAS[1] in a and "tendencia_anual" in a for a in avisos)


def test_perfil_mensual_marca_anios_completos(diaria):
    p = eda.perfil_mensual(diaria, inicio="2021-06-01")
    assert list(p.columns) == eda.COLUMNAS_PERFIL_MENSUAL
    completos = p[p["anio_completo"]]
    assert set(completos["anio"]) == {2022, 2023}
    assert completos.groupby(["ruta_id", "anio"])["razon_vs_media_anual"].mean().between(0.9, 1.1).all()
    # 2021 desde junio no es un año completo
    assert not p[p["anio"] == 2021]["anio_completo"].any()


def test_tendencia_anual_compara_ventanas_equivalentes_entre_anios():
    x = _diaria(tendencia_anual=0.10)
    t = eda.tendencia_anual(x, inicio="2021-06-01")
    assert list(t.columns) == eda.COLUMNAS_TENDENCIA
    r = t[t["ruta_id"] == RUTAS[0]].set_index("anio")
    assert r.loc[2022, "media_jun_dic"] > r.loc[2021, "media_jun_dic"]
    assert r.loc[2023, "media_jun_dic"] > r.loc[2022, "media_jun_dic"]
    assert pd.isna(r.loc[2021, "variacion_pct_jun_dic"])
    esperado = 100 * (r.loc[2022, "media_jun_dic"] / r.loc[2021, "media_jun_dic"] - 1)
    assert r.loc[2022, "variacion_pct_jun_dic"] == pytest.approx(esperado)
    esperado = 100 * (r.loc[2023, "media_ene_abr"] / r.loc[2022, "media_ene_abr"] - 1)
    assert r.loc[2023, "variacion_pct_ene_abr"] == pytest.approx(esperado)


def test_descomposicion_recupera_periodo_semanal_conocido():
    # con ruido: sin él el residuo es ~0 y la «fuerza» de cualquier componente tiende a 1 (artefacto de la fórmula)
    comp, resumen = eda.descomposicion(_diaria(ruido=0.05), inicio="2021-06-01")
    assert list(comp.columns) == eda.COLUMNAS_DESCOMPOSICION
    assert comp["fecha"].min() == pd.Timestamp("2021-06-01")
    assert comp["fecha"].nunique() == (pd.Timestamp("2023-12-31") - pd.Timestamp("2021-06-01")).days + 1
    # reconstrucción exacta: observado = tendencia + semanal + anual + residuo
    suma = comp["tendencia"] + comp["semanal"] + comp["anual"] + comp["residuo"]
    assert np.allclose(suma, comp["observado_log1p"])
    # el componente semanal debe repetirse cada 7 días y su rango debe parecerse al del patrón conocido (en log1p)
    r = comp[comp["ruta_id"] == RUTAS[0]].sort_values("fecha")
    s = r["semanal"].to_numpy()
    assert np.corrcoef(s[:-7], s[7:])[0, 1] > 0.99
    rango_esperado = np.log(FACTOR_SEMANAL.max() / FACTOR_SEMANAL.min())
    assert (np.percentile(s, 99) - np.percentile(s, 1)) == pytest.approx(rango_esperado, rel=0.2)
    # fuerza semanal alta. La anual NO se acota por debajo: con ~2,6 ciclos el componente anual de MSTL absorbe ruido
    # (en esta serie sin ciclo anual sale ~0,7), así que solo se exige que sea menor que la semanal.
    fila = resumen.set_index("ruta_id").loc[RUTAS[0]]
    assert fila["fuerza_semanal"] > 0.95
    assert fila["fuerza_anual"] < fila["fuerza_semanal"]
    assert fila["sin_registro_imputados"] == 0


def test_descomposicion_interpola_dias_sin_registro_dentro_del_periodo():
    x = _diaria()
    huecos = (x["ruta_id"] == RUTAS[0]) & (x["fecha"] >= "2022-01-10") & (x["fecha"] <= "2022-01-12")
    x.loc[huecos, ["pasajeros", "despachos"]] = 0
    x.loc[huecos, "sin_registro"] = True
    comp, resumen = eda.descomposicion(x, inicio="2021-06-01")
    assert resumen.set_index("ruta_id").loc[RUTAS[0], "sin_registro_imputados"] == 3
    obs = comp[(comp["ruta_id"] == RUTAS[0]) & (comp["fecha"].between("2022-01-10", "2022-01-12"))]["observado_log1p"]
    assert (obs > np.log1p(500)).all()  # no entra el cero


def test_descomposicion_exige_dos_ciclos_del_periodo_mayor():
    corto = _diaria().query("fecha <= '2022-03-01'")
    with pytest.raises(ValueError, match="observaciones"):
        eda.descomposicion(corto, inicio="2021-06-01")


def test_fuerza_estacionalidad_formula():
    rng = np.random.default_rng(0)
    s = np.sin(np.linspace(0, 20 * np.pi, 500))
    r = 0.1 * rng.standard_normal(500)
    esperado = max(0.0, 1 - np.var(r) / np.var(s + r))
    assert eda.fuerza(s, r) == pytest.approx(esperado)
    assert eda.fuerza(np.zeros(10), r[:10]) == 0.0


# ---------------------------------------------------------------- efecto de calendario (solo si existe CA-1)
def test_efecto_calendario_mide_razon_contra_mismo_dia_de_semana_vecino():
    x = _diaria()
    dia = pd.Timestamp("2022-08-15")  # un lunes
    x.loc[(x["fecha"] == dia), "pasajeros"] = (x.loc[x["fecha"] == dia, "pasajeros"] * 1.5).round().astype("int64")
    cal = d.calendario(["2022-08-15"])
    t = eda.efecto_calendario(x, cal, "festivo", inicio="2021-06-01")
    assert list(t.columns) == eda.COLUMNAS_EFECTO_CALENDARIO
    assert (t["n_dias"] == 1).all()
    assert np.allclose(t["razon_mediana"], 1.5, atol=0.02)


def test_efecto_calendario_sin_dias_marcados_devuelve_tabla_vacia():
    t = eda.efecto_calendario(_diaria(), d.calendario([]), "festivo", inicio="2021-06-01")
    assert t.empty and list(t.columns) == eda.COLUMNAS_EFECTO_CALENDARIO


def test_vacaciones_usan_la_columna_de_la_ciudad_de_origen_de_cada_ruta():
    x = _diaria()
    marcado = pd.Timestamp("2022-08-17")  # miércoles
    # solo la ruta con origen 76001 sube ese día; la columna de Bogotá (11001) marca OTRO día
    mask = (x["ruta_id"] == RUTAS[1]) & (x["fecha"] == marcado)
    x.loc[mask, "pasajeros"] = (x.loc[mask, "pasajeros"] * 2).astype("int64")
    cal = d.calendario(vacaciones={"76001": ["2022-08-17"], "11001": ["2022-08-24"]})
    t = eda.efecto_calendario(x, cal, "vacaciones_escolares", inicio="2021-06-01", por_origen=True).set_index("ruta_id")
    assert t.loc[RUTAS[1], "columna"] == "vacaciones_escolares_76001"
    assert t.loc[RUTAS[0], "columna"] == "vacaciones_escolares_11001"
    assert t.loc[RUTAS[1], "razon_mediana"] == pytest.approx(2.0, abs=0.02)
    assert t.loc[RUTAS[0], "razon_mediana"] == pytest.approx(1.0, abs=0.02)
    # con la columna de Bogotá para todas, la ruta de Cali ya no mediría el 2,0 (la marca de Bogotá es otro día): confirma que la columna importa
    t_bog = eda.efecto_calendario(x, cal, "vacaciones_escolares_11001", inicio="2021-06-01")
    assert abs(t_bog.set_index("ruta_id").loc[RUTAS[1], "razon_mediana"] - 2.0) > 0.5


def test_vacaciones_con_nulos_los_excluye_y_los_cuenta():
    x = _diaria()
    cal = d.calendario(vacaciones={"11001": ["2022-08-17"]}, nulos={"11001": ["2022-08-10"]})
    t = eda.efecto_calendario(x, cal, "vacaciones_escolares", inicio="2021-06-01", por_origen=True).set_index("ruta_id")
    assert t.loc[RUTAS[0], "n_nulos_excluidos"] == 1
    assert t.loc[RUTAS[0], "n_dias"] == 1  # el nulo no se cuenta ni como marcado ni como vecino


def test_hipotesis_de_vacaciones_declara_los_dias_nulos_excluidos(diaria, res_sin_calendario):
    cal = d.calendario(vacaciones={"11001": ["2022-08-17"], "76001": ["2022-08-17"]}, nulos={"11001": ["2022-08-10"]})
    r = dict(res_sin_calendario)
    r["calendario"], r["efectos"], r["calendario_faltan"] = cal, {}, []
    eda.agregar_efectos_calendario(r, diaria, cal, eda.parametros({}))
    h = {x["id"]: x for x in eda_hipotesis.construir_hipotesis(r)}
    assert "ciudad de origen" in h["H-M1-3"]["resultado"]
    assert "excluyeron 1 día" in h["H-M1-3"]["resultado"]


def test_calendario_sin_columna_por_ciudad_declara_que_falta(diaria, res_sin_calendario):
    cal = d.calendario(["2022-08-15"]).drop(columns=["vacaciones_escolares_76001"])
    r = dict(res_sin_calendario)
    r["calendario"], r["efectos"], r["calendario_faltan"] = cal, {}, []
    eda.agregar_efectos_calendario(r, diaria, cal, eda.parametros({}))
    h = {x["id"]: x for x in eda_hipotesis.construir_hipotesis(r)}
    assert h["H-M1-3"]["resultado"] == "falta la columna vacaciones_escolares_76001 en calendario.parquet"


# ---------------------------------------------------------------- hipótesis (sección 5 y 7)
def test_hipotesis_sin_calendario_deja_pendientes_las_de_calendario(res_sin_calendario):
    h = eda_hipotesis.construir_hipotesis(res_sin_calendario)
    validar_hipotesis(h)
    por_id = {x["id"]: x for x in h}
    # orden del enunciado: día de la semana, festivos y puentes, temporada escolar, Semana Santa, fin de año, pospandemia, ...
    assert [x["id"] for x in h] == [f"H-M1-{i}" for i in range(1, 11)]
    for i in (2, 3, 4):
        assert por_id[f"H-M1-{i}"]["resultado"] == "falta el calendario de CA-1"
    for i in (1, 5, 6):
        assert por_id[f"H-M1-{i}"]["resultado"] != "falta el calendario de CA-1"
        assert por_id[f"H-M1-{i}"]["resultado"].strip()
    assert all(x["veredicto"] in VEREDICTOS for x in h)
    assert all(x["veredicto"] == "pendiente" for x in h)  # por norma §5.12/§7: nada se confirma hasta modelar


def test_hipotesis_con_calendario_evalua_festivos_y_declara_lo_demas(res_con_calendario):
    h = {x["id"]: x for x in eda_hipotesis.construir_hipotesis(res_con_calendario)}
    assert h["H-M1-2"]["resultado"].startswith("festivo: ")
    assert "puente" in h["H-M1-2"]["resultado"]  # la columna puente no tiene días marcados: se declara, no se inventa
    # vacaciones (por ciudad) y Semana Santa no tienen días marcados en este calendario: un único resultado esperado
    assert h["H-M1-3"]["resultado"] == "sin días marcados o sin vecinos suficientes en: vacaciones_escolares"
    assert h["H-M1-4"]["resultado"] == "sin días marcados o sin vecinos suficientes en: semana_santa"
    assert h["H-M1-3"]["veredicto"] == "pendiente"


def test_hipotesis_tienen_todos_los_campos_y_figura_o_tabla_no_vacio(res_sin_calendario):
    for x in eda_hipotesis.construir_hipotesis(res_sin_calendario):
        for k in ("enunciado", "justificacion", "evidencia_esperada", "figura_o_tabla", "resultado", "evidencia"):
            assert isinstance(x[k], str) and x[k].strip(), (x["id"], k)


def test_h5_solo_perfil_mensual_y_nombra_fin_de_anio(res_sin_calendario):
    h5 = {x["id"]: x for x in eda_hipotesis.construir_hipotesis(res_sin_calendario)}["H-M1-5"]
    assert "sin calendario externo" not in h5["justificacion"]
    assert "perfil mensual" in h5["justificacion"] and "fin_de_anio" in h5["justificacion"]
    assert h5["figura_o_tabla"].startswith("perfil_mensual.csv")


def test_textos_salen_de_los_parametros_y_umbrales(res_sin_calendario):
    r = copy.deepcopy(res_sin_calendario)
    r["params"]["inicio_analisis"] = "2021-07-01"
    r["params"]["ventana_calendario_dias"] = 28
    h = {x["id"]: x for x in eda_hipotesis.construir_hipotesis(r)}
    assert "Desde 2021-07-01" in h["H-M1-1"]["resultado"]
    assert "±28 días" in h["H-M1-2"]["evidencia_esperada"] and "±42" not in h["H-M1-2"]["evidencia_esperada"]
    assert f"{eda_hipotesis.UMBRAL_SIN_TRANSITO_PCT:g}".replace(".", ",") + " %" in h["H-M1-7"]["resultado"]
    imp = eda_hipotesis.construir_implicaciones(r)
    obs = int(r["descomposicion_resumen"]["observaciones"].min())
    assert f"{obs / eda_hipotesis.ANUAL:.1f}".replace(".", ",") + " ciclos anuales" in imp["ventana"]["base"]
    assert "2021-07-01" in imp["particion"]["decision"]


def test_hipotesis_con_ruta_sin_pasajeros_no_revienta(diaria, res_sin_calendario):
    x = d.diaria()
    x.loc[x["ruta_id"] == RUTAS[1], "pasajeros"] = 0
    r = dict(res_sin_calendario)
    r["perfil_semanal"] = eda.perfil_semanal(x, "2021-06-01")
    r["perfil_mensual"] = eda.perfil_mensual(x, "2021-06-01")
    r["tendencia"] = eda.tendencia_anual(x, "2021-06-01")
    r["hallazgos"] = eda.calcular_hallazgos(r, eda.parametros({}))
    h = eda_hipotesis.construir_hipotesis(r)
    validar_hipotesis(h)
    assert "inf" not in " ".join(x["resultado"] for x in h)


# ---------------------------------------------------------------- main: contratos de salida
def _cfg(tmp_path: Path) -> dict:
    proc = tmp_path / "proc"
    proc.mkdir()
    x = _diaria()
    x.to_parquet(proc / "demanda_diaria.parquet", index=False)
    _detalle(x).to_parquet(proc / "demanda_detalle.parquet", index=False)
    _marcas(x).to_parquet(proc / "marcas_anomalos.parquet", index=False)
    return {"salida": {"carpeta": str(proc), "detalle": "demanda_detalle.parquet", "diaria": "demanda_diaria.parquet",
                       "marcas": "marcas_anomalos.parquet", "eda": str(tmp_path / "eda")}}


def test_main_escribe_los_archivos_y_respeta_los_de_daniel(tmp_path):
    cfg = _cfg(tmp_path)
    eda_dir = Path(cfg["salida"]["eda"])
    eda_dir.mkdir()
    for nombre in ("ficha.json", "calidad.csv", "diccionario.json"):  # los de Daniel no se tocan
        (eda_dir / nombre).write_text("{}" if nombre.endswith("json") else "x\n", encoding="utf-8")
    assert eda.main(cfg) == 0
    for nombre in eda.ARCHIVOS_SALIDA:
        assert (eda_dir / nombre).exists(), nombre
    assert (eda_dir / "ficha.json").read_text(encoding="utf-8") == "{}"
    assert (eda_dir / "calidad.csv").read_text(encoding="utf-8") == "x\n"
    assert (eda_dir / "diccionario.json").read_text(encoding="utf-8") == "{}"
    h = leer_hipotesis(eda_dir / "hipotesis.json")  # valida el esquema
    assert {x["id"] for x in h} >= {f"H-M1-{i}" for i in range(1, 7)}
    # la descomposición guardada cubre todas las rutas desde el inicio configurado
    comp = pd.read_parquet(eda_dir / "descomposicion.parquet")
    assert set(comp["ruta_id"]) == set(RUTAS)
    # el JSON de implicaciones y el de hallazgos existen y son JSON
    for nombre in ("implicaciones.json", "hallazgos.json"):
        json.loads((eda_dir / nombre).read_text(encoding="utf-8"))


def test_main_es_determinista(tmp_path):
    cfg = _cfg(tmp_path)
    eda.main(cfg)
    carpeta = Path(cfg["salida"]["eda"])
    antes = {n: (carpeta / n).read_bytes() for n in ("hipotesis.json", "perfil_semanal.csv", "implicaciones.json")}
    eda.main(cfg)
    despues = {n: (carpeta / n).read_bytes() for n in antes}
    assert antes == despues


def test_main_usa_calendario_si_existe(tmp_path):
    cfg = _cfg(tmp_path)
    cal = d.calendario(["2022-08-15"])
    cal.to_parquet(Path(cfg["salida"]["carpeta"]) / "calendario.parquet", index=False)
    eda.main(cfg)
    h = {x["id"]: x for x in leer_hipotesis(Path(cfg["salida"]["eda"]) / "hipotesis.json")}
    assert h["H-M1-2"]["resultado"] != "falta el calendario de CA-1"


def test_ninguna_tabla_de_entrada_a_modelos_lleva_las_marcas(tmp_path):
    """Las marcas `anomalo`/`sin_registro` solo viven en la serie marcada y en el conteo por ruta (descriptivos)."""
    cfg = _cfg(tmp_path)
    eda.main(cfg)
    carpeta = Path(cfg["salida"]["eda"])
    permitidos = {"serie_marcada.parquet", "objetivo_por_ruta.csv"}
    for nombre in eda.ARCHIVOS_SALIDA:
        if nombre.endswith(".json") or nombre in permitidos:
            continue
        df = pd.read_parquet(carpeta / nombre) if nombre.endswith(".parquet") else pd.read_csv(carpeta / nombre)
        assert not {"anomalo", "sin_registro"} & set(df.columns), nombre


def test_rutas_por_defecto_son_relativas_a_la_raiz_del_repo_no_al_cwd():
    assert eda.RAIZ.joinpath("src").is_dir()
    assert Path(eda.CARPETA_SALIDA).is_absolute() and Path(eda.CARPETA_SALIDA) == eda.RAIZ / "results/data/m1/eda"
    assert eda.ruta_en_raiz("data/processed/m1") == eda.RAIZ / "data/processed/m1"
    assert eda.ruta_en_raiz("/tmp/x") == Path("/tmp/x")


def test_implicaciones_cubren_los_temas(res_sin_calendario):
    imp = eda_hipotesis.construir_implicaciones(res_sin_calendario)
    assert set(imp) >= {"ventana", "variables_calendario", "perdida_conteo", "particion", "cambio_de_regimen", "mayo_2021", "transito"}
    for k, v in imp.items():
        assert isinstance(v, dict) and v.get("decision") and v.get("base"), k
