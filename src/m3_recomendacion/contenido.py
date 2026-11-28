"""M3 — variables de contenido de la red de dos torres (JJ-5; D15 de docs/spec/partes/juanjose.md §3.2).

La red necesita, además del historial de train que recibe en ``ajustar``, variables de contenido del usuario y del destino.
Este módulo es el ÚNICO que las lee, y solo de dos archivos: ``destinos.parquet`` y ``usuarios.parquet`` (rutas de
``cfg["datos"]``). Son atributos de la fuente (Kaggle), fijos y conocidos antes de cualquier recomendación: no se calculan con
el historial de uso, así que no pueden filtrar validación ni prueba (D9; lo vigila ``tests/test_fuga_m3.py``).

Codificación one-hot por opción, orden fijo y documentado (la exportación a la app de JJ-7 lo necesita, núcleo §5.8):
  destino → ``tipo`` (5 categorías, en orden alfabético): columnas «tipo=<categoría>». No entran ``lugar``, ``estado`` ni
            ``mejor_epoca`` (en el catálogo son función del mismo lugar: repetirían la información de ``tipo``), ni el
            atributo numérico de la fuente sobre la fama del destino (D15: ρ = −0,011 con el uso en H-M3-3).
  usuario → las 5 preferencias ``pref_*`` (booleanas: 1 si el usuario la marcó), en el orden de ``COLUMNAS_PREFERENCIAS``;
            con ``usar_demografia``, además ``genero``, ``n_adultos`` y ``n_ninos`` one-hot por valor (orden ascendente),
            columnas «<variable>=<valor>».
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

COLUMNAS_PREFERENCIAS = ("pref_adventure", "pref_beaches", "pref_city", "pref_historical", "pref_nature")
COLUMNAS_DEMOGRAFIA = ("genero", "n_adultos", "n_ninos")
COLUMNA_TIPO = "tipo"


@dataclass(frozen=True)
class Contenido:
    """Matriz de contenido: fila r ↔ ``ids[r]``; columnas en el orden de ``columnas``; ``X`` es float32 con 0/1."""

    ids: np.ndarray
    X: np.ndarray
    columnas: tuple[str, ...]

    def filas(self, ids: Sequence[int]) -> np.ndarray:
        """Fila de cada id pedido; error claro si alguno no está en la tabla. Sin ids pedidos: arreglo vacío (0,)."""
        pedidos = np.asarray(ids, dtype="int64").reshape(-1)
        if len(pedidos) == 0:
            return np.empty(0, dtype="int64")
        if len(self.ids) == 0:
            raise ValueError(f"la tabla de contenido está vacía; se pidieron los ids {pedidos[:10].tolist()}")
        orden = np.argsort(self.ids, kind="stable")
        pos = np.minimum(np.searchsorted(self.ids, pedidos, sorter=orden), len(self.ids) - 1)
        filas = orden[pos]
        faltan = pedidos[self.ids[filas] != pedidos]
        if len(faltan):
            raise ValueError(f"ids que no están en la tabla de contenido: {faltan[:10].tolist()}")
        return filas


def _ids_unicos(df: pd.DataFrame, columna: str) -> np.ndarray:
    if columna not in df.columns:
        raise ValueError(f"falta la columna {columna}; hay {list(df.columns)}")
    ids = df[columna].to_numpy(dtype="int64")
    if len(np.unique(ids)) != len(ids):
        raise ValueError(f"{columna} repetidos en la tabla de contenido")
    return ids


def _one_hot(valores: pd.Series, nombre: str) -> tuple[np.ndarray, list[str]]:
    """One-hot por valor, categorías en orden ascendente; error claro si hay faltantes."""
    if valores.isna().any():
        raise ValueError(f"la columna {nombre} tiene valores faltantes")
    categorias = sorted(valores.unique().tolist())
    X = np.stack([(valores == c).to_numpy() for c in categorias], axis=1).astype(np.float32)
    return X, [f"{nombre}={c}" for c in categorias]


def contenido_destinos(destinos: pd.DataFrame) -> Contenido:
    """x_i = one-hot de ``tipo`` (D15); filas en el orden de la tabla."""
    ids = _ids_unicos(destinos, "destino_id")
    if COLUMNA_TIPO not in destinos.columns:
        raise ValueError(f"falta la columna {COLUMNA_TIPO} en destinos; hay {list(destinos.columns)}")
    X, columnas = _one_hot(destinos[COLUMNA_TIPO], COLUMNA_TIPO)
    return Contenido(ids=ids, X=X, columnas=tuple(columnas))


def contenido_usuarios(usuarios: pd.DataFrame, usar_demografia: bool = False) -> Contenido:
    """x_u = las 5 preferencias (1 si el usuario la marcó) y, con ``usar_demografia``, la demografía one-hot por valor."""
    ids = _ids_unicos(usuarios, "usuario_id")
    faltan = [c for c in COLUMNAS_PREFERENCIAS if c not in usuarios.columns]
    if faltan:
        raise ValueError(f"faltan las columnas de preferencias {faltan} en usuarios")
    pref = usuarios[list(COLUMNAS_PREFERENCIAS)]
    if pref.isna().any().any():
        raise ValueError("las preferencias tienen valores faltantes")
    bloques, columnas = [pref.to_numpy(dtype=bool).astype(np.float32)], list(COLUMNAS_PREFERENCIAS)
    if usar_demografia:
        for c in COLUMNAS_DEMOGRAFIA:
            if c not in usuarios.columns:
                raise ValueError(f"falta la columna {c} en usuarios (modelo.usar_demografia = true)")
            X, nombres = _one_hot(usuarios[c], c)
            bloques.append(X)
            columnas += nombres
    return Contenido(ids=ids, X=np.concatenate(bloques, axis=1), columnas=tuple(columnas))


def cargar_contenido(cfg: dict, usar_demografia: bool) -> tuple[Contenido, Contenido]:
    """(usuarios, destinos) leídos SOLO de ``datos.carpeta / datos.usuarios`` y ``datos.carpeta / datos.destinos``."""
    d = cfg["datos"]
    carpeta = Path(d["carpeta"])
    usuarios = pd.read_parquet(carpeta / d["usuarios"])
    destinos = pd.read_parquet(carpeta / d["destinos"])
    return contenido_usuarios(usuarios, usar_demografia=usar_demografia), contenido_destinos(destinos)
