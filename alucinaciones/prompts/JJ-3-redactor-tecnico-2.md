# JJ-3 — 2.ª vuelta del orquestador (Opus 5.5) al redactor-tecnico (Sonnet), 2026-11-26

Corrige la subsección «### Partición» de `blog/secciones/07-m3-recomendacion.md` (mismas reglas de la 1.ª vuelta; solo ese
archivo; sin commits). Dos hallazgos:

1. **«El lugar ya se conoce» es falso tal como está.** El auditor-fugas midió que la coincidencia de lugar es la esperable por
   azar: 204 de 606 usuarios de prueba tienen otro id del mismo lugar en su historial conocido, y el azar predice 198,0
   (`resumen.json`, `diagnosticos.mismo_lugar_en_historial_conocido.prueba.esperado_por_azar`; en validación 95 frente a
   95,8). Con 5 lugares es lo normal, y un modelo no sabe cuál de sus lugares conocidos es el del objetivo, así que NO es un
   acierto «trivial» ni «resuelto de antemano». La frase la sembró el prompt del orquestador; corrígela. Reescribe ese punto
   y el párrafo final («La consecuencia práctica…») para decir: qué se cuenta; que es lo esperable por azar con 5 lugares
   (cita `esperado_por_azar` y el supuesto de `supuesto_esperado_por_azar`); y que, por eso, todo acierto por lugar se
   compara con su línea base del azar y la métrica principal es la de `destino_id`. Lee la nueva `definicion` del JSON y no
   la contradigas. Mantén el comentario `revisar` del acierto por lugar (JJ-6).
2. **Usuarios sin interacciones.** El texto dice que los 141 «sirven más adelante para el escenario de usuario nuevo». No
   tienen interacciones con qué medir: cambia a que no se evalúan y que, como mucho, sirven para mostrar recomendaciones sin
   métricas; la medición de usuarios nuevos (pregunta de negocio 1) se decide en JJ-6. Agrega
   `<!-- revisar: Juan José — D10 dice que los 141 sirven para el escenario de usuario nuevo; sin interacciones no hay con qué medir; decidir en JJ-6. -->`.
3. Añade una frase: como la validación solo tiene usuarios de «muchas», los hiperparámetros se eligen con ese grupo
   (sesgo de selección a tener en cuenta al comparar grupos).

Recalcula los porcentajes que dejes con las cifras del JSON. Aceptación: `NO_MKDOCS_2_WARNING=1 .venv/Scripts/mkdocs build
--strict -f blog/mkdocs.yml` y `.venv/Scripts/python -m pytest -q tests/test_blog.py` en verde. Entrega el texto nuevo y la
salida real.
