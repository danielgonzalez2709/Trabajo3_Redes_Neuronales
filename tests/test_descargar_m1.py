"""Pruebas sin red de scripts/descargar_m1.py (construcción de consultas SoQL, paginación, ranking, reintentos)."""
import argparse
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest
import requests

RAIZ = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("descargar_m1", RAIZ / "scripts" / "descargar_m1.py")
dm = importlib.util.module_from_spec(_spec)
sys.modules["descargar_m1"] = dm
_spec.loader.exec_module(dm)

RUTAS = [("05001", "11001"), ("11001", "05001")]


def test_where_mes_rango_y_fechas_imposibles():
    w = dm.where_mes(2021, 12)
    assert 'fecha_despacho >= "2021-12-01T00:00:00"' in w
    assert 'fecha_despacho < "2022-01-01T00:00:00"' in w  # fin exclusivo, cruza de año
    assert 'fecha_despacho < "2100-01-01"' in w
    assert "municipio_origen_ruta" not in w


def test_where_mes_con_lista_de_rutas():
    w = dm.where_mes(2022, 2, RUTAS)
    assert "(municipio_origen_ruta='05001' AND municipio_destino_ruta='11001')" in w
    assert "(municipio_origen_ruta='11001' AND municipio_destino_ruta='05001')" in w
    assert " OR " in w
    assert 'fecha_despacho < "2022-03-01T00:00:00"' in w


def test_where_rutas_rechaza_codigos_malos_y_vacio():
    with pytest.raises(ValueError):
        dm.where_rutas([("5001", "11001")])
    with pytest.raises(ValueError):
        dm.where_rutas([("05001", "1'; DROP")])
    with pytest.raises(ValueError):
        dm.where_rutas([])


def test_params_descarga_group_order_paginacion():
    p = dm.params_descarga_mes(2022, 1, RUTAS)
    claves = "municipio_origen_ruta, municipio_destino_ruta, fecha_despacho, tipo_despacho, clase_vehiculo"
    assert p["$group"] == claves and p["$order"] == claves
    assert "sum(pasajeros) as pasajeros" in p["$select"] and "sum(despachos) as despachos" in p["$select"]
    assert "$limit" not in p and "$offset" not in p  # los pone `paginar`


def test_params_ranking_dia():
    p = dm.params_ranking_dia(date(2021, 1, 13))
    assert p["$group"] == "municipio_origen_ruta, municipio_destino_ruta"
    assert 'fecha_despacho = "2021-01-13T00:00:00"' in p["$where"]
    assert "count(*) as filas" in p["$select"]


def test_dias_muestra_son_36_segundos_miercoles():
    dias = dm.dias_muestra()
    assert len(dias) == 36 and dias[0].year == 2021 and dias[-1] == date(2023, 12, 13)
    assert all(d.weekday() == 2 and 8 <= d.day <= 14 for d in dias)
    assert dias[0] == date(2021, 1, 13)


def test_paginar_recorre_paginas_y_exige_order():
    llamadas = []

    def falsa(p, **kw):
        llamadas.append((p["$limit"], p["$offset"]))
        return [{"x": 1}] * 2 if p["$offset"] < 4 else [{"x": 1}]

    assert len(dm.paginar({"$order": "x"}, pagina=2, consulta=falsa)) == 5
    assert llamadas == [(2, 0), (2, 2), (2, 4)]
    with pytest.raises(ValueError):
        dm.paginar({}, consulta=falsa)


MUESTRAS = {
    "2021-01-13": [
        {"municipio_origen_ruta": "05001", "municipio_destino_ruta": "11001", "pasajeros": "100", "despachos": "10", "filas": "5"},
        {"municipio_origen_ruta": "11001", "municipio_destino_ruta": "05001", "pasajeros": "80", "despachos": "8", "filas": "4"},
        {"municipio_origen_ruta": "05001", "municipio_destino_ruta": "05001", "pasajeros": "999", "despachos": "9", "filas": "9"},
        {"municipio_origen_ruta": "76001", "municipio_destino_ruta": "76306", "pasajeros": "50", "despachos": "5", "filas": "2"},
    ],
    "2021-02-10": [
        {"municipio_origen_ruta": "05001", "municipio_destino_ruta": "11001", "pasajeros": "20", "despachos": "2", "filas": "1"},
        {"municipio_origen_ruta": "76306", "municipio_destino_ruta": "76001", "pasajeros": "70", "despachos": "7", "filas": "3"},
    ],
    "2021-03-10": [],
}


