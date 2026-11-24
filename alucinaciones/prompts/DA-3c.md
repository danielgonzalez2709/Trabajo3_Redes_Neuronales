# Prompt DA-3c — implementador (Sonnet) — 2026-11-24 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/implementador.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`; **no hagas commit ni push**).
Usa `.venv\Scripts\python`; no cambies `requirements.txt`. No toques `docs/`, `blog/`, `alucinaciones/`.

Contexto: DA-3/DA-4 (`src/m1_demanda/datos.py`, `scripts/descargar_m1.py`, sus pruebas, `configs/m1/datos.yaml`) pasó por
revisor-spec (APROBADO), auditor-fugas (sin fuga activa) y revisor-calidad (CAMBIOS REQUERIDOS). Lee
`docs/spec/SPEC.md` §5.1 y §5.3 (v0.5) y `docs/investigacion/DA-3_auditoria_fugas.md`. Corrige **solo esto**, prueba primero:

## Bloqueantes (revisor-calidad)
1. `datos.py` ~350-355: el conteo «pasajeros = 0 con despachos ≥ 1» usa `(crudo["pasajeros"] == 0).sum()` sin filtrar
   despachos. Haz que el número y la frase digan lo mismo y agrega una prueba con una fila (0, 0).
2. `datos.py` ~564-568 `_fecha_descarga`: no usar el mtime de los parquets. Tomar la fecha del log de descarga
   (`data/raw/m1/consultas_log.jsonl`, campo de momento) o escribir la fecha al descargar en un archivo versionado; si no hay
   log, error claro. Documéntalo.

## Revisor-spec, observación 4
3. El Anexo pide «número de registros»: agrega en `resumen_datos.json` y en `ficha.json` (`conteos`) el número de **registros
   crudos** de las 6 rutas en 2021–2023 (`count(*)` en la fuente, sin agrupar). Mídelo con una consulta nueva de
   `scripts/descargar_m1.py` (subcomando `contar` o similar, por mes y ruta, reanudable), guarda el resultado en
   `data/processed/m1/conteo_registros.csv` con la fecha de consulta y regístralo en `data/fuentes.md`. Distingue en el resumen
   los tres números: registros del conjunto completo (49.202.812), registros crudos de las 6 rutas, filas agregadas descargadas,
   y filas de la serie.

## Recomendados (revisor-calidad)
4. `datos.py` ~236: quitar `.fillna(False)` redundante (o comentar por qué), cuidando el dtype bool.
5. `datos.py` ~232-235: si MAD = 0 la regla queda desactivada para esa ruta: comentarlo en el código y probarlo.
6. `datos.py` ~244-247 `aplicar_marcas`: unir por (`ruta_id`, `fecha`) o afirmar el alineamiento, no por posición.
7. `datos.py` ~504-507 y ~144-146: una sola función para el filtro de ruta y periodo.
8. `leer_divipola` y `sha256` duplicados entre `datos.py` y `scripts/descargar_m1.py`: un solo origen. `sha256` puede ir en
   `src/comun/results.py` si ya hay algo parecido (repórtalo); si no, deja el de `datos.py` y que el script lo importe.
9. `datos.py` ~548-549: `calidad.csv` con `reindex(columns=[...])` legible. ~533: no asumir que todas las rutas tienen la misma
   longitud (o comentar por qué es cierto).
10. `scripts/descargar_m1.py`: `r.json()` dentro del `try` con reintento (~62); `except` limitado a errores de red/consulta
    (~226); `ranking` sin `divipola.csv` y `descargar` con `--desde > --hasta` salen con código ≠ 0; `leer_rutas` valida el
    formato con mensaje propio; `pd.set_option` solo dentro de `pd.option_context`; quitar los parámetros `pagina`/`offset` que
    solo usa la prueba (~121) y ajustar la prueba.
11. Pruebas: quitar la afirmación tautológica `n_registros == 123` (o dejarla como comprobación de que pasa el valor de config,
    con nombre claro); agregar casos borde: ruta con pasajeros totales 0, ruta con todos los días sin registro, MAD = 0, MAD sin
    datos; `ranking` con fallos y `armar_ranking` con muestras vacías.

## Aceptación
- `.venv\Scripts\python -m pytest -q` en verde (pega la salida).
- `.venv\Scripts\python run.py m1-datos --config configs/m1/datos.yaml` regenera todo. `demanda_diaria.parquet`,
  `demanda_detalle.parquet` y `marcas_anomalos.parquet` deben quedar **byte a byte iguales** a los versionados (compara SHA-256
  antes y después); solo `resumen_datos.json` y `ficha.json` pueden cambiar (por los puntos 1–3). Si algo más cambia, detente y
  repórtalo.
- Entrega: archivos cambiados, salidas reales, el conteo de registros crudos por ruta, dudas.
