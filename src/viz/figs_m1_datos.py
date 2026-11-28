"""Figuras del análisis descriptivo de M1 (CA-4, Camila): series, descomposición, perfiles, tendencia, tránsito y clases.

Lee solo `results/data/m1/eda/` (lo escribe `python run.py m1-eda`; los modelos no dibujan, núcleo §3) y guarda en
`results/figures/m1/`. `python run.py figures` llama a `generar()`; si todavía no hay resultados devuelve `[]`.
El color sigue a la ruta (o a la clase), nunca a la posición en la figura (`src/viz/paleta.py`).
"""

from __future__ import annotations

import json
import zlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.m1_demanda.eda_hipotesis import ANUAL, SEMANAL  # noqa: E402
from src.viz import paleta  # noqa: E402
from src.viz.estilo import aplicar_estilo, guardar_figura  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
CARPETA_EDA = RAIZ / "results" / "data" / "m1" / "eda"
CARPETA_FIGURAS = RAIZ / "results" / "figures" / "m1"
# Orden fijo de las seis rutas del periodo (rutas.yaml): el color depende de la ruta, no de la subtrama.
RUTAS_FIJAS = ["11001-76001", "76001-11001", "11001-15759", "15759-11001", "52001-52356", "52356-52001"]
NOMBRES = {
    "11001-76001": "Bogotá a Cali",
    "76001-11001": "Cali a Bogotá",
    "11001-15759": "Bogotá a Sogamoso",
    "15759-11001": "Sogamoso a Bogotá",
    "52001-52356": "Pasto a Ipiales",
    "52356-52001": "Ipiales a Pasto",
}
DIAS_CORTOS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
MESES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
FUENTE = "Fuente: Supertransporte (datos.gov.co eh75-8ah6), series de `data/processed/m1/`; cálculo propio."


def color_ruta(ruta_id: str) -> str:
    """Color fijo por ruta; una ruta fuera de las seis conocidas toma un color estable por su identificador."""
    if ruta_id in RUTAS_FIJAS:
        return paleta.CATEGORICA[RUTAS_FIJAS.index(ruta_id) % len(paleta.CATEGORICA)]
    return paleta.CATEGORICA[zlib.crc32(ruta_id.encode()) % len(paleta.CATEGORICA)]


def _nombre(ruta_id: str) -> str:
    return NOMBRES.get(ruta_id, ruta_id)


def _rutas(df: pd.DataFrame) -> list[str]:
    presentes = set(df["ruta_id"])
    return [r for r in RUTAS_FIJAS if r in presentes] + sorted(presentes - set(RUTAS_FIJAS))


