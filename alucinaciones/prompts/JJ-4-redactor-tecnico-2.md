# JJ-4 — prompt del orquestador (Opus 5.5) al redactor-tecnico (Sonnet), 2.ª vuelta, 2026-11-27

El verificador-matematico (R1) rechazó JJ-4 por un hallazgo bloqueante en el CÓDIGO, ya corregido y regenerado. Tienes que
actualizar «### Métricas de evaluación» y «### Modelos de referencia» de `blog/secciones/07-m3-recomendacion.md`. Mismas reglas
de la primera vuelta (solo este archivo; cifras leídas de los JSON; sin rutas en las frases; `::: tabla` citadas; Hu et al. en
prosa con `TODO(cita)`; nada sobre la red; interpretaciones con `<!-- revisar: Juan José — … -->`).

## Qué cambió en los resultados (relee TODOS los JSON: casi todas las cifras de la MF cambiaron)
- **H1 (corregido).** En la primera búsqueda, la mejor factorización era la solución trivial X = Y = 0: con λ > (1 + α)·σ_max,
  donde σ_max es el mayor valor singular de la matriz de interacciones de entrenamiento (2,871, medido solo con train), el único
  mínimo global de la pérdida es X = Y = 0 (cota: L(X, Y) − L(0, 0) ≥ (λ − (1 + α)σ_max)(‖X‖² + ‖Y‖²)). 8 de los 20 ensayos
  estaban en esa región, entre ellos los 5 mejores; sus listas salían del residuo numérico (por eso empataban los ensayos 3, 14 y
  18). Ahora: el tope de λ es 5,0 (< (1 + α_min)·σ_max ≈ 5,74) y una guarda marca como degenerado todo ajuste con puntajes
  máximos por debajo de una tolerancia; un ensayo degenerado nunca puede ser el mejor y el experimento falla si la MF final lo es.
  Nueva búsqueda: 0 degenerados; mejor ensayo y parámetros en `hpo_ensayos.json`.
- Escríbelo en el blog en pocas líneas, dentro de la búsqueda declarada: la cota (con su derivación de una línea:
  ⟨P, XYᵀ⟩ ≤ σ_max‖XYᵀ‖_* y ‖XYᵀ‖_* ≤ ½(‖X‖² + ‖Y‖²)), por qué se acotó λ y la guarda. Puedes decir que en una primera corrida
  la búsqueda eligió la solución nula y que se detectó al verificar la pérdida de los factores (es parte de la metodología). Borra
  las frases que ya no son ciertas: «el empate de 3, 14 y 18 no se explica», «el mejor λ en el interior», y toda cifra vieja.
- `summary.json` trae ahora `n_parametros_con_datos` para la MF: explica en la tabla de presupuesto que (n_usuarios + n_destinos)·f
  incluye las filas de los destinos sin entrenamiento, que son 0 por construcción, y da también la cifra con datos (H5).

## Observaciones menores de R1 que debes aplicar (comprueba cada cifra con los JSON nuevos)
- H2: el rango de las diferencias frente al piso que escribiste («de 0,0004 a …») no era el mínimo real; recalcúlalo con las
  cifras nuevas o reescribe sin un rango que no hayas calculado.
- H3: las cotas de Gini y HHI dependen de K: con listas de K destinos distintos para |U| usuarios sobre n destinos, lo alcanzable es
  Gini ≤ 1 − K/n y HHI ≤ 1/K (y con K = 1 y |U| = 606, HHI ≥ 1/606). Corrige «Gini hasta 0,999; HHI de 0,001 a 1» y, si aplica,
  di qué tan cerca del máximo alcanzable queda la popularidad.
- H4: «de 1 a 3 aciertos por grupo» → recalcula (media × n_usuarios del grupo) con las cifras nuevas y escribe el rango real.
- H6: si comparas dos modelos, el error estándar de la diferencia es √(SE₁² + SE₂²), no el SE de uno solo; la cifra de
  validación del mejor ensayo es de una sola semilla y de una población distinta (solo «muchas»).

## Comprobación
`.venv\Scripts\python -m mkdocs build --strict -f blog/mkdocs.yml` y `.venv\Scripts\python -m pytest -q tests/test_blog.py`; pega
la salida real. Informe breve: qué cambiaste, las cifras nuevas de cada tabla y su clave de JSON, y lo marcado como `revisar`.
