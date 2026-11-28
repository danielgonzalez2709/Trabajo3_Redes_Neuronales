JO-3, cuarta vuelta: hallazgos del auditor-fugas + segunda revisión de calidad. Mismas reglas: prueba primero, sin commits, sin
push, sin archivos compartidos (src/comun/, run.py, requirements.txt, README, SPEC.md), .venv/bin/python, no correr
`run.py figures` ni la suite completa sin devolver después blog/docs/figures/m3/ a HEAD (`git checkout -- blog/docs/figures/m3/`).
La partición VA a cambiar en esta vuelta (D9): está bien; reporta la nueva huella.

## A. Auditor-fugas (evidencias en alucinaciones/evidencias/JO-3/auditor-fugas/, prueba nueva tests/test_fuga_m2_auditoria.py)
A1. D9 [DECIDIDO, José, 28-nov] (ya en docs/spec/partes/jose.md §3.2): arista adicional entre dos fotos cuya marca de tiempo de
   cámara (nombre original `IMG_AAAAMMDD_HHMMSSmmm`, leído de data/processed/m2/origen.csv; 404 fotos según el auditor —verifícalo)
   difiera ≤ `umbral_segundos` = 10 (en configs/m2/particion.yaml). Usa auditoria_m2.py del auditor como referencia del parseo,
   pero escribe la función en duplicados.py con su prueba (formato, milisegundos, fotos sin marca, fechas distintas). La arista no
   usa la clase. La guarda del 15 % sigue aplicando; si salta, PARA y reporta. Agrega `criterio = tiempo` en pares_cercanos.csv
   y los conteos en resumen.json.
A2. Las pruebas xfail strict del auditor: la de ráfagas (≤ 3 s) debe pasar ahora → quítale el xfail (y extiéndela a ≤ 10 s).
   La de la caché (A3) también → quítale el xfail. No borres las pruebas del auditor; puedes moverlas a test_fuga_m2.py si queda
   más claro.
A3. La clave de validez de la caché incluye `red`, `media` y `desviacion` (guárdalos en el .npz y compáralos en `cache_valida`).
A4. Textos: corrige `limitacion_conductor` y `fugas_descartadas` (y cualquier otro texto) que digan que se eliminan «ráfagas casi
   iguales». Deben decir con exactitud lo que se elimina (pares sobre los umbrales, espejos, ráfagas con marca de tiempo ≤ 10 s) y
   lo que NO (ráfagas sin marca de tiempo bajo los umbrales; mismo conductor en otra pose; rotaciones/recortes del rango del
   artículo no son propios del criterio: su ausencia entre splits se comprobó empíricamente con variantes ±5/10/15°, zoom 0,9/0,8
   y espejo). Agrega a resumen.json un bloque `fuga_residual` con las cifras RECALCULADAS tras D9 (no copiadas del auditor):
   para validación y prueba, cuántas imágenes tienen su vecino más cercano en train con coseno en [0,90; 0,95), [0,94; 0,95) y
   < 0,90, la mediana, y cuántas fotos con marca de tiempo tienen una de train a ≤ 60 s. Debe poder regenerarse con el comando.

## B. Revisión de calidad 2 (bloqueantes)
B1. scripts/descargar_pesos_m2.py importa `sha256_archivo` de src.m2_conduccion.datos como hace scripts/descargar_m1.py:25-27
   (sys.path), con prueba de identidad como tests/test_descargar_m1.py:177-179. Quita el comentario falso.
B2. Prueba de la delegación `etapa: particion` en src/m2_conduccion/datos.py:561-563 (que `datos.main` con esa config delega en
   la partición).
B3. Quita de tests/test_descargar_pesos_m2.py:81 la aserción `not list(destino.parent.glob("*.sha256"))` (no puede fallar).

## C. Revisión de calidad 2 (recomendados que sí se hacen)
C1. duplicados.py:136-137: el docstring del margen debe decir que también lo usa el barrido.
C2. configs/m2/particion.yaml:43: `bloque` es memoria, no reproducibilidad. configs/m2/particion.yaml:35: matiza «cpu hace
    reproducibles los cosenos» a «en la misma máquina y versiones».
C3. Pruebas de las ramas de error de `_validar_cfg` (coseno fuera de [0,1], tam_hash ≠ 8, espejo no booleano, red no soportada)
    y del SystemExit por URL distinta del script.
C4. Prueba sobre los 7 276 hashes reales de que todo pHash tiene 32 unos (base de «d_H siempre par»), o matiza el texto.
C5. Docstring de `_escribir_salidas`/`main`: «todo o nada» cubre el cálculo y las comprobaciones; la escritura es secuencial.
    Dilo con exactitud (o escribe a temporal y renombra, si es simple).
C6. Nits: `_validar_cfg` no devuelve nada; `import imagehash` al inicio del módulo; número mágico 6 de figs_m2.py:70 con nombre;
    docstring de `componentes`: «reducción a la mitad del camino (path halving)».
No hagas: subcomando `m2-particion` ni cambios en src/comun/cli.py (compartido).

## Entrega (salida real)
Comando de partición dos veces (sha256sum idénticos), nueva huella y SHA de indice.csv; conteos: grupos, grupo mayor (% y si
cambió), pares por criterio incluido `tiempo`, split × clase en %, desviación en σ; bloque `fuga_residual`;
`pytest -q tests/test_fuga_m2.py tests/test_fuga_m2_auditoria.py tests/test_descargar_pesos_m2.py -v`; `pytest -q -m "not lento"`
y después `git checkout -- blog/docs/figures/m3/`; `git status --short`. Regenera la figura de M2 solo con figs_m2.
