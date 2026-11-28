# Prompt JO-1b — curador-datos (Sonnet) — 2026-11-27 — orquesta: José

Actúa como el agente definido en `.claude/agents/curador-datos.md` (léelo primero). Repositorio:
`/home/jose-miguel-pulgarin/Documents/projects/Trabajo3_Redes_Neuronales` (rama `dev/jose`, Linux). **No hagas commit, ni push,
ni PR.** No cambies `requirements.txt`, `run.py` ni nada de `src/comun/` (archivos compartidos). Usa `.venv/bin/python`.
**Prueba primero, luego código.**

Lee antes: `docs/spec/SPEC.md` §0, §3, §4.1, §5.5, §5.6 (solo el párrafo del preprocesado), §5.12 y §7.1, y del Anexo de ese
archivo «Módulo 2 → Datos» y «Entregables → 2. Repositorio Git reproducible»; `docs/spec/partes/jose.md` §3.0 (preprocesado),
§3.1, la fila JO-1 de §4 y §5. Insumos de la fase A (léelos completos): `docs/investigacion/JO-1_inventario_salida.txt`,
`docs/investigacion/JO-1_fuentes_m2.md`, `scripts/descargar_m2.py`, la entrada M2 de `data/fuentes.md`. Como referencia de estilo
(no de contenido): `src/m3_recomendacion/datos.py` (`main`, lectura de config), `configs/m3/datos.yaml`, `tests/test_datos_m3.py`,
`src/comun/eda.py` (`escribir_ficha`, `validar_ficha`, `tabla_calidad`) y `src/comun/cli.py` (el subcomando `m2-datos` ya está
registrado y llama a `src.m2_conduccion.datos:main`). Nada de otras partes.

## Decisiones de José (no las cambies)
- **Se versionan las 7 276 imágenes legibles** procesadas (el enunciado exige los datos procesados en el repositorio).
- Resolución **224×224**, redimensionado **estirando** (sin conservar proporción) con interpolación **bilineal** de PIL, RGB, JPEG
  calidad 85 — coherente con el preprocesado fijo de la app (spec de José §3.0). Todo en `configs/m2/datos.yaml`, nada fijo en el
  código.
- Los 10 archivos ilegibles se **excluyen y se registran** (no se reparan).
- Nombres de clase = nombres exactos de las carpetas (`other_activities`, `safe_driving`, `talking_phone`, `texting_phone`,
  `turning`).

## Supuestos [PROPUESTO] que debes implementar como parámetros de config y reportar con sus conteos medidos
- `aplicar_orientacion_exif: true` (aplicar `ImageOps.exif_transpose` antes de redimensionar). Reporta cuántas imágenes cambian
  (Orientation 6 y 8) y guarda en la salida 2 ejemplos (id) de cada caso para que José los mire.
- PNG RGBA → RGB: **antes** de decidir, mide en los 200 PNG si el canal alfa es completamente opaco (todos 255). Si lo es en todos,
  `convert("RGB")` no pierde información; si no, reporta cuántos y con qué fracción de píxeles no opacos, usa composición sobre
  fondo blanco (parámetro `fondo_alfa: [255, 255, 255]`) y dilo.

## Tarea
1. **Pruebas** `tests/test_datos_m2.py` con fixtures pequeños **generados por código** en `tests/fixtures/m2/` (un .zip mínimo con
   la misma estructura de carpetas: unas pocas imágenes JPEG y PNG RGBA de tamaños distintos, una con EXIF Orientation 6 y un
   archivo ilegible con sus primeros bytes en cero), que corran sin `data/raw/` y sin internet. Cubren: salida 224×224 RGB JPEG;
   exclusión y registro del ilegible; orientación EXIF aplicada; columnas de `indice.csv`; ids únicos y estables; dos corridas
   producen archivos idénticos byte a byte (determinismo); `ficha.json` válida con `validar_ficha`; parámetros leídos de la
   config. Más una prueba que, **si existen** los procesados reales versionados, verifica que `indice.csv` tiene 7 276 filas, que
   cada archivo listado existe y que su huella coincide con la registrada (se salta con `pytest.skip` solo si no existen).
