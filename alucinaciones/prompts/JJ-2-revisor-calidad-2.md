# Prompt JJ-2 (R3, 2.ª vuelta) — revisor-calidad (Haiku) — 2026-11-26 — orquesta: Juan José

Mismas reglas que tu primer encargo (`alucinaciones/prompts/JJ-2-revisor-calidad.md`): solo lectura, sin commit/push.
El analista aplicó tus hallazgos según `alucinaciones/prompts/JJ-2-analista-experimentos-4.md` (B1–B4, R1, R2, R3, R5, R7,
R10, R11, R6 parcial); el analista se colgó al final y la sesión principal terminó R1 (pie de `preferencias_tipo.png` con la
línea base por fila, `src/viz/figs_m3.py:texto_linea_base`) y quitó la prueba de largo de línea (fijaba estilo, no
comportamiento). `eda.py` quedó dividido en `eda.py`, `eda_estadistica.py` y `eda_hipotesis.py`.

Verifica **solo** que B1–B4 y R1, R2, R3, R5, R7, R10, R11 están resueltos (archivo:línea), y que
`.venv/Scripts/python -m pytest -q tests/test_eda_m3.py tests/test_datos_m3.py -p no:cacheprovider` pasa. No pidas R4, R8, R9
total ni opcionales (quedan como pendientes declarados). Responde **APROBADO** / **NO APROBADO** con los hallazgos que queden.
