"""M1 — análisis descriptivo, secciones 3-7 de la plantilla común (núcleo §5.12; CA-4, Camila).

`python run.py m1-eda --config configs/m1/datos.yaml` lee `data/processed/m1/` y escribe en `results/data/m1/eda/`
tablas CSV/parquet y tres JSON (`hallazgos.json`, `hipotesis.json`, `implicaciones.json`). Este módulo calcula las
tablas de las secciones 3-4 y los hallazgos; las hipótesis y las implicaciones (secciones 5-7, cálculo y texto) están en
`eda_hipotesis.py`. Las rutas relativas de la configuración se leen desde la raíz del repo, no desde el cwd. Las secciones 1-2
(`ficha.json`, `calidad.csv`, `diccionario.json`) son de Daniel (DA-4) y este módulo NO las toca. Los modelos no
dibujan: las figuras salen de `src/viz/figs_m1_datos.py` leyendo estos archivos.

Reglas que respeta:
- Todo es DESCRIPTIVO. Las marcas `anomalo` / `sin_registro` y las ventanas centradas miran toda la serie (núcleo §5.1):
  aquí solo se cuentan o se usan para describir, nunca producen una variable de entrada de un modelo.
- Ninguna fecha de festivo, puente, temporada escolar ni Semana Santa se escribe aquí. Si existe
  `data/processed/m1/calendario.parquet` (CA-1, núcleo §5.2) se usa; si no, esas hipótesis quedan `pendiente` con
  `resultado` = «falta el calendario de CA-1». Las vacaciones escolares usan la columna de la ciudad de origen de cada ruta.
- Los veredictos son `pendiente` hasta modelar (§5.12, sección 7): el resultado descriptivo va en `resultado`/`evidencia`.

Parámetros propuestos para un bloque `eda:` de `configs/m1/datos.yaml` (el archivo es de Daniel; mientras no exista el
bloque se usan `PARAMETROS_POR_DEFECTO`): ver ese diccionario.
"""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.comun.eda import escribir_hipotesis
from src.comun.results import save_json
from src.m1_demanda.datos import REGLAS, TIPOS_DESPACHO
from src.m1_demanda.eda_hipotesis import (
    ANUAL,
    COLUMNAS_CALENDARIO,
    FALTA_CALENDARIO,
    SEMANAL,
    construir_hipotesis,
    construir_implicaciones,
)

RAIZ = Path(__file__).resolve().parents[2]
ORIGEN, TRANSITO = TIPOS_DESPACHO

# ---------------------------------------------------------------------------------------------- constantes
PARAMETROS_POR_DEFECTO: dict[str, Any] = {
    # La descomposición y los perfiles arrancan aquí para no contaminar con mayo-2021 (núcleo §5.1, Daniel 24-nov).
    "inicio_analisis": "2021-06-01",
    # Último origen de pronóstico del arnés (núcleo §5.3, rejilla anclada para que el test cubra el fin de año).
    "ultimo_origen_test": "2023-12-01",
    # Efecto de calendario: se compara cada día marcado con el mismo día de la semana a ±ventana días sin marca.
    "ventana_calendario_dias": 42,
    "min_vecinos_calendario": 2,
    # Hallazgos de la spec de Camila §3.0 (rutas y fechas por parámetro, no quemadas en las funciones).
    "salto_transito": {"ruta_id": "11001-15759", "mes": "2022-11", "meses_comparacion": 6},
    "microbus": {"ruta_id": "11001-76001", "clase": "MICROBUS", "anio": 2023},
    "asimetria_clases": {"rutas": ["52001-52356", "52356-52001"]},
}

# MSTL: ventana del suavizador estacional de cada periodo (SEMANAL, ANUAL; Anexo, M1 figuras mínimas).
# Con el valor por defecto de statsmodels (11 y 15) el
# componente anual sigue el ruido día a día (2-3 puntos por día del año) y el residuo queda casi en cero; una ventana
# mayor que el número de ciclos y grado 0 lo vuelve periódico (el mismo perfil anual en todos los años).
VENTANAS_MSTL = (11, 100001)
GRADO_ESTACIONAL_MSTL = 0

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]
CARPETA_SALIDA = RAIZ / "results" / "data" / "m1" / "eda"

COLUMNAS_OBJETIVO = (
    ["ruta_id", "dias", "pasajeros_total", "media_diaria", "mediana_diaria", "minimo", "maximo", "ceros",
     "ceros_con_despachos", "sin_registro", "anomalos"] + [f"anomalos_{r}" for r in REGLAS]
)
COLUMNAS_TRANSITO = ["ruta_id", "anio", "pasajeros_origen", "pasajeros_transito", "pct_transito", "despachos_origen",
                     "despachos_transito", "razon_transito_origen"]