def test_armar_ranking():
    rk = dm.armar_ranking(MUESTRAS, n_dias=3)
    assert not (rk["origen"] == rk["destino"]).any()  # sin intramunicipales
    fila = rk[(rk.origen == "05001") & (rk.destino == "11001")].iloc[0]
    assert (fila.pasajeros, fila.dias_con_registros, fila.pasajeros_regreso, fila.dias_regreso) == (120, 2, 80, 1)
    assert fila.min_ida_regreso == 80 and fila.n_dias_muestra == 3
    sin_regreso = rk[(rk.origen == "76001") & (rk.destino == "76306")].iloc[0]
    assert sin_regreso.pasajeros == 50 and sin_regreso.pasajeros_regreso == 70


def test_pares_ida_regreso_orden_y_nombres():
    rk = dm.armar_ranking(MUESTRAS, n_dias=3)
    dv = pd.DataFrame({"cod_mpio": ["05001", "11001", "76001"], "nom_mpio": ["A", "B", "C"], "dpto": ["X", "Y", "Z"]})
    top = dm.pares_ida_regreso(rk, dv, n=5)
    # un renglón por par no ordenado: (05001,11001) con min 80 y (76001,76306) con min 50
    assert list(zip(top.origen, top.destino)) == [("05001", "11001"), ("76001", "76306")]
    assert top.loc[0, "origen_nombre"] == "A" and top.loc[0, "destino_dpto"] == "Y"
    assert pd.isna(top.loc[1, "destino_nombre"])  # 76306 no está en este DIVIPOLA de prueba
    assert dm.codigos_fuera_de_divipola(rk, dv) == ["76306"]


def test_descargar_rutas_reanudable(tmp_path):
    cuenta = []

    def falsa(p, **kw):
        cuenta.append(p["$where"])
        return [{"municipio_origen_ruta": "05001", "municipio_destino_ruta": "11001", "fecha_despacho": "2022-01-02T00:00:00.000",
                 "tipo_despacho": "ORIGEN", "clase_vehiculo": "BUS", "pasajeros": "7", "despachos": "1"}]

    esc = dm.descargar_rutas(RUTAS, date(2022, 1, 1), date(2022, 2, 28), destino=tmp_path, consulta=falsa)
    assert [f.name for f in esc] == ["2022-01.parquet", "2022-02.parquet"] and len(cuenta) == 2
    df = pd.read_parquet(tmp_path / "2022-01.parquet")
    assert df["pasajeros"].dtype == "int64" and df.loc[0, "pasajeros"] == 7
    assert dm.descargar_rutas(RUTAS, date(2022, 1, 1), date(2022, 2, 28), destino=tmp_path, consulta=falsa) == []
    assert len(cuenta) == 2  # reanudó: no volvió a consultar


class _Resp:
    def __init__(self, codigo, datos=None):
        self.status_code, self._d, self.url = codigo, datos or [], "https://ejemplo/x?a=1"

    def json(self):
        return self._d

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)


class _Sesion:
    def __init__(self, *respuestas):
        self.resp = list(respuestas)
        self.n = 0

    def get(self, url, params, timeout):
        self.n += 1
        r = self.resp.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def test_consultar_reintenta_5xx_y_timeout_y_registra(tmp_path):
    s = _Sesion(requests.Timeout("lento"), _Resp(503), _Resp(200, [{"a": 1}]))
    log = tmp_path / "log.jsonl"
    assert dm.consultar({"$limit": 1}, reintentos=3, espera=0, sesion=s, log=log) == [{"a": 1}]
    assert s.n == 3 and len(log.read_text().splitlines()) == 3


def test_consultar_agota_reintentos_y_no_reintenta_4xx(tmp_path):
    s = _Sesion(_Resp(500), _Resp(500))
    with pytest.raises(requests.HTTPError):
        dm.consultar({}, reintentos=2, espera=0, sesion=s, log=tmp_path / "l.jsonl")
    s = _Sesion(_Resp(400))
    with pytest.raises(requests.HTTPError):
        dm.consultar({}, reintentos=3, espera=0, sesion=s, log=tmp_path / "l.jsonl")
    assert s.n == 1


# --------------------------------------------------------------------------- DA-3c
def test_un_solo_origen_de_sha256_y_leer_divipola():
    from src.m1_demanda import datos
    assert dm.sha256 is datos.sha256 and dm.leer_divipola is datos.leer_divipola


