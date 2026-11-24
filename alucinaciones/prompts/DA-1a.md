# Prompt DA-1a — implementador (Sonnet) — 2026-11-24 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/implementador.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`; **no hagas commit ni push**).
Referencia para portar (solo lectura, mismo equipo, Trabajo 2):
`C:\Users\danie\AppData\Local\Temp\claude\4dc77ad0ee14e84c\6f603fae-d809-443f-a910-1822e4048a3e\scratchpad\t2repo`.

Lee antes: `docs/spec/SPEC.md` §0, §3, §4, §4.1, §5.10, §7.1, §7.2, §8 y `docs/spec/partes/daniel.md` §3.1.

## Tarea DA-1a — infraestructura común (parte de DA-1)
1. **Entorno:** crea `.venv` con `py -3.12 -m venv .venv`. Instala las dependencias directas y fija versiones con `pip freeze`
   en `requirements.txt`, con un encabezado como el del Trabajo 2 (Python 3.12, instrucciones, lista de directas). Directas:
   numpy, pandas, pyarrow, PyYAML, pytest, scikit-learn, scipy, matplotlib, joblib, torch, torchvision (versión compatible con
   torch), optuna, statsmodels, onnx, onnxruntime, imagehash, pillow, requests (solo para scripts de descarga), jupytext,
   nbclient, ipykernel, mkdocs==1.6.1, mkdocs-material, pypandoc_binary. Si alguna no instala en 3.12, repórtalo.
2. **Portar de `t2repo/src/common/` a `src/comun/`** (renombrando el paquete y sus imports): `config.py`, `cli.py`, `seeds.py`,
   `results.py`, `torch_utils.py`, `notebooks.py`, `__init__.py`. Quita lo específico del Trabajo 2 (PD, LGD, scorecard, EL,
   preprocesador de Lending Club). Conserva el comportamiento del cargador: YAML 1.2, `--set` repetible, clave inexistente =
   error, herencia con `hereda:`, imprime la config resuelta y el tiempo total.
3. **`run.py` y `src/comun/cli.py`** con los subcomandos de SPEC §4.1: `m1-datos, m1-eda, m1, m1-hpo, m1-operacion, m2-datos,
   m2-eda, m2, m2-hpo, m2-alertas, m3-datos, m3-eda, m3, m3-hpo, export, figures, notebooks`. Cada subcomando de módulo
   despacha de forma perezosa a una función `main(cfg)` de un módulo de `src/m1_demanda/`, `src/m2_conduccion/` o
   `src/m3_recomendacion/` (tú decides el nombre del archivo según SPEC §4; documenta la tabla subcomando → archivo:función en
   el docstring de `cli.py`). Si la función aún no existe, el comando imprime «pendiente: <dueño> (<ID de tarea>)» y sale con
   código 2. `export`, `figures` y `notebooks` recorren lo que exista de cada módulo.
4. **Paquetes de módulo:** `src/__init__.py`, `src/m1_demanda/__init__.py`, `src/m2_conduccion/__init__.py`,
   `src/m3_recomendacion/__init__.py`, `src/viz/__init__.py`, y un `README.md` corto en cada carpeta de módulo (dueño, comandos,
   configs, datos, resultados, notebook; lo pendiente se marca «pendiente»). El enunciado pide «una carpeta por módulo».
5. **Pruebas** (portadas y adaptadas): `tests/conftest.py`, `test_config.py`, `test_cli.py` (incluye: cada subcomando existe y
   uno no implementado sale con código 2), `test_seeds.py`, `test_no_network.py`. `pytest.ini` con el marcador `lento`.
6. **CI** `.github/workflows/ci.yml` como el del Trabajo 2 (Python 3.12, torch de CPU desde el índice de PyTorch, `pytest -q -m
   "not lento"`), **sin** los pasos de la app (llegan en DA-5; deja un comentario). El job se llama `pruebas`.
7. **`.gitignore`** adaptado del Trabajo 2 (incluye `data/raw/`, salidas `*_demo`, `.venv/`, `blog/site/`, `node_modules/`,
   `.claude/settings.local.json`, `*.pdf`).
8. **`README.md` raíz**: título, enlaces a Spec/PLAN/MEMORIA, instalación en Windows y Linux (como el Trabajo 2, con torch CPU
   en Linux), comandos de §4.1, semillas. Enlaces de blog, app y video como «pendiente».

## Aceptación
`.venv\Scripts\python -m pytest -q` en verde (pega la salida); `.venv\Scripts\python run.py --help` lista los 17 subcomandos;
`.venv\Scripts\python run.py m1 --config <una config de prueba>` imprime «pendiente: …» y sale con código 2.

## Reglas
- No toques `docs/`, `.claude/`, `alucinaciones/`, `blog/`, `data/`. No crees configs de módulos (son de sus dueños).
- No inventes nada que el Spec no diga; si algo es ambiguo, decide lo mínimo y repórtalo.

Entrega: archivos creados, salida real de pytest y de `run.py --help`, versiones instaladas de torch y torchvision, dudas.
