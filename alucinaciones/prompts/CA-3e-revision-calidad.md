# Prompt CA-3e-revision-calidad — revisor-calidad (2.ª vuelta) — 2026-11-27 — orquesta: Camila

Repo /Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales, rama dev/camila. Segunda vuelta de calidad de CA-3d
tras las correcciones de CA-3e (cambios sin commitear sobre el commit 1a27df7; mira `git diff`). Hallazgos de la 1.ª vuelta:
`alucinaciones/prompts/CA-3d-revision-calidad.md` es el encargo; los hallazgos (1 bloqueante: print de N* con semanas
incompletas; 12 recomendados) y las decisiones de Camila están en `alucinaciones/prompts/CA-3e.md`. Archivos:
`src/m1_demanda/operacion.py`, `configs/m1/operacion.yaml`, `tests/test_operacion_m1.py`, `results/data/m1/operacion/`.

Comprueba que cada hallazgo quedó resuelto (o que la razón para no aplicarlo es válida: la doble llamada a
`capacidad_supuesta` sobre datos distintos) y revisa el código nuevo (variante m por corredor, `reproduccion_variantes`,
`_imprimir_resumen`, pruebas nuevas). Solo lectura: no modifiques archivos del repo ni ejecutes git add/commit/stash/checkout;
si corres el módulo, redirige la salida al scratchpad. Reporta APROBADO / NO APROBADO con hallazgos `archivo:línea` y severidad.
