# Registro de la Cacería de la alucinación

Meta: ≥ 5 hallazgos genuinos, ≥ 3 categorías (Matemáticas, Código, Datos del mundo real, Bibliografía, Conceptos),
≥ 1 por módulo (M1, M2, M3) y ≥ 1 por persona. Consolida: Andrés. **Nunca inventar:** un hallazgo sin prompt literal o sin
evidencia no cuenta.

## Cobertura
| Módulo / categoría | Matemáticas | Código | Datos del mundo real | Bibliografía | Conceptos |
|---|---|---|---|---|---|
| M1 | | | | | |
| M2 | | | | | |
| M3 | 1 candidato sin número (JJ-2, redactor) | 1 candidato menor sin número (JJ-2, analista) | 2 candidatos sin número (JJ-1b) | | 1 candidato condicionado a fuente primaria (JJ-2, redactor) |
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

### H-?? (JJ-2) — «Los p de H-M3-1 a H-M3-4 son por permutación entre usuarios … los intervalos son por remuestreos de usuarios»
- **Módulo / categoría / quién lo encontró:** M3 / **Matemáticas** (descripción del método de inferencia: cómo se calculan
  los p y los IC; Andrés puede reclasificarlo como Código) / lo detectó el `verificador-matematico` (Opus) en R2, 1.ª vuelta
  (bloqueante B2); lo reprodujo el `cazador-alucinaciones` (Opus) en R4. Dirige: Juan José.
- **1. Prompt literal:** `alucinaciones/prompts/JJ-2-redactor-tecnico.md` (redactor-tecnico, Sonnet, 26-nov-2026). El prompt
  obligaba a sacar cada cifra y método de `results/data/m3/eda/`, incluido `pruebas_hipotesis.json`.
- **2. Respuesta relevante de la IA:** primera versión de `blog/secciones/07-m3-recomendacion.md` (herramienta Write del
  redactor, 2026-11-26T07:01:19Z; l. 302-304 de esa versión): «Los p de H-M3-1 a H-M3-4 son por permutación entre usuarios
  (10 000 permutaciones, …); los de H-M3-5, por simulación del reparto uniforme (2 000); los intervalos son por percentiles
  de 2 000 remuestreos de usuarios (o de destinos en H-M3-3) (`pruebas_hipotesis.json`, `metodo_p`, …)». Hay dos errores y
  una omisión: (a) H-M3-3 no permuta entre usuarios; (b) los IC de H-M3-5 no son remuestreos; (c) no dice que los p de
  H-M3-6 son asintóticos. La frase cita como fuente el mismo archivo que la contradice.
- **3. Cómo se sospechó:** R2 recalculó cada prueba con código propio y comparó la frase con `metodo_p` y `metodo_ic` de
  cada entrada.
- **4. Evidencia** (reproducible; en `alucinaciones/evidencias/JJ-2/`, copiada por la sesión principal desde el scratchpad
  de R4):
  - `blog_07_redactor_v1.md` es la primera versión del blog, sacada sin cambios de la llamada Write del transcript del
    subagente (SHA-256 `40c16854…cdae42`). El blog no estaba versionado: `HEAD` solo tiene el esqueleto.
  - `verificar_R4.py` §4 → `verificar_R4_salida.txt`. En `results/data/m3/eda/pruebas_hipotesis.json`:
    - `H3_spearman_popularidad.descripcion` = «Permutación de la popularidad entre los destinos».
    - `H5_*.efecto.metodo_ic` = «observado menos los percentiles de 2000 simulaciones … no es un bootstrap».
    - `H6_*.metodo_p` = «asintótica (χ²)» y «asintótica con corrección por empates».
  - Informe de R2: B2 y «candidato a hallazgo 1».
- **5. Corrección:** el redactor la reescribió siguiendo `alucinaciones/prompts/JJ-2-redactor-tecnico-2.md` (punto 1). El
  blog vigente (l. 312-324) da el método de cada hipótesis por separado: H-M3-1, H-M3-2 y H-M3-4 permutan entre usuarios;
  H-M3-3 entre destinos; H-M3-5 usa simulación con IC por inversión; H-M3-6 usa p asintóticos. R2 lo aprobó en su 2.ª vuelta
  y R4 lo comprobó.
- **6. Lección aprendida:** generalizar un método a un rango («de H-M3-1 a H-M3-4») suena bien pero es falso cuando una sola
  prueba difiere. La verificación que lo habría evitado es generar esa lista desde `metodo_p` y `metodo_ic` (o comparar la
  frase con esas claves en una prueba), en vez de resumirla a mano.
- **Estado:** candidato (lo numera y lo decide Andrés).

