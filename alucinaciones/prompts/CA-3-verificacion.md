# Prompt CA-3-verificacion — verificador-matematico (Opus) — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/verificador-matematico.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). Python: `.venv/bin/python`.
**Solo lectura sobre el repositorio: no edites archivos, no hagas `git commit` ni `git push`.** Si necesitas scripts, escríbelos en
`/private/tmp/claude-501/-Users-softwaresolenium-CoursesExercises-Trabajo3-Redes-Neuronales/98577556-2e6f-4e02-a506-be57e6ccb0ee/scratchpad/`.

Contexto: `docs/spec/SPEC.md` §5.1 (pasajeros = origen + tránsito; flota con despachos de ORIGEN), §5.4 y el Anexo («Módulo 1 →
Preguntas de negocio 1 y 2», «Limitaciones» —sentido de regreso, demanda censurada—, «Fundamentación matemática» —modelo de
dimensionamiento de flota y conductores—); `docs/spec/partes/camila.md` §3.3 y §5 (punto caliente: fórmula que olvida el regreso o
mezcla vueltas con despachos). Implementación generada por IA (prompt literal `alucinaciones/prompts/CA-3a.md`):
`src/m1_demanda/operacion.py` (ecuaciones (1)–(5) en su encabezado), `configs/m1/operacion.yaml`, `tests/test_operacion_m1.py`.
Decisiones de Camila (26-nov) aplicadas en la config: `fraccion_demanda_en_origen` = fracción de pasajeros en ORIGEN de train;
`ocupacion_objetivo` = 1.0 porque la capacidad por clase es el p99 observado de pasajeros por despacho; mínimo 1 vuelta aunque el
ciclo supere las horas de operación; segundo conductor desactivado.

## Tarea
1. Deriva independientemente el modelo de dimensionamiento (despachos, vueltas, vehículos con ida y regreso, conductores con
   jornada efectiva, ausentismo, descanso semanal) y compáralo término a término con el código: unidades, redondeos (⌈⌉/⌊⌋ y la
   tolerancia 1e-9), dominio, doble conteo de ida y regreso, flota por corredor.
2. Comprueba numéricamente con casos a mano (y al menos uno con los datos reales del ejemplo de `results/data/m1/operacion/`) que el
   código da lo que dice la derivación.
3. Evalúa las decisiones de Camila: ¿es coherente usar f = fracción en origen (¿qué supuesto implica sobre el tránsito?), ρ = 1 con
   capacidad = p99 observado de promedios diarios (¿sesgo?), y el mínimo de 1 vuelta cuando T_ciclo > H (¿cuánto subestima la flota en
   Bogotá–Cali?). Cuantifica, no opines.
4. La ecuación de conductores: ¿cuenta conductores en servicio por día o la nómina? ¿Es correcto multiplicar vehículos·H cuando
   v·T_ciclo < H? Propón la formulación correcta si hay error.
5. Sensibilidad (negocio 1): ¿qué parámetro debería ser el más influyente según la fórmula (elasticidades)? Compruébalo numéricamente.
Entrega: veredicto APROBADO / APROBADO CON OBSERVACIONES / RECHAZADO; la derivación en LaTeX lista para el blog; cada error con
archivo:línea, contraejemplo numérico y corrección propuesta. Marca como **candidato a hallazgo** (Matemáticas) todo error que la IA
haya cometido en el código o en la propuesta de fórmula de la spec §3.3.
