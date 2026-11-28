# JJ-4 — evidencia: la «mejor» factorización de la búsqueda era X = Y = 0 (2026-11-27)

Candidato a la cacería (sin numerar, H-?? (JJ-4)). Categoría: **Matemáticas** (con efecto en Código). Módulo 3.

## Origen
- Prompt del orquestador (Opus 5.5) al implementador (Sonnet): `alucinaciones/prompts/JJ-4-implementador.md`, sección C5:
  «Rangos [PROPUESTO por esta tarea …]: factores 4–64, λ 1e-3–1e2, α 1–100, iteraciones 5–30».
- El implementador (Sonnet) declaró ese espacio en `configs/m3/hpo.yaml` (copia: `hpo_colapsado.yaml`), corrió la búsqueda y
  reportó como mejor el ensayo 3 (f = 8, λ = 29,542, α = 1,248, 16 barridos; NDCG@5 en validación 0,0101) sin advertir nada.
- El redactor (Sonnet) escribió en el blog que el empate de los ensayos 3, 14 y 18 «no se explica» y presentó la fila de la MF
  como una factorización normal.

## Cómo se sospechó
El verificador-matematico (Opus, R1; prompt `JJ-4-verificador-matematico.md`) recalculó la pérdida de los factores guardados y
encontró que era exactamente (1 + α)·1 066, la pérdida en X = Y = 0.

## Evidencia
- Factores guardados (`models/m3/mf_als.npz` de la 1.ª vuelta): max|X| = 6,45e-23, max|Y| = 1,31e-23 (medido por la sesión
  principal con numpy). Metadatos: `mf_als_colapsado.json`; ensayos: `hpo_ensayos_colapsado.json`.
- σ_max(P_train) = 2,871 (svds de la matriz usuario × destino de train, medido por la sesión principal).
- Derivación (Z = XYᵀ): L(X, Y) − L(0, 0) = Σ c z² − 2(1 + α)⟨P, Z⟩ + λ(‖X‖² + ‖Y‖²); con ⟨P, Z⟩ ≤ σ‖Z‖_* y
  ‖Z‖_* ≤ ½(‖X‖² + ‖Y‖²) se obtiene L(X, Y) − L(0, 0) ≥ (λ − (1 + α)σ)(‖X‖² + ‖Y‖²) > 0 si λ > (1 + α)σ, salvo en 0.
- 8 de 20 ensayos cumplen λ > (1 + α)·2,871 (1, 3, 6, 11, 12, 14, 16, 18); los 5 mejores (3, 14, 18, 11, 6) están entre ellos.
  Las listas salían del residuo numérico de una iteración de potencias (correlación 0,999999998 con una iteración de potencias
  pura, según el verificador), por eso 3, 14 y 18 (los tres con f = 8 y la misma inicialización) empataban.

## Corrección
Tope de λ por debajo de (1 + α_min)·σ_max(P_train) y guarda que marca como degenerado todo ajuste con max|x_uᵀy_i| < tolerancia
(nunca puede ser el mejor ensayo; el experimento falla si la MF final es degenerada). Prompt: `JJ-4-implementador-2.md`.

## Lección
Una búsqueda que maximiza una métrica sobre datos casi aleatorios puede premiar una solución degenerada que «empata» con el azar.
Verificación que lo habría evitado: mirar la norma de los factores (o la pérdida frente a L(0, 0)) del mejor ensayo y acotar la
regularización con la escala de los datos antes de declarar el espacio.
