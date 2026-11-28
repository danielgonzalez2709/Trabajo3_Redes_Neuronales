# Spec de José — M2: conducción distractiva

| | |
|---|---|
| Responsable | **José** |
| Rama | `dev/jose` |
| Archivos propios | `src/m2_conduccion/`, `configs/m2/`, `data/processed/m2/`, `data/fuentes.md` (M2), `results/data/m2/`, `models/m2/`, `src/viz/figs_m2.py`, `notebooks/04_m2.py`, `app/public/model/m2/`, blog: M2 completo |
| Lee del núcleo | §0, §1.2, §3, §4.1, §5.5, §5.6, §5.9, §5.10, §5.12, §6. **Anexo:** M2 completo; Regla de comparación justa; Discusión; figuras comunes |
| Dependencias | **Ninguna para avanzar.** Entregas a Daniel (app), a Juan José (lista de activaciones/optimizador/regularización) y al blog |

## 1. Lo que pide el enunciado
- Datos: imágenes por clase y resolución; cómo se construyó el conjunto según el artículo, **incluido el aumento previo**.
- Tareas 1–7: caso de uso (quién recibe la alerta, cuándo, qué acción, restricciones de cámara, cómputo y latencia);
  descriptivo (balance, iluminación, ángulo, tipo de vehículo, duplicados y casi duplicados, hipótesis de clases difíciles);
  **partición sin fuga demostrada**; logística multinomial sobre características congeladas; CNN propia y ajuste fino con
  búsqueda justificada; exactitud, F1 macro, precisión y sensibilidad por clase, matriz de confusión, 10 aciertos y 10 errores
  explicados; Grad-CAM (u otro método citado).
- Negocio: política de alertas (agrupación, umbral, falsas alarmas y no detectadas por 1.000 imágenes, costo relativo),
  generalización a una flota colombiana y cómo validarla, medidas preventivas.
- Fundamentación: convolución, pooling, normalización por lotes; softmax y entropía cruzada desde la verosimilitud
  multinomial; ajuste fino y aumentos usados; métricas y método de interpretabilidad.
- Figuras mínimas del módulo y comunes por red final.

## 2. Consumo / Entrego
| Entrego | A | Cuándo |
|---|---|---|
| Ficha y descriptivo (plantilla §5.12) | blog | mié 25 |
| Partición sin fuga + `test_fuga_m2.py` | todos (es evidencia) | mié 25, noche |
| Activación, optimizador y regularización usados | Juan José | vie 27 |
| `modelo.onnx` + `meta.json` con casos de paridad (§5.6) | Daniel | **sáb 28, noche** |
| Sección del blog de M2 | Daniel | dom 29, 8 p. m. |

## 3. Especificación

### 3.0 Contrato con la app (aviso de Daniel, 24-nov, DA-5)
La app ya corre un ONNX de juguete con la forma de tu modelo (`app/public/model/m2/`). Para exportar el real (JO-9) sigue el
núcleo §5.6 y valida tu `meta.json` con `app/lib/contratos.ts`. **Importante para entrenar:** el preprocesado de la app es
fijo — redimensionar **estirando** con interpolación **bilineal** (como PIL `Image.BILINEAR`), RGB, escala 0–1 y luego
media/desviación. Entrena y evalúa con ese mismo preprocesado. Salidas del ONNX: `logits` (5) y `mapas` (última
convolución); cabeza GAP + lineal (sus pesos van en `pesos_cabeza` y `sesgo_cabeza`). Referencia: `scripts/generar_juguetes_app.py`.

**CAM ≡ Grad-CAM en la app (DA-7, verificado el 26-nov con el juguete).** Para que la equivalencia valga con tu modelo real:
(1) la salida `mapas` del ONNX es exactamente el tensor al que se aplica el GAP (si hay BN o ReLU al final, exporta su
salida); (2) la cabeza es solo GAP (media) + una única `nn.Linear` sobre los logits previos al softmax; (3) `pesos_cabeza` =
`cabeza.weight` (clases × canales, filas en el orden de `clases`) y `sesgo_cabeza` = `cabeza.bias`; (4) en cada caso de
paridad `logits ≈ W·mean(mapas) + b` (atol 1e-4); (5) forma NCHW `[1, C, H, W]` con C = columnas de W, exportado en `eval()`;
(6) repite con tu modelo la prueba `test_m2_cam_coincide_con_grad_cam` de `tests/test_juguetes_app.py` (gradiente constante =
w/(H·W) y H·W·Grad-CAM = ReLU(CAM)).

### 3.1 Datos y descriptivo (JO-1, JO-2)
Descarga desde Mendeley (DOI 10.17632/mzb4b6dff3.1) [VERIFICAR estructura de carpetas y conteos]; lectura del artículo de Data in
Brief (DOI 10.1016/j.dib.2025.111529) con `investigador-fuentes`. Imágenes redimensionadas y comprimidas en el repo (§5.5).
Plantilla común §5.12 completa; sección 4 con iluminación (brillo medio), ángulo y tipo de vehículo (si la fuente lo
etiqueta [VERIFICAR]; si no, muestra anotada a mano y declarada).

