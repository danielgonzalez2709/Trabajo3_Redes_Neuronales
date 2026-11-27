# Prompt CA-3b — implementador-experto (Opus) — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/implementador-experto.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). Python: `.venv/bin/python`.
**Prohibido hacer `git commit`, `git push` o cualquier operación que cambie el historial: Camila revisa todo antes.**
Otro agente trabaja en paralelo en `calendario.py`, `data/externos/`, `data/fuentes.md` y `docs/investigacion/`: no los toques.

Lee: `docs/spec/SPEC.md` §0, §3, §4.1, §5.1, §5.4 y el Anexo («Módulo 1 → Preguntas de negocio 1 y 2», «Limitaciones»,
«Fundamentación matemática»); `docs/spec/partes/camila.md` §3.2, §3.3; el prompt original `alucinaciones/prompts/CA-3a.md`;
y los tres informes de revisión, que son la base de esta ronda:
- `docs/investigacion/CA-2_verificacion.md` (cazador-alucinaciones: normas confirmadas y citas exactas, §7 y §9),
- el reporte del verificador matemático, resumido abajo (fórmula (5') y calibración),
- el reporte de los revisores, resumido abajo.

## Tarea CA-3 (ronda 2): corregir el modelo de dimensionamiento
Archivos tuyos (solo estos): `src/m1_demanda/operacion.py`, `configs/m1/operacion.yaml`, `tests/test_operacion_m1.py`,
salidas en `results/data/m1/operacion/`. Prueba primero: cada cambio de fórmula con un caso a mano en el comentario.

**Decisiones de Camila (26-nov), obligatorias. Ya no hay banderas opcionales: todo lo de abajo es la fórmula base.**
1. **Conductores (5')**, reemplaza la ec. (5) actual (el verificador la rechazó: veh·H cuenta horas de disponibilidad, no de
   trabajo, y no es monótona en H; contraejemplo: 1 despacho por sentido, T = 4 h, H = 18 → 3 conductores cuando basta 1):
   - en servicio, por corredor {r, r'} y día: C_serv = ⌈ k_r · (n_r + n_r') · t_r / J_ef ⌉ (t_r = horas de recorrido por
     sentido; documenta si el alistamiento cuenta como trabajo y por qué);
   - equivalente de nómina: C_nom = ⌈ C_serv / (1 − a) · 7 / (7 − s) ⌉ con **s = 1** (descanso semanal obligatorio);
   - salida con las dos columnas, `conductores_servicio` y `conductores` (= nómina; es la que pide §5.4).
2. **Segundo conductor por norma**: k_r = 2 si t_r > 8 h (Res. 315/2013 art. 6, confirmada vigente por el cazador); si no, 1.
   Además, error claro si t_r / k_r supera la jornada máxima diaria (un conductor no puede cubrir la pierna).
3. **Vueltas = H / T_ciclo** (fracción, sin piso ni mínimo de 1) en todas las rutas; veh = ⌈ max(n_r, n_r') / v_r ⌉.
   Quitar `vueltas_fraccionarias`, `segundo_conductor_activo` y la regla de mínimo 1 vuelta.
4. **Calibración con train**:
   - `fraccion_demanda_en_origen` (f) **se calcula al ejecutar** con train (no escrita a mano), con los **últimos meses de
     train** para captar el régimen reciente (clave de config `calibracion.meses_fraccion`, [PROPUESTO] 2; el verificador midió
     que en 11001-15759 f cae de 0,417 a 0,31 desde el 8-nov-2022 y a 0,273 en 2023). El YAML ya no lleva el valor por ruta.
   - **Capacidad física supuesta** por clase: el máximo observado de pasajeros por despacho ORIGEN en train, recortado al rango
     del Decreto 171/2001 arts. 50–51, hoy **compilados como arts. 2.2.1.4.7.3 y 2.2.1.4.7.4 del Decreto 1079 de 2015** (cita
     exacta en `CA-2_verificacion.md`). `supuesto: true` (la norma da rangos, no capacidades).
   - **Ocupación objetivo ρ calibrada en train**: ρ* = Σ f·D / κ̄ ÷ Σ despachos ORIGEN observados (ventana de train). Mantén
     `operacion.ocupacion_objetivo` como hoja escalar sobreescribible con `--set` (núcleo §4.1, control de la app); su valor por
     defecto = ρ* redondeado, con una prueba que lo ate a los datos (como ya existe para las capacidades). Reporta cuánto
     despacho observado reproduce el modelo con ρ* (antes: 46–81 %).
5. **Fuentes que pasan de supuesto a `fuente`** (citas exactas del §7 de `CA-2_verificacion.md`; no inventes ninguna):
   `jornada_max_diaria_h = 8` (Ley 2466/2025 art. 11, nota: rige desde el 25-jun-2025); `umbral_segundo_conductor_h = 8`
   (Res. 315/2013 art. 6); `dias_descanso_semana = 1` (CST, cita del informe); nueva `jornada_max_semanal_h = 42` (Ley 2101/2021,
   cronograma; 42 h desde el 15-jul-2026). Comprueba y prueba que J_ef · (7 − s) ≤ jornada_max_semanal_h.
6. **Costos** (`costo_pasajero_sin_atender`, `costo_vehiculo_dia_sobrante`): se quedan (§5.4 los exige; los usa negocio 3 / CA-6),
   pero la nota debe decir que `dimensionar` no los usa.

**Correcciones de los revisores:**
- Flota por corredor: las filas r y r' repiten vehículos y conductores; agrega una salida o columna que evite que alguien los sume
  dos veces (p. ej. `corredor` y una tabla por corredor y día).
- `demanda_ejemplo` debe excluir días `sin_registro` y validar inicio y fin de la ventana de train (prueba).
- `cuantil` debe estar en {0.5, 0.75, 0.9, 0.95} (§5.3), con error claro.
- La prueba que exige `supuesto: true` en todo → exigir solo «`fuente` XOR `supuesto`».
- Renombrar `test_dimensionar_cuantil_mayor_nunca_pide_menos` → `test_flota_monotona_en_la_demanda`.
- División por cero en `fraccion_pasajeros_origen` si una ruta no tiene pasajeros en train → error claro + prueba.
- Quitar anclas/alias YAML en `meta` si complican explicarlo en vivo; corregir el docstring que dice «el Spec fija 1».
- `main`: renombrar la variable `d`, separar escritura de salidas, sin `insert` en posición mágica.
- Encabezado de `operacion.py`: ecuaciones (1)–(5') actualizadas, en el mismo orden que el blog usará.

Verifica: `.venv/bin/python -m pytest -q` y
`.venv/bin/python run.py m1-operacion --config configs/m1/operacion.yaml --set operacion.ocupacion_objetivo=0.8 --set operacion.cuantil=0.9`;
al final vuelve a correr el comando **sin** `--set` para que `results/data/m1/operacion/` quede con la config por defecto.

## Reporte
Archivos; salida real de pytest y del comando; tabla antes/después del máximo diario por corredor (vehículos, conductores en
servicio, nómina); ρ*, f por ruta y capacidades calculadas; qué % de los despachos ORIGEN observados reproduce el modelo; decisiones
[PROPUESTO] que queden. Nada de commits.