COLUMNAS_CLASES = ["ruta_id", "anio", "clase_vehiculo", "pasajeros", "pct"]
COLUMNAS_TRANSITO_MENSUAL = ["ruta_id", "mes", "dias_con_registro", "pasajeros_dia_origen", "pasajeros_dia_transito",
                             "pasajeros_dia_transito_microbus", "despachos_dia_origen", "despachos_dia_transito"]
COLUMNAS_PERFIL_SEMANAL = ["ruta_id", "dia_semana", "dia", "n_dias", "media", "mediana", "razon_vs_media_semanal",
                           "razon_mediana"]
COLUMNAS_PERFIL_MENSUAL = ["ruta_id", "anio", "mes", "n_dias", "media_diaria", "anio_completo", "razon_vs_media_anual"]
COLUMNAS_TENDENCIA = ["ruta_id", "anio", "media_ene_abr", "variacion_pct_ene_abr", "media_jun_dic",
                      "variacion_pct_jun_dic"]
COLUMNAS_DESCOMPOSICION = ["ruta_id", "fecha", "observado_log1p", "tendencia", "semanal", "anual", "residuo"]
COLUMNAS_RESUMEN_DESCOMPOSICION = ["ruta_id", "observaciones", "sin_registro_imputados", "anomalos_en_ventana",
                                   "fuerza_tendencia", "fuerza_semanal", "fuerza_anual", "razon_max_min_semanal"]
COLUMNAS_EFECTO_CALENDARIO = ["ruta_id", "columna", "n_dias", "n_nulos_excluidos", "razon_media", "razon_mediana",
                              "razon_min", "razon_max"]

ARCHIVOS_SALIDA = (
    "serie_marcada.parquet",
    "objetivo_por_ruta.csv",
    "transito_por_ruta_anio.csv",
    "transito_mensual.csv",
    "clases_por_ruta_anio.csv",
    "perfil_semanal.csv",
    "perfil_mensual.csv",
    "tendencia_anual.csv",
    "descomposicion.parquet",
    "descomposicion_resumen.csv",
    "efectos_calendario.csv",
    "hallazgos.json",
    "hipotesis.json",
    "implicaciones.json",
)


# ---------------------------------------------------------------------------------------------- utilidades
def parametros(cfg: dict | None) -> dict:
    """`PARAMETROS_POR_DEFECTO` sobrescritos por el bloque `eda:` de la configuración (si existe)."""
    p = copy.deepcopy(PARAMETROS_POR_DEFECTO)
    extra = (cfg or {}).get("eda") or {}
    for clave, valor in extra.items():
        if clave not in p:
            raise ValueError(f"eda.{clave}: parámetro desconocido (válidos: {sorted(p)})")
        if isinstance(p[clave], dict) and isinstance(valor, dict):
            p[clave].update(valor)
        else:
            p[clave] = valor
    return p


def ruta_en_raiz(ruta: str | Path) -> Path:
    """Las rutas relativas de la configuración se leen desde la raíz del repo (no desde el cwd); las absolutas, tal cual."""
    r = Path(ruta)
    return r if r.is_absolute() else RAIZ / r


def _fecha_ns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"]).astype("datetime64[ns]")
    return df


def _n(x: float, d: int = 2) -> str:
    """Número con coma decimal (texto en español)."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/d"
    return f"{x:.{d}f}".replace(".", ",")


def _py(x: Any) -> Any:
    """Convierte escalares de numpy a Python y redondea para que los archivos sean estables."""
    if isinstance(x, (np.floating, float)):
        return None if np.isnan(x) else round(float(x), 4)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    return x


def fuerza(componente: np.ndarray, residuo: np.ndarray) -> float:
    """Fuerza de un componente: max(0, 1 − Var(residuo) / Var(componente + residuo)).

    TODO(cita): definición tomada de la medida de fuerza de tendencia/estacionalidad de Hyndman y Athanasopoulos,
    *Forecasting: Principles and Practice* (3.ª ed., cap. 4, «Strength of trend and seasonality»); verificar contra la fuente.
    """
    v = float(np.var(np.asarray(componente) + np.asarray(residuo)))
    if v == 0.0:
        return 0.0
    return float(max(0.0, 1.0 - float(np.var(residuo)) / v))


def cargar_datos(carpeta: str | Path, salida: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Lee diaria, detalle y marcas de `data/processed/m1/` (nombres de `cfg["salida"]`)."""
    c = ruta_en_raiz(carpeta)
    s = salida or {}
    diaria = _fecha_ns(pd.read_parquet(c / s.get("diaria", "demanda_diaria.parquet")))
    detalle = _fecha_ns(pd.read_parquet(c / s.get("detalle", "demanda_detalle.parquet")))
    marcas = _fecha_ns(pd.read_parquet(c / s.get("marcas", "marcas_anomalos.parquet")))
    return diaria, detalle, marcas


