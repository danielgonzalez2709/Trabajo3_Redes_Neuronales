"""JO-1 fase A: inventario medido del .zip de M2 (Multi-Class Driver Behavior Image Dataset).

Solo archivos locales (sin internet). Solo biblioteca estándar + numpy + pillow. Sin aleatoriedad.
El .zip se lee con `zipfile` sin extraerlo a disco; los .zip anidados se abren en memoria. El contenido se trata como datos
no confiables: los nombres de los miembros solo se usan como texto, nunca como rutas del sistema de archivos.

Uso (desde la raíz del repositorio):
    .venv/bin/python -I docs/investigacion/JO-1_inventario.py
Salida: se imprime y se escribe en UTF-8 en docs/investigacion/JO-1_inventario_salida.txt
"""
from __future__ import annotations

import hashlib
import io
import re
import sys
import warnings
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

import numpy as np
from PIL import ExifTags, Image

RAIZ = Path(__file__).resolve().parents[2]
ZIP = RAIZ / "data" / "raw" / "m2" / "Multi-Class Driver Behavior Image Dataset.zip"
SALIDA = RAIZ / "docs" / "investigacion" / "JO-1_inventario_salida.txt"
EXT_IMAGEN = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}
FORMATO_ESPERADO = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".bmp": "BMP", ".gif": "GIF", ".tif": "TIFF",
                    ".tiff": "TIFF", ".webp": "WEBP"}
EXIF_CLAVES = {271: "Make", 272: "Model", 274: "Orientation", 306: "DateTime"}
PATRONES = {  # nombre -> expresión regular (sobre el nombre de archivo, sin distinguir mayúsculas)
    "aug": r"aug",
    "flip": r"flip",
    "rot": r"rot",
    "copy|copia": r"copy|copia",
    "(n) al final del nombre": r"\(\d+\)\s*(\.[^.]+)?$",
    "_n al final del nombre": r"_\d+(\.[^.]+)?$",
    "solo dígitos": r"^\d+\.[^.]+$",
    "contiene dígitos": r"\d",
    "espacios": r"\s",
    "guion bajo": r"_",
    "guion": r"-",
    "mayúsculas en la extensión": None,  # se mide aparte (distingue mayúsculas)
}

_lineas: list[str] = []


def p(texto: str = "") -> None:
    print(texto)
    _lineas.append(texto)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def normalizar(nombre: str) -> str:
    return nombre.replace("\\", "/")


def resumen_num(v: list[float]) -> str:
    a = np.asarray(v, dtype=float)
    return f"mín {a.min():.0f} / mediana {np.median(a):.0f} / máx {a.max():.0f}"


def porcentaje(n: int, total: int) -> str:
    return f"{100 * n / total:.2f} %" if total else "n/d"


# --------------------------------------------------------------------------- recorrido del zip
def recorrer(zf: zipfile.ZipFile, prefijo: str, miembros: list[dict], anidados: list[str]) -> None:
    """Agrega un dict por miembro-archivo (no directorio). Los .zip anidados se abren en memoria y se recorren igual."""
    for info in sorted(zf.infolist(), key=lambda i: i.filename):
        if info.is_dir():
            continue
        nombre = prefijo + normalizar(info.filename)
        ext = PurePosixPath(normalizar(info.filename)).suffix
        if ext.lower() == ".zip":
            anidados.append(nombre)
            try:
                with zipfile.ZipFile(io.BytesIO(zf.read(info))) as interno:
                    miembros.append({"ruta": nombre, "bytes": info.file_size, "ext": ext, "es_zip": True, "zf": None})
                    recorrer(interno, nombre + "!/", miembros, anidados)
            except zipfile.BadZipFile as e:
                p(f"  .zip anidado ilegible {nombre}: {e}")
            continue
        miembros.append({"ruta": nombre, "bytes": info.file_size, "ext": ext, "es_zip": False, "zf": zf, "info": info})


def ruta_directorio(ruta: str) -> str:
    return str(PurePosixPath(ruta).parent)


def clase_de(ruta: str) -> str:
    """Carpeta inmediata del archivo (copiada tal cual)."""
    return PurePosixPath(ruta).parent.name or "(raíz)"


