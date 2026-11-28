"""M2 — imágenes procesadas (JO-1, fase B) y secciones 1–2 de la plantilla común (núcleo §5.12). Sin red.

Entrada: ``Multi-Class Driver Behavior Image Dataset.zip`` (Mendeley Data, DOI 10.17632/mzb4b6dff3.1) en ``data/raw/m2/``; se
lee SIN extraerlo a disco y su tamaño y SHA-256 se verifican contra la config (``configs/m2/datos.yaml``).
Salida (núcleo §5.5 y §5.12):
  ``data/processed/m2/imagenes/<clase>/<id>.jpg``  imágenes legibles, estiradas a 224x224 (parámetros de la config);
  ``data/processed/m2/indice.csv``   ``id, archivo, clase, grupo_duplicado, split, ancho, alto``;
  ``data/processed/m2/origen.csv``   ``id, archivo_original, sha256_original, formato, modo, orientacion_exif``;
  ``results/data/m2/eda/{ficha.json, calidad.csv, diccionario.json, procesado.json}``.

Decisiones [DECIDIDO, José] (``configs/m2/datos.yaml``): se versionan todas las imágenes legibles; 224x224, estirando, bilineal,
RGB, JPEG calidad 85; los ilegibles se excluyen y se registran (no se reparan); la clase es el nombre exacto de la carpeta.
Supuestos [PROPUESTO por el orquestador, pendientes de José]:
  * ``aplicar_orientacion_exif``: se aplica ``ImageOps.exif_transpose`` antes de redimensionar.
  * ``ancho`` y ``alto`` de ``indice.csv`` son los ORIGINALES tras aplicar la orientación EXIF (no el tamaño de salida).
  * ``id`` = ``m2_NNNNN`` con NNNNN = posición (desde 1) en el orden (clase, nombre de archivo, ruta) de TODOS los miembros
    de imagen del .zip; un ilegible conserva su número y no se reutiliza, así los ids no dependen de qué se excluye.
  * ``n_variables`` = 2 (imagen y clase).
``tipo_vehiculo`` (núcleo §5.5 «si la fuente lo trae») NO se incluye: la fuente no etiqueta tipo de vehículo (F-19 de
docs/investigacion/JO-1_fuentes_m2.md). ``grupo_duplicado`` y ``split`` quedan vacías: las llena JO-3.

Un PNG con canal alfa se compone sobre ``fondo_alfa`` solo si tiene píxeles no opacos; si es totalmente opaco, ``convert("RGB")``
no pierde información.

Toda cifra de las salidas la calcula este módulo desde el .zip; todo texto de la fuente viene de la config (copiado de
docs/investigacion/JO-1_fuentes_m2.md; una prueba comprueba que son citas literales). Las salidas son deterministas: sin fechas
de ejecución ni rutas absolutas añadidas.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import platform
import re
import shutil
import warnings
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import PIL
from PIL import Image, ImageOps

from src.comun.eda import escribir_ficha
from src.comun.results import save_json

COLUMNAS_INDICE = ["id", "archivo", "clase", "grupo_duplicado", "split", "ancho", "alto"]
COLUMNAS_ORIGEN = ["id", "archivo_original", "sha256_original", "formato", "modo", "orientacion_exif"]
COLUMNAS_CALIDAD = ["categoria", "elemento", "valor", "detalle"]
INTERPOLACIONES = {"bilineal": Image.Resampling.BILINEAR}
FORMATO_POR_EXTENSION = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG"}
ETIQUETA_EXIF_ORIENTACION, ETIQUETA_EXIF_MARCA, ETIQUETA_EXIF_MODELO, ETIQUETA_EXIF_FECHA = 0x0112, 0x010F, 0x0110, 0x0132
ORIENTACIONES_QUE_CAMBIAN = range(2, 9)       # exif_transpose solo modifica la imagen con Orientation 2..8
BYTES_INICIALES_ILEGIBLE = 12
MAX_EJEMPLOS = 2
TOP_RESOLUCIONES = 10
BLOQUE = 1024 * 1024
VARIABLES_QUE_LA_FUENTE_NO_TRAE = ["tipo_vehiculo", "iluminacion", "angulo"]   # JO-1_fuentes_m2.md §7
DIRECCION_MEMORIA = re.compile(r" at 0x[0-9a-fA-F]+")
PATRON_EXIF_FECHA = re.compile(r"^(\d{4}):(\d{2}):(\d{2}) (\d{2}):(\d{2}):(\d{2})$")
# Fechas que aparecen en el NOMBRE del archivo (interpretación nuestra de patrones vistos en el inventario de la fase A).
PATRONES_NOMBRE = {
    "AAAA-MM-DDhh-mm-ss": re.compile(r"^(\d{4})-(\d{2})-(\d{2})(\d{2})-(\d{2})-(\d{2})\.[^.]+$"),
    "photo_AAAA-MM-DD_hh-mm-ss": re.compile(r"^photo_(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})"),
    "IMG_AAAAMMDD_hhmmss": re.compile(r"^IMG_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})"),
}


# --------------------------------------------------------------------------- configuración
def validar_preprocesado(prep: dict) -> dict:
    """Valida el bloque ``preprocesado`` y devuelve los parámetros ya interpretados (error ``ValueError`` con la clave)."""
    if prep.get("redimensionado") != "estirar":
        raise ValueError(f"preprocesado.redimensionado={prep.get('redimensionado')!r} no soportado (solo 'estirar')")
    if prep.get("interpolacion") not in INTERPOLACIONES:
        raise ValueError(f"preprocesado.interpolacion={prep.get('interpolacion')!r} no soportada "
                         f"(opciones: {sorted(INTERPOLACIONES)})")
    if prep.get("modo") != "RGB":
        raise ValueError(f"preprocesado.modo={prep.get('modo')!r} no soportado (solo 'RGB')")
    if prep.get("formato") != "JPEG":
        raise ValueError(f"preprocesado.formato={prep.get('formato')!r} no soportado (solo 'JPEG')")
    tamano = prep.get("tamano")
    if not (isinstance(tamano, (list, tuple)) and len(tamano) == 2 and all(isinstance(v, int) and v > 0 for v in tamano)):
        raise ValueError(f"preprocesado.tamano={tamano!r} debe ser [ancho, alto] con enteros positivos")
    calidad = prep.get("calidad_jpeg")
    if not (isinstance(calidad, int) and not isinstance(calidad, bool) and 1 <= calidad <= 95):
        raise ValueError(f"preprocesado.calidad_jpeg={calidad!r} debe ser un entero entre 1 y 95")
    if not isinstance(prep.get("aplicar_orientacion_exif"), bool):
        raise ValueError("preprocesado.aplicar_orientacion_exif debe ser true o false")
    fondo = prep.get("fondo_alfa")
    if not (isinstance(fondo, (list, tuple)) and len(fondo) == 3 and all(isinstance(v, int) and 0 <= v <= 255 for v in fondo)):
        raise ValueError(f"preprocesado.fondo_alfa={fondo!r} debe ser [R, G, B] con enteros de 0 a 255")
    return {"tamano": (int(tamano[0]), int(tamano[1])), "resample": INTERPOLACIONES[prep["interpolacion"]],
            "calidad": calidad, "exif": prep["aplicar_orientacion_exif"], "fondo": tuple(fondo)}


# --------------------------------------------------------------------------- entrada: .zip
def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(BLOQUE), b""):
            h.update(bloque)
    return h.hexdigest()


def verificar_zip(ent: dict) -> str:
    """Existe, tamaño y SHA-256 iguales a la config; devuelve el SHA-256. No se escribe nada si falla."""
    ruta = Path(ent["zip"])
    if not ruta.is_file():
        raise FileNotFoundError(f"Falta {ruta}. Descárgalo con scripts/descargar_m2.py (ver data/fuentes.md, entrada M2).")
    if ruta.stat().st_size != ent["tamano_bytes_esperado"]:
        raise ValueError(f"El tamaño de {ruta.name} es {ruta.stat().st_size} B y la config espera "
                         f"{ent['tamano_bytes_esperado']} B")
    obtenido = sha256_archivo(ruta)
    if obtenido != ent["sha256_esperado"]:
        raise ValueError(f"El SHA-256 de {ruta.name} es {obtenido} y la config espera {ent['sha256_esperado']}")
    return obtenido


def listar_miembros(z: zipfile.ZipFile, ent: dict) -> list[dict]:
    """Miembros de imagen en orden determinista (clase, nombre, ruta) con su ``id``. Error si algo no es imagen o clase."""
    clases, extensiones = set(ent["clases"]), set(ent["extensiones_imagen"])
    miembros = []
    for info in z.infolist():
        if info.is_dir():
            continue
        ruta = info.filename.replace("\\", "/")
        partes = [p for p in ruta.split("/") if p]
        if ruta.startswith("/") or ".." in partes:
            raise ValueError(f"Ruta insegura en el .zip: {info.filename!r}")
        ext = Path(partes[-1]).suffix
        if ext.lower() not in extensiones:
            raise ValueError(f"El miembro {info.filename!r} no es una imagen (extensión {ext!r}); extensiones admitidas: "
                             f"{sorted(extensiones)}")
        if len(partes) < 2 or partes[-2] not in clases:
            carpeta = partes[-2] if len(partes) >= 2 else None
            raise ValueError(f"El miembro {info.filename!r} está en la carpeta de clase desconocida {carpeta!r}; "
                             f"clases de la config: {sorted(clases)}")
        miembros.append({"info": info, "ruta": "/".join(partes), "clase": partes[-2], "nombre": partes[-1], "ext": ext})
    miembros.sort(key=lambda m: (m["clase"], m["nombre"], m["ruta"]))
    for n, m in enumerate(miembros, start=1):
        m["id"] = f"m2_{n:05d}"
    return miembros


# --------------------------------------------------------------------------- una imagen
def _leer_exif(img: Image.Image) -> tuple[dict, bool]:
    """(orientación, marca, modelo, fecha) del EXIF; el segundo valor indica que no se pudo leer (no invalida la imagen)."""
    try:
        exif = img.getexif()
        return {"orientacion": exif.get(ETIQUETA_EXIF_ORIENTACION), "marca": exif.get(ETIQUETA_EXIF_MARCA),
                "modelo": exif.get(ETIQUETA_EXIF_MODELO), "fecha": exif.get(ETIQUETA_EXIF_FECHA)}, False
    except Exception:
        return {"orientacion": None, "marca": None, "modelo": None, "fecha": None}, True


def _como_entero(valor) -> int | None:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _como_texto(valor) -> str | None:
    if valor is None:
        return None
    texto = valor.decode("latin-1") if isinstance(valor, bytes) else str(valor)
    return texto.strip("\x00 ").strip() or None


def procesar_imagen(datos: bytes, p: dict) -> dict:
    """Decodifica por completo (advertencias como error), aplica la receta y devuelve el JPEG y las medidas.

    Si no se puede abrir o decodificar: ``{"ilegible": True, "error": <tipo>, "mensaje": ...}``.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            img = Image.open(io.BytesIO(datos))
            formato, modo = img.format, img.mode
            exif, exif_error = _leer_exif(img)
            img.load()
    except Exception as e:                     # cualquier fallo de apertura o decodificación = ilegible
        # se quita la dirección de memoria del BytesIO («at 0x…») que algunas versiones de Pillow ponen en el mensaje
        return {"ilegible": True, "error": type(e).__name__, "mensaje": DIRECCION_MEMORIA.sub("", str(e))}
    orientacion = _como_entero(exif["orientacion"])
    tam_sin_exif = img.size
    aplicada = bool(p["exif"] and orientacion in ORIENTACIONES_QUE_CAMBIAN)
    if p["exif"]:
        img = ImageOps.exif_transpose(img)
    tam_original = img.size                    # ancho y alto del índice: originales, tras la orientación EXIF
    alfa = {"tiene_alfa": False, "fraccion_no_opaca": 0.0}
    if img.mode in ("RGBA", "LA", "PA") or "transparency" in img.info:
        rgba = img.convert("RGBA")
        canal = np.asarray(rgba.getchannel("A"))
        no_opacos = int((canal != 255).sum())
        alfa = {"tiene_alfa": True, "fraccion_no_opaca": no_opacos / canal.size}
        if no_opacos:
            lienzo = Image.new("RGB", rgba.size, p["fondo"])
            lienzo.paste(rgba, mask=rgba.getchannel("A"))
            img = lienzo
        else:
            img = rgba.convert("RGB")
    else:
        img = img.convert("RGB")
    img = img.resize(p["tamano"], p["resample"])
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=p["calidad"])
    return {"ilegible": False, "jpeg": buf.getvalue(), "formato": formato, "modo": modo, "orientacion": orientacion,
            "orientacion_aplicada": aplicada, "exif_error": exif_error, "marca": _como_texto(exif["marca"]),
            "modelo": _como_texto(exif["modelo"]), "fecha_exif": _como_texto(exif["fecha"]),
            "tam_sin_exif": tam_sin_exif, "tam_original": tam_original, "alfa": alfa}


