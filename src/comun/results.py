"""Escritura y lectura de resultados en JSON (núcleo §5.9; portado del Trabajo 2).

- ``to_jsonable``: convierte tipos numpy, tuplas y ``Path`` a tipos nativos de JSON.
- ``save_json``: UTF-8, ``indent=2``, ``ensure_ascii=False``, sin NaN/inf y escritura atómica
  (archivo temporal en la misma carpeta + ``os.replace``).
"""

from __future__ import annotations

import contextlib
import json
import math
import os
import tempfile
from pathlib import Path, PurePath
from typing import Any

import numpy as np

_CODIFICACION = "utf-8"
_INDENTACION = 2
_SEPARADORES_COMPACTOS = (",", ":")  # save_json(..., sangria=None)
_PERMISOS_ARCHIVO = 0o644


def to_jsonable(obj: Any) -> Any:
    """Convierte ``obj`` recursivamente a tipos nativos de JSON.

    numpy escalar → int/float/bool/str; ``np.ndarray`` → listas anidadas; tupla → lista;
    ``Path`` → str con separadores ``/``. Las claves de los diccionarios deben ser texto
    (``str`` o ``numpy.str_``); cualquier otra clave produce ``TypeError`` con su ruta.
    Los valores no finitos se conservan como ``float`` (``save_json`` los rechaza).
    Un tipo no soportado produce ``TypeError`` con su ruta.
    """
    return _convertir(obj, "$")


def _convertir(obj: Any, ruta: str) -> Any:
    """Convierte ``obj`` (ubicado en ``ruta``, p. ej. ``$.history[1]``) a tipos nativos de JSON."""
    # np.generic va primero: np.float64 es subclase de float y np.str_ de str, y deben salir nativos.
    if isinstance(obj, np.generic):
        return _convertir(obj.item(), ruta)
    if isinstance(obj, np.ndarray):
        return _convertir(obj.tolist(), ruta)
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, PurePath):
        return obj.as_posix()
    if isinstance(obj, dict):
        convertido = {}
        for k, v in obj.items():
            if not isinstance(k, str):  # numpy.str_ es subclase de str
                raise TypeError(
                    f"Clave de diccionario no textual en {ruta}: {k!r} ({type(k).__name__}); "
                    "las claves de los resultados deben ser str "
                )
            clave = str(k)
            convertido[clave] = _convertir(v, f"{ruta}.{clave}")
        return convertido
    if isinstance(obj, (list, tuple)):
        return [_convertir(v, f"{ruta}[{i}]") for i, v in enumerate(obj)]
    raise TypeError(f"Tipo no convertible a JSON en {ruta}: {type(obj).__name__} ({obj!r})")


def _ruta_no_finita(obj: Any, ruta: str = "$") -> str | None:
    """Devuelve la ruta (p. ej. ``$.history[2].f_best``) del primer valor NaN/inf, o None."""
    if isinstance(obj, float) and not math.isfinite(obj):
        return ruta
    if isinstance(obj, dict):
        for k, v in obj.items():
            encontrado = _ruta_no_finita(v, f"{ruta}.{k}")
            if encontrado is not None:
                return encontrado
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            encontrado = _ruta_no_finita(v, f"{ruta}[{i}]")
            if encontrado is not None:
                return encontrado
    return None


def save_json(path: str | os.PathLike, obj: Any, sangria: int | None = _INDENTACION) -> Path:
    """Escribe ``obj`` en ``path`` de forma atómica y devuelve la ruta escrita.

    Crea las carpetas que falten. Un NaN o inf produce ``ValueError`` indicando dónde está,
    sin crear ni modificar el archivo destino. ``sangria=None`` escribe JSON compacto en una
    sola línea (sin espacios tras ``,`` y ``:``).
    """
    destino = Path(path)
    datos = to_jsonable(obj)
    no_finito = _ruta_no_finita(datos)
    if no_finito is not None:
        raise ValueError(f"Valor no finito (NaN o inf) en {no_finito}: JSON no admite NaN/inf; no se escribió {destino}")
    separadores = _SEPARADORES_COMPACTOS if sangria is None else None
    texto = json.dumps(datos, indent=sangria, separators=separadores, ensure_ascii=False, allow_nan=False) + "\n"
    _escribir_atomico(destino, texto)
    return destino


def _escribir_atomico(destino: Path, texto: str) -> None:
    """Escribe ``texto`` en un temporal de la misma carpeta y lo mueve a ``destino`` con ``os.replace``.

    Si algo falla, borra el temporal y deja intacto el archivo anterior (si existía).
    """
    destino.parent.mkdir(parents=True, exist_ok=True)
    fd, temporal = tempfile.mkstemp(prefix=f".{destino.name}.", suffix=".tmp", dir=destino.parent)
    try:
        with os.fdopen(fd, "w", encoding=_CODIFICACION, newline="\n") as f:
            f.write(texto)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporal, destino)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.remove(temporal)
        raise
    # mkstemp crea el temporal con 0o600 y os.replace conserva esos permisos, tanto en un archivo nuevo
    # como al sobrescribir uno existente; el resultado debe quedar legible (en Windows es inocuo).
    os.chmod(destino, _PERMISOS_ARCHIVO)


def _rechazar_constante(nombre: str) -> None:
    raise ValueError(f"JSON inválido: contiene {nombre} (NaN/Infinity no son JSON estándar)")


def load_json(path: str | os.PathLike) -> Any:
    """Lee un JSON UTF-8. Rechaza ``NaN``/``Infinity`` literales con ``ValueError``."""
    with open(path, encoding=_CODIFICACION) as f:
        return json.load(f, parse_constant=_rechazar_constante)
