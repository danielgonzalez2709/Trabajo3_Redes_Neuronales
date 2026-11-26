# Prompt JJ-1b (R1) — revisor-spec (Sonnet) — 2026-11-25 — orquesta: Juan José

Actúa como el agente definido en `.claude/agents/revisor-spec.md` (léelo primero). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales` (rama `dev/juanjose`). Solo lees y ejecutas; **no modifiques ningún archivo**, no
hagas commit ni push. Usa `.venv\Scripts\python`.

Lee antes: `docs/spec/SPEC.md` §0, §3, §4.1, §5.7, §5.12 y §8, y del Anexo «Módulo 3 → Datos»; `docs/spec/partes/juanjose.md`
§3.1 (decisiones D1–D7 [DECIDIDO, Juan José, 25-nov]) y la fila JJ-1 de §4; el diseño pedido al implementador en
`alucinaciones/prompts/JJ-1b-implementador.md` y su respuesta en `alucinaciones/evidencias/JJ-1b/respuesta-implementador.md`.
Nada de otras partes.

## Qué revisar (tarea JJ-1, fase B)
Archivos: `configs/m3/datos.yaml`, `src/m3_recomendacion/datos.py`, `tests/test_datos_m3.py`, `tests/fixtures/m3/*`,
`data/processed/m3/*.parquet`, `results/data/m3/eda/{ficha.json,calidad.csv,diccionario.json}`, la sección M3 de
`data/fuentes.md`, la entrada `mehra2024` de `blog/references.bib`, `src/m3_recomendacion/README.md` y el cambio B7 en
`alucinaciones/evidencias/JJ-1a/redescarga_A3/` (y las referencias ajustadas en `docs/investigacion/JJ-1_verificacion_A3.md` y
`JJ-1_fuentes_m3.md` §3.2).

1. **Núcleo §5.7**: `interacciones.parquet` (`usuario_id, destino_id, calificacion, [fecha]`; sin `split`, que es de JJ-3),
   `usuarios.parquet` y `destinos.parquet` con las variables de contenido.
2. **Núcleo §5.12**: `ficha.json` con todas las claves (`validar_ficha`) y la fila M3 de la plantilla (usuarios, destinos,
   interacciones, escala, densidad, ¿real o sintético?); sección 2 (variables citadas de la fuente; faltantes) en
   `diccionario.json` y `calidad.csv`.
3. **Anexo M3 «Datos»**: número de usuarios, destinos e interacciones, escala de calificaciones, densidad, variables de usuarios
   y destinos, real o sintético según la fuente y qué implica. ¿Está todo y sale de una salida regenerable?
4. **D1–D7**, una por una: ¿se cumplen exactamente (ni más ni menos)? En particular D1 (unión implícita, `calificacion` +
   `origen`), D2 (1 000 ids + `lugar`), D3 (no se crea la partición; `VisitDate` solo descriptiva), D4 (cita literal + señales
   + conclusión), D5 (MIT + contradicción), D6 (sin `Name`, `Email` ni `ReviewText` en `data/processed/` ni en `results/`).
5. **Diseño del prompt del implementador** (B1–B7): ¿cumple cada punto? Lista las desviaciones que reportó el implementador (su
   §4) y di si alguna contradice el Spec o D1–D7. Nota del orquestador: poner `real_o_sintetico` y `licencia` como claves de
   primer nivel de la ficha (no dentro de `conteos`) fue decisión del orquestador; evalúa si contradice §5.12.
6. **Reglas**: sin internet en `src/`; config sin semillas; nada hardcodeado que debería venir de la config o de los datos;
   ninguna cifra o cita inventada (las citas deben ser subcadenas de `docs/investigacion/JJ-1_kaggle_metadata.json`).
7. Ejecuta `.venv\Scripts\python -m pytest -q tests/test_datos_m3.py` y
   `.venv\Scripts\python run.py m3-datos --config configs/m3/datos.yaml`; pega el final de cada salida.

## Entrega
Veredicto **APROBADO** o **RECHAZADO**, y la lista de hallazgos con archivo:línea, la regla incumplida (sección del Spec o
decisión D-n) y la corrección propuesta. Separa lo bloqueante de lo menor.
