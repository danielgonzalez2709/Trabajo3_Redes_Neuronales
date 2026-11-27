"""CA-1 verificación: recálculo independiente de los festivos 2021-2024 (sin dateutil ni el código del repo).
Pascua: algoritmo anónimo gregoriano (Meeus/Jones/Butcher), escrito aquí. Regla: Ley 51/1983 art. 1 num. 1-2
(texto leído en alcaldiabogota.gov.co Norma1.jsp?i=4954 y C-107/94). Compara con data/processed/m1/calendario.parquet.
Uso: .venv/bin/python alucinaciones/evidencias/CA-1/recalculo_festivos.py"""
from datetime import date, timedelta
from pathlib import Path
import pandas as pd

def pascua(y):
    a = y % 19; b, c = divmod(y, 100); d, e = divmod(b, 4); f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30; i, k = divmod(c, 4); l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451; mes, dia = divmod(h + l - 7 * m + 114, 31)
    return date(y, mes, dia + 1)

lunes = lambda d: d + timedelta(days=(7 - d.weekday()) % 7)   # mismo día si ya es lunes
FIJOS = [(1, 1), (5, 1), (7, 20), (8, 7), (12, 8), (12, 25)]
TRASL = [(1, 6), (3, 19), (6, 29), (8, 15), (10, 12), (11, 1), (11, 11)]
esperado = set()
for y in range(2021, 2025):
    p = pascua(y)
    esperado |= {date(y, m, d) for m, d in FIJOS} | {lunes(date(y, m, d)) for m, d in TRASL}
    esperado |= {p - timedelta(3), p - timedelta(2)}
    # Ascensión: 40.º día contando la Pascua como día 1 = jueves P+39; Corpus: jueves tras Trinidad (P+56) = P+60;
    # Sagrado Corazón: viernes tras el 2.º domingo después de Pentecostés (P+63) = P+68
    esperado |= {lunes(p + timedelta(k)) for k in (39, 60, 68)}
raiz = Path(__file__).resolve().parents[3]
df = pd.read_parquet(raiz / "data/processed/m1/calendario.parquet")
obtenido = set(df.loc[df.festivo, "fecha"])
print("Pascuas:", [str(pascua(y)) for y in range(2021, 2025)])
print("esperado", len(esperado), "parquet", len(obtenido))
print("solo esperado:", sorted(esperado - obtenido)); print("solo parquet:", sorted(obtenido - esperado))
