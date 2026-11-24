"""Interfaz de línea de comandos de `run.py` (núcleo §4.1). Portada del Trabajo 2.

    python run.py m1-datos --config configs/m1/datos.yaml
    python run.py m1       --config configs/m1/demo.yaml [--set clave.subclave=valor ...]
    python run.py export | figures | notebooks            (sin --config)

Cada subcomando de módulo despacha, de forma perezosa (`run.py --help` no carga torch ni pandas), a una función
`main(cfg: dict) -> int | None` de un módulo de `src/`. Si el módulo o la función `main` todavía no existen, el comando
imprime «pendiente: <dueño> (<ID de tarea>)» y sale con código 2. Tabla subcomando → archivo:función (núcleo §4):

    m1-datos       src/m1_demanda/datos.py:main         Daniel (DA-3)
    m1-eda         src/m1_demanda/eda.py:main           Camila (CA-4)
    m1             src/m1_demanda/experimento.py:main   Andrés (AN-5)
    m1-hpo         src/m1_demanda/hpo.py:main           Andrés (AN-4)
    m1-operacion   src/m1_demanda/operacion.py:main     Camila (CA-3)
    m2-datos       src/m2_conduccion/datos.py:main      José (JO-1)
    m2-eda         src/m2_conduccion/eda.py:main        José (JO-2)
    m2             src/m2_conduccion/experimento.py:main  José (JO-6)
    m2-hpo         src/m2_conduccion/hpo.py:main        José (JO-5)
    m2-alertas     src/m2_conduccion/alertas.py:main    José (JO-8)
    m3-datos       src/m3_recomendacion/datos.py:main   Juan José (JJ-1)
    m3-eda         src/m3_recomendacion/eda.py:main     Juan José (JJ-2)
    m3             src/m3_recomendacion/experimento.py:main  Juan José (JJ-5)
    m3-hpo         src/m3_recomendacion/hpo.py:main     Juan José (JJ-5)

Subcomandos que recorren lo que exista de cada módulo (lo que falta se omite, no es un error):
    export     `exportar.py:main(None)` de cada `src/m*_*/` (no recibe --config; núcleo §4.1)
    figures    `generar()` de cada módulo `src/viz/figs_*.py` (devuelve las rutas escritas)
    notebooks  `src/comun/notebooks.py:manejador` (notebooks/NN_*.py → .ipynb ejecutado)
"""

from __future__ import annotations

import argparse
import importlib
import pkgutil
import sys
import time
from collections.abc import Callable
from typing import NamedTuple

import yaml

from src.comun.config import apply_overrides, load_config

Manejador = Callable[[dict | None], int]

CABECERA_CONFIG = "Configuración final resuelta:"
DESTINO_PARSER = "parser_subcomando"
# Tildes y "ñ" intactas aunque se redirija la salida (en Windows sería cp1252).
CODIFICACION_SALIDA = "utf-8"
CODIGO_PENDIENTE = 2
PAQUETES_MODULO = ("src.m1_demanda", "src.m2_conduccion", "src.m3_recomendacion")
AYUDA_SET = (
    "Sobrescribe un parámetro existente; el valor se interpreta como YAML (repetible).\n"
    "Ej.: --set entrenamiento.lr=5e-4 --set modelo.capas=[64, 32]\n"
    'En PowerShell, los valores con espacios van entre comillas: --set "modelo.capas=[64, 32]"'
)


class Subcomando(NamedTuple):
    ayuda: str
    usa_config: bool  # True: --config obligatorio y --set repetible
    manejador: Manejador


def _importar_si_existe(modulo: str):
    """Importa `modulo`; devuelve None solo si ESE módulo no existe (un fallo interno se propaga)."""
    try:
        return importlib.import_module(modulo)
    except ModuleNotFoundError as exc:
        if exc.name is not None and (modulo == exc.name or modulo.startswith(exc.name + ".")):
            return None
        raise


def _despachar(modulo: str, dueno: str, tarea: str) -> Manejador:
    """Manejador perezoso hacia `modulo.main(cfg)`; si no existe, «pendiente» y código 2."""

    def manejador(cfg: dict | None) -> int:
        mod = _importar_si_existe(modulo)
        funcion = getattr(mod, "main", None) if mod is not None else None
        if funcion is None:
            print(f"pendiente: {dueno} ({tarea})")
            return CODIGO_PENDIENTE
        return int(funcion(cfg) or 0)

    return manejador


def _modulo(nombre: str, ayuda: str, modulo: str, dueno: str, tarea: str) -> tuple[str, Subcomando]:
    return nombre, Subcomando(ayuda, True, _despachar(modulo, dueno, tarea))


def _export(cfg: dict | None) -> int:
    """Recorre `exportar.py` de cada módulo que lo tenga y llama `main(None)`."""
    for paquete in PAQUETES_MODULO:
        mod = _importar_si_existe(f"{paquete}.exportar")
        funcion = getattr(mod, "main", None) if mod is not None else None
        if funcion is None:
            print(f"export: {paquete}.exportar aún no existe; se omite")
            continue
        print(f"export: {paquete}")
        codigo = int(funcion(None) or 0)
        if codigo != 0:
            return codigo
    return 0


