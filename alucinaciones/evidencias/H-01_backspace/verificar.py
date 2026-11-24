r"""H-01: la marca \bibliografia del blog quedó guardada con un carácter de control (backspace, 0x08).

Uso (desde la raíz del repo): .venv\Scripts\python alucinaciones\evidencias\H-01_backspace\verificar.py
"""
import subprocess

viejo = subprocess.run(["git", "show", "ba19487:blog/docs/index.md"], capture_output=True, check=True).stdout
nuevo = open("blog/docs/index.md", "rb").read()
for nombre, contenido in (("commit ba19487 (DA-1b, en main)", viejo), ("árbol corregido (DA-9a)", nuevo)):
    i = contenido.find(b"ibliografia")
    print(f"{nombre}: bytes={contenido[max(0, i - 2):i + 11]!r} | contiene 0x08: {b'\x08' in contenido}")
