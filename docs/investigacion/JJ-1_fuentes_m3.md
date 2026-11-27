# JJ-1 (fase A) — Fuentes e inventario del Módulo 3: Travel Recommendation Dataset (Kaggle)

Fecha: **2026-11-25**. Orquesta: Juan José (rama `dev/juanjose`). Prompt de la sesión: `alucinaciones/prompts/JJ-1a.md`.
Fase A = medir y documentar **sin decisiones de modelado**. La definición de «interacción», la partición y la construcción de
`data/processed/m3/` son de la fase B.

| Pieza | Agente (modelo) | Prompt literal | Producto |
|---|---|---|---|
| A1 inventario medido | curador-datos (Sonnet) | `alucinaciones/prompts/JJ-1a-curador-datos.md` | `JJ-1_inventario.py` → `JJ-1_inventario_salida.txt` |
| A2 documentación de la fuente | investigador-fuentes (Sonnet) | `alucinaciones/prompts/JJ-1a-investigador-fuentes.md` | `JJ-1_kaggle_metadata.json` (respuestas crudas de la API) |
| A3 verificación adversarial | cazador-alucinaciones (Opus) | `alucinaciones/prompts/JJ-1a-cazador-alucinaciones.md` | `JJ-1_verificacion_A3.md` + `alucinaciones/evidencias/JJ-1a/` |

Respuestas literales de los tres subagentes: `alucinaciones/evidencias/JJ-1a/respuesta-*.md`.

**Cómo leer las cifras.** Toda cifra sale de `docs/investigacion/JJ-1_inventario_salida.txt` (sección `§A1.x`), que se
regenera con `.venv\Scripts\python -I docs/investigacion/JJ-1_inventario.py` desde la raíz. A3 la recalculó con un script
independiente (`alucinaciones/evidencias/JJ-1a/verificar_A3.py`): 137 de 140 comprobaciones coinciden y las 3 que difieren son
redondeos de A1. La salida se reproduce bit a bit. Las cifras marcadas «(derivado)» son restas de cifras medidas. Todo lo que
se dice de la fuente sale de `JJ-1_kaggle_metadata.json`, consultado el 2026-11-25 a las 23:16 UTC (A3 lo volvió a descargar
a las 23:26 UTC y es idéntico byte a byte).

---

## 1. Ficha preliminar

| Dato | Valor | De dónde sale |
|---|---|---|
| Conjunto | «Travel Recommendation Dataset». La descripción lo titula «India Travel Recommender System Dataset» | `title`; primera línea de `info.description` |
| Autor / propietario | «Aman Mehra», usuario `amanmehra23` | `creatorName`, `ownerName`, `ownerRef` (`datasets/view`) |
| Plataforma | Kaggle, ref. `amanmehra23/travel-recommendation-dataset`, id 4345382 | `ref`, `id` |
| URL | https://www.kaggle.com/datasets/amanmehra23/travel-recommendation-dataset | `url` (`datasets/list?search=`) |
| Versión | 1, «Initial release», creada el 2024-01-23T17:07:26.487Z. Sin actualizaciones posteriores (`lastUpdated` es la misma fecha) | `versions[0]`, `lastUpdated` |
| DOI | No hay | Ausencia comprobada con búsqueda por código (A3) |
| Licencia | Contradictoria; ver §3.2 | — |
| Descarga | 2026-11-25, Juan José, a mano desde la página de Kaggle con su cuenta (botón Download → `archive.zip`) en `data/raw/m3/` (no versionado) | Contexto de la tarea |
| Consulta de metadatos | 2026-11-25, 23:16 UTC (API pública de Kaggle, sin credenciales) | `JJ-1_kaggle_metadata.json` |
| ¿Real o sintético? | La fuente dice «generated for educational and research purposes»; no usa «synthetic» ni «real». Ver §3.1 | `info.description` |

**Cita APA 7 propuesta** (en el formato del blog: título en minúscula de oración y tipo en español, como `supertransporte2026`
de `blog/references.bib`):

> Mehra, A. (2024). *Travel recommendation dataset* (Versión 1) [Conjunto de datos]. Kaggle.
> https://www.kaggle.com/datasets/amanmehra23/travel-recommendation-dataset

