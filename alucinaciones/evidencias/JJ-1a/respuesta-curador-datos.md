# Respuesta literal de A1 (curador-datos, Sonnet) — JJ-1a — 2026-11-25

Prompt: `alucinaciones/prompts/JJ-1a-curador-datos.md`. Copiado sin cambios del informe final del subagente.

---

## Informe A1 (curador-datos, JJ-1 fase A)

El script corre sin errores y su salida es determinista: dos ejecuciones dan el mismo SHA-256. No hice commit ni push, no instalé nada y no toqué nada fuera de los dos archivos de abajo. No usé internet.

### 1. Archivos y comando
- `C:\Repositorios\Trabajo3_Redes_Neuronales\docs\investigacion\JJ-1_inventario.py`
- `C:\Repositorios\Trabajo3_Redes_Neuronales\docs\investigacion\JJ-1_inventario_salida.txt` (UTF-8, 14 secciones `## A1.1` a `## A1.14`, unas 680 líneas)
- Comando, desde la raíz: `.venv\Scripts\python -I docs/investigacion/JJ-1_inventario.py`
- No hay aleatoriedad ni semilla. Usa solo la biblioteca estándar, pandas, numpy y scipy (que está instalado). El .zip se lee en memoria con `zipfile`.
- El git status también muestra `alucinaciones/evidencias/JJ-1a/` y `docs/investigacion/JJ-1_kaggle_metadata.json`. Los creó otro agente, no yo.

### 2. Afirmaciones medidas
Formato: `[A1-n] afirmación — valor — sección`.

**Archivos**
- [A1-1] Hay 5 archivos en `data/raw/m3/`: `archive.zip` (34679 B, sha256 `117e3135…d004d`) y 4 CSV. Los SHA-256 completos están en la salida — A1.1
- [A1-2] Los 4 CSV sueltos son idénticos byte a byte a sus miembros del .zip. El CRC del .zip está sin errores — A1.1
- [A1-3] Los CSV son UTF-8 estricto, sin BOM, sin caracteres no ASCII y con fin de línea LF. El conteo de filas con `csv` coincide con el de pandas, y todas las filas tienen el mismo número de campos — A1.1

**Tamaños y estructura**
- [A1-4] Filas de datos: Destinations 1000, Reviews 999, UserHistory 999, Users 999 — A1.1, A1.2
- [A1-5] Usuarios (maestra) 999, con UserID 1..999 sin huecos. Destinos (maestra) 1000, con DestinationID 1..1000 sin huecos — A1.2, A1.3
- [A1-6] No hay faltantes, cadenas vacías ni duplicados exactos en ningún archivo. La primera columna de cada archivo (los 4 ids de fila o maestros) es un contador 1..n en orden — A1.2
- [A1-7] Users, ignorando UserID, tiene 657 filas duplicadas y solo 342 combinaciones distintas. Las demás tablas no tienen duplicados al ignorar su contador — A1.2
- [A1-8] La integridad referencial es total. Todos los UserID y DestinationID de Reviews y UserHistory existen en las maestras (0 filas y 0 ids sin maestro) — A1.3

**Calificaciones**
- [A1-9] `Rating` (Reviews) va de 1 a 5, con 5 valores distintos y media 3.023. Frecuencias: 1=198, 2=199, 3=185, 4=216, 5=201 — A1.4
- [A1-10] `ExperienceRating` (UserHistory) también va de 1 a 5, con media 2.905. Frecuencias: 1=206, 2=228, 3=201, 4=183, 5=181 — A1.4
- [A1-11] `Popularity` (Destinations) es decimal continua, con 1000 valores distintos, mín 7.5045, máx 9.4998 y mediana 8.4965 — A1.4

