## Uso de IA

<!-- borrador DA-9a (redactor-tecnico, Sonnet): solo la parte metodológica y ejemplos reales de revisión de DA-1 y DA-3. Falta la lista final de prompts principales y la discusión final de impacto (DA-12). Pendiente de revisión de Daniel. -->

El enunciado espera que se use inteligencia artificial y advierte que esta se equivoca, a veces con total seguridad. Este equipo
trabajó con Claude Code y organizó el uso de la IA como un proceso con reglas, no como una conversación suelta: un Spec que manda,
subagentes con tareas pequeñas y revisores que no son quien escribió. Esta sección explica el proceso, dónde queda la evidencia
y qué detectaron los revisores en las dos primeras tareas de datos de M1 (DA-1 y DA-3).

Este borrador fue escrito por el agente `redactor-tecnico` (Sonnet) a partir de un prompt guardado en
`alucinaciones/prompts/DA-9a.md`, y los juicios sobre impacto quedan marcados para que Daniel los valide.

### Spec Driven y Subagent Driven Development

**Spec Driven.** Primero se escribe lo que hay que construir, y solo después se construye. La fuente de verdad es
`docs/spec/SPEC.md`: un núcleo con las reglas, los contratos entre módulos y la plantilla común de análisis descriptivo, y en su
Anexo el enunciado literal del trabajo. Cada integrante tiene además una spec personal en `docs/spec/partes/`, y el tablero
`docs/spec/PLAN.md` lleva una línea por tarea. Las reglas que más importan para el uso de IA son estas (núcleo §0):

- El Spec está por encima del código: si un subagente lo contradice, gana el Spec o se cambia el Spec de forma explícita
  (por pull request, subiendo la versión y con una línea en el historial).
- Los subagentes no cambian el Spec ni resuelven lo que está marcado como pendiente o propuesto: lo escalan a la persona que los dirige.
- **Prohibido inventar** datos, constantes, normas, significados de variables, códigos DIVIPOLA, referencias o resultados. Si falta
  algo se escribe `TODO(dato-faltante)` o `TODO(cita)` y se reporta: un dato inventado es peor que uno faltante.
- El significado de las variables sale del diccionario oficial de cada conjunto, nunca de una IA, y toda norma colombiana se cita
  desde su fuente oficial.
- Todo prompt enviado a una IA se guarda literal antes de enviarlo.

**Subagent Driven.** Cada integrante dirige su propia sesión de Claude Code (el orquestador, en el modelo más capaz) y esta reparte
el trabajo entre agentes especializados definidos en `.claude/agents/`. Cada subagente recibe el contexto mínimo y suficiente:
la tarea, su sección de la spec personal, las secciones del núcleo que consume o produce, los apartados del enunciado que cubre y
su prueba de aceptación, y nada de otras partes (núcleo §10.2). Escribir primero la prueba y después el código es otra regla fija
del proyecto.

### El flujo de cada tarea

```
Responsable (orquesta su sesión de Claude Code, Opus)
  → implementador (Sonnet) o implementador-experto (Opus, tareas difíciles)   [prueba primero]
  → revisor-spec (Sonnet) → revisor-calidad (Haiku)
  → verificador de la tarea (verificador-matematico / auditor-fugas / cazador-alucinaciones, Opus)
  → pull request del responsable → Daniel revisa y fusiona → documentador (Haiku) actualiza MEMORIA y PLAN
```

Ese es el flujo de núcleo §10.1. Dicho en prosa: el implementador escribe la prueba y el código; el `revisor-spec` comprueba si
cumple el Spec y el enunciado al pie de la letra; el `revisor-calidad` revisa claridad y pruebas, con prioridad en lo que alguien
del equipo tendría que explicar o modificar en vivo en la sustentación; y el verificador de la columna «+ Verificador» de la tarea
(matemático, de fugas o cazador de alucinaciones) intenta romper el resultado. Cada revisor recibe un prompt propio que dice qué
revisar y que **no modifica archivos**: solo informa. Si un revisor rechaza, la tarea vuelve al implementador con los hallazgos.
Todo error de un subagente que se detecta es candidato al registro de la Cacería de la alucinación
(`alucinaciones/registro.md`; ver la sección «Cacería de la alucinación»).

### Los agentes, su modelo y por qué

La regla de asignación (núcleo §10.3) es: Haiku para lo mecánico y fácil de verificar; Sonnet para implementación con una spec
clara; Opus para diseño, matemáticas, fugas y auditoría, donde un error suena convincente. La sesión principal (el orquestador)
corre en Opus ([[tab:uso-ia-agentes]]).

::: tabla uso-ia-agentes
Título: Agentes del proyecto, su modelo y para qué se usan
Fuente: `docs/spec/SPEC.md` §10.3 (agentes definidos en `.claude/agents/`). La columna «Por qué ese nivel» aplica la regla de asignación del mismo apartado.

