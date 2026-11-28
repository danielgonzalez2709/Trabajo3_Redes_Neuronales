# JJ-5 — prompt literal del orquestador (Opus 5.5) al implementador-experto (Opus), 2026-11-27

Eres el implementador-experto de la tarea JJ-5 (🧠) del Trabajo 3: la red neuronal recomendadora de M3 (búsqueda Optuna y 30
semillas). Te dirige Juan José; rama `dev/juanjose` (ya incluye JJ-1 a JJ-4). Repositorio: `C:\Repositorios\Trabajo3_Redes_Neuronales`.

## Reglas (obligatorias)
- **Prueba primero, luego código.** Escribe las pruebas, córrelas y míralas fallar; después implementa.
- Siempre `.venv\Scripts\python` (en Git Bash: `.venv/Scripts/python`). Sin internet. **Nada de librerías nuevas**
  (torch 2.15, optuna 5.1, numpy, pandas, scipy y matplotlib ya están).
- **NO hagas commits, push ni PR.**
- Solo tocas: `src/m3_recomendacion/{red.py (nuevo), contenido.py (nuevo), referencias.py, hpo.py, experimento.py (solo el
  cambio de 3 líneas descrito abajo)}`, `configs/m3/{base,demo,hpo}.yaml`, `tests/test_red_m3.py` (nuevo), `tests/test_fuga_m3.py`,
  `tests/test_metricas_m3.py` (solo si un cambio de experimento.py lo exige), `src/viz/figs_m3.py`, `src/m3_recomendacion/README.md`,
  y las salidas `results/data/m3/`, `models/m3/`, `blog/docs/figures/m3/`. **No toques** `src/comun/`, `run.py`,
  `requirements.txt`, `docs/spec/`, el blog (`blog/secciones/`) ni archivos de otras personas.
- **NO reescribas `experimento.py`**: el arnés de JJ-4 se extiende con una entrada en `referencias.MODELOS`, una en
  `hpo.BUSQUEDAS` y un bloque de config. Lo único permitido en `experimento.py` es el reordenamiento de `_presupuesto` (abajo).
- Prohibido inventar datos, constantes, referencias o resultados. Lo que elijas sin fuente márcalo `[PROPUESTO]` en el
  comentario de la config y repórtalo. Si algo del Spec o de esta tarea es imposible o contradictorio, **detente y repórtalo**.
- Semillas: `src/comun/seeds.py` (`make_rng(base_seed, run_id)`); nunca `np.random.seed`.

## Lee antes de empezar
- `docs/spec/SPEC.md`: §0 (reglas), §4.1 (comandos y claves de cambio en vivo), §5.7–§5.9 (contratos de datos, app y
  resultados), §6 (comparación justa) y en el Anexo «Módulo 3» (tarea 5, «Fundamentación matemática del módulo»), «Aplicación
  web», «Regla de comparación justa» y «Figuras mínimas comunes» (en «Entregables → 1»).
- `docs/spec/partes/juanjose.md` §3.0 (contrato con la app), §3.1 (D8–D10), §3.2 (D11–D14 y **D15–D19 + «Implementación de
  JJ-5»**, recién registradas: son tu especificación) y §3.3 (D12).
- Código: `src/m3_recomendacion/{particion,metricas,referencias,experimento,hpo}.py`, `configs/m3/*.yaml`,
  `tests/test_fuga_m3.py` (guardas `AJUSTES_SOLO_TRAIN`, `ARCHIVOS_DE_MODELO_M3`, `LECTURAS_DE_ARCHIVOS`,
  `PROHIBIDAS_PARA_MODELOS`, `SALIDAS_DE_EVALUACION_M3`), `tests/test_metricas_m3.py` (patrón de pruebas de punta a punta con
  datos pequeños en `tmp_path`), `src/comun/torch_utils.py`, `src/comun/config.py` (una clave de `--set` que no existe es
  error), `src/viz/{figs_m3,estilo,paleta}.py`, `app/lib/contratos.ts` (validadores M3, líneas ~737–990) y `app/lib/recomendar.ts`.

## Hechos medidos (no los cambies; úsalos)
- 999 usuarios, 1 000 destinos, 1 998 interacciones: train 1 066, validación 326, prueba 606 (`split` en
  `data/processed/m3/interacciones.parquet`). 326 usuarios evaluables en validación y 606 en prueba.
