# Prompt JJ-2 — redactor-tecnico (Sonnet), 2.ª vuelta (hallazgos de R1 y R2) — 2026-11-26 — orquesta: Juan José

Mismas reglas que tu primer encargo (`alucinaciones/prompts/JJ-2-redactor-tecnico.md`): escribes SOLO en
`blog/secciones/07-m3-recomendacion.md`; toda cifra sale de `results/data/m3/eda/` con su archivo/clave; sin citas nuevas;
sin commit/push. El analista regeneró `results/data/m3/eda/` y las figuras (ningún veredicto ni p cambió, pero hay claves
nuevas y una renombrada: `gini_corregido` → `gini_reescalado`, que es un reescalado a [0, 1], **no** una corrección de
sesgo). Vuelve a leer `pruebas_hipotesis.json`, `coincidencia_preferencias.json`, `hipotesis.json`, `concentracion.json` y
`configs/m3/eda.yaml` antes de editar. **Usa la herramienta Edit**, no scripts por heredoc (riesgo de `\b` → backspace).

Correcciones:
1. **B2 / M-1 (bloqueante).** El párrafo de métodos (≈ l. 301-303) dice que los p de H-M3-1 a H-M3-4 son por permutación
   entre usuarios y que los IC son bootstrap de usuarios (o destinos en H-M3-3). Corrige según `metodo_p` / `metodo_ic` de
   cada prueba en `pruebas_hipotesis.json`: H-M3-1, H-M3-2 y H-M3-4 → permutación entre usuarios; H-M3-3 → permutación de la
   popularidad entre destinos; H-M3-5 → simulación del reparto uniforme; H-M3-6 → asintóticos (χ² y Mann–Whitney), que
   suponen independencia. IC: bootstrap por usuarios (por destinos en H-M3-3), salvo H-M3-5, donde es «observado menos
   percentiles de la simulación», una inversión aproximada bajo un modelo de desplazamiento, no un bootstrap.
2. **H-1 (H-M3-1).** Explica, con las cifras de los archivos: efecto pequeño (≈ 2 pp, menor que el mínimo), p crudo 0,02,
   p Holm 0,20; el IC 95 % sin ajustar excluye el 0 y excluye un efecto ≥ mínimo; el IC ajustado por multiplicidad
   (nivel 1 − α/m; `global.diferencia_exacta_ic_ajustado`) incluye el 0 y el mínimo → no concluyente. Menciona que está
   marcado «en el límite» (`efecto.en_el_limite`).
3. **H-2.** La frase «hay una asociación débil» del χ² combinación × tipo: di que es un indicio de asociación débil
   (p sin ajustar, prueba fuera de la familia) que en su mayor parte **no** está en las celdas que coinciden con las
   preferencias (aporte al χ²: coincidentes vs. no coincidentes; residuo máximo y su celda, indicando que es el residuo
   estandarizado ajustado y, si lo das, también el de Pearson; claves en `chi2_combinacion_tipo`).
4. **H-3 / H-4 (H-M3-4).** «La demografía no se asocia con el tipo» dice más de lo medido (veredicto no concluyente).
   Cámbialo por «no se detectó asociación; los IC excluyen V ≥ 0,10 para género y niños, pero no para adultos», y di que el
   resultado de `n_adultos` está en el límite del criterio (marca `en_el_limite`, tolerancia de la config) y no debe leerse
   como hallazgo. Revisa también la «lectura de conjunto» y la tabla de veredictos para que no afirmen ausencia de efecto.
5. **H-6 (H-M3-6).** No digas que reseñas e historial «se parecen» sin calificar: «no difieren en más que un efecto pequeño
   (|δ| < 0,147; V corregida < 0,10)», con el IC de δ por usuarios que tiene en cuenta que muchos usuarios están en los dos
   orígenes (`pruebas_hipotesis.json`). Ajusta el enunciado de H-M3-5 y H-M3-6 a «o» si el blog los copia (ya cambiaron en
   `hipotesis.json`).
6. **Efectos mínimos.** El blog dice que los mínimos «no son umbrales de la literatura». No lo afirmes: di que son una
   convención nuestra declarada en `configs/m3/eda.yaml` y deja `<!-- TODO(cita): el 0,147 de δ de Cliff se atribuye a
   Romano et al. (2006); verificar la fuente primaria en JJ-9 -->`. Para la V corregida, deja
   `<!-- TODO(cita): Bergsma (2013), doi 10.1016/j.jkss.2012.10.002 — verificar en JJ-9 -->` en lugar del TODO genérico.
   No agregues `[@…]` nuevos.
7. **Gini.** Si el blog habla de «Gini corregido», cámbialo a «reescalado a [0, 1] (G·n/(n−1))» o elimínalo si no se usa.
8. **Lorenz.** Donde describas la banda del azar en `[[fig:m3-lorenz]]`, di que es un IC 95 % puntual, no simultáneo.
9. **Caso de uso (R1, decide Juan José).** Amplía el comentario `<!-- revisar: Juan José — … -->` del caso de uso para que
   diga también que la disponibilidad de los datos demográficos al recomendar y el correo de campaña son diseño nuestro
   (§5.8 solo pone `preferencias` en el perfil nuevo).
10. Comprueba que ninguna cifra antigua quedó desactualizada (compara cada cifra del texto con los JSON regenerados).

Al terminar: `.venv/Scripts/mkdocs build --strict -f blog/mkdocs.yml` y `.venv/Scripts/python -m pytest -q tests/test_blog.py`
(pega las salidas) y responde con la lista de cambios y la lista **actualizada y completa** de cifras con su archivo y clave
(para el cazador de alucinaciones).