De dónde sale cada parte: autor de `creatorName` («Aman Mehra»; invertir a «Mehra, A.» es la regla APA); año de
`versions[0].creationDate`; título de `title`; versión de `currentVersionNumber`; URL de `url`. A2 la propuso con el título en
mayúsculas iniciales y «[Data set]»; A3 señaló el formato (minúscula de oración e idioma mezclado) y aquí se corrigió.

**Archivos** (tamaño en bytes y SHA-256 de los bytes en disco; `§A1.1`):

| Archivo | Bytes | SHA-256 | Tamaño según Kaggle (`datasetFiles[].totalBytes`) |
|---|---|---|---|
| `archive.zip` | 34 679 | `117e3135b2fb8ff1ecb1e3a2d4b57315273f7954520567bbb5663af2912d004d` | 34 679 (`totalBytes` de `datasets/list?search=`) |
| `Expanded_Destinations.csv` | 60 768 | `5e311d3df9ebd626df28c90060b4804cfaeaee11012e1ffcfcc27c1817179766` | 60 768 |
| `Final_Updated_Expanded_Reviews.csv` | 33 710 | `bd9a10fb063592418511fa05350862fc6e8e81d6ab087422992ce64a066aca48` | 33 710 |
| `Final_Updated_Expanded_UserHistory.csv` | 24 683 | `df8a5b21e0c1f45ca9e48dfe98db83ae291a45ee0f8be800bd4274a81ac7307b` | 24 683 |
| `Final_Updated_Expanded_Users.csv` | 58 535 | `a3c51b1583ed727fed42278af77bde007aeba2a71fc1fd17c477080e275aaeac` | 58 535 |

Los 4 CSV sueltos son idénticos byte a byte a los miembros del .zip (CRC sin errores). Son UTF-8 sin BOM, solo ASCII, con fin
de línea LF, y el módulo `csv` y pandas cuentan las mismas filas. La suma de los 4 CSV es 177 696 B, igual al `totalBytes` de
`datasets/view`; el otro `totalBytes` (34 679) es el tamaño del .zip, así que no es una contradicción (A3).

---

## 2. Inventario medido

### 2.1 Estructura por archivo (`§A1.2`, `§A1.3`)

| Archivo | Filas | Columnas | Faltantes | Duplicados exactos | Primera columna |
|---|---|---|---|---|---|
| Destinations | 1 000 | `DestinationID, Name, State, Type, Popularity, BestTimeToVisit` | 0 | 0 | `DestinationID` = 1..1000 sin huecos, única |
| Reviews | 999 | `ReviewID, DestinationID, UserID, Rating, ReviewText` | 0 | 0 | `ReviewID` = 1..999, única |
| UserHistory | 999 | `HistoryID, UserID, DestinationID, VisitDate, ExperienceRating` | 0 | 0 | `HistoryID` = 1..999, única |
| Users | 999 | `UserID, Name, Email, Preferences, Gender, NumberOfAdults, NumberOfChildren` | 0 | 0 | `UserID` = 1..999 sin huecos, única |

- Sin `UserID`, Users tiene solo **342 filas distintas** (657 repetidas). Las demás tablas no repiten filas al quitar su contador.
- **Integridad referencial total**: todo `UserID` y `DestinationID` de Reviews y UserHistory existe en Users y Destinations
  (0 filas y 0 ids huérfanos).
- Tablas maestras: **999 usuarios** y **1 000 destinos**.

### 2.2 Columnas: tipo, valores distintos y ejemplos (`§A1.2`, `§A1.11`)