**Interacciones y densidad**
- [A1-12] Reviews tiene 999 pares (usuario, destino) distintos, 0 repetidos, 624 usuarios y 651 destinos. UserHistory tiene 999 pares distintos, 0 repetidos, 642 usuarios y 638 destinos — A1.5
- [A1-13] Densidad con denominador (a), maestras 999×1000: 0.001000 (0.1000 %) en ambos archivos. Con denominador (b), los que aparecen: Reviews 0.002459 y UserHistory 0.002439 — A1.5
- [A1-14] Los usuarios maestros que no aparecen son 375 en Reviews y 357 en UserHistory. Los destinos maestros que no aparecen son 349 y 362 — A1.5
- [A1-15] Interacciones por usuario, solo los que aparecen. Reviews: mediana 1, media 1.601, máx 5, con 1/2/3/4/≥5 = 355/190/58/15/6. UserHistory: mediana 1, media 1.556, máx 6, con 384/180/60/16/2 — A1.5
- [A1-16] Interacciones por destino, solo los que aparecen. Reviews: mediana 1, máx 5, con 396/178/62/14/1. UserHistory: máx 6, con 383/177/56/17/5 — A1.5

**Solapamiento y opciones de interacción**
- [A1-17] Los pares comunes entre Reviews y UserHistory son 0. Hay 999 pares solo en Reviews, 999 solo en UserHistory y 1998 en la unión. No hay calificaciones que comparar — A1.6
- [A1-18] Sí hay usuarios y destinos en común. 408 usuarios aparecen en ambos archivos (216 solo en Reviews, 234 solo en UserHistory) y 423 destinos (228 y 215) — A1.6
- [A1-19] Opciones de interacción, medidas sin elegir:
  - (i) solo Reviews: 999 pares, 624 usuarios, 651 destinos.
  - (ii) solo UserHistory: 999 pares, 642 usuarios, 638 destinos.
  - (iii) unión: 1998 pares, 858 usuarios, 866 destinos. Densidad (a) 0.002000 y (b) 0.002689. Mediana de 2 pares por usuario, con 252, 532 y 806 usuarios con menos de 2, 3 y 5.
  - (iv) intersección: 0 pares, por lo que queda vacía — A1.7
- [A1-20] Contando como 0 a los usuarios maestros que no aparecen, tendrían menos de 2, 3 y 5 interacciones: (i) 730/920/993; (ii) 741/921/997; (iii) 393/673/947, de 999 — A1.7

**Fechas**
- [A1-21] Hay una sola columna de fecha, `UserHistory.VisitDate`. Parsea 999 de 999 como AAAA-MM-DD, con 3 valores distintos: 2024-01-01, 2024-02-15 y 2024-03-20, 333 filas cada uno. El rango es 2024-01-01 a 2024-03-20 — A1.8
- [A1-22] `VisitDate` es una función exacta de `HistoryID mod 3` (pureza 1.000 con k=3; el resto de k son 0.333 o 1.000 en múltiplos de 3) — A1.8
- [A1-23] 195 de 642 usuarios tienen interacciones en más de una fecha distinta. Con 2 fechas son 172 y con 3 son 23. Los otros 447 tienen una sola — A1.8
- [A1-24] `BestTimeToVisit` aparece como candidata por su nombre, pero no parsea como fecha (0 de 1000). Tiene 5 valores y es función exacta de `DestinationID mod 5` — A1.8
- [A1-25] Reviews no tiene ninguna columna de fecha — A1.8

