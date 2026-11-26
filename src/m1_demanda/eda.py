"""M1 — análisis descriptivo, secciones 3-7 de la plantilla común (núcleo §5.12; CA-4, Camila).

`python run.py m1-eda --config configs/m1/datos.yaml` lee `data/processed/m1/` y escribe en `results/data/m1/eda/`
tablas CSV/parquet y tres JSON (`hallazgos.json`, `hipotesis.json`, `implicaciones.json`). Las secciones 1-2
(`ficha.json`, `calidad.csv`, `diccionario.json`) son de Daniel (DA-4) y este módulo NO las toca. Los modelos no
dibujan: las figuras salen de `src/viz/figs_m1_datos.py` leyendo estos archivos.

Reglas que respeta:
- Todo es DESCRIPTIVO. Las marcas `anomalo` / `sin_registro` y las ventanas centradas miran toda la serie (núcleo §5.1):
  aquí solo se cuentan o se usan para describir, nunca producen una variable de entrada de un modelo.
- Ninguna fecha de festivo, puente, temporada escolar ni Semana Santa se escribe aquí. Si existe
  `data/processed/m1/calendario.parquet` (CA-1, núcleo §5.2) se usa; si no, esas hipótesis quedan `pendiente` con
  `resultado` = «falta el calendario de CA-1».
- Los veredictos son `pendiente` hasta modelar (§5.12, sección 7): el resultado descriptivo va en `resultado`/`evidencia`.

Parámetros propuestos para un bloque `eda:` de `configs/m1/datos.yaml` (el archivo es de Daniel; mientras no exista el
bloque se usan `PARAMETROS_POR_DEFECTO`): ver ese diccionario.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.comun.eda import escribir_hipotesis
from src.comun.results import save_json

# ---------------------------------------------------------------------------------------------- constantes
PARAMETROS_POR_DEFECTO: dict[str, Any] = {
    # La descomposición y los perfiles arrancan aquí para no contaminar con mayo-2021 (núcleo §5.1, Daniel 24-nov).
    "inicio_analisis": "2021-06-01",
    # Periodos del MSTL: semanal y anual (Anexo, M1 figuras mínimas).
    "periodos": [7, 365],
    # Efecto de calendario: se compara cada día marcado con el mismo día de la semana a ±ventana días sin marca.
    "ventana_calendario_dias": 42,
    "min_vecinos_calendario": 2,
    # Hallazgos de la spec de Camila §3.0 (rutas y fechas por parámetro, no quemadas en las funciones).
    "salto_transito": {"ruta_id": "11001-15759", "mes": "2022-11", "meses_comparacion": 6},
    "microbus": {"ruta_id": "11001-76001", "clase": "MICROBUS", "anio": 2023},
    "asimetria_clases": {"rutas": ["52001-52356", "52356-52001"]},
}

REGLAS = ("despachos_sin_pasajeros", "caida_robusta", "pico_robusto", "pasajeros_por_despacho_bajo")
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]
COLUMNAS_CALENDARIO = {  # hipótesis → columna de calendario.parquet (núcleo §5.2)
    "festivos y puentes": ("festivo", "puente"),
    "vacaciones escolares": ("vacaciones_escolares",),
    "Semana Santa": ("semana_santa",),
}
FALTA_CALENDARIO = "falta el calendario de CA-1"
CARPETA_SALIDA = "results/data/m1/eda"

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
COLUMNAS_EFECTO_CALENDARIO = ["ruta_id", "columna", "n_dias", "razon_media", "razon_mediana", "razon_min", "razon_max"]

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


def _fecha(df: pd.DataFrame) -> pd.DataFrame:
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
    c = Path(carpeta)
    s = salida or {}
    diaria = _fecha(pd.read_parquet(c / s.get("diaria", "demanda_diaria.parquet")))
    detalle = _fecha(pd.read_parquet(c / s.get("detalle", "demanda_detalle.parquet")))
    marcas = _fecha(pd.read_parquet(c / s.get("marcas", "marcas_anomalos.parquet")))
    return diaria, detalle, marcas


def _serie_marcada(diaria: pd.DataFrame, marcas: pd.DataFrame) -> pd.DataFrame:
    base = _fecha(diaria)[["ruta_id", "fecha", "pasajeros", "despachos", "sin_registro", "anomalo"]]
    m = _fecha(marcas)
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
            "minimo": int(con["pasajeros"].min()),
            "maximo": int(con["pasajeros"].max()),
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
    d = _fecha(detalle)
    d["anio"] = d["fecha"].dt.year
    p = d.pivot_table(index=["ruta_id", "anio"], columns="tipo_despacho", values=["pasajeros", "despachos"],
                      aggfunc="sum", fill_value=0)
    out = pd.DataFrame(index=p.index)
    for tipo, nombre in (("ORIGEN", "origen"), ("TRANSITO", "transito")):
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
    d = _fecha(detalle)
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
    d = _fecha(detalle)
    d["mes"] = d["fecha"].dt.strftime("%Y-%m")
    filas = []
    for (ruta, mes), g in d.groupby(["ruta_id", "mes"], sort=True):
        dias = int(g["fecha"].nunique())
        o, t = g[g["tipo_despacho"] == "ORIGEN"], g[g["tipo_despacho"] == "TRANSITO"]
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
    d = _fecha(diaria)
    return d[(d["fecha"] >= pd.Timestamp(inicio)) & (~d["sin_registro"])]


def perfil_semanal(diaria: pd.DataFrame, inicio: str) -> pd.DataFrame:
    """Perfil por día de la semana (0 = lunes) desde `inicio`, sin días `sin_registro`.

    `razon_vs_media_semanal` = media del día / promedio de las siete medias; `razon_mediana` ídem con medianas (los
    anómalos se dejan: la mediana los amortigua y así se ve cuánto pesan).
    """
    d = _validos(diaria, inicio)
    d["dia_semana"] = d["fecha"].dt.day_of_week
    g = d.groupby(["ruta_id", "dia_semana"])["pasajeros"].agg(n_dias="size", media="mean", mediana="median").reset_index()
    g["razon_vs_media_semanal"] = g["media"] / g.groupby("ruta_id")["media"].transform("mean")
    g["razon_mediana"] = g["mediana"] / g.groupby("ruta_id")["mediana"].transform("mean")
    g["dia"] = g["dia_semana"].map(lambda i: DIAS[i])
    return g[COLUMNAS_PERFIL_SEMANAL].sort_values(["ruta_id", "dia_semana"]).reset_index(drop=True)


def perfil_mensual(diaria: pd.DataFrame, inicio: str) -> pd.DataFrame:
    """Media diaria por ruta, año y mes desde `inicio` (sin `sin_registro`) y su razón con la media diaria del año.

    La razón solo se calcula en años con los 12 meses (`anio_completo`); con los años actuales son 2022 y 2023, así
    que el perfil anual se apoya en dos ciclos como máximo.
    """
    d = _validos(diaria, inicio)
    d["anio"], d["mes"] = d["fecha"].dt.year, d["fecha"].dt.month
    g = d.groupby(["ruta_id", "anio", "mes"])["pasajeros"].agg(n_dias="size", media_diaria="mean").reset_index()
    meses = g.groupby(["ruta_id", "anio"])["mes"].transform("nunique")
    g["anio_completo"] = meses == 12
    media_anio = d.groupby(["ruta_id", "anio"])["pasajeros"].mean().rename("media_anio").reset_index()
    g = g.merge(media_anio, on=["ruta_id", "anio"])
    g["razon_vs_media_anual"] = np.where(g["anio_completo"], g["media_diaria"] / g["media_anio"], np.nan)
    return g[COLUMNAS_PERFIL_MENSUAL].sort_values(["ruta_id", "anio", "mes"]).reset_index(drop=True)


def tendencia_anual(diaria: pd.DataFrame, inicio: str) -> pd.DataFrame:
    """Media diaria por ruta y año en dos ventanas comparables: enero-abril y junio-diciembre (sin `sin_registro`).

    La ventana de junio-diciembre arranca en `inicio` en 2021 (mayo-2021 casi vacío); se compara contra el año previo.
    Es el proxy de pospandemia: la caída de 2020 no está en los datos (núcleo §5.1).
    """
    d = _fecha(diaria)
    d = d[~d["sin_registro"]].copy()
    d["anio"], d["mes"] = d["fecha"].dt.year, d["fecha"].dt.month
    ini = pd.Timestamp(inicio)
    ene_abr = d[d["mes"].between(1, 4)].groupby(["ruta_id", "anio"])["pasajeros"].mean().rename("media_ene_abr")
    jun_dic = d[(d["mes"] >= 6) & (d["fecha"] >= ini)].groupby(["ruta_id", "anio"])["pasajeros"].mean().rename("media_jun_dic")
    t = pd.concat([ene_abr, jun_dic], axis=1).reset_index().sort_values(["ruta_id", "anio"])
    for col, nueva in (("media_ene_abr", "variacion_pct_ene_abr"), ("media_jun_dic", "variacion_pct_jun_dic")):
        t[nueva] = 100.0 * (t[col] / t.groupby("ruta_id")[col].shift(1) - 1.0)
    return t[COLUMNAS_TENDENCIA].reset_index(drop=True)


def descomposicion(diaria: pd.DataFrame, inicio: str, periodos: tuple[int, int] | list[int] = (7, 365)) -> tuple[pd.DataFrame, pd.DataFrame]:
    """MSTL (statsmodels) de log(1 + pasajeros) con periodos semanal y anual, por ruta, desde `inicio`.

    - Se trabaja en log(1 + y): el componente semanal y el anual quedan como efectos multiplicativos (la amplitud
      crece con el nivel de la ruta).
    - Los días `sin_registro` dentro de la ventana no son demanda cero: se marcan como faltantes y se interpolan
      linealmente en log(1 + y) para poder descomponer; el número de días imputados se reporta (con `inicio` en
      2021-06-01 deberían ser 0).
    - Los días `anomalo` se dejan tal cual; el STL interno es robusto (`robust=True`) y los pondera menos.
    - Se exigen al menos dos ciclos del periodo más largo (`2 × 365 = 730` observaciones).

    Devuelve (componentes por ruta y día, resumen por ruta). Observado = tendencia + semanal + anual + residuo.
    """
    from statsmodels.tsa.seasonal import MSTL

    periodos = tuple(int(p) for p in periodos)
    nombres = {7: "semanal", 365: "anual"}
    if sorted(periodos) != [7, 365]:
        raise ValueError(f"descomposicion: solo se soportan los periodos 7 y 365; recibido {periodos}")
    d = _fecha(diaria)
    d = d[d["fecha"] >= pd.Timestamp(inicio)]
    comps, resumen = [], []
    for ruta, g in d.groupby("ruta_id", sort=True):
        g = g.sort_values("fecha").set_index("fecha")
        rejilla = pd.date_range(g.index.min(), g.index.max(), freq="D")
        if len(rejilla) != len(g):
            raise ValueError(f"{ruta}: la serie tiene huecos de fecha (contrato §5.1: sin huecos)")
        if len(g) < 2 * max(periodos):
            raise ValueError(
                f"{ruta}: {len(g)} observaciones desde {inicio}; MSTL con periodo {max(periodos)} exige al menos "
                f"{2 * max(periodos)} (dos ciclos)"
            )
        y = np.log1p(g["pasajeros"].astype(float))
        sin = g["sin_registro"].to_numpy()
        y[sin] = np.nan
        y = y.interpolate(limit_direction="both")
        res = MSTL(y, periods=list(periodos), iterate=2, stl_kwargs={"robust": True}).fit()
        seas = res.seasonal
        sem = seas[f"seasonal_{7}"].to_numpy()
        anu = seas[f"seasonal_{365}"].to_numpy()
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
    del nombres
    return (pd.DataFrame(pd.concat(comps, ignore_index=True), columns=COLUMNAS_DESCOMPOSICION),
            pd.DataFrame(resumen, columns=COLUMNAS_RESUMEN_DESCOMPOSICION))


def efecto_calendario(diaria: pd.DataFrame, calendario: pd.DataFrame, columna: str, inicio: str,
                      ventana_dias: int = 42, min_vecinos: int = 2) -> pd.DataFrame:
    """Razón entre la demanda de los días con `columna` verdadera y la del MISMO día de la semana a ±`ventana_dias`.

    La referencia son los días vecinos sin marca de esa columna, con registro y no anómalos (el día marcado se conserva
    aunque esté marcado `anomalo`, para no ocultar su efecto). Un día se omite si tiene menos de `min_vecinos`
    vecinos. Descriptivo: la ventana mira a ambos lados de la fecha, así que no es una variable de modelo.
    """
    if columna not in calendario.columns:
        raise KeyError(columna)
    d = _fecha(diaria)
    cal = _fecha(calendario)[["fecha", columna]].rename(columns={columna: "_marca"})
    d = d.merge(cal, on="fecha", how="left")
    d["_marca"] = d["_marca"].fillna(False).astype(bool)
    d = d[(d["fecha"] >= pd.Timestamp(inicio)) & (~d["sin_registro"])]
    filas = []
    for ruta, g in d.groupby("ruta_id", sort=True):
        g = g.sort_values("fecha").reset_index(drop=True)
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
            filas.append({"ruta_id": ruta, "columna": columna, "n_dias": len(r), "razon_media": r.mean(),
                          "razon_mediana": float(np.median(r)), "razon_min": r.min(), "razon_max": r.max()})
    return pd.DataFrame(filas, columns=COLUMNAS_EFECTO_CALENDARIO)


# ---------------------------------------------------------------------------------------------- hallazgos
def calcular_hallazgos(res: dict, p: dict) -> dict:
    """Cifras de los hallazgos de la spec §3.0 (rutas y fechas salen de `p`); no disponible si la ruta no está."""
    h: dict[str, Any] = {}
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
         "pct_por_anio": {int(a): _py(v) for a, v in zip(sel["anio"], sel["pct"])}}
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
    comp, resumen = descomposicion(diaria, inicio, p["periodos"])
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
        for nombre, cols in COLUMNAS_CALENDARIO.items():
            for col in cols:
                if col not in calendario.columns:
                    res["calendario_faltan"].append(col)
                    continue
                res["efectos"][col] = efecto_calendario(diaria, calendario, col, inicio, p["ventana_calendario_dias"],
                                                        p["min_vecinos_calendario"])
    res["hallazgos"] = calcular_hallazgos(res, p)
    return res


def _efectos_todos(res: dict) -> pd.DataFrame:
    partes = [df for df in res["efectos"].values() if len(df)]
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLUMNAS_EFECTO_CALENDARIO)


# ---------------------------------------------------------------------------------------------- sección 5 y 7
def _hipotesis(id_: int, enunciado: str, justificacion: str, esperada: str, figura: str, resultado: str, evidencia: str) -> dict:
    return {
        "id": f"H-M1-{id_}",
        "enunciado": enunciado,
        "justificacion": justificacion,
        "evidencia_esperada": esperada,
        "figura_o_tabla": figura,
        "resultado": resultado,
        "veredicto": "pendiente",  # §5.12: se cierra después de modelar
        "evidencia": evidencia,
    }


def _resultado_calendario(res: dict, nombre: str) -> tuple[str, str]:
    """(resultado, evidencia) de una hipótesis de calendario: falta el calendario, falta columna, sin días o cifras."""
    if res["calendario"] is None:
        return FALTA_CALENDARIO, "data/processed/m1/calendario.parquet no existe (CA-1 pendiente)"
    cols = COLUMNAS_CALENDARIO[nombre]
    faltan = [c for c in cols if c in res["calendario_faltan"]]
    if faltan:
        return f"falta la columna {', '.join(faltan)} en calendario.parquet", "calendario.parquet sin esa columna"
    partes, vacias = [], []
    for c in cols:
        e = res["efectos"][c]
        if e.empty:
            vacias.append(c)
            continue
        ponderada = float(np.average(e["razon_mediana"], weights=e["n_dias"]))
        partes.append(
            f"{c}: {int(e['n_dias'].max())} días marcados por ruta; razón mediana contra el mismo día de la semana "
            f"±{res['params']['ventana_calendario_dias']} días entre {_n(e['razon_mediana'].min())} y "
            f"{_n(e['razon_mediana'].max())} según ruta (promedio ponderado {_n(ponderada)})"
        )
    if vacias:
        partes.append(f"sin días marcados o sin vecinos suficientes en: {', '.join(vacias)}")
    return "; ".join(partes), "results/data/m1/eda/efectos_calendario.csv"


def construir_hipotesis(res: dict) -> list[dict]:
    """H-M1-1…10 (sección 5). Todas con veredicto `pendiente`; la evidencia descriptiva va en `resultado`."""
    p = res["params"]
    ps, pm, ten = res["perfil_semanal"], res["perfil_mensual"], res["tendencia"]
    rs, tr, hall = res["descomposicion_resumen"], res["transito_anio"], res["hallazgos"]
    inicio = p["inicio_analisis"]

    # 1. día de la semana
    partes = []
    for ruta, g in ps.groupby("ruta_id"):
        pico, valle = g.loc[g["media"].idxmax()], g.loc[g["media"].idxmin()]
        partes.append(f"{ruta}: pico {pico['dia']} ({_n(pico['razon_vs_media_semanal'])}×), valle {valle['dia']} "
                      f"({_n(valle['razon_vs_media_semanal'])}×)")
    h1 = (
        f"Desde {inicio}, razón día/media semanal por ruta: " + "; ".join(partes)
        + f". Fuerza de la estacionalidad semanal (MSTL sobre log(1+y)) entre {_n(rs['fuerza_semanal'].min())} y "
        f"{_n(rs['fuerza_semanal'].max())}; razón máx/mín del ciclo semanal entre {_n(rs['razon_max_min_semanal'].min())} y "
        f"{_n(rs['razon_max_min_semanal'].max())}."
    )

    # 2-4. calendario
    r2, e2 = _resultado_calendario(res, "festivos y puentes")
    r3, e3 = _resultado_calendario(res, "vacaciones escolares")
    r4, e4 = _resultado_calendario(res, "Semana Santa")

    # 5. fin de año (por fecha, sin calendario externo)
    comp = pm[pm["anio_completo"]]
    por_mes = comp[comp["mes"].isin([1, 12])].groupby(["ruta_id", "mes"])["razon_vs_media_anual"].mean().unstack()
    if {1, 12} <= set(por_mes.columns) and len(por_mes):
        anios = sorted(comp["anio"].unique())
        h5 = (
            f"Media diaria del mes / media diaria del año (años completos {', '.join(map(str, anios))}, promedio de años): "
            f"diciembre entre {_n(por_mes[12].min())} y {_n(por_mes[12].max())}; enero entre {_n(por_mes[1].min())} y "
            f"{_n(por_mes[1].max())} según ruta. Sin separar tendencia, ni días concretos (calendario de CA-1)."
        )
    else:
        h5 = "no hay años completos para comparar diciembre y enero"

    # 6. pospandemia
    var_jd = ten.dropna(subset=["variacion_pct_jun_dic"])
    var_ea = ten.dropna(subset=["variacion_pct_ene_abr"])
    if len(var_jd):
        partes6 = []
        for anio, g in var_jd.groupby("anio"):
            partes6.append(f"jun-dic {anio} vs {anio - 1}: de {_n(g['variacion_pct_jun_dic'].min(), 1)} % a "
                           f"{_n(g['variacion_pct_jun_dic'].max(), 1)} % según ruta")
        for anio, g in var_ea.groupby("anio"):
            partes6.append(f"ene-abr {anio} vs {anio - 1}: de {_n(g['variacion_pct_ene_abr'].min(), 1)} % a "
                           f"{_n(g['variacion_pct_ene_abr'].max(), 1)} %")
        h6 = "Variación de la media diaria entre ventanas equivalentes: " + "; ".join(partes6) + ". 2020 no está en los datos."
    else:
        h6 = "no hay dos años comparables"

    # 7. tránsito pesa tanto como origen
    pesados = tr[tr["pasajeros_transito"] > 0]
    r7 = (
        f"Proporción de tránsito sobre el total por ruta y año: entre {_n(tr['pct_transito'].min(), 1)} % y "
        f"{_n(tr['pct_transito'].max(), 1)} %; en {int((tr['pct_transito'] > 50).sum())} de {len(tr)} combinaciones ruta-año "
        f"el tránsito supera al origen. Casi sin tránsito (< 6 %): "
        + (", ".join(sorted(set(tr.loc[tr['pct_transito'] < 6, 'ruta_id']))) or "ninguna")
        + f". Con tránsito > 0: {len(pesados)} filas."
    )

    # 8. salto del tránsito
    s = hall["salto_transito"]
    r8 = (
        f"{s['ruta_id']}: tránsito/día {_n(s['transito_dia_antes'], 0)} ({s['meses_antes'][0]} a {s['meses_antes'][1]}) → "
        f"{_n(s['transito_dia_despues'], 0)} ({s['meses_despues'][0]} a {s['meses_despues'][1]}), razón {_n(s['razon_transito'])}; "
        f"origen/día {_n(s['origen_dia_antes'], 0)} → {_n(s['origen_dia_despues'], 0)} (razón {_n(s['razon_origen'])}); "
        f"despachos de tránsito/día {_n(s['despachos_transito_dia_antes'], 1)} → {_n(s['despachos_transito_dia_despues'], 1)}; "
        f"MICROBUS en tránsito/día {_n(s['microbus_transito_dia_antes'], 0)} → {_n(s['microbus_transito_dia_despues'], 0)}."
        if s.get("disponible")
        else s["motivo"]
    )

    # 9. composición por clase
    m, a = hall["microbus"], hall["asimetria_clases"]
    r9 = []
    if m.get("disponible"):
        r9.append(f"{m['clase']} en {m['ruta_id']}, % de pasajeros por año: "
                  + ", ".join(f"{k}: {_n(v, 1)}" for k, v in m["pct_por_anio"].items()))
    else:
        r9.append(m["motivo"])
    if a.get("disponible"):
        for ruta in a["rutas"]:
            f = [x for x in a["pct_por_ruta_anio_clase"] if x["ruta_id"] == ruta and x["anio"] == max(y["anio"] for y in a["pct_por_ruta_anio_clase"])]
            if f:
                r9.append(f"{ruta} (último año): " + ", ".join(f"{x['clase_vehiculo']} {_n(x['pct'], 1)} %"
                                                              for x in sorted(f, key=lambda x: -x['pct'])[:4]))
    else:
        r9.append(a["motivo"])

    # 10. escala y sentido
    esc = hall["escala_entre_rutas"]
    r10 = (f"Media diaria jun-dic {esc['anio']} por ruta: "
           + "; ".join(f"{k}: {_n(v, 0)}" for k, v in esc["por_ruta"].items()) + ".")

    ev = "results/data/m1/eda/"
    return [
        _hipotesis(1, "La demanda depende del día de la semana: el perfil semanal tiene una razón máximo/mínimo claramente "
                      "mayor que 1 en las seis rutas, y esa estructura se repite cada siete días.",
                   "Viaje intermunicipal por trabajo, estudio y ocio concentra la demanda en ciertos días (supuesto a contrastar).",
                   "Razón máx/mín del perfil semanal > 1,2 en las seis rutas y fuerza de estacionalidad semanal alta; "
                   "se refutaría con perfiles planos.",
                   "perfil_semanal.csv; descomposicion_resumen.csv; figuras m1_perfil_semanal.png y m1_descomposicion_*.png",
                   h1, ev + "perfil_semanal.csv; " + ev + "descomposicion_resumen.csv"),
        _hipotesis(2, "Los festivos y los puentes (festivo trasladado a lunes) aumentan la demanda de salida y retorno "
                      "respecto del mismo día de la semana en días vecinos.",
                   "Los días de descanso prolongado concentran viajes; calendario conocible con meses de antelación (regla 0.9).",
                   "Razón mediana > 1 en días marcados, contra el mismo día de la semana ±42 días sin marca.",
                   "efectos_calendario.csv", r2, e2),
        _hipotesis(3, "Las vacaciones escolares elevan la demanda frente a los mismos días de la semana fuera de ellas.",
                   "Calendario escolar como determinante de viajes familiares (supuesto a contrastar).",
                   "Razón mediana > 1 en días de vacaciones escolares (ventana ±42 días).",
                   "efectos_calendario.csv", r3, e3),
        _hipotesis(4, "Semana Santa modifica la demanda respecto del mismo día de la semana en semanas vecinas, con un "
                      "patrón distinto entre días de la semana (salida y regreso).",
                   "Festividad móvil con puentes largos; su fecha cambia cada año, por eso se toma del calendario.",
                   "Razón mediana ≠ 1 en días de Semana Santa, con signos distintos por día.",
                   "efectos_calendario.csv", r4, e4),
        _hipotesis(5, "Diciembre y enero tienen una demanda diaria superior a la media del año en las rutas con mayor "
                      "tránsito de pasajeros, y esa temporada no se explica solo por la tendencia.",
                   "Fin de año como temporada alta (viajes de vacaciones y reuniones familiares); se mide por mes, sin "
                   "calendario externo.",
                   "Razón mes/año > 1 en diciembre o enero en la mayoría de las rutas; refutada si todas quedan por debajo de 1.",
                   "perfil_mensual.csv; figura m1_perfil_mensual.png", h5, ev + "perfil_mensual.csv"),
        _hipotesis(6, "La demanda de 2021 a 2023 crece en todas las rutas respecto del año previo (recuperación posterior a "
                      "la pandemia, medida como tendencia).",
                   "La caída de 2020 no está en los datos; solo se observa la tendencia 2021-2023, que mezcla recuperación "
                   "y cambios de reporte (núcleo §5.1).",
                   "Variación positiva de la media de jun-dic 2022 vs 2021 y 2023 vs 2022 en las seis rutas.",
                   "tendencia_anual.csv; figuras m1_tendencia_anual.png y m1_series_rutas.png", h6, ev + "tendencia_anual.csv"),
        _hipotesis(7, "En las rutas desde y hacia Bogotá el tránsito (pasajeros que suben en terminales intermedias) pesa "
                      "tanto como el origen; en Pasto-Ipiales casi no hay tránsito.",
                   "El conjunto registra pasajeros por terminal y tipo de despacho; la serie suma origen y tránsito (núcleo §5.1).",
                   "Proporción de tránsito entre 40 % y 70 % en los corredores de Bogotá y < 6 % en Pasto-Ipiales.",
                   "transito_por_ruta_anio.csv; figura m1_transito_origen.png", r7, ev + "transito_por_ruta_anio.csv"),
        _hipotesis(8, "La demanda de tránsito de Bogotá→Sogamoso cambia de régimen desde noviembre de 2022 (el origen no).",
                   "Auditoría de DA-3: salto del tránsito con despachos casi constantes; causa no verificada (¿cambio de reporte?).",
                   "Razón tránsito después/antes claramente mayor que 1 con razón de origen cercana a 1.",
                   "transito_mensual.csv; hallazgos.json; figura m1_transito_mensual.png", r8, ev + "transito_mensual.csv; " + ev + "hallazgos.json"),
        _hipotesis(9, "La composición por clase de vehículo cambia con el tiempo y entre sentidos: MICROBUS desaparece de "
                      "Bogotá→Cali en 2023 y Pasto-Ipiales es asimétrica entre ida y regreso.",
                   "Afecta capacidad por clase y dimensionamiento de flota (CA-3); puede ser cambio de reporte.",
                   "Participación de MICROBUS = 0 en 2023 en 11001-76001; clases distintas en cada sentido de Pasto-Ipiales.",
                   "clases_por_ruta_anio.csv; figura m1_clases_rutas.png", " | ".join(r9), ev + "clases_por_ruta_anio.csv"),
        _hipotesis(10, "Las rutas difieren en escala entre sí y entre sentidos, así que un modelo único exige normalizar por ruta.",
                   "Volúmenes distintos por corredor y asimetría ida/regreso (Anexo, limitaciones).",
                   "Razón entre la mayor y la menor media diaria de las seis rutas claramente mayor que 1.",
                   "objetivo_por_ruta.csv; figura m1_series_rutas.png", r10, ev + "objetivo_por_ruta.csv; " + ev + "tendencia_anual.csv"),
    ]


# ---------------------------------------------------------------------------------------------- sección 6
def construir_implicaciones(res: dict) -> dict:
    """Implicaciones para el modelado (sección 6) con la cifra que respalda cada una. Todas [PROPUESTO] (Camila decide)."""
    obj, rs, ten = res["objetivo"], res["descomposicion_resumen"], res["tendencia"]
    h = res["hallazgos"]
    s = h["salto_transito"]
    sin_reg = int(obj["sin_registro"].sum())
    var = ten.dropna(subset=["variacion_pct_jun_dic"])
    salto = (f"{s['ruta_id']} razón de tránsito {_n(s['razon_transito'])} entre {s['meses_antes'][1]} y {s['meses_despues'][0]}"
             if s.get("disponible") else s["motivo"])
    return {
        "ventana": {
            "decision": "Ventanas de rezagos múltiplos de 7 días (mínimo 28) y una variante de 365 para la estacionalidad anual; "
                        "el horizonte de 30 días obliga a pronosticar directo o recursivo sin covariables observadas.",
            "base": f"Estacionalidad semanal con fuerza {_n(rs['fuerza_semanal'].min())}-{_n(rs['fuerza_semanal'].max())} (MSTL) "
                    f"y anual con {_n(rs['fuerza_anual'].min())}-{_n(rs['fuerza_anual'].max())}, sobre {int(rs['observaciones'].min())} días.",
            "estado": "[PROPUESTO]",
        },
        "variables_calendario": {
            "decision": "Día de la semana y mes por fecha; festivo, puente, Semana Santa y vacaciones escolares solo desde "
                        "calendario.parquet (CA-1), conocibles 30 días antes.",
            "base": "H-M1-1 y H-M1-5 se evalúan por fecha; H-M1-2, 3 y 4 dependen del calendario: "
                    + ("pendientes (falta CA-1)." if res["calendario"] is None else "evaluadas con calendario.parquet."),
            "estado": "[PROPUESTO]",
        },
        "perdida_conteo": {
            "decision": "Pérdida de conteo (Poisson o binomial negativa) o MAE sobre log1p; cuantil alto con pérdida pinball. "
                        "Enmascarar `sin_registro` y `despachos_sin_pasajeros`.",
            "base": f"Variable entera ≥ 0 con media diaria entre {_n(obj['media_diaria'].min(), 0)} y {_n(obj['media_diaria'].max(), 0)} "
                    f"pasajeros; {int(obj['ceros'].sum())} ceros, de los cuales {sin_reg} son `sin_registro`.",
            "estado": "[PROPUESTO]",
        },
        "particion": {
            "decision": "Partición temporal con origen rodante desde 2021-06-01, último origen anclado al 2023-12-01 para que "
                        "el test cubra el fin de año; escalas de normalización solo con train.",
            "base": ("Variación de la media jun-dic entre años de " + _n(var["variacion_pct_jun_dic"].min(), 1) + " % a "
                     + _n(var["variacion_pct_jun_dic"].max(), 1) + " %: hay tendencia, así que ninguna partición aleatoria.")
            if len(var) else "sin años comparables",
            "estado": "[PROPUESTO]",
        },
        "cambio_de_regimen": {
            "decision": "Indicadora de régimen solo con datos de train o ventana reciente para el escalado; reportar el MASE "
                        "de 11001-15759 con y sin el cambio.",
            "base": salto,
            "estado": "[PROPUESTO]",
        },
        "mayo_2021": {
            "decision": "Mantener la serie completa para el descriptivo con marcas; entrenar desde 2021-06-01 y no usar los ceros de "
                        "mayo-2021 como demanda.",
            "base": f"{sin_reg} días-ruta `sin_registro` (todos antes de 2021-06-01); la descomposición desde "
                    f"{res['params']['inicio_analisis']} imputó {int(rs['sin_registro_imputados'].sum())} días.",
            "estado": "[PROPUESTO]",
        },
        "transito": {
            "decision": "Modelar la serie total (origen + tránsito) como define el núcleo §5.1, pero usar despachos de ORIGEN para "
                        "flota; explorar tránsito y origen por separado como entrada auxiliar solo si se conoce 30 días antes.",
            "base": f"El tránsito supera al origen en {int((res['transito_anio']['pct_transito'] > 50).sum())} de "
                    f"{len(res['transito_anio'])} combinaciones ruta-año (pct_transito en transito_por_ruta_anio.csv).",
            "estado": "[PROPUESTO]",
        },
    }


# ---------------------------------------------------------------------------------------------- escritura y main
def _csv(df: pd.DataFrame, ruta: Path) -> None:
    df.round(6).to_csv(ruta, index=False, encoding="utf-8", lineterminator="\n")


def escribir_resultados(res: dict, carpeta: str | Path) -> list[Path]:
    """Escribe las tablas y JSON de `ARCHIVOS_SALIDA` en `carpeta` (nunca ficha.json, calidad.csv ni diccionario.json)."""
    c = Path(carpeta)
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
    ruta_cal = Path(sal["carpeta"]) / "calendario.parquet"
    calendario = _fecha(pd.read_parquet(ruta_cal)) if ruta_cal.exists() else None
    if calendario is None:
        print(f"m1-eda: {ruta_cal.as_posix()} no existe; hipótesis de calendario quedan pendientes ({FALTA_CALENDARIO})")
    res = calcular_resultados(diaria, detalle, marcas, calendario, p)
    destino = escribir_resultados(res, sal.get("eda", CARPETA_SALIDA))
    print(f"m1-eda: {len(destino)} archivos en {Path(sal.get('eda', CARPETA_SALIDA)).as_posix()}")
    return 0
