"""Figuras del análisis descriptivo de M3 (JJ-2; núcleo §5.12 y «Figuras mínimas» del enunciado, módulo 3).

Lee SOLO ``results/data/m3/eda/`` (lo que escribe ``python run.py m3-eda --config configs/m3/eda.yaml``); no lee los datos crudos
ni los procesados. Escribe en ``blog/docs/figures/m3/``:
  cola_larga.png            interacciones por usuario y por destino frente al reparto uniforme al azar (figura mínima)
  lorenz.png                curva de Lorenz por destino_id y por lugar, con la diagonal y la referencia uniforme
  preferencias_tipo.png     combinación de preferencias × tipo de destino (proporciones por fila)
  calificaciones_origen.png calificaciones 1–5 de reseñas e historial

``run.py figures`` llama ``generar()`` sin argumentos. Los datos son generados (D4): las figuras describen el conjunto, no
turistas reales.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sin ventana: también corre en CI y en la sesión sin pantalla

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from src.comun.config import load_config  # noqa: E402
from src.viz import paleta as p  # noqa: E402
from src.viz.estilo import aplicar_estilo, guardar_figura, mapa_secuencial  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / "configs" / "m3" / "eda.yaml"
COMANDO = "python run.py m3-eda --config configs/m3/eda.yaml"
NOTA_DATOS = "Datos generados (D4): describen el conjunto de Kaggle, no a turistas reales"

PIE_LORENZ = ("La banda gris es un IC 95 % puntual (percentiles del azar en cada punto de la curva), no simultánea. "
              + NOTA_DATOS)
COLOR_OBSERVADO = p.CATEGORICA[0]
COLOR_AZAR = p.TINTA_TENUE
COLOR_ORIGEN = {"resena": p.CATEGORICA[2], "historial": p.CATEGORICA[6]}
ETIQUETA_ORIGEN = {"resena": "Reseñas", "historial": "Historial"}


def _f(x: float, dec: int = 2) -> str:
    return f"{x:.{dec}f}".replace(".", ",")


def _miles(n: int) -> str:
    """Separador de miles con espacio, como en el blog («1 998»)."""
    return f"{int(n):,}".replace(",", " ")


def _coma(x: float, pos) -> str:
    """Formateador de marcas de eje con coma decimal (dos decimales)."""
    return f"{x:.2f}".replace(".", ",")


def _ejes_con_coma(*ejes) -> None:
    for eje in ejes:
        eje.set_major_formatter(FuncFormatter(_coma))


def texto_linea_base(coin: dict, filas: list[dict]) -> str:
    """Pie de ``preferencias_tipo.png``: línea base exacta leída de ``coincidencia_preferencias.json`` (no tecleada).

    ``filas``: una por combinación, con ``combinacion``, ``n_recuadradas`` y ``linea_base`` (la de esa fila). Solo se
    afirma una suma única de las celdas recuadradas si todas las filas tienen la misma línea base y el mismo número de
    celdas recuadradas.
    """
    ids = coin["ids_por_tipo"]
    total = sum(ids.values())
    fracciones = {round(v / total, 9) for v in ids.values()}
    celda = (f"cada celda tendría {_f(next(iter(fracciones)), 2)}" if len(fracciones) == 1
             else "cada celda tendría la fracción de ids de su tipo")
    bases = {round(f["linea_base"], 9) for f in filas}
    n_rec = {int(f["n_recuadradas"]) for f in filas}
    if len(bases) == 1 and len(n_rec) == 1:
        suma = f"y la suma de las {n_rec.pop()} recuadradas {_f(bases.pop(), 2)} (línea base exacta)."
    else:
        por_fila = "; ".join(f"{f['combinacion']}: {_f(f['linea_base'], 2)}" for f in filas)
        suma = f"y la suma de las recuadradas (línea base exacta) es, por fila: {por_fila}."
    return (f"Si el destino se eligiera al azar en el catálogo, {celda} {suma} Tasa de coincidencia observada "
            f"{_f(coin['tasa'], 3)} frente a {_f(coin['linea_base_exacta'], 3)} (línea base exacta promedio).")


def _leer_json(carpeta: Path, nombre: str) -> dict:
    ruta = carpeta / nombre
    if not ruta.is_file():
        raise FileNotFoundError(f"Falta {ruta.as_posix()}: corre primero `{COMANDO}`")
    return json.loads(ruta.read_text(encoding="utf-8"))


def _leer_csv(carpeta: Path, nombre: str) -> pd.DataFrame:
    ruta = carpeta / nombre
    if not ruta.is_file():
        raise FileNotFoundError(f"Falta {ruta.as_posix()}: corre primero `{COMANDO}`")
    return pd.read_csv(ruta)


def _pie(fig, texto: str) -> None:
    ajustado = "\n".join(textwrap.fill(linea, 105) for linea in texto.split("\n"))
    fig.text(0.5, -0.02, ajustado, ha="center", va="top", fontsize=9, color=p.TINTA_SECUNDARIA)


def fig_cola_larga(carpeta: Path, destino: Path) -> Path:
    dist = _leer_json(carpeta, "distribucion_actividad.json")
    fig, ejes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, clave, titulo, etiqueta in ((ejes[0], "usuarios", "Interacciones por usuario", "usuarios"),
                                        (ejes[1], "destinos", "Interacciones por destino", "destinos")):
        d = dist[clave]
        cats = list(d["observado"])
        x = np.arange(len(cats))
        obs = np.array([d["observado"][k] for k in cats])
        media = np.array([d["azar_media"][k] for k in cats])
        lo = np.array([d["azar_ic95"][k][0] for k in cats])
        hi = np.array([d["azar_ic95"][k][1] for k in cats])
        ax.bar(x, obs, color=COLOR_OBSERVADO, width=0.62, label="Observado")
        ax.errorbar(x, media, yerr=[np.maximum(media - lo, 0), np.maximum(hi - media, 0)], fmt="o", color=p.TINTA,
                    ecolor=p.TINTA_SECUNDARIA, capsize=4, markersize=5, linewidth=1.4,
                    label=f"Azar uniforme: media e IC {int(round(dist['nivel_ic'] * 100))} %")
        tope = float(max(obs.max(), hi.max()))
        for xi, v, h in zip(x, obs, hi):
            ax.text(xi, max(v, h) + 0.012 * tope, str(int(v)), ha="center", va="bottom", fontsize=9, color=p.TINTA_SECUNDARIA)
        ax.set_ylim(0, tope * 1.38)
        ax.set_xticks(x, cats)
        ax.set_xlabel("Número de interacciones")
        ax.set_ylabel(f"Número de {etiqueta}")
        ax.set_title(titulo)
        ax.legend(loc="upper right")
        ax.grid(axis="x", visible=False)
    fig.suptitle(f"Distribución de interacciones frente al reparto uniforme al azar ({_miles(dist['n_interacciones'])} interacciones; "
                 f"{_miles(dist['n_simulaciones'])} simulaciones)", y=1.02)
    _pie(fig, NOTA_DATOS)
    return guardar_figura(fig, destino / "cola_larga.png")


def fig_lorenz(carpeta: Path, destino: Path) -> Path:
    conc = _leer_json(carpeta, "concentracion.json")
    niveles = conc["niveles"]
    fig, ejes = plt.subplots(1, len(niveles), figsize=(5.6 * len(niveles), 5.0))
    ejes = np.atleast_1d(ejes)
    for ax, (nombre, info) in zip(ejes, niveles.items()):
        obs, az = info["observado"], info["azar_uniforme"]
        x = np.array(obs["lorenz"]["x"])
        ax.plot([0, 1], [0, 1], linestyle="--", color=p.TINTA_TENUE, linewidth=1.4, label="Igualdad perfecta")
        ax.fill_between(x, az["lorenz"]["ic95_inf"], az["lorenz"]["ic95_sup"], color=COLOR_AZAR, alpha=0.30, linewidth=0,
                        label="Azar uniforme: IC 95 % puntual")
        ax.plot(x, az["lorenz"]["media"], color=COLOR_AZAR, linewidth=1.6, label="Azar uniforme: media")
        marcador = "o" if info["n_entidades"] <= 20 else None
        ax.plot(x, obs["lorenz"]["y"], color=COLOR_OBSERVADO, marker=marcador, label="Observado")
        g = az["gini"]
        ax.set_title(f"{'Destinos (destino_id)' if nombre == 'destino_id' else 'Lugares (' + str(info['n_entidades']) + ')'}")
        ax.text(0.04, 0.95, f"Gini observado {_f(obs['gini'], 3)}\nGini del azar {_f(g['media'], 3)} "
                f"(IC 95 % {_f(g['ic95'][0], 3)}–{_f(g['ic95'][1], 3)})", transform=ax.transAxes, va="top", fontsize=9.5,
                color=p.TINTA_SECUNDARIA)
        ax.set_xlabel("Fracción acumulada de entidades (de menos a más interacciones)")
        ax.set_ylabel("Fracción acumulada de interacciones")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        _ejes_con_coma(ax.xaxis, ax.yaxis)
        ax.set_aspect("equal")
        ax.legend(loc="lower right")
    fig.suptitle("Curva de Lorenz de las interacciones frente al reparto uniforme al azar", y=1.0)
    _pie(fig, PIE_LORENZ)
    return guardar_figura(fig, destino / "lorenz.png")


def fig_preferencias_tipo(carpeta: Path, destino: Path) -> Path:
    m = _leer_csv(carpeta, "matriz_preferencias_tipo.csv")
    resumen = _leer_json(carpeta, "coincidencia_preferencias.json")
    coin = {**resumen["global"], "ids_por_tipo": resumen["ids_por_tipo"]}
    combos = sorted(m["combinacion"].unique())
    tipos = sorted(m["tipo"].unique())
    prop = m.pivot(index="combinacion", columns="tipo", values="proporcion_fila").loc[combos, tipos]
    coincide = m.pivot(index="combinacion", columns="tipo", values="coincide").loc[combos, tipos].astype(bool)
    n_fila = m.groupby("combinacion")["n_interacciones_fila"].first().loc[combos]
    fig, ax = plt.subplots(figsize=(8.6, 3.9))
    vmax = float(np.nanmax(prop.to_numpy()))
    im = ax.imshow(prop.to_numpy(), cmap=mapa_secuencial(), vmin=0, vmax=vmax, aspect="auto")
    for i in range(len(combos)):
        for j in range(len(tipos)):
            v = prop.iat[i, j]
            ax.text(j, i, _f(v, 2), ha="center", va="center", fontsize=11, color="white" if v > 0.6 * vmax else p.TINTA)
            if coincide.iat[i, j]:
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, edgecolor=p.TINTA, linewidth=2.6))
    ax.set_xticks(range(len(tipos)), tipos)
    ax.set_yticks(range(len(combos)), [f"{c}\n(n = {int(n_fila[c])})" for c in combos])
    ax.grid(False)
    for lado in ax.spines.values():
        lado.set_visible(False)
    ax.set_xlabel("Tipo de destino")
    ax.set_ylabel("Preferencias del usuario")
    ax.set_title("Tipo de destino de las interacciones, por combinación de preferencias (proporción de cada fila)")
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("Proporción de la fila")
    _ejes_con_coma(cb.ax.yaxis)
    filas = [{"combinacion": c, "n_recuadradas": int(coincide.loc[c].sum()),
              "linea_base": resumen["por_combinacion"][c]["linea_base_exacta"]} for c in combos]
    _pie(fig, "Recuadro = tipo cubierto por las preferencias (emparejamiento léxico nuestro, no de la fuente). "
              + texto_linea_base(coin, filas) + f"\n{NOTA_DATOS}.")
    return guardar_figura(fig, destino / "preferencias_tipo.png")


def fig_calificaciones_origen(carpeta: Path, destino: Path) -> Path:
    df = _leer_csv(carpeta, "calificaciones.csv")
    origenes = [o for o in ("resena", "historial") if o in set(df["origen"])]
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    ancho = 0.38
    for k, o in enumerate(origenes):
        sub = df[df["origen"] == o].sort_values("calificacion")
        x = sub["calificacion"].to_numpy() + (k - (len(origenes) - 1) / 2) * ancho
        etiqueta = (f"{ETIQUETA_ORIGEN[o]} (n = {int(sub['n_origen'].iloc[0])}; media {_f(float(sub['media_origen'].iloc[0]), 2)}; "
                    f"desv. {_f(float(sub['desviacion_origen'].iloc[0]), 2)})")
        barras = ax.bar(x, sub["proporcion"], width=ancho, color=COLOR_ORIGEN[o], label=etiqueta)
        for b, v in zip(barras, sub["proporcion"]):
            ax.text(b.get_x() + b.get_width() / 2, v, _f(v, 2), ha="center", va="bottom", fontsize=8.5, color=p.TINTA_SECUNDARIA)
    ax.set_xticks(sorted(df["calificacion"].unique()))
    ax.set_xlabel("Calificación (1 a 5)")
    ax.set_ylabel("Proporción de las interacciones del origen")
    ax.set_title("Distribución de las calificaciones por origen")
    ax.set_ylim(0, float(df["proporcion"].max()) * 1.38)
    _ejes_con_coma(ax.yaxis)
    ax.legend(loc="upper center", ncol=1)
    ax.grid(axis="x", visible=False)
    _pie(fig, NOTA_DATOS)
    return guardar_figura(fig, destino / "calificaciones_origen.png")


def generar(carpeta_resultados: str | Path | None = None, carpeta_figuras: str | Path | None = None) -> list[Path]:
    """Genera las 4 figuras de M3 y devuelve las rutas escritas. Sin argumentos usa las rutas de ``configs/m3/eda.yaml``."""
    if carpeta_resultados is None or carpeta_figuras is None:
        cfg = load_config(CONFIG)
        carpeta_resultados = RAIZ / cfg["salida"]["carpeta"] if carpeta_resultados is None else carpeta_resultados
        carpeta_figuras = RAIZ / cfg["figuras"]["carpeta"] if carpeta_figuras is None else carpeta_figuras
    res, fig = Path(carpeta_resultados), Path(carpeta_figuras)
    if not res.is_dir():
        raise FileNotFoundError(f"Falta la carpeta de resultados {res.as_posix()}: corre primero `{COMANDO}`")
    aplicar_estilo()
    return [fig_cola_larga(res, fig), fig_lorenz(res, fig), fig_preferencias_tipo(res, fig), fig_calificaciones_origen(res, fig)]