# --------------------------------------------------------------------------- medidas agregadas
def _dict_ordenado(c: Counter) -> dict:
    return {str(k): int(c[k]) for k in sorted(c, key=str)}


def _resoluciones(c: Counter) -> list[list]:
    orden = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
    return [[k, int(v)] for k, v in orden[:TOP_RESOLUCIONES]]


def _resumen_fechas(fechas: list[dt.datetime]) -> dict:
    if not fechas:
        return {"n": 0, "minimo": None, "maximo": None, "por_anio_mes": {}}
    meses = Counter(f"{f.year:04d}-{f.month:02d}" for f in fechas)
    return {"n": len(fechas), "minimo": min(fechas).isoformat(sep=" "), "maximo": max(fechas).isoformat(sep=" "),
            "por_anio_mes": _dict_ordenado(meses)}


def _fecha_de(patron: re.Pattern, texto: str) -> dt.datetime | None | bool:
    """None si el texto no tiene la forma; False si la tiene pero no es una fecha válida; si no, la fecha."""
    m = patron.match(texto)
    if m is None:
        return None
    try:
        return dt.datetime(*(int(g) for g in m.groups()))
    except ValueError:
        return False


def medir_fechas(legibles: list[dict]) -> dict:
    """Fechas que aparecen en el EXIF y en los nombres de archivo. Solo descriptivo: no hay fecha por imagen declarada."""
    exif, exif_invalidas = [], 0
    for r in legibles:
        if r["fecha_exif"] is None:
            continue
        f = _fecha_de(PATRON_EXIF_FECHA, r["fecha_exif"])
        if isinstance(f, dt.datetime):
            exif.append(f)
        else:
            exif_invalidas += 1
    nombres = {}
    for etiqueta, patron in PATRONES_NOMBRE.items():
        validas, invalidas = [], 0
        for r in legibles:
            f = _fecha_de(patron, r["nombre"])
            if isinstance(f, dt.datetime):
                validas.append(f)
            elif f is False:
                invalidas += 1
        nombres[etiqueta] = {**_resumen_fechas(validas), "con_forma_pero_no_fecha_valida": invalidas}
    return {"exif_datetime": {**_resumen_fechas(exif), "no_interpretables": exif_invalidas},
            "nombres_de_archivo": nombres,
            "nota": ("Fechas medidas en el archivo, sin interpretar: la fuente declara «October 2024» (periodo) y no da una "
                     "fecha por imagen; el patrón del nombre es una lectura nuestra de los nombres vistos en la fase A.")}


