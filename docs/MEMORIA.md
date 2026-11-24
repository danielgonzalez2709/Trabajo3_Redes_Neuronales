# MEMORIA — estado del Trabajo 3 (≤ 150 líneas)

## Estado
- Spec v0.2. `main` protegida (ruleset `proteger-main`: PR + Code Owners; Daniel fusiona). Ramas `dev/*` creadas.
- DA-1 (infraestructura) terminado en `dev/daniel` y en PR hacia `main`: `src/comun/` (config, cli, seeds, results,
  torch_utils, notebooks, eda), `run.py` con los 17 subcomandos (los pendientes salen con código 2), blog MkDocs con el
  esqueleto de 14 secciones, serie sintética de M1 en `data/sintetico/m1/`, CI (job `pruebas`), `.gitattributes`.
  233 pruebas en verde. Revisado por revisor-spec (APROBADO), revisor-calidad y auditor-reproducibilidad (correcciones aplicadas).
- DA-2: investigación de fuentes lista en `docs/investigacion/DA-2_fuentes_m1.md`; falta decidir periodo y filtro y descargar.
- Entrega: mar 1-dic-2026 (hora por confirmar).

## Decisiones vigentes
- Git: solo Daniel fusiona a `main` por PR; cada quien en `dev/<nombre>`; push permitido a otras ramas, nunca a `main`.
- App en Vercel (Next.js estático). Blog en MkDocs Material + hook del Trabajo 2.
- Plantilla común de análisis descriptivo para los 3 módulos (núcleo §5.12); veredicto `pendiente` hasta modelar.
- Daniel hace las primeras tareas de M1 (DA-2/DA-3); Camila continúa desde el descriptivo.
- Serie sintética: códigos ficticios del departamento `00`; picos de temporada como proxy de festivos.
- JSON de juguete de la app: en DA-5.
- Conjunto de M1: datos.gov.co `eh75-8ah6` (Supertransporte). DIVIPOLA: DANE en datos.gov.co `gdxc-w37w` (corte 30-dic-2024).

## Avisos para el equipo
- Windows: clonar en una ruta corta (p. ej. `C:\proy\`); en rutas profundas `pip install` falla por el límite de 260 caracteres.
- Usar siempre `.venv\Scripts\python` (el `python` del PATH puede ser 3.13).
- Si `configs/<m>/` aún no existe, cada dueño crea las suyas en su tarea.

## Pendientes
1. Hora de la entrega y fecha de la sustentación.
2. M1: periodo útil (hueco casi total en 2024 y dic-2025), filtro `tipo_despacho` y rutas (Daniel + Camila, DA-3).
3. GPU para las 30 semillas de M2.

## Cacería
- Hallazgos confirmados: 0 / meta ≥ 5 (≥ 3 categorías, ≥ 1 por módulo).
- Ojo: las inconsistencias del diccionario de M1 (DA-2) son hallazgos de datos para el blog, no alucinaciones, salvo que una
  IA haya afirmado lo contrario con prompt literal guardado.

## Bitácora (más reciente arriba)
- 2026-11-24 · Daniel · DA-1 terminado y en PR; investigación de fuentes de M1 (DA-2) lista; Spec v0.2.
- 2026-11-23 · Daniel · Spec v0.1, PLAN, agentes y plantillas del Trabajo 3.
