# JJ-3 — prompt literal de Juan José a la sesión principal (Opus 5.5), 2026-11-26

Tarea JJ-3 (partición sin fuga de M3). Te dirige Juan José; rama dev/juanjose (ya incluye JJ-1, JJ-2 y el merge de main con el Spec v0.7).

ANTES DE NADA
1. Guarda este prompt LITERAL en alucinaciones/prompts/JJ-3.md antes de despachar subagentes, y cada prompt a un subagente en alucinaciones/prompts/JJ-3-<agente>.md.
2. Lee: docs/spec/SPEC.md (§0, §5.7, §5.9, §6 "Regla de comparación justa", §8 y el Anexo "Módulo 3" tareas 3–6), docs/spec/partes/juanjose.md (decisiones D1–D7, sobre todo D3), docs/MEMORIA.md, src/m3_recomendacion/datos.py, configs/m3/datos.yaml, tests/test_datos_m3.py, src/comun/seeds.py y results/data/m3/eda/distribucion_actividad.json.
3. Reglas: NO commits, NI push, NI PR (los hace Juan José en GitHub Desktop). Siempre .venv\Scripts\python. Prueba primero, luego código. Sin internet. No toques archivos compartidos (src/comun/, run.py, requirements.txt, SPEC.md, archivos de otros) salvo PLAN.md, MEMORIA.md y registro.md al cierre.

QUÉ PIDE EL ENUNCIADO (Anexo M3, tarea 3)
"Definan y justifiquen cómo separan los conjuntos de entrenamiento, validación y prueba (…excluyendo interacciones por usuario). Ninguna interacción de prueba puede usarse para entrenar." Y la regla de comparación justa: todos los modelos de un módulo usan el mismo preprocesamiento y las mismas particiones (SHA-256 en cada JSON).

DECISIONES (D3 ya decidida; regístralas como [DECIDIDO, Juan José, 26-nov] en juanjose.md §3.1, junto a D3, las nuevas D8–D10)
- D3 (ya vigente): por usuario, no por tiempo. Prueba = 1 interacción al azar de cada usuario con ≥ 2; validación = 1 más de cada usuario con ≥ 3; el resto, entrenamiento; usuarios con 1 interacción solo en entrenamiento; semilla fija. Cifras esperadas (de JJ-2): 1 066 train, 326 validación, 606 prueba; verifícalas, no las copies.
- D8. Dónde vive la partición: la calcula run.py m3-datos (config configs/m3/datos.yaml, bloque `particion` con su semilla) y queda en la columna `split` ∈ {train, validacion, prueba} de data/processed/m3/interacciones.parquet (núcleo §5.7). Una sola partición para todos los modelos de M3 (referencias y red), con su SHA-256 registrado.
- D9. Uso de los conjuntos: la búsqueda de hiperparámetros y la parada temprana usan validación; los modelos finales (referencias y red, y las 30 semillas) se entrenan SOLO con train y se evalúan una vez en prueba. Toda estadística derivada de las interacciones (popularidad, conteos por destino, negativos por popularidad, umbrales de actividad usados como variable) se calcula SOLO con train.
- D10. Candidatos al evaluar: para cada usuario de prueba se rankean todos los destinos del catálogo EXCEPTO los que ya tiene en train y validación (su historial conocido); en validación, excepto los de train. Así un destino ya visto nunca cuenta como acierto. Los usuarios sin interacciones (los 141 que no aparecen) no se evalúan en prueba; sirven después para el escenario de usuario nuevo (JJ-6).
Si algo de esto contradice el Spec o una cifra medida, dímelo antes de implementarlo.

QUÉ CONSTRUIR (implementador-experto, Opus; prueba primero)
P1. tests/test_fuga_m3.py (núcleo §8), con los fixtures de tests/fixtures/m3/ y además sobre data/processed/m3/ real cuando exista:
   - ninguna pareja (usuario, destino) de prueba o validación aparece en train; ningún id_origen está en dos particiones;
   - cada usuario con ≥ 2 interacciones tiene exactamente 1 en prueba; con ≥ 3, exactamente 1 en validación; con 1, solo train; con 0, nada;
   - la popularidad de entrenamiento NO cambia si se alteran o eliminan interacciones de validación/prueba (prueba de invarianza);
   - el conjunto de candidatos de D10 nunca contiene un destino del historial conocido del usuario, y sí contiene su destino de prueba;
   - determinismo: misma semilla → mismo split byte a byte; semilla distinta → split distinto pero mismas cantidades.
