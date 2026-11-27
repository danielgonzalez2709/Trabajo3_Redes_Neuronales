# JJ-4 — prompt del orquestador (Opus 5.5) al implementador (Sonnet), 2026-11-27

Tarea JJ-4 del Trabajo 3: **modelos de referencia de M3 (popularidad, factorización de matrices implícita por ALS, aleatorio)
y métricas @K**. Te dirige la sesión principal de Juan José, rama `dev/juanjose`. **Prueba primero, luego código.**

## Reglas
- NO commits, NI push, NI PR. Siempre `.venv\Scripts\python` (en Bash: `.venv/Scripts/python`). Sin internet.
- Nada de librerías nuevas: numpy, scipy, pandas, optuna (ya están en requirements.txt). No toques `requirements.txt`,
  `src/comun/`, `run.py`, `docs/spec/SPEC.md`, `tests/test_no_network.py` ni archivos de otros integrantes.
- Archivos que SÍ puedes crear/editar: `src/m3_recomendacion/{metricas,referencias,experimento,hpo}.py`,
  `configs/m3/{base,hpo,demo}.yaml`, `tests/test_metricas_m3.py`, `tests/test_fuga_m3.py` (solo para agregar entradas a
  `AJUSTES_SOLO_TRAIN`, nada más), y las salidas `results/data/m3/*` y `models/m3/*`.
- **Prohibido inventar** cifras, constantes, referencias o resultados. Si algo falta: `TODO(dato-faltante)` y repórtalo.
  La cita de Hu, Koren y Volinsky (2008) va como texto con `[VERIFICAR]`, **sin DOI**.
- Docstrings y comentarios en español. Funciones puras donde se pueda; toda aleatoriedad llega por un
  `np.random.Generator` recibido, creado con `src.comun.seeds.make_rng(base_seed, run_id)`; nunca `np.random.seed`.
- Usa `src.comun.results.save_json` / `load_json` para los JSON (rechaza NaN).
- Si algo de este prompt choca con el Spec o con lo que mides en los datos, DETENTE y repórtalo en vez de improvisar.

## Contexto que debes leer (solo esto)
- `docs/spec/SPEC.md`: §4.1 (comandos y claves de cambio en vivo: M3 `evaluacion.k`, todos `semillas.n`), §5.7, §5.9, §6,
  §7.1 y el Anexo «Módulo 3» (tareas 4 y 6, «Regla de comparación justa», «Fundamentación matemática del módulo»).
- `docs/spec/partes/juanjose.md` §3.1 (D1–D10), §3.2 (D11, D13, D14) y §3.3 (D12).
- `src/m3_recomendacion/particion.py` (usa `popularidad_train`, `historial_conocido`, `relevantes`, `candidatos`, `huella`,
  constantes `TRAIN/VALIDACION/PRUEBA`).
- `tests/test_fuga_m3.py` líneas ~515–570 (`AJUSTES_SOLO_TRAIN`, `PROHIBIDAS_PARA_MODELOS`, la guarda estática).
- `results/data/m3/particion/resumen.json` (solo su bloque `sha256` puede leerse desde código de modelos).
- `src/comun/{config,seeds,results,cli}.py`; `src/m3_recomendacion/eda_estadistica.py` (funciones `gini`, `hhi`).
- `configs/m3/datos.yaml` y `configs/m3/eda.yaml` (estilo de comentarios que debes imitar).

## Datos medidos (no los copies en el código: el código los recalcula; úsalos para comprobar)
- `data/processed/m3/interacciones.parquet`: 1 998 filas, columnas `usuario_id, destino_id, origen, id_origen, calificacion,
  fecha_visita, split`; split: 1 066 train / 326 validación / 606 prueba. 858 usuarios con interacciones (todos con ≥ 1 en
  train), 606 evaluables en prueba (1 destino de prueba cada uno), 326 en validación (1 cada uno).
- `destinos.parquet`: 1 000 destinos, columnas `destino_id, nombre, lugar, estado, tipo, mejor_epoca, popularidad`. **La
  columna `popularidad` es un atributo de la fuente y NO la usa ningún modelo de JJ-4.** `lugar` tiene 5 valores.
- 205 de las 606 interacciones de prueba son de destinos sin ninguna interacción en train («destinos fríos»).
- Grupos de actividad (total de interacciones del usuario, train + validación + prueba): pocas = 1..2, muchas ≥ 3. En prueba:
  280 usuarios de «pocas» y 326 de «muchas».

