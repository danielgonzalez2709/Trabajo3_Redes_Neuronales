Revisa la tarea JO-3 (M2: casi duplicados y partición sin fuga por grupos) en la rama dev/jose, directorio
/home/jose-miguel-pulgarin/Documents/projects/Trabajo3_Redes_Neuronales. Los cambios están sin commit (git status / git diff).

Contra qué revisar:
- Anexo de docs/spec/SPEC.md, «Módulo 2 → Tareas → 3. Partición sin fuga de información» y «Regla de comparación justa».
- SPEC.md §5.5 (columnas de indice.csv), §5.9 (evidencia con SHA-256 de la partición), §8 (test_fuga_m2.py), §5.12 fila 4.
- docs/spec/partes/jose.md §3.2: decisiones D1–D8 [DECIDIDO, José]. Ni más ni menos.
- Reglas de CLAUDE.md: sin internet en experimentos (solo scripts/descargar_pesos_m2.py), semillas con src/comun/seeds.py,
  parámetros en config, no tocar archivos compartidos (src/comun/, run.py, requirements.txt, README, SPEC.md), prohibido inventar.

Archivos: scripts/descargar_pesos_m2.py, src/m2_conduccion/{duplicados.py,particion.py,datos.py}, src/viz/figs_m2.py,
configs/m2/particion.yaml, tests/test_fuga_m2.py, data/processed/m2/indice.csv, results/data/m2/particion/*,
results/data/m2/eda/{calidad.csv,procesado.json}, blog/docs/figures/m2/frontera_duplicados.png.

Comprueba en particular: que indice.csv solo cambió grupo_duplicado y split (columnas y orden de filas como en HEAD); que todo
umbral/semilla/proporción viene de la config; que resumen.json trae la huella y la limitación D5; que los textos de D4 dicen
«misma escena, otra acción»; que ningún número del resumen está inventado (recalcula 2–3 cifras desde indice.csv y
pares_cercanos.csv). Usa .venv/bin/python. No edites nada. Veredicto: APROBADO / APROBADO CON OBSERVACIONES / RECHAZADO, con
hallazgos concretos (archivo:línea).
