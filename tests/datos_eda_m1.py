"""Constructores de series sintéticas para las pruebas del análisis descriptivo de M1 (CA-4).

No es un archivo de pruebas: lo importan `test_eda_m1.py` y `test_figs_m1_datos.py`. Todo se construye aquí con periodos y
patrones conocidos; ninguna cifra es real.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

RUTAS = ["11001-76001", "76001-11001"]
ORIGENES = ["11001", "76001"]
FACTOR_SEMANAL = np.array([1.0, 0.8, 0.8, 0.9, 1.2, 1.5, 1.3])  # lunes..domingo (patrón conocido)
REGLAS = ("despachos_sin_pasajeros", "caida_robusta", "pico_robusto", "pasajeros_por_despacho_bajo")


def fechas() -> pd.DatetimeIndex:
    return pd.date_range("2021-01-01", "2023-12-31", freq="D")


def diaria(tendencia_anual: float = 0.0, ruido: float = 0.0) -> pd.DataFrame:
    """Dos rutas con perfil semanal exacto, nivel 1000 y (opcional) tendencia lineal y ruido lognormal (semilla fija)."""
    rng = np.random.default_rng(123)
    f = fechas()
    filas = []
    for k, ruta in enumerate(RUTAS):
        t = np.arange(len(f)) / 365.0
        y = 1000.0 * (1 + k) * (1 + tendencia_anual * t) * FACTOR_SEMANAL[f.day_of_week]
        y = y * np.exp(ruido * rng.standard_normal(len(f)))
        filas.append(
            pd.DataFrame(
                {
                    "ruta_id": ruta,
                    "origen_divipola": ruta[:5],
                    "destino_divipola": ruta[6:],
                    "fecha": f,
                    "pasajeros": np.round(y).astype("int64"),
                    "despachos": 50,
                    "sin_registro": False,
                    "anomalo": False,
                }
            )
        )
    d = pd.concat(filas, ignore_index=True)
    sin = (d["fecha"] >= "2021-05-02") & (d["fecha"] <= "2021-05-31")
    d.loc[sin, ["pasajeros", "despachos"]] = 0
    d.loc[sin, "sin_registro"] = True
    return d


def detalle(d: pd.DataFrame) -> pd.DataFrame:
    """60 % origen / 40 % tránsito; BUS y MICROBUS (este solo hasta 2022)."""
    partes = []
    for tipo, p_tipo in (("ORIGEN", 0.6), ("TRANSITO", 0.4)):
        for clase in ("BUS", "MICROBUS"):
            p = p_tipo * (0.7 if clase == "BUS" else 0.3)
            x = d[["ruta_id", "origen_divipola", "destino_divipola", "fecha", "pasajeros", "despachos"]].copy()
            if clase == "MICROBUS":
                x = x[x["fecha"] < "2023-01-01"]
            x["pasajeros"] = np.round(x["pasajeros"] * p).astype("int64")
            x["despachos"] = np.round(x["despachos"] * p).astype("int64")
            x["tipo_despacho"], x["clase_vehiculo"] = tipo, clase
            partes.append(x)
    return pd.concat(partes, ignore_index=True)


def marcas(d: pd.DataFrame) -> pd.DataFrame:
    m = d[["ruta_id", "fecha"]].copy()
    for regla in REGLAS:
        m[regla] = False
    idx = d.index[(d["ruta_id"] == RUTAS[0]) & (d["fecha"] == "2022-03-15")]
    m.loc[idx, "caida_robusta"] = True  # un día anómalo por una sola regla, para contarlo
    return m


def calendario(festivos: list[str] = (), vacaciones: dict[str, list[str]] | None = None,
               nulos: dict[str, list[str]] | None = None) -> pd.DataFrame:
    """Calendario con las columnas del núcleo §5.2 y `vacaciones_escolares_<DIVIPOLA>` por ciudad de origen.

    `vacaciones` y `nulos` mapean un código DIVIPOLA a fechas (marcadas verdaderas / nulas en esa ciudad).
    """
    cal = pd.DataFrame({"fecha": fechas()})
    for col in ("festivo", "puente", "semana_santa", "vacaciones_escolares", "fin_de_anio"):
        cal[col] = False
    cal.loc[cal["fecha"].isin(pd.to_datetime(list(festivos))), "festivo"] = True
    for cod in ORIGENES:
        col = pd.Series(False, index=cal.index, dtype="boolean")
        col[cal["fecha"].isin(pd.to_datetime((vacaciones or {}).get(cod, [])))] = True
        col[cal["fecha"].isin(pd.to_datetime((nulos or {}).get(cod, [])))] = pd.NA
        cal[f"vacaciones_escolares_{cod}"] = col
    cal["dia_semana"] = cal["fecha"].dt.day_of_week
    return cal