# --------------------------------------------------------------------------- análisis de imágenes
def analizar_imagen(m: dict) -> dict:
    r = {"ruta": m["ruta"], "clase": clase_de(m["ruta"]), "dir": ruta_directorio(m["ruta"]), "ext": m["ext"],
         "bytes": m["bytes"], "sha": None, "error": None}
    try:
        datos = m["zf"].read(m["info"])  # verifica la CRC del miembro
    except Exception as e:  # noqa: BLE001
        r["error"] = f"lectura del zip: {type(e).__name__}: {str(e)[:200]}"
        r["sha"] = f"ilegible:{m['ruta']}"
        return r
    r["bytes"], r["sha"] = len(datos), sha256_bytes(datos)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # DecompressionBombWarning u otras advertencias cuentan como fallo
            with Image.open(io.BytesIO(datos)) as im:
                r["formato"] = im.format
                r["modo"] = im.mode
                r["ancho"], r["alto"] = im.size
                try:
                    exif = im.getexif()
                    r["exif"] = {EXIF_CLAVES[k]: str(v) for k, v in exif.items() if k in EXIF_CLAVES}
                    r["exif_n"] = len(exif)
                except Exception as e:  # EXIF ilegible no invalida la imagen
                    r["exif"], r["exif_n"] = {}, 0
                    r["exif_error"] = f"{type(e).__name__}: {e}"
                im.load()
                r["pix"] = sha256_bytes(f"{im.mode}|{im.size}|".encode() + im.tobytes())
    except Exception as e:  # noqa: BLE001  (cualquier fallo de decodificación es un hallazgo)
        r["error"] = f"{type(e).__name__}: " + re.sub(r" at 0x[0-9a-f]+", "", str(e))[:200]  # sin direcciones de memoria
        r["magia"] = datos[:12].hex()  # primeros bytes del archivo (firma) para diagnosticar
    return r


