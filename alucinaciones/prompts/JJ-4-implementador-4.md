# JJ-4 — prompt del orquestador (Opus 5.5) al implementador (Sonnet), 4.ª vuelta, 2026-11-27

R1 (2.ª vuelta) APROBÓ CON OBSERVACIONES. Corrige dos puntos (prueba primero):

**N1 (Código).** La guarda `max|x_uᵀy_i| < 1e-8` no detecta colapsos poco profundos: con los datos reales, f = 4, α = 1 y
λ/((1 + α)σ_max) = 1,05 con 5 barridos, max|S| = 8,7e-5 (no detectado). Además R1 mostró (N3) que la condición es EXACTA: si
λ < (1 + α)σ_max el origen es un punto de silla (en la dirección t(u₁e₁ᵀ, v₁e₁ᵀ), L − L(0,0) = 2t²(λ − (1 + α)σ_max) + O(t⁴) < 0) y
existe un mínimo no nulo; si λ ≥ (1 + α)σ_max, X = Y = 0 es el único mínimo global. Nueva regla en `MFImplicitaALS`:
`degenerado = (λ ≥ (1 + α)·σ_max(P_train)) or (L_final ≥ L(0, 0)) or (max|S| < tolerancia_degenerado)`, con L(0, 0) = (1 + α)·|train|
(pares únicos) y σ_max calculado SOLO con train dentro de `ajustar` (reutiliza el cálculo de `hpo.cota_solucion_nula` moviéndolo a
`referencias.py` o a una función común, sin duplicar). Expón `motivo_degenerado` (qué condición se cumplió) y guárdalo en cada
ensayo de `hpo_ensayos.json`. Pruebas: los tres motivos, cada uno por separado (incluido un caso con λ apenas por encima de la
cota y pocos barridos, donde max|S| > tolerancia pero el modelo es degenerado por la primera condición).

**N3 (texto).** En `configs/m3/hpo.yaml` y en los docstrings: la condición λ ≥ (1 + α)σ_max ⇔ «0 es el único mínimo global» es
exacta (si y solo si); lo «suficiente, no necesario» es solo el tope del espacio λ_max < (1 + α_min)σ_max (garantiza que ningún
punto del espacio colapsa, pero no hace falta que λ_max esté tan abajo para todos los α). Corrige la nota de `cota_solucion_nula`.

Regenera `run.py m3-hpo --config configs/m3/hpo.yaml`, `run.py m3 --config configs/m3/base.yaml` (los resultados deben quedar
idénticos salvo tiempos y los campos nuevos: compruébalo), la demo (con tiempo) y `pytest -q -m "not lento"`. Pega la salida real.
Mismas reglas. No toques el blog.
