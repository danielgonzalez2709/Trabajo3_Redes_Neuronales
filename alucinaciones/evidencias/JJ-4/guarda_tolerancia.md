# JJ-4 — evidencia: la tolerancia 1e-8 no detecta colapsos poco profundos (2026-11-27)

Tomado del informe del verificador-matematico (Opus), R1 2.ª vuelta (N1 y N3), con su ALS denso propio (sin importar `src/`)
sobre los datos reales (f = 4, α = 1). S = XYᵀ.

| λ / ((1 + α)σ_max) | Barridos | max|S| | ¿Lo detecta max|S| < 1e-8? |
|---|---|---|---|
| 1,05 | 5 | 8,7e-5 | no |
| 1,2 | 5 | 7,0e-6 | no |
| 1,5 | 5 | 1,0e-7 | no |
| 1,05 | 30 | 8,1e-7 | no |
| 2,0 | 5 | 4e-10 | sí |

Condición exacta (N3): en la dirección (X, Y) = t(u₁e₁ᵀ, v₁e₁ᵀ), con u₁, v₁ los primeros vectores singulares de P_train,
L − L(0, 0) = 2t²(λ − (1 + α)σ_max) + O(t⁴). Si λ < (1 + α)σ_max el origen es un punto de silla y hay un mínimo no nulo (corrida
con cociente 0,95 y 30 barridos: L − L(0, 0) = −0,045); si λ ≥ (1 + α)σ_max, 0 es el único mínimo global. Por tanto «la cota es
suficiente, no necesaria» era incorrecto para la condición (solo vale para el tope del espacio).

En la 3.ª vuelta el verificador reprodujo el caso 1,05 / 5 barridos con la regla corregida: degenerado por `lambda_ge_cota`.
