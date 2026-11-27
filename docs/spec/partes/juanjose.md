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

### 3.0 Contrato con la app (aviso de Daniel, 24-nov, DA-5)
La app recomienda a un **perfil nuevo** con un formato de **dos torres lineal/MLP** (núcleo §5.8): selección de preferencias
→ one-hot por opción → capas de la `torre_usuario` (`W` con forma salida × entrada, como `torch.nn.Linear.weight`) → puntaje
⟨u, embedding del destino⟩ + sesgo. Diseña la red de JJ-5 de modo que su torre de usuario se pueda exportar así (o ajusta una
torre lineal sobre las preferencias para el perfil nuevo). Valida tus JSON con `app/lib/contratos.ts`; ejemplo completo en
`app/public/model/m3/` y `scripts/generar_juguetes_app.py`. La «lista de preferencias para elegir» del enunciado sale de
`preferencias` en `perfil_nuevo.json`: defínela con las variables reales del conjunto de Kaggle.

### 3.1 Datos, descriptivo y partición (JJ-1 a JJ-3)
Descarga manual desde Kaggle el 2026-11-25 (`archive.zip` + 4 CSV en `data/raw/m3/`; no se versiona la clave). Inventario,
fuente y verificación: `docs/investigacion/JJ-1_fuentes_m3.md` (fase A) y `JJ-1_verificacion_A3.md`. `test_fuga_m3.py`:
ninguna interacción de test en train ni en el cálculo de popularidad.

Decisiones [DECIDIDO, Juan José, 25-nov], con la justificación medida en la fase A (cifras de `JJ-1_fuentes_m3.md`):
- **D1. Interacción = unión de Reviews y UserHistory, como retroalimentación implícita (sí/no).** Los dos archivos no comparten
  ningún par (usuario, destino); la intersección está vacía. La unión da 1 998 interacciones de 858 usuarios (mediana 2 por
  usuario, frente a 1 en cada archivo por separado) y deja 606 usuarios con ≥ 2 interacciones (269 con solo Reviews, 258 con
  solo UserHistory). `Rating` y `ExperienceRating` (las dos de 1 a 5, compatibles con la uniforme y sin escala documentada) se
  conservan como atributo `calificacion` con su `origen`; el objetivo de los modelos es la interacción, no la calificación.
- **D2. Destino = los 1 000 `DestinationID`** (catálogo de la fuente). `Name`, `State`, `Type`, `BestTimeToVisit` y `Popularity`
  son variables de contenido del destino. Problema de calidad documentado: los 1 000 ids son 5 lugares (nombre, estado, tipo y
  temporada idénticos) repetidos 200 veces cada uno, en ciclo `DestinationID mod 5`. Se agrega `lugar` (los 5 lugares) para un
  análisis complementario de «acierto por lugar» en la evaluación.
- **D3. Partición por usuario, no por tiempo (la implementa JJ-3).** `VisitDate` solo existe en UserHistory, tiene 3 valores
  que dependen de `HistoryID mod 3` y 666 de 999 son posteriores a la creación de la versión 1 en Kaggle (2024-01-23): no es una fecha
  real y queda solo descriptiva. Prueba = 1 interacción al azar de cada usuario con ≥ 2; validación = 1 más de cada usuario con
  ≥ 3; el resto, entrenamiento; los usuarios con 1 interacción quedan solo en entrenamiento; semilla fija. Con la unión hay 606
  usuarios en prueba y 326 en validación, y el grupo «pocas interacciones» existe en prueba.
- **D4. Real o sintético.** Se cita literal la fuente («generated for educational and research purposes», «enriched with
  gender diversity»), se aclara que no usa la palabra «synthetic» y se listan las señales medidas (5 lugares en 1 000 ids, 3
  textos de reseña sin relación con el destino, 3 valores de `VisitDate` de los que 2 —666 de 999 filas— son posteriores a
  la creación de la versión 1 en Kaggle (2024-01-23), 20 nombres para 999 usuarios, preferencias periódicas en el id). Conclusión: datos generados; las conclusiones valen para el método, no para el
  comportamiento real de turistas.
- **D5. Licencia.** Se cita la MIT del campo formal de Kaggle (`licenses`) y se documenta la contradicción con la descripción
  («CC0: Public Domain» y «free to use for non-commercial purposes») para la sección de ética.