def _bloques(fechas: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Tramos de fechas consecutivas (para sombrear los días sin registro)."""
    f = pd.to_datetime(fechas).sort_values().reset_index(drop=True)
    if f.empty:
        return []
    out, ini, prev = [], f.iloc[0], f.iloc[0]
    for x in f.iloc[1:]:
        if (x - prev).days > 1:
            out.append((ini, prev))
            ini = x
        prev = x
    out.append((ini, prev))
    return out


def _pie(fig, texto: str = FUENTE, y: float = -0.01) -> None:
    fig.text(0.01, y, texto, fontsize=8, color=paleta.TINTA_TENUE, ha="left", va="top")


# ---------------------------------------------------------------------------------------------- figuras
def fig_series(serie: pd.DataFrame, salida: Path) -> Path:
    """Series diarias de las rutas, con los días `sin_registro` sombreados y los días `anomalo` marcados."""
    rutas = _rutas(serie)
    ncol = 2
    nfil = int(np.ceil(len(rutas) / ncol))
    fig, axes = plt.subplots(nfil, ncol, figsize=(12, 2.6 * nfil), sharex=True, squeeze=False)
    for ax, ruta in zip(axes.ravel(), rutas):
        g = serie[serie["ruta_id"] == ruta].sort_values("fecha")
        ax.plot(g["fecha"], g["pasajeros"], color=color_ruta(ruta), lw=1.1)
        for ini, fin in _bloques(g.loc[g["sin_registro"], "fecha"]):
            ax.axvspan(ini - pd.Timedelta(hours=12), fin + pd.Timedelta(hours=12), color=paleta.EJE, alpha=0.6, lw=0)
        an = g[g["anomalo"]]
        ax.scatter(an["fecha"], an["pasajeros"], marker="x", s=28, color=paleta.CATEGORICA[7], zorder=3, linewidths=1.4)
        ax.set_title(_nombre(ruta), fontsize=10, loc="left")
        ax.set_ylabel("pasajeros por día")
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    handles = [
        plt.Line2D([], [], color=paleta.EJE, lw=8, alpha=0.6, label="días sin registro"),
        plt.Line2D([], [], color=paleta.CATEGORICA[7], marker="x", ls="", label="día marcado anómalo (descriptivo)"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.02))
    fig.suptitle(f"Demanda diaria de pasajeros por ruta, {serie['fecha'].min().year}-{serie['fecha'].max().year}", y=1.06,
                 fontsize=13)
    _pie(fig)
    fig.tight_layout()
    return guardar_figura(fig, salida / "m1_series_rutas.png")


def _nota_anual(comp: pd.DataFrame) -> str:
    """Advertencia del componente anual, con los ciclos y puntos por día calculados de la propia descomposición."""
    n = comp.loc[comp["ruta_id"] == comp["ruta_id"].iloc[0], "fecha"].nunique()
    ciclos = n / ANUAL
    return (f"* Componente anual periódico estimado con ~{ciclos:.1f} ciclos ({n // ANUAL}-{-(-n // ANUAL)} puntos por día del año): "
            f"no leerlo como estacionalidad confirmada; la tendencia (ventana > {ANUAL} d) no recoge la recuperación del primer año.\n"
            ).replace(".", ",", 1)


def fig_descomposicion(comp: pd.DataFrame, ruta: str, salida: Path) -> Path:
    """Observado, tendencia, componente semanal, componente anual y residuo (MSTL de log(1 + pasajeros))."""
    g = comp[comp["ruta_id"] == ruta].sort_values("fecha")
    paneles = [
        ("observado_log1p", "observado, log(1 + pasajeros)"),
        ("tendencia", "tendencia"),
        ("semanal", "estacionalidad semanal"),
        ("anual", "estacionalidad anual*"),
        ("residuo", "residuo"),
    ]
    fig, axes = plt.subplots(len(paneles), 1, figsize=(11, 8.5), sharex=True)
    for ax, (col, etiqueta) in zip(axes, paneles):
        ax.plot(g["fecha"], g[col], color=color_ruta(ruta), lw=1.1)
        ax.set_ylabel(etiqueta, fontsize=9)
        if col != "observado_log1p" and col != "tendencia":
            ax.axhline(0, color=paleta.EJE, lw=0.8)
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    inicio = g["fecha"].min().strftime("%Y-%m-%d")
    fig.suptitle(f"Descomposición MSTL (periodos {SEMANAL} y {ANUAL}) de {_nombre(ruta)}, desde {inicio}", y=0.995, fontsize=13)
    _pie(fig, _nota_anual(comp) + FUENTE)
    fig.tight_layout()
    return guardar_figura(fig, salida / f"m1_descomposicion_{ruta}.png")


def fig_perfil_semanal(ps: pd.DataFrame, salida: Path, inicio: str) -> Path:
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    for ruta in _rutas(ps):
        g = ps[ps["ruta_id"] == ruta].sort_values("dia_semana")
        ax.plot(g["dia_semana"], g["razon_vs_media_semanal"], marker="o", color=color_ruta(ruta), label=_nombre(ruta))
    ax.axhline(1.0, color=paleta.EJE, lw=1)
    ax.set_xticks(range(7), DIAS_CORTOS)
    ax.set_ylabel("media del día / media semanal")
    ax.set_title(f"Perfil semanal de la demanda por ruta (desde {inicio})")
    ax.legend(ncol=2, fontsize=9)
    _pie(fig)
    return guardar_figura(fig, salida / "m1_perfil_semanal.png")


def fig_perfil_mensual(pm: pd.DataFrame, salida: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    completos = pm[pm["anio_completo"]]
    anios = sorted(completos["anio"].unique())
    for ruta in _rutas(completos):
        g = completos[completos["ruta_id"] == ruta].groupby("mes")["razon_vs_media_anual"].mean().reindex(range(1, 13))
        ax.plot(range(1, 13), g.to_numpy(), marker="o", color=color_ruta(ruta), label=_nombre(ruta))
    ax.axhline(1.0, color=paleta.EJE, lw=1)
    ax.set_xticks(range(1, 13), MESES_CORTOS)
    ax.set_ylabel("media diaria del mes / media diaria del año")
    ax.set_title(f"Perfil mensual (promedio de los años completos: {', '.join(map(str, anios)) or 'ninguno'})")
    ax.legend(ncol=2, fontsize=9)
    _pie(fig, f"{len(anios)} años completos: la tendencia no está separada.\n" + FUENTE)
    return guardar_figura(fig, salida / "m1_perfil_mensual.png")


def fig_tendencia(ten: pd.DataFrame, salida: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=False)
    for ax, col, titulo in ((axes[0], "media_ene_abr", "enero-abril"), (axes[1], "media_jun_dic", "junio-diciembre")):
        for ruta in _rutas(ten):
            g = ten[ten["ruta_id"] == ruta].sort_values("anio").dropna(subset=[col])
            ax.plot(g["anio"], g[col], marker="o", color=color_ruta(ruta), label=_nombre(ruta))
        ax.set_xticks(sorted(ten["anio"].unique()))
        ax.set_title(f"Media diaria, {titulo}")
        ax.set_ylabel("pasajeros por día")
    axes[0].legend(fontsize=8, ncol=2)
    anios = sorted(ten["anio"].unique())
    fig.suptitle(f"Tendencia {anios[0]}-{anios[-1]} (proxy de pospandemia; 2020 no está en los datos)", y=1.02, fontsize=13)
    _pie(fig)
    fig.tight_layout()
    return guardar_figura(fig, salida / "m1_tendencia_anual.png")


def fig_transito_origen(tr: pd.DataFrame, salida: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    anios = sorted(tr["anio"].unique())
    rutas = _rutas(tr)
    ancho = 0.8 / max(len(rutas), 1)
    for i, ruta in enumerate(rutas):
        g = tr[tr["ruta_id"] == ruta].set_index("anio").reindex(anios)
        ax.bar(np.arange(len(anios)) + i * ancho, g["pct_transito"].to_numpy(), ancho, color=color_ruta(ruta), label=_nombre(ruta))
    ax.axhline(50, color=paleta.TINTA_TENUE, lw=1, ls="--")
    ax.set_xticks(np.arange(len(anios)) + 0.4 - ancho / 2, [str(a) for a in anios])
    ax.set_ylabel("% de los pasajeros en tránsito")
    ax.set_title("Proporción de pasajeros de tránsito sobre el total (origen + tránsito)")
    ax.legend(ncol=3, fontsize=8)
    _pie(fig, "Línea discontinua: tránsito = origen (50 %).\n" + FUENTE)
    return guardar_figura(fig, salida / "m1_transito_origen.png")


def fig_transito_mensual(tm: pd.DataFrame, ruta: str, mes_ref: str | None, salida: Path) -> Path:
    g = tm[tm["ruta_id"] == ruta].sort_values("mes").copy()
    g["fecha"] = pd.to_datetime(g["mes"] + "-01")
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ax.plot(g["fecha"], g["pasajeros_dia_origen"], marker="o", ms=3, color=paleta.CATEGORICA[0], label="origen")
    ax.plot(g["fecha"], g["pasajeros_dia_transito"], marker="s", ms=3, color=paleta.CATEGORICA[1], label="tránsito")
    ax.plot(g["fecha"], g["pasajeros_dia_transito_microbus"], marker="^", ms=3, color=paleta.CATEGORICA[2],
            label="tránsito, solo MICROBUS")
    if mes_ref:
        ax.axvline(pd.Timestamp(mes_ref + "-01"), color=paleta.TINTA_TENUE, ls="--", lw=1)
        ax.annotate(mes_ref, (pd.Timestamp(mes_ref + "-01"), ax.get_ylim()[1]), fontsize=8, color=paleta.TINTA_SECUNDARIA,
                    va="top", ha="left")
    ax.set_ylabel("pasajeros por día")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.set_title(f"Pasajeros por día de origen y de tránsito, {_nombre(ruta)}")
    ax.legend(fontsize=9)
    _pie(fig)
    return guardar_figura(fig, salida / "m1_transito_mensual.png")


def fig_clases(cl: pd.DataFrame, salida: Path) -> Path:
    clases = sorted(cl.loc[cl["pct"] > 0, "clase_vehiculo"].unique())
    color_clase = {c: paleta.CATEGORICA[i % len(paleta.CATEGORICA)] for i, c in enumerate(clases)}
    etiquetas = []  # (ruta, año) en el orden de las barras
    for ruta in _rutas(cl):
        etiquetas += [(ruta, anio) for anio in sorted(cl.loc[cl["ruta_id"] == ruta, "anio"].unique())]
    pct = cl.groupby(["ruta_id", "anio", "clase_vehiculo"])["pct"].sum()  # una sola pasada; falta = 0
    fig, ax = plt.subplots(figsize=(12, 4.8))
    base = np.zeros(len(etiquetas))
    for c in clases:
        vals = np.array([pct.get((r, a, c), 0.0) for r, a in etiquetas])
        ax.bar(range(len(etiquetas)), vals, bottom=base, color=color_clase[c], label=c, width=0.8)
        base += vals
    ax.set_xticks(range(len(etiquetas)), [f"{_nombre(r)}\n{a}" for r, a in etiquetas], fontsize=6.5, rotation=90)
    ax.set_ylabel("% de los pasajeros de la ruta")
    ax.set_title("Composición por clase de vehículo, por ruta y año")
    ax.legend(ncol=len(clases), fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.33))
    _pie(fig, FUENTE, y=-0.36)
    return guardar_figura(fig, salida / "m1_clases_rutas.png")


# ---------------------------------------------------------------------------------------------- orquestación
def generar(carpeta_eda: str | Path = CARPETA_EDA, salida: str | Path = CARPETA_FIGURAS) -> list[Path]:
    """Escribe las figuras de la sección 3-4 de M1 desde `results/data/m1/eda/`; `[]` si todavía no existen."""
    eda = Path(carpeta_eda)
    out = Path(salida)
    if not (eda / "serie_marcada.parquet").exists() or not (eda / "descomposicion.parquet").exists():
        return []
    aplicar_estilo()
    serie = pd.read_parquet(eda / "serie_marcada.parquet")
    serie["fecha"] = pd.to_datetime(serie["fecha"])
    comp = pd.read_parquet(eda / "descomposicion.parquet")
    comp["fecha"] = pd.to_datetime(comp["fecha"])
    csv = lambda n: pd.read_csv(eda / n)  # noqa: E731
    tm = csv("transito_mensual.csv")
    hall = json.loads((eda / "hallazgos.json").read_text(encoding="utf-8")) if (eda / "hallazgos.json").exists() else {}
    salto = hall.get("salto_transito", {})
    ruta_salto = salto.get("ruta_id") if salto.get("disponible") else None
    if ruta_salto is None or ruta_salto not in set(tm["ruta_id"]):
        ruta_salto, mes_ref = _rutas(tm)[0], None
    else:
        mes_ref = salto.get("mes_referencia")
    rutas = [
        fig_series(serie, out),
        *[fig_descomposicion(comp, r, out) for r in _rutas(comp)],
        fig_perfil_semanal(csv("perfil_semanal.csv"), out, comp["fecha"].min().strftime("%Y-%m-%d")),
        fig_perfil_mensual(csv("perfil_mensual.csv"), out),
        fig_tendencia(csv("tendencia_anual.csv"), out),
        fig_transito_origen(csv("transito_por_ruta_anio.csv"), out),
        fig_transito_mensual(tm, ruta_salto, mes_ref, out),
        fig_clases(csv("clases_por_ruta_anio.csv"), out),
    ]
    return rutas
