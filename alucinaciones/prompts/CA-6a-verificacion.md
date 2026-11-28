# Prompt CA-6a-verificacion — cazador-alucinaciones (Opus) — 2026-11-27 — orquesta: Camila

Repo /Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales, rama dev/camila. Verifica de forma adversarial el
informe `docs/investigacion/CA-6_costos_flota.md`, generado por un `investigador-fuentes` (Sonnet) con el prompt literal
`alucinaciones/prompts/CA-6a.md`. Para qué se usará: la pregunta de negocio 4 de M1 (enunciado en `docs/spec/SPEC.md`, Anexo,
«Módulo 1 → Preguntas de negocio», punto 4): vehículos y conductores adicionales en temporada alta y recomendación de flota
propia, arrendada o convenio. Referencia de cómo se verificó un informe parecido: `docs/investigacion/CA-2_verificacion.md`.

## Qué verificar (abre la fuente primaria; no te quedes con resúmenes del buscador)
1. Cada artículo citado del Decreto 1079 de 2015 (al menos 2.2.1.4.7.1, 2.2.1.4.7.2, 2.2.1.4.8.1–8.3, 2.2.1.4.9.2, 2.2.1.4.6.8 y
   su parágrafo): ¿existe con ese número, dice literalmente lo que el informe le atribuye (3 % de capacidad en propiedad; máxima
   ≤ mínima + 20 %; convenios entre empresas habilitadas con autorización; contratación con servicio especial en temporada alta
   solo en rutas autorizadas) y está vigente? Contrasta con una segunda copia oficial si puedes (SUIN-Juriscol, MinTransporte).
2. **Vigencia posterior a sep-2025**: abre el Decreto 1017 de 2025 (y cualquier modificación posterior que encuentres) y di si
   cambia alguno de esos artículos.
3. **Arriendo simple**: el informe afirma que el capítulo no tiene esa figura (solo leasing). Comprueba si es una ausencia real
   o si existe otra norma (p. ej. sobre vinculación temporal, cesión o servicios ocasionales) que la regule.
4. **DANE ICTIP**: los pesos (combustibles 31,00 %, costos fijos 32,99 %, peajes y terminales 20,39 %, insumos 8,78 %, partes y
   mantenimiento 6,84 %), la variación de mano de obra (+22,11 % corrido 2026 vs. +7,77 % total), la fecha del boletín
   (22-oct-2026) y la frase literal «ausencia de un mercado establecido de alquiler de vehículos de pasajeros» (metodología
   DSO-ICTIP-MET-001 v2, pág. 10).
5. Cualquier otra afirmación del informe que una conclusión de negocio vaya a usar.

## Reglas
- Prohibido inventar; lo no verificable queda «NO VERIFICABLE» con lo que intentaste.
- Guarda fragmentos literales y PDF/HTML de evidencia en `alucinaciones/evidencias/CA-6/`.
- Escribe tu informe en `docs/investigacion/CA-6_verificacion.md` (tabla afirmación → veredicto CONFIRMADA / INCORRECTA /
  NO VERIFICABLE → evidencia → corrección propuesta). **No edites** `CA-6_costos_flota.md` ni ningún otro archivo.
- Si una afirmación del informe resulta falsa, redacta el candidato a hallazgo con la plantilla de `alucinaciones/registro.md`
  dentro de tu informe (no edites el registro).
- No hagas `git add`, `git commit` ni `git push`.

Reporta: veredicto global, tabla resumen, correcciones propuestas y candidatos a hallazgo.
