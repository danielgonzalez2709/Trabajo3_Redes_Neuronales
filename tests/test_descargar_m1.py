"""Pruebas sin red de scripts/descargar_m1.py (construcción de consultas SoQL, paginación, ranking, reintentos)."""
import importlib.util
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
    p = dm.params_descarga_mes(2022, 1, RUTAS, pagina=1000, offset=2000)
    claves = "municipio_origen_ruta, municipio_destino_ruta, fecha_despacho, tipo_despacho, clase_vehiculo"
    assert p["$group"] == claves and p["$order"] == claves
    assert "sum(pasajeros) as pasajeros" in p["$select"] and "sum(despachos) as despachos" in p["$select"]
    assert p["$limit"] == 1000 and p["$offset"] == 2000


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
