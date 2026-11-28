# JJ-4 — prompt del orquestador (Opus 5.5) al verificador-matematico (Opus), 3.ª vuelta, 2026-11-27

Comprobación corta de las correcciones de tus observaciones N1–N3 (mismas reglas: solo lees y calculas):
- **N1/N3 (código):** `src/m3_recomendacion/referencias.py` (`sigma_max_train`, regla `degenerado` = λ ≥ (1 + α)σ_max(P_train)
  o L_final ≥ L(0, 0) = (1 + α)|train| o max|S| < tolerancia, `motivo_degenerado`), `hpo.py` (`cota_solucion_nula` y su `nota`),
  comentarios de `configs/m3/hpo.yaml` y `base.yaml`, y las pruebas nuevas de `tests/test_metricas_m3.py` sobre los tres motivos.
  σ_max ahora sale de `scipy.sparse.linalg.svds` (k = 1, arranque fijo): ¿es fiable y determinista aquí? Reproduce con tu ALS el
  caso λ = 1,05·(1 + α)σ con 5 barridos y comprueba que ahora se marca degenerado.
- Resultados regenerados (dicen ser idénticos salvo tiempos): confirma con `recomendaciones_prueba.parquet`, `summary.json` y
  `models/m3/mf_als.npz` que nada de las métricas ni los factores cambió respecto de lo que verificaste en la 2.ª vuelta.
- **N2/N3 (blog):** `blog/secciones/07-m3-recomendacion.md`, el párrafo de la solución nula, la descripción de la guarda, la
  frase de «la mayor diferencia en Recall@K» y las cifras de tiempo de la tabla de presupuesto frente a `summary.json`.
Informe: veredicto y estado de N1–N3; cualquier hallazgo nuevo con archivo, línea y evidencia.