def _diferencia(declarado: int, medido: int) -> int:
    return medido - declarado


def comparar_declarado(cfg: dict, por_clase_zip: Counter, por_clase_leg: Counter, total_zip: int, total_leg: int,
                       res_exif: Counter) -> dict:
    dec = cfg["declarado"]
    ancho, alto = dec["resolucion"]
    por_clase = {c: {"declarado": n, "medido_en_zip": int(por_clase_zip.get(c, 0)),
                     "medido_legibles": int(por_clase_leg.get(c, 0)),
                     "diferencia_zip": _diferencia(n, int(por_clase_zip.get(c, 0))),
                     "diferencia_legibles": _diferencia(n, int(por_clase_leg.get(c, 0)))}
                 for c, n in dec["por_clase"].items()}
    return {
        "fuente_de_lo_declarado": dec["fuente"],
        "total": {"declarado": dec["total"], "medido_en_zip": total_zip, "medido_legibles": total_leg,
                  "diferencia_zip": _diferencia(dec["total"], total_zip),
                  "diferencia_legibles": _diferencia(dec["total"], total_leg)},
        "por_clase": por_clase,
        "resolucion_declarada": f"{ancho}x{alto}",
        "texto_resolucion_declarada": dec["texto_resolucion"],
        "imagenes_con_la_resolucion_declarada": int(res_exif.get(f"{ancho}x{alto}", 0)),
        "imagenes_con_la_resolucion_declarada_en_cualquier_orientacion":
            int(res_exif.get(f"{ancho}x{alto}", 0) + (res_exif.get(f"{alto}x{ancho}", 0) if ancho != alto else 0)),
        "nota_correspondencia": ("La correspondencia de las clases declaradas con las carpetas es por nombre (inferencia "
                                 "nuestra; «Others» ↔ other_activities)."),
    }