## Guardas existentes que tu código debe respetar (si no, falla la CI)
- `test_ningun_modelo_de_m3_lee_estadisticas_calculadas_con_todas_las_interacciones` busca en todo archivo nuevo de
  `src/m3_recomendacion/` los textos de `PROHIBIDAS_PARA_MODELOS`, entre ellos **`grupo_actividad`**, **`items_frios`**,
  `results/data/m3/eda`, `actividad_usuarios`, `distribucion_actividad`, `concentracion.json`, `particion_d3`,
  `mismo_lugar_en_historial_conocido`, `interacciones_por_destino`, `interacciones_por_usuario`. **No escribas esos textos en
  tus archivos** (ni en comentarios). Usa p. ej. `grupo` / `por_grupo` y `destinos_frios`.
- De `resumen.json` solo se lee el bloque `sha256` (para la `evidencia`).

## Decisiones vigentes que implementas (texto completo en juanjose.md)
D9 (solo train para ajustar; HPO con validación; finales evaluados una vez en prueba), D10 (candidatos = catálogo − historial
conocido; prueba: train ∪ validación; validación: train), D11, D12, D13, D14.

## Qué construir

### C1. `tests/test_metricas_m3.py` (primero; córrelo y míralo fallar antes de escribir el código)
1. Cada métrica contra un cálculo a mano en ejemplos pequeños (escribe el cálculo en el comentario): acierto@K, Precision@K,
   Recall@K, NDCG@K (con un relevante en el rango 1, 2, 3 y fuera del top-K; y un caso general con |R| = 2 para fijar la IDCG),
   un **usuario sin acierto**, y un **empate** de puntajes (el desempate al azar es determinista con la misma semilla y cambia
   con otra; ningún candidato se pierde ni se repite).
2. Cobertura, exposiciones, Gini y HHI de las exposiciones a mano (p. ej. 3 usuarios, catálogo de 5, top-2).
3. Aleatorio: el valor esperado analítico ≈ la media simulada (p. ej. 2 000 réplicas, tolerancia de 4–5 errores estándar y
   explica la tolerancia en el comentario) para acierto@K, NDCG@K, cobertura@K y acierto por lugar@K.
4. Popularidad y MF respetan `AJUSTES_SOLO_TRAIN`: agrega en `tests/test_fuga_m3.py` las entradas
   `"referencias.popularidad"` y `"referencias.mf_als"` (función `(inter, cat) -> np.ndarray` que ajusta el modelo con una
   semilla fija y devuelve sus puntajes o factores). La prueba existente las verifica sola. Agrega además en
   `test_metricas_m3.py` una prueba de que el **objetivo de la búsqueda** (NDCG@5 en validación de una configuración fija) no
   cambia si se alteran o eliminan las interacciones de **prueba** (la búsqueda nunca lee prueba).
5. ALS: en un ejemplo pequeño (p. ej. 8 usuarios × 12 destinos), la función de pérdida **no aumenta después de cada
   medio paso** (actualizar X y luego Y; tolerancia relativa 1e-10) y la misma semilla da exactamente los mismos factores;
   otra semilla da otros. También: cada actualización cerrada coincide con minimizar numéricamente la pérdida respecto de un
   x_u (p. ej. comparar contra `np.linalg.lstsq` del sistema ponderado equivalente) y un destino sin interacciones en train
   queda con y_i = 0 exacto.
6. `summary.json` cumple §5.9 (corrida de `experimento.main` sobre datos sintéticos pequeños en `tmp_path`, 2 semillas, 2
   ensayos): por modelo, métricas con `media, desviacion, mejor, peor`; `n_parametros`; `n_configuraciones_busqueda`;
   `tiempo_total_s`; `device`; `evidencia` con la huella de la partición y los SHA-256 de los parquet. Y existen
   `semillas/<modelo>_seed<k>.json`, `metricas_por_k.json`, `metricas_por_grupo.json`, `recomendaciones_prueba.parquet`,
   `hpo_ensayos.json` y los factores en la carpeta de modelos.
7. Cambios en vivo: `apply_overrides(load_config("configs/m3/demo.yaml"), ["evaluacion.k=3", "semillas.n=2"])` corre (con
   las rutas redirigidas a `tmp_path` por `--set`) y las métricas salen solo @3 con 2 semillas; `evaluacion.k` acepta un
   entero o una lista.
