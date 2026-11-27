# JJ-4 — prompt del orquestador (Opus 5.5) al redactor-tecnico (Sonnet), 4.ª vuelta, 2026-11-27

R1 (2.ª vuelta) aprobó con observaciones; aplica en `blog/secciones/07-m3-recomendacion.md` (mismas reglas):
- **N2.** «La mayor diferencia con el esperado en la [[tab:m3-resultados-k]] es la de la popularidad con K = 10» es falsa tal
  como está: en esa tabla la cobertura se aleja mucho más. Di que es la mayor diferencia **en Recall@K**.
- **N3.** La condición es exacta: λ ≥ (1 + α)σ_max ⇔ X = Y = 0 es el único mínimo global; si λ < (1 + α)σ_max, el origen es un
  punto de silla (en la dirección de los primeros vectores singulares, L − L(0, 0) = 2t²(λ − (1 + α)σ_max) + O(t⁴) < 0) y hay un
  mínimo no nulo. Lo «suficiente, no necesario» es solo el tope del espacio (λ_max < (1 + α_min)σ_max). Corrige el texto donde
  diga otra cosa.
- **Guarda.** Ahora un ajuste es degenerado si se cumple cualquiera de: λ ≥ (1 + α)σ_max(P_train), pérdida final ≥ L(0, 0)
  = (1 + α)·|train|, o max|x_uᵀy_i| < tolerancia (1e-8). Describe la regla así (sin prometer más de lo que hace) y quita
  cualquier afirmación de que la tolerancia sola basta.
- Se regeneraron búsqueda, corrida base y demo: resultados idénticos salvo **tiempos**; relee y actualiza toda cifra de tiempo.
Build estricto + `tests/test_blog.py`, salida real, informe de 3–5 líneas.
