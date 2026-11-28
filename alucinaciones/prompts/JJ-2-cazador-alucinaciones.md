# Prompt JJ-2 (R4) — cazador-alucinaciones (Opus) — 2026-11-26 — orquesta: Juan José

Actúa como el agente definido en `.claude/agents/cazador-alucinaciones.md` (léelo primero). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales` (rama `dev/juanjose`). Solo lees y ejecutas, **salvo** `alucinaciones/registro.md`,
donde puedes agregar candidatos (sin numerar: `H-?? (JJ-2)`). No hagas commit ni push. Usa `.venv/Scripts/python`.

Lee antes: `docs/spec/SPEC.md` §0 y §9; `docs/spec/partes/juanjose.md` §3.1 (D1–D7); `alucinaciones/registro.md` (formato de
los candidatos existentes); los prompts literales de esta tarea en `alucinaciones/prompts/JJ-2*.md`.

## Qué contrastar
1. **Cada cifra** de `blog/secciones/07-m3-recomendacion.md` (texto, tablas, títulos y fuentes de figuras) contra el
   archivo de `results/data/m3/eda/` (o `app/public/model/m3/perfil_nuevo.json` para K) que la respalda. Recorre el archivo
   completo de forma sistemática (un script que extraiga los números del markdown ayuda); para cada una: ¿existe en el
   archivo citado?, ¿el redondeo es correcto?, ¿la clave citada es la correcta? Reporta las que no tengan respaldo.
2. **Afirmaciones cualitativas** del blog que digan más que las cifras (p. ej. «no hay efecto» cuando el veredicto es no
   concluyente; atribuir patrones a turistas reales, contra D4).
3. **Cita del conjunto**: `[@mehra2024]` contra la entrada de `blog/references.bib` y contra
   `results/data/m3/eda/ficha.json` (`cita`, `url`, `fecha_descarga`) y `docs/investigacion/JJ-1_kaggle_metadata.json`
   (autor, título, versión, fecha de creación de la versión 1 = 2024-01-23). Que el blog no diga «publicación» para esa
   fecha. Las citas literales de la fuente en el blog deben ser subcadenas exactas de `info.description` del JSON de
   Kaggle.
4. Que no haya ninguna referencia bibliográfica nueva (`[@…]`) ni afirmación de autoría de una fórmula sin `TODO(cita)`.
5. Que `figs_m3.py` y las figuras no muestren cifras tecleadas (todas leídas de `results/`).

## Candidatos a la cacería
Además de lo que encuentres, evalúa y registra (si se sostienen con evidencia reproducible) estos dos detectados por el
verificador-matematico en R2 (primera vuelta), ya corregidos, cuya evidencia está en su informe resumido así:
- **Redactor (Sonnet, prompt `JJ-2-redactor-tecnico.md`)**: el blog afirmaba «Los p de H-M3-1 a H-M3-4 son por permutación
  entre usuarios … los intervalos son por percentiles de 2 000 remuestreos de usuarios (o de destinos en H-M3-3)», cuando
  H-M3-3 permuta entre destinos, H-M3-5 usa simulación (IC por inversión) y H-M3-6 p asintóticos. (Ya corregido: la versión
  original no está en el repo; búscala con `git diff` si aún no hay commit, o regístrala como evidencia textual del informe de
  R2 citado aquí.)
- **Analista (Sonnet, prompt `JJ-2-analista-experimentos.md`)**: el texto de la regla de veredicto escrito en
  `pruebas_hipotesis.json` decía «refuta si p ajustado ≥ alfa y el IC 95 % queda dentro de ±mínimo», contradiciendo la función
  `veredicto_de_prueba`, que exige además que el IC contenga el 0; aplicada a H-M3-1 la regla escrita daba «refutada» y el
  código «no concluyente». (Ya corregido.)
Juzga si son alucinaciones (afirmación falsa con apariencia de verdad) o errores de redacción/código; regístralos como
candidatos solo si encajan en §9, con categoría, módulo (M3), modelo, prompt y evidencia. Uno débil, no lo registres y dilo.

Responde con: tabla de cifras revisadas (n.º, coinciden, no coinciden con detalle), afirmaciones problemáticas con
archivo:línea y corrección, estado de la cita, y los candidatos registrados (o descartados, con la razón).
