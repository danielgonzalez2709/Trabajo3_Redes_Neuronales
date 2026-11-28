# Prompt JJ-2 — analista-experimentos (Sonnet), 4.ª vuelta (hallazgos de R3 y un menor de R2) — 2026-11-26 — orquesta: Juan José

Mismas reglas que antes (sin commit/push, `.venv/Scripts/python`, solo tus archivos; **no** toques `src/comun/` ni
`blog/secciones/`). R1 y R2 ya aprobaron los cálculos: este refactor **no puede cambiar ningún número**. Antes de empezar,
guarda los SHA-256 actuales de `results/data/m3/eda/*`; al final, todos los archivos deben ser byte-idénticos **salvo**
`hipotesis.json` y `pruebas_hipotesis.json`, y en esos dos solo pueden cambiar textos (compara cargando los JSON: todos los
valores numéricos idénticos). Usa la herramienta Edit; en Windows, rutas Windows para Python.

## Bloqueantes de R3 (revisor-calidad)
- **B1.** `configs/m3/eda.yaml:71` `ajuste_multiple` no hace nada (Holm fijo en `eda.py:~1210`). Despacha por esa clave
  (solo `holm` soportado; cualquier otro valor → `ValueError` claro) o quítala y deja «Holm» en un comentario. Que la prueba
  verifique el comportamiento (valor desconocido → error), no que se repita el valor.
- **B2.** Config que rompe o miente al cambiarla en vivo:
  - `eda.py:~1093` lee `cuota_top['0.1']` fijo y `~1080` lee `niveles["destino_id"]` y `["lugar"]` fijos: con
    `fracciones_top: [0.2]` o `niveles: [destino_id]` termina en `KeyError`. Toma las claves de la config (mismo formato
    `f"{f:g}"`) o valida al inicio de `main` que las claves que necesitan los textos estén, con error claro **antes** de
    calcular. Prueba: cambiar `fracciones_top` / `niveles` no rompe (o falla al inicio con mensaje claro).
  - `eda.py:566–571`: la justificación del umbral escribe «1 o 2» y «3» a mano; genérala desde `pocas_max`. Prueba con
    `pocas_max: 3`.
- **B3.** Nombres ilegibles en `Datos` (`eda.py:359–421`) y `analizar_h1` (`614–694`): `C, S, R, Rt, Um, Un, Co, Cr, m_u,
  b_u, b2_u, ui, ti, ki, oi, pd_`. Renómbralos a nombres en español que se entiendan solos (p. ej.
  `coincidencias_si_combinacion`, `linea_base_por_usuario`, …) y deja un docstring corto en `Datos` con la forma de cada
  arreglo.
- **B4.** `construir_hipotesis` (`eda.py:938–1149`, 212 líneas): una función por hipótesis (≲ 40 líneas cada una); puedes
  moverlas a `src/m3_recomendacion/eda_hipotesis.py` si eso deja ambos archivos más claros. Calcula `veredicto_de_prueba`
  una sola vez por prueba (hoy se recalcula en ~922, 949 y 956) y reutilízalo.

## Recomendados de R3 que sí van ahora
- **R1.** `figs_m3.py:~67–79, ~193`: el pie de `preferencias_tipo.png` afirma que la suma de las celdas recuadradas es la
  línea base exacta tomando la fila 0; solo vale si todas las combinaciones cubren la misma fracción del catálogo. Calcula
  la fracción por fila y, si difiere entre filas, no afirmes una suma única. Prueba con combinaciones de distinto tamaño.
- **R2.** Combinación sin interacciones → `np.mean([])` → NaN → `save_json` falla al final (`eda.py:319–321`): maneja el
  caso (omitir con aviso claro o error claro al inicio) y pruébalo.
- **R3.** Código muerto y parámetros sin uso (`construir_hipotesis` sin usar `d`/`actividad`; retorno descartado de
  `analizar_h1`; bool de `verificar_contra_ficha` que nadie lee; `()` en `medidas`; `self.cfg`; `pop("_dif_boot")` →
  devuélvelo aparte).
- **R5.** Índices posicionales frágiles (`conf[0]` en ~1223, `efectos_adicionales[0]` en ~1013–1014, 1036): busca por
  `id_prueba` / `nombre`.
- **R7.** Fixture `corrida` de `tests/test_eda_m3.py:91–95` con scope función (main corre ~14 veces): pásalo a
  `scope="module"` con `tmp_path_factory`.
- **R10.** `eda.yaml:72–75` dice que `regla_de_veredicto` es «la ÚNICA fuente» del criterio: ajusta el comentario a la
  verdad (el texto la describe; la implementa `veredicto_de_prueba`; una prueba fija que concuerdan).
- **R11.** `TOLERANCIA = 1e-12` (`eda.py:42`) → `TOLERANCIA_NUMERICA`.
- **R6 (parcial).** La aserción vacía `"no se cita aquí de memoria" not in fuente` (`tests/test_eda_m3.py:~704–707`): quítala
  o hazla útil. Las pruebas que fijan redacción, agrúpalas con un comentario «textos obligatorios» (no hace falta quitarlas).
- **R9 (parcial).** Al refactorizar, deja las líneas ≤ 120 caracteres en lo que toques (como `datos.py`).

## Menor de R2 (verificador-matematico)
- **M1.** En el `resultado` de H-M3-1, la frase «en el límite» nombra el extremo superior del IC (0,0469 frente a 0,05),
  pero el que decide el veredicto es el **inferior** (≈ 0,0006, junto al 0: si fuera ≤ 0, la prueba refutaría). Corrige el
  texto para que diga eso, con las cifras calculadas. (No cambies el criterio de `en_el_limite`; eso lo decide Juan José.)

## No van ahora (dilo en tu informe como pendientes)
R4 (duplicados con `datos.py` y un CSV atómico en `src/comun`, que requiere PR dedicado), R8 (más casos borde), R9 total y
las opcionales.

## Al terminar
`run.py m3-eda` dos veces (pega el tiempo con `time` y los SHA-256, y la comparación con los anteriores), `run.py figures`,
`pytest -q tests/test_eda_m3.py tests/test_datos_m3.py` y `pytest -q -m "not lento"`. Informe: cambios por punto, tamaño
nuevo de los archivos y de la función más larga, y el texto nuevo del `resultado` de H-M3-1.
