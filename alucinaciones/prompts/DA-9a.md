# Prompt DA-9a — redactor-tecnico (Sonnet) — 2026-11-24 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/redactor-tecnico.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`; **no hagas commit ni push**).
Usa `.venv\Scripts\python`. Otro agente está editando `app/` al mismo tiempo: **no toques `app/`**. Tampoco `docs/spec/`.

Lee antes: `blog/README.md` (sintaxis de figuras, tablas y citas del hook), `docs/spec/SPEC.md` §0, §5.1, §5.12 y el Anexo
(«Propósito», «Módulo 1 → Datos», «Entregables → 1» y «Cacería»), `docs/investigacion/DA-2_fuentes_m1.md`,
`results/data/m1/eda/{ficha.json,calidad.csv,diccionario.json}`, `data/processed/m1/{resumen_datos.json,rutas.yaml}`,
`data/fuentes.md` y `docs/spec/SPEC.md` §10 (metodología con subagentes).

## Tarea DA-9a — primeras secciones del blog de Daniel (borrador)
1. **`blog/secciones/01-introduccion.md`**: el caso de negocio de la empresa de transporte intermunicipal (los tres retos del
   Propósito del enunciado), qué resuelve cada módulo y la idea de que las redes no siempre son la mejor herramienta (comparación
   justa). Sin cifras de resultados (aún no existen).
2. **`blog/secciones/03-m1-datos-descriptivo.md`**, solo las subsecciones **«Ficha del conjunto»** y **«Diccionario y calidad»**
   de la plantilla común (las demás son de Camila; déjalas con su comentario `pendiente`):
   - Ficha: fuente (Supertransporte, datos.gov.co `eh75-8ah6`), licencia, fecha de consulta, registros y variables del conjunto
     completo, periodo usado (2021–2023) y por qué (2024 casi vacío, 2020 casi sin datos), las 6 rutas con códigos DIVIPOLA y
     nombres del DANE, criterio de selección, los cuatro conteos (registros del conjunto, registros crudos de las 6 rutas,
     filas agregadas, filas de la serie). Una **tabla** con las rutas y otra con los conteos.
   - Diccionario y calidad: **tabla** con las 10 variables y su descripción **literal** de la fuente (copiada de
     `diccionario.json`, entre comillas); **tabla** de inconsistencias diccionario vs. datos; cómo se agregan los registros,
     cómo se tratan los días sin registro (0 con marca, mayo de 2021) y las reglas de anómalos (R1–R4 con sus ecuaciones en LaTeX,
     idénticas al docstring de `src/m1_demanda/datos.py`) con la tabla de días marcados por ruta; la nota de que las marcas
     miran el futuro y no entran a los modelos.
   - Toda cifra con su archivo de origen en el texto o en la fuente de la tabla. Ninguna cifra que no esté en esos archivos.
3. **`blog/references.bib`**: agrega solo las entradas de los dos conjuntos de datos (Supertransporte `eh75-8ah6` y DANE
   DIVIPOLA `gdxc-w37w`) con los datos exactos de las citas APA del informe `DA-2_fuentes_m1.md` (tipo `@misc` o `@dataset`
   según soporte el hook; URL y fecha de consulta). Nada de memoria. Cítalas en 03.
4. **`blog/secciones/11-uso-ia.md`**: borrador de la parte metodológica (sin la lista final de prompts): Spec Driven + Subagent
   Driven Development, el flujo implementador → revisor-spec → revisor-calidad → verificador, la tabla de agentes con su modelo
   (núcleo §10.3) y por qué se escogió cada nivel, dónde se guardan los prompts literales (`alucinaciones/prompts/`) y ejemplos
   reales de lo que los revisores detectaron en DA-1 y DA-3 (léelos en `alucinaciones/prompts/DA-1-revision.md`,
   `DA-3-revision.md`, `docs/investigacion/DA-3_auditoria_fugas.md` y los commits `git log`). Marca con
   `<!-- revisar: Daniel -->` todo juicio sobre el impacto.
5. **`blog/secciones/13-reproducibilidad.md`**: instalación (ruta corta en Windows, `.venv\Scripts\python`), comandos que ya
   funcionan, semillas, datos procesados en el repo y cómo se reconstruyen (`scripts/descargar_m1.py`), CI. Lo pendiente con
   comentario.

## Aceptación
`.venv\Scripts\python -m mkdocs build --strict -f blog/mkdocs.yml` sin errores y `.venv\Scripts\python -m pytest -q
tests/test_blog.py` en verde (pega las salidas). No se rompe la estructura de 7 subsecciones de 03.

## Reglas
Tono técnico y claro en español; nada inventado; ninguna figura sin generar (si una figura haría falta, deja
`<!-- pendiente: figura … -->`). Entrega: archivos cambiados, salidas reales y la lista de afirmaciones que Daniel debe revisar.
