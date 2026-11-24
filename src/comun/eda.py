"""Plantilla común de análisis descriptivo (núcleo §5.12).

Los tres módulos usan los mismos títulos de sección y los mismos contratos de salida
(``results/data/<m>/eda/ficha.json`` y ``hipotesis.json``). Aquí solo hay lo común: validación y
escritura de ambos JSON y la tabla de calidad; cada módulo agrega lo específico de su sección 4.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import pandas as pd

from src.comun.results import load_json, save_json

SECCIONES_PLANTILLA = (
    "Ficha del conjunto",
    "Diccionario y calidad",
    "Variable objetivo",
    "Estructura y heterogeneidad",
    "Hipótesis explícitas",
    "Implicaciones para el modelado",
    "Veredicto de las hipótesis",
)

CLAVES_FICHA = (
    "fuente",
    "cita",
    "url",
    "fecha_descarga",
    "sha256",
    "unidad_de_observacion",
    "n_registros",
    "n_variables",
    "periodo",
    "conteos",
)

CLAVES_HIPOTESIS = (
    "id",
    "enunciado",
    "justificacion",
    "evidencia_esperada",
    "figura_o_tabla",
    "resultado",
    "veredicto",
    "evidencia",
)
VEREDICTOS = ("pendiente", "confirmada", "refutada", "no concluyente")
PATRON_ID_HIPOTESIS = re.compile(r"^H-M[123]-[0-9]+$")
COLUMNAS_CALIDAD = ["columna", "tipo", "faltantes", "pct_faltantes", "unicos", "ejemplo"]


def validar_ficha(datos: Any) -> None:
    """Error claro (``ValueError``) si ``datos`` no es un diccionario o le falta una clave de ``ficha.json``."""
    if not isinstance(datos, dict):
        raise ValueError(f"ficha.json debe ser un diccionario; se recibió {type(datos).__name__}")
    faltan = [c for c in CLAVES_FICHA if c not in datos]
    if faltan:
        raise ValueError(f"ficha.json: faltan las claves obligatorias {faltan} (§5.12)")


def escribir_ficha(ruta: str | os.PathLike, datos: dict) -> Path:
    """Valida las claves obligatorias de la ficha y la escribe como JSON UTF-8 (atómico)."""
    validar_ficha(datos)
    return save_json(ruta, datos)


def tabla_calidad(df: pd.DataFrame) -> pd.DataFrame:
    """Una fila por columna: tipo, faltantes, % faltantes, valores únicos (sin contar faltantes) y un ejemplo (texto)."""
    n = len(df)
    filas = []
    for col in df.columns:
        serie = df[col]
        faltantes = int(serie.isna().sum())
        no_nulos = serie.dropna()
        filas.append(
            {
                "columna": str(col),
                "tipo": str(serie.dtype),
                "faltantes": faltantes,
                "pct_faltantes": 100.0 * faltantes / n if n else 0.0,
                "unicos": int(no_nulos.nunique()),
                "ejemplo": "" if no_nulos.empty else str(no_nulos.iloc[0]),
            }
        )
    return pd.DataFrame(filas, columns=COLUMNAS_CALIDAD)


def validar_hipotesis(hipotesis: Any) -> None:
    """Valida ``hipotesis.json``: lista de dicts con todas las claves, id ``H-M[123]-<n>`` único y veredicto válido."""
    if not isinstance(hipotesis, list):
        raise ValueError(f"hipotesis.json debe ser una lista; se recibió {type(hipotesis).__name__}")
    vistos: set[str] = set()
    for i, h in enumerate(hipotesis):
        if not isinstance(h, dict):
            raise ValueError(f"hipotesis[{i}] debe ser un diccionario; se recibió {type(h).__name__}")
        faltan = [c for c in CLAVES_HIPOTESIS if c not in h]
        if faltan:
            raise ValueError(f"hipotesis[{i}]: faltan las claves {faltan} (§5.12)")
        id_ = h["id"]
        if not isinstance(id_, str) or not PATRON_ID_HIPOTESIS.match(id_):
            raise ValueError(f"hipotesis[{i}]: id {id_!r} no cumple el patrón H-M[123]-<n> (p. ej. H-M1-1)")
        if id_ in vistos:
            raise ValueError(f"hipotesis[{i}]: id repetido {id_!r}")
        vistos.add(id_)
        if h["veredicto"] not in VEREDICTOS:
            raise ValueError(f"hipotesis[{i}] ({id_}): veredicto {h['veredicto']!r} inválido; debe ser uno de {list(VEREDICTOS)}")


def escribir_hipotesis(ruta: str | os.PathLike, hipotesis: list[dict]) -> Path:
    """Valida el esquema y escribe ``hipotesis.json`` (UTF-8, atómico)."""
    validar_hipotesis(hipotesis)
    return save_json(ruta, hipotesis)


def leer_hipotesis(ruta: str | os.PathLike) -> list[dict]:
    """Lee ``hipotesis.json`` y valida su esquema."""
    hipotesis = load_json(ruta)
    validar_hipotesis(hipotesis)
    return hipotesis
