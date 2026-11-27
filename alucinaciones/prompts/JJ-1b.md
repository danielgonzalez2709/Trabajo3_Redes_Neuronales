# Prompt JJ-1b — sesión orquestadora (Opus) — 2026-11-25 — orquesta: Juan José

Prompt literal recibido por la sesión principal (copiado sin cambios):

```text
Tarea JJ-1, fase B (construcción de los datos de M3 y cierre de JJ-1). Te dirige Juan José; rama dev/juanjose.

ANTES DE NADA
1. Guarda este prompt LITERAL en alucinaciones/prompts/JJ-1b.md antes de despachar cualquier subagente, y cada prompt a un subagente en alucinaciones/prompts/JJ-1b-<agente>.md.
2. Relee docs/investigacion/JJ-1_fuentes_m3.md (tu entregable de la fase A) y docs/investigacion/JJ-1_verificacion_A3.md.
3. Mismas reglas de la fase A: NO commits, NI push, NI PR (los hace Juan José en GitHub Desktop). Siempre .venv\Scripts\python. Prohibido inventar. Prueba primero, luego código. Sin internet en el código de src/.

DECISIONES DE JUAN JOSÉ (25-nov) — regístralas en docs/spec/partes/juanjose.md §3.1 como [DECIDIDO, Juan José, 25-nov], con la justificación medida en la fase A (cifras del informe):
D1. Interacción = UNIÓN de Reviews y UserHistory (no comparten pares; 1 998 interacciones de 858 usuarios), tratada como retroalimentación implícita (sí/no). Rating y ExperienceRating se conservan como atributo `calificacion` (1–5) con su `origen`, pero el objetivo de los modelos es la interacción, no la calificación.
D2. Destino = los 1 000 DestinationID (catálogo de la fuente). Name, State, Type, BestTimeToVisit y Popularity son VARIABLES DE CONTENIDO del destino. Se documenta como problema de calidad que los 1 000 ids son 5 lugares repetidos 200 veces cada uno, y se agrega `lugar` (los 5 lugares) para un análisis complementario "acierto por lugar" en la evaluación.
D3. Partición (la implementa JJ-3, NO ahora): por usuario, no por tiempo (VisitDate solo tiene 3 valores ligados al número de fila y es posterior a la publicación: no es una fecha real; queda solo descriptiva). Prueba = 1 interacción al azar de cada usuario con ≥ 2; validación = 1 más de cada usuario con ≥ 3; el resto entrenamiento; usuarios con 1 interacción solo en entrenamiento; semilla fija. Así el grupo "pocas interacciones" existe en prueba.
D4. Real o sintético: se cita literal la frase de la fuente ("generated for educational and research purposes", "enriched with gender diversity"), se aclara que la fuente no usa la palabra "synthetic" y se listan las señales medidas. Conclusión: datos generados; las conclusiones valen para el método, no para el comportamiento real de turistas.
D5. Licencia: se cita la MIT del campo formal de Kaggle y se documenta la contradicción (CC0 y "no comercial" en la descripción) para la sección de ética.
D6. Privacidad: Name y Email de los usuarios NO pasan a data/processed/ ni a results/. ReviewText tampoco pasa a lo procesado (son 3 textos sin relación con el destino; se describe en el diccionario).
D7. El candidato débil de A1 ("las variables son independientes") no se registra en la cacería.

QUÉ CONSTRUIR (implementador, Sonnet; prueba primero)
B1. tests/test_datos_m3.py con datos de prueba PEQUEÑOS y claramente ficticios en tests/fixtures/m3/ (mismas columnas que los 4 CSV reales; la CI no tiene data/raw). Debe probar al menos: unión sin pares repetidos y sin intersección perdida; todo usuario/destino de las interacciones existe en las tablas maestras; Name/Email/ReviewText ausentes de las salidas; escala y densidad calculadas correctamente contra un conteo a mano del fixture; preferencias separadas bien ("Beaches, Historical" → dos opciones); la ficha pasa src/comun/eda.validar_ficha; error claro si falta un archivo o si un SHA-256 no coincide con el de la config; ejecución determinista (dos corridas → mismos bytes).
B2. configs/m3/datos.yaml (comentado como configs/m1/datos.yaml): rutas de entrada en data/raw/m3/, SHA-256 esperado de cada CSV y del .zip (los medidos en la fase A), metadatos de la fuente (nombre, autor, url, fecha_descarga 2026-11-25, cita APA, licencia), carpetas de salida. Sin semillas (no hay azar en JJ-1).
B3. src/m3_recomendacion/datos.py con main(cfg) (lo llama `run.py m3-datos`), que:
   - verifica los SHA-256 contra la config;
   - escribe data/processed/m3/destinos.parquet (destino_id, nombre, lugar, estado, tipo, mejor_epoca, popularidad), usuarios.parquet (usuario_id, preferencias como texto normalizado + una columna booleana pref_<opcion> por cada opción medida, genero, n_adultos, n_ninos) e interacciones.parquet (usuario_id, destino_id, origen ∈ {resena, historial}, id_origen, calificacion, fecha_visita solo descriptiva) — núcleo §5.7; la columna `split` la agrega JJ-3, no la crees;
   - escribe results/data/m3/eda/ficha.json con src/comun/eda.escribir_ficha (claves de §5.12; n_registros = interacciones de la unión; periodo = texto que explique que no hay fechas reales; bajo `conteos`: usuarios, destinos, lugares, interacciones por origen y unión, escala medida de cada calificación, densidad por origen y de la unión, usuarios por número de interacciones (0,1,2,3,4,5+), y un bloque real_o_sintetico con la cita literal, las señales medidas y la conclusión de D4; licencia con la contradicción de D5);
   - escribe results/data/m3/eda/calidad.csv (src/comun/eda.tabla_calidad por tabla, con una columna `tabla`) y results/data/m3/eda/diccionario.json: por columna original, nombre procesado, tipo, y significado SOLO si la fuente lo documenta; si no, "no documentado por la fuente" (cita la descripción de la fuente a nivel de archivo cuando exista, literal); incluye las inconsistencias detectadas (p. ej. la fuente menciona "mountain" y no existe ese tipo; 1 000 ids = 5 lugares; VisitDate).
   - Imprime un resumen corto y termina en < 10 s.
B4. data/fuentes.md: sección "## M3 — Recomendación de destinos" con el formato de la de M1 (conjunto, URL, licencia con la contradicción, fecha 2026-11-25, descargó Juan José a mano con su cuenta de Kaggle, archivos con tamaño y SHA-256, cómo regenerar: descargar el .zip a data/raw/m3/ y correr el comando). No toques la sección de M1.
B5. blog/references.bib: entrada @dataset del conjunto de Kaggle con los datos verificados de la fase A (mismo estilo que las de M1; clave apellido+año).
B6. src/m3_recomendacion/README.md: actualiza configs, datos y comando de m3-datos.
B7. Las evidencias en alucinaciones/evidencias/JJ-1a/redescarga_A3/: elimina SOLO los textos completos de las licencias MIT y CC0 (no se versionan); conserva lo demás y ajusta cualquier referencia a ellos.

REVISIÓN (en este orden; si alguno falla, devuelve al implementador con los hallazgos)
R1. revisor-spec (Sonnet): ¿cumple el núcleo §5.7, §5.12 y el Anexo M3 "Datos" (usuarios, destinos, interacciones, escala, densidad, variables de usuarios y destinos, real o sintético y qué implica)? ¿Cumple D1–D7?
R2. revisor-calidad (Haiku): claridad y pruebas.
R3. cazador-alucinaciones (Opus): cada cifra de ficha.json, diccionario.json, fuentes.md y references.bib contra los archivos y docs/investigacion/JJ-1_kaggle_metadata.json. Errores de un subagente → candidato con evidencia, sin numerar en registro.md.

CIERRE
- Corre y pega la salida real de: .venv\Scripts\python run.py m3-datos --config configs/m3/datos.yaml (dos veces, y comprueba que los archivos no cambian) y .venv\Scripts\python -m pytest -q -m "not lento" (todo en verde, incluidas las pruebas de los demás).
- Marca JJ-1 ✅ en docs/spec/PLAN.md y en la tabla de docs/spec/partes/juanjose.md, y que el documentador actualice docs/MEMORIA.md (estado, decisiones vigentes de M3 y una línea arriba en la bitácora), sin borrar nada de otros.
- Muéstrame: lista de archivos creados/modificados, salida de los comandos, veredicto de R1–R3, candidatos a la cacería y cualquier punto que deba decidir Juan José. Luego DETENTE.
```