def _serie_marcada(diaria: pd.DataFrame, marcas: pd.DataFrame) -> pd.DataFrame:
    base = _fecha_ns(diaria)[["ruta_id", "fecha", "pasajeros", "despachos", "sin_registro", "anomalo"]]
    m = _fecha_ns(marcas)
    cols = [r for r in REGLAS if r in m.columns]
    out = base.merge(m[["ruta_id", "fecha", *cols]], on=["ruta_id", "fecha"], how="left")
    for r in REGLAS:
        out[r] = out[r].fillna(False).astype(bool) if r in out else False
    return out.sort_values(["ruta_id", "fecha"]).reset_index(drop=True)


# ---------------------------------------------------------------------------------------------- sección 3
def tabla_objetivo(diaria: pd.DataFrame, marcas: pd.DataFrame) -> pd.DataFrame:
    """Pasajeros por ruta y día: escala, ceros, días sin registro y anómalos (total y por regla)."""
    s = _serie_marcada(diaria, marcas)
    filas = []
    for ruta, g in s.groupby("ruta_id", sort=True):
        con = g[~g["sin_registro"]]
        fila = {
            "ruta_id": ruta,
            "dias": int(len(g)),
            "pasajeros_total": int(g["pasajeros"].sum()),
            "media_diaria": float(con["pasajeros"].mean()),
            "mediana_diaria": float(con["pasajeros"].median()),
            # sin ningún día con registro no hay mínimo ni máximo: None (nulo), no un error
            "minimo": int(con["pasajeros"].min()) if len(con) else None,
            "maximo": int(con["pasajeros"].max()) if len(con) else None,
            "ceros": int((g["pasajeros"] == 0).sum()),
            "ceros_con_despachos": int(((g["pasajeros"] == 0) & (g["despachos"] > 0)).sum()),
            "sin_registro": int(g["sin_registro"].sum()),
            "anomalos": int(g["anomalo"].sum()),
        }
        for r in REGLAS:
            fila[f"anomalos_{r}"] = int(g[r].sum())
        filas.append(fila)
    return pd.DataFrame(filas, columns=COLUMNAS_OBJETIVO)


def proporcion_transito(detalle: pd.DataFrame) -> pd.DataFrame:
    """Pasajeros y despachos de ORIGEN y de TRANSITO por ruta y año, y la proporción en tránsito."""
    d = _fecha_ns(detalle)
    d["anio"] = d["fecha"].dt.year
    p = d.pivot_table(index=["ruta_id", "anio"], columns="tipo_despacho", values=["pasajeros", "despachos"],
                      aggfunc="sum", fill_value=0)
    out = pd.DataFrame(index=p.index)
    for tipo, nombre in ((ORIGEN, "origen"), (TRANSITO, "transito")):
        for var, pref in (("pasajeros", "pasajeros"), ("despachos", "despachos")):
            out[f"{pref}_{nombre}"] = p[(var, tipo)] if (var, tipo) in p.columns else 0
    out = out.reset_index()
    total = out["pasajeros_origen"] + out["pasajeros_transito"]
    out["pct_transito"] = np.where(total > 0, 100.0 * out["pasajeros_transito"] / total.replace(0, np.nan), 0.0)
    out["razon_transito_origen"] = out["pasajeros_transito"] / out["pasajeros_origen"].replace(0, np.nan)
    return out[COLUMNAS_TRANSITO]


def composicion_clases(detalle: pd.DataFrame) -> pd.DataFrame:
    """Participación (%) de cada clase de vehículo en los pasajeros de la ruta y el año (origen + tránsito).

    Una clase vista en algún año de la ruta aparece con 0 en los años en que no hay filas (así se ve que desaparece).
    """
    d = _fecha_ns(detalle)
    d["anio"] = d["fecha"].dt.year
    p = d.pivot_table(index=["ruta_id", "anio"], columns="clase_vehiculo", values="pasajeros", aggfunc="sum",
                      fill_value=0)
    pct = p.div(p.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0) * 100.0
    largo = (
        p.stack().rename("pasajeros").reset_index().merge(pct.stack().rename("pct").reset_index(),
                                                          on=["ruta_id", "anio", "clase_vehiculo"])
    )
    largo["pasajeros"] = largo["pasajeros"].astype("int64")
    return largo[COLUMNAS_CLASES].sort_values(["ruta_id", "anio", "clase_vehiculo"]).reset_index(drop=True)


