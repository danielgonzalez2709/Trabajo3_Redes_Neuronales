Revisa la calidad del código de la tarea JO-3 (M2: casi duplicados y partición por grupos) en la rama dev/jose, directorio
/home/jose-miguel-pulgarin/Documents/projects/Trabajo3_Redes_Neuronales. Cambios sin commit (git status / git diff).

Archivos: scripts/descargar_pesos_m2.py, src/m2_conduccion/duplicados.py, src/m2_conduccion/particion.py, el cambio en
src/m2_conduccion/datos.py (delegación por `etapa: particion`), src/viz/figs_m2.py, configs/m2/particion.yaml,
tests/test_fuga_m2.py.

Criterios: legibilidad y nombres; funciones pequeñas y puras; ningún parámetro fijo en el código; pruebas que prueban
comportamiento (no implementación) y que fallarían con un error real; determinismo; eficiencia razonable (7 276 imágenes, ~90 000
pares); manejo de errores claro (pesos ausentes, guarda del 15 %); que José pueda explicarlo y modificarlo en vivo en la
sustentación. Puedes correr .venv/bin/python -m pytest -q tests/test_fuga_m2.py. No edites nada.
Veredicto: APROBADO / APROBADO CON OBSERVACIONES / RECHAZADO, con hallazgos concretos (archivo:línea), separando bloqueantes de
sugerencias.
