# JJ-3 — prompt del orquestador (Opus 5.5) al implementador-experto (Opus), 2026-11-26

Tarea JJ-3 🧠 del Trabajo 3: **partición sin fuga de M3** (recomendación de destinos). Te dirige la sesión principal de Juan José,
rama `dev/juanjose`. Prueba primero, luego código.

## Reglas
- NO hagas commits, push ni PR. Usa siempre `.venv\Scripts\python` (en Bash: `.venv/Scripts/python`). Sin internet.
- Solo tocas: `tests/test_fuga_m3.py` (nuevo), `src/m3_recomendacion/particion.py` (nuevo), `src/m3_recomendacion/datos.py`,
  `configs/m3/datos.yaml`, `tests/test_datos_m3.py` (solo para ajustar lo que cambia legítimamente: hoy afirma que no hay
  `split`), `results/data/m3/particion/` (salida nueva) y `data/processed/m3/interacciones.parquet` (regenerado por el comando).
  NO toques `src/comun/`, `run.py`, `requirements.txt`, `docs/spec/`, el blog ni archivos de otros. No cambies el Spec: si
  algo de abajo choca con el Spec o con una cifra medida, detente y escálalo en tu respuesta.
- Prohibido inventar cifras: todo número de las salidas lo calcula el código. Semillas con `src/comun/seeds.py`
  (`make_rng(base_seed, run_id)`), nada global (`np.random.seed` prohibido).
- Sigue el estilo de `src/m3_recomendacion/datos.py` (español, docstrings cortos, errores claros, escritura atómica,
  salidas deterministas sin fechas de ejecución ni rutas absolutas).

## Lee primero
- `docs/spec/SPEC.md`: §0, §3, §4.1, §5.7 (contrato de `interacciones.parquet` con `split`), §5.9 (`evidencia` con SHA-256 de
  la partición), §6 (regla de comparación justa: misma partición para todos los modelos), §8 (`test_fuga_m3.py`: ninguna
  interacción de prueba en train), y en el Anexo «Módulo 3» las tareas 3 y 6.
- `docs/spec/partes/juanjose.md` §3.1: D1–D3 y las nuevas **D8–D10** (ahí están escritas; son [DECIDIDO]).
- `src/m3_recomendacion/datos.py`, `configs/m3/datos.yaml`, `tests/test_datos_m3.py` (fixtures y función `montar`),
  `tests/fixtures/m3/`, `src/comun/seeds.py`, `configs/m3/eda.yaml` (bloque `actividad.pocas_max`) y
  `results/data/m3/eda/actividad_usuarios.json` (`particion_d3`: conteo de la regla hecho por JJ-2, sin semilla).

## Enunciado que cubre (Anexo, M3 tarea 3, literal)
«**Partición.** Definan y justifiquen cómo separan los conjuntos de entrenamiento, validación y prueba (por ejemplo, por tiempo
si hay fechas, o excluyendo interacciones por usuario). Ninguna interacción de prueba puede usarse para entrenar.»
Y la regla de comparación justa: «todos los modelos de un módulo usan el mismo preprocesamiento y las mismas particiones».

## Decisiones (resumen; el texto vigente está en juanjose.md §3.1)
- **D3.** Por usuario, no por tiempo (`fecha_visita` no es una fecha real). Prueba = 1 interacción al azar de cada usuario con
  ≥ 2; validación = 1 más de cada usuario con ≥ 3; el resto, train; usuarios con 1 interacción solo en train; semilla fija.
- **D8.** La partición la calcula `run.py m3-datos` y queda en la columna `split` ∈ {`train`, `validacion`, `prueba`} de
  `interacciones.parquet`. Una sola partición para todos los modelos de M3, con su SHA-256 registrado.
- **D9.** HPO y parada temprana con validación; modelos finales entrenados SOLO con train y evaluados una vez en prueba. Toda
  estadística derivada de las interacciones (popularidad, conteos por destino, negativos por popularidad, umbrales de actividad
  usados como variable) se calcula SOLO con train.
