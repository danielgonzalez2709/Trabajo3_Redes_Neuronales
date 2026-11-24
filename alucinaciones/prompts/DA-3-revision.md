# Prompts de revisión de DA-3/DA-4 — 2026-11-24 — orquesta: Daniel

Repositorio: `C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales`, rama `dev/daniel` (último commit:
«DA-3/DA-4: series reales de M1…»). Prompts de implementación: `alucinaciones/prompts/DA-3a.md` y `DA-3b.md`.
Archivos bajo revisión: `scripts/descargar_m1.py`, `src/m1_demanda/datos.py`, `configs/m1/datos.yaml`,
`tests/test_datos_m1.py`, `tests/test_descargar_m1.py`, `data/processed/m1/*`, `results/data/m1/eda/*`, `data/fuentes.md`.
Los datos crudos están en `data/raw/m1/` (no versionados). **Ningún revisor modifica archivos del repo.**

## R1 — revisor-spec (Sonnet)
Actúa como el agente definido en `.claude/agents/revisor-spec.md` (léelo primero). Revisa contra `docs/spec/SPEC.md` §0, §4.1,
§5.1 (v0.3), §5.12, §8, el Anexo («Módulo 1 → Datos» y tarea 2) y `docs/spec/partes/daniel.md` §3.2 y filas DA-3 y DA-4.
En particular: esquema exacto de §5.1 (nombres, tipos —¿`fecha` como date?—, sin huecos, 6 rutas decididas, periodo),
`demanda_detalle` y su suma = serie, `rutas.yaml` con `ruta_regreso_id`, `resumen_datos.json` y `ficha.json` según §5.12, que el
Anexo quede cubierto (registros y variables, periodo, rutas, significado citado del diccionario, inconsistencias, agregación,
días sin registro, anómalos), y nada añadido sin justificar (p. ej. `marcas_anomalos.parquet`). Ejecuta pytest y
`.venv\Scripts\python run.py m1-datos --config configs/m1/datos.yaml`. Salida: APROBADO o RECHAZADO + hallazgos.

## R2 — auditor-fugas (Opus)
Actúa como el agente definido en `.claude/agents/auditor-fugas.md` (léelo primero). Alcance: M1, los datos que reciben Camila y
Andrés. Revisa: las marcas `anomalo` (ventana centrada y MAD sobre la serie completa: ¿está bien aislado que no entren a los
modelos?, ¿qué pasa si alguien filtra el entrenamiento con ellas?), la imputación de `sin_registro` como 0 y su efecto en
rezagos y en la escala de MASE, cualquier columna de `demanda_diaria` o del detalle que no sea conocible 30 días antes del día
pronosticado, y el cambio de composición de tránsito en 11001-15759 desde nov-2022 frente a la partición temporal (test en el
segundo semestre de 2023). Escribe las pruebas que hagan falta solo en un archivo temporal fuera del repo y reporta su salida.
Salida: tabla riesgo | evidencia | veredicto | recomendación para Camila y Andrés (y si debe ir al Spec).

## R3 — revisor-calidad (Haiku)
Actúa como el agente definido en `.claude/agents/revisor-calidad.md` (léelo primero). Revisa `src/m1_demanda/datos.py`,
`scripts/descargar_m1.py` y sus pruebas, priorizando lo que Daniel tendrá que explicar en vivo (reglas de anómalos y
`sin_registro`). Salida: APROBADO o CAMBIOS REQUERIDOS con archivo:línea.
