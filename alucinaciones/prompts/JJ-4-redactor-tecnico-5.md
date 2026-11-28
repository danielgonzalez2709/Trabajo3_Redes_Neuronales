# JJ-4 — prompt del orquestador (Opus 5.5) al redactor-tecnico (Sonnet), 5.ª vuelta, 2026-11-27

El revisor-spec (R3) señaló que en `blog/secciones/07-m3-recomendacion.md` hay rutas o claves de archivo dentro de las frases:
línea ~579 («`results/data/m3/summary.json`, `n_usuarios_evaluados`») y ~707 («`summary.json`, `evidencia.particion_huella`»).
Las rutas y claves van solo en la línea «Fuente:» de una tabla o en un comentario HTML. Revisa TODAS las frases de «### Métricas de
evaluación» y «### Modelos de referencia» (no solo esas dos) y saca de ellas cualquier ruta, nombre de archivo o clave de JSON
(los nombres de configuración que el lector usaría en un cambio en vivo, como `evaluacion.k`, pueden quedar si son parte de la
explicación). No cambies cifras. Build estricto + `tests/test_blog.py`; informe de 3 líneas.
