# Respuesta literal del implementador (Sonnet), correcciones de R1 — JJ-1b — 2026-11-25

Prompt: `alucinaciones/prompts/JJ-1b-implementador-2.md`. Copiado sin cambios del informe final del subagente.

Nota del orquestador: el punto «nació en mi propio texto» es impreciso; la frase venía de `JJ-1_fuentes_m3.md` §3.2 (fase A,
orquestador) y el implementador la copió en `lectura_licencia`. Ver `licencia_citar/README.md`.

---

Las cuatro correcciones de R1 (B-1, B-2, M-3, M-4) están hechas y verificadas. `pytest -q -m "not lento"` da 366 pasadas. `tests/test_datos_m3.py` queda en 37 pasadas, frente a 35 antes y 5 en rojo al escribir las pruebas nuevas. No hice commit ni push.

## Archivos tocados
- `tests/test_datos_m3.py` (escrito primero; al correrlo, 5 pruebas fallaron)
- `src/m3_recomendacion/datos.py`
- `configs/m3/datos.yaml`
- `data/fuentes.md` (solo la fila Licencia de la sección M3)
- Salidas regeneradas: `ficha.json` y `diccionario.json`. Los 3 parquet y `calidad.csv` no cambiaron.

## Qué cambió
- **B-1.**
  - Quité `fuente.lectura_licencia` del YAML y su uso en `datos.py`. `licencia.contradiccion` ahora sale solo del JSON (campo formal, «License», «Usage») y de la comparación que ya hacía el código: «El campo formal no aparece en la sección «License»: las declaraciones son distintas.».
  - En `data/fuentes.md` quedó: «Para este trabajo académico no comercial las tres permiten el uso; solo la sección «Usage» pide citar la fuente.».
  - No toqué `JJ-1_fuentes_m3.md`.
  - La prueba nueva pone a propósito una clave `lectura_licencia` en la config y comprueba que el código la ignora. También exige que la contradicción no contenga «piden citar» ni «permiten», y que sí contenga el campo formal y las dos citas literales.
- **B-2.** La `descripcion` de `vocabularios_preferencias_vs_type` se deriva de lo medido. En los datos reales dice: «4 de 5 opciones de Preferences coinciden con valores de Type; solo en Preferences: Beaches; solo en Type: Beach. Cruzarlos exige un emparejamiento que es supuesto nuestro, no de la fuente.». Si los vocabularios coincidieran, dice «Las N opciones de Preferences coinciden con los valores de Type.». Hay prueba con el fixture para las dos formas.
- **M-3.** `real_o_sintetico.senales_medidas.resenas.asociacion_con_el_lugar_del_destino` ya está en la ficha, con chi2 = 3.6946, gl = 8, p = 0.8836 y V = 0.0430. Es la misma medición que usa `diccionario.json` y hay prueba de que coinciden.
- **M-4.** Si `palabra_synthetic_en_la_fuente` resulta verdadera, `main` lanza `ValueError` antes de escribir nada. El mensaje pide revisar `conclusion_real_o_sintetico` en la config, porque ese texto afirma que la fuente no usa la palabra. Esto reemplazó la prueba anterior, que esperaba `True` en la ficha. Ahora cubre la palabra en la descripción y en un nombre de archivo, y comprueba que no se escribe nada.

## Corridas
- `run.py m3-datos --config configs/m3/datos.yaml` dos veces: código 0 y SHA-256 idénticos entre corridas.
- Nuevos SHA-256 de las 6 salidas:
```
064bd2dbe130fffaa0595d2183721bce11a3746915da28614689cbedf1dcb6b8  data/processed/m3/destinos.parquet
c55e0981ca7b66c06c68972ad5ba025c9855ea9d18b38d040514278aa58e4f52  data/processed/m3/interacciones.parquet
8135ee4a7382c05e43cc938a692e998c22ed4f6dc238e7e802992037a0569c7e  data/processed/m3/usuarios.parquet
7e217a72ca4f5a647e3834fe46d0870ffac3fe4c7aacba3e416749fff852f328  results/data/m3/eda/calidad.csv
dde9978f44688583fd6ab659297afa5146ed8b26d10d93910806051e694c7d1e  results/data/m3/eda/diccionario.json   (antes 9856d778…)
31d4d888c82f337dfe5731a70b214d4b952326783bd24fdf72a9a273ce28793a  results/data/m3/eda/ficha.json        (antes 76791bbf…)
```

## Para ti
- La falsa afirmación «y todas piden citar la fuente» nació en mi propio texto de `lectura_licencia`, no de un dato verificado. Ya está eliminada de config, código y `fuentes.md`; el revisor pidió registrar el caso en `alucinaciones/registro.md` (lo decides tú).
- Grep de comprobación: ya no queda `lectura_licencia` ni «piden citar» en `configs/`, en `datos.py` ni en `fuentes.md`. En el repo solo aparecen en las pruebas nuevas de `tests/test_datos_m3.py` y en los textos de la revisión.
