# JJ-3 — prompt del orquestador (Opus 5.5) al revisor-calidad (Haiku), 2026-11-26

Revisa la calidad del código y de las pruebas de la tarea JJ-3 (partición sin fuga de M3), ya aprobada en lo funcional por el
auditor-fugas (sin fuga). Directorio `C:\Repositorios\Trabajo3_Redes_Neuronales`. Solo lectura (puedes correr pruebas con
`.venv/Scripts/python -m pytest`); no edites nada; sin commits.

Archivos: `src/m3_recomendacion/particion.py` (nuevo), los cambios de `src/m3_recomendacion/datos.py` y
`configs/m3/datos.yaml` (`git diff`), `tests/test_fuga_m3.py` (nuevo) y los cambios de `tests/test_datos_m3.py`.

Criterios: legibilidad y nombres (español, estilo de `datos.py`); funciones cortas y de una sola responsabilidad; docstrings y
la ecuación comentada (Juan José la explicará en vivo en la sustentación: ¿se entiende la regla D3 leyendo `asignar_split`?);
duplicación entre `particion.py` y `datos.py`; errores claros; eficiencia razonable (1 998 filas, 1 000 destinos); pruebas que
puedan fallar de verdad, sin redundancia excesiva, con nombres que digan qué comprueban, y que no dependan del orden ni del
azar global; que las pruebas con datos reales se salten limpiamente si faltan los datos; facilidad para modificar en vivo
(p. ej. `--set particion.semilla=7`).

Entrega: APROBADO / CAMBIOS NECESARIOS, con hallazgos bloqueantes (archivo:línea, por qué, propuesta) separados de las
sugerencias menores.
