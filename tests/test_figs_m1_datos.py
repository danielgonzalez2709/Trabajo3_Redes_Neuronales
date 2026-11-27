"""Pruebas de las figuras del análisis descriptivo de M1 (CA-4): `generar()` debe escribir las figuras esperadas."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import pytest  # noqa: E402

import datos_eda_m1 as d  # noqa: E402  (módulo de utilidades de pruebas; tests/ queda en sys.path)
from src.m1_demanda import eda  # noqa: E402
from src.viz import figs_m1_datos  # noqa: E402


@pytest.fixture(scope="module")
def carpeta_eda(tmp_path_factory):
    x = d.diaria()
    res = eda.calcular_resultados(x, d.detalle(x), d.marcas(x), None, eda.parametros({}))
    destino = tmp_path_factory.mktemp("eda")
    eda.escribir_resultados(res, destino)
    return destino


def test_generar_escribe_las_figuras_minimas(carpeta_eda, tmp_path):
    rutas = figs_m1_datos.generar(carpeta_eda=carpeta_eda, salida=tmp_path / "figs")
    nombres = {r.name for r in rutas}
    esperadas = {
        "m1_series_rutas.png",
        "m1_perfil_semanal.png",
        "m1_perfil_mensual.png",
        "m1_tendencia_anual.png",
        "m1_transito_origen.png",
        "m1_transito_mensual.png",
        "m1_clases_rutas.png",
    } | {f"m1_descomposicion_{ruta}.png" for ruta in d.RUTAS}
    assert esperadas <= nombres, esperadas - nombres
    for r in rutas:
        assert r.exists() and r.stat().st_size > 1000, r


def test_generar_sin_resultados_no_falla_y_no_escribe(tmp_path):
    assert figs_m1_datos.generar(carpeta_eda=tmp_path / "no_existe", salida=tmp_path / "figs") == []


def test_cada_ruta_tiene_un_color_fijo():
    """El color sigue a la entidad (paleta.py): la misma ruta usa el mismo color en todas las figuras."""
    c1 = figs_m1_datos.color_ruta("11001-76001")
    c2 = figs_m1_datos.color_ruta("11001-76001")
    assert c1 == c2
    assert figs_m1_datos.color_ruta("76001-11001") != c1


def test_carpetas_por_defecto_son_relativas_a_la_raiz_del_repo():
    assert figs_m1_datos.CARPETA_EDA.is_absolute() and figs_m1_datos.CARPETA_EDA == eda.RAIZ / "results/data/m1/eda"
    assert figs_m1_datos.CARPETA_FIGURAS == eda.RAIZ / "results/figures/m1"