def construir_conteos(cfg: dict, miembros: list[dict], resultados: list[dict]) -> tuple[dict, list[dict]]:
    """Todos los conteos de ``ficha.json`` y las filas de ``calidad.csv`` (medidos sobre el .zip)."""
    legibles = [r for r in resultados if not r["ilegible"]]
    ilegibles = [r for r in resultados if r["ilegible"]]
    aplicar = cfg["preprocesado"]["aplicar_orientacion_exif"]
    por_clase_zip = Counter(r["clase"] for r in resultados)
    por_clase_leg = Counter(r["clase"] for r in legibles)
    res_exif = Counter(f"{r['tam_original'][0]}x{r['tam_original'][1]}" for r in legibles)
    res_sin = Counter(f"{r['tam_sin_exif'][0]}x{r['tam_sin_exif'][1]}" for r in legibles)
    orient = Counter(str(r["orientacion"]) if r["orientacion"] is not None else "sin_orientacion" for r in legibles)
    aplicadas = [r for r in legibles if r["orientacion_aplicada"]]
    ejemplos = {}
    por_valor = Counter(str(r["orientacion"]) for r in aplicadas)
    for valor in sorted(por_valor):
        ejemplos[valor] = [r["id"] for r in aplicadas if str(r["orientacion"]) == valor][:MAX_EJEMPLOS]
    alfa_r = [r for r in legibles if r["alfa"]["tiene_alfa"]]
    no_opacos = [{"id": r["id"], "fraccion_pixeles_no_opacos": r["alfa"]["fraccion_no_opaca"]}
                 for r in alfa_r if r["alfa"]["fraccion_no_opaca"] > 0]
    fondo = cfg["preprocesado"]["fondo_alfa"]
    decision_alfa = (f"composición sobre fondo {list(fondo)} en las {len(no_opacos)} con píxeles no opacos; "
                     "convert('RGB') en las demás" if no_opacos
                     else "convert('RGB') sin pérdida: el alfa es totalmente opaco en todas")
    mismatch = [r for r in legibles if FORMATO_POR_EXTENSION.get(r["ext"].lower()) != r["formato"]]
    conteos = {
        "total_en_zip": len(resultados), "ilegibles": len(ilegibles), "legibles": len(legibles),
        "por_clase_en_zip": _dict_ordenado(por_clase_zip), "por_clase_legibles": _dict_ordenado(por_clase_leg),
        "ilegibles_por_clase": _dict_ordenado(Counter(r["clase"] for r in ilegibles)),
        "extensiones_en_zip": _dict_ordenado(Counter(r["ext"] for r in resultados)),
        "formatos": _dict_ordenado(Counter(r["formato"] for r in legibles)),
        "modos": _dict_ordenado(Counter(r["modo"] for r in legibles)),
        "extension_distinta_del_formato_real": len(mismatch),
        "resoluciones_tras_exif_mas_frecuentes": _resoluciones(res_exif),
        "resoluciones_distintas_tras_exif": len(res_exif),
        "resoluciones_sin_exif_mas_frecuentes": _resoluciones(res_sin),
        "resoluciones_distintas_sin_exif": len(res_sin),
        "exif": {
            "aplicar_orientacion_exif": aplicar, "orientacion_distribucion": _dict_ordenado(orient),
            "orientacion_aplicada_n": len(aplicadas), "orientacion_aplicada_por_valor": _dict_ordenado(por_valor),
            "ejemplos_por_orientacion": ejemplos, "errores_de_lectura": sum(1 for r in legibles if r["exif_error"]),
            "marca": _dict_ordenado(Counter(r["marca"] for r in legibles if r["marca"])),
            "modelo": _dict_ordenado(Counter(r["modelo"] for r in legibles if r["modelo"])),
        },
        "png_alfa": {
            "n_png": sum(1 for r in legibles if r["formato"] == "PNG"),
            "n_rgba": sum(1 for r in legibles if r["modo"] == "RGBA"),
            "n_con_alfa_no_opaco": len(no_opacos), "n_alfa_totalmente_opaco": len(alfa_r) - len(no_opacos),
            "no_opacos": no_opacos, "decision": decision_alfa,
        },
        "fechas_medidas": medir_fechas(legibles),
        "declarado_vs_medido": comparar_declarado(cfg, por_clase_zip, por_clase_leg, len(resultados), len(legibles), res_exif),
        "variables_que_la_fuente_no_trae": VARIABLES_QUE_LA_FUENTE_NO_TRAE,
    }
    return conteos, filas_calidad(conteos, ilegibles, mismatch)


