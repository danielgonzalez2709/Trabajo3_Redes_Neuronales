# Prompt CA-1a — investigador-fuentes (Sonnet) — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/investigador-fuentes.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). Lee también
`docs/spec/SPEC.md` §0, §3, §5.2 y el Anexo («Módulo 1 → Tareas 1, 3 y 4»), y `docs/spec/partes/camila.md` §3.1 y §5.

## Tarea (CA-1, parte de investigación)
Encontrar y citar la **fuente primaria** de cada columna del calendario exógeno de M1 (`data/processed/m1/calendario.parquet`,
núcleo §5.2), para el periodo **2021-01-01 a 2024-12-31** (periodo de los datos 2021–2023 + horizonte de 30 días + margen para
la app). Rutas del módulo: Bogotá D.C. (11001) ↔ Santiago de Cali (76001), Bogotá D.C. (11001) ↔ Sogamoso (15759, Boyacá),
Pasto (52001) ↔ Ipiales (52356) (Nariño).

1. **Festivos de Colombia**: la ley (o leyes) que fijan los días festivos y la regla de traslado al lunes siguiente; qué festivos
   se trasladan y cuáles no; cómo se fijan los festivos que dependen de la Pascua (Semana Santa, Ascensión, Corpus Christi,
   Sagrado Corazón). Texto literal del artículo, desde el sitio oficial (p. ej. Secretaría del Senado o Función Pública). Si
   existe una fuente oficial que publique la lista de festivos de cada año 2021–2024, cítala también; si no, dilo.
2. **Lista de fechas** de festivos 2021, 2022, 2023 y 2024 derivada **de la regla citada** (no de memoria ni de una página de
   calendario comercial). Indica para cada fecha la regla aplicada. Marca las que no puedas respaldar con `TODO(cita)`.
3. **Semana Santa**: fechas del Jueves y Viernes Santo 2021–2024 y la fuente o el cálculo (fecha de Pascua) con que se obtienen.
4. **Vacaciones escolares**: en Colombia cada secretaría de educación certificada fija su calendario académico por resolución
   anual. Busca las resoluciones de calendario académico (calendario A) de 2021, 2022, 2023 y 2024 para las secretarías de las
   entidades de las rutas: Bogotá D.C., Santiago de Cali, Boyacá y/o Sogamoso, Nariño, Pasto e Ipiales. Para cada una: número y
   fecha de la resolución, URL, y los periodos de receso estudiantil (vacaciones) literales. Si no encuentras alguna, dilo; no
   la completes con otra. Propón cómo combinarlas en una sola columna por fecha (p. ej. vacaciones de la ciudad de origen de cada
   ruta, o la de Bogotá como referencia) y qué supuesto habría que declarar.
5. **Fin de año / temporada**: ¿existe una definición oficial de temporada alta de transporte por carretera (p. ej. del
   Ministerio de Transporte o la Superintendencia de Transporte) para fin de año, Semana Santa o mitad de año? Si existe, cítala;
   si no, dilo para que se declare como supuesto.
6. **Conocible 30 días antes**: para cada fuente, indica cuándo se publicó (fecha de expedición de la ley o resolución) y si es
   razonable que se conociera con 30 días de anticipación a las fechas que cubre (núcleo regla 0.9). Señala cualquier caso dudoso
   (p. ej. calendario modificado a mitad de año).

## Entregable
Un informe en `docs/investigacion/CA-1_fuentes_calendario.md` con, por cada dato: dato · fragmento literal · cita APA 7 · URL ·
fecha de consulta (hoy, 2026-11-26) · nivel de confianza; las tablas de fechas 2021–2024 (festivos, Semana Santa, recesos
escolares por secretaría) en un formato fácil de pasar a código (p. ej. tablas markdown con fecha ISO); la lista de supuestos a
declarar; y la lista de `TODO(cita)`. No escribas código ni toques otros archivos (ni `data/fuentes.md`: eso se hace después).

## Reglas
- Nada de memoria: cada dato con URL abierta por ti. Si no lo encuentras, `TODO(cita)`. Un dato inventado es peor que uno
  faltante.
- Si una página secundaria (blog, calendario comercial, respuesta de IA) contradice la fuente primaria, márcalo como
  CANDIDATO A HALLAZGO con el fragmento de ambas.
- No cambies el Spec. Lo que sea [PROPUESTO] o una decisión (p. ej. cómo combinar calendarios escolares) se escala a Camila
  en tu informe.
- Reporta al final: archivos creados, `TODO` abiertos y decisiones que Camila debe tomar.