| Archivo.columna | Tipo medido | Distintos | Valores o ejemplos |
|---|---|---|---|
| Destinations.Name | texto | 5 | Taj Mahal, Goa Beaches, Jaipur City, Kerala Backwaters, Leh Ladakh (200 c/u) |
| Destinations.State | texto | 5 | Uttar Pradesh, Goa, Rajasthan, Kerala, Jammu and Kashmir (200 c/u) |
| Destinations.Type | texto | 5 | Historical, Beach, City, Nature, Adventure (200 c/u) |
| Destinations.Popularity | decimal | 1 000 | mín 7.5045, q1 8.0345, mediana 8.4965, q3 9.0208, máx 9.4998 |
| Destinations.BestTimeToVisit | texto (no parsea como fecha) | 5 | Nov-Feb, Nov-Mar, Oct-Mar, Sep-Mar, Apr-Jun (200 c/u) |
| Reviews.Rating | entero | 5 | 1–5 |
| Reviews.ReviewText | texto | 3 | «Incredible monument!», «Loved the beaches!», «A historical wonder» (333 c/u) |
| UserHistory.VisitDate | texto AAAA-MM-DD | 3 | 2024-01-01, 2024-02-15, 2024-03-20 (333 c/u) |
| UserHistory.ExperienceRating | entero | 5 | 1–5 |
| Users.Name | texto | 20 | 38 a 64 ids por nombre (p. ej. Aanya 64, Diya 38) |
| Users.Email | texto | 20 | siempre `<nombre en minúsculas>@example.com` (999 de 999) |
| Users.Preferences | lista en texto («, ») | 3 combinaciones | «Beaches, Historical», «Nature, Adventure», «City, Historical» (333 c/u); siempre 2 opciones; 5 opciones distintas: Historical 666, Beaches 333, Nature 333, Adventure 333, City 333 |
| Users.Gender | texto | 2 | Male 503, Female 496 |
| Users.NumberOfAdults | entero | 2 | 1: 495, 2: 504 |
| Users.NumberOfChildren | entero | 3 | 0: 338, 1: 341, 2: 320 |

### 2.3 Calificaciones: escala medida (`§A1.4`)

| Columna | Mín | Máx | Valores | Frecuencias (1/2/3/4/5) | Media |
|---|---|---|---|---|---|
| Reviews.Rating | 1 | 5 | 5 enteros | 198 / 199 / 185 / 216 / 201 | 3.023 |
| UserHistory.ExperienceRating | 1 | 5 | 5 enteros | 206 / 228 / 201 / 183 / 181 | 2.905 |

Las dos son compatibles con la uniforme (χ² = 2.44, p = 0.656 y χ² = 7.36, p = 0.118; gl = 4; `§A1.13a`). La fuente no
documenta la escala (§4).

### 2.4 Interacciones por archivo (`§A1.5`)

| | Reviews | UserHistory |
|---|---|---|
| Filas | 999 | 999 |
| Pares (usuario, destino) distintos | 999 (0 repetidos) | 999 (0 repetidos) |
| Usuarios que aparecen / maestros que no | 624 / 375 | 642 / 357 |
| Destinos que aparecen / maestros que no | 651 / 349 | 638 / 362 |
| Por usuario (solo los que aparecen): mín, mediana, media, máx | 1, 1, 1.601, 5 | 1, 1, 1.556, 6 |
| Usuarios con 1 / 2 / 3 / 4 / ≥ 5 | 355 / 190 / 58 / 15 / 6 | 384 / 180 / 60 / 16 / 2 |
| Por destino: mín, mediana, media, máx | 1, 1, 1.535, 5 | 1, 1, 1.566, 6 |
| Destinos con 1 / 2 / 3 / 4 / ≥ 5 | 396 / 178 / 62 / 14 / 1 | 383 / 177 / 56 / 17 / 5 |
| Densidad (a) maestras 999 × 1 000 | 0.001000 (0.10 %) | 0.001000 (0.10 %) |
| Densidad (b) los que aparecen | 999 / (624 × 651) = 0.002459 | 999 / (642 × 638) = 0.002439 |

La dispersión de interacciones por usuario y por destino (varianza/media de 0.918 a 1.029) y los ceros (349 a 375 contra 367–368
esperados) son los de repartir usuario y destino al azar de manera uniforme (`§A1.13b`).

### 2.5 Solapamiento Reviews vs. UserHistory (`§A1.6`)

| Pares en ambos | Solo Reviews | Solo UserHistory | Unión |
|---|---|---|---|
| **0** | 999 | 999 | 1 998 |