P2. src/m3_recomendacion/particion.py: función pura que agrega `split` (usa src/comun/seeds.py o un generador de numpy con la semilla de la config; nada global), helpers `historial_conocido(...)`, `candidatos(...)` (D10) y `popularidad_train(...)` (conteo por destino SOLO con train, listo para que JJ-4 lo use). Docstrings claros en español.
P3. src/m3_recomendacion/datos.py y configs/m3/datos.yaml: integrar la partición en m3-datos (bloque `particion` comentado con la semilla y la regla de D3). Escribir además results/data/m3/particion/resumen.json con: semilla, regla, conteos por split (interacciones y usuarios), usuarios por grupo de actividad en prueba (pocas ≤ 2 / muchas ≥ 3, el umbral de JJ-2), SHA-256 de interacciones.parquet y de una huella de la partición (p. ej. SHA-256 de la tabla ordenada usuario_id, destino_id, split). Actualiza ficha.json solo si el Spec lo requiere; no rompas las pruebas de JJ-1 y JJ-2 (ajústalas si el parquet cambia de forma legítima).
P4. Revisa si JJ-2 (src/m3_recomendacion/eda*.py) usa algún conteo que ahora deba distinguir split; si las cifras del descriptivo cambian, regenera con run.py m3-eda y avísame. El descriptivo describe todo el conjunto (eso no es fuga); lo que usen los MODELOS es lo que debe salir solo de train.
P5. Blog (redactor-tecnico, Sonnet), blog/secciones/07-m3-recomendacion.md: nueva subsección «### Partición» DESPUÉS de «### Análisis descriptivo», con la regla (D3), por qué no es temporal, D9 y D10 en palabras simples, y una tabla (::: tabla con título y fuente, citada en el texto) con los conteos de results/data/m3/particion/resumen.json. Sin rutas de archivos dentro de las frases (las rutas van en la línea «Fuente:» de la tabla). Actualiza «Implicaciones para el modelado» si hace falta para que sea coherente.

REVISIÓN (en este orden; si falla, vuelve al autor)
R1. auditor-fugas (Opus) — verificador de JJ-3: busca activamente cualquier camino por el que información de validación o prueba llegue al entrenamiento o a la evaluación: split, popularidad, candidatos, el caso de los 5 lugares (un usuario puede tener en train el «Taj Mahal #178» y en prueba el «Taj Mahal #3»: no es fuga a nivel de id, pero hace trivial un «acierto por lugar»; dilo y propón cómo reportarlo), usuarios sin historial, y que las pruebas de P1 fallen con mutantes (p. ej. popularidad calculada con todo, candidatos sin excluir historial, un usuario con 2 en prueba).
R2. revisor-spec (Sonnet): tarea 3 del Anexo M3, §5.7, §6 (mismas particiones y SHA-256), §8 (test_fuga_m3.py) y D3, D8–D10.
R3. revisor-calidad (Haiku): código y pruebas.
Si al final corriges algo tú, vuelve a pasar el revisor correspondiente sobre ese cambio.

CIERRE
- Corre y pega la salida real de: .venv\Scripts\python run.py m3-datos --config configs/m3/datos.yaml (dos veces, mismas salidas); .venv\Scripts\python run.py m3-eda --config configs/m3/eda.yaml; .venv\Scripts\python -m pytest -q tests/test_fuga_m3.py -v; la construcción estricta del blog; y .venv\Scripts\python -m pytest -q -m "not lento" (todo en verde).
- Marca JJ-3 ✅ en docs/spec/PLAN.md y en juanjose.md; que el documentador actualice docs/MEMORIA.md sin borrar nada de otros.
- Muéstrame: archivos creados/modificados, salidas, conteos de la partición, veredictos de R1–R3, candidatos a la cacería (sin numerar, H-?? (JJ-3)) y lo que deba decidir Juan José. Luego DETENTE.