- `destinos.parquet`: `destino_id, nombre, lugar, estado, tipo, mejor_epoca, popularidad`. `tipo`, `estado` y `mejor_epoca` son
  función de `lugar` (5 lugares × 200 ids). `usuarios.parquet`: `usuario_id, preferencias, pref_adventure, pref_beaches,
  pref_city, pref_historical, pref_nature (bool), genero, n_adultos, n_ninos`; solo 3 combinaciones de preferencias.
- 345 destinos sin ninguna interacción en train; 205 de los 606 usuarios de prueba tienen un objetivo frío (ya lo reporta el
  arnés en `summary.json → destinos_frios`, por modelo).
- Referencias de JJ-4 en prueba (30 semillas): NDCG@5 popularidad 0,0016, MF 0,0024, aleatorio 0,0029 (esperado 0,0030);
  Recall@10 0,0069 / 0,0105 / 0,0096 (esperado 0,0100). La MF eligió f = 4. Todo al nivel del azar: es lo esperable con datos
  generados (D4); NO intentes «mejorar» la red para ganarle al azar, implementa bien y reporta lo que salga.

## Qué construir

### Diseño (D15–D19 de `juanjose.md` §3.2; resumen operativo)
1. **`src/m3_recomendacion/contenido.py`** (nuevo): la red necesita variables de contenido pero `ajustar(inter, catalogo, rng)`
   no las trae y los archivos de modelo no pueden abrir archivos (guarda `LECTURAS_DE_ARCHIVOS`). Este módulo lee SOLO
   `destinos.parquet` y `usuarios.parquet` (rutas de `cfg["datos"]`; nunca interacciones ni `results/`) y construye las matrices
   one-hot con orden fijo y documentado: destinos → `tipo` (5 columnas, categorías ordenadas); usuarios → las 5 `pref_*` (y, si
   `modelo.usar_demografia`, `genero`, `n_adultos`, `n_ninos` one-hot por valor). Devuelve también los nombres de columna (los
   necesita la exportación de JJ-7: el contrato pide «one-hot por opción, orden fijo»). Agrega en `tests/test_fuga_m3.py` una guarda
   de que `contenido.py` no lee interacciones ni salidas (`interacciones`, `results/`, ni las cadenas de `PROHIBIDAS_PARA_MODELOS`).