Al no haber pares comunes, no hay calificaciones que comparar. Sí se comparten usuarios (408 en ambos; 216 solo en Reviews,
234 solo en UserHistory) y destinos (423 en ambos; 228 y 215).

### 2.6 Fechas (`§A1.8`)

- **Única columna de fecha: `UserHistory.VisitDate`.** Parsean 999 de 999. Solo hay **3 valores**: 2024-01-01, 2024-02-15 y
  2024-03-20, con 333 filas cada uno. Es una función exacta de `HistoryID mod 3`.
- 195 de los 642 usuarios de UserHistory tienen visitas en más de una fecha (172 en 2 fechas y 23 en 3).
- **Reviews no tiene fecha.** `BestTimeToVisit` no es una fecha (0 de 1 000 parsean).
- 666 de las 999 visitas (las de 2024-02-15 y 2024-03-20) son **posteriores a la creación de la versión 1 en Kaggle**
  (2024-01-23) (A3, `verificar_A3_salida.txt §V10`).

### 2.7 Destinos e identificadores (`§A1.9`)

- **1 000 identificadores, 5 nombres distintos**, 200 ids por nombre. Para un mismo nombre, `State`, `Type` y
  `BestTimeToVisit` no cambian: solo hay **5 combinaciones** de nombre y atributos. Lo único que varía entre los 200 ids de
  un nombre es `Popularity` (media por nombre de 8.49 a 8.55).
- Nombre, estado, tipo y temporada son función exacta de `DestinationID mod 5`, en el ciclo Taj Mahal (Historical), Goa
  Beaches (Beach), Jaipur City (City), Kerala Backwaters (Nature) y Leh Ladakh (Adventure).
- Interacciones por nombre (`§A1.13e`): en Reviews 190 / 191 / 201 / 218 / 199 (Goa / Jaipur / Kerala / Leh / Taj); en
  UserHistory 190 / 185 / 211 / 204 / 209.

### 2.8 Variables de contenido disponibles (`§A1.11`)

| Tabla | Variable | Tipo | Categorías |
|---|---|---|---|
| Users | `Preferences` | lista de 2 opciones | 3 combinaciones; 5 opciones (Beaches, City, Historical, Nature, Adventure) |
| Users | `Gender` | categórica | 2 |
| Users | `NumberOfAdults` | entera | 2 (1, 2) |
| Users | `NumberOfChildren` | entera | 3 (0, 1, 2) |
| Users | `Name`, `Email` | texto identificador | 20 (no son variables de contenido útiles; ver ética en §5) |
| Destinations | `Type` | categórica | 5 (Historical, Beach, City, Nature, Adventure) |
| Destinations | `State` | categórica | 5 (misma partición que `Name` y `Type`) |
| Destinations | `BestTimeToVisit` | categórica (rango de meses) | 5 (misma partición) |
| Destinations | `Popularity` | continua | 1 000 valores |

En los destinos, `Name`, `State`, `Type` y `BestTimeToVisit` definen la **misma** partición en 5 grupos: como variable de
contenido, aportan la misma información.

### 2.9 Señales de datos generados (solo lo medido; `§A1.13`)

| Señal | Medición |
|---|---|
| Uniformidad exacta | Destinations.Name/State/Type/BestTimeToVisit: 200 c/u; ReviewText, VisitDate y Preferences: 333 c/u (razón máx/mín = 1.000) |
| Uniformidad aproximada | Rating, ExperienceRating, Gender, NumberOfAdults, NumberOfChildren y Name: no se rechaza la uniforme (p de 0.118 a 0.825) |
| Periodicidad respecto al id de fila | Destinos `mod 5`; `Preferences` `mod 3`; `ReviewText` `mod 3`; `VisitDate` `mod 3` |
| Texto incoherente con el destino | `ReviewText` vs. destino reseñado: χ² p = 0.884, V = 0.043 (p. ej., «Incredible monument!» 60 veces sobre Goa Beaches); vs. `Rating`: p = 0.547 |
| Visitas «futuras» | 666 de 999 `VisitDate` posteriores a la creación de la versión 1 en Kaggle (2024-01-23) |
| Usuarios repetidos | 20 nombres para 999 ids; el correo es siempre el nombre + `@example.com`; 342 perfiles distintos |
| Preferencias vs. tipo visitado | Coincidencia observada frente a la esperada al azar: (i) 0.429 vs. 0.400 (z = 1.90, p = 0.058); (ii) 0.417 vs. 0.400 (z = 1.12, p = 0.26); (iii) 0.423 vs. 0.400 (z = 2.14, p = 0.033). Supuesto del análisis: `Beaches` ↔ `Beach` |
| Calificación vs. contenido | Sin asociación con tipo de destino, género ni tamaño del grupo (Kruskal–Wallis p ≥ 0.18). Única χ² con p < 0.05: `Preferences` × `ExperienceRating`, p = 0.0074 (V = 0.10), con Kruskal–Wallis p = 0.18 |
| `Popularity` vs. datos | Spearman con la calificación ρ = 0.044 y 0.028; con el número de interacciones ρ = −0.041 y 0.022 (p > 0.16) |

