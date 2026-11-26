# M3 — Recomendación de destinos de viaje

- **Dueño (núcleo §1.1):** Juan José (`datos.py`, `particion.py`, `eda.py`, `referencia.py`, `redes.py`, `metricas.py`,
  `negocio.py`, `hpo.py`, `experimento.py`, `exportar.py`).
- **Comandos:** `m3-datos` (listo), `m3-eda`, `m3`, `m3-hpo` (pendientes; ver `python run.py --help` y la tabla de
  `src/comun/cli.py`). Datos: `.venv\Scripts\python run.py m3-datos --config configs/m3/datos.yaml` (sin red; < 10 s).
- **Configs:** `configs/m3/datos.yaml` (listo: SHA-256 de la fuente, citas literales verificadas, parámetros de la ficha);
  `configs/m3/{base,demo,hpo}.yaml` — pendiente.
- **Datos:** `data/processed/m3/{destinos,usuarios,interacciones}.parquet` (núcleo §5.7; JJ-1 listo, sin `split`: la
  partición es de JJ-3) y `results/data/m3/eda/{ficha.json,calidad.csv,diccionario.json}` (plantilla §5.12, secciones 1–2).
  Fuente y regeneración: `data/fuentes.md` (sección M3). `Name`, `Email` y `ReviewText` no pasan a ninguna salida.
- **Resultados:** `results/data/m3/` y `results/tables/` (núcleo §5.9) — pendiente.
- **Notebook:** `notebooks/05_m3` — pendiente.
- **Código:** `datos.py` listo (JJ-1); los demás módulos `.py` los agrega el dueño (mientras no existan, su comando imprime
  «pendiente»). Pruebas: `tests/test_datos_m3.py` con fixtures ficticios en `tests/fixtures/m3/`.
