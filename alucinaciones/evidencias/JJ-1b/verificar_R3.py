r"""Verificación independiente R3 de JJ-1 (fase B), cazador-alucinaciones (Opus), 2026-11-25.

NO importa src/m3_recomendacion/datos.py: recalcula todo desde los CSV de data/raw/m3/ y desde la respuesta cruda de la
API de Kaggle (docs/investigacion/JJ-1_kaggle_metadata.json), y lo compara con:
  results/data/m3/eda/ficha.json, results/data/m3/eda/diccionario.json, data/fuentes.md (sección M3),
  blog/references.bib (mehra2024) y data/processed/m3/*.parquet.
Sin internet. Uso, desde la raíz:
  .venv\Scripts\python -I alucinaciones/evidencias/JJ-1b/verificar_R3.py [CARPETA_LICENCIAS]
CARPETA_LICENCIAS (opcional): carpeta con los HTML descargados de las licencias (no se versionan), con nombres
  https___opensource_org_license_mit.html, https___creativecommons_org_publicdomain_zero_1_0_.html,
  https___creativecommons_org_publicdomain_zero_1_0_legalcode_en.html
  (obtenidos con: curl -sL -A "Mozilla/5.0" -o <nombre> <url>). Si no se da, se omite la parte de licencias.
Escribe la salida en verificar_R3_salida.txt (junto a este script).
"""
import csv
import hashlib
import html
import io
import json
import math
import re
import statistics
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.parquet as pq
from scipy.stats import chi2 as chi2_dist

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
RAW = RAIZ / "data" / "raw" / "m3"
EDA = RAIZ / "results" / "data" / "m3" / "eda"
PROC = RAIZ / "data" / "processed" / "m3"

salida = io.StringIO()
CUENTA = Counter()


def out(*a):
    print(*a, file=salida)


def chequear(nombre, obtenido, esperado, tol=None):
    if tol is None:
        ok = obtenido == esperado
    else:
        ok = math.isclose(obtenido, esperado, rel_tol=0, abs_tol=tol)
    CUENTA["OK" if ok else "FALLA"] += 1
    marca = "OK   " if ok else "FALLA"
    out(f"[{marca}] {nombre}: ficha/artefacto={esperado!r} | recalculado={obtenido!r}")
    return ok


