# Prompts JO-1 — revisiones — 2026-11-27 — orquesta: José

Contexto común (va en los tres prompts): repositorio `/home/jose-miguel-pulgarin/Documents/projects/Trabajo3_Redes_Neuronales`,
rama `dev/jose`, Linux, `.venv/bin/python`. JO-1 quedó en dos commits: `b0c081f` (fase A: `scripts/descargar_m2.py`,
`docs/investigacion/JO-1_inventario.py` y su salida, `docs/investigacion/JO-1_fuentes_m2.md`, entrada M2 de `data/fuentes.md`) y
`3531620` (fase B: `src/m2_conduccion/datos.py`, `configs/m2/datos.yaml`, `tests/test_datos_m2.py`, `tests/fixtures/m2/`,
`data/processed/m2/` con 7 276 imágenes 224×224, `indice.csv`, `origen.csv`, y `results/data/m2/eda/{ficha.json, calidad.csv,
diccionario.json, procesado.json}`). Prompts de los implementadores en `alucinaciones/prompts/JO-1a-*.md` y `JO-1b-*.md`.
Decisiones de José (no se discuten): versionar las 7 276 imágenes procesadas (Anexo, «Repositorio Git reproducible»); 224×224
estirado bilineal, RGB, JPEG 85; excluir y registrar los 10 ilegibles. `grupo_duplicado` y `split` vacíos a propósito (JO-3).
No hagas commit, ni push, ni PR. El zip crudo está en `data/raw/m2/` (no versionado; no lo extraigas a disco).

---

## revisor-spec (Sonnet)
Actúa como `.claude/agents/revisor-spec.md`. Lee `docs/spec/SPEC.md` §0, §3, §4.1, §5.5, §5.6 (preprocesado), §5.12 y §7.1, el
Anexo «Módulo 2 → Datos» y «Entregables → 2. Repositorio Git reproducible», y `docs/spec/partes/jose.md` §3.0, §3.1, fila JO-1
de §4 y §5. Revisa que JO-1 cumpla **exactamente** la spec y su aceptación («`ficha.json`; conteos por clase y resolución
medidos»): contrato de `indice.csv` (§5.5), campos de `ficha.json` (§5.12), parámetros por config, preprocesado coherente con la
app, reproducibilidad (un comando, sin internet tras la descarga, determinismo), y que no se haya hecho de más (casi duplicados,
partición, descriptivo). Lista los supuestos [PROPUESTO] que encuentres para que José decida. Corre `.venv/bin/python -m pytest -q
tests/test_datos_m2.py`. Veredicto: APROBADO / CAMBIOS REQUERIDOS, con hallazgos `archivo:línea` y severidad.

## revisor-calidad (Sonnet)
Actúa como `.claude/agents/revisor-calidad.md`. Revisa la calidad de `scripts/descargar_m2.py`, `docs/investigacion/JO-1_inventario.py`,
`src/m2_conduccion/datos.py`, `tests/test_datos_m2.py` y `tests/fixtures/m2/generar.py`: legibilidad, estructura, pruebas que
prueben comportamiento (no implementación), eficiencia (2,6 GB leídos en streaming), manejo de errores, y que José pueda
explicarlo y modificarlo en vivo en la sustentación. Compara el estilo con `src/m3_recomendacion/datos.py` y
`scripts/descargar_m1.py`. Veredicto: APROBADO / CAMBIOS REQUERIDOS, con hallazgos `archivo:línea`, severidad y arreglo propuesto.
No edites código.

## cazador-alucinaciones (Opus)
Actúa como `.claude/agents/cazador-alucinaciones.md`. Contrasta con las **fuentes primarias** y con **los datos** cada afirmación
de los informes de JO-1: las afirmaciones `[F-n]` de `docs/investigacion/JO-1_fuentes_m2.md` (cotejar las citas textuales con
el artículo, PMC12019831 / DOI 10.1016/j.dib.2025.111529, con la página de Mendeley DOI 10.17632/mzb4b6dff3.1 y con Zenodo
14908802), y las cifras de `JO-1_inventario_salida.txt`, `ficha.json`, `calidad.csv` y `diccionario.json` (recalcula tú, con
código propio en el scratchpad de tu sesión o en `alucinaciones/evidencias/JO-1/`, al menos: conteo por clase, ilegibles,
resoluciones más frecuentes, alfa de los PNG, orientaciones EXIF y las fechas de `conteos.fechas_medidas`). Verifica también:
que cada definición de clase de `diccionario.json` sea cita literal de la fuente; la cita APA 7 y la licencia; y la
afirmación del orquestador en `JO-1b-curador-datos.md` de que el preprocesado es «coherente con el preprocesado fijo de la app»
(contrasta con `app/lib/imagen.ts` y `app/lib/contratos.ts`: ¿estirar + bilineal en ambos? ¿el JPEG 85 intermedio introduce una
diferencia que haya que declarar?). Para cada afirmación: CORRECTA / INCORRECTA / NO VERIFICABLE, con evidencia. Las
discrepancias **fuente vs. datos** (p. ej., «400 × 600», «October 2024» frente a nombres de 2019) son hallazgos de datos, no
alucinaciones; una afirmación **de una IA** del equipo que resulte falsa sí es candidato: regístralo en `alucinaciones/registro.md`
como candidato (sin número), con el prompt de origen y la evidencia en `alucinaciones/evidencias/JO-1/`. Escribe solo en
`alucinaciones/registro.md` y `alucinaciones/evidencias/JO-1/`.
