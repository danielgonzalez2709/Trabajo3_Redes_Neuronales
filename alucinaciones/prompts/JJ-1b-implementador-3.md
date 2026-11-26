# Prompt JJ-1b (correcciones de R2) — implementador (Sonnet), mismo agente — 2026-11-25 — orquesta: Juan José

El revisor-calidad pidió cambios (informe literal: `alucinaciones/evidencias/JJ-1b/respuesta-revisor-calidad-1.md`; usa sus
ids). Mismas reglas que antes: sin commit ni push; `.venv\Scripts\python`; prueba primero; solo tus archivos; no toques
`src/comun/` (R10 queda fuera: es un PR dedicado a lo común).

**Obligatorios:** B1, B2, B3, B4 (reescríbela: un texto único en `citas_literales` debe aparecer en
`ficha["licencia"]["contradiccion"]`, y nada que no venga del JSON o del código), B5.

**También hazlos** (Juan José debe poder explicar el código en vivo): R1 (CSV sin filas → error claro, con prueba); R2 (una
prueba parametrizada por función de error: `leer_csv`, `_enteros`, `verificar_citas`, `verificar_archivos`, `separar_opciones`);
R4 (prueba sin red que lea `configs/m3/datos.yaml` y `docs/investigacion/JJ-1_kaggle_metadata.json` y llame a la verificación de
citas y de la fecha de la versión, para que la CI proteja la config real); R5; R6; R7 (una sola clasificación de tipos, el mismo
nombre en la ficha y en el diccionario); R8 solo para `inconsistencias` (una función corta por inconsistencia; `inconsistencias`
solo las ensambla); R9 (las frases deben salir de lo medido o quitarse); R11; R12; O2; O6 (columna constante → «constante»);
O7 (docstrings que digan qué produce cada función); O9 (mensajes de error sin «la fase A»: di el motivo).

**No hagas:** R3, R10, O1, O3, O4, O5, O8, O10.

Si algún cambio altera una cifra de las salidas, detente y explícalo (ninguno debería). Luego corre `tests/test_datos_m3.py`,
`run.py m3-datos --config configs/m3/datos.yaml` dos veces (SHA-256 iguales entre corridas) y `pytest -q -m "not lento"`
completo. Entrega: archivos tocados, salidas reales, SHA-256 de las 6 salidas y, si cambió alguno, por qué.