8. Coherencia de configs: `evaluacion.umbral_pocas_max` de `configs/m3/base.yaml` == `particion.umbral_pocas_max` de
   `configs/m3/datos.yaml`; `busqueda.n_ensayos` de `hpo.yaml` == 20 (D13); `semillas.n` de `base.yaml` == 30 (D14).
9. Experimento falla con un error claro si la huella o el SHA-256 del parquet no coinciden con `resumen.json`.
10. Una corrida pequeña de `experimento.main` con la red bloqueada (monkeypatch de `socket.socket` y
    `socket.create_connection` que lanzan error) termina bien.
Para los datos sintéticos, arma en `tmp_path` interacciones con `particion.asignar_split`, destinos con `lugar`, usuarios y un
`resumen.json` mínimo con su bloque `sha256` (no reuses archivos reales). Marca `@pytest.mark.lento` solo lo que tarde > 5 s.

### C2. `src/m3_recomendacion/metricas.py` — funciones puras, cada una con su fórmula en el docstring
Notación: para el usuario u, C_u = candidatos (D10), R_u = relevantes (en prueba |R_u| = 1), L_u^K = top-K recomendado
(lista ordenada sin repetidos, L_u^K ⊂ C_u), rango r = posición 1-indexada.
- `ordenar_candidatos(puntajes, candidatos, k, rng)`: top-k por puntaje descendente; **los empates se rompen al azar** con
  `rng` (p. ej. permutación aleatoria y luego orden estable por −puntaje). Común a todos los modelos.
- `acierto_en_k` = 1[|L_u^K ∩ R_u| > 0]; `precision_en_k` = |L_u^K ∩ R_u| / K; `recall_en_k` = |L_u^K ∩ R_u| / |R_u|;
  `ndcg_en_k` = DCG/IDCG con DCG = Σ_{r=1}^{K} 1[L_u^K(r) ∈ R_u] / log2(r + 1) e IDCG = Σ_{r=1}^{min(|R_u|, K)} 1/log2(r + 1)
  (con un relevante: 1/log2(r + 1) si r ≤ K, si no 0; IDCG = 1). El docstring del módulo dice explícito que con
  |R_u| = 1: Recall@K = acierto@K y Precision@K = acierto@K / K (D12).
- `exposiciones(tops, catalogo, k)`: e_i = #{u : i ∈ L_u^K} para cada destino del catálogo (0 si nunca aparece).
- `cobertura(tops, n_catalogo, k)` = |∪_u L_u^K| / |catálogo| (D12: / 1 000).
- Gini y HHI de las exposiciones: **reutiliza** `gini` y `hhi` de `eda_estadistica.py` (mismas definiciones que el
  descriptivo de JJ-2: Gini sin corrección 2·Σ i·e_(i)/(n·Σe) − (n+1)/n; HHI = Σ s_i², s_i = e_i/Σe, sobre los n = 1 000
  destinos del catálogo, incluidos los de exposición 0).
- `acierto_por_lugar_en_k` = 1[∃ i ∈ L_u^K : lugar(i) = lugar(objetivo_u)] (solo K ∈ `evaluacion.k_lugar` = {1, 3}).
- Esperados analíticos del recomendador aleatorio (top-K uniforme sin reemplazo dentro de C_u, N_u = |C_u|):
  E[acierto@K] = min(K, N_u)/N_u; E[Precision@K] = E[acierto@K]/K; E[Recall@K] = E[acierto@K];
  E[NDCG@K] = (1/N_u)·Σ_{r=1}^{min(K,N_u)} 1/log2(r+1);
  E[acierto por lugar@K] = 1 − C(N_u − m_u, K)/C(N_u, K), con m_u = #{i ∈ C_u : lugar(i) = lugar(objetivo_u)} (incluye el
  objetivo) — esta es la **línea base del azar** del acierto por lugar que se reporta junto a CADA modelo;
  E[cobertura@K] = (1/n)·Σ_i [1 − Π_{u : i ∈ C_u} (1 − min(K, N_u)/N_u)] (independencia entre usuarios).
  Promedios sobre los usuarios evaluados. Usa `math.comb` o `scipy.special` con cuidado numérico (log si hace falta).
- `resumir_semillas(valores)` → `{media, desviacion, mejor, peor, n}` con desviación muestral (ddof = 1; dilo en el docstring)
  y mejor = máximo, peor = mínimo (todas las métricas de acierto son «mayor es mejor»). Gini y HHI no tienen dirección de
  «mejor»: van en un bloque aparte `concentracion` con `media, desviacion, minimo, maximo`.

