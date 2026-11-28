# Prompt JJ-2 — analista-experimentos (Sonnet) — 2026-11-26 — orquesta: Juan José

Actúa como el agente definido en `.claude/agents/analista-experimentos.md` (léelo primero). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales`, rama `dev/juanjose`. **No hagas commit, push ni PR.** Usa siempre
`.venv\Scripts\python` (desde Git Bash: `.venv/Scripts/python`). Sin internet. **Prueba primero, luego código.**
No toques archivos compartidos: `src/comun/`, `run.py`, `requirements.txt`, `docs/spec/SPEC.md`, `src/viz/estilo.py`,
`src/viz/paleta.py`, ni archivos de otros módulos. Puedes crear/modificar SOLO: `tests/test_eda_m3.py`,
`configs/m3/eda.yaml`, `src/m3_recomendacion/eda.py`, `src/viz/figs_m3.py`, `blog/docs/figures/m3/*.png` (generadas),
`results/data/m3/eda/*` (generados por código, nunca a mano), y para E6: `src/m3_recomendacion/datos.py`,
`configs/m3/datos.yaml`, `tests/test_datos_m3.py`, `src/m3_recomendacion/README.md`.

## Contexto que debes leer (y nada de otras partes)
- `docs/spec/SPEC.md`: §0 (reglas), §5.7 (datos de M3), §5.12 (plantilla común de análisis descriptivo y contrato de
  `hipotesis.json`), §6 (comparación justa) y el Anexo «Módulo 3: Recomendación de destinos de viaje» (Datos, Tareas 1–2,
  Figuras mínimas).
- `docs/spec/partes/juanjose.md` §3.1 (decisiones D1–D7 [DECIDIDO, Juan José, 25-nov]) y §3.3.
- `results/data/m3/eda/ficha.json` y `diccionario.json` (salidas de JJ-1); `src/m3_recomendacion/datos.py` y
  `configs/m3/datos.yaml` (estilo de código y de config a imitar); `tests/test_datos_m3.py` y `tests/fixtures/m3/`.
- `src/comun/eda.py` (usa `escribir_hipotesis`, `validar_hipotesis`), `src/comun/results.py` (`save_json`),
  `src/comun/seeds.py` (`make_rng(base_seed, run_id)`; prohibido `np.random.seed` global), `src/comun/config.py`,
  `src/comun/cli.py` (cómo `run.py m3-eda` llama a `main(cfg)` y cómo `run.py figures` llama a `generar()` de
  `src/viz/figs_*.py` y espera las rutas escritas), `src/viz/estilo.py` (`aplicar_estilo`, `guardar_figura`,
  `mapa_secuencial`) y `src/viz/paleta.py`.

## Hechos de los datos procesados que ya midió la sesión principal (verifícalos tú con código; no los copies)
- `data/processed/m3/`: `destinos.parquet` (destino_id, nombre, lugar, estado, tipo, mejor_epoca, popularidad),
  `usuarios.parquet` (usuario_id, preferencias, pref_adventure, pref_beaches, pref_city, pref_historical, pref_nature,
  genero, n_adultos, n_ninos), `interacciones.parquet` (usuario_id, destino_id, origen ∈ {resena, historial}, id_origen,
  calificacion 1–5, fecha_visita solo descriptiva). 999 usuarios, 1 000 destinos, 1 998 interacciones, sin pares repetidos.
- Cada `lugar` tiene un único `tipo` (goa_beaches→Beach, jaipur_city→City, kerala_backwaters→Nature,
  leh_ladakh→Adventure, taj_mahal→Historical), 200 ids por lugar.
- Solo hay 3 combinaciones de `preferencias` («Beaches, Historical», «Adventure, Nature», «City, Historical»), 333
  usuarios cada una; cada combinación cubre 2 de los 5 tipos.
- Las opciones de preferencia y los tipos usan vocabularios distintos («Beaches» vs «Beach»). El emparejamiento
  opción → tipo (Beaches→Beach, Historical→Historical, City→City, Adventure→Adventure, Nature→Nature) **no lo documenta la
  fuente**: ponlo explícito en `configs/m3/eda.yaml` con un comentario que diga que es un emparejamiento léxico nuestro, y
  repítelo así en el `resultado`/`justificacion` de la hipótesis.

## Qué construir

### E1. `tests/test_eda_m3.py` (primero; que falle antes de tener el código)
Con datos mínimos construidos en la prueba (o los fixtures de `tests/fixtures/m3/` pasados por `datos.py`), probar:
- `hipotesis.json` escrito por `main` pasa `src/comun/eda.validar_hipotesis`; ids `H-M3-<n>`; cada hipótesis con
  `veredicto` válido; las que dependen de modelos con `pendiente`.
- Gini, HHI, cuota del top 10 % y top 20 % y la curva de Lorenz contra un **cálculo a mano** en un ejemplo pequeño (p. ej.
  conteos [0, 1, 1, 2, 6]; escribe en un comentario el cálculo y el valor esperado). Define la fórmula que uses (Gini con
  corrección o sin ella; HHI con cuotas en [0, 1]) y que la prueba fije esa definición. Incluye casos borde: todos iguales
  → Gini 0; uno solo concentra todo.
- Tasa de coincidencia preferencia–tipo y su **línea base de azar exacta** en un ejemplo a mano (catálogo pequeño con
  tipos de distinto tamaño, para que la línea base no sea trivialmente 2/5).
- Determinismo: dos corridas de `main` con la misma config → mismos bytes en todos los archivos de salida.
- Que `main` no lea `data/raw` (p. ej., config apuntando a una carpeta temporal con solo los parquet procesados).
- `figs_m3.generar()` escribe los PNG esperados leyendo solo de una carpeta de resultados (puedes parametrizar las rutas
  para poder probarlo en `tmp_path`).
Marca como `@pytest.mark.lento` lo que tarde más de ~2 s (revisa `pytest.ini`/`conftest.py` para la marca existente).

### E2. `configs/m3/eda.yaml` (comentado, en el estilo de `configs/m3/datos.yaml`)
Rutas de entrada (`data/processed/m3/`), salida (`results/data/m3/eda/`), carpeta de figuras
(`blog/docs/figures/m3/`) si la necesitas, `base_seed`, `n_permutaciones` (un número que haga el p-valor de permutación
suficientemente fino y que corra en segundos, p. ej. 10 000 si cabe), `n_simulaciones_azar` para la referencia uniforme,
niveles de análisis (`destino_id`, `lugar`), emparejamiento preferencia→tipo, umbral de actividad, nivel `alfa` (0,05) y
el método de ajuste por comparaciones múltiples (Holm). Cada `run_id` distinto para cada uso del azar (p. ej. permutación
de H-M3-1 = run 0, simulación uniforme = run 1, …), documentado en la config.

### E3. `src/m3_recomendacion/eda.py` con `main(cfg) -> int` (lo llama `run.py m3-eda --config configs/m3/eda.yaml`)
Lee SOLO `data/processed/m3/` y escribe en `results/data/m3/eda/` (no toques `ficha.json`, `calidad.csv` ni
`diccionario.json`, que son de `m3-datos`). Salidas (nombres sugeridos; elige nombres claros en español y sé consistente):
- `interacciones_por_usuario.csv` y `interacciones_por_destino.csv` / `interacciones_por_lugar.csv` (conteo por entidad,
  incluidos los de 0) y `distribucion_actividad.json`: histograma de usuarios por número de interacciones (0, 1, 2, 3, 4,
  5+) **y** de destinos por número de interacciones; para cada uno, la referencia de lo esperado si las 1 998 interacciones
  se repartieran uniformemente al azar (simulada con la semilla, media e intervalo del 95 % sobre las simulaciones).
  Debe coincidir con `ficha.json` → `conteos.usuarios_por_numero_de_interacciones.union` (compruébalo en el código o en la
  prueba).
- `calificaciones.csv`: distribución 1–5 por origen (conteo y proporción), media y desviación por origen.
- `concentracion.json`: para `destino_id` y `lugar`: Gini, HHI (y HHI normalizado si lo usas, declarado), cuota del top
  10 % y top 20 % de entidades más populares, puntos de la curva de Lorenz, y lo mismo bajo asignación uniforme al azar
  (media e IC 95 % de las simulaciones) con el percentil/p-valor del observado dentro de esa distribución.
- `actividad_usuarios.json`: usuarios por grupo de actividad «pocas» vs «muchas» interacciones, con el umbral y su
  justificación coherente con D3 (con D3 un usuario con 1 interacción solo está en train, con 2 tiene 1 en train y 1 en
  prueba, con ≥ 3 aporta además validación; un umbral natural es pocas ≤ 2, muchas ≥ 3: justifícalo o propón otro con
  razones). Reporta también cuántos usuarios de cada grupo tendrán interacción de prueba según D3 (cálculo de conteo, sin
  hacer la partición, que es de JJ-3) y la proporción de usuarios con pocas interacciones.
- `pruebas_hipotesis.json`: una entrada por prueba con estadístico, gl si aplica, p-valor crudo, p-valor ajustado (Holm
  sobre la familia de pruebas confirmatorias, declarada en el archivo), tamaño de efecto con su intervalo cuando aplique, n.
- `matriz_preferencias_tipo.csv`: conteos y proporciones por fila (combinación de preferencias × tipo de destino), para la
  figura (c).
- `hipotesis.json` con `src/comun/eda.escribir_hipotesis`.
Imprime un resumen corto. Debe tardar segundos y ser determinista (orden de filas fijo, flotantes sin aleatoriedad
no sembrada; JSON escrito con `save_json`).

### E4. Hipótesis (ids `H-M3-1`, `H-M3-2`, …): enunciado, justificación, evidencia esperada, figura o tabla, resultado y
veredicto (`confirmada` / `refutada` / `no concluyente` / `pendiente`), y `evidencia` con las cifras y la ruta del archivo
de donde salen. Mínimo:
1. Las preferencias declaradas explican el TIPO de destino con el que interactúa el usuario. Medida: tasa de coincidencia
   (interacción cuyo tipo está entre los tipos que cubre la combinación de preferencias del usuario). Línea base de azar
   **exacta**: para cada interacción, la probabilidad de coincidir si el destino se eligiera uniforme en el catálogo
   (= fracción de ids del catálogo cuyo tipo está en las preferencias del usuario); su promedio sobre las interacciones.
   Reporta también una segunda línea base que conserve la distribución marginal de tipos observada en las interacciones.
   Pruebas: χ² de independencia en la tabla combinación × tipo (V de Cramér) y prueba de permutación de la tasa de
   coincidencia (permuta las combinaciones de preferencias entre usuarios, conservando cuántas interacciones tiene cada uno;
   p = (1 + #{T* ≥ T_obs}) / (1 + B)). Reporta la diferencia (tasa − línea base) con IC 95 % (bootstrap por usuarios o
   aproximación normal, declarada). Da la tasa por combinación.
2. La calificación es mayor cuando el destino coincide con las preferencias (Mann–Whitney o permutación; diferencia de
   medias con IC; tamaño de efecto, p. ej. delta de Cliff o probabilidad de superioridad).
3. `popularidad` del destino se relaciona con su número de interacciones (Spearman con IC o permutación, a nivel
   `destino_id`; ojo: 1 000 destinos con 0–pocas interacciones, hay muchos empates).
4. La demografía (género, n_adultos, n_ninos) se relaciona con el tipo/lugar elegido (p. ej. familias con niños → playa):
   χ² por variable × tipo con V de Cramér; cuidado con la dependencia de varias interacciones del mismo usuario (decláralo
   como limitación o usa permutación a nivel de usuario).
5. Hay concentración en pocos destinos (cola larga) más allá de lo esperado por azar: Gini/HHI/cuota top observados frente
   a la distribución bajo asignación uniforme simulada, a nivel `destino_id` y `lugar`.
6. Reseñas e historial se comportan distinto: tipos (χ² origen × tipo) y calificaciones (χ² origen × calificación o
   Mann–Whitney).
7. Al menos una hipótesis que SOLO se cierra al modelar, con `veredicto: "pendiente"` y `resultado` que diga que se cierra
   en JJ-10; p. ej. «una red con variables de contenido no supera a la popularidad por más que la variabilidad entre
   semillas (NDCG@5, 30 semillas)». Puedes agregar otra pendiente, p. ej. «el acierto por `lugar` es mucho mayor que el
   acierto por `destino_id`».
Familia de comparaciones múltiples: las pruebas confirmatorias de 1–6 (decláralas); ajuste de Holm. Veredicto según el
p-valor **ajustado** y el tamaño de efecto: no declares «confirmada» si el efecto es despreciable aunque el p-valor sea
pequeño (define el criterio en la config y en el `resultado`; p. ej. V de Cramér < 0,1 = efecto pequeño → como mucho
«no concluyente» o describe el efecto con su tamaño). «Refutada» solo si la evidencia es contraria o el efecto es
compatible con cero con un intervalo estrecho, y explica por qué. No adelantes conclusiones que los números no respalden.
**Advertencia:** los datos son generados (D4). Si un patrón aparece, no lo atribuyas a comportamiento real de turistas.

### E5. `src/viz/figs_m3.py` con `generar() -> list[Path]` (lo llama `run.py figures`)
Lee SOLO de `results/data/m3/eda/` (no `data/raw`, y en lo posible tampoco `data/processed`), usa `aplicar_estilo()` y
`guardar_figura()`, y escribe en `blog/docs/figures/m3/`:
- (a) `cola_larga.png` (obligatoria, figura mínima del enunciado): interacciones por usuario y por destino (dos paneles;
  p. ej. histograma o rango-frecuencia), con la referencia de lo esperado por azar (media e IC de la simulación).
- (b) `lorenz.png`: curva de Lorenz (o cuota acumulada) para `destino_id` y `lugar`, con la diagonal de igualdad y la
  referencia uniforme simulada.
- (c) `preferencias_tipo.png`: matriz combinación de preferencias × tipo de destino (proporciones por fila, con anotación
  de la proporción), marcando las celdas que coinciden con las preferencias; menciona en el título o un pie la línea base.
- (d) `calificaciones_origen.png`: distribución de calificaciones 1–5 por origen.
Títulos, ejes y leyendas en español. Sin datos inventados; si falta un archivo de resultados, error claro que diga qué
comando correr (`run.py m3-eda`).

### E6. Rótulo impreciso de JJ-1
Kaggle no da «fecha de publicación»: la fecha 2024-01-23 es la **creación de la versión 1 en Kaggle**
(`versions[0].creationDate`). En `src/m3_recomendacion/datos.py`, `configs/m3/datos.yaml` (comentario de
`conclusion_real_o_sintetico`), `tests/test_datos_m3.py` y `src/m3_recomendacion/README.md`, cambia los textos «posteriores a
la publicación (del conjunto)» por «posteriores a la creación de la versión 1 en Kaggle» y las claves
`fecha_publicacion` → `fecha_creacion_version_1` y `filas_posteriores_a_la_publicacion` →
`filas_posteriores_a_la_version_1` (renombra también la función `_publicacion`). Luego **regenera** con
`.venv/Scripts/python run.py m3-datos --config configs/m3/datos.yaml` (no edites `results/` a mano) y comprueba con `grep`
que «publicaci» ya no aparece en `results/data/m3/`, `configs/m3/`, `src/m3_recomendacion/` ni `tests/test_datos_m3.py`.
(Los textos de `docs/` los corrige la sesión principal; no los toques.)

## Al terminar
1. `.venv/Scripts/python -m pytest -q -m "not lento"` en verde (pega la salida); corre también `tests/test_eda_m3.py`
   completo.
2. Corre `run.py m3-eda --config configs/m3/eda.yaml` **dos veces** y demuestra con SHA-256 que las salidas son idénticas;
   corre `run.py figures`. Pega las salidas reales y el tiempo.
3. Responde con: archivos creados/modificados; tabla de hipótesis (id, enunciado corto, estadístico, p crudo, p ajustado,
   efecto con IC, veredicto); 5–10 viñetas de lo que muestran los datos sin exagerar; y cualquier decisión que tomaste y que
   Juan José deba confirmar (umbral de actividad, criterio de veredicto, emparejamiento). Si algo del Spec o de D1–D7 te
   impide hacer lo pedido, **no lo resuelvas tú**: repórtalo.
