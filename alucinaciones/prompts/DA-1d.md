# Prompt DA-1d — implementador (Sonnet) — 2026-11-24 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/implementador.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`, commit `ba19487`; **no hagas
commit ni push**). Usa `.venv\Scripts\python`; no cambies `requirements.txt`.

Contexto: DA-1 (infraestructura) pasó por tres revisores. `revisor-spec` lo aprobó. `revisor-calidad` y
`auditor-reproducibilidad` pidieron estos cambios. Corrige **solo esto**, prueba primero cuando aplique:

## Bloqueantes
1. `src/comun/notebooks.py` (`correr_demo`, ~l. 75): `subprocess.run(..., timeout=...)` lanza `TimeoutExpired` sin capturar.
   Captúralo y devuelve un resultado con estado `"timeout"` y un mensaje claro (la celda del notebook de sustentación no debe
   terminar en traceback). Prueba en `tests/test_notebooks_comun.py` con un comando que exceda un timeout pequeño.
2. `README.md` (Windows):
   - Advertir que el clon debe ir en una **ruta corta** (p. ej. `C:\proy\Trabajo3_Redes_Neuronales`) porque `pip install`
     falla por el límite de 260 caracteres de Windows en rutas profundas; mencionar la alternativa de habilitar rutas largas
     (requiere administrador).
   - Usar `.venv\Scripts\python` (o activar el venv explícitamente) en **todos** los comandos: en esa máquina `python` del
     PATH es 3.13, no 3.12.
3. `README.md`: los comandos de §4.1 usan `configs/...`, que aún no existe (cada config la crea su dueño en su tarea). Deja
   en el README los comandos que **ya funcionan hoy** (`--help`, pytest, mkdocs, `python -m src.m1_demanda.sintetico`) y
   presenta la tabla de §4.1 como «se habilita cuando el dueño entrega su tarea» con la columna dueño (ID). La sección
   «Semillas» no debe afirmar que `base_seed` ya está en `configs/`.

## Recomendados
4. Eliminar `_texto_comando` (sin uso) en `notebooks.py`; `config_notebook` debe reutilizar `_valor_set` en vez de duplicarlo.
5. `tests/test_config.py`: quitar imports y constantes sin uso (`subprocess`, `sys`, `ROOT`).
6. Mover a `tests/conftest.py` las fixtures duplicadas en `test_cli.py` y `test_config.py` (`recibido`, `cfg_file`,
   `_config_impresa`).
7. `tests/test_cli.py`: las pruebas que dependen de subcomandos reales pendientes (`m1-operacion`, `m1`) fallarán cuando los
   dueños los implementen. Reemplázalas por un subcomando falso registrado con `monkeypatch` (o un módulo falso) para probar
   el despacho y el «pendiente» con código 2. Cambia la afirmación casi siempre verdadera (~l. 128) por la salida exacta.
   No parchees `cli.importlib.import_module` (módulo `importlib` completo): parchea la función interna del CLI.
8. `src/m1_demanda/sintetico.py` (~l. 81 y 83): reemplazar la división por `86_400e9` por
   `(fechas - pd.Timestamp("1970-01-01")) / pd.Timedelta(days=1)` o equivalente sin suponer nanosegundos. La serie debe
   seguir siendo **idéntica** (SHA-256 del parquet versionado
   `4a720e00ddca354d97b66da5108129470911844caec1ac229b25a0b42d705ae7`); si cambiara, detente y repórtalo.
9. Pruebas para lo que sostiene garantías: `src/comun/results.py` (rechazo de NaN en `save_json`, escritura atómica),
   `src/comun/torch_utils.py` (`resolver_device`, rechazo de NaN en `a_tensor`), `src/comun/notebooks.py` (el punto 1 y
   `config_notebook`).
10. `.gitattributes` (como el del Trabajo 2): `*.py, *.yaml, *.md, *.json, *.ts, *.tsx text eol=lf`;
    `data/processed/** -text`; `alucinaciones/evidencias/** -text`; `*.parquet, *.pt, *.joblib, *.onnx binary`. Después
    corre `git add --renormalize .` y reporta qué archivos cambian (no hagas commit).
11. `README.md`: mencionar que `NO_MKDOCS_2_WARNING=1` silencia el aviso informativo de Material en `mkdocs build`.

## Aceptación
`.venv\Scripts\python -m pytest -q` en verde (pega la salida), SHA-256 del parquet sintético sin cambios tras regenerarlo,
`mkdocs build --strict` sin errores. Entrega: archivos cambiados, salidas reales, dudas.
