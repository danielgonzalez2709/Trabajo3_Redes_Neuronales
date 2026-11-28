# Prompt CA-12b — implementador (Sonnet) — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/implementador.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). Python: `.venv/bin/python`.
**Prohibido hacer `git commit`, `git push` o cualquier operación que cambie el historial: Camila revisa todo antes.**
Otro agente trabaja en paralelo en `operacion.py`, `configs/m1/operacion.yaml` y `tests/test_operacion_m1.py`: no los toques.

Lee: `docs/spec/SPEC.md` §0, §5.2 y §9; `docs/spec/partes/camila.md` §3.1–§3.2; los prompts `alucinaciones/prompts/CA-1b.md`
(decisiones de Camila del calendario) y los dos informes de verificación del cazador-alucinaciones:
`docs/investigacion/CA-1_verificacion.md` y `docs/investigacion/CA-2_verificacion.md` (sus secciones de correcciones).

## Tarea: aplicar las correcciones de las verificaciones de CA-1 y CA-2
Archivos tuyos (solo estos): `data/externos/m1/calendario_fuentes.yaml`, `src/m1_demanda/calendario.py`,
`tests/test_calendario_m1.py`, `data/processed/m1/calendario.parquet` (regenerado), la sección «Calendario exógeno de M1» de
`data/fuentes.md`, y una sección nueva «Fe de erratas» al **inicio** de `docs/investigacion/CA-1_fuentes_calendario.md` y de
`docs/investigacion/CA-2_normativa_operacion.md`.

**Regla importante:** los informes CA-1 y CA-2 los generó una IA y sus errores son evidencia para la cacería de alucinaciones.
**No reescribas ni borres su texto original**: agrega solo la «Fe de erratas» arriba, con cada corrección, la sección afectada y
el enlace a la verificación que la sustenta.

**CA-1 (calendario):**
1. Quitar la supuesta «contradicción» del Decreto 333/2021 de Sogamoso de la nota del YAML y de «Discrepancias entre fuentes» en
   `data/fuentes.md` (los semestres incluyen recesos; ver `CA-1_verificacion.md`).
2. `data/fuentes.md`: explicar las fechas 6-dic (firma) / 22-dic (sanción) de la Ley 51/1983; corregir la descripción de la
   Res. 0002/2021 de Cali (desarrollo institucional, no vacaciones docentes); cerrar los `TODO(cita)` del ponente de la C-107/94 y
   de la C-568/93 con lo verificado; matizar la frase general «expedidos antes del 1-nov del año anterior» con las excepciones
   que el mismo archivo documenta (Pasto 2021 y 2022, Ipiales 2021, Cali 2023).
3. **1-ene-2024 de Pasto e Ipiales**: ningún acto lo cubre → **nulo**, por la regla de vacíos sin fuente de Camila (CA-1b, decisión
   5). Ajusta el código o el YAML para que un día fuera de toda cobertura documentada quede nulo, y prueba ese caso.
4. **Cali 2023**: anotar en el YAML y en `data/fuentes.md` la contradicción interna del afiche (30-ene como receso y como primer día
   de clases; 39 semanas lectivas; semana del 26-jun al 2-jul sin rótulo). **No cambies el valor** del 2023-01-30: déjalo como está y
   márcalo como decisión pendiente de Camila en tu reporte.
5. Fe de erratas del informe CA-1: lo anterior, la descripción de la Res. 0002 y el rango faltante `sogamoso,2022-01-17,2022-01-23` de
   la tabla §3.3.

**CA-2 (normativa), solo Fe de erratas del informe** (el YAML de operación lo corrige otro agente):
correcciones C-1 a C-9 de `CA-2_verificacion.md`: en especial 46 → **47 h** el 7-may-2024 (§6.1 del informe), base legal 2021–2025
(el art. 161 CST según la Ley 50/1990 fue sustituido por la Ley 2101 el 15-jul-2021), título literal de la Ley 2466/2025, cita del
Decreto 171/2001 compilado en el Decreto 1079/2015 (arts. 2.2.1.4.7.3 y 2.2.1.4.7.4) y los `TODO` que quedaron cerrados.

Regenera con `.venv/bin/python -m src.m1_demanda.calendario` y corre `.venv/bin/python -m pytest -q`. Reporta: archivos, salida real,
qué celdas del parquet cambiaron (debería ser solo 1-ene-2024 de 52001 y 52356) y el nuevo SHA-256 del parquet. Nada de commits.
