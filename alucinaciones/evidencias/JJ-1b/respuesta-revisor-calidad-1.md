# Respuesta literal de R2 (revisor-calidad, Haiku), primera revisión — JJ-1b — 2026-11-25

Prompt: `alucinaciones/prompts/JJ-1b-revisor-calidad.md`. Copiado sin cambios del informe final del subagente.

---

VEREDICTO: RECHAZADO (en terminología del agente: CAMBIOS REQUERIDOS). Son correcciones pequeñas: borrar código muerto, quitar dos parámetros, una línea duplicada y dos aserciones vacías. Ninguna cambia las salidas.

Rutas (leyenda): D = C:\Repositorios\Trabajo3_Redes_Neuronales\src\m3_recomendacion\datos.py ; T = C:\Repositorios\Trabajo3_Redes_Neuronales\tests\test_datos_m3.py ; C = C:\Repositorios\Trabajo3_Redes_Neuronales\configs\m3\datos.yaml ; M1 = C:\Repositorios\Trabajo3_Redes_Neuronales\src\m1_demanda\datos.py ; F = C:\Repositorios\Trabajo3_Redes_Neuronales\tests\fixtures\m3\

VERIFICACIONES EJECUTADAS
- .venv\Scripts\python -m pytest -q tests/test_datos_m3.py: 37 passed en 6,0 s.
- run.py m3-datos --config configs/m3/datos.yaml sobre data/raw/m3: EXIT 0, "Tiempo de ejecución: 1.9 s" (límite 10 s). Usuarios 999, destinos 1000, interacciones 1998.
- Antes y después de correr comparé sha256 de data/processed/m3 y results/data/m3/eda: idénticos (determinismo). Ningún archivo versionado modificado por mí.
- Experimentos en un script de scratchpad (C:\Users\juanj\AppData\Local\Temp\claude\C--Repositorios-Trabajo3-Redes-Neuronales\e3c9a77d-52af-4212-a7d4-efbc2d0ac3bb\scratchpad\edge_m3.py); no toca el repo.
- Sin ruff ni pyflakes en el venv: el código muerto y los parámetros sin uso se comprobaron con grep y AST.

LO QUE ESTÁ BIEN (no rehacer)
- Estructura por secciones (utilidades, entrada y verificación, tablas, medidas, ficha/diccionario, escritura). main() valida todo antes de escribir y la prueba lo comprueba.
- Fixtures pequeños y claramente ficticios (7 destinos, 4+4 filas, nombres «UsuarioPrueba», correos .invalid). Conteo a mano documentado en la cabecera de la prueba.
- Casos borde cubiertos: usuario sin historial (usuario 5), destino sin interacciones (destino 7), pares repetidos en uno y en dos archivos, ids huérfanos, hash distinto, privacidad (Name/Email/ReviewText fuera de las salidas), determinismo, sin red.
- La comprobación de bytes de los .parquet en la prueba de privacidad es válida: un control negativo con «UsuarioPruebaA» la detecta.
- Estilo muy parecido a M1 (mismos nombres de helpers, mismo patrón de fixture y de pruebas de error).

BLOQUEANTES (corregir antes de fusionar)
B1. D:43-44. COLUMNAS_USUARIOS_FIJAS y COLUMNAS_USUARIOS_FINALES no tienen ninguna referencia en el repo. Borrarlas.
B2. D:523 construir_diccionario(cfg, raw, usuarios, destinos, opciones, meta, sen, asoc, incons): usuarios y destinos no se usan en el cuerpo (confirmado con AST). La llamada D:602 los pasa. Quitarlos de firma y de llamada. En vivo, la pregunta «¿qué es usuarios aquí?» no tiene respuesta.
B3. D:389-390 calcula formales y en_license dentro de inconsistencias, igual que formal_en_license (D:442-445). Son dos cálculos que pueden divergir. Usar formal_en_license(meta, cfg) y quitar formales si queda sin uso.
B4. T:329-337 (prueba de licencia). Pasa lectura_licencia=... dentro de c["fuente"]; el código nunca lee esa clave (aparece solo aquí). La prueba pasa siempre y su nombre afirma algo que no comprueba. Borrarla, o reescribirla: poner en citas_literales.uso o licencia un texto único y comprobar que aparece en ficha["licencia"]["contradiccion"] y que no aparecen palabras ajenas.
B5. T:434 assert "no comparten" not in inc["descripcion"]. El código nunca produce esa frase: aserción vacía. Borrar.

