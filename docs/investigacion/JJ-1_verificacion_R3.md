# JJ-1 fase B — R3: verificación del cazador-alucinaciones

Agente: cazador-alucinaciones (Opus), 2026-11-25, rama `dev/juanjose`; dirige Juan José. Prompt literal:
`alucinaciones/prompts/JJ-1b-cazador-alucinaciones.md`.

**Evidencia.**
- Script propio: `alucinaciones/evidencias/JJ-1b/verificar_R3.py` (SHA-256 `286c5a77…d57c`). **No importa**
  `src/m3_recomendacion/datos.py`: recalcula todo desde los CSV de `data/raw/m3/` (módulo `csv`, `zipfile`, `hashlib`;
  `pyarrow` solo para leer los parquet y `scipy.stats.chi2.sf` solo para el valor p; el χ² se calcula a mano) y desde
  `docs/investigacion/JJ-1_kaggle_metadata.json`.
- Salida: `alucinaciones/evidencias/JJ-1b/verificar_R3_salida.txt` (SHA-256 `5f69e5ab…7c36`; dos corridas, mismo hash).
  Se cita como `§0`…`§7`. **Resumen: 279 comprobaciones, 279 iguales, 0 diferencias.**
- Comando, desde la raíz y sin internet: `.venv\Scripts\python -I alucinaciones/evidencias/JJ-1b/verificar_R3.py <carpeta>`.
  `<carpeta>` contiene los HTML de las licencias, que no se versionan. Sin ese argumento se omite §7.
- Textos oficiales de las licencias: los descargué con `curl -sL` el 2026-11-26 a las 00:36:29–00:36:32 UTC (2026-11-25,
  19:36 hora de Colombia), con HTTP 200 en los tres. Los fragmentos literales, la URL y la hora están en
  `alucinaciones/evidencias/JJ-1b/licencias_fragmentos.md`; §7 comprueba que cada fragmento es subcadena exacta del texto
  descargado.
- DOI del conjunto: lo busqué el 2026-11-26 a las 00:37–00:39 UTC.
  - DataCite, `https://api.datacite.org/dois?query=amanmehra23`: 0 resultados.
  - DataCite con `prefix=10.34740` (el prefijo de Kaggle; el control con solo el prefijo devuelve 71 669 DOI) y
    `query=Mehra`, `travel recommendation` o `titles.title:"Travel Recommendation Dataset"`: 0 resultados cada uno.
    `query=recommendation` devuelve 17 DOI, ninguno de Mehra ni de viajes.
  - Crossref, `query.bibliographic=Travel Recommendation Dataset Mehra Kaggle`: ninguna coincidencia.
  - La metadata guardada no tiene ningún campo `doi`.
- Además corrí `tests/test_datos_m3.py -k sha256` (1 prueba, pasa) y volví a correr
  `alucinaciones/evidencias/JJ-1b/licencia_citar/verificar.py`. Ese script reescribe su `salida.txt`: el texto quedó igual al
  que había y solo cambió la fecha de modificación.
- No modifiqué ningún archivo de JJ-1. Los SHA-256 actuales de las salidas son: `ficha.json` `7919a3f1…`,
  `diccionario.json` `6ae2b0d8…` y los parquet `064bd2db…` (destinos), `c55e0981…` (interacciones) y `8135ee4a…` (usuarios).

## 1. Tabla de verificación

Veredictos: **C** = correcta, **I** = incorrecta, **IM** = imprecisa, **NV** = no verificable, **INR** = inferencia no
respaldada.

### 1.1 `results/data/m3/eda/ficha.json`

