# Prompt JJ-2 (R2) — verificador-matematico (Opus) — 2026-11-26 — orquesta: Juan José

Actúa como el agente definido en `.claude/agents/verificador-matematico.md` (léelo primero). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales` (rama `dev/juanjose`). Solo lees y ejecutas (puedes escribir scripts de
verificación SOLO en tu carpeta temporal / scratchpad, nunca en el repo); **no modifiques archivos del repo**, no hagas commit
ni push. Usa `.venv/Scripts/python`. Sin internet para los datos; si consultas una fuente para una definición, cítala con URL.

Lee antes: `docs/spec/SPEC.md` §0 y §5.12; `docs/spec/partes/juanjose.md` §3.1 (D1–D3); el encargo
`alucinaciones/prompts/JJ-2-analista-experimentos.md` (sección E4: qué se pidió medir y cómo). Nada de otras partes.

## Qué verificar, de forma independiente (recalcula con tu propio código desde `data/processed/m3/*.parquet`)
Archivos: `src/m3_recomendacion/eda.py`, `configs/m3/eda.yaml`, `tests/test_eda_m3.py`, salidas en
`results/data/m3/eda/` (`concentracion.json`, `distribucion_actividad.json`, `coincidencia_preferencias.json`,
`pruebas_hipotesis.json`, `hipotesis.json`, `actividad_usuarios.json`, `calificaciones.csv`, `demografia_tipo.csv`,
`matriz_preferencias_tipo.csv`) y la sección `blog/secciones/07-m3-recomendacion.md` (fórmulas escritas y conclusiones).

1. **Concentración**: definición y cálculo de Gini (¿qué estimador?, ¿con o sin corrección n/(n−1)?, ¿coherente entre la
   fórmula del blog, el código y la prueba a mano?), HHI (cuotas en [0, 1]; si hay HHI normalizado, su fórmula), cuota
   top 10 % y 20 % (cómo se tratan los empates en el corte), curva de Lorenz (puntos, orden ascendente, (0,0) y (1,1)).
   Recalcula a nivel `destino_id` (incluidos los destinos con 0 interacciones) y `lugar`.
2. **Referencia de azar uniforme**: qué modelo nulo se simula (multinomial uniforme de 1 998 interacciones sobre 999
   usuarios / 1 000 destinos / 5 lugares; ¿se permiten pares repetidos usuario–destino, que los datos no tienen?, ¿importa?);
   IC 95 % por percentiles; definición del p-valor del observado frente a la distribución simulada (una o dos colas;
   corrección +1).
3. **Coincidencia preferencia–tipo (H-M3-1)**: tasa observada; **línea base exacta** (promedio por interacción de la
   fracción del catálogo cubierta por las preferencias del usuario) y la línea base marginal; prueba de permutación
   (qué se permuta, qué se conserva, fórmula del p); IC de la diferencia (bootstrap por usuarios u otro: ¿válido con
   interacciones agrupadas por usuario?); χ² combinación × tipo y V de Cramér (y la versión con corrección de sesgo:
   comprueba la fórmula, p. ej. la de Bergsma 2013, y dilo con fuente).
4. **H-M3-2** (calificación si coincide): estadístico, permutación, delta de Cliff y su IC; signo de la diferencia.
5. **H-M3-3** (popularidad vs. interacciones): Spearman con empates, IC y p (permutación entre destinos).
6. **H-M3-4** (demografía × tipo): χ², gl, V; ¿se trata la dependencia de varias interacciones del mismo usuario (p.
   ej. permutación a nivel de usuario)? Si el p es de χ² asintótico con observaciones no independientes, dilo.
7. **H-M3-5** (concentración frente al azar) y **H-M3-6** (reseñas vs. historial): estadísticos, gl, p y efectos.
8. **Comparaciones múltiples**: familia declarada (¿cuáles 10 pruebas?), ajuste de Holm bien implementado (orden,
   multiplicadores m−i+1, monotonía, tope en 1); veredicto según p ajustado.
9. **Lógica de veredicto**: aplica el criterio de `configs/m3/eda.yaml` a cada hipótesis y comprueba que sale el veredicto
   escrito. Juzga si el criterio es razonable y si alguna conclusión (en `hipotesis.json` o en el blog) dice **más** de lo
   que muestran los p-valores e intervalos (p. ej. «refutada» cuando lo correcto sería «no concluyente» o al revés;
   «no hay efecto» en vez de «no se detectó un efecto mayor que X»). Atención especial a H-M3-1 (p crudo ≈ 0,02, IC de la
   diferencia que excluye el 0 por poco, p Holm 0,20) y a H-M3-6 (Mann–Whitney p crudo ≈ 0,063).
10. **Actividad y partición D3** (solo conteos): 1 066 / 326 / 606 y los grupos pocas/muchas; recalcula.
11. **Pruebas**: ¿los ejemplos a mano de `tests/test_eda_m3.py` están bien calculados (revisa los comentarios con el
    cálculo)?

Responde con veredicto **APROBADO** / **NO APROBADO**, una tabla «magnitud — valor en results — tu valor — ¿coincide?», y
los hallazgos (bloqueantes / menores) con archivo:línea y la corrección propuesta. Si encuentras un error matemático que
introdujo un subagente (fórmula, definición o conclusión), descríbelo con evidencia reproducible: es candidato a la cacería.
