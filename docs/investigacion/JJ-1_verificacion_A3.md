# JJ-1 fase A — A3: verificación adversarial de A1 y A2

Agente: cazador-alucinaciones (Opus), 2026-11-25, rama `dev/juanjose`; lo dirige Juan José. Prompt literal:
`alucinaciones/prompts/JJ-1a-cazador-alucinaciones.md`.

**Evidencia.** Todo veredicto sale de código que ejecuté:

- Mi script propio: `alucinaciones/evidencias/JJ-1a/verificar_A3.py`. Su salida es
  `alucinaciones/evidencias/JJ-1a/verificar_A3_salida.txt`, con SHA-256
  `72613f122a9b1b80853a41f24c5f994ad5aa60018a27becf81fb0a9258fa28f0`. Dos corridas dan el mismo hash.
- Las secciones de mi salida se citan como `§V1`…`§V10`, `§W1`…`§W4` y `§R`.
- El script no importa ni copia `JJ-1_inventario.py`. Recalcula todo desde los CSV con pandas, `csv` y `zipfile`, en memoria.
- Comando: `.venv\Scripts\python -I alucinaciones/evidencias/JJ-1a/verificar_A3.py`. Lo corro desde la raíz y sin internet.
- Volví a consultar los 4 endpoints públicos distintos de Kaggle (2026-11-25, 23:26 UTC). Las respuestas están en
  `alucinaciones/evidencias/JJ-1a/redescarga_A3/` (`r0..r3.body` e `indice.txt`). Los textos oficiales de las licencias MIT y CC0 no se versionan: se
  consultan en https://opensource.org/license/mit y https://creativecommons.org/publicdomain/zero/1.0/ (consultas del
  2026-11-25 registradas en `indice_licencias.txt`).
- No modifiqué nada de A1 ni de A2. El SHA-256 de `JJ-1_inventario_salida.txt` sigue en `d3d258d7…88cb93`.

**Resumen.**

- Mi script hace 140 comprobaciones automáticas: 137 coinciden y 3 difieren. Las 3 diferencias son redondeos o cotas
  imprecisas de A1, sin efecto en las conclusiones.
- No hay ninguna columna inventada, ningún significado inventado, ningún número que no se reproduzca y ninguna cita no
  literal.
- La salida de A1 se reproduce bit a bit.
- El contenido que guardó A2 es idéntico byte a byte a lo que Kaggle sirve hoy.
- No hay candidatos sólidos a hallazgo. Hay un candidato débil, que **no** recomiendo contar (§4).

## 1. Tabla de verificación

Clases: **C** correcta · **I** imprecisa · **X** incorrecta · **NV** no verificable · **INR** inferencia no respaldada.

### 1.1 Afirmaciones de A1 (curador-datos)

