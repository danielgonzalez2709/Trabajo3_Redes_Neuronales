# JJ-4 — prompt del orquestador (Opus 5.5) al auditor-fugas (Opus), 2.ª vuelta, 2026-11-27

Revisa SOLO este cambio en `tests/test_fuga_m3.py` (rama `dev/juanjose`; solo lees, sin commits; `.venv\Scripts\python`):
1. Nueva entrada `"referencias.aleatorio": _ajuste_aleatorio` en `AJUSTES_SOLO_TRAIN` (ajusta `referencias.Aleatorio` con
   `make_rng(0, 0)` y devuelve `puntuar([1, 2])`).
2. Nueva guarda `test_los_modelos_no_leen_archivos_ni_salidas_de_evaluacion` (la que propusiste en JJ-4): `ARCHIVOS_DE_MODELO_M3 =
   {"referencias.py"}`, `SALIDAS_DE_EVALUACION_M3` y `LECTURAS_DE_ARCHIVOS = ("read_parquet", "load_json", "open(", "read_csv")`.
Comprueba que coincide con tu propuesta, que la entrada del aleatorio prueba algo útil (¿detectaría un aleatorio que usara
`inter` de validación o prueba?), y que la guarda detecta un mutante (p. ej. `pd.read_parquet` o `"summary.json"` añadidos a una
copia de `referencias.py` en el scratchpad; no modifiques el repo). Corre `.venv\Scripts\python -m pytest -q tests/test_fuga_m3.py`.
Informe corto: veredicto (APROBADO / RECHAZADO), resultado de los mutantes y cualquier hueco.
