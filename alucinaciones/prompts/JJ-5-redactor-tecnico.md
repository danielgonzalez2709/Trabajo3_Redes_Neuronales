# JJ-5 — prompt literal del orquestador (Opus 5.5) al redactor-tecnico (Sonnet), 2026-11-27

Eres el redactor-tecnico de la tarea JJ-5 del Trabajo 3 (M3: red neuronal recomendadora de dos torres). Repositorio
`C:\Repositorios\Trabajo3_Redes_Neuronales`, rama `dev/juanjose`. Sin commits. Usa `.venv\Scripts\python` para leer los JSON (con
`PYTHONIOENCODING=utf-8` si imprimes). Prohibido inventar cifras, referencias o resultados: **toda cifra sale de un archivo de
`results/data/m3/`** (núcleo §0.7) y la copias con los decimales del archivo, redondeando de forma explícita. Lo que sea cálculo o
interpretación tuya lo marcas con un comentario `<!-- revisar: Juan José — ... -->` como ya hace la sección, explicando de dónde sale.

## Qué escribir
En `blog/secciones/07-m3-recomendacion.md`, **después** de la sección «### Modelos de referencia» (y antes de lo que venga a
continuación, si hay algo), una sección nueva **«### Red neuronal de dos torres»** con:
1. **Arquitectura**: ecuaciones de la torre de usuario, la torre de destino y el puntaje, con la notación del docstring de
   `src/m3_recomendacion/red.py` (x_u: 5 preferencias one-hot; x_i: tipo one-hot de 5 columnas; MLP con ReLU en las capas ocultas
   y dropout; embeddings de id sumados a la salida, índice 0 = «sin id», vector nulo fijo; [v_i; b_i] ∈ ℝ^{d+1}; s_ui = ⟨u, v_i⟩ + b_i;
   «dropout de id» con probabilidad p). Explica por qué solo `tipo` (en el catálogo `tipo`, `estado`, `mejor_epoca` y `lugar` son la
   misma variable de 5 categorías) y por qué ninguna popularidad (H-M3-3: ρ = −0,011). Que la torre de usuario con índice 0 es la que
   recibe un perfil nuevo en la aplicación (solo ReLU y capas lineales, como pide el contrato de la app). Cita la figura de
   arquitectura.
2. **Pérdidas derivadas de su modelo probabilístico**: BCE con negativos muestreados desde y_ui ~ Bernoulli(σ(s_ui)) con
   independencia (−log verosimilitud, normalizada por B(1+m)) y BPR desde P(i ≻_u j) = σ(s_ui − s_uj) (−log verosimilitud,
   normalizada por Bm). Di que no son equivalentes (BPR solo mira diferencias: sumar una constante a todos los puntajes no la cambia;
   la BCE sí). Si citas BPR, usa una clave de `blog/references.bib` si existe; si no existe, escribe `TODO(cita)` y repórtalo (no
   inventes la entrada; la verifica JJ-9).
3. **Justificación** con cifras: dimensión d (la búsqueda eligió d = 32; relación parámetros / interacciones de train = 52 192 /
   1 066 ≈ 49; la MF eligió f = 4; dilo con honestidad: d = 32 salió del máximo de 20 NDCG@5 de validación con pocos aciertos, no de
   un criterio de parsimonia); negativos uniformes sobre catálogo − train del usuario, re-muestreados cada época (H-M3-5: Gini por
   destino 0,383 frente a 0,386 del reparto uniforme, IC 95 % [0,370; 0,401]: el muestreo por popularidad no aportaría); pérdida (la
   búsqueda eligió BCE).
4. **Búsqueda**: Optuna TPE con semilla fija, 20 ensayos (mismo presupuesto que la MF), objetivo NDCG@5 en validación, espacio
   (de `configs/m3/hpo.yaml` → `red.busqueda.espacio`; o `hpo_ensayos.json` → `familias.red.espacio`), tiempo y mejor configuración
   (`familias.red.mejor`). Cita la figura de la búsqueda. Parada temprana por NDCG@5 de validación con paciencia 10; cita la figura de
   curvas y di lo que muestra (la pérdida de validación no baja mientras la de train sí; la mejor época y la parada).
