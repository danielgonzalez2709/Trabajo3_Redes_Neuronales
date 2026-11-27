# JJ-4 — prompt del orquestador (Opus 5.5) al auditor-fugas (Opus), 2026-11-27

Auditoría adversarial de fuga de información de la tarea JJ-4 del Trabajo 3 (M3, recomendación): **modelos de referencia
(popularidad, factorización implícita por ALS, aleatorio), búsqueda Optuna y arnés de evaluación @K**. Te dirige la sesión
principal de Juan José, rama `dev/juanjose`. Sin commits. Siempre `.venv\Scripts\python`. Sin internet.

## Reglas que se deben cumplir (docs/spec/partes/juanjose.md §3.1–§3.3)
- D9: la búsqueda de hiperparámetros usa validación; los modelos finales se entrenan **solo con train** y se evalúan una vez en
  prueba; toda estadística derivada de las interacciones (popularidad, conteos, σ_max de la matriz, umbrales usados como
  variable) se calcula **solo con train**.
- D10: candidatos de prueba = catálogo − (train ∪ validación) del usuario; de validación = catálogo − train (la validación NO
  excluye prueba, porque excluirla usaría la prueba).
- D11: la popularidad es `particion.popularidad_train`, nunca la columna `popularidad` de `destinos.parquet` (atributo de la
  fuente; no es fuga, pero no es la referencia decidida).
- Los grupos de actividad (total de interacciones del usuario) solo estratifican la evaluación; no entran a ningún modelo.
- Núcleo §6: una sola partición (huella SHA-256 en cada JSON).

## Qué auditar
Archivos: `src/m3_recomendacion/{referencias,metricas,experimento,hpo}.py`, `configs/m3/{base,hpo,demo}.yaml`,
`tests/test_metricas_m3.py`, y las entradas nuevas de `AJUSTES_SOLO_TRAIN` en `tests/test_fuga_m3.py`.
1. ¿Algún `ajustar` (popularidad, MF, aleatorio) o el cálculo de σ_max / L(0, 0) / guarda de degeneración usa filas de
   validación o prueba? ¿La MF crea filas de X para usuarios que solo tienen validación/prueba, o su índice depende de ellas?
2. ¿La búsqueda (`hpo.py`) lee el split de prueba en algún camino (candidatos, relevantes, objetivo, desempate, semilla)? ¿El
   modelo de cada ensayo se ajusta solo con train?
3. ¿El arnés pasa al modelo algo calculado con prueba (destinos fríos, grupos, línea base del azar, acierto por lugar)? Estas
   cosas son legítimas como **evaluación**, pero no pueden llegar a `ajustar` ni a `puntuar`.
4. ¿Las listas recomendadas excluyen el historial conocido según D10 y contienen al objetivo como candidato? ¿El desempate de
   puntajes con el `rng` puede depender del objetivo?
5. ¿El experimento verifica de verdad la huella y el SHA-256 del parquet contra `resumen.json`, y de ese archivo lee solo el
   bloque `sha256`?
6. ¿Las pruebas existentes detectarían una fuga? Escribe (en un archivo temporal fuera del repo o en el scratchpad) al menos tres
   mutantes concretos — p. ej. la MF ajustada con `split != "prueba"`, la búsqueda con candidatos de prueba, la popularidad con
   todas las interacciones — y di si la suite actual (`pytest -q tests/test_metricas_m3.py tests/test_fuga_m3.py`) los detecta.
   Restaura todo al terminar y comprueba con `git diff --stat` que no dejaste cambios. Si encuentras un hueco, **propón** la
   prueba que falta (código completo en tu informe); puedes agregarla tú a `tests/test_metricas_m3.py` solo si es una prueba
   pura que no cambia el código de producción, y dilo.

## Informe
Veredicto **SIN FUGA** / **FUGA** (con su camino exacto) / **SIN FUGA CON OBSERVACIONES**; tabla de lo revisado (punto, archivo y
línea, evidencia); resultado de los mutantes; pruebas propuestas o agregadas.
