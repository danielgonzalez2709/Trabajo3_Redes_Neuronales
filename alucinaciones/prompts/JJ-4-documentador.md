# JJ-4 — prompt del orquestador (Opus 5.5) al documentador (Sonnet), 2026-11-27

Actualiza `docs/MEMORIA.md` por el cierre de JJ-4 (M3: referencias + métricas @K). Reglas: ≤ 150 líneas en total; **no borres
nada de otros integrantes** (Daniel, Camila, Andrés, José); puedes condensar líneas de Juan José ya cerradas para hacer espacio;
no inventes cifras (todas las de abajo están medidas; si dudas, léelas de `results/data/m3/summary.json` y `hpo_ensayos.json`).
Solo editas `docs/MEMORIA.md`.

1. **Estado** — nueva viñeta (después de JJ-3): JJ-4 terminado en `dev/juanjose` el vie 27, pendiente de PR. `run.py m3-hpo
   --config configs/m3/hpo.yaml` (Optuna TPE, 20 ensayos, NDCG@5 en validación; mejor ensayo 19: f = 4, λ ≈ 0,0021, α ≈ 1,485, 9
   barridos; 0 degenerados) y `run.py m3 --config configs/m3/base.yaml` (popularidad de train, MF implícita por ALS y aleatorio;
   30 semillas; `summary.json`, `semillas/` (90), `metricas_por_k.json`, `metricas_por_grupo.json`, `hpo_ensayos.json`,
   `recomendaciones_prueba.parquet` en `results/data/m3/`; factores en `models/m3/`). Demo `configs/m3/demo.yaml` (< 2 min; escribe
   en `results/data/m3_demo/`). Resultados al nivel del azar (Recall@10: popularidad 0,0069, MF 0,0105, aleatorio 0,0096,
   esperado 0,0100; diferencias menores que el error estándar de 606 usuarios); cobertura@10: 0,025 / 0,101 / 0,997. Revisado por
   verificador-matematico (APROBADO en la 3.ª vuelta), auditor-fugas (SIN FUGA CON OBSERVACIONES; 3 pruebas agregadas),
   revisor-spec (APROBADO) y revisor-calidad (APROBADO en la 2.ª vuelta). Blog 07: «Métricas de evaluación» y «Modelos de
   referencia».
2. **Decisiones vigentes** — viñeta M3 [DECIDIDO, Juan José, 27-nov; `juanjose.md` §3.2–§3.3, D11–D14]: referencias = popularidad
   de train (empates al azar), MF implícita por ALS (Hu, Koren y Volinsky, 2008 [VERIFICAR en JJ-9]) y aleatorio con esperado
   analítico; Recall@K = acierto@K y Precision@K = acierto@K/K (1 relevante por usuario); cobertura /1 000; Gini y HHI de
   exposiciones; acierto por lugar solo K ∈ {1, 3} con línea base; búsqueda 20 ensayos NDCG@5 en validación; 30 semillas.
   Añade: λ ≥ (1 + α)σ_max(P_train) ⇔ X = Y = 0 es el único mínimo (tope λ ≤ 5,0 y guarda de degeneración de tres condiciones).
3. **Avisos para el equipo** — M3/JJ-5: la red se agrega con una entrada en `referencias.MODELOS`, una en `hpo.BUSQUEDAS` y un bloque
   `<nombre>:` en la config, sin tocar `experimento.py`; su `diagnosticos()` debe traer `degenerado`; hoy el bloque `busqueda:` es de
   la MF (la red necesita su propio espacio). El PR de JJ-4 debe incluir `results/data/m3/*` y `models/m3/*` (las pruebas reales los
   leen).
4. **Pendientes** (punto 4, Juan José) — agrega: decidir lo [PROPUESTO] de JJ-4 (rangos del espacio, tope λ = 5,0, tolerancia 1e-8,
   semilla del sampler 2026, `n_parametros` de la popularidad = 1 000 conteos, respaldo de la MF 16/0,1/10/10, grupo vacío como
   `{"n_usuarios": 0}`); la guarda propuesta por el auditor-fugas en `test_fuga_m3.py` (los modelos no abren archivos ni leen salidas
   de evaluación) y poner `Aleatorio` en `AJUSTES_SOLO_TRAIN`; menores de calidad abiertos (N1 precedencia de
   `ejecutar_en_experimento` frente a `hiperparametros_desde: config`, N3 `diagnosticos["degenerado"]` obligatorio, N5 nota de la
   cota duplicada, N6–N8); el mejor λ quedó cerca del límite inferior (1e-3) del rango; Hu et al. (2008): DOI 10.1109/ICDM.2008.22
   según el verificador, verificar en JJ-9 antes de citar.
5. **Cacería** — agrega: 3 candidatos de M3 de JJ-4 (sin número): «la mejor MF era X = Y = 0» (Matemáticas; origen en el prompt del
   orquestador Opus, no detectado por implementador y redactor Sonnet); «la tolerancia 1e-8 detecta el colapso / la cota es
   suficiente, no necesaria» (Código, menor); afirmaciones numéricas del redactor en la lectura de resultados (Matemáticas, menor);
   evidencia en `alucinaciones/evidencias/JJ-4/`.
6. **Bitácora** — línea nueva arriba: «2026-11-27 · Juan José · JJ-4 ✅: popularidad, MF implícita por ALS y aleatorio con métricas
   @K (30 semillas, 20 ensayos), blog 07 «Métricas de evaluación» y «Modelos de referencia»; MF colapsada a X = Y = 0 detectada y
   corregida; D11–D14; 3 candidatos a la cacería.»