| # | Afirmación | Veredicto | Evidencia |
|---|---|---|---|
| 01 | `fuente`: Travel Recommendation Dataset, Aman Mehra, `amanmehra23/travel-recommendation-dataset` | C | `title`, `creatorName` y `ref` de `datasets/view` (§5) |
| 02 | `cita` APA: autor, año 2024, versión 1, título, URL | C | La cadena reconstruida desde `creatorName`, `versions[0].creationDate`, `currentVersionNumber` y `url` es idéntica (§5) |
| 03 | `url` | C | Igual a `url` de `datasets/list?search=` (§5) |
| 04 | `fecha_descarga` 2026-11-25 | C | Fecha de modificación de `archive.zip`: 2026-11-25 18:00 (−05:00). Coincide con el prompt `JJ-1a.md` |
| 05 | `sha256` de los 5 archivos | C | §1: recalculados; iguales en `ficha.json`, en `data/fuentes.md` y en `configs/m3/datos.yaml` |
| 06 | `unidad_de_observacion`: par (usuario, destino) con reseña o visita; la calificación es atributo | C | La unión es disjunta (intersección 0) y no hay pares repetidos (§2). Coincide con D1 |
| 07 | `n_registros` = 1 998 | C | §2 |
| 08 | `n_variables` = 23; `variables_por_archivo` 6/5/5/7 | C | §2: cabeceras de los CSV |
| 09 | `periodo`: VisitDate con 3 valores, función de `HistoryID mod 3`, 666 de 999 posteriores | C | §3 (k mínimo = 3; 666) |
| 10 | `usuarios_maestra` 999, `destinos_maestra` 1 000, `lugares` 5 | C | §2: ids únicos; 5 combinaciones de nombre, estado, tipo y temporada |
| 11 | `interacciones` 999 / 999 / 1 998 | C | §2 (0 pares repetidos por archivo; intersección 0) |
| 12 | `usuarios_que_aparecen` 624 / 642 / 858 | C | §2 |
| 13 | `destinos_que_aparecen` 651 / 638 / 866 | C | §2 |
| 14 | `escala_calificacion` (mínimo, máximo, valores y frecuencias de reseñas, historial y unión) | C | §2 (p. ej. unión 404/427/386/399/382) |
| 15 | `densidad`: 3 orígenes × 2 denominadores (999 000; 406 224 / 409 596 / 743 028) | C | §2: tolerancia 1e-15 |
| 16 | `usuarios_por_numero_de_interacciones` (0, 1, 2, 3, 4, 5+) de los tres orígenes | C | §2, contando con 0 a los maestros que no aparecen |
| 17 | `variables_de_contenido.usuarios` (tipos y número de categorías de las 9 variables) | C | §2 |
| 18 | `variables_de_contenido.destinos`: 5 categorías; `popularidad` de 7.5045 a 9.4998 con 1 000 valores distintos | C | §2: igualdad exacta de los `float` |
| 19 | `citas_literales` (generado, diversidad de género, uso, licencia) | C | §4: cada una es subcadena exacta de `info.description`. «uso» y «licencia» son exactamente las secciones «Usage» y «License»; «generated…» está en «Acknowledgements» y «enriched…» en el componente «Users» |
| 20 | `palabra_synthetic_en_la_fuente` = false | C | §3: «synthetic» no aparece en ninguna respuesta del JSON ni en los nombres de archivo |
| 21 | Señales de destinos: 1 000 ids, 5 lugares × 200; los ids de un lugar comparten los 4 atributos | C | §3 |
| 22 | Señales de reseñas: 3 textos (333 c/u); χ² = 3.6946, gl = 8, p = 0.8836, V = 0.0430 | C | §3: χ² de Pearson calculado a mano sobre la tabla texto × lugar |
| 23 | Señales de VisitDate: valores 2024-01-01, 2024-02-15 y 2024-03-20; 666 posteriores a 2024-01-23 | C | §3 |
| 24 | Rótulo «fecha_publicacion» / «posteriores a la publicación del conjunto (2024-01-23)» (también en `periodo` y en el diccionario) | **IM** | La metadata no da una fecha de *publicación*. Da la de creación de la versión 1 (`versions[0].creationDate` = 2024-01-23T17:07:26.487Z) y la de cada archivo (`datasetFiles[].creationDate`, 17:07:27–28Z, que coincide con la fecha de modificación de los CSV dentro del zip). El fondo es correcto, e incluso más fuerte: 2 de los 3 valores de VisitDate son posteriores a la creación de los propios archivos. Solo sobra el nombre: decir «creación de la versión 1». No es una alucinación: el rótulo viene de D3 |
| 25 | Señales de usuarios: 999 ids, 20 nombres, 999 correos con la forma nombre en minúsculas + dominio, 3 combinaciones | C | §3 (dominio `example.com` en los 999) |
| 26 | Periodicidad con el id (k ≤ 10): nombre 5, ReviewText 3, VisitDate 3, Preferences 3 | C | §3 (k mínimo; además State, Type y BestTimeToVisit tienen k = 5) |
| 27 | `conclusion`: la fuente dice «generated», no usa «synthetic» ni dice con qué método; señales «compatibles con generación por programa» | C | La descripción no describe ningún método (lectura completa de `info.description`). «Compatibles» está redactado como inferencia y corresponde a D4 (decisión de Juan José) |
| 28 | `licencia.campo_formal` = ["MIT"] | C | §4: `info.licenses[].name`; `licenseName` = MIT en `view` y en `list?search` |
| 29 | `licencia.en_la_descripcion` (license, usage) | C | §4: iguales a las secciones |
| 30 | `licencia.contradiccion` | C | §4: idéntica, carácter por carácter, a la plantilla del código más las citas del JSON. «MIT» no aparece en «License» |