def transito_mensual(detalle: pd.DataFrame) -> pd.DataFrame:
    """Por ruta y mes: pasajeros/día de origen y de tránsito (y de MICROBUS en tránsito) y despachos/día.

    El divisor son los días con alguna fila en el detalle (los días sin filas no cuentan como demanda cero).
    """
    d = _fecha_ns(detalle)
    d["mes"] = d["fecha"].dt.strftime("%Y-%m")
    filas = []
    for (ruta, mes), g in d.groupby(["ruta_id", "mes"], sort=True):
        dias = int(g["fecha"].nunique())
        o, t = g[g["tipo_despacho"] == ORIGEN], g[g["tipo_despacho"] == TRANSITO]
        tm = t[t["clase_vehiculo"] == "MICROBUS"]
        filas.append(
            {
                "ruta_id": ruta,
                "mes": mes,
                "dias_con_registro": dias,
                "pasajeros_dia_origen": o["pasajeros"].sum() / dias,
                "pasajeros_dia_transito": t["pasajeros"].sum() / dias,
                "pasajeros_dia_transito_microbus": tm["pasajeros"].sum() / dias,
                "despachos_dia_origen": o["despachos"].sum() / dias,
                "despachos_dia_transito": t["despachos"].sum() / dias,
            }
        )
    return pd.DataFrame(filas, columns=COLUMNAS_TRANSITO_MENSUAL)


# ---------------------------------------------------------------------------------------------- sección 4
def _validos(diaria: pd.DataFrame, inicio: str) -> pd.DataFrame:
    d = _fecha_ns(diaria)
    return d[(d["fecha"] >= pd.Timestamp(inicio)) & (~d["sin_registro"])]


def perfil_semanal(diaria: pd.DataFrame, inicio: str) -> pd.DataFrame:
    """Perfil por día de la semana (0 = lunes) desde `inicio`, sin días `sin_registro`.

    `razon_vs_media_semanal` = media del día / promedio de las siete medias; `razon_mediana` ídem con medianas (los
    anómalos se dejan: la mediana los amortigua y así se ve cuánto pesan). Si el promedio es 0 la razón queda NaN
    (`calcular_hallazgos` lo avisa).
    """
    d = _validos(diaria, inicio)
    d["dia_semana"] = d["fecha"].dt.day_of_week
    g = d.groupby(["ruta_id", "dia_semana"])["pasajeros"].agg(n_dias="size", media="mean", mediana="median").reset_index()
    g["razon_vs_media_semanal"] = g["media"] / g.groupby("ruta_id")["media"].transform("mean").replace(0, np.nan)
    g["razon_mediana"] = g["mediana"] / g.groupby("ruta_id")["mediana"].transform("mean").replace(0, np.nan)
    g["dia"] = g["dia_semana"].map(lambda i: DIAS[i])
    return g[COLUMNAS_PERFIL_SEMANAL].sort_values(["ruta_id", "dia_semana"]).reset_index(drop=True)


def perfil_mensual(diaria: pd.DataFrame, inicio: str) -> pd.DataFrame:
    """Media diaria por ruta, año y mes desde `inicio` (sin `sin_registro`) y su razón con la media diaria del año.

    La razón solo se calcula en años con los 12 meses (`anio_completo`) y media anual distinta de 0 (si no, NaN); con
    los años actuales son 2022 y 2023, así que el perfil anual se apoya en dos ciclos como máximo.
    """
    d = _validos(diaria, inicio)
    d["anio"], d["mes"] = d["fecha"].dt.year, d["fecha"].dt.month
    g = d.groupby(["ruta_id", "anio", "mes"])["pasajeros"].agg(n_dias="size", media_diaria="mean").reset_index()
    meses = g.groupby(["ruta_id", "anio"])["mes"].transform("nunique")
    g["anio_completo"] = meses == 12
    media_anio = d.groupby(["ruta_id", "anio"])["pasajeros"].mean().rename("media_anio").reset_index()
    g = g.merge(media_anio, on=["ruta_id", "anio"])
    razon = g["media_diaria"] / g["media_anio"].replace(0, np.nan)
    g["razon_vs_media_anual"] = razon.where(g["anio_completo"])
    return g[COLUMNAS_PERFIL_MENSUAL].sort_values(["ruta_id", "anio", "mes"]).reset_index(drop=True)


def tendencia_anual(diaria: pd.DataFrame, inicio: str) -> pd.DataFrame:
    """Media diaria por ruta y año en dos ventanas comparables: enero-abril y junio-diciembre (sin `sin_registro`).

    La ventana de junio-diciembre arranca en `inicio` en 2021 (mayo-2021 casi vacío); se compara contra el año previo.
    Es el proxy de pospandemia: la caída de 2020 no está en los datos (núcleo §5.1). Con media previa 0 la variación es
    NaN (no infinito; `calcular_hallazgos` lo avisa).
    """
    d = _fecha_ns(diaria)
    d = d[~d["sin_registro"]].copy()
    d["anio"], d["mes"] = d["fecha"].dt.year, d["fecha"].dt.month
    ini = pd.Timestamp(inicio)
    ene_abr = d[d["mes"].between(1, 4)].groupby(["ruta_id", "anio"])["pasajeros"].mean().rename("media_ene_abr")
    jun_dic = d[(d["mes"] >= 6) & (d["fecha"] >= ini)].groupby(["ruta_id", "anio"])["pasajeros"].mean().rename("media_jun_dic")
    t = pd.concat([ene_abr, jun_dic], axis=1).reset_index().sort_values(["ruta_id", "anio"])
    for col, nueva in (("media_ene_abr", "variacion_pct_ene_abr"), ("media_jun_dic", "variacion_pct_jun_dic")):
        previo = t.groupby("ruta_id")[col].shift(1).replace(0, np.nan)
        t[nueva] = 100.0 * (t[col] / previo - 1.0)
    return t[COLUMNAS_TENDENCIA].reset_index(drop=True)


