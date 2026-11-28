# JJ-5 — prompt literal del orquestador (Opus 5.5) al verificador-matematico (Opus), 2026-11-27

Eres el verificador-matematico de la tarea JJ-5 del Trabajo 3 (M3: red neuronal recomendadora de dos torres). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales`, rama `dev/juanjose`. Verificas de forma independiente; **no modificas código ni
resultados** (solo lees, corres cálculos propios en la carpeta temporal y reportas). Usa `.venv\Scripts\python`. Sin commits.

## Contexto que debes leer
- Especificación: `docs/spec/partes/juanjose.md` §3.2 (D15–D19 y «Implementación de JJ-5») y §3.3 (D12: métricas).
- Anexo de `docs/spec/SPEC.md`, «Módulo 3 → Fundamentación matemática del módulo»: «arquitectura de red neuronal usada» y
  «derivación de la función de pérdida (BCE con muestreo de negativos o BPR) a partir de un modelo probabilístico».
- Código: `src/m3_recomendacion/red.py` (docstring con la formulación, torres, pérdidas, negativos, parada temprana,
  `contar_parametros`, `diagnostico_degeneracion`), `src/m3_recomendacion/contenido.py`, `src/m3_recomendacion/metricas.py`
  (NDCG/Recall/Precision ya verificados en JJ-4) y `tests/test_red_m3.py`.
- Resultados reales: `results/data/m3/summary.json` (bloque `red`), `results/data/m3/semillas/red_seed*.json`,
  `results/data/m3/curvas/red.json`, `results/data/m3/arquitectura/red.json`, `results/data/m3/hpo_ensayos.json` (familia `red`),
  `results/data/m3/recomendaciones_prueba.parquet` (columnas `modelo, semilla, usuario_id, rango, destino_id, puntaje`; top-10),
  `models/m3/red.pt` y `models/m3/red.json`. Datos: `data/processed/m3/interacciones.parquet` (`split`).

## Qué verificar (cada punto con veredicto CORRECTO / INCORRECTO / NO VERIFICABLE y evidencia)
1. **Derivación de la BCE con negativos:** desde y_ui ~ Bernoulli(σ(s_ui)) con independencia, −log verosimilitud sobre
   positivos y negativos muestreados = la pérdida implementada en `perdida_bce` (incluida la normalización). Comprueba
   numéricamente contra `BCEWithLogitsLoss` y contra la fórmula con log σ estable.
2. **Derivación de BPR:** P(i ≻_u j) = σ(s_ui − s_uj) e independencia de pares → −log verosimilitud = `perdida_bpr`; signo correcto
   (el positivo debe quedar arriba); estabilidad con logits grandes. Señala si en algún comentario o docstring se afirma que BCE con
   negativos y BPR son equivalentes (no lo son) o cualquier otra afirmación matemática falsa.
3. **Ecuaciones de las torres contra el código:** u = MLP_u(x_u) + E_U[k(u)], [v_i; b_i] = MLP_i(x_i) + E_I[k(i)], s_ui = ⟨u, v_i⟩ +
   b_i; ReLU solo en capas ocultas; dropout solo en entrenamiento; fila 0 = vector nulo fijo. Carga `models/m3/red.pt` y
   recalcula a mano (numpy, con los pesos) los puntajes de algunos usuarios de prueba y compáralos con
   `recomendaciones_prueba.parquet` (semilla base). Verifica que la torre de usuario con índice 0 es exactamente la composición
   «W·h + b y ReLU» de las capas `Linear` (lo que usa la app, `app/lib/recomendar.ts`).
4. **n_parametros:** recuenta a mano, con las formas de `arquitectura/red.json` y los hiperparámetros finales, el número de
   parámetros entrenables (sin las filas `padding_idx`) y compáralo con `n_parametros` de `summary.json` y con
   `sum(p.numel())` del `state_dict`. Reporta la relación parámetros / interacciones de train (1 066).
5. **Que la red no colapse** (como le pasó a la MF en JJ-4 con X = Y = 0): puntajes no constantes por usuario, embeddings no nulos,
   personalización (¿los puntajes varían entre usuarios o la red se redujo a un sesgo por destino?), tratamiento de los 345
   destinos sin train (índice 0: puntaje solo por su tipo; ¿todos los fríos del mismo tipo tienen el mismo puntaje?). Mira
   `diagnosticos` en `summary.json` y los JSON por semilla, y compruébalo con los pesos guardados.
6. **Métricas de la red recalculadas** desde `recomendaciones_prueba.parquet` (modelo `red`, las 30 semillas) y los relevantes de
   prueba (`split == "prueba"`): NDCG@5, NDCG@10, Recall@5, Recall@10, Precision@5 y cobertura@10; media, desviación (ddof = 1),
   mejor y peor; compáralas con `summary.json` (tolerancia 1e-12). Recalcula también el esperado del azar de NDCG@5 y Recall@10 y el
   error estándar muestral de Recall@10 con 606 usuarios (√(p(1−p)/606)).
7. **Curvas y parada temprana:** `curvas/red.json` es coherente (la mejor época tiene el máximo NDCG@5 de validación, la parada
   ocurre a `paciencia` épocas de la mejor, longitudes iguales).

## Reporte
Veredicto global APROBADO / APROBADO CON OBSERVACIONES / RECHAZADO; por punto, veredicto y evidencia (cifras y fragmentos de
código con `archivo:línea`); los errores encontrados, con la corrección exacta propuesta; y cualquier afirmación del código, los
comentarios o las configs que sea matemáticamente falsa (son candidatos a la cacería de alucinaciones: cita el texto literal).
