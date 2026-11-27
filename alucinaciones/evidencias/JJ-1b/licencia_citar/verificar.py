r"""Evidencia del candidato «todas las licencias piden citar la fuente» (JJ-1b, R1 B-1).

Lee la respuesta cruda de Kaggle guardada en la fase A y muestra qué secciones de la descripción piden citar o atribuir.
Sin internet. Uso, desde la raíz: .venv\Scripts\python -I alucinaciones/evidencias/JJ-1b/licencia_citar/verificar.py
"""
import io
import json
import sys
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
META = RAIZ / "docs" / "investigacion" / "JJ-1_kaggle_metadata.json"

salida = io.StringIO()
_print = print
def print(*a, **k):
    _print(*a, **k, file=salida)

respuestas = json.loads(META.read_text(encoding="utf-8"))["respuestas"]
info = next(r["cuerpo"]["info"] for r in respuestas if r["url"].endswith("datasets/metadata/amanmehra23/travel-recommendation-dataset"))
descripcion = info["description"]
print("Campo formal de licencia:", [l["name"] for l in info["licenses"]])

secciones = dict(re.findall(r"### (\w[\w ]*)\n(.*?)(?=\n### |\Z)", descripcion, flags=re.S))
patron = re.compile(r"\b(cite|citation|attribut\w*|credit)\b", re.I)
for nombre in ("Usage", "License"):
    texto = secciones[nombre].strip()
    print(f"\nSección «{nombre}»: {texto!r}")
    print("  pide citar/atribuir:", bool(patron.search(texto)), "->", patron.findall(texto))

(Path(__file__).parent / "salida.txt").write_text(salida.getvalue(), encoding="utf-8")
sys.stdout.buffer.write(salida.getvalue().encode("utf-8"))
