"""CLI de `run.py` (núcleo §4.1): registro de subcomandos, `--set`, errores claros y subcomandos pendientes."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from src.comun import cli

ROOT = Path(__file__).resolve().parents[1]

SUBCOMANDOS_NUCLEO = [
    "m1-datos", "m1-eda", "m1", "m1-hpo", "m1-operacion",
    "m2-datos", "m2-eda", "m2", "m2-hpo", "m2-alertas",
    "m3-datos", "m3-eda", "m3", "m3-hpo",
    "export", "figures", "notebooks",
]


@pytest.fixture
def cfg_file(tmp_path: Path) -> Path:
    ruta = tmp_path / "cfg.yaml"
    ruta.write_text(
        yaml.safe_dump({"base_seed": 0, "modelo": {"tipo": "gru", "capas": [32, 16]}, "entrenamiento": {"lr": 1e-3}}),
        encoding="utf-8",
    )
    return ruta


@pytest.fixture
def recibido(monkeypatch) -> dict:
    """Sustituye los manejadores del registro por uno falso que guarda la config recibida."""
    llamadas: dict = {}
    for nombre, sub in list(cli.SUBCOMANDOS.items()):

        def falso(cfg, nombre=nombre):
            llamadas[nombre] = cfg
            return 0

        monkeypatch.setitem(cli.SUBCOMANDOS, nombre, sub._replace(manejador=falso))
    return llamadas


def _config_impresa(salida: str) -> dict:
    return yaml.safe_load(salida.split("---", 1)[1].split("...", 1)[0])


def test_registro_de_subcomandos_del_nucleo():
    assert list(cli.SUBCOMANDOS) == SUBCOMANDOS_NUCLEO
    usa_config = {nombre: sub.usa_config for nombre, sub in cli.SUBCOMANDOS.items()}
    assert usa_config == {nombre: nombre not in {"export", "figures", "notebooks"} for nombre in SUBCOMANDOS_NUCLEO}


@pytest.mark.parametrize("nombre", SUBCOMANDOS_NUCLEO)
def test_cada_subcomando_existe_en_el_parser(nombre: str, capsys):
    with pytest.raises(SystemExit) as exc:
        cli.build_parser().parse_args([nombre, "--help"])
    assert exc.value.code == 0
    assert f"run.py {nombre}" in capsys.readouterr().out


def test_set_imprime_y_entrega_la_config_final(cfg_file: Path, recibido: dict, capsys):
    argv = ["m1", "--config", str(cfg_file), "--set", "entrenamiento.lr=5e-4", "--set", "modelo.capas=[64, 32]"]
    assert cli.main(argv) == 0
    salida = capsys.readouterr().out
    impreso = _config_impresa(salida)
    assert impreso["modelo"] == {"tipo": "gru", "capas": [64, 32]}
    assert impreso["entrenamiento"] == {"lr": 5e-4}
    assert recibido["m1"] == impreso
    assert "Tiempo de ejecución:" in salida


def test_clave_inexistente_es_error_con_uso_del_subcomando(cfg_file: Path, recibido: dict, capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["m2", "--config", str(cfg_file), "--set", "entrenamiento.lt=1"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "entrenamiento.lt" in err and "usage: run.py m2" in err
    assert recibido == {}


def test_subcomando_sin_config(recibido: dict):
    assert cli.main(["figures"]) == 0
    assert recibido == {"figures": None}


def test_subcomando_no_implementado_sale_con_codigo_2(cfg_file: Path, capsys):
    """`m1-operacion` no existe todavía (es de Camila): «pendiente: <dueño> (<ID>)» y código 2."""
    assert cli.main(["m1-operacion", "--config", str(cfg_file)]) == 2
    assert "pendiente: Camila (CA-3)" in capsys.readouterr().out


def test_subcomando_conectado_se_despacha_a_main(cfg_file: Path, monkeypatch):
    """Un módulo con `main(cfg)` se ejecuta y su código de salida se respeta."""
    import types

    visto: dict = {}

    def main(cfg):
        visto["cfg"] = cfg

    falso = types.ModuleType("falso")
    falso.main = main
    monkeypatch.setattr(cli.importlib, "import_module", lambda nombre: falso)
    assert cli._despachar("src.m1_demanda.datos", "Daniel", "DA-3")({"a": 1}) == 0
    assert visto["cfg"] == {"a": 1}


def test_fallo_interno_de_un_modulo_no_se_confunde_con_pendiente(monkeypatch):
    """Si el módulo existe pero le falta otra dependencia, el error se propaga (no es «pendiente»)."""

    def importar(nombre):
        raise ModuleNotFoundError("No module named 'otra_cosa'", name="otra_cosa")

    monkeypatch.setattr(cli.importlib, "import_module", importar)
    with pytest.raises(ModuleNotFoundError):
        cli._despachar("src.m1_demanda.datos", "Daniel", "DA-3")(None)


def test_export_y_figures_recorren_lo_que_exista(capsys):
    assert cli.main(["export"]) == 0
    assert cli.main(["figures"]) == 0
    salida = capsys.readouterr().out
    assert "se omite" in salida or "export:" in salida


def test_run_py_ayuda_en_otro_proceso():
    res = subprocess.run([sys.executable, "run.py", "--help"], cwd=ROOT, capture_output=True,
                         encoding="utf-8", check=False)
    assert res.returncode == 0, res.stderr
    for nombre in SUBCOMANDOS_NUCLEO:
        assert nombre in res.stdout


def test_run_py_subcomando_pendiente_en_otro_proceso(cfg_file: Path):
    res = subprocess.run([sys.executable, "run.py", "m1", "--config", str(cfg_file)], cwd=ROOT,
                         capture_output=True, encoding="utf-8", check=False)
    assert res.returncode == 2, res.stdout + res.stderr
    assert "pendiente:" in res.stdout
