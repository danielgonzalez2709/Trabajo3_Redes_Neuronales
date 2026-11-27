# Prompt CA-134-revision-spec — revisor-spec (Sonnet) — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/revisor-spec.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). Python: `.venv/bin/python`.
**Solo lectura: no edites archivos, no hagas `git commit` ni `git push`.** Revisa el árbol de trabajo actual (no el commit
`abe4b11`, que tiene versiones intermedias).

Lee: `docs/spec/SPEC.md` §0, §3, §4.1, §5.1, §5.2, §5.3 (reglas contra fuga), §5.4, §5.12 y el Anexo («Módulo 1»);
`docs/spec/partes/camila.md` completo; prompts de cada tarea en `alucinaciones/prompts/CA-1b.md`, `CA-3a.md` y `CA-4a.md`
(incluyen las decisiones de Camila). Decisiones de Camila posteriores al prompt de CA-3 (26-nov), ya aplicadas en
`configs/m1/operacion.yaml`: `fraccion_demanda_en_origen` = fracción de pasajeros en ORIGEN estimada con train;
`ocupacion_objetivo` = 1.0 (las capacidades ya son ocupación observada p99); mínimo 1 vuelta (`vueltas_fraccionarias: 0`);
segundo conductor desactivado.

## Qué revisar (una sección y un veredicto APROBADO / CAMBIOS REQUERIDOS por tarea)
- **CA-1** calendario: `src/m1_demanda/calendario.py`, `tests/test_calendario_m1.py`, `data/externos/m1/calendario_fuentes.yaml`,
  `data/processed/m1/calendario.parquet`, sección nueva de `data/fuentes.md`. Esquema §5.2, cada columna con fuente o supuesto
  declarado, conocible 30 días antes, decisiones de Camila del prompt CA-1b cumplidas.
- **CA-3** operación: `src/m1_demanda/operacion.py`, `configs/m1/operacion.yaml`, `tests/test_operacion_m1.py`,
  `results/data/m1/operacion/`. Firma `dimensionar` §5.4, ida y regreso, composición solo con train y ORIGEN, `--set` del §4.1,
  cada parámetro con `unidad` y `fuente` o `supuesto: true`, preparación para el formato de exportación de `app/lib/contratos.ts`.
- **CA-4** descriptivo: `src/m1_demanda/eda.py`, `tests/test_eda_m1.py`, `src/viz/figs_m1_datos.py`, `tests/test_figs_m1_datos.py`,
  salidas en `results/data/m1/eda/` y `results/figures/m1/`. Plantilla §5.12 secciones 3–7, `hipotesis.json`, figuras mínimas
  (series y descomposición semanal y anual), modelos no dibujan, ninguna marca como variable de modelo, nada sintético en
  resultados reales.

Para cada tarea: incumplimientos (con archivo:línea), cosas de más que no pide el Spec, datos o citas sin fuente, riesgos de fuga.
Corre `.venv/bin/python -m pytest -q`, `.venv/bin/python run.py m1-eda --config configs/m1/datos.yaml`,
`.venv/bin/python run.py m1-operacion --config configs/m1/operacion.yaml --set operacion.ocupacion_objetivo=0.8 --set operacion.cuantil=0.9`
y `.venv/bin/python -m src.m1_demanda.calendario` y reporta la salida real resumida. No cambies el Spec: lo que sea decisión se
escala a Camila.
