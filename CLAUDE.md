# Trabajo 3 — Redes neuronales para series de tiempo, imágenes y recomendación

Fuente de verdad: `docs/spec/SPEC.md` (núcleo con los contratos y, en su **Anexo, el enunciado literal del trabajo**) y la
spec personal en `docs/spec/partes/` (daniel, camila, andres, jose, juanjose). Tablero: `docs/spec/PLAN.md`.
Idioma del proyecto: español. Entrega: mar 1-dic-2026.

**Al iniciar una sesión:** lee el núcleo completo (incluido el Anexo) y la spec personal de quien te dirige antes de proponer
o cambiar nada.

## Memoria del proyecto (estado actual — se carga en cada sesión)
@docs/MEMORIA.md

**Obligatorio:** al cerrar una tarea del PLAN, fusionar un PR o registrar una decisión, actualizar `docs/MEMORIA.md`
(estado, decisiones vigentes, pendientes, cacería y una línea nueva arriba en la bitácora). Mantenerla ≤ 150 líneas.

## Reglas para cualquier sesión o subagente
- Cualquier integrante puede cambiar el Spec bajo su criterio (núcleo §0.1): por PR, subiendo la versión, con una línea en el
  historial y avisando a los afectados si toca un contrato o un hito. El Anexo (enunciado) no se edita.
- Los subagentes no cambian el Spec: lo [DECIDIDO], [PENDIENTE] o [PROPUESTO] se escala al humano que los dirige.
- **Prohibido inventar** datos, significados de variables, normas, códigos DIVIPOLA, constantes, referencias o resultados.
  Si falta algo: `TODO(dato-faltante)` / `TODO(cita)` y reportarlo.
- Variables: del diccionario oficial de cada conjunto. Normas: de su fuente oficial. Nunca de una IA.
- **Fuga de información:** M1 solo con información conocible 30 días antes; M2 partición por grupos de casi duplicados;
  M3 ninguna interacción de prueba en train. Preprocesamiento ajustado solo con train.
- Análisis descriptivo: los tres módulos siguen la **plantilla común** del núcleo §5.12.
- Los experimentos nunca usan internet. Semillas con `src/comun/seeds.py` (`base_seed + run_id`).
- Prueba primero, luego código.
- **Nunca push a `main`; a `main` solo se llega por PR** (lo aprueba y fusiona Daniel). Push libre a la rama propia
  `dev/<nombre>` y, si hace falta, a la de un compañero avisándole. Claude hace commits frecuentes y el push cuando el
  integrante lo indique.
- Trabaja solo en los archivos de tus tareas; los compartidos (`src/comun/`, `run.py`, `requirements.txt`, README, núcleo)
  solo por PR dedicado.

## Protocolo del orquestador (la sesión principal de cada integrante, en Opus)
1. Tomar la siguiente tarea ⬜ propia de la spec personal cuyas dependencias estén ✅ (o trabajar con sintéticos si no).
2. Armar el contexto del subagente (núcleo §10.2): texto de la tarea + su sección de la spec personal + las secciones del
   núcleo §5 que consume o produce + los apartados del Anexo que cubre + prueba de aceptación. **Nada de otras partes.**
3. **Guardar el prompt literal** en `alucinaciones/prompts/<ID>.md` antes de enviarlo.
4. Despachar `implementador` (Sonnet) o `implementador-experto` (Opus) si la tarea tiene 🧠; `implementador-web` en
   `app/`/`video/`; `curador-datos` o `investigador-fuentes` en tareas de datos y fuentes.
5. Despachar `revisor-spec`; si falla, devolver al implementador con los hallazgos.
6. Despachar `revisor-calidad`; si falla, ídem.
7. Despachar el verificador de la columna «+ Verificador» (`verificador-matematico`, `auditor-fugas`, `cazador-alucinaciones`…).
8. Todo error de un subagente que se haya detectado (fórmula, dato, norma, referencia, fuga) → candidato en
   `alucinaciones/registro.md`.
9. Marcar la tarea en `PLAN.md` y en la spec personal; abrir el PR hacia `main` con la plantilla (lo fusiona solo Daniel).
10. `documentador` actualiza `docs/MEMORIA.md`.
