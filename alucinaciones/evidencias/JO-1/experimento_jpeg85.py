"""JO-1 (M2) - how far is the versioned 224x224 JPEG (quality 85) from the plain bilinear stretch the app computes?

The app (app/lib/imagen.ts) decodes the user's image at its original size and stretches it to 224x224 with a
PIL-like bilinear filter; it never re-encodes to JPEG. The training images in data/processed/m2/ are that same
stretch saved as JPEG quality 85. This script measures, on a deterministic sample (every 25th id), the per-pixel
difference between
  R = stretch(original)                      (what the app feeds the model, up to the +-1 browser tolerance)
  J = decode(data/processed/m2/<id>.jpg)     (what the model is trained on)
It also checks that re-encoding R as JPEG 85 reproduces the versioned bytes.

    .venv/bin/python -I alucinaciones/evidencias/JO-1/experimento_jpeg85.py
"""

import csv
import io
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

RAIZ = Path.cwd()
ZIP = RAIZ / "data/raw/m2/Multi-Class Driver Behavior Image Dataset.zip"
PROC = RAIZ / "data/processed/m2"
SALIDA = RAIZ / "alucinaciones/evidencias/JO-1/experimento_jpeg85_salida.txt"
PASO = 25

with open(PROC / "origen.csv", encoding="utf-8") as f:
    origen = {r["id"]: r["archivo_original"] for r in csv.DictReader(f)}
with open(PROC / "indice.csv", encoding="utf-8") as f:
    indice = {r["id"]: r["archivo"] for r in csv.DictReader(f)}
ids = sorted(indice)[::PASO]

difs = []
bytes_iguales = 0
mae_por_imagen = []
with zipfile.ZipFile(ZIP) as z:
    for i in ids:
        im = Image.open(io.BytesIO(z.read(origen[i])))
        im = ImageOps.exif_transpose(im).convert("RGB")
        r = im.resize((224, 224), Image.Resampling.BILINEAR)
        buf = io.BytesIO()
        r.save(buf, "JPEG", quality=85)
        guardado = (PROC / indice[i]).read_bytes()
        bytes_iguales += buf.getvalue() == guardado
        j = np.asarray(Image.open(io.BytesIO(guardado)).convert("RGB"), dtype=np.int16)
        d = np.abs(np.asarray(r, dtype=np.int16) - j)
        difs.append(d.ravel())
        mae_por_imagen.append(float(d.mean()))

d = np.concatenate(difs)
lineas = [
    "# JPEG 85 frente al estirado bilineal sin recomprimir (lo que calcula la app)",
    f"Muestra: {len(ids)} imagenes (cada {PASO}.a id de indice.csv), {d.size} valores de canal",
    f"Recodificar R como JPEG 85 reproduce los bytes versionados: {bytes_iguales} de {len(ids)}",
    f"|R - J| medio por valor de canal: {d.mean():.3f} niveles (de 255)",
    f"|R - J| mediana / p95 / p99 / maximo: {np.median(d):.0f} / {np.percentile(d, 95):.0f} / "
    f"{np.percentile(d, 99):.0f} / {d.max()}",
    f"Fraccion de valores con |R - J| > 1 (fuera de la tolerancia +-1 de la paridad de la app): {(d > 1).mean():.4f}",
    f"MAE por imagen: min {min(mae_por_imagen):.3f} / mediana {np.median(mae_por_imagen):.3f} / max {max(mae_por_imagen):.3f}",
]
SALIDA.write_text("\n".join(lineas) + "\n", encoding="utf-8")
print("\n".join(lineas))
