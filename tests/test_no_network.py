"""Los experimentos no usan internet (enunciado: «que la ejecución no dependa de conexión a internet ni de APIs
externas»; núcleo §7.1). Portada del Trabajo 2. Revisa que el código de `src/` no importe bibliotecas de red y que
los comandos de `run.py` corran con la red bloqueada.

`requests` es solo para los scripts de descarga (`scripts/`, fuera de `src/`): ningún experimento descarga nada.
Cada dueño agrega su subcomando a `COMANDOS` cuando lo conecte (con `--set` a un directorio temporal si escribe).
"""
import ast
import socket
import urllib.request
from pathlib import Path

import pytest

from src.comun import cli

RAIZ = Path(__file__).resolve().parents[1]
MODULOS_DE_RED = {"socket", "urllib", "http", "requests", "httpx", "aiohttp", "ftplib", "smtplib"}
# Comandos que no necesitan config (los de módulo se agregan al conectarse). Las figuras que guarde `figures` se
# redirigen a una carpeta temporal (fixture `figuras_a_temporal`); `export` aún no tiene exportadores: cuando los
# tenga, escribirá en `app/public/model/` y habrá que redirigirlo igual.
COMANDOS = [["export"], ["figures"]]


class RedBloqueada(RuntimeError):
    pass


@pytest.fixture
def sin_red(monkeypatch):
    """Cualquier intento de abrir una conexión (o de resolver un nombre) lanza RedBloqueada."""

    def _bloqueado(*args, **kwargs):
        raise RedBloqueada("intento de usar la red durante un experimento")

    monkeypatch.setattr(socket.socket, "connect", _bloqueado)
    monkeypatch.setattr(socket.socket, "connect_ex", _bloqueado)
    monkeypatch.setattr(socket, "create_connection", _bloqueado)
    monkeypatch.setattr(socket, "getaddrinfo", _bloqueado)


def test_el_bloqueo_si_detecta_un_acceso_a_la_red(sin_red):
    """Control de la propia prueba: si el bloqueo no funcionara, las demás pasarían sin probar nada."""
    with pytest.raises(RedBloqueada):
        urllib.request.urlopen("https://example.org", timeout=5)


@pytest.fixture
def figuras_a_temporal(monkeypatch, tmp_path):
    """`figures` escribe en carpetas versionadas (`blog/docs/figures/`, `results/figures/`): toda figura que se guarde
    durante la prueba va a `tmp_path` (misma ruta relativa a la raíz), así la prueba no pisa archivos del repositorio.
    Devuelve la lista de rutas pedidas, para comprobar que la redirección sí actuó."""
    from matplotlib.figure import Figure

    original = Figure.savefig
    pedidas: list[Path] = []

    def _savefig(self, fname, *args, **kwargs):
        if isinstance(fname, (str, Path)):
            ruta = Path(fname).resolve()
            pedidas.append(ruta)
            rel = ruta.relative_to(RAIZ) if ruta.is_relative_to(RAIZ) else Path(ruta.name)
            fname = tmp_path / rel
            fname.parent.mkdir(parents=True, exist_ok=True)
        return original(self, fname, *args, **kwargs)

    monkeypatch.setattr(Figure, "savefig", _savefig)
    return pedidas


@pytest.mark.parametrize("argv", COMANDOS, ids=lambda a: a[0])
def test_comandos_de_run_py_corren_sin_red(sin_red, figuras_a_temporal, monkeypatch, tmp_path, argv):
    """`notebooks` no entra: el kernel de Jupyter se comunica con el proceso por sockets locales (no es internet)."""
    monkeypatch.chdir(RAIZ)
    assert cli.main(argv) == 0
    for ruta in figuras_a_temporal:
        rel = ruta.relative_to(RAIZ) if ruta.is_relative_to(RAIZ) else Path(ruta.name)
        assert (tmp_path / rel).is_file(), f"{rel.as_posix()} no quedó en la carpeta temporal"


def test_figures_no_escribe_en_el_repositorio(sin_red, figuras_a_temporal, monkeypatch):
    """Regresión: `run.py figures` dentro de esta prueba regeneraba las PNG versionadas (llegaron a un PR ajeno)."""
    monkeypatch.chdir(RAIZ)
    versionadas = [p for c in ("blog/docs/figures", "results/figures") for p in (RAIZ / c).rglob("*.png")]
    antes = {p: p.stat().st_mtime_ns for p in versionadas}
    assert cli.main(["figures"]) == 0
    despues = {p: p.stat().st_mtime_ns for p in antes if p.exists()}
    assert despues == antes


def _modulos_importados(archivo: Path) -> set[str]:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    nombres = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.update(alias.name.split(".")[0] for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            nombres.add(nodo.module.split(".")[0])
    return nombres


@pytest.mark.parametrize("archivo", sorted((RAIZ / "src").rglob("*.py")) + [RAIZ / "run.py"],
                         ids=lambda p: p.relative_to(RAIZ).as_posix())
def test_el_codigo_de_los_experimentos_no_importa_bibliotecas_de_red(archivo):
    prohibidos = _modulos_importados(archivo) & MODULOS_DE_RED
    assert not prohibidos, f"{archivo.name} importa {prohibidos}: los experimentos no usan internet"