Nota de A3 sobre las pruebas: hay más de 60 valores p en la salida, y los pocos menores de 0.05 (0.0074 a 0.033) no resisten
una corrección de Bonferroni. El p de 6.96e-47 de «Preferences (opciones separadas)» no es una prueba válida (las opciones no
son independientes) y no debe ir al blog.

---

## 3. Qué dice la fuente: real o sintético, y licencia

### 3.1 Real o sintético (citas literales de `info.description`)

- Sección «Acknowledgements»: *«This dataset was generated for educational and research purposes and is intended to be used in
  hackathons, academic projects, and by AI enthusiasts aiming to enhance the travel experience through technology.»*
- Sección «Users»: *«This dataset has been enriched with gender diversity and includes details on the number of adults and
  children for travel.»*
- Sección «Reviews»: *«User-generated reviews and ratings for the different destinations, offering insights into visitor
  experiences and satisfaction.»*
- Los nombres de archivo llevan «Expanded» y «Final_Updated_Expanded» (`datasetFiles[].name`). La fuente no dice qué se
  expandió ni desde qué conjunto.
- En ninguna de las respuestas aparecen «synthetic», «simulated», «augmented», «sample», «scraped», «collected» ni «survey».
  Lo comprobó A3 con búsqueda por código. `userSpecifiedSources` está vacío y la única etiqueta es «travel».

**Lectura estricta:** la fuente dice que el conjunto fue *«generated»* con fines educativos y de investigación, pero no dice
con qué método ni si parte de datos reales. Tampoco usa la palabra «sintético». Las señales medidas de §2.9 son compatibles con
datos generados por programa, pero eso es evidencia de los datos, no documentación de la fuente: en el blog hay que separar
las dos cosas.

### 3.2 Licencia: tres declaraciones que se contradicen

| Declaración literal | Campo |
|---|---|
| «MIT» | `info.licenses[0].name` (`datasets/metadata`), `licenseName` (`datasets/view`, `datasets/list?search=`) |
| «CC0: Public Domain - The dataset is in the public domain and can be used without restrictions.» | `info.description`, sección «License» |
| «This dataset is free to use for non-commercial purposes. For commercial use, please contact the dataset provider. Remember to cite the source when using this dataset in your projects.» | `info.description`, sección «Usage» |

MIT y CC0 permiten el uso comercial; la sección «Usage» lo restringe (A3 lo contrastó con los textos oficiales de MIT y CC0,
https://opensource.org/license/mit y https://creativecommons.org/publicdomain/zero/1.0/; consultas del 2026-11-25 registradas
en `alucinaciones/evidencias/JJ-1a/redescarga_A3/indice_licencias.txt`). Para este trabajo académico no comercial las tres permiten el
uso. Solo la sección «Usage» pide citar la fuente («Remember to cite the source when using this dataset in your projects.»);
la sección «License» (CC0) no exige atribución y la MIT pide conservar el aviso de copyright y de permiso en las copias, que
no es lo mismo que citar. *(Corregido el 2026-11-25 en JJ-1b: la versión de la fase A decía «y todas coinciden en pedir que se
cite la fuente», lo que es falso; lo detectó el revisor-spec, ver `alucinaciones/evidencias/JJ-1b/`.)*

