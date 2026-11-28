# JJ-5 — prompt literal del orquestador (Opus 5.5) al implementador-experto (Opus), 3.ª vuelta, 2026-11-27

Tercera vuelta de JJ-5: correcciones del revisor-calidad. Mismas reglas que antes (prueba primero, `.venv\Scripts\python`, sin
internet, sin commits, solo tus archivos, un solo proceso de Python con torch a la vez). Desde tu 2.ª vuelta el orquestador cambió
`medidas_personalizacion` (denominador por la descomposición ortogonal), `descripcion_frios`, comentarios de `configs/m3/{base,hpo}.yaml`
y el README, y agregó pruebas en `tests/test_red_m3.py`: respétalos. El verificador-matematico, el auditor-fugas (20/20 mutantes
muertos) y el revisor-spec ya aprobaron.

**Condición dura: son refactorizaciones de claridad; los resultados no pueden cambiar.** El consumo de los generadores aleatorios
debe quedar idéntico: después, `run.py m3 --config configs/m3/base.yaml` debe dar métricas y diagnósticos idénticos (compáralos con
una copia de `results/data/m3/summary.json` hecha ANTES de tocar nada; solo pueden cambiar tiempos). Si algo no se puede hacer sin
cambiar resultados, no lo hagas y repórtalo.

Corrige:
- **B1.** `red.negativos_train` es una copia paralela de la preparación de `ajustar` y `_lotes`; las pruebas de negativos
  (`tests/test_red_m3.py` ~228 y ~249, `tests/test_fuga_m3.py` ~578) no prueban el camino real. Extrae un único helper de
  preparación de train (usuarios, filas, columnas, excluidos) que usen `ajustar` y `negativos_train`, de modo que romper la
  exclusión de train dentro de `ajustar` haga fallar esas pruebas (compruébalo con un mutante y reviértelo). Corrige el docstring.
- **B2.** `tests/test_red_m3.py` ~365: `if n < 40: assert ...` → precondición `assert n < 40` y la aserción fuera del `if`.
- **R1.** Parte `ajustar`: `_preparar_train(...)` y `_entrenar_con_parada(...)` (el `for` de épocas con `mejor` / `sin_mejora` /
  `mejor_estado`), para que «cuándo para» se lea en una función corta y con nombre propio.
- **R2.** Una sola función de NDCG medio (p. ej. `metricas.ndcg_medio(tops, rel, usuarios, k)`) usada por `hpo.evaluar_configuracion_red`
  y por `val_loop` (si `hpo.evaluar_configuracion` de la MF puede usarla sin cambiar resultados, también; si no, déjala).
- **R3.** `n_negativos_por_epoca` sin efecto secundario dentro del generador `_lotes` ni `getattr(..., 0)`.
- **R4.** `red.py` ~191-192: usa `_en_ordenado` y `np.searchsorted` en dos líneas legibles.
- **R5.** `self._val = None` en `__init__` y la misma guarda `RuntimeError` clara en `ndcg5_validacion_actual`,
  `vector_usuario_sin_id`, `arquitectura` y `capas_torre_usuario`; prueba de cada una.
- **R6.** Un helper que recorra las capas Linear/ReLU/Dropout de una MLP, usado por `capas_torre_usuario` y `arquitectura`.
- **R7 y R8.** Sin la lambda con `noqa`; sin el alias `h = self._hp` (lee `hp["..."]` explícito).
- **R9.** Una prueba que compare los valores buscados de los bloques de `configs/m3/base.yaml` con `familias.red.mejor.params` de
  `results/data/m3/hpo_ensayos.json` (si el archivo existe; si no, `skip`).
- **R14.** `Contenido.filas` con `ids` vacío: error claro (o arreglo vacío con la forma correcta), con prueba.
- **M4, M5, M6.** `import copy` al inicio de `hpo.py` si no hay razón para el import tardío; el no-op `.replace('NDCG', 'NDCG')` y la
  repetición de etiquetas en `src/viz/figs_m3.py`; `np.array([0 * 45 + 0])` → `np.array([0])`.
No hagas R10–R13, M1–M3, M7, M8 (no valen el riesgo a esta altura); dilo en el reporte.

Al final: `.venv\Scripts\python -m pytest -q tests/test_red_m3.py tests/test_fuga_m3.py tests/test_metricas_m3.py -m "not lento"`;
`.venv\Scripts\python run.py m3 --config configs/m3/base.yaml` con la comparación contra la copia previa; `.venv\Scripts\python run.py
figures`. Pega las salidas reales. No corras `m3-hpo`.