**Destinos y usuarios**
- [A1-26] Los destinos tienen 5 nombres distintos para 1000 ids. Cada nombre se repite en 200 ids. Los otros atributos (State, Type, BestTimeToVisit) no cambian dentro de un nombre. Solo hay 5 combinaciones nombre+atributos — A1.9
- [A1-27] Name, State, Type y BestTimeToVisit de destinos son una función exacta de `DestinationID mod 5`. El ciclo es Taj Mahal, Goa Beaches, Jaipur City, Kerala Backwaters, Leh Ladakh. La `Popularity` media por nombre va de 8.49 a 8.55 — A1.9
- [A1-28] Los usuarios tienen 20 nombres distintos para 999 ids (38 a 64 ids por nombre). Las combinaciones (Name, Email) distintas son 20. El único dominio de correo es `example.com` (999) — A1.10
- [A1-29] En los usuarios, el correo es exactamente el nombre en minúsculas + `@example.com` en 999 de 999 filas — A1.10
- [A1-30] Cada nombre de usuario tiene un único valor de Gender (0 de 20 nombres con más de uno) — A1.10
- [A1-31] En los usuarios, `Preferences` es función exacta de `UserID mod 3`. Name, Email, Gender, NumberOfAdults y NumberOfChildren no muestran periodicidad (k ≤ 60) — A1.10
- [A1-32] `Preferences` tiene 3 combinaciones distintas con 333 filas cada una, y siempre 2 opciones por fila. Las 5 opciones sueltas son Historical (666), Beaches (333), Nature (333), Adventure (333) y City (333) — A1.11
- [A1-33] Variables de contenido de usuarios: Name (20 categorías), Email (20), Preferences (3), Gender (2: Male 503 y Female 496), NumberOfAdults (2: valores 1 y 2) y NumberOfChildren (3: valores 0, 1 y 2). Las de destinos: Name, State, Type y BestTimeToVisit (5 categorías cada una, 200 filas c/u) y Popularity (continua) — A1.11
- [A1-34] Gender, NumberOfAdults, NumberOfChildren y Preferences son independientes entre sí (todos los p de χ² ≥ 0.20) — A1.10

**Textos**
- [A1-35] `ReviewText` tiene 3 textos distintos con 333 filas cada uno. Es función exacta de `ReviewID mod 3` — A1.12, A1.13c
- [A1-36] `ReviewText` no se asocia con la calificación (χ² p=0.5465, V=0.059), con el destino reseñado (p=0.8836, V=0.043) ni con las preferencias del usuario (p=0.2971). El texto no es coherente con el destino. Por ejemplo, «Loved the beaches!» aparece sobre los 5 destinos casi por igual — A1.12

**Señales de datos generados (solo medidas)**
- [A1-37] Uniformidad exacta (razón máx/mín = 1.000) en Destinations.Name, State, Type y BestTimeToVisit (200 cada una), ReviewText, VisitDate y Users.Preferences (333 cada una). Las demás columnas categóricas tienen razones de 1.014 a 1.684 y p de 0.12 a 0.83, sin rechazar la uniforme. La excepción es la tabla de opciones sueltas de `Preferences`, que da 2:1 (666 contra 333) por la forma de las 3 combinaciones — A1.13a
- [A1-38] Las calificaciones son compatibles con la uniforme: Rating χ²=2.44 (gl 4, p=0.656) y ExperienceRating χ²=7.36 (gl 4, p=0.118). Ninguna de las dos sigue un patrón periódico respecto a su id de fila — A1.13a, A1.13c
- [A1-39] El índice de dispersión de las interacciones por usuario y por destino está entre 0.918 y 1.029, y los ceros observados (349 a 375) están cerca de los esperados por asignación uniforme al azar (367 a 368). La distribución de interacciones es compatible con asignar usuario y destino al azar — A1.13b
- [A1-40] Afinidad entre las preferencias y el tipo de destino. Emparejamiento explícito, impreso en la salida y marcado como supuesto del análisis: `{'Beaches': 'Beach'}`; el resto por igualdad exacta.

  | Opción | Observada | Esperada al azar | z | p |
  |---|---|---|---|---|
  | (i) solo Reviews | 0.4294 | 0.4000 | 1.90 | 0.058 |
  | (ii) solo UserHistory | 0.4174 | 0.4000 | 1.12 | 0.26 |
  | (iii) unión | 0.4234 | 0.4000 | 2.14 | 0.033 |

  La fórmula es la misma para cada opción. La esperada es la media de P(tipo ∈ preferencias) sobre los mismos pares, con el catálogo maestro (cada tipo vale 0.200). Solo (iii) cruza el 0.05, con un efecto pequeño — A1.13d
