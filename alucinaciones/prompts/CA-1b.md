# Prompt CA-1b — implementador (Sonnet) — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/implementador.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). Python: `.venv/bin/python`
(3.12, dependencias ya instaladas). **Prohibido hacer `git commit`, `git push` o cualquier operación que cambie el historial:
Camila revisa todo antes. Deja los cambios en el árbol de trabajo.**

Lee: `docs/spec/SPEC.md` §0, §3, §4.1, §5.1 y §5.2 (contrato que produces) y el Anexo («Módulo 1 → Tareas 1 y 4»);
`docs/spec/partes/camila.md` §3.1 y §5; **`docs/investigacion/CA-1_fuentes_calendario.md`** (fuente de todas las fechas:
transcríbelas de ahí, nunca de memoria); `data/fuentes.md` (formato de las secciones existentes); `data/processed/m1/rutas.yaml`.
Otros agentes trabajan en paralelo en `src/m1_demanda/eda.py`, `src/m1_demanda/operacion.py`, `src/viz/figs_m1_datos.py` y sus
pruebas: no los toques.

## Tarea CA-1: calendario exógeno de M1
Archivos tuyos (solo estos): `src/m1_demanda/calendario.py`, `tests/test_calendario_m1.py`, `data/externos/m1/calendario_fuentes.yaml`
(nuevo: tablas transcritas del informe, con la cita de cada bloque), `data/processed/m1/calendario.parquet` (salida) y una nueva
sección «Calendario exógeno de M1» en `data/fuentes.md` (solo agregar; no edites las secciones de Daniel).

**Decisiones de Camila (26-nov), obligatorias:**
1. **Vacaciones escolares: una columna por ciudad** `vacaciones_escolares_11001`, `_76001`, `_15759`, `_52001`, `_52356`
   (calendario A de cada secretaría certificada, tabla del informe) **más** `vacaciones_escolares` = la de Bogotá (11001) por
   compatibilidad con §5.2. Para Pasto, el informe trata como sin clases todo lo que no es «Desarrollo Académico» (no literal):
   respétalo y documéntalo como supuesto.
2. **Versión original** de cada calendario escolar (la conocible 30 días antes); las modificaciones posteriores quedan solo
   documentadas en `data/fuentes.md`.
3. **`fin_de_anio`** = del 15-dic al 15-ene (ambos inclusive) — **supuesto** declarado (no hay definición oficial).
4. **`puente`** = fin de semana largo: sábado, domingo y lunes de un fin de semana cuyo lunes es festivo (incluidos los
   trasladados por la Ley 51/1983); y viernes, sábado y domingo si el festivo cae en viernes — **supuesto** declarado.
5. Vacíos sin fuente (p. ej. 1–17 de enero de 2021 de las ciudades sin calendario 2020, Sogamoso 2024): valor **nulo** (booleano
   anulable de pandas) y documentado; **no imputar**. Los modelos entrenan desde el 2021-06-01 (§5.1), así que enero de 2021 no
   los afecta; repórtalo.

**Contenido** — una fila por `fecha` del 2021-01-01 al 2024-12-31, sin huecos: `fecha`, `dia_semana` (0 = lunes),
`festivo`, `festivo_nombre` (texto o nulo), `festivo_trasladado` (bool: se movió al lunes por la Ley 51/1983), `puente`,
`semana_santa` (Domingo de Ramos a Domingo de Resurrección; si el informe define otra ventana, usa la del informe y dilo),
`jueves_viernes_santo`, las columnas de vacaciones de arriba y `fin_de_anio`. Si agregas otra columna, que sea conocible 30
días antes y con fuente.

**Cómo**:
- Festivos **calculados por la regla** de la Ley 51/1983 citada en el informe (fijos que no se trasladan, fijos que se trasladan
  al lunes siguiente, móviles desde la Pascua). Pascua con `dateutil.easter.easter` (ya en `requirements.txt`). La prueba compara
  la salida con **las tablas 2021–2024 del informe** (18 por año), fecha por fecha. Los desfases de Ascensión, Corpus Christi y
  Sagrado Corazón: usa los del informe y conserva su `TODO(cita)` en el código y en `data/fuentes.md`.
- Recesos escolares: leídos de `data/externos/m1/calendario_fuentes.yaml`, donde cada rango lleva entidad, año, acto
  administrativo (número y fecha), URL y fecha de consulta, tal como en el informe.
- `main()` ejecutable con `python -m src.m1_demanda.calendario` (no hay subcomando en `run.py` y no se toca `run.py`); escribe el
  parquet; imprime conteos por columna. Sin internet.
- Pruebas (primero): fechas conocidas del informe (p. ej. un festivo trasladado, uno no trasladado, Jueves/Viernes Santo de cada
  año, un receso por ciudad, un día nulo documentado), sin huecos de fecha, tipos, un `puente` de lunes festivo y uno de viernes,
  `fin_de_anio` en los bordes 14/15-dic y 15/16-ene.

## Aceptación (spec de Camila, CA-1)
Esquema §5.2; cada columna con fuente (o supuesto declarado) en `data/fuentes.md`; prueba de fechas conocidas; suite completa pasa
(`.venv/bin/python -m pytest -q`).

## Reglas
Prueba primero. Prohibido inventar fechas, normas o citas: si una fecha no está en el informe, `TODO(dato-faltante)` y nulo. Nada
de internet en el código. No toques archivos fuera de los tuyos. Nada de commits. Reporta al final: archivos creados, salida real de
pytest y de `main()`, conteos, `TODO` abiertos y diferencias que hayas encontrado entre la regla calculada y las tablas del informe
(cualquier diferencia es importante: no la ocultes ajustando la regla).
