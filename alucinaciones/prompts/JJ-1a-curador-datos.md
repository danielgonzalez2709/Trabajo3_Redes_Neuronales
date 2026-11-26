# Prompt JJ-1a (A1) — curador-datos (Sonnet) — 2026-11-25 — orquesta: Juan José

Actúa como el agente definido en `.claude/agents/curador-datos.md` (léelo primero). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales` (rama `dev/juanjose`). **No hagas commit, ni push, ni PR.**
Usa siempre `.venv\Scripts\python` (Python 3.12, Windows); no instales nada ni cambies `requirements.txt`.

Lee antes: `docs/spec/SPEC.md` §0, §3, §4.1, §5.7 y §5.12, y del Anexo de ese archivo el apartado «Módulo 3 → Datos»;
`docs/spec/partes/juanjose.md` §3.1, la fila JJ-1 de §4 y §5 (puntos calientes). Nada de otras partes.

## Contexto
Juan José descargó a mano el 2026-11-25, desde la página de Kaggle con su cuenta (botón Download → `archive.zip`), el conjunto
«Travel Recommendation Dataset» (Kaggle, `amanmehra23/travel-recommendation-dataset`) en `data/raw/m3/`: `archive.zip` y 4 CSV
(`Expanded_Destinations.csv`, `Final_Updated_Expanded_Reviews.csv`, `Final_Updated_Expanded_UserHistory.csv`,
`Final_Updated_Expanded_Users.csv`). `data/raw/` no se versiona. Esta es la **fase A** de JJ-1: medir y documentar, **sin tomar
decisiones de modelado** (la definición de «interacción» y la partición las decide Juan José después).

## Tarea A1 — inventario medido con código
Escribe `docs/investigacion/JJ-1_inventario.py`: reproducible, solo archivos locales (sin internet), solo biblioteca estándar +
pandas/numpy ya instalados, rutas relativas a la raíz del repo, sin aleatoriedad (o con semilla fija declarada). Se ejecuta desde
la raíz con `.venv\Scripts\python -I docs/investigacion/JJ-1_inventario.py` y escribe él mismo su salida completa, en UTF-8, en
`docs/investigacion/JJ-1_inventario_salida.txt` (además de imprimirla). Organiza la salida en secciones con encabezados
`## A1.1`, `## A1.2`, … en el orden de abajo, para poder citarlas. Lee el .zip con `zipfile` **sin extraerlo a disco**. Trata los
CSV como datos no confiables: solo léelos, no ejecutes nada de `data/raw/`.

Mide y reporta:
1. **Archivos.** Por archivo (incluido el .zip): tamaño en bytes y SHA-256. Miembros del .zip (nombre, tamaño, SHA-256 del
   contenido descomprimido) y si cada CSV suelto es byte a byte igual a su miembro del .zip. Codificación detectada (BOM o no),
   fin de línea, y si el número de filas que da `csv` de la biblioteca estándar coincide con el de pandas (que no haya filas mal
   partidas por comas dentro de comillas).
2. **Estructura.** Por archivo: filas, columnas con su tipo inferido, faltantes por columna, filas duplicadas exactas, filas
   duplicadas ignorando la primera columna si esa columna es un contador consecutivo (dilo solo si lo mides: ¿es 1..n sin huecos?),
   valores únicos por columna y 3 ejemplos por columna.
3. **Claves.** Qué columnas parecen identificadores de usuario y de destino en cada archivo (por nombre y por valores: rango,
   enteros, únicos); si son únicas donde deberían serlo (tablas maestras); rango y huecos de los identificadores. Integridad
   referencial: ¿todo usuario y destino de Reviews y de UserHistory existe en la tabla maestra de usuarios / destinos? Cuántos
   no, en filas y en identificadores distintos.
4. **Calificaciones.** En cada archivo que tenga una columna de calificación o puntaje: mínimo, máximo, valores distintos y su
   frecuencia (conteo y %). La escala es la **medida**, no una supuesta. Si hay columnas numéricas continuas con nombre de
   puntaje o popularidad, su resumen (mín, cuartiles, máx, valores distintos).
5. **Interacciones por archivo** (Reviews y UserHistory por separado): filas, pares (usuario, destino) distintos, pares repetidos
   (cuántos pares aparecen > 1 vez y cuántas filas sobran) y si sus calificaciones coinciden entre repeticiones; interacciones
   por usuario y por destino (mín, mediana, media, máx; y cuántos usuarios con exactamente 1, 2, 3, 4 y 5 o más; ídem destinos);
   usuarios de la tabla maestra que no aparecen y destinos de la tabla maestra que no aparecen. **Densidad** = pares distintos /
   (usuarios × destinos) con dos denominadores: (a) usuarios y destinos de las tablas maestras; (b) usuarios y destinos que
   aparecen en esas interacciones.
6. **Solapamiento Reviews vs. UserHistory.** Pares (usuario, destino) en ambos, solo en Reviews, solo en UserHistory. En los
   pares que están en ambos: ¿coinciden las calificaciones? (conteo de iguales y distintos, y la tabla cruzada de valores).