def filas_calidad(conteos: dict, ilegibles: list[dict], mismatch: list[dict]) -> list[dict]:
    filas = []
    for r in ilegibles:
        filas.append({"categoria": "ilegible", "elemento": r["ruta"], "valor": r["error"],
                      "detalle": f"{r['mensaje']}; bytes {r['bytes']}; primeros {BYTES_INICIALES_ILEGIBLE} bytes (hex) "
                                 f"{r['bytes_iniciales_hex']}; id reservado {r['id']} (no se reutiliza)"})
    exif = conteos["exif"]
    for valor, n in exif["orientacion_aplicada_por_valor"].items():
        filas.append({"categoria": "orientacion_aplicada", "elemento": valor, "valor": n,
                      "detalle": f"ejemplos (id): {', '.join(exif['ejemplos_por_orientacion'][valor])}"})
    a = conteos["png_alfa"]
    filas.append({"categoria": "png_alfa", "elemento": "png_rgba", "valor": a["n_rgba"],
                  "detalle": f"PNG {a['n_png']}; alfa opaco {a['n_alfa_totalmente_opaco']}; no opaco "
                             f"{a['n_con_alfa_no_opaco']}; {a['decision']}"})
    for r in a["no_opacos"]:
        filas.append({"categoria": "png_alfa_no_opaco", "elemento": r["id"], "valor": r["fraccion_pixeles_no_opacos"],
                      "detalle": "fracción de píxeles con alfa distinto de 255"})
    for r in mismatch:
        filas.append({"categoria": "extension_distinta_del_formato", "elemento": r["ruta"], "valor": r["formato"],
                      "detalle": f"extensión {r['ext']}"})
    d = conteos["declarado_vs_medido"]
    t = d["total"]
    filas.append({"categoria": "declarado_vs_medido", "elemento": "total", "valor": t["medido_legibles"],
                  "detalle": f"declarado {t['declarado']}; medido en el .zip {t['medido_en_zip']}; legibles "
                             f"{t['medido_legibles']}; diferencia (legibles - declarado) {t['diferencia_legibles']}"})
    for clase, c in d["por_clase"].items():
        filas.append({"categoria": "declarado_vs_medido", "elemento": clase, "valor": c["medido_legibles"],
                      "detalle": f"declarado {c['declarado']}; medido en el .zip {c['medido_en_zip']}; legibles "
                                 f"{c['medido_legibles']}; diferencia (legibles - declarado) {c['diferencia_legibles']}"})
    top = conteos["resoluciones_tras_exif_mas_frecuentes"][0]
    filas.append({"categoria": "declarado_vs_medido", "elemento": "resolucion",
                  "valor": d["imagenes_con_la_resolucion_declarada"],
                  "detalle": f"declarada {d['resolucion_declarada']}; imágenes con esa resolución "
                             f"{d['imagenes_con_la_resolucion_declarada']} (en cualquier orientación "
                             f"{d['imagenes_con_la_resolucion_declarada_en_cualquier_orientacion']}); la más frecuente medida "
                             f"es {top[0]} con {top[1]} imágenes; {conteos['resoluciones_distintas_tras_exif']} resoluciones distintas"})
    return filas


