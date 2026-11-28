# Prompt JJ-1b (B1–B7) — implementador (Sonnet) — 2026-11-25 — orquesta: Juan José

Actúa como el agente definido en `.claude/agents/implementador.md` (léelo primero). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales` (rama `dev/juanjose`). **No hagas commit, ni push, ni PR.** Usa siempre
`.venv\Scripts\python` (Python 3.12, Windows); no instales nada ni cambies `requirements.txt`. **Prueba primero, luego código.**
Sin internet en `src/` (lo vigila `tests/test_no_network.py`).

Lee antes:
- `docs/spec/SPEC.md` §0, §3, §4.1, §5.7, §5.8 (solo para saber que las preferencias alimentan la app), §5.12 y §8, y del Anexo
  «Módulo 3 → Datos».
- `docs/spec/partes/juanjose.md` §3.1 completo: **las decisiones D1–D7 [DECIDIDO, Juan José, 25-nov] son la especificación**.
- `docs/investigacion/JJ-1_fuentes_m3.md` (inventario y fuente; todas las cifras de referencia) y
  `docs/investigacion/JJ-1_kaggle_metadata.json` (respuestas crudas de la API de Kaggle; es la única fuente de las citas).
- Para el estilo: `configs/m1/datos.yaml`, `src/m1_demanda/datos.py` (`main`, `sha256`, `_escribir_parquet`),
  `tests/test_datos_m1.py`, `src/comun/eda.py` (`escribir_ficha`, `validar_ficha`, `tabla_calidad`), `src/comun/results.py`
  (`save_json`), `results/data/m1/eda/calidad.csv` (formato con `tabla, filas, duplicados_clave` + columnas de
  `tabla_calidad`), la sección «## M1» de `data/fuentes.md` y las entradas `@dataset` de `blog/references.bib`.
Nada de otras partes.

## Archivos que puedes crear o modificar (solo estos)
`tests/test_datos_m3.py`, `tests/fixtures/m3/*`, `configs/m3/datos.yaml`, `src/m3_recomendacion/datos.py`,
`src/m3_recomendacion/README.md`, `data/fuentes.md` (solo agregar la sección M3), `blog/references.bib` (solo agregar la
entrada M3), las salidas que genera el comando (`data/processed/m3/`, `results/data/m3/eda/`) y lo de B7. No toques
`src/comun/`, `run.py`, `requirements.txt`, el README raíz, `SPEC.md`, `PLAN.md`, `MEMORIA.md`, `alucinaciones/registro.md` ni
pruebas de otros.

## Diseño (decidido por el orquestador; no lo cambies sin escalar)

### B2. `configs/m3/datos.yaml` (comentado como `configs/m1/datos.yaml`; sin semillas: no hay azar)
- `entrada`: `carpeta: data/raw/m3`; nombres de los 4 CSV y del zip; `metadatos_fuente:
  docs/investigacion/JJ-1_kaggle_metadata.json`.
- `sha256_esperado`: un SHA-256 por archivo, **copiados de la tabla de §1 de `JJ-1_fuentes_m3.md`** (los 4 CSV y `archive.zip`).
- `fuente`: `nombre`, `autor` («Aman Mehra»), `usuario_kaggle`, `ref`, `url`, `version` (1), `fecha_creacion_version`,
  `fecha_descarga: "2026-11-25"`, `descargo` (Juan José, a mano con su cuenta de Kaggle), y la `cita` APA 7 de §1 de
  `JJ-1_fuentes_m3.md` en texto plano: `Mehra, A. (2024). Travel recommendation dataset (Versión 1) [Conjunto de datos].
  Kaggle. https://www.kaggle.com/datasets/amanmehra23/travel-recommendation-dataset`.
- `citas_literales`: los fragmentos de la descripción que usa la ficha y el diccionario (D4: «generated for educational and
  research purposes», «enriched with gender diversity»; las descripciones de cada componente; las secciones «Usage» y
  «License»), copiados de `JJ-1_kaggle_metadata.json`. **El código comprueba que cada fragmento es subcadena exacta de la
  descripción leída del JSON y falla con error claro si no lo es** (así ninguna cita puede inventarse).
- `componentes`: archivo → fragmento literal del componente de la descripción (Destinations, Users, Reviews, User History),
  con un comentario: la correspondencia archivo ↔ componente es inferencia nuestra, la fuente no nombra los archivos.
- `conclusion_real_o_sintetico`: el texto de la conclusión de D4.
- `salida`: `carpeta: data/processed/m3`, nombres de los 3 parquet, `eda: results/data/m3/eda`.

### B3. `src/m3_recomendacion/datos.py` con `main(cfg) -> int` (lo llama `run.py m3-datos`)
1. **SHA-256**: si falta un archivo o un SHA-256 no coincide con la config → `FileNotFoundError` / `ValueError` con el
   archivo, el esperado y el obtenido. Nada se escribe si falla.
2. **destinos.parquet** (orden por `destino_id`): `destino_id` (int, de `DestinationID`), `nombre` (`Name`), `lugar`,
   `estado` (`State`), `tipo` (`Type`), `mejor_epoca` (`BestTimeToVisit`, texto tal cual), `popularidad` (`Popularity`).
   `lugar` = clave en minúsculas con guiones bajos derivada del nombre (p. ej. «Taj Mahal» → `taj_mahal`). Antes de crearla,
   el código comprueba que cada `nombre` tiene una sola combinación (estado, tipo, mejor_epoca); si no, `ValueError`.
3. **usuarios.parquet** (orden por `usuario_id`): `usuario_id`, `preferencias` (opciones separadas por coma, sin espacios
   sobrantes, **ordenadas alfabéticamente** y unidas con «, »), una columna booleana `pref_<opcion>` por cada opción **medida
   en los datos** (no fija en el código; `<opcion>` en minúsculas, p. ej. `pref_beaches`), `genero` (`Gender`, valores tal
   cual la fuente), `n_adultos` (`NumberOfAdults`), `n_ninos` (`NumberOfChildren`). **Sin `Name` ni `Email`** (D6).
4. **interacciones.parquet** (orden por `usuario_id, destino_id`; D1): `usuario_id`, `destino_id`, `origen` ∈ {`resena`,
   `historial`}, `id_origen` (`ReviewID` o `HistoryID`), `calificacion` (`Rating` o `ExperienceRating`, entero 1–5 tal cual),
   `fecha_visita` (fecha de `VisitDate` en `historial`, nula en `resena`; solo descriptiva). **Sin `ReviewText`** (D6). **No
   crees `split`** (es de JJ-3). Reglas: todo `usuario_id`/`destino_id` debe existir en las tablas maestras (si no,
   `ValueError` con los ids); si un par (usuario, destino) aparece más de una vez, dentro de un archivo o entre los dos, →
   `ValueError` con los pares (la fase A midió 0; no se fusiona en silencio).
5. **results/data/m3/eda/ficha.json** con `src.comun.eda.escribir_ficha`:
   - claves de §5.12: `fuente`, `cita`, `url`, `fecha_descarga`, `sha256` (dict archivo → hash, los 5 archivos),
     `unidad_de_observacion` (par usuario–destino con interacción implícita: reseña o visita), `n_registros` (= interacciones
     de la unión), `n_variables` (= columnas de los 4 CSV crudos, con su desglose por archivo en `conteos`), `periodo` (texto:
     no hay fechas reales; `VisitDate` solo en UserHistory, sus valores distintos y que es posterior a la publicación; D3).
   - `conteos`: usuarios (maestra), destinos (maestra), lugares, interacciones por origen y de la unión, usuarios y destinos
     que aparecen (por origen y unión), escala medida de cada calificación (mín, máx, valores y frecuencias), densidad por
     origen y de la unión con los **dos denominadores** de la fase A (maestras; los que aparecen), usuarios por número de
     interacciones de la unión sobre los 999 maestros (`0, 1, 2, 3, 4, 5+`) y también por origen, variables de contenido de
     usuarios y destinos (nombre procesado y número de categorías; `popularidad` continua).
   - Claves adicionales de primer nivel (no son conteos): `real_o_sintetico` = {`citas_literales` (de la config, ya
     verificadas contra el JSON), `palabra_synthetic_en_la_fuente` (búsqueda sin distinguir mayúsculas en la descripción y
     los nombres de archivo del JSON → booleano), `senales_medidas` (calculadas aquí, no copiadas: ids de destino vs. lugares;
     textos de reseña distintos; valores distintos de `VisitDate` y cuántas filas son posteriores a `fecha_creacion_version`
     de la config — que debe coincidir con `versions[0].creationDate` del JSON —; nombres de usuario distintos vs. ids, sin
     listar los nombres; filas cuyo correo es nombre en minúsculas + dominio, sin listar correos; combinaciones de
     preferencias; el menor k ≤ 10 tal que la columna es función exacta de `id mod k`, para nombre de destino, `ReviewText`,
     `VisitDate` y `Preferences`), `conclusion` (de la config)}; y `licencia` = {`campo_formal` (leído de
     `info.licenses[].name` del JSON), `en_la_descripcion` (los fragmentos literales de «License» y «Usage»), `contradiccion`
     (texto breve)}.
   - Cero nombres o correos de usuarios y cero textos de reseña en cualquier salida.
6. **results/data/m3/eda/calidad.csv**: por cada tabla **procesada** (`destinos`, `usuarios`, `interacciones`), las columnas
   `tabla, filas, duplicados_clave` + las de `src.comun.eda.tabla_calidad` (mismo formato que el de M1). Clave: `destino_id`,
   `usuario_id`, `(usuario_id, destino_id)`.
7. **results/data/m3/eda/diccionario.json**: `fuente_del_diccionario` (qué campo del JSON se revisó y que la fuente no documenta
   columnas: `datasetFiles[].columns` vacío), y por cada columna de los 4 CSV: `archivo`, `columna_original`,
   `nombre_procesado` (o `null` si se excluye), `tipo` (medido), `significado` = «no documentado por la fuente» (ninguna está
   documentada), `descripcion_del_archivo_en_la_fuente` (fragmento literal del componente; con la nota de que la
   correspondencia es inferencia), `excluida_motivo` cuando aplique (D6: privacidad para `Name`/`Email`; `ReviewText`: 3
   textos sin relación con el destino, con sus conteos medidos). Más `inconsistencias`, **cada una calculada por el código**:
   la descripción menciona «mountain» y ningún `Type` lo contiene; 1 000 ids = 5 lugares (200 c/u); `VisitDate` con 3 valores
   función de `HistoryID mod 3` y posteriores a la publicación; `ReviewText` con 3 textos sin relación con el destino;
   vocabularios distintos entre las opciones de `Preferences` y los valores de `Type` (diferencia de conjuntos medida);
   licencias contradictorias (del JSON).
8. Imprime un resumen corto (filas por tabla, interacciones por origen, densidad de la unión, archivos escritos) y devuelve 0.
   Debe tardar < 10 s. Escritura atómica como en M1; salidas **deterministas** (mismo orden de filas y columnas, sin fechas de
   ejecución ni rutas absolutas en los JSON).

### B1. Pruebas primero: `tests/test_datos_m3.py` + `tests/fixtures/m3/`
Fixtures **pequeños y claramente ficticios**, con las **mismas columnas y orden** que los 4 CSV reales (nombres como «Lugar
Ficticio Uno», «Estado Ficticio», «Usuario Prueba A», correos `@prueba.invalid`, reseñas «Texto de prueba 1»…) y un
`kaggle_metadata_prueba.json` mínimo, ficticio, con la misma estructura que usa el código. Construye el fixture para que
cubra: un usuario sin interacciones, pares solo en reseñas y solo en historial, un destino repetido con otro id (mismo lugar),
preferencias «Beaches, Historical». Los SHA-256 de la config de prueba se calculan en la prueba. Pruebas mínimas (una función
por idea, nombres que se lean como frase):
- unión sin pares repetidos y sin pares perdidos (n = |reseñas| + |historial|, todos presentes); par repetido → `ValueError`;
- todo usuario/destino de las interacciones existe en las maestras; id huérfano → `ValueError`;
- `Name`, `Email` y `ReviewText` ausentes de todas las salidas (columnas y valores; también en los JSON y el CSV);
- escala y densidad contra un **conteo a mano escrito en la prueba** (con los dos denominadores) y usuarios por número de
  interacciones;
- «Beaches, Historical» → `pref_beaches` y `pref_historical` verdaderas y las demás falsas; `preferencias` normalizada;
- `lugar` agrupa los ids del mismo nombre; nombre con dos combinaciones → `ValueError`;
- `ficha.json` pasa `src.comun.eda.validar_ficha` y trae los bloques `conteos`, `real_o_sintetico` y `licencia`;
- cita de la config que no es subcadena de la descripción → `ValueError`;
- archivo faltante → error claro; SHA-256 distinto → `ValueError` que nombra el archivo;
- determinismo: dos corridas → mismos bytes en todas las salidas;
- `main` no usa la red (bloquea `socket` como en `tests/test_datos_m1.py`).
Corre las pruebas y confirma que **fallan** antes de escribir `datos.py`; luego impleméntalo hasta que pasen.

### B4. `data/fuentes.md`: agrega al final `## M3 — Recomendación de destinos` con el formato de la sección M1: conjunto,
URL, licencia con la contradicción (D5), fecha de descarga 2026-11-25, descargó Juan José a mano con su cuenta de Kaggle (botón
Download → `archive.zip`), tabla de archivos con tamaño y SHA-256 (de `JJ-1_fuentes_m3.md` §1), metadatos consultados
(`docs/investigacion/JJ-1_kaggle_metadata.json`, 2026-11-25 23:16 UTC) y cómo regenerar (descargar el .zip a `data/raw/m3/`,
descomprimirlo ahí y correr `.venv\Scripts\python run.py m3-datos --config configs/m3/datos.yaml`). No toques la sección M1.

### B5. `blog/references.bib`: agrega una entrada `@dataset{mehra2024, …}` en el estilo de las de M1 (comentario de
procedencia: fase A de JJ-1, consulta del 25-nov-2026; sin DOI). Campos: `author = {Mehra, Aman}`, `year = {2024}`,
`title = {Travel recommendation dataset}`, `version = {1}`, `type = {Conjunto de datos}`, `publisher = {Kaggle}`,
`url`, `urldate = {2026-11-25}`. Todo de `JJ-1_kaggle_metadata.json`.

### B6. `src/m3_recomendacion/README.md`: actualiza las líneas de configs, datos y el comando de `m3-datos` (deja «pendiente»
en lo que siga pendiente).

### B7. En `alucinaciones/evidencias/JJ-1a/redescarga_A3/` elimina **solo** `licencia_mit.html` y `licencia_cc0.html`
(textos completos de licencias; no se versionan). Conserva lo demás. Ajusta las referencias: en `indice_licencias.txt` agrega
una línea que diga que los textos completos no se versionan y se consultan en las URL indicadas; en
`docs/investigacion/JJ-1_verificacion_A3.md` (línea ~16) y en `docs/investigacion/JJ-1_fuentes_m3.md` §3.2, cambia la mención a
los archivos por las URL oficiales (https://opensource.org/license/mit y https://creativecommons.org/publicdomain/zero/1.0/)
más `indice_licencias.txt`. **No edites** `alucinaciones/evidencias/JJ-1a/respuesta-*.md` (son respuestas literales).

## Cierre
- Corre `.venv\Scripts\python run.py m3-datos --config configs/m3/datos.yaml` dos veces y confirma con SHA-256 que las 6
  salidas no cambian.
- Corre `.venv\Scripts\python -m pytest -q -m "not lento"` (todas, también las de los demás) y deja todo en verde.
- Prohibido inventar: toda cifra de las salidas la calcula el código desde los CSV o el JSON; toda cita es subcadena verificada.

## Entrega (tu mensaje final)
1. Archivos creados/modificados/eliminados.
2. Salida real de las pruebas en rojo (antes de `datos.py`) y en verde (después), y de las dos corridas del comando con los
   SHA-256 de las salidas.
3. Cifras clave de `ficha.json` (usuarios, destinos, lugares, interacciones por origen y unión, escalas, densidades, usuarios
   por número de interacciones).
4. Cualquier cosa que no pudiste cumplir o que contradiga el diseño, y lo que debe decidir Juan José.