def test_consultar_json_invalido_se_reintenta_y_se_registra(tmp_path):
    class _Rota(_Resp):
        def json(self):
            raise requests.exceptions.JSONDecodeError("no es json", "<html>", 0)

    s = _Sesion(_Rota(200), _Resp(200, [{"a": 1}]))
    log = tmp_path / "log.jsonl"
    assert dm.consultar({}, reintentos=2, espera=0, sesion=s, log=log) == [{"a": 1}]
    assert s.n == 2 and "error" in log.read_text().splitlines()[0]
    s = _Sesion(_Rota(200), _Rota(200))
    with pytest.raises(ValueError):
        dm.consultar({}, reintentos=2, espera=0, sesion=s, log=tmp_path / "l2.jsonl")


def test_leer_rutas_valida_el_formato():
    assert dm.leer_rutas("05001-11001, 11001-05001") == RUTAS
    for malo in ("05001", "05001-11001-76001", "5001-11001", "05001-abcde", ""):
        with pytest.raises(ValueError, match="ORIGEN-DESTINO|vacía"):
            dm.leer_rutas(malo)


def test_params_conteo_mes_cuenta_registros_sin_agrupar_por_clase():
    p = dm.params_conteo_mes(2022, 1, RUTAS)
    assert "count(*) as registros" in p["$select"]
    assert p["$group"] == "municipio_origen_ruta, municipio_destino_ruta" and "$order" in p
    assert "clase_vehiculo" not in p["$select"] + p["$group"]  # no se confunde con la descarga en el log
    assert 'fecha_despacho >= "2022-01-01T00:00:00"' in p["$where"] and "(municipio_origen_ruta='05001'" in p["$where"]


def _conteo_falso(cuenta):
    def falsa(p, **kw):
        cuenta.append(p["$where"])
        mes = p["$where"].split('"')[1][:7]
        n = {"2022-01": 10, "2022-02": 20}.get(mes, 0)
        return [{"municipio_origen_ruta": "05001", "municipio_destino_ruta": "11001", "registros": str(n)}] if n else []

    return falsa


def test_contar_registros_por_mes_y_ruta_con_ceros_y_reanudable(tmp_path):
    cuenta: list[str] = []
    csv = tmp_path / "conteo.csv"
    t = dm.contar_registros(RUTAS, date(2022, 1, 1), date(2022, 3, 31), csv, consulta=_conteo_falso(cuenta),
                            fecha="2026-11-25")
    assert len(cuenta) == 3 and len(t) == 6  # 3 meses × 2 rutas; las que no devuelven filas quedan en 0
    assert list(t.columns) == ["mes", "ruta_id", "registros", "fecha_consulta"]
    fila = t[(t["mes"] == "2022-02") & (t["ruta_id"] == "05001-11001")].iloc[0]
    assert fila["registros"] == 20 and fila["fecha_consulta"] == "2026-11-25"
    assert t[(t["mes"] == "2022-03")]["registros"].tolist() == [0, 0]
    assert t["registros"].dtype == "int64" and pd.read_csv(csv, dtype={"mes": str}).shape == (6, 4)
    # reanudable: no vuelve a consultar los meses que ya están
    dm.contar_registros(RUTAS, date(2022, 1, 1), date(2022, 3, 31), csv, consulta=_conteo_falso(cuenta))
    assert len(cuenta) == 3
    # un mes nuevo solo consulta ese mes
    dm.contar_registros(RUTAS, date(2022, 1, 1), date(2022, 4, 30), csv, consulta=_conteo_falso(cuenta),
                        fecha="2026-11-26")
    assert len(cuenta) == 4
    t2 = pd.read_csv(csv, dtype={"mes": str})
    assert t2["mes"].nunique() == 4 and set(t2["fecha_consulta"]) == {"2026-11-25", "2026-11-26"}


