# JJ-5 — prompt literal del orquestador (Opus 5.5) al verificador-matematico (Opus), 2.ª vuelta, 2026-11-27

Segunda vuelta corta de tu verificación de JJ-5 (repositorio `C:\Repositorios\Trabajo3_Redes_Neuronales`). El implementador aplicó
tu corrección del candidato «`personalizacion` no mide personalización» y tus observaciones O1 y O2. No modifiques código ni
resultados. **Usa solo numpy/pandas (no cargues torch)**: hay otro agente corriendo procesos con torch y la memoria libre es escasa.

Verifica:
1. `src/m3_recomendacion/red.py`, función `medidas_personalizacion` (~línea 308) y su uso en `_calcular_diagnosticos` (~567):
   la descomposición S = μ + α_u + β_i + E, `personalizacion = E.std(axis=0).mean()`, `fraccion_varianza_interaccion = ‖E‖²/‖S − μ‖²`,
   `listas_top10_distintas` y `fraccion_mismo_top1`; que el comentario sea matemáticamente correcto; casos borde (S constante,
   un solo usuario, empates en el top-10).
2. Las pruebas nuevas de `tests/test_red_m3.py` (~400–430): que el valor «a mano» de la interacción pura S = u vᵀ (personalización
   = √2,5 · media|v_i|) sea correcto; rehaz la cuenta.
3. `descripcion_frios` (~390): que ya no afirme nada falso.
4. `results/data/m3/summary.json` → `modelos.red.diagnosticos`: que las cifras nuevas sean coherentes con tu cálculo propio de la
   semilla 8 de la primera vuelta (tus scripts están en
   `C:\Users\juanj\AppData\Local\Temp\claude\92481566dd5b376c\7690fb16-ed9d-4177-8666-ce080137b320\scratchpad\jj5\`), y que las métricas
   de los 4 modelos no cambiaron.

Reporte: APROBADO / RECHAZADO, con evidencia (`archivo:línea`, cifras).
