"""Pruebas sin red de src/m1_demanda/datos.py (DA-3/DA-4): series diarias de §5.1, reglas de días sin registro y de
anómalos, rutas.yaml, resumen, validación DIVIPOLA y secciones 1–2 de la plantilla común (§5.12).

Todo con parquets crudos y un DIVIPOLA de juguete creados en la prueba. Códigos de juguete del departamento 00 (no existe
en DIVIPOLA real), salvo cuando se prueba que un código falta en el DIVIPOLA de juguete.
"""
from __future__ import annotations

import datetime as dt
import json
import socket

import numpy as np
import pandas as pd
import pytest
import yaml

from src.m1_demanda import datos as dm

A, B, C = "00001", "00002", "00003"
INICIO, FIN = "2021-01-01", "2021-03-31"
DIAS = pd.date_range(INICIO, FIN, freq="D")

COLUMNAS_51 = ["ruta_id", "origen_divipola", "destino_divipola", "fecha", "pasajeros", "despachos", "sin_registro",
               "anomalo"]


# --------------------------------------------------------------------------- utilidades de juguete
def fila(o, d, fecha, tipo="ORIGEN", clase="BUS", pas=10, desp=1):
    return {"municipio_origen_ruta": o, "municipio_destino_ruta": d, "fecha_despacho": pd.Timestamp(fecha),
            "tipo_despacho": tipo, "clase_vehiculo": clase, "pasajeros": pas, "despachos": desp}


def crudo_base(huecos=(), ceros=(), caidas=(), picos=(), subreportes=()):
    """Ida A→B y regreso B→A todos los días del periodo, con dos clases y algo de tránsito. Pasajeros por día de la
    ida: 100 + 2·(día de la semana mód 3) (BUS ORIGEN, 2 despachos) + 20 (MICROBUS TRANSITO, 1), salvo los días
    modificados; así la serie no es constante y el MAD de los residuos es > 0. Un día de `subreportes` tiene los
    pasajeros normales pero 60 despachos BUS en vez de 2 (pocos pasajeros por despacho, nivel normal)."""
    filas = []
    for d in DIAS:
        f = d.strftime("%Y-%m-%d")
        if f not in huecos:
            pas_bus = 100 + 2 * (d.day_of_week % 3)
            if f in ceros:
                filas.append(fila(A, B, d, "ORIGEN", "BUS", 0, 2))
                filas.append(fila(A, B, d, "TRANSITO", "MICROBUS", 0, 1))
                pas_bus = None
            elif f in caidas:
                pas_bus = 2
            elif f in picos:
                pas_bus = 2000
            if pas_bus is not None:
                filas.append(fila(A, B, d, "ORIGEN", "BUS", pas_bus, 60 if f in subreportes else 2))
                filas.append(fila(A, B, d, "TRANSITO", "MICROBUS", 20, 1))
        filas.append(fila(B, A, d, "ORIGEN", "BUSETA", 50 + (d.day_of_week % 3), 1))
    # Una ruta ajena (no configurada) y un día fuera del periodo: no deben entrar.
    filas.append(fila(A, C, "2021-01-05", pas=999, desp=9))
    filas.append(fila(A, B, "2020-12-31", pas=999, desp=9))
    return pd.DataFrame(filas)


def divipola_juguete(codigos=(A, B, C)):
    nombres = {A: "MUNICIPIO A", B: "MUNICIPIO B", C: "MUNICIPIO C"}
    return pd.DataFrame({"cod_dpto": [c[:2] for c in codigos], "dpto": ["DEPTO CERO"] * len(codigos),
                         "cod_mpio": list(codigos), "nom_mpio": [nombres.get(c, "X") for c in codigos],
                         "tipo_municipio": ["Municipio"] * len(codigos), "longitud": ["0"] * len(codigos),
                         "latitud": ["0"] * len(codigos)})