2. **`src/m3_recomendacion/red.py`** (nuevo), estilo del curso: clases `nn.Module` con `__init__` y `forward`
   (`TorreUsuario`, `TorreDestino`, `DosTorres`), funciones explícitas `train_loop(...)` y `val_loop(...)` con `model.train()`
   / `model.eval()` y `torch.no_grad()` en validación, `torch.optim.Adam(..., weight_decay=...)`, `state_dict`. Comentarios en
   español que se puedan explicar en la sustentación.
   - Torre de usuario: x_u (one-hot) → `capas_usuario` capas ocultas `Linear → ReLU → Dropout` de `unidades_usuario` →
     `Linear(·, d)` sin activación. Si `usar_id_usuario`: u = MLP(x_u) + E_u[idx(u)], con `nn.Embedding(n+1, d, padding_idx=0)`
     inicializado en cero (índice 0 = «sin id»: vector nulo fijo). Solo ReLU como activación (contrato de la app).
   - Torre de destino: x_i (tipo one-hot) → MLP análoga (`capas_destino`, `unidades_destino`) → `Linear(·, d + 1)`: las primeras d
     salidas son v_i y la última el sesgo b_i. Si `usar_id_destino`: se suma E_i[idx(i)] (`nn.Embedding(n+1, d+1, padding_idx=0)`,
     inicializado en cero).
   - Puntaje s_ui = ⟨u, v_i⟩ + b_i (logit).
   - Índices de id: se construyen SOLO con train: usuarios y destinos con al menos una interacción en train reciben 1..n; los
     demás (incluidos los 345 destinos fríos y cualquier perfil nuevo) reciben 0. Las tablas tienen n+1 filas (n = con train).
   - «Dropout de id»: en `train_loop`, con probabilidad `modelo.dropout_id` (por ejemplo, de forma independiente para usuario y
     destino) el índice se reemplaza por 0, con el generador sembrado. En evaluación no hay dropout de id.
   - Pérdidas (D16), ambas sobre logits y estables: `bce` = `BCEWithLogitsLoss` sobre positivos (etiqueta 1) y negativos
     muestreados (etiqueta 0); `bpr` = −mean(logsigmoid(s⁺ − s⁻)) sobre pares (positivo, negativo). Exporta funciones puras
     `perdida_bce(s_pos, s_neg)` y `perdida_bpr(s_pos, s_neg)` para probarlas a mano. Docstrings con el modelo probabilístico del
     que sale cada una (Bernoulli con p = σ(s) e independencia → −log verosimilitud = BCE; P(i ≻_u j) = σ(s_ui − s_uj) → −log
     verosimilitud = BPR). Sin citas bibliográficas inventadas: si nombras a Rendle et al. (2009) para BPR, márcalo `[VERIFICAR en JJ-9]`.
   - Negativos (D17): `muestrear_negativos(...)` uniforme sobre catálogo − train del usuario, `negativos_por_positivo` por
     positivo, re-muestreados cada época con el `np.random.Generator` de la corrida. Nunca devuelve un destino de train del usuario.
     (Los destinos de validación del usuario SÍ pueden salir como negativos en train: excluirlos usaría validación.)
   - Entrenamiento (D19): Adam (`entrenamiento.lr`), `regularizacion.weight_decay`, `regularizacion.dropout`, minilotes de
     `entrenamiento.tam_lote`, hasta `entrenamiento.max_epocas`. Al final de cada época, `val_loop` calcula la pérdida de
     validación (positivos de validación con negativos muestreados UNA vez con un generador fijo derivado del de la corrida,
     excluyendo train y el propio positivo) y NDCG@5 en validación con candidatos = catálogo − train (`particion.candidatos(...,
     VALIDACION)` y `metricas.rankear_usuarios` + `metricas.ndcg_en_k`; el desempate con un generador fijo derivado del de la
     corrida, igual en todas las épocas). Parada temprana con `entrenamiento.paciencia` sobre el NDCG@5 de validación; se
     restauran los pesos de la mejor época. Se guardan por época: pérdida de train, pérdida de validación, NDCG@5 de validación;
     y `mejor_epoca` y `epoca_parada` (época en que se detuvo).
   - Al entrar, `ajustar` descarta las filas de prueba (como `hpo.evaluar_configuracion`). Toda aleatoriedad de torch sale del
     `rng` recibido (p. ej. `torch.Generator().manual_seed(int(rng.integers(2**31)))` para la inicialización y el barajado) y se
     llama `torch_utils.activar_determinismo("cpu")`. Misma semilla → mismos pesos y mismos puntajes.
   - Interfaz de `referencias.Recomendador`: `nombre = "red"`, `hiperparametros` (dict plano con claves con punto, p. ej.
     `"modelo.dim_embedding"`), `descripcion_frios` (los fríos usan el índice 0: puntaje solo por su tipo), `ajustar`, `puntuar`
     (n_usuarios × n_catálogo, columnas en el orden de `catalogo`; un usuario sin train usa índice 0, no falla), `n_parametros()`
     (parámetros entrenables: Σ numel de los que tienen `requires_grad`, **menos las filas `padding_idx`**, que son fijas;
     documéntalo), `diagnosticos()` (debe traer `degenerado` y `motivo_degenerado`; degenerado si hay puntajes no finitos, si los
     puntajes de validación son constantes por usuario (rango máximo < tolerancia de la config) o si max ‖u‖·‖v‖ < tolerancia; además
     `mejor_epoca`, `epoca_parada`, `ndcg5_validacion_mejor` y una medida de personalización, p. ej. la media sobre destinos de la
     desviación entre usuarios de s_ui) y `guardar(carpeta, semilla, evidencia)`.
   - `guardar` (el arnés la llama con la primera semilla): `models/m3/red.pt` (state_dict) y `models/m3/red.json` (hiperparámetros,
     semilla, columnas one-hot de usuario y de destino en orden, mapas id → índice de los embeddings, d, n_parametros, evidencia, y
     cómo se exporta: la MLP de usuario con índice 0 es la `torre_usuario` del contrato §5.8; (v_i, b_i) de cada destino se precalculan
     con su torre). Además escribe en `cfg["salida"]["carpeta"]` (la fábrica recibe el cfg completo): `curvas/red.json` (núcleo §5.9:
     por época `perdida_train`, `perdida_validacion`, `ndcg5_validacion`; `mejor_epoca`, `epoca_parada`, semilla, evidencia) y
     `arquitectura/red.json` (por capa: nombre, tipo, forma de entrada y de salida, activación, parámetros; total = `n_parametros()`).
     `red.py` NO puede contener ninguna cadena de `LECTURAS_DE_ARCHIVOS`, `SALIDAS_DE_EVALUACION_M3` ni `PROHIBIDAS_PARA_MODELOS`
     (lo vigila la prueba): escribir con `save_json` / `torch.save` está bien.
   - Fábrica `fabrica_red(cfg)`: hiperparámetros efectivos = bloques de primer nivel `modelo`, `perdida`, `entrenamiento`,
     `regularizacion` de la config, con `cfg["red"]["hiperparametros"]` (claves con punto) superpuesto encima. Con
     `red.hiperparametros_desde: hpo` el arnés pone ahí el mejor ensayo; con `config`, `red.hiperparametros: {}` y quedan los de
     los bloques (así funcionan `--set modelo.dim_embedding=8`, `--set perdida.tipo=bpr`, `--set modelo.negativos_por_positivo=1`).
     Registra `"red": fabrica_red` en `referencias.MODELOS` (import sin ciclos: `red.py` no importa `referencias` en el nivel del
     módulo si eso crea un ciclo).
