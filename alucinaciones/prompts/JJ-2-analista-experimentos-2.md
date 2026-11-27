# Prompt JJ-2 — analista-experimentos (Sonnet), 2.ª vuelta — 2026-11-26 — orquesta: Juan José

Ajustes menores (mismas reglas que tu primer encargo: sin commit/push, `.venv/Scripts/python`, prueba primero si cambias
comportamiento, solo tus archivos):

1. `src/viz/figs_m3.py`, figura `preferencias_tipo.png`: (a) la barra de color usa punto decimal (0.20) y las anotaciones
   coma (0,22); usa coma decimal en toda la figura (y en las demás figuras de M3 si pasa lo mismo). (b) El pie dice «Si el
   destino fuera al azar en el catálogo, cada fila tendría 0,40 en las celdas recuadradas»: es ambiguo; di que cada celda
   tendría 0,20 y la suma de las dos recuadradas 0,40 (línea base exacta), leyendo esos valores de los resultados, no
   tecleados.
   (c) Separador de miles: en los títulos sale «1.998» y «2.000»; el blog usa espacio («1 998»). Unifica con espacio.
2. `src/m3_recomendacion/README.md`: actualiza la parte de `m3-eda` (comando, config `configs/m3/eda.yaml`, salidas en
   `results/data/m3/eda/`, figuras con `run.py figures` en `blog/docs/figures/m3/`), en el estilo del resto del README.
3. Vuelve a correr `run.py m3-eda` (si tocaste algo que lo afecte), `run.py figures` y
   `pytest -q tests/test_eda_m3.py`; pega las salidas. No toques `blog/secciones/` (lo está escribiendo otro agente).
