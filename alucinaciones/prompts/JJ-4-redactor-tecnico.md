# JJ-4 — prompt del orquestador (Opus 5.5) al redactor-tecnico (Sonnet), 2026-11-27

Tarea JJ-4 (C6) del Trabajo 3: redacta en `blog/secciones/07-m3-recomendacion.md`, **justo después de la subsección
«### Partición»** (al final del archivo hoy), dos subsecciones nuevas: **«### Métricas de evaluación»** y **«### Modelos de
referencia»**. Te dirige la sesión principal de Juan José, rama `dev/juanjose`. Idioma: español.

## Reglas
- NO commits, NI push, NI PR. Siempre `.venv\Scripts\python` (Bash: `.venv/Scripts/python`). Sin internet.
- Solo editas `blog/secciones/07-m3-recomendacion.md` (y nada más). No toques `blog/references.bib`.
- **Toda cifra sale de un archivo de `results/data/m3/`** (léelo tú; no copies cifras de este prompt sin comprobarlas). Prohibido
  inventar cifras, referencias o interpretaciones de los datos. Lo que sea interpretación tuya va marcado con un comentario
  `<!-- revisar: Juan José — … -->`, como en las subsecciones anteriores.
- **Sin rutas de archivos dentro de las frases**: las rutas van solo en la línea «Fuente:» de cada tabla.
- Tablas con el formato del hook del blog (mira las de «### Partición»): bloque `::: tabla <id>` con `Título:` y `Fuente:`,
  cerrado con `:::`, y **citada en el texto** con `[[tab:<id>]]` antes o cerca de la tabla. Ids nuevos con prefijo `m3-`.
- Ecuaciones con `$…$` en línea y `$$ … $$` en bloque (como en `03-m1-datos-descriptivo.md`).
- **Citas:** la bibliografía solo admite entradas verificadas con DOI o URL, y una cita `[@clave]` que no esté en
  `references.bib` rompe la construcción. Hu, Koren y Volinsky (2008) aún NO está verificada (JJ-9): escríbela en prosa,
  «Hu, Koren y Volinsky (2008)», sin `[@…]`, con un comentario `<!-- TODO(cita): Hu, Koren y Volinsky (2008) [VERIFICAR en JJ-9];
  pasar a [@clave] cuando esté en references.bib -->`. No agregues otras referencias.
- **Sin conclusiones sobre la red neuronal** (eso es JJ-5/JJ-10) y sin responder las preguntas de negocio (JJ-6); sí puedes decir
  qué medida se usará para la pregunta de negocio 2 (concentración).

## Lee antes de escribir
- `blog/secciones/07-m3-recomendacion.md` completo (tono, formato y lo ya dicho; no lo repitas: refiérete a «Partición»).
- `docs/spec/partes/juanjose.md` §3.1 (D9, D10), §3.2 (D11, D13, D14) y §3.3 (D12).
- Código (para que las ecuaciones coincidan EXACTAMENTE con lo implementado): `src/m3_recomendacion/metricas.py`,
  `referencias.py` (clase de ALS implícito), `hpo.py`, `experimento.py`; configs `configs/m3/base.yaml`, `hpo.yaml`.
- Resultados: `results/data/m3/summary.json`, `metricas_por_k.json`, `metricas_por_grupo.json`, `hpo_ensayos.json`.

## Contenido

### «### Métricas de evaluación»
- Notación: usuario u, candidatos $C_u$ (catálogo menos el historial conocido, D10), relevantes $R_u$, lista recomendada
  $L_u^K$, rango $r$.
- Definiciones con ecuación de: acierto@K, Precision@K, Recall@K, NDCG@K (DCG e IDCG generales y su forma con un relevante),
  cobertura del catálogo, exposiciones $e_i$, Gini y HHI de las exposiciones (las mismas fórmulas del código y del
  descriptivo), acierto por lugar@K (solo K ∈ {1, 3}) y su línea base del azar. Cada métrica se promedia sobre los usuarios
  evaluados (dilo con la ecuación del promedio).
- Aclaración explícita: como cada usuario de prueba tiene exactamente un destino relevante, Recall@K = acierto@K,
  Precision@K = acierto@K / K e IDCG = 1. Por eso Precision@K tiene techo 1/K.
- Valores esperados del recomendador aleatorio (las fórmulas de `metricas.py`), para leer los resultados contra el piso.
- K ∈ {1, 3, 5, 10}; K = 5 es el valor por defecto del caso de uso.
- Resultados por grupo de actividad (pocas ≤ 2, muchas ≥ 3, con el total de interacciones del usuario): solo estratifica.

### «### Modelos de referencia»
- **Popularidad**: puntaje = conteo de interacciones del destino en entrenamiento (D9, D11), igual para todos; empates al
  azar con la semilla de la corrida; destinos sin interacciones en entrenamiento quedan al final. Aclara que la columna de
  popularidad de la fuente NO se usa.
- **Factorización de matrices implícita por ALS** (Hu, Koren y Volinsky, 2008, ver regla de citas): $p_{ui}$, $c_{ui} = 1 +
  \alpha r_{ui}$, función objetivo completa con la regularización, actualizaciones cerradas de $x_u$ y de $y_i$ (y la
  identidad $Y^\top C^u Y = Y^\top Y + Y^\top (C^u - I) Y$ que las hace baratas), inicialización, puntaje $x_u^\top y_i$, por qué
  la pérdida no aumenta en cada medio paso (cada uno minimiza exactamente un problema cuadrático convexo), y que un destino sin
  interacciones en entrenamiento queda con $y_i = 0$. Número de parámetros $(n_\text{usuarios} + n_\text{destinos})\cdot f$.
- **Aleatorio**: piso de referencia, con su esperado analítico.
- **Búsqueda declarada (comparación justa)**: Optuna TPE, 20 ensayos, objetivo NDCG@5 en validación, espacio (rangos del YAML,
  di que son elección del equipo), mejor configuración y su valor; popularidad y aleatorio con 1 configuración y 0
  hiperparámetros. Recuerda el sesgo ya anotado en «Partición»: la validación solo tiene usuarios de «muchas».
- **Tablas** (todas con `::: tabla`, título, fuente y citadas en el texto):
  1. Presupuesto y complejidad por modelo: `n_parametros`, `n_configuraciones_busqueda`, `tiempo_total_s`, hiperparámetros.
  2. Resultados en prueba por K, media ± desviación sobre 30 semillas, para Precision, Recall, NDCG y cobertura de los tres
     modelos, con la columna del esperado analítico del aleatorio.
  3. Resultados por grupo de actividad (pocas / muchas) para al menos NDCG@5 y Recall@10 (media ± desviación) con el esperado
     del aleatorio de cada grupo y el número de usuarios por grupo.
  4. Concentración de las exposiciones (Gini y HHI, por K o al menos K = 5 y 10) y acierto por lugar (K = 1, 3) con su línea
     base del azar.
  5. Destinos fríos (D14): usuarios con objetivo frío, techo de acierto de la popularidad, cuántas veces entra un destino frío
     en la lista de cada modelo.
- **Lectura de los resultados** (corta, sin exagerar): compara con el piso aleatorio usando la variabilidad que de verdad
  aplica. Aclara que la desviación entre las 30 semillas solo recoge la inicialización y los empates, **no** la incertidumbre
  muestral de los 606 usuarios de prueba: para una proporción $\hat p$ con $n = 606$ el error estándar es
  $\sqrt{\hat p(1-\hat p)/n}$ (calcúlalo tú con la cifra del JSON y escríbelo como cálculo tuyo en un comentario `revisar`).
  Relaciona con lo hallado en el descriptivo (interacciones parecidas a un reparto uniforme al azar) sin repetirlo entero.
  Di qué significa una concentración alta de la popularidad y la MF frente al aleatorio, sin responder aún la pregunta de
  negocio 2. Nada sobre la red.

## Comprobación (pega la salida real en tu informe)
- `.venv\Scripts\mkdocs build --strict -f blog/mkdocs.yml` (o `.venv\Scripts\python -m mkdocs build --strict -f
  blog/mkdocs.yml`) sin advertencias.
- `.venv\Scripts\python -m pytest -q tests/test_blog.py` en verde.

## Informe final (breve)
Qué escribiste (ids de las tablas), de qué claves de qué JSON sale cada cifra, la salida de las dos comprobaciones y la lista de
lo que marcaste como `revisar` o `TODO(cita)`.
