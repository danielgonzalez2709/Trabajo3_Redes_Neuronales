# Respuesta literal del implementador (Sonnet) — JJ-1b (B1–B7) — 2026-11-25

Prompt: `alucinaciones/prompts/JJ-1b-implementador.md`. Copiado sin cambios del informe final del subagente.

---

JJ-1b (B1–B7) está terminado. `pytest -q -m "not lento"` da 364 pasadas, y `run.py m3-datos` produce las 6 salidas con SHA-256 idénticos en dos corridas. No hice commit, push ni PR. Las cifras de `ficha.json` coinciden con las de la fase A.

## 1. Archivos

**Creados**
- `C:\Repositorios\Trabajo3_Redes_Neuronales\tests\test_datos_m3.py` (35 pruebas)
- `C:\Repositorios\Trabajo3_Redes_Neuronales\tests\fixtures\m3\`: los 4 CSV ficticios con las mismas columnas y orden que los reales, y `kaggle_metadata_prueba.json`.
- `C:\Repositorios\Trabajo3_Redes_Neuronales\configs\m3\datos.yaml`
- `C:\Repositorios\Trabajo3_Redes_Neuronales\src\m3_recomendacion\datos.py`
- Salidas generadas:
  - `data/processed/m3/{destinos,usuarios,interacciones}.parquet`
  - `results/data/m3/eda/{ficha.json,calidad.csv,diccionario.json}`

**Modificados**
- `src/m3_recomendacion/README.md` (B6)
- `data/fuentes.md` (sección `## M3` al final; la de M1 no se tocó)
- `blog/references.bib` (entrada `@dataset{mehra2024}`, con finales de línea CRLF como el resto del archivo)
- `docs/investigacion/JJ-1_verificacion_A3.md` (línea ~16 y, además, línea ~134)
- `docs/investigacion/JJ-1_fuentes_m3.md` (§3.2)
- `alucinaciones/evidencias/JJ-1a/redescarga_A3/indice_licencias.txt` (línea añadida)

**Eliminados**
- `redescarga_A3/licencia_mit.html` y `redescarga_A3/licencia_cc0.html`

No toqué `respuesta-*.md` ni nada de `src/comun/`, `run.py`, `requirements.txt` o los archivos del orquestador. `docs/spec/partes/juanjose.md` ya figuraba modificado en el `git status` inicial; no es mío.

## 2. Pruebas

**En rojo, antes de `datos.py`:**
```
ImportError while importing test module '...\tests\test_datos_m3.py'.
tests\test_datos_m3.py:26: from src.m3_recomendacion import datos as dm
E   ImportError: cannot import name 'datos' from 'src.m3_recomendacion'
ERROR tests/test_datos_m3.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!
1 error in 5.31s
```

**En verde:**
```
tests/test_datos_m3.py: 35 passed in 9.18 s
.venv\Scripts\python -m pytest -q -m "not lento"  ->  364 passed in 49.99s
```

**Cobertura de las pruebas:**
- Unión sin pares repetidos ni perdidos; par repetido en un archivo o entre los dos → `ValueError`.
- Ids huérfanos de usuario y de destino → `ValueError`.
- `Name`, `Email` y `ReviewText` no aparecen en ninguna salida (ni en columnas ni en valores ni en los bytes de los archivos).
- Escala, densidad con los dos denominadores y usuarios por número de interacciones, contra un conteo a mano escrito en la prueba.
- Normalización de «Beaches, Historical» y columnas `pref_<opcion>`.
- `lugar` agrupa los ids del mismo nombre; nombre con dos combinaciones → `ValueError`; dos nombres con la misma clave → `ValueError`.
- `ficha.json` pasa `validar_ficha` y trae `conteos`, `real_o_sintetico` y `licencia`.
- Cita de la config que no es subcadena de la descripción → `ValueError`; también falla si la fecha de la versión no coincide con el JSON o si la fuente llegara a documentar columnas.
- Archivo faltante → `FileNotFoundError`; SHA-256 distinto → `ValueError` que nombra el archivo; en ambos casos no se escribe nada.
- Determinismo (mismos bytes en las 6 salidas) y que `main` no usa la red.
- Funciones auxiliares: `periodo_minimo` y `chi2_y_v` con casos a mano.

**Dos corridas de `run.py m3-datos --config configs/m3/datos.yaml`** (2.3 s; las dos dieron exactamente los mismos SHA-256):
```
064bd2dbe130fffaa0595d2183721bce11a3746915da28614689cbedf1dcb6b8  data/processed/m3/destinos.parquet
c55e0981ca7b66c06c68972ad5ba025c9855ea9d18b38d040514278aa58e4f52  data/processed/m3/interacciones.parquet
8135ee4a7382c05e43cc938a692e998c22ed4f6dc238e7e802992037a0569c7e  data/processed/m3/usuarios.parquet
7e217a72ca4f5a647e3834fe46d0870ffac3fe4c7aacba3e416749fff852f328  results/data/m3/eda/calidad.csv
9856d77852b1eaa2221d0b5fc7ed4ae3ce6b42e1d57acb6b79a7c69c91ffc2f9  results/data/m3/eda/diccionario.json
76791bbf4d94b1a3babb93c158fe41ffa2b6784df07035e9a21ee2d790cd8c1d  results/data/m3/eda/ficha.json
```
Busqué en `data/processed/m3/` y `results/data/m3/` nombres, correos y textos de reseña reales (`example.com`, «Aanya», «Kavya», los 3 textos): no aparece ninguno.

