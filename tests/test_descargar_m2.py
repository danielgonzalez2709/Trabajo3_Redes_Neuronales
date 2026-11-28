"""Pruebas sin red de scripts/descargar_m2.py (consulta a la API, verificación de tamaño y SHA-256, archivo ya presente).

``requests.get`` se reemplaza por respuestas falsas: ninguna prueba abre una conexión.
"""
import hashlib
import importlib.util
import socket
import sys
from pathlib import Path

import pytest
import requests

RAIZ = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("descargar_m2", RAIZ / "scripts" / "descargar_m2.py")
dm = importlib.util.module_from_spec(_spec)
sys.modules["descargar_m2"] = dm
_spec.loader.exec_module(dm)

CONTENIDO = b"contenido de prueba del zip" * 100
SHA = hashlib.sha256(CONTENIDO).hexdigest()


class _Respuesta:
    def __init__(self, cuerpo: bytes = b"", json_=None):
        self._cuerpo, self._json = cuerpo, json_

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def raise_for_status(self):
        pass

    def json(self):
        return self._json

    def iter_content(self, bloque):
        for i in range(0, len(self._cuerpo), bloque):
            yield self._cuerpo[i:i + bloque]


def _archivo_api(nombre=dm.NOMBRE_ZIP, tamano=len(CONTENIDO), sha=SHA) -> dict:
    return {"filename": nombre, "content_details": {"size": tamano, "sha256_hash": sha.upper(),
                                                      "download_url": "https://ejemplo.invalido/zip"}}


@pytest.fixture(autouse=True)
def sin_red_ni_espera(monkeypatch):
    def _bloqueado(*a, **k):
        raise AssertionError("las pruebas no deben abrir conexiones de red")

    monkeypatch.setattr(socket, "socket", _bloqueado)
    monkeypatch.setattr(socket, "create_connection", _bloqueado)
    monkeypatch.setattr(dm.time, "sleep", lambda s: None)


def _falso_get(monkeypatch, respuestas: dict):
    """Instala un ``requests.get`` falso; ``respuestas`` mapea URL -> _Respuesta. Devuelve la lista de URL pedidas."""
    pedidas = []

    def _get(url, **k):
        pedidas.append(url)
        return respuestas[url]

    monkeypatch.setattr(dm.requests, "get", _get)
    return pedidas


def _meta(**cambios) -> dict:
    return {"nombre": dm.NOMBRE_ZIP, "tamano": len(CONTENIDO), "sha256": SHA, "url": "https://ejemplo.invalido/zip", **cambios}


# --------------------------------------------------------------------------- consulta a la API
def test_consultar_archivo_devuelve_los_metadatos(monkeypatch):
    _falso_get(monkeypatch, {dm.URL_API: _Respuesta(json_=[_archivo_api(), _archivo_api(nombre="otro.txt")])})
    assert dm.consultar_archivo(5, 1) == _meta()           # el SHA-256 de la API se normaliza a minúsculas


@pytest.mark.parametrize("lista", [[], [_archivo_api(nombre="otro.txt")], [_archivo_api(), _archivo_api()]])
def test_api_con_cero_o_dos_archivos_falla(monkeypatch, lista):
    pedidas = _falso_get(monkeypatch, {dm.URL_API: _Respuesta(json_=lista)})
    with pytest.raises(RuntimeError, match="exactamente un archivo"):
        dm.consultar_archivo(5, 3)
    assert len(pedidas) == 1                                # un error de contenido no se reintenta


def test_consultar_con_reintentos_menores_que_uno_es_error_explicito():
    for funcion in (lambda: dm.consultar_archivo(5, 0), lambda: dm.descargar(_meta(), Path("x"), 5, 0)):
        with pytest.raises(ValueError, match="reintentos"):
            funcion()


def test_consultar_reintenta_y_relanza_el_ultimo_error_de_red(monkeypatch):
    llamadas = []

    def _get(url, **k):
        llamadas.append(url)
        raise requests.ConnectionError("sin red")

    monkeypatch.setattr(dm.requests, "get", _get)
    with pytest.raises(requests.ConnectionError):
        dm.consultar_archivo(5, 3)
    assert len(llamadas) == 3


# --------------------------------------------------------------------------- descarga y verificación
def test_descarga_correcta_deja_el_archivo_y_no_el_temporal(tmp_path, monkeypatch):
    _falso_get(monkeypatch, {"https://ejemplo.invalido/zip": _Respuesta(CONTENIDO)})
    destino = dm.descargar(_meta(), tmp_path / "raw" / dm.NOMBRE_ZIP, 5, 1)
    assert destino.read_bytes() == CONTENIDO
    assert not list(tmp_path.rglob("*.part"))


def test_sha256_incorrecto_falla_y_no_deja_el_destino(tmp_path, monkeypatch):
    _falso_get(monkeypatch, {"https://ejemplo.invalido/zip": _Respuesta(CONTENIDO)})
    destino = tmp_path / dm.NOMBRE_ZIP
    with pytest.raises(SystemExit, match="SHA-256 NO COINCIDE"):
        dm.descargar(_meta(sha256="0" * 64), destino, 5, 1)
    assert not destino.exists()                             # nada a medias bajo el nombre final
    assert destino.with_suffix(".zip.part").exists()        # se deja el temporal para inspección


def test_tamano_distinto_falla_y_no_deja_el_destino(tmp_path, monkeypatch):
    _falso_get(monkeypatch, {"https://ejemplo.invalido/zip": _Respuesta(CONTENIDO)})
    destino = tmp_path / dm.NOMBRE_ZIP
    with pytest.raises(SystemExit, match="TAMAÑO NO COINCIDE"):
        dm.descargar(_meta(tamano=len(CONTENIDO) + 1), destino, 5, 1)
    assert not destino.exists()


def test_archivo_presente_con_el_sha_correcto_no_descarga(tmp_path, monkeypatch):
    destino = tmp_path / dm.NOMBRE_ZIP
    destino.write_bytes(CONTENIDO)
    pedidas = _falso_get(monkeypatch, {})
    assert dm.descargar(_meta(), destino, 5, 1) == destino
    assert pedidas == []                                    # ninguna petición
    assert destino.read_bytes() == CONTENIDO


def test_archivo_presente_con_otro_sha_se_vuelve_a_descargar(tmp_path, monkeypatch):
    destino = tmp_path / dm.NOMBRE_ZIP
    destino.write_bytes(b"x" * len(CONTENIDO))              # mismo tamaño, otro contenido
    pedidas = _falso_get(monkeypatch, {"https://ejemplo.invalido/zip": _Respuesta(CONTENIDO)})
    dm.descargar(_meta(), destino, 5, 1)
    assert pedidas == ["https://ejemplo.invalido/zip"]
    assert destino.read_bytes() == CONTENIDO


def test_la_copia_de_sha256_coincide_con_la_del_modulo_de_datos(tmp_path):
    from src.m2_conduccion.datos import sha256_archivo
    f = tmp_path / "a.bin"
    f.write_bytes(CONTENIDO)
    assert dm.sha256(f) == sha256_archivo(f) == SHA
