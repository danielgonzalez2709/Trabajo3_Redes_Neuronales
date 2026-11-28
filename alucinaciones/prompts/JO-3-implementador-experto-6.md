JO-3, sexta y última vuelta (corta): observaciones de la ronda final. Ambos revisores aprobaron; esto es pulido. La partición NO
debe cambiar (huella e0a6b55a…747370, SHA de indice.csv 7d5fe2cf…2e639e); si cambia, PARA y explica. Mismas reglas de siempre.

Auditor-fugas:
O1. `textos.metodo` (y por lo tanto resumen.json.metodo) debe incluir la arista por marca de tiempo (D9): «… o marcas de tiempo
    del nombre original a ≤ umbral_segundos (D9)».
O2. Tu reescritura de la prueba A3 en tests/test_fuga_m2_auditoria.py quedó trivial: guarda la caché con red="resnet18", media y
    desviacion correctas, comprueba que con esos valores SÍ se usa la caché, y luego cambia solo `media` y espera el rechazo
    (FileNotFoundError por pesos ausentes). Demuestra que falla si se quita `media` de la clave de la caché.
Revisor-calidad:
R1. Notas de `tiempo_camara` (particion.py:448-450) y `fuga_residual` (:486-487) a `textos` de la config.
R2. `(?!\d)` al final del patrón IMG_ (y donde aplique), con prueba de `IMG_20240930_1323166650.jpg` → sin marca.
R3. Si falla `os.replace` a mitad, limpia los `.tmp` que queden.
R4. Una sola función para «dentro del umbral de tiempo» usada por `pares_por_tiempo` y las aristas.
R5. Prueba de un par que cumple hash y tiempo a la vez (criterio `hamming`, `segundos` relleno).
R6. Helper por split para `fuga_residual`; renombra `_clave`.
R7. Saca el popcount de 32 unos a una prueba con nombre propio.
Nits: lambda de tests/test_fuga_m2.py:433 → función explícita; import de PATRONES_NOMBRE a nivel de módulo; docstring del módulo
particion.py menciona segundos, tiempo_camara y fuga_residual; `_validar_cfg` exige `tiempo.formatos` no vacío.

Entrega: dos corridas (misma huella y SHA que arriba), pytest -v de los tres archivos de M2, `pytest -q -m "not lento"` y luego
`git checkout -- blog/docs/figures/m3/`, `git status --short`.
