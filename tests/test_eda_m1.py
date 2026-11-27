"""Pruebas del análisis descriptivo de M1 (CA-4): secciones 3-7 de la plantilla común (núcleo §5.12).

Todo con series construidas aquí (periodos y patrones conocidos); ninguna cifra real. El comportamiento con los datos
reales lo cubre la corrida de `run.py m1-eda`.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.comun.eda import VEREDICTOS, leer_hipotesis, validar_hipotesis
from src.m1_demanda import eda

RUTAS = ["11001-76001", "76001-11001"]
FACTOR_SEMANAL = np.array([1.0, 0.8, 0.8, 0.9, 1.2, 1.5, 1.3])  # lunes..domingo (patrón conocido)


def _fechas() -> pd.DatetimeIndex:
    return pd.date_range("2021-01-01", "2023-12-31", freq="D")


def _diaria(tendencia_anual: float = 0.0, ruido: float = 0.0) -> pd.DataFrame:
    """Dos rutas con perfil semanal exacto, nivel 1000 y (opcional) tendencia lineal y ruido lognormal (semilla fija)."""
    rng = np.random.default_rng(123)
    fechas = _fechas()
    filas = []
    for k, ruta in enumerate(RUTAS):
        t = np.arange(len(fechas)) / 365.0
        y = 1000.0 * (1 + k) * (1 + tendencia_anual * t) * FACTOR_SEMANAL[fechas.day_of_week]
        y = y * np.exp(ruido * rng.standard_normal(len(fechas)))
        filas.append(
            pd.DataFrame(
                {
                    "ruta_id": ruta,
                    "origen_divipola": ruta[:5],
                    "destino_divipola": ruta[6:],
                    "fecha": fechas,
                    "pasajeros": np.round(y).astype("int64"),
                    "despachos": 50,
                    "sin_registro": False,
                    "anomalo": False,
                }
            )
        )
    d = pd.concat(filas, ignore_index=True)
    sin = (d["fecha"] >= "2021-05-02") & (d["fecha"] <= "2021-05-31")
    d.loc[sin, ["pasajeros", "despachos"]] = 0
    d.loc[sin, "sin_registro"] = True
    return d


def _detalle(diaria: pd.DataFrame) -> pd.DataFrame:
    """60 % origen / 40 % tránsito; BUS y MICROBUS (este solo hasta 2022)."""
    partes = []
    for tipo, p_tipo in (("ORIGEN", 0.6), ("TRANSITO", 0.4)):
        for clase in ("BUS", "MICROBUS"):
            p = p_tipo * (0.7 if clase == "BUS" else 0.3)
            d = diaria[["ruta_id", "origen_divipola", "destino_divipola", "fecha", "pasajeros", "despachos"]].copy()
            if clase == "MICROBUS":
                d = d[d["fecha"] < "2023-01-01"]
            d["pasajeros"] = np.round(d["pasajeros"] * p).astype("int64")
            d["despachos"] = np.round(d["despachos"] * p).astype("int64")
            d["tipo_despacho"], d["clase_vehiculo"] = tipo, clase
            partes.append(d)
    return pd.concat(partes, ignore_index=True)


def _marcas(diaria: pd.DataFrame) -> pd.DataFrame:
    m = diaria[["ruta_id", "fecha"]].copy()
    for regla in ("despachos_sin_pasajeros", "caida_robusta", "pico_robusto", "pasajeros_por_despacho_bajo"):
        m[regla] = False
    # un día anómalo por una sola regla, para contarlo
    idx = diaria.index[(diaria["ruta_id"] == RUTAS[0]) & (diaria["fecha"] == "2022-03-15")]
    m.loc[idx, "caida_robusta"] = True
    return m


@pytest.fixture
def diaria() -> pd.DataFrame:
    return _diaria()


# ---------------------------------------------------------------- sección 3: variable objetivo
def test_tabla_objetivo_cuenta_ceros_sin_registro_y_anomalos(diaria):
    marcas = _marcas(diaria)
    diaria.loc[(diaria["ruta_id"] == RUTAS[0]) & (diaria["fecha"] == "2022-03-15"), "anomalo"] = True
    t = eda.tabla_objetivo(diaria, marcas)
    assert list(t.columns) == eda.COLUMNAS_OBJETIVO
    assert set(t["ruta_id"]) == set(RUTAS)
    fila = t.set_index("ruta_id").loc[RUTAS[0]]
    assert fila["dias"] == len(_fechas())
    assert fila["sin_registro"] == 30  # mayo de 2021 desde el 2
    assert fila["ceros"] == 30
    assert fila["anomalos"] == 1
    assert fila["anomalos_caida_robusta"] == 1
    assert fila["anomalos_pico_robusto"] == 0
    assert fila["pasajeros_total"] == diaria.loc[diaria["ruta_id"] == RUTAS[0], "pasajeros"].sum()


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
    assert micro23.empty or (micro23["pct"] == 0).all()


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
    d = _diaria()
    # sin exclusión, mayo-2021 (ceros) rebajaría la media: con inicio anterior debe seguir siendo el patrón exacto
    p = eda.perfil_semanal(d, inicio="2021-01-01")
    r = p[p["ruta_id"] == RUTAS[0]].sort_values("dia_semana")
    assert np.allclose(r["razon_vs_media_semanal"].to_numpy(), FACTOR_SEMANAL / FACTOR_SEMANAL.mean(), atol=0.01)


def test_perfil_mensual_marca_anios_completos(diaria):
    p = eda.perfil_mensual(diaria, inicio="2021-06-01")
    assert list(p.columns) == eda.COLUMNAS_PERFIL_MENSUAL
    completos = p[p["anio_completo"]]
    assert set(completos["anio"]) == {2022, 2023}
    assert completos.groupby(["ruta_id", "anio"])["razon_vs_media_anual"].mean().between(0.9, 1.1).all()
    # 2021 desde junio no es un año completo
    assert not p[p["anio"] == 2021]["anio_completo"].any()


def test_tendencia_anual_compara_ventanas_equivalentes_entre_anios():
    d = _diaria(tendencia_anual=0.10)
    t = eda.tendencia_anual(d, inicio="2021-06-01")
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
    comp, resumen = eda.descomposicion(_diaria(ruido=0.05), inicio="2021-06-01", periodos=(7, 365))
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
    d = _diaria()
    huecos = (d["ruta_id"] == RUTAS[0]) & (d["fecha"] >= "2022-01-10") & (d["fecha"] <= "2022-01-12")
    d.loc[huecos, ["pasajeros", "despachos"]] = 0
    d.loc[huecos, "sin_registro"] = True
    comp, resumen = eda.descomposicion(d, inicio="2021-06-01", periodos=(7, 365))
    assert resumen.set_index("ruta_id").loc[RUTAS[0], "sin_registro_imputados"] == 3
    obs = comp[(comp["ruta_id"] == RUTAS[0]) & (comp["fecha"].between("2022-01-10", "2022-01-12"))]["observado_log1p"]
    assert (obs > np.log1p(500)).all()  # no entra el cero


def test_descomposicion_exige_dos_ciclos_del_periodo_mayor():
    d = _diaria()
    corto = d[d["fecha"] <= "2022-03-01"]
    with pytest.raises(ValueError, match="observaciones"):
        eda.descomposicion(corto, inicio="2021-06-01", periodos=(7, 365))


def test_fuerza_estacionalidad_formula():
    rng = np.random.default_rng(0)
    s = np.sin(np.linspace(0, 20 * np.pi, 500))
    r = 0.1 * rng.standard_normal(500)
    esperado = max(0.0, 1 - np.var(r) / np.var(s + r))
    assert eda.fuerza(s, r) == pytest.approx(esperado)
    assert eda.fuerza(np.zeros(10), r[:10]) == 0.0


# ---------------------------------------------------------------- efecto de calendario (solo si existe CA-1)
def _calendario_con_festivo(fechas_festivo: list[str]) -> pd.DataFrame:
    f = _fechas()
    cal = pd.DataFrame({"fecha": f})
    for col in ("festivo", "puente", "semana_santa", "vacaciones_escolares", "fin_de_anio"):
        cal[col] = False
    cal.loc[cal["fecha"].isin(pd.to_datetime(fechas_festivo)), "festivo"] = True
    cal["dia_semana"] = cal["fecha"].dt.day_of_week
    return cal


def test_efecto_calendario_mide_razon_contra_mismo_dia_de_semana_vecino():
    d = _diaria()
    dia = pd.Timestamp("2022-08-15")  # un lunes
    d.loc[(d["fecha"] == dia), "pasajeros"] = (d.loc[d["fecha"] == dia, "pasajeros"] * 1.5).round().astype("int64")
    cal = _calendario_con_festivo(["2022-08-15"])
    t = eda.efecto_calendario(d, cal, "festivo", inicio="2021-06-01")
    assert list(t.columns) == eda.COLUMNAS_EFECTO_CALENDARIO
    assert (t["n_dias"] == 1).all()
    assert np.allclose(t["razon_mediana"], 1.5, atol=0.02)


def test_efecto_calendario_sin_dias_marcados_devuelve_tabla_vacia():
    d = _diaria()
    cal = _calendario_con_festivo([])
    t = eda.efecto_calendario(d, cal, "festivo", inicio="2021-06-01")
    assert t.empty and list(t.columns) == eda.COLUMNAS_EFECTO_CALENDARIO


# ---------------------------------------------------------------- hipótesis (sección 5 y 7)
_CACHE: dict = {}


def _resultados(diaria, calendario=None) -> dict:
    """Cálculo costoso (MSTL): se reutiliza entre pruebas con la misma entrada sin calendario."""
    if calendario is None and "sin" in _CACHE:
        return _CACHE["sin"]
    r = eda.calcular_resultados(diaria, _detalle(diaria), _marcas(diaria), calendario, eda.parametros({}))
    if calendario is None:
        _CACHE["sin"] = r
    return r


def test_hipotesis_sin_calendario_deja_pendientes_las_de_calendario(diaria):
    h = eda.construir_hipotesis(_resultados(diaria))
    validar_hipotesis(h)
    por_id = {x["id"]: x for x in h}
    # orden del enunciado: día de la semana, festivos y puentes, temporada escolar, Semana Santa, fin de año, pospandemia
    assert [por_id[f"H-M1-{i}"]["enunciado"].split()[0:1] for i in (1,)]  # existe
    for i in (2, 3, 4):
        assert por_id[f"H-M1-{i}"]["veredicto"] == "pendiente"
        assert por_id[f"H-M1-{i}"]["resultado"] == "falta el calendario de CA-1"
    for i in (1, 5, 6):
        assert por_id[f"H-M1-{i}"]["resultado"] != "falta el calendario de CA-1"
        assert por_id[f"H-M1-{i}"]["resultado"].strip()
    assert all(x["veredicto"] in VEREDICTOS for x in h)
    # por norma §5.12/§7: nada se confirma hasta modelar
    assert all(x["veredicto"] == "pendiente" for x in h)
    assert len(h) >= 6


def test_hipotesis_con_calendario_evalua_festivos(diaria):
    cal = _calendario_con_festivo(["2022-08-15", "2022-10-17"])
    h = {x["id"]: x for x in eda.construir_hipotesis(_resultados(diaria, cal))}
    assert h["H-M1-2"]["resultado"] != "falta el calendario de CA-1"
    # las demás columnas de calendario no tienen días marcados: se declara, no se inventa
    assert "sin días marcados" in h["H-M1-3"]["resultado"] or h["H-M1-3"]["resultado"] == "falta el calendario de CA-1"
    assert h["H-M1-3"]["veredicto"] == "pendiente"


def test_hipotesis_tienen_todos_los_campos_y_figura_o_tabla_no_vacio(diaria):
    for x in eda.construir_hipotesis(_resultados(diaria)):
        for k in ("enunciado", "justificacion", "evidencia_esperada", "figura_o_tabla", "resultado", "evidencia"):
            assert isinstance(x[k], str) and x[k].strip(), (x["id"], k)


# ---------------------------------------------------------------- main: contratos de salida
def _cfg(tmp_path: Path) -> dict:
    proc = tmp_path / "proc"
    proc.mkdir()
    d = _diaria()
    d.to_parquet(proc / "demanda_diaria.parquet", index=False)
    _detalle(d).to_parquet(proc / "demanda_detalle.parquet", index=False)
    _marcas(d).to_parquet(proc / "marcas_anomalos.parquet", index=False)
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
    cal = _calendario_con_festivo(["2022-08-15"])
    cal.to_parquet(Path(cfg["salida"]["carpeta"]) / "calendario.parquet", index=False)
    eda.main(cfg)
    h = {x["id"]: x for x in leer_hipotesis(Path(cfg["salida"]["eda"]) / "hipotesis.json")}
    assert h["H-M1-2"]["resultado"] != "falta el calendario de CA-1"


def test_main_no_toca_marcas_como_entrada_de_modelos(tmp_path):
    """El EDA es descriptivo: las marcas solo se cuentan; el módulo no debe exponer funciones que las devuelvan como X."""
    assert not hasattr(eda, "matriz_entrada")


def test_implicaciones_cubren_los_seis_temas(diaria):
    imp = eda.construir_implicaciones(_resultados(diaria))
    assert set(imp) >= {"ventana", "variables_calendario", "perdida_conteo", "particion", "cambio_de_regimen", "mayo_2021", "transito"}
    for k, v in imp.items():
        assert isinstance(v, dict) and v.get("decision") and v.get("base"), k