- **D10.** Candidatos: para un usuario de prueba, todo el catálogo (los 1 000 `destino_id` de `destinos.parquet`) menos su
  historial conocido (train ∪ validación); para validación, el catálogo menos train. Usuarios sin interacciones no se evalúan.
- **Clave de una interacción = `(origen, id_origen)`**: lo medí sobre los datos reales; `id_origen` solo NO es único (ReviewID e
  HistoryID se solapan), el par sí. Cada par `(usuario_id, destino_id)` es único (D1; `construir_interacciones` ya falla si se
  repite).

Cifras que medí en `data/processed/m3/interacciones.parquet` (compruébalas con tu código, no las copies a ninguna salida):
1 998 interacciones, 858 usuarios con ≥ 1, 606 con ≥ 2, 326 con ≥ 3, 252 con 1, 141 de 999 sin interacciones →
train 1 066, validación 326, prueba 606.

## Qué construir
**P1. `tests/test_fuga_m3.py`** (primero; córrelo y muéstralo en rojo antes de implementar). Con los fixtures de
`tests/fixtures/m3/` (reutiliza `montar`/`salidas` de `test_datos_m3.py` importándolos o con un helper equivalente, y agrega
tablas sintéticas pequeñas hechas a mano cuando haga falta: p. ej. usuarios con 0, 1, 2, 3 y 6 interacciones) y además sobre
`data/processed/m3/` real con `skipif` cuando no exista:
- ninguna pareja (usuario, destino) de prueba o validación aparece en train; ninguna clave `(origen, id_origen)` está en dos
  particiones; la unión de las tres particiones es exactamente la tabla original (ni se pierde ni se duplica ninguna fila, y
  las demás columnas no cambian);
- cada usuario con ≥ 2 interacciones tiene exactamente 1 en prueba; con ≥ 3, exactamente 1 en validación; con 2, 0 en
  validación; con 1, solo train; los usuarios sin interacciones no aparecen; todo usuario con interacciones tiene ≥ 1 en train;
- `popularidad_train` NO cambia si se alteran (otro `destino_id`) o se eliminan interacciones de validación/prueba
  (invarianza), y SÍ cambia si se altera una de train (para que la prueba pueda fallar); cubre los 1 000 destinos (0 para los
  que no aparecen en train);
- `candidatos` (D10) nunca contiene un destino del historial conocido del usuario y sí contiene su destino de prueba (y en
  validación, su destino de validación, y no los de train); su tamaño es catálogo − historial conocido;
- determinismo: misma semilla → misma columna `split` byte a byte (y mismo `interacciones.parquet` de dos corridas de `main`);
  semilla distinta → split distinto pero las mismas cantidades por partición y por usuario;
- con los datos reales: los conteos por partición coinciden con `results/data/m3/eda/actividad_usuarios.json` →
  `particion_d3` (total y por grupo pocas/muchas), y `resumen.json` coincide con lo recalculado desde el parquet (incluidos los
  dos SHA-256);
- `particion.umbral_pocas_max` de `configs/m3/datos.yaml` es igual a `actividad.pocas_max` de `configs/m3/eda.yaml`.
Las pruebas deben poder fallar de verdad: comprueba (y repórtalo) que fallan con al menos estos mutantes, aplicados a mano y
revertidos: popularidad calculada con todas las interacciones; candidatos sin excluir el historial; un usuario con 2 en prueba;
validación para usuarios con exactamente 2.

**P2. `src/m3_recomendacion/particion.py`**: funciones puras, sin estado global, docstrings claros en español:
- `asignar_split(inter, semilla) -> DataFrame` (o nombre equivalente): agrega `split` sin cambiar el orden ni las demás
  columnas; el azar sale de `make_rng(semilla, 0)` (o documenta otro `run_id`) y es independiente del orden de entrada
  (ordena por la clave antes de sortear). Escribe en un comentario la regla formal (para cada usuario u con n_u
  interacciones: si n_u ≥ 2, una al azar → prueba; si n_u ≥ 3, otra al azar de las restantes → validación; el resto → train).
  Error claro si faltan columnas o si un par (usuario, destino) se repite.