# --------------------------------------------------------------------------- documentos de salida
def construir_ficha(cfg: dict, sha_zip: str, conteos: dict) -> dict:
    f = cfg["fuente"]
    return {
        "fuente": f["nombre"], "cita": " ".join(f["cita"].split()), "url": f["url"],
        "fecha_descarga": f["fecha_descarga"], "sha256": sha_zip,
        "unidad_de_observacion": " ".join(f["unidad_de_observacion"].split()),
        "n_registros": conteos["legibles"], "n_variables": f["n_variables"],
        "n_variables_justificacion": " ".join(f["n_variables_justificacion"].split()),
        "periodo": {k: " ".join(str(v).split()) for k, v in f["periodo"].items()},
        "conteos": conteos,
    }


def construir_diccionario(cfg: dict) -> dict:
    d = cfg["diccionario"]
    clases = {}
    for clase in cfg["entrada"]["clases"]:
        if clase not in d["clases"]:
            raise ValueError(f"diccionario.clases de la config no define la clase {clase!r}")
        entrada = d["clases"][clase]
        clases[clase] = {"carpeta": clase}
        for origen in ("articulo", "mendeley"):
            e = entrada[origen]
            clases[clase][origen] = {"nombre": e["nombre"], "fuente": e["fuente"], "elidido": e["elidido"],
                                     "texto": " ".join(e["texto"].split())}
    return {
        "nota": " ".join(d["nota"].split()),
        "nota_variables": ("La fuente no publica un diccionario de variables por imagen: solo describe las 5 clases (carpetas). "
                           "TODO(dato-faltante): metadatos por imagen (docs/investigacion/JO-1_fuentes_m2.md §7)."),
        "clases": clases,
        "diferencias_entre_fuentes": " ".join(d["diferencias_entre_fuentes"].split()),
    }


