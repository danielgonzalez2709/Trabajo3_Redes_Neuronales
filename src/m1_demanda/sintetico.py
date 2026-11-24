"""Serie sintética de M1 (núcleo §5.11), solo para desarrollo y pruebas.

Esquema exacto de §5.1: ``ruta_id, origen_divipola, destino_divipola, fecha, pasajeros, despachos, sin_registro,
anomalo``, una fila por ``(ruta, fecha)`` sin huecos.

**Los códigos son ficticios y NO existen en DIVIPOLA**: usan el departamento ``00`` (``00001``, ``00002``, ``00003``).
Ninguna cifra, figura o conclusión del blog puede salir de estos datos (núcleo §0.8). El archivo ``rutas.yaml`` lo declara
con ``sintetico: true``.

Pasajeros ~ Poisson(media), con media = nivel de la ruta × tendencia × factor semanal × factor anual × factor pandemia
× picos de temporada alta. Un día ``sin_registro`` tiene pasajeros y despachos en 0; un día ``anomalo`` tiene pasajeros 0
y despachos > 0. Todo sale de un único ``np.random.Generator`` sembrado con ``src/comun/seeds.py``.

Uso: ``python -m src.m1_demanda.sintetico [--semilla N] [--destino CARPETA]``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.comun.seeds import make_rng

SEMILLA_BASE = 0
RUN_ID = 0
DESTINO = Path("data/sintetico/m1")
NOMBRE_PARQUET = "demanda_diaria.parquet"
NOMBRE_RUTAS = "rutas.yaml"

INICIO = "2019-01-01"
FIN = "2024-12-31"

# Códigos ficticios: departamento 00, inexistente en DIVIPOLA. Nombres también ficticios.
MUNICIPIOS = {
    "00001": "Municipio ficticio A",
    "00002": "Municipio ficticio B",
    "00003": "Municipio ficticio C",
}
# (origen, destino, nivel medio de pasajeros/día en 2019, tendencia anual relativa)
RUTAS = (
    ("00001", "00002", 600.0, 0.04),
    ("00002", "00001", 560.0, 0.03),
    ("00001", "00003", 300.0, 0.06),
    ("00003", "00001", 280.0, 0.05),
)

# Factor por día de la semana (lunes = 0 ... domingo = 6).
FACTOR_SEMANAL = (0.95, 0.85, 0.85, 0.95, 1.30, 1.10, 1.25)
AMPLITUD_ANUAL = 0.15
DIA_PICO_ANUAL = 355  # cerca de diciembre

# Pandemia: caída lineal, valle, recuperación lineal hasta el nivel previo.
PANDEMIA_INICIO = "2020-03-15"
PANDEMIA_VALLE = "2020-04-15"
PANDEMIA_FIN_VALLE = "2020-08-31"
PANDEMIA_RECUPERADO = "2022-06-30"
FACTOR_VALLE = 0.08

# Picos aleatorios de temporada alta.
PICOS_POR_ANIO = 8
DURACION_PICO = (3, 6)  # días, extremos incluidos
FACTOR_PICO = (1.4, 2.0)

PROB_SIN_REGISTRO = 0.01
PROB_ANOMALO = 0.005
DESPACHOS_ANOMALO = (1, 3)  # extremos incluidos
CAPACIDAD_DESPACHO = 40  # pasajeros por despacho

MEDIA_MINIMA = 0.5  # evita medias nulas en el valle de la pandemia


def _dias_desde_epoca(fechas: pd.DatetimeIndex) -> np.ndarray:
    """Días (float) desde 1970-01-01, sin suponer la resolución (ns, us, s...) del índice."""
    return np.asarray((fechas - pd.Timestamp("1970-01-01")) / pd.Timedelta(days=1), dtype=float)


def _factor_pandemia(fechas: pd.DatetimeIndex) -> np.ndarray:
    """Factor multiplicativo: 1 → valle → 1 con rampas lineales (por interpolación en días)."""
    puntos = [PANDEMIA_INICIO, PANDEMIA_VALLE, PANDEMIA_FIN_VALLE, PANDEMIA_RECUPERADO]
    x = _dias_desde_epoca(pd.to_datetime(puntos))
    y = [1.0, FACTOR_VALLE, FACTOR_VALLE, 1.0]
    return np.interp(_dias_desde_epoca(fechas), x, y)


def _factor_picos(rng: np.random.Generator, fechas: pd.DatetimeIndex) -> np.ndarray:
    factor = np.ones(len(fechas))
    n_anios = fechas.year.max() - fechas.year.min() + 1
    for _ in range(PICOS_POR_ANIO * n_anios):
        inicio = int(rng.integers(0, len(fechas)))
        duracion = int(rng.integers(DURACION_PICO[0], DURACION_PICO[1] + 1))
        factor[inicio : inicio + duracion] = np.maximum(factor[inicio : inicio + duracion], rng.uniform(*FACTOR_PICO))
    return factor


def _serie_ruta(rng: np.random.Generator, fechas: pd.DatetimeIndex, nivel: float, tendencia: float) -> pd.DataFrame:
    anios = (fechas - fechas[0]).days.to_numpy() / 365.25
    semanal = np.array(FACTOR_SEMANAL)[fechas.day_of_week.to_numpy()]
    anual = 1.0 + AMPLITUD_ANUAL * np.cos(2 * np.pi * (fechas.day_of_year.to_numpy() - DIA_PICO_ANUAL) / 365.25)
    media = nivel * (1.0 + tendencia * anios) * semanal * anual * _factor_pandemia(fechas) * _factor_picos(rng, fechas)
    pasajeros = rng.poisson(np.maximum(media, MEDIA_MINIMA)).astype("int64")
    despachos = np.ceil(pasajeros / CAPACIDAD_DESPACHO).astype("int64")

    sin_registro = rng.random(len(fechas)) < PROB_SIN_REGISTRO
    anomalo = (rng.random(len(fechas)) < PROB_ANOMALO) & ~sin_registro
    extra = rng.integers(DESPACHOS_ANOMALO[0], DESPACHOS_ANOMALO[1] + 1, len(fechas))
    pasajeros[sin_registro | anomalo] = 0
    despachos[sin_registro] = 0
    despachos[anomalo] = extra[anomalo]
    return pd.DataFrame({"pasajeros": pasajeros, "despachos": despachos, "sin_registro": sin_registro, "anomalo": anomalo})


def generar(semilla: int) -> pd.DataFrame:
    """Serie sintética completa (4 rutas × todos los días de 2019-2024) con el esquema de §5.1. Determinista en ``semilla``."""
    rng = make_rng(semilla, RUN_ID)
    fechas = pd.date_range(INICIO, FIN, freq="D")
    fecha_date = [d.date() for d in fechas]
    partes = []
    for origen, destino, nivel, tendencia in RUTAS:
        parte = _serie_ruta(rng, fechas, nivel, tendencia)
        parte.insert(0, "fecha", pd.Series(fecha_date, dtype=object))
        parte.insert(0, "destino_divipola", destino)
        parte.insert(0, "origen_divipola", origen)
        parte.insert(0, "ruta_id", f"{origen}-{destino}")
        partes.append(parte)
    return pd.concat(partes, ignore_index=True)


def _rutas_yaml(semilla: int) -> dict:
    ids = {(o, d) for o, d, _, _ in RUTAS}
    rutas = []
    for origen, destino, _, _ in RUTAS:
        if (destino, origen) not in ids:  # defensa: cada ruta debe tener regreso
            raise ValueError(f"La ruta {origen}-{destino} no tiene ruta de regreso")
        rutas.append(
            {
                "ruta_id": f"{origen}-{destino}",
                "origen_municipio": MUNICIPIOS[origen],
                "destino_municipio": MUNICIPIOS[destino],
                "ruta_regreso_id": f"{destino}-{origen}",
                "criterios_seleccion": "Ruta ficticia generada para desarrollo; no hay selección real (DA-3 elige las reales).",
            }
        )
    return {
        "sintetico": True,
        "aviso": "Códigos ficticios del departamento 00, que no existe en DIVIPOLA. Solo para desarrollo y pruebas (§5.11).",
        "semilla": semilla,
        "periodo": [INICIO, FIN],
        "rutas": rutas,
    }


def escribir(semilla: int = SEMILLA_BASE, destino: str | os.PathLike = DESTINO) -> tuple[Path, Path]:
    """Escribe ``demanda_diaria.parquet`` y ``rutas.yaml`` en ``destino``; devuelve ambas rutas."""
    carpeta = Path(destino)
    carpeta.mkdir(parents=True, exist_ok=True)
    parquet = carpeta / NOMBRE_PARQUET
    generar(semilla).to_parquet(parquet, index=False)
    rutas = carpeta / NOMBRE_RUTAS
    rutas.write_text(yaml.safe_dump(_rutas_yaml(semilla), allow_unicode=True, sort_keys=False), encoding="utf-8", newline="\n")
    return parquet, rutas


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Genera la serie sintética de M1 (solo desarrollo).")
    ap.add_argument("--semilla", type=int, default=SEMILLA_BASE)
    ap.add_argument("--destino", default=str(DESTINO))
    args = ap.parse_args(argv)
    for ruta in escribir(args.semilla, args.destino):
        print(ruta)


if __name__ == "__main__":
    main()
