"""R4 (cazador-alucinaciones, JJ-2). Uso: python -I verificar_R4.py <raiz_repo> <carpeta_R4>"""
import json, re, sys, hashlib
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
R, E = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
eda = R / "results/data/m3/eda"
J = lambda n: json.loads((eda / n).read_text(encoding="utf-8"))
blog = (R / "blog/secciones/07-m3-recomendacion.md").read_text(encoding="utf-8")
ok = mal = 0


def chk(desc, cond):
    global ok, mal
    ok += bool(cond)
    mal += (not cond)
    print(("OK  " if cond else "MAL ") + desc)


print("== 1. Claves citadas en el blog que deben contener la cifra ==")
lug = (eda / "interacciones_por_lugar.csv").read_text(encoding="utf-8")
c = J("concentracion.json")
chk("l.225-226: el Gini por lugar (0,025 / 0,023) se cita a interacciones_por_lugar.csv; columnas del CSV: "
    + lug.splitlines()[0], "gini" in lug.splitlines()[0])
print("     (el Gini por lugar está en concentracion.json niveles.lugar: %.4f / %.4f)"
      % (c["niveles"]["lugar"]["observado"]["gini"], c["niveles"]["lugar"]["azar_uniforme"]["gini"]["media"]))
d = J("distribucion_actividad.json")
chk("l.224: 'máximo medio del azar 7,915' = destinos.max_interacciones_azar_media (%s; usuarios %s)"
    % (d["destinos"]["max_interacciones_azar_media"], d["usuarios"]["max_interacciones_azar_media"]),
    d["destinos"]["max_interacciones_azar_media"] == 7.915)
dentro = all(lo <= d[n]["observado"][k] <= hi for n in ("usuarios", "destinos") for k, (lo, hi) in d[n]["azar_ic95"].items())
chk("l.150: todas las barras observadas dentro del IC 95 %% del azar: %s" % dentro, dentro)
f = J("ficha.json")
chk("l.53: los_que_aparecen union 0,00269 -> %.5f" % f["conteos"]["densidad"]["union"]["los_que_aparecen"],
    round(f["conteos"]["densidad"]["union"]["los_que_aparecen"], 5) == 0.00269)
chk("tabla m3-ficha: denominadores = usuarios x destinos que aparecen",
    all(f["conteos"]["densidad"][o]["denominador_los_que_aparecen"]
        == f["conteos"]["usuarios_que_aparecen"][o] * f["conteos"]["destinos_que_aparecen"][o]
        for o in ("resena", "historial", "union")))
pr = J("pruebas_hipotesis.json")
P = {t["id_prueba"]: t for t in pr["pruebas"]}
lim = sorted(k for k, t in P.items() if t["familia"] == "confirmatoria" and t["efecto"].get("en_el_limite"))
chk("l.310: en_el_limite = true solo en H1_permutacion_tasa y H4_n_adultos: %s" % lim,
    lim == ["H1_permutacion_tasa", "H4_n_adultos"])
fam = pr["familia_confirmatoria"]
ps = sorted((P[k]["p_crudo"], k) for k in fam)
m, acc, holm = len(ps), 0.0, {}
for i, (p, k) in enumerate(ps):
    acc = max(acc, min(1.0, (m - i) * p))
    holm[k] = acc
chk("Holm recalculado = p_ajustado guardado (10 pruebas)", all(abs(holm[k] - P[k]["p_ajustado"]) < 1e-12 for k in fam))

print("== 2. Regla vigente: función frente a lo guardado en hipotesis.json (10 pruebas) ==")
sys.path.insert(0, str(R))
from src.m3_recomendacion.eda_hipotesis import veredicto_de_prueba  # noqa: E402
mins = pr["criterio_de_veredicto"]["efecto_minimo"]
h = {x["id"]: x for x in J("hipotesis.json")}
for k in fam:
    t = P[k]
    e = t["efecto"]
    v = veredicto_de_prueba(t["p_ajustado"], e["valor"], tuple(e["ic95"]), mins[e["umbral"]], 0.05, t["alternativa"])
    chk(f"  {k}: función -> {v}; coincide con hipotesis.json", (k + ": " + v) in h[t["hipotesis"]]["resultado"])

print("== 3. Candidato analista: regla escrita en pruebas_hipotesis.json (copia del 26-nov 02:21) ==")
pa = json.loads((E / "pr_antes.json").read_text(encoding="utf-8"))
ha = json.loads((E / "hip_antes.json").read_text(encoding="utf-8"))
print("  regla escrita:", pa["criterio_de_veredicto"]["regla"])
t = next(x for x in pa["pruebas"] if x["id_prueba"] == "H1_permutacion_tasa")
lo, hi = t["efecto"]["ic95"]
escrita = "refuta" if (t["p_ajustado"] >= 0.05 and -0.05 < lo and hi < 0.05) else "otra"
codigo = veredicto_de_prueba(t["p_ajustado"], t["efecto"]["valor"], (lo, hi), 0.05, 0.05, "mayor")
vh = next(x for x in ha if x["id"] == "H-M3-1")["veredicto"]
print(f"  H1: p_aj={t['p_ajustado']:.5f}, IC=[{lo:.6f}; {hi:.6f}] -> regla escrita: {escrita} (H-M3-1 «refutada»); "
      f"función: {codigo}; veredicto guardado: {vh}")
