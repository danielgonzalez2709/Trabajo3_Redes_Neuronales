# Prompt CA-1c — implementador (Sonnet) — 2026-11-27 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/implementador.md` (léelo primero). Repo
/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales, rama dev/camila. Python: `.venv/bin/python`.
**Prohibido `git add`, `git commit`, `git push`, `git stash`, `git checkout`.** Prueba primero.
Otra sesión edita en paralelo `alucinaciones/registro.md`, `docs/investigacion/CA-6_costos_flota.md` y `docs/MEMORIA.md`: no los toques.

## Decisión de Camila (27-nov)
La verificación CA-6 (`docs/investigacion/CA-6_verificacion.md`, fila V-7; evidencia `alucinaciones/evidencias/CA-6/
res_264_2020_mintransporte.{pdf,txt}`) encontró que la **Resolución 264 de 2020 del Ministerio de Transporte, art. 8**
(«Periodos de alta demanda para la definición de contratos») fija como periodo de alta demanda, entre otros, **del 10 de
diciembre al 15 de enero**. El calendario de CA-1 tenía `fin_de_anio` = 15-dic a 15-ene como **supuesto del equipo** «sin
definición oficial». Camila decide: **`fin_de_anio` = 10-dic a 15-ene, ambos inclusive, con la Res. 264/2020 art. 8 como
fuente** (deja de ser supuesto). No se agregan columnas para los demás periodos del art. 8.

Lee antes: `src/m1_demanda/calendario.py`, `data/externos/m1/calendario_fuentes.yaml` (bloque `fin_de_anio`),
`tests/test_calendario_m1.py`, la sección «Calendario exógeno de M1» de `data/fuentes.md`, la fila V-7 de la verificación y el
texto de la resolución en la evidencia (cita el fragmento literal del art. 8 que fija «10 de diciembre … 15 de enero»; si el
OCR no lo deja leer con certeza, detente y repórtalo en lugar de suponerlo).

## Qué hacer
1. YAML: `fin_de_anio` con `inicio_mes_dia: "12-10"`, `fin_mes_dia: "01-15"`, y la fuente (Resolución 264 de 2020 del
   Ministerio de Transporte, art. 8; URL de la copia en la evidencia; fecha de consulta 2026-11-27). Anota en la nota los límites
   que dejó la verificación: la copia es un escaneo firmado alojado en bogota.gov.co, la fecha exacta del acto no se lee en el
   OCR (`TODO(cita)`: copia del normograma de MinTransporte con fecha y vigencia) y la vigencia se infiere de que el Decreto
   1048 de 2026 la cita. Conocibilidad (regla 0.9): es de 2020 y los modelos entrenan desde 2021-06-01; dilo.
2. `calendario.py`: docstring (líneas ~20 y ~30) sin «supuesto» para `fin_de_anio`; el código ya lee el YAML.
3. Pruebas: bordes 2021-12-09 falso / 2021-12-10 verdadero / 2022-01-15 verdadero / 2022-01-16 falso; actualiza
   `test_fin_de_anio_bordes`. En `tests/test_referencia_m1.py:56` el calendario sintético usa día ≥ 15: cámbialo a ≥ 10 para
   que coincida con la regla.
4. Regenera `data/processed/m1/calendario.parquet` (`.venv/bin/python -m src.m1_demanda.calendario` o el subcomando de
   `run.py`) y reporta el SHA-256 nuevo.
5. `data/fuentes.md`, sección del calendario: fila de `fin_de_anio` con la fuente, el texto «Supuesto del equipo» fuera, la nota
   de conocibilidad, y quita ese tema de la lista de `TODO(cita)` abiertos («definición oficial de temporada alta»), dejando
   el `TODO(cita)` de la copia con fecha. Nada más de esa sección.
6. Regenera lo que consume el calendario y se versiona: las salidas de las referencias de M1 (`results/data/m1/pred_test_*.parquet`
   y `results/data/m1/referencia/presupuesto.json`, que guarda el SHA-256 del calendario) y las del descriptivo de M1
   (`results/data/m1/eda/`, si usa `fin_de_anio`). Busca los subcomandos en `run.py`. Reporta qué archivos cambiaron y cuánto
   cambian las métricas o hipótesis afectadas (p. ej. la de fin de año en `hipotesis.json`).
7. Corre `.venv/bin/python -m pytest -q` (suite completa).

Reporta: fragmento literal del art. 8 usado; diff resumido por archivo; SHA-256 nuevo; efecto en referencias y descriptivo;
salida de pytest; `TODO` nuevos.