def _figures(cfg: dict | None) -> int:
    """Recorre los módulos `src/viz/figs_*.py` y llama `generar()`, que devuelve las rutas escritas."""
    import src.viz

    nombres = sorted(m.name for m in pkgutil.iter_modules(src.viz.__path__) if m.name.startswith("figs_"))
    if not nombres:
        print("figures: aún no hay módulos src/viz/figs_*.py; nada que generar")
    for nombre in nombres:
        for ruta in importlib.import_module(f"src.viz.{nombre}").generar():
            print(ruta.as_posix())
    return 0


def _notebooks(cfg: dict | None) -> int:
    """notebooks/NN_*.py → .ipynb ejecutado (núcleo §5.10)."""
    from src.comun.notebooks import manejador

    return manejador(cfg)


# Registro único nombre -> (ayuda, usa_config, manejador), en el orden de núcleo §4.1.
SUBCOMANDOS: dict[str, Subcomando] = dict(
    [
        _modulo("m1-datos", "M1: crudo → data/processed/m1", "src.m1_demanda.datos", "Daniel", "DA-3"),
        _modulo("m1-eda", "M1: plantilla común de análisis descriptivo", "src.m1_demanda.eda", "Camila", "CA-4"),
        _modulo("m1", "M1: referencias y redes (demo o completo según la config)",
                "src.m1_demanda.experimento", "Andrés", "AN-5"),
        _modulo("m1-hpo", "M1: búsqueda Optuna de las redes", "src.m1_demanda.hpo", "Andrés", "AN-4"),
        _modulo("m1-operacion", "M1: dimensionamiento de la operación", "src.m1_demanda.operacion", "Camila", "CA-3"),
        _modulo("m2-datos", "M2: crudo → data/processed/m2", "src.m2_conduccion.datos", "José", "JO-1"),
        _modulo("m2-eda", "M2: plantilla común de análisis descriptivo", "src.m2_conduccion.eda", "José", "JO-2"),
        _modulo("m2", "M2: referencias y redes (demo o completo según la config)",
                "src.m2_conduccion.experimento", "José", "JO-6"),
        _modulo("m2-hpo", "M2: búsqueda Optuna de las redes", "src.m2_conduccion.hpo", "José", "JO-5"),
        _modulo("m2-alertas", "M2: política de alertas", "src.m2_conduccion.alertas", "José", "JO-8"),
        _modulo("m3-datos", "M3: datos → data/processed/m3", "src.m3_recomendacion.datos", "Juan José", "JJ-1"),
        _modulo("m3-eda", "M3: plantilla común de análisis descriptivo",
                "src.m3_recomendacion.eda", "Juan José", "JJ-2"),
        _modulo("m3", "M3: referencias y red (demo o completo según la config)",
                "src.m3_recomendacion.experimento", "Juan José", "JJ-5"),
        _modulo("m3-hpo", "M3: búsqueda Optuna de la red", "src.m3_recomendacion.hpo", "Juan José", "JJ-5"),
        ("export", Subcomando("Modelos → app/public/model/{m1,m2,m3}/ + casos de paridad", False, _export)),
        ("figures", Subcomando("Regenera todas las figuras desde results/", False, _figures)),
        ("notebooks", Subcomando("Convierte y ejecuta los notebooks en modo demo", False, _notebooks)),
    ]
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="Punto de entrada único del Trabajo 3 (núcleo §4.1).",
    )
    sub = parser.add_subparsers(dest="comando", required=True)
    for nombre, subcomando in SUBCOMANDOS.items():
        p = sub.add_parser(
            nombre,
            help=subcomando.ayuda,
            description=subcomando.ayuda,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        if not subcomando.usa_config:
            continue
        # Se guarda el parser del subcomando en el Namespace para que main() emita los errores de
        # configuración con el uso de ESTE subcomando (y no el del parser raíz).
        p.set_defaults(**{DESTINO_PARSER: p})
        p.add_argument("--config", required=True, help="Ruta al archivo YAML de configuración")
        p.add_argument(
            "--set",
            dest="overrides",
            action="append",
            default=[],
            metavar="CLAVE.SUBCLAVE=VALOR",
            help=AYUDA_SET,
        )
    return parser


def _imprimir_config(cfg: dict) -> None:
    print(CABECERA_CONFIG)
    texto = yaml.safe_dump(
        cfg, sort_keys=False, allow_unicode=True, explicit_start=True, explicit_end=True
    )
    print(texto, end="")


def _forzar_utf8() -> None:
    """Al redirigir en Windows Python usa la codificación local (cp1252); se fuerza UTF-8."""
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding=CODIFICACION_SALIDA)


def main(argv: list[str] | None = None) -> int:
    _forzar_utf8()
    inicio = time.perf_counter()
    args = build_parser().parse_args(argv)
    subcomando = SUBCOMANDOS[args.comando]
    cfg: dict | None = None
    if subcomando.usa_config:
        try:
            cfg = apply_overrides(load_config(args.config), args.overrides)
        except (FileNotFoundError, ValueError) as exc:
            # El Namespace trae el parser del subcomando: su .error() imprime "usage: run.py m1 ..."
            # y sale con código 2.
            getattr(args, DESTINO_PARSER).error(str(exc))
        _imprimir_config(cfg)
    codigo = subcomando.manejador(cfg)
    print(f"Tiempo de ejecución: {time.perf_counter() - inicio:.1f} s")
    return codigo
