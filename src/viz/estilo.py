"""Estilo común de las figuras estáticas de matplotlib (portado del Trabajo 2). Uso:

    from src.viz.estilo import aplicar_estilo, guardar_figura
    aplicar_estilo()                      # antes de crear las figuras
    guardar_figura(fig, "results/figures/m1/fig.png")
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from src.viz import paleta as p

DPI = 150


def parametros() -> dict:
    """rcParams comunes: sans del sistema, líneas de 2 px, cuadrícula tenue, sin bordes superior/derecho."""
    return {
        "font.family": "sans-serif",
        "font.sans-serif": p.FUENTES,
        "font.size": 11,
        "text.color": p.TINTA,
        "axes.facecolor": p.SUPERFICIE,
        "axes.edgecolor": p.EJE,
        "axes.linewidth": 1,
        "axes.labelcolor": p.TINTA_SECUNDARIA,
        "axes.titleweight": "semibold",
        "axes.titlecolor": p.TINTA,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "axes.prop_cycle": mpl.cycler(color=p.CATEGORICA),
        "grid.color": p.CUADRICULA,
        "grid.linewidth": 1,
        "grid.linestyle": "-",
        "xtick.color": p.TINTA_TENUE,
        "ytick.color": p.TINTA_TENUE,
        "lines.linewidth": p.ANCHO_LINEA,
        "lines.solid_capstyle": "round",
        "lines.markersize": p.TAMANO_MARCADOR,
        "legend.frameon": False,
        "legend.labelcolor": p.TINTA_SECUNDARIA,
        "figure.facecolor": p.SUPERFICIE,
        "figure.dpi": DPI,
        "savefig.facecolor": p.SUPERFICIE,
        "savefig.dpi": DPI,
        "savefig.bbox": "tight",
    }


def aplicar_estilo() -> None:
    """Aplica el estilo común a matplotlib (global al proceso)."""
    mpl.rcParams.update(parametros())


def mapa_secuencial() -> LinearSegmentedColormap:
    """Rampa azul de un solo tono (claro → oscuro) para mapas de calor."""
    return LinearSegmentedColormap.from_list("secuencial_azul", p.SECUENCIAL_AZUL)


def guardar_figura(fig: mpl.figure.Figure, ruta: str | os.PathLike, cerrar: bool = True) -> Path:
    """Guarda ``fig`` de forma uniforme (DPI y fondo del estilo, carpetas creadas) y la cierra; devuelve la ruta."""
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=DPI, facecolor=p.SUPERFICIE, bbox_inches="tight")
    if cerrar:
        plt.close(fig)
    return destino
