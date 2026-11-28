"""Pruebas sin red de scripts/descargar_pesos_m2.py (JO-3, D2): destino y SHA-256 completo leídos de
configs/m2/particion.yaml, verificación del SHA-256 completo y del prefijo del nombre, archivo ya presente.

``requests.get`` se reemplaza por respuestas falsas (patrón de tests/test_descargar_m2.py): ninguna prueba abre una conexión.
"""
import hashlib
import importlib.util
import socket
import sys
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("descargar_pesos_m2", RAIZ / "scripts" / "descargar_pesos_m2.py")
dp = importlib.util.module_from_spec(_spec)
sys.modules["descargar_pesos_m2"] = dp
_spec.loader.exec_module(dp)

CONTENIDO = b"pesos de prueba" * 1000
SHA = hashlib.sha256(CONTENIDO).hexdigest()
URL = "https://ejemplo.invalido/modelos/resnet18-xxxx.pth"


class _Respuesta:
    def __init__(self, cuerpo: bytes):
        self._cuerpo = cuerpo

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def raise_for_status(self):
        pass

    def iter_content(self, bloque):
        for i in range(0, len(self._cuerpo), bloque):
            yield self._cuerpo[i:i + bloque]


@pytest.fixture(autouse=True)
def sin_red_ni_espera(monkeypatch):
    def _bloqueado(*a, **k):
        raise AssertionError("las pruebas no deben abrir conexiones de red")

    monkeypatch.setattr(socket, "socket", _bloqueado)
    monkeypatch.setattr(socket, "create_connection", _bloqueado)
    monkeypatch.setattr(dp.time, "sleep", lambda s: None)


def _falso_get(monkeypatch, cuerpo: bytes) -> list:
    pedidas = []

    def _get(url, **k):
        pedidas.append(url)
        return _Respuesta(cuerpo)

    monkeypatch.setattr(dp.requests, "get", _get)
    return pedidas


def _destino(tmp_path: Path, sha: str = SHA) -> Path:
    return tmp_path / "pesos" / f"resnet18-{sha[:8]}.pth"


def test_lee_destino_y_sha_de_la_config_real():
    cfg = yaml.safe_load((RAIZ / "configs" / "m2" / "particion.yaml").read_text(encoding="utf-8"))
    destino, sha = dp.leer_config(RAIZ / "configs" / "m2" / "particion.yaml")
    assert destino == RAIZ / cfg["caracteristicas"]["pesos"] and sha == cfg["caracteristicas"]["sha256_pesos"]
    assert sha.startswith(dp.prefijo_de(destino.name)) and len(sha) == 64


def test_descarga_correcta(tmp_path, monkeypatch):
    pedidas = _falso_get(monkeypatch, CONTENIDO)
    destino = _destino(tmp_path)
    assert dp.descargar(URL, destino, SHA, timeout=5, reintentos=1) == SHA
    assert pedidas == [URL] and destino.read_bytes() == CONTENIDO
    assert not destino.with_suffix(".pth.part").exists()


def test_archivo_ya_existente_no_se_descarga(tmp_path, monkeypatch):
    pedidas = _falso_get(monkeypatch, b"no deberia pedirse")
    destino = _destino(tmp_path)
    destino.parent.mkdir(parents=True)
    destino.write_bytes(CONTENIDO)
    assert dp.descargar(URL, destino, SHA, timeout=5, reintentos=1) == SHA
    assert pedidas == []


def test_sha_que_no_coincide_falla_y_no_deja_el_destino(tmp_path, monkeypatch):
    _falso_get(monkeypatch, CONTENIDO + b"alterado")
    destino = _destino(tmp_path)
    with pytest.raises(SystemExit, match="SHA-256 NO COINCIDE"):
        dp.descargar(URL, destino, SHA, timeout=5, reintentos=1)
    assert not destino.exists()


def test_mismo_prefijo_pero_sha_completo_distinto_falla(tmp_path, monkeypatch):
    """Verificar solo el prefijo de 8 hex no basta: se exige el SHA-256 completo de la config."""
    _falso_get(monkeypatch, CONTENIDO)
    falso = SHA[:8] + ("0" if SHA[8] != "0" else "1") + SHA[9:]
    with pytest.raises(SystemExit, match="SHA-256 NO COINCIDE"):
        dp.descargar(URL, _destino(tmp_path), falso, timeout=5, reintentos=1)


def test_existente_con_sha_distinto_se_vuelve_a_bajar(tmp_path, monkeypatch):
    pedidas = _falso_get(monkeypatch, CONTENIDO)
    destino = _destino(tmp_path)
    destino.parent.mkdir(parents=True)
    destino.write_bytes(b"viejo")
    assert dp.descargar(URL, destino, SHA, timeout=5, reintentos=1) == SHA and pedidas == [URL]


def test_config_incoherente_nombre_y_sha(tmp_path, monkeypatch):
    _falso_get(monkeypatch, CONTENIDO)
    with pytest.raises(ValueError, match="prefijo"):
        dp.descargar(URL, tmp_path / "resnet18-00000000.pth", SHA, timeout=5, reintentos=1)


def test_reintentos_invalidos(tmp_path):
    with pytest.raises(ValueError, match="reintentos"):
        dp.descargar(URL, _destino(tmp_path), SHA, timeout=5, reintentos=0)


def test_un_solo_origen_de_sha256():
    """B1: el script usa la misma función que src (como scripts/descargar_m1.py)."""
    from src.m2_conduccion import datos
    assert dp.sha256_archivo is datos.sha256_archivo


def test_url_de_torchvision_distinta_del_destino_falla(tmp_path, monkeypatch):
    _falso_get(monkeypatch, CONTENIDO)
    monkeypatch.setattr(dp, "url_pesos", lambda: "https://ejemplo.invalido/modelos/resnet18-ffffffff.pth")
    monkeypatch.setattr(dp, "leer_config", lambda ruta=None: (_destino(tmp_path), SHA))
    with pytest.raises(SystemExit, match="no corresponde"):
        dp.main([])
    assert not _destino(tmp_path).exists()
