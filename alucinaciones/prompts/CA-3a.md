# Prompt CA-3a — implementador-experto (Opus) — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/implementador-experto.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). Python: `.venv/bin/python`
(3.12, dependencias ya instaladas). **Prohibido hacer `git commit`, `git push` o cualquier operación que cambie el historial:
Camila revisa todo antes. Deja los cambios en el árbol de trabajo.**

Lee: `docs/spec/SPEC.md` §0, §3, §4.1 y §5.1, §5.4 (contrato que produces) y el Anexo («Módulo 1 → Preguntas de negocio 1 y 2»,
«Limitaciones», «Fundamentación matemática» —modelo de dimensionamiento—); `docs/spec/partes/camila.md` §3.0, §3.2, §3.3 y §5;
`docs/investigacion/CA-2_normativa_operacion.md` (informe de fuentes, aún **sin verificar** por el cazador-alucinaciones);
`app/lib/contratos.ts` (`ParametrosOperacion`, `OperacionJson`, `validarOperacion`, `CasoOperacion`) y
`app/tests/fixtures/juguete/m1/operacion.json` + `app/lib/dimensionar.ts` (juguete, solo como referencia de forma);
`src/comun/config.py` (`load_config`, `apply_overrides`) y `src/comun/cli.py` (cómo `run.py m1-operacion` llama `main(cfg)`).

## Tarea CA-3 🧠: `dimensionar()` y conductores
Archivos tuyos (solo estos): `src/m1_demanda/operacion.py`, `configs/m1/operacion.yaml`, `tests/test_operacion_m1.py`.

1. **Prueba primero** (`tests/test_operacion_m1.py`), con casos hechos a mano (cuentas escritas en el comentario de cada
   prueba) que cubran: techo de despachos; vueltas con `floor`; que los vehículos usen el **máximo de los dos sentidos**
   (ida y regreso de la misma fecha); conductores con jornada efectiva y ausentismo; capacidad efectiva ponderada por la
   composición de clases; que la composición por clase se estime **solo con despachos de ORIGEN hasta la fecha de fin de
   entrenamiento** (núcleo §5.4: nada posterior); bordes (demanda 0, parámetros fuera de rango → error claro); y que
   `python run.py m1-operacion --config configs/m1/operacion.yaml --set operacion.ocupacion_objetivo=0.8 --set
   operacion.cuantil=0.9` funcione tal cual (núcleo §4.1).
2. **Fórmula de partida** (spec de Camila §3.3, [PROPUESTO]):
   - capacidad_efectiva(r) = Σ_c composición(r, c) · capacidad(c)
   - despachos(r, d) = ⌈ D(r, d) / (capacidad_efectiva(r) · ocupación_objetivo) ⌉
   - vueltas(r) = ⌊ horas_operación / tiempo_ciclo(r) ⌋, ciclo = ida **y** regreso (mínimo 1; si el ciclo excede las horas,
     documenta qué pasa en vez de esconderlo)
   - vehículos(r, d) = ⌈ max(despachos ida, despachos regreso) / vueltas(r) ⌉ (el par se toma de `ruta_regreso_id` en
     `data/processed/m1/rutas.yaml`)
   - conductores(r, d) = ⌈ vehículos · horas_operación / jornada_efectiva · 1/(1 − ausentismo) ⌉
   Si encuentras un error o un término mal definido en esta fórmula (unidades, doble conteo de ida y regreso, la Res. 315/2013
   art. 6 de segundo conductor en recorridos > 8 h según el informe CA-2), **no la cambies en silencio**: implementa la
   versión de arriba, deja un parámetro desactivado por defecto si hace falta (p. ej. `conductores_por_vehiculo` o regla de
   segundo conductor) y explica la propuesta en tu reporte para que Camila decida.
3. **`configs/m1/operacion.yaml`**: el cargador rechaza `--set` sobre un bloque, así que `operacion.ocupacion_objetivo` y
   `operacion.cuantil` deben ser hojas escalares. Diseña el YAML para que (a) los valores de uso sean escalares sobreescribibles
   con `--set` y (b) cada parámetro tenga `unidad` y `fuente` **o** `supuesto: true` (+ `nota`), de modo que la futura
   exportación a `app/public/model/m1/operacion.json` (núcleo §5.4, `globales`, `por_ruta`, `por_clase`, `composicion_clases`)
   sea mecánica. **Todos los valores van primero como `supuesto: true`** (spec §2: «primero con valores marcados como
   supuesto»); en la `nota` referencia el apartado del informe CA-2 que los respalda o la razón del supuesto. No inventes citas:
   donde el informe tiene `TODO(cita)`, déjalo en la nota. Capacidades: las clases que aparecen en
   `data/processed/m1/demanda_detalle.parquet` (BUS, MICROBUS, BUSETA, CAMPERO, CAMIONETA, AUTOMOVIL); cada valor supuesto dentro
   del rango del Decreto 171/2001 citado en el informe, justificado con los pasajeros por despacho observados (percentil alto por
   clase en los despachos de ORIGEN; calcúlalo y escríbelo en la nota). La fecha de fin de entrenamiento para la composición es
   una clave de configuración; Andrés aún no publica su partición (AN-1): usa un valor marcado [PROPUESTO] ≤ 2023-01-01 y
   escálalo en el reporte.
4. **`dimensionar(demanda: pd.DataFrame, params: dict) -> pd.DataFrame`** (núcleo §5.4): entrada `ruta_id, fecha, demanda`
   (punto o cuantil); salida + `despachos, vehiculos, conductores` y, si sirve para la paridad, columnas de pasos intermedios.
   Funciones puras, pequeñas y explicables en la sustentación. Una función aparte estima la composición con train.
   `main(cfg)` imprime la config resuelta y, mientras no existan pronósticos reales (AN-5, sáb 28), dimensiona una demanda de
   ejemplo **claramente marcada como tal** (p. ej. la serie real de un mes de train) y escribe en `results/data/m1/operacion/`.
   Nada de internet.
5. **Contrato con la app**: `casos_paridad[].entrada` del contrato trae **una sola** `demanda` por ruta y fecha, pero la
   fórmula usa ida y regreso. No cambies `app/` ni el contrato: describe en el reporte la tensión y una propuesta concreta
   (p. ej. agregar `demanda_regreso` al caso) para que Camila la lleve a Daniel.

## Aceptación
Pruebas con casos a mano pasan (`.venv/bin/python -m pytest tests/test_operacion_m1.py -q` y la suite completa sin romper nada);
usa ida y regreso; el comando de §4.1 corre; todo parámetro con `unidad` y `fuente` o `supuesto: true`.

## Reglas
Prueba primero. Prohibido inventar normas, cifras o citas (`TODO(cita)` / `TODO(dato-faltante)`). No toques archivos fuera de
los tres tuyos (ni `src/comun/`, `run.py`, `app/`, el Spec). Nada de commits. Reporta al final: archivos creados, salida real
de pytest y del comando, decisiones [PROPUESTO] que debe tomar Camila y errores que hayas detectado en la fórmula o el informe.