def test_ranking_con_fallos_registra_y_sigue(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(dm, "RAW", tmp_path / "raw")
    monkeypatch.setattr(dm, "DIVIPOLA_CSV", tmp_path / "divipola.csv")
    pd.DataFrame({"cod_mpio": ["05001", "11001"], "nom_mpio": ["A", "B"], "dpto": ["X", "Y"]}).to_csv(
        tmp_path / "divipola.csv", index=False)
    dias = dm.dias_muestra()
    malo = dias[1]

    def falsa(params, **kw):
        if f'"{malo:%Y-%m-%d}T' in params["$where"]:
            raise requests.Timeout("lento")
        return [{"municipio_origen_ruta": "05001", "municipio_destino_ruta": "11001", "pasajeros": "9",
                 "despachos": "1", "filas": "1"},
                {"municipio_origen_ruta": "11001", "municipio_destino_ruta": "05001", "pasajeros": "8",
                 "despachos": "1", "filas": "1"}]

    monkeypatch.setattr(dm, "paginar", lambda params, **kw: falsa(params))
    args = argparse.Namespace(timeout=1, reintentos=1, paralelo=2)
    assert dm.cmd_ranking(args) == 0
    guardado = json.loads((tmp_path / "raw" / "ranking_dias.json").read_text(encoding="utf-8"))
    assert list(guardado["fallidos"]) == [malo.isoformat()] and "Timeout" in guardado["fallidos"][malo.isoformat()]
    assert len(guardado["muestras"]) == len(dias) - 1
    rk = pd.read_csv(tmp_path / "raw" / "ranking_rutas.csv", dtype=str)
    assert rk["n_dias_muestra"].iloc[0] == str(len(dias))  # el denominador cuenta los días que fallaron
    assert "FALLO" in capsys.readouterr().out


def test_ranking_error_que_no_es_de_red_no_se_traga(tmp_path, monkeypatch):
    monkeypatch.setattr(dm, "RAW", tmp_path / "raw")

    def con_bug(params, **kw):
        raise KeyError("bug de programación")

    monkeypatch.setattr(dm, "paginar", con_bug)
    with pytest.raises(KeyError):
        dm.cmd_ranking(argparse.Namespace(timeout=1, reintentos=1, paralelo=1))


def test_ranking_sin_divipola_sale_con_codigo_distinto_de_cero(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(dm, "RAW", tmp_path / "raw")
    monkeypatch.setattr(dm, "DIVIPOLA_CSV", tmp_path / "no_existe.csv")
    monkeypatch.setattr(dm, "paginar", lambda params, **kw: [])
    assert dm.cmd_ranking(argparse.Namespace(timeout=1, reintentos=1, paralelo=1)) != 0
    assert "divipola" in capsys.readouterr().err.lower()


def test_descargar_con_desde_mayor_que_hasta_o_rutas_malas_sale_con_codigo_distinto_de_cero(capsys):
    assert dm.main(["descargar", "--rutas", "05001-11001", "--desde", "2022-03-01", "--hasta", "2022-01-01"]) != 0
    assert dm.main(["descargar", "--rutas", "05001", "--desde", "2022-01-01", "--hasta", "2022-02-01"]) != 0
    assert dm.main(["contar", "--rutas", "05001-11001", "--desde", "2022-03-01", "--hasta", "2022-01-01"]) != 0
    err = capsys.readouterr().err
    assert "--desde" in err and "ORIGEN-DESTINO" in err


def test_armar_ranking_con_muestras_vacias():
    rk = dm.armar_ranking({"2021-01-13": [], "2021-02-10": []})
    assert rk.empty and list(rk.columns)[:2] == ["origen", "destino"] and "min_ida_regreso" in rk.columns
    assert dm.armar_ranking({}).empty
    assert dm.pares_ida_regreso(rk).empty  # no revienta aguas abajo
    dv = pd.DataFrame({"cod_mpio": ["05001"], "nom_mpio": ["A"], "dpto": ["X"]})
    assert dm.codigos_fuera_de_divipola(rk, dv) == []


def test_cmd_ranking_no_modifica_las_opciones_globales_de_pandas(tmp_path, monkeypatch):
    monkeypatch.setattr(dm, "RAW", tmp_path / "raw")
    monkeypatch.setattr(dm, "DIVIPOLA_CSV", tmp_path / "divipola.csv")
    pd.DataFrame({"cod_mpio": ["05001", "11001"], "nom_mpio": ["A", "B"], "dpto": ["X", "Y"]}).to_csv(
        tmp_path / "divipola.csv", index=False)
    monkeypatch.setattr(dm, "paginar", lambda params, **kw: [
        {"municipio_origen_ruta": "05001", "municipio_destino_ruta": "11001", "pasajeros": "9", "despachos": "1",
         "filas": "1"},
        {"municipio_origen_ruta": "11001", "municipio_destino_ruta": "05001", "pasajeros": "8", "despachos": "1",
         "filas": "1"}])
    antes = pd.get_option("display.width")
    assert dm.cmd_ranking(argparse.Namespace(timeout=1, reintentos=1, paralelo=1)) == 0
    assert pd.get_option("display.width") == antes
