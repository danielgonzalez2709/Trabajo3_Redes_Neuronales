# Prompt JJ-1b (R2) — revisor-calidad (Haiku) — 2026-11-25 — orquesta: Juan José

Actúa como el agente definido en `.claude/agents/revisor-calidad.md` (léelo primero). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales` (rama `dev/juanjose`). Solo lees y ejecutas; **no modifiques ningún archivo**, no
hagas commit ni push. Usa `.venv\Scripts\python`.

Contexto: tarea JJ-1 fase B (datos de M3), ya **APROBADA por el revisor-spec**. Lee `docs/spec/partes/juanjose.md` §3.1
(decisiones D1–D7) y `docs/spec/SPEC.md` §5.7 y §5.12 solo para entender qué hace el código. Nada de otras partes.

Revisa la calidad de: `src/m3_recomendacion/datos.py`, `tests/test_datos_m3.py`, `tests/fixtures/m3/*` y
`configs/m3/datos.yaml`. Compara el estilo con `src/m1_demanda/datos.py` y `tests/test_datos_m1.py` (el código debe leerse
como el del resto del repo).

Criterios:
1. Legibilidad: nombres, funciones cortas con una sola responsabilidad, docstrings útiles, comentarios donde el porqué no es
   obvio. Juan José debe poder explicar y modificar el código en vivo en la sustentación.
2. Estructura: separación entre lectura/verificación, construcción de tablas, ficha/diccionario y escritura; nada duplicado sin
   necesidad; nada hardcodeado que debería estar en la config.
3. Pruebas: ¿cubren los casos importantes y los errores? ¿Son legibles (una idea por prueba, nombres como frase)? ¿Los
   fixtures son pequeños y claramente ficticios? ¿Hay pruebas frágiles o redundantes?
4. Eficiencia: debe tardar < 10 s (mídelo con `run.py m3-datos --config configs/m3/datos.yaml`).
5. Corre `.venv\Scripts\python -m pytest -q tests/test_datos_m3.py`.

Entrega: veredicto **APROBADO** o **RECHAZADO**; hallazgos con archivo:línea, por qué importa y la corrección concreta;
separa lo que hay que corregir de lo opcional.
