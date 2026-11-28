# Prompt CA-5-revision — revisor-spec (Sonnet), revisor-calidad y auditor-fugas (Opus) — 2026-11-26 — orquesta: Camila

(Mismo texto para los tres agentes; cada uno aplica su propio rol definido en `.claude/agents/<rol>.md`, que debe leer primero.)

Repositorio: `/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). Python: `.venv/bin/python`.
**Solo lectura sobre el código: no edites archivos del repositorio (salvo el auditor-fugas, que puede proponer una prueba en su
reporte pero NO escribirla), no hagas `git commit` ni `git push`.** Otro agente modifica en paralelo `operacion.py`: no lo revises.

Contexto: `docs/spec/SPEC.md` §0, §3, §4.1, §5.1, §5.2, §5.3 (protocolo `Pronosticador` y reglas contra fuga 1–5), §5.9, §6 y el
Anexo («Módulo 1 → Tareas 1, 5 y 8», «Regla de comparación justa»); `docs/spec/partes/camila.md` §3.5; prompt de la tarea
`alucinaciones/prompts/CA-5a.md` (decisión de Camila: el modelo estadístico es una regresión lineal con rezagos y calendario).

Tarea CA-5 a revisar: `src/m1_demanda/referencia.py`, `configs/m1/referencia.yaml`, `tests/test_referencia_m1.py`,
`results/data/m1/pred_test_ingenuo_estacional.parquet`, `results/data/m1/pred_test_regresion_calendario.parquet`,
`results/data/m1/referencia/presupuesto.json`. Datos: `data/processed/m1/demanda_diaria.parquet` y
`data/processed/m1/calendario.parquet`. El arnés común de Andrés (AN-1) aún no existe; los modelos implementan el protocolo §5.3.

- **revisor-spec:** ¿cumple exactamente §5.3 (firma, columnas de salida, cuantiles), §5.9/§6 (presupuesto, `n_parametros`,
  evidencia) y el enunciado (ingenuo estacional + modelo estadístico o lineal)? Nada de más, nada de menos. Veredicto.
- **revisor-calidad:** legibilidad, funciones pequeñas, pruebas que prueban comportamiento, constantes en config, facilidad para
  explicar en vivo. `archivo:línea`, severidad, arreglo. Veredicto.
- **auditor-fugas:** auditoría adversarial: ¿alguna variable no conocible 30 días antes / en el origen? ¿estadísticos, cuantiles de
  residuos o coeficientes estimados con datos > `fin_entrenamiento`? ¿ventanas que miran al futuro? ¿`sin_registro`/`anomalo`
  usados como entrada (la máscara de `sin_registro` es una excepción declarada; juzga si es legítima)? ¿calendario con
  información posterior (p. ej. resoluciones escolares modificadas)? ¿la rejilla de orígenes respeta §5.3 regla 4? Demuéstralo con
  experimentos (scripts fuera del repo, en `/tmp`) y propón la prueba que lo demostraría. Veredicto: SIN FUGA / FUGA.

Corre `.venv/bin/python -m pytest tests/test_referencia_m1.py -q` y
`.venv/bin/python -m src.m1_demanda.referencia --config configs/m1/referencia.yaml` y reporta la salida real.
