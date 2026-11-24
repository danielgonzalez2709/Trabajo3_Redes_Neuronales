# Prompts de revisión de DA-5 — 2026-11-24 — orquesta: Daniel

Repositorio: `C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales`, rama `dev/daniel`, último commit
«DA-5: esqueleto de la app…». Prompt de implementación: `alucinaciones/prompts/DA-5a.md`. Next.js se subió de 16.4.3 a 16.4.6
por avisos de seguridad. **Ningún revisor modifica archivos del repo.** Para la app: `npm --prefix app test` y
`npm --prefix app run build` (no dejes procesos `next dev` corriendo al terminar).

## R1 — revisor-spec (Sonnet)
Actúa como el agente definido en `.claude/agents/revisor-spec.md` (léelo primero). Revisa DA-5 contra `docs/spec/SPEC.md` §3
(App, Interpretabilidad M2), §5.4, §5.6, §5.8, §8, el Anexo («Aplicación web» y «Entregables → 4») y `docs/spec/partes/daniel.md`
§3.3 y fila DA-5. En particular: ¿los esquemas de `app/lib/contratos.ts` cubren lo que el Anexo exige a cada página (ruta,
pronóstico a 30 días con banda, flota y conductores, ≥ 2 parámetros operativos; imagen, clase, probabilidad por clase, alerta
según umbral, mapa; usuario existente o perfil nuevo con lista de preferencias, K destinos e historial)?; ¿sirven para que
Andrés/Camila, José y Juan José exporten sin ambigüedad?; ¿la app funciona sin internet (wasm local)?; ¿los datos de juguete
están marcados y no son datos de personas reales?; ¿enlaces a reporte, video y videos individuales? Señala lo que falte en los
contratos para DA-6/DA-7/DA-8. Salida: APROBADO o RECHAZADO + hallazgos (archivo:línea, sección).

## R2 — revisor-calidad (Haiku)
Actúa como el agente definido en `.claude/agents/revisor-calidad.md` (léelo primero). Revisa `app/lib/*.ts`, `app/hooks/`,
`app/components/`, las páginas de `app/app/`, `app/tests/`, `scripts/generar_juguetes_app.py` y `tests/test_juguetes_app.py`.
Prioriza claridad para explicar en vivo, pruebas que puedan fallar de verdad y que nada quede «provisional» sin marcar.
Salida: APROBADO o CAMBIOS REQUERIDOS con archivo:línea.
