"""JO-1 (M2) - independent recount by the hallucination hunter.

Does NOT import src/m2_conduccion/datos.py nor docs/investigacion/JO-1_inventario.py.
Reads the raw .zip in streaming (no extraction to disk) and the versioned processed
files, recomputes the figures and compares them with ficha.json, calidad.csv and
procesado.json. Run from the repo root:

    .venv/bin/python -I alucinaciones/evidencias/JO-1/verificar_datos.py
"""

import csv
import hashlib
import io
import json
import re
import sys
import warnings
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

RAIZ = Path.cwd()
ZIP = RAIZ / "data/raw/m2/Multi-Class Driver Behavior Image Dataset.zip"
EDA = RAIZ / "results/data/m2/eda"
PROC = RAIZ / "data/processed/m2"
SALIDA = RAIZ / "alucinaciones/evidencias/JO-1/verificar_datos_salida.txt"
EXT = {".jpg", ".jpeg", ".png"}

lineas = []


def out(s=""):
    lineas.append(str(s))
    print(s)


def comparar(nombre, mio, suyo):
    ok = mio == suyo
    out(f"[{'IGUAL' if ok else 'DISTINTO'}] {nombre}: recalculado={mio!r} | publicado={suyo!r}")
    return ok


def sha_file(p, bloque=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(bloque):
            h.update(b)
    return h.hexdigest()


ficha = json.loads((EDA / "ficha.json").read_text(encoding="utf-8"))
proc = json.loads((EDA / "procesado.json").read_text(encoding="utf-8"))
c = ficha["conteos"]
resultados = []

out("# Recalculo independiente de JO-1 (M2)")
out(f"Python {sys.version.split()[0]}, Pillow {Image.__version__}, numpy {np.__version__}")

out("\n## 1. Archivo .zip")
resultados.append(comparar("tamano_bytes", ZIP.stat().st_size, proc["config"]["entrada"]["tamano_bytes_esperado"]))
resultados.append(comparar("sha256_zip", sha_file(ZIP), ficha["sha256"]))

por_clase = Counter()
ilegibles = {}
ilegibles_clase = Counter()
legibles_clase = Counter()
ext = Counter()
fmt = Counter()
modo = Counter()
res_raw = Counter()
res_exif = Counter()
orient = Counter()
make = Counter()
model = Counter()
png_n = png_rgba = png_opaco = 0
exif_dt = []
nombres_fechas = {"AAAA-MM-DDhh-mm-ss": [], "photo_AAAA-MM-DD_hh-mm-ss": [], "IMG_AAAAMMDD_hhmmss": []}
pat = {
    "AAAA-MM-DDhh-mm-ss": re.compile(r"^(\d{4})-(\d{2})-(\d{2})(\d{2})-(\d{2})-(\d{2})"),
    "photo_AAAA-MM-DD_hh-mm-ss": re.compile(r"^photo_(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})"),
    "IMG_AAAAMMDD_hhmmss": re.compile(r"^IMG_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})"),
}

with zipfile.ZipFile(ZIP) as z:
    miembros = sorted((i for i in z.infolist() if not i.is_dir()), key=lambda i: i.filename)
    for info in miembros:
        partes = info.filename.split("/")
        nombre = partes[-1]
        e = Path(nombre).suffix
        if e.lower() not in EXT:
            continue
        clase = partes[-2]
        por_clase[clase] += 1
        ext[e] += 1
        datos = z.read(info)
        for k, rx in pat.items():
            m = rx.match(nombre)
            if m:
                g = m.groups()
                nombres_fechas[k].append(f"{g[0]}-{g[1]}-{g[2]} {g[3]}:{g[4]}:{g[5]}")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                im = Image.open(io.BytesIO(datos))
                im.load()
        except Exception as ex:  # noqa: BLE001 - we only count failures
            ilegibles[info.filename] = type(ex).__name__
            ilegibles_clase[clase] += 1
            continue
        legibles_clase[clase] += 1
        fmt[im.format] += 1
        modo[im.mode] += 1
        res_raw[f"{im.width}x{im.height}"] += 1
        ex = im.getexif()
        o = ex.get(0x0112)
        orient[str(o) if o is not None else "sin_orientacion"] += 1
        if ex.get(0x010F):
            make[str(ex.get(0x010F)).strip("\x00 ")] += 1
        if ex.get(0x0110):
            model[str(ex.get(0x0110)).strip("\x00 ")] += 1
        if ex.get(0x0132):
            exif_dt.append(str(ex.get(0x0132)).strip("\x00 "))
        t = ImageOps.exif_transpose(im)
        res_exif[f"{t.width}x{t.height}"] += 1
        if im.format == "PNG":
            png_n += 1
            if im.mode == "RGBA":
                png_rgba += 1
                a = np.asarray(im.getchannel("A"))
                if (a == 255).all():
                    png_opaco += 1

out("\n## 2. Conteos por clase")
resultados.append(comparar("por_clase_en_zip", dict(sorted(por_clase.items())), dict(sorted(c["por_clase_en_zip"].items()))))
resultados.append(comparar("total_en_zip", sum(por_clase.values()), c["total_en_zip"]))
resultados.append(comparar("ilegibles", len(ilegibles), c["ilegibles"]))
resultados.append(comparar("ilegibles_por_clase", dict(sorted(ilegibles_clase.items())), dict(sorted(c["ilegibles_por_clase"].items()))))
resultados.append(comparar("por_clase_legibles", dict(sorted(legibles_clase.items())), dict(sorted(c["por_clase_legibles"].items()))))
resultados.append(comparar("n_registros", sum(legibles_clase.values()), ficha["n_registros"]))
cal_ileg = []
with open(EDA / "calidad.csv", encoding="utf-8") as f:
    for fila in csv.DictReader(f):
        if fila["categoria"] == "ilegible":
            cal_ileg.append(fila["elemento"])
resultados.append(comparar("archivos ilegibles (calidad.csv)", sorted(ilegibles), sorted(cal_ileg)))
out(f"  tipos de error: {Counter(ilegibles.values())}")

out("\n## 3. Formato, modo, extension")
resultados.append(comparar("extensiones", dict(sorted(ext.items())), dict(sorted(c["extensiones_en_zip"].items()))))
resultados.append(comparar("formatos", dict(sorted(fmt.items())), dict(sorted(c["formatos"].items()))))
resultados.append(comparar("modos", dict(sorted(modo.items())), dict(sorted(c["modos"].items()))))

out("\n## 4. Resoluciones")
top_raw = [list(x) for x in sorted(res_raw.items(), key=lambda kv: (-kv[1], kv[0]))[:10]]
top_exif = [list(x) for x in sorted(res_exif.items(), key=lambda kv: (-kv[1], kv[0]))[:10]]
out(f"  top-10 sin EXIF (desempate por nombre): {top_raw}")
out(f"  top-10 tras EXIF (desempate por nombre): {top_exif}")
# Compare only entries with unique counts (ties among count==1 can be ordered differently).
resultados.append(comparar("top-6 sin EXIF", top_raw[:6], c["resoluciones_sin_exif_mas_frecuentes"][:6]))
resultados.append(comparar("top-6 tras EXIF", top_exif[:6], c["resoluciones_tras_exif_mas_frecuentes"][:6]))
resultados.append(comparar("distintas sin EXIF", len(res_raw), c["resoluciones_distintas_sin_exif"]))
resultados.append(comparar("distintas tras EXIF", len(res_exif), c["resoluciones_distintas_tras_exif"]))
pub_raw = {k: v for k, v in c["resoluciones_sin_exif_mas_frecuentes"]}
pub_exif = {k: v for k, v in c["resoluciones_tras_exif_mas_frecuentes"]}
resultados.append(comparar("cada par publicado sin EXIF existe con ese conteo", all(res_raw.get(k) == v for k, v in pub_raw.items()), True))
resultados.append(comparar("cada par publicado tras EXIF existe con ese conteo", all(res_exif.get(k) == v for k, v in pub_exif.items()), True))
d = c["declarado_vs_medido"]
resultados.append(comparar("imagenes 400x600 o 600x400", res_raw.get("400x600", 0) + res_raw.get("600x400", 0), d["imagenes_con_la_resolucion_declarada_en_cualquier_orientacion"]))

out("\n## 5. EXIF")
resultados.append(comparar("orientacion_distribucion", dict(sorted(orient.items())), dict(sorted(c["exif"]["orientacion_distribucion"].items()))))
aplicada = {k: v for k, v in orient.items() if k not in {"1", "sin_orientacion"}}
resultados.append(comparar("orientacion_aplicada_por_valor", dict(sorted(aplicada.items())), dict(sorted(c["exif"]["orientacion_aplicada_por_valor"].items()))))
resultados.append(comparar("orientacion_aplicada_n", sum(aplicada.values()), c["exif"]["orientacion_aplicada_n"]))
resultados.append(comparar("marca", dict(sorted(make.items())), dict(sorted(c["exif"]["marca"].items()))))
resultados.append(comparar("modelo", dict(sorted(model.items())), dict(sorted(c["exif"]["modelo"].items()))))

out("\n## 6. PNG alfa")
resultados.append(comparar("n_png", png_n, c["png_alfa"]["n_png"]))
resultados.append(comparar("n_rgba", png_rgba, c["png_alfa"]["n_rgba"]))
resultados.append(comparar("n_alfa_totalmente_opaco", png_opaco, c["png_alfa"]["n_alfa_totalmente_opaco"]))

out("\n## 7. Fechas medidas")


def resumen_fechas(lst):
    lst = sorted(lst)
    return {"n": len(lst), "minimo": lst[0] if lst else None, "maximo": lst[-1] if lst else None,
            "por_anio_mes": dict(sorted(Counter(x[:7] for x in lst).items()))}


dt_norm = [x[:4] + "-" + x[5:7] + "-" + x[8:10] + x[10:] for x in exif_dt]
mio = resumen_fechas(dt_norm)
suyo = c["fechas_medidas"]["exif_datetime"]
resultados.append(comparar("exif_datetime", mio, {k: suyo[k] for k in ("n", "minimo", "maximo", "por_anio_mes")}))
for k, lst in nombres_fechas.items():
    suyo = c["fechas_medidas"]["nombres_de_archivo"][k]
    resultados.append(comparar(f"nombres {k}", resumen_fechas(lst), {kk: suyo[kk] for kk in ("n", "minimo", "maximo", "por_anio_mes")}))

out("\n## 8. Procesados versionados")
with open(PROC / "indice.csv", encoding="utf-8", newline="") as f:
    filas = list(csv.DictReader(f))
resultados.append(comparar("filas de indice.csv", len(filas), 7276))
resultados.append(comparar("sha256 indice.csv", sha_file(PROC / "indice.csv"), proc["sha256_indice"]))
h = hashlib.sha256()
dims = Counter()
modos_p = Counter()
fmts_p = Counter()
clases_p = Counter()
for fila in sorted(filas, key=lambda r: r["id"]):
    p = PROC / fila["archivo"]
    b = p.read_bytes()
    h.update(b)
    with Image.open(io.BytesIO(b)) as im:
        dims[im.size] += 1
        modos_p[im.mode] += 1
        fmts_p[im.format] += 1
    clases_p[fila["clase"]] += 1
resultados.append(comparar("huella de imagenes procesadas", h.hexdigest(), proc["sha256_imagenes"]))
resultados.append(comparar("tamanos procesados", dict(dims), {(224, 224): 7276}))
resultados.append(comparar("modos procesados", dict(modos_p), {"RGB": 7276}))
resultados.append(comparar("formatos procesados", dict(fmts_p), {"JPEG": 7276}))
resultados.append(comparar("clases en indice.csv", dict(sorted(clases_p.items())), dict(sorted(legibles_clase.items()))))
vacias = all(r["grupo_duplicado"] == "" and r["split"] == "" for r in filas)
resultados.append(comparar("grupo_duplicado y split vacios", vacias, True))

out(f"\n## Resumen: {sum(resultados)} de {len(resultados)} comprobaciones IGUALES")
SALIDA.write_text("\n".join(lineas) + "\n", encoding="utf-8")