5. **Resultados en prueba frente a las referencias**: tabla numerada con los 4 modelos (media ± desviación sobre 30 semillas de
   NDCG@5, NDCG@10, Recall@5, Recall@10, cobertura@10, `n_parametros`, `n_configuraciones_busqueda`, `tiempo_total_s`) y el esperado
   del azar (`summary.json → linea_base_aleatoria_analitica.global`). Cita la figura de cajas. Lee las diferencias frente al error
   muestral de 606 usuarios (√(p(1−p)/606) ≈ 0,004 en Recall@10), no solo frente a la desviación entre semillas. Reporta los
   destinos fríos (`summary.json → destinos_frios`): la red, como la popularidad y la MF, no acierta ningún objetivo frío y no mete
   ningún frío en sus listas, aunque les da puntaje por su tipo. Reporta los diagnósticos de la red (`summary.json →
   modelos.red.diagnosticos`): ninguna semilla degenerada; personalización, fracción de varianza de interacción, listas top-10
   distintas y fracción con el mismo top-1, **diciendo que se calculan sobre los 326 usuarios de validación**, y que en 4 de las 30
   semillas (8, 10, 13 y 16, de los JSON por semilla) todos esos usuarios reciben el mismo top-1.
6. **Solo resultados**: la respuesta a «¿qué aportó la red?» queda para JJ-10; aquí no concluyas. La fundamentación común (neurona,
   activaciones, backpropagation, Adam, regularización) NO va aquí: es JJ-8; puedes remitir a ella sin desarrollarla.

Además, en «### Modelos de referencia», **actualiza los tiempos** que cambiaron al volver a correr la búsqueda y el experimento (las
métricas NO cambiaron): la MF hoy tiene `tiempo_total_s`, `tiempo_busqueda_s` y `tiempo_corridas_finales_s` distintos de los que
cita el texto (33,86 s, 17,16 s y 16,70 s) y la popularidad y el aleatorio también; tómalos de `summary.json`. Revisa todo número de
tiempo de esa sección y de sus tablas.

## Formato (mismo que el resto de la sección)
- Figuras con el bloque `::: figura <id>` / `Título:` / `Fuente: Elaboración propia a partir de results/data/m3/...; datos generados
  de [@mehra2024].` / `![texto alternativo](figures/m3/<archivo>.png)` / `:::`, y citadas en el texto con `[[fig:<id>]]` ANTES de
  aparecer. Tablas igual con `::: tabla <id>` (mira cómo están hechas las de la sección) y `[[tab:<id>]]`. Las figuras son
  `red_arquitectura.png`, `red_curvas.png`, `busqueda_m3.png` y `cajas_m3.png` en `blog/docs/figures/m3/` (mira las imágenes).
- Sin rutas de archivo en las frases del texto (sí en «Fuente:» y en los comentarios `revisar`). Español, decimales con coma,
  ecuaciones en LaTeX como el resto. Datos generados (D4): las conclusiones valen para el método, no para turistas reales.
- Al final corre la construcción estricta del blog: `.venv\Scripts\python -m mkdocs build --strict -f blog/mkdocs.yml` (pega la
  salida; debe terminar sin advertencias).

## Fuentes que puedes leer
`docs/spec/partes/juanjose.md` §3.2 (D15–D19), el Anexo de `docs/spec/SPEC.md` «Módulo 3» (tarea 5 y fundamentación) y «Figuras
mínimas comunes», `src/m3_recomendacion/red.py` (docstring), `configs/m3/{base,hpo}.yaml`, y en `results/data/m3/`: `summary.json`,
`hpo_ensayos.json`, `curvas/red.json`, `arquitectura/red.json`, `semillas/red_seed*.json`, `eda/hipotesis.json`.

## Reporte
Secciones escritas o cambiadas (líneas), lista de cada cifra nueva con su archivo y clave de origen, comentarios `revisar` que dejaste,
`TODO(cita)` pendientes y la salida de la construcción estricta.