def descomposicion(diaria: pd.DataFrame, inicio: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """MSTL (statsmodels) de log(1 + pasajeros) con periodos semanal (`SEMANAL`) y anual (`ANUAL`), por ruta, desde `inicio`.

    - Se trabaja en log(1 + y): el componente semanal y el anual quedan como efectos multiplicativos (la amplitud
      crece con el nivel de la ruta).
    - Los días `sin_registro` dentro de la ventana no son demanda cero: se marcan como faltantes y se interpolan
      linealmente en log(1 + y) para poder descomponer; el número de días imputados se reporta (con `inicio` en
      2021-06-01 deberían ser 0).
    - Los días `anomalo` se dejan tal cual; el STL interno es robusto (`robust=True`) y los pondera menos.
    - Se exigen al menos dos ciclos del periodo más largo (`2 × ANUAL` observaciones).
    - El componente anual es PERIÓDICO (`VENTANAS_MSTL`, grado 0): con la ventana por defecto de statsmodels el residuo
      se anulaba porque el componente seguía el ruido. Con ~2-3 ciclos anuales (observaciones / `ANUAL`) cada día del año se estima con
      2-3 puntos, así que la «fuerza anual» sale sesgada hacia arriba (con ruido blanco y sin ciclo anual, ~0,4) y la
      tendencia (ventana > 365 por exigencia de STL) no recoge la recuperación de 2021. No leer `fuerza_anual` ni `anual`
      como estacionalidad confirmada; la evidencia directa es el perfil mensual de años completos y su consistencia.

    Devuelve (componentes por ruta y día, resumen por ruta). Observado = tendencia + semanal + anual + residuo.
    """
    from statsmodels.tsa.seasonal import MSTL

    periodos = [SEMANAL, ANUAL]
    d = _fecha_ns(diaria)
    d = d[d["fecha"] >= pd.Timestamp(inicio)]
    comps, resumen = [], []
    for ruta, g in d.groupby("ruta_id", sort=True):
        g = g.sort_values("fecha").set_index("fecha")
        rejilla = pd.date_range(g.index.min(), g.index.max(), freq="D")
        if len(rejilla) != len(g):
            raise ValueError(f"{ruta}: la serie tiene huecos de fecha (contrato §5.1: sin huecos)")
        if len(g) < 2 * ANUAL:
            raise ValueError(
                f"{ruta}: {len(g)} observaciones desde {inicio}; MSTL con periodo {ANUAL} exige al menos "
                f"{2 * ANUAL} (dos ciclos)"
            )
        y = np.log1p(g["pasajeros"].astype(float))
        sin = g["sin_registro"].to_numpy()
        y[sin] = np.nan
        y = y.interpolate(limit_direction="both")
        res = MSTL(y, periods=periodos, windows=list(VENTANAS_MSTL), iterate=2,
                   stl_kwargs={"robust": True, "seasonal_deg": GRADO_ESTACIONAL_MSTL}).fit()
        seas = res.seasonal
        sem = seas[f"seasonal_{SEMANAL}"].to_numpy()
        anu = seas[f"seasonal_{ANUAL}"].to_numpy()
        tend, resid = np.asarray(res.trend), np.asarray(res.resid)
        comps.append(
            pd.DataFrame(
                {"ruta_id": ruta, "fecha": g.index, "observado_log1p": y.to_numpy(), "tendencia": tend,
                 "semanal": sem, "anual": anu, "residuo": resid}
            )
        )
        dow = g.index.day_of_week
        ciclo = pd.Series(sem).groupby(dow).mean()
        resumen.append(
            {
                "ruta_id": ruta,
                "observaciones": int(len(g)),
                "sin_registro_imputados": int(sin.sum()),
                "anomalos_en_ventana": int(g["anomalo"].sum()),
                "fuerza_tendencia": fuerza(tend, resid),
                "fuerza_semanal": fuerza(sem, resid),
                "fuerza_anual": fuerza(anu, resid),
                "razon_max_min_semanal": float(np.exp(ciclo.max() - ciclo.min())),
            }
        )
    return (pd.DataFrame(pd.concat(comps, ignore_index=True), columns=COLUMNAS_DESCOMPOSICION),
            pd.DataFrame(resumen, columns=COLUMNAS_RESUMEN_DESCOMPOSICION))


def efecto_calendario(diaria: pd.DataFrame, calendario: pd.DataFrame, columna: str, inicio: str,
                      ventana_dias: int = 42, min_vecinos: int = 2, por_origen: bool = False) -> pd.DataFrame:
    """Razón entre la demanda de los días con `columna` verdadera y la del MISMO día de la semana a ±`ventana_dias`.

    La referencia son los días vecinos sin marca de esa columna, con registro y no anómalos (el día marcado se conserva
    aunque esté marcado `anomalo`, para no ocultar su efecto). Un día se omite si tiene menos de `min_vecinos`
    vecinos. Descriptivo: la ventana mira a ambos lados de la fecha, así que no es una variable de modelo.

    Con `por_origen`, cada ruta usa la columna `<columna>_<origen_divipola>` de SU ciudad de origen (p. ej.
    `vacaciones_escolares_76001` para Cali→Bogotá). Los días con marca nula (vacío sin fuente en el calendario) no son ni
    marcados ni vecinos: se excluyen y se cuentan en `n_nulos_excluidos`.
    """
    d = _fecha_ns(diaria)
    cal = _fecha_ns(calendario)
    filas = []
    for ruta, g in d.groupby("ruta_id", sort=True):
        col = f"{columna}_{g['origen_divipola'].iloc[0]}" if por_origen else columna
        if col not in cal.columns:
            raise KeyError(col)
        g = g.merge(cal[["fecha", col]].rename(columns={col: "_marca"}), on="fecha", how="left")
        g = g[(g["fecha"] >= pd.Timestamp(inicio)) & (~g["sin_registro"])].sort_values("fecha").reset_index(drop=True)
        nulos = g["_marca"].isna()
        g = g[~nulos].copy()
        g["_marca"] = g["_marca"].astype(bool)
        base = g[(~g["_marca"]) & (~g["anomalo"])]
        razones = []
        for _, f in g[g["_marca"]].iterrows():
            vec = base[(base["fecha"].dt.day_of_week == f["fecha"].day_of_week)
                       & ((base["fecha"] - f["fecha"]).abs() <= pd.Timedelta(days=ventana_dias))]
            if len(vec) < min_vecinos or vec["pasajeros"].mean() <= 0:
                continue
            razones.append(f["pasajeros"] / vec["pasajeros"].mean())
        if razones:
            r = np.asarray(razones)
            filas.append({"ruta_id": ruta, "columna": col, "n_dias": len(r), "n_nulos_excluidos": int(nulos.sum()),
                          "razon_media": r.mean(), "razon_mediana": float(np.median(r)), "razon_min": r.min(),
                          "razon_max": r.max()})
    return pd.DataFrame(filas, columns=COLUMNAS_EFECTO_CALENDARIO)


def agregar_efectos_calendario(res: dict, diaria: pd.DataFrame, calendario: pd.DataFrame, p: dict) -> None:
    """Calcula los efectos de las columnas de `COLUMNAS_CALENDARIO` y los guarda en `res["efectos"]`.

    Una columna ausente del calendario (o, en las de ciudad, la de algún origen de las rutas) se anota en
    `res["calendario_faltan"]` y esa hipótesis queda con «falta la columna …».
    """
    origenes = sorted(set(_fecha_ns(diaria)["origen_divipola"]))
    for cols, por_origen in COLUMNAS_CALENDARIO.values():
        for col in cols:
            necesarias = [f"{col}_{o}" for o in origenes] if por_origen else [col]
            ausentes = [c for c in necesarias if c not in calendario.columns]
            if ausentes:
                res["calendario_faltan"].extend(ausentes)
                continue
            res["efectos"][col] = efecto_calendario(diaria, calendario, col, p["inicio_analisis"],
                                                    p["ventana_calendario_dias"], p["min_vecinos_calendario"], por_origen)


# ---------------------------------------------------------------------------------------------- hallazgos
def _avisos_razones(res: dict) -> list[str]:
    """Rutas con razones sin definir (media 0 o año previo en 0): NaN en las tablas, nunca infinito ni cero inventado."""
    avisos = []
    ps, ten, pm = res["perfil_semanal"], res["tendencia"], res["perfil_mensual"]
    con_previo = ten[ten.groupby("ruta_id")["anio"].transform("min") != ten["anio"]]  # el primer año no tiene previo
    pm = pm[pm["anio_completo"]]
    for tabla, df, columnas in (
        ("perfil_semanal", ps, ("razon_vs_media_semanal", "razon_mediana")),
        ("perfil_mensual", pm, ("razon_vs_media_anual",)),
        ("tendencia_anual", con_previo, ("variacion_pct_jun_dic", "variacion_pct_ene_abr")),
    ):
        for col in columnas:
            for ruta in sorted(set(df.loc[df[col].isna(), "ruta_id"])):
                avisos.append(f"{tabla}.{col}: {ruta} sin razón definida (media o año previo igual a 0)")
    return avisos


def calcular_hallazgos(res: dict, p: dict) -> dict:
    """Cifras de los hallazgos de la spec §3.0 (rutas y fechas salen de `p`); no disponible si la ruta no está."""
    h: dict[str, Any] = {}
    h["avisos"] = _avisos_razones(res)
    tr = res["transito_anio"]
    h["transito_vs_origen"] = {
        "descripcion": "Pasajeros de tránsito sobre el total (origen + tránsito) por ruta y año",
        "filas": [{k: _py(v) for k, v in r.items()} for r in tr.to_dict("records")],
    }
    # salto del tránsito
    cfg = p["salto_transito"]
    tm = res["transito_mes"]
    t = tm[tm["ruta_id"] == cfg["ruta_id"]].sort_values("mes").reset_index(drop=True)
    if cfg["mes"] in set(t["mes"]):
        i = int(t.index[t["mes"] == cfg["mes"]][0])
        k = int(cfg["meses_comparacion"])
        antes, despues = t.iloc[max(0, i - k):i], t.iloc[i + 1:i + 1 + k]
        if len(antes) and len(despues):
            a, b = antes["pasajeros_dia_transito"].mean(), despues["pasajeros_dia_transito"].mean()
            ao, bo = antes["pasajeros_dia_origen"].mean(), despues["pasajeros_dia_origen"].mean()
            h["salto_transito"] = {
                "disponible": True, "ruta_id": cfg["ruta_id"], "mes_referencia": cfg["mes"], "meses_comparados": k,
                "meses_antes": [antes["mes"].iloc[0], antes["mes"].iloc[-1]],
                "meses_despues": [despues["mes"].iloc[0], despues["mes"].iloc[-1]],
                "transito_dia_antes": _py(a), "transito_dia_despues": _py(b), "razon_transito": _py(b / a if a else np.nan),
                "origen_dia_antes": _py(ao), "origen_dia_despues": _py(bo), "razon_origen": _py(bo / ao if ao else np.nan),
                "despachos_transito_dia_antes": _py(antes["despachos_dia_transito"].mean()),
                "despachos_transito_dia_despues": _py(despues["despachos_dia_transito"].mean()),
                "microbus_transito_dia_antes": _py(antes["pasajeros_dia_transito_microbus"].mean()),
                "microbus_transito_dia_despues": _py(despues["pasajeros_dia_transito_microbus"].mean()),
            }
    h.setdefault("salto_transito", {"disponible": False, "motivo": f"no hay datos de {cfg['ruta_id']} en {cfg['mes']}"})
    # MICROBUS
    cm = p["microbus"]
    cl = res["clases"]
    sel = cl[(cl["ruta_id"] == cm["ruta_id"]) & (cl["clase_vehiculo"] == cm["clase"])].sort_values("anio")
    h["microbus"] = (
        {"disponible": True, "ruta_id": cm["ruta_id"], "clase": cm["clase"],
         "pct_por_anio": {str(int(a)): _py(v) for a, v in zip(sel["anio"], sel["pct"])}}
        if len(sel)
        else {"disponible": False, "motivo": f"no hay {cm['clase']} en {cm['ruta_id']}"}
    )
    # asimetría de clases
    ca = p["asimetria_clases"]["rutas"]
    sub = cl[cl["ruta_id"].isin(ca)]
    h["asimetria_clases"] = (
        {"disponible": True, "rutas": ca,
         "pct_por_ruta_anio_clase": [{k: _py(v) for k, v in r.items()} for r in sub[sub["pct"] > 0].to_dict("records")]}
        if len(sub)
        else {"disponible": False, "motivo": f"no hay datos de {ca}"}
    )
    # consistencia del perfil mensual entre los dos primeros años completos (evidencia de un ciclo anual repetible)
    pm = res["perfil_mensual"]
    comp = pm[pm["anio_completo"]]
    anios = sorted(comp["anio"].unique())
    cons: dict[str, Any] = {"anios": [int(a) for a in anios[:2]], "corr_por_ruta": {}}
    if len(anios) >= 2:
        for ruta, g in comp.groupby("ruta_id"):
            a = g[g["anio"] == anios[0]].set_index("mes")["razon_vs_media_anual"]
            b = g[g["anio"] == anios[1]].set_index("mes")["razon_vs_media_anual"]
            cons["corr_por_ruta"][ruta] = _py(float(np.corrcoef(a.reindex(range(1, 13)), b.reindex(range(1, 13)))[0, 1]))
    h["consistencia_anual"] = cons
    # escala entre rutas y entre sentidos (media diaria de junio-diciembre del último año completo)
    ten = res["tendencia"]
    ult = int(ten["anio"].max())
    esc = ten[ten["anio"] == ult][["ruta_id", "media_jun_dic"]].dropna()
    h["escala_entre_rutas"] = {
        "anio": ult, "descripcion": "Media diaria de pasajeros de junio a diciembre",
        "por_ruta": {r.ruta_id: _py(r.media_jun_dic) for r in esc.itertuples()},
    }
    return h


# ---------------------------------------------------------------------------------------------- resultados
def calcular_resultados(diaria: pd.DataFrame, detalle: pd.DataFrame, marcas: pd.DataFrame,
                        calendario: pd.DataFrame | None, p: dict) -> dict:
    """Calcula todas las tablas y cifras de las secciones 3-6 (sin escribir nada)."""
    inicio = p["inicio_analisis"]
    comp, resumen = descomposicion(diaria, inicio)
    res: dict[str, Any] = {
        "params": p,
        "serie": _serie_marcada(diaria, marcas),
        "objetivo": tabla_objetivo(diaria, marcas),
        "transito_anio": proporcion_transito(detalle),
        "transito_mes": transito_mensual(detalle),
        "clases": composicion_clases(detalle),
        "perfil_semanal": perfil_semanal(diaria, inicio),
        "perfil_mensual": perfil_mensual(diaria, inicio),
        "tendencia": tendencia_anual(diaria, inicio),
        "descomposicion": comp,
        "descomposicion_resumen": resumen,
        "calendario": calendario,
        "efectos": {},
        "calendario_faltan": [],
    }
    if calendario is not None:
        agregar_efectos_calendario(res, diaria, calendario, p)
    res["hallazgos"] = calcular_hallazgos(res, p)
    return res


def _efectos_todos(res: dict) -> pd.DataFrame:
    partes = [df for df in res["efectos"].values() if len(df)]
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLUMNAS_EFECTO_CALENDARIO)


