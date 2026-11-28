JO-3, tercera vuelta: correcciones de la revisión de calidad (revisor-calidad, CAMBIOS REQUERIDOS). Aplica esto; prueba primero
donde aplique. Mismas reglas: sin commits, sin push, sin archivos compartidos, .venv/bin/python. NO vuelvas a correr
`run.py figures` (regenera las figuras de M3, que no son nuestras): genera solo la figura de M2 llamando a src/viz/figs_m2.py.
Los resultados (indice.csv, huella) NO deben cambiar: si cambian, para y explícalo.

B1 (decisión de la sesión principal): la partición es un paso de datos, no la demo del módulo (la demo < 2 min es `run.py m2`,
JO-10), así que no se versiona la caché. Pero `resumen.json` debe registrar con honestidad el tiempo de la extracción sin caché:
guarda en `resumen.json` el tiempo medido de la última corrida SIN caché (la tuya de la 1.ª vuelta midió 169,5 s de
características y 199,1 s total; vuelve a medirlo corriendo una vez sin caché, no copies la cifra) además del de la corrida con
caché, con su dispositivo. Explícito en el campo que la caché la reutiliza JO-4.
B2: parte `particion.main` (particion.py:272-387) en funciones con nombre (`_calcular_pares_y_grupos`, `_comprobar_particion`,
`_construir_resumen`, `_escribir_salidas` o similar) para que `main` se lea en ~10 líneas.
R1: el docstring «todo o nada» debe ser verdad: calcula todo y comprueba antes de escribir, o corrige la frase.
R2: extrae `_margenes(cfg)` con una línea que explique qué cubren.
R3: el `run_id` fijo de `make_rng(cfg["frontera"]["semilla"], 0)` sale de la config.
R4: textos fijos de particion.py:248 y figs_m2.py:75-76 pasan a `textos:` de configs/m2/particion.yaml.
R5: figs_m2.py con frontera vacía: error claro o figura que lo diga, no un ValueError de NaN; con prueba.
R6: scripts/descargar_pesos_m2.py: lee destino y SHA-256 completo de configs/m2/particion.yaml (sin duplicarlos), verifica el SHA
completo además del prefijo, quita el `.sha256` si nadie lo lee, y agrega tests/test_descargar_pesos_m2.py con requests falso
(patrón de tests/test_descargar_m2.py): archivo ya existente, SHA que no coincide, descarga correcta. Sin red en las pruebas.
R7: reutiliza `datos.sha256_archivo` en src (en el script, comentario que justifique la copia si se queda, como en descargar_m2.py:30).
R8: `pares_hamming` solo lo usa la prueba: muévelo a la prueba o elimínalo.
R9: el pHash del espejo se calcula solo si `hash.espejo` es true.
R10: pruebas: elimina la que busca cadenas en el código fuente (test_fuga_m2.py:648-652); usa la `_desviacion_en_sigmas` de
particion.py en vez de reimplementarla; renombra la prueba D7 de la semilla 6 para que diga que es un caso fijo de regresión;
`match="fraccion_maxima_grupo"` (o el texto real del error) en vez de `match="15"`; agrega prueba de `estadisticas_vecinos`
contra fuerza bruta.
R11 (menor): nombres completos en vez de alias `dup`/`part`; constante con nombre para `p.CATEGORICA[3]` y para los bins de
duplicados.py:168-169. No toques figs_m3.py.

Entrega con salida real: corrida sin caché (tiempos), corrida con caché, sha256sum de indice.csv (debe ser
fc2b37eb5109658dfc419a6f37a0a601b1dc419110c29df6c8e3e78200a3368d) y huella (9a845cbb…badb3ca), pytest de test_fuga_m2.py y
test_descargar_pesos_m2.py -v, pytest -q -m "not lento", `git status --short` (sin archivos de M3), longitud de `main`.
