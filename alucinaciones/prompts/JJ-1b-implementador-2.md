# Prompt JJ-1b (correcciones de R1) — implementador (Sonnet), mismo agente — 2026-11-25 — orquesta: Juan José

El revisor-spec RECHAZÓ la entrega (informe literal: `alucinaciones/evidencias/JJ-1b/respuesta-revisor-spec-1.md`). Corrige
solo esto, con las mismas reglas que antes (sin commit ni push; `.venv\Scripts\python`; prueba primero; solo tus archivos):

1. **B-1 (bloqueante).** La frase «y todas piden citar la fuente» es falsa: solo la sección «Usage» pide citar; «License» (CC0)
   no lo pide. Elimina la clave `fuente.lectura_licencia` de `configs/m3/datos.yaml` y su uso en `datos.py`: el texto de
   `licencia.contradiccion` debe salir solo de lo leído del JSON (campo formal, «License», «Usage») y de la comparación que ya
   hace el código, sin interpretaciones normativas. En `data/fuentes.md` (sección M3, fila Licencia) borra «y piden citar la
   fuente» y deja: «Para este trabajo académico no comercial las tres permiten el uso; solo la sección «Usage» pide citar la
   fuente.» (Yo ya corregí `docs/investigacion/JJ-1_fuentes_m3.md` §3.2; no lo toques.) Agrega una prueba de que
   `licencia.contradiccion` no contiene texto que no venga del JSON o del código (p. ej., que no aparece «piden citar»).
2. **B-2 (bloqueante).** En `vocabularios_preferencias_vs_type`, la `descripcion` debe derivarse de lo medido
   (`solo_en_preferencias`, `solo_en_type`, `en_ambos`): p. ej. «4 de 5 opciones de Preferences coinciden con valores de Type;
   difieren solo Beaches (Preferences) y Beach (Type): cruzarlos exige un emparejamiento que es supuesto nuestro, no de la
   fuente.», con los números y etiquetas calculados. Agrega una prueba con el fixture.
3. **M-3.** Copia la asociación de `ReviewText` con el lugar del destino (V de Cramér y p, ya calculadas) a
   `real_o_sintetico.senales_medidas.resenas` de la ficha.
4. **M-4.** Si `palabra_synthetic_en_la_fuente` resulta verdadera, `main` debe fallar con un error claro que pida revisar
   `conclusion_real_o_sintetico` (el texto de la config afirma que la fuente no usa esa palabra). Prueba con el fixture.

Luego: corre `tests/test_datos_m3.py`, `run.py m3-datos --config configs/m3/datos.yaml` dos veces (SHA-256 iguales entre
corridas) y `pytest -q -m "not lento"` completo. Entrega: archivos tocados, las salidas reales y los nuevos SHA-256 de las 6
salidas.
