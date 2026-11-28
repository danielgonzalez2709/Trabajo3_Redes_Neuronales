# Registro de la Cacería de la alucinación

Meta: ≥ 5 hallazgos genuinos, ≥ 3 categorías (Matemáticas, Código, Datos del mundo real, Bibliografía, Conceptos),
≥ 1 por módulo (M1, M2, M3) y ≥ 1 por persona. Consolida: Andrés. **Nunca inventar:** un hallazgo sin prompt literal o sin
evidencia no cuenta.

## Cobertura
| Módulo / categoría | Matemáticas | Código | Datos del mundo real | Bibliografía | Conceptos |
|---|---|---|---|---|---|
| M1 | | 1 candidato menor sin número (CA-3d, implementador-experto) | | | 1 candidato sin número (CA-6a, investigador-fuentes) |
| M2 | | | | | |
| M3 | 1 candidato sin número (JJ-2, redactor) · 1 candidato sin número (JJ-3, implementador-experto + orquestador) · 1 candidato sin número (JJ-4, orquestador + implementador: MF colapsada) · 1 candidato menor sin número (JJ-4, redactor) · 1 candidato menor sin número (JJ-5, orquestador + implementador-experto: personalización) | 1 candidato menor sin número (JJ-2, analista) · 1 candidato menor sin número (JJ-4, guarda 1e-8) · 1 candidato menor sin número (JJ-5, fracción en [0, 1]) | 2 candidatos sin número (JJ-1b) · 1 candidato menor sin número (JJ-3, orquestador + redactor) | | 1 candidato condicionado a fuente primaria (JJ-2, redactor) · 1 candidato menor sin número (JJ-5, orquestador: destinos fríos) |
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

### H-?? (JJ-3) — «Para esos usuarios un "acierto por lugar" es trivial» (204 de 606 usuarios de prueba)
- **Módulo / categoría / quién lo encontró:** M3 / **Matemáticas** (razonamiento probabilístico sobre una línea base; Andrés
  puede reclasificarlo como Conceptos) / lo detectó el `auditor-fugas` (Opus) en R1 de JJ-3; lo reprodujo la sesión principal.
  Dirige: Juan José.
