"""`src/comun/notebooks.py`: `config_notebook` y `correr_demo` (núcleo §5.10)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.comun import notebooks


def _demo(nombre: str = "m1", **extra) -> dict:
    return {"demos": {nombre: {"subcomando": "m1", "config": "demo.yaml", **extra}}}


@pytest.fixture
def carpeta_demo(tmp_path: Path, monkeypatch) -> Path:
    """Directorio de trabajo con un `demo.yaml` y un `run.py` falso que cada prueba rellena."""
    (tmp_path / "demo.yaml").write_text("base_seed: 0\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ------------------------------------------------------------- config_notebook


def test_config_notebook_aplica_cambios_como_set(cfg_file: Path):
    cfg = notebooks.config_notebook(cfg_file, {"entrenamiento.lr": 5e-4, "modelo.capas": [64, 32]}, imprimir=False)
    assert cfg["entrenamiento"] == {"lr": 5e-4}
    assert cfg["modelo"] == {"tipo": "gru", "capas": [64, 32]}


def test_config_notebook_valor_texto_y_entero(cfg_file: Path):
    cfg = notebooks.config_notebook(cfg_file, {"modelo.tipo": "lstm", "base_seed": 7}, imprimir=False)
    assert cfg["modelo"]["tipo"] == "lstm" and cfg["base_seed"] == 7


def test_config_notebook_clave_inexistente_es_error(cfg_file: Path):
    with pytest.raises(ValueError, match="Clave inexistente"):
        notebooks.config_notebook(cfg_file, {"entrenamiento.lt": 1}, imprimir=False)


def test_config_notebook_imprime_la_config_resuelta(cfg_file: Path, capsys):
    notebooks.config_notebook(cfg_file, {"base_seed": 3})
    salida = capsys.readouterr().out
    assert salida.startswith("Configuración final resuelta:\n")
    assert yaml.safe_load(salida.split("\n", 1)[1])["base_seed"] == 3


def test_config_notebook_sin_cambios_y_sin_imprimir(cfg_file: Path, capsys):
    cfg = notebooks.config_notebook(cfg_file, imprimir=False)
    assert cfg["base_seed"] == 0
    assert capsys.readouterr().out == ""


# ------------------------------------------------------------------ correr_demo


def test_correr_demo_pendiente_si_falta_la_config(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert notebooks.correr_demo(_demo(), "m1") == {"estado": "pendiente"}
    assert "Pendiente: todavía no existe demo.yaml" in capsys.readouterr().out


def test_correr_demo_pendiente_si_falta_un_requisito(carpeta_demo: Path):
    res = notebooks.correr_demo(_demo(requiere=["data/no_existe.parquet"]), "m1")
    assert res == {"estado": "pendiente"}


def test_correr_demo_ok_pasa_cambios_y_salida_temporal(carpeta_demo: Path, capsys):
    (carpeta_demo / "run.py").write_text("import sys\nprint('ARGS', sys.argv[1:])\n", encoding="utf-8")
    res = notebooks.correr_demo(_demo(salida_temporal="salida.carpeta"), "m1", {"entrenamiento.lr": 5e-4})
    assert res["estado"] == "ok" and res["codigo"] == 0
    assert "--config', 'demo.yaml'" in res["salida"]
    assert "entrenamiento.lr=0.0005" in res["salida"]
    assert "salida.carpeta=" in res["salida"] and "demo_m1_" in res["salida"]
    assert "$ python run.py m1 --config demo.yaml" in capsys.readouterr().out


def test_correr_demo_error_devuelve_codigo_y_muestra_stderr(carpeta_demo: Path, capsys):
    (carpeta_demo / "run.py").write_text("import sys\nprint('algo salio mal', file=sys.stderr)\nsys.exit(3)\n",
                                         encoding="utf-8")
    res = notebooks.correr_demo(_demo(), "m1")
    assert res["estado"] == "error" and res["codigo"] == 3
    assert "algo salio mal" in capsys.readouterr().out


def test_correr_demo_timeout_no_lanza_y_avisa(carpeta_demo: Path, capsys):
    """Un comando que excede `timeout_s` no debe terminar la celda del notebook en un traceback."""
    (carpeta_demo / "run.py").write_text("import time\nprint('empieza', flush=True)\ntime.sleep(60)\n",
                                         encoding="utf-8")
    res = notebooks.correr_demo(_demo(), "m1", timeout_s=1)
    assert res["estado"] == "timeout"
    assert res["segundos"] >= 1
    assert "1 s" in res["mensaje"] and "m1" in res["mensaje"]
    assert res["mensaje"] in capsys.readouterr().out