# ---------------------------------------------------------------------------------------------- escritura y main
def _csv(df: pd.DataFrame, ruta: Path) -> None:
    df.round(6).to_csv(ruta, index=False, encoding="utf-8", lineterminator="\n")


def escribir_resultados(res: dict, carpeta: str | Path) -> list[Path]:
    """Escribe las tablas y JSON de `ARCHIVOS_SALIDA` en `carpeta` (nunca ficha.json, calidad.csv ni diccionario.json)."""
    c = ruta_en_raiz(carpeta)
    c.mkdir(parents=True, exist_ok=True)
    res["serie"].to_parquet(c / "serie_marcada.parquet", index=False)
    _csv(res["objetivo"], c / "objetivo_por_ruta.csv")
    _csv(res["transito_anio"], c / "transito_por_ruta_anio.csv")
    _csv(res["transito_mes"], c / "transito_mensual.csv")
    _csv(res["clases"], c / "clases_por_ruta_anio.csv")
    _csv(res["perfil_semanal"], c / "perfil_semanal.csv")
    _csv(res["perfil_mensual"], c / "perfil_mensual.csv")
    _csv(res["tendencia"], c / "tendencia_anual.csv")
    res["descomposicion"].to_parquet(c / "descomposicion.parquet", index=False)
    _csv(res["descomposicion_resumen"], c / "descomposicion_resumen.csv")
    _csv(_efectos_todos(res), c / "efectos_calendario.csv")
    save_json(c / "hallazgos.json", res["hallazgos"])
    escribir_hipotesis(c / "hipotesis.json", construir_hipotesis(res))
    save_json(c / "implicaciones.json", construir_implicaciones(res))
    return [c / n for n in ARCHIVOS_SALIDA]


def main(cfg: dict) -> int:
    """`python run.py m1-eda --config configs/m1/datos.yaml`: secciones 3-7 de la plantilla común para M1."""
    sal = cfg["salida"]
    p = parametros(cfg)
    diaria, detalle, marcas = cargar_datos(sal["carpeta"], sal)
    ruta_cal = ruta_en_raiz(sal["carpeta"]) / "calendario.parquet"
    calendario = _fecha_ns(pd.read_parquet(ruta_cal)) if ruta_cal.exists() else None
    if calendario is None:
        print(f"m1-eda: {ruta_cal.as_posix()} no existe; hipótesis de calendario quedan pendientes ({FALTA_CALENDARIO})")
    res = calcular_resultados(diaria, detalle, marcas, calendario, p)
    if calendario is not None:
        res["calendario_sha256"] = hashlib.sha256(ruta_cal.read_bytes()).hexdigest()
    carpeta_eda = ruta_en_raiz(sal.get("eda", CARPETA_SALIDA))
    destino = escribir_resultados(res, carpeta_eda)
    print(f"m1-eda: {len(destino)} archivos en {carpeta_eda.as_posix()}")
    return 0