PARAMS = {
    "despachos_sin_pasajeros": {"activa": True},
    "caida_robusta": {"activa": True, "ventana_dias": 15, "min_periodos": 7, "umbral_mad": 5.0, "escala_mad": 1.4826},
    "pico_robusto": {"activa": True, "ventana_dias": 15, "min_periodos": 7, "umbral_mad": 5.0, "escala_mad": 1.4826},
    "pasajeros_por_despacho_bajo": {"activa": True, "ventana_dias": 15, "min_periodos": 7, "umbral_mad": 5.0,
                                    "escala_mad": 1.4826},
}

VIEWS = {"columns": [
    {"fieldName": "terminal", "name": "TERMINAL", "dataTypeName": "text", "description": "Sede de la terminal"},
    {"fieldName": "pasajeros", "name": "PASAJEROS", "dataTypeName": "number", "description": "Número de pasajeros"},
]}

INFORME = """# Informe
## 1.7 Inconsistencias
### 1.7 Inconsistencias diccionario vs. datos (para el apartado de datos del enunciado)

| # | Diccionario dice | Datos muestran |
|---|---|---|
| 1 | `clase_vehiculo`: «Identificador numérico» | Texto: BUS |
| 2 | Algo \\| con barra | Otra cosa |

## 2. Otra sección
| # | no | entra |
|---|---|---|
| 9 | x | y |
"""


