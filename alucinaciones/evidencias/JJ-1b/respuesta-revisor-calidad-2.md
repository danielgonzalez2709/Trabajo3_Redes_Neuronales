# Respuesta literal de R2 (revisor-calidad, Haiku), segunda revisión — JJ-1b — 2026-11-25

Prompt: `alucinaciones/prompts/JJ-1b-revisor-calidad-2.md`. Copiado sin cambios del informe final del subagente.

---

VEREDICTO: APROBADO, con una condición de PR (ver N1). Ningún bloqueante queda abierto en el código.

Rutas: D = C:\Repositorios\Trabajo3_Redes_Neuronales\src\m3_recomendacion\datos.py ; T = C:\Repositorios\Trabajo3_Redes_Neuronales\tests\test_datos_m3.py ; C = C:\Repositorios\Trabajo3_Redes_Neuronales\configs\m3\datos.yaml

MEDICIONES
- .venv\Scripts\python -m pytest -q tests/test_datos_m3.py: 52 passed en 8,7 s.
- run.py m3-datos --config configs/m3/datos.yaml: EXIT 0, "Tiempo de ejecución: 1.5 s" (límite 10 s). Usuarios 999, destinos 1000, interacciones 1998.
- sha256 de las salidas tras mi corrida: diccionario.json 6ae2b0d8…, ficha.json 7919a3f1…, destinos/interacciones/usuarios.parquet y calidad.csv sin cambio. Coinciden con la respuesta del implementador.

CIERRE DE B1–B5
- B1 (constantes COLUMNAS_USUARIOS_*): cerrado; ya no aparecen en D.
- B2 (parámetros usuarios/destinos en construir_diccionario): cerrado; firma D:585-586 y llamada D:665 coherentes.
- B3 (licencia duplicada): cerrado; _inc_licencias (D:455-464) usa formal_en_license (D:490).
- B4 (prueba vacía de lectura_licencia): cerrado; T:333-350 exige marca única en «Usage» y la frase completa igual a la plantilla. Esta prueba sí puede fallar.
- B5 (aserción «no comparten»): cerrado; no queda en T ni en D.

RECOMENDADOS APLICADOS
- R1: cerrado. leer_csv (D:155-156) rechaza CSV sin filas y hay prueba directa (T:525-529).
- R2: cerrado. Parametrizada de 7 casos de error (T:505-522) y separar_opciones parametrizada (T:532-539).
- R4: cerrado, con la condición de N1.
- R5: cerrado. Id tipo_buscado_ausente (D:405); la palabra sale de la config (D:471).
- R6: cerrado. columnas_documentadas (D:185-187) la usan verificar_citas (D:212) y el diccionario (D:619).
- R7: cerrado. Una sola clasificar_tipo (D:321-332) para ficha y diccionario; prueba de coincidencia en T:398-401.
- R8 (solo inconsistencias): cerrado. Seis funciones _inc_* cortas (D:401-464) y ensamblado en D:467-476.
- R9: cerrado. Desaparecen «Sin fechas reales» y «dice otra cosa»; periodo lista columnas medidas (D:516-525); ids_vs_lugares y tipo_buscado salen de lo medido.
- R11: cerrado. RESENA/HISTORIAL en D:43.
- R12: cerrado. conteos_por_texto se calcula una vez en senales (D:368) y lo usan el diccionario (D:603) y _inc_review_text (D:442).
- O2: cerrado. C:4 dice D1–D6 y D7 de proceso.
- O6: cerrado. texto_periodicidad (D:392-397) dice «constante» y T:454-464 lo prueba.
- O7: cerrado. Docstrings en escala, clasificar_tipo, describir_contenido, construir_ficha, construir_diccionario; tipos en construir_ficha (D:528-529) y construir_diccionario (D:585-586).
- O9: cerrado. «fase A» ya no aparece en mensajes de error de D ni de T.

NO APLICADOS, FUERA DE ALCANCE (sin hallazgo): R3, R10, O1, O3, O4, O5, O8, O10.

HALLAZGOS QUE QUEDAN
N1 (condición de PR, no de código). T:542-549 (prueba R4) lee C y docs/investigacion/JJ-1_kaggle_metadata.json. Según git status, C, el JSON y tests/fixtures/m3/ están sin versionar (??). Si el PR no los incluye, CI falla con FileNotFoundError en esa prueba. Incluirlos en el mismo PR.
N2 (recomendado, decidir y documentar). Asimetría entre columnas constantes: VisitDate constante no se marca (D:424, se_presenta = (k > 1) or post > 0; T:454-464 lo fija), mientras ReviewText constante sí se marca (D:438, textos_distintos < filas). Son el mismo tipo de señal de plantilla. Unificar o dejar escrito por qué.
N3 (opcional). D:471 y D:475 calculan sorted(destinos["tipo"].unique()) dos veces. Calcularlo una vez y pasarlo.
N4 (opcional). Texto de salida: D:462 mete la palabra `medido` con backticks en prosa de la salida; D:424 y D:521-522 generan «1 valores distintos» cuando la columna es constante.

Sobre los pasos: corrí pytest y run.py m3-datos. El segundo regenera data/processed/m3 y results/data/m3/eda con hashes idénticos. No modifiqué archivos del repo.