- **D6. Privacidad.** `Name` y `Email` de los usuarios no pasan a `data/processed/` ni a `results/`. `ReviewText` tampoco pasa a
  lo procesado (3 textos sin relación con el destino); se describe en el diccionario.
- **D7.** El candidato débil de A1 («las variables son independientes») no se registra en la cacería.

Decisiones de la partición (JJ-3) [DECIDIDO, Juan José, 26-nov], que concretan D3:
- **D8. Dónde vive la partición.** La calcula `run.py m3-datos` (bloque `particion` de `configs/m3/datos.yaml`, con su
  semilla) y queda en la columna `split` ∈ {`train`, `validacion`, `prueba`} de `data/processed/m3/interacciones.parquet`
  (núcleo §5.7). Es **una sola partición para todos los modelos de M3** (referencias y red); su SHA-256 y el de una huella de
  la tabla (`usuario_id, destino_id, split` ordenada) quedan en `results/data/m3/particion/resumen.json` y van en la
  `evidencia` de cada JSON de resultados (núcleo §5.9, §6).
- **D9. Uso de los conjuntos.** La búsqueda de hiperparámetros y la parada temprana usan validación; los modelos finales
  (referencias y red, y las 30 semillas) se entrenan **solo con train** y se evalúan una vez en prueba. Toda estadística
  derivada de las interacciones (popularidad, conteos por destino, negativos por popularidad, umbrales de actividad usados
  como variable) se calcula **solo con train**.
- **D10. Candidatos al evaluar.** Para cada usuario de prueba se rankean todos los destinos del catálogo **excepto** su
  historial conocido (los de train y validación); en validación, excepto los de train. Un destino ya visto nunca cuenta como
  acierto. Los usuarios sin interacciones (141 de 999) no se evalúan en prueba; sirven después para el escenario de usuario
  nuevo (JJ-6).
- Nota de JJ-3: `id_origen` no es único entre orígenes (ReviewID e HistoryID se solapan); la clave de una interacción es
  `(origen, id_origen)`.
- [PROPUESTO por el orquestador de JJ-3, 26-nov; pendiente de Juan José] `resumen.json` trae además `diagnosticos` medidos
  para leer la evaluación (no son entrada de ningún modelo): destinos de prueba y validación sin interacciones en train
  («fríos») y usuarios con otro id del mismo lugar en su historial conocido, con su `esperado_por_azar` (204 frente a 198,0
  en prueba: coincidencia esperable con 5 lugares, no un atajo). `tests/test_fuga_m3.py` trae guardas para JJ-4/JJ-5
  (`AJUSTES_SOLO_TRAIN`, prohibición de leer estadísticas calculadas con todas las interacciones), propuestas por el
  auditor-fugas.

Salidas de JJ-1 (`run.py m3-datos`) [DECIDIDO, Juan José, 25-nov]:
- `interacciones.parquet` trae `usuario_id, destino_id, origen, id_origen, calificacion, fecha_visita`. Frente al núcleo §5.7
  (`usuario_id, destino_id, calificacion, [fecha], split`): `origen` lo pide D1; `id_origen` (ReviewID o HistoryID) da
  trazabilidad a la fila cruda; la fecha se llama `fecha_visita` porque no es una fecha real (D3); `split` lo agrega JJ-3.
  Pendiente: Daniel decide si actualiza §5.7 del núcleo (avisado por Juan José).
- `ficha.json` trae, además de las 10 claves de §5.12, dos claves de primer nivel que no son conteos: `real_o_sintetico`
  (D4) y `licencia` (D5). `validar_ficha` las admite.

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
| JJ-1 | Descarga y ficha; real o sintético | mar 24 | curador-datos (Sonnet) + investigador-fuentes (Sonnet) | cazador-alucinaciones (Opus) | `ficha.json` con densidad y escala medidas | ✅ 25-nov |
| JJ-2 | Descriptivo M3 (plantilla §5.12) + caso de uso | mié 25 | analista-experimentos (Sonnet) | revisor-spec (Sonnet) | `hipotesis.json`; figura de cola larga | ✅ 26-nov |
| JJ-3 | Partición sin fuga | mié 25 | implementador-experto (Opus) 🧠 | auditor-fugas (Opus) | `test_fuga_m3.py` en verde | ✅ 26-nov |
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
