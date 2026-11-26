# Registro de la Cacería de la alucinación

Meta: ≥ 5 hallazgos genuinos, ≥ 3 categorías (Matemáticas, Código, Datos del mundo real, Bibliografía, Conceptos),
≥ 1 por módulo (M1, M2, M3) y ≥ 1 por persona. Consolida: Andrés. **Nunca inventar:** un hallazgo sin prompt literal o sin
evidencia no cuenta.

## Cobertura
| Módulo / categoría | Matemáticas | Código | Datos del mundo real | Bibliografía | Conceptos |
|---|---|---|---|---|---|
| M1 | | | | | |
| M2 | | | | | |
| M3 | | | 2 candidatos sin número (JJ-1b) | | |
| Común | | H-01 (candidato) | | | |

## Hallazgos

### H-01 — La marca `\bibliografia` del blog se guardó con un carácter de control
- **Módulo / categoría / quién lo encontró:** Común (blog) / **Código** / Daniel (lo detectó el subagente `redactor-tecnico`
  de DA-9a al citar la primera referencia; lo confirmó Daniel con los bytes del commit).
- **1. Prompt literal:** `alucinaciones/prompts/DA-1b.md` (subagente `implementador`, Sonnet, 24-nov-2026), que pedía portar
  `blog/docs/index.md` del Trabajo 2 con la marca de bibliografía.
- **2. Respuesta relevante de la IA:** el archivo `blog/docs/index.md` del commit `ba19487` contiene los bytes
  `\n\x08ibliografia` (backspace, 0x08) donde debía ir `\bibliografia`, y el agente reportó «`mkdocs build --strict` termina con
  código 0 … No hay WARNING ni ERROR».
- **3. Cómo se sospechó:** en DA-9a, al agregar la primera cita (`[@supertransporte2026]`), el build estricto falló con
  «citas sin marca de bibliografía»; el agente encontró el byte 0x08 al inspeccionar la marca.
- **4. Evidencia:** `alucinaciones/evidencias/H-01_backspace/verificar.py` y `salida.txt`: en `ba19487` la marca es
  `b'\n\x08ibliografia'` (contiene 0x08: True); en el árbol corregido es `b'\\bibliografia'` (0x08: False). El build pasaba
  porque el hook solo exige la marca cuando hay citas, y en DA-1b el blog no tenía ninguna.
- **5. Corrección:** se reescribió la marca como `\bibliografia` (DA-9a) y se agregaron dos pruebas en `tests/test_blog.py`
  (`test_fuentes_del_blog_sin_caracteres_de_control`, `test_la_marca_de_bibliografia_esta_bien_escrita`) que fallan con la
  versión de `ba19487` y pasan con la corregida.
- **6. Lección aprendida:** «el build pasa» no prueba que una marca funcione si el caso que la ejercita no existe todavía.
  Una prueba con una cita de prueba (o que busque caracteres de control) lo habría atrapado en DA-1. Al escribir archivos con
  barras invertidas desde código (`"\b"` en Python es backspace), usar cadenas crudas o verificar los bytes.
- **Estado:** candidato (falta revisión de Andrés como consolidador). Nota: es un error de escritura de código de la IA, no
  una afirmación falsa; Andrés decide si cuenta en la categoría Código.

### H-?? (JJ-1b) — «Las tres licencias del conjunto de Kaggle piden citar la fuente»
- **Módulo / categoría / quién lo encontró:** M3 / **Datos del mundo real** (licencia del conjunto) / lo detectó el
  `revisor-spec` (Sonnet) en la revisión 1 de JJ-1b (bloqueante B-1); lo verificó de forma independiente el
  `cazador-alucinaciones` (Opus) en R3. Dirige: Juan José.
- **1. Prompt literal:** `alucinaciones/prompts/JJ-1a.md` (sesión orquestadora, Opus, fase A: redactar
  `docs/investigacion/JJ-1_fuentes_m3.md` con la licencia «con citas literales») y `alucinaciones/prompts/JJ-1b-implementador.md`
  (implementador, Sonnet, fase B: «licencia con la contradicción (D5)»).
- **2. Respuesta relevante de la IA:** la orquestadora escribió en `JJ-1_fuentes_m3.md` §3.2 (fase A): «Para este trabajo
  académico no comercial las tres permiten el uso, y todas coinciden en pedir que se cite la fuente.» El implementador lo
  copió y lo amplió en la clave `fuente.lectura_licencia` de `configs/m3/datos.yaml` («Para este trabajo académico no
  comercial las tres declaraciones permiten el uso y todas piden citar la fuente»), que el código copiaba a
  `ficha.json` (`licencia.contradiccion`) y a `data/fuentes.md`; en su informe lo describió como «el texto de §3.2»
  (`alucinaciones/evidencias/JJ-1b/respuesta-implementador.md` §4, punto 1). Un posible origen: la respuesta de A2
  (`alucinaciones/evidencias/JJ-1a/respuesta-investigador-fuentes.md`, línea 118) termina con «Pide citar la fuente.», sin
  sujeto explícito.
