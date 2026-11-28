# JJ-4 — prompt del orquestador (Opus 5.5) al verificador-matematico (Opus), 2.ª vuelta, 2026-11-27

Tu primera verificación de JJ-4 fue RECHAZADO por H1 (la MF elegida era X = Y = 0), con H2–H6 menores. Se corrigió así:
- `configs/m3/hpo.yaml`: λ ∈ [1e-3, 5,0]; `hpo.py` escribe `familias.mf_als.cota_solucion_nula` (σ_max de train, α_min, λ_max,
  cota) en `results/data/m3/hpo_ensayos.json`.
- Guarda de degeneración (`mf_als.tolerancia_degenerado` = 1e-8 sobre max|x_uᵀy_i|): un ensayo degenerado se poda y nunca es el
  mejor; el experimento falla si la MF final es degenerada. Pruebas nuevas en `tests/test_metricas_m3.py`.
- `n_parametros_con_datos` en `summary.json`.
- Búsqueda y corridas regeneradas (mejor: ensayo 19, f = 4, λ ≈ 0,0021, α ≈ 1,485, 9 barridos) y blog actualizado (H1–H6).

Mismas reglas (solo lees y calculas; scripts en el scratchpad que ya usaste, sin importar `src/`). Verifica:
1. **H1 cerrado**: la MF final de `models/m3/mf_als.npz` no es degenerada (normas, max|XYᵀ|, pérdida frente a L(0, 0) =
   (1 + α)·|train|), su pérdida coincide con el último valor de `historial_perdida` y éste no crece; ningún ensayo de
   `hpo_ensayos.json` está en la región λ > (1 + α)σ_max y `cota_solucion_nula` es correcta (recalcula σ_max solo con train).
   Recalcula con tu ALS denso el NDCG@5 en validación del mejor ensayo. Revisa que la guarda y sus pruebas tengan sentido (¿una
   tolerancia absoluta de 1e-8 detecta el colapso en esta escala? ¿la cota de la prueba sintética es correcta?).
2. **Métricas** recalculadas de forma independiente desde `recomendaciones_prueba.parquet` contra `semillas/*.json`,
   `summary.json`, `metricas_por_k.json` y `metricas_por_grupo.json` (como en la 1.ª vuelta; reporta la diferencia máxima).
3. **Blog** (`blog/secciones/07-m3-recomendacion.md`, «Métricas de evaluación» y «Modelos de referencia»): la derivación de la
   cota de la solución nula, las cotas de Gini/HHI dependientes de K, los errores estándar y el de la diferencia, los rangos y
   multiplicaciones del texto, las cifras de cada tabla frente a su «Fuente:», y que no quede ninguna cifra o frase de la corrida
   colapsada presentada como resultado vigente.

Informe: veredicto (APROBADO / APROBADO CON OBSERVACIONES / RECHAZADO), estado de H1–H6 (cerrado / abierto) y hallazgos nuevos
con archivo, línea, evidencia y gravedad.
