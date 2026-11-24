"""Configuración común de pytest: hace importables el paquete src/ (desde la raíz) y scripts/."""

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
for ruta in (SCRIPTS, ROOT):
    if str(ruta) not in sys.path:
        sys.path.insert(0, str(ruta))


@pytest.fixture
def cfg() -> dict:
    """Configuración de ejemplo común a las pruebas de config, CLI y notebooks."""
    return {
        "runs": 30,
        "base_seed": 0,
        "w": [25],
        "methods": ["gdfijo", "pso"],
        "pso": {"w": 0.7298, "vecindario": {"tipo": "gbest", "k": 3}},
        "gd": {"armijo": False, "eta": 0.002},
        "costo": {"valor_hora": 25},
        "modelo": {"tipo": "gru", "capas": [32, 16]},
        "entrenamiento": {"lr": 1e-3},
    }


@pytest.fixture
def cfg_file(tmp_path: Path, cfg: dict) -> Path:
    ruta = tmp_path / "cfg.yaml"
    ruta.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return ruta


@pytest.fixture
def recibido(monkeypatch) -> dict:
    """Sustituye los manejadores del registro del CLI por uno falso que guarda la config recibida."""
    from src.comun import cli

    llamadas: dict = {}
    for nombre, sub in list(cli.SUBCOMANDOS.items()):

        def falso(cfg, nombre=nombre):
            llamadas[nombre] = cfg
            return 0

        monkeypatch.setitem(cli.SUBCOMANDOS, nombre, sub._replace(manejador=falso))
    return llamadas


@pytest.fixture
def config_impresa():
    """Devuelve una función que extrae la config YAML que el CLI imprime entre `---` y `...`."""

    def extraer(salida: str) -> dict:
        return yaml.safe_load(salida.split("---", 1)[1].split("...", 1)[0])

    return extraer