3. **Búsqueda (`hpo.BUSQUEDAS["red"] = buscar_red`)**: Optuna TPE con `busqueda.semilla_sampler`, `busqueda.n_ensayos` (= 20,
   mismo presupuesto que la MF), objetivo `busqueda.objetivo`@`busqueda.objetivo_k` (NDCG@5) en validación; la búsqueda descarta
   prueba al entrar y cada ensayo usa `make_rng(base_seed, 0)` (como la MF). Espacio propio en `configs/m3/hpo.yaml`, bloque
   `red.busqueda.espacio`, con claves con punto iguales a las de la config (`modelo.dim_embedding`, `entrenamiento.lr`,
   `regularizacion.weight_decay`, `regularizacion.dropout`, `modelo.capas_usuario`, `modelo.unidades_usuario`,
   `modelo.capas_destino`, `modelo.unidades_destino`, `modelo.negativos_por_positivo`, `perdida.tipo`, `modelo.usar_id_destino`,
   `modelo.usar_id_usuario`). Extiende `hpo._sugerir` con `tipo: categorico` (`valores: [...]`) sin romper la MF. d ∈ {4, 8, 16, 32}
   (D18). Rangos [PROPUESTO]: lr 1e-4–1e-2 (log), weight_decay 1e-6–1e-2 (log), dropout 0–0,5, capas {0, 1, 2}, unidades {16, 32,
   64}, negativos {1, 2, 4, 8}, pérdida {bce, bpr}, ids {true, false}. Cada ensayo guarda params, valor, NDCG@5 y Recall@5/10 de
   validación, `mejor_epoca`, `epoca_parada`, tiempo, `degenerado`; un ensayo degenerado se poda y nunca es el mejor. La familia
   `red` se escribe con `hpo.escribir_familia` (conserva la de la MF).
4. **`experimento._presupuesto`**: reordena para que `hiperparametros_desde: config` gane a `busqueda.ejecutar_en_experimento`
   (hoy la búsqueda corre primero aunque el bloque diga `config`). Solo ese cambio; prueba que lo demuestre.
5. **Configs.** `base.yaml`: agrega `red` a `modelos`; bloques `modelo`, `perdida`, `entrenamiento`, `regularizacion` (valores por
   defecto; tras la búsqueda real, **cópiales el mejor ensayo** con un comentario «copiado del mejor ensayo N de m3-hpo,
   27-nov»), y `red: {hiperparametros_desde: hpo, hiperparametros: {}, tolerancia_degenerado: ...}`. Fijos [PROPUESTO]:
   `max_epocas` 100, `paciencia` 10, `tam_lote` 256, `dropout_id` 0,2, `usar_demografia` false. Comentario en la cabecera con las
   claves en vivo de §4.1. `hpo.yaml`: el bloque `red.busqueda.espacio`. `demo.yaml`: `red.hiperparametros_desde: config` (la MF
   sigue buscándose en vivo con 4 ensayos); la demo completa (`run.py m3 --config configs/m3/demo.yaml`: 3 semillas × 4 modelos +
   búsqueda de la MF) debe tardar **< 2 min en CPU**; mídelo.
