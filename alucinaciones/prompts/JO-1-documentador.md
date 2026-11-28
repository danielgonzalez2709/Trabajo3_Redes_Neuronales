# Prompt JO-1 — documentador (Sonnet) — 2026-11-27 — orquesta: José

Actúa como `.claude/agents/documentador.md`. Repositorio `/home/jose-miguel-pulgarin/Documents/projects/Trabajo3_Redes_Neuronales`,
rama `dev/jose`. No hagas commit. Edita **solo** `docs/MEMORIA.md` (máximo 150 líneas en total; si te pasas, compacta entradas
antiguas de «Estado» sin perder datos vigentes).

JO-1 (José, M2) quedó cerrado el 2026-11-27. Copia los datos de estos archivos (no de este prompt si difieren):
`docs/spec/partes/jose.md` §3.1 (bloque «[DECIDIDO, José, 27-nov] (JO-1)»), `results/data/m2/eda/ficha.json`,
`alucinaciones/registro.md` (candidato «H-?? (JO-1)» y bloque «JO-1» de «Verificaciones que salieron correctas»).

Actualiza:
1. **Estado:** una entrada de JO-1: terminado en `dev/jose` el vie 27, pendiente de PR; `run.py m2-datos --config
   configs/m2/datos.yaml` lee `data/raw/m2/` (Mendeley, un .zip; se baja con `scripts/descargar_m2.py`, verifica SHA-256; no
   versionado) y escribe `data/processed/m2/{imagenes/,indice.csv,origen.csv}` y `results/data/m2/eda/{ficha.json,calidad.csv,
   diccionario.json,procesado.json}`; 7 286 en el .zip, 10 ilegibles, 7 276 procesadas 224×224; fuentes en
   `docs/investigacion/JO-1_fuentes_m2.md`. Revisado por revisor-spec (aprobado con observaciones), revisor-calidad (aprobado en
   la 2.ª vuelta) y cazador-alucinaciones (39/39 cifras recalculadas).
2. **Decisiones vigentes:** una línea M2 [DECIDIDO, José, 27-nov] con D1–D5 resumidas (ver `jose.md` §3.1).
3. **Avisos para el equipo:** (a) el artículo declara 400×600 y «October 2024», pero lo medido es 640×480 en el 91 % y fechas de
   2019 y septiembre de 2024 (hallazgos de datos para el blog de M2); (b) el entrenamiento de M2 usa JPEG 85 y la app no recomprime
   (diferencia declarada); (c) para que la CI pase, el PR de JO-1 debe incluir `data/processed/m2/`, `results/data/m2/eda/`,
   `configs/m2/datos.yaml` y `tests/fixtures/m2/`; (d) la máquina de José no tiene GPU NVIDIA (afecta JO-6).
4. **Pendientes:** agrega a José: PR de JO-1; ética (C-6: acuerdo de uso de Zenodo frente a CC BY 4.0 de Mendeley, rostros
   visibles) para JO-11; GPU para JO-6. No toques los pendientes de otros.
5. **Cacería:** suma el candidato de M2 (JO-1, Código, menor, orquestador Opus: «coherente con el preprocesado fijo de la app»,
   omitía la recompresión JPEG; evidencia en `alucinaciones/evidencias/JO-1/`).
6. **Bitácora:** una línea nueva arriba: `2026-11-27 · José · JO-1 ✅: …` (descarga verificada, 7 276 imágenes 224×224 versionadas,
   ficha/calidad/diccionario, D1–D5, 1 candidato a la cacería).

Entrega: número de líneas final de `docs/MEMORIA.md` y resumen de lo cambiado.