| id | Afirmación (resumida) | Veredicto | Valor verificado | Evidencia |
|---|---|---|---|---|
| A1-1 | 5 archivos; zip de 34679 B, sha `117e3135…d004d` | C | 5 archivos; 34679 B; el hash empieza y termina igual | §V1 |
| A1-2 | Los 4 CSV son idénticos a los miembros del zip; CRC sin errores | C | 4/4 idénticos; `testzip()` = None | §V1 |
| A1-3 | UTF-8 estricto, sin BOM, sin no-ASCII, LF; `csv` = pandas; campos constantes | C | Se cumple en los 4 archivos (0 bytes >127, 0 `\r`) | §V1 |
| A1-4 | Filas: D 1000, R 999, H 999, U 999 | C | Igual | §V2 |
| A1-5 | UserID 1..999 y DestinationID 1..1000 sin huecos | C | Igual | §V2 |
| A1-6 | 0 faltantes, 0 vacías, 0 duplicados; la primera columna es un contador 1..n | C | Igual en los 4 archivos | §V2 |
| A1-7 | Users sin UserID: 657 sobrantes y 342 combinaciones; las demás, 0 | C | (657, 342); D/R/H = 0 | §V2 |
| A1-8 | Integridad referencial total | C | 0 filas fuera de las maestras | §V2 |
| A1-9 | Rating 1..5, media 3.023, frecuencias 198/199/185/216/201 | C | Igual | §V3 |
| A1-10 | ExperienceRating 1..5, media 2.905, frecuencias 206/228/201/183/181 | C | Igual | §V3 |
| A1-11 | Popularity: 1000 distintos, mín 7.5045, máx 9.4998, mediana 8.4965 | C | Igual | §V3 |
| A1-12 | R: 999 pares, 0 repetidos, 624 u, 651 d. H: 999 pares, 0 repetidos, 642 u, 638 d | C | Igual | §V4 |
| A1-13 | Densidad (a) 0.001000; (b) 0.002459 y 0.002439 | C | Igual (fórmula pares/(u×d)) | §V4 |
| A1-14 | Usuarios ausentes 375/357; destinos ausentes 349/362 | C | Igual | §V4 |
| A1-15 | Por usuario: R med 1, media 1.601, máx 5, 355/190/58/15/6; H med 1, media 1.556, máx 6, 384/180/60/16/2 | C | Igual | §V4 |
| A1-16 | Por destino: R med 1, máx 5, 396/178/62/14/1; H máx 6, 383/177/56/17/5 | C | Igual | §V4 |
| A1-17 | Pares comunes 0; solo R 999; solo H 999; unión 1998 | C | Igual | §V5 |
| A1-18 | 408 usuarios comunes (216/234); 423 destinos comunes (228/215) | C | Igual | §V5 |
| A1-19 | Opciones (i)–(iv); unión: 1998/858/866, densidades 0.002000 y 0.002689, mediana 2, <2/<3/<5 = 252/532/806 | C | Igual | §V5 |
| A1-20 | Contando los ceros: (i) 730/920/993; (ii) 741/921/997; (iii) 393/673/947 | C | Igual | §V5 |
| A1-21 | Una sola columna de fecha, `VisitDate`: 3 valores × 333, de 2024-01-01 a 2024-03-20 | C | Igual. Es la única columna de texto que parsea como fecha | §V6 |
| A1-22 | `VisitDate` es una función exacta de `HistoryID mod 3`; «el resto de k son 0.333 o 1.000 en múltiplos de 3» | **I** | k mínimo = 3 (correcto). Para los k que no son múltiplo de 3, la pureza va de 0.333 a **0.364** (k=52) y solo redondea a 0.333 con k=1 y k=37 | §V6 |
| A1-23 | 195 de 642 usuarios con >1 fecha (172 con 2, 23 con 3; 447 con 1) | C | Igual | §V6 |
| A1-24 | `BestTimeToVisit` no parsea (0/1000); 5 valores; función de `DestinationID mod 5` | C | Igual | §V6 |
| A1-25 | Reviews no tiene columna de fecha | C | Igual | §V6 |
| A1-26 | 5 nombres de destino, 200 ids cada uno, atributos constantes, 5 combinaciones | C | Igual | §V7 |
| A1-27 | Name/State/Type/BestTimeToVisit dependen de `id mod 5`; ciclo Taj Mahal…Leh Ladakh; Popularity media de 8.49 a 8.55 | C | Igual | §V7 |
| A1-28 | 20 nombres de usuario (38 a 64 ids); 20 pares (Name, Email); dominio `example.com` ×999 | C | Igual | §V7 |
| A1-29 | Correo = nombre en minúsculas + `@example.com` (999/999) | C | 999 | §V7 |
| A1-30 | Un solo Gender por nombre | C | 0 nombres con más de uno | §V7 |
| A1-31 | `Preferences` depende de `UserID mod 3`; las demás columnas no muestran periodo con k ≤ 60 | C | Igual | §V7 |
| A1-32 | 3 combinaciones × 333; 2 opciones por fila; Historical 666 y las demás 333 | C | Igual | §V7 |
| A1-33 | Categorías y valores de las variables de contenido | C | Male 503 / Female 496; adultos {1,2}; niños {0,1,2} | §V7, salida de A1 §A1.11 |
| A1-34 | «Gender, NumberOfAdults, NumberOfChildren y Preferences **son independientes** entre sí (todos los p ≥ 0.20)» | **INR** | Los p son correctos (mínimo 0.2024). La conclusión no se sigue: no rechazar H0 no prueba independencia, y la potencia frente a w=0.05 es de solo 0.21–0.35 | §V7 (potencia) |
| A1-35 | `ReviewText`: 3 textos × 333; función de `ReviewID mod 3` | C | Igual | §V8 |
| A1-36 | Texto sin asociación con la calificación (p=0.5465), con el destino (p=0.8836) ni con las preferencias (p=0.2971); «el texto no es coherente con el destino» | C | Los p coinciden. «Loved the beaches!» aparece en los 5 destinos (57–80 por destino), así que la conclusión está respaldada | §V8 |
| A1-37 | Uniformidad exacta en 7 columnas; las demás con razón de 1.014 a 1.684 y **p de 0.12 a 0.83** | **I** | 7 columnas y razones correctas. El p máximo es 0.8247, que redondea a **0.82** | §V9 |
| A1-38 | Rating χ²=2.44 (p=0.656) y ExperienceRating χ²=7.36 (p=0.118); sin periodo | C | Igual | §V9 |
| A1-39 | Índice de dispersión de 0.918 a 1.029; ceros 349–375 frente a 367–368 esperados | C | Igual (fórmula comprobada, §2) | §V9 |
| A1-40 | Afinidad entre preferencia y tipo: obs, esp, z y p para (i), (ii) y (iii) | C | Igual. Control con binomial exacta: p = 0.061 / 0.272 / 0.0337 | §V9 |
| A1-41 | χ² de Preferences × Type: (i) p=0.171, V=0.076; (ii) 0.026, 0.093; (iii) 0.019, 0.068 | C | Igual | §V9 |
| A1-42 | Reviews: p de χ² ≥ 0.21 y **p de Kruskal-Wallis ≥ 0.26**; H: p de Preferences×ER = 0.0074 (V 0.102), KW 0.18 | **I** | Todo coincide salvo la cota: el p mínimo de KW es **0.2576** (Gender), que es menor que 0.26 | §V9 |
| A1-43 | Spearman: ρ = 0.044, 0.028, −0.041 y 0.022; todos los p > 0.16 | C | Igual (p de 0.167 a 0.485) | §V9 |

