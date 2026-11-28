"""Figuras de M3: análisis descriptivo (JJ-2; núcleo §5.12 y «Figuras mínimas» del enunciado, módulo 3) y figuras mínimas
comunes de la red final (JJ-5; enunciado, «Entregables → 1»).

Descriptivo: lee SOLO ``results/data/m3/eda/`` (lo que escribe ``python run.py m3-eda --config configs/m3/eda.yaml``); no lee
los datos crudos ni los procesados. Escribe en ``blog/docs/figures/m3/``:
  cola_larga.png            interacciones por usuario y por destino frente al reparto uniforme al azar (figura mínima)
  lorenz.png                curva de Lorenz por destino_id y por lugar, con la diagonal y la referencia uniforme
  preferencias_tipo.png     combinación de preferencias × tipo de destino (proporciones por fila)
  calificaciones_origen.png calificaciones 1–5 de reseñas e historial

Modelos (JJ-5): leen SOLO los JSON del experimento en ``results/data/m3/`` (``m3-hpo`` y ``m3``):
  red_arquitectura.png      diagrama de las dos torres: capas, dimensiones, activaciones y parámetros (arquitectura/red.json)
  red_curvas.png            pérdida de train y validación y NDCG@5 de validación por época, con la mejor época y la parada
                            temprana (curvas/red.json)
  busqueda_m3.png           NDCG@5 de validación de cada ensayo de la búsqueda, red y MF (hpo_ensayos.json)
  cajas_m3.png              NDCG@5 y Recall@10 en prueba de los 4 modelos sobre las semillas, con el esperado del azar
                            (semillas/<modelo>_seed<k>.json y summary.json)

``run.py figures`` llama ``generar()`` sin argumentos (las 8 figuras). Los datos son generados (D4): las figuras describen el
conjunto, no turistas reales.
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
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from src.comun.config import load_config  # noqa: E402
from src.viz import paleta as p  # noqa: E402
from src.viz.estilo import aplicar_estilo, guardar_figura, mapa_secuencial  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / "configs" / "m3" / "eda.yaml"
CONFIG_EXPERIMENTO = RAIZ / "configs" / "m3" / "base.yaml"
COMANDO = "python run.py m3-eda --config configs/m3/eda.yaml"
COMANDO_EXPERIMENTO = ("python run.py m3-hpo --config configs/m3/hpo.yaml y luego "
                       "python run.py m3 --config configs/m3/base.yaml")
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


def _pie(fig, texto: str, y: float = -0.02) -> None:
    ajustado = "\n".join(textwrap.fill(linea, 105) for linea in texto.split("\n"))
    fig.text(0.5, y, ajustado, ha="center", va="top", fontsize=9, color=p.TINTA_SECUNDARIA)


def _decimales(n: int) -> FuncFormatter:
    """Marcas de eje con n decimales y coma decimal (evita etiquetas repetidas como «0,64» cuando los ticks son finos)."""
    return FuncFormatter(lambda x, pos: f"{x:.{n}f}".replace(".", ","))


def _leyenda_abajo(ax, ncol: int = 2, fontsize: float = 9) -> None:
    """Leyenda debajo del panel, fuera del área de datos (no tapa curvas ni puntos atípicos)."""
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=ncol, fontsize=fontsize)


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


# =========================================================================== figuras de los modelos (JJ-5)
NOMBRE_MODELO = {"popularidad": "Popularidad", "mf_als": "MF implícita (ALS)", "aleatorio": "Aleatorio",
                 "red": "Red de dos torres"}
COLOR_MODELO = {"red": p.CATEGORICA[0], "popularidad": p.CATEGORICA[1], "mf_als": p.CATEGORICA[2],
                "aleatorio": p.TINTA_TENUE}
COLOR_TORRE = {"usuario": p.CATEGORICA[0], "destino": p.CATEGORICA[2]}


def _leer_experimento(carpeta: Path, nombre: str) -> dict:
    ruta = carpeta / nombre
    if not ruta.is_file():
        raise FileNotFoundError(f"Falta {ruta.as_posix()}: corre primero `{COMANDO_EXPERIMENTO}`")
    return json.loads(ruta.read_text(encoding="utf-8"))


def _caja(ax, x: float, y: float, ancho: float, alto: float, texto: str, color: str, relleno: float = 0.14) -> None:
    ax.add_patch(FancyBboxPatch((x - ancho / 2, y - alto / 2), ancho, alto, boxstyle="round,pad=0.008,rounding_size=0.012",
                                facecolor=matplotlib.colors.to_rgba(color, relleno), edgecolor=color, linewidth=1.6))
    ax.text(x, y, texto, ha="center", va="center", fontsize=9.2, color=p.TINTA)


def _flecha(ax, x0: float, y0: float, x1: float, y1: float) -> None:
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops={"arrowstyle": "-|>", "color": p.TINTA_SECUNDARIA, "lw": 1.3})


def _texto_capa(c: dict) -> str:
    if c["tipo"] == "Embedding":
        return f"+ Embedding de id → {c['salida']}\n{_miles(c['parametros'])} parámetros (fila 0 fija)"
    act = "ReLU" if c["activacion"] == "relu" else "sin activación"
    drop = f" · Dropout {_f(c['dropout'], 2)}" if c.get("dropout") else ""
    return f"Linear {c['entrada']} → {c['salida']} · {act}{drop}\n{_miles(c['parametros'])} parámetros"


def fig_red_arquitectura(carpeta: Path, destino: Path) -> Path:
    """Diagrama de las dos torres desde ``arquitectura/red.json``: capas, dimensiones, activaciones y parámetros."""
    a = _leer_experimento(carpeta, "arquitectura/red.json")
    torres = {t: [c for c in a["capas"] if c["torre"] == t] for t in ("usuario", "destino")}
    n_filas = max(len(c) for c in torres.values()) + 2
    fig, ax = plt.subplots(figsize=(11, 1.15 * n_filas + 1.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    paso = 0.80 / n_filas
    entradas = {"usuario": f"x_u: {len(a['entrada_usuario'])} preferencias one-hot\n({', '.join(a['entrada_usuario'])})",
                "destino": f"x_i: tipo one-hot ({len(a['entrada_destino'])} columnas)\n"
                           f"({', '.join(c.split('=')[-1] for c in a['entrada_destino'])})"}
    d = a["hiperparametros"]["modelo.dim_embedding"]
    salidas = {"usuario": rf"$u \in \mathbb{{R}}^{{{d}}}$",
               "destino": rf"$(v_i, b_i) \in \mathbb{{R}}^{{{d}}} \times \mathbb{{R}}$"}
    bases: dict[str, float] = {}
    for x, (torre, capas) in zip((0.27, 0.73), torres.items()):
        color = COLOR_TORRE[torre]
        y = 0.93
        ax.text(x, 0.995, f"Torre de {torre}", ha="center", va="top", fontsize=11.5, fontweight="semibold", color=p.TINTA)
        _caja(ax, x, y - 0.03, 0.40, paso * 0.72, textwrap.fill(entradas[torre], 58), p.TINTA_TENUE, 0.08)
        y -= 0.03
        for c in capas:
            _flecha(ax, x, y - paso * 0.36, x, y - paso + paso * 0.36)
            y -= paso
            _caja(ax, x, y, 0.40, paso * 0.72, _texto_capa(c), color)
        _flecha(ax, x, y - paso * 0.36, x, y - paso + paso * 0.36)
        y -= paso
        _caja(ax, x, y, 0.30, paso * 0.6, salidas[torre], color, 0.30)
        bases[torre] = y
    y_puntaje = min(bases.values()) - paso * 1.05
    for x, torre in zip((0.27, 0.73), ("usuario", "destino")):
        _flecha(ax, x, bases[torre] - paso * 0.30, 0.5 + (x - 0.5) * 0.25, y_puntaje + paso * 0.30)
    _caja(ax, 0.5, y_puntaje, 0.36, paso * 0.6, r"Puntaje (logit): $s_{ui} = \langle u, v_i \rangle + b_i$", p.TINTA, 0.06)
    ax.set_ylim(y_puntaje - paso, 1.0)
    fig.suptitle(f"Arquitectura de la red de dos torres de M3 ({_miles(a['total_parametros'])} parámetros entrenables)",
                 y=1.01)
    _pie(fig, "Los embeddings de id se suman a la salida de su MLP; el índice 0 («sin id») es un vector nulo fijo que reciben "
              "los perfiles nuevos y los destinos sin interacciones en train. " + NOTA_DATOS + ".")
    return guardar_figura(fig, destino / "red_arquitectura.png")


def _marcar_parada(ax, c: dict) -> None:
    ax.axvline(c["mejor_epoca"], color=p.TINTA, linestyle="--", linewidth=1.3, label=f"Mejor época ({c['mejor_epoca']})")
    ax.axvline(c["epoca_parada"], color=p.TINTA_TENUE, linestyle=":", linewidth=1.6,
               label=f"Parada temprana ({c['epoca_parada']})")


def fig_red_curvas(carpeta: Path, destino: Path) -> Path:
    """Curvas de aprendizaje desde ``curvas/red.json``, con la mejor época y la parada temprana marcadas."""
    c = _leer_experimento(carpeta, "curvas/red.json")
    ep = c["epoca"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.3))
    ax1.plot(ep, c["perdida_train"], color=p.CATEGORICA[0], label="Train (negativos nuevos por época)")
    if any(v is not None for v in c["perdida_validacion"]):
        ax1.plot(ep, c["perdida_validacion"], color=p.CATEGORICA[1], label="Validación (negativos fijos)")
    _marcar_parada(ax1, c)
    ax1.set_xlabel("Época")
    ax1.set_ylabel(f"Pérdida {str(c.get('perdida_tipo', '')).upper()} (media por término)")
    ax1.set_title("Pérdida por época")
    _leyenda_abajo(ax1)
    ax1.yaxis.set_major_formatter(_decimales(3))
    if any(v is not None for v in c["ndcg5_validacion"]):
        ax2.plot(ep, c["ndcg5_validacion"], color=COLOR_MODELO["red"], marker="o", markersize=3.5, label="NDCG@5 de validación")
    _marcar_parada(ax2, c)
    ax2.set_xlabel("Época")
    ax2.set_ylabel("NDCG@5 (validación)")
    ax2.set_title("Criterio de la parada temprana")
    ax2.yaxis.set_major_formatter(_decimales(3))
    _leyenda_abajo(ax2)
    fig.suptitle(f"Curvas de aprendizaje de la red (semilla {c['semilla']}; paciencia {c['paciencia']} épocas)", y=1.02)
    _pie(fig, "La red se queda con los pesos de la mejor época (mayor NDCG@5 de validación) y se detiene tras «paciencia» "
              "épocas sin mejorar. " + NOTA_DATOS + ".", y=-0.17)
    return guardar_figura(fig, destino / "red_curvas.png")


def fig_busqueda(carpeta: Path, destino: Path) -> Path:
    """NDCG@5 de validación de cada ensayo de la búsqueda (red y MF) desde ``hpo_ensayos.json``."""
    fam = _leer_experimento(carpeta, "hpo_ensayos.json")["familias"]
    nombres = [n for n in ("red", "mf_als") if n in fam]
    fig, ejes = plt.subplots(1, len(nombres), figsize=(5.8 * len(nombres), 4.3), squeeze=False)
    for ax, n in zip(ejes[0], nombres):
        f = fam[n]
        ens = f["ensayos"]
        num = np.array([e["numero"] for e in ens])
        val = np.array([e["valor"] for e in ens])
        deg = np.array([bool(e["degenerado"]) for e in ens])
        ax.scatter(num[~deg], val[~deg], color=COLOR_MODELO[n], s=36, label="Ensayo válido", zorder=3)
        if deg.any():
            ax.scatter(num[deg], val[deg], color=p.TINTA_TENUE, marker="x", s=46, label="Ensayo degenerado (podado)",
                       zorder=3)
        mejor_hasta = np.maximum.accumulate(np.where(deg, -np.inf, val))
        ax.step(num, np.where(np.isfinite(mejor_hasta), mejor_hasta, np.nan), where="post", color=p.TINTA_SECUNDARIA,
                linewidth=1.3, label="Mejor hasta el ensayo")
        m = f["mejor"]
        ax.scatter([m["numero"]], [m["valor"]], marker="*", s=230, color=p.CATEGORICA[3], edgecolor=p.TINTA, zorder=4,
                   label=f"Mejor: ensayo {m['numero']} ({_f(m['valor'], 4)})")
        ax.set_xlabel("Número de ensayo (orden de Optuna)")
        ax.set_ylabel(f"{f['objetivo_nombre'].upper()} en validación")
        ax.set_title(f"{NOMBRE_MODELO[n]}: {f['n_ensayos']} ensayos ({_f(f['tiempo_total_s'], 1)} s)")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:.3f}".replace(".", ",")))
        ax.legend(loc="lower right", fontsize=8.5)
    fig.suptitle("Búsqueda de hiperparámetros (Optuna, TPE con semilla fija): desempeño en validación por ensayo", y=1.02)
    _pie(fig, "Mismo presupuesto (número de ensayos), objetivo y partición para las dos familias; cada ensayo se entrena "
              "solo con train. " + NOTA_DATOS + ".")
    return guardar_figura(fig, destino / "busqueda_m3.png")


def _metrica_por_semilla(carpeta: Path, modelo: str, clave: str) -> list[float]:
    rutas = sorted((carpeta / "semillas").glob(f"{modelo}_seed*.json"))
    return [json.loads(r.read_text(encoding="utf-8"))["metricas"]["global"][clave] for r in rutas]


def fig_cajas(carpeta: Path, destino: Path) -> Path:
    """NDCG@5 y Recall@10 en prueba por modelo sobre las semillas (diagramas de caja) y el esperado del azar."""
    s = _leer_experimento(carpeta, "summary.json")
    modelos = [m for m in ("popularidad", "mf_als", "aleatorio", "red") if m in s["modelos"]]
    azar = s["linea_base_aleatoria_analitica"]["global"]
    metricas_fig = [c for c in ("ndcg@5", "recall@10") if c in azar]
    fig, ejes = plt.subplots(1, len(metricas_fig), figsize=(5.8 * len(metricas_fig), 4.6), squeeze=False)
    for ax, clave in zip(ejes[0], metricas_fig):
        datos = [_metrica_por_semilla(carpeta, m, clave) for m in modelos]
        if any(len(d) == 0 for d in datos):
            raise FileNotFoundError(f"Faltan semillas en {(carpeta / 'semillas').as_posix()}: corre `{COMANDO_EXPERIMENTO}`")
        cajas = ax.boxplot(datos, patch_artist=True, widths=0.55, medianprops={"color": p.TINTA, "linewidth": 1.6})
        for caja, m in zip(cajas["boxes"], modelos):
            caja.set_facecolor(matplotlib.colors.to_rgba(COLOR_MODELO[m], 0.35))
            caja.set_edgecolor(COLOR_MODELO[m])
        for j, (d, m) in enumerate(zip(datos, modelos), start=1):
            ax.scatter(np.full(len(d), j) + np.linspace(-0.12, 0.12, len(d)), d, s=9, color=COLOR_MODELO[m], zorder=3)
        ax.axhline(azar[clave], color=p.TINTA_SECUNDARIA, linestyle="--", linewidth=1.3,
                   label=f"Esperado del azar ({_f(azar[clave], 4)})")
        ax.set_xticks(range(1, len(modelos) + 1), [NOMBRE_MODELO[m] for m in modelos], rotation=12)
        etiqueta = clave.replace("ndcg", "NDCG").replace("recall", "Recall")
        ax.set_ylabel(f"{etiqueta} en prueba")
        ax.set_title(etiqueta)
        ax.yaxis.set_major_formatter(_decimales(4))
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), fontsize=9)
        ax.grid(axis="x", visible=False)
    n = s["semillas"]["n"]
    fig.suptitle(f"Comparación de los modelos en prueba: variabilidad entre {n} semillas", y=1.02)
    _pie(fig, f"{s['n_usuarios_evaluados']} usuarios de prueba; un punto por semilla. La popularidad es determinista salvo "
              "los empates. " + NOTA_DATOS + ".", y=-0.12)
    return guardar_figura(fig, destino / "cajas_m3.png")


def generar_modelos(carpeta_experimento: str | Path, carpeta_figuras: str | Path) -> list[Path]:
    """Las 4 figuras mínimas comunes de la red final (JJ-5) desde los JSON de ``carpeta_experimento``."""
    res, fig = Path(carpeta_experimento), Path(carpeta_figuras)
    if not res.is_dir():
        raise FileNotFoundError(f"Falta la carpeta de resultados {res.as_posix()}: corre primero `{COMANDO_EXPERIMENTO}`")
    aplicar_estilo()
    return [fig_red_arquitectura(res, fig), fig_red_curvas(res, fig), fig_busqueda(res, fig), fig_cajas(res, fig)]


def generar(carpeta_resultados: str | Path | None = None, carpeta_figuras: str | Path | None = None,
            carpeta_experimento: str | Path | None = None) -> list[Path]:
    """Genera las figuras de M3 y devuelve las rutas escritas.

    Siempre las 4 del descriptivo (desde ``carpeta_resultados``); las 4 de los modelos, si se pasa ``carpeta_experimento`` o
    si se llama sin argumentos (``run.py figures``: rutas de ``configs/m3/eda.yaml`` y ``configs/m3/base.yaml``)."""
    sin_argumentos = carpeta_resultados is None and carpeta_figuras is None and carpeta_experimento is None
    if carpeta_resultados is None or carpeta_figuras is None:
        cfg = load_config(CONFIG)
        carpeta_resultados = RAIZ / cfg["salida"]["carpeta"] if carpeta_resultados is None else carpeta_resultados
        carpeta_figuras = RAIZ / cfg["figuras"]["carpeta"] if carpeta_figuras is None else carpeta_figuras
    if sin_argumentos:
        carpeta_experimento = RAIZ / load_config(CONFIG_EXPERIMENTO)["salida"]["carpeta"]
    res, fig = Path(carpeta_resultados), Path(carpeta_figuras)
    if not res.is_dir():
        raise FileNotFoundError(f"Falta la carpeta de resultados {res.as_posix()}: corre primero `{COMANDO}`")
    aplicar_estilo()
    rutas = [fig_cola_larga(res, fig), fig_lorenz(res, fig), fig_preferencias_tipo(res, fig), fig_calificaciones_origen(res, fig)]
    if carpeta_experimento is not None:
        rutas += generar_modelos(carpeta_experimento, fig)
    return rutas
