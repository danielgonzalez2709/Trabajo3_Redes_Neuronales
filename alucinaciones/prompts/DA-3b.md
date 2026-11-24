# Prompt DA-3b — implementador-experto (Opus) — 2026-11-24 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/implementador-experto.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`; **no hagas commit ni push**).
Usa `.venv\Scripts\python`; no cambies `requirements.txt`.

Lee antes: `docs/spec/SPEC.md` §0 (en especial 0.4, 0.5, 0.8, 0.9), §4.1, §5.1 (v0.3), §5.11, §5.12, §8;
`docs/spec/partes/daniel.md` §3.2 (rutas decididas) y las filas DA-3 y DA-4 de §4; `docs/investigacion/DA-2_fuentes_m1.md`
completo (diccionario literal, inconsistencias, tiempos de la API); `scripts/descargar_m1.py` y `data/fuentes.md` (DA-3a);
`src/comun/eda.py`, `src/comun/config.py`, `src/comun/cli.py` (subcomando `m1-datos` → qué módulo y función espera).
Del Anexo: «Módulo 1 → Datos» y tarea 2.

## Tarea DA-3 (series reales) + DA-4 (secciones 1–2 de la plantilla) — entrega **mié 25, 2 p. m.**
Rutas decididas (3 pares = 6 series): 11001↔76001, 11001↔15759, 52001↔52356. Periodo 2021-01-01 a 2023-12-31.
`pasajeros` = origen + tránsito (§5.1 v0.3).

1. **Descarga** (red solo aquí): ejecuta `scripts/descargar_m1.py descargar` para las 6 rutas dirigidas y los 36 meses
   (agrupa por origen, destino, fecha, `tipo_despacho`, `clase_vehiculo`). Hasta 4 meses en paralelo si el script lo permite.
   Reanudable. Registra en `data/fuentes.md` la fecha, las consultas y el SHA-256 de cada parquet crudo. Si un mes falla tras
   los reintentos, repórtalo y sigue.
2. **`configs/m1/datos.yaml`**: rutas, periodo, rutas de archivos de entrada y salida, y los parámetros de las reglas de
   anómalos (nada de números mágicos en el código). Usa `base_seed` solo si algo es aleatorio.
3. **`src/m1_demanda/datos.py`** con `main(cfg)` (el que espera `run.py m1-datos`), **sin red**, que a partir de
   `data/raw/m1/rutas/*.parquet` y `data/processed/m1/divipola.csv` escriba:
   - `data/processed/m1/demanda_detalle.parquet` (ruta, fecha, `tipo_despacho`, `clase_vehiculo`, `pasajeros`, `despachos`).
   - `data/processed/m1/demanda_diaria.parquet` con el **esquema exacto de §5.1**: una fila por (ruta, fecha), sin huecos en
     2021-01-01..2023-12-31; es la suma del detalle.
   - `sin_registro`: el día no tiene ninguna fila en la fuente para esa ruta. Decide y **documenta** cómo se imputan
     `pasajeros` y `despachos` esos días (p. ej. 0 con la marca, para que el modelo decida); no borres filas.
   - `anomalo`: reglas explícitas y justificadas con los datos, como mínimo «despachos > 0 y pasajeros = 0 en el día» (el
     enunciado lo pide). Si propones una regla de atípicos, que use solo información de la misma ruta, que sea robusta
     (mediana/MAD o cuantiles) y **no invente capacidades de vehículo**. Las marcas son descriptivas: deja escrito que no se usan
     como variable de entrada de los modelos y que la regla mira la serie completa (el `auditor-fugas` lo revisará). Reporta
     cuántos días marca cada regla por ruta y muestra ejemplos.
   - `data/processed/m1/rutas.yaml`: por ruta `ruta_id`, códigos, nombres de municipio y departamento tomados de
     `divipola.csv`, `ruta_regreso_id`, criterio de selección (copia el de `daniel.md` §3.2).
   - `data/processed/m1/resumen_datos.json`: registros y variables del conjunto crudo (cita las cifras **medidas** del informe de
     DA-2 con su fecha de consulta), periodo usado, rutas, filas descargadas, y por ruta: días, días sin registro, días anómalos
     por regla, pasajeros totales, % de pasajeros en tránsito y por clase de vehículo.
   - Valida que todos los códigos estén en DIVIPOLA (los que no, se reportan como inconsistencia).
4. **DA-4 — plantilla común, secciones 1–2** con `src/comun/eda.py` en `results/data/m1/eda/`:
   - `ficha.json` (claves de §5.12; `conteos` con lo propio de M1).
   - `calidad.csv` con `tabla_calidad` sobre el detalle y la serie.
   - `diccionario.json`: las 10 columnas con su descripción **literal** de la fuente (del informe de DA-2) y la tabla de
     **inconsistencias diccionario vs. datos** del informe, más las que encuentres tú en las rutas descargadas.
   - Puede llamarse desde `datos.py` o desde una función propia; el comando `run.py m1-datos` debe dejar todo regenerado.
5. **Pruebas primero** en `tests/test_datos_m1.py`, sin red, con parquets crudos de juguete creados en la prueba: esquema y
   tipos de §5.1, sin huecos, suma detalle = serie, regla `sin_registro`, cada regla de anómalos con un caso hecho a mano,
   `ruta_regreso_id` recíproco, códigos validados contra un DIVIPOLA de juguete, y que `datos.py` no haga red
   (`tests/test_no_network.py` ya vigila `src/`).
6. Corre `.venv\Scripts\python run.py m1-datos --config configs/m1/datos.yaml` sobre los datos reales y la suite completa.

## Reglas
- Nada inventado: nombres de municipio desde `divipola.csv`; significados desde el diccionario literal; cifras medidas.
- No toques `docs/spec/`, `blog/`, `src/comun/` (si necesitas algo de ahí, repórtalo), ni el trabajo de otros.
- Si los datos contradicen el Spec (p. ej. un mes casi vacío dentro de 2021–2023), detente en ese punto y repórtalo con cifras.

## Entrega
Formulación de las reglas (sin registro, anómalos) con su justificación; tabla por ruta (días, sin registro, anómalos por
regla, pasajeros totales, % tránsito); tamaños de los archivos procesados; salida real de `run.py m1-datos` y de pytest;
inconsistencias nuevas; riesgos de fuga o de calidad que veas para Camila y Andrés.