### 1.2 `results/data/m3/eda/diccionario.json`

| # | Afirmación | Veredicto | Evidencia |
|---|---|---|---|
| 31 | La fuente documenta 0 columnas en 4 archivos listados | C | §4: `columns` = [] y `description` = "" en los 4 `datasetFiles` |
| 32 | Lista las 23 columnas crudas, cada una con su nombre procesado | C | §4: el conjunto coincide con las cabeceras; los nombres procesados coinciden con las columnas de los parquet (§6) |
| 33 | `tipo` de cada una de las 23 columnas | C | §4: tipo inferido de los valores crudos |
| 34 | `significado` = «no documentado por la fuente» en las 23 | C | Igual que en la fila 31 |
| 35 | `descripcion_del_archivo_en_la_fuente`, con la correspondencia archivo ↔ componente marcada como inferencia | C | §4: las 23 citas son subcadenas exactas |
| 36 | Motivos de exclusión: 20 nombres, 20 correos y 999 con forma; V = 0.043 y p = 0.884; 333 por texto | C | §3–§4 |
| 37 | La descripción menciona «mountain» y ningún `Type` lo contiene | C | §4 |
| 38 | `ids_vs_lugares` (200 por lugar, k = 5) | C | §3–§4 |
| 39 | `visitdate_periodica_y_posterior` | C | §4; el rótulo «publicación» ya está en la fila 24 |
| 40 | `reviewtext_plantilla` (k = 3; V y p iguales a los de la ficha) | C | §4 |
| 41 | `vocabularios_preferencias_vs_type`: «4 de 5 … coinciden; solo Beaches / Beach» | C | §4. Es la versión corregida; la original es el candidato B (§2) |
| 42 | `licencias_contradictorias` | C | §4 |

### 1.3 `data/fuentes.md`, sección «## M3»

| # | Afirmación | Veredicto | Evidencia |
|---|---|---|---|
| 43 | Título, título de la descripción («India Travel Recommender System Dataset»), autor, usuario, ref e id 4345382 | C | §4–§5 |
| 44 | URL | C | §5 |
| 45 | Versión 1 («Initial release»), creada el 2024-01-23T17:07:26.487Z, sin actualizaciones posteriores | C | §5: hay 1 sola versión y `lastUpdated` = `creationDate` (en la consulta del 2026-11-25) |
| 46 | DOI: no hay | C | Búsqueda negativa en DataCite (prefijo de Kaggle) y en Crossref (ver «Evidencia»). Que no exista un DOI no se puede probar del todo; con lo consultado, no hay ninguno |
| 47 | Licencia: citas literales de «MIT», «License» y «Usage» | C | §5 |
| 48 | «Los textos oficiales de MIT y CC0 permiten el uso comercial; “Usage” lo restringe» | C | §7. MIT: «…publish, distribute, sublicense, and/or sell copies of the Software». CC0, escritura: «even for commercial purposes, all without asking permission». CC0, código legal: «(iv) for any purpose whatsoever, including without limitation commercial…» |
| 49 | «Para este trabajo académico no comercial las tres permiten el uso» | C | Se sigue de los fragmentos de la fila 48 y de «free to use for non-commercial purposes» |
| 50 | «Solo la sección “Usage” pide citar la fuente» | C | Igual que en la fila 67 |
| 51 | Fecha de descarga 2026-11-25 | C | Igual que en la fila 04 |
| 52 | «Descargó: Juan José, a mano desde la página de Kaggle con su cuenta …; sin clave de API» | NV | Es una declaración del humano. No tengo cómo comprobarla, pero coincide con `JJ-1a.md` |
| 53 | Cita APA 7 | C | §5 |
| 54 | ¿Real o sintético?: «generated for educational and research purposes»; no usa «synthetic» | C | §3–§5 |
| 55 | Bytes y SHA-256 de los 5 archivos | C | §1. Los bytes también coinciden con los `totalBytes` de Kaggle: los de los CSV vienen de `datasets/list` y los del zip (34 679) de `list?search` |
| 56 | «Los 4 CSV sueltos son idénticos byte a byte a los miembros del .zip» | C | §1 |
| 57 | «Los mismos SHA-256 están en `configs/m3/datos.yaml` (`sha256_esperado`): el comando se detiene si algún archivo no coincide» | C | §1 encuentra los 5 hashes en el YAML. `tests/test_datos_m3.py::test_sha256_distinto_es_error_que_nombra_el_archivo` pasa |
| 58 | Metadatos consultados el 2026-11-25 a las 23:16 UTC, con `columns` vacío | C | §5: el campo `consultado_utc` de las 5 respuestas dice 2026-11-25T23:16; §0 confirma que el cuerpo guardado tiene el SHA-256 declarado |
| 59 | Cómo regenerar: existe `run.py m3-datos`; `Name`, `Email` y `ReviewText` no pasan a ninguna salida | C | `src/comun/cli.py:145`; §6 (ninguna cadena sensible en las salidas) |

