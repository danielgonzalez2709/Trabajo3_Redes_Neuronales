# Prompt CA-3-verificacion-2 — verificador-matematico (Opus) — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/verificador-matematico.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). Python: `.venv/bin/python`.
**Solo lectura: no edites archivos del repo, no hagas `git commit` ni `git push`.** Scripts en `/tmp/verif_ca3b/`.

Segunda verificación de CA-3 tras dos rondas de correcciones. Tu verificación anterior (rechazo de la ec. (5) por veh·H, descanso
semanal, mínimo de 1 vuelta, calibración) originó estos cambios (prompts literales `alucinaciones/prompts/CA-3b.md` y `CA-3c.md`):
conductores por piernas — P = 2·max(desp_r, desp_r'), h = t/k con k = 2 si t > 8 h (Res. 315/2013 art. 6), L = max(1, ⌊J_ef/h⌋),
C_serv = ⌈k·P/L⌉, nómina = ⌈C_serv/(1−a)·7/(7−s)⌉ con s = 1; vueltas = H/T (fracción); f por ruta con los últimos 2 meses de train;
capacidad = máximo observado recortado al rango del Decreto 1079/2015; ρ* calibrado en la ventana de f (0,61).

Contexto: `docs/spec/SPEC.md` §5.1, §5.4 y el Anexo («Módulo 1 → Preguntas de negocio 1 y 2», «Limitaciones», «Fundamentación
matemática»); `docs/spec/partes/camila.md` §3.3; código `src/m1_demanda/operacion.py` (ecuaciones en el encabezado),
`configs/m1/operacion.yaml`, `tests/test_operacion_m1.py`, `results/data/m1/operacion/`; normas confirmadas en
`docs/investigacion/CA-2_verificacion.md`.

Tarea: (1) deriva de nuevo y compara término a término con el código, con casos a mano y una fila real; (2) ¿la cuenta por piernas es
coherente con la ec. (4) de vehículos y con la ley (jornada diaria 8 h, semanal 42 h, descanso, segundo conductor)? Evalúa el
supuesto «el relevo a bordo no consume jornada»; (3) ¿la calibración de ρ* y f tiene sesgos o fugas? cuantifica el desajuste por ruta
(46 %–134 % de despachos ORIGEN reproducidos); (4) sensibilidad ±10 % de demanda y del parámetro más influyente (negocio 1), con
elasticidades; (5) derivación LaTeX final lista para el blog. Veredicto APROBADO / APROBADO CON OBSERVACIONES / RECHAZADO, cada
error con archivo:línea, contraejemplo y corrección; candidatos a hallazgo (Matemáticas) solo si un error vino de una IA.
