# Spec de Andrés — M1: redes neuronales, evaluación y valor del pronóstico

| | |
|---|---|
| Responsable | **Andrés** |
| Rama | `dev/andres` |
| Archivos propios | `src/m1_demanda/{evaluacion,perdidas,redes,hpo,experimento}.py`, `configs/m1/{base,demo,hpo}.yaml`, `results/data/m1/`, `models/m1/`, `src/viz/figs_m1_redes.py`, `notebooks/02_m1_redes.py`, exportación de pronósticos a `app/public/model/m1/`, blog: redes de M1 y fundamentación de M1, cacería (consolidación) |
| Lee del núcleo | §0, §1.2, §3, §4.1, §5.1–§5.4, §5.9, §5.10, §6, §9. **Anexo:** M1 tareas 1, 6, 7, 8; negocio 3; fundamentación y figuras de M1; Regla de comparación justa; Discusión; Cacería |
| Arranque | Desde el martes con la serie sintética (§5.11); al llegar las reales (mié 25, 2 p. m.) solo cambia `datos.ruta` |

## 1. Lo que pide el enunciado (de lo mío)
- Tarea 6: **MLP con ventanas de rezagos** y **al menos una arquitectura secuencial** (LSTM, GRU o CNN 1D); optimizar ventana,
  capas, unidades, regularización, optimizador y tasa de aprendizaje; justificar el método de búsqueda y **global vs. por ruta**.
- Tarea 7: pérdida justificada por la naturaleza de **conteo**; además del punto, **al menos un cuantil alto (P90)**.
- Tarea 8: particiones temporales, **origen rodante** a 30 días; MAE, RMSE, MASE por ruta y agregados; error por horizonte
  (1–7, 8–14, 15–30); cobertura y pérdida cuantílica; pronóstico vs. real con **al menos una temporada alta en prueba**.
- Negocio 3: punto vs. cuantil alto; pasajeros sin atender y vehículos-día sobrantes con la mejor red y el mejor modelo de
  referencia; cómo cambia la decisión según el costo relativo; ¿justifica la red su complejidad?
- Fundamentación: ecuaciones de la arquitectura secuencial; derivación de la pérdida de conteo y de la cuantílica desde un
  modelo probabilístico; definición de MASE, cobertura y pérdida cuantílica.
- Figuras: pronóstico vs. real con banda del cuantil; error por horizonte (días 1 a 30) por modelo; figuras comunes de cada red
  final (arquitectura, curvas con parada temprana, búsqueda, cajas de 30 semillas).
- Consolidar la Cacería de la alucinación (≥ 5 hallazgos, ≥ 3 categorías, ≥ 1 por módulo).

## 2. Consumo / Entrego
| Consumo | De | Cuándo |
|---|---|---|
| Serie sintética | Daniel | mar 24, mediodía |
| Series reales (§5.1) | Daniel | **mié 25, 2 p. m.** |
| Calendario (§5.2) | Camila | mié 25 |
| `dimensionar()` (§5.4) | Camila | jue 26 |
| Hallazgos de la cacería de todos | todos | dom 29, 8 p. m. |

| Entrego | A | Cuándo |
|---|---|---|
| Arnés `evaluar_origen_rodante` + métricas + partición temporal (§5.3) | Camila | **mié 25, noche** |
| Pronósticos de test con cuantiles (mejor red y mejor referencia) | Camila, Daniel | **sáb 28, mediodía** |
| Pronósticos de los próximos 30 días por ruta para la app | Daniel | sáb 28, noche |
| Activación, optimizador y regularización usados | Juan José | vie 27 |

## 3. Especificación

### 3.1 Partición y origen rodante (AN-1) 🧠 [PROPUESTO]
Train / val / test por fecha; el test incluye al menos una temporada alta (p. ej. fin de año o Semana Santa) [VERIFICAR con el
periodo real]. Orígenes rodantes cada 7 días dentro de val (búsqueda) y de test (reporte), horizonte 30. Toda variable usada en
el origen t se conoce en t (rezagos ≤ t; calendario sí, porque es conocible). `test_fuga_m1.py` lo prueba.

### 3.2 Pérdidas (AN-2) 🧠 [PROPUESTO]
- Punto: NLL de **Poisson** (salida con softplus o exp = tasa λ); alternativa binomial negativa si hay sobredispersión (decidir
  con el descriptivo: varianza vs. media por ruta).
- Cuantiles: **pérdida pinball** para q ∈ {0.5, 0.75, 0.9, 0.95} (cabezas múltiples), con su derivación desde la
  verosimilitud de la distribución asimétrica de Laplace; control de cuantiles cruzados.
