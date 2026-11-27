# M3 — Recomendación de destinos de viaje

- **Dueño (núcleo §1.1):** Juan José (`datos.py`, `particion.py`, `eda.py`, `referencia.py`, `redes.py`, `metricas.py`,
  `negocio.py`, `hpo.py`, `experimento.py`, `exportar.py`).
- **Comandos:** `m3-datos` y `m3-eda` (listos), `m3` y `m3-hpo` (pendientes; ver `python run.py --help` y la tabla de
  `src/comun/cli.py`). Datos: `.venv\Scripts\python run.py m3-datos --config configs/m3/datos.yaml` (sin red; < 10 s).
- **Configs:** `configs/m3/datos.yaml` (listo: SHA-256 de la fuente, citas literales verificadas, parámetros de la ficha);
  `configs/m3/eda.yaml` (listo: semillas por uso del azar, tamaños de permutación, bootstrap y simulación, emparejamiento
  preferencia→tipo, umbral de actividad, alfa, ajuste de Holm y criterio de veredicto);
  `configs/m3/{base,demo,hpo}.yaml` — pendiente.
- **Datos:** `data/processed/m3/{destinos,usuarios,interacciones}.parquet` (núcleo §5.7; JJ-1 listo; JJ-3 agrega la
  columna `split` ∈ {`train`, `validacion`, `prueba`}, una sola partición para todos los modelos) y `results/data/m3/eda/{ficha.json,calidad.csv,diccionario.json}` (plantilla §5.12, secciones 1–2).
  Fuente y regeneración: `data/fuentes.md` (sección M3). `Name`, `Email` y `ReviewText` no pasan a ninguna salida.
- **Partición (JJ-3, D3 y D8–D10 de `docs/spec/partes/juanjose.md` §3.1):** la calcula `m3-datos` con la semilla de
  `particion.semilla` (`configs/m3/datos.yaml`) y escribe `results/data/m3/particion/resumen.json` (conteos, diagnósticos,
  SHA-256 del parquet y huella de la partición). `particion.py` da `popularidad_train`, `historial_conocido` y `candidatos`:
  los modelos solo usan estadísticas de train. Pruebas: `tests/test_fuga_m3.py`.
- **Análisis descriptivo (JJ-2, secciones 3–7 de la plantilla §5.12):**
  `.venv\Scripts\python run.py m3-eda --config configs/m3/eda.yaml` (sin red; lee solo `data/processed/m3/`; unos 5 s; salidas
  deterministas) escribe en `results/data/m3/eda/` los conteos por entidad, `distribucion_actividad.json`,
  `concentracion.json`, `actividad_usuarios.json`, `calificaciones.csv`, `coincidencia_preferencias.json`,
  `matriz_preferencias_tipo.csv`, `demografia_tipo.csv`, `pruebas_hipotesis.json` y `hipotesis.json`. Las 4 figuras
  (`cola_larga`, `lorenz`, `preferencias_tipo`, `calificaciones_origen`) salen con `.venv\Scripts\python run.py figures` en
  `blog/docs/figures/m3/`, leyendo solo `results/data/m3/eda/`. Pruebas: `tests/test_eda_m3.py`.
- **Resultados:** `results/data/m3/` y `results/tables/` (núcleo §5.9) — pendiente.
- **Notebook:** `notebooks/05_m3` — pendiente.
- **Código:** `datos.py` (JJ-1), `eda.py` (JJ-2) y `particion.py` (JJ-3) listos; los demás módulos `.py` los agrega el dueño (mientras no existan, su comando imprime
  «pendiente»). Pruebas: `tests/test_datos_m3.py` con fixtures ficticios en `tests/fixtures/m3/`.
