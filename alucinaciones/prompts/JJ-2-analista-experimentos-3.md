# Prompt JJ-2 — analista-experimentos (Sonnet), 3.ª vuelta (hallazgos de R1 y R2) — 2026-11-26 — orquesta: Juan José

Mismas reglas que tu primer encargo (`JJ-2-analista-experimentos.md`): sin commit/push, `.venv/Scripts/python`, prueba
primero cuando cambies comportamiento, solo tus archivos. No toques `blog/secciones/` (lo corrige el redactor después, con
tus salidas). R1 (revisor-spec) aprobó y R2 (verificador-matematico) recalculó todas las cifras de forma independiente y
coinciden; lo que sigue son correcciones de coherencia y de texto en el código:

1. **B1 (bloqueante, R2).** `src/m3_recomendacion/eda.py:1125-1128`: el texto `criterio_de_veredicto.regla` que se escribe
   en `pruebas_hipotesis.json` dice que «refuta» si p ajustado ≥ alfa y el IC queda dentro de ±mínimo; la función
   `veredicto_de_prueba` (l. ~233) exige además que el IC contenga el 0 (en unilaterales, que empiece en 0 o antes). Haz que
   el texto describa exactamente la regla implementada (léelo de la config `configs/m3/eda.yaml:74-77` si ya está ahí, para
   que haya una sola fuente) y agrega una prueba que fije que el texto y la función concuerdan en el caso de H-M3-1
   (p ajustado ≈ 0,20, IC [0,0006; 0,047], mínimo 0,05, «mayor» → «indeterminada»/no concluyente).
2. **M-2 (R1).** `eda.py:1043` y `1055`: en H-M3-8 y H-M3-9 `figura_o_tabla` dice «Se cierra al modelar (JJ-6)»; el
   `resultado` y el resto dicen JJ-10. Unifica: la figura/tabla saldrá de JJ-6 y la hipótesis se cierra en JJ-10 (escríbelo
   así, sin contradicción).
3. **H-5 (R2).** El enunciado de H-M3-6 dice «difieren en los tipos … y en … calificaciones» (eda.py:~1014) y el de H-M3-5
   «destino_id y lugar», pero la regla combina con «confirmada si alguna cumple»: cambia «y» por «o» en esos enunciados.
4. **H-7 (R2).** Las pruebas χ² están etiquetadas `"dos_colas"` (eda.py:623, 807, 818); el χ² es de cola derecha: usa la
   etiqueta que corresponda (p. ej. `"mayor"`) sin cambiar ningún p ni veredicto (compruébalo).
5. **H-1 (R2).** Para H-M3-1 agrega al JSON (y al `resultado`) un IC de la diferencia (tasa − línea base exacta) coherente
   con la multiplicidad: nivel 1 − alfa/m (m = tamaño de la familia, leído del código, no tecleado), con el mismo bootstrap
   por usuarios. El `resultado` debe decir, con las cifras calculadas: efecto pequeño (≈ 2 pp), p crudo 0,02, p Holm 0,20;
   el IC 95 % sin ajustar excluye un efecto ≥ mínimo; el IC ajustado incluye 0 y el mínimo → no concluyente.
6. **H-2 (R2).** Para el χ² combinación × tipo de H-M3-1, guarda los residuos estandarizados (ajustados) de la tabla y la
   parte del χ² que aportan las celdas coincidentes frente a las no coincidentes (R2 midió 5,7 de 18,35 y residuo máximo
   −2,70 en «Beaches, Historical» × Nature); que el `resultado` lo diga con las cifras calculadas.
7. **H-4 (R2).** En H-M3-4, el límite superior del IC de la V corregida de `n_adultos` (≈ 0,1008) está pegado al mínimo
   0,10 y el veredicto «no concluyente»/«refutada» depende del ruido de Monte Carlo (R2 lo vio cambiar con la semilla). No
   cambies la semilla ni el criterio para mover el resultado. Agrega una marca calculada `en_el_limite: true` cuando
   |límite − mínimo| < una tolerancia declarada en la config (p. ej. 0,005), y que el `resultado` de H-M3-4 lo diga
   explícitamente («el veredicto de n_adultos está en el límite del criterio y no debe leerse como hallazgo»).
8. **Menores de figuras / JSON (R2).** (a) En `lorenz.png`, la banda del azar es **puntual** (por percentil en cada
   punto), no simultánea: dilo en la leyenda o el pie. (b) En `pruebas_hipotesis.json`, el `metodo_ic` de H5 ya dice
   «observado menos percentiles»; agrega que es una inversión aproximada bajo un modelo de desplazamiento, no un bootstrap.
   (c) El «Gini corregido» G·n/(n−1) es un reescalado a [0, 1], no una corrección de sesgo: renómbralo o descríbelo así en
   el JSON (p. ej. `gini_reescalado`), actualizando pruebas y figuras que lo lean.
9. **V de Cramér corregida (R2).** R2 confirmó la fórmula con fuentes secundarias (Wikipedia «Cramér's V»; DescTools
   `CramerV(correct=TRUE)`), que la atribuyen a Bergsma (2013), *Journal of the Korean Statistical Society* 42(3), 323–328,
   doi 10.1016/j.jkss.2012.10.002. **No la des por verificada**: cambia el `TODO(cita)` de `eda.py:~210` por
   `TODO(cita): Bergsma (2013), doi 10.1016/j.jkss.2012.10.002 — verificar con la fuente primaria en JJ-9`.
10. Regenera: `run.py m3-eda` (dos veces, mismos SHA-256), `run.py figures`, `pytest -q -m "not lento"` y
    `pytest -q tests/test_eda_m3.py`; pega las salidas. Responde con la lista de cambios, los veredictos (¿cambió alguno?) y
    las cifras nuevas que el redactor debe usar (IC ajustado de H-M3-1, residuos y aporte al χ², marca de límite de H-M3-4),
    con el archivo y la clave de cada una.

Lo que NO debes cambiar (decide Juan José): umbral de actividad, efectos mínimos, criterio de veredicto (incluido el caso
borde H-8: IC entero por debajo de 0 con p < α en alternativa «mayor» → hoy «indeterminada»).