### C3. `src/m3_recomendacion/referencias.py` — cada modelo con `ajustar`, `puntuar`, `n_parametros`
Interfaz común (escríbela como `Protocol` o clase base documentada; JJ-5 agregará la red implementándola, **sin reescribir el
arnés**):
```
ajustar(inter, catalogo, rng) -> self     # inter TRAE la columna split; el modelo usa SOLO split == "train" (D9)
puntuar(usuario_ids) -> np.ndarray       # (n_usuarios, n_catalogo), columnas en el orden de `catalogo`
n_parametros() -> int                    # parámetros estimados (núcleo §6)
nombre: str; hiperparametros: dict
```
- `Popularidad`: puntaje(u, i) = `particion.popularidad_train(inter, catalogo)[i]` (igual para todos los usuarios). Destinos
  sin train → 0 → quedan al final (empates al azar con el `rng` de la corrida en `ordenar_candidatos`). `n_parametros` = 0
  hiperparámetros, pero sí estima 1 000 conteos: decide y **documenta** cuál cifra reportas (recomiendo reportar el número de
  conteos estimados, n_catálogo, y explicarlo en el docstring); no lo dejes ambiguo.
- `Aleatorio`: puntaje = `rng.random((n_usuarios, n_catalogo))`; `n_parametros` = 0.
- `MFImplicitaALS` (Hu, Koren y Volinsky, 2008 [VERIFICAR]): con P ∈ {0,1}^{U×I} (p_ui = 1 si (u, i) está en train; r_ui = 1
  para cada interacción, D1: implícita binaria) y c_ui = 1 + α·r_ui, minimiza
  L(X, Y) = Σ_{u,i} c_ui (p_ui − x_uᵀ y_i)² + λ (Σ_u ‖x_u‖² + Σ_i ‖y_i‖²), la suma sobre TODOS los pares usuario × destino.
  Actualizaciones cerradas: x_u = (YᵀC^u Y + λI)⁻¹ YᵀC^u p(u) y y_i = (XᵀC^i X + λI)⁻¹ XᵀC^i p(i), con
  YᵀC^u Y = YᵀY + Yᵀ(C^u − I)Y (solo suman los destinos de u) para no armar matrices U × I densas por usuario.
  Filas de X = usuarios con ≥ 1 interacción en train; filas de Y = los destinos del catálogo. Inicialización
  N(0, `escala_inicial`²) desde el `rng`; luego `iteraciones` barridos (X, luego Y). Guarda la pérdida tras cada medio paso
  (`historial_perdida`). Puntaje = x_uᵀ y_i. `n_parametros` = (n_usuarios_train + n_catálogo)·f. Un destino sin train queda con
  y_i = 0 (puntaje 0): documéntalo. Resuelve con `np.linalg.solve` o `scipy.linalg.cho_factor/cho_solve` (la matriz es
  simétrica definida positiva si λ > 0; valida λ > 0, α ≥ 0, f ≥ 1, iteraciones ≥ 1).
- Registro de modelos: un diccionario `nombre → fábrica(cfg)` (p. ej. `MODELOS = {"popularidad": ..., "mf_als": ...,
  "aleatorio": ...}`) que el arnés recorre según `cfg["modelos"]`; JJ-5 solo agrega una entrada.

### C4. `src/m3_recomendacion/experimento.py` — `main(cfg) -> int` (lo llama `run.py m3`)
1. Lee los tres parquet de `cfg["datos"]` y de `resumen.json` SOLO el bloque `sha256`. Recalcula `particion.huella(inter)` y el
   SHA-256 de `interacciones.parquet`; si no coinciden con `resumen.json`, error claro (no son la misma partición).
   `evidencia` = {huella de la partición, su formato y SHA-256 de los tres parquet} (de `resumen.json` solo el bloque
   `sha256`).
2. Hiperparámetros de la MF: si `mf_als.hiperparametros_desde == "hpo"`, del bloque `familias.mf_als.mejor` de
   `<salida.carpeta>/hpo_ensayos.json` (error claro si no existe y no se pidió correr la búsqueda); si `"config"`, de
   `mf_als.hiperparametros`. Si la config trae `busqueda.ejecutar_en_experimento: true` (demo), corre primero la búsqueda de
   `hpo.py` con `busqueda.n_ensayos` y usa su mejor.
