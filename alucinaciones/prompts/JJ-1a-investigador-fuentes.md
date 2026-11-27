# Prompt JJ-1a (A2) — investigador-fuentes (Sonnet) — 2026-11-25 — orquesta: Juan José

Actúa como el agente definido en `.claude/agents/investigador-fuentes.md` (léelo primero). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales` (rama `dev/juanjose`). **No hagas commit, ni push, ni PR.**
Si usas Python, usa `.venv\Scripts\python` (Python 3.12, Windows); no instales nada.

Lee antes: `docs/spec/SPEC.md` §0 y §5.12 (fila M3 de la sección 1 «Ficha del conjunto» y 2 «Diccionario y calidad»), y del
Anexo de ese archivo el apartado «Módulo 3 → Datos»; `docs/spec/partes/juanjose.md` §3.1 y §5 (puntos calientes). Nada de otras
partes.

## Contexto
El Módulo 3 usa el conjunto «Travel Recommendation Dataset» publicado en Kaggle
(https://www.kaggle.com/datasets/amanmehra23/travel-recommendation-dataset). Juan José lo descargó a mano el 2026-11-25. El
enunciado exige: «Indiquen si los datos son reales o sintéticos, según la documentación de la fuente». Esta es la fase A de JJ-1:
documentar la fuente, sin decisiones de modelado.

## Tarea A2 — documentación de la fuente, citada literal y con fecha de consulta
La página de Kaggle se dibuja con JavaScript; usa los endpoints públicos que sí responden:
- https://www.kaggle.com/api/v1/datasets/metadata/amanmehra23/travel-recommendation-dataset
- https://www.kaggle.com/api/v1/datasets/list/amanmehra23/travel-recommendation-dataset

1. Descarga ambas respuestas (sin credenciales) y guárdalas en `docs/investigacion/JJ-1_kaggle_metadata.json` como un objeto
   JSON con la lista `respuestas`, un elemento por endpoint: `url`, `consultado_utc` (fecha y hora ISO 8601), `status` HTTP,
   `sha256_cuerpo` (de los bytes recibidos), `cuerpo_crudo` (el texto exacto recibido, como cadena, sin reformatear) y `cuerpo`
   (el mismo cuerpo parseado como JSON si lo es; si no, `null`). Si un endpoint falla, guarda el status y el cuerpo del error.
   Puedes intentar otros endpoints públicos de `www.kaggle.com/api/v1/` del mismo conjunto si aportan documentación (p. ej. la
   lista de archivos); si los usas, guárdalos igual en `respuestas`.
2. De las respuestas crudas extrae, **copiando literal** (entre comillas, con el campo JSON del que sale):
   - título, subtítulo, autor/propietario (todo campo de nombre o usuario que traiga), identificador/ref, URL;
   - descripción completa;
   - licencia(s) declarada(s): todos los campos que hablen de licencia. **Si se contradicen entre sí, dilo** y cita cada una;
   - fechas de creación, publicación y actualización, y versión, si existen;
   - lista de archivos con su tamaño y fechas, si la fuente la da;
   - descripción de columnas/campos, si existe (por archivo y por columna). Si la fuente no describe una columna, dilo así:
     «no documentado por la fuente»;
   - **toda** frase o palabra sobre cómo se generaron u obtuvieron los datos (real, sintético, simulado, «generated», «synthetic»,
     «enriched», «expanded», «augmented», «sample», «scraped», «collected», «survey»…), copiada literal con su campo. Busca
     también en etiquetas/keywords. Si la fuente no dice nada sobre real/sintético, escribe exactamente: «La fuente no documenta
     si los datos son reales o sintéticos».
   - Otros metadatos que traiga (etiquetas, puntaje de usabilidad, descargas, votos, DOI si existe).
3. Propón la **cita APA 7** del conjunto ([Data set], Kaggle), con autor, año y versión tomados de los campos de la respuesta
   (di de qué campo sale cada parte). Si un dato necesario para APA no está en la respuesta (p. ej. el nombre completo del autor),
   no lo completes de memoria: márcalo `TODO(cita)` y di de dónde podría salir (el enunciado del curso nombra al autor como
   «Aman Mehra»; úsalo solo declarándolo como fuente secundaria).

## Reglas
- Solo lo que dice la fuente: **nada de memoria ni de otras páginas que describan «un conjunto parecido»** (las IA suelen
  describir otro conjunto de viajes). Una página de terceros no es fuente primaria; si consultas una, sepárala y márcala así.
- **No abras ni describas los CSV de `data/raw/m3/`**: tu trabajo es solo lo que documenta la fuente. Otro agente mide los datos.
- Toda cita con la fecha de consulta (2026-11-25) y la URL exacta.
- Si encuentras algo que contradiga lo que una IA suele afirmar o lo que dice el enunciado, márcalo como CANDIDATO A HALLAZGO con el
  fragmento literal.
- No crees ni modifiques nada fuera de `docs/investigacion/JJ-1_kaggle_metadata.json` (en particular nada en `src/`, `configs/`,
  `data/`, `results/`, `blog/`, `alucinaciones/registro.md`).

## Entrega (tu mensaje final)
1. Archivo creado y endpoints consultados (URL, status, hora UTC, SHA-256 del cuerpo).
2. Tabla: dato · fragmento literal · campo JSON · URL · fecha de consulta · nivel de confianza.
3. Sección «Real o sintético»: todas las frases literales encontradas, o la frase «La fuente no documenta si los datos son
   reales o sintéticos».
4. Sección «Licencia»: cada declaración literal y si se contradicen.
5. Sección «Columnas»: lo que la fuente documente por columna, literal; lo demás, «no documentado por la fuente».
6. Cita APA 7 propuesta, indicando el campo de origen de cada parte, con `TODO(cita)` donde falte algo.
7. Lista numerada de **afirmaciones** en formato `[A2-n] afirmación — campo JSON / URL` para que otro agente las verifique.
8. Candidatos a hallazgo, si los hay.
