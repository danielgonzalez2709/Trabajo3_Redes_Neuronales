# Prompt DA-1c — implementador (Sonnet) — 2026-11-24 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/implementador.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`; **no hagas commit ni push**).
Usa `.venv\Scripts\python`; no cambies `requirements.txt`. Referencia de estilo (solo lectura, Trabajo 2):
`C:\Users\danie\AppData\Local\Temp\claude\4dc77ad0ee14e84c\6f603fae-d809-443f-a910-1822e4048a3e\scratchpad\t2repo`.

Lee antes: `docs/spec/SPEC.md` §0, §5.1, §5.11, §5.12, §8 y `src/comun/` (ya existe: config, cli, seeds, results).

## Tarea DA-1c — plantilla común de análisis descriptivo, estilo de figuras y serie sintética de M1 (parte de DA-1)
1. **`src/comun/eda.py`** (plantilla común §5.12), prueba primero en `tests/test_eda_comun.py`:
   - `SECCIONES_PLANTILLA`: tupla con los siete títulos exactos de §5.12, en orden.
   - `escribir_ficha(ruta, datos: dict)`: valida que estén las claves obligatorias de `ficha.json` (§5.12: `fuente, cita, url,
     fecha_descarga, sha256, unidad_de_observacion, n_registros, n_variables, periodo, conteos`) y escribe JSON UTF-8.
     Clave faltante = error claro.
   - `tabla_calidad(df) -> DataFrame`: por columna: tipo, faltantes, % faltantes, valores únicos, un ejemplo.
   - `escribir_hipotesis(ruta, hipotesis: list[dict])` y `leer_hipotesis(ruta)`: validan el esquema de `hipotesis.json`
     (§5.12): `id` con patrón `H-M[123]-<n>`, `enunciado`, `justificacion`, `evidencia_esperada`, `figura_o_tabla`,
     `resultado`, `veredicto` ∈ {`pendiente`, `confirmada`, `refutada`, `no concluyente`}, `evidencia`. Ids repetidos = error.
   - Usa la escritura de `src/comun/results.py` si ya ofrece escritura atómica de JSON.
2. **`src/viz/estilo.py`**: estilo común de figuras portado de `t2repo/src/viz/style.py` y `paleta.py` (sin nada específico del
   Trabajo 2), con una función para guardar figuras de forma uniforme. Prueba mínima de que se aplica sin error.
3. **Serie sintética de M1** (§5.11): `src/m1_demanda/sintetico.py` con `generar(semilla: int) -> pd.DataFrame` y una función
   que la escribe en `data/sintetico/m1/demanda_diaria.parquet` y `data/sintetico/m1/rutas.yaml`.
   - Esquema **exacto** de §5.1: `ruta_id, origen_divipola, destino_divipola, fecha, pasajeros, despachos, sin_registro,
     anomalo`, una fila por (ruta, fecha) sin huecos.
   - 4 rutas = 2 pares ida/regreso. **Códigos ficticios que no existen en DIVIPOLA**: usa departamento `00` (p. ej. `00001`,
     `00002`, `00003`) y dilo en un comentario y en `rutas.yaml` (`sintetico: true`). No uses códigos reales.
   - Periodo 2019-01-01 a 2024-12-31. Pasajeros ~ Poisson con tendencia, estacionalidad semanal y anual, una caída tipo
     pandemia en 2020 con recuperación, picos aleatorios de temporada alta, algunos días `sin_registro` (pasajeros 0) y algunos
     `anomalo` (despachos > 0 con pasajeros 0). Despachos coherentes con los pasajeros. Todo con semilla (`src/comun/seeds.py`).
   - `tests/test_sintetico.py`: esquema y tipos de §5.1, sin huecos de fecha por ruta, reproducible con la misma semilla,
     ruta de regreso declarada en `rutas.yaml`.
   - Genera y deja los archivos en `data/sintetico/m1/` (sí se versionan; deben pesar poco).

## Aceptación
`.venv\Scripts\python -m pytest -q` completo en verde (pega la salida); tamaño del parquet sintético.

## Reglas
- Solo tocas `src/comun/eda.py`, `src/viz/estilo.py`, `src/m1_demanda/sintetico.py`, `data/sintetico/`, y las pruebas nuevas.
- No cambies contratos del Spec; si algo no cuadra, repórtalo.

Entrega: archivos creados, salida real de pytest, dudas.
