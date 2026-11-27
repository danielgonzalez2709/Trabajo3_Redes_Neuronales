# JJ-3 — prompt del orquestador (Opus 5.5) al documentador (Haiku), 2026-11-26

Actualiza `docs/MEMORIA.md` por el cierre de JJ-3 (partición sin fuga de M3, Juan José, rama `dev/juanjose`). Solo ese archivo;
sin commits. **No borres nada de otros integrantes**; mantén el archivo en ≤ 150 líneas (`wc -l`); conserva el formato. Usa
solo los datos de abajo (no inventes cifras).

1. **Estado:** agrega una viñeta después de la de JJ-2: «JJ-3 (partición sin fuga de M3) terminado en `dev/juanjose` el jue 26,
   pendiente de PR junto con JJ-1 y JJ-2: `run.py m3-datos` agrega `split` ∈ {train, validacion, prueba} a
   `interacciones.parquet` (semilla `particion.semilla` = 2026) y escribe `results/data/m3/particion/resumen.json` (conteos,
   diagnósticos, SHA-256 del parquet y huella `b35cd70b…58e8b8`). 1 066 train / 326 validación / 606 prueba; 858 usuarios con
   interacciones, 141 no evaluables. `src/m3_recomendacion/particion.py` (`asignar_split`, `popularidad_train`,
   `historial_conocido`, `candidatos`); `tests/test_fuga_m3.py` (53 pruebas; mutantes detectados). Revisado por auditor-fugas
   (SIN FUGA), revisor-spec (aprobado en la 2.ª vuelta) y revisor-calidad (aprobado en la 2.ª vuelta, más un ajuste de la
   sesión principal). Blog 07: subsección «Partición».»
2. **Decisiones vigentes**, viñeta de M3 [DECIDIDO, Juan José, 25-nov]: corrige el texto «`VisitDate` solo descriptiva: 3
   valores ligados al número de fila y posteriores a la creación de la versión 1 en Kaggle, 2024-01-23» por «`VisitDate` solo
   descriptiva: 3 valores ligados al número de fila, 2 de ellos (666 de 999 filas) posteriores a la creación de la versión 1
   en Kaggle, 2024-01-23» (era impreciso: 2024-01-01 es anterior; es un candidato de la cacería). Agrega una viñeta nueva:
   «M3 [DECIDIDO, Juan José, 26-nov; `juanjose.md` §3.1, D8–D10]: una sola partición en la columna `split` del parquet para
   todos los modelos, con su huella en la `evidencia`; HPO y parada temprana con validación, modelos finales solo con train y
   una evaluación en prueba; toda estadística de interacciones solo con train (`popularidad_train`); candidatos = catálogo
   menos historial conocido (prueba: train ∪ validación; validación: train); clave de una interacción = `(origen, id_origen)`.»
   Y en la viñeta [PROPUESTO …] agrega: «diagnósticos de `resumen.json` (destinos fríos, coincidencia de lugar con su
   esperado por azar), guardas `AJUSTES_SOLO_TRAIN` para JJ-4/JJ-5 y nombre `particion.semilla` = 2026».
3. **Avisos para el equipo:** en la viñeta de M3 sobre la CI, agrega que el PR debe incluir también
   `results/data/m3/particion/resumen.json` (las pruebas reales de `test_fuga_m3.py` lo leen). Y una viñeta: «M3: la demo en
   vivo con otra semilla debe redirigir las salidas a `results/data/m3_demo/` (orden en `configs/m3/datos.yaml`); sin
   redirigir se pisan archivos versionados.»
4. **Pendientes**, punto 4 (Juan José): quita «JJ-3, con una prueba que compare la partición real con `actividad_usuarios.json`
   → `particion_d3`» (hecho) y agrega: «decidir lo [PROPUESTO] de JJ-3 (diagnósticos, guardas, nombre de la semilla) y el
   alcance de D10 sobre los 141 usuarios sin interacciones (sin verdad de terreno: solo ejemplos; los usuarios nuevos de la
   pregunta de negocio 1 se simulan en JJ-6 con usuarios de prueba); en JJ-4/JJ-5 registrar cada ajuste en
   `AJUSTES_SOLO_TRAIN` y copiar la huella a `evidencia`; reportar el acierto por lugar frente a su línea base del azar.»
5. **Cacería:** agrega «2 candidatos de M3 de JJ-3 (sin número): "acierto por lugar trivial" (Matemáticas; premisa del
   prompt humano convertida en hecho por el orquestador Opus y el implementador-experto Opus; 204 observados frente a 198,0
   por azar) y "los 3 valores de VisitDate son posteriores" (Datos del mundo real, menor; MEMORIA → orquestador → redactor
   Sonnet); evidencia en `alucinaciones/evidencias/JJ-3/`».
6. **Bitácora**, línea nueva arriba: «2026-11-26 · Juan José · JJ-3 ✅: partición sin fuga de M3 (1 066 / 326 / 606, semilla
   2026, huella en `resumen.json`), `test_fuga_m3.py`, blog 07 «Partición»; D8–D10; 2 candidatos a la cacería.»

Entrega: el diff y `wc -l` del archivo.