### 1.4 `blog/references.bib`, entrada `mehra2024`

| # | Afirmación | Veredicto | Evidencia |
|---|---|---|---|
| 60 | `author` = {Mehra, Aman}, `year` = {2024}, `title` = {Travel recommendation dataset}, `version` = {1}, `publisher` = {Kaggle}, `url`, `urldate` = {2026-11-25}; sin caracteres de control | C | §5, contra `creatorName`, `versions[0].creationDate`, `title`, `currentVersionNumber` y `url`. La regla «BibTeX oficial del DOI y contraste con Crossref» no aplica porque el conjunto no tiene DOI (fila 46): la entrada se contrastó con la metadata oficial de Kaggle |

### 1.5 `data/processed/m3/*.parquet`

| # | Afirmación (D1, D2, D6) | Veredicto | Evidencia |
|---|---|---|---|
| 61 | `interacciones.parquet`: columnas `usuario_id, destino_id, origen, id_origen, calificacion, fecha_visita`; sin `split`; 1 998 filas, 999 por origen | C | §6 |
| 62 | Cada interacción corresponde a una fila cruda por (`origen`, `id_origen`) | C | §6. La relación es biyectiva con las 1 998 filas crudas, y en las 1 998 coinciden usuario, destino, calificación y fecha (nula en las reseñas) |
| 63 | `usuarios.parquet`: 999 filas, sin `Name` ni `Email`; preferencias, indicadores `pref_*`, género, adultos y niños iguales a `Users.csv` | C | §6 (0 filas distintas) |
| 64 | `destinos.parquet`: 1 000 filas; nombre, estado, tipo, temporada, popularidad y `lugar` iguales a `Destinations.csv` | C | §6 (0 filas distintas) |
| 65 | Ningún nombre, correo, texto de reseña ni «example.com» en `data/processed/m3/` ni en `results/data/m3/` | C | §6 (44 cadenas buscadas, 0 apariciones) |

### 1.6 Afirmaciones normativas sobre licencias (`JJ-1_fuentes_m3.md` §3.2 y fila Licencia de `data/fuentes.md`)

| # | Afirmación | Veredicto | Evidencia |
|---|---|---|---|
| 66 | «La sección “License” (CC0) no exige atribución» | C | §7: el código legal de CC0 no usa cite, citation, attribution ni credit (0 apariciones) y renuncia también a los «moral rights retained by the original author(s)», «to the greatest extent permitted». La escritura (deed) dice «all without asking permission». La escritura sí dice «When using or citing the work, you should not imply endorsement…», pero eso no obliga a citar; y aclara que «This Deed itself has no legal value» |
| 67 | «Solo la sección “Usage” pide citar» | C | §4: «Remember to cite the source…» es la única aparición de *cite* en la descripción. En el texto legal de la MIT no aparece cite, citation, attribution ni credit (§7) |
| 68 | «La MIT pide conservar el aviso de copyright y de permiso en las copias, que no es lo mismo que citar» | C | §7: la única condición de la MIT es «The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.». La paráfrasis omite «o partes sustanciales», sin cambiar el sentido. Observación para Juan José, no es un error: `data/processed/m3/` no está en `.gitignore`, así que los parquet derivados se versionarían. Con la lectura MIT correspondería acompañarlos del aviso, pero la fuente no publica ningún aviso concreto (la plantilla es «Copyright <YEAR> <COPYRIGHT HOLDER>»). Es un punto para la sección de ética, no un hallazgo |
| 69 | §3.2: «MIT y CC0 permiten el uso comercial; la sección “Usage” lo restringe» | C | Igual que en la fila 48 |
| 70 | §3.2, tabla: «MIT» en `info.licenses[0].name` y en `licenseName` (de `view` y de `list?search`) | C | §4 |
| 71 | §3.2: «consultas del 2026-11-25 registradas en `indice_licencias.txt`» | C | El índice registra 23:32:53Z y 23:32:54Z, con HTTP 200 |

### 1.7 Recuento