6. **Guardas (`tests/test_fuga_m3.py`)**: agrega `red.py` y `contenido.py` donde corresponda: `red.py` a `ARCHIVOS_DE_MODELO_M3`;
   a `LECTURAS_DE_ARCHIVOS` agrega `"np.load"`, `"read_text"`, `"read_bytes"` (y `"torch.load"`; `"open("` ya está). En
   `AJUSTES_SOLO_TRAIN`: los negativos muestreados y un entrenamiento de la red a épocas fijas sin parada temprana (pesos con
   semilla fija). Guarda nueva `AJUSTES_SIN_PRUEBA` (invariante a alterar o eliminar PRUEBA) con el ajuste completo de la red
   (con parada temprana) y su búsqueda; documenta que validación solo entra por la parada temprana (D9). Y una prueba de que el
   «dropout de id» no usa validación ni prueba (los índices salen solo de train).
7. **Pruebas `tests/test_red_m3.py`** (rápidas; lo lento con `@pytest.mark.lento`): formas de entrada/salida de cada torre;
   `n_parametros` contra un conteo a mano en una configuración pequeña (escribe la cuenta en el comentario); BCE y BPR contra un
   cálculo a mano con 2–3 pares (valores escritos a mano en la prueba); los negativos nunca incluyen destinos de train del
   usuario; con id de usuario = 0 la torre de usuario depende solo de las preferencias (y coincide con aplicar a mano las capas
   `Linear` como lo hace `app/lib/recomendar.ts`: W·h + b y ReLU); la pérdida baja en un ejemplo pequeño memorizable; determinismo
   con la misma semilla (mismos puntajes); `config` gana a `ejecutar_en_experimento`; las claves en vivo `modelo.dim_embedding`,
   `modelo.negativos_por_positivo`, `perdida.tipo`, `evaluacion.k`, `semillas.n` cambian lo que deben con `--set` (cargador real
   `src/comun/config.py`); y de punta a punta con datos pequeños en `tmp_path`: `summary.json` (bloque `red` con métricas
   media/desviación/mejor/peor, `n_parametros`, `n_configuraciones_busqueda`, `tiempo_total_s`, `device`, `evidencia`),
   `semillas/red_seed<k>.json`, `curvas/red.json`, `arquitectura/red.json` y `hpo_ensayos.json` (familias `mf_als` y `red`)
   cumplen el núcleo §5.9.
8. **Corridas reales** (en este orden, pega la salida real en tu reporte): `.venv\Scripts\python run.py m3-hpo --config
   configs/m3/hpo.yaml`; copia el mejor ensayo de la red a los bloques de `base.yaml`; `.venv\Scripts\python run.py m3 --config
   configs/m3/base.yaml` (30 semillas, 4 modelos); la demo con su tiempo; `.venv\Scripts\python -m pytest -q -m "not lento"`.
   Las 3 referencias deben dar las mismas métricas que antes (son deterministas); si cambian, detente y repórtalo.
9. **Figuras comunes (`src/viz/figs_m3.py`, desde `results/data/m3/` con `src/viz/estilo.py` y `paleta.py`)**, en
   `blog/docs/figures/m3/`: (a) `red_arquitectura.png`: diagrama de las dos torres con capas, dimensiones de entrada/salida,
   activaciones y parámetros por capa y total (desde `arquitectura/red.json`); (b) `red_curvas.png`: pérdida de train y de
   validación por época y NDCG@5 de validación, con la mejor época y la parada temprana marcadas (desde `curvas/red.json`); (c)
   `busqueda_m3.png`: NDCG@5 de validación por ensayo para la red y para la MF (desde `hpo_ensayos.json`), mejor ensayo marcado y
   degenerados distinguidos; (d) `cajas_m3.png`: diagramas de caja de NDCG@5 y Recall@10 en prueba de los 4 modelos sobre las 30
   semillas (desde los JSON por semilla), con el esperado del azar como línea horizontal. `generar()` debe seguir produciendo las 4
   figuras del descriptivo y agregar estas; corre `.venv\Scripts\python run.py figures`. Sin rutas de archivo en los títulos.
10. Actualiza `src/m3_recomendacion/README.md` (comandos y archivos de la red).

## Reporte final (en español)
Archivos creados/modificados; salidas reales pegadas de los comandos del punto 8 y de `run.py figures`; mejor configuración de
la red (ensayo, params, NDCG@5 de validación); tabla de los 4 modelos en prueba (media ± desviación de NDCG@5, NDCG@10,
Recall@5, Recall@10) y el esperado del azar; aciertos sobre destinos fríos por modelo (`summary.json → destinos_frios`); tiempos
(búsqueda, finales, demo) y `n_parametros`; diagnósticos de degeneración de la red; todo lo que marcaste `[PROPUESTO]`; y
cualquier cosa del Spec o de este prompt que te pareció incorrecta o imposible (con la evidencia).