**[DECIDIDO, José, 27-nov] (JO-1).** Fuente medida: un .zip de Mendeley (SHA-256 `427fec9d…af41c8c`, 2 556 850 881 B) con 7 286
imágenes en 5 carpetas (`other_activities`, `safe_driving`, `talking_phone`, `texting_phone`, `turning`); 10 ilegibles; la fuente
**no** etiqueta tipo de vehículo, iluminación ni ángulo (`docs/investigacion/JO-1_fuentes_m2.md`, F-42). Decisiones:
- D1. Se versionan las **7 276 imágenes legibles** procesadas en `data/processed/m2/imagenes/` (~112 MB): el Anexo exige los datos
  procesados en el repositorio. Los 10 ilegibles se excluyen y se registran en `results/data/m2/eda/calidad.csv`.
- D2. **224×224**, estirado, bilineal (PIL), RGB, **JPEG calidad 85**. La recompresión JPEG no existe en la app: diferencia
  medida y declarada en `ficha.json` (`conteos.diferencias_con_app`) y en el blog (limitación).
- D3. Se aplica la orientación EXIF antes de redimensionar (113 imágenes).
- D4. `ancho`/`alto` de `indice.csv` = dimensiones **originales** tras EXIF; sin `tipo_vehiculo` (la fuente no lo trae).
  Trazabilidad en `data/processed/m2/origen.csv`; huellas en `results/data/m2/eda/procesado.json`.
- D5. Ids `m2_NNNNN` por posición en el .zip (con huecos para los ilegibles); `n_variables` = 2 (imagen y clase).
- Pendiente de ética (JO-11): el `DATA USE AGREEMENT` del depósito en Zenodo prohíbe redistribuir y menciona rostros visibles,
  frente a CC BY 4.0 en Mendeley (C-6 de `JO-1_fuentes_m2.md`).

### 3.2 Partición sin fuga (JO-3) 🧠
Hash perceptual (pHash/dHash) + similitud coseno de características de la red congelada → grafo de casi duplicados →
componentes conexas = `grupo_duplicado`. Partición estratificada **por grupo** (70/15/15). Umbrales justificados con ejemplos
visuales en la frontera. `test_fuga_m2.py`: ningún grupo en dos particiones y ningún par por debajo del umbral cruzado.

**[DECIDIDO, José, 27-nov] (JO-3).** Motivo: el artículo declara imágenes aumentadas guardadas junto a las originales sin decir
cuáles (F-36, C-4 de `JO-1_fuentes_m2.md`) y 178 conductores fotografiados durante 30 días (ráfagas casi iguales).
- D1. pHash de 64 bits (`imagehash`) de cada imagen **y de su espejo horizontal** (el artículo menciona volteos); distancia de
  Hamming = mínimo entre la imagen y el espejo de la otra. Se calcula sobre las 224×224 versionadas (reproducible sin el .zip).
- D2. Características de **ResNet-18 ImageNet** (torchvision) congelada, vector GAP de 512, similitud coseno. Los pesos se bajan
  una sola vez con un script que verifica su huella; los experimentos corren sin internet. Las características quedan en caché
  (no versionada) y JO-4 las reutiliza.
- D3. Arista si Hamming ≤ umbral **o** coseno ≥ umbral; grupos = componentes conexas. Umbrales en la config, propuestos con la
  distribución y una figura de pares en la frontera, aprobados por José. Si un grupo supera el **15 %** de las imágenes se
  detiene y se decide con José.
- D4. 70/15/15 por grupo, estratificada por clase, semilla en la config, huella SHA-256 en `results/data/m2/particion/resumen.json`.
  Casi duplicados de clases distintas no se corrigen: se registran como hallazgo de datos (misma escena, otra acción: el mismo
  conductor segundos después; revisado a ojo en la figura de la frontera, no son etiquetas mal puestas).
- D5. Limitación declarada: no se elimina la fuga por identidad del conductor (la fuente no trae id de conductor); va al blog.

**[DECIDIDO, José, 28-nov] (JO-3, tras la figura de la frontera).**
- D6. Umbrales `umbral_hamming` = 2 y `umbral_coseno` = 0,95: los más permisivos (los que agrupan más) que no superan la guarda del 15 % (con 4 / 0,94
  el grupo mayor llega a 35,8 % / 28,6 % por encadenamiento). Los pares justo fuera siguen siendo el mismo conductor (D5).
- D7. Estratificación por el **conteo de clases de cada grupo** (no por su clase mayoritaria), para que cada clase quede en 70/15/15.
- D8. `particion.semilla` = 2026 (la misma de M3).
- D9. (Tras auditor-fugas.) Arista adicional por **marca de tiempo de la cámara** (nombre original `IMG_AAAAMMDD_HHMMSSmmm` en
  `origen.csv`, 404 fotos): dos fotos a ≤ 10 s se unen. Es metadato, no la clase. Se mantiene la guarda del 15 %. Lo que queda se
  declara con cifras en el blog: ráfagas sin marca de tiempo por debajo de los umbrales y el mismo conductor en otra pose (D5);
  la protección contra rotaciones y recortes del rango del artículo es empírica (búsqueda con variantes), no propia del criterio.
  Ampliación (José, 28-nov): la misma regla de ≤ 10 s se aplica a los otros dos formatos de nombre con hora que registra JO-1
  (`PATRONES_NOMBRE` de `datos.py`: 183 PNG `AAAA-MM-DDhh-mm-ss` y 11 `photo_AAAA-MM-DD_hh-mm-ss`, resolución de segundos).