def escribir_entorno(tmp_path, crudo=None, divipola=None, pares=None):
    """Crea la carpeta cruda, el DIVIPOLA, los metadatos y el informe de juguete, y devuelve la config."""
    carpeta = tmp_path / "raw" / "rutas"
    carpeta.mkdir(parents=True)
    crudo = crudo_base() if crudo is None else crudo
    meses = crudo["fecha_despacho"].dt.strftime("%Y-%m")
    for mes, parte in crudo.groupby(meses):
        parte.to_parquet(carpeta / f"{mes}.parquet", index=False)
    (divipola if divipola is not None else divipola_juguete()).to_csv(tmp_path / "divipola.csv", index=False)
    (tmp_path / "views.json").write_text(json.dumps(VIEWS, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "informe.md").write_text(INFORME, encoding="utf-8")
    return {
        "periodo": {"inicio": INICIO, "fin": FIN},
        "criterio_seleccion": "Criterio de juguete.",
        "pares": pares or [{"a": A, "b": B, "descripcion": "par de juguete"}],
        "entrada": {"crudo_rutas": str(carpeta), "divipola": str(tmp_path / "divipola.csv"),
                    "metadatos_fuente": str(tmp_path / "views.json"), "informe_fuentes": str(tmp_path / "informe.md")},
        "salida": {"carpeta": str(tmp_path / "proc"), "detalle": "detalle.parquet", "diaria": "diaria.parquet",
                   "marcas": "marcas.parquet", "rutas": "rutas.yaml", "resumen": "resumen.json",
                   "eda": str(tmp_path / "eda")},
        "fuente": {"nombre": "Conjunto de juguete", "entidad": "Entidad", "id_socrata": "xxxx-yyyy",
                   "url": "https://example.org/d", "url_api": "https://example.org/r", "licencia": "CC BY-SA 4.0",
                   "cita": "Cita de juguete.", "fecha_consulta_informe": "2026-11-24", "n_registros_medido": 123,
                   "n_variables_medido": 10, "fecha_min_medida": "2019-08-04", "fecha_max_medida_valida": "2026-04-07",
                   "divipola_cita": "DANE de juguete."},
        "anomalos": PARAMS,
        "calidad": {"cambio_composicion_pp": 10.0},
    }


def crudo_salida():
    return crudo_base(huecos=("2021-02-10", "2021-02-11"), ceros=("2021-01-20",), caidas=("2021-03-03",),
                      picos=("2021-03-15",), subreportes=("2021-02-24",))


@pytest.fixture
def salida(tmp_path):
    """Corre main() sobre el entorno de juguete con huecos, un día de ceros, una caída, un pico y un sub-reporte en A→B."""
    cfg = escribir_entorno(tmp_path, crudo_salida())
    assert dm.main(cfg) == 0
    proc = tmp_path / "proc"
    return {
        "cfg": cfg, "tmp": tmp_path,
        "diaria": pd.read_parquet(proc / "diaria.parquet"),
        "detalle": pd.read_parquet(proc / "detalle.parquet"),
        "marcas": pd.read_parquet(proc / "marcas.parquet"),
        "rutas": yaml.safe_load((proc / "rutas.yaml").read_text(encoding="utf-8")),
        "resumen": json.loads((proc / "resumen.json").read_text(encoding="utf-8")),
    }


def dia(df, ruta, fecha):
    return df[(df["ruta_id"] == ruta) & (df["fecha"] == dt.date.fromisoformat(fecha))].iloc[0]


# --------------------------------------------------------------------------- esquema y tipos (§5.1)
def test_esquema_exacto_y_tipos_de_la_serie(salida):
    d = salida["diaria"]
    assert list(d.columns) == COLUMNAS_51
    for c in ("ruta_id", "origen_divipola", "destino_divipola"):
        assert d[c].map(type).eq(str).all(), c
    assert d["origen_divipola"].str.fullmatch(r"\d{5}").all() and d["destino_divipola"].str.fullmatch(r"\d{5}").all()
    assert (d["ruta_id"] == d["origen_divipola"] + "-" + d["destino_divipola"]).all()
    assert d["fecha"].map(type).eq(dt.date).all()
    assert d["pasajeros"].dtype == np.int64 and d["despachos"].dtype == np.int64
    assert (d["pasajeros"] >= 0).all() and (d["despachos"] >= 0).all()
    assert d["sin_registro"].dtype == bool and d["anomalo"].dtype == bool


def test_esquema_del_detalle(salida):
    det = salida["detalle"]
    assert list(det.columns) == dm.COLUMNAS_DETALLE
    assert set(det["tipo_despacho"]) <= {"ORIGEN", "TRANSITO"}
    assert det["fecha"].map(type).eq(dt.date).all()
    assert det["pasajeros"].dtype == np.int64 and det["despachos"].dtype == np.int64
    assert not det.duplicated(["ruta_id", "fecha", "tipo_despacho", "clase_vehiculo"]).any()


def test_sin_huecos_una_fila_por_ruta_y_fecha(salida):
    d = salida["diaria"]
    assert set(d["ruta_id"]) == {f"{A}-{B}", f"{B}-{A}"}
    for _, g in d.groupby("ruta_id"):
        assert list(pd.to_datetime(g["fecha"])) == list(DIAS)
    assert not d.duplicated(["ruta_id", "fecha"]).any()
    assert len(d) == 2 * len(DIAS)


def test_solo_rutas_configuradas_y_periodo(salida):
    det = salida["detalle"]
    assert f"{A}-{C}" not in set(det["ruta_id"])
    assert det["fecha"].min() >= dt.date(2021, 1, 1) and det["fecha"].max() <= dt.date(2021, 3, 31)


def test_la_serie_es_la_suma_del_detalle(salida):
    d, det = salida["diaria"], salida["detalle"]
    suma = det.groupby(["ruta_id", "fecha"])[["pasajeros", "despachos"]].sum()
    con = d[~d["sin_registro"]].set_index(["ruta_id", "fecha"])[["pasajeros", "despachos"]]
    pd.testing.assert_frame_equal(con.sort_index(), suma.sort_index(), check_names=False)
    assert d["pasajeros"].sum() == det["pasajeros"].sum()
    # Caso hecho a mano (lunes 4-ene-2021): 100 (BUS ORIGEN) + 20 (MICROBUS TRANSITO) y 2 + 1 despachos.
    f = dia(d, f"{A}-{B}", "2021-01-04")
    assert (f["pasajeros"], f["despachos"]) == (120, 3)


def test_suma_de_filas_repetidas_en_el_crudo():
    """Si el crudo trae dos filas con la misma clave (p. ej. dos parquets solapados), el detalle las suma."""
    crudo = pd.DataFrame([fila(A, B, "2021-01-01", pas=3, desp=1), fila(A, B, "2021-01-01", pas=4, desp=2)])
    det = dm.construir_detalle(crudo, [f"{A}-{B}"], INICIO, FIN)
    assert len(det) == 1 and det.iloc[0]["pasajeros"] == 7 and det.iloc[0]["despachos"] == 3


# --------------------------------------------------------------------------- sin registro
def test_regla_sin_registro_imputa_cero_y_marca(salida):
    d = salida["diaria"]
    for f in ("2021-02-10", "2021-02-11"):
        r = dia(d, f"{A}-{B}", f)
        assert bool(r["sin_registro"]) and r["pasajeros"] == 0 and r["despachos"] == 0
        assert not bool(r["anomalo"])  # sin registro y anómalo son marcas distintas
    assert d.loc[d["ruta_id"] == f"{B}-{A}", "sin_registro"].sum() == 0
    assert d["sin_registro"].sum() == 2


def test_un_dia_con_filas_de_cero_pasajeros_no_es_sin_registro(salida):
    r = dia(salida["diaria"], f"{A}-{B}", "2021-01-20")
    assert not bool(r["sin_registro"]) and r["pasajeros"] == 0 and r["despachos"] == 3


# --------------------------------------------------------------------------- anómalos
def test_regla_despachos_sin_pasajeros_caso_a_mano(salida):
    m = salida["marcas"]
    r = dia(m, f"{A}-{B}", "2021-01-20")
    assert bool(r["despachos_sin_pasajeros"])
    assert m["despachos_sin_pasajeros"].sum() == 1
    assert bool(dia(salida["diaria"], f"{A}-{B}", "2021-01-20")["anomalo"])


def test_regla_caida_robusta_caso_a_mano(salida):
    m = salida["marcas"]
    assert bool(dia(m, f"{A}-{B}", "2021-03-03")["caida_robusta"])  # 2 + 20 = 22 frente a 120 los demás días
    # Solo marca la caída y el día de ceros (que también es caída); nunca un día sin registro.
    marcados = set(m.loc[m["caida_robusta"], "fecha"].astype(str))
    assert marcados == {"2021-03-03", "2021-01-20"}


def test_regla_pico_robusto_caso_a_mano(salida):
    m = salida["marcas"]
    assert bool(dia(m, f"{A}-{B}", "2021-03-15")["pico_robusto"])
    assert set(m.loc[m["pico_robusto"], "fecha"].astype(str)) == {"2021-03-15"}


def test_regla_pasajeros_por_despacho_bajo_caso_a_mano(salida):
    """24-feb: 122 pasajeros (nivel normal) con 61 despachos en vez de 3: solo esta regla lo marca (junto con los días de
    ceros y de caída, donde también hay pocos pasajeros por despacho)."""
    m = salida["marcas"]
    r = dia(m, f"{A}-{B}", "2021-02-24")
    assert bool(r["pasajeros_por_despacho_bajo"]) and not bool(r["caida_robusta"]) and not bool(r["pico_robusto"])
    assert set(m.loc[m["pasajeros_por_despacho_bajo"], "fecha"].astype(str)) == {"2021-02-24", "2021-01-20",
                                                                                "2021-03-03"}
    assert not bool(dia(m, f"{A}-{B}", "2021-03-15")["pasajeros_por_despacho_bajo"])  # pico: muchos por despacho


def test_ruta_regular_sin_marcas(salida):
    """La variación semanal 50/51/52 del regreso no es atípica con el MAD."""
    m = salida["marcas"]
    assert not m.loc[m["ruta_id"] == f"{B}-{A}", dm.REGLAS].any().any()


def test_anomalo_es_el_o_de_las_reglas(salida):
    d = salida["diaria"].set_index(["ruta_id", "fecha"])
    m = salida["marcas"].set_index(["ruta_id", "fecha"])
    assert (d["anomalo"] == m[dm.REGLAS].any(axis=1)).all()
    assert list(salida["marcas"].columns) == ["ruta_id", "fecha", *dm.REGLAS]


def test_dias_sin_registro_nunca_se_marcan_anomalos(salida):
    d = salida["diaria"]
    assert not (d["sin_registro"] & d["anomalo"]).any()
    m = salida["marcas"].merge(d[["ruta_id", "fecha", "sin_registro"]], on=["ruta_id", "fecha"])
    assert not m.loc[m["sin_registro"], dm.REGLAS].any().any()


def test_residuo_robusto_a_mano():
    """y = log1p(P); mediana centrada de ventana 3 (min 1); residuo = y - mediana."""
    p = pd.Series([10.0, 10.0, 1000.0, 10.0, 10.0])
    y = np.log1p(p)
    r = dm.residuo_robusto(y, ventana=3, min_periodos=1)
    assert r.iloc[2] == pytest.approx(y[2] - np.log1p(10.0))
    assert r.iloc[0] == pytest.approx(0.0) and r.iloc[4] == pytest.approx(0.0)


def test_residuo_ignora_nan_y_exige_min_periodos():
    y = pd.Series([1.0, 2.0, np.nan, 4.0, 9.0])
    r = dm.residuo_robusto(y, ventana=3, min_periodos=2)
    assert r.iloc[0] == pytest.approx(1.0 - 1.5)  # ventana [1, 2]
    assert np.isnan(r.iloc[2])  # día sin registro: residuo NaN
    assert r.iloc[3] == pytest.approx(4.0 - 6.5)  # ventana [nan, 4, 9] → mediana de {4, 9}
    r1 = dm.residuo_robusto(pd.Series([1.0, np.nan, np.nan]), ventana=3, min_periodos=2)
    assert r1.isna().all()  # ningún día con 2 valores en la ventana


def test_transformacion_por_despacho_a_mano():
    g = pd.DataFrame({"pasajeros": [9, 0], "despachos": [2, 0], "sin_registro": [False, True]})
    y = dm.transformar(g, "log_pasajeros_por_despacho")
    assert y.iloc[0] == pytest.approx(np.log(10 / 3)) and np.isnan(y.iloc[1])


def test_mad_escalado_a_mano():
    r = pd.Series([1.0, 2.0, 3.0, 4.0, 100.0])  # mediana 3; |r-3| = 2,1,0,1,97 → MAD 1
    assert dm.mad_escalado(r, 1.4826) == pytest.approx(1.4826)


def test_regla_desactivada_no_marca(tmp_path):
    cfg = escribir_entorno(tmp_path, crudo_base(caidas=("2021-03-03",)))
    cfg["anomalos"] = {**PARAMS, "caida_robusta": {**PARAMS["caida_robusta"], "activa": False}}
    dm.main(cfg)
    m = pd.read_parquet(tmp_path / "proc" / "marcas.parquet")
    assert not m["caida_robusta"].any()


def test_reglas_desconocidas_o_faltantes_son_error(tmp_path):
    cfg = escribir_entorno(tmp_path)
    cfg["anomalos"] = {**PARAMS, "regla_inventada": {"activa": True}}
    with pytest.raises(ValueError, match="regla_inventada"):
        dm.main(cfg)
    cfg["anomalos"] = {k: v for k, v in PARAMS.items() if k != "pico_robusto"}
    with pytest.raises(ValueError, match="pico_robusto"):
        dm.main(cfg)


def test_ventana_par_es_error():
    with pytest.raises(ValueError):
        dm.residuo_robusto(pd.Series([1.0, 2.0]), ventana=4, min_periodos=1)


# --------------------------------------------------------------------------- rutas y DIVIPOLA
def test_rutas_yaml_reciproco_y_nombres_de_divipola(salida):
    rutas = {r["ruta_id"]: r for r in salida["rutas"]["rutas"]}
    assert set(rutas) == {f"{A}-{B}", f"{B}-{A}"}
    for rid, r in rutas.items():
        assert rutas[r["ruta_regreso_id"]]["ruta_regreso_id"] == rid
        o, d = rid.split("-")
        assert (r["origen_divipola"], r["destino_divipola"]) == (o, d)
        assert r["criterios_seleccion"].startswith("Criterio de juguete.")
    assert rutas[f"{A}-{B}"]["origen_municipio"] == "MUNICIPIO A"
    assert rutas[f"{A}-{B}"]["destino_municipio"] == "MUNICIPIO B"
    assert rutas[f"{A}-{B}"]["origen_departamento"] == "DEPTO CERO"


def test_codigo_fuera_de_divipola_se_reporta(tmp_path):
    cfg = escribir_entorno(tmp_path, divipola=divipola_juguete((A, C)))  # falta B
    assert dm.main(cfg) == 0
    res = json.loads((tmp_path / "proc" / "resumen.json").read_text(encoding="utf-8"))
    assert res["codigos_fuera_de_divipola"] == [B]
    rutas = yaml.safe_load((tmp_path / "proc" / "rutas.yaml").read_text(encoding="utf-8"))["rutas"]
    r = next(x for x in rutas if x["ruta_id"] == f"{A}-{B}")
    assert r["destino_municipio"].startswith("TODO(dato-faltante)")
    dic = json.loads((tmp_path / "eda" / "diccionario.json").read_text(encoding="utf-8"))
    assert any(B in i["datos_muestran"] for i in dic["inconsistencias_nuevas"])


def test_validar_codigos():
    assert dm.validar_codigos({A, B, "99999"}, divipola_juguete()) == ["99999"]
    assert dm.validar_codigos({A}, divipola_juguete()) == []


def test_pares_repetidos_o_codigos_malos_son_error(tmp_path):
    cfg = escribir_entorno(tmp_path, pares=[{"a": A, "b": B, "descripcion": "x"}, {"a": B, "b": A, "descripcion": "y"}])
    with pytest.raises(ValueError):
        dm.main(cfg)
    cfg["pares"] = [{"a": "1", "b": B, "descripcion": "x"}]
    with pytest.raises(ValueError):
        dm.main(cfg)


# --------------------------------------------------------------------------- resumen
def test_resumen_por_ruta(salida):
    res = salida["resumen"]
    assert res["periodo"] == {"inicio": INICIO, "fin": FIN, "dias": len(DIAS)}
    assert res["conjunto_crudo"]["n_registros"] == 123  # cifra medida citada, no recalculada
    assert res["conjunto_crudo"]["fecha_consulta"] == "2026-11-24"
    r = res["por_ruta"][f"{A}-{B}"]
    assert r["dias"] == len(DIAS) and r["dias_sin_registro"] == 2
    assert r["dias_anomalos_por_regla"]["despachos_sin_pasajeros"] == 1
    det = salida["detalle"]
    ab = det[det["ruta_id"] == f"{A}-{B}"]
    assert r["pasajeros_totales"] == int(ab["pasajeros"].sum())
    pct = 100 * ab.loc[ab["tipo_despacho"] == "TRANSITO", "pasajeros"].sum() / ab["pasajeros"].sum()
    assert r["pct_pasajeros_transito"] == pytest.approx(pct)
    assert sum(r["pct_pasajeros_por_clase"].values()) == pytest.approx(100.0)
    assert res["filas_descargadas"] == len(crudo_salida())
    assert res["filas_fuera_de_rutas_o_periodo"] == 2
    assert len(r["ejemplos_anomalos"]["despachos_sin_pasajeros"]) == 1


# --------------------------------------------------------------------------- plantilla común (DA-4)
def test_ficha_calidad_y_diccionario(salida):
    eda = salida["tmp"] / "eda"
    ficha = json.loads((eda / "ficha.json").read_text(encoding="utf-8"))
    from src.comun.eda import CLAVES_FICHA, COLUMNAS_CALIDAD
    assert set(CLAVES_FICHA) <= set(ficha)
    assert ficha["n_registros"] == 123 and ficha["n_variables"] == 10
    assert set(ficha["sha256"]) == {"2020-12.parquet", "2021-01.parquet", "2021-02.parquet", "2021-03.parquet"}
    assert all(len(v) == 64 for v in ficha["sha256"].values())
    assert ficha["conteos"]["rutas"] == 2
    cal = pd.read_csv(eda / "calidad.csv")
    assert set(COLUMNAS_CALIDAD) <= set(cal.columns) and set(cal["tabla"]) == {"detalle", "serie"}
    dic = json.loads((eda / "diccionario.json").read_text(encoding="utf-8"))
    assert [v["campo"] for v in dic["variables"]] == ["terminal", "pasajeros"]
    assert dic["variables"][1]["descripcion_literal"] == "Número de pasajeros"
    assert [i["n"] for i in dic["inconsistencias_informe"]] == ["1", "2"]
    assert dic["inconsistencias_informe"][1]["diccionario_dice"] == "Algo | con barra"


def test_main_no_usa_la_red(tmp_path, monkeypatch):
    def bloqueado(*a, **k):
        raise RuntimeError("red")

    monkeypatch.setattr(socket.socket, "connect", bloqueado)
    monkeypatch.setattr(socket, "create_connection", bloqueado)
    monkeypatch.setattr(socket, "getaddrinfo", bloqueado)
    assert dm.main(escribir_entorno(tmp_path)) == 0


def test_main_es_determinista(tmp_path):
    cfg = escribir_entorno(tmp_path)
    dm.main(cfg)
    a = (tmp_path / "proc" / "diaria.parquet").read_bytes()
    dm.main(cfg)
    assert (tmp_path / "proc" / "diaria.parquet").read_bytes() == a


def test_sin_parquets_crudos_es_error(tmp_path):
    cfg = escribir_entorno(tmp_path)
    for f in (tmp_path / "raw" / "rutas").glob("*.parquet"):
        f.unlink()
    with pytest.raises(FileNotFoundError):
        dm.main(cfg)


def test_cambio_de_composicion_a_mano():
    """Ruta X: 2021 todo BUS; 2022 mitad BUS y mitad MICROBUS → ambas clases cambian 50 puntos (> 10)."""
    det = pd.DataFrame({
        "ruta_id": ["X"] * 3, "fecha": [dt.date(2021, 5, 1), dt.date(2022, 5, 1), dt.date(2022, 5, 2)],
        "tipo_despacho": ["ORIGEN"] * 3, "clase_vehiculo": ["BUS", "BUS", "MICROBUS"],
        "pasajeros": [100, 50, 50], "despachos": [1, 1, 1]})
    comp = dm.composicion_anual(det, "clase_vehiculo")
    assert comp.loc[("X", 2021), "BUS"] == pytest.approx(100.0)
    assert comp.loc[("X", 2022), "MICROBUS"] == pytest.approx(50.0)
    cambios = dm.cambios_de_composicion(det, 10.0)
    assert {(c["columna"], c["categoria"]) for c in cambios} == {("clase_vehiculo", "BUS"), ("clase_vehiculo", "MICROBUS")}
    assert dm.cambios_de_composicion(det, 60.0) == []


def test_inconsistencias_nuevas_incluyen_el_dia_de_ceros(salida):
    dic = json.loads((salida["tmp"] / "eda" / "diccionario.json").read_text(encoding="utf-8"))
    nuevas = dic["inconsistencias_nuevas"]
    assert all(i["tipo"] in ("diccionario vs. datos", "calidad") for i in nuevas)
    assert any("2021-01-20" in i["datos_muestran"] and i["tipo"] == "diccionario vs. datos" for i in nuevas)
    assert any("sin ningún registro" in i["datos_muestran"] and "2021-02" in i["datos_muestran"] for i in nuevas)
