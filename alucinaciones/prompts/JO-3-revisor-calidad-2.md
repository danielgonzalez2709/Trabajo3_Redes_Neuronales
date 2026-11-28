Segunda revisión de calidad de JO-3 (M2: casi duplicados y partición por grupos), rama dev/jose, directorio
/home/jose-miguel-pulgarin/Documents/projects/Trabajo3_Redes_Neuronales. Cambios sin commit (git status / git diff).

En la 1.ª revisión pediste: B1 registrar el tiempo sin caché (la sesión principal decidió que la partición es un paso de datos y
no la demo < 2 min de `run.py m2`, así que la caché no se versiona; solo se exige registrar el tiempo con honestidad);
B2 partir `particion.main`; R1–R11 (todo o nada, `_margenes`, run_id en config, textos a la config, frontera vacía, pruebas y SHA
completo en scripts/descargar_pesos_m2.py, reutilizar sha256_archivo, pares_hamming fuera de src, espejo condicional, pruebas
frágiles, nombres y constantes).

Verifica que cada punto quedó resuelto y que no se introdujeron problemas nuevos en: scripts/descargar_pesos_m2.py,
src/m2_conduccion/{duplicados.py,particion.py,datos.py}, src/viz/figs_m2.py, configs/m2/particion.yaml, tests/test_fuga_m2.py,
tests/test_descargar_pesos_m2.py. Corre .venv/bin/python -m pytest -q tests/test_fuga_m2.py tests/test_descargar_pesos_m2.py.
NO corras la suite completa ni `run.py figures` (reescriben figuras versionadas de M3). No edites nada.
Veredicto: APROBADO / APROBADO CON OBSERVACIONES / CAMBIOS REQUERIDOS, con hallazgos archivo:línea, bloqueantes separados.