def leer_csv(nombre):
    with open(RAW / nombre, encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        filas = list(lector)
        return lector.fieldnames, filas


# ---------------------------------------------------------------- 0. Entradas
ficha = json.loads((EDA / "ficha.json").read_text(encoding="utf-8"))
dicc = json.loads((EDA / "diccionario.json").read_text(encoding="utf-8"))
meta = json.loads((RAIZ / "docs" / "investigacion" / "JJ-1_kaggle_metadata.json").read_text(encoding="utf-8"))
resp = {r["url"]: r for r in meta["respuestas"]}
U_META = "https://www.kaggle.com/api/v1/datasets/metadata/amanmehra23/travel-recommendation-dataset"
U_LIST = "https://www.kaggle.com/api/v1/datasets/list/amanmehra23/travel-recommendation-dataset"
U_VIEW = "https://www.kaggle.com/api/v1/datasets/view/amanmehra23/travel-recommendation-dataset"
U_SRCH = "https://www.kaggle.com/api/v1/datasets/list?search=travel-recommendation-dataset&user=amanmehra23"
info = resp[U_META]["cuerpo"]["info"]
view = resp[U_VIEW]["cuerpo"]
srch = resp[U_SRCH]["cuerpo"][0]
files_meta = resp[U_LIST]["cuerpo"]["datasetFiles"]
desc = info["description"]
secciones = dict(re.findall(r"### (\w[\w ]*)\n(.*?)(?=\n### |\Z)", desc, flags=re.S))
sec_license = secciones["License"].strip()
sec_usage = secciones["Usage"].strip()
creacion = view["versions"][0]["creationDate"]
fecha_pub = creacion[:10]

out("=== 0. Integridad de la fuente local ===")
for r in meta["respuestas"]:
    cuerpo = r["cuerpo_crudo"].encode("utf-8")
    chequear(f"sha256 del cuerpo crudo {r['url'][-60:]}", hashlib.sha256(cuerpo).hexdigest(), r["sha256_cuerpo"])
    chequear(f"cuerpo == json(cuerpo_crudo) {r['url'][-60:]}", json.loads(r["cuerpo_crudo"]), r["cuerpo"])

# ---------------------------------------------------------------- 1. SHA-256 y tamaños
out("\n=== 1. SHA-256 y tamaños (ficha.json, data/fuentes.md, metadatos de Kaggle) ===")
fuentes = (RAIZ / "data" / "fuentes.md").read_text(encoding="utf-8")
m3 = fuentes[fuentes.index("## M3"):]
tabla_fuentes = {m.group(1): (int(m.group(2).replace(" ", "").replace(" ", "").replace("\xa0", "")), m.group(3))
                 for m in re.finditer(r"\| `([^`]+)` \| ([\d  \xa0]+) \| `([0-9a-f]{64})` \|", m3)}
bytes_kaggle = {f["name"]: f["totalBytes"] for f in files_meta}
bytes_kaggle["archive.zip"] = srch["totalBytes"]
for nombre in ["archive.zip", "Expanded_Destinations.csv", "Final_Updated_Expanded_Reviews.csv",
               "Final_Updated_Expanded_UserHistory.csv", "Final_Updated_Expanded_Users.csv"]:
    datos = (RAW / nombre).read_bytes()
    h = hashlib.sha256(datos).hexdigest()
    chequear(f"sha256 {nombre} (ficha)", h, ficha["sha256"][nombre])
    chequear(f"sha256 {nombre} (fuentes.md)", h, tabla_fuentes[nombre][1])
    chequear(f"bytes {nombre} (fuentes.md)", len(datos), tabla_fuentes[nombre][0])
    chequear(f"bytes {nombre} (Kaggle totalBytes)", len(datos), bytes_kaggle[nombre])
with zipfile.ZipFile(RAW / "archive.zip") as z:
    miembros = sorted(z.namelist())
    chequear("miembros del zip", miembros, sorted(bytes_kaggle.keys() - {"archive.zip"}))
    for n in miembros:
        chequear(f"zip:{n} idéntico al CSV suelto", z.read(n) == (RAW / n).read_bytes(), True)
yaml_txt = (RAIZ / "configs" / "m3" / "datos.yaml").read_text(encoding="utf-8")
for nombre, (_, h) in tabla_fuentes.items():
    chequear(f"sha256 {nombre} presente en configs/m3/datos.yaml", f"{nombre}: {h}" in yaml_txt, True)

# ---------------------------------------------------------------- 2. Lectura de los CSV
cab_d, D = leer_csv("Expanded_Destinations.csv")
cab_r, R = leer_csv("Final_Updated_Expanded_Reviews.csv")
cab_h, H = leer_csv("Final_Updated_Expanded_UserHistory.csv")
cab_u, U = leer_csv("Final_Updated_Expanded_Users.csv")


def slug(s):
    return re.sub(r"[^0-9a-z]+", "_", s.lower()).strip("_")


dest = {int(d["DestinationID"]): d for d in D}
usr = {int(u["UserID"]): u for u in U}
lugar_de = {i: slug(d["Name"]) for i, d in dest.items()}

out("\n=== 2. Conteos de ficha.json → conteos ===")
c = ficha["conteos"]
chequear("usuarios_maestra", len(usr), c["usuarios_maestra"])
chequear("filas Users == ids únicos", len(U), len(usr))
chequear("destinos_maestra", len(dest), c["destinos_maestra"])
combos_lugar = {(d["Name"], d["State"], d["Type"], d["BestTimeToVisit"]) for d in D}
chequear("lugares (combinaciones nombre, estado, tipo, temporada)", len(combos_lugar), c["lugares"])
chequear("lugares por nombre", len({d["Name"] for d in D}), c["lugares"])
vpa = {"Expanded_Destinations.csv": len(cab_d), "Final_Updated_Expanded_Reviews.csv": len(cab_r),
       "Final_Updated_Expanded_UserHistory.csv": len(cab_h), "Final_Updated_Expanded_Users.csv": len(cab_u)}
chequear("variables_por_archivo", vpa, c["variables_por_archivo"])
chequear("n_variables", sum(vpa.values()), ficha["n_variables"])

pares_r = [(int(x["UserID"]), int(x["DestinationID"])) for x in R]
pares_h = [(int(x["UserID"]), int(x["DestinationID"])) for x in H]
chequear("pares repetidos en Reviews", len(pares_r) - len(set(pares_r)), 0)
chequear("pares repetidos en UserHistory", len(pares_h) - len(set(pares_h)), 0)
chequear("intersección Reviews ∩ UserHistory", len(set(pares_r) & set(pares_h)), 0)
union = set(pares_r) | set(pares_h)
chequear("interacciones", {"resena": len(R), "historial": len(H), "union": len(union)}, c["interacciones"])
chequear("n_registros", len(union), ficha["n_registros"])
ap_u = {k: len({p[0] for p in s}) for k, s in (("resena", pares_r), ("historial", pares_h), ("union", union))}
ap_d = {k: len({p[1] for p in s}) for k, s in (("resena", pares_r), ("historial", pares_h), ("union", union))}
chequear("usuarios_que_aparecen", ap_u, c["usuarios_que_aparecen"])
chequear("destinos_que_aparecen", ap_d, c["destinos_que_aparecen"])
chequear("integridad: usuarios de interacciones ⊆ Users", {p[0] for p in union} <= set(usr), True)
chequear("integridad: destinos de interacciones ⊆ Destinations", {p[1] for p in union} <= set(dest), True)

cal_r = [int(x["Rating"]) for x in R]
cal_h = [int(x["ExperienceRating"]) for x in H]
for k, v in (("resena", cal_r), ("historial", cal_h), ("union", cal_r + cal_h)):
    fr = Counter(v)
    rec = {"minimo": min(v), "maximo": max(v), "valores": sorted(fr),
           "frecuencias": {str(a): fr[a] for a in sorted(fr)}}
    chequear(f"escala_calificacion.{k}", rec, c["escala_calificacion"][k])

nu, nd = len(usr), len(dest)
for k, s in (("resena", pares_r), ("historial", pares_h), ("union", list(union))):
    e = c["densidad"][k]
    chequear(f"densidad.{k}.interacciones", len(s), e["interacciones"])
    chequear(f"densidad.{k}.denominador_maestras", nu * nd, e["denominador_maestras"])
    chequear(f"densidad.{k}.maestras", len(s) / (nu * nd), e["maestras"], tol=1e-15)
    den = ap_u[k] * ap_d[k]
    chequear(f"densidad.{k}.denominador_los_que_aparecen", den, e["denominador_los_que_aparecen"])
    chequear(f"densidad.{k}.los_que_aparecen", len(s) / den, e["los_que_aparecen"], tol=1e-15)

por_usuario = {}
for k, s in (("resena", pares_r), ("historial", pares_h), ("union", list(union))):
    cnt = Counter(p[0] for p in s)
    por_usuario[k] = cnt
    hist = Counter(min(cnt.get(u, 0), 5) for u in usr)
    rec = {str(i): hist[i] for i in range(5)}
    rec["5+"] = hist[5]
    chequear(f"usuarios_por_numero_de_interacciones.{k}", rec, c["usuarios_por_numero_de_interacciones"][k])

out("\n--- Cifras de D1/D3 (spec personal §3.1) que dependen de lo mismo ---")
chequear("D1 mediana por usuario (unión, usuarios que aparecen)", statistics.median(por_usuario["union"].values()), 2)
chequear("D1 mediana por usuario (Reviews)", statistics.median(por_usuario["resena"].values()), 1)
chequear("D1 mediana por usuario (UserHistory)", statistics.median(por_usuario["historial"].values()), 1)
chequear("D1 usuarios con ≥2 (unión)", sum(v >= 2 for v in por_usuario["union"].values()), 606)
chequear("D1 usuarios con ≥2 (solo Reviews)", sum(v >= 2 for v in por_usuario["resena"].values()), 269)
chequear("D1 usuarios con ≥2 (solo UserHistory)", sum(v >= 2 for v in por_usuario["historial"].values()), 258)
chequear("D3 usuarios con ≥3 (unión)", sum(v >= 3 for v in por_usuario["union"].values()), 326)

out("\n--- variables_de_contenido ---")
OPC = lambda s: [o.strip() for o in s.split(",") if o.strip()]
opciones = sorted({o for u in U for o in OPC(u["Preferences"])})
vc_u = {"preferencias": {"tipo": "texto", "n_categorias": len({u["Preferences"] for u in U})}}
for o in opciones:
    vc_u[f"pref_{o.lower()}"] = {"tipo": "booleano", "n_categorias": len({o in OPC(u["Preferences"]) for u in U})}
vc_u["genero"] = {"tipo": "texto", "n_categorias": len({u["Gender"] for u in U})}
vc_u["n_adultos"] = {"tipo": "entero", "n_categorias": len({int(u["NumberOfAdults"]) for u in U})}
vc_u["n_ninos"] = {"tipo": "entero", "n_categorias": len({int(u["NumberOfChildren"]) for u in U})}
chequear("variables_de_contenido.usuarios", vc_u, c["variables_de_contenido"]["usuarios"])
pop = [float(d["Popularity"]) for d in D]
vc_d = {"nombre": {"tipo": "texto", "n_categorias": len({d["Name"] for d in D})},
        "lugar": {"tipo": "texto", "n_categorias": len(set(lugar_de.values()))},
        "estado": {"tipo": "texto", "n_categorias": len({d["State"] for d in D})},
        "tipo": {"tipo": "texto", "n_categorias": len({d["Type"] for d in D})},
        "mejor_epoca": {"tipo": "texto", "n_categorias": len({d["BestTimeToVisit"] for d in D})},
        "popularidad": {"tipo": "decimal", "minimo": min(pop), "maximo": max(pop), "n_valores_distintos": len(set(pop))}}
chequear("variables_de_contenido.destinos", vc_d, c["variables_de_contenido"]["destinos"])

# ---------------------------------------------------------------- 3. Señales medidas
out("\n=== 3. real_o_sintetico.senales_medidas ===")
sm = ficha["real_o_sintetico"]["senales_medidas"]
ids_por_lugar = dict(sorted(Counter(lugar_de.values()).items()))
chequear("destinos", {"ids": len(dest), "lugares": len(ids_por_lugar), "ids_por_lugar": ids_por_lugar}, sm["destinos"])
for lugar in ids_por_lugar:
    combos = {(d["Name"], d["State"], d["Type"], d["BestTimeToVisit"]) for i, d in dest.items() if lugar_de[i] == lugar}
    chequear(f"ids de {lugar} comparten nombre, estado, tipo y temporada", len(combos), 1)

textos = Counter(x["ReviewText"] for x in R)
lugares_orden = sorted(ids_por_lugar)
textos_orden = sorted(textos)
tabla = [[0] * len(lugares_orden) for _ in textos_orden]
for x in R:
    tabla[textos_orden.index(x["ReviewText"])][lugares_orden.index(lugar_de[int(x["DestinationID"])])] += 1
n = len(R)
filas_t = [sum(f) for f in tabla]
cols_t = [sum(tabla[i][j] for i in range(len(tabla))) for j in range(len(lugares_orden))]
x2 = sum((tabla[i][j] - filas_t[i] * cols_t[j] / n) ** 2 / (filas_t[i] * cols_t[j] / n)
         for i in range(len(tabla)) for j in range(len(lugares_orden)))
gl = (len(tabla) - 1) * (len(lugares_orden) - 1)
p = float(chi2_dist.sf(x2, gl))
v = math.sqrt(x2 / (n * (min(len(tabla), len(lugares_orden)) - 1)))
a = sm["resenas"]["asociacion_con_el_lugar_del_destino"]
chequear("resenas.filas", n, sm["resenas"]["filas"])
chequear("resenas.textos_distintos", len(textos), sm["resenas"]["textos_distintos"])
chequear("resenas.conteos_por_texto", sorted(textos.values()), sorted(sm["resenas"]["conteos_por_texto"]))
chequear("chi2 (χ² de Pearson calculado a mano)", x2, a["chi2"], tol=1e-9)
chequear("gl", gl, a["gl"])
chequear("p (scipy.stats.chi2.sf)", p, a["p"], tol=1e-9)
chequear("V de Cramér", v, a["v_de_cramer"], tol=1e-12)

fechas = [x["VisitDate"] for x in H]
chequear("visit_date.filas", len(fechas), sm["visit_date"]["filas"])
chequear("visit_date.valores_distintos", sorted(set(fechas)), sm["visit_date"]["valores_distintos"])
chequear("visit_date.fecha_publicacion == versions[0].creationDate[:10]", fecha_pub, sm["visit_date"]["fecha_publicacion"])
chequear("visit_date.filas_posteriores_a_la_publicacion", sum(f > fecha_pub for f in fechas),
         sm["visit_date"]["filas_posteriores_a_la_publicacion"])
chequear("todas las VisitDate con forma AAAA-MM-DD", all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", f) for f in fechas), True)

nombres = {u["Name"] for u in U}
correos = {u["Email"] for u in U}
forma = sum(u["Email"].split("@")[0] == u["Name"].lower() for u in U)
dominios = Counter(u["Email"].split("@")[1] for u in U)
chequear("usuarios.ids", len(usr), sm["usuarios"]["ids"])
chequear("usuarios.nombres_distintos", len(nombres), sm["usuarios"]["nombres_distintos"])
chequear("usuarios.correos_nombre_en_minusculas_mas_dominio", forma, sm["usuarios"]["correos_nombre_en_minusculas_mas_dominio"])
chequear("usuarios.combinaciones_de_preferencias", len({frozenset(OPC(u["Preferences"])) for u in U}),
         sm["usuarios"]["combinaciones_de_preferencias"])
out(f"   (informativo) correos distintos = {len(correos)}; dominios = {dict(dominios)}")


def k_min(filas, col_id, col_val, kmax):
    for k in range(1, kmax + 1):
        mapa = defaultdict(set)
        for f in filas:
            mapa[int(f[col_id]) % k].add(f[col_val])
        if all(len(s) == 1 for s in mapa.values()):
            return k
    return None


per = sm["periodicidad_con_el_id"]
kmax = per["k_max_buscado"]
chequear("periodicidad.nombre_de_destino", k_min(D, "DestinationID", "Name", kmax), per["nombre_de_destino"])
chequear("periodicidad.review_text", k_min(R, "ReviewID", "ReviewText", kmax), per["review_text"])
chequear("periodicidad.visit_date", k_min(H, "HistoryID", "VisitDate", kmax), per["visit_date"])
chequear("periodicidad.preferences", k_min(U, "UserID", "Preferences", kmax), per["preferences"])
for col in ("State", "Type", "BestTimeToVisit"):
    chequear(f"periodicidad (extra) {col} vs DestinationID", k_min(D, "DestinationID", col, kmax), 5)

todo_texto = json.dumps(meta, ensure_ascii=False).lower() + " ".join(bytes_kaggle).lower()
chequear("palabra_synthetic_en_la_fuente", "synthetic" in todo_texto,
         ficha["real_o_sintetico"]["palabra_synthetic_en_la_fuente"])

# ---------------------------------------------------------------- 4. Citas literales
out("\n=== 4. Citas literales (subcadena exacta del campo indicado) ===")
for k, t in ficha["real_o_sintetico"]["citas_literales"].items():
    chequear(f"ficha.citas_literales.{k} ⊂ info.description", t in desc, True)
chequear("ficha.citas_literales.licencia == sección «License»", ficha["real_o_sintetico"]["citas_literales"]["licencia"], sec_license)
chequear("ficha.citas_literales.uso == sección «Usage»", ficha["real_o_sintetico"]["citas_literales"]["uso"], sec_usage)
chequear("«generated for…» está en la sección «Acknowledgements»",
         "generated for educational and research purposes" in desc[desc.index("**Acknowledgements**"):desc.index("**Inspiration**")], True)
chequear("«enriched with gender diversity» está en el componente «Users»",
         "enriched with gender diversity" in desc[desc.index("2. **Users**"):desc.index("3. **Reviews**")], True)
lic = ficha["licencia"]
chequear("licencia.campo_formal == info.licenses[].name", [l["name"] for l in info["licenses"]], lic["campo_formal"])
chequear("licenseName (view) y (list?search)", [view["licenseName"], srch["licenseName"]], ["MIT", "MIT"])
chequear("licencia.en_la_descripcion.license == «License»", lic["en_la_descripcion"]["license"], sec_license)
chequear("licencia.en_la_descripcion.usage == «Usage»", lic["en_la_descripcion"]["usage"], sec_usage)
esperada = ("Campo formal de licencia de Kaggle: «MIT». Sección «License» de la descripción: «" + sec_license +
            "». Sección «Usage»: «" + sec_usage + "». El campo formal no aparece en la sección «License»: las declaraciones son distintas.")
chequear("licencia.contradiccion = solo citas del JSON + comparación", lic["contradiccion"], esperada)
chequear("'MIT' aparece en la sección «License»", "MIT" in sec_license, False)
chequear("la sección «Usage» contiene 'cite'", bool(re.search(r"\bcite\b", sec_usage)), True)
chequear("la sección «License» contiene cite/attribut/credit", bool(re.search(r"\b(cite|citation|attribut\w*|credit)\b", sec_license, re.I)), False)
chequear("título de la descripción «India Travel Recommender System Dataset»",
         desc.startswith("### Title: India Travel Recommender System Dataset"), True)

out("\n--- diccionario.json ---")
chequear("columnas documentadas por la fuente (suma de len(columns))", sum(len(f["columns"]) for f in files_meta),
         dicc["columnas_documentadas_por_la_fuente"])
chequear("archivos listados en datasets/list", len(files_meta), 4)
chequear("description de cada archivo vacía", all(f["description"] == "" for f in files_meta), True)
for vdic in dicc["variables"]:
    chequear(f"cita de componente ({vdic['archivo']}.{vdic['columna_original']}) ⊂ info.description",
             vdic["descripcion_del_archivo_en_la_fuente"] in desc, True)
cabeceras = {"Expanded_Destinations.csv": (cab_d, D), "Final_Updated_Expanded_Reviews.csv": (cab_r, R),
             "Final_Updated_Expanded_UserHistory.csv": (cab_h, H), "Final_Updated_Expanded_Users.csv": (cab_u, U)}
listadas = [(vd["archivo"], vd["columna_original"]) for vd in dicc["variables"]]
todas = [(a, col) for a, (cab, _) in cabeceras.items() for col in cab]
chequear("el diccionario lista exactamente las 23 columnas crudas", sorted(listadas), sorted(todas))


def tipo_crudo(valores):
    if all(re.fullmatch(r"-?\d+", s) for s in valores):
        return "entero"
    if all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) for s in valores):
        return "texto con forma AAAA-MM-DD"
    try:
        [float(s) for s in valores]
        return "decimal"
    except ValueError:
        return "texto"


