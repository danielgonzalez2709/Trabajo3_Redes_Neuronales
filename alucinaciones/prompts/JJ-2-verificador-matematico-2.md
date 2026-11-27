# Prompt JJ-2 (R2, 2.ª vuelta) — verificador-matematico (Opus) — 2026-11-26 — orquesta: Juan José

Mismas reglas que tu primer encargo (`alucinaciones/prompts/JJ-2-verificador-matematico.md`): solo lectura del repo; tus
scripts en tu carpeta del scratchpad (`...\scratchpad\R2\`). El analista y el redactor aplicaron tus hallazgos (encargos
`JJ-2-analista-experimentos-3.md` y `JJ-2-redactor-tecnico-2.md`). Verifica **solo** que:

1. B1: el texto `criterio_de_veredicto.regla` de `results/data/m3/eda/pruebas_hipotesis.json` (que ahora sale de
   `configs/m3/eda.yaml` → `regla_de_veredicto`) describe exactamente `veredicto_de_prueba` en `src/m3_recomendacion/eda.py`;
   aplica la regla escrita a las 10 pruebas y comprueba que da los veredictos guardados.
2. B2: el párrafo/lista de métodos y la nota de la tabla `m3-pruebas` en `blog/secciones/07-m3-recomendacion.md` coinciden
   con `metodo_p` / `metodo_ic` de cada prueba.
3. H-1: el IC ajustado de H-M3-1 (`coincidencia_preferencias.json` → `global.diferencia_exacta_ic_ajustado`, nivel 0,995)
   — recalcúlalo con tu bootstrap por usuarios — y su redacción en `hipotesis.json` y el blog.
4. H-2: residuos estandarizados ajustados y de Pearson, aporte al χ² de celdas coincidentes / no coincidentes (5,695 /
   12,651), residuo máximo −3,73 (ajustado) / −2,70 (Pearson); recalcula y revisa la redacción.
5. H-3/H-4: redacción de H-M3-4 («no se detectó…», «en el límite») y la marca `en_el_limite` (tolerancia 0,005) en las
   pruebas; que ninguna frase del blog afirme ausencia de efecto donde el veredicto es no concluyente.
6. H-5, H-6, H-7: enunciados con «o»; redacción de H-M3-6; etiquetas `"mayor"` de los χ² sin cambiar p.
7. Menores: banda puntual en Lorenz, `metodo_ic` de H5, `gini_reescalado`, TODO(cita) de Bergsma y Romano (sin `[@…]`
   nuevos).
8. Que ningún número cambió frente a tu primera verificación (salvo las cifras nuevas) y que `pytest -q
   tests/test_eda_m3.py -p no:cacheprovider` pasa.

Responde **APROBADO** / **NO APROBADO** con los hallazgos que queden (archivo:línea, corrección propuesta).