### 3.3 Modelos (JO-4, JO-5, JO-6) [PROPUESTO]
- Referencia: características de una red preentrenada **congelada** (en caché) + regresión logística multinomial (C con búsqueda
  pequeña, contada en el presupuesto).
- CNN propia: bloques conv–BN–ReLU–pool, cabeza **GAP + lineal**.
- Ajuste fino: red base ligera (coherente con el cómputo del vehículo; p. ej. MobileNetV3 o ResNet-18) con cabeza **GAP +
  lineal** para que CAM ≡ Grad-CAM en la app (núcleo §3).
- Búsqueda Optuna: CNN propia 15 y ajuste fino 10 ensayos [PROPUESTO]; 30 semillas finales en GPU; resolución y épocas fijadas
  para que quepa en el tiempo (se reporta).

### 3.4 Evaluación, interpretabilidad y alertas (JO-7, JO-8)
Métricas sobre test; galería de 10 aciertos y 10 errores; Grad-CAM (Selvaraju et al., cita verificada) sobre aciertos y errores;
agrupación sin alerta / con alerta justificada; curva de falsas alarmas y no detectadas por 1.000 imágenes vs. umbral; umbral
elegido según costo relativo (en `configs/m2/alertas.yaml`).

## 4. Tareas
| ID | Tarea | Fecha | Agente (modelo) | + Verificador | Aceptación | Estado |
|---|---|---|---|---|---|---|
| JO-1 | Descarga, ficha y lectura del artículo | mar 24 | curador-datos (Sonnet) + investigador-fuentes (Sonnet) | cazador-alucinaciones (Opus) | `ficha.json`; conteos por clase y resolución medidos | ✅ 27-nov |
| JO-2 | Descriptivo M2 (plantilla §5.12) | mié 25 | analista-experimentos (Sonnet) | revisor-spec (Sonnet) | `hipotesis.json` con clases difíciles | ⬜ |
| JO-3 | Casi duplicados y partición por grupos (§3.2) | mié 25 | implementador-experto (Opus) 🧠 | auditor-fugas (Opus) | `test_fuga_m2.py` en verde; figura de pares en la frontera | ✅ 28-nov |
| JO-4 | Características congeladas + logística | jue 26 | implementador (Sonnet) | revisor-spec (Sonnet) | `summary.json` con presupuesto y parámetros | ⬜ |
| JO-5 | CNN propia + ajuste fino + búsqueda | jue 26–vie 27 | implementador (Sonnet) | revisor-calidad (Haiku) | Parámetros desde config; `hpo_ensayos.json` | ⬜ |
| JO-6 | 30 semillas (GPU) | vie 27–sáb 28 | analista-experimentos (Sonnet) | revisor-spec (Sonnet) | 30 archivos por red; dispositivo y tiempo registrados | ⬜ |
| JO-7 | Evaluación + Grad-CAM + galerías | sáb 28 | implementador-experto (Opus) 🧠 | verificador-matematico (Opus) | Grad-CAM verificado; CAM ≡ Grad-CAM con la cabeza usada | ⬜ |
| JO-8 | Política de alertas, generalización, medidas preventivas | sáb 28 | analista-experimentos (Sonnet) | revisor-spec (Sonnet) | Tabla por 1.000 imágenes y umbral justificado | ⬜ |
| JO-9 | Exportación ONNX + `meta.json` + paridad | sáb 28, noche | implementador (Sonnet) | revisor-spec (Sonnet) | Paridad ONNX vs. PyTorch (probabilidades y mapa) | ⬜ |
| JO-10 | Demo < 2 min, notebook 04, figuras | dom 29 | implementador (Sonnet) | auditor-reproducibilidad (Haiku) | Corre en CPU < 2 min | ⬜ |
| JO-11 | Blog M2 + fundamentación de M2 | dom 29, 8 p. m. | redactor-tecnico (Sonnet) | verificador-matematico (Opus) | Figuras mínimas numeradas y citadas | ⬜ |

## 5. Puntos calientes de alucinación
- Número de imágenes, clases y aumento previo del conjunto (leer el artículo, no la IA).
- Partición aleatoria por imagen «sin fuga» cuando hay aumentos de la misma foto.
- Grad-CAM con el gradiente respecto a la entrada (eso es un mapa de saliencia) o sin la ReLU final.
- Entropía cruzada aplicada sobre softmax dos veces (`CrossEntropyLoss` ya incluye log-softmax).
- Normalización de ImageNet olvidada al exportar a ONNX.

## 6. Definición de terminado
Mis tareas ✅; fuga demostrada ausente; ONNX funcionando en la app; ≥ 1 hallazgo propio; video individual grabado.
