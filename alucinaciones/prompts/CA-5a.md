# Prompt CA-5a — implementador (Sonnet) — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/implementador.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). Python: `.venv/bin/python`
(3.12, dependencias instaladas). **Prohibido hacer `git commit`, `git push` o cualquier operación que cambie el historial:
Camila revisa todo antes.** Otros agentes revisan en paralelo (solo lectura) `calendario.py`, `operacion.py` y `eda.py`: no
toques esos archivos.

Lee: `docs/spec/SPEC.md` §0, §3, §4.1, §5.1, §5.2, §5.3 (protocolo `Pronosticador` y **reglas contra fuga 1–4**), §5.9, §6
(comparación justa) y el Anexo («Módulo 1 → Tareas 5, 7 y 8», «Regla de comparación justa»); `docs/spec/partes/camila.md` §3.0
y §3.5; `docs/MEMORIA.md` («Avisos para el equipo» de M1); `results/data/m1/eda/implicaciones.json` y `hipotesis.json`
(descriptivo de CA-4: Semana Santa y diciembre son los efectos más fuertes, estacionalidad semanal moderada, cambio de régimen
del tránsito en 11001-15759 desde nov-2022); `src/comun/config.py`, `src/comun/results.py`, `src/comun/seeds.py`.
Datos: `data/processed/m1/demanda_diaria.parquet` y `data/processed/m1/calendario.parquet` (CA-1, esquema en
`data/fuentes.md`, sección «Calendario exógeno de M1»).

## Tarea CA-5: modelos de referencia de M1
Archivos tuyos (solo estos): `src/m1_demanda/referencia.py`, `configs/m1/referencia.yaml`, `tests/test_referencia_m1.py` y
salidas en `results/data/m1/` (`pred_test_<modelo>.parquet`) y `results/data/m1/referencia/`.

**Situación:** el arnés común `evaluar_origen_rodante` y las métricas (AN-1, Andrés) **aún no existen**. Implementa los modelos
contra el protocolo `Pronosticador` del §5.3 tal cual, para que el arnés de Andrés los evalúe sin cambios cuando llegue. No
implementes el arnés ni `metricas.py` (son de Andrés).

1. **Ingenuo estacional** (`nombre = "ingenuo_estacional"`): para el origen t₀ y el horizonte h, el pronóstico es el valor
   observado del mismo día de la semana en la última semana con dato **≤ t₀** (p. ej. y(t₀+h−7k) con el menor k tal que
   t₀+h−7k ≤ t₀). Cuantiles: cuantiles empíricos de los errores del propio método en train, por ruta y por tramo de horizonte
   (1–7, 8–14, 15–30), sumados al punto y truncados en 0. Justifícalo en el docstring.
2. **Regresión lineal con rezagos y calendario** (`nombre = "regresion_calendario"`) [DECIDIDO por Camila, 26-nov, como el
   modelo estadístico del enunciado, tarea 5]: un modelo **directo** por ruta sobre log1p(pasajeros) cuyas variables, para la
   fecha objetivo t₀+h, son solo información conocible en t₀: (a) resúmenes de la serie **hasta t₀** (p. ej. media de los
   últimos 7 y 28 días, media del mismo día de la semana en las últimas 4 semanas), (b) variables del calendario de la fecha
   objetivo (`dia_semana` en dummies, `festivo`, `puente`, `semana_santa`, `jueves_viernes_santo`, `fin_de_anio`, vacaciones
   escolares de la ciudad de origen de la ruta: `vacaciones_escolares_<origen_divipola>`), y (c) `h` (o tramos de h). Mínimos
   cuadrados (sklearn `LinearRegression` o `Ridge` con α fijo en config; sin búsqueda, o si la haces cuéntala). Cuantiles:
   cuantiles empíricos de los residuos de train por tramo de horizonte, en escala log, retransformados (documenta el sesgo de la
   retransformación). Nulos del calendario: decide y documenta (los modelos entrenan desde 2021-06-01, donde no hay nulos
   salvo Sogamoso 2024, fuera del periodo).
3. **Reglas contra fuga (§5.3), cada una con prueba**: lista blanca de columnas (`ruta_id, fecha, pasajeros` + calendario;
   nunca `anomalo`, `sin_registro`, `despachos`); `inicio_entrenamiento = 2021-06-01` también para las ventanas;
   `pronosticar(origen)` usa solo observaciones con fecha ≤ origen (prueba: cambiar todos los valores posteriores al origen no
   cambia el pronóstico); parámetros (coeficientes, cuantiles de residuos) estimados solo con fechas ≤ `fin_entrenamiento`
   (clave de config, [PROPUESTO] `2022-12-31`, igual que `configs/m1/operacion.yaml`, a alinear con AN-1); días `sin_registro`
   excluidos de la estimación. Ambigüedad del protocolo: `ajustar(serie, calendario)` recibe la serie y `pronosticar` no; guarda
   la historia en el objeto y filtra por origen. Repórtalo para que Camila lo acuerde con Andrés.
4. **`main(cfg)`** ejecutable como `python -m src.m1_demanda.referencia --config configs/m1/referencia.yaml` (no hay subcomando
   en `run.py`; no lo toques): imprime la config resuelta; rejilla de orígenes según §5.3 regla 4 (último origen 2023-12-01 y los
   demás cada 7 días hacia atrás; número de orígenes en config, [PROPUESTO], ningún origen < `fin_entrenamiento`); escribe
   `results/data/m1/pred_test_<modelo>.parquet` con las columnas exactas del §5.3 (`origen, ruta_id, fecha, h, y, punto, q0.5,
   q0.75, q0.9, q0.95`; `y` = observado, para que el arnés lo consuma) y `results/data/m1/referencia/presupuesto.json` con, por
   modelo, `n_parametros` (estimados), `n_configuraciones_busqueda`, `tiempo_total_s`, `device: cpu` y `evidencia` (SHA-256 de
   `demanda_diaria.parquet` y `calendario.parquet`) — núcleo §5.9 y §6. Debe correr en < 2 min en CPU, sin internet.
5. **Pruebas primero** (`tests/test_referencia_m1.py`) con la serie sintética (`data/sintetico/m1/demanda_diaria.parquet`) o
   fixtures pequeños: ingenuo estacional con un caso a mano; columnas y `h` 1..30; cuantiles monótonos (q0.5 ≤ q0.75 ≤ q0.9 ≤
   q0.95) y ≥ 0; las pruebas de fuga del punto 3; `main` con una config pequeña.
6. Para el reporte (no como resultado oficial): MAE por modelo y ruta sobre la rejilla, calculado en un script desechable en
   `/private/tmp/claude-501/-Users-softwaresolenium-CoursesExercises-Trabajo3-Redes-Neuronales/98577556-2e6f-4e02-a506-be57e6ccb0ee/scratchpad/`.

## Aceptación (spec de Camila, CA-5)
Ambos modelos implementan el protocolo §5.3 y están listos para el arnés común; `pred_test_*.parquet` con el esquema del §5.3;
presupuesto y parámetros registrados; pruebas de fuga; suite completa pasa (`.venv/bin/python -m pytest -q`).

## Reglas
Prueba primero. Nada de internet. Prohibido inventar datos o citas (`TODO(cita)`). No toques archivos fuera de los tuyos (ni
`src/comun/`, `run.py`, el Spec, `operacion.py`, `eda.py`, `calendario.py`). Nada de commits. Reporta al final: archivos,
salida real de pytest y de `main`, MAE provisional, decisiones [PROPUESTO] para Camila y la ambigüedad del protocolo.
