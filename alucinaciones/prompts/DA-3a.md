# Prompt DA-3a — curador-datos (Sonnet) — 2026-11-24 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/curador-datos.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`; **no hagas commit ni push**).
Usa `.venv\Scripts\python`; no cambies `requirements.txt` (ya trae `requests`, `pandas`, `pyarrow`).

Lee antes: `docs/spec/SPEC.md` §0, §5.1 (v0.3: periodo 2021–2023, pasajeros = origen + tránsito, tabla de detalle),
`docs/spec/partes/daniel.md` §3.2, y **todo** `docs/investigacion/DA-2_fuentes_m1.md` (identificador `eh75-8ah6`, columnas,
tiempos de la API, consulta SoQL probada y sus notas).

## Tarea DA-3a — script de descarga y ranking de rutas candidatas
1. **`scripts/descargar_m1.py`** (fuera de `src/`: es el único código con red; los experimentos no usan internet y
   `tests/test_no_network.py` lo vigila). Funciones reutilizables:
   - `consultar(params, timeout, reintentos)`: GET a `https://www.datos.gov.co/resource/eh75-8ah6.json` con reintentos y espera
     creciente ante timeout o 5xx; registra cada consulta (URL completa, duración, filas) en un log.
   - Paginación con `$limit`/`$offset` y `$order` estable.
   - Subcomando `ranking`: ver punto 2. Subcomando `descargar` (lo usará DA-3b): recibe una lista de rutas (origen, destino) y un
     rango de fechas, descarga **por mes** con `$where` filtrado por esas rutas y el mes, agrupando por
     `municipio_origen_ruta, municipio_destino_ruta, fecha_despacho, tipo_despacho, clase_vehiculo` con `sum(pasajeros)` y
     `sum(despachos)`, y guarda un parquet por mes en `data/raw/m1/rutas/AAAA-MM.parquet` (reanudable: si el mes ya existe, lo
     salta). Implementa `descargar` pero **no lo ejecutes** todavía.
   - Subcomando `divipola`: descarga `gdxc-w37w` completo y lo guarda en `data/processed/m1/divipola.csv` (sí se versiona,
     ~1.122 filas) con las columnas tal cual; registra URL, fecha y SHA-256.
   - Excluye siempre las fechas imposibles (`fecha_despacho < "2100-01-01"`).
2. **Ranking de rutas (ejecútalo):** las agregaciones completas caducan (ver el informe). Usa una muestra de **un día por mes**
   de 2021-01 a 2023-12 (36 días; p. ej. el segundo miércoles de cada mes, y anota cuáles), con
   `group by municipio_origen_ruta, municipio_destino_ruta` y `sum(pasajeros), sum(despachos), count(*)`, todos los tipos de
   despacho. Puedes lanzar hasta 4 consultas en paralelo. Con eso arma `data/raw/m1/ranking_rutas.csv` y un resumen:
   - por par (origen, destino): pasajeros totales en la muestra, número de días de la muestra con registros (de 36), y si
     existe el **sentido de regreso** (destino, origen) con su volumen;
   - excluye rutas intramunicipales (origen = destino);
   - ordena los **pares ida/regreso** por el mínimo de los dos sentidos, y muestra los 15 mejores con nombres de municipio y
     departamento tomados de `divipola.csv` (corre antes el subcomando `divipola`). Valida que todos los códigos existan en
     DIVIPOLA y lista los que no.
3. Agrega a `data/fuentes.md` (créalo si no existe) la sección M1 con: conjunto, URL, licencia, fecha de consulta, consulta
   del ranking, DIVIPOLA (URL, corte, SHA-256 del CSV). Nada de cifras no medidas.
4. Pruebas sin red en `tests/test_descargar_m1.py`: construcción de la consulta SoQL (where por mes y por lista de rutas,
   group, order, paginación) y armado del ranking a partir de un JSON de ejemplo. Nada de red en las pruebas.

## Reglas
- No inventes nombres de columnas ni de municipios: salen de la API y de `divipola.csv`.
- Si una consulta falla tras los reintentos, regístralo y sigue; reporta qué días faltan en el ranking.
- No toques `src/`, `docs/spec/`, `blog/`.

## Entrega
Tabla de los 15 mejores pares (códigos, nombres, pasajeros de cada sentido en la muestra, días con registros de 36), códigos
fuera de DIVIPOLA, tiempos de las consultas, salida de pytest, archivos creados.