- **1. Prompt literal:** la premisa la escribió Juan José en `alucinaciones/prompts/JJ-3.md` (R1: «hace trivial un "acierto por
  lugar"»). La sesión principal (Opus 5.5) la convirtió en afirmación sobre un grupo medido en
  `alucinaciones/prompts/JJ-3-implementador-experto.md` (l. 102: «un "acierto por lugar" sería trivial para ellos») y en
  `JJ-3-redactor-tecnico.md` (l. 39). El `implementador-experto` (Opus) la escribió como hecho en el código.
- **2. Respuesta relevante de la IA:** `src/m3_recomendacion/particion.py`, 1.ª vuelta, `definicion` de
  `diagnosticos.mismo_lugar_en_historial_conocido` en `results/data/m3/particion/resumen.json`: «… del mismo lugar que su
  destino objetivo: los 1000 ids del catálogo son 5 lugares (D2), así que para ellos un «acierto por lugar» es trivial». El
  `redactor-tecnico` (Sonnet) lo llevó al blog: «una tercera parte de los usuarios de prueba lo tiene resuelto de antemano».
- **3. Cómo se sospechó:** el auditor comparó el conteo observado con el esperado si el lugar del objetivo fuera independiente
  del historial, y probó la heurística «repetir el lugar más frecuente del historial».
- **4. Evidencia:** `alucinaciones/evidencias/JJ-3/verificar_mismo_lugar.py` → `verificar_mismo_lugar_salida.txt`:
  observado 204, esperado por azar 198,0 (Σ_u |lugares distintos conocidos| / 5). La coincidencia es la del azar con 5
  lugares. El modelo no sabe cuál de sus lugares conocidos es el objetivo. Según el auditor, la heurística acierta a K = 1 el
  0,196 global, frente a 0,2 del azar. El 0,583 que da dentro de los 204 es selección por la respuesta: ese grupo se define con
  el lugar del objetivo de prueba.
- **5. Corrección:** `JJ-3-implementador-experto-2.md`: la `definicion` ya no dice «trivial». `resumen.json` trae
  `esperado_por_azar` (198,0 en prueba, 95,8 en validación) y su supuesto. Para el blog, `JJ-3-redactor-tecnico-2.md`: el
  acierto por lugar se compara con su línea base del azar y la métrica principal es la de `destino_id`.
- **6. Lección aprendida:** «X ocurre» no implica «X es un atajo»: antes de llamar trivial a un acierto, hay que compararlo con
  lo que da el azar. Con pocas clases (5 lugares), las coincidencias son frecuentes por construcción.
- **Estado:** candidato. Matiz para Andrés: la premisa la puso un humano en su prompt; el error de la IA es haberla convertido,
  sin medirla, en un hecho sobre un grupo concreto, en el código y en el blog.

### H-?? (JJ-3) — «Los 3 valores de VisitDate son posteriores a la creación del conjunto»
- **Módulo / categoría / quién lo encontró:** M3 / **Datos del mundo real** (lo medido en el conjunto de Kaggle) / lo detectó la
  sesión principal (Opus 5.5) al revisar el blog contra la Ficha. Dirige: Juan José.
- **1. Prompt literal:** `alucinaciones/prompts/JJ-3-redactor-tecnico.md`, l. 24 (sesión principal → redactor-tecnico,
  Sonnet): «la fecha de visita no es una fecha real (3 valores ligados al número de fila, posteriores a la creación del
  conjunto…)». La sesión principal lo tomó de `docs/MEMORIA.md` (Decisiones vigentes, M3: «3 valores ligados al número de fila
  y posteriores a la creación de la versión 1 en Kaggle»), que se carga en cada sesión.
- **2. Respuesta relevante de la IA:** el redactor lo copió al blog (subsección «Partición», 1.ª versión): «3 valores ligados
  al número de fila, posteriores a la creación del conjunto».
- **3. Cómo se sospechó:** la misma sección del blog, en la Ficha, dice «666 de 999 filas son posteriores».
- **4. Evidencia:** `alucinaciones/evidencias/JJ-3/visitdate_posteriores.md`. En `ficha.json`,
  `real_o_sintetico.senales_medidas.visit_date` da los valores 2024-01-01, 2024-02-15 y 2024-03-20, la versión 1 del
  2024-01-23 y 666 filas posteriores. 2024-01-01 es anterior.
- **5. Corrección:** el blog dice «3 valores ligados al número de fila, 2 de ellos —666 de 999 filas— posteriores a la creación
  de la versión 1 en Kaggle». `docs/MEMORIA.md` se corrigió al cierre de JJ-3.
- **6. Lección aprendida:** una memoria resumida que se carga en cada sesión propaga sus imprecisiones a todos los prompts
  siguientes. Las cifras de un prompt se copian del archivo de resultados, no de la memoria.
- **Estado:** candidato menor. El origen probable es la redacción de MEMORIA (documentador o sesión de JJ-2; no se buscó el
  prompt exacto); el prompt literal del eslabón de JJ-3 sí está guardado.

### H-?? (JJ-4) — La «mejor» factorización de la búsqueda era la solución trivial X = Y = 0
- **Módulo / categoría / quién lo encontró:** M3 / **Matemáticas** (con efecto en Código) / lo detectó el
  `verificador-matematico` (Opus) en R1 de JJ-4; lo confirmó la sesión principal con numpy. Dirige: Juan José.
- **1. Prompt literal:** `alucinaciones/prompts/JJ-4-implementador.md`, C5 (sesión principal, Opus 5.5 → implementador, Sonnet):
  «Rangos [PROPUESTO por esta tarea …]: factores 4–64, λ 1e-3–1e2, α 1–100, iteraciones 5–30».
- **2. Respuesta relevante de la IA:** el implementador declaró ese espacio, corrió 20 ensayos y reportó como mejor el ensayo 3
  (f = 8, λ = 29,542, α = 1,248; NDCG@5 en validación 0,0101) sin advertencia; el redactor (Sonnet) escribió que el empate de los
  ensayos 3, 14 y 18 «no se explica» y presentó la fila de la MF como una factorización normal.
- **3. Cómo se sospechó:** el verificador recalculó la pérdida de los factores guardados y dio exactamente (1 + α)·1 066, la
  pérdida en X = Y = 0.
- **4. Evidencia:** `alucinaciones/evidencias/JJ-4/colapso_mf.md` (+ `hpo_ensayos_colapsado.json`, `mf_als_colapsado.json`,
  `hpo_colapsado.yaml`): max|X| = 6,45e-23, max|Y| = 1,31e-23; σ_max(P_train) = 2,871; derivación
  L(X, Y) − L(0, 0) ≥ (λ − (1 + α)σ_max)(‖X‖² + ‖Y‖²); 8 de 20 ensayos (los 5 mejores entre ellos) con λ > (1 + α)·2,871.
- **5. Corrección:** λ ≤ 5,0 < (1 + α_min)σ_max = 5,742 (calculado solo con train y escrito en `hpo_ensayos.json`), guarda de
  degeneración, búsqueda y 30 corridas regeneradas (0 degenerados; mejor ensayo 19). Prompts `JJ-4-implementador-2.md` a `-4.md`.
- **6. Lección aprendida:** con datos casi aleatorios una búsqueda puede premiar una solución degenerada que empata con el azar;
  hay que mirar la norma de los factores (o la pérdida frente a L(0, 0)) del mejor ensayo y acotar la regularización con la
  escala de los datos antes de declarar el espacio.
- **Estado:** candidato. Origen en el prompt del orquestador (Opus); el implementador y el redactor (Sonnet) no lo detectaron.

### H-?? (JJ-4) — «La tolerancia 1e-8 detecta el colapso» y «la cota es suficiente, no necesaria»
- **Módulo / categoría / quién lo encontró:** M3 / **Código** (menor; con un matiz de Matemáticas) / `verificador-matematico`
  (Opus), R1 2.ª vuelta (N1 y N3).
- **1. Prompt literal:** `alucinaciones/prompts/JJ-4-implementador-2.md` (sesión principal → implementador): «una guarda marca
  como degenerado todo ajuste con max|x_uᵀy_i| < tolerancia … nunca puede ser el mejor» y «la cota es suficiente, no necesaria».
- **2. Respuesta relevante de la IA:** el implementador (Sonnet) lo implementó tal cual y el redactor lo escribió en el blog
  («la búsqueda nunca elige un ensayo degenerado»).
- **3. Cómo se sospechó:** el verificador probó ajustes justo encima de la cota con pocos barridos.
- **4. Evidencia:** informe de R1 (2.ª vuelta): con λ/((1 + α)σ_max) = 1,05 y 5 barridos, max|S| = 8,7e-5 > 1e-8 (no detectado);
  además, en la dirección de los primeros vectores singulares, L − L(0, 0) = 2t²(λ − (1 + α)σ_max) + O(t⁴): la condición es «si y
  solo si», no solo suficiente (lo suficiente es solo el tope del espacio). Tabla en
  `alucinaciones/evidencias/JJ-4/guarda_tolerancia.md` (los scripts del verificador quedaron en el scratchpad, no versionados).
- **5. Corrección:** regla exacta de tres condiciones (λ ≥ (1 + α)σ_max, pérdida ≥ L(0, 0), o max|S| < tolerancia) con pruebas de
  cada motivo (`JJ-4-implementador-4.md`); texto corregido en YAML, docstrings y blog.
- **6. Lección aprendida:** un umbral numérico absoluto no sustituye a la condición teórica cuando ésta se conoce.
- **Estado:** candidato menor (origen compartido orquestador Opus + implementador Sonnet).

### H-?? (JJ-4) — Afirmaciones numéricas del redactor en la «lectura de resultados»
- **Módulo / categoría / quién lo encontró:** M3 / **Matemáticas** (menor) / `verificador-matematico` (Opus), R1 (H2, H3, H4, N2).
- **1. Prompt literal:** `alucinaciones/prompts/JJ-4-redactor-tecnico.md` y `-2.md` (sesión principal → redactor, Sonnet).
- **2. Respuesta relevante de la IA:** «diferencias de 0,0004 a 0,0035» (el mínimo real era 0,00017); «Gini hasta 0,999; HHI de
  0,001 a 1» sin depender de K; «de 1 a 3 aciertos por grupo» (eran 0,97 a 3,33); «la mayor diferencia con el esperado en la tabla
  es la de la popularidad con K = 10» (falso en esa tabla: la cobertura se aleja mucho más).
- **3. Cómo se sospechó:** recálculo independiente de cada cifra del texto contra los JSON.
- **4. Evidencia:** informes de R1 (1.ª y 2.ª vuelta): con listas de K destinos distintos, Gini ≤ 1 − K/n y HHI ≤ 1/K; cobertura de
  la popularidad 0,0250 frente a 0,9977 esperado con K = 10.
- **5. Corrección:** texto reescrito con las cifras recalculadas (`JJ-4-redactor-tecnico-2.md` y `-4.md`).
- **6. Lección aprendida:** toda frase comparativa («la mayor», «de a … b») se recalcula sobre todas las filas de la tabla.
- **Estado:** candidato menor.

### H-?? (JJ-5) — «Personalización = desviación entre usuarios de s_ui» no mide la personalización del ranking
- **Módulo / categoría / quién lo encontró:** M3 / **Matemáticas** (menor) / `verificador-matematico` (Opus), R1 de JJ-5.
  Dirige: Juan José.
- **1. Prompt literal:** `alucinaciones/prompts/JJ-5-implementador-experto.md`, punto 2 (sesión principal, Opus 5.5 →
  implementador-experto, Opus): «una medida de personalización, p. ej. la media sobre destinos de la desviación entre usuarios de
  s_ui».
- **2. Respuesta relevante de la IA:** el implementador la implementó con el comentario «b_i no aporta: es común a todos» y la
  reportó entre semillas (media 0,091, máximo 0,242 en la semilla 8) como medida de personalización.
- **3. Cómo se sospechó:** el verificador descompuso S en efectos de usuario, de destino e interacción y comparó con las listas.
- **4. Evidencia:** `alucinaciones/evidencias/JJ-5/diagnosticos_red.md` (C1), `v5_semilla8.py`, `v3_colapso.py`: la semilla con la
  medida más alta da el mismo top-1 a los 606 usuarios y solo 6 listas top-10 distintas; el desplazamiento ⟨u, v̄⟩ de cada usuario
  infla la desviación sin cambiar ningún orden.
- **5. Corrección:** interacción doble centrada y tres diagnósticos de listas (`JJ-5-implementador-experto-2.md`); pruebas con una
  matriz aditiva (personalización 0) y una de interacción pura (cálculo a mano).
- **6. Lección aprendida:** una medida de «cuánto difieren los usuarios» debe ser invariante a lo que no cambia el orden
  (desplazamientos por usuario); se comprueba con un caso aditivo puro.
- **Estado:** candidato menor. Origen en el prompt del orquestador (Opus); el implementador (Opus) no lo detectó.

### H-?? (JJ-5) — «La fracción de varianza es 0 si S es constante» y «está en [0, 1]» (punto flotante)
- **Módulo / categoría / quién lo encontró:** M3 / **Código** (menor; matiz de Matemáticas) / `verificador-matematico` (Opus), R1
  2.ª y 3.ª vuelta.
- **1. Prompt literal:** `alucinaciones/prompts/JJ-5-implementador-experto-2.md` (orquestador → implementador: «`fraccion_varianza_
  interaccion` (‖E‖²/‖S − S.mean()‖²)»); la garantía «∈ [0, 1]» la escribió el orquestador al corregir (registrado en
  `JJ-5-verificador-matematico-3.md`).
- **2. Respuesta relevante de la IA:** docstring «(0 si S es constante)» con la guarda `total > 0`; luego «∈ [0, 1]; 0 si S es
  constante» con la guarda `ptp == 0`.
- **3. Cómo se sospechó:** el verificador probó matrices constantes y casi constantes.
- **4. Evidencia:** `alucinaciones/evidencias/JJ-5/diagnosticos_red.md` (C2), `w1_funcion.py`, `x1_frac.py`: 2,25 y 1 089 con S
  constante; hasta 2,7e9 con una celda a un ulp; 66 de 75 casos casi constantes fuera de [0, 1].
- **5. Corrección:** denominador por la descomposición ortogonal y guarda `ptp == 0` (`x2_arreglo.py`; 0 de 75 fuera de [0, 1]);
  pruebas de S constante y casi constante. No cambió ningún resultado (ninguna semilla real tiene S casi constante).
- **6. Lección aprendida:** un cociente de sumas de cuadrados centradas no hereda en punto flotante las cotas de la matemática
  exacta; se prueba con entradas a pocos ulp.
- **Estado:** candidato menor (implementador Opus + orquestador Opus).

### H-?? (JJ-5) — «Los destinos fríos quedan por debajo de los destinos con train»
- **Módulo / categoría / quién lo encontró:** M3 / **Conceptos** (menor) / `verificador-matematico` (Opus), R1 2.ª y 3.ª vuelta.
- **1. Prompt literal:** `alucinaciones/prompts/JJ-5-implementador-experto-2.md`, punto 2 (orquestador → implementador): «que diga
  que los fríos reciben puntaje solo por su tipo … y que en la práctica quedan por debajo de los destinos con train».
- **2. Respuesta relevante de la IA:** el implementador lo copió en `descripcion_frios` (también en `summary.json`); el
  orquestador lo reescribió como «pueden superar a destinos con train, pero no a los mejor puntuados de cada usuario».
- **3. Cómo se sospechó:** el verificador midió la posición del mejor frío en la lista de cada usuario.
- **4. Evidencia:** `alucinaciones/evidencias/JJ-5/diagnosticos_red.md` (C3), `x3_frios.py`: el mejor frío supera entre el 62,3 % y
  el 88,7 % de los destinos con train; posición mínima 75. Solo es empírico que ningún frío entre al top-10 (30 semillas).
- **5. Corrección:** «Pueden superar a destinos con train; si entran o no al top-K depende del entrenamiento, así que se MIDE en
  `frios_por_lista`.»
- **6. Lección aprendida:** no convertir un resultado de una corrida (0 fríos en el top-10) en una propiedad del modelo.
- **Estado:** candidato menor (orquestador Opus; el implementador lo copió).

### H-?? (CA-3d) — «R1: 15,5 / 0,6 · … ≠ 31» en el comentario de una prueba (la carga real es 16,5)
- **Módulo / categoría / quién lo encontró:** M1 / **Código** (cifra falsa en el comentario de una prueba; menor) / lo señaló
  el `revisor-calidad` (Sonnet) en la 1.ª vuelta de CA-3d como comentario ilegible (C10); el `implementador-experto` de CA-3e
  (Opus) al reescribirlo encontró que la cifra estaba mal; lo verificó la sesión orquestadora con un script propio. Dirige: Camila.
- **1. Prompt literal:** `alucinaciones/prompts/CA-3d.md` (subagente `implementador-experto`, Opus, 27-nov-2026), que pedía
  calibrar m_r y probar con «el caso a mano en el comentario».
- **2. Respuesta relevante de la IA:** en el commit `1a27df7`, `tests/test_operacion_m1.py:747`
  (`test_multiplicadores_reproducen_cada_ruta`): «# con ρ* global solo el total coincide (R1: 15,5 / 0,6 · … ≠ 31).»
- **3. Cómo se sospechó:** C10 de `alucinaciones/prompts/CA-3e.md` pidió escribir el cálculo completo; al hacerlo, el
  implementador de CA-3e obtuvo 16,5 y no 15,5.
- **4. Evidencia:** `alucinaciones/evidencias/CA-3d/verificar_comentario_R1.py` → `salida_comentario_R1.txt` (no importa
  `src/`; lee el comentario del commit `1a27df7` con `git show`): con los datos de la propia prueba, Σ f·D/cap_ef de R1 =
  0,5·(400+260)/20 = **16,5**; ρ* = 21,5/36 = 0,5972; 16,5/0,6 = 27,5 y 16,5/ρ* = 27,63, ambos ≠ 31. Con la cifra del comentario
  saldría 15,5/0,6 = 25,83. La conclusión (≠ 31) era cierta; el número que la sostenía, no.
- **5. Corrección:** CA-3e reescribió el comentario con el cálculo completo (`tests/test_operacion_m1.py:736-744` y `:770-772`:
  16,5 / 0,5972 = 27,63 ≠ 31); la 2.ª vuelta de `revisor-calidad` lo verificó.
- **6. Lección aprendida:** un «caso a mano» en un comentario no lo ejecuta nadie: si la prueba no aserta ese número, puede
  estar mal sin que nada falle. Escribir el cálculo completo con los datos de la prueba, o convertirlo en aserción.
- **Estado:** candidato (menor: no afectó ningún resultado; Andrés decide si cuenta en la categoría Código).

### H-?? (CA-6a) — «Arrendar en vez de comprar mueve ~un tercio de la estructura de costos»
- **Módulo / categoría / quién lo encontró:** M1 / **Conceptos** (interpretación de un índice de costos) / cazador-alucinaciones
  (Opus) en la verificación CA-6, 27-nov-2026. Dirige: Camila.
- **1. Prompt literal:** `alucinaciones/prompts/CA-6a.md` (investigador-fuentes, Sonnet, 27-nov-2026), sección «Entrega»: «una
  sección "Qué se puede concluir con esto" que diga qué comparación de costos es defendible y cuál no».
- **2. Respuesta relevante de la IA:** `docs/investigacion/CA-6_costos_flota.md` §8, «Defendible (con cita)», punto 3:
  «Estructura relativa de costos: combustible ~31 %, costos fijos ~33 % (incluye conductores), peajes y terminales ~20 %. Permite
  argumentar, por ejemplo, que una opción que reduzca costos fijos (arrendar, no comprar) mueve ~un tercio de la estructura».
- **3. Cómo se sospechó:** la misma frase reconoce que los costos fijos «incluye[n] conductores»; arrendar un vehículo no elimina
  el salario del conductor, así que el «tercio» no puede atribuirse a la decisión comprar/arrendar.
- **4. Evidencia:** DANE, metodología DSO-ICTIP-MET-001 v2 (2018): «costos fijos (parqueaderos, seguros, costo del vehículo,
  impuestos y mano de obra)» (`alucinaciones/evidencias/CA-6/ictip_met_v2.txt`). DANE, boletín ICTIP III-2026 (22-oct-2026),
  Tabla 3: «Costos fijos 32,99 14,07 4,83» y Tabla 4: «Mano de obra conductor(es) y ayudante(s) 22,11 4,72»
  (`ictip_bol_IIItrim2026.txt`): de los 4,83 p.p. que aportó el grupo en el año corrido, 4,72 vienen de la mano de obra.
  `verificar.py` → `salida.txt` (fragmentos CF, C-2c, C-2cf).
- **5. Corrección:** «Arrendar en vez de comprar sustituye solo el componente de capital ("Costo del vehículo y su
  apalancamiento"), cuyo peso no está en el boletín (T-9); conductores, combustible, peajes y seguros se mantienen. No se puede
  cuantificar el ahorro con el 32,99 %».
- **6. Lección aprendida:** un grupo de un índice de precios no es una palanca de decisión: antes de decir qué «mueve» una
  opción, bajar al nivel de clase de costo y comprobar qué componentes cambia realmente.
- **Estado:** candidato. Detalle: `docs/investigacion/CA-6_verificacion.md` (V-20). Es un error de razonamiento, no un dato inventado:
  Andrés decide si cuenta en la categoría Conceptos.

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
