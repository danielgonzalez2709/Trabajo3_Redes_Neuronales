# M3 — Recomendación de destinos de viaje

- **Dueño (núcleo §1.1):** Juan José. Módulos: `datos.py` (JJ-1), `eda.py`, `eda_estadistica.py`, `eda_hipotesis.py` (JJ-2),
  `particion.py` (JJ-3), `metricas.py`, `referencias.py`, `hpo.py`, `experimento.py` (JJ-4), `contenido.py`, `red.py` (JJ-5).
  Pendientes: `negocio.py` (JJ-6) y `exportar.py` (JJ-7).
- **Comandos** (siempre con `.venv\Scripts\python`; ninguno usa internet):
  - `run.py m3-datos --config configs/m3/datos.yaml` — crudo → `data/processed/m3/` y partición (< 10 s).
  - `run.py m3-eda --config configs/m3/eda.yaml` — análisis descriptivo (unos 5 s).
  - `run.py m3-hpo --config configs/m3/hpo.yaml` — búsqueda Optuna (TPE, semilla 2026, 20 ensayos por familia, NDCG@5 en
    validación) de la MF (`mf_als`) y de la red (`red`); escribe `results/data/m3/hpo_ensayos.json`.
  - `run.py m3 --config configs/m3/base.yaml` — 30 semillas × 4 modelos (popularidad, MF, aleatorio, red), una evaluación en
    prueba; la MF y la red usan los hiperparámetros de la config (copia exacta del mejor ensayo de `m3-hpo`; si coinciden,
    `summary.json` reporta el presupuesto de la búsqueda).
  - `run.py m3 --config configs/m3/demo.yaml` — demo en vivo (< 2 min en CPU): 3 semillas × 4 modelos; la MF se busca en vivo
    con 4 ensayos y la red usa los bloques de la config (`red.hiperparametros_desde: config`). Escribe en
    `results/data/m3_demo/` y `models/m3_demo/` (no versionados).
  - `run.py figures` — las 4 figuras del descriptivo y las 4 de los modelos en `blog/docs/figures/m3/`.
- **Claves en vivo (núcleo §4.1):** `--set modelo.dim_embedding=8`, `--set modelo.negativos_por_positivo=1`,
  `--set perdida.tipo=bpr`, `--set evaluacion.k=3`, `--set semillas.n=5`; funcionan con `base.yaml` y con la demo (las dos usan
  `config` para la red). Un `--set` sobre un hiperparámetro buscado hace que ese modelo se reporte con 1 configuración y 0 s; uno
  sobre un fijo (no buscado) no cambia el presupuesto reportado, porque `hpo_ensayos.json` no guarda los fijos.
- **Configs:** `configs/m3/datos.yaml` (fuente, citas, partición), `eda.yaml` (descriptivo), `base.yaml` (evaluación, MF y los
  bloques `modelo`, `perdida`, `entrenamiento`, `regularizacion` y `red` de la red), `hpo.yaml` (espacios de búsqueda:
  `busqueda.espacio` de la MF y `red.busqueda.espacio` de la red), `demo.yaml`.
- **Datos:** `data/processed/m3/{destinos,usuarios,interacciones}.parquet` (núcleo §5.7; `split` ∈ {`train`, `validacion`,
  `prueba`}, una sola partición para todos los modelos) y `results/data/m3/particion/resumen.json` (huella y SHA-256). `Name`,
  `Email` y `ReviewText` no pasan a ninguna salida.
- **Red de dos torres (JJ-5, D15–D19 de `docs/spec/partes/juanjose.md` §3.2):** `contenido.py` arma el contenido (tipo del
  destino y preferencias del usuario, one-hot con orden fijo) leyendo solo `destinos.parquet` y `usuarios.parquet`; `red.py`
  tiene las torres (`TorreUsuario`, `TorreDestino`, `DosTorres`), las pérdidas `perdida_bce` y `perdida_bpr`, el muestreo de
  negativos, `train_loop` / `val_loop` y el recomendador `RedDosTorres` (la formulación está en su docstring).
- **Resultados (núcleo §5.9) en `results/data/m3/`:** `summary.json`, `semillas/<modelo>_seed<k>.json`, `metricas_por_k.json`,
  `metricas_por_grupo.json`, `recomendaciones_prueba.parquet`, `hpo_ensayos.json`, `curvas/red.json` (pérdidas y NDCG@5 de
  validación por época, mejor época y parada temprana) y `arquitectura/red.json` (capas, formas, activaciones, parámetros).
  Modelos en `models/m3/`: `mf_als.{npz,json}` y `red.{pt,json}` (state_dict; columnas one-hot y mapas de id para la
  exportación de JJ-7), de la semilla `base_seed + 0`.
- **Pruebas:** `tests/test_datos_m3.py`, `tests/test_eda_m3.py`, `tests/test_fuga_m3.py` (partición y guardas de fuga de todos
  los modelos, incluidas `AJUSTES_SOLO_TRAIN` y `AJUSTES_SIN_PRUEBA`), `tests/test_metricas_m3.py` (métricas, referencias y
  arnés) y `tests/test_red_m3.py` (red: formas, parámetros, pérdidas a mano y por diferencias finitas, negativos, determinismo,
  parada temprana, claves en vivo y punta a punta).
- **Notebook:** `notebooks/05_m3` — pendiente (JJ-10).
