# Prompt JJ-1a — sesión orquestadora (Opus) — 2026-11-25 — orquesta: Juan José

Prompt literal recibido por la sesión principal (copiado sin cambios):

```text
Tarea JJ-1, fase A (inventario de los datos de M3). Te dirige Juan José; rama dev/juanjose.

ANTES DE NADA
1. Guarda este prompt LITERAL en alucinaciones/prompts/JJ-1a.md (núcleo §0 regla 6 y §9) antes de despachar cualquier subagente. Guarda también, literal, cada prompt que envíes a un subagente en alucinaciones/prompts/JJ-1a-<agente>.md.
2. Lee completos docs/spec/SPEC.md (incluido el Anexo, sobre todo "Módulo 3") y docs/spec/partes/juanjose.md, y docs/MEMORIA.md.
3. Reglas de esta sesión (prevalecen sobre CLAUDE.md en lo que choquen):
   - NO hagas commits, NI push, NI PR. Los hace Juan José a mano en GitHub Desktop después de revisar.
   - Usa siempre .venv\Scripts\python (Windows, Python 3.12).
   - No toques archivos compartidos (src/comun/, run.py, requirements.txt, README raíz, SPEC.md, PLAN.md, MEMORIA.md, tests de otros) en esta fase.
   - Prohibido inventar: columnas, significados de variables, escalas, conteos o si los datos son reales/sintéticos. Todo número sale de código ejecutado sobre los archivos; todo significado sale de la documentación de Kaggle citada literal. Si algo no está documentado: escribir "no documentado por la fuente" o TODO(dato-faltante), nunca suponer.

CONTEXTO
Juan José descargó a mano el conjunto "Travel Recommendation Dataset" (Kaggle, amanmehra23/travel-recommendation-dataset) en data/raw/m3/: el .zip original y 4 CSV (Expanded_Destinations.csv, Final_Updated_Expanded_Reviews.csv, Final_Updated_Expanded_UserHistory.csv, Final_Updated_Expanded_Users.csv). data/raw/ no se versiona.
Fecha de descarga: 2026-11-25 (la hizo Juan José desde la página de Kaggle con su cuenta; botón Download → archive.zip).

OBJETIVO DE LA FASE A
Medir y documentar el conjunto SIN tomar todavía decisiones de modelado, y DETENERTE con un informe. La definición de "interacción" y la construcción de data/processed/m3/ son de la fase B, después de que Juan José decida.

QUÉ HACER
A1 (curador-datos, Sonnet). Inventario medido con código, guardando el script en docs/investigacion/JJ-1_inventario.py (reproducible, sin internet) y su salida en docs/investigacion/JJ-1_inventario_salida.txt:
  - Por archivo: tamaño en bytes, SHA-256 (también del .zip), filas, columnas con su tipo, faltantes por columna, filas duplicadas exactas, valores únicos por columna y 3 ejemplos.
  - Claves: qué columnas parecen identificadores de usuario y de destino en cada archivo; ¿son únicas donde deberían?; integridad referencial (¿todo usuario/destino de Reviews y UserHistory existe en Users/Destinations? cuántos no).
  - Calificaciones: en cada archivo que las tenga, mínimo, máximo, valores distintos y su frecuencia (escala medida, no supuesta).
  - Interacciones por archivo: pares (usuario, destino) distintos, pares repetidos, interacciones por usuario y por destino (mín, mediana, media, máx, y cuántos usuarios con 1, 2, 3, 4, 5+), densidad = pares distintos / (usuarios × destinos) usando como denominador los usuarios y destinos de las tablas maestras (y también los que aparecen en las interacciones).
  - Solapamiento entre Reviews y UserHistory: ¿cuántos pares (usuario, destino) están en ambos, solo en uno? ¿coinciden las calificaciones cuando están en ambos?
  - Fechas: ¿hay alguna columna de fecha o tiempo? (define si la partición puede ser temporal).
  - Destinos: ¿hay nombres repetidos con distintos identificadores (posible catálogo "expandido" con duplicados)? cuántos nombres distintos vs. identificadores distintos.
  - Variables de contenido disponibles de usuarios y de destinos (lista con tipo y número de categorías). Si alguna columna trae listas en texto (p. ej. varias preferencias separadas por comas), cuántas opciones distintas aparecen al separarlas.
  - Señales de datos generados: distribuciones demasiado uniformes (calificaciones, categorías, género), correlaciones ausentes entre preferencia y destino visitado, textos repetidos, etc. Solo reporta lo medido.
A2 (investigador-fuentes, Sonnet). Documentación de la fuente, citada literal y con fecha de consulta. La página de Kaggle se dibuja con JavaScript; usa los endpoints públicos que sí responden: https://www.kaggle.com/api/v1/datasets/metadata/amanmehra23/travel-recommendation-dataset y https://www.kaggle.com/api/v1/datasets/list/amanmehra23/travel-recommendation-dataset. Guarda la respuesta cruda en docs/investigacion/JJ-1_kaggle_metadata.json. Extrae: título, autor, descripción, licencia(s) declarada(s) (si se contradicen, dilo), fecha de creación/actualización, descripción de columnas si existe, y TODA frase sobre cómo se generaron los datos (real, sintético, "generated", "enriched"…), copiada literal. Propón la cita APA 7 del conjunto.
A3 (cazador-alucinaciones, Opus). Contrasta cada afirmación de A1 y A2 contra los archivos y la respuesta cruda de Kaggle. Si algún subagente afirmó algo falso o no respaldado (una columna que no existe, un significado inventado, "es sintético/real" sin cita), es candidato a hallazgo: anótalo con prompt literal, respuesta y evidencia, pero NO lo numeres todavía en alucinaciones/registro.md (la numeración H-xx la coordina Andrés).

ENTREGABLE DE LA FASE A
docs/investigacion/JJ-1_fuentes_m3.md con: (1) ficha preliminar (fuente, cita APA, URL, fecha de descarga, SHA-256, tamaños); (2) tablas del inventario; (3) qué dice la fuente sobre real/sintético y licencia, con citas literales; (4) diccionario: por columna, significado SOLO si la fuente lo documenta, si no "no documentado por la fuente"; (5) inconsistencias y problemas de calidad; (6) opciones para definir "interacción" (solo Reviews, solo UserHistory, unión, intersección) con los conteos y la densidad de cada una, ventajas y riesgos, SIN elegir; (7) implicaciones para la partición (¿hay fechas? ¿cuántos usuarios tendrían < 2, < 3 interacciones?); (8) candidatos a hallazgo de A3.

Luego DETENTE y muéstrame un resumen corto: los números clave, las preguntas que debe decidir Juan José y la lista de archivos creados. No crees nada en src/, configs/, data/processed/ ni results/ todavía.
```
