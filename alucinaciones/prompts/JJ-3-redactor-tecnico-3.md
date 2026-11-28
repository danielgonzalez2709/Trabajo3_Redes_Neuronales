# JJ-3 — 3.ª vuelta del orquestador (Opus 5.5) al redactor-tecnico (Sonnet), 2026-11-26

El revisor-spec rechazó el blog por **rutas y nombres de archivo dentro de las frases**. Regla de Juan José: «Sin rutas de
archivos dentro de las frases (las rutas van en la línea «Fuente:» de la tabla)». Corrige SOLO esto en
`blog/secciones/07-m3-recomendacion.md` (sin commits, sin cambiar cifras ni contenido):

- En la subsección «### Partición»: quita de las frases las menciones `(resumen.json, semilla …)`, `(resumen.json,
  sha256.huella; …)`, `(resumen.json, conteos.usuarios_sin_interacciones_no_evaluables)`, `(resumen.json, diagnosticos)` y
  cualquier otra referencia a un archivo o clave de JSON dentro del texto corrido. Esas referencias van en la línea «Fuente:»
  de `m3-particion-final`. Si una cifra del texto no está en esa tabla (semilla, huella, diagnósticos de destinos fríos y de
  lugar, 141 no evaluables), amplía la línea «Fuente:» de la tabla para nombrar las claves de las que salen (o, si queda más
  claro, agrega una segunda tabla pequeña `::: tabla m3-particion-diagnosticos` con Título y Fuente y cítala con
  `[[tab:m3-particion-diagnosticos]]`). Las referencias a decisiones (D3, D8…) y a «núcleo §6» sí pueden quedar.
- En «#### Implicaciones para el modelado», punto (a): quita las rutas `results/data/m3/eda/actividad_usuarios.json`
  (`particion_d3.total`) y `results/data/m3/particion/resumen.json` (…) de la frase; di la coincidencia en palabras y remite a
  la tabla de la subsección «Partición», cuya «Fuente:» ya nombra el archivo (agrega ahí `actividad_usuarios.json`,
  `particion_d3`, como comprobación).
- No toques el resto de la sección (las partes de JJ-2 siguen su propia convención).

Aceptación: `NO_MKDOCS_2_WARNING=1 .venv/Scripts/mkdocs build --strict -f blog/mkdocs.yml` y
`.venv/Scripts/python -m pytest -q tests/test_blog.py` en verde, y `awk '/^### Partición/,0'` sobre el archivo sin ninguna
mención a `.json` fuera de las líneas «Fuente:». Entrega el diff y la salida real.