def main() -> int:
    if not ZIP.exists():
        p(f"TODO(dato-faltante): no existe {ZIP.relative_to(RAIZ)}; corre scripts/descargar_m2.py")
        return 1
    p("# JO-1 fase A — inventario medido del .zip de M2")
    p(f"Archivo: {ZIP.relative_to(RAIZ)}")
    p(f"Python {sys.version.split()[0]}, Pillow {Image.__version__}, numpy {np.__version__}")
    p()

    # ------------------------------------------------------------------ A2.1
    p("## A2.1 Archivo")
    p(f"Tamaño del .zip: {ZIP.stat().st_size} bytes")
    p(f"SHA-256 del .zip: {sha256_archivo(ZIP)}")
    miembros: list[dict] = []
    anidados: list[str] = []
    with zipfile.ZipFile(ZIP) as zf:
        total_entradas = len(zf.infolist())
        n_dirs = sum(1 for i in zf.infolist() if i.is_dir())
        con_barra_inv = sum(1 for i in zf.infolist() if "\\" in i.filename)
        inseguros = [i.filename for i in zf.infolist()
                     if i.filename.startswith(("/", "\\")) or ".." in normalizar(i.filename).split("/")]
        p(f"Entradas del .zip: {total_entradas} ({n_dirs} directorios, {total_entradas - n_dirs} archivos)")
        p(f"Entradas con barra invertida en el nombre (se normalizan a '/' solo para agrupar): {con_barra_inv}")
        p(f"Entradas con ruta absoluta o '..' (no se extrae nada; solo se cuentan): {len(inseguros)}")
        recorrer(zf, "", miembros, anidados)
        p(f"Miembros-archivo contados (incluidos los de .zip anidados, excluidos los propios .zip anidados): "
          f"{sum(1 for m in miembros if not m['es_zip'])}")
        p(f".zip anidados: {len(anidados)}" + (f" -> {anidados}" if anidados else ""))
        if anidados:
            p("Qué se hizo: cada .zip anidado se abrió en memoria (io.BytesIO) y sus miembros se analizaron igual, con la "
              "ruta prefijada por «<anidado>!/».")
        no_img = [m for m in miembros if not m["es_zip"] and m["ext"].lower() not in EXT_IMAGEN]
        p(f"Miembros que no son imágenes (por extensión): {len(no_img)}")
        for m in no_img[:60]:
            p(f"  {m['ruta']}  ({m['bytes']} bytes)")
        if len(no_img) > 60:
            p(f"  ... y {len(no_img) - 60} más; por extensión: {dict(Counter(m['ext'] for m in no_img))}")
        ext_cnt = Counter(m["ext"] for m in miembros if not m["es_zip"])
        p(f"Extensiones de todos los miembros (tal cual, distingue mayúsculas): {dict(sorted(ext_cnt.items()))}")
        p()

        imgs_m = [m for m in miembros if not m["es_zip"] and m["ext"].lower() in EXT_IMAGEN]
        regs = []
        for i, m in enumerate(imgs_m, 1):
            regs.append(analizar_imagen(m))
            if i % 5000 == 0:
                print(f"  ... {i}/{len(imgs_m)} imágenes analizadas", file=sys.stderr)

    total = len(regs)
    clases = sorted({r["clase"] for r in regs})

    # ------------------------------------------------------------------ A2.2
    p("## A2.2 Estructura de carpetas")
    dir_directo: Counter = Counter(r["dir"] for r in regs)
    todos_dirs: set[str] = set()
    for d in dir_directo:
        partes = PurePosixPath(d).parts
        for k in range(1, len(partes) + 1):
            todos_dirs.add(str(PurePosixPath(*partes[:k])))
    dir_rec = {d: sum(n for dd, n in dir_directo.items() if dd == d or dd.startswith(d + "/")) for d in todos_dirs}
    p("Árbol (carpeta: imágenes directas / imágenes en total dentro):")
    for d in sorted(todos_dirs):
        prof = len(PurePosixPath(d).parts) - 1
        p(f"  {'  ' * prof}{PurePosixPath(d).name}/  {dir_directo.get(d, 0)} / {dir_rec[d]}")
    p(f"Profundidad máxima de carpetas con imágenes: {max(len(PurePosixPath(d).parts) for d in dir_directo)}")
    p(f"Carpetas inmediatas de las imágenes (candidatas a clase, tal cual): {clases}")
    niveles = defaultdict(set)
    for d in todos_dirs:
        partes = PurePosixPath(d).parts
        niveles[len(partes)].add(partes[-1])
    for n in sorted(niveles):
        p(f"  Nombres de carpeta en el nivel {n}: {sorted(niveles[n])}")
    p("Nota: este script no interpreta los nombres de carpeta; si alguno corresponde a una partición previa u otra "
      "división, hay que leerlo en el árbol de arriba.")
    p()

    # ------------------------------------------------------------------ A2.3
    p("## A2.3 Conteos")
    p(f"Total de imágenes (por extensión): {total}")
    por_clase = Counter(r["clase"] for r in regs)
    p("Imágenes por carpeta inmediata (clase candidata):")
    for c in clases:
        p(f"  {c}: {por_clase[c]} ({porcentaje(por_clase[c], total)})")
    if por_clase:
        p(f"Razón máx/mín entre carpetas inmediatas: {max(por_clase.values()) / min(por_clase.values()):.4f} "
          f"(máx {max(por_clase.values())}, mín {min(por_clase.values())})")
    por_dir = Counter(r["dir"] for r in regs)
    if len(por_dir) != len(por_clase):
        p("Imágenes por ruta completa de carpeta (hay más de un nivel o la misma clase aparece en varias carpetas):")
        for d in sorted(por_dir):
            p(f"  {d}: {por_dir[d]} ({porcentaje(por_dir[d], total)})")
        p(f"Razón máx/mín entre rutas completas: {max(por_dir.values()) / min(por_dir.values()):.4f}")
    p()

    # ------------------------------------------------------------------ A2.4
    p("## A2.4 Formato y resolución")
    ok = [r for r in regs if r["error"] is None]
    for c in clases:
        rc = [r for r in regs if r["clase"] == c]
        oc = [r for r in rc if r["error"] is None]
        p(f"### Clase {c}  (archivos {len(rc)}, decodificados {len(oc)})")
        p(f"  Extensiones: {dict(Counter(r['ext'] for r in rc))}")
        p(f"  Formato real PIL: {dict(Counter(r['formato'] for r in oc))}")
        disc = Counter((r["ext"], r["formato"]) for r in oc if FORMATO_ESPERADO.get(r["ext"].lower()) != r["formato"])
        p(f"  Extensión que no coincide con el formato real: {sum(disc.values())} {dict(disc) if disc else ''}")
        p(f"  Modos: {dict(Counter(r['modo'] for r in oc))}")
        if not oc:
            continue
        res = Counter((r["ancho"], r["alto"]) for r in oc)
        p(f"  Resoluciones distintas (ancho x alto): {len(res)}")
        for (w, h), n in res.most_common():
            p(f"    {w}x{h}: {n} ({porcentaje(n, len(oc))})")
        ori = Counter("vertical" if r["alto"] > r["ancho"] else "horizontal" if r["ancho"] > r["alto"] else "cuadrada"
                      for r in oc)
        p(f"  Orientación: {dict(ori)}")
        p(f"  Ancho: {resumen_num([r['ancho'] for r in oc])}")
        p(f"  Alto: {resumen_num([r['alto'] for r in oc])}")
        p(f"  Bytes: {resumen_num([r['bytes'] for r in rc])}")
        con_exif = [r for r in oc if r["exif_n"] > 0]
        p(f"  Con algún EXIF: {len(con_exif)} de {len(oc)}")
        for k in EXIF_CLAVES.values():
            vals = Counter(r["exif"][k] for r in oc if k in r["exif"])
            if vals:
                top = vals.most_common(8)
                p(f"    {k}: presente en {sum(vals.values())}; valores distintos {len(vals)}; "
                  f"más frecuentes {top}" if k != "DateTime" else
                  f"    {k}: presente en {sum(vals.values())}; valores distintos {len(vals)} (no se listan)")
    p("### Global")
    resg = Counter((r["ancho"], r["alto"]) for r in ok)
    p(f"  Resoluciones distintas en todo el conjunto: {len(resg)}")
    for (w, h), n in resg.most_common():
        p(f"    {w}x{h}: {n} ({porcentaje(n, len(ok))})")
    p(f"  Modos: {dict(Counter(r['modo'] for r in ok))}")
    p(f"  Formato real PIL: {dict(Counter(r['formato'] for r in ok))}")
    p()

    # ------------------------------------------------------------------ A2.5
    p("## A2.5 Archivos corruptos")
    malos = [r for r in regs if r["error"]]
    p(f"Imágenes que PIL no abre o no decodifica por completo (open + load, advertencias como error): {len(malos)}")
    for r in malos[:50]:
        p(f"  {r['ruta']}: {r['error']}; bytes {r['bytes']}; primeros 12 bytes (hex) {r.get('magia', 'n/d')}")
    if len(malos) > 50:
        p(f"  ... y {len(malos) - 50} más")
    p(f"Imágenes con error al leer EXIF (no invalida la imagen): {sum(1 for r in ok if 'exif_error' in r)}")
    p()

    # ------------------------------------------------------------------ A2.6
    p("## A2.6 Duplicados exactos")

    def grupos(clave: str, base: list[dict]):
        d: dict[str, list[dict]] = defaultdict(list)
        for r in base:
            d[r[clave]].append(r)
        return {k: v for k, v in d.items() if len(v) > 1}

    for titulo, clave, base in (("Mismo SHA-256 del archivo", "sha", regs), ("Mismos píxeles decodificados", "pix", ok)):
        g = grupos(clave, base)
        sobran = sum(len(v) - 1 for v in g.values())
        cruzan = {k: v for k, v in g.items() if len({r["clase"] for r in v}) > 1}
        p(f"{titulo}: {len(g)} grupos; archivos que sobran (total - únicos): {sobran}; "
          f"archivos implicados: {sum(len(v) for v in g.values())}; grupos que cruzan carpetas inmediatas: {len(cruzan)}")
        tam = Counter(len(v) for v in g.values())
        p(f"  Tamaños de grupo (n archivos: n grupos): {dict(sorted(tam.items()))}")
        dentro = Counter(next(iter({r['clase'] for r in v})) for v in g.values() if len({r['clase'] for r in v}) == 1)
        p(f"  Grupos dentro de una sola carpeta inmediata, por carpeta: {dict(dentro)}")
        if len(cruzan) and sum(len(v) for v in cruzan.values()) <= 30:
            for v in cruzan.values():
                p(f"  cruce: {[r['ruta'] for r in v]}")
        elif cruzan:
            p(f"  Archivos en grupos que cruzan: {sum(len(v) for v in cruzan.values())} (> 30: no se listan)")
            for v in list(cruzan.values())[:5]:
                p(f"  ejemplo de cruce: {[r['ruta'] for r in v]}")
        if 0 < len(g) and sum(len(v) for v in g.values()) <= 30:
            for v in g.values():
                p(f"  grupo: {[r['ruta'] for r in v]}")
    gp = grupos("pix", ok)
    gf = grupos("sha", regs)
    solo_pix = [v for k, v in gp.items() if len({r["sha"] for r in v}) > 1]
    p(f"Grupos de píxeles idénticos cuyos archivos difieren en bytes: {len(solo_pix)}")
    p()

    # ------------------------------------------------------------------ A2.7
    p("## A2.7 Nombres de archivo")
    p("Expresiones regulares (re.IGNORECASE, sobre el nombre de archivo sin carpeta); conteo por clase:")
    nombres = {r["ruta"]: PurePosixPath(r["ruta"]).name for r in regs}
    cab = ["patrón (regex)"] + clases + ["total"]
    p("  " + " | ".join(cab))
    for nombre, rx in PATRONES.items():
        if rx is None:
            cnt = {c: sum(1 for r in regs if r["clase"] == c and r["ext"] != r["ext"].lower()) for c in clases}
            etiqueta = "extensión con mayúsculas (comparación exacta)"
        else:
            cr = re.compile(rx, re.IGNORECASE)
            cnt = {c: sum(1 for r in regs if r["clase"] == c and cr.search(nombres[r["ruta"]])) for c in clases}
            etiqueta = f"{nombre}  [{rx}]"
        p("  " + " | ".join([etiqueta] + [str(cnt[c]) for c in clases] + [str(sum(cnt.values()))]))
    p("Plantillas de nombre (dígitos -> '#', sin extensión); más frecuentes por clase:")
    for c in clases:
        pl = Counter(re.sub(r"\d+", "#", PurePosixPath(nombres[r["ruta"]]).stem) for r in regs if r["clase"] == c)
        p(f"  {c}: {len(pl)} plantillas distintas; {pl.most_common(8)}")
    pl_g = Counter(re.sub(r"\d+", "#", PurePosixPath(nombres[r["ruta"]]).stem) for r in regs)
    p(f"Plantillas distintas en todo el conjunto: {len(pl_g)}; más frecuentes: {pl_g.most_common(8)}")
    p("Ejemplos de nombres (primeros 3 por clase, orden del zip):")
    for c in clases:
        ej = [nombres[r["ruta"]] for r in regs if r["clase"] == c][:3]
        p(f"  {c}: {ej}")
    rep = Counter(nombres.values())
    rep = {k: v for k, v in rep.items() if v > 1}
    p(f"Nombres de archivo repetidos en carpetas distintas: {len(rep)} nombres distintos; "
      f"{sum(rep.values())} archivos implicados")
    p()

    # ------------------------------------------------------------------ A2.8
    p("## A2.8 Resumen final")
    p("| Medida | Valor |")
    p("|---|---|")
    p(f"| Total de imágenes | {total} |")
    for c in clases:
        p(f"| Imágenes en «{c}» | {por_clase[c]} ({porcentaje(por_clase[c], total)}) |")
    p(f"| Resoluciones más frecuentes | {[f'{w}x{h}: {n}' for (w, h), n in resg.most_common(5)]} |")
    p(f"| Resoluciones distintas | {len(resg)} |")
    p(f"| Corruptos | {len(malos)} |")
    g_f = grupos("sha", regs)
    g_p = grupos("pix", ok)
    p(f"| Duplicados exactos de archivo | {len(g_f)} grupos, {sum(len(v) - 1 for v in g_f.values())} archivos sobran |")
    p(f"| Duplicados exactos de píxeles | {len(g_p)} grupos, {sum(len(v) - 1 for v in g_p.values())} archivos sobran |")
    p(f"| Grupos de archivo que cruzan clases | "
      f"{sum(1 for v in g_f.values() if len({r['clase'] for r in v}) > 1)} |")
    p(f"| Grupos de píxeles que cruzan clases | "
      f"{sum(1 for v in g_p.values() if len({r['clase'] for r in v}) > 1)} |")
    p(f"| .zip anidados | {len(anidados)} |")
    p(f"| Miembros que no son imágenes | {len(no_img)} |")

    SALIDA.write_text("\n".join(_lineas) + "\n", encoding="utf-8")
    print(f"\nEscrito {SALIDA.relative_to(RAIZ)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
