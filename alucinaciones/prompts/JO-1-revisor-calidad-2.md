# Prompt JO-1 — revisor-calidad, 2.ª vuelta (Sonnet) — 2026-11-27 — orquesta: José

Actúa como `.claude/agents/revisor-calidad.md`. Repositorio `/home/jose-miguel-pulgarin/Documents/projects/Trabajo3_Redes_Neuronales`,
rama `dev/jose`, `.venv/bin/python`. No edites código; no hagas commit.

En la 1.ª vuelta diste CAMBIOS REQUERIDOS con 3 bloqueantes (B1 `main` demasiado largo; B2 `construir_conteos`/`filas_calidad`
densas; B3 `COLUMNAS_CALIDAD` duplicada y prueba vacía) y recomendados (casos borde, pruebas de `descargar_m2.py`, `except`
amplio, `assert` de control, `_diferencia`, `ETIQUETAS_EXIF`, `_a_rgb`, prueba de implementación del zip). Las correcciones están
en el commit `86ca3eb` (prompt del corrector: `alucinaciones/prompts/JO-1c-curador-datos.md`). Revisa con `git show 86ca3eb` y los
archivos `src/m2_conduccion/datos.py`, `scripts/descargar_m2.py`, `tests/test_datos_m2.py`, `tests/test_descargar_m2.py`,
`tests/fixtures/m2/generar.py`. Corre `.venv/bin/python -m pytest -q tests/test_datos_m2.py tests/test_descargar_m2.py`.

Para cada hallazgo de la 1.ª vuelta: RESUELTO / NO RESUELTO / RESUELTO PARCIALMENTE, y cualquier problema **nuevo** que haya
introducido la corrección. Criterio central: que José pueda explicar y modificar `datos.py` en vivo en la sustentación.
Veredicto: APROBADO / CAMBIOS REQUERIDOS (solo bloqueantes reales). Breve.
