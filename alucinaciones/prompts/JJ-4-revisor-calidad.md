# JJ-4 — prompt del orquestador (Opus 5.5) al revisor-calidad (Haiku), 2026-11-27

Revisa la calidad del código de la tarea JJ-4 del Trabajo 3 (M3: popularidad, factorización implícita por ALS, aleatorio,
métricas @K, búsqueda Optuna y arnés), ya aprobada por el verificador-matematico, el auditor-fugas y el revisor-spec. Rama
`dev/juanjose`; solo lees (no edites nada). Siempre `.venv\Scripts\python`.

Archivos: `src/m3_recomendacion/metricas.py`, `referencias.py`, `experimento.py`, `hpo.py`; `configs/m3/base.yaml`, `hpo.yaml`,
`demo.yaml`; `tests/test_metricas_m3.py` y las entradas de `AJUSTES_SOLO_TRAIN` en `tests/test_fuga_m3.py`.

Criterios: legibilidad y nombres (en español, coherentes con `particion.py`); funciones cortas y con una responsabilidad;
duplicación; manejo de errores con mensajes claros; eficiencia razonable (sin bucles Python innecesarios sobre 606 × 1 000);
que las pruebas prueben comportamiento y no detalles internos, sin redundancias, y que corran rápido; que un integrante pueda
**explicar y modificar en vivo** cada archivo en la sustentación (p. ej. cambiar `evaluacion.k`, `semillas.n` o agregar el modelo
de JJ-5 en `referencias.MODELOS`); que los YAML estén comentados y sin claves muertas. Ten en cuenta dos observaciones ya
conocidas del revisor-spec (no las repitas, pero di si estás de acuerdo): `experimento.py` no limpia `semillas/` de corridas
previas con otro `semillas.n`, y `metricas_por_grupo.json` resume solo con media y desviación.

Corre `.venv\Scripts\python -m pytest -q tests/test_metricas_m3.py tests/test_fuga_m3.py --durations=10` y pega la salida.

Informe: veredicto **APROBADO** / **RECHAZADO**; hallazgos numerados con archivo y línea, problema, propuesta concreta y
gravedad (bloqueante / menor / sugerencia). Máximo 15 hallazgos, los más importantes primero.