---

## 4. Diccionario

La fuente **no documenta ninguna columna**: en `datasets/list`, cada archivo trae `"columns": []` y `"description": ""`. Lo
único que hay es la descripción narrativa de cada componente, que no nombra archivos ni columnas. La correspondencia entre
componente y archivo (y entre frase y columna) es una inferencia nuestra y se marca así.

| Archivo.columna | Significado según la fuente | Texto narrativo relacionado (sin nombrar la columna; la correspondencia es inferencia) |
|---|---|---|
| Destinations.DestinationID | no documentado por la fuente | — |
| Destinations.Name | no documentado por la fuente | «Information about various travel destinations in India» |
| Destinations.State | no documentado por la fuente | — |
| Destinations.Type | no documentado por la fuente | «type of destination (beach, mountain, historical site, etc.)» |
| Destinations.Popularity | no documentado por la fuente (ni su escala ni cómo se calculó) | «popularity» |
| Destinations.BestTimeToVisit | no documentado por la fuente | «best time to visit» |
| Reviews.ReviewID | no documentado por la fuente | — |
| Reviews.DestinationID, Reviews.UserID | no documentado por la fuente | — |
| Reviews.Rating | no documentado por la fuente (tampoco la escala) | «User-generated reviews and ratings for the different destinations» |
| Reviews.ReviewText | no documentado por la fuente | ídem |
| UserHistory.HistoryID | no documentado por la fuente | — |
| UserHistory.UserID, UserHistory.DestinationID | no documentado por la fuente | «including destinations visited» |
| UserHistory.VisitDate | no documentado por la fuente | «Records of users' past travel experiences» |
| UserHistory.ExperienceRating | no documentado por la fuente (tampoco la escala) | «and ratings provided» |
| Users.UserID, Users.Name, Users.Email | no documentado por la fuente | «Profiles of users» |
| Users.Preferences | no documentado por la fuente | «including their preferences» |
| Users.Gender | no documentado por la fuente | «enriched with gender diversity» |
| Users.NumberOfAdults, Users.NumberOfChildren | no documentado por la fuente | «details on the number of adults and children for travel» |

`TODO(dato-faltante)`: la diferencia entre `Rating` (Reviews) y `ExperienceRating` (UserHistory) y el significado de
`Popularity` no están documentados. Solo se puede describir lo medido.

---

## 5. Inconsistencias y problemas de calidad

1. **Catálogo «expandido» con 5 destinos reales.** Hay 1 000 `DestinationID`, pero solo 5 combinaciones de nombre, estado,
   tipo y temporada, que se repiten en ciclo (`id mod 5`). Lo único que distingue los 200 ids de un mismo nombre es
   `Popularity`, que no se relaciona con las calificaciones ni con el número de interacciones (§2.9). Que esos 200 ids sean
   «el mismo lugar» es una inferencia, porque la fuente no documenta qué es `DestinationID`.
2. **La descripción contradice los datos en los tipos.** La fuente dice «type of destination (beach, mountain, historical
   site, etc.)», pero `Type` solo trae Historical, Beach, City, Nature y Adventure: no hay ningún tipo «mountain».
   Lo verificó la sesión principal leyendo el JSON y la columna.
3. **Fechas imposibles y periódicas.** `VisitDate` tiene 3 valores, es función de `HistoryID mod 3`, y 666 de 999 visitas son
   posteriores a la creación de la versión 1 en Kaggle (2024-01-23).
4. **Reseñas plantilla.** Hay 3 textos (`ReviewID mod 3`) que no tienen relación con el destino ni con la calificación.
5. **Usuarios repetidos.** 999 ids con 20 nombres; 342 perfiles distintos. `Preferences` es función de `UserID mod 3`.
   141 usuarios maestros no aparecen en ninguna interacción (A1.7, unión).
6. **Vocabularios distintos** entre `Preferences` («Beaches») y `Type` («Beach»). Para cruzarlos hace falta un emparejamiento
   que es supuesto nuestro, no de la fuente.
