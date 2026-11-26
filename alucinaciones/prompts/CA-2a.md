# Prompt CA-2a — investigador-fuentes (Sonnet) — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/investigador-fuentes.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). Lee también
`docs/spec/SPEC.md` §0, §3, §5.4 y el Anexo («Módulo 1 → Preguntas de negocio» y «Limitaciones»), y
`docs/spec/partes/camila.md` §3.0, §3.2, §3.3 y §5.

## Tarea (CA-2, parte de investigación)
Encontrar y citar la **fuente primaria** de los parámetros operativos de `configs/m1/operacion.yaml` (núcleo §5.4) que puedan
venir de una norma, y dejar explícito cuáles **no** vienen de ninguna norma (serán supuestos). Contexto: transporte público
terrestre automotor de pasajeros **por carretera** (intermunicipal) en Colombia; rutas Bogotá↔Cali, Bogotá↔Sogamoso,
Pasto↔Ipiales.

1. **Jornada de los conductores** (lo más importante; es un punto caliente de alucinación). Busca la normativa colombiana
   **vigente** a 2026 sobre:
   - jornada máxima de trabajo (Código Sustantivo del Trabajo y sus reformas recientes sobre reducción de la jornada semanal;
     indica el cronograma de reducción si existe y qué valor rige en cada año 2021–2026);
   - tiempos máximos de conducción continua y diaria, pausas y descansos de conductores de servicio público de transporte
     terrestre (decretos o resoluciones del Ministerio de Transporte u otra autoridad); si una norma específica para conductores
     existe, si está vigente, derogada, suspendida o en periodo de transición;
   - descanso entre jornadas y descanso semanal obligatorio.
   Para cada norma: número, fecha, artículo, fragmento literal, URL oficial (Secretaría del Senado, Función Pública – Gestor
   Normativo, Ministerio de Transporte, Diario Oficial) y **estado de vigencia** comprobado (busca derogatorias o
   modificaciones). Si dos normas parecen contradecirse, cita ambas y explica cuál rige.
2. **Capacidad por clase de vehículo** (BUS, BUSETA, MICROBUS, u otras que aparezcan en `data/processed/m1/demanda_detalle.parquet`,
   columna `clase_vehiculo`; puedes leer el archivo con pandas si hay un intérprete disponible, si no lista la duda). ¿Alguna norma
   colombiana fija la capacidad en pasajeros por clase para el servicio intermunicipal (p. ej. una norma de clasificación o de
   homologación de vehículos)? Si la norma solo da rangos o no la fija, dilo con el fragmento literal: el valor será supuesto.
3. **Diccionario del conjunto** `eh75-8ah6` (datos.gov.co): ¿qué dice literalmente sobre `clase_vehiculo`, `despachos` y
   `pasajeros`? (Ya hay notas en `docs/investigacion/DA-2_fuentes_m1.md`; léelas primero y solo complementa.)
4. **Tiempo de ciclo y horas de operación por ruta**: ¿existe una fuente oficial con distancia o tiempo de viaje entre
   Bogotá–Cali, Bogotá–Sogamoso y Pasto–Ipiales (p. ej. Instituto Nacional de Vías, Ministerio de Transporte)? Si la hay, cítala;
   si no, dilo para que se declare como supuesto.
5. **Ausentismo** y **costos** (quedarse corto vs. sobrar): ¿hay una cifra oficial publicada (DANE, Ministerio del Trabajo,
   Supertransporte) aplicable? Si no, dilo: serán supuestos con justificación.

## Entregable
Un informe en `docs/investigacion/CA-2_normativa_operacion.md` con, por cada parámetro: dato · fragmento literal · cita APA 7 ·
URL · fecha de consulta (hoy, 2026-11-26) · vigencia · nivel de confianza; una tabla final «parámetro → valor propuesto →
`fuente` o `supuesto: true`»; y la lista de `TODO(cita)`. No escribas código ni el YAML; no toques otros archivos.

## Reglas
- Nada de memoria: cada dato con URL oficial abierta por ti. Si no lo encuentras, `TODO(cita)`. Un dato inventado es peor que
  uno faltante.
- Si una fuente secundaria o una IA afirma una jornada, una capacidad o una norma distinta a la fuente primaria (o una norma
  derogada como vigente), márcalo como CANDIDATO A HALLAZGO con el fragmento de ambas.
- No cambies el Spec. Lo que sea decisión (p. ej. qué valor usar cuando la norma da un rango) se escala a Camila en el informe.
- Reporta al final: archivos creados, `TODO` abiertos y decisiones que Camila debe tomar.
