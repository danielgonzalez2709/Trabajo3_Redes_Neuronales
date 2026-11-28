JO-3, quinta vuelta: ampliación de D9 [DECIDIDO, José, 28-nov] (ya en docs/spec/partes/jose.md §3.2).
Aplica la arista por tiempo (≤ `umbral_segundos` = 10) también a los otros dos formatos de nombre con hora que reportaste y que
JO-1 registra en `PATRONES_NOMBRE` de src/m2_conduccion/datos.py: los PNG `AAAA-MM-DDhh-mm-ss` (183) y `photo_AAAA-MM-DD_hh-mm-ss`
(11), con resolución de segundos. Verifica los conteos, no los copies. Patrones en la config (lista), ancho fijo y fecha armada
con enteros como hiciste con IMG_; reutiliza los patrones de JO-1 si se puede sin duplicar. Compara marcas entre formatos distintos
solo si es correcto hacerlo (misma escala de tiempo: dilo y justifícalo en el docstring; si no hay forma de saber si dos cámaras
comparten reloj, compáralas igual, porque unir de más solo cuesta tamaño de grupo, pero repórtalo).

Prueba primero (cada formato, fechas imposibles, mezcla de formatos, el umbral inclusivo con resolución de segundos). Extiende la
prueba de ráfagas del auditor a los tres formatos. Actualiza los textos (limitación y fugas descartadas), `tiempo_camara` y
`fuga_residual` de resumen.json. La guarda del 15 % sigue; si salta, PARA y reporta. Mismas reglas de siempre (sin commits, sin
archivos compartidos, devolver blog/docs/figures/m3/ a HEAD tras la suite, figura de M2 solo con figs_m2).

Entrega con salida real: dos corridas (sha256sum idénticos), nueva huella y SHA de indice.csv, fotos con marca por formato,
pares por tiempo, grupos, grupo mayor, split × clase en %, desviación en σ, `fuga_residual`, pytest de los tres archivos de M2 -v,
`pytest -q -m "not lento"`, `git status --short`.
