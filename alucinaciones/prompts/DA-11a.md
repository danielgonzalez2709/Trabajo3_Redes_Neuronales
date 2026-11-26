# Prompt DA-11a — implementador (Sonnet) — 2026-11-26 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/implementador.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`; **no hagas commit ni push**). Usa
`.venv\Scripts\python`. Solo tocas: `notebooks/00_sustentacion.py` (nuevo), `configs/notebooks/00_sustentacion.yaml` (nuevo) y
`tests/test_notebook_00.py` (nuevo). No cambies `src/comun/` (si crees que hace falta, dilo en el informe). Otros agentes
trabajan a la vez en `app/`, `scripts/`, `tests/test_juguetes_app.py` y `blog/`: no los toques.

## Tarea DA-11 (spec de Daniel; núcleo §5.10)
Lee `src/comun/notebooks.py` (`config_notebook`, `correr_demo`), `src/comun/cli.py` (subcomandos y «pendiente») y el núcleo
§4.1 y §5.10 en `docs/spec/SPEC.md`. El notebook `00_sustentacion` tiene **una celda por módulo** porque el profesor escoge el
módulo en el momento y suele pedir cambios de hiperparámetros en vivo.

- Formato *percent* de Jupytext. **Primera celda de código = parámetros**: `CONFIG = "configs/notebooks/00_sustentacion.yaml"`
  y un `SET` por módulo (`SET_M1`, `SET_M2`, `SET_M3`), dicts vacíos con un comentario de ejemplo; no inventes claves que no
  existan: como las configs de demo aún no existen, el ejemplo va comentado y marcado «ajustar cuando exista la config de demo
  de <dueño>». Segunda celda: `config_notebook(CONFIG)` imprime la config resuelta.
- Una sección por módulo (M1 demanda, M2 conducción, M3 recomendación), cada una con: markdown corto (qué demuestra, dueño,
  comando equivalente de terminal), celda markdown «Predicción antes de ejecutar» (plantilla para escribir la predicción) y
  celda de código que llama a `correr_demo(cfg, "<m>", SET_Mx)` e imprime el estado. Cero lógica en el notebook.
- `configs/notebooks/00_sustentacion.yaml`: `demos.m1|m2|m3 = {subcomando, config, requiere?, salida_temporal?}` con los
  subcomandos `m1`, `m2`, `m3` de `run.py` y configs de demo `configs/m1/demo.yaml`, `configs/m2/demo.yaml`,
  `configs/m3/demo.yaml` (hoy **no existen**: los crean los dueños; así la celda imprime «Pendiente» y no falla). Si la clave
  de salida temporal no está definida en el Spec, déjala fuera y anótalo como pendiente para los dueños.
- Pruebas (`tests/test_notebook_00.py`): la primera celda de código define `CONFIG` y los `SET_*`; la config carga con
  `config_notebook`; con las configs de demo ausentes cada `correr_demo` devuelve `{"estado": "pendiente"}` sin lanzar; con una
  config de demo falsa en `tmp_path` que apunte a un subcomando «pendiente», devuelve `error` con código 2 (sin red, < 10 s).
- Si `run.py notebooks` permite ejecutar solo este notebook rápido, verifica que convierte y ejecuta `00_sustentacion` (todas
  las celdas «Pendiente»); si no, dilo y no generes `.ipynb` de los demás.

## Aceptación
`.venv\Scripts\python -m pytest -q` en verde; el notebook corre completo hoy (con «Pendiente») en < 1 min. Informe ≤ 30 líneas
con archivos, decisiones, pendientes para los dueños (qué deben crear para que su celda funcione) y resultados. Nada inventado.