for vd in dicc["variables"]:
    _, filas = cabeceras[vd["archivo"]]
    chequear(f"tipo {vd['archivo']}.{vd['columna_original']}", tipo_crudo([f[vd["columna_original"]] for f in filas]), vd["tipo"])
    chequear(f"significado {vd['columna_original']} = 'no documentado por la fuente'", vd["significado"], "no documentado por la fuente")
excl = {vd["columna_original"]: vd.get("excluida_motivo", "") for vd in dicc["variables"] if vd["nombre_procesado"] is None}
chequear("columnas excluidas (nombre_procesado null)", sorted(excl), ["Email", "Name", "ReviewText"])
chequear("motivo Name: «20 nombres distintos en 999 usuarios»", f"{len(nombres)} nombres distintos en {len(usr)} usuarios" in excl["Name"], True)
chequear("motivo Email: «20 correos distintos en 999 usuarios»", f"{len(correos)} correos distintos en {len(usr)} usuarios" in excl["Email"], True)
chequear("motivo Email: «999 tienen la forma nombre en minúsculas + dominio»", f"{forma} tienen la forma" in excl["Email"], True)
chequear("motivo ReviewText: V y p redondeados", f"V de Cramér = {v:.3f}, χ² p = {p:.3f}" in excl["ReviewText"], True)