chk("  la regla escrita y la función discrepan en H1", escrita != codigo and vh == "no concluyente")
v1 = (E / "eda_analista_v1.py").read_text(encoding="utf-8")
print("  eda.py 1.ª versión del analista (06:50), condición 'estrecho':", re.search(r"estrecho = [^\n]+", v1).group())
print("  sha256 pr_antes.json:", hashlib.sha256((E / "pr_antes.json").read_bytes()).hexdigest())

print("== 4. Candidato redactor: frase de métodos de la 1.ª versión del blog (07:01) ==")
b1 = (E / "blog_07_redactor_v1.md").read_text(encoding="utf-8")
i = b1.find("Los p de H-M3-1 a H-M3-4")
print("  v1:", b1[i:i + 330].replace("\n", " "))
for k in ("H3_spearman_popularidad", "H5_gini_destino_id", "H6_chi2_origen_tipo", "H6_mann_whitney_calificacion"):
    print(f"  {k}: descripcion={P[k]['descripcion'][:62]!r} | metodo_p={P[k]['metodo_p'][:40]!r} | "
          f"metodo_ic={P[k]['efecto']['metodo_ic'][:45]!r}")
chk("  H-M3-3 permuta entre destinos, no entre usuarios", "entre los destinos" in P["H3_spearman_popularidad"]["descripcion"])
chk("  los IC de H-M3-5 no son remuestreos de usuarios", "no es un bootstrap" in P["H5_gini_destino_id"]["efecto"]["metodo_ic"])
chk("  los p de H-M3-6 son asintóticos", all("asint" in P[k]["metodo_p"] for k in ("H6_chi2_origen_tipo", "H6_mann_whitney_calificacion")))
chk("  la frase v1 ya no está en el blog vigente", "Los p de H-M3-1 a H-M3-4" not in blog)
i = b1.find("no son umbrales")
print("  v1 (mínimos):", b1[i - 270:i + 30].replace("\n", " "))
print("  sha256 blog_07_redactor_v1.md:", hashlib.sha256((E / "blog_07_redactor_v1.md").read_bytes()).hexdigest())

print("== 5. Cita del conjunto ==")
meta = json.loads((R / "docs/investigacion/JJ-1_kaggle_metadata.json").read_text(encoding="utf-8"))
vista = next(r for r in meta["respuestas"] if "/view/" in r["url"])["cuerpo"]
desc = vista["description"]
ver = vista["versions"][0]
print("  creatorName:", vista["creatorName"], "| title:", vista["title"], "| currentVersionNumber:",
      vista["currentVersionNumber"], "| versions[0]:", ver.get("versionNumber"), ver["creationDate"])
bib = (R / "blog/references.bib").read_text(encoding="utf-8")
ent = bib[bib.find("@dataset{mehra2024"):].split("\n}")[0]
chk("  bib: autor Mehra, Aman", "Mehra, Aman" in ent and vista["creatorName"] == "Aman Mehra")
chk("  bib: year 2024 = año de creación de la versión 1", "{2024}" in ent and ver["creationDate"].startswith("2024-01-23"))
chk("  bib: version 1", "version      = {1}" in ent and vista["currentVersionNumber"] == 1)
chk("  bib: título", "Travel recommendation dataset" in ent and vista["title"].lower() == "travel recommendation dataset")
chk("  bib = ficha: url", f["url"] in ent)
chk("  bib urldate = ficha fecha_descarga = 2026-11-25", "urldate      = {2026-11-25}" in ent and f["fecha_descarga"] == "2026-11-25")
chk("  ficha.cita coherente con bib", f["cita"].startswith("Mehra, A. (2024). Travel recommendation dataset (Versión 1)"))
chk("  blog: «publicaci» solo aparece para negar que 2024-01-23 sea publicación",
    len(re.findall("publicaci", blog)) == 1 and "no una fecha de publicación" in blog)
ingles = re.compile(r"\b(the|dataset|generated|enriched|with|for|purposes|use)\b")
for q in re.findall(r"«([^»]+)»", blog):
    q = re.sub(r"\s+", " ", q)
    if ingles.search(q) and not re.search(r"[áéíóúñ¿]", q):
        chk(f"  cita literal (en inglés) ⊂ info.description: «{q[:72]}»", q in re.sub(r"\s+", " ", desc))
chk("  título alterno «India Travel Recommender System Dataset» ⊂ description", "India Travel Recommender System Dataset" in desc)
chk("  únicas referencias [@…] del blog: mehra2024", set(re.findall(r"\[@([^\]]+)\]", blog)) == {"mehra2024"})
print(f"\nTOTAL: {ok} OK, {mal} MAL")
