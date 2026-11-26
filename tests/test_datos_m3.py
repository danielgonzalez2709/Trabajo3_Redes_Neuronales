"""Pruebas sin red de src/m3_recomendacion/datos.py (JJ-1, fase B): interacciones, usuarios y destinos de M3 y las
secciones 1–2 de la plantilla común (núcleo §5.12).

Todo con los CSV ficticios de tests/fixtures/m3/ (mismas columnas y orden que los 4 CSV reales de Kaggle) y un JSON de
metadatos ficticio con la misma estructura que usa el código. Nombres, correos y textos de reseña del fixture son
ficticios («UsuarioPruebaA», «@prueba.invalid», «Texto de prueba 1»); la prueba de privacidad exige que no salgan.

Conteo a mano del fixture (5 usuarios, 7 destinos, 4 lugares):
    reseñas   (usuario, destino): (1,1) (2,2) (1,3) (3,5)          calificaciones 5, 3, 4, 1
    historial (usuario, destino): (1,2) (2,4) (4,1) (3,6)          calificaciones 4, 2, 5, 3
    unión: 8 pares distintos; usuarios que aparecen {1,2,3,4}; destinos que aparecen {1,2,3,4,5,6}; usuario 5 sin nada.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import socket
import zipfile
from pathlib import Path

import pandas as pd
import pytest
import yaml

from src.comun.eda import COLUMNAS_CALIDAD, validar_ficha
from src.m3_recomendacion import datos as dm

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "m3"
DESTINOS, RESENAS = "Expanded_Destinations.csv", "Final_Updated_Expanded_Reviews.csv"
HISTORIAL, USUARIOS = "Final_Updated_Expanded_UserHistory.csv", "Final_Updated_Expanded_Users.csv"
ZIP, META = "archive.zip", "kaggle_metadata_prueba.json"
CSV = [DESTINOS, RESENAS, HISTORIAL, USUARIOS]

FRAGMENTOS = {
    "generado": "generated for educational and research purposes",
    "diversidad_de_genero": "enriched with gender diversity",
    "uso": "Free to use for tests only.",
    "licencia": "CC0: Public Domain - fixture text.",
}
COMPONENTES = {
    DESTINOS: ("Fictitious destinations, including type of destination (beach, mountain, historical site, etc.), "
               "popularity and best time to visit."),
    RESENAS: "Fictitious reviews and ratings for the destinations.",
    HISTORIAL: "Fictitious records of past visits and ratings.",
    USUARIOS: "Fictitious profiles of users including their preferences. This fixture has been enriched with gender diversity.",
}
PROHIBIDOS_EN_SALIDAS = ["UsuarioPrueba", "usuarioprueba", "prueba.invalid", "Texto de prueba"]


# --------------------------------------------------------------------------- entorno de juguete
def sha(ruta: Path) -> str:
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def montar(tmp_path: Path, csv: dict | None = None, meta=None, cfg_extra=None) -> dict:
    """Copia los fixtures a ``tmp_path/raw`` (con ``csv`` {archivo: texto} sustituyendo archivos y ``meta`` una función
    que modifica el JSON de metadatos), crea el .zip, calcula los SHA-256 y devuelve la config."""
    raw = tmp_path / "raw"
    raw.mkdir(parents=True)
    for nombre in CSV:
        shutil.copy(FIXTURES / nombre, raw / nombre)
    for nombre, texto in (csv or {}).items():
        (raw / nombre).write_text(texto, encoding="utf-8", newline="\n")
    metadatos = json.loads((FIXTURES / META).read_text(encoding="utf-8"))
    if meta is not None:
        meta(metadatos)
    (raw / META).write_text(json.dumps(metadatos), encoding="utf-8")
    with zipfile.ZipFile(raw / ZIP, "w") as z:
        for nombre in CSV:
            z.write(raw / nombre, nombre)
    cfg = {
        "entrada": {"carpeta": str(raw), "destinos": DESTINOS, "resenas": RESENAS, "historial": HISTORIAL,
                    "usuarios": USUARIOS, "zip": ZIP, "metadatos_fuente": str(raw / META)},
        "sha256_esperado": {nombre: sha(raw / nombre) for nombre in [*CSV, ZIP]},
        "fuente": {"nombre": "Conjunto Ficticio de Prueba", "autor": "Autor Ficticio", "usuario_kaggle": "ficticio",
                   "ref": "ficticio/prueba", "url": "https://ejemplo.invalid/prueba", "version": 1,
                   "fecha_creacion_version": "2024-01-23T17:07:26.487Z", "fecha_descarga": "2026-11-25",
                   "descargo": "Persona de prueba, a mano", "cita": "Autor Ficticio. (2024). Prueba. Ejemplo."},
        "citas_literales": dict(FRAGMENTOS),
        "componentes": dict(COMPONENTES),
        "conclusion_real_o_sintetico": "Conclusión de prueba.",
        "ficha": {"tope_usuarios_por_interacciones": 5, "k_max_periodicidad": 10, "palabra_sintetico": "synthetic",
                  "tipo_mencionado_sin_datos": "mountain"},
        "salida": {"carpeta": str(tmp_path / "proc"), "destinos": "destinos.parquet", "usuarios": "usuarios.parquet",
                   "interacciones": "interacciones.parquet", "eda": str(tmp_path / "eda")},
    }
    if cfg_extra is not None:
        cfg_extra(cfg)
    return cfg


def salidas(tmp_path: Path) -> dict[str, Path]:
    return {"destinos": tmp_path / "proc" / "destinos.parquet", "usuarios": tmp_path / "proc" / "usuarios.parquet",
            "interacciones": tmp_path / "proc" / "interacciones.parquet", "ficha": tmp_path / "eda" / "ficha.json",
            "calidad": tmp_path / "eda" / "calidad.csv", "diccionario": tmp_path / "eda" / "diccionario.json"}


@pytest.fixture
def corrida(tmp_path):
    cfg = montar(tmp_path)
    assert dm.main(cfg) == 0
    s = salidas(tmp_path)
    return {"cfg": cfg, "ruta": s, "destinos": pd.read_parquet(s["destinos"]), "usuarios": pd.read_parquet(s["usuarios"]),
            "inter": pd.read_parquet(s["interacciones"]),
            "ficha": json.loads(s["ficha"].read_text(encoding="utf-8")),
            "dic": json.loads(s["diccionario"].read_text(encoding="utf-8"))}


def con_fila(archivo: str, fila: str) -> str:
    return (FIXTURES / archivo).read_text(encoding="utf-8") + fila + "\n"


# --------------------------------------------------------------------------- interacciones (D1)
def test_la_union_no_repite_ni_pierde_pares(corrida):
    inter = corrida["inter"]
    esperados = {(1, 1), (2, 2), (1, 3), (3, 5), (1, 2), (2, 4), (4, 1), (3, 6)}
    assert len(inter) == 4 + 4 == len(esperados)
    assert set(zip(inter["usuario_id"], inter["destino_id"])) == esperados
    assert not inter.duplicated(["usuario_id", "destino_id"]).any()
    assert list(inter.columns) == ["usuario_id", "destino_id", "origen", "id_origen", "calificacion", "fecha_visita"]
    assert inter["origen"].value_counts().to_dict() == {"resena": 4, "historial": 4}
    assert list(inter["usuario_id"]) == sorted(inter["usuario_id"])  # orden por (usuario_id, destino_id)
    assert "split" not in inter.columns


def test_calificacion_origen_y_fecha_de_cada_par(corrida):
    inter = corrida["inter"].set_index(["usuario_id", "destino_id"])
    assert inter.loc[(1, 1), ["origen", "id_origen", "calificacion"]].tolist() == ["resena", 1, 5]
    assert inter.loc[(3, 6), ["origen", "id_origen", "calificacion"]].tolist() == ["historial", 4, 3]
    assert pd.isna(inter.loc[(1, 1), "fecha_visita"])
    assert pd.Timestamp(inter.loc[(4, 1), "fecha_visita"]) == pd.Timestamp("2024-03-20")


def test_un_par_repetido_en_un_archivo_es_error(tmp_path):
    cfg = montar(tmp_path, csv={RESENAS: con_fila(RESENAS, "5,1,1,2,Texto de prueba 2")})  # (usuario 1, destino 1) otra vez
    with pytest.raises(ValueError, match=r"repetid.*\(1, 1\)"):
        dm.main(cfg)


def test_un_par_repetido_entre_los_dos_archivos_es_error(tmp_path):
    cfg = montar(tmp_path, csv={HISTORIAL: con_fila(HISTORIAL, "5,1,1,2024-01-01,2")})  # (1, 1) ya está en reseñas
    with pytest.raises(ValueError, match=r"repetid.*\(1, 1\)"):
        dm.main(cfg)


def test_ids_huerfanos_son_error(tmp_path):
    cfg = montar(tmp_path, csv={RESENAS: con_fila(RESENAS, "5,1,99,2,Texto de prueba 2")})
    with pytest.raises(ValueError, match="usuario.*99"):
        dm.main(cfg)
    cfg = montar(tmp_path / "otro", csv={HISTORIAL: con_fila(HISTORIAL, "5,1,98,2024-01-01,2")})
    with pytest.raises(ValueError, match="destino.*98"):
        dm.main(cfg)


def test_todo_id_de_las_interacciones_existe_en_las_maestras(corrida):
    inter, usuarios, destinos = corrida["inter"], corrida["usuarios"], corrida["destinos"]
    assert set(inter["usuario_id"]) <= set(usuarios["usuario_id"])
    assert set(inter["destino_id"]) <= set(destinos["destino_id"])


# --------------------------------------------------------------------------- usuarios y destinos (D2, D6)
def test_preferencias_normalizadas_y_una_columna_por_opcion_medida(corrida):
    u = corrida["usuarios"].set_index("usuario_id")
    assert u.loc[1, "preferencias"] == "Beaches, Historical"
    assert u.loc[3, "preferencias"] == "Beaches, Historical"      # «Historical, Beaches» se ordena
    assert u.loc[2, "preferencias"] == "Adventure, Nature"        # «Nature, Adventure» se ordena
    pref = [c for c in u.columns if c.startswith("pref_")]
    assert pref == ["pref_adventure", "pref_beaches", "pref_historical", "pref_nature"]
    assert {c: bool(u.loc[1, c]) for c in pref} == {"pref_adventure": False, "pref_beaches": True,
                                                    "pref_historical": True, "pref_nature": False}
    assert {c: bool(u.loc[2, c]) for c in pref} == {"pref_adventure": True, "pref_beaches": False,
                                                    "pref_historical": False, "pref_nature": True}
    assert all(u[c].dtype == bool for c in pref)


def test_columnas_y_orden_de_usuarios_y_destinos(corrida):
    assert list(corrida["usuarios"].columns) == ["usuario_id", "preferencias", "pref_adventure", "pref_beaches",
                                                 "pref_historical", "pref_nature", "genero", "n_adultos", "n_ninos"]
    assert list(corrida["destinos"].columns) == ["destino_id", "nombre", "lugar", "estado", "tipo", "mejor_epoca",
                                                 "popularidad"]
    assert list(corrida["usuarios"]["usuario_id"]) == [1, 2, 3, 4, 5]
    assert list(corrida["destinos"]["destino_id"]) == [1, 2, 3, 4, 5, 6, 7]
    u = corrida["usuarios"].set_index("usuario_id")
    assert (u.loc[1, "genero"], u.loc[1, "n_adultos"], u.loc[1, "n_ninos"]) == ("Female", 2, 1)


def test_lugar_agrupa_los_ids_del_mismo_nombre(corrida):
    d = corrida["destinos"]
    por_lugar = d.groupby("lugar")["destino_id"].apply(list).to_dict()
    assert por_lugar == {"lugar_ficticio_uno": [1, 3], "lugar_ficticio_dos": [2, 4],
                         "lugar_ficticio_tres": [5, 6], "lugar_ficticio_cuatro": [7]}
    assert d.set_index("destino_id").loc[1, "nombre"] == "Lugar Ficticio Uno"
    assert d.set_index("destino_id").loc[2, "popularidad"] == 9.0


def test_clave_de_lugar():
    assert dm.clave_lugar("Taj Mahal") == "taj_mahal"
    assert dm.clave_lugar("  Leh   Ladakh ") == "leh_ladakh"
    assert dm.clave_lugar("Jammu & Kashmir (Norte)") == "jammu_kashmir_norte"


def test_un_nombre_con_dos_combinaciones_es_error(tmp_path):
    texto = (FIXTURES / DESTINOS).read_text(encoding="utf-8").replace(
        "3,Lugar Ficticio Uno,Estado Ficticio A", "3,Lugar Ficticio Uno,Estado Ficticio OTRO")
    cfg = montar(tmp_path, csv={DESTINOS: texto})
    with pytest.raises(ValueError, match="Lugar Ficticio Uno"):
        dm.main(cfg)


def test_dos_nombres_distintos_con_la_misma_clave_de_lugar_son_error(tmp_path):
    texto = (FIXTURES / DESTINOS).read_text(encoding="utf-8").replace("Lugar Ficticio Dos", "Lugar-Ficticio Dos", 1)
    cfg = montar(tmp_path, csv={DESTINOS: texto})
    # id 2 pasa a «Lugar-Ficticio Dos»; id 4 sigue en «Lugar Ficticio Dos»: dos nombres, misma clave → error
    with pytest.raises(ValueError, match="lugar_ficticio_dos"):
        dm.main(cfg)


def test_name_email_y_reviewtext_no_salen_en_ninguna_salida(tmp_path, corrida):
    prohibidas = {"name", "email", "reviewtext", "review_text", "texto", "correo", "nombre_usuario"}
    for clave in ("destinos", "usuarios", "inter"):
        df = corrida[clave]
        assert not ({c.lower() for c in df.columns} & prohibidas)
        for col in df.columns:
            if df[col].dtype == object or str(df[col].dtype) in ("str", "string"):
                for valor in df[col].astype(str):
                    assert not any(p.lower() in valor.lower() for p in PROHIBIDOS_EN_SALIDAS)
    for ruta in corrida["ruta"].values():
        crudo = ruta.read_bytes()
        for p in PROHIBIDOS_EN_SALIDAS:
            assert p.encode() not in crudo, f"{p!r} aparece en {ruta.name}"
    cal = pd.read_csv(corrida["ruta"]["calidad"])
    assert not (set(cal["columna"].str.lower()) & prohibidas)


# --------------------------------------------------------------------------- ficha: escala, densidad, usuarios
def test_escala_y_frecuencias_de_cada_calificacion(corrida):
    esc = corrida["ficha"]["conteos"]["escala_calificacion"]
    assert esc["resena"] == {"minimo": 1, "maximo": 5, "valores": [1, 3, 4, 5],
                             "frecuencias": {"1": 1, "3": 1, "4": 1, "5": 1}}
    assert esc["historial"] == {"minimo": 2, "maximo": 5, "valores": [2, 3, 4, 5],
                                "frecuencias": {"2": 1, "3": 1, "4": 1, "5": 1}}
    assert set(esc) >= {"resena", "historial", "union"}
    assert esc["union"]["frecuencias"] == {"1": 1, "2": 1, "3": 2, "4": 2, "5": 2}


def test_conteos_y_densidad_contra_el_conteo_a_mano(corrida):
    c = corrida["ficha"]["conteos"]
    assert (c["usuarios_maestra"], c["destinos_maestra"], c["lugares"]) == (5, 7, 4)
    assert c["interacciones"] == {"resena": 4, "historial": 4, "union": 8}
    assert c["usuarios_que_aparecen"] == {"resena": 3, "historial": 4, "union": 4}
    assert c["destinos_que_aparecen"] == {"resena": 4, "historial": 4, "union": 6}
    d = c["densidad"]
    assert d["resena"]["maestras"] == pytest.approx(4 / (5 * 7))
    assert d["resena"]["los_que_aparecen"] == pytest.approx(4 / (3 * 4))
    assert d["historial"]["maestras"] == pytest.approx(4 / (5 * 7))
    assert d["historial"]["los_que_aparecen"] == pytest.approx(4 / (4 * 4))
    assert d["union"]["maestras"] == pytest.approx(8 / (5 * 7))
    assert d["union"]["los_que_aparecen"] == pytest.approx(8 / (4 * 6))


def test_usuarios_por_numero_de_interacciones_sobre_todos_los_maestros(corrida):
    u = corrida["ficha"]["conteos"]["usuarios_por_numero_de_interacciones"]
    # unión: usuarios 1..5 con 3, 2, 2, 1, 0 interacciones
    assert u["union"] == {"0": 1, "1": 1, "2": 2, "3": 1, "4": 0, "5+": 0}
    assert u["resena"] == {"0": 2, "1": 2, "2": 1, "3": 0, "4": 0, "5+": 0}
    assert u["historial"] == {"0": 1, "1": 4, "2": 0, "3": 0, "4": 0, "5+": 0}
    assert sum(u["union"].values()) == 5


def test_la_cola_5_mas_depende_del_parametro(tmp_path):
    cfg = montar(tmp_path, cfg_extra=lambda c: c["ficha"].update(tope_usuarios_por_interacciones=3))
    dm.main(cfg)
    ficha = json.loads(salidas(tmp_path)["ficha"].read_text(encoding="utf-8"))
    assert ficha["conteos"]["usuarios_por_numero_de_interacciones"]["union"] == {"0": 1, "1": 1, "2": 2, "3+": 1}


def test_variables_de_contenido(corrida):
    v = corrida["ficha"]["conteos"]["variables_de_contenido"]
    assert v["usuarios"]["preferencias"]["n_categorias"] == 2        # «Beaches, Historical» y «Adventure, Nature»
    assert v["usuarios"]["pref_beaches"]["n_categorias"] == 2
    assert v["usuarios"]["genero"]["n_categorias"] == 2
    assert v["usuarios"]["n_ninos"]["n_categorias"] == 3
    assert v["destinos"]["tipo"]["n_categorias"] == 4
    assert v["usuarios"]["pref_beaches"]["tipo"] == "booleano" and v["usuarios"]["n_ninos"]["tipo"] == "entero"
    assert v["destinos"]["lugar"]["n_categorias"] == 4
    assert v["destinos"]["popularidad"]["tipo"] == "decimal"


def test_la_ficha_cumple_la_plantilla_y_trae_los_bloques(corrida):
    f = corrida["ficha"]
    validar_ficha(f)
    assert set(f["sha256"]) == set([*CSV, ZIP])
    assert f["sha256"] == corrida["cfg"]["sha256_esperado"]
    assert f["n_registros"] == 8
    assert f["n_variables"] == 6 + 5 + 5 + 7
    assert f["conteos"]["variables_por_archivo"] == {DESTINOS: 6, RESENAS: 5, HISTORIAL: 5, USUARIOS: 7}
    assert f["fecha_descarga"] == "2026-11-25" and f["cita"] and f["url"] and f["fuente"] and f["unidad_de_observacion"]
    assert isinstance(f["periodo"], str) and "2024-01-23" in f["periodo"]
    assert HISTORIAL + " (VisitDate)" in f["periodo"] and "mod 3" in f["periodo"]
    assert {"real_o_sintetico", "licencia"} <= set(f)


def test_bloque_real_o_sintetico(corrida):
    r = corrida["ficha"]["real_o_sintetico"]
    assert r["citas_literales"] == FRAGMENTOS
    assert r["palabra_synthetic_en_la_fuente"] is False
    assert r["conclusion"] == "Conclusión de prueba."
    s = r["senales_medidas"]
    assert s["destinos"]["ids"] == 7 and s["destinos"]["lugares"] == 4
    assert s["resenas"]["textos_distintos"] == 3
    asoc = s["resenas"]["asociacion_con_el_lugar_del_destino"]
    assert set(asoc) == {"chi2", "gl", "p", "v_de_cramer"} and asoc["gl"] == 4
    assert s["resenas"]["conteos_por_texto"] == [2, 1, 1]
    assert s["visit_date"]["valores_distintos"] == ["2024-01-01", "2024-02-15", "2024-03-20"]
    assert s["visit_date"]["filas_posteriores_a_la_publicacion"] == 2 and s["visit_date"]["filas"] == 4
    assert s["usuarios"]["ids"] == 5 and s["usuarios"]["nombres_distintos"] == 2
    assert s["usuarios"]["correos_nombre_en_minusculas_mas_dominio"] == 4
    assert s["usuarios"]["combinaciones_de_preferencias"] == 2
    p = s["periodicidad_con_el_id"]
    assert p["k_max_buscado"] == 10
    # el menor k tal que la columna es función exacta de id mod k (a mano con los ids 1..n del fixture)
    assert (p["visit_date"], p["review_text"], p["preferences"]) == (3, 3, 3)


def test_bloque_licencia(corrida):
    lic = corrida["ficha"]["licencia"]
    assert lic["campo_formal"] == ["LICENCIA-PRUEBA"]
    assert lic["en_la_descripcion"] == {"license": FRAGMENTOS["licencia"], "usage": FRAGMENTOS["uso"]}
    assert isinstance(lic["contradiccion"], str) and lic["contradiccion"]


def test_la_contradiccion_de_licencia_es_solo_texto_del_json_y_del_codigo(tmp_path):
    """Un texto único puesto en «Usage» (JSON y config) debe aparecer en la contradicción, y la frase completa es la
    plantilla del código con lo leído del JSON: nada más."""
    marca = "MARCA-UNICA-DE-USO"
    uso = FRAGMENTOS["uso"] + " " + marca

    def en_el_json(m):
        info = m["respuestas"][0]["cuerpo"]["info"]
        info["description"] = info["description"].replace(FRAGMENTOS["uso"], uso)

    dm.main(montar(tmp_path, meta=en_el_json, cfg_extra=lambda c: c["citas_literales"].update(uso=uso)))
    ficha = json.loads(salidas(tmp_path)["ficha"].read_text(encoding="utf-8"))
    texto = ficha["licencia"]["contradiccion"]
    assert marca in texto
    assert texto == ("Campo formal de licencia de Kaggle: «LICENCIA-PRUEBA». Sección «License» de la descripción: "
                     f"«{FRAGMENTOS['licencia']}». Sección «Usage»: «{uso}». "
                     "El campo formal no aparece en la sección «License»: las declaraciones son distintas.")
    assert "piden citar" not in texto and "permiten" not in texto


def test_la_palabra_synthetic_en_la_fuente_obliga_a_revisar_la_conclusion(tmp_path):
    """La conclusión de la config afirma que la fuente no usa «synthetic»: si la usa, hay que revisarla (no se escribe nada)."""
    def en_la_descripcion(m):
        m["respuestas"][0]["cuerpo"]["info"]["description"] += " A SYNTHETIC set."

    def en_un_archivo(m):
        m["respuestas"][1]["cuerpo"]["datasetFiles"][0]["name"] = "Synthetic_Destinations.csv"

    for i, meta in enumerate((en_la_descripcion, en_un_archivo)):
        d = tmp_path / str(i)
        d.mkdir()
        with pytest.raises(ValueError, match="conclusion_real_o_sintetico"):
            dm.main(montar(d, meta=meta))
        assert not (d / "proc").exists() and not (d / "eda").exists()


# --------------------------------------------------------------------------- calidad y diccionario
def test_calidad_csv_por_tabla_procesada(corrida):
    cal = pd.read_csv(corrida["ruta"]["calidad"])
    assert list(cal.columns) == ["tabla", "filas", "duplicados_clave", *COLUMNAS_CALIDAD]
    assert cal.groupby("tabla", sort=False)["filas"].first().to_dict() == {"destinos": 7, "usuarios": 5, "interacciones": 8}
    assert list(cal["tabla"].drop_duplicates()) == ["destinos", "usuarios", "interacciones"]
    assert (cal["duplicados_clave"] == 0).all()
    fv = cal[(cal["tabla"] == "interacciones") & (cal["columna"] == "fecha_visita")].iloc[0]
    assert fv["faltantes"] == 4  # las 4 reseñas no tienen fecha


def test_diccionario_cubre_las_23_columnas_y_excluye_lo_privado(corrida):
    dic = corrida["dic"]
    cols = {(v["archivo"], v["columna_original"]): v for v in dic["variables"]}
    assert len(cols) == 23
    for archivo in CSV:
        esperadas = pd.read_csv(FIXTURES / archivo).columns
        assert {c for a, c in cols if a == archivo} == set(esperadas)
    for clave in ((USUARIOS, "Name"), (USUARIOS, "Email"), (RESENAS, "ReviewText")):
        assert cols[clave]["nombre_procesado"] is None and cols[clave]["excluida_motivo"]
    assert cols[(RESENAS, "Rating")]["nombre_procesado"] == "interacciones.calificacion"
    assert cols[(HISTORIAL, "VisitDate")]["tipo"] == "texto con forma AAAA-MM-DD"
    assert cols[(DESTINOS, "Popularity")]["tipo"] == "decimal"
    assert cols[(USUARIOS, "NumberOfAdults")]["tipo"] == "entero"
    assert all(v["significado"] == "no documentado por la fuente" for v in cols.values())
    assert cols[(DESTINOS, "Name")]["descripcion_del_archivo_en_la_fuente"] == COMPONENTES[DESTINOS]
    assert "inferencia" in cols[(DESTINOS, "Name")]["nota_correspondencia"]
    assert "columns" in dic["fuente_del_diccionario"]
    assert dic["columnas_documentadas_por_la_fuente"] == 0
    # una sola clasificación de tipos: el mismo nombre en la ficha y en el diccionario
    ficha_v = corrida["ficha"]["conteos"]["variables_de_contenido"]
    assert ficha_v["destinos"]["popularidad"]["tipo"] == cols[(DESTINOS, "Popularity")]["tipo"] == "decimal"
    assert ficha_v["usuarios"]["n_ninos"]["tipo"] == cols[(USUARIOS, "NumberOfChildren")]["tipo"] == "entero"


def test_si_la_fuente_documenta_columnas_el_diccionario_falla(tmp_path):
    def con_columnas(m):
        m["respuestas"][1]["cuerpo"]["datasetFiles"][0]["columns"] = [{"name": "DestinationID"}]

    with pytest.raises(ValueError, match="columns"):
        dm.main(montar(tmp_path, meta=con_columnas))


def test_inconsistencias_calculadas(corrida):
    inc = {i["id"]: i for i in corrida["dic"]["inconsistencias"]}
    assert set(inc) == {"tipo_buscado_ausente", "ids_vs_lugares", "visitdate_periodica_y_posterior",
                        "reviewtext_plantilla", "vocabularios_preferencias_vs_type", "licencias_contradictorias"}
    assert all("descripcion" in i and "medido" in i and isinstance(i["se_presenta"], bool) for i in inc.values())
    assert inc["tipo_buscado_ausente"]["se_presenta"] is True
    assert inc["tipo_buscado_ausente"]["medido"]["tipos_medidos"] == ["Beach", "City", "Historical", "Nature"]
    assert inc["ids_vs_lugares"]["medido"]["ids"] == 7 and inc["ids_vs_lugares"]["medido"]["lugares"] == 4
    assert inc["ids_vs_lugares"]["medido"]["ids_por_lugar"] == {
        "lugar_ficticio_cuatro": 1, "lugar_ficticio_dos": 2, "lugar_ficticio_tres": 2, "lugar_ficticio_uno": 2}
    assert inc["visitdate_periodica_y_posterior"]["medido"]["k_minimo_historyid"] == 3
    assert inc["visitdate_periodica_y_posterior"]["medido"]["filas_posteriores_a_la_publicacion"] == 2
    rt = inc["reviewtext_plantilla"]["medido"]
    assert rt["textos_distintos"] == 3 and rt["filas"] == 4 and rt["conteos_por_texto"] == [2, 1, 1]
    assert rt["k_minimo_reviewid"] == 3
    assert rt["asociacion_con_el_lugar_del_destino"] == corrida["ficha"]["real_o_sintetico"]["senales_medidas"]["resenas"][
        "asociacion_con_el_lugar_del_destino"]
    voc = inc["vocabularios_preferencias_vs_type"]["medido"]
    assert voc["opciones_de_preferencias"] == ["Adventure", "Beaches", "Historical", "Nature"]
    assert voc["valores_de_type"] == ["Beach", "City", "Historical", "Nature"]
    assert voc["solo_en_preferencias"] == ["Adventure", "Beaches"] and voc["solo_en_type"] == ["Beach", "City"]
    assert inc["vocabularios_preferencias_vs_type"]["se_presenta"] is True
    assert voc["en_ambos"] == ["Historical", "Nature"]
    assert inc["vocabularios_preferencias_vs_type"]["descripcion"] == (
        "2 de 4 opciones de Preferences coinciden con valores de Type; solo en Preferences: Adventure, Beaches; "
        "solo en Type: Beach, City. Cruzarlos exige un emparejamiento que es supuesto nuestro, no de la fuente.")
    lic = inc["licencias_contradictorias"]["medido"]
    assert lic["campo_formal"] == ["LICENCIA-PRUEBA"] and lic["formal_aparece_en_license"] is False
    assert inc["licencias_contradictorias"]["se_presenta"] is True


def test_si_los_vocabularios_coinciden_la_descripcion_lo_dice(tmp_path):
    texto = (FIXTURES / DESTINOS).read_text(encoding="utf-8")
    texto = texto.replace(",Beach,", ",Beaches,").replace(",City,", ",Adventure,")  # Type pasa a {Historical, Beaches, Adventure, Nature}
    dm.main(montar(tmp_path, csv={DESTINOS: texto}))
    dic = json.loads(salidas(tmp_path)["diccionario"].read_text(encoding="utf-8"))
    inc = {i["id"]: i for i in dic["inconsistencias"]}["vocabularios_preferencias_vs_type"]
    assert inc["se_presenta"] is False
    assert inc["medido"]["solo_en_preferencias"] == [] and inc["medido"]["solo_en_type"] == []
    assert inc["descripcion"] == "Las 4 opciones de Preferences coinciden con los valores de Type."


def test_una_columna_constante_se_dice_constante(tmp_path):
    filas = [(1, 2, 4), (2, 4, 2), (4, 1, 5), (3, 6, 3)]
    texto = "HistoryID,UserID,DestinationID,VisitDate,ExperienceRating\n" + "\n".join(
        f"{i},{u},{d},2024-01-01,{r}" for i, (u, d, r) in enumerate(filas, 1)) + "\n"
    dm.main(montar(tmp_path, csv={HISTORIAL: texto}))
    ficha = json.loads(salidas(tmp_path)["ficha"].read_text(encoding="utf-8"))
    dic = json.loads(salidas(tmp_path)["diccionario"].read_text(encoding="utf-8"))
    inc = {i["id"]: i for i in dic["inconsistencias"]}["visitdate_periodica_y_posterior"]
    for frase in (ficha["periodo"], inc["descripcion"]):
        assert "constante" in frase and " mod " not in frase
    assert inc["medido"]["k_minimo_historyid"] == 1 and inc["se_presenta"] is False


def test_las_frases_de_inconsistencias_salen_de_lo_medido(corrida):
    inc = {i["id"]: i for i in corrida["dic"]["inconsistencias"]}
    assert inc["ids_vs_lugares"]["descripcion"].startswith("7 DestinationID corresponden a 4 lugares")
    assert "LICENCIA-PRUEBA" in inc["licencias_contradictorias"]["descripcion"]
    assert "no aparece" in inc["licencias_contradictorias"]["descripcion"]
    assert "no menciona" not in inc["tipo_buscado_ausente"]["descripcion"]
    assert "mountain" in inc["tipo_buscado_ausente"]["descripcion"]


# --------------------------------------------------------------------------- errores de las funciones de entrada
def _csv(tmp_path: Path, texto: str) -> Path:
    ruta = tmp_path / "t.csv"
    ruta.write_text(texto, encoding="utf-8", newline="\n")
    return ruta


def _cfg_y_meta(tmp_path: Path, cambio=None):
    cfg = montar(tmp_path, cfg_extra=cambio)
    return cfg, dm.leer_metadatos(Path(cfg["entrada"]["metadatos_fuente"]))


def _sin_clave_obligatoria(c):
    del c["citas_literales"]["licencia"]


def _sin_componente(c):
    del c["componentes"][RESENAS]


def _sin_hash(c):
    del c["sha256_esperado"][RESENAS]


def _verificar_archivos_sin_hash(tmp_path: Path):
    cfg = montar(tmp_path, cfg_extra=_sin_hash)
    return dm.verificar_archivos(cfg["entrada"], cfg["sha256_esperado"])


CASOS_DE_ERROR = {
    "leer_csv: columnas distintas": (lambda p: dm.leer_csv(_csv(p, "a,b\n1,2\n"), ["a", "c"]), "columnas"),
    "leer_csv: valor faltante": (lambda p: dm.leer_csv(_csv(p, "a,b\n1,\n"), ["a", "b"]), "faltantes"),
    "leer_csv: sin filas": (lambda p: dm.leer_csv(_csv(p, "a,b\n"), ["a", "b"]), "no tiene filas"),
    "_enteros: decimal en una columna entera": (lambda p: dm._enteros(pd.Series([1.0, 3.5]), "Rating"), "Rating.*enteros"),
    "verificar_citas: falta una clave obligatoria":
        (lambda p: dm.verificar_citas(*_cfg_y_meta(p, _sin_clave_obligatoria)), "obligatorias.*licencia"),
    "verificar_citas: componente sin fragmento":
        (lambda p: dm.verificar_citas(*_cfg_y_meta(p, _sin_componente)), "falta el fragmento"),
    "verificar_archivos: hash sin clave en la config": (_verificar_archivos_sin_hash, "sha256_esperado no tiene"),
}


@pytest.mark.parametrize("caso", list(CASOS_DE_ERROR))
def test_las_funciones_de_entrada_dan_error_claro(caso, tmp_path):
    llamada, patron = CASOS_DE_ERROR[caso]
    with pytest.raises(ValueError, match=patron):
        llamada(tmp_path)


def test_un_csv_con_solo_la_cabecera_detiene_main_con_error_claro(tmp_path):
    cfg = montar(tmp_path, csv={RESENAS: "ReviewID,DestinationID,UserID,Rating,ReviewText\n"})
    with pytest.raises(ValueError, match="no tiene filas"):
        dm.main(cfg)
    assert not (tmp_path / "proc").exists()


@pytest.mark.parametrize("texto, esperado", [
    ("Historical, Beaches", ["Beaches", "Historical"]),
    ("  Nature ,Adventure,  Nature ", ["Adventure", "Nature"]),
    ("A,,B", ["A", "B"]),
    ("", []),
])
def test_separar_opciones_quita_espacios_repetidas_y_ordena(texto, esperado):
    assert dm.separar_opciones(texto) == esperado


def test_la_config_real_cita_literalmente_la_descripcion_del_json_versionado():
    """Protege en CI la config real: si alguien cambia un fragmento, la fecha de la versión o los nombres de archivo, falla."""
    raiz = Path(__file__).resolve().parents[1]
    cfg = yaml.safe_load((raiz / "configs" / "m3" / "datos.yaml").read_text(encoding="utf-8"))
    meta = dm.leer_metadatos(raiz / cfg["entrada"]["metadatos_fuente"])
    dm.verificar_citas(cfg, meta)
    nombres = {cfg["entrada"][k] for k in ("destinos", "resenas", "historial", "usuarios", "zip")}
    assert set(cfg["sha256_esperado"]) == nombres


# --------------------------------------------------------------------------- funciones auxiliares
def test_periodo_minimo():
    ids = [1, 2, 3, 4, 5, 6]
    assert dm.periodo_minimo(["a", "b", "a", "b", "a", "b"], ids, 10) == 2
    assert dm.periodo_minimo(["x"] * 6, ids, 10) == 1
    assert dm.periodo_minimo(["a", "b", "c", "a", "b", "c"], ids, 10) == 3
    assert dm.periodo_minimo(["b", "a", "b", "a", "b", "a"], [2, 3, 4, 5, 6, 7], 10) == 2   # depende del id, no de la posición
    assert dm.periodo_minimo([str(i) for i in range(30)], list(range(1, 31)), 10) is None
    assert dm.periodo_minimo([str(i) for i in range(30)], list(range(1, 31)), 30) == 30


def test_chi2_y_v_de_cramer_a_mano():
    ind = dm.chi2_y_v([[5, 5], [5, 5]])
    assert ind["chi2"] == pytest.approx(0.0) and ind["v_de_cramer"] == pytest.approx(0.0) and ind["p"] == pytest.approx(1.0)
    perfecta = dm.chi2_y_v([[10, 0], [0, 10]])
    assert perfecta["chi2"] == pytest.approx(20.0) and perfecta["gl"] == 1 and perfecta["v_de_cramer"] == pytest.approx(1.0)
    assert dm.chi2_y_v([[3, 4, 5]])["v_de_cramer"] is None   # una sola fila: sin asociación definida


# --------------------------------------------------------------------------- citas, hashes y archivos
def test_una_cita_que_no_es_subcadena_de_la_descripcion_es_error(tmp_path):
    cfg = montar(tmp_path, cfg_extra=lambda c: c["citas_literales"].update(generado="texto que la fuente nunca dijo"))
    with pytest.raises(ValueError, match="generado"):
        dm.main(cfg)
    cfg = montar(tmp_path / "otro", cfg_extra=lambda c: c["componentes"].update({RESENAS: "Frase inventada."}))
    with pytest.raises(ValueError, match="Final_Updated_Expanded_Reviews"):
        dm.main(cfg)
    assert not (tmp_path / "proc").exists()


def test_la_fecha_de_version_debe_coincidir_con_el_json(tmp_path):
    cfg = montar(tmp_path, cfg_extra=lambda c: c["fuente"].update(fecha_creacion_version="2025-01-01T00:00:00Z"))
    with pytest.raises(ValueError, match="creationDate|fecha_creacion_version"):
        dm.main(cfg)


def test_archivo_faltante_es_error_claro_y_no_se_escribe_nada(tmp_path):
    cfg = montar(tmp_path)
    (tmp_path / "raw" / USUARIOS).unlink()
    with pytest.raises(FileNotFoundError, match=USUARIOS):
        dm.main(cfg)
    assert not (tmp_path / "proc").exists() and not (tmp_path / "eda").exists()


def test_zip_faltante_es_error(tmp_path):
    cfg = montar(tmp_path)
    (tmp_path / "raw" / ZIP).unlink()
    with pytest.raises(FileNotFoundError, match=ZIP):
        dm.main(cfg)


def test_sha256_distinto_es_error_que_nombra_el_archivo(tmp_path):
    cfg = montar(tmp_path)
    with open(tmp_path / "raw" / RESENAS, "a", encoding="utf-8") as f:
        f.write("5,7,5,3,Texto de prueba 2\n")  # un registro válido más: cambia el hash
    with pytest.raises(ValueError, match=RESENAS) as e:
        dm.main(cfg)
    assert cfg["sha256_esperado"][RESENAS] in str(e.value)
    assert not (tmp_path / "proc").exists() and not (tmp_path / "eda").exists()


# --------------------------------------------------------------------------- determinismo y red
def test_main_es_determinista(tmp_path):
    cfg = montar(tmp_path)
    dm.main(cfg)
    primera = {k: v.read_bytes() for k, v in salidas(tmp_path).items()}
    dm.main(cfg)
    assert {k: v.read_bytes() for k, v in salidas(tmp_path).items()} == primera
    assert len(primera) == 6


def test_main_no_usa_la_red(tmp_path, monkeypatch):
    def bloqueado(*a, **k):
        raise RuntimeError("red")

    monkeypatch.setattr(socket.socket, "connect", bloqueado)
    monkeypatch.setattr(socket, "create_connection", bloqueado)
    monkeypatch.setattr(socket, "getaddrinfo", bloqueado)
    assert dm.main(montar(tmp_path)) == 0
