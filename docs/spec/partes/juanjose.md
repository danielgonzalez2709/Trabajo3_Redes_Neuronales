# Spec de Juan José — M3: recomendación, fundamentación común, bibliografía y clon limpio

| | |
|---|---|
| Responsable | **Juan José** |
| Rama | `dev/juanjose` |
| Archivos propios | `src/m3_recomendacion/`, `configs/m3/`, `data/processed/m3/`, `data/fuentes.md` (M3), `results/data/m3/`, `models/m3/`, `src/viz/figs_m3.py`, `notebooks/05_m3.py`, `app/public/model/m3/`, `blog/references.bib`, blog: M3, fundamentación común |
| Lee del núcleo | §0, §1.2, §3, §4.1, §5.7–§5.10, §5.12, §6, §7.1. **Anexo:** M3 completo; Entregable 1 (fundamentación común, APA); Entregable 3 (clon limpio); Regla de comparación justa; Discusión |
| Dependencias | **Ninguna para avanzar en M3.** Para la fundamentación común necesitas, el vie 27, qué activaciones, optimizador y regularización usó cada uno; para la bibliografía, las referencias que te pidan; para el clon limpio, todo en `main` el lun 30 |

## 1. Lo que pide el enunciado
- Datos: usuarios, destinos, interacciones, escala de calificaciones, densidad, variables de usuarios y destinos; **¿real o
  sintético según la fuente?** y qué implica.
- Tareas 1–6: caso de uso (momento, canal, K, información disponible); descriptivo (interacciones por usuario y destino,
  concentración, usuarios con pocas interacciones, hipótesis); partición sin interacciones de prueba en train; popularidad y
  filtrado colaborativo clásico; recomendador neuronal con **al menos una variable de contenido**, justificando dimensión de
  embeddings, muestreo de negativos y pérdida; Precision, Recall, NDCG@K, cobertura, pocos vs. muchos, 5 usuarios explicados.
- Negocio: usuarios nuevos (≥ 2 estrategias simuladas), concentración de la demanda, campaña de un destino con supuestos.
- Fundamentación de M3: factorización de matrices y arquitectura; derivación de la pérdida (BCE con negativos o BPR); métricas.
- **Fundamentación común:** neurona artificial, cada activación usada, backpropagation, ecuaciones del optimizador usado,
  formulación de cada regularización usada.
- **Bibliografía APA 7**: toda referencia existe, es verificable y está citada.
- **Clon limpio** en una máquina distinta a la de desarrollo.

## 2. Consumo / Entrego
| Consumo | De | Cuándo |
|---|---|---|
| Activaciones, optimizador y regularización usados | Andrés, José, Camila | vie 27 |
| Referencias por verificar | todos | continuo |
| Todo en `main` | Daniel | lun 30 |

| Entrego | A | Cuándo |
|---|---|---|
| Ficha y descriptivo de M3 (plantilla §5.12) | blog | mié 25 |
| Exportación del recomendador (§5.8) | Daniel | **sáb 28, noche** |
| Fundamentación común | blog | dom 29, 8 p. m. |
| `references.bib` verificado | blog | dom 29, 8 p. m. |
| Informe del clon limpio | Daniel | lun 30 |

## 3. Especificación

### 3.1 Datos, descriptivo y partición (JJ-1 a JJ-3) [PROPUESTO]
Descarga manual desde Kaggle (no se versiona la clave) [VERIFICAR archivos y columnas]. Real o sintético: citar lo que diga la
página del conjunto; si no lo dice, declararlo «no documentado» y analizar señales (distribuciones demasiado uniformes, etc.).
Partición: por tiempo si hay fechas; si no, *leave-k-out* por usuario con semilla fija (usuarios con < k interacciones solo en
train y reportados aparte). `test_fuga_m3.py`: ninguna interacción de test en train ni en el cálculo de popularidad.

### 3.2 Modelos (JJ-4, JJ-5) [PROPUESTO]
- Popularidad (calculada solo con train) y factorización de matrices (o KNN por ítems).
- Red: NCF o dos torres con variables de contenido del usuario (p. ej. preferencias) y del destino (p. ej. tipo, región)
  [VERIFICAR cuáles existen]. Negativos muestreados uniformes o por popularidad, justificados; pérdida BCE o BPR derivada.
