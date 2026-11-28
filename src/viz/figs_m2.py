"""Figuras de M2. JO-3: pares de imágenes en la frontera de los umbrales de casi duplicados (jose.md §3.2, D3).

Lee ``results/data/m2/particion/{frontera.csv, resumen.json}`` (los escribe
``python run.py m2-datos --config configs/m2/particion.yaml``) y las imágenes 224x224 versionadas de ``data/processed/m2/``.
Escribe ``blog/docs/figures/m2/frontera_duplicados.png``: cuatro columnas (justo dentro / justo fuera del umbral de Hamming y
del umbral de coseno), cada fila un par lado a lado con d_H, coseno y clases. «Fuera» = sin arista por ningún criterio: son
pares que la partición SÍ puede separar.

``run.py figures`` llama ``generar()`` sin argumentos.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sin ventana: también corre en CI

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402

from src.viz import paleta as p  # noqa: E402
from src.viz.estilo import aplicar_estilo, guardar_figura  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
COMANDO = "python run.py m2-datos --config configs/m2/particion.yaml"
LADO_MINIATURA = 112
SEPARACION_PAR_PX = 6                          # franja blanca entre las dos imágenes de un par
PANELES = [("hamming", "dentro"), ("hamming", "fuera"), ("coseno", "dentro"), ("coseno", "fuera")]
COLOR_CLASES_DISTINTAS = p.CATEGORICA[3]       # rótulo de un par cuyas dos imágenes son de clases distintas
COLOR_MISMA_CLASE = p.TINTA


def _f(x: float, dec: int = 3) -> str:
    return f"{x:.{dec}f}".replace(".", ",")


def _titulo_panel(panel: str, lado: str, r: dict) -> str:
    u = r["umbrales"]
    if panel == "hamming":
        regla = f"d_H ≤ {u['hamming']}" if lado == "dentro" else f"d_H > {u['hamming']}"
    else:
        regla = f"cos ≥ {_f(u['coseno'], 2)}" if lado == "dentro" else f"cos < {_f(u['coseno'], 2)}"
    return f"{'Justo dentro' if lado == 'dentro' else 'Justo fuera (sin arista)'}\n{regla}"


def _miniatura(ruta: Path) -> np.ndarray:
    with Image.open(ruta) as img:
        return np.asarray(img.convert("RGB").resize((LADO_MINIATURA, LADO_MINIATURA), Image.Resampling.BILINEAR))


def figura_frontera(frontera: pd.DataFrame, resumen: dict, carpeta_procesada: Path) -> plt.Figure:
    if frontera.empty:
        raise ValueError(f"frontera.csv no tiene pares que mostrar (¿umbrales o márgenes que no dejan pares cerca?); "
                         f"revisa frontera y barrido en configs/m2/particion.yaml y vuelve a correr: {COMANDO}")
    n = int(frontera.groupby(["panel", "lado"]).size().max())
    fig, ejes = plt.subplots(n, len(PANELES), figsize=(3.2 * len(PANELES), 1.75 * n + 1.2), squeeze=False)
    for c, (panel, lado) in enumerate(PANELES):
        filas = frontera[(frontera["panel"] == panel) & (frontera["lado"] == lado)].reset_index(drop=True)
        ejes[0, c].set_title(_titulo_panel(panel, lado, resumen), fontsize=10)
        for r in range(n):
            ax = ejes[r, c]
            ax.set_axis_off()
            if r >= len(filas):
                continue
            f = filas.iloc[r]
            par = np.concatenate([_miniatura(carpeta_procesada / f["archivo_a"]), np.full((LADO_MINIATURA, SEPARACION_PAR_PX, 3), 255, np.uint8),
                                  _miniatura(carpeta_procesada / f["archivo_b"])], axis=1)
            ax.imshow(par)
            mismo = f["clase_a"] == f["clase_b"]
            ax.text(0.5, -0.04, f"d_H {f['hamming']} · cos {_f(float(f['coseno']), 4)}\n{f['clase_a']} / {f['clase_b']}",
                    transform=ax.transAxes, ha="center", va="top", fontsize=7,
                    color=COLOR_MISMA_CLASE if mismo else COLOR_CLASES_DISTINTAS)
    u = resumen["umbrales"]
    fig.suptitle(f"Pares en la frontera de los umbrales de casi duplicados (arista si d_H ≤ {u['hamming']} o "
                 f"cos ≥ {_f(u['coseno'], 2)})", fontsize=12, y=1.0)
    fig.text(0.5, -0.01, resumen["pie_figura_frontera"], ha="center", fontsize=8, color=p.TINTA_SECUNDARIA)
    fig.tight_layout()
    return fig


def generar(carpeta_resultados: Path | None = None, carpeta_figuras: Path | None = None,
            carpeta_procesada: Path | None = None) -> list[Path]:
    res = Path(carpeta_resultados or RAIZ / "results" / "data" / "m2" / "particion")
    destino = Path(carpeta_figuras or RAIZ / "blog" / "docs" / "figures" / "m2")
    procesada = Path(carpeta_procesada or RAIZ / "data" / "processed" / "m2")
    ruta_frontera, ruta_resumen = res / "frontera.csv", res / "resumen.json"
    if not (ruta_frontera.is_file() and ruta_resumen.is_file()):
        raise FileNotFoundError(f"Faltan {ruta_frontera} o {ruta_resumen}; genéralos con: {COMANDO}")
    frontera = pd.read_csv(ruta_frontera, dtype=str, keep_default_na=False)
    resumen = json.loads(ruta_resumen.read_text(encoding="utf-8"))
    aplicar_estilo()
    return [guardar_figura(figura_frontera(frontera, resumen, procesada), destino / "frontera_duplicados.png")]