### H-?? (JJ-2) — La regla de veredicto escrita en `pruebas_hipotesis.json` no era la que aplicaba el código
- **Módulo / categoría / quién lo encontró:** M3 / **Código** (la salida documenta una regla distinta de la implementada) /
  lo detectó el `verificador-matematico` (Opus) en R2, 1.ª vuelta (bloqueante B1); lo reprodujo el `cazador-alucinaciones`
  (Opus) en R4. Dirige: Juan José.
- **1. Prompt literal:** `alucinaciones/prompts/JJ-2-analista-experimentos.md` (analista-experimentos, Sonnet, 26-nov-2026),
  E4: «define el criterio en la config y en el `resultado` … "Refutada" solo si … el efecto es compatible con cero con un
  intervalo estrecho».
- **2. Respuesta relevante de la IA:** en `src/m3_recomendacion/eda.py`, el analista escribió como texto fijo la clave
  `criterio_de_veredicto.regla` de `pruebas_hipotesis.json`: «refuta si p ajustado >= alfa y el IC 95 % del efecto queda
  dentro de ±mínimo». Así lo muestran la llamada Write de 06:50:19Z y la copia `pr_antes.json` de las 02:21 hora local
  (SHA-256 `64fba6e8…96fee8`).
  - En la primera versión, la función `veredicto_de_prueba` también decía eso (`estrecho = hi < minimo` en las pruebas
    «mayor»).
  - A las 06:53 el propio analista cambió la función, su docstring y `configs/m3/eda.yaml` para exigir además que el IC
    contenga el 0. **No actualizó el texto fijo.**
  - En su informe dijo: «La regla de «refuta» exige que el IC contenga el 0. La primera versión no lo exigía y declaraba
    refutada H-M3-1». Eso era cierto para el código, pero no para la regla publicada en el JSON.
- **3. Cómo se sospechó:** R2 aplicó la regla escrita a las 10 pruebas. En H-M3-1 daba un veredicto distinto del guardado.
- **4. Evidencia** (en `alucinaciones/evidencias/JJ-2/`):
  - `verificar_R4.py` §3 → `verificar_R4_salida.txt`, con `pr_antes.json`, `hip_antes.json` y `eda_analista_v1.py`.
  - Valores de H1: p ajustado 0,19998 ≥ 0,05; IC [0,000599; 0,046898] ⊂ (−0,05; 0,05).
  - Con esos valores, la regla escrita da «refuta», o sea H-M3-1 «refutada».
  - `veredicto_de_prueba` da «indeterminada», y `hip_antes.json` guarda «no concluyente».
  - Informe de R2: B1 y «candidato a hallazgo 2».
- **5. Corrección:** `alucinaciones/prompts/JJ-2-analista-experimentos-3.md`, punto 1. Ahora el texto se lee de
  `configs/m3/eda.yaml` (`regla_de_veredicto`), que es la única fuente, y una prueba fija el caso de H-M3-1. R2 (2.ª vuelta)
  y R4 (`verificar_R4.py` §2) comprobaron que las 10 pruebas dan, con la función vigente, los criterios guardados en
  `hipotesis.json`.
- **6. Lección aprendida:** si una regla existe en dos lugares (código y texto fijo), cambiar uno deja el otro desactualizado
  sin que falle nada. Una sola fuente para el texto y una prueba que aplique la regla escrita a un caso límite lo habrían
  atrapado.
- **Estado:** candidato **menor**. Es un cambio a medias, no una afirmación inventada sobre el mundo; Andrés decide si cuenta
  en Código, igual que H-01.

### H-?? (JJ-2) — «Los efectos mínimos … no son umbrales de la literatura» (CONDICIONADO: falta fuente primaria)
- **Módulo / categoría / quién lo encontró:** M3 / **Conceptos** (afirmación sobre la literatura estadística; podría ser
  Bibliografía) / lo detectó el `verificador-matematico` (Opus) en R2, 1.ª vuelta (tabla de fórmulas, fila «Mínimo de
  δ = 0,147»); lo evaluó el `cazador-alucinaciones` (Opus) en R4.
- **1. Prompt literal:** `alucinaciones/prompts/JJ-2-redactor-tecnico.md` (redactor-tecnico, Sonnet), punto 6: «Declara el
  criterio de veredicto y los efectos mínimos como **convención nuestra** …, sin presentarlos como norma de la literatura».
  El prompt pedía no *presentarlos* como norma. La IA lo convirtió en la afirmación de que *no son* umbrales de la
  literatura.
