"""Pruebas de la serie sintética de M1 (núcleo §5.1 y §5.11)."""

import datetime as dt

import pandas as pd
import pytest
import yaml

from src.m1_demanda import sintetico

COLUMNAS = ["ruta_id", "origen_divipola", "destino_divipola", "fecha", "pasajeros", "despachos", "sin_registro", "anomalo"]


@pytest.fixture(scope="module")
def df():
    return sintetico.generar(0)


def test_esquema_exacto(df):
    assert list(df.columns) == COLUMNAS
    assert len(df) > 0


def test_tipos(df):
    assert df["ruta_id"].map(type).eq(str).all()
    for col in ("origen_divipola", "destino_divipola"):
        assert df[col].map(type).eq(str).all()
        assert df[col].str.len().eq(5).all()
    assert df["fecha"].map(type).eq(dt.date).all()
    assert pd.api.types.is_integer_dtype(df["pasajeros"]) and (df["pasajeros"] >= 0).all()
    assert pd.api.types.is_integer_dtype(df["despachos"]) and (df["despachos"] >= 0).all()
    assert df["sin_registro"].dtype == bool
    assert df["anomalo"].dtype == bool
    assert (df["ruta_id"] == df["origen_divipola"] + "-" + df["destino_divipola"]).all()


def test_cuatro_rutas_dos_pares(df):
    rutas = set(df["ruta_id"])
    assert len(rutas) == 4
    for r in rutas:
        o, d = r.split("-")
        assert f"{d}-{o}" in rutas


def test_codigos_ficticios_departamento_00(df):
    codigos = set(df["origen_divipola"]) | set(df["destino_divipola"])
    assert all(c.startswith("00") for c in codigos)


def test_sin_huecos_y_periodo(df):
    esperado = pd.date_range("2019-01-01", "2024-12-31", freq="D")
    for _, g in df.groupby("ruta_id"):
        fechas = pd.to_datetime(g["fecha"])
        assert list(fechas) == list(esperado)
    assert not df.duplicated(["ruta_id", "fecha"]).any()


def test_reglas_de_dias_especiales(df):
    sr = df[df["sin_registro"]]
    an = df[df["anomalo"]]
    assert len(sr) > 0 and len(an) > 0
    assert (sr["pasajeros"] == 0).all() and (sr["despachos"] == 0).all()
    assert (an["pasajeros"] == 0).all() and (an["despachos"] > 0).all()
    assert not (df["sin_registro"] & df["anomalo"]).any()
    normales = df[~df["sin_registro"] & ~df["anomalo"] & (df["pasajeros"] > 0)]
    assert (normales["despachos"] > 0).all()  # despachos coherentes con pasajeros


def test_estructura_pandemia_y_semana(df):
    df = df.assign(f=pd.to_datetime(df["fecha"]))
    m = df.groupby(df["f"].dt.to_period("Q"))["pasajeros"].mean()
    assert m["2020Q2"] < 0.5 * m["2019Q2"]  # caída tipo pandemia
    assert m["2024Q2"] > 2 * m["2020Q2"]  # recuperación


def test_reproducible(df):
    pd.testing.assert_frame_equal(df, sintetico.generar(0))
    assert not df["pasajeros"].equals(sintetico.generar(1)["pasajeros"])


def test_escribir_archivos(tmp_path):
    parquet, rutas_yaml = sintetico.escribir(0, tmp_path)
    leido = pd.read_parquet(parquet)
    assert list(leido.columns) == COLUMNAS
    assert len(leido) == len(sintetico.generar(0))
    assert parquet.name == "demanda_diaria.parquet" and rutas_yaml.name == "rutas.yaml"

    contenido = yaml.safe_load(rutas_yaml.read_text(encoding="utf-8"))
    assert contenido["sintetico"] is True
    ids = {r["ruta_id"] for r in contenido["rutas"]}
    assert ids == set(leido["ruta_id"])
    for r in contenido["rutas"]:
        assert r["ruta_regreso_id"] in ids
        regreso = next(x for x in contenido["rutas"] if x["ruta_id"] == r["ruta_regreso_id"])
        assert regreso["ruta_regreso_id"] == r["ruta_id"]
