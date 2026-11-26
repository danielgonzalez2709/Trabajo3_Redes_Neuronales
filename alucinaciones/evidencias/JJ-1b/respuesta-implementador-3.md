# Respuesta literal del implementador (Sonnet), correcciones de R2 — JJ-1b — 2026-11-25

Prompt: `alucinaciones/prompts/JJ-1b-implementador-3.md`. Copiado sin cambios del informe final del subagente.

---

Las correcciones de R2 están hechas: B1–B5 y los recomendados que pedías (R1, R2, R4, R5, R6, R7, R8 solo en `inconsistencias`, R9, R11, R12, O2, O6, O7, O9). No hice R3, R10, O1, O3, O4, O5, O8 ni O10, y no toqué `src/comun/`. Sin commit ni push. Ninguna cifra cambió; sí cambió el texto de algunas salidas y hay una clave nueva en la ficha.

## Pruebas
- **Rojo primero:** con las pruebas nuevas y las actualizadas, 9 fallaron antes de tocar `datos.py` (43 pasaban).
- **`tests/test_datos_m3.py`:** 52 pasadas.
- **Suite completa:** `pytest -q -m "not lento"` da 381 pasadas.
- **Salidas:** `run.py m3-datos --config configs/m3/datos.yaml` corrió dos veces con código 0 y SHA-256 iguales entre corridas.

## Archivos tocados
- `src/m3_recomendacion/datos.py`
- `tests/test_datos_m3.py`
- `configs/m3/datos.yaml` (solo el comentario de la cabecera, O2: ahora dice «D1–D6 (D7 es de proceso)»)
- Salidas regeneradas: `ficha.json` y `diccionario.json`

## Qué hice con cada id
- **B1.** Borré `COLUMNAS_USUARIOS_FIJAS` y `COLUMNAS_USUARIOS_FINALES`.
- **B2.** Quité `usuarios` y `destinos` de `construir_diccionario`. Su firma queda `(cfg, raw, opciones, meta, sen, asoc, incons)`.
- **B3.** `_inc_licencias` usa `formal_en_license(meta, cfg)`, el mismo cálculo que `licencia.contradiccion`. Ya no hay dos cálculos que puedan divergir.
- **B4.** La prueba nueva pone una marca única en «Usage» (en el JSON y en la config). Exige que la marca aparezca en `licencia.contradiccion` y que el texto completo sea exactamente la plantilla del código más lo leído del JSON. Además comprueba que no aparecen «piden citar» ni «permiten».
- **B5.** Borré la aserción vacía de «no comparten».
- **R1.** `leer_csv` da `no tiene filas de datos` si el CSV solo tiene la cabecera. Hay prueba directa y otra con `main`, que no escribe nada.
- **R2.** Una prueba parametrizada con 7 casos de error cubre `leer_csv` (3 casos), `_enteros`, `verificar_citas` (2 casos) y `verificar_archivos`. Aparte hay una prueba parametrizada de `separar_opciones`.
- **R4.** Una prueba sin red lee `configs/m3/datos.yaml` y `docs/investigacion/JJ-1_kaggle_metadata.json` y llama a `verificar_citas`. También comprueba que `sha256_esperado` tiene los 5 nombres de archivo. Así CI protege la config real. Esa prueba necesita el JSON de metadatos en el repo (hoy sin versionar).
- **R5.** El id pasó a `tipo_buscado_ausente`, y la palabra sale de `ficha.tipo_mencionado_sin_datos`.
- **R6.** `columnas_documentadas_por_la_fuente` se calcula con la nueva `columnas_documentadas(meta)`. Esa función también la usa `verificar_citas`.
- **R7.** Hay una sola función, `clasificar_tipo`, con los nombres `booleano`, `entero`, `decimal`, `texto con forma AAAA-MM-DD` y `texto`. La usan la ficha y el diccionario. Se fue la etiqueta «continua»: `popularidad` ahora es `decimal` en las dos. Una prueba comprueba que ficha y diccionario dan el mismo nombre a la misma columna.
- **R8.** `inconsistencias` solo ensambla seis funciones cortas: `_inc_tipo_buscado`, `_inc_ids_vs_lugares`, `_inc_visit_date`, `_inc_review_text`, `_inc_vocabularios` y `_inc_licencias`.
- **R9.**
  - `periodo` ahora lista las columnas con forma de fecha medidas (hoy `Final_Updated_Expanded_UserHistory.csv (VisitDate)`). «Sin fechas reales» se cambió por «Interpretación (D3): no es un periodo observado; solo descriptiva.».
  - La descripción de licencias dice si el campo formal aparece o no en «License»; ya no afirma que «Usage» dice otra cosa.
  - `ids_vs_lugares` dejó de afirmar que lo único que cambia es `Popularity`. Ahora dice que los ids del mismo lugar comparten nombre, estado, tipo y temporada, lo cual se comprueba al construir destinos.
  - La descripción de `tipo_buscado_ausente` también se arma con lo medido.