- Ambas derivaciones verificadas por el `verificador-matematico` (gradiente vs. diferencias finitas).

### 3.3 Redes (AN-3) [PROPUESTO]
- **Modelo global** (una red para todas las rutas, con embedding de ruta) como opción principal; justificar contra por ruta
  con datos (pocas series, ~cientos de días cada una).
- MLP sobre ventana de rezagos + calendario del día objetivo; LSTM o GRU sobre la ventana; salida directa multihorizonte (30).
- Normalización por ruta ajustada solo con train.

### 3.4 Búsqueda y semillas (AN-4, AN-5)
Optuna TPE, semilla fija; presupuesto declarado (núcleo §6): MLP 25 y secuencial 25 ensayos [PROPUESTO]. Configuración final con
30 semillas; `summary.json`, `semillas/`, `curvas/`, `arquitectura/` según §5.9. Demo en `configs/m1/demo.yaml` < 2 min en CPU.

### 3.5 Valor del pronóstico (AN-7)
Para cada opción (punto, P90) y cada modelo (mejor red, mejor referencia): pasajeros sin atender = Σ max(0, y − capacidad
ofrecida) y vehículos-día sobrantes, usando `dimensionar()` de Camila. Curva de costo total vs. razón costo_corto/costo_sobra.

## 4. Tareas
| ID | Tarea | Fecha | Agente (modelo) | + Verificador | Aceptación | Estado |
|---|---|---|---|---|---|---|
| AN-1 | Partición, origen rodante y métricas (§3.1) | mar 24–mié 25 | implementador-experto (Opus) 🧠 | auditor-fugas (Opus) | Métricas contra cálculo a mano; `test_fuga_m1.py` en verde | ⬜ |
| AN-2 | Pérdidas Poisson y pinball (§3.2) | mié 25 | implementador-experto (Opus) 🧠 | verificador-matematico (Opus) | Gradientes vs. diferencias finitas; cuantiles sin cruce | ⬜ |
| AN-3 | MLP y red secuencial (§3.3) | mié 25–jue 26 | implementador (Sonnet) | revisor-spec (Sonnet) | Entrenan sobre sintéticos; parámetros desde config | ⬜ |
| AN-4 | Búsqueda Optuna | jue 26 | analista-experimentos (Sonnet) | revisor-spec (Sonnet) | `hpo_ensayos.json` con presupuesto y tiempo | ⬜ |
| AN-5 | 30 semillas + pronósticos de test | vie 27 (noche)–sáb 28, 12 m. | analista-experimentos (Sonnet) | auditor-fugas (Opus) | 30 archivos por red; `pred_test_*.parquet` según §5.3 | ⬜ |
| AN-6 | Figuras de redes de M1 | sáb 28 | implementador (Sonnet) | auditor-entregables (Haiku) | Figuras mínimas de M1 y comunes por red | ⬜ |
| AN-7 | Negocio 3: valor del pronóstico (§3.5) | sáb 28 | analista-experimentos (Sonnet) | verificador-matematico (Opus) | Tabla punto vs. P90 × red vs. referencia; curva de costo | ⬜ |
| AN-8 | Exportación a la app + demo + notebook 02 | sáb 28–dom 29 | implementador (Sonnet) | auditor-reproducibilidad (Haiku) | Demo < 2 min; JSON según contrato | ⬜ |
| AN-9 | Blog: redes de M1 y fundamentación de M1 | dom 29, 8 p. m. | redactor-tecnico (Sonnet) | verificador-matematico (Opus) | Ecuaciones LSTM/GRU, derivaciones, definiciones | ⬜ |
| AN-10 | Cacería consolidada | dom 29–lun 30 | cazador-alucinaciones (Opus) | — | ≥ 5 hallazgos, ≥ 3 categorías, ≥ 1 por módulo, plantilla de 6 puntos | ⬜ |

## 5. Puntos calientes de alucinación
- MASE con la escala equivocada (escala en test en vez de train, o ingenuo no estacional).
- Pérdida pinball con el signo o el peso invertido; «la pinball es la NLL de una normal».
- Fuga por normalizar con toda la serie o por usar rezagos dentro del horizonte (h > 1 con rezagos que aún no se conocen).
- Ecuaciones de LSTM/GRU con compuertas intercambiadas.
- «La LSTM siempre supera a SARIMA» u otras afirmaciones sin evidencia.

## 6. Definición de terminado
Mis tareas ✅; comparación justa completa en `summary.json`; negocio 3 respondido; cacería consolidada; ≥ 1 hallazgo propio;
video individual grabado.