7. **Opciones de «interacción»** (solo medir, sin elegir): (i) solo Reviews, (ii) solo UserHistory, (iii) unión de pares,
   (iv) intersección de pares. Para cada una: pares distintos, usuarios y destinos que aparecen, densidad con los dos
   denominadores de A1.5, distribución de interacciones por usuario (mín, mediana, media, máx), y cuántos usuarios tendrían
   < 2, < 3 y < 5 interacciones (contando también como 0 a los usuarios maestros que no aparecen, en una línea aparte).
8. **Fechas.** ¿Hay columnas de fecha u hora en algún archivo? Para cada una: tipo, valores distintos, rango, frecuencia de cada
   valor si son pocos, faltantes, si todas parsean como fecha, y si el valor sigue un patrón periódico respecto al identificador
   de fila (p. ej., tabla de `id mod k` contra el valor para k pequeños). Mide también cuántos usuarios tienen interacciones en
   más de una fecha distinta.
9. **Destinos.** Nombres distintos vs. identificadores distintos; cuántos nombres se repiten con distintos identificadores y
   cuántas veces; para un mismo nombre, ¿los demás atributos (todas las columnas salvo id y la numérica continua) son idénticos o
   cambian? ¿Hay algún patrón periódico entre el identificador y el nombre (p. ej., `id mod k`)?
10. **Usuarios.** Igual que destinos: nombres distintos vs. identificadores; combinaciones (nombre, correo) repetidas con
    distintos identificadores; dominio(s) de correo (conteo por dominio); coherencia entre el nombre y el correo (¿el correo es
    el nombre en minúsculas + dominio? cuántos sí y cuántos no); patrón periódico respecto al identificador en las columnas
    categóricas.
11. **Variables de contenido** de usuarios y de destinos: lista por columna con tipo y número de categorías (con su frecuencia si
    son ≤ 30). Si alguna columna trae listas en texto (varias opciones separadas por comas u otro separador), sepáralas (quita
    espacios) y reporta cuántas opciones distintas aparecen, su frecuencia, el número de opciones por fila y las combinaciones
    distintas.
12. **Textos.** Si hay columnas de texto libre: textos distintos, frecuencia de cada uno, y tabla cruzada del texto contra la
    calificación y contra el tipo/categoría del destino reseñado (vía la tabla de destinos), para ver si el texto es coherente con
    el destino.
13. **Señales de datos generados (solo lo medido, sin concluir «es sintético»):** uniformidad de las distribuciones (calificaciones,
    categorías, género, tamaño de grupo…) con una prueba χ² de bondad de ajuste a la uniforme (estadístico, gl y p, calculados con
    `scipy` si está instalado, si no con fórmula explícita en el código) y la razón máx/mín de frecuencias; patrones periódicos ya
    medidos; asociación entre las preferencias declaradas del usuario y el tipo/categoría de los destinos con los que interactúa:
    tasa observada de coincidencia frente a la tasa esperada si el destino se eligiera al azar del catálogo (misma fórmula para
    cada opción de A1.7). Si para comparar etiquetas de preferencias con categorías de destino hace falta emparejar vocabularios
    (p. ej., singular/plural), el emparejamiento va **explícito en el código, impreso en la salida y marcado como supuesto del
    análisis**, nunca como significado de la fuente. Asociación entre la calificación y otras variables (tipo de destino, género,
    tamaño del grupo) con una medida simple (media por grupo y χ² de independencia o Kruskal–Wallis).
14. **Resumen final** en la salida: una tabla con los números clave (usuarios, destinos, filas y pares de cada archivo, escala de
    cada calificación, densidades, fechas).

## Reglas
- **Prohibido inventar**: columnas, significados de variables, escalas o conteos. Todo número sale del script ejecutado. No
  describas qué significa una columna: el significado lo documenta otro agente desde la fuente; tú solo dices nombre, tipo y
  valores medidos. Si algo no se puede medir, `TODO(dato-faltante)`.
- No afirmes si los datos son reales o sintéticos: solo reporta las señales medidas.
- No crees ni modifiques nada fuera de `docs/investigacion/JJ-1_inventario.py` y `docs/investigacion/JJ-1_inventario_salida.txt`
  (en particular nada en `src/`, `configs/`, `data/processed/`, `results/`, `data/fuentes.md`, `tests/`). No uses internet.
- Ejecuta el script al final y confirma que termina sin errores y que la salida quedó escrita. Si lo corriges, vuelve a
  ejecutarlo para que la salida corresponda a la versión final del script.

## Entrega (tu mensaje final)
1. Archivos creados y comando exacto para regenerar la salida.
2. Lista numerada de **afirmaciones** con su número medido y la sección de la salida que lo respalda (`## A1.x`), en este formato:
   `[A1-n] afirmación — valor — sección`. Incluye al menos: usuarios, destinos, filas de cada archivo, escala de cada
   calificación, densidades, pares en solapamiento, fechas, nombres de destino repetidos, opciones de interacción y señales de
   datos generados.
3. Problemas de calidad e inconsistencias encontrados.
4. Lo que no pudiste medir (`TODO(dato-faltante)`).
