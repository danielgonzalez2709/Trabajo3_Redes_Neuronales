# Prompt JJ-2 (R3) — revisor-calidad (Haiku) — 2026-11-26 — orquesta: Juan José

Actúa como el agente definido en `.claude/agents/revisor-calidad.md` (léelo primero). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales` (rama `dev/juanjose`). Solo lees y ejecutas; **no modifiques archivos**, no hagas
commit ni push. Usa `.venv/Scripts/python`. La tarea JJ-2 ya pasó la revisión de Spec (R1) y la verificación matemática
(R2): no repitas esas revisiones.

Revisa la calidad de: `src/m3_recomendacion/eda.py`, `src/viz/figs_m3.py`, `configs/m3/eda.yaml`, `tests/test_eda_m3.py`
y el cambio de JJ-2 en `src/m3_recomendacion/datos.py`, `tests/test_datos_m3.py` y `src/m3_recomendacion/README.md`
(`git diff` para estos tres). Como referencia de estilo del proyecto: `src/m3_recomendacion/datos.py` y `src/comun/eda.py`.

Criterios: legibilidad y estructura (funciones cortas con un propósito; nombres claros en español; sin código muerto ni
duplicado); que Juan José pueda **explicarlo y modificarlo en vivo en la sustentación** (p. ej. cambiar `n_permutaciones`,
el umbral de actividad o un efecto mínimo en la config y predecir qué cambia); pruebas (¿prueban comportamiento y no
detalles?, ¿cubren los casos borde?, ¿son rápidas?, ¿hay pruebas frágiles o redundantes?); eficiencia (corre en segundos;
¿hay bucles evitables?); parámetros en la config y no tecleados en el código; manejo de errores con mensajes claros;
comentarios y docstrings proporcionados (ni de más ni de menos, como el código vecino).

Ejecuta: `.venv/Scripts/python -m pytest -q tests/test_eda_m3.py tests/test_datos_m3.py -p no:cacheprovider` y
`.venv/Scripts/python run.py m3-eda --config configs/m3/eda.yaml` (mide el tiempo). Si quieres saber el tamaño:
`wc -l` de los archivos.

Responde con **APROBADO** / **NO APROBADO** y hallazgos priorizados (bloqueantes / recomendados / opcionales), cada uno
con archivo:línea y una corrección concreta. Bloqueante solo si dificulta de verdad entenderlo, modificarlo o confiar en
él; lo cosmético va en opcional.
