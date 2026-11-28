# JJ-5 — prompt literal del orquestador (Opus 5.5) al verificador-matematico (Opus), 4.ª vuelta, 2026-11-27

Cuarta vuelta, muy corta (repositorio `C:\Repositorios\Trabajo3_Redes_Neuronales`). El orquestador aplicó tus dos correcciones de
la 3.ª vuelta. No modifiques nada; solo numpy/pandas (no cargues torch; extrae la función con `ast` como antes).

1. `src/m3_recomendacion/red.py`, `medidas_personalizacion`: denominador = ‖E‖² + n_destinos·‖α‖² + n_usuarios·‖β‖² (tu arreglo de
   `jj5c\x2_arreglo.py`), guarda `ptp == 0`, y el docstring nuevo (casi constante = ruido de redondeo; NaN; ≈ 1e-30 a 1e-27). Corre
   tus 75 casos de `jj5c\x1_frac.py` contra la función nueva: ¿todos en [0, 1]? ¿Mismo valor en S genérica y en S0?
2. `tests/test_red_m3.py`: `test_personalizacion_con_puntajes_casi_constantes_queda_en_cero_uno` y
   `test_la_fraccion_con_la_descomposicion_es_la_misma_en_una_matriz_generica`.
3. `descripcion_frios`: «Pueden superar a destinos con train; si entran o no al top-K depende del entrenamiento, así que se MIDE en
   `frios_por_lista`.» (tu texto).

`summary.json` todavía tiene el texto anterior: el orquestador vuelve a correr el experimento al final y lo compara él. No lo revises.

Reporte: APROBADO / RECHAZADO con evidencia.
