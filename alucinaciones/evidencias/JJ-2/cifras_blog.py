"""R4 (cazador, JJ-2): extrae cada cifra de blog/secciones/07-m3-recomendacion.md y busca un valor de
results/data/m3/eda/* (o perfil_nuevo.json) que, redondeado a la precisión mostrada, la reproduzca.
Uso: python -I cifras_blog.py <raiz_repo>"""
import csv, json, re, sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

raiz = Path(sys.argv[1])
eda = raiz / "results/data/m3/eda"
valores = []          # (archivo, ruta, float)

def plano(o, ruta, arch):
    if isinstance(o, dict):
        for k, v in o.items():
            plano(v, f"{ruta}.{k}", arch)
            try: valores.append((arch, f"{ruta}.<clave>", float(k)))
            except ValueError: pass
    elif isinstance(o, list):
        for i, v in enumerate(o): plano(v, f"{ruta}[{i}]", arch)
    elif isinstance(o, bool) or o is None: pass
    elif isinstance(o, (int, float)): valores.append((arch, ruta, float(o)))
    elif isinstance(o, str):
        for m in re.finditer(r"-?\d+(?:[.,]\d+)?", o):
            valores.append((arch, ruta + "<texto>", float(m.group().replace(",", "."))))

for p in sorted(eda.glob("*.json")) + [raiz / "app/public/model/m3/perfil_nuevo.json"]:
    plano(json.loads(p.read_text(encoding="utf-8")), "", p.name)
for p in sorted(eda.glob("*.csv")):
    with p.open(encoding="utf-8") as f:
        for i, fila in enumerate(csv.DictReader(f)):
            for k, v in fila.items():
                try: valores.append((p.name, f"[{i}].{k}", float(v)))
                except (ValueError, TypeError): pass
                if v and not re.fullmatch(r"-?\d+(\.\d+)?", v):
                    for m in re.finditer(r"\d+", v): valores.append((p.name, f"[{i}].{k}<texto>", float(m.group())))

md = (raiz / "blog/secciones/07-m3-recomendacion.md").read_text(encoding="utf-8").splitlines()
patron = re.compile(r"(?<![\w.§@-])[−-]?\d{1,3}(?: \d{3})+(?:,\d+)?(?![\d])|(?<![\w.§@-])[−-]?\d+(?:,\d+)?(?![\d\w])")

def coincide(texto, v):
    t = texto.replace("−", "-").replace(" ", "").replace(",", ".")
    dec = len(t.split(".")[1]) if "." in t else 0
    q = Decimal(1).scaleb(-dec)
    cand = [v, v * 100]     # proporción mostrada en %
    return any(Decimal(repr(c)).quantize(q, ROUND_HALF_UP) == Decimal(t) for c in cand) or \
           any(Decimal(repr(abs(c))).quantize(q, ROUND_HALF_UP) == Decimal(t.lstrip("-")) and t.startswith("-") == (c < 0) for c in cand)

total, sin = 0, []
for n, linea in enumerate(md, 1):
    if linea.lstrip().startswith("<!--"): continue
    limpia = re.sub(r"`[^`]*`", "", linea)              # claves y rutas
    limpia = re.sub(r"\[\[[^\]]*\]\]|\[@[^\]]*\]|\([^)]*\.png\)", "", limpia)
    for m in patron.finditer(limpia):
        tok = m.group()
        total += 1
        hits = [(a, r) for a, r, v in valores if coincide(tok, v)]
        if not hits: sin.append((n, tok, linea.strip()[:110]))
print(f"cifras extraídas: {total}; sin ningún valor que las reproduzca: {len(sin)}")
for n, tok, l in sin: print(f"  l.{n}: {tok!r} | {l}")
