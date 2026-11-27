# JJ-4 — prompt del orquestador (Opus 5.5) al revisor-spec (Sonnet), 2026-11-27

Revisa que la tarea JJ-4 del Trabajo 3 (M3: popularidad + filtrado colaborativo clásico + métricas @K) cumpla EXACTAMENTE el Spec
y el enunciado, ni más ni menos. Rama `dev/juanjose`; solo lees (no edites nada). Siempre `.venv\Scripts\python`.

## Contra qué revisas
- Anexo de `docs/spec/SPEC.md`, «Módulo 3»: tarea 4 («Ajusten una recomendación basada en popularidad y un filtrado colaborativo
  clásico (vecinos más cercanos o factorización de matrices)»), tarea 6 en su parte de métricas (Precision, Recall y NDCG@K,
  cobertura del catálogo, desempeño separado para usuarios con pocas y muchas interacciones), «Regla de comparación justa» y
  «Fundamentación matemática del módulo» (formulación de la factorización; definición de Precision, Recall, NDCG y cobertura).
- Núcleo: §0 (reglas 4, 6, 7), §4.1 (comandos `m3`/`m3-hpo`; claves de cambio en vivo `evaluacion.k` y `semillas.n`), §5.7, §5.9
  (`summary.json` con `media, desviacion, mejor, peor`, `n_parametros`, `n_configuraciones_busqueda`, `tiempo_total_s`, `device`,
  `evidencia`; `semillas/<modelo>_seed<k>.json`; `hpo_ensayos.json`), §6, §7.1 (demo < 2 min, sin internet, semillas,
  modelos guardados).
- `docs/spec/partes/juanjose.md`: D9, D10 (§3.1), D11, D13, D14 (§3.2) y D12 (§3.3).

## Qué revisar
- Código: `src/m3_recomendacion/{metricas,referencias,experimento,hpo}.py`; configs `configs/m3/{base,hpo,demo}.yaml`; pruebas
  `tests/test_metricas_m3.py` y las entradas nuevas de `AJUSTES_SOLO_TRAIN` en `tests/test_fuga_m3.py`.
- Salidas: `results/data/m3/{summary.json, metricas_por_k.json, metricas_por_grupo.json, hpo_ensayos.json,
  recomendaciones_prueba.parquet, semillas/}` y `models/m3/{mf_als.npz, mf_als.json}`.
- Blog: `blog/secciones/07-m3-recomendacion.md`, subsecciones «### Métricas de evaluación» y «### Modelos de referencia»
  (deben ir después de «### Partición»; tablas con `::: tabla`, título, fuente y citadas; sin rutas en las frases; sin
  conclusiones sobre la red; Hu, Koren y Volinsky (2008) sin `[@…]` y con `TODO(cita)`).
- Ejecuta: `.venv\Scripts\python run.py m3 --config configs/m3/demo.yaml` (mide que tarde < 2 min y que escriba solo en
  `results/data/m3_demo/` y `models/m3_demo/`), `.venv\Scripts\python run.py m3 --config configs/m3/demo.yaml --set
  evaluacion.k=3 --set semillas.n=2` y `.venv\Scripts\python -m pytest -q tests/test_metricas_m3.py tests/test_fuga_m3.py`. No
  corras la base ni la búsqueda (pisarían resultados versionados; si quieres, compara con `git status` que no cambió nada).

## Contexto de la revisión
R1 (verificador-matematico) aprobó tras tres vueltas: en la 1.ª la MF elegida era X = Y = 0 (λ fuera de la región útil); se
acotó λ ≤ 5,0 por debajo de (1 + α_min)σ_max(P_train) y se agregó una guarda de degeneración. R2 (auditor-fugas): sin fuga, con 3
pruebas agregadas. Decisiones [PROPUESTO] que siguen abiertas para Juan José (no son incumplimientos): rangos del espacio, tope de
λ, tolerancia 1e-8, semilla del sampler, `n_parametros` de la popularidad = 1 000 conteos.

## Informe
Veredicto **APROBADO** / **RECHAZADO**; lista de incumplimientos (requisito, dónde, evidencia, gravedad) y de cosas de más (lo
que no pide el Spec); estado de cada decisión D9–D14 (cumple / no cumple / parcial) y de cada requisito del Anexo revisado.