- `historial_conocido(inter, split_objetivo)`: por usuario, los destinos que se consideran conocidos al evaluar
  `split_objetivo` (prueba → train ∪ validación; validación → train).
- `candidatos(...)`: D10, catálogo menos historial conocido, para un usuario o para todos (elige la forma más útil para JJ-4).
- `popularidad_train(inter, catalogo)`: conteo de interacciones por `destino_id` SOLO con `split == "train"`, reindexado a todo
  el catálogo (0 si no aparece). Comenta que es la única popularidad que pueden usar los modelos (D9).
- La función que arma el resumen (abajo) y la huella: SHA-256 de la tabla `usuario_id, destino_id, split` ordenada por
  `(usuario_id, destino_id)` serializada de forma estable (p. ej. CSV con `\n`, sin índice) — documenta exactamente cómo.

**P3. Integración en `m3-datos`.**
- `configs/m3/datos.yaml`: bloque `particion` comentado: `semilla` (fija; un entero), la regla de D3 en el comentario,
  `umbral_pocas_max: 2` (comentado: debe ser igual a `actividad.pocas_max` de `eda.yaml`, umbral de JJ-2 [PROPUESTO, a
  confirmar por Juan José]), y la salida `results/data/m3/particion` (p. ej. en `salida`). Corrige el comentario de cabecera
  que dice «Nada aleatorio: no hay base_seed».
- `datos.py`: `main` agrega `split` antes de escribir el parquet (`COLUMNAS_INTERACCIONES` con `split` al final; actualiza el
  docstring del módulo y la línea de D3) y escribe `results/data/m3/particion/resumen.json` con: semilla, regla (texto),
  conteos por split (interacciones y usuarios), usuarios con prueba por grupo de actividad (pocas = 1..umbral, muchas >
  umbral; aclara en el JSON que el grupo se define con el total de interacciones del usuario y que es solo para estratificar
  el reporte, no una variable de los modelos), usuarios sin interacciones (no evaluables), SHA-256 de `interacciones.parquet`
  y SHA-256 de la huella; y dos diagnósticos medidos útiles para la evaluación: (a) cuántos destinos de prueba (y de
  validación) no tienen ninguna interacción en train (ítems fríos: su popularidad de train es 0), (b) cuántos usuarios de
  prueba tienen en su historial conocido otro id del mismo `lugar` que su destino de prueba (los 1 000 ids son 5 lugares: un
  «acierto por lugar» sería trivial para ellos). Imprime los conteos de la partición en `_imprimir`.
- `ficha.json` NO cambia (el Spec no lo pide). No rompas `run.py m3-eda` (lee el parquet y acepta columnas extra; verifícalo)
  ni las pruebas de JJ-1/JJ-2: ajusta en `test_datos_m3.py` solo lo que cambia de forma legítima (columnas con `split`).
- Corre `.venv/Scripts/python run.py m3-datos --config configs/m3/datos.yaml` dos veces y comprueba que las salidas son
  idénticas byte a byte (parquet, resumen.json y los archivos de `results/data/m3/eda/` de m3-datos); corre
  `.venv/Scripts/python run.py m3-eda --config configs/m3/eda.yaml` y dime si cambió algún archivo de `results/data/m3/eda/`
  (con `git status`/`git diff --stat`; no debería).

## Aceptación
`.venv/Scripts/python -m pytest -q tests/test_fuga_m3.py -v` en verde; `.venv/Scripts/python -m pytest -q -m "not lento"` en
verde; conteos de la partición real = 1 066 / 326 / 606 calculados por el código; mutantes detectados.

## Entrega
Formulación (5–10 líneas), archivos creados/modificados, salida real de las pruebas (rojo y verde) y de los dos `m3-datos`,
conteos y diagnósticos de `resumen.json`, resultado de los mutantes, puntos donde una fuga es posible y cómo la descarta cada
prueba, y riesgos residuales o dudas para Juan José.