## 3. Cifras de `ficha.json` (calculadas por el código)

- **Maestras:** 999 usuarios, 1 000 destinos, 5 lugares; `n_variables` = 23 (6 + 5 + 5 + 7).
- **Interacciones:** reseñas 999, historial 999, unión 1 998.
- **Que aparecen:** usuarios 624 / 642 / 858; destinos 651 / 638 / 866.
- **Escalas:** reseñas 1–5 con frecuencias 198/199/185/216/201; historial 1–5 con 206/228/201/183/181; unión 404/427/386/399/382.
- **Densidad:**

| | Maestras | Los que aparecen |
|---|---|---|
| Reseñas | 0.001000 | 0.002459 |
| Historial | 0.001000 | 0.002439 |
| Unión | 0.002000 | 0.002689 |

- **Usuarios por número de interacciones:**

| Interacciones | 0 | 1 | 2 | 3 | 4 | 5+ |
|---|---|---|---|---|---|---|
| Unión | 141 | 252 | 280 | 195 | 79 | 52 |
| Reseñas | 375 | 355 | 190 | 58 | 15 | 6 |
| Historial | 357 | 384 | 180 | 60 | 16 | 2 |

  Con la unión, 858 − 252 = 606 usuarios tienen 2 o más interacciones.
- **Señales:**
  - 5 lugares con 200 ids cada uno.
  - 3 textos de reseña distintos.
  - `VisitDate` con 3 valores y 666 de 999 filas posteriores a 2024-01-23.
  - 20 nombres para 999 usuarios; 999 de 999 correos son nombre en minúsculas más dominio.
  - 3 combinaciones de preferencias.
  - Menor k tal que la columna es función exacta de `id mod k`: nombre de destino 5, `ReviewText` 3, `VisitDate` 3, `Preferences` 3.
  - `palabra_synthetic_en_la_fuente` = false.
- **`ReviewText` contra el lugar reseñado:** V de Cramér = 0.043 y χ² p = 0.884, igual que en la fase A.
- **Licencia:** `campo_formal` = ["MIT"], y la contradicción con «License» (CC0) y «Usage» queda con las citas literales.
- **Vocabularios:** solo `Beaches` está en `Preferences` y no en `Type`; solo `Beach` está en `Type` y no en `Preferences`.

## 4. Decisiones mías, lo que se desvía del diseño y lo que debe decidir Juan José

1. **Claves de config añadidas.** Son `ficha.tope_usuarios_por_interacciones` (5), `ficha.k_max_periodicidad` (10), `ficha.palabra_sintetico` («synthetic»), `ficha.tipo_mencionado_sin_datos` («mountain») y `fuente.lectura_licencia`. Esta última es el texto de §3.2 sobre «las tres permiten el uso no comercial»; es opcional. Las cuatro primeras son obligatorias en `ficha`, y esas dos palabras son parámetros de análisis, no datos de la fuente.
2. **Formas que elegí para algunas claves.**
   - `periodo` es un texto, no un dict como en M1.
   - `licencia.campo_formal` es una lista (`info.licenses[].name` puede traer varias).
   - `diccionario.json` lleva `inconsistencias` como lista de `{id, se_presenta, descripcion, medido}`, con 6 ids: `tipo_mountain_ausente`, `ids_vs_lugares`, `visitdate_periodica_y_posterior`, `reviewtext_plantilla`, `vocabularios_preferencias_vs_type`, `licencias_contradictorias`.
   - El campo `descripcion` de cada inconsistencia es texto fijo; `se_presenta` es el que dice si la medición la confirma.
3. **«ReviewText sin relación con el destino».** El código mide V de Cramér y p contra el lugar reseñado, y la ficha y el diccionario escriben solo esas cifras, sin el adjetivo. Dejé que el lector concluya «sin relación»; si prefieres escribirlo con todas las letras, hay que decidirlo tú.
4. **`periodo_minimo`.** Es trivial cuando k es mayor o igual que el número de filas. Con los datos reales (999 o más filas y k ≤ 10) no afecta; en el fixture sí, y las pruebas lo tienen en cuenta.
5. **Preferencias.** `combinaciones_de_preferencias` cuenta las combinaciones ya normalizadas (en los datos reales son 3, igual que sin normalizar). `Preferences` se mide sobre el texto crudo para la periodicidad.
6. **B7, línea extra.** Además de la línea ~16 de `JJ-1_verificacion_A3.md`, la línea ~134 decía «Guardados en `redescarga_A3/`». La ajusté para que no apunte a archivos borrados.
7. **Alucinación mía, ya corregida y apta para `registro.md`.** Al editar con scripts desde el shell se me coló un carácter de retroceso (`\x08`) en lugar de `\b` en una regex de `datos.py`. Es el mismo tipo de error que H-01 (la marca `\bibliografia`). Lo encontré con `od -c` y `grep -P "\x08"`; ya no hay ninguno en `datos.py`, `fuentes.md`, `references.bib` ni el YAML. No toqué `registro.md`; decide si lo registras.
8. **Una búsqueda mía sigue en segundo plano.** Un `grep -r` sobre todo el repo (comando que lancé al buscar referencias a los archivos de licencia, ID `by2xmu726`) superó el tiempo límite. Solo lee archivos y no escribe nada; terminará solo.