- **2. Respuesta relevante de la IA:** primera versión del blog (`blog_07_redactor_v1.md`, l. 292 y 299-300): «Criterio de
  veredicto (convención nuestra, no una norma de la literatura)» y «Los efectos mínimos (0,05 puntos de tasa, V de Cramér
  0,10, delta de Cliff 0,147, ρ de Spearman 0,10 y exceso de Gini 0,05) son **convención nuestra** …; no son umbrales de la
  literatura.»
- **3. Cómo se sospechó:** el valor 0,147 no es un número redondo. R2 lo buscó y lo encontró como el corte
  «despreciable/pequeño» del δ de Cliff.
- **4. Evidencia (solo secundaria por ahora):**
  - Documentación del paquete R `rstatix`, `cliff_delta` (https://rdrr.io/cran/rstatix/man/cliff_delta.html, consultada
    por R4 el 2026-11-26): «The magnitude thresholds are those of Romano et al. (2006)» y «|delta| < 0.147 "negligible",
    < 0.33 "small", < 0.474 "medium", otherwise "large"».
  - Documentación de `effsize`, consultada por R2.
  - **No se encontró el texto primario** (Romano, Kromrey, Coraggio y Skowronek, 2006, ponencia en la Florida Association
    of Institutional Research). Por eso «no son umbrales de la literatura» es falso **según dos fuentes secundarias
    concordantes**, pero no está verificado contra la primaria.
- **5. Corrección:** `alucinaciones/prompts/JJ-2-redactor-tecnico-2.md`, punto 6. El blog vigente (l. 299-300) dice solo que
  los mínimos son «una **convención nuestra** declarada en `configs/m3/eda.yaml`». Además deja
  `<!-- TODO(cita): el 0,147 de δ de Cliff se atribuye a Romano et al. (2006); verificar la fuente primaria en JJ-9 -->`.
- **6. Lección aprendida:** «no lo presentes como X» no autoriza a afirmar «no es X». Una afirmación negativa sobre la
  literatura también exige fuente. Un número no redondo como 0,147 es una señal de que viene de alguna parte.
- **Estado:** candidato **condicionado**. Como un «SIN PROMPT», no cuenta hasta que JJ-9 lea la ponencia primaria y confirme
  el 0,147.

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

### JJ-2 (M3, análisis descriptivo y blog 07) — R4, cazador-alucinaciones (Opus), 2026-11-26
- **Cifras del blog:** `cifras_blog.py` extrajo 669 tokens numéricos de `blog/secciones/07-m3-recomendacion.md` (sin contar
  comentarios ni claves). Todos se reproducen con algún valor de `results/data/m3/eda/` o de `perfil_nuevo.json` a la
  precisión mostrada. Es un filtro débil, porque basta con que el valor exista en cualquier archivo. Por eso se cotejaron a
  mano, contra su archivo y su clave, las cifras de cada tabla y de cada párrafo:
  - ficha y densidades (incluidos los denominadores, que son productos de los que aparecen);
  - calificaciones, actividad, sensibilidad y partición D3;
  - concentración: las 28 celdas de la tabla;
  - las 10 pruebas, con Holm recalculado;
  - H-M3-1: tasas, IC, IC ajustado, residuos y aporte al χ²;
  - H-M3-2 a H-M3-6 y veredictos.

  Todas coinciden y están bien redondeadas. Una sola cita de clave está mal: el Gini por lugar (l. 225-226) se atribuye a
  `interacciones_por_lugar.csv`, pero está en `concentracion.json` → `niveles.lugar`.
- **Cita del conjunto:** `mehra2024` coincide con la metadata de Kaggle y con `ficha.json`: autor Aman Mehra, 2024,
  «Travel recommendation dataset», versión 1 (`versions[0].creationDate` 2024-01-23), URL, y `urldate` = `fecha_descarga`
  = 2026-11-25. El blog solo usa «publicación» para negar que 2024-01-23 lo sea. Las 4 citas literales en inglés son
  subcadenas exactas de `info.description`. La única referencia `[@…]` es `mehra2024`, y hay 3 `TODO(cita)` (Romano,
  Bergsma, Gini/HHI/Holm).
- **Figuras:** `src/viz/figs_m3.py` lee todos los valores de `results/`. Solo están tecleados los rótulos «IC 95 %» y
  «Calificación (1 a 5)» y constantes de diseño.
- **Regla vigente:** las 10 pruebas dan, con `veredicto_de_prueba`, el criterio que guarda `hipotesis.json`.
- **Archivos:** `verificar_R4.py` → `verificar_R4_salida.txt` (35 OK, 1 MAL: la clave del Gini por lugar) y
  `cifras_blog.py` → `cifras_blog_salida.txt`, en `alucinaciones/evidencias/JJ-2/`. La clave mal citada del Gini por lugar
  y las cuatro frases que decían más que las cifras las corrigió la sesión principal en el blog (26-nov).
