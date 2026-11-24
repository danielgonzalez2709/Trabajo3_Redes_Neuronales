"""CLI de `run.py` (núcleo §4.1): registro de subcomandos, `--set`, errores claros y subcomandos pendientes."""

from __future__ import annotations

import subprocess
import sys
import types
from pathlib import Path

import pytest

from src.comun import cli

ROOT = Path(__file__).resolve().parents[1]

SUBCOMANDOS_NUCLEO = [
    "m1-datos", "m1-eda", "m1", "m1-hpo", "m1-operacion",
    "m2-datos", "m2-eda", "m2", "m2-hpo", "m2-alertas",
    "m3-datos", "m3-eda", "m3", "m3-hpo",
    "export", "figures", "notebooks",
]


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


def test_set_imprime_y_entrega_la_config_final(cfg_file: Path, recibido: dict, config_impresa, capsys):
    argv = ["m1", "--config", str(cfg_file), "--set", "entrenamiento.lr=5e-4", "--set", "modelo.capas=[64, 32]"]
    assert cli.main(argv) == 0
    salida = capsys.readouterr().out
    impreso = config_impresa(salida)
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


@pytest.fixture
def subcomando_falso(monkeypatch):
    """Registra `fantasma` en el CLI; el módulo y el dueño se fijan en cada prueba."""

    def registrar(modulo: str) -> None:
        monkeypatch.setitem(cli.SUBCOMANDOS, "fantasma",
                            cli.Subcomando("falso", True, cli._despachar(modulo, "Dueña", "XX-1")))

    return registrar


def test_subcomando_no_implementado_sale_con_codigo_2(cfg_file: Path, subcomando_falso, capsys):
    """Si el módulo no existe: «pendiente: <dueño> (<ID>)» y código 2."""
    subcomando_falso("src.m_inexistente.modulo_que_no_existe")
    assert cli.main(["fantasma", "--config", str(cfg_file)]) == 2
    salida = capsys.readouterr().out
    assert "pendiente: Dueña (XX-1)\n" in salida


def test_modulo_sin_main_tambien_es_pendiente(cfg_file: Path, subcomando_falso, monkeypatch, capsys):
    monkeypatch.setattr(cli, "_importar_si_existe", lambda nombre: types.ModuleType("sin_main"))
    subcomando_falso("src.falso.sin_main")
    assert cli.main(["fantasma", "--config", str(cfg_file)]) == 2
    assert "pendiente: Dueña (XX-1)" in capsys.readouterr().out


def test_subcomando_conectado_se_despacha_a_main(cfg_file: Path, subcomando_falso, monkeypatch, config_impresa, capsys):
    """Un módulo con `main(cfg)` recibe la config final y su código de salida se respeta."""
    visto: dict = {}

    def main(cfg):
        visto["cfg"] = cfg
        return 7

    falso = types.ModuleType("falso")
    falso.main = main
    pedidos: list[str] = []

    def importar(nombre):
        pedidos.append(nombre)
        return falso

    monkeypatch.setattr(cli, "_importar_si_existe", importar)
    subcomando_falso("src.falso.modulo")
    assert cli.main(["fantasma", "--config", str(cfg_file), "--set", "base_seed=5"]) == 7
    assert pedidos == ["src.falso.modulo"]
    assert visto["cfg"] == config_impresa(capsys.readouterr().out)
    assert visto["cfg"]["base_seed"] == 5


def test_main_que_devuelve_none_es_exito(subcomando_falso, monkeypatch, cfg_file: Path):
    falso = types.ModuleType("falso")
    falso.main = lambda cfg: None
    monkeypatch.setattr(cli, "_importar_si_existe", lambda nombre: falso)
    subcomando_falso("src.falso.modulo")
    assert cli.main(["fantasma", "--config", str(cfg_file)]) == 0


def test_importar_si_existe_devuelve_none_solo_si_falta_ese_modulo():
    assert cli._importar_si_existe("src.m_inexistente.modulo") is None
    assert cli._importar_si_existe("src.comun.seeds").__name__ == "src.comun.seeds"


def test_fallo_interno_de_un_modulo_no_se_confunde_con_pendiente(tmp_path: Path, monkeypatch):
    """Si el módulo existe pero le falta otra dependencia, el error se propaga (no es «pendiente»)."""
    (tmp_path / "modulo_con_dependencia_rota.py").write_text("import otra_cosa_que_no_existe\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    with pytest.raises(ModuleNotFoundError, match="otra_cosa_que_no_existe"):
        cli._importar_si_existe("modulo_con_dependencia_rota")


def test_export_omite_lo_que_no_existe_con_salida_exacta(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_importar_si_existe", lambda nombre: None)
    assert cli.main(["export"]) == 0
    salida = capsys.readouterr().out
    esperado = "".join(f"export: {paquete}.exportar aún no existe; se omite\n" for paquete in cli.PAQUETES_MODULO)
    assert salida.startswith(esperado)
    assert salida[len(esperado):].startswith("Tiempo de ejecución:")


def test_export_llama_main_de_cada_modulo_y_se_detiene_en_un_error(monkeypatch, capsys):
    llamadas: list = []

    def importar(nombre):
        modulo = types.ModuleType(nombre)
        modulo.main = lambda cfg, nombre=nombre: llamadas.append((nombre, cfg)) or (1 if "m2" in nombre else 0)
        return modulo

    monkeypatch.setattr(cli, "_importar_si_existe", importar)
    assert cli.main(["export"]) == 1
    assert llamadas == [("src.m1_demanda.exportar", None), ("src.m2_conduccion.exportar", None)]
    assert "export: src.m1_demanda\nexport: src.m2_conduccion\n" in capsys.readouterr().out


def test_figures_sin_modulos_avisa_con_salida_exacta(monkeypatch, capsys):
    monkeypatch.setattr(cli.pkgutil, "iter_modules", lambda path: [])
    assert cli.main(["figures"]) == 0
    salida = capsys.readouterr().out
    assert salida.startswith("figures: aún no hay módulos src/viz/figs_*.py; nada que generar\n")


def test_run_py_ayuda_en_otro_proceso():
    res = subprocess.run([sys.executable, "run.py", "--help"], cwd=ROOT, capture_output=True,
                         encoding="utf-8", check=False)
    assert res.returncode == 0, res.stderr
    for nombre in SUBCOMANDOS_NUCLEO:
        assert nombre in res.stdout
