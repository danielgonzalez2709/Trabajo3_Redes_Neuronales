# Respuesta literal de A2 (investigador-fuentes, Sonnet) — JJ-1a — 2026-11-25

Prompt: `alucinaciones/prompts/JJ-1a-investigador-fuentes.md`. Copiado sin cambios del informe final del subagente.

---

# JJ-1a / A2 — Documentación de la fuente Kaggle (Travel Recommendation Dataset)

Fecha de consulta: 2026-11-25. Todo viene de endpoints públicos de `www.kaggle.com/api/v1/`, sin credenciales. Kaggle es la fuente primaria del conjunto. No usé páginas de terceros. No abrí los CSV de `data/raw/m3/`.

## 1. Archivo creado y endpoints
Archivo: `C:\Repositorios\Trabajo3_Redes_Neuronales\docs\investigacion\JJ-1_kaggle_metadata.json`. Es un objeto con la lista `respuestas` de 5 elementos. Cada uno trae `url`, `consultado_utc`, `status`, `sha256_cuerpo`, `cuerpo_crudo` y `cuerpo`. Verifiqué que el SHA-256 de `cuerpo_crudo` coincide con `sha256_cuerpo` en las 5. No hice commit ni modifiqué nada más. Los scripts temporales quedaron en el scratchpad.

