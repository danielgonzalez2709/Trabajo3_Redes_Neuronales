# JJ-4 — prompt del orquestador (Opus 5.5) al implementador (Sonnet), 3.ª vuelta, 2026-11-27

Ajuste pequeño para cumplir el núcleo §0.7 (toda cifra del blog sale de un archivo de `results/` y se regenera con un comando):
el blog usa σ_max(P_train) = 2,871 y la cota (1 + α_min)·σ_max ≈ 5,74, que hoy solo están en un comentario del YAML.

1. Prueba primero: en `tests/test_metricas_m3.py`, que `hpo_ensayos.json` (corrida sintética) trae en `familias.mf_als` un bloque
   `cota_solucion_nula` con `sigma_max_train` (mayor valor singular de la matriz binaria usuario × destino de TRAIN, igual al de
   `np.linalg.norm(P, 2)` calculado en la prueba), `alfa_min` y `lambda_max` (del espacio), `cota` = (1 + alfa_min)·sigma_max_train
   y `lambda_max_bajo_la_cota` (bool), más una `nota` con la desigualdad L(X, Y) − L(0, 0) ≥ (λ − (1 + α)σ_max)(‖X‖² + ‖Y‖²).
   Y que el cálculo es invariante a alterar o eliminar validación y prueba (solo usa train).
2. Implementa en `hpo.py` (calcúlalo solo con train; no leas prueba). Si `lambda_max_bajo_la_cota` es falso, escribe una
   advertencia clara en consola (no un error: la guarda de degeneración ya protege).
3. Regenera solo `run.py m3-hpo --config configs/m3/hpo.yaml` y luego `run.py m3 --config configs/m3/base.yaml` (los resultados de
   la MF deben quedar idénticos a los de la 2.ª vuelta: compruébalo comparando `summary.json` antes y después, salvo tiempos) y
   `pytest -q -m "not lento"`. Pega la salida real y el bloque nuevo.

Mismas reglas de siempre. No toques el blog.
