# Respuesta literal de R1 (revisor-spec, Sonnet), segunda revisión — JJ-1b — 2026-11-25

Prompt: `alucinaciones/prompts/JJ-1b-revisor-spec-2.md`. Copiado sin cambios del informe final del subagente.

---

**Veredicto de la segunda revisión: APROBADO.** B-1, B-2, M-3 y M-4 quedan cerrados y no encontré nada roto en D1–D7, §5.7 ni §5.12. No hay hallazgos bloqueantes. Solo quedan dos observaciones menores.

## Ejecución (solo lectura)
- `.venv\Scripts\python -m pytest -q tests/test_datos_m3.py` da `37 passed in 9.26s`.
- `.venv\Scripts\python run.py m3-datos --config configs/m3/datos.yaml` termina bien en 1.7 s. Imprime «Interacciones: resena 999 · historial 999 · union 1998» y «Densidad de la unión: 0.002000 (maestras) · 0.002689 (los que aparecen)».
- Los SHA-256 coinciden con los que reportó el implementador.
  - Sin cambios: los 3 parquet (`064bd2db…`, `c55e0981…`, `8135ee4a…`) y `calidad.csv` (`7e217a72…`).
  - Cambiados a propósito: `diccionario.json` (`dde9978f…`) y `ficha.json` (`31d4d888…`).
- No toqué ningún archivo, aparte de regenerar las salidas con la configuración por defecto, que son deterministas.

## Cierre de los hallazgos anteriores
- **B-1 (licencia): cerrado.**
  - `lectura_licencia` ya no está en `configs/`, `src/` ni `results/`.
  - `licencia.contradiccion` en `ficha.json` sale solo del JSON: campo formal «MIT», las secciones «License» y «Usage» literales, y «El campo formal no aparece en la sección «License»: las declaraciones son distintas.».
  - Ya no hay «piden citar» ni «permiten» en esa salida.
  - `data/fuentes.md:150` ahora dice: «las tres permiten el uso; solo la sección «Usage» pide citar la fuente».
  - `JJ-1_fuentes_m3.md` §3.2 (líneas 224-229) dice lo correcto: solo «Usage» pide citar, CC0 no exige atribución y MIT pide conservar el aviso de copyright.
  - La cadena «piden citar» solo aparece en `tests/test_datos_m3.py:330-334`, como aserción negativa de la prueba nueva, que además comprueba que el código ignora una clave `lectura_licencia` ajena.
  - `JJ-1_fuentes_m3.md:227` conserva entre paréntesis la frase vieja («y todas coinciden en pedir que se cite la fuente»), citada como corregida. Es una anotación de procedencia, no una afirmación vigente, pero ese archivo no queda sin rastro de la frase.
- **B-2 (vocabularios): cerrado.** La descripción se deriva de lo medido: «4 de 5 opciones de Preferences coinciden con valores de Type; solo en Preferences: Beaches; solo en Type: Beach. Cruzarlos exige un emparejamiento que es supuesto nuestro, no de la fuente.». Es coherente con `medido`.
- **M-3 (señal de reseñas): cerrado.** `ficha.json` → `real_o_sintetico.senales_medidas.resenas.asociacion_con_el_lugar_del_destino` trae chi2 = 3.6946, gl = 8, p = 0.8836 y V = 0.0430. Son las mismas cifras que el diccionario.
- **M-4 (palabra «synthetic»): cerrado.** `datos.py:604-605` lanza `ValueError` antes de escribir si `palabra_synthetic_en_la_fuente` es verdadera. El texto de la conclusión ya no puede quedar obsoleto sin avisar.

## Verificaciones sin regresión
- **D1 a D7:** siguen cumplidos. D4 en `juanjose.md` ahora dice «3 valores de `VisitDate` de los que 2 —666 de 999 filas— son posteriores», lo que corrige M-5.
- **§5.7 (M-1):** las columnas de `interacciones.parquet` no cambiaron: `usuario_id, destino_id, origen, id_origen, calificacion, fecha_visita`. La nota [PROPUESTO] en `juanjose.md` §3.1 lo documenta y deja la decisión a Juan José. Si la confirma, hay que actualizar §5.7 por un PR dedicado al núcleo. Queda abierto como decisión del humano, no como defecto.
- **§5.12 (M-2):** `ficha.json` trae las 10 claves obligatorias más `real_o_sintetico` y `licencia`, que la nota de `juanjose.md` ya registra. `validar_ficha` las admite.
- **Archivos compartidos:** `git diff --stat` sobre `src/comun`, `run.py` y `requirements.txt` sale vacío.
- **Privacidad (D6):** no la volví a medir en esta pasada. Los parquet y `calidad.csv` no cambiaron, y en la primera revisión busqué nombres, correos y textos de reseña y salieron 0 coincidencias. La prueba `test_name_email_y_reviewtext_no_salen_en_ninguna_salida` sigue en verde.

## Observaciones menores que quedan (no bloquean)
1. **M-1:** decidir `fecha_visita` frente a `fecha` e `id_origen`, y luego el PR de §5.7.
2. **M-6:** el diccionario repite el mismo párrafo del componente en las 23 columnas. Lo dejaste sin cambiar a propósito.