7. **Dos tablas de interacción disjuntas.** Reviews y UserHistory no comparten ningún par (usuario, destino). Cada una tiene su
   propia calificación de 1 a 5, con distribución compatible con la uniforme, y la fuente no documenta ninguna de las dos.
8. **Señal débil.** La afinidad entre preferencias y tipo visitado está apenas por encima del azar (0.42–0.43 contra 0.40), y
   las calificaciones no se asocian con nada medido. A1 escribió «no hay señal fuerte que aprender»; A3 lo calificó de
   razonable pero inferido: solo el modelado lo confirma.
9. **Licencia contradictoria** (§3.2).
10. **Lo que está bien:** no hay faltantes, filas duplicadas ni filas mal partidas, la integridad referencial es total y los
    CSV coinciden con el .zip.
11. **Ética / privacidad (para la sección del blog):** Users trae `Name` y `Email`. Los 20 correos usan el dominio
    `example.com` (999 de 999) y son `nombre@example.com`. Aun así, conviene no exportar `Email` a `data/processed/m3/` ni a
    la app. La fuente no documenta si las personas son reales.

---

## 6. Opciones para definir «interacción» (sin elegir; `§A1.7`)

| | (i) solo Reviews | (ii) solo UserHistory | (iii) unión de pares | (iv) intersección |
|---|---|---|---|---|
| Pares distintos | 999 | 999 | 1 998 | **0** |
| Usuarios que aparecen | 624 | 642 | 858 | 0 |
| Destinos que aparecen | 651 | 638 | 866 | 0 |
| Densidad (a) maestras 999 × 1 000 | 0.001000 | 0.001000 | 0.002000 | 0 |
| Densidad (b) los que aparecen | 0.002459 | 0.002439 | 0.002689 | — |
| Por usuario: mediana / media / máx | 1 / 1.601 / 5 | 1 / 1.556 / 6 | 2 / 2.329 / 7 | — |
| Calificación disponible | `Rating` 1–5 | `ExperienceRating` 1–5 | dos columnas distintas, sin pares comunes para compararlas | — |
| Fecha disponible | no | `VisitDate` (3 valores) | solo en la mitad de los pares | — |
| Afinidad preferencia–tipo (obs. vs. azar 0.400) | 0.429 (p = 0.058) | 0.417 (p = 0.26) | 0.423 (p = 0.033) | — |

**Ventajas y riesgos (para decidir):**

- **(i) Reviews.** Ventaja: una sola semántica («reseñó», con calificación). Riesgos: el 57 % de los usuarios que aparecen
  tiene 1 sola interacción (355 de 624). No hay fecha, así que la partición tiene que ser por usuario.
- **(ii) UserHistory.** Ventaja: es la que más se parece a «historial» (el enunciado pide recomendar «a partir del historial»)
  y es la única con fecha. Riesgos: tiene aún más usuarios con 1 interacción (384 de 642) y su fecha no sirve para una
  partición temporal real (§7).
- **(iii) Unión.** Ventaja: duplica los pares, sube la mediana a 2 por usuario y deja 606 usuarios con ≥ 2 interacciones
  (derivado: 858 − 252). Riesgos: mezcla dos fuentes con calificaciones posiblemente distintas, sin pares comunes que
  permitan comprobar si son comparables. Si se usa como señal implícita (interactuó sí/no), la calificación se descarta o se
  trata aparte.
- **(iv) Intersección.** No es viable: está vacía.
- **Decisión transversal:** ¿el ítem es `DestinationID` (1 000) o el destino real por `Name` (5)? Con 5 ítems, Precision,
  Recall y NDCG@K con K ∈ {1, 3, 5, 10} pierden sentido (K = 5 recomienda el catálogo entero). Con 1 000, el modelo distingue
  ids que la fuente no permite diferenciar salvo por `Popularity`. La densidad al nivel de `Name` no se midió:
  `TODO(dato-faltante)` para la fase B si se considera esa opción.

---

## 7. Implicaciones para la partición

