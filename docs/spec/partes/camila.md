# Spec de Camila — M1: calendario, análisis descriptivo, modelos de referencia y operación

| | |
|---|---|
| Responsable | **Camila** |
| Rama | `dev/camila` |
| Archivos propios | `src/m1_demanda/{calendario,eda,referencia,operacion}.py`, `configs/m1/operacion.yaml`, `data/processed/m1/calendario.parquet`, `data/fuentes.md` (calendario y normativa), `src/viz/figs_m1_datos.py`, `src/viz/figs_m1_operacion.py`, `notebooks/01_m1_datos.py` (secciones 3–7), `notebooks/03_m1_operacion.py`, blog: descriptivo de M1, operación y ética |
| Lee del núcleo | §0, §1.2, §3, §4.1, §5.1–§5.4, §5.9, §5.12, §6. **Anexo:** M1 completo (énfasis tareas 1, 3, 4, 5; preguntas de negocio 1, 2, 4; limitaciones; fundamentación «modelo de dimensionamiento»); Entregable 1 (sección de ética) |
| Arranque | **No espera datos:** CA-1, CA-2 y CA-3 se hacen desde el martes con fuentes externas y la serie sintética. Daniel hace la descarga y las series (DA-2, DA-3) y te las entrega el mié 25 a las 2 p. m. |

## 1. Lo que pide el enunciado (de lo mío)
- Tarea 1 **caso de uso**: quién usa el pronóstico, para qué decisión, con cuánta anticipación (30 días), con qué información.
- Tarea 3 **análisis descriptivo** con hipótesis explícitas (día de la semana, festivos y puentes, temporadas escolares, Semana
  Santa, fin de año, pospandemia), tendencia y estacionalidad por ruta, y cuáles se confirmaron.
- Tarea 4 **variables exógenas** disponibles al decidir, guardadas en el repo, con fuente primaria.
- Tarea 5 **modelos de referencia**: ingenuo estacional y un modelo estadístico o lineal.
- Negocio 1 (flota, fórmula y sensibilidad ±10 %), 2 (conductores con normativa vigente citada de fuente oficial) y 4
  (temporada alta vs. semana normal; flota propia, arrendada o convenios). Parámetros operativos en un archivo de configuración.
- Limitaciones: abordaje solo en terminal, sentido de regreso como otra serie, demanda censurada por la oferta.
- Fundamentación: formulación del modelo de dimensionamiento de flota y conductores.
- Figuras: series de las rutas; descomposición semanal y anual; flota y conductores por día (30 días); sensibilidad.
- Sección de ética del reporte (consolidas los aportes de todos).

## 2. Consumo / Entrego
| Consumo | De | Cuándo |
|---|---|---|
| Serie sintética (§5.11) | Daniel | mar 24, mediodía |
| Series reales, `rutas.yaml`, `ficha.json` y calidad (§5.1) | Daniel | **mié 25, 2 p. m.** |
| Arnés `evaluar_origen_rodante` y métricas (§5.3) | Andrés | mié 25, noche |
| Pronósticos de test con cuantiles de la mejor red y el mejor modelo de referencia | Andrés | sáb 28, mediodía |
| Ética de cada módulo | todos | dom 29, 8 p. m. |

| Entrego | A | Cuándo |
|---|---|---|
| `calendario.parquet` con fuentes (§5.2) | Andrés | mié 25 |
| `operacion.yaml` + `dimensionar()` (§5.4), primero con valores marcados como supuesto | Andrés, Daniel | jue 26 |
| Modelos de referencia evaluados con el arnés común | Andrés (comparación) | jue 26, noche |
| Hipótesis cerradas (`hipotesis.json`) | blog | sáb 28 |
| Exportación de parámetros operativos para la app | Daniel | sáb 28, noche |

## 3. Especificación

