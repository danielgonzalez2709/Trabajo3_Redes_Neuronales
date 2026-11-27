# Prompt CA-2-verificacion — cazador-alucinaciones (Opus) — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/cazador-alucinaciones.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). **No hagas `git commit` ni
`git push`. No edites código, configs ni `alucinaciones/registro.md`**: Camila revisa todo antes. Tu único archivo de salida es
`docs/investigacion/CA-2_verificacion.md` (y evidencias en `alucinaciones/evidencias/CA-2/` si las guardas).

Contexto: `docs/spec/SPEC.md` §0, §5.4 y §9 y el Anexo («Módulo 1 → Preguntas de negocio 1 y 2»); `docs/spec/partes/camila.md`
§3.2 y §5 (puntos calientes); el informe generado por IA `docs/investigacion/CA-2_normativa_operacion.md` (prompt literal en
`alucinaciones/prompts/CA-2a.md`) y cómo se usó en `configs/m1/operacion.yaml` (notas `meta`, prompt `CA-3a.md`).

## Tarea
Verificar adversarialmente, contra **fuentes primarias que abras tú** (Secretaría del Senado, Función Pública – Gestor Normativo,
Ministerio de Transporte, Diario Oficial):
1. Ley 2101 de 2021, arts. 2–3: reducción de la jornada semanal y su cronograma (el informe **derivó** las fechas 15-jul-2023,
   2024, 2025, 2026 desde la publicación; compruébalo con el texto y la fecha de publicación oficial).
2. Ley 2466 de 2025: art. 11 (nuevo art. 161 CST: 8 h diarias, 42 h semanales), art. 13 (horas extras), art. 14 (descanso);
   el informe solo leyó el 80 % del texto.
3. Resolución 315 de 2013 del MinTransporte, art. 6 (segundo conductor si el recorrido supera 8 h): texto literal y **vigencia**
   (¿compilada, modificada o derogada por el Decreto 1079 de 2015 u otra norma posterior?).
4. Decreto 1393 de 1970, art. 56 (tope de 10 h para conductores): existencia, texto y vigencia.
5. Que **no exista** una norma vigente de tiempos máximos de conducción continua o diaria para conductores de pasajeros por
   carretera (el informe dice que no la halló; busca a fondo, p. ej. resoluciones del MinTransporte de 2022–2026 o el PESV).
6. Decreto 171 de 2001, arts. 50–51: rangos de capacidad por clase y su vigencia en el Decreto 1079 de 2015; si el rango incluye o
   no al conductor.
Entrega por afirmación: CONFIRMADA / REFUTADA / NO VERIFICABLE, con fragmento literal, URL y fecha de consulta; qué valores de
`configs/m1/operacion.yaml` pueden pasar de `supuesto: true` a `fuente:` y con qué cita exacta. Al final, **candidatos a hallazgo**
(solo errores de una IA con prompt literal guardado, con los 6 puntos del enunciado, §9) y correcciones necesarias (no las apliques).
