r"""Evidencia JJ-3: ¿«acierto por lugar trivial» para los usuarios de prueba con otro id del mismo lugar en su historial?
Cuenta los usuarios de prueba cuyo lugar objetivo está entre los lugares de su historial conocido (train ∪ validación) y lo
compara con lo esperado si el lugar del objetivo fuera uniforme sobre los 5 lugares e independiente del historial.
Uso: .venv\Scripts\python alucinaciones/evidencias/JJ-3/verificar_mismo_lugar.py"""
import pandas as pd

i = pd.read_parquet("data/processed/m3/interacciones.parquet")
d = pd.read_parquet("data/processed/m3/destinos.parquet")
i = i.merge(d[["destino_id", "lugar"]], on="destino_id")
n_lugares = d["lugar"].nunique()
objetivo = i[i["split"] == "prueba"].set_index("usuario_id")["lugar"]
conocidos = i[i["split"] != "prueba"].groupby("usuario_id")["lugar"].apply(set)
observado = sum(objetivo[u] in conocidos[u] for u in objetivo.index)
esperado = sum(len(conocidos[u]) / n_lugares for u in objetivo.index)
print(f"usuarios de prueba: {len(objetivo)} · lugares: {n_lugares}")
print(f"con otro id del mismo lugar en el historial conocido: observado {observado} · esperado por azar {esperado:.1f}")