- **3. Cómo se sospechó:** el `revisor-spec` vio una afirmación normativa que D5 no pedía y que nadie había contrastado
  (A3 solo había verificado que MIT y CC0 permiten el uso comercial): `alucinaciones/evidencias/JJ-1b/respuesta-revisor-spec-1.md`, B-1.
- **4. Evidencia:** (a) fuente del conjunto: `alucinaciones/evidencias/JJ-1b/licencia_citar/verificar.py` → `salida.txt`
  y `alucinaciones/evidencias/JJ-1b/verificar_R3.py` §4 → `verificar_R3_salida.txt`: en la respuesta cruda de Kaggle solo la
  sección «Usage» contiene «cite»; la sección «License» («CC0: Public Domain - … can be used without restrictions.») no
  contiene cite, citation, attribution ni credit. (b) Textos oficiales (fragmentos literales con URL y hora de consulta en
  `alucinaciones/evidencias/JJ-1b/licencias_fragmentos.md`; `verificar_R3.py` §7): el código legal de CC0 no tiene ninguna
  condición de cita ni de atribución (0 apariciones de esas palabras en el texto legal) y su renuncia abarca los «moral
  rights retained by the original author(s)» y «any purpose whatsoever, including without limitation commercial»; la
  escritura (deed) dice «all without asking permission». La única condición de la MIT es «The above copyright notice and this
  permission notice shall be included in all copies or substantial portions of the Software.»: conservar un aviso en las
  copias, no citar la fuente en un trabajo. Conclusión: de las tres declaraciones, solo «Usage» pide citar. **Límite de la
  evidencia:** los archivos de las fases A y B no estaban versionados, así que el texto original solo consta en la nota de
  corrección de `JJ-1_fuentes_m3.md` §3.2, en el informe literal del revisor (B-1) y en `licencia_citar/README.md`.
- **5. Corrección:** `JJ-1_fuentes_m3.md` §3.2 corregido por la orquestadora (con nota de procedencia); `lectura_licencia`
  eliminada del YAML y del código, y fila Licencia de `data/fuentes.md` corregida por el implementador
  (`alucinaciones/prompts/JJ-1b-implementador-2.md`); `licencia.contradiccion` ahora es solo la plantilla del código más las
  citas leídas del JSON, con una prueba que exige que no aparezcan «piden citar» ni «permiten» (`tests/test_datos_m3.py`).
  R3 comprobó que el texto vigente coincide exactamente con esa plantilla.
- **6. Lección aprendida:** una afirmación sobre lo que *exige* una licencia es normativa: se contrasta cláusula por cláusula
  con el texto legal oficial, no con un resumen. Verificar que «las tres permiten el uso comercial» no verifica que «las tres
  piden citar». Un `grep` de cite/attribution en la sección «License» y en el código legal de CC0 lo habría atrapado en la
  fase A. Y lo que una IA escribe en un archivo de configuración se propaga a todas las salidas: mejor que el código solo
  emita citas leídas de la fuente.
- **Estado:** candidato (lo numera y lo decide Andrés).

### H-?? (JJ-1b) — «Las opciones de Preferences y los valores de Type no comparten vocabulario»
- **Módulo / categoría / quién lo encontró:** M3 / **Datos del mundo real** (característica del conjunto; el texto estaba
  fijo en el código) / lo detectó el `revisor-spec` (Sonnet) en la revisión 1 de JJ-1b (bloqueante B-2); el
  `cazador-alucinaciones` (Opus, R3) reprodujo la medición. Dirige: Juan José.
- **1. Prompt literal:** `alucinaciones/prompts/JJ-1b-implementador.md` (implementador, Sonnet), que pedía documentar
  «vocabularios distintos entre las opciones de `Preferences` y los valores de `Type` (diferencia de conjuntos medida)».
- **2. Respuesta relevante de la IA:** en `src/m3_recomendacion/datos.py` (líneas 418-419 de esa versión) el implementador
  escribió como texto fijo la `descripcion` de la inconsistencia `vocabularios_preferencias_vs_type`, que pasaba a
  `results/data/m3/eda/diccionario.json`: «Las opciones de Preferences y los valores de Type **no comparten vocabulario**»
  (cita literal del revisor, `alucinaciones/evidencias/JJ-1b/respuesta-revisor-spec-1.md`, B-2). En su informe el
  implementador confirma que «El campo `descripcion` de cada inconsistencia es texto fijo; `se_presenta` es el que dice si
  la medición la confirma» (`respuesta-implementador.md` §4, punto 2).
- **3. Cómo se sospechó:** el revisor comparó la frase con el bloque `medido` de la misma entrada, que mostraba 4 de 5
  opciones en común.
