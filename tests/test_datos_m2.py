"""Pruebas sin red ni data/raw/ de src/m2_conduccion/datos.py (JO-1, fase B): imágenes procesadas de M2, índice, origen y
secciones 1–2 de la plantilla común (núcleo §5.12).

El .zip de pruebas (tests/fixtures/m2/driver_prueba.zip) lo genera tests/fixtures/m2/generar.py por código; si falta, esta
suite lo vuelve a generar. Conteo a mano del fixture (9 imágenes, 1 ilegible):

    ids (orden por clase y nombre de archivo, sobre los 9 miembros; el ilegible conserva su número):
      m2_00001 other_activities/img_4.jpg          40x40
      m2_00002 other_activities/img_roto.jpg       ILEGIBLE (excluido)
      m2_00003 other_activities/translucida.png    20x20, alfa 0 en la mitad izquierda
      m2_00004 safe_driving/IMG_2.JPG              48x64
      m2_00005 safe_driving/img_1.jpg              64x48
      m2_00006 talking_phone/foto_exif6.jpg        60x40 con Orientation 6 -> 40x60
      m2_00007 talking_phone/foto_exif8.jpg        50x30 con Orientation 8 -> 30x50
      m2_00008 texting_phone/captura.png           80x60, alfa opaco
      m2_00009 turning/img_3.jpg                   100x70
    legibles por clase: other_activities 2, safe_driving 2, talking_phone 2, texting_phone 1, turning 1 (total 8).
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import re
import socket
import struct
import zipfile
from pathlib import Path

import pandas as pd
import PIL
import pytest
import yaml
from PIL import Image, ImageOps

from src.comun.eda import validar_ficha
from src.m2_conduccion import datos as dm

RAIZ = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "m2"
ZIP_PRUEBA = FIXTURES / "driver_prueba.zip"
CONFIG_REAL = RAIZ / "configs" / "m2" / "datos.yaml"
FUENTES_MD = RAIZ / "docs" / "investigacion" / "JO-1_fuentes_m2.md"
PROCESADO_REAL = RAIZ / "data" / "processed" / "m2"
EDA_REAL = RAIZ / "results" / "data" / "m2" / "eda"
RAIZ_ZIP = "Multi-Class Driver Behavior Image Dataset"

# Oráculo: las columnas se repiten a propósito (no se importan de dm) para que renombrarlas en el código rompa la prueba.
COLUMNAS_INDICE = ["id", "archivo", "clase", "grupo_duplicado", "split", "ancho", "alto"]
COLUMNAS_ORIGEN = ["id", "archivo_original", "sha256_original", "formato", "modo", "orientacion_exif"]
COLUMNAS_HALLAZGOS = ["categoria", "elemento", "valor", "detalle"]     # calidad.csv de M2 es una tabla de hallazgos
EVIDENCIA_JPEG85 = RAIZ / "alucinaciones" / "evidencias" / "JO-1" / "experimento_jpeg85_salida.txt"
# id -> (clase, nombre en el zip, ancho y alto tras la orientación EXIF)
ESPERADO = {
    "m2_00001": ("other_activities", "img_4.jpg", 40, 40),
    "m2_00003": ("other_activities", "translucida.png", 20, 20),
    "m2_00004": ("safe_driving", "IMG_2.JPG", 48, 64),
    "m2_00005": ("safe_driving", "img_1.jpg", 64, 48),
    "m2_00006": ("talking_phone", "foto_exif6.jpg", 40, 60),
    "m2_00007": ("talking_phone", "foto_exif8.jpg", 30, 50),
    "m2_00008": ("texting_phone", "captura.png", 80, 60),
    "m2_00009": ("turning", "img_3.jpg", 100, 70),
}
ID_ILEGIBLE = "m2_00002"
LEGIBLES_POR_CLASE = {"other_activities": 2, "safe_driving": 2, "talking_phone": 2, "texting_phone": 1, "turning": 1}


def _generador():
    spec = importlib.util.spec_from_file_location("generar_fixture_m2", FIXTURES / "generar.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def zip_prueba() -> Path:
    if not ZIP_PRUEBA.is_file():
        _generador().construir_zip(ZIP_PRUEBA)
    return ZIP_PRUEBA


def _sha(ruta: Path) -> str:
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def _config(tmp_path: Path, zip_prueba: Path, **cambios) -> dict:
    """Config real (configs/m2/datos.yaml) apuntando al fixture y a carpetas temporales."""
    cfg = yaml.safe_load(CONFIG_REAL.read_text(encoding="utf-8"))
    cfg["entrada"]["zip"] = str(zip_prueba)
    cfg["entrada"]["sha256_esperado"] = _sha(zip_prueba)
    cfg["entrada"]["tamano_bytes_esperado"] = zip_prueba.stat().st_size
    cfg["salida"]["carpeta"] = str(tmp_path / "processed")
    cfg["salida"]["eda"] = str(tmp_path / "eda")
    for ruta, valor in cambios.items():
        bloque, clave = ruta.split(".")
        cfg[bloque][clave] = valor
    return cfg


def _correr(cfg: dict) -> tuple[Path, Path]:
    assert dm.main(cfg) == 0
    return Path(cfg["salida"]["carpeta"]), Path(cfg["salida"]["eda"])


def _leer(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(ruta, dtype=str, keep_default_na=False)


def _miembro(zip_prueba: Path, clase: str, nombre: str) -> bytes:
    with zipfile.ZipFile(zip_prueba) as z:
        return z.read(f"{RAIZ_ZIP}/{clase}/{nombre}")


def _esperado_jpeg(datos: bytes, tamano=(224, 224), calidad=85, exif=True, fondo=(255, 255, 255)) -> bytes:
    """Oráculo independiente: la receta de la config aplicada a mano con PIL."""
    img = Image.open(io.BytesIO(datos))
    img.load()
    if exif:
        img = ImageOps.exif_transpose(img)
    if img.mode == "RGBA":
        lienzo = Image.new("RGB", img.size, tuple(fondo))
        lienzo.paste(img, mask=img.getchannel("A"))
        img = lienzo
    else:
        img = img.convert("RGB")
    img = img.resize(tuple(tamano), Image.Resampling.BILINEAR)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=calidad)
    return buf.getvalue()


@pytest.fixture(autouse=True)
def sin_red(monkeypatch):
    def _bloqueado(*a, **k):
        raise AssertionError("M2 no debe abrir conexiones de red")

    monkeypatch.setattr(socket, "socket", _bloqueado)
    monkeypatch.setattr(socket, "create_connection", _bloqueado)


# --------------------------------------------------------------------------- salida de imágenes
def test_salida_224_rgb_jpeg(tmp_path, zip_prueba):
    procesado, _ = _correr(_config(tmp_path, zip_prueba))
    indice = _leer(procesado / "indice.csv")
    assert list(indice["id"]) == sorted(ESPERADO)
    for _, fila in indice.iterrows():
        ruta = procesado / fila["archivo"]
        assert ruta.is_file()
        with Image.open(ruta) as img:
            assert img.format == "JPEG"
            assert img.mode == "RGB"
            assert img.size == (224, 224)


def test_receta_igual_al_oraculo_bytes(tmp_path, zip_prueba):
    """JPEG normal, EXIF 6, EXIF 8 y PNG translúcido coinciden byte a byte con la receta aplicada a mano."""
    procesado, _ = _correr(_config(tmp_path, zip_prueba))
    for id_ in ("m2_00005", "m2_00006", "m2_00007", "m2_00003", "m2_00008"):
        clase, nombre, _, _ = ESPERADO[id_]
        obtenido = (procesado / "imagenes" / clase / f"{id_}.jpg").read_bytes()
        assert obtenido == _esperado_jpeg(_miembro(zip_prueba, clase, nombre)), id_


def test_archivo_relativo_a_la_carpeta_procesada(tmp_path, zip_prueba):
    procesado, _ = _correr(_config(tmp_path, zip_prueba))
    indice = _leer(procesado / "indice.csv")
    for _, fila in indice.iterrows():
        assert fila["archivo"] == f"imagenes/{fila['clase']}/{fila['id']}.jpg"


# --------------------------------------------------------------------------- ilegibles
def test_ilegible_excluido_y_registrado(tmp_path, zip_prueba):
    procesado, eda = _correr(_config(tmp_path, zip_prueba))
    indice = _leer(procesado / "indice.csv")
    origen = _leer(procesado / "origen.csv")
    assert ID_ILEGIBLE not in set(indice["id"]) | set(origen["id"])
    assert not any("img_roto" in a for a in origen["archivo_original"])
    assert not list((procesado / "imagenes").rglob(f"{ID_ILEGIBLE}.jpg"))
    calidad = _leer(eda / "calidad.csv")
    ilegibles = calidad[calidad["categoria"] == "ilegible"]
    assert len(ilegibles) == 1
    fila = ilegibles.iloc[0]
    assert fila["elemento"] == f"{RAIZ_ZIP}/other_activities/img_roto.jpg"
    assert "UnidentifiedImageError" in fila["valor"]
    assert "000000000000000000000000" in fila["detalle"]      # primeros 12 bytes en cero, en hex
    ficha = json.loads((eda / "ficha.json").read_text(encoding="utf-8"))
    c = ficha["conteos"]
    assert (c["total_en_zip"], c["ilegibles"], c["legibles"]) == (9, 1, 8)
    assert c["ilegibles_por_clase"] == {"other_activities": 1}
    assert c["por_clase_en_zip"]["other_activities"] == 3
    assert c["por_clase_legibles"] == LEGIBLES_POR_CLASE


# --------------------------------------------------------------------------- orientación EXIF
def test_orientacion_exif_aplicada(tmp_path, zip_prueba):
    procesado, eda = _correr(_config(tmp_path, zip_prueba))
    indice = _leer(procesado / "indice.csv").set_index("id")
    # 60x40 con Orientation 6 y 50x30 con Orientation 8: ancho y alto se intercambian
    assert (indice.loc["m2_00006", "ancho"], indice.loc["m2_00006", "alto"]) == ("40", "60")
    assert (indice.loc["m2_00007", "ancho"], indice.loc["m2_00007", "alto"]) == ("30", "50")
    origen = _leer(procesado / "origen.csv").set_index("id")
    assert origen.loc["m2_00006", "orientacion_exif"] == "6"
    assert origen.loc["m2_00007", "orientacion_exif"] == "8"
    assert origen.loc["m2_00005", "orientacion_exif"] == ""
    ficha = json.loads((eda / "ficha.json").read_text(encoding="utf-8"))
    exif = ficha["conteos"]["exif"]
    assert exif["orientacion_aplicada_n"] == 2
    assert exif["ejemplos_por_orientacion"] == {"6": ["m2_00006"], "8": ["m2_00007"]}
    assert exif["aplicar_orientacion_exif"] is True


def test_orientacion_exif_desactivada_por_config(tmp_path, zip_prueba):
    cfg = _config(tmp_path, zip_prueba)
    cfg["preprocesado"]["aplicar_orientacion_exif"] = False
    procesado, eda = _correr(cfg)
    indice = _leer(procesado / "indice.csv").set_index("id")
    assert (indice.loc["m2_00006", "ancho"], indice.loc["m2_00006", "alto"]) == ("60", "40")
    clase, nombre, _, _ = ESPERADO["m2_00006"]
    obtenido = (procesado / "imagenes" / clase / "m2_00006.jpg").read_bytes()
    assert obtenido == _esperado_jpeg(_miembro(zip_prueba, clase, nombre), exif=False)
    ficha = json.loads((eda / "ficha.json").read_text(encoding="utf-8"))
    assert ficha["conteos"]["exif"]["orientacion_aplicada_n"] == 0


# --------------------------------------------------------------------------- PNG con alfa
def test_png_alfa_medido_y_compuesto_sobre_fondo(tmp_path, zip_prueba):
    procesado, eda = _correr(_config(tmp_path, zip_prueba))
    ficha = json.loads((eda / "ficha.json").read_text(encoding="utf-8"))
    alfa = ficha["conteos"]["png_alfa"]
    assert alfa["n_png"] == 2 and alfa["n_rgba"] == 2
    assert alfa["n_con_alfa_no_opaco"] == 1 and alfa["n_alfa_totalmente_opaco"] == 1
    assert alfa["no_opacos"] == [{"id": "m2_00003", "fraccion_pixeles_no_opacos": 0.5}]
    calidad = _leer(eda / "calidad.csv")
    assert len(calidad[calidad["categoria"] == "png_alfa_no_opaco"]) == 1
    # con fondo negro la mitad izquierda queda oscura
    cfg = _config(tmp_path / "negro", zip_prueba)
    cfg["preprocesado"]["fondo_alfa"] = [0, 0, 0]
    proc2, _ = _correr(cfg)
    with Image.open(proc2 / "imagenes" / "other_activities" / "m2_00003.jpg") as img:
        assert max(img.getpixel((10, 100))) < 16


# --------------------------------------------------------------------------- índice y origen
def test_columnas_y_valores_del_indice(tmp_path, zip_prueba):
    procesado, _ = _correr(_config(tmp_path, zip_prueba))
    indice = _leer(procesado / "indice.csv")
    assert list(indice.columns) == COLUMNAS_INDICE                 # sin tipo_vehiculo: la fuente no lo etiqueta
    assert (indice["grupo_duplicado"] == "").all() and (indice["split"] == "").all()   # las llena JO-3
    for _, fila in indice.iterrows():
        clase, _nombre, ancho, alto = ESPERADO[fila["id"]]
        assert (fila["clase"], int(fila["ancho"]), int(fila["alto"])) == (clase, ancho, alto)


def test_columnas_y_trazabilidad_del_origen(tmp_path, zip_prueba):
    procesado, _ = _correr(_config(tmp_path, zip_prueba))
    origen = _leer(procesado / "origen.csv")
    assert list(origen.columns) == COLUMNAS_ORIGEN
    assert list(origen["id"]) == sorted(ESPERADO)
    for _, fila in origen.iterrows():
        clase, nombre, _, _ = ESPERADO[fila["id"]]
        assert fila["archivo_original"] == f"{RAIZ_ZIP}/{clase}/{nombre}"
        assert fila["sha256_original"] == hashlib.sha256(_miembro(zip_prueba, clase, nombre)).hexdigest()
        assert fila["formato"] == ("PNG" if nombre.endswith(".png") else "JPEG")
        assert fila["modo"] == ("RGBA" if nombre.endswith(".png") else "RGB")


def test_ids_unicos_y_estables(tmp_path, zip_prueba):
    procesado, _ = _correr(_config(tmp_path, zip_prueba))
    ids = list(_leer(procesado / "indice.csv")["id"])
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"m2_\d{5}", i) for i in ids)
    assert ids == sorted(ESPERADO)           # el id lo fija el orden (clase, nombre) de TODOS los miembros del .zip
    # quitar un miembro legible no cambia el id de los demás que lo preceden, pero el ilegible conserva su número
    # (m2_00002 no se reutiliza): ids = {1, 3, 4, ...}
    assert ID_ILEGIBLE not in ids and "m2_00001" in ids and "m2_00003" in ids


# --------------------------------------------------------------------------- determinismo
def _instantanea(*carpetas: Path) -> dict[str, bytes]:
    return {f"{i}/{p.relative_to(c).as_posix()}": p.read_bytes()
            for i, c in enumerate(carpetas) for p in sorted(c.rglob("*")) if p.is_file()}


def test_dos_corridas_identicas_byte_a_byte(tmp_path, zip_prueba):
    cfg = _config(tmp_path, zip_prueba)
    procesado, eda = _correr(cfg)
    primera = _instantanea(procesado, eda)
    assert primera
    _correr(cfg)
    assert _instantanea(procesado, eda) == primera


def test_corrida_en_otra_carpeta_da_las_mismas_imagenes(tmp_path, zip_prueba):
    p1, _ = _correr(_config(tmp_path / "a", zip_prueba))
    p2, _ = _correr(_config(tmp_path / "b", zip_prueba))
    assert _instantanea(p1) == _instantanea(p2)


def test_corrida_nueva_borra_imagenes_viejas(tmp_path, zip_prueba):
    cfg = _config(tmp_path, zip_prueba)
    procesado, _ = _correr(cfg)
    viejo = procesado / cfg["salida"]["imagenes"] / "turning" / "m2_99999.jpg"
    viejo.write_bytes(b"x")
    _correr(cfg)
    assert not viejo.exists()


# --------------------------------------------------------------------------- ficha, calidad, diccionario, procesado
def test_ficha_valida_y_con_la_fuente(tmp_path, zip_prueba):
    cfg = _config(tmp_path, zip_prueba)
    _, eda = _correr(cfg)
    ficha = json.loads((eda / "ficha.json").read_text(encoding="utf-8"))
    validar_ficha(ficha)
    assert ficha["n_registros"] == 8 and ficha["n_variables"] == 2
    assert ficha["sha256"] == _sha(zip_prueba)
    assert ficha["cita"] == " ".join(cfg["fuente"]["cita"].split())
    assert ficha["url"] == "https://doi.org/10.17632/mzb4b6dff3.1"
    assert ficha["fecha_descarga"] == "2026-11-27"
    assert ficha["periodo"]["rotulo"] == "según el artículo"
    assert "October 2024" in ficha["periodo"]["texto"]
    assert ficha["n_variables_justificacion"]
    assert "tipo_vehiculo" in ficha["conteos"]["variables_que_la_fuente_no_trae"]


def test_conteos_de_la_ficha_medidos(tmp_path, zip_prueba):
    _, eda = _correr(_config(tmp_path, zip_prueba))
    c = json.loads((eda / "ficha.json").read_text(encoding="utf-8"))["conteos"]
    assert c["formatos"] == {"JPEG": 6, "PNG": 2}
    assert c["modos"] == {"RGB": 6, "RGBA": 2}
    assert c["extensiones_en_zip"] == {".JPG": 1, ".jpg": 6, ".png": 2}
    res = dict(map(tuple, c["resoluciones_tras_exif_mas_frecuentes"]))
    assert res["40x40"] == 1 and res["48x64"] == 1 and sum(res.values()) == 8
    assert c["resoluciones_distintas_tras_exif"] == 8
    assert c["resoluciones_distintas_sin_exif"] == 8        # 60x40 y 50x30 sin orientar; 40x40, 20x20, 48x64, 64x48, 80x60, 100x70
    assert c["extension_distinta_del_formato_real"] == 0


def test_declarado_vs_medido(tmp_path, zip_prueba):
    cfg = _config(tmp_path, zip_prueba)
    _, eda = _correr(cfg)
    dec = json.loads((eda / "ficha.json").read_text(encoding="utf-8"))["conteos"]["declarado_vs_medido"]
    assert dec["total"] == {"declarado": 7286, "medido_en_zip": 9, "medido_legibles": 8,
                            "diferencia_zip": 9 - 7286, "diferencia_legibles": 8 - 7286}
    assert dec["por_clase"]["turning"] == {"declarado": 1343, "medido_en_zip": 1, "medido_legibles": 1,
                                           "diferencia_zip": 1 - 1343, "diferencia_legibles": 1 - 1343}
    assert dec["por_clase"]["other_activities"]["medido_en_zip"] == 3
    assert dec["por_clase"]["other_activities"]["medido_legibles"] == 2
    assert dec["resolucion_declarada"] == "400x600"
    assert dec["imagenes_con_la_resolucion_declarada"] == 0
    calidad = _leer(eda / "calidad.csv")
    assert (calidad["categoria"] == "declarado_vs_medido").any()


def test_calidad_csv_columnas(tmp_path, zip_prueba):
    _, eda = _correr(_config(tmp_path, zip_prueba))
    calidad = _leer(eda / "calidad.csv")
    assert list(calidad.columns) == COLUMNAS_HALLAZGOS == dm.COLUMNAS_HALLAZGOS
    assert {"ilegible", "orientacion_aplicada", "declarado_vs_medido", "png_alfa",
            "diferencia_con_app"} <= set(calidad["categoria"])


def test_diccionario_citado_de_la_fuente(tmp_path, zip_prueba):
    _, eda = _correr(_config(tmp_path, zip_prueba))
    dic = json.loads((eda / "diccionario.json").read_text(encoding="utf-8"))
    assert set(dic["clases"]) == set(LEGIBLES_POR_CLASE)
    for clase, d in dic["clases"].items():
        for fuente in ("articulo", "mendeley"):
            assert d[fuente]["texto"] and d[fuente]["fuente"] and "elidido" in d[fuente], (clase, fuente)
    assert dic["diferencias_entre_fuentes"]


def test_textos_de_la_config_son_citas_literales_de_la_fase_a():
    """Cada definición de la config es subcadena (sin contar saltos de línea) de docs/investigacion/JO-1_fuentes_m2.md."""
    if not FUENTES_MD.is_file():
        pytest.skip("falta docs/investigacion/JO-1_fuentes_m2.md")
    fuente = " ".join(FUENTES_MD.read_text(encoding="utf-8").split())
    cfg = yaml.safe_load(CONFIG_REAL.read_text(encoding="utf-8"))
    for clase, d in cfg["diccionario"]["clases"].items():
        for origen in ("articulo", "mendeley"):
            texto = " ".join(d[origen]["texto"].split())
            assert texto in fuente, f"{clase}/{origen}: la definición no está literal en JO-1_fuentes_m2.md"
    assert " ".join(cfg["declarado"]["texto_resolucion"].split()) in fuente
    assert " ".join(cfg["fuente"]["cita"].split()).replace("Multi-class driver behavior image dataset",
                                                             "*Multi-class driver behavior image dataset*") in fuente


def test_procesado_json_huellas(tmp_path, zip_prueba):
    cfg = _config(tmp_path, zip_prueba)
    procesado, eda = _correr(cfg)
    p = json.loads((eda / "procesado.json").read_text(encoding="utf-8"))
    assert p["sha256_indice"] == _sha(procesado / "indice.csv")
    h = hashlib.sha256()
    for id_ in sorted(ESPERADO):
        h.update((procesado / "imagenes" / ESPERADO[id_][0] / f"{id_}.jpg").read_bytes())
    assert p["sha256_imagenes"] == h.hexdigest()
    assert p["n_imagenes"] == 8
    assert p["config"]["preprocesado"] == cfg["preprocesado"]
    assert p["pillow"] == PIL.__version__
    assert re.fullmatch(r"\d+\.\d+\.\d+", p["python"])


# --------------------------------------------------------------------------- parámetros de la config
def test_tamano_leido_de_la_config(tmp_path, zip_prueba):
    cfg = _config(tmp_path, zip_prueba)
    cfg["preprocesado"]["tamano"] = [32, 48]
    procesado, _ = _correr(cfg)
    ruta = procesado / "imagenes" / "turning" / "m2_00009.jpg"
    with Image.open(ruta) as img:
        assert img.size == (32, 48)
    assert ruta.read_bytes() == _esperado_jpeg(_miembro(zip_prueba, "turning", "img_3.jpg"), tamano=(32, 48))
    # ancho/alto del índice son los ORIGINALES, no el tamaño de salida
    fila = _leer(procesado / "indice.csv").set_index("id").loc["m2_00009"]
    assert (fila["ancho"], fila["alto"]) == ("100", "70")


def test_calidad_jpeg_leida_de_la_config(tmp_path, zip_prueba):
    alta, _ = _correr(_config(tmp_path / "alta", zip_prueba))
    cfg = _config(tmp_path / "baja", zip_prueba)
    cfg["preprocesado"]["calidad_jpeg"] = 20
    baja, _ = _correr(cfg)
    ruta = Path("imagenes") / "turning" / "m2_00009.jpg"
    assert (baja / ruta).stat().st_size < (alta / ruta).stat().st_size
    assert (baja / ruta).read_bytes() == _esperado_jpeg(_miembro(zip_prueba, "turning", "img_3.jpg"), calidad=20)


def test_parametros_de_preprocesado_no_soportados_fallan(tmp_path, zip_prueba):
    for clave, valor in (("interpolacion", "bicubica"), ("redimensionado", "recortar"), ("modo", "L"), ("formato", "PNG")):
        cfg = _config(tmp_path / clave, zip_prueba)
        cfg["preprocesado"][clave] = valor
        with pytest.raises(ValueError, match=clave):
            dm.main(cfg)
        assert not (Path(cfg["salida"]["carpeta"]) / "indice.csv").exists()


def _prep_valido() -> dict:
    return yaml.safe_load(CONFIG_REAL.read_text(encoding="utf-8"))["preprocesado"]


@pytest.mark.parametrize("clave, valor", [
    ("calidad_jpeg", 0), ("calidad_jpeg", 96), ("calidad_jpeg", "85"), ("calidad_jpeg", True), ("calidad_jpeg", 85.0),
    ("aplicar_orientacion_exif", "true"), ("aplicar_orientacion_exif", 1), ("aplicar_orientacion_exif", None),
    ("fondo_alfa", [255, 255]), ("fondo_alfa", [256, 0, 0]), ("fondo_alfa", [0, 0, -1]), ("fondo_alfa", "blanco"),
    ("fondo_alfa", [255, 255, 255.0]), ("tamano", [224]), ("tamano", [0, 224]),
])
def test_validar_preprocesado_rechaza_valores_invalidos(clave, valor):
    prep = _prep_valido()
    prep[clave] = valor
    with pytest.raises(ValueError, match=clave):
        dm.validar_preprocesado(prep)


def test_validar_preprocesado_acepta_la_config_real_y_los_limites():
    p = dm.validar_preprocesado(_prep_valido())
    assert (p["tamano"], p["calidad"], p["exif"], p["fondo"]) == ((224, 224), 85, True, (255, 255, 255))
    limites = {**_prep_valido(), "calidad_jpeg": 1, "fondo_alfa": [0, 0, 0], "aplicar_orientacion_exif": False}
    assert dm.validar_preprocesado(limites)["calidad"] == 1
    assert dm.validar_preprocesado({**limites, "calidad_jpeg": 95})["calidad"] == 95


# --------------------------------------------------------------------------- casos borde del .zip
def _zip_con(tmp_path: Path, contenido: dict[str, bytes], nombre: str = "borde.zip") -> Path:
    return _generador().construir_zip(tmp_path / nombre, contenido)


def _crudo(tmp_path: Path, miembros: dict[str, bytes], nombre: str = "crudo.zip") -> Path:
    """Zip sin la jerarquía del fixture: los nombres se escriben tal cual (para rutas inseguras)."""
    ruta = tmp_path / nombre
    with zipfile.ZipFile(ruta, "w") as z:
        for n, d in miembros.items():
            z.writestr(n, d)
    return ruta


def test_zip_sin_ninguna_imagen_legible_falla_sin_escribir(tmp_path):
    g = _generador().miembros()
    ruta = _crudo(tmp_path, {f"{RAIZ_ZIP}/turning/a.jpg": g["other_activities/img_roto.jpg"],
                             f"{RAIZ_ZIP}/safe_driving/b.png": b"no es una imagen"})
    cfg = _config(tmp_path, ruta)
    with pytest.raises(ValueError, match="Ninguna imagen"):
        dm.main(cfg)
    assert not Path(cfg["salida"]["carpeta"]).exists() and not Path(cfg["salida"]["eda"]).exists()


@pytest.mark.parametrize("nombre", ["../fuera.jpg", f"{RAIZ_ZIP}/../turning/x.jpg", "/abs/turning/x.jpg",
                                    "turning\\..\\x.jpg"])
def test_miembro_con_ruta_insegura_falla_sin_escribir(tmp_path, nombre):
    g = _generador().miembros()
    ruta = _crudo(tmp_path, {nombre: g["turning/img_3.jpg"]})
    cfg = _config(tmp_path, ruta)
    with pytest.raises(ValueError, match="insegura"):
        dm.main(cfg)
    assert not Path(cfg["salida"]["carpeta"]).exists() and not Path(cfg["salida"]["eda"]).exists()


def test_png_que_en_realidad_es_jpeg_se_registra(tmp_path):
    g = _generador().miembros()
    ruta = _zip_con(tmp_path, {"turning/falso.png": g["turning/img_3.jpg"], "turning/ok.jpg": g["turning/img_3.jpg"]})
    procesado, eda = _correr(_config(tmp_path, ruta))
    c = json.loads((eda / "ficha.json").read_text(encoding="utf-8"))["conteos"]
    assert c["extension_distinta_del_formato_real"] == 1
    assert c["formatos"] == {"JPEG": 2}
    calidad = _leer(eda / "calidad.csv")
    fila = calidad[calidad["categoria"] == "extension_distinta_del_formato"]
    assert list(fila["elemento"]) == [f"{RAIZ_ZIP}/turning/falso.png"]
    assert list(fila["valor"]) == ["JPEG"] and "extensión .png" in fila.iloc[0]["detalle"]
    assert len(_leer(procesado / "indice.csv")) == 2           # se procesa igual: el formato real manda, no la extensión


def test_leer_exif_acota_las_excepciones():
    class _Roto:
        def __init__(self, error):
            self._error = error

        def getexif(self):
            raise self._error

    vacio = {"orientacion": None, "marca": None, "modelo": None, "fecha": None}
    for error in (struct.error("x"), ValueError("x"), SyntaxError("x"), KeyError("x"), TypeError("x"), OSError("x")):
        assert dm._leer_exif(_Roto(error)) == (vacio, True)
    with pytest.raises(RuntimeError):                          # un fallo no previsto no se traga en silencio
        dm._leer_exif(_Roto(RuntimeError("inesperado")))


# --------------------------------------------------------------------------- diferencia con la app (decisión 27-nov)
def test_diferencia_con_la_app_declarada_en_ficha_y_calidad(tmp_path, zip_prueba):
    cfg = _config(tmp_path, zip_prueba)
    _, eda = _correr(cfg)
    d = json.loads((eda / "ficha.json").read_text(encoding="utf-8"))["conteos"]["diferencias_con_app"]
    assert d["decision"].startswith("[DECIDIDO, José, 27-nov]")
    assert d["evidencia"].startswith("alucinaciones/evidencias/JO-1/experimento_jpeg85_salida.txt")
    assert d["muestra_imagenes"] == 292
    assert d["diferencia_absoluta_media_niveles"] == 2.741
    assert (d["mediana"], d["p95"], d["p99"], d["maximo"]) == (2, 9, 14, 90)
    assert d["fraccion_fuera_de_mas_menos_1"] == 0.5572
    assert d["calidad_jpeg_del_entrenamiento"] == cfg["preprocesado"]["calidad_jpeg"]
    calidad = _leer(eda / "calidad.csv")
    fila = calidad[calidad["categoria"] == "diferencia_con_app"]
    assert len(fila) == 1
    assert fila.iloc[0]["valor"] == "2.741" and "55,7 %" in fila.iloc[0]["detalle"]
    assert "alucinaciones/evidencias/JO-1/experimento_jpeg85_salida.txt" in fila.iloc[0]["detalle"]


def test_diferencia_con_la_app_copia_las_cifras_de_la_evidencia():
    """Las cifras de la config se copian (no se re-miden) del archivo de evidencia del cazador."""
    if not EVIDENCIA_JPEG85.is_file():
        pytest.skip("falta el archivo de evidencia del cazador")
    texto = EVIDENCIA_JPEG85.read_text(encoding="utf-8")
    d = yaml.safe_load(CONFIG_REAL.read_text(encoding="utf-8"))["diferencias_con_app"]
    assert f"Muestra: {d['muestra_imagenes']} imagenes" in texto
    assert f"{d['valores_de_canal']} valores de canal" in texto
    assert f"medio por valor de canal: {d['diferencia_absoluta_media_niveles']} niveles" in texto
    assert f"{d['mediana']} / {d['p95']} / {d['p99']} / {d['maximo']}" in texto
    assert f"+-1 de la paridad de la app): {d['fraccion_fuera_de_mas_menos_1']}" in texto
    mae = d["mae_por_imagen"]
    assert f"min {mae['minimo']:.3f} / mediana {mae['mediana']:.3f} / max {mae['maximo']:.3f}" in texto


# --------------------------------------------------------------------------- validaciones de entrada
def test_sha256_distinto_falla_sin_escribir(tmp_path, zip_prueba):
    cfg = _config(tmp_path, zip_prueba)
    cfg["entrada"]["sha256_esperado"] = "0" * 64
    with pytest.raises(ValueError, match="SHA-256"):
        dm.main(cfg)
    assert not Path(cfg["salida"]["carpeta"]).exists() and not Path(cfg["salida"]["eda"]).exists()


def test_falta_el_zip_falla_con_mensaje(tmp_path, zip_prueba):
    cfg = _config(tmp_path, zip_prueba)
    cfg["entrada"]["zip"] = str(tmp_path / "no_existe.zip")
    with pytest.raises(FileNotFoundError, match="descargar_m2"):
        dm.main(cfg)


def test_carpeta_de_clase_desconocida_falla(tmp_path, zip_prueba):
    cfg = _config(tmp_path, zip_prueba)
    cfg["entrada"]["clases"] = ["safe_driving", "turning"]
    with pytest.raises(ValueError, match="clase"):
        dm.main(cfg)
    assert not Path(cfg["salida"]["carpeta"]).exists()


def test_miembro_que_no_es_imagen_falla(tmp_path):
    zpath = tmp_path / "raro.zip"
    with zipfile.ZipFile(zpath, "w") as z:
        z.writestr(f"{RAIZ_ZIP}/turning/notas.txt", b"hola")
    cfg = _config(tmp_path, zpath)
    with pytest.raises(ValueError, match="notas.txt"):
        dm.main(cfg)


def _arbol(carpeta: Path) -> set[str]:
    return {p.relative_to(carpeta).as_posix() for p in carpeta.rglob("*")}


def test_no_deja_archivos_fuera_de_la_carpeta_de_salida(tmp_path, zip_prueba, monkeypatch):
    """Comportamiento: leer el .zip no lo extrae; tras la corrida solo aparecen archivos nuevos bajo las dos carpetas de salida."""
    trabajo = tmp_path / "trabajo"
    trabajo.mkdir()
    monkeypatch.chdir(trabajo)                                   # una extracción relativa caería aquí
    antes_fixtures = _arbol(FIXTURES)
    cfg = _config(tmp_path / "salida", zip_prueba)
    _correr(cfg)
    assert _arbol(trabajo) == set()
    assert _arbol(FIXTURES) == antes_fixtures
    nuevos = _arbol(tmp_path / "salida")
    assert nuevos and all(n.split("/")[0] in {"processed", "eda"} for n in nuevos)


def test_config_real_esta_completa():
    cfg = yaml.safe_load(CONFIG_REAL.read_text(encoding="utf-8"))
    assert cfg["preprocesado"]["tamano"] == [224, 224]
    assert cfg["preprocesado"]["interpolacion"] == "bilineal" and cfg["preprocesado"]["calidad_jpeg"] == 85
    assert cfg["entrada"]["clases"] == ["other_activities", "safe_driving", "talking_phone", "texting_phone", "turning"]
    assert cfg["declarado"]["total"] == sum(cfg["declarado"]["por_clase"].values())
    assert cfg["preprocesado"]["aplicar_orientacion_exif"] is True and cfg["fuente"]["n_variables"] == 2


def test_decisiones_de_jose_del_27_nov_quedan_marcadas():
    """Lo que antes era [PROPUESTO] y José decidió el 27-nov se rotula [DECIDIDO, José, 27-nov] en config y docstring."""
    config = CONFIG_REAL.read_text(encoding="utf-8")
    codigo = Path(dm.__file__).read_text(encoding="utf-8")
    assert "[PROPUESTO" not in config and "[PROPUESTO" not in codigo
    assert config.count("[DECIDIDO, José, 27-nov]") >= 4 and "[DECIDIDO, José, 27-nov]" in codigo


# --------------------------------------------------------------------------- procesados reales (si existen)
def test_procesados_reales_versionados():
    indice_ruta = PROCESADO_REAL / "indice.csv"
    huellas = EDA_REAL / "procesado.json"
    if not (indice_ruta.is_file() and huellas.is_file()):
        pytest.skip("no existen los procesados reales de M2 (se generan con run.py m2-datos)")
    indice = _leer(indice_ruta)
    assert len(indice) == 7276
    assert list(indice.columns) == COLUMNAS_INDICE
    assert indice["id"].is_unique
    p = json.loads(huellas.read_text(encoding="utf-8"))
    assert p["sha256_indice"] == _sha(indice_ruta)
    h = hashlib.sha256()
    for _, fila in indice.sort_values("id").iterrows():
        ruta = PROCESADO_REAL / fila["archivo"]
        assert ruta.is_file(), fila["archivo"]
        h.update(ruta.read_bytes())
    assert h.hexdigest() == p["sha256_imagenes"]
    assert p["n_imagenes"] == 7276
