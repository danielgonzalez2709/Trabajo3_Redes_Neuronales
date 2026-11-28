# JJ-4 — prompt del orquestador (Opus 5.5) al redactor-tecnico (Sonnet), 3.ª vuelta, 2026-11-27

Dos ajustes en `blog/secciones/07-m3-recomendacion.md` (mismas reglas):
1. σ_max(P_train) = 2,871, α_min, λ_max y la cota (1 + α_min)·σ_max ahora están en `results/data/m3/hpo_ensayos.json`,
   `familias.mf_als.cota_solucion_nula` (`sigma_max_train`, `alfa_min`, `lambda_max`, `cota`, `lambda_max_bajo_la_cota`). Toma
   de ahí esas cifras, cita esa clave en la «Fuente:» de la tabla que corresponda (o agrega una fila a la tabla de la búsqueda) y
   quita el `revisar` que decía que no estaban en un JSON. Los factores ~1e-23 y la pérdida L(0, 0) de la primera corrida siguen
   sin estar en `results/`: déjalos como hecho de la metodología sin cifra, o con la cifra marcada como de la verificación (su
   evidencia está fuera de `results/`); no las presentes como resultado regenerable.
2. Se regeneró la búsqueda y la corrida base: los resultados son idénticos salvo los **tiempos**. Relee `tiempo_total_s` y
   los tiempos de búsqueda y corridas de `summary.json` y `hpo_ensayos.json` y actualiza toda cifra de tiempo del texto y las
   tablas.
Comprueba con el build estricto y `tests/test_blog.py` y pega la salida. Informe de 3–5 líneas.