2. **Código** `src/m2_conduccion/datos.py` con `main(...)` (misma firma/estilo que `m3-datos`): lee el .zip de `data/raw/m2/`
   **sin extraerlo a disco**, verifica su SHA-256 contra la config, procesa en orden determinista y escribe:
   - `data/processed/m2/imagenes/<clase>/<id>.jpg`.
   - `data/processed/m2/indice.csv` con las columnas de §5.5: `id, archivo, clase, grupo_duplicado, split, ancho, alto`.
     `grupo_duplicado` y `split` quedan **vacías** (las llena JO-3). `ancho`/`alto` = dimensiones **originales** (tras la
     orientación EXIF) [PROPUESTO; dilo]. `tipo_vehiculo` **no** se incluye porque la fuente no lo etiqueta (F-19 de
     `JO-1_fuentes_m2.md`); déjalo dicho en el docstring y en el reporte. `archivo` relativo a `data/processed/m2/`.
   - `data/processed/m2/origen.csv`: `id, archivo_original` (ruta dentro del .zip), `sha256_original, formato, modo,
     orientacion_exif` (para trazabilidad y para JO-3).
   - `results/data/m2/eda/ficha.json` (con `escribir_ficha`): `fuente`, `cita` (APA 7 del conjunto, copiada de
     `JO-1_fuentes_m2.md` §1), `url` (DOI), `fecha_descarga` (la de `data/fuentes.md`), `sha256` (del .zip),
     `unidad_de_observacion`, `n_registros` (imágenes legibles), `n_variables` (justifica el valor en el reporte), `periodo` (lo
     que dice la fuente, rotulado «según el artículo», con su cita; no hay fecha por imagen) y `conteos`: total en el .zip,
     ilegibles, legibles, por clase (antes y después de excluir), resoluciones originales más frecuentes, formatos, modos, EXIF
     con orientación aplicada, y los conteos **declarados** por los autores al lado de los medidos (con la diferencia).
   - `results/data/m2/eda/calidad.csv` (o `.json`): ilegibles con su error, PNG con alfa, orientaciones aplicadas, discrepancias
     declarado vs. medido (p. ej., resolución «400 × 600» frente a la medida).
   - `results/data/m2/eda/diccionario.json`: por clase, la definición de los autores **citada textualmente** desde
     `JO-1_fuentes_m2.md` (con fuente y sección); si artículo y Mendeley difieren, ambas. Nada de definiciones propias.
   - Una huella: SHA-256 de `indice.csv` y un SHA-256 global de las imágenes procesadas (en orden de `id`), en
     `results/data/m2/eda/procesado.json` junto con la config usada y las versiones de Python y Pillow.
3. `configs/m2/datos.yaml` con todos los parámetros (rutas, SHA-256 esperado, tamaño, interpolación, calidad, supuestos).
4. Completa en `data/fuentes.md` (solo la entrada M2) la licencia, los autores y la cita, copiados de `JO-1_fuentes_m2.md`.
5. Ejecuta `.venv/bin/python run.py m2-datos --config configs/m2/datos.yaml` sobre los datos reales y luego la suite completa
   `.venv/bin/python -m pytest -q`. Reporta el tamaño total en MB de `data/processed/m2/` y el tiempo de la corrida.

## Reglas
- **Prohibido inventar**: conteos, definiciones de clase, cita, licencia o periodo. Todo número sale del código ejecutado; todo
  texto de la fuente, de `JO-1_fuentes_m2.md` con su cita. Si falta algo: `TODO(dato-faltante)`.
- No hagas casi duplicados, partición, aumentos ni análisis descriptivo (son JO-2/JO-3).
- Escribe solo en: `src/m2_conduccion/datos.py`, `configs/m2/datos.yaml`, `tests/test_datos_m2.py`, `tests/fixtures/m2/`,
  `data/processed/m2/`, `results/data/m2/eda/` y la entrada M2 de `data/fuentes.md`. Sin internet.

## Entrega (tu mensaje final, breve)
1. Archivos creados y comando para regenerar todo.
2. Resultado de las pruebas (las nuevas y la suite completa) y tamaño/tiempo de la corrida.
3. Afirmaciones `[B-n] afirmación — valor — archivo` con: legibles por clase, ilegibles, orientaciones aplicadas, resultado del
   alfa de los PNG, huellas, `n_variables` y su justificación.
4. Supuestos [PROPUESTO] que quedaron en la config y `TODO(dato-faltante)`.