| # | URL (prefijo `https://www.kaggle.com/api/v1/`) | Status | UTC | SHA-256 del cuerpo |
|---|---|---|---|---|
| 0 | `datasets/metadata/amanmehra23/travel-recommendation-dataset` | 200 | 2026-11-25T23:16:55Z | bb5d50608d20e6416319fe2cb0a094efafbb2892441c4e06fbc363c9c6923170 |
| 1 | `datasets/list/amanmehra23/travel-recommendation-dataset` | 200 | 2026-11-25T23:16:55Z | 6cde29d898d0fdb38d22610fc83461878d493d21a8aa8cb13fc89b6609156513 |
| 2 | `datasets/metadata/amanmehra23/travel-recommendation-dataset/` (con barra final) | 200 | 2026-11-25T23:16:55Z | bb5d5060…c9923170 (idéntico al #0) |
| 3 | `datasets/view/amanmehra23/travel-recommendation-dataset` | 200 | 2026-11-25T23:16:56Z | 186a1c5ccc4109b135bfdfc78a6e1657de3e5da95feb4a9b7e5fa065078fb58a |
| 4 | `datasets/list?search=travel-recommendation-dataset&user=amanmehra23` | 200 | 2026-11-25T23:16:56Z | a5b3836fea1aabfa3f0ff3517a259ca0cf681f9170b6809de2b7baee162860c9 |

Los endpoints #3 y #4 los añadí yo porque aportan autor, versión y fechas. El #2 es redundante con el #0.

## 2. Tabla de datos

| Dato | Fragmento literal | Campo JSON | Endpoint | Confianza |
|---|---|---|---|---|
| Título | "Travel Recommendation Dataset" | `info.title` (#0); `title` (#3, #4) | #0, #3, #4 | Alta |
| Título dentro de la descripción | "### Title: India Travel Recommender System Dataset" | `info.description` (#0) | #0 | Alta |
| Subtítulo | "" (vacío) | `info.subtitle` | #0 | Alta |
| Propietario (usuario) | "amanmehra23" | `info.ownerUser` (#0); `ownerRef` (#3, #4) | #0, #3, #4 | Alta |
| Autor / propietario (nombre) | "Aman Mehra" | `creatorName`, `ownerName` (#3, #4); `versions[0].creatorName` (#3) | #3, #4 | Alta |
| Ref / ID | "amanmehra23/travel-recommendation-dataset"; id 4345382 | `ref`, `id` (#3, #4); `info.datasetId` (#0) | #0, #3, #4 | Alta |
| URL | "https://www.kaggle.com/datasets/amanmehra23/travel-recommendation-dataset" | `url` (#4). En #3 `url` viene "" | #4 | Alta |
| Versión | 1 | `currentVersionNumber`; `versions[0].versionNumber` | #3, #4 | Alta |
| Notas de versión | "Initial release" | `versions[0].versionNotes` | #3 | Alta |
| Creación de la versión 1 | "2024-01-23T17:07:26.487Z" | `versions[0].creationDate` | #3 | Alta |
| Última actualización | "2024-01-23T17:07:26.487Z" | `lastUpdated` | #3, #4 | Alta |
| Fecha de publicación | No existe un campo propio. `versions[0].creationDate` es la fecha de creación de la versión 1. | — | — | Media: es una inferencia |
| Archivos | Ver lista abajo | `datasetFiles[]` (#1) | #1 | Alta |
| Tamaño total | 177696 bytes | `totalBytes` (#3) | #3 | Alta |
| Tamaño total (otro valor) | 34679 bytes | `totalBytes` (#4) | #4 | Ver observación 3 |
| Etiquetas | "travel" (ruta: "subject > people and society > business > travel") | `info.keywords` (#0); `tags[0].fullPath` (#3, #4) | #0, #3, #4 | Alta |
| Usabilidad | 0.5882352941176471 (#0); 0.5882353 (#3, #4) | `info.usabilityRating` / `usabilityRating` | #0, #3, #4 | Alta |
| Descargas / vistas / votos | 4014 / 18351 / 15 | `totalDownloads`, `totalViews`, `totalVotes` (#0); `downloadCount`, `viewCount`, `voteCount` (#3, #4) | #0, #3, #4 | Alta |
| Cuadernos (kernels) | 1 | `kernelCount` | #3, #4 | Alta |
| Frecuencia de actualización | "not specified" | `info.expectedUpdateFrequency` | #0 | Alta |
| Fuentes especificadas por el usuario | "" (`hasUserSpecifiedSources: false`) | `info.userSpecifiedSources` | #0 | Alta |
| DOI | La respuesta no trae ningún campo de DOI. | — | — | Alta (ausencia) |
| Colaboradores | `[]` | `info.collaborators` | #0 | Alta |

Archivos según #1 (`datasetFiles[]`; `creationDate` en el campo del mismo nombre; los tamaños suman 177696, igual que `totalBytes` de #3):
- "Expanded_Destinations.csv": `totalBytes` 60768, `creationDate` "2024-01-23T17:07:28.041Z".
- "Final_Updated_Expanded_Reviews.csv": `totalBytes` 33710, `creationDate` "2024-01-23T17:07:28.068Z".
- "Final_Updated_Expanded_UserHistory.csv": `totalBytes` 24683, `creationDate` "2024-01-23T17:07:27.95Z".
- "Final_Updated_Expanded_Users.csv": `totalBytes` 58535, `creationDate` "2024-01-23T17:07:28.103Z".

## 3. Descripción completa (`info.description`, #0; idéntica en `description` de #3)

```
### Title: India Travel Recommender System Dataset

### Description

**Context**  
Travel is a diverse and vibrant industry, and India, with its rich cultural heritage and varied landscapes, offers a myriad of experiences for travelers. The India Travel Recommender System Dataset is designed to facilitate the development of personalized travel recommendation systems. This dataset provides an extensive compilation of travel destinations across India, along with user profiles, reviews, and historical travel data. It's an invaluable resource for anyone looking to create AI-powered travel applications focused on the Indian subcontinent.

**Content**  
The dataset is divided into four primary components:

1. **Destinations**: Information about various travel destinations in India, including details like type of destination (beach, mountain, historical site, etc.), popularity, and best time to visit.

2. **Users**: Profiles of users including their preferences and demographic information. This dataset has been enriched with gender diversity and includes details on the number of adults and children for travel.

3. **Reviews**: User-generated reviews and ratings for the different destinations, offering insights into visitor experiences and satisfaction.

4. **User History**: Records of users' past travel experiences, including destinations visited and ratings provided.

Each of these components is presented in a separate CSV file, allowing for easy integration and manipulation in data processing and machine learning workflows.

**Acknowledgements**  
This dataset was generated for educational and research purposes and is intended to be used in hackathons, academic projects, and by AI enthusiasts aiming to enhance the travel experience through technology.

**Inspiration**  
The dataset is perfect for exploring a variety of questions and tasks, such as:
- Building a recommendation engine to suggest travel destinations based on user preferences.
- Analyzing travel trends in India.
- Understanding the relationship between user demographics and travel preferences.
- Sentiment analysis of travel destination reviews.
- Forecasting the popularity of travel destinations based on historical data.

We encourage Kaggle users to explore this dataset to uncover unique insights and develop innovative solutions in the realm of travel technology. Whether you're a data scientist, a student, or a travel tech enthusiast, this dataset offers a wealth of opportunities for exploration and creativity.

### Usage
This dataset is free to use for non-commercial purposes. For commercial use, please contact the dataset provider. Remember to cite the source when using this dataset in your projects.

### License
CC0: Public Domain - The dataset is in the public domain and can be used without restrictions.
```

## 4. Real o sintético
La fuente NO dice literalmente «sintético», «real», «simulated» ni «synthetic». Dice lo siguiente, todo en `info.description` (#0; mismo texto en `description` de #3):
- "This dataset was generated for educational and research purposes and is intended to be used in hackathons, academic projects, and by AI enthusiasts aiming to enhance the travel experience through technology." (sección Acknowledgements). La palabra clave es "generated". No dice con qué método ni si hay datos reales de base.
- "This dataset has been enriched with gender diversity and includes details on the number of adults and children for travel." (sección Users). Palabra clave: "enriched", sin decir cómo.
- "User-generated reviews and ratings for the different destinations" (sección Reviews). Esto afirma que las reseñas son de usuarios, pero no aclara si los usuarios son personas reales.
- Los nombres de los archivos contienen "Expanded" y "Final_Updated_Expanded" (`datasetFiles[].name`, #1). Sugieren una ampliación, pero la fuente no documenta cómo se hizo.
- Etiquetas (`info.keywords`): solo "travel". No hay etiquetas de tipo synthetic o real.
- No aparecen en la descripción: "synthetic", "simulated", "augmented", "sample", "scraped", "collected", "survey". `userSpecifiedSources` está vacío.

Conclusión: la fuente documenta que los datos fueron "generated" para fines educativos y que fueron "enriched" y "expanded" (esto último solo por los nombres de archivo). No documenta de forma explícita si los datos son reales o sintéticos. La frase exacta pedida, "La fuente no documenta si los datos son reales o sintéticos", es correcta en sentido estricto. La interpretación más natural es que los datos son generados o sintéticos, pero eso es inferencia y no cita. El informe debe separar lo literal ("generated for educational and research purposes") de la inferencia.

## 5. Licencia
Hay tres declaraciones y dos de ellas se contradicen:
- "MIT" en `info.licenses[0].name` (#0), `licenseName` y `licenseNameNullable` (#3, #4). Es el campo de metadatos formal de Kaggle.
- "CC0: Public Domain - The dataset is in the public domain and can be used without restrictions." en `info.description`, sección "### License".
- "This dataset is free to use for non-commercial purposes. For commercial use, please contact the dataset provider. Remember to cite the source when using this dataset in your projects." en `info.description`, sección "### Usage". Esta restringe el uso comercial, lo que no encaja ni con CC0 ni con MIT.

Sí se contradicen: MIT (campo formal) frente a CC0 (texto libre), y además "Usage" restringe el uso comercial, mientras que CC0 dice "without restrictions". Recomendación para citar: usar la licencia formal de Kaggle (MIT) y mencionar la contradicción en el blog. Para este trabajo académico no comercial no cambia el uso. Pide citar la fuente.

## 6. Columnas
La fuente no documenta ninguna columna. En #1, cada archivo trae `"columns": []` y `"description": ""` (`hasDescription: false`). En #3 `files` es `[]` y en #0 `data` es `[]`.
- Lo que sí hay son descripciones narrativas por archivo, en `info.description`:
  - Destinations: "Information about various travel destinations in India, including details like type of destination (beach, mountain, historical site, etc.), popularity, and best time to visit."
  - Users: "Profiles of users including their preferences and demographic information. ... includes details on the number of adults and children for travel."
  - Reviews: "User-generated reviews and ratings for the different destinations, offering insights into visitor experiences and satisfaction."
  - User History: "Records of users' past travel experiences, including destinations visited and ratings provided."
- La descripción no dice qué archivo corresponde a cuál componente. La correspondencia con los nombres de archivo es inferencia.
- Para toda columna concreta (nombre, tipo, escala de calificaciones, rango, unidades): **no documentado por la fuente**. Tampoco documenta la escala de las calificaciones, que el enunciado pide reportar. Debe medirse en los datos y declarar que no hay documentación.

## 7. Cita APA 7 propuesta
Mehra, A. (2024). *Travel Recommendation Dataset* (Versión 1) [Data set]. Kaggle. https://www.kaggle.com/datasets/amanmehra23/travel-recommendation-dataset

Origen de cada parte:
- Autor "Mehra, A.": `creatorName` / `ownerName` = "Aman Mehra" (#3, #4). El orden apellido-nombre es mi interpretación, porque la fuente da solo el nombre completo en un campo. Si se quiere evitar la interpretación, el usuario de Kaggle es "amanmehra23" (`ownerRef`). El enunciado del curso también nombra "Aman Mehra" (fuente secundaria).
- Año 2024: `versions[0].creationDate` y `lastUpdated` = "2024-01-23T17:07:26.487Z".
- Título: `title` = "Travel Recommendation Dataset".
- Versión 1: `currentVersionNumber` = 1.
- [Data set] y Kaggle: formato APA 7 estándar para conjuntos de datos alojados en Kaggle; Kaggle es la plataforma.
- URL: `url` (#4).
- Consultado el 2026-11-25. APA no lo exige para contenido estable, pero conviene anotarlo en el registro.
- DOI: la respuesta no trae uno. Si el profesor lo exige, `TODO(cita)`: se podría buscar en la pestaña Citation de la página, que se dibuja con JavaScript y no verifiqué.

## 8. Afirmaciones para verificar
[A2-1] El título del conjunto es "Travel Recommendation Dataset" — `info.title` (#0) / `title` (#3, #4)
[A2-2] El título dentro de la descripción es "India Travel Recommender System Dataset" — `info.description`, primera línea
[A2-3] El autor es "Aman Mehra", usuario "amanmehra23" — `creatorName`, `ownerRef` (#3, #4)
[A2-4] La ref es "amanmehra23/travel-recommendation-dataset", id 4345382 — `ref`, `id` (#3, #4)
[A2-5] Hay una sola versión (1), notas "Initial release", creada el "2024-01-23T17:07:26.487Z" — `versions[0]` (#3)
[A2-6] Última actualización "2024-01-23T17:07:26.487Z" — `lastUpdated` (#3, #4)
[A2-7] Cuatro archivos CSV: Expanded_Destinations.csv (60768 B), Final_Updated_Expanded_Reviews.csv (33710 B), Final_Updated_Expanded_UserHistory.csv (24683 B), Final_Updated_Expanded_Users.csv (58535 B) — `datasetFiles[]` (#1)
[A2-8] La suma de los archivos (177696 B) coincide con `totalBytes` de #3 — #1, #3
[A2-9] Ningún archivo trae descripción de columnas (`columns: []`, `description: ""`) — `datasetFiles[]` (#1)
[A2-10] La descripción dice: "This dataset was generated for educational and research purposes..." — `info.description` (#0)
[A2-11] La descripción dice: "This dataset has been enriched with gender diversity and includes details on the number of adults and children for travel." — `info.description`
[A2-12] La descripción dice: "User-generated reviews and ratings for the different destinations" — `info.description`
[A2-13] La palabra "synthetic" no aparece en ninguna de las 5 respuestas — búsqueda en todos los `cuerpo_crudo`; ver nota al final
[A2-14] La licencia formal es "MIT" — `info.licenses[0].name` (#0), `licenseName` (#3, #4)
[A2-15] El texto libre declara "CC0: Public Domain - The dataset is in the public domain and can be used without restrictions." — `info.description`
[A2-16] El texto libre declara "This dataset is free to use for non-commercial purposes. For commercial use, please contact the dataset provider." — `info.description`
[A2-17] La única etiqueta es "travel" — `info.keywords` (#0), `tags` (#3, #4)
[A2-18] usabilityRating = 0.5882352941176471; descargas 4014, vistas 18351, votos 15, kernelCount 1 — #0, #3, #4
[A2-19] No hay DOI en ninguna respuesta — ausencia en las 5
[A2-20] `expectedUpdateFrequency` = "not specified"; `userSpecifiedSources` = "" — `info` (#0)

Nota sobre A2-13: no ejecuté la búsqueda de "synthetic" como paso programático separado. La afirmación se apoya en la lectura completa de los cuerpos que imprimí. El verificador debe hacer un `grep -i` sobre el JSON guardado.

## 9. Candidatos a hallazgo y observaciones
1. **CANDIDATO A HALLAZGO (fuente vs. suposición de una IA):** la fuente no dice "synthetic" ni "real". La frase literal es "This dataset was generated for educational and research purposes" (`info.description`). Si alguna IA afirmó «datos sintéticos según Kaggle» o «datos reales de usuarios», no tiene respaldo literal. Si una IA describió la fuente como "real", eso contradice "generated" y "enriched". No tengo evidencia de lo que haya afirmado una IA en concreto, así que es un candidato condicionado a que alguien lo haya afirmado.
2. **Contradicción de licencias dentro de la misma página:** "MIT" (campo formal) frente a "CC0: Public Domain" y a "free to use for non-commercial purposes" (texto libre). Es un hallazgo de datos para el blog, no una alucinación.
3. **Inconsistencia de tamaño dentro de Kaggle:** `totalBytes` es 177696 en `datasets/view` (#3) y 34679 en `datasets/list?search=` (#4). Los archivos de #1 suman 177696.
4. **Inconsistencia de ruta:** #3 devuelve `url: ""` y `creatorUrl: ""`, mientras que #4 trae la URL correcta. No afecta a la cita.
5. **El enunciado exige reportar la escala de las calificaciones, y la fuente no la documenta.** Hay que medirla en los datos y declarar que la fuente no la documenta.
6. **Nombres de archivo "Expanded" y "Final_Updated_Expanded":** la fuente no documenta de qué conjunto original parten ni qué se expandió. Esto afecta la discusión de qué implica el origen para las conclusiones. Conviene que el medidor de datos mire si las cifras sugieren generación automática, pero eso es medición de datos y no fuente.
7. Mi primer intento con `datasets/meta/...`, una URL mal escrita por mí, devolvió 404 con HTML. No quedó guardado en el archivo. Los endpoints correctos del prompt responden 200.
