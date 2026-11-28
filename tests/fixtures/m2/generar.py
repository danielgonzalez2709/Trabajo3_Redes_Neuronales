"""Genera por código el .zip mínimo de pruebas de M2 (misma estructura de carpetas que el conjunto real).

Contenido (9 miembros de imagen, 5 clases; todo ficticio, sin datos reales):

    safe_driving/img_1.jpg            JPEG RGB 64x48
    safe_driving/IMG_2.JPG            JPEG RGB 48x64 (extensión en mayúsculas)
    talking_phone/foto_exif6.jpg      JPEG RGB 60x40 con EXIF Orientation 6  -> 40x60 tras aplicar la orientación
    talking_phone/foto_exif8.jpg      JPEG RGB 50x30 con EXIF Orientation 8  -> 30x50
    texting_phone/captura.png         PNG RGBA 80x60, alfa opaco en todos los píxeles
    turning/img_3.jpg                 JPEG RGB 100x70
    other_activities/img_roto.jpg     JPEG cuyos primeros 12 bytes son cero (ilegible)
    other_activities/translucida.png  PNG RGBA 20x20 con la mitad izquierda totalmente transparente
    other_activities/img_4.jpg        JPEG RGB 40x40

Es determinista: mismas fechas fijas en el .zip, mismos píxeles, mismo Pillow -> mismos bytes.
Uso: ``.venv/bin/python tests/fixtures/m2/generar.py`` escribe ``tests/fixtures/m2/driver_prueba.zip``.
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ_ZIP = "Multi-Class Driver Behavior Image Dataset"
NOMBRE_ZIP = "driver_prueba.zip"
CLASES = ["other_activities", "safe_driving", "talking_phone", "texting_phone", "turning"]
FECHA_FIJA = (2024, 11, 15, 0, 0, 0)


def _pixeles(ancho: int, alto: int, semilla: int) -> np.ndarray:
    """Imagen RGB determinista (degradados distintos por semilla)."""
    x = np.linspace(0, 255, ancho, dtype=np.float64)[None, :].repeat(alto, axis=0)
    y = np.linspace(0, 255, alto, dtype=np.float64)[:, None].repeat(ancho, axis=1)
    canales = [(x + 37 * semilla) % 256, (y + 71 * semilla) % 256, ((x + y) / 2 + 13 * semilla) % 256]
    return np.stack(canales, axis=-1).astype(np.uint8)


def _jpeg(ancho: int, alto: int, semilla: int, orientacion: int | None = None) -> bytes:
    img = Image.fromarray(_pixeles(ancho, alto, semilla), "RGB")
    buf = io.BytesIO()
    if orientacion is None:
        img.save(buf, "JPEG", quality=90)
    else:
        exif = Image.Exif()
        exif[0x0112] = orientacion
        img.save(buf, "JPEG", quality=90, exif=exif.tobytes())
    return buf.getvalue()


def _png_rgba(ancho: int, alto: int, semilla: int, mitad_transparente: bool) -> bytes:
    rgb = _pixeles(ancho, alto, semilla)
    alfa = np.full((alto, ancho, 1), 255, dtype=np.uint8)
    if mitad_transparente:
        alfa[:, : ancho // 2, :] = 0
    img = Image.fromarray(np.concatenate([rgb, alfa], axis=-1), "RGBA")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def miembros() -> dict[str, bytes]:
    roto = bytearray(_jpeg(40, 30, 9))
    roto[:12] = bytes(12)
    return {
        "safe_driving/img_1.jpg": _jpeg(64, 48, 1),
        "safe_driving/IMG_2.JPG": _jpeg(48, 64, 2),
        "talking_phone/foto_exif6.jpg": _jpeg(60, 40, 3, orientacion=6),
        "talking_phone/foto_exif8.jpg": _jpeg(50, 30, 4, orientacion=8),
        "texting_phone/captura.png": _png_rgba(80, 60, 5, mitad_transparente=False),
        "turning/img_3.jpg": _jpeg(100, 70, 6),
        "other_activities/img_roto.jpg": bytes(roto),
        "other_activities/translucida.png": _png_rgba(20, 20, 7, mitad_transparente=True),
        "other_activities/img_4.jpg": _jpeg(40, 40, 8),
    }


def construir_zip(ruta: Path) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_STORED) as z:
        for carpeta in [RAIZ_ZIP + "/", *[f"{RAIZ_ZIP}/{c}/" for c in CLASES]]:
            info = zipfile.ZipInfo(carpeta, FECHA_FIJA)
            info.external_attr = 0o40755 << 16
            z.writestr(info, b"")
        for nombre, datos in miembros().items():
            info = zipfile.ZipInfo(f"{RAIZ_ZIP}/{nombre}", FECHA_FIJA)
            info.external_attr = 0o100644 << 16
            z.writestr(info, datos)
    return ruta


if __name__ == "__main__":
    print(construir_zip(Path(__file__).resolve().parent / NOMBRE_ZIP))
