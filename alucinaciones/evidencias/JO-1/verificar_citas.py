"""JO-1 (M2) - check every quoted text «...» of the source reports against the primary sources.

Primary sources were downloaded on 2026-11-27 to alucinaciones/evidencias/JO-1/fuentes/:
  pmc.xml            PMC12019831 via NCBI E-utilities efetch (db=pmc)  -> article text (A)
  mendeley_ds.json   Mendeley public API, dataset mzb4b6dff3 v1        -> description and licence (M)
  zenodo.json        Zenodo API, record 14908802                        -> description (Z)
  crossref_art.json  Crossref, DOI 10.1016/j.dib.2025.111529            -> metadata (C)

Each quote is split at the ellipsis «…» and every fragment must appear verbatim (after normalising
whitespace, typographic quotes and the PMC ``...'' quotes) in at least one source.

    .venv/bin/python -I alucinaciones/evidencias/JO-1/verificar_citas.py
"""

import html
import json
import re
from pathlib import Path

RAIZ = Path.cwd()
F = RAIZ / "alucinaciones/evidencias/JO-1/fuentes"
SALIDA = RAIZ / "alucinaciones/evidencias/JO-1/verificar_citas_salida.txt"
INFORMES = [
    RAIZ / "docs/investigacion/JO-1_fuentes_m2.md",
    RAIZ / "results/data/m2/eda/diccionario.json",
    RAIZ / "results/data/m2/eda/ficha.json",
]


def norm(s):
    s = html.unescape(s)
    s = s.replace("``", '"').replace("''", '"').replace("“", '"').replace("”", '"').replace("’", "'")
    s = s.replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip().lower()


x = (F / "pmc.xml").read_text(encoding="utf-8")
x = re.sub(r"<(sec|title|p|td|th|tr|list-item|caption)[^>]*>", "\n", x)
pmc = re.sub(r"<[^>]+>", "", x)
md = json.loads((F / "mendeley_ds.json").read_text(encoding="utf-8"))
zen = json.loads((F / "zenodo.json").read_text(encoding="utf-8"))
cr = json.loads((F / "crossref_art.json").read_text(encoding="utf-8"))["message"]
fuentes = {
    "A(PMC)": norm(pmc),
    "M(desc)": norm(md["description"]),
    "M(licencia)": norm(md["data_licence"]["description"] + " " + md["data_licence"]["short_name"]),
    "Z(desc)": norm(re.sub(r"<[^>]+>", " ", zen["metadata"]["description"])),
    "C": norm(json.dumps(cr, ensure_ascii=False)),
}

lineas = []
total = encontradas = 0
for informe in INFORMES:
    texto = informe.read_text(encoding="utf-8")
    if informe.suffix == ".json":
        citas = []

        def recorrer(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "texto" and isinstance(v, str):
                        citas.append(v)
                    recorrer(v)
            elif isinstance(o, list):
                for v in o:
                    recorrer(v)

        recorrer(json.loads(texto))
        citas += re.findall(r"«([^»]+)»", texto)
    else:
        citas = re.findall(r"«([^»]+)»", texto)
    lineas.append(f"\n## {informe.relative_to(RAIZ)} — {len(citas)} citas")
    for cita in citas:
        frags = [f.strip(" .,;:") for f in re.split(r"…|\.\.\.", cita) if len(f.strip(" .,;:")) >= 12]
        if not frags:
            continue
        for frag in frags:
            total += 1
            donde = [n for n, t in fuentes.items() if norm(frag) in t]
            if donde:
                encontradas += 1
                lineas.append(f"[ENCONTRADA en {', '.join(donde)}] {frag[:110]}")
            else:
                lineas.append(f"[NO ENCONTRADA] {frag}")

lineas.append(f"\nResumen: {encontradas} de {total} fragmentos encontrados literalmente en las fuentes primarias descargadas.")
SALIDA.write_text("\n".join(lineas) + "\n", encoding="utf-8")
print("\n".join(l for l in lineas if "NO ENCONTRADA" in l or l.startswith("\n") or l.startswith("Resumen")))