- **¿Hay fechas?** Solo `VisitDate`, solo en UserHistory, con 3 valores que dependen de `HistoryID mod 3` y en su mayoría
  posteriores a la creación de la versión 1 en Kaggle. Una partición «temporal» daría a lo sumo 2 puntos de corte (3 bloques de 333) y equivaldría
  a partir por el resto del id de fila (A3). Reviews no tiene fecha. Así que no hay una base real para una partición
  temporal, y la regla de la spec (§3.1: «si no, *leave-k-out* por usuario») apunta a *leave-k-out*.
- **Usuarios con pocas interacciones** (de los 999 maestros, contando como 0 a los que no aparecen):

| Opción | < 2 | < 3 | < 5 | Usuarios con ≥ 2 (derivado) | Usuarios con ≥ 3 (derivado) |
|---|---|---|---|---|---|
| (i) Reviews | 730 | 920 | 993 | 269 | 79 |
| (ii) UserHistory | 741 | 921 | 997 | 258 | 78 |
| (iii) Unión | 393 | 673 | 947 | 606 | 326 |

  Solo entre los que aparecen: (i) 355 / 545 / 618 de 624; (ii) 384 / 564 / 640 de 642; (iii) 252 / 532 / 806 de 858.
- **Consecuencia para *leave-one-out*:** solo los usuarios con ≥ 2 interacciones pueden dejar una para prueba y conservar al
  menos una en train. Si además se quiere una para validación, hacen falta ≥ 3. Con (i) o (ii), eso es menos de 80 usuarios;
  con (iii), 326. Los demás quedan solo en train y se reportan aparte (spec §3.1). El grupo «pocas interacciones» que pide el
  enunciado sería casi todo el conjunto.
- **Popularidad sin fuga:** calcularla solo con las interacciones de train (núcleo §5.7, `test_fuga_m3.py`).

---

## 8. Candidatos a hallazgo (A3)

**No hay candidatos sólidos.** A1 y A2 no inventaron columnas, significados ni citas. Todo número se reproduce con código
independiente, y ninguno afirmó «real» o «sintético» sin cita. Veredictos de las 63 afirmaciones numeradas: 59 correctas,
3 imprecisas (A1-22, A1-37 y A1-42: redondeos o cotas) y 1 inferencia no respaldada (A1-34). No hay ninguna incorrecta ni
no verificable. Detalle completo en `docs/investigacion/JJ-1_verificacion_A3.md`.

- **Candidato débil, sin numerar (A3 recomienda no contarlo; decide Andrés):** M3 / Matemáticas. A1 escribió que Gender,
  NumberOfAdults, NumberOfChildren y Preferences «son independientes entre sí (todos los p de χ² ≥ 0.20)». No rechazar H0 no
  demuestra independencia, y la potencia del χ² frente a una dependencia pequeña (w = 0.05) es de 0.21 a 0.35. Está redactado
  con la plantilla de 6 puntos en `JJ-1_verificacion_A3.md §4`. **No se agregó a `alucinaciones/registro.md`.**
- **Imprecisiones menores** (no son alucinaciones según la regla): A2 llamó «inconsistencia de tamaño» a lo que es el tamaño
  del .zip frente al de los CSV. La cita APA de A2 tenía el formato del título y el idioma mezclados (corregida en §1). A1
  dijo que la partición temporal daría «3 cortes» (son 2) y afirmó, sin medirlo, que «un modelo no puede aprender identidad de
  destino».
- **Verificaciones correctas** (documentables si faltan hallazgos): las de A3 §5. Incluyen la re-descarga idéntica de la
  fuente, las 10 citas literales y las ausencias comprobadas.
- M3 sigue **sin hallazgo genuino**. Los puntos calientes que quedan (spec §5: NDCG/Recall@K, el signo de BPR, «BCE ≡ BPR»,
  popularidad con fuga y referencias de NCF, BPR y Adam) son mejores fuentes de candidatos en JJ-3 a JJ-5.

---

## Pendiente para la fase B (después de que Juan José decida)
- Registrar M3 en `data/fuentes.md` (archivo, URL, fecha, SHA-256, tamaño, quién descargó, licencia contradictoria).
- `results/data/m3/eda/ficha.json` (núcleo §5.12) con la densidad y la escala de la opción elegida.
- Construir `data/processed/m3/` (núcleo §5.7) con la definición de interacción e ítem elegidas, sin `Email`.
