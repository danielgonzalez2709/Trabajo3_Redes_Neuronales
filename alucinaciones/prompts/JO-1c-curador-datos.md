# Prompt JO-1c — curador-datos (Sonnet) — 2026-11-27 — orquesta: José

Actúa como el agente definido en `.claude/agents/curador-datos.md`. Repositorio:
`/home/jose-miguel-pulgarin/Documents/projects/Trabajo3_Redes_Neuronales` (rama `dev/jose`, Linux, `.venv/bin/python`). **No hagas
commit, ni push, ni PR.** No toques `requirements.txt`, `run.py`, `src/comun/` ni ningún prompt de `alucinaciones/prompts/`.
**Prueba primero, luego código.**

Es la vuelta de correcciones de JO-1 (commits `b0c081f`, `3531620`, `5316940`). Lee tu propio prompt anterior
`alucinaciones/prompts/JO-1b-curador-datos.md` para el contexto y las mismas lecturas de Spec. Revisiones de las que salen estas
correcciones: revisor-spec (APROBADO con observaciones), revisor-calidad (CAMBIOS REQUERIDOS) y cazador-alucinaciones
(evidencia en `alucinaciones/evidencias/JO-1/`, en especial `experimento_jpeg85_salida.txt`).

## Decisiones de José (27-nov) — márcalas como `[DECIDIDO, José, 27-nov]` donde hoy dicen [PROPUESTO]
1. **JPEG calidad 85 se mantiene**, y se **declara** la diferencia con la app: la app redimensiona la foto original sin
   recompresión; el entrenamiento usa la imagen recomprimida (medido por el cazador en 292 imágenes: diferencia media 2,74 niveles
   de 255, p99 14, máx. 90; 55,7 % de los valores fuera de ±1). Agrégalo como fila en `calidad.csv` y como entrada en `ficha.json`
   (`conteos.diferencias_con_app`), citando el archivo de evidencia. No re-midas: copia esas cifras con su referencia.
2. **`ancho`/`alto` de `indice.csv` = dimensiones originales tras EXIF** (se conservan los nombres del contrato §5.5). Documenta
   su significado en el docstring del módulo y en `diccionario.json` (sección de columnas del índice).
3. **`aplicar_orientacion_exif: true`.**
4. **`origen.csv` y `procesado.json` se conservan.**
5. **Ids `m2_NNNNN` (huecos para los ilegibles) y `n_variables = 2`.**

## Correcciones de calidad (revisor-calidad)
- **B1** `src/m2_conduccion/datos.py` `main` (~63 líneas): partir en `_procesar_zip`, `_construir_tablas` y `_escribir_salidas`
  (o nombres equivalentes) para que `main` se lea como receta: validar → procesar en memoria → construir → escribir (~15 líneas).
- **B2** dividir `construir_conteos` en subfunciones por sección (`_conteos_exif`, `_conteos_alfa`, `_conteos_formato`, …) y
  `filas_calidad` en `_filas_ilegibles`, `_filas_alfa`, `_filas_declarado`; quitar el parámetro sin uso `miembros`.
- **B3** renombrar la constante `COLUMNAS_CALIDAD` de M2 (choca con la de `src/comun/eda.py`, que tiene otro significado), p. ej.
  `COLUMNAS_HALLAZGOS`; quitar la prueba vacía `assert COLUMNAS_CALIDAD` y los imports sin uso; si las columnas se duplican en la
  prueba como oráculo, dilo con un comentario.
- Quitar `_diferencia` (usar la resta en línea con un comentario «medido − declarado»).
- `ETIQUETAS_EXIF` como dict en lugar del desempaquetado de 4 constantes en una línea; extraer `_a_rgb(img, fondo)` de
  `procesar_imagen`.
- Acotar el `except Exception` de `_leer_exif` a excepciones concretas, o justificarlo en un comentario.
- `scripts/descargar_m2.py`: reemplazar `assert ultimo is not None` por un `raise` explícito; quitar la variable innecesaria; agregar
  `tests/test_descargar_m2.py` sin red (monkeypatch o inyección, como `tests/test_descargar_m1.py`): SHA-256 incorrecto, tamaño
  distinto, API con 0 o con 2 archivos, y archivo ya presente con el SHA correcto (no descarga).
- Comentario en las copias de `sha256_archivo`: «copia deliberada: el script no importa de `src`» (o que el script importe la de
  `datos.py`, lo que sea más simple de explicar).
- Docstring de `docs/investigacion/JO-1_inventario.py`: «solo evidencia de la fase A; no se mantiene». No cambies su lógica ni su
  salida.
- Reemplazar `test_no_extrae_el_zip_a_disco` (prueba de implementación) por una de comportamiento: tras la corrida no aparecen
  archivos nuevos fuera de la carpeta de salida.
- **Casos borde nuevos** (agrega miembros al generador del fixture si hace falta, y regenera el fixture): zip sin ninguna imagen
  legible (debe fallar sin escribir nada); miembro con ruta insegura (`../`, absoluta); un archivo `.png` que en realidad es JPEG
  (rama `extension_distinta_del_formato_real`); valores inválidos de `calidad_jpeg`, `aplicar_orientacion_exif` y `fondo_alfa` en
  `validar_preprocesado`.

## Correcciones de fuentes (cazador-alucinaciones)
En `docs/investigacion/JO-1_fuentes_m2.md`: (a) C-9 cita «Unlike staged datasets» en §1/§4, pero está en la §8 del artículo
(verifícalo en `alucinaciones/evidencias/JO-1/fuentes/pmc.xml`); (b) el rótulo «Value of the Data» no existe como título en el XML
de PMC: cámbialo por el título real de esa sección según el XML; (c) numera las afirmaciones como `[F-n]` para poder citarlas y
actualiza la referencia «F-19» del docstring/ficha si cambia de número. No cambies ninguna cita textual.

## Cierre
- Vuelve a correr `.venv/bin/python run.py m2-datos --config configs/m2/datos.yaml`. **Las imágenes, `indice.csv` y
  `sha256_imagenes` no deben cambiar** (la refactorización no altera la salida); si cambian, detente y explica por qué.
  `ficha.json`, `calidad.csv`, `diccionario.json` y `procesado.json` sí pueden cambiar por lo agregado.
- Suite completa `.venv/bin/python -m pytest -q`. Si regenera figuras ajenas (p. ej. `blog/docs/figures/m3/`), restáuralas con
  `git checkout -- <ruta>`.
- Escribe solo en: `src/m2_conduccion/datos.py`, `configs/m2/datos.yaml`, `scripts/descargar_m2.py`, `tests/test_datos_m2.py`,
  `tests/test_descargar_m2.py`, `tests/fixtures/m2/`, `docs/investigacion/JO-1_inventario.py` (solo el docstring),
  `docs/investigacion/JO-1_fuentes_m2.md`, `data/processed/m2/` y `results/data/m2/eda/`.

## Entrega (breve)
1. Tabla: hallazgo → qué cambiaste (archivo:línea) o por qué no.
2. Pruebas (nuevas y suite completa) y confirmación de que las huellas de imágenes e índice no cambiaron (valores antes/después).
3. Cualquier cosa que no pudiste hacer.
