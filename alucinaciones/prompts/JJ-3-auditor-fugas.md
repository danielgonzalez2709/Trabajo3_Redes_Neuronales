# JJ-3 — prompt del orquestador (Opus 5.5) al auditor-fugas (Opus), 2026-11-26

Eres el verificador de la tarea JJ-3 (partición sin fuga de M3, recomendación de destinos), rama `dev/juanjose`. Directorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales`. NO hagas commits, push ni PR. Usa `.venv/Scripts/python`. Sin internet.
Puedes agregar pruebas a `tests/test_fuga_m3.py` si demuestran una fuga o cierran un hueco; NO cambies `particion.py`,
`datos.py` ni la config: si encuentras un problema, descríbelo con evidencia (prueba que falla o cálculo) y la corrección
propuesta, y lo devuelvo al implementador. No cambies el Spec.

## Contexto que debes leer
- `docs/spec/SPEC.md`: §0, §5.7, §5.9 (`evidencia`), §6 (misma partición para todos los modelos, SHA-256), §8
  (`test_fuga_m3.py`), y del Anexo «Módulo 3» las tareas 3–6 y la pregunta de negocio 1 (usuarios nuevos).
- `docs/spec/partes/juanjose.md` §3.1: D1–D3 y D8–D10 [DECIDIDO].
- Implementación: `src/m3_recomendacion/particion.py`, `src/m3_recomendacion/datos.py` (función `main` y `leer_config_particion`),
  `configs/m3/datos.yaml` (bloque `particion`), `tests/test_fuga_m3.py`, `tests/test_datos_m3.py`, y las salidas
  `data/processed/m3/interacciones.parquet` y `results/data/m3/particion/resumen.json`.

## Enunciado (Anexo M3, tarea 3, literal)
«**Partición.** Definan y justifiquen cómo separan los conjuntos de entrenamiento, validación y prueba (por ejemplo, por tiempo
si hay fechas, o excluyendo interacciones por usuario). Ninguna interacción de prueba puede usarse para entrenar.»

## Qué auditar (busca activamente; no te limites a leer las pruebas)
1. **Split**: ninguna interacción en dos particiones; regla D3 exacta por usuario; clave `(origen, id_origen)` (id_origen solo
   no es único); el sorteo usa `make_rng` sin estado global; el parquet versionado corresponde a la semilla de la config.
2. **Popularidad**: `popularidad_train` solo con train; ¿hay algún otro camino por el que una estadística de interacciones
   (conteos por destino o por usuario, actividad, ítems fríos, `particion_d3`, `distribucion_actividad.json`, la tabla
   `interacciones_por_destino.csv` de JJ-2) pueda terminar como entrada de un modelo? Señala qué archivos de `results/` y
   columnas del parquet un modelo futuro (JJ-4/JJ-5) NO debe leer y propone cómo hacerlo verificable (p. ej. una prueba que
   JJ-4 deba heredar). Revisa también si la columna `popularidad` de `destinos.parquet` (atributo de la fuente, no
   documentado) es un riesgo.
3. **Candidatos (D10)**: nunca contienen el historial conocido; contienen el objetivo; validación no excluye ni usa la prueba.
4. **El caso de los 5 lugares**: los 1 000 ids son 5 lugares repetidos (D2). Un usuario puede tener en train el «Taj Mahal
   #178» y en prueba el «Taj Mahal #3»: no es fuga a nivel de id, pero hace trivial un «acierto por lugar». `resumen.json`
   mide cuántos usuarios de prueba están en ese caso (204 de 606). Dilo con claridad y **propón cómo reportarlo** en la
   evaluación (JJ-6): p. ej. acierto por lugar con y sin esos usuarios, línea base del azar por lugar, o candidatos por lugar
   excluyendo los lugares ya vistos; razona cuál es honesto y por qué.
5. **Usuarios sin historial**: los 141 sin interacciones; ¿se cuelan en alguna evaluación? Comenta además (sin implementar)
   cómo deben simularse los usuarios nuevos de la pregunta de negocio 1 sin fuga (los 141 no tienen verdad de terreno).
6. **Mutantes**: verifica tú mismo que `tests/test_fuga_m3.py` falla con al menos: popularidad calculada con todo; candidatos
   sin excluir historial; un usuario con 2 en prueba; validación para usuarios con exactamente 2. Aplica cada mutante sobre
   una copia o restaura el archivo original al terminar (comprueba con `git diff --stat` que `particion.py` queda igual).
7. Cualquier otra vía: semilla distinta por modelo (rompería §6), SHA-256 que no detecte un cambio en `split`, `m3-eda`
   recalculando algo con la partición, etc.

## Entrega
Veredicto (SIN FUGA / FUGA / RIESGO), lista de hallazgos con severidad, evidencia (comando y salida real), resultado de los
mutantes, la propuesta para el caso de los 5 lugares y para usuarios nuevos, pruebas que agregaste (si alguna) y su salida.