- **4. Evidencia:** `alucinaciones/evidencias/JJ-1b/verificar_R3.py` §4 → `verificar_R3_salida.txt`, recalculado desde los
  CSV: opciones de `Preferences` = {Adventure, Beaches, City, Historical, Nature}; valores de `Type` = {Adventure, Beach,
  City, Historical, Nature}; en ambos: Adventure, City, Historical y Nature; solo difieren `Beaches` ↔ `Beach`. «No comparten
  vocabulario» es falso. **Límite de la evidencia:** `datos.py` y `diccionario.json` no estaban versionados; el texto
  original solo consta en la cita literal del revisor (la versión de `diccionario.json` con SHA-256 `9856d778…`, que reporta
  `respuesta-implementador.md`, ya no existe).
- **5. Corrección:** la `descripcion` se deriva ahora de lo medido («4 de 5 opciones de Preferences coinciden con valores de
  Type; solo en Preferences: Beaches; solo en Type: Beach. …»), con prueba en las dos formas
  (`alucinaciones/prompts/JJ-1b-implementador-2.md`, `respuesta-implementador-2.md`). R3 comprobó que la frase vigente
  coincide con su medición.
- **6. Lección aprendida:** un texto descriptivo fijo junto a una medición puede contradecirla sin que falle nada. Si la frase
  se deriva de los números (o una prueba compara la frase con `medido`), el error es imposible. La consigna del prompt
  («vocabularios distintos») era correcta; la IA la exageró al pasarla a una frase absoluta.
- **Estado:** candidato menor (lo numera y lo decide Andrés; puede contarse como Datos del mundo real o como Código).

## Plantilla (copiar por hallazgo)
### H-XX — título corto
- **Módulo / categoría / quién lo encontró:**
- **1. Prompt literal:** enlace a `alucinaciones/prompts/<ID>.md`
- **2. Respuesta relevante de la IA:**
- **3. Cómo se sospechó:**
- **4. Evidencia** (derivación, experimento o fuente primaria): enlace a `alucinaciones/evidencias/`
- **5. Corrección:**
- **6. Lección aprendida** (qué verificación lo habría evitado):
- **Estado:** candidato / confirmado / descartado

## Verificaciones que salieron correctas
<!-- El enunciado permite documentarlas si faltan hallazgos. -->

### JJ-1 (M3, datos de Kaggle) — fase A (A3) y fase B (R3), cazador-alucinaciones (Opus), 2026-11-25
- **Fase A (A3):** 63 afirmaciones numeradas de A1 (curador-datos) y A2 (investigador-fuentes), con código propio:
  59 correctas, 3 imprecisas (redondeos o cotas), 1 inferencia no respaldada, 0 incorrectas. 140 comprobaciones automáticas
  (137 iguales; las 3 diferencias son esos redondeos). La salida de A1 se reproduce bit a bit; las respuestas de la API de
  Kaggle re-descargadas son idénticas byte a byte a las guardadas; las 10 citas literales son subcadenas exactas.
  `docs/investigacion/JJ-1_verificacion_A3.md`, `alucinaciones/evidencias/JJ-1a/verificar_A3.py` y `verificar_A3_salida.txt`.
- **Fase B (R3):** 279 comprobaciones automáticas, 279 iguales, con código independiente (no importa `datos.py`):
  SHA-256 y tamaños (contra `ficha.json`, `data/fuentes.md`, la config y los `totalBytes` de Kaggle); zip = CSV sueltos;
  todos los conteos, escalas, densidades (dos denominadores), usuarios por número de interacciones y señales de
  `ficha.json` (incluidos χ² = 3.6946, gl = 8, p = 0.8836 y V = 0.0430, recalculados a mano); tipos, citas e
  inconsistencias de `diccionario.json`; cita, autor, año, versión, título y URL de `mehra2024` contra la metadata; los tres
  parquet (columnas de D1, D2 y D6, sin `Name`, `Email`, `ReviewText` ni `split`; cada interacción es biyectiva con su fila
  cruda por `origen` + `id_origen`; usuarios y destinos reproducen los CSV); y ninguna cadena sensible en
  `data/processed/m3/` ni en `results/data/m3/`. Las afirmaciones vigentes sobre licencias (`data/fuentes.md` y
  `JJ-1_fuentes_m3.md` §3.2) coinciden con los textos oficiales de MIT y CC0. Una imprecisión de nombre, no de fondo:
  «publicación» por «creación de la versión 1» (2024-01-23). No se encontró DOI del conjunto (DataCite, prefijo de Kaggle
  10.34740, y Crossref). `docs/investigacion/JJ-1_verificacion_R3.md`, `alucinaciones/evidencias/JJ-1b/verificar_R3.py`,
  `verificar_R3_salida.txt` y `licencias_fragmentos.md`.
