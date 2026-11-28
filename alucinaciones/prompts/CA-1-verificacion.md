# Prompt CA-1-verificacion — cazador-alucinaciones (Opus) — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/cazador-alucinaciones.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). **No hagas `git commit` ni
`git push`. No edites código, datos ni `alucinaciones/registro.md`**: Camila revisa todo antes. Tu único archivo de salida es
`docs/investigacion/CA-1_verificacion.md` (y evidencias en `alucinaciones/evidencias/CA-1/` si guardas capturas o fragmentos).

Contexto: `docs/spec/SPEC.md` §0, §5.2 y §9; `docs/spec/partes/camila.md` §3.1 y §5 (puntos calientes); el informe generado por
IA `docs/investigacion/CA-1_fuentes_calendario.md` (prompt literal en `alucinaciones/prompts/CA-1a.md`) y su implementación
`data/externos/m1/calendario_fuentes.yaml` + `src/m1_demanda/calendario.py` (prompt `CA-1b.md`).

## Tarea
Verificar adversarialmente, contra **fuentes primarias que abras tú**, las afirmaciones del informe y de la transcripción:
1. Ley 51 de 1983: texto del art. 1, qué festivos se trasladan; fecha de la ley (el informe reporta dos fechas distintas entre
   fuentes); vigencia.
2. Las 72 fechas de festivos 2021–2024 que produce `calendario.parquet` (`festivo`, `festivo_nombre`): contrástalas con una fuente
   oficial independiente si existe (p. ej. decretos o circulares oficiales que listen los festivos del año) y con la regla.
   Desfases de Ascensión, Corpus Christi y Sagrado Corazón respecto de la Pascua: busca la fuente primaria (son `TODO(cita)`).
3. Muestra de recesos escolares: al menos un acto administrativo por ciudad (Bogotá, Cali, Sogamoso, Pasto, Ipiales), abre la URL
   citada y compara las fechas literales con `calendario_fuentes.yaml`. Revisa en especial Bogotá 2022 (13 semanas), Cali 2022
   (4 semanas en julio), Ipiales 2023 (octubre), Pasto (inferencia «todo lo que no es Desarrollo Académico»).
4. Errores de transcripción informe → YAML → parquet (compara con pandas usando `.venv/bin/python`).
Entrega por afirmación: CONFIRMADA / REFUTADA / NO VERIFICABLE, con fragmento literal, URL y fecha de consulta. Al final, una lista
de **candidatos a hallazgo** para la cacería (solo errores de una IA con prompt literal guardado, con los 6 puntos del enunciado,
§9) y una lista de correcciones necesarias en el YAML o el código (no las apliques).
