# JJ-5 — prompt literal del orquestador (Opus 5.5) al documentador (Haiku), 2026-11-27

Actualiza `C:\Repositorios\Trabajo3_Redes_Neuronales\docs\MEMORIA.md` por el cierre de la tarea JJ-5 (Juan José). Reglas de CLAUDE.md:
actualizar estado, decisiones vigentes, pendientes, cacería y una línea nueva ARRIBA en la bitácora; **mantenerla ≤ 150 líneas**;
**no borres nada de otros integrantes** (Daniel, Camila, Andrés, José). Si para no pasar de 150 líneas hay que condensar, condensa
solo entradas de Juan José (JJ-1 a JJ-4) sin perder cifras ni decisiones vigentes. No toques ningún otro archivo. Sin commits.

Contenido a reflejar (todo verificado por la sesión principal):
- **Estado (nueva viñeta tras JJ-4):** JJ-5 (red de dos torres de M3) terminado en `dev/juanjose` el vie 27, pendiente de PR (junto
  con JJ-4): `run.py m3-hpo --config configs/m3/hpo.yaml` busca la MF y la red (20 ensayos cada una; red: mejor ensayo 18, NDCG@5 de
  validación 0,0067; d = 32, 1 capa de 64 (usuario) y 16 (destino), ids de usuario y destino, 2 negativos por positivo, BCE,
  lr ≈ 7,4e-4, weight decay ≈ 3,6e-4, dropout ≈ 0,25; copiados a los bloques de `base.yaml`); `run.py m3 --config configs/m3/base.yaml`
  evalúa los 4 modelos con 30 semillas. Red en prueba: NDCG@5 0,0026 ± 0,0010, Recall@10 0,0098 ± 0,0034 (azar 0,0030 y 0,0100;
  referencias sin cambios), cobertura@10 0,028, 52 192 parámetros (≈ 49 por interacción de train), 96 s (38 s de búsqueda); al nivel
  del azar. Ningún destino frío entra a sus listas (como popularidad y MF). Demo 26 s; claves en vivo `modelo.dim_embedding`,
  `perdida.tipo`, `modelo.negativos_por_positivo` comprobadas con la demo. Archivos nuevos: `src/m3_recomendacion/{red,contenido}.py`,
  `tests/test_red_m3.py`; salidas `curvas/red.json`, `arquitectura/red.json`, `semillas/red_seed*.json`, `models/m3/red.{pt,json}`;
  4 figuras comunes (`red_arquitectura`, `red_curvas`, `busqueda_m3`, `cajas_m3`); blog 07 «Red neuronal de dos torres». Revisado por
  verificador-matematico (APROBADO en la 4.ª vuelta), auditor-fugas (SIN FUGA; 20/20 mutantes muertos), revisor-spec (APROBADO) y
  revisor-calidad (APROBADO en la 2.ª vuelta).
- **Decisiones vigentes (nueva viñeta M3, Juan José, 27-nov; `juanjose.md` §3.2, D15–D19):** dos torres (usuario: 5 preferencias
  one-hot + id opcional; destino: `tipo` one-hot + id opcional; MLP con ReLU; ids sumados a la salida, índice 0 = «sin id» para
  perfiles nuevos y destinos fríos, «dropout de id»); ninguna popularidad en la red; pérdida `bce` o `bpr` (la eligió la búsqueda:
  BCE); negativos uniformes sobre catálogo − train; d ∈ {4, 8, 16, 32}; parada temprana por NDCG@5 de validación; la red lee los
  bloques `modelo/perdida/entrenamiento/regularizacion` y en `_presupuesto` «config» gana a `ejecutar_en_experimento`; guarda
  `AJUSTES_SIN_PRUEBA`; `contenido.py` solo lee destinos y usuarios.
- **Avisos para el equipo (M3):** el PR de JJ-5 debe incluir `results/data/m3/{curvas,arquitectura}/`, `semillas/red_seed*.json`,
  `hpo_ensayos.json`, `summary.json`, `recomendaciones_prueba.parquet`, `models/m3/red.*` y las 4 figuras nuevas (las pruebas y
  `run.py figures` los leen). Con `base.yaml` las claves en vivo de la red no cambian nada (manda el mejor ensayo) salvo con
  `--set red.hiperparametros_desde=config`; la demo ya usa config. Si se vuelve a correr `m3-hpo`, hay que volver a copiar el mejor
  ensayo a `base.yaml` (lo vigila una prueba). La máquina de Juan José tiene ~0,8 GB libres: un solo proceso con torch a la vez.
- **Pendientes de Juan José (agregar):** decidir lo [PROPUESTO] de JJ-5 (fijos de entrenamiento, rangos, guarda 1e-6, diagnósticos de
  personalización); decidir si `base.yaml` usa `red.hiperparametros_desde: config` (claves en vivo también con base); recomendaciones
  abiertas del revisor-calidad (R-1 a R-19 de la 2.ª vuelta; ninguna bloqueante); JJ-6: los usuarios nuevos simulados deben
  reentrenar sin sus interacciones (el auditor-fugas advierte que poner índice 0 en la red ya entrenada no oculta su historial) y
  revisar el acierto por lugar con K = 3 de la red (0,2308 frente a 0,4883 del azar); JJ-9: verificar Rendle et al. (2009) para BPR
  (`TODO(cita)` en el blog) y la cifra de páginas; agregar a la bibliografía la doc. de `torch.optim.Adam` si JJ-8 la cita.
- **Cacería (agregar a la de M3):** 3 candidatos de JJ-5 (sin número): «personalización = desviación entre usuarios de s_ui»
  (Matemáticas, origen en el prompt del orquestador Opus, adoptado por el implementador-experto Opus); «la fracción es 0 si S es
  constante / está en [0, 1]» en punto flotante (Código, menor; implementador Opus + orquestador Opus); «los fríos quedan por debajo
  de los destinos con train» (Conceptos, menor; orquestador Opus). Evidencia en `alucinaciones/evidencias/JJ-5/`.
- **Bitácora (línea nueva arriba):** «2026-11-27 · Juan José · JJ-5 ✅: red de dos torres (preferencias + tipo, ids con índice 0
  para perfiles nuevos), BCE/BPR, búsqueda de 20 ensayos y 30 semillas; al nivel del azar como las referencias; 4 figuras comunes y
  blog 07 «Red neuronal de dos torres»; D15–D19; 3 candidatos a la cacería.»

Al terminar, reporta el número de líneas final de `docs/MEMORIA.md` y qué condensaste (si algo).
