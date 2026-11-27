# Prompt CA-15c — implementador (Sonnet) — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/implementador.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). Python: `.venv/bin/python`.
**Prohibido hacer `git commit`, `git push` o cualquier operación que cambie el historial: Camila revisa todo antes.**
No toques `operacion.py`, `eda.py`, `eda_hipotesis.py`, `src/comun/`, `run.py` ni el Spec. **No crees `tests/test_fuga_m1.py`**
(Camila decidió dejarlo a Andrés, dueño del arnés).

Contexto: `docs/spec/SPEC.md` §0 (regla 0.9: nada que no se conozca 30 días antes), §5.2, §5.3 (reglas contra fuga); prompts
`alucinaciones/prompts/CA-1b.md` y `CA-5a.md`; `data/fuentes.md` (sección «Calendario exógeno de M1»).

## Parte 1 — calendario: columna «conocible desde» (fuga hallada por auditor-fugas)
El auditor encontró que `vacaciones_escolares_52001` vale True del 2022-01-03 al 2022-01-06 por la Res. 2706 de Pasto, expedida el
2021-12-07: pronósticos con origen anterior a esa fecha usan información que no existía. **Decisión de Camila: regla general**.
Archivos: `data/externos/m1/calendario_fuentes.yaml`, `src/m1_demanda/calendario.py`, `tests/test_calendario_m1.py`,
`data/processed/m1/calendario.parquet`, sección del calendario en `data/fuentes.md`.
- Por cada columna de vacaciones por ciudad, agrega `vacaciones_escolares_<DIVIPOLA>_conocible_desde` (fecha): la fecha de
  expedición del acto (versión original, decisión de Camila) que fija el valor de ese día; nulo si el valor es nulo. Úsala también
  para `vacaciones_escolares` (Bogotá). Festivos: la Ley 51/1983 es de 1983, todo es conocible; no hace falta columna, decláralo.
  `fin_de_anio` y `puente` son reglas fijas (supuestos), conocibles siempre.
- Si un acto no tiene fecha de expedición en el YAML, `TODO(dato-faltante)` y nulo; no la inventes.
- Pruebas: Pasto 2022-01-03 → conocible_desde = 2021-12-07; toda fecha conocible_desde ≤ la fecha del día que describe o
  documentada si no; tipos.
- Actualiza `data/fuentes.md` explicando la columna y cómo deben usarla los modelos (anular la variable cuando
  origen < conocible_desde). Avisa en tu reporte el nuevo SHA-256 del parquet.

## Parte 2 — referencias: respetar «conocible desde» + calidad (CA-5)
Archivos: `src/m1_demanda/referencia.py`, `configs/m1/referencia.yaml`, `tests/test_referencia_m1.py`, salidas en
`results/data/m1/pred_test_*.parquet` y `results/data/m1/referencia/`.
1. En `regresion_calendario`, al construir las variables de un par (origen, objetivo) —en train y en pronóstico— la variable de
   vacaciones del objetivo vale 0/NaN (documenta cuál y por qué) si `origen < conocible_desde`. Prueba: con el calendario real, la
   fila de Pasto con origen 2021-12-05 y objetivo 2022-01-04 no ve la vacación; con origen 2021-12-08 sí. Reporta cuánto cambian el
   MAE provisional y los coeficientes de 52001-52356.
2. Agrega a `evidencia` de `presupuesto.json` un SHA-256 de la partición (`inicio_entrenamiento`, `fin_entrenamiento` y la rejilla
   de orígenes), como pide §6 (observación del revisor-spec).
3. Recomendaciones del revisor-calidad: quitar `self._cols` (código muerto); helper único `_cuantiles_desplazados` para los dos
   modelos; partir `_matriz` en `_resumenes_historia` y `_variables_calendario` (docstring (a), (b), (c)); partir `_leer` en
   `_leer_serie` y `_leer_calendario`; documentar en una línea por qué el ajuste excluye puntos NaN y el pronóstico del ingenuo usa la
   media de respaldo; fechas como `Timestamp` hasta la salida; helper `assert_mismos_parametros` en las pruebas; quitar la aserción
   trivial de `test_referencia_m1.py:129-130`; reescribir el comentario con pregunta de la línea 198; mover `_nanmean` junto a los
   helpers; condiciones largas en varias líneas; pruebas de bordes: origen antes del primero usable, ruta sin residuos o sin filas,
   ingenuo con todos los candidatos NaN, serie con ceros, horizonte fuera de rango, `fin <= inicio`, `_validar_tramos`.

Al final corre: `.venv/bin/python -m src.m1_demanda.calendario`, `.venv/bin/python -m src.m1_demanda.referencia --config
configs/m1/referencia.yaml`, `.venv/bin/python run.py m1-eda --config configs/m1/datos.yaml`, `.venv/bin/python run.py figures`
y `.venv/bin/python -m pytest -q`. Reporta salida real, celdas/columnas nuevas del parquet, SHA nuevo y MAE antes/después.
