# JJ-3 — 3.ª vuelta del orquestador (Opus 5.5) al implementador-experto (Opus), 2026-11-26

El revisor-calidad (Haiku) pidió CAMBIOS NECESARIOS. Corrige lo siguiente (mismas reglas: sin commits; solo `particion.py`,
`datos.py`, `configs/m3/datos.yaml`, `tests/test_fuga_m3.py`; NO toques `eda.py`, `tests/test_eda_m3.py`, `src/comun/` ni el
blog; no cambies ninguna cifra ni el comportamiento de la partición: la huella y el SHA-256 del parquet deben quedar iguales).

**Bloqueantes**
- B1. Las pruebas con datos reales deben saltarse limpiamente si falta CUALQUIER archivo que leen (interacciones, usuarios y
  destinos `.parquet`, `resumen.json`, `actividad_usuarios.json`): una lista de rutas requeridas y un `skipif` con un mensaje
  que nombre los faltantes.
- B2. `run.py m3-datos --set particion.semilla=7` sin redirigir salidas sobrescribe archivos versionados y luego las pruebas
  reales fallan. Documenta en `configs/m3/datos.yaml`, junto al bloque `particion`, la orden de demo en vivo con
  `--set salida.carpeta=… --set salida.eda=… --set salida.particion=…` hacia una carpeta temporal (comprueba que funciona y
  pega la salida), y di en el comentario que sin redirigir se pisan los archivos versionados.

**Recomendados que sí aplicar**
- R1. En `asignar_split`, reemplaza el `np.where` anidado por `es_prueba = (n_u >= 2) & (posicion == 0)` y
  `es_validacion = (n_u >= 3) & (posicion == 1)` con nombres claros (`posicion_en_usuario` en vez de `rango`) y comentarios
  de paso; quita `orden_canonico` solo si es redundante de verdad (comprueba que la huella no cambia).
- R4. Divide `resumen_particion` en auxiliares (`_grupos_de_actividad`, `_diagnosticos`).
- R5. Cambia el alias `pt` por `particion` en `datos.py` y en `test_fuga_m3.py`.
- R7. En `test_fuga_m3.py`: la prueba «byte a byte» compara con `Series.equals` y se renombra si hace falta; la `lambda` con
  `noqa` pasa a `def`; quita la comprobación de la palabra «trivial» (sustitúyela por una de contenido: que la definición
  menciona el azar / `esperado_por_azar`); `pytest.raises` con `match`; quita comentarios de historial de revisión
  («2.ª vuelta, R14»); la prueba del azar global no debe dejar `np.random` sembrado (guarda y restaura el estado).
- R8. Pruebas de los errores de `leer_config_particion` (clave faltante, semilla texto, semilla negativa) y de la tabla vacía.
- R9. Comenta o toma de `resumen.json`/config las constantes 141 y 1000 de las pruebas reales.
- R10. `_ids_catalogo` → `np.asarray(catalogo, dtype="int64")` si equivale.
- R11. Reescribe el comentario de `COLUMNAS_INTERACCIONES` en `datos.py` (por qué hay dos listas) y explica `inter_split` vs
  `inter` en `main`.
- R12. `dtype="str"` → el tipo explícito que deje el parquet idéntico (si cambia el SHA-256 del parquet, NO lo cambies y dilo).
- Validar la semilla antes del trabajo O(n).

**No aplicar** (se escalan a Juan José): R2/R3 (unificar la regla y «pocas/muchas» con `eda.py`), R6 (mover `montar`), R13
(duplicación con `src/comun`), renombrar `umbral_pocas_max`.

Al final: `.venv/Scripts/python run.py m3-datos --config configs/m3/datos.yaml` dos veces (idénticas byte a byte y con el
mismo SHA-256 del parquet y la misma huella que antes: `4e143626…5e315e` y `b35cd70b…58e8b8`; `resumen.json` igual), y
`.venv/Scripts/python -m pytest -q tests/test_fuga_m3.py` y `-m "not lento"` en verde. Entrega los cambios y la salida real.