def _csv(df: pd.DataFrame, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta, index=False, encoding="utf-8", lineterminator="\n")


# --------------------------------------------------------------------------- principal
def main(cfg: dict) -> int:
    ent, sal, prep_cfg = cfg["entrada"], cfg["salida"], cfg["preprocesado"]
    # 1) Todo se lee, se procesa y se valida en memoria antes de escribir: si algo falla, no queda nada a medias.
    p = validar_preprocesado(prep_cfg)
    diccionario = construir_diccionario(cfg)
    sha_zip = verificar_zip(ent)
    resultados, jpegs = [], {}
    with zipfile.ZipFile(ent["zip"]) as z:
        miembros = listar_miembros(z, ent)
        for n, m in enumerate(miembros, start=1):
            datos = z.read(m["info"])
            r = procesar_imagen(datos, p)
            r.update(id=m["id"], clase=m["clase"], nombre=m["nombre"], ext=m["ext"], ruta=m["ruta"],
                     sha256_original=hashlib.sha256(datos).hexdigest())
            if r["ilegible"]:
                r.update(bytes=len(datos), bytes_iniciales_hex=datos[:BYTES_INICIALES_ILEGIBLE].hex())
            else:
                jpegs[m["id"]] = r.pop("jpeg")
            resultados.append(r)
            if n % 1000 == 0:
                print(f"  {n}/{len(miembros)} imágenes revisadas", flush=True)
    legibles = [r for r in resultados if not r["ilegible"]]
    if not legibles:
        raise ValueError("Ninguna imagen del .zip es legible; no se escribe nada")
    conteos, filas = construir_conteos(cfg, miembros, resultados)
    ficha = construir_ficha(cfg, sha_zip, conteos)

    indice = pd.DataFrame([{"id": r["id"], "archivo": f"{sal['imagenes']}/{r['clase']}/{r['id']}.jpg", "clase": r["clase"],
                            "grupo_duplicado": "", "split": "", "ancho": r["tam_original"][0],
                            "alto": r["tam_original"][1]} for r in legibles], columns=COLUMNAS_INDICE)
    origen = pd.DataFrame([{"id": r["id"], "archivo_original": r["ruta"], "sha256_original": r["sha256_original"],
                            "formato": r["formato"], "modo": r["modo"],
                            "orientacion_exif": "" if r["orientacion"] is None else r["orientacion"]}
                           for r in legibles], columns=COLUMNAS_ORIGEN)
    calidad = pd.DataFrame(filas, columns=COLUMNAS_CALIDAD)

    # 2) Escritura. La carpeta de imágenes es nuestra: se recrea para que no queden archivos de corridas anteriores.
    salida, eda = Path(sal["carpeta"]), Path(sal["eda"])
    dir_imagenes = salida / sal["imagenes"]
    if dir_imagenes.exists():
        shutil.rmtree(dir_imagenes)
    huella_imagenes = hashlib.sha256()
    for r in legibles:
        destino = dir_imagenes / r["clase"] / f"{r['id']}.jpg"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(jpegs[r["id"]])
        huella_imagenes.update(jpegs[r["id"]])
    _csv(indice, salida / sal["indice"])
    _csv(origen, salida / sal["origen"])
    escribir_ficha(eda / "ficha.json", ficha)
    _csv(calidad, eda / "calidad.csv")
    save_json(eda / "diccionario.json", diccionario)
    save_json(eda / "procesado.json", {
        "n_imagenes": len(legibles),
        "sha256_indice": sha256_archivo(salida / sal["indice"]),
        "sha256_imagenes": huella_imagenes.hexdigest(),
        "definicion_huella_imagenes": ("SHA-256 de la concatenación de los bytes de cada JPEG procesado, en orden de id "
                                       "(el mismo orden de indice.csv)"),
        "python": platform.python_version(), "pillow": PIL.__version__, "config": cfg,
    })
    _imprimir(conteos, [salida / sal["indice"], salida / sal["origen"], eda / "ficha.json", eda / "calidad.csv",
                        eda / "diccionario.json", eda / "procesado.json"])
    return 0


def _imprimir(c: dict, archivos: list[Path]) -> None:
    print(f"Imágenes en el .zip: {c['total_en_zip']} · legibles: {c['legibles']} · ilegibles: {c['ilegibles']}")
    print("Legibles por clase: " + " · ".join(f"{k} {v}" for k, v in c["por_clase_legibles"].items()))
    print(f"Orientación EXIF aplicada: {c['exif']['orientacion_aplicada_n']} · PNG con alfa no opaco: "
          f"{c['png_alfa']['n_con_alfa_no_opaco']} de {c['png_alfa']['n_png']}")
    for f in archivos:
        print(f"  {f.as_posix()} ({f.stat().st_size} B)")
