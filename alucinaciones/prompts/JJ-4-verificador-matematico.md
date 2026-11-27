# JJ-4 — prompt del orquestador (Opus 5.5) al verificador-matematico (Opus), 2026-11-27

Eres el verificador de la tarea JJ-4 del Trabajo 3 (M3, recomendación de destinos): **modelos de referencia (popularidad,
factorización de matrices implícita por ALS, aleatorio) y métricas @K**. Te dirige la sesión principal de Juan José, rama
`dev/juanjose`. **Solo lees y calculas**: no edites archivos del repositorio (scripts de comprobación, solo en una carpeta
temporal fuera del repo o con `python -c`). Siempre `.venv\Scripts\python` (Bash: `.venv/Scripts/python`). Sin internet salvo
para consultar la fuente primaria del método si la necesitas (no es obligatorio; la cita queda [VERIFICAR] para JJ-9).

## Qué verificar
1. **Métricas recalculadas de forma independiente** (escribe tu propio cálculo; no importes `src/m3_recomendacion/metricas.py`):
   desde `results/data/m3/recomendaciones_prueba.parquet` (columnas `modelo, semilla, usuario_id, rango, destino_id, puntaje`,
   top-10 de cada usuario de prueba para cada modelo y semilla) y `data/processed/m3/interacciones.parquet` (columna `split`),
   recalcula para cada modelo, semilla y K ∈ {1, 3, 5, 10}: acierto@K, Precision@K, Recall@K, NDCG@K, cobertura@K (/1 000),
   Gini y HHI de las exposiciones sobre los 1 000 destinos de `destinos.parquet`, y acierto por lugar@K (K = 1, 3; `lugar` de
   `destinos.parquet`). Compáralos con `results/data/m3/semillas/<modelo>_seed<k>.json` y con los resúmenes (media, desviación
   muestral ddof = 1, mejor, peor) de `summary.json`, `metricas_por_k.json` y `metricas_por_grupo.json` (grupo: pocas = 1..2,
   muchas ≥ 3 interacciones en TOTAL por usuario). Comprueba además que cada lista: no repite destinos, no contiene ningún
   destino del historial conocido del usuario (train ∪ validación) y tiene 10 elementos; que hay 606 usuarios por modelo y
   semilla; y el bloque `destinos_frios` de `summary.json` (205 usuarios con objetivo sin train; techo de la popularidad
   401/606; destinos fríos por lista).
2. **Línea base del aleatorio**: deriva tú los esperados analíticos de un top-K uniforme sin reemplazo sobre C_u (catálogo menos
   historial conocido, N_u = |C_u|): acierto, Precision, Recall, NDCG, cobertura (bajo independencia entre usuarios) y acierto por
   lugar (hipergeométrica: 1 − C(N_u − m_u, K)/C(N_u, K), m_u = candidatos del lugar del objetivo, incluido éste). Recalcúlalos
   con los datos y compáralos con `summary.json` → `linea_base_aleatoria_analitica` (global y por grupo) y con la media simulada
   del modelo aleatorio.
3. **ALS implícito** (Hu, Koren y Volinsky, 2008): en `src/m3_recomendacion/referencias.py` revisa la función objetivo
   L(X, Y) = Σ_{u,i} c_ui (p_ui − x_uᵀy_i)² + λ(Σ‖x_u‖² + Σ‖y_i‖²) con c_ui = 1 + α r_ui (r binaria), su implementación por la
   descomposición «todos los pares + corrección en los observados», y **deriva** las actualizaciones cerradas
   x_u = (YᵀC^uY + λI)⁻¹YᵀC^u p(u), y_i = (XᵀC^iX + λI)⁻¹XᵀC^i p(i), con YᵀC^uY = YᵀY + Yᵀ(C^u − I)Y. Comprueba que el código
   implementa exactamente eso (y que YᵀC^u p(u) = (1 + α)Σ_{i∈N(u)} y_i), que la pérdida no puede aumentar en cada medio paso
   (argumento: minimización exacta de una cuadrática estrictamente convexa por bloque), que y_i = 0 para un destino sin train es
   el mínimo de su bloque, y que n_parametros = (n_usuarios_train + n_destinos)·f = 14 864 con f = 8. Recalcula la pérdida de
   los factores guardados en `models/m3/mf_als.npz` con tu propia fórmula y compárala con el último valor de
   `historial_perdida` en `models/m3/mf_als.json`; comprueba que el historial es no creciente.
4. **Búsqueda**: en `results/data/m3/hpo_ensayos.json`, que el valor de cada ensayo es NDCG@5 medio en VALIDACIÓN (recalcula el
   del mejor ensayo ajustando tú la MF con sus parámetros y la semilla que usa `hpo.py`, o con el código del repo si reimplementar
   es desproporcionado — dilo), y que el mejor declarado es el máximo.
5. **Blog**: en `blog/secciones/07-m3-recomendacion.md`, subsecciones «### Métricas de evaluación» y «### Modelos de
   referencia»: cada ecuación coincide con el código (notación, índices, límites de las sumas, logaritmo en base 2, IDCG,
   normalización de la cobertura, Gini sin reescalar, HHI, esperados del aleatorio, objetivo y actualizaciones de ALS); cada
   cifra de las tablas coincide con el JSON que cita su «Fuente:»; y las afirmaciones de la «lectura de resultados» (errores
   estándar √(p̂(1−p̂)/606), «del mismo orden», 1/HHI como número equivalente, «al menos 394 destinos con exposición 0») son
   correctas matemáticamente. Señala cualquier afirmación que sea falsa o que diga más de lo que las cifras sostienen.

## Informe
Veredicto **APROBADO** / **APROBADO CON OBSERVACIONES** / **RECHAZADO**. Lista numerada de hallazgos, cada uno con: archivo y
línea, lo que dice, lo correcto, la evidencia (tu cálculo o derivación) y la gravedad (bloqueante / menor). Incluye las
diferencias numéricas máximas que encontraste en (1) y (2). Si un hallazgo es un error de una IA (implementador o redactor),
márcalo como candidato a la cacería de alucinaciones (categoría: Matemáticas o Código).