inc = {i["id"]: i for i in dicc["inconsistencias"]}
tipos = sorted({d["Type"] for d in D})
chequear("inc.tipo_buscado_ausente: 'mountain' en la descripción", "mountain" in desc, inc["tipo_buscado_ausente"]["medido"]["descripcion_menciona_el_tipo"])
chequear("inc.tipo_buscado_ausente: tipos medidos", tipos, inc["tipo_buscado_ausente"]["medido"]["tipos_medidos"])
chequear("inc.tipo_buscado_ausente: ningún Type contiene 'mountain'", not any("mountain" in t.lower() for t in tipos),
         inc["tipo_buscado_ausente"]["medido"]["ningun_tipo_lo_contiene"])
chequear("inc.ids_vs_lugares.ids_por_lugar", ids_por_lugar, inc["ids_vs_lugares"]["medido"]["ids_por_lugar"])
chequear("inc.ids_vs_lugares.k_minimo", k_min(D, "DestinationID", "Name", 10), inc["ids_vs_lugares"]["medido"]["k_minimo_destinationid_nombre"])
chequear("inc.visitdate.k_minimo_historyid", k_min(H, "HistoryID", "VisitDate", 10), inc["visitdate_periodica_y_posterior"]["medido"]["k_minimo_historyid"])
chequear("inc.visitdate.posteriores", sum(f > fecha_pub for f in fechas), inc["visitdate_periodica_y_posterior"]["medido"]["filas_posteriores_a_la_publicacion"])
chequear("inc.reviewtext.k_minimo_reviewid", k_min(R, "ReviewID", "ReviewText", 10), inc["reviewtext_plantilla"]["medido"]["k_minimo_reviewid"])
chequear("inc.reviewtext.asociacion == ficha", inc["reviewtext_plantilla"]["medido"]["asociacion_con_el_lugar_del_destino"], a)
sp, st = set(opciones), set(tipos)
mv = inc["vocabularios_preferencias_vs_type"]["medido"]
chequear("inc.vocab.opciones_de_preferencias", sorted(sp), mv["opciones_de_preferencias"])
chequear("inc.vocab.solo_en_preferencias", sorted(sp - st), mv["solo_en_preferencias"])
chequear("inc.vocab.solo_en_type", sorted(st - sp), mv["solo_en_type"])
chequear("inc.vocab.en_ambos", sorted(sp & st), mv["en_ambos"])
chequear("inc.vocab.descripcion «4 de 5 opciones … coinciden»", f"{len(sp & st)} de {len(sp)} opciones de Preferences coinciden" in
         inc["vocabularios_preferencias_vs_type"]["descripcion"], True)