| Agente | Modelo | Para qué | Por qué ese nivel |
|---|---|---|---|
| `implementador` | Sonnet | Una tarea de código Python estándar, prueba primero | Implementación con una spec clara |
| `implementador-experto` | Opus | Tareas difíciles: pérdidas, origen rodante, partición sin fuga, Grad-CAM/CAM, negativos y pérdida de M3, modelo de flota | Un error de diseño o matemático suena convincente |
| `implementador-web` | Sonnet | App Next.js y video Remotion | Implementación con una spec clara |
| `curador-datos` | Sonnet | Descarga, diccionario, conteos, fuentes, ficha | Implementación con una spec clara |
| `analista-experimentos` | Sonnet | Corre búsquedas y 30 semillas, vigila la comparación justa, señala resultados sospechosos | Ejecución guiada por la spec |
| `revisor-spec` | Sonnet | ¿Cumple exactamente el Spec y el enunciado? | Contraste contra un texto de referencia |
| `revisor-calidad` | Haiku | Claridad y pruebas del código (se explica en vivo) | Lo mecánico y fácil de verificar |
| `verificador-matematico` | Opus | Deriva y comprueba numéricamente cada fórmula (pérdidas, LSTM/GRU, softmax y entropía cruzada, CAM, métricas, flota) | Matemáticas: donde un error suena convincente |
| `cazador-alucinaciones` | Opus | Contrasta afirmaciones de IA con fuentes primarias o experimentos; registra hallazgos | Auditoría adversarial |
| `redactor-tecnico` | Sonnet | Secciones del blog con figuras y tablas numeradas y citadas | Redacción guiada por resultados ya generados |
| `tutor-sustentacion` | Sonnet | Fichas, preguntas probables, predicciones verificadas para cambios en vivo | Redacción guiada por la spec |
| `auditor-reproducibilidad` | Haiku | Clon limpio, demos de menos de 2 minutos, sin internet, un comando | Lista de chequeo mecánica |
| `documentador` | Haiku | MEMORIA, PLAN, README, pies de figura, registro de prompts | Lo mecánico y fácil de verificar |
| `auditor-fugas` | Opus | Auditoría adversarial de fuga en los tres módulos: variables de M1 no conocibles 30 días antes y ventanas que miran al futuro; casi duplicados de M2 entre particiones; interacciones de prueba de M3 en entrenamiento o en la popularidad. Escribe la prueba que lo demuestra | Fugas: un error es silencioso y suena convincente |
| `investigador-fuentes` | Sonnet (con web) | Busca y cita la fuente primaria de lo que no sale de los datos (normativa, DIVIPOLA, diccionarios, artículos). Entrega cita APA, URL y fecha de consulta | Búsqueda y cita con formato fijo; su resultado se contrasta |
| `auditor-entregables` | Haiku | Recorre el enunciado como lista de chequeo y reporta qué existe y qué falta | Lista de chequeo mecánica |
:::

<!-- revisar: Daniel — la columna «Por qué ese nivel» es una justificación del redactor basada en la regla de §10.3; para los agentes que §10.3 no justifica uno a uno (analista-experimentos, tutor-sustentacion, investigador-fuentes, redactor-tecnico) es una inferencia. Ajusta o confirma. -->

### Dónde quedan los prompts

Cada prompt que se envía a un subagente (incluidos los del orquestador) se guarda **literal** en
`alucinaciones/prompts/<ID>.md` **antes** de enviarlo (núcleo §0, regla 6, y §9). El identificador es el de la tarea más una
letra: `DA-1a`, `DA-1b`… son los prompts de implementación de la tarea DA-1; `DA-1d` es el de corrección a partir de la revisión;
`DA-1-revision.md` y `DA-3-revision.md` contienen los prompts de los revisores. La razón es doble: el enunciado exige el prompt
literal de cada hallazgo de la cacería, y un prompt que se reconstruye de memoria después deja de ser evidencia.

<!-- pendiente: lista final de los prompts principales con enlace al repositorio y discusión de su impacto en el resultado final (DA-12). -->

### Qué detectaron los revisores en DA-1 y DA-3

Las dos tareas ya pasaron por todo el flujo. Los revisores no encontraron lo mismo que el implementador había dado por
terminado, y eso es lo que justifica tener el flujo ([[tab:uso-ia-revisiones]]).

::: tabla uso-ia-revisiones
Título: Ejemplos de lo que los revisores detectaron en DA-1 y DA-3
Fuente: `alucinaciones/prompts/DA-1-revision.md` y `DA-1d.md` (DA-1); `alucinaciones/prompts/DA-3-revision.md` y `DA-3c.md`, `docs/investigacion/DA-3_auditoria_fugas.md` y `alucinaciones/evidencias/DA-3_auditoria_fugas/` (DA-3); mensajes de commit de `git log` (9d54ae1, 8ceed41, aafdb4c).

