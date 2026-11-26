"""Notebook `00_sustentacion` (núcleo §5.10): estructura, config y celdas por módulo con las demos aún pendientes."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

from src.comun import notebooks

RAIZ = Path(__file__).resolve().parents[1]
FUENTE = RAIZ / "notebooks" / "00_sustentacion.py"
CONFIG = RAIZ / "configs" / "notebooks" / "00_sustentacion.yaml"
MODULOS = ("m1", "m2", "m3")


def _celdas_codigo() -> list[str]:
    import jupytext

    nb = jupytext.read(FUENTE)
    return [c.source for c in nb.cells if c.cell_type == "code"]


def test_primera_celda_de_codigo_define_config_y_un_set_por_modulo():
    espacio: dict = {}
    exec(_celdas_codigo()[0], espacio)  # noqa: S102 - celda de parámetros del propio repo
    assert espacio["CONFIG"] == "configs/notebooks/00_sustentacion.yaml"
    for m in MODULOS:
        assert espacio[f"SET_{m.upper()}"] == {}


def test_segunda_celda_resuelve_la_config_y_una_celda_por_modulo():
    celdas = _celdas_codigo()
    assert "config_notebook(CONFIG)" in celdas[1]
    for m in MODULOS:
        assert sum(f'correr_demo(cfg, "{m}", SET_{m.upper()})' in c for c in celdas) == 1


def test_la_config_carga_con_config_notebook(capsys):
    cfg = notebooks.config_notebook(CONFIG)
    assert "Configuración final resuelta:" in capsys.readouterr().out
    for m in MODULOS:
        demo = cfg["demos"][m]
        assert demo["subcomando"] == m and demo["config"] == f"configs/{m}/demo.yaml"


@pytest.mark.parametrize("modulo", MODULOS)
def test_demo_ausente_devuelve_pendiente_sin_lanzar(modulo, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # sin configs de demo, pase lo que pase en el repo
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert notebooks.correr_demo(cfg, modulo, {}) == {"estado": "pendiente"}


def test_demo_que_apunta_a_un_subcomando_pendiente_devuelve_error_codigo_2(monkeypatch, tmp_path):
    # Subcomando cuyo módulo aún no existe; si ya existe, la prueba deja de ser aplicable.
    if importlib.util.find_spec("src.m2_conduccion.alertas") is not None:
        pytest.skip("m2-alertas ya existe: no hay subcomando pendiente que usar")
    falsa = tmp_path / "demo_falsa.yaml"
    falsa.write_text("base_seed: 0\n", encoding="utf-8")
    monkeypatch.chdir(RAIZ)
    cfg = {"demos": {"m2": {"subcomando": "m2-alertas", "config": str(falsa)}}}
    res = notebooks.correr_demo(cfg, "m2", {})
    assert res["estado"] == "error" and res["codigo"] == 2
    assert "pendiente" in res["salida"]