chequear("inc.licencias: license/usage", [inc["licencias_contradictorias"]["medido"]["license"], inc["licencias_contradictorias"]["medido"]["usage"]],
         [sec_license, sec_usage])
chequear("todas las inconsistencias con se_presenta = true", all(i["se_presenta"] for i in dicc["inconsistencias"]), True)

# ---------------------------------------------------------------- 5. fuentes.md (M3) y references.bib
out("\n=== 5. data/fuentes.md (M3) y blog/references.bib (mehra2024) ===")
chequear("fuentes.md: id 4345382", f"id {info['datasetId']})" in m3, True)
chequear("fuentes.md: ref", f"`{view['ref']}`" in m3, True)
chequear("fuentes.md: versión 1 («Initial release»)",
         f"| {view['currentVersionNumber']} («{view['versions'][0]['versionNotes']}»)" in m3, True)
chequear("fuentes.md: creada el <creationDate>", f"creada el {creacion}" in m3, True)
chequear("sin actualizaciones: 1 versión y lastUpdated == creationDate",
         (len(view["versions"]), view["lastUpdated"] == creacion), (1, True))
chequear("fuentes.md: URL == urlNullable de list?search", srch["url"] in m3, True)
chequear("fuentes.md: consulta 23:16 UTC == consultado_utc", sorted({r["consultado_utc"][:16] for r in meta["respuestas"]}),
         ["2026-11-25T23:16"])
