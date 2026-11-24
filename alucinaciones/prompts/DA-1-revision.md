# Prompts de revisión de DA-1 — 2026-11-24 — orquesta: Daniel

Repositorio: `C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales`, rama `dev/daniel`, commit `ba19487`
(DA-1 completo: `src/comun/`, `run.py`, CI, blog, `src/comun/eda.py`, `src/viz/`, serie sintética de M1). Los prompts de
implementación fueron `alucinaciones/prompts/DA-1a.md`, `DA-1b.md` y `DA-1c.md`. **Ningún revisor modifica archivos del repo.**

## R1 — revisor-spec (Sonnet)
Actúa como el agente definido en `.claude/agents/revisor-spec.md` (léelo primero). Revisa DA-1 contra
`docs/spec/SPEC.md` (§0, §3, §4, §4.1, §5.1, §5.10, §5.11, §5.12, §7.1, §7.2, §8) y `docs/spec/partes/daniel.md` §3.1 y la fila
DA-1 de §4. En particular: los 17 subcomandos de §4.1 y su despacho; `--set` y clave inexistente = error; esquema exacto de §5.1
en la serie sintética y códigos ficticios (no DIVIPOLA reales); plantilla §5.12 en `eda.py` y en el blog (03, 06, 07); pruebas
mínimas de §8 que correspondan a DA-1; nada añadido que el Spec no pida. Ejecuta `.venv\Scripts\python -m pytest -q`.
Salida: APROBADO o RECHAZADO + hallazgos con archivo:línea y sección del Spec.

## R2 — revisor-calidad (Haiku)
Actúa como el agente definido en `.claude/agents/revisor-calidad.md` (léelo primero). Revisa la calidad del código de DA-1:
`src/comun/*.py`, `src/viz/*.py`, `src/m1_demanda/sintetico.py`, `run.py` y las pruebas en `tests/`. Prioriza lo que alguien
del equipo tendría que explicar o modificar en vivo (CLI, config, semillas, eda). Salida: APROBADO o CAMBIOS REQUERIDOS con
hallazgos priorizados (bloqueante / recomendado) y archivo:línea.

## R3 — auditor-reproducibilidad (Haiku)
Actúa como el agente definido en `.claude/agents/auditor-reproducibilidad.md` (léelo primero). Alcance de hoy: solo lo que
DA-1 debe cumplir (aún no hay modelos, demos, app ni datos reales). Pasos:
1. `git clone --branch dev/daniel "C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales" <carpeta temporal nueva>`
   (usa una carpeta dentro de
   `C:\Users\danie\AppData\Local\Temp\claude\4dc77ad0ee14e84c\6f603fae-d809-443f-a910-1822e4048a3e\scratchpad\`).
2. Sigue el README al pie de la letra para Windows: venv con Python 3.12 e `pip install -r requirements.txt`. Mide el tiempo.
3. `python -m pytest -q`, `python run.py --help`, un subcomando pendiente (debe salir con código 2),
   `python -m mkdocs build --strict -f blog/mkdocs.yml`, y `python -m src.m1_demanda.sintetico` (debe regenerar la serie igual:
   compara el SHA-256 del parquet con el versionado).
4. Reporta cualquier paso que el README no documente.
Salida: tabla `requisito | resultado | evidencia (comando y salida)`. Borra la carpeta temporal al terminar.
