# Evidencia JJ-3 — «los 3 valores de VisitDate son posteriores a la creación del conjunto»

**Afirmación (IA):** «la fecha de visita no es una fecha real (3 valores ligados al número de fila, posteriores a la creación
del conjunto)».
- Aparece en el prompt del orquestador (Opus 5.5) al redactor-tecnico: `alucinaciones/prompts/JJ-3-redactor-tecnico.md`,
  línea 24.
- El orquestador la tomó de `docs/MEMORIA.md` (bloque «Decisiones vigentes», M3), que dice «`VisitDate` solo descriptiva: 3
  valores ligados al número de fila y posteriores a la creación de la versión 1 en Kaggle, 2024-01-23».
- El redactor-tecnico (Sonnet) la copió al blog (`blog/secciones/07-m3-recomendacion.md`, subsección «Partición», primera
  versión): «3 valores ligados al número de fila, posteriores a la creación del conjunto».

**Lo medido** (`results/data/m3/eda/ficha.json`, `real_o_sintetico.senales_medidas.visit_date`, calculado por
`src/m3_recomendacion/datos.py` desde el CSV):

```json
{"filas": 999, "valores_distintos": ["2024-01-01", "2024-02-15", "2024-03-20"], "fecha_creacion_version_1": "2024-01-23",
 "filas_posteriores_a_la_version_1": 666}
```

2024-01-01 es ANTERIOR a 2024-01-23. Solo 2 de los 3 valores (666 de 999 filas) son posteriores. La spec (`juanjose.md` §3.1,
D3 y D4) lo dice bien: «666 de 999 son posteriores».

**Cómo se detectó:** el orquestador revisó la subsección del blog contra la Ficha (que en la misma sección dice «666 de 999
filas son posteriores»).

**Corrección:** blog corregido a «3 valores ligados al número de fila, 2 de ellos —666 de 999 filas— posteriores a la creación
de la versión 1 en Kaggle»; `docs/MEMORIA.md` corregido al cierre de JJ-3.