fila_lic = next(l for l in m3.splitlines() if l.startswith("| Licencia |"))
chequear("fuentes.md fila Licencia: cita «License» literal", f"«{sec_license}»" in fila_lic, True)
chequear("fuentes.md fila Licencia: cita «Usage» literal", f"«{sec_usage}»" in fila_lic, True)
chequear("fuentes.md fila Licencia: «MIT» del campo formal", "«MIT»" in fila_lic, True)
chequear("fuentes.md: título de la descripción", "«India Travel Recommender System Dataset»" in m3, True)
chequear("fuentes.md: «generated for educational and research purposes» ⊂ desc",
         "generated for educational and research purposes" in desc and "«generated for educational and research purposes»" in m3, True)

bib = (RAIZ / "blog" / "references.bib").read_text(encoding="utf-8")
ent = re.search(r"@dataset\{mehra2024,(.*?)\n\}", bib, re.S).group(1)
campos = dict(re.findall(r"(\w+)\s*=\s*\{(.*?)\},?\n", ent + "\n"))
nombre_k = view["creatorName"].split()
chequear("bib author == creatorName (Apellido, Nombre)", campos["author"], f"{nombre_k[-1]}, {' '.join(nombre_k[:-1])}")
chequear("bib year == año de versions[0].creationDate", campos["year"], creacion[:4])
chequear("bib version == currentVersionNumber", campos["version"], str(view["currentVersionNumber"]))
chequear("bib title (sin mayúsculas) == title de Kaggle", campos["title"].lower(), view["title"].lower())
chequear("bib publisher", campos["publisher"], "Kaggle")
chequear("bib url == urlNullable", campos["url"], srch["url"])
chequear("bib sin campo doi", "doi" in campos, False)
chequear("bib sin caracteres de control", bool(re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", bib)), False)
cita = f"Mehra, A. ({creacion[:4]}). Travel recommendation dataset (Versión {view['currentVersionNumber']}) [Conjunto de datos]. Kaggle. {srch['url']}"
chequear("ficha.cita (APA 7) con autor, año, versión, título y URL de la fuente", ficha["cita"], cita)
chequear("ficha.url", ficha["url"], srch["url"])
chequear("fuentes.md: cita APA", f"Mehra, A. ({creacion[:4]}). *Travel recommendation dataset* (Versión 1) [Conjunto de datos]. Kaggle. {srch['url']}" in m3, True)

# ---------------------------------------------------------------- 6. Parquet
out("\n=== 6. data/processed/m3/*.parquet ===")
ti = pq.read_table(PROC / "interacciones.parquet").to_pylist()
tu = pq.read_table(PROC / "usuarios.parquet").to_pylist()
td = pq.read_table(PROC / "destinos.parquet").to_pylist()
cols = {n: pq.read_schema(PROC / f"{n}.parquet").names for n in ("interacciones", "usuarios", "destinos")}
out(f"   columnas: {cols}")
chequear("interacciones: columnas (D1, propuesta §3.1)", cols["interacciones"],
         ["usuario_id", "destino_id", "origen", "id_origen", "calificacion", "fecha_visita"])
prohib = {"Name", "Email", "ReviewText", "nombre_usuario", "email", "correo", "texto_resena", "review_text", "split"}
for n, cs in cols.items():
    chequear(f"{n}: sin Name/Email/ReviewText/split", sorted(set(cs) & prohib) + [x for x in cs if x.lower() in {"name", "email", "reviewtext", "split"}], [])
chequear("interacciones: filas", len(ti), 1998)
chequear("usuarios: filas", len(tu), 999)
chequear("destinos: filas", len(td), 1000)
crudo = {("resena", int(x["ReviewID"])): (int(x["UserID"]), int(x["DestinationID"]), int(x["Rating"]), None) for x in R}
crudo.update({("historial", int(x["HistoryID"])): (int(x["UserID"]), int(x["DestinationID"]), int(x["ExperienceRating"]), x["VisitDate"]) for x in H})
claves = [(f["origen"], f["id_origen"]) for f in ti]
chequear("(origen, id_origen) únicos", len(set(claves)), len(claves))
chequear("(origen, id_origen) == filas crudas (biyección)", set(claves) == set(crudo), True)
malas = 0
for f in ti:
    fv = f["fecha_visita"].strftime("%Y-%m-%d") if f["fecha_visita"] is not None else None
    if (f["usuario_id"], f["destino_id"], f["calificacion"], fv) != crudo[(f["origen"], f["id_origen"])]:
        malas += 1
chequear("filas de interacciones que no reproducen su fila cruda", malas, 0)
chequear("pares (usuario, destino) únicos en interacciones", len({(f["usuario_id"], f["destino_id"]) for f in ti}), 1998)
chequear("origen: conteos", dict(Counter(f["origen"] for f in ti)), {"resena": 999, "historial": 999})
out(f"   usuarios: columnas {cols['usuarios']}")
out(f"   destinos: columnas {cols['destinos']}")
mal_u = 0
for f in tu:
    u = usr[f["usuario_id"]]
    ops = set(OPC(u["Preferences"]))
    ok = (f["genero"] == u["Gender"] and f["n_adultos"] == int(u["NumberOfAdults"]) and f["n_ninos"] == int(u["NumberOfChildren"])
          and set(OPC(f["preferencias"])) == ops and all(f[f"pref_{o.lower()}"] == (o in ops) for o in opciones))
    mal_u += not ok
chequear("usuarios: filas que no reproducen Users.csv (sin Name/Email)", mal_u, 0)
chequear("usuarios: ids == Users.csv", sorted(f["usuario_id"] for f in tu), sorted(usr))
mal_d = 0
for f in td:
    d = dest[f["destino_id"]]
    ok = (f["nombre"] == d["Name"] and f["estado"] == d["State"] and f["tipo"] == d["Type"] and f["mejor_epoca"] == d["BestTimeToVisit"]
          and f["popularidad"] == float(d["Popularity"]) and f["lugar"] == lugar_de[f["destino_id"]])
    mal_d += not ok
chequear("destinos: filas que no reproducen Destinations.csv", mal_d, 0)
chequear("destinos: ids == Destinations.csv", sorted(f["destino_id"] for f in td), sorted(dest))

# PII y textos de reseña en salidas (bytes de los parquet y de results/data/m3)
sensibles = sorted(nombres | correos | set(textos) | {"example.com"})
hall = []
for ruta in list(PROC.glob("*.parquet")) + list(EDA.glob("*")):
    if ruta.suffix == ".parquet":
        celdas = " ".join(str(x) for t in pq.read_table(ruta).to_pylist() for x in t.values())
    else:
        celdas = ruta.read_text(encoding="utf-8")
    for s in sensibles:
        if s in celdas:
            hall.append((ruta.name, s))
out(f"   (informativo) cadenas sensibles buscadas: {len(sensibles)} (nombres, correos, 3 textos de reseña y example.com)")
chequear("nombres, correos, textos de reseña o 'example.com' en data/processed/m3 o results/data/m3", hall, [])

# ---------------------------------------------------------------- 7. Licencias (textos oficiales)
out("\n=== 7. Textos oficiales de las licencias ===")


def html_a_texto(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t))


if len(sys.argv) > 1:
    carpeta = Path(sys.argv[1])
    frag = (AQUI / "licencias_fragmentos.md").read_text(encoding="utf-8")
    textos_lic = {}
    actual = None
    for linea in frag.splitlines():
        if linea.startswith("## "):
            _, url, cuando = [s.strip() for s in linea[3:].split("|")]
            nombre = re.sub(r"[^a-zA-Z0-9]", "_", url) + ".html"
            actual = html_a_texto((carpeta / nombre).read_text(encoding="utf-8", errors="replace"))
            textos_lic[url] = actual
            out(f"   {url} (consulta {cuando}); sha256 del HTML = {hashlib.sha256((carpeta / nombre).read_bytes()).hexdigest()}")
        elif linea.startswith("> "):
            chequear(f"fragmento literal: {linea[2:70]}…", linea[2:] in actual, True)
    PAL = re.compile(r"\b(cite|cited|citation|citing|attribut\w*|credit)\b", re.I)
    mit = textos_lic["https://opensource.org/license/mit"]
    mit_legal = mit[mit.index("Copyright <YEAR>"):mit.index("OTHER DEALINGS IN THE SOFTWARE.") + 31]
    chequear("MIT (texto legal): palabras cite/citation/attribution/credit", PAL.findall(mit_legal), [])
    chequear("MIT (texto legal): única condición = incluir el aviso en copias",
             re.findall(r"subject to the following conditions: (.*?) THE SOFTWARE IS PROVIDED", mit_legal),
             ["The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software."])
    cc = textos_lic["https://creativecommons.org/publicdomain/zero/1.0/legalcode.en"]
    cc_legal = cc[cc.index("Statement of Purpose The laws"):cc.index("CC0 or use of the Work.") + 23]
    chequear("CC0 (código legal): palabras cite/citation/attribution/credit", PAL.findall(cc_legal), [])
    deed = textos_lic["https://creativecommons.org/publicdomain/zero/1.0/"]
    deed_cuerpo = deed[deed.index("No Copyright The person"):deed.index("Creative Commons is not a law firm")]
    out(f"   (informativo) CC0 deed, palabras de cita en el cuerpo: {PAL.findall(deed_cuerpo)} (es «When using or citing the work, you should not imply endorsement»: no exige citar)")
else:
    out("   (omitido: no se pasó la carpeta con los HTML de las licencias)")

out(f"\nRESUMEN: {CUENTA['OK']} OK, {CUENTA['FALLA']} FALLA")
(AQUI / "verificar_R3_salida.txt").write_text(salida.getvalue(), encoding="utf-8")
sys.stdout.buffer.write(salida.getvalue().encode("utf-8"))
