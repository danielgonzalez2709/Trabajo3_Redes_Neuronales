# Prompt CA-134-revision-calidad — revisor-calidad — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/revisor-calidad.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). Python: `.venv/bin/python`.
**Solo lectura: no edites archivos, no hagas `git commit` ni `git push`.** Revisa el árbol de trabajo actual.

Contexto mínimo: `docs/spec/SPEC.md` §0, §3, §4.1 y §5.10 (los notebooks son capa delgada; el código se explica en vivo en la
sustentación) y `docs/spec/partes/camila.md` §3.1, §3.3 y §3.4.

Revisa la calidad del código de tres tareas de Camila (el cumplimiento del Spec lo revisa otro agente en paralelo):
- CA-1: `src/m1_demanda/calendario.py`, `tests/test_calendario_m1.py`.
- CA-3: `src/m1_demanda/operacion.py`, `configs/m1/operacion.yaml`, `tests/test_operacion_m1.py`.
- CA-4: `src/m1_demanda/eda.py` (≈800 líneas), `tests/test_eda_m1.py`, `src/viz/figs_m1_datos.py`, `tests/test_figs_m1_datos.py`.

Criterios: legibilidad y nombres en español coherentes con `src/comun/` y `src/m1_demanda/datos.py`; funciones pequeñas y puras;
duplicación (¿reutiliza `src/comun/eda.py`, `src/comun/results.py`, `src/viz/estilo.py`?); pruebas que prueban comportamiento y
no implementación; eficiencia razonable (`run.py m1-eda` < 30 s); facilidad para que Camila explique y modifique cada fórmula en
vivo; constantes quemadas que deberían ir a config. Para cada hallazgo: `archivo:línea`, severidad (alta/media/baja), problema y
arreglo sugerido. Veredicto por tarea: APROBADO / CAMBIOS REQUERIDOS. Corre `.venv/bin/python -m pytest -q` y reporta el resultado.
