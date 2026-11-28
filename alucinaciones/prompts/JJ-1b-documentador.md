# Prompt JJ-1b (cierre) — documentador (Haiku) — 2026-11-25 — orquesta: Juan José

Actúa como el agente definido en `.claude/agents/documentador.md` (léelo primero). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales` (rama `dev/juanjose`). **No hagas commit ni push.** Edita **solo**
`docs/MEMORIA.md`. No decidas nada ni redactes contenido técnico nuevo: copia los datos de abajo.

Reglas de `docs/MEMORIA.md` (ver `CLAUDE.md`): ≤ 150 líneas; **no borres ni cambies nada de otros integrantes**; mantén el
formato y el estilo de las secciones existentes (Estado, Decisiones vigentes, Avisos para el equipo, Pendientes, Cacería,
Bitácora más reciente arriba).

Agrega exactamente esto (redacción corta, en el estilo del archivo):

1. **Estado** — una viñeta nueva: «JJ-1 (datos de M3) terminado en `dev/juanjose` el mié 25, pendiente de PR: `run.py m3-datos`
   construye `data/processed/m3/{destinos,usuarios,interacciones}.parquet` y `results/data/m3/eda/{ficha,calidad,diccionario}`
   desde `data/raw/m3/` (Kaggle `amanmehra23/travel-recommendation-dataset`, descarga manual del 25-nov; no versionado).
   999 usuarios, 1 000 destinos (5 lugares), 1 998 interacciones (999 reseñas + 999 historial), densidad 0,20 %. Revisado por
   revisor-spec y revisor-calidad (aprobados en la 2.ª vuelta) y cazador-alucinaciones (0 afirmaciones incorrectas vigentes).
   Investigación: `docs/investigacion/JJ-1_fuentes_m3.md`.»
2. **Decisiones vigentes** — una viñeta nueva: «M3 [DECIDIDO, Juan José, 25-nov; `docs/spec/partes/juanjose.md` §3.1]:
   interacción = unión de Reviews y UserHistory como implícita (no comparten pares); destino = los 1 000 `DestinationID`, con
   `lugar` (5 lugares) para el análisis complementario; partición por usuario (JJ-3; `VisitDate` solo descriptiva: 3 valores
   ligados al número de fila y posteriores a la publicación); datos generados según la fuente («generated for educational and
   research purposes»); licencia MIT del campo formal con contradicción documentada; `Name`, `Email` y `ReviewText` no pasan a
   procesados ni a resultados.»
3. **Avisos para el equipo** — una viñeta nueva: «M3: para que la CI pase, el PR de JJ-1 debe incluir
   `configs/m3/datos.yaml`, `docs/investigacion/JJ-1_kaggle_metadata.json` y `tests/fixtures/m3/` (las pruebas los leen).»
4. **Pendientes** — una viñeta nueva al final de la lista numerada: «Juan José: PR de JJ-1; confirmar las columnas de
   `interacciones.parquet` frente a §5.7 (`fecha_visita`, `id_origen`, `origen`) y, si se confirman, PR dedicado al núcleo;
   JJ-2 y JJ-3.»
5. **Cacería** — cambia solo la línea de candidatos para agregar, sin quitar H-01: «2 candidatos de M3 (JJ-1b, sin número,
   Datos del mundo real): "las tres licencias piden citar la fuente" (orquestador Opus + implementador Sonnet) y "Preferences y
   Type no comparten vocabulario" (implementador Sonnet); ver `alucinaciones/registro.md`.»
6. **Bitácora** — una línea nueva **arriba**: «2026-11-25 · Juan José · JJ-1 ✅ (fases A y B): inventario y fuente de M3
   verificados, datos procesados de M3, ficha/calidad/diccionario, D1–D7 en `juanjose.md` §3.1; 2 candidatos a la cacería.»

Al terminar, verifica que el archivo tiene ≤ 150 líneas y que todas las líneas que había antes siguen ahí (salvo la línea de
candidatos de Cacería, que se amplía). Entrega: el diff de `docs/MEMORIA.md` y el número de líneas.
