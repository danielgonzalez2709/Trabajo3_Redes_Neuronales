# Prompt DA-9b — redactor-tecnico (Sonnet) — 2026-11-26 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/redactor-tecnico.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`; **no hagas commit ni push**). Solo
tocas `blog/secciones/08-app.md` (y `blog/references.bib` solo si citas algo con DOI/URL verificable que abriste). Otros
agentes trabajan a la vez en `app/` (página de conducción) y `notebooks/`: no los toques.

## Tarea: borrador de la sección 08 «Aplicación web» del reporte (DA-9)
Fuentes (nada fuera de ellas): el Anexo de `docs/spec/SPEC.md` (apartado «Aplicación web» y Entregables), núcleo §3
(decisiones de la app), §5.4, §5.6 y §5.8; `app/lib/contratos.ts`, `app/lib/*.ts`, las páginas `app/app/*/page.tsx`,
`app/vercel.json`, la sección de la app del `README.md`, y `blog/secciones/01-introduccion.md` y `11-uso-ia.md` para el
estilo. URL pública: https://trabajo3-redes-neuronales.vercel.app/

Contenido (español, primera persona del plural como el resto del blog; sin relleno):
1. Para qué sirve y quién la usa (empresa de transporte intermunicipal): una línea por módulo, ligada a la pregunta de negocio.
2. Arquitectura: sitio estático (Next.js `output: "export"`) en Vercel; toda la inferencia en el navegador (M1 y M3 desde
   JSON, M2 con ONNX Runtime Web, wasm servido por la propia app); ningún dato del usuario sale del navegador; la app nunca
   reentrena.
3. Contratos de exportación (tabla corta: módulo → archivos → qué traen) y por qué existen (paridad Python ↔ navegador; cada
   dueño exporta sin tocar la app). Pruebas de paridad en CI.
4. Una subsección por página con los controles que pide el enunciado (demanda: ruta, pronóstico a 30 días con banda, flota y
   conductores, ocupación objetivo y cuantil; conducción: imagen, probabilidades, clase, alerta con umbral, mapa CAM;
   recomendación: usuario existente o perfil nuevo con lista de preferencias, top-K). Donde el resultado depende de los modelos
   reales, deja `<!-- pendiente: captura y cifras con el modelo real (sáb 28) -->`; **ninguna cifra inventada**.
5. Limitaciones honestas (p. ej. M2 corre en la CPU del navegador; el top-K de usuarios existentes viene precalculado).
Sin figuras todavía (no hay capturas reales): marca dónde irán con comentarios HTML. Las frases que sean interpretación tuya y
no hechos del código o del Spec, márcalas con `<!-- revisar: Daniel -->`. Respeta el formato del hook
(`blog/hooks/reporte.py`: citas, figuras y tablas numeradas; mira cómo lo hacen 01 y 03).

## Aceptación
`.venv\Scripts\python -m mkdocs build --strict -f blog/mkdocs.yml` sin errores y `.venv\Scripts\python -m pytest -q
tests/test_blog.py` en verde. Informe ≤ 20 líneas: qué escribiste, qué quedó pendiente y qué marcaste para revisar.
