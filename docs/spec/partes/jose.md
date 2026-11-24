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

### 3.1 Datos y descriptivo (JO-1, JO-2)
Descarga desde Mendeley (DOI 10.17632/mzb4b6dff3.1) [VERIFICAR estructura de carpetas y conteos]; lectura del artículo de Data in
Brief (DOI 10.1016/j.dib.2025.111529) con `investigador-fuentes`. Imágenes redimensionadas y comprimidas en el repo (§5.5).
Plantilla común §5.12 completa; sección 4 con iluminación (brillo medio), ángulo y tipo de vehículo (si la fuente lo
etiqueta [VERIFICAR]; si no, muestra anotada a mano y declarada).

### 3.2 Partición sin fuga (JO-3) 🧠 [PROPUESTO]
Hash perceptual (pHash/dHash) + similitud coseno de características de la red congelada → grafo de casi duplicados →
componentes conexas = `grupo_duplicado`. Partición estratificada **por grupo** (70/15/15). Umbrales justificados con ejemplos
visuales en la frontera. `test_fuga_m2.py`: ningún grupo en dos particiones y ningún par por debajo del umbral cruzado.

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
| JO-1 | Descarga, ficha y lectura del artículo | mar 24 | curador-datos (Sonnet) + investigador-fuentes (Sonnet) | cazador-alucinaciones (Opus) | `ficha.json`; conteos por clase y resolución medidos | ⬜ |
| JO-2 | Descriptivo M2 (plantilla §5.12) | mié 25 | analista-experimentos (Sonnet) | revisor-spec (Sonnet) | `hipotesis.json` con clases difíciles | ⬜ |
| JO-3 | Casi duplicados y partición por grupos (§3.2) | mié 25 | implementador-experto (Opus) 🧠 | auditor-fugas (Opus) | `test_fuga_m2.py` en verde; figura de pares en la frontera | ⬜ |
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