Otras afirmaciones del informe de A1 (fuera de la lista numerada):

| Afirmación | Veredicto | Evidencia |
|---|---|---|
| «salida determinista: dos ejecuciones dan el mismo SHA-256» | C | §R: dos corridas del script original dan `d3d258d7…`, igual que el archivo guardado |
| «14 secciones, unas 680 líneas» | C | §R: 14 secciones `## A1.` y 682 líneas |
| «141 usuarios maestros no aparecen en ninguno de los dos archivos» | C | §V5 |
| «No usé internet» | NV | El script no abre ninguna conexión (lectura del código); el resto no se puede comprobar |

### 1.2 Afirmaciones de A2 (investigador-fuentes)

Primero comprobé la integridad (§W1):

- Las 5 respuestas cumplen `sha256(cuerpo_crudo) == sha256_cuerpo` y `json.loads(cuerpo_crudo) == cuerpo`, con status 200.
- La #2 es idéntica a la #0.
- **Mi re-descarga independiente de los 4 endpoints distintos es idéntica byte a byte a lo que guardó A2.** Esto descarta que
  el JSON se haya fabricado o editado.

| id | Afirmación (resumida) | Veredicto | Valor verificado | Evidencia (campo JSON) |
|---|---|---|---|---|
| A2-1 | Título «Travel Recommendation Dataset» | C | Igual en #0, #3 y #4 | `info.title`, `title` |
| A2-2 | Título en la descripción: «India Travel Recommender System Dataset» | C | Primera línea literal | `info.description` |
| A2-3 | Autor «Aman Mehra», usuario «amanmehra23» | C | Igual en 5 campos de nombre y 3 de usuario | `creatorName`, `ownerName`, `versions[0].creatorName`, `ownerRef`, `info.ownerUser` |
| A2-4 | Ref `amanmehra23/travel-recommendation-dataset`, id 4345382 | C | Igual | `ref`, `id`, `info.datasetId` |
| A2-5 | Una sola versión (1), «Initial release», creada el 2024-01-23T17:07:26.487Z | C | `versions` de #3 tiene 1 elemento. #4 trae `versions: []` | `versions[0]` (#3) |
| A2-6 | `lastUpdated` 2024-01-23T17:07:26.487Z | C | Igual en #3 y #4 | `lastUpdated` |
| A2-7 | 4 CSV con 60768 / 33710 / 24683 / 58535 B y sus fechas | C | Igual. **Además coinciden con los tamaños locales y con los del zip** | `datasetFiles[]` (#1); §W4 |
| A2-8 | La suma (177696) = `totalBytes` de #3 | C | Igual | §W2 |
| A2-9 | Ningún archivo describe sus columnas | C | `columns: []`, `description: ""`, `hasDescription: false` en los 4; `files: []` (#3); `data: []` (#0) | §W2 |
| A2-10 | «This dataset was generated for educational and research purposes…» | C | Literal en el campo, en el crudo y en #3 | `info.description` |
| A2-11 | «This dataset has been enriched with gender diversity…» | C | Literal | `info.description` |
| A2-12 | «User-generated reviews and ratings for the different destinations» | C | Literal | `info.description` |
| A2-13 | «synthetic» no aparece en ninguna de las 5 respuestas | C | 0 apariciones (subcadena, sin distinguir mayúsculas). A2 admitió no haberlo buscado con código; ahora está comprobado | §W3 |
| A2-14 | Licencia formal «MIT» | C | 5 campos «MIT»; una sola licencia en #0 | `info.licenses[0].name`, `licenseName`, `licenseNameNullable` |
| A2-15 | Texto libre «CC0: Public Domain - …without restrictions.» | C | Literal | `info.description` |
| A2-16 | Texto libre «free to use for non-commercial purposes…» | C | Literal | `info.description` |
| A2-17 | Única etiqueta: «travel» | C | `keywords = ["travel"]`; 1 tag con `fullPath` literal | `info.keywords`, `tags` |
| A2-18 | Usabilidad 0.5882352941176471 y 0.5882353; 4014 / 18351 / 15; kernelCount 1 | C | Igual en #0, #3 y #4 | §W2 |
| A2-19 | No hay DOI | C | 0 apariciones de «doi», 0 del patrón `10.NNNN/` y 0 claves con «doi» | §W3 |
| A2-20 | `expectedUpdateFrequency` «not specified»; `userSpecifiedSources` «» | C | Igual; `hasUserSpecifiedSources: false` | §W2 |

Otras afirmaciones de A2 (tablas y secciones 3 a 9):

| Afirmación | Veredicto | Evidencia |
|---|---|---|
| La descripción completa de su §3 es idéntica a `info.description` y a la de #3 | C | §W2: igualdad exacta, incluidos los dos espacios finales de «**Context**  » |
| Fragmentos de su §6 (Destinations, Users, Reviews, User History) y de Usage | C | §W2: literales. En el crudo, el apóstrofo de «users'» va escapado como `'` |
| No aparecen synthetic, simulated, augmented, sample, scraped, collected ni survey en la descripción; «real» no aparece | C | §W3: 0 apariciones. «real» solo aparece como subcadena de «realm» |
| «expanded» solo en los nombres de archivo | C | §W3: 0 apariciones en la descripción; 8 como subcadena en los crudos (nombres de archivo) |
| No hay un campo de fecha de publicación | C | §W3: ninguna clave contiene «publi». Las claves de fecha son `creationDate` y `lastUpdated` |
| Subtítulo vacío, colaboradores `[]`, `url` y `creatorUrl` vacíos en #3, URL correcta en #4 | C | §W2. Nota: `creatorUrl` de #4 vale «amanmehra23», que no es una URL |
| La descripción no dice qué archivo corresponde a cada componente | C | Solo dice «Each of these components is presented in a separate CSV file» (§W3); no nombra los archivos |
| «Usage» restringe el uso comercial, y eso no encaja ni con CC0 ni con MIT | C | Los textos oficiales permiten el uso comercial. MIT: «to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell» (opensource.org/license/mit). CC0: «…commercial purposes, all without asking permission» (creativecommons.org/publicdomain/zero/1.0/). Consultas registradas en `redescarga_A3/indice_licencias.txt` (los textos completos no se versionan) |
| Obs. 3: «inconsistencia de tamaño»: 177696 (#3) frente a 34679 (#4) | **I** | Los dos valores son literales, pero la etiqueta de «inconsistencia» se explica de otro modo: **34679 B es exactamente el tamaño del `archive.zip` descargado** (§W4). El endpoint de búsqueda reporta el tamaño comprimido y `view` la suma sin comprimir. Lo de «comprimido» es una inferencia: la API no documenta el campo, pero la coincidencia es exacta |
| Cita APA 7: «Mehra, A. (2024). *Travel Recommendation Dataset* (Versión 1) [Data set]. Kaggle. URL» | **I** (formato) | Autor, año, versión, editorial y URL salen de los campos correctos. Pero (a) APA 7 escribe el título de la obra en minúscula de oración. El ejemplo oficial de conjunto de datos es «*Content analysis of undergraduate psychology textbooks* (ICPSR 36966; Version V1) [Data set]». La página oficial apastyle.apa.org bloqueó la descarga directa (Incapsula); el ejemplo se tomó del resultado de búsqueda que la cita. Lo correcto sería «*Travel recommendation dataset*». (b) Mezcla de idiomas: «(Versión 1)» con «[Data set]». La inversión «Mehra, A.» la marcó el propio A2 como interpretación y es razonable |
| Conclusión de real o sintético: «no documenta explícitamente…; la interpretación más natural es generados o sintéticos, pero eso es inferencia» | C | Inferencia bien marcada y separada de la cita literal. Se apoya en «generated» (×2 en la descripción: «User-generated» y «was generated»), en «enriched» y en los nombres de archivo |
| «Recomendación para citar: usar la licencia formal de Kaggle (MIT)» | INR (decisión) | Es una recomendación razonable, pero le toca decidirla a Juan José (§3) |
| «APA no exige fecha de consulta para contenido estable» | NV aquí | No lo contrasté con la fuente oficial (página bloqueada). No afecta a ningún dato |
| Primer intento con `datasets/meta/…` (404) | NV | No quedó guardado; no afecta a nada |

### 1.3 Recuento de veredictos

| Clase | A1 (43) | A2 (20) | Total (63) |
|---|---|---|---|
| Correcta | 39 | 20 | 59 |
| Imprecisa | 3 (A1-22, A1-37, A1-42) | 0 | 3 |
| Inferencia no respaldada | 1 (A1-34) | 0 | 1 |
| Incorrecta | 0 | 0 | 0 |
| No verificable | 0 | 0 | 0 |

Afirmaciones adicionales fuera de la lista numerada:

- A1: 3 correctas y 1 no verificable.
- A2: 9 correctas, 2 imprecisas (la obs. 3 y el formato de la cita APA), 1 inferencia o decisión y 2 no verificables.
- Afirmaciones interpretativas de A1 en §3 (sin contar [A1-34]): 3 respaldadas, 2 razonables pero inferidas, 1 imprecisa
  y 1 no respaldada.

## 2. Errores en el script de A1 (`docs/investigacion/JJ-1_inventario.py`)

Reproducibilidad (§R):

- Ejecuté el script original dos veces con `runpy`, interceptando `Path.write_text` para que no sobrescribiera nada.
- Las dos corridas producen exactamente la salida guardada (SHA-256 `d3d258d725d8…88cb93`).
- SHA-256 del script: `e21e00a1088c…aba680`.

**No encontré errores de implementación que cambien un número reportado.** Revisé las fórmulas una por una:

- **Densidad:** `pares distintos / (nu × nd)` con los dos denominadores pedidos. Correcta (`densidad()`, l. 439).
- **Conteos «< k»:** separa bien los usuarios que aparecen de los que tienen 0 (reindexa sobre la maestra con
  `fill_value=0`, l. 539). Mis cifras coinciden con los dos casos.
- **Índice de dispersión:** varianza poblacional (ddof=0) entre la media, sobre todos los ids de la maestra (con ceros).
  Compara contra `1 − 1/N` y los ceros contra `N(1−1/N)^m`. Las dos referencias son exactas para una multinomial de m
  bolas en N celdas: E[(c_i − m/N)²] = m(1/N)(1−1/N), y la media vale m/N.
- **Tasa esperada de coincidencia entre preferencia y tipo:** media sobre los pares de P(tipo ∈ preferencias), con las
  cuotas del catálogo maestro. Cada tipo vale 0.2 y cada usuario tiene 2 tipos, así que la tasa es 0.4. El z usa
  `Σp(1−p)`. Mi implementación independiente da los mismos valores, y la binomial exacta no cambia ninguna conclusión
  (§V9).
- **χ² de bondad de ajuste:** E = n/k, con gl = k−1. Correcto, y concuerda con `scipy.stats.chisquare`.

Observaciones de método, menores, que no cambian ninguna afirmación de A1:

1. **Fila «Users.Preferences (opciones separadas)» de A1.13a.** Da χ²=222, p=6.959e-47, pero no es una prueba válida: las
   1998 opciones no son independientes (2 por fila) y la razón 2:1 de «Historical» la fija la composición de las 3
   combinaciones (§V9). A1 no cita ese p y explica la razón 2:1, pero el p está impreso en la tabla. **No debe copiarse al
   blog como prueba.**
2. **χ² sin corrección de Yates**, sin declararlo. Solo afecta a la única tabla 2×2 (Gender × NumberOfAdults): p=0.5464
   sin corrección frente a 0.5893 con ella (§V7). La conclusión no cambia.
3. **Comparaciones múltiples.** Entre A1.10 y A1.13 hay más de 60 valores p (51 de χ², Kruskal-Wallis, Spearman y z, más 15
   filas de bondad de ajuste; conteo con grep sobre la salida). Los p «significativos» (0.0074, 0.019, 0.026 y 0.033) no
   resisten una corrección de Bonferroni (0.05/60 ≈ 0.0008). Esto refuerza la lectura de A1 de que las desviaciones son
   pequeñas; conviene decirlo en el blog.
4. La detección de periodos usa pureza exacta y k ≤ 60, como se declara. Una dependencia con k > 60, o no exacta, no se
   detectaría. Es una limitación declarada, no un error.

## 3. Afirmaciones interpretativas o no pedidas

| Quién | Afirmación | Juicio |
|---|---|---|
| A1 §3.1 | Estructura demasiado regular; «sin concluir sintético» | **Respaldada** por las mediciones (§V6–§V9) y bien acotada |
| A1 §3.2 | «Un mismo nombre en 200 ids significa que `DestinationID` no identifica un lugar distinto» | **Razonable pero inferida.** Que sea el mismo lugar es una inferencia a partir de Name, State, Type y BestTimeToVisit idénticos; la fuente no documenta qué es `DestinationID` |
| A1 §3.2 | «un modelo no puede aprender identidad de destino con 200 ids que comparten todos sus atributos salvo Popularity» | **No respaldada (afirmación de modelado no medida).** Un modelo de solo contenido no los distingue más que por Popularity. Uno con *embedding* por id sí puede aprender diferencias a partir de las interacciones, aunque con 0 a 6 interacciones por id la señal es pobre. A1 tenía orden de no decidir modelado |
| A1 §3.4 | «Casi todas las calificaciones son compatibles con ruido uniforme… no hay señal fuerte que aprender» | **Razonable pero inferida.** La primera parte está medida (marginales y asociaciones). «No hay señal que aprender» es una predicción que solo se confirma modelando |
| A1 §3.5 | «Una partición por tiempo solo permitiría 3 cortes» | **Imprecisa.** Con 3 fechas hay a lo sumo **2 puntos de corte** (3 bloques). Además, como `VisitDate` es función exacta de `HistoryID mod 3` (§V10), una partición «temporal» equivale a partir por el resto del id de fila, y solo existe en UserHistory |
| A1 §3.7 | El emparejamiento `Beaches→Beach` es un supuesto del análisis | **Respaldada y bien marcada** (impreso en la salida) |
| A1 [A1-34] | «son independientes» | **No respaldada** (ver §1.1 y §4) |
| A1 [A1-36] | «El texto no es coherente con el destino» | **Respaldada** (χ² p=0.88; «Incredible monument!» aparece 60 veces sobre Goa Beaches) |
| A2 §4 | Real o sintético: «no documenta explícitamente»; lo natural es «generados», pero es inferencia | **Respaldada y bien separada** de lo literal |
| A2 §5 | Las licencias se contradicen; se recomienda citar MIT | Lo de la contradicción está **respaldado** por los textos oficiales. La recomendación es **razonable pero inferida**, y la decide Juan José |
| A2 §6 | La correspondencia entre archivo y componente es inferencia | **Correcta.** La fuente no nombra los archivos |
| A2 §7 | Formato de la cita APA 7 | **Imprecisa en el formato** (minúscula de oración e idioma). Las partes sí salen de sus campos |
| A2 obs. 3 | «Inconsistencia de tamaño dentro de Kaggle» | **Imprecisa:** 34679 = tamaño del zip (§W4) |

**Observaciones nuevas de A3 para el blog.** Son hallazgos de datos, no alucinaciones:

- **666 de 999 filas de UserHistory (las de 2024-02-15 y 2024-03-20) tienen `VisitDate` posterior a la creación de la
  versión 1 en Kaggle**, el 2024-01-23 (`versions[0].creationDate`) (§V10). Es otra señal de datos generados: el conjunto
  registra «visitas» que aún no habían ocurrido cuando se publicó.
- Los miembros del zip tienen fecha 2024-01-23 17:07:28 (hora local del zip, sin zona). Es coherente con `creationDate`
  (17:07:27.95Z a 17:07:28.103Z) (§W4).
- Tipo de destino por nombre: Taj Mahal = Historical, Goa Beaches = Beach, Jaipur City = City, Kerala Backwaters = Nature y
  Leh Ladakh = Adventure (§V10).

## 4. Candidatos a hallazgo

**No hay candidatos sólidos.** Ningún subagente inventó columnas, significados ni citas. Ninguno afirmó «real» o
«sintético» sin cita, y todo número se reproduce. Lo que encontré son imprecisiones menores de redondeo o de redacción
(A1-22, A1-37, A1-42 y A1 §3.5) y un formato de cita mejorable. Según la regla («un error de redacción menor o una
inferencia razonable bien marcada no es una alucinación»), no las propongo.

Dejo redactado **un candidato débil**, solo para que Juan José y Andrés decidan con todo a la vista. **Recomiendo no
contarlo**, salvo que el equipo decida admitir imprecisiones conceptuales de bajo impacto. Si se cuenta, hay que declararlo
como «impreciso», no como «incorrecto».

### Candidato débil (sin numerar) — «no significativo» presentado como «independientes»

- **Módulo / categoría / quién lo encontró:** M3 / Matemáticas (interpretación de una prueba estadística) / Juan José, con
  el subagente cazador-alucinaciones (A3).
- **1. Prompt literal:** [`alucinaciones/prompts/JJ-1a-curador-datos.md`](../../alucinaciones/prompts/JJ-1a-curador-datos.md).
  Su punto 13 pide «Señales de datos generados (solo lo medido, sin concluir…)» y su regla dice «No afirmes si los datos
  son reales o sintéticos: solo reporta las señales medidas».
- **2. Respuesta relevante** (`alucinaciones/evidencias/JJ-1a/respuesta-curador-datos.md`): «[A1-34] Gender,
  NumberOfAdults, NumberOfChildren y Preferences son independientes entre sí (todos los p de χ² ≥ 0.20) — A1.10».
- **3. Cómo se sospechó:** un p alto solo indica que no se rechaza H0. La afirmación convierte una no-significancia en una
  propiedad de los datos.
- **4. Evidencia** (`alucinaciones/evidencias/JJ-1a/verificar_A3.py`, salida §V7):
  - Los p son correctos (0.2024 a 0.8244; V de Cramér de 0.019 a 0.057).
  - Pero la potencia del χ² con n=999 y α=0.05 frente a una dependencia pequeña (w de Cohen = 0.05) es de solo 0.352 (gl=1),
    0.273 (gl=2) y 0.207 (gl=4).
  - La prueba no habría detectado una dependencia de ese tamaño en la mayoría de los casos, así que «son independientes»
    no se sigue de la medición.
- **5. Corrección:** «No se rechaza la independencia entre Gender, NumberOfAdults, NumberOfChildren y Preferences (χ², p ≥
  0.20; V de Cramér ≤ 0.057). La prueba tiene poca potencia frente a dependencias pequeñas (w=0.05: 0.21–0.35)».
- **6. Lección:** cuando se pida una prueba, exigir en el prompt la redacción «se rechaza / no se rechaza H0» junto con el
  tamaño del efecto. La verificación que lo habría evitado es calcular la potencia de la prueba antes de concluir ausencia
  de efecto.
- **Estado:** candidato débil; no recomendado. Lo decide Andrés como consolidador.

**Cobertura de la cacería.** Esta verificación no cambia la cobertura:

- Sigue el H-01 (candidato, Común / Código).
- M3 sigue sin hallazgo genuino. Los puntos calientes de M3 que siguen abiertos (juanjose.md §5) son: NDCG y Recall@K,
  el signo de BPR, la «BCE con negativos ≡ BPR», la popularidad con fuga y las referencias de NCF, BPR y Adam. Son mejores
  fuentes de candidatos que esta fase.

## 5. Verificaciones que salieron correctas

Se pueden documentar como verificaciones hechas (el enunciado lo permite si faltan hallazgos):

1. **Inventario de A1:** 39 de 43 afirmaciones correctas. Todos los conteos reproducen con código independiente:
   usuarios, destinos, interacciones, escala 1–5, densidades, solapamiento 0, opciones de interacción, fechas, periodos
   `mod 3` y `mod 5`, y pruebas χ², Kruskal-Wallis y Spearman. Las 4 restantes tienen bien los números y solo fallan en
   una cota o en la redacción.
2. **Reproducibilidad de A1:** la salida guardada se regenera bit a bit (dos corridas, el mismo SHA-256).
3. **Integridad de la fuente de A2:** los 5 hashes son correctos y la re-descarga independiente es idéntica byte a byte.
4. **Citas literales de A2:** las 10 que comprobé están literales en el campo indicado y en el crudo. La descripción
   completa es idéntica a la fuente.
5. **Ausencias de A2** («synthetic», DOI, columnas documentadas, fecha de publicación): confirmadas con búsqueda
   programática sin distinguir mayúsculas.
6. **Tamaños y fechas de Kaggle frente a los archivos locales:** los 4 tamaños coinciden con los archivos locales y con el
   zip. El `totalBytes` de #4 coincide con el tamaño del zip, y las fechas del zip son coherentes con `creationDate`.
7. **Contradicción de licencias:** confirmada con los textos oficiales de MIT y CC0, que permiten el uso comercial, frente a
   «Usage», que lo restringe.
