José aceptó (28-nov) lo siguiente, ya registrado en docs/spec/partes/jose.md §3.2 como D6–D8 y en la redacción de D4:
- D6 umbrales umbral_hamming = 2 y umbral_coseno = 0,95 (déjalos como [DECIDIDO, José, 28-nov] en configs/m2/particion.yaml).
- D7 estratificación por el CONTEO DE CLASES de cada grupo: implementa tu propuesta k* = argmax_k Σ_c v_gc·(p_k·N_c − n_kc)
  (ajusta docstring y la cota que demostraste, o deja claro qué cota vale ahora). Reemplaza el método por clase mayoritaria.
- D8 particion.semilla = 2026.
- D4 redacción: los pares entre clases son «misma escena, otra acción» (mismo conductor segundos después), NO «etiqueta dudosa».
  Corrige ese texto donde aparezca (calidad.csv, resumen.json, comentarios, figura si lo dice).

Prueba primero: agrega una prueba que falle con el método de clase mayoritaria y pase con el nuevo (p. ej. proporciones por
clase dentro de una tolerancia estrecha justificada en el conjunto real o en un sintético con grupos mixtos). Regenera
indice.csv, resumen.json, procesado.json (sha256_indice), calidad.csv y la figura si cambia. Mismas reglas que antes: sin commits,
sin push, sin tocar archivos compartidos, .venv/bin/python.

Entrega con salida real: comando de partición dos veces (sha256sum idénticos), pytest tests/test_fuga_m2.py -v,
pytest -q -m "not lento", la prueba nueva fallando contra el método viejo, conteos split × clase en %, nueva huella de la partición.