- [A1-41] χ² de Preferences × tipo de destino: (i) p=0.171, V=0.076; (ii) p=0.026, V=0.093; (iii) p=0.019, V=0.068 — A1.13d
- [A1-42] La calificación casi no se asocia con tipo de destino, género ni tamaño del grupo. En Reviews todos los p son ≥ 0.21 (χ²) y ≥ 0.26 (Kruskal-Wallis). En UserHistory el χ² de Preferences × ExperienceRating da p=0.0074 (V=0.102), pero su Kruskal-Wallis da p=0.18 y el resto es no significativo — A1.13e
- [A1-43] La Popularity del destino no se asocia con la calificación (Spearman ρ=0.044 con Rating y ρ=0.028 con ExperienceRating) ni con el número de interacciones del destino (ρ=-0.041 y ρ=0.022, todos con p>0.16) — A1.13e

### 3. Problemas de calidad e inconsistencias
1. El conjunto tiene una estructura demasiado regular, y varias columnas son función exacta del id de fila módulo k (A1-22, A1-24, A1-27, A1-31, A1-35). Los 1000 destinos son solo 5 destinos repetidos con distinto id y `Popularity` distinta. Los 999 usuarios son 342 combinaciones distintas. Solo reporto lo medido, sin concluir «sintético».
2. Un mismo nombre de destino en 200 ids significa que `DestinationID` no identifica un lugar distinto. Esto afecta al modelado: un modelo no puede aprender identidad de destino con 200 ids que comparten todos sus atributos salvo `Popularity`.
3. Reviews y UserHistory no comparten ningún par (usuario, destino). La matriz es muy poco densa (0.1 % con las maestras, 0.2 a 0.3 % con los que aparecen). La unión da mediana 2 por usuario, y 141 usuarios maestros no aparecen en ninguno de los dos archivos.
4. Casi todas las calificaciones son compatibles con ruido uniforme. Las únicas desviaciones del azar son pequeñas (A1-40, A1-41). Esto es un riesgo para los supuestos de la tarea, porque no hay señal fuerte que aprender.
5. `VisitDate` tiene solo 3 valores y no es una fecha continua. Una partición por tiempo (el caso previsto en la spec 3.1) solo permitiría 3 cortes, y el 33 % de las filas comparte cada fecha. Esto lo decide Juan José, no yo.
6. Nombres de columna con apariencia de fecha que no lo son: `BestTimeToVisit` (valores como `Nov-Feb`).
7. Las etiquetas de preferencias y los tipos de destino usan vocabularios distintos (`Beaches` frente a `Beach`). El emparejamiento está marcado como supuesto del análisis, no como significado de la fuente.
8. No hay inconsistencias entre archivos en tipos ni en codificación, ni filas mal partidas.

Candidatos a hallazgo de la cacería: ninguno confirmado. Lo que sí queda como señal para el blog es la estructura periódica. Si una IA describió este conjunto como «datos reales» o con destinos y nombres variados, eso contradice [A1-26] y [A1-27]. Para registrarlo hace falta el prompt literal guardado.

### 4. Lo que no pude medir (`TODO(dato-faltante)`)
- Si los datos son reales o sintéticos según la fuente. Esto requiere la página y la documentación de Kaggle, que no están en los archivos locales. Lo verifica el investigador-fuentes.
- El significado de cada columna (Popularity, Rating frente a ExperienceRating, BestTimeToVisit, NumberOfAdults y NumberOfChildren, etc.). Tampoco hay diccionario local, y no lo describo por orden. Si alguna etiqueta no estuviera en la documentación de Kaggle, habría que escalarlo al humano.
- La fecha de descarga y quién descargó están en tu prompt (2026-11-25, Juan José). El script no puede medirlas y no escribí `data/fuentes.md` ni `ficha.json`, porque la tarea lo prohibía.
- `Kruskal-Wallis` y `Spearman` se calcularon con scipy. Sin scipy quedarían como `TODO(dato-faltante)`, pero aquí no aplica porque scipy está instalado.
