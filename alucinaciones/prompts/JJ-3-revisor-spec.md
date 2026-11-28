# JJ-3 — prompt del orquestador (Opus 5.5) al revisor-spec (Sonnet), 2026-11-26

Revisa que la tarea JJ-3 (partición sin fuga de M3) cumpla EXACTAMENTE el Spec y el enunciado, ni más ni menos. Directorio
`C:\Repositorios\Trabajo3_Redes_Neuronales`, rama `dev/juanjose`. Solo lectura (puedes correr comandos con `.venv/Scripts/python`);
no edites nada; sin commits.

## Contra qué revisar
- Anexo del núcleo (`docs/spec/SPEC.md`), «Módulo 3», tarea 3 (literal): «**Partición.** Definan y justifiquen cómo separan los
  conjuntos de entrenamiento, validación y prueba (por ejemplo, por tiempo si hay fechas, o excluyendo interacciones por
  usuario). Ninguna interacción de prueba puede usarse para entrenar.» y la «Regla de comparación justa» (mismas particiones).
- Núcleo §0 (reglas, no inventar), §5.7 (contrato de `interacciones.parquet`: columnas y `split`, partición por usuario),
  §5.9 (`evidencia` con SHA-256 de la partición), §6 (una partición por módulo, SHA-256), §8 (`test_fuga_m3.py`: ninguna
  interacción de prueba en train), §4.1 (`run.py m3-datos --config configs/m3/datos.yaml`, `--set`, imprime config).
- `docs/spec/partes/juanjose.md` §3.1: D3 y D8–D10 [DECIDIDO, Juan José, 26-nov] y la nota sobre `(origen, id_origen)`; fila
  JJ-3 de §4 (aceptación: `test_fuga_m3.py` en verde).
- Pedido de Juan José para el contenido de `results/data/m3/particion/resumen.json`: semilla, regla, conteos por split
  (interacciones y usuarios), usuarios por grupo de actividad en prueba (pocas ≤ 2 / muchas ≥ 3), SHA-256 de
  `interacciones.parquet` y de una huella de la partición. `ficha.json` solo cambia si el Spec lo requiere.
- Pedido para el blog: subsección «### Partición» DESPUÉS de «### Análisis descriptivo», con la regla (D3), por qué no es
  temporal, D9 y D10 en palabras simples, y una tabla (`::: tabla` con título y fuente, citada en el texto) con los conteos de
  `resumen.json`; sin rutas de archivos dentro de las frases (solo en la línea «Fuente:»); «Implicaciones para el modelado»
  coherente.

## Qué revisar
`src/m3_recomendacion/particion.py`, `src/m3_recomendacion/datos.py`, `configs/m3/datos.yaml`, `tests/test_fuga_m3.py`,
`tests/test_datos_m3.py`, `results/data/m3/particion/resumen.json`, `data/processed/m3/interacciones.parquet` (columnas y
valores de `split`), `blog/secciones/07-m3-recomendacion.md` (subsección «Partición» y punto (a) de «Implicaciones»),
`src/m3_recomendacion/README.md` y el registro de D8–D10 en `juanjose.md`. Usa `git diff` y `git status` para ver lo nuevo.

Comprueba en concreto: columnas del parquet = §5.7 (`usuario_id, destino_id, origen, id_origen, calificacion, fecha_visita,
split`); valores de `split` ∈ {train, validacion, prueba}; los conteos 1 066 / 326 / 606 salen del código; regla D3 exacta;
D9/D10 implementados donde corresponde (helpers) y no más; semilla por config (y que `--set particion.semilla=…` funcione);
el SHA-256 de la partición existe para que JJ-4/JJ-5 lo copien a `evidencia`; ninguna cifra del blog que no esté en un JSON
(salvo porcentajes declarados como división); que no se haya cambiado nada fuera del alcance (archivos compartidos, Spec
núcleo, archivos de otros). Corre `.venv/Scripts/python -m pytest -q tests/test_fuga_m3.py`.

## Entrega
APROBADO / RECHAZADO, con la lista de incumplimientos (archivo:línea, qué dice el Spec, qué hay) y lo que es más de lo pedido.
