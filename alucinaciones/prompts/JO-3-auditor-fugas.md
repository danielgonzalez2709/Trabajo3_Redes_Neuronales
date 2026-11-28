Auditoría adversarial de fuga de JO-3 (M2: partición sin fuga por grupos de casi duplicados), rama dev/jose, directorio
/home/jose-miguel-pulgarin/Documents/projects/Trabajo3_Redes_Neuronales. Cambios sin commit.

Contexto: Anexo de docs/spec/SPEC.md, «Módulo 2 → Tareas → 3» («Demuestren que no hay imágenes iguales o casi iguales (por
ejemplo, versiones aumentadas de una misma foto) en particiones distintas, y describan el método con que lo verificaron»);
SPEC §5.5, §8; docs/spec/partes/jose.md §3.2 (D1–D8); docs/investigacion/JO-1_fuentes_m2.md §6 y C-2 a C-4 (el artículo dice que
guardó imágenes aumentadas —rotación ≤ 15°, volteo, zoom, brillo, recorte— junto a las originales, sin identificarlas).
Código: src/m2_conduccion/{duplicados.py,particion.py}, configs/m2/particion.yaml, tests/test_fuga_m2.py. Salidas:
data/processed/m2/indice.csv, results/data/m2/particion/{resumen.json,pares_cercanos.csv,frontera.csv}. Imágenes en
data/processed/m2/imagenes/. Caché de características (no versionada) en data/processed/m2/cache/ y pesos en data/raw/m2/pesos/.

Busca activamente caminos de fuga, con evidencia medida:
1. Pares de imágenes en splits distintos que sean versiones aumentadas o casi idénticas y que el criterio no unió. Pruebas
   sugeridas: para una muestra de imágenes de prueba, busca su vecino más cercano en train (coseno con la caché y Hamming) y mira
   la distribución y los casos más cercanos que cruzan; prueba hashes robustos a rotación/recorte (p. ej. dHash/aHash, o pHash de
   versiones recortadas/rotadas) para ver si aparecen pares cruzados que pHash+coseno no ven. Guarda las imágenes de los casos
   peores en alucinaciones/evidencias/JO-3/ si las hay.
2. Que nada del proceso use la clase o el split para formar grupos o elegir umbrales.
3. Que la guarda, el espejo y la comprobación de pares cruzados no se puedan saltar (orden de escritura, caché obsoleta con otras
   imágenes o pesos).
4. La fuga por identidad del conductor (D5, ya declarada): cuantifícala si puedes sin inventar ids (p. ej. cuántas imágenes de
   prueba tienen un vecino en train con coseno en [0,90; 0,95)) para que el blog lo reporte con cifras.
Si encuentras un camino real, escribe la prueba que lo demuestra (al final de tests/test_fuga_m2.py o en un archivo aparte, sin
romper las existentes). NO corras `run.py figures` ni la suite completa (reescriben figuras versionadas de M3); corre solo
.venv/bin/python -m pytest -q tests/test_fuga_m2.py. No modifiques código de src ni salidas versionadas. Sin internet.
Veredicto: SIN FUGA / FUGA ENCONTRADA / FUGA RESIDUAL DECLARADA, con cifras reales.
