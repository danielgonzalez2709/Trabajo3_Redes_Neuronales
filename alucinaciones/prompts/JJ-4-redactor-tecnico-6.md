# JJ-4 — prompt del orquestador (Opus 5.5) al redactor-tecnico (Sonnet), 6.ª vuelta, 2026-11-27

Última corrida (definitiva; no se volverá a regenerar antes del PR). En `blog/secciones/07-m3-recomendacion.md`:
1. Cambió el formato de `summary.json`: `n_parametros_con_datos` y `max_abs_puntaje` ya no están en la raíz del bloque del
   modelo; ahora van en `modelos.<modelo>.diagnosticos.<clave>` resumidos entre semillas (`media, desviacion, minimo, maximo, n`).
   Corrige las líneas «Fuente:» (y comentarios) que citan esas claves; las cifras (6 052; 0,805 y 0,028) no cambian, compruébalo.
   `metricas_por_grupo.json` ahora trae `mejor, peor, n` por métrica (si la «Fuente:» lo describe, ajústala).
2. Relee y actualiza TODA cifra de tiempo (tabla de presupuesto y lectura de resultados) desde `summary.json`
   (`tiempo_total_s`, `tiempo_busqueda_s`, `tiempo_corridas_finales_s`) y `hpo_ensayos.json`.
No cambies ninguna otra cifra. Build estricto + `tests/test_blog.py`; informe de 3 líneas.