RECOMENDADOS
R1. Error críptico con datos vacíos. D:288-291 (escala): int(s.min()) sobre serie vacía lanza «cannot convert float NaN to integer». Reproducido con reseñas.csv que solo tiene cabecera (montar() de la prueba + dm.main). En uso real lo para antes la verificación de SHA, pero la suite no lo cubre. Fix: validar en leer_csv (D:147-153) que hay al menos una fila, con mensaje claro, y añadir la prueba.
R2. Errores sin prueba directa. leer_csv (D:147-153: columnas distintas, NaN); _enteros (D:208-211: Rating = 3.5 da «se esperaban enteros», reproducido, funciona, falta prueba); verificar_citas (D:184-196: faltan claves obligatorias, componente sin fragmento); verificar_archivos (D:137-139: hash sin clave en la config); separar_opciones (D:235-237: el docstring promete quitar repetidas y espacios). Tests con 0 referencias directas: leer_csv, verificar_citas, separar_opciones, _enteros, leer_metadatos. Una prueba parametrizada por caso basta.
R3. Ramas «se_presenta = False» sin prueba: D:392 (palabra mountain presente en Type), D:396 (sin ids duplicados), D:401 (visitdate sin periodicidad ni fechas posteriores), D:410 (reviewtext sin plantilla), D:423 con el campo formal presente en License (rama D:452-453, texto distinto). Solo se prueba el caso verdadero. Un caso por rama con fixture mínima.
R4. La config no está protegida en CI. Nada en la suite comprueba C contra docs/investigacion/JJ-1_kaggle_metadata.json (los CSV no están versionados, así que CI no corre la carga real). Comprobé a mano que verificar_citas pasa con la config real y el JSON versionado. Añadir una prueba sin red que lea C y el JSON y llame a verificar_citas: si alguien cambia un fragmento, falla en CI.
R5. Id atado a un valor de la config. D:392 «tipo_mountain_ausente» ignora ficha.tipo_mencionado_sin_datos (C:76). Si cambian la palabra, el id y la prosa mienten. Usar un id genérico (p. ej. tipo_buscado_ausente) y la palabra desde el medido.
R6. Cifra escrita a mano en la salida: D:561 "columnas_documentadas_por_la_fuente": 0. Contradice el contrato de la cabecera (D:17: «Toda cifra de las salidas la calcula este módulo»). El valor es correcto porque verificar_citas aborta si no lo es, pero debe calcularse: sum(len(f.get("columns") or []) for f in meta["archivos"]).
R7. Clasificación de tipos duplicada con etiquetas distintas: describir_contenido (D:309-322) y tipo_medido (D:325-334) clasifican igual con vocabularios distintos (booleana/booleano, entera/entero, continua/decimal, categorica/texto). La ficha y el diccionario dan dos nombres a la misma columna. Una sola función de clasificación.
R8. Funciones largas de difícil explicación: inconsistencias (D:377-428, 52 líneas, seis diccionarios literales) y construir_ficha (D:458-511, 54 líneas, 8 parámetros sin tipo). Propuesta: una función corta por inconsistencia que devuelva su dict, e inconsistencias solo las ensambla.
R9. Frases fijas que afirman sin medir: D:469 «Sin fechas reales» y D:424-425 «y la sección «Usage» dice otra cosa» se emiten siempre, sin depender de los datos. Redactarlas desde lo medido o marcarlas como interpretación.
R10. Duplicación entre módulos (no bloquea esta tarea; PR dedicado a src/comun/, avisando a quien tiene M1): sha256 (D:72-77 = M1:94-99); _escribir_parquet (D:568-572 = M1:451-455); reindexado de columnas de calidad (D:519-520 = M1:587-588); test_main_no_usa_la_red (T:508-515 = test de M1 en tests/test_datos_m1.py:448-455).
R11. Índice mágico: D:265 y D:269 usan ORIGENES[0] y ORIGENES[1]. Nombrarlos (RESENA, HISTORIAL = ORIGENES) o usar las cadenas.
R12. Cálculo repetido: conteos de ReviewText en D:387 y D:530; n_textos y n_filas (D:529) ya están en sen["resenas"].

OPCIONALES
O1. Claves de C no leídas por el código: C:27 (usuario_kaggle), C:30 (version), C:33 (descargo). Son documentación; o validar version contra versions[0].versionNumber del JSON.
O2. Desalineación: C:4 dice «Decisiones D1–D7»; la cabecera de D (D:8-15) lista D1–D6. D7 es de proceso (docs/spec/partes/juanjose.md §3.1). Alinear el texto.
O3. Nombres: senales (D:341) sería más claro como medir_senales_generadas. Abreviaturas res (reseñas, choca con «resultado»), hist, usr, fic, asoc, incons: coherentes con M1, pero explicarlas en vivo cuesta.
O4. T:417-419 y T:433 fijan prosa completa; se rompen al editar un texto. Comparar con fragmentos o con cifras.
O5. Redundancias y legibilidad: T:155-158 repite lo que construir_interacciones ya garantiza (D:274-279); T:218 test_name_email… recibe tmp_path sin usarlo; T:117 «4 + 4 == len(esperados)» es menos legible que escribir 8.
O6. Columna constante: periodo_minimo devuelve k=1 (D:102-110) y la ficha dice «función exacta de … mod 1» (D:404, 412, 471). Sin prueba de ese flujo. El texto debería decir «constante».
O7. Docstrings: faltan en escala, describir_contenido, tipo_medido, construir_ficha, construir_diccionario (la pregunta en vivo es qué produce cada una). Faltan tipos de DataFrame en construir_ficha (D:458) y construir_diccionario (D:523).
O8. Estructura: inconsistencias, descripcion_vocabularios, formal_en_license y texto_contradiccion (D:377-454) viven bajo el banner «medidas de la ficha» (D:287) pero redactan diccionario y ficha. Mover a su propia sección.
O9. Jerga interna en mensajes de error: D:152 y D:261 dicen «la fase A midió 0». Un estudiante no sabe qué es la fase A. Redactar el motivo.
O10. fecha_descarga es manual (C:32, usada en D:481). M1 la deriva del log (M1:603-624). Aquí no hay log: al menos documentarlo en la ficha.

SOBRE LOS PASOS
Ejecuté run.py m3-datos, que regenera data/processed/m3 y results/data/m3/eda: con hashes idénticos a los existentes. pytest creó caché de Python en el repo; no se tocó ningún archivo fuente ni de configuración.
