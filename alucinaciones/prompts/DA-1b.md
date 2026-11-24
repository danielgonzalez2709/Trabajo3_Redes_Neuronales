# Prompt DA-1b — implementador (Sonnet) — 2026-11-24 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/implementador.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`; **no hagas commit ni push**).
Usa el entorno `.venv` que ya existe (`.venv\Scripts\python`); no instales ni cambies `requirements.txt` (si falta un paquete,
repórtalo). Referencia para portar (solo lectura, Trabajo 2 del mismo equipo):
`C:\Users\danie\AppData\Local\Temp\claude\4dc77ad0ee14e84c\6f603fae-d809-443f-a910-1822e4048a3e\scratchpad\t2repo`.

Lee antes: `docs/spec/SPEC.md` §3 (fila Blog), §5.12 y el Anexo («Entregables → 1. Reporte técnico»), y
`docs/spec/partes/daniel.md` §3.4.

## Tarea DA-1b — infraestructura del blog (parte de DA-1)
1. Portar `t2repo/blog/` a `blog/`: `mkdocs.yml`, `hooks/reporte.py`, `apa.csl`, `docs/javascripts/katex.js`,
   `docs/stylesheets/ds.css`, `docs/index.md`, `README.md`. Adaptar `mkdocs.yml`: `site_name` «Redes neuronales y algoritmos
   bioinspirados. Trabajo 3», `site_url: https://danielgonzalez2709.github.io/Trabajo3_Redes_Neuronales/`, `repo_url` y
   `repo_name` del Trabajo 3, navegación con las secciones de abajo.
2. `blog/references.bib` **vacío** (solo un comentario de encabezado). No copies referencias del Trabajo 2 ni inventes ninguna.
3. Esqueleto de secciones en `blog/secciones/` (un archivo por sección, solo títulos, subtítulos y un comentario
   `<!-- pendiente: <dueño> (<ID>) -->`, sin contenido inventado):
   `00-resumen` (Daniel) · `01-introduccion` (Daniel: caso de negocio de la empresa) · `02-fundamentos-comunes` (Juan José) ·
   `03-m1-datos-descriptivo` (Daniel y Camila) · `04-m1-redes` (Andrés) · `05-m1-operacion` (Camila) · `06-m2-conduccion`
   (José) · `07-m3-recomendacion` (Juan José) · `08-app` (Daniel) · `09-discusion` (todos) · `10-etica` (Camila) ·
   `11-uso-ia` (Daniel) · `12-caceria` (Andrés) · `13-reproducibilidad` (Daniel).
   En 03, 06 y 07 la subsección «Análisis descriptivo» lleva **las siete subsecciones de la plantilla común** del núcleo §5.12,
   con esos nombres y en ese orden: Ficha del conjunto · Diccionario y calidad · Variable objetivo · Estructura y
   heterogeneidad · Hipótesis explícitas · Implicaciones para el modelado · Veredicto de las hipótesis.
   En 00 o en `docs/index.md` deja los enlaces a repositorio, app y video promocional (app y video «pendiente»).
4. Portar `t2repo/tests/test_blog.py` (y su fixture `tests/fixtures/referencias_prueba.bib` si lo usa) a `tests/`, adaptado.
   Agrega una prueba de que 03, 06 y 07 contienen las siete subsecciones en orden.
5. `.github/workflows/blog.yml` portado (publica en GitHub Pages desde `main`).

## Aceptación
`.venv\Scripts\python -m mkdocs build --strict -f blog/mkdocs.yml` sin errores ni advertencias, y
`.venv\Scripts\python -m pytest -q tests/test_blog.py` en verde (pega ambas salidas).

## Reglas
- Solo tocas `blog/`, `tests/test_blog.py`, `tests/fixtures/` y `.github/workflows/blog.yml`.
- Nada de contenido técnico inventado en las secciones: solo estructura.

Entrega: archivos creados, salidas reales, dudas.