3. Para cada modelo de `cfg["modelos"]` y cada `run_id` en `range(semillas.n)`: `rng = make_rng(semillas.base_seed, run_id)`;
   ajusta con `inter` completo (el modelo filtra train), puntúa a los 606 usuarios de prueba, ordena con
   `ordenar_candidatos(·, candidatos(inter, catalogo, "prueba")[u], max(k, top_guardar), rng)` y evalúa contra
   `relevantes(inter, "prueba")`. Mide el tiempo (ajuste + evaluación) con `time.perf_counter`.
4. Escribe en `salida.carpeta`:
   - `semillas/<modelo>_seed<k>.json` (k = semilla efectiva): métricas globales por K, por grupo, acierto por lugar, cobertura,
     Gini/HHI de exposiciones, tiempo, hiperparámetros, evidencia.
   - `summary.json` (§5.9): `modelos.<nombre>` con `metricas` (`precision@K`, `recall@K`, `ndcg@K`, `acierto@K`,
     `cobertura@K`, `acierto_por_lugar@K` → `{media, desviacion, mejor, peor, n}`), `concentracion` (`gini@K`, `hhi@K` →
     `{media, desviacion, minimo, maximo}`), `n_parametros`, `n_configuraciones_busqueda` (MF: ensayos de la búsqueda usada;
     popularidad y aleatorio: 1), `tiempo_total_s` (MF: tiempo de la búsqueda + suma de las corridas finales; otros: suma de
     corridas), `hiperparametros`, `device` ("cpu"), `semillas_efectivas`; y a nivel raíz `evidencia`, `k`, `split_evaluado`
     ("prueba"), `n_usuarios_evaluados`, `linea_base_aleatoria_analitica` (todas las esperanzas de C2, por K y por grupo) y
     `destinos_frios` (D14): usuarios de prueba cuyo destino objetivo no tiene interacciones en train (debe dar 205 en los
     reales; calcúlalo con `popularidad_train`), y por modelo y K los aciertos medios en objetivos fríos y no fríos, y una
     frase de cómo trata cada modelo los destinos fríos (popularidad: puntaje 0, al final, nunca alcanzables mientras haya ≥ K
     candidatos con conteo ≥ 1 → techo de acierto = (606 − 205)/606; MF: y_i = 0, puntaje 0, su posición depende del signo de
     los demás puntajes del usuario → se MIDE cuántas veces entran al top-K; aleatorio: todos alcanzables).
   - `metricas_por_k.json` (por modelo y K: media y desviación de cada métrica y de la concentración, + esperado aleatorio):
     alimenta la figura «Precision, Recall y NDCG en función de K» y la de cobertura/concentración.
   - `metricas_por_grupo.json`: por modelo, grupo («pocas» ≤ `evaluacion.umbral_pocas_max` < «muchas», con el TOTAL de
     interacciones del usuario, solo para estratificar la evaluación) y K: media, desviación, n_usuarios, y el esperado
     aleatorio de cada grupo.
   - `recomendaciones_prueba.parquet`: columnas `modelo, semilla, usuario_id, rango, destino_id, puntaje` con el top-
     `top_guardar` (10) de cada usuario de prueba, **para todas las semillas** (el verificador recalcula las métricas desde
     aquí; JJ-6 lo usa).
   - Factores de la MF de la semilla `base_seed + 0` en `salida.modelos` (`mf_als.npz` con X, Y, `usuario_ids`,
     `destino_ids`, y un `mf_als.json` con hiperparámetros, semilla, `historial_perdida` y evidencia).
5. Imprime una tabla corta por modelo (media ± desviación de NDCG@5, Recall@10, cobertura@10) y devuelve 0.
6. Deja el punto de extensión claro (comentario en el docstring del módulo: «JJ-5 agrega su modelo en `referencias.MODELOS` o
   en su propio módulo y lo nombra en `cfg["modelos"]`»).

### C5. `src/m3_recomendacion/hpo.py` — `main(cfg) -> int` (lo llama `run.py m3-hpo`)
- Optuna `TPESampler(seed=busqueda.semilla_sampler)`, `busqueda.n_ensayos` ensayos (D13: 20), objetivo **NDCG@5 medio en
  VALIDACIÓN** (`busqueda.objetivo_k`), con candidatos `candidatos(inter, catalogo, "validacion")` (catálogo − train) y
  relevantes de validación. El modelo se ajusta solo con train (`rng = make_rng(semillas.base_seed, 0)` en todos los ensayos,
  para que solo cambien los hiperparámetros). **Nunca lee el split de prueba** (ni para candidatos).