### 3.0 Datos reales (DA-3, aviso de Daniel, 24-nov)
Series de 2021-01-01 a 2023-12-31 (6 series: Bogotá↔Cali, Bogotá↔Sogamoso, Pasto↔Ipiales) y detalle por tipo de despacho y
clase de vehículo en `data/processed/m1/`. Ficha, calidad y diccionario (secciones 1–2) en `results/data/m1/eda/`. Para el
descriptivo, mayo de 2021 se queda con sus marcas (útil para la hipótesis de recuperación); **los modelos de referencia
entrenan desde el 2021-06-01** (`datos.inicio_entrenamiento`). Para la flota usa los **despachos de ORIGEN** del detalle (los de
tránsito cuentan el mismo vehículo en cada terminal) y la composición por clase de vehículo. Hallazgos a analizar: el tránsito
pesa tanto como el origen; salto del tránsito en Bogotá→Sogamoso desde nov-2022; MICROBUS desaparece en Bogotá→Cali en 2023;
asimetría de clases en Pasto–Ipiales.
**Contrato con la app (DA-5):** tus parámetros operativos se exportan a `app/public/model/m1/operacion.json` con el formato
del núcleo §5.4 (cada parámetro `{valor, unidad, fuente | supuesto: true}`; `globales`, `por_ruta`, `por_clase`,
`composicion_clases`; controles obligatorios `globales.ocupacion_objetivo` y `globales.cuantil`). Diseña `dimensionar()` y
`configs/m1/operacion.yaml` pensando en ese formato; valida con `app/lib/contratos.ts`.

### 3.1 Calendario exógeno (CA-1) [PROPUESTO]
Festivos de Colombia, puentes (festivo trasladado a lunes), Semana Santa, vacaciones escolares, temporada de fin de año. Cada
columna con fuente primaria en `data/fuentes.md` (ley o decreto para festivos; calendario oficial para temporadas escolares)
[VERIFICAR con `investigador-fuentes`]. Si una fuente no existe para todo el periodo, se documenta el supuesto. Todo debe ser
conocible 30 días antes.

### 3.2 Normativa y parámetros operativos (CA-2) [PROPUESTO]
`configs/m1/operacion.yaml` con: capacidad por clase de vehículo, ocupación objetivo, tiempo de ciclo por ruta, horas de
operación, jornada máxima y descansos de conductores, ausentismo, costo de quedarse corto y de sobrar, cuantil usado.
- La jornada de los conductores se cita de la **norma colombiana vigente desde su fuente oficial** `TODO(cita)`; no se acepta la
  cita de una IA sin abrir la fuente.
- Lo que no venga de una norma ni de los datos se marca `supuesto: true` con su justificación.

### 3.3 Modelo de flota y conductores (CA-3) 🧠 [PROPUESTO]
Propuesta de partida para discutir con el `verificador-matematico` (el dueño la ajusta):
- despachos(r, d) = ⌈ D(r, d) / (capacidad · ocupación_objetivo) ⌉
- vueltas(r) = ⌊ horas_operación / tiempo_ciclo(r) ⌋, donde el ciclo incluye ida **y regreso** (así entra el sentido de regreso)
- vehículos(r, d) = ⌈ max(despachos ida, despachos regreso) / vueltas(r) ⌉
- conductores = ⌈ vehículos · horas_operación / jornada_efectiva · 1/(1 − ausentismo) ⌉, con descansos dentro de la jornada efectiva
Cada término justificado en el blog. Sensibilidad: demanda ±10 % y cada parámetro ±x %, para encontrar el más influyente.

### 3.4 Análisis descriptivo de M1 (CA-4)
Plantilla común del núcleo §5.12, secciones 3–7 (Daniel hace 1–2). Descomposición STL o MSTL con estacionalidad semanal y anual de
al menos una ruta. Hipótesis H-M1-1… con figura o tabla que las prueba. Caso de uso (tarea 1) en la introducción del módulo.

### 3.5 Modelos de referencia (CA-5)
Ingenuo estacional (mismo día de la semana anterior) y un modelo estadístico o lineal (SARIMA, ETS o regresión con rezagos y
calendario) [PROPUESTO: elegir uno tras el descriptivo]. Implementan el protocolo `Pronosticador` (núcleo §5.3) y se evalúan
**con el mismo arnés y la misma partición que las redes**; su búsqueda (si la hay) se cuenta en el presupuesto (§6).