- La torre de usuario debe poder recibir un **perfil nuevo armado con la lista de preferencias** (lo pide la app).
- Búsqueda Optuna 20 ensayos [PROPUESTO]; 30 semillas.

### 3.3 Evaluación y negocio (JJ-6)
Métricas @K para K ∈ {1, 3, 5, 10} [PROPUESTO], cobertura, Gini o HHI de las exposiciones, desempeño por grupo de actividad,
5 usuarios explicados, t-SNE o UMAP de los embeddings de destinos. Usuarios nuevos simulados ocultando su historial en test
(popularidad vs. contenido/preferencias). Campaña: grupo objetivo y conversiones esperadas con supuestos explícitos.

### 3.4 Fundamentación común (JJ-8) y bibliografía (JJ-9)
Lista cerrada el vie 27 a partir de las configs finales de todos. Cada ecuación revisada por el `verificador-matematico`.
`references.bib` solo con BibTeX oficial del DOI contrastado con Crossref (`investigador-fuentes` + `cazador-alucinaciones`).

## 4. Tareas
| ID | Tarea | Fecha | Agente (modelo) | + Verificador | Aceptación | Estado |
|---|---|---|---|---|---|---|
| JJ-1 | Descarga y ficha; real o sintético | mar 24 | curador-datos (Sonnet) + investigador-fuentes (Sonnet) | cazador-alucinaciones (Opus) | `ficha.json` con densidad y escala medidas | ⬜ |
| JJ-2 | Descriptivo M3 (plantilla §5.12) + caso de uso | mié 25 | analista-experimentos (Sonnet) | revisor-spec (Sonnet) | `hipotesis.json`; figura de cola larga | ⬜ |
| JJ-3 | Partición sin fuga | mié 25 | implementador-experto (Opus) 🧠 | auditor-fugas (Opus) | `test_fuga_m3.py` en verde | ⬜ |
| JJ-4 | Popularidad + FC clásico + métricas @K | jue 26 | implementador (Sonnet) | verificador-matematico (Opus) | Métricas contra cálculo a mano | ⬜ |
| JJ-5 | Red con contenido, negativos, pérdida, búsqueda, 30 semillas | jue 26–vie 27 | implementador-experto (Opus) 🧠 | verificador-matematico (Opus) | `summary.json` completo | ⬜ |
| JJ-6 | Negocio, 5 usuarios, embeddings 2D | sáb 28 | analista-experimentos (Sonnet) | revisor-spec (Sonnet) | Tablas y figuras mínimas de M3 | ⬜ |
| JJ-7 | Exportación para la app + paridad | sáb 28, noche | implementador (Sonnet) | revisor-spec (Sonnet) | Top-K igual en Python y en los casos de paridad | ⬜ |
| JJ-8 | Fundamentación matemática común | mié 25–dom 29 | redactor-tecnico (Sonnet) | verificador-matematico (Opus) | Cubre todo lo usado por los tres módulos | ⬜ |
| JJ-9 | Bibliografía APA 7 verificada | continuo–dom 29 | investigador-fuentes (Sonnet) | cazador-alucinaciones (Opus) | Toda entrada con DOI o URL que resuelve y citada en el texto | ⬜ |
| JJ-10 | Demo < 2 min, notebook 05, blog M3 | dom 29 | implementador (Sonnet) + redactor-tecnico (Sonnet) | auditor-entregables (Haiku) | Corre en CPU < 2 min | ⬜ |
| JJ-11 | Clon limpio en otra máquina | lun 30 | auditor-reproducibilidad (Haiku) | — | Tabla requisito / resultado / evidencia | ⬜ |

## 5. Puntos calientes de alucinación
- Si el conjunto de Kaggle es real o sintético, y sus columnas (la IA suele describir otro conjunto de viajes).
- NDCG con la ganancia o el descuento mal definidos; Recall@K con el denominador equivocado.
- BPR con el signo invertido; «la BCE con negativos es equivalente a BPR».
- Popularidad calculada con todas las interacciones (fuga).
- Referencias de NCF, BPR, Adam o Grad-CAM con año, autores o DOI equivocados.

## 6. Definición de terminado
Mis tareas ✅; M3 en la app; fundamentación común y bibliografía cerradas; clon limpio aprobado; ≥ 1 hallazgo propio; video
individual grabado.