- Espacio en `configs/m3/hpo.yaml` → `busqueda.espacio`: `factores` (entero, log), `regularizacion` (λ, real, log), `alfa`
  (real, log), `iteraciones` (entero). Rangos [PROPUESTO por esta tarea, comentados en el YAML como elección nuestra, no de la
  literatura]: factores 4–64, λ 1e-3–1e2, α 1–100, iteraciones 5–30. Optuna sin almacenamiento en disco (sin `.db`), sin
  barras de progreso ruidosas (`optuna.logging.set_verbosity(WARNING)`).
- Escribe `<salida.carpeta>/hpo_ensayos.json` = `{evidencia, familias: {mf_als: {n_ensayos, objetivo, espacio, sampler,
  semilla_sampler, ensayos: [{numero, params, valor, tiempo_s, ndcg@K y recall@K en validación para K de evaluacion.k}],
  mejor: {numero, params, valor}, tiempo_total_s}}}`. Si el archivo ya existe con la **misma huella**, conserva las familias
  que no corriste (JJ-5 agregará la suya); si la huella es otra, lo reemplaza.

### C6. Configs (comentadas como `configs/m3/datos.yaml` y `eda.yaml`: uso, decisiones D9–D14, qué es [PROPUESTO])
- `configs/m3/base.yaml`: `datos` (carpeta, los 3 parquet, `resumen_particion`), `salida` (`carpeta: results/data/m3`,
  `modelos: models/m3`), `semillas: {base_seed: 0, n: 30}`, `device: cpu`, `modelos: [popularidad, mf_als, aleatorio]`,
  `evaluacion: {k: [1, 3, 5, 10], k_lugar: [1, 3], top_guardar: 10, umbral_pocas_max: 2}`,
  `mf_als: {hiperparametros_desde: hpo, hiperparametros: {...valores de respaldo...}, escala_inicial: 0.01}`.
- `configs/m3/hpo.yaml`: `hereda: base.yaml` + bloque `busqueda` (`n_ensayos: 20`, `objetivo: ndcg`, `objetivo_k: 5`,
  `semilla_sampler`, `ejecutar_en_experimento: false`, `espacio`).
- `configs/m3/demo.yaml`: `hereda: hpo.yaml`; `semillas.n: 3`, `busqueda.n_ensayos: 4`, `busqueda.ejecutar_en_experimento:
  true`, `salida.carpeta: results/data/m3_demo`, `salida.modelos: models/m3_demo` (ambos en `.gitignore`). Debe correr en
  < 2 min en CPU (mídelo).
- Las claves `evaluacion.k` y `semillas.n` deben funcionar con `--set` sin editar código (entero o lista para `k`).

## Aceptación (corre y pega la salida REAL en tu informe)
1. `.venv\Scripts\python -m pytest -q tests/test_metricas_m3.py tests/test_fuga_m3.py` en verde, y luego
   `.venv\Scripts\python -m pytest -q -m "not lento"` (todo el repo) en verde.
2. `.venv\Scripts\python run.py m3-hpo --config configs/m3/hpo.yaml` (20 ensayos; anota el mejor y el tiempo).
3. `.venv\Scripts\python run.py m3 --config configs/m3/base.yaml` (30 semillas × 3 modelos).
4. `.venv\Scripts\python run.py m3 --config configs/m3/demo.yaml` con su tiempo (< 2 min) y
   `.venv\Scripts\python run.py m3 --config configs/m3/demo.yaml --set evaluacion.k=3`.
5. Comprobaciones sobre los resultados reales: 606 usuarios evaluados; destinos fríos = 205; el aleatorio simulado (media de 30
   semillas) cerca de su esperado analítico; la popularidad nunca acierta un destino frío.

## Informe final (breve)
Archivos creados/modificados; salidas reales de los comandos; tabla por modelo y K (media ± desviación) de Precision, Recall,
NDCG y cobertura frente al aleatorio analítico; mejores hiperparámetros de la MF; cualquier cosa que no pudiste cumplir, que
choque con el Spec, o que hayas decidido tú (marcada [PROPUESTO]). No redactes el blog (lo hace otro agente).
