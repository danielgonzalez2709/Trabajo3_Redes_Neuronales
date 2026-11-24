"""Pruebas de la plantilla común de análisis descriptivo (núcleo §5.12)."""

import json

import numpy as np
import pandas as pd
import pytest

from src.comun import eda

FICHA_OK = {
    "fuente": "Fuente de prueba",
    "cita": "TODO(cita)",
    "url": "https://example.org",
    "fecha_descarga": "2026-11-24",
    "sha256": "0" * 64,
    "unidad_de_observacion": "ruta-día",
    "n_registros": 10,
    "n_variables": 3,
    "periodo": "2019-01-01/2024-12-31",
    "conteos": {"rutas": 4},
}


def _hipotesis(id_="H-M1-1", **cambios):
    h = {
        "id": id_,
        "enunciado": "Los viernes hay más pasajeros.",
        "justificacion": "Viajes de fin de semana.",
        "evidencia_esperada": "Media de viernes mayor que la de martes.",
        "figura_o_tabla": "fig_semanal",
        "resultado": "",
        "veredicto": "pendiente",
        "evidencia": "",
    }
    h.update(cambios)
    return h


def test_secciones_plantilla_exactas():
    assert eda.SECCIONES_PLANTILLA == (
        "Ficha del conjunto",
        "Diccionario y calidad",
        "Variable objetivo",
        "Estructura y heterogeneidad",
        "Hipótesis explícitas",
        "Implicaciones para el modelado",
        "Veredicto de las hipótesis",
    )


def test_ficha_ok_utf8(tmp_path):
    ruta = tmp_path / "eda" / "ficha.json"
    datos = dict(FICHA_OK, fuente="Ministerio de Transporte, año ñ")
    eda.escribir_ficha(ruta, datos)
    assert json.loads(ruta.read_text(encoding="utf-8")) == datos
    assert "ñ" in ruta.read_text(encoding="utf-8")


@pytest.mark.parametrize("clave", sorted(FICHA_OK))
def test_ficha_clave_faltante(tmp_path, clave):
    datos = {k: v for k, v in FICHA_OK.items() if k != clave}
    with pytest.raises(ValueError, match=clave):
        eda.escribir_ficha(tmp_path / "ficha.json", datos)
    assert not (tmp_path / "ficha.json").exists()


def test_tabla_calidad():
    df = pd.DataFrame({"a": [1, 2, np.nan, 2], "b": ["x", None, "y", "x"]})
    t = eda.tabla_calidad(df)
    assert list(t.columns) == ["columna", "tipo", "faltantes", "pct_faltantes", "unicos", "ejemplo"]
    assert list(t["columna"]) == ["a", "b"]
    fila_a = t.set_index("columna").loc["a"]
    assert fila_a["faltantes"] == 1
    assert fila_a["pct_faltantes"] == pytest.approx(25.0)
    assert fila_a["unicos"] == 2
    assert fila_a["ejemplo"] in ("1.0", "2.0")
    fila_b = t.set_index("columna").loc["b"]
    assert fila_b["faltantes"] == 1 and fila_b["unicos"] == 2 and fila_b["ejemplo"] in ("x", "y")


def test_tabla_calidad_columna_vacia():
    t = eda.tabla_calidad(pd.DataFrame({"a": [None, None]}))
    assert t.loc[0, "pct_faltantes"] == 100.0 and t.loc[0, "ejemplo"] == ""


def test_hipotesis_ida_y_vuelta(tmp_path):
    ruta = tmp_path / "hipotesis.json"
    hs = [_hipotesis("H-M1-1"), _hipotesis("H-M2-10", veredicto="confirmada")]
    eda.escribir_hipotesis(ruta, hs)
    assert eda.leer_hipotesis(ruta) == hs


@pytest.mark.parametrize("malo", ["H-M4-1", "H-M1-", "M1-1", "H-M1-a", "h-M1-1"])
def test_hipotesis_id_invalido(tmp_path, malo):
    with pytest.raises(ValueError, match="id"):
        eda.escribir_hipotesis(tmp_path / "h.json", [_hipotesis(malo)])


def test_hipotesis_id_repetido(tmp_path):
    with pytest.raises(ValueError, match="repetid"):
        eda.escribir_hipotesis(tmp_path / "h.json", [_hipotesis(), _hipotesis()])


def test_hipotesis_veredicto_invalido(tmp_path):
    with pytest.raises(ValueError, match="veredicto"):
        eda.escribir_hipotesis(tmp_path / "h.json", [_hipotesis(veredicto="quizá")])


@pytest.mark.parametrize("clave", ["enunciado", "justificacion", "evidencia_esperada", "figura_o_tabla", "resultado", "evidencia"])
def test_hipotesis_clave_faltante(tmp_path, clave):
    h = _hipotesis()
    del h[clave]
    with pytest.raises(ValueError, match=clave):
        eda.escribir_hipotesis(tmp_path / "h.json", [h])


def test_leer_hipotesis_valida_esquema(tmp_path):
    ruta = tmp_path / "h.json"
    ruta.write_text(json.dumps([_hipotesis(veredicto="nada")]), encoding="utf-8")
    with pytest.raises(ValueError, match="veredicto"):
        eda.leer_hipotesis(ruta)


def test_hipotesis_no_es_lista(tmp_path):
    with pytest.raises(ValueError, match="lista"):
        eda.escribir_hipotesis(tmp_path / "h.json", {"id": "H-M1-1"})
