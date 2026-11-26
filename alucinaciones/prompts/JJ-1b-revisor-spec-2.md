# Prompt JJ-1b (R1, segunda revisión) — revisor-spec (Sonnet), mismo agente — 2026-11-25 — orquesta: Juan José

El implementador corrigió tus hallazgos (respuesta literal: `alucinaciones/evidencias/JJ-1b/respuesta-implementador-2.md`;
prompt: `alucinaciones/prompts/JJ-1b-implementador-2.md`). Además, el orquestador:
- corrigió `docs/investigacion/JJ-1_fuentes_m3.md` §3.2 (B-1);
- en `docs/spec/partes/juanjose.md` §3.1 corrigió la redacción de D4 (M-5) y agregó una nota [PROPUESTO] sobre las columnas de
  `interacciones.parquet` frente a §5.7 (M-1) y las claves extra de la ficha (M-2); M-1 lo decide Juan José y, si lo confirma,
  §5.7 se actualiza por un PR dedicado al núcleo;
- dejó M-6 sin cambiar (menor).

Vuelve a revisar con las mismas reglas (solo lees y ejecutas; no modifiques nada): ¿quedan cerrados B-1, B-2, M-3 y M-4 sin
romper nada de D1–D7, §5.7 o §5.12? Corre `tests/test_datos_m3.py` y `run.py m3-datos --config configs/m3/datos.yaml`, y
comprueba que «piden citar» y `lectura_licencia` ya no están en `configs/`, `src/`, `data/fuentes.md`, `results/` ni
`JJ-1_fuentes_m3.md`. Entrega: veredicto APROBADO o RECHAZADO y los hallazgos que queden.