| Veredicto | Afirmaciones vigentes (01–71) | Afirmaciones históricas, ya corregidas (§2) |
|---|---|---|
| Correcta | 69 | — |
| Imprecisa | 1 (fila 24, rótulo «publicación») | 1 (D) |
| No verificable | 1 (fila 52, declaración del humano) | 1 (C) |
| Incorrecta | 0 | 2 (A, B) |
| Inferencia no respaldada | 0 | 0 |

## 2. Candidatos a hallazgo

**A. «Las tres licencias piden citar la fuente».** Registrado como `### H-?? (JJ-1b)` en `alucinaciones/registro.md`
(M3, Datos del mundo real). Veredicto: **incorrecta**, verificado de forma independiente.
- La orquestadora (Opus) lo afirmó en la fase A: «…y todas coinciden en pedir que se cite la fuente» (prompt `JJ-1a.md`).
- El implementador (Sonnet) lo copió y lo amplió: «…y todas piden citar la fuente» (prompt `JJ-1b-implementador.md`; ver
  `respuesta-implementador.md` §4.1).
- Evidencia: solo «Usage» contiene *cite* (§4 y `licencia_citar/salida.txt`). El código legal de CC0 no pone ninguna
  condición de atribución y la única condición de la MIT es conservar el aviso en las copias (§7 y `licencias_fragmentos.md`).
- Límite: los archivos originales no estaban versionados. El texto original solo consta en la nota de corrección de §3.2, en
  el informe literal del revisor (B-1) y en `licencia_citar/README.md`.
- Posible semilla: A2 terminó su respuesta con «Pide citar la fuente.», sin sujeto (`respuesta-investigador-fuentes.md:118`).

**B. «Las opciones de Preferences y los valores de Type no comparten vocabulario».** Registrado como `### H-?? (JJ-1b)`
(M3, Datos del mundo real, o Código). Veredicto: **incorrecta**; es un candidato menor.
- El implementador (Sonnet) escribió como texto fijo, en `datos.py`, una frase que contradecía su propia medición (bloqueante
  B-2 del revisor).
- Lo reproduje desde los CSV (§4): 4 de 5 opciones coinciden y solo difieren `Beaches` ↔ `Beach`.
- Límite: el texto original solo consta en la cita literal del revisor (`respuesta-revisor-spec-1.md`, B-2), porque el
  `diccionario.json` original (SHA-256 `9856d778…`) ya no existe. Lo dejo para que Andrés decida si cuenta.

**C. Carácter de retroceso (`\x08`) en una regex de `datos.py` (`respuesta-implementador.md` §4, punto 7). No lo registro:
no hay evidencia reproducible.**
- `datos.py` no está versionado y no queda ninguna copia de la versión defectuosa.
- `grep -P "\x08"` no lo encuentra en ningún archivo de texto de M3.
- El único `.pyc` (`src/m3_recomendacion/__pycache__/datos.cpython-312.pyc`) está compilado desde la fuente actual: su
  cabecera trae la misma fecha de modificación (2026-11-26 00:29:56 UTC) y el mismo tamaño (41 931 bytes). Ninguna de sus
  constantes de texto contiene 0x08.
- La regex actual (`rf"\b{re.escape(f)}\b"`, línea 492) está bien escrita.
- Lo único que hay es el autoinforme del implementador. Si aparece una copia de la versión anterior, por ejemplo en un
  registro de sesión, habría que reabrirlo; sería del mismo tipo que H-01.

**D. «La falsa afirmación nació en mi propio texto de `lectura_licencia`» (`respuesta-implementador-2.md`): imprecisa.**
- La frase ya estaba en `JJ-1_fuentes_m3.md` §3.2 (fase A), como anotó la orquestadora en ese mismo archivo.
- Es una atribución equivocada sobre el propio proceso, no una afirmación sobre datos, normas ni código. No la registro; la
  menciono porque explica la procedencia de A.

**No registrados por instrucción:** el candidato débil de A1 sobre «independencia» (D7).

## 3. Cobertura de la cacería (registro, 2026-11-25)

- Confirmados: 0 de la meta de 5 o más.
- Candidatos:
  - H-01: Común, Código (Daniel).
  - Dos `H-?? (JJ-1b)`: M3, Datos del mundo real (Juan José).
- Categorías con candidato: 2 de 5 (Código y Datos del mundo real). Faltan Matemáticas, Bibliografía y Conceptos para llegar
  a 3 o más.
- Módulos con candidato: M3 y Común. Faltan M1 y M2.
- Puntos calientes pendientes en M3 (spec §5): NDCG y Recall@K, el signo de BPR, «BCE ≡ BPR», la popularidad con fuga y las
  referencias de NCF, BPR y Adam (JJ-3 a JJ-5 y JJ-9).