- **R11.** Constantes `RESENA` y `HISTORIAL` en lugar de `ORIGENES[0]` y `ORIGENES[1]`.
- **R12.** Los conteos por texto de reseña se calculan una vez, en `senales`. Los usan `inconsistencias` y `construir_diccionario`.
- **O6.** Una columna constante dice «constante» en lugar de «función exacta de … mod 1». Hay prueba con `VisitDate` constante.
- **O7.** Agregué docstrings (qué produce cada función) a `escala`, `clasificar_tipo`, `describir_contenido`, `construir_ficha`, `construir_diccionario` y otras. Tipé los parámetros de `construir_ficha` y `construir_diccionario`.
- **O9.** Los mensajes de error ya no dicen «la fase A». Ahora dan el motivo: las tablas no imputan nada, y los pares repetidos no se fusionan en silencio.

## SHA-256 de las 6 salidas (iguales entre las dos corridas)
```
064bd2dbe130fffaa0595d2183721bce11a3746915da28614689cbedf1dcb6b8  data/processed/m3/destinos.parquet       (sin cambio)
c55e0981ca7b66c06c68972ad5ba025c9855ea9d18b38d040514278aa58e4f52  data/processed/m3/interacciones.parquet  (sin cambio)
8135ee4a7382c05e43cc938a692e998c22ed4f6dc238e7e802992037a0569c7e  data/processed/m3/usuarios.parquet       (sin cambio)
7e217a72ca4f5a647e3834fe46d0870ffac3fe4c7aacba3e416749fff852f328  results/data/m3/eda/calidad.csv         (sin cambio)
6ae2b0d877fb79c524bbbedfe6d38b31e2c566acd1620a2d3a540bda0e28d7a4  results/data/m3/eda/diccionario.json    (antes dde9978f…)
7919a3f1dab7a879110b4acbc840f9ba113a2008a00321edcdc47e81f9263a5e  results/data/m3/eda/ficha.json          (antes 31d4d888…)
```

## Por qué cambiaron los dos JSON
- **Textos:** el `periodo` de la ficha y las descripciones de varias inconsistencias, por R5, R9 y la frase de licencias.
- **Etiquetas de tipo:** los cambios de R7.
- **Dos valores:**
  - `columnas_documentadas_por_la_fuente`, que sigue valiendo 0 pero ahora se calcula.
  - `fuente_del_diccionario`, que ahora dice «documenta 0 columnas (4 archivos listados)».
- **Clave nueva:** `senales_medidas.resenas.conteos_por_texto` en la ficha ([333, 333, 333]). Es por R12, y contiene solo conteos, ningún texto de reseña.
- **Cifras:** revisé a mano y siguen iguales. Interacciones 999/999/1 998, densidad de la unión 0.002, usuarios por número de interacciones de la unión 141/252/280/195/79/52, y V de Cramér = 0.043 con p = 0.884.

## Para ti
`pytest` y `run.py` no pasan por `_inc_review_text` con V de Cramér indefinida (una sola fila o columna) ni por `texto_periodicidad` con `None` en todas las ramas. Son ramas simples y R3 las incluía entre las que quedan sin prueba, así que no las toqué.