### 3.6 Negocio 1, 2 y 4 (CA-6)
Con los pronósticos de Andrés: flota y conductores por ruta y día durante 30 días; sensibilidad; temporada alta de prueba vs.
semana normal (vehículos y conductores adicionales) y recomendación propia/arrendada/convenio con supuestos explícitos.
Limitaciones discutidas con datos cuando sea posible.

## 4. Tareas
| ID | Tarea | Fecha | Agente (modelo) | + Verificador | Aceptación | Estado |
|---|---|---|---|---|---|---|
| CA-1 | Calendario exógeno (§3.1) | mar 24–mié 25 | investigador-fuentes (Sonnet) + implementador (Sonnet) | cazador-alucinaciones (Opus) | Esquema §5.2; cada columna con fuente; prueba de fechas conocidas | ⬜ |
| CA-2 | Normativa y `operacion.yaml` (§3.2) | mar 24–mié 25 | investigador-fuentes (Sonnet) | cazador-alucinaciones (Opus) | Cada valor normativo con cita primaria; supuestos marcados | ⬜ |
| CA-3 | `dimensionar()` y conductores (§3.3) | mié 25–jue 26 | implementador-experto (Opus) 🧠 | verificador-matematico (Opus) | Pruebas con casos hechos a mano; usa ida y regreso | ⬜ |
| CA-4 | Análisis descriptivo M1 secciones 3–7 (§3.4) | mié 25–jue 26 | analista-experimentos (Sonnet) | revisor-spec (Sonnet) | `hipotesis.json` válido; figuras de series y descomposición | ⬜ |
| CA-5 | Modelos de referencia (§3.5) | jue 26 | implementador (Sonnet) | auditor-fugas (Opus) | Evaluados con el arnés común; `summary.json` con presupuesto y parámetros | ⬜ |
| CA-6 | Negocio 1, 2 y 4 + limitaciones (§3.6) | sáb 28 | analista-experimentos (Sonnet) | verificador-matematico (Opus) | Tablas y figuras de flota, conductores, sensibilidad y temporada alta | ⬜ |
| CA-7 | Figuras de M1 (datos y operación) | sáb 28 | implementador (Sonnet) | auditor-entregables (Haiku) | Todas las figuras mínimas que me tocan, regenerables con `run.py figures` | ⬜ |
| CA-8 | Exportación de parámetros y casos de paridad para la app | sáb 28 | implementador (Sonnet) | revisor-spec (Sonnet) | Casos de paridad de `dimensionar()` en `app/public/model/m1/` | ⬜ |
| CA-9 | Notebooks 01 (secc. 3–7) y 03 | dom 29 | implementador (Sonnet) | tutor-sustentacion (Sonnet) | Corren en < 2 min; primera celda de parámetros | ⬜ |
| CA-10 | Blog: descriptivo M1, operación, ética consolidada | dom 29, 8 p. m. | redactor-tecnico (Sonnet) | auditor-entregables (Haiku) | Figuras numeradas y citadas; ética con privacidad, sesgos y riesgos de los 3 sistemas | ⬜ |

## 5. Puntos calientes de alucinación
- Normativa de jornada de conductores de servicio público (número de horas, descansos, norma vigente vs. derogada).
- Fechas de festivos, regla de traslado a lunes y Semana Santa de años concretos.
- Capacidad de vehículos por clase (bus, buseta, microbús) atribuida a una norma que no la fija.
- Fórmula de flota que olvida el sentido de regreso o mezcla vueltas con despachos.
- Interpretación de MASE o de la descomposición STL.

## 6. Definición de terminado
Mis tareas ✅; hipótesis de M1 cerradas con evidencia; flota y conductores con fórmula verificada; ética consolidada;
≥ 1 hallazgo propio; video individual grabado.
