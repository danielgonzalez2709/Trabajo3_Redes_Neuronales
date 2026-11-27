# Prompt JJ-2 (R1) — revisor-spec (Sonnet) — 2026-11-26 — orquesta: Juan José

Actúa como el agente definido en `.claude/agents/revisor-spec.md` (léelo primero). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales` (rama `dev/juanjose`). Solo lees y ejecutas; **no modifiques ningún archivo**, no
hagas commit ni push. Usa `.venv/Scripts/python`.

Lee antes: `docs/spec/SPEC.md` §0, §5.7, §5.8, §5.12 y §6, y del Anexo «Módulo 3» (Datos, Tareas 1 y 2, Figuras mínimas);
`docs/spec/partes/juanjose.md` §3.0, §3.1 (D1–D7 [DECIDIDO, Juan José, 25-nov]) y §3.3; el encargo literal de la tarea en
`alucinaciones/prompts/JJ-2.md` y los encargos a los subagentes `JJ-2-analista-experimentos.md`,
`JJ-2-analista-experimentos-2.md` y `JJ-2-redactor-tecnico.md`. Nada de otras partes.

## Qué revisar (tarea JJ-2)
Archivos: `tests/test_eda_m3.py`, `configs/m3/eda.yaml`, `src/m3_recomendacion/eda.py`, `src/viz/figs_m3.py`,
`results/data/m3/eda/*` (los nuevos y `ficha.json`/`diccionario.json` regenerados), `blog/docs/figures/m3/*.png`,
`blog/secciones/07-m3-recomendacion.md`, y el cambio E6 (`src/m3_recomendacion/datos.py`, `configs/m3/datos.yaml`,
`tests/test_datos_m3.py`, `src/m3_recomendacion/README.md`, `docs/spec/partes/juanjose.md` D3–D4,
`docs/investigacion/JJ-1_fuentes_m3.md`). Usa `git diff` y `git status` para ver qué cambió.

1. **Anexo M3, tarea 1 (caso de uso)**: ¿el párrafo de caso de uso dice momento, canal, K e información disponible del
   usuario? ¿Es coherente con §5.8 (contrato de la app: `k_defecto`, perfil nuevo con preferencias) y con D6? ¿Está sin
   encabezado propio y antes de «### Análisis descriptivo»?
2. **Anexo M3, tarea 2**: distribución de interacciones por usuario y por destino, concentración en populares, proporción
   de usuarios con pocas interacciones, hipótesis sobre qué explica las preferencias. ¿Está todo, medido y en el blog?
3. **Plantilla §5.12**: las 7 subsecciones con los nombres exactos y en orden; `hipotesis.json` con el esquema (claves,
   ids `H-M3-n`, veredictos válidos; las que dependen de modelos en `pendiente`) y escrito con `escribir_hipotesis`.
4. **Figura mínima** «Distribución de interacciones por usuario y por destino (cola larga)»: existe, se genera con
   `run.py figures` solo desde `results/`, y está en el blog con título, fuente y cita en el texto.
5. **D1–D7**: interacción = unión implícita; destino = 1 000 ids con `lugar`; el umbral de actividad y las cifras de
   partición son coherentes con D3 (sin implementar la partición, que es JJ-3); real o sintético según D4 (y ninguna
   frase atribuye patrones a turistas reales); licencia D5; `Name`/`Email`/`ReviewText` ausentes de salidas y blog (D6).
6. **E6**: la fecha 2024-01-23 aparece como «creación de la versión 1 en Kaggle» y no como «publicación» en
   `configs/m3/`, `results/data/m3/`, `src/m3_recomendacion/`, `tests/test_datos_m3.py`, la sección M3 de `data/fuentes.md`,
   `juanjose.md` (D3, D4) y `JJ-1_fuentes_m3.md`. (Las evidencias históricas de JJ-1 en `alucinaciones/evidencias/` y
   `docs/investigacion/JJ-1_verificacion_R3.md` no se reescriben.)
7. **Reglas §0 y del encargo**: config para todo parámetro (semillas `base_seed + run_id` vía `src/comun/seeds.py`,
   `n_permutaciones`, umbral, criterio de veredicto); `eda.py` lee solo `data/processed/m3/`; no se tocaron archivos
   compartidos (`src/comun/`, `run.py`, `requirements.txt`, `SPEC.md`, `estilo.py`, `paleta.py`, otras secciones del blog);
   ninguna cita bibliográfica nueva salvo `mehra2024`; lo que no tiene fuente queda como `TODO(cita)`.
8. **Ni más ni menos**: señala lo que sobra (alcance de JJ-3/JJ-6/JJ-10 adelantado) o lo que falta.

Ejecuta: `.venv/Scripts/python run.py m3-eda --config configs/m3/eda.yaml`, `.venv/Scripts/python run.py figures`,
`.venv/Scripts/python -m pytest -q tests/test_eda_m3.py tests/test_datos_m3.py tests/test_blog.py` y
`.venv/Scripts/mkdocs build --strict -f blog/mkdocs.yml`; comprueba con `git status` que la corrida no cambió bytes de
`results/data/m3/eda/`.

Responde con un veredicto **APROBADO** o **NO APROBADO** y la lista de hallazgos (bloqueantes / menores), cada uno con
archivo:línea y la regla del Spec o del encargo que incumple. Lo que sea una decisión del humano ([PROPUESTO], umbrales,
criterios), repórtalo como «decide Juan José», no como defecto.