| Tarea | Revisor (modelo) | Qué detectó | Qué se hizo |
|---|---|---|---|
| DA-1 | `revisor-spec` (Sonnet) | Aprobó: la infraestructura cumple el Spec | Nada que corregir |
| DA-1 | `revisor-calidad` y `auditor-reproducibilidad` (Haiku) | `correr_demo` en `src/comun/notebooks.py` no capturaba `TimeoutExpired`, así que la celda del notebook de sustentación terminaría en un traceback | Se captura y devuelve el estado `"timeout"` con un mensaje claro, con prueba |
| DA-1 | ídem | El README listaba como funcionando comandos con configs que aún no existían, y en Windows pedía instalar sin avisar que la ruta profunda rompe `pip install` (límite de 260 caracteres) ni que el `python` del PATH era 3.13 y no 3.12 | README con ruta corta, `.venv\Scripts\python` en todos los comandos y los comandos de §4.1 presentados como «se habilita cuando el dueño entrega su tarea» |
| DA-1 | `revisor-calidad` (Haiku) | Pruebas del CLI dependían de subcomandos reales que seguían pendientes: fallarían cuando los dueños los implementaran | Se reemplazan por un subcomando falso registrado en la prueba |
| DA-1 | ídem | Una conversión de fechas dividía por `86_400e9`, suponiendo nanosegundos | Se cambia por una resta con `pd.Timedelta`, exigiendo que el SHA-256 de la serie sintética no cambie |
| DA-3 | `revisor-spec` (Sonnet) | Aprobó, con una observación: el enunciado pide el número de registros y solo se reportaba el del conjunto completo y las filas descargadas | Se mide con `scripts/descargar_m1.py contar` el número de registros crudos de las 6 rutas (1 372 746) y se distinguen cuatro conteos |
| DA-3 | `revisor-calidad` (Haiku) | El conteo «pasajeros = 0 con despachos ≥ 1» contaba solo `pasajeros == 0`, sin filtrar despachos: el número y la frase decían cosas distintas | Se corrige el conteo (531 de 25 248 filas descargadas) y se prueba con una fila (0, 0) |
| DA-3 | ídem | La fecha de descarga de `ficha.json` se tomaba de la fecha de modificación de los archivos, no de la descarga | Se toma del registro de consultas (`consultas_log.jsonl`) y falla con un error claro si no existe |
| DA-3 | `auditor-fugas` (Opus) | Ninguna fuga activa, pero tres riesgos para el arnés de evaluación: usar `anomalo` como variable de entrada, excluir anómalos del test, y que con orígenes semanales desde el 2023-07-01 nadie pronosticaba del 26 al 31 de diciembre de 2023 | Entran al núcleo §5.3 (Spec v0.5): lista blanca de columnas, test sin excluir anómalos, última fecha de origen anclada al 2023-12-01 |
| DA-3 | ídem | Si se usara el `despachos` del día objetivo como entrada, el MAE de prueba bajaría de 281 a 109 (52001-52356) y de 856 a 531 (15759-11001): una fuga grave que hoy nadie comete | Se deja escrito en el Spec que `despachos` y el detalle solo entran como rezagos de 30 días o más |
:::

Dos aclaraciones sobre estos ejemplos. Primero, son defectos del código y de la documentación que generó la IA y que el flujo
atrapó antes de que otro integrante los consumiera; por sí solos no son «hallazgos de la cacería» hasta que tengan su prompt
literal, la respuesta de la IA y la evidencia, con las seis partes que pide el enunciado (el registro de hallazgos a la fecha de
este borrador no tiene hallazgos confirmados, `docs/MEMORIA.md`). Segundo, las inconsistencias entre el diccionario de datos.gov.co
y los datos mismos, documentadas en la sección de datos de M1, son un hallazgo sobre los datos, no una alucinación, salvo que alguna
IA haya afirmado lo contrario con un prompt guardado.

<!-- revisar: Daniel — decide cuáles de estas filas pasan al registro de la cacería (alucinaciones/registro.md). El auditor-fugas (DA-3) declaró «candidatos a hallazgo: ninguno». -->

### Impacto

<!-- revisar: Daniel — todo lo de este apartado es juicio sobre el impacto de la IA y debe ser tuyo; lo siguiente es solo un borrador basado en lo medible. -->

Lo que se puede afirmar con evidencia del repositorio es lo siguiente. El flujo con revisores separados atrapó defectos reales en
la infraestructura (DA-1) y en las series de M1 (DA-3) antes de que alguien los consumiera, y llevó a cambios en el Spec
(la versión 0.5, «a partir de auditor-fugas», en la cabecera de `docs/spec/SPEC.md`). El verificador de fugas pudo cuantificar cuánto cambiaría una
métrica si se usara una variable no conocible 30 días antes, algo que ni el implementador ni la revisión de código revisan por sí solos.

Lo que este reporte todavía no puede afirmar, y debe decidir Daniel con la evidencia que reúna el resto del equipo: cuánto tiempo
ahorró la IA en la práctica, qué porcentaje del código quedó tal como lo generó el implementador, y si hubo errores que ningún
revisor atrapó y se descubrieron después.

<!-- pendiente: impacto cuantitativo (tiempo, proporción de código generado, errores no atrapados) y lecciones del equipo completo (DA-12). -->
