# Prompt DA-2a — investigador-fuentes (Sonnet) — 2026-11-24 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/investigador-fuentes.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`). Lee también
`docs/spec/SPEC.md` §0, §5.1 y el Anexo («Módulo 1 → Datos»), y `docs/spec/partes/daniel.md` §3.2.

## Tarea (DA-2, parte de investigación)
Identificar con fuentes primarias el conjunto de datos del Módulo 1 y la codificación DIVIPOLA, **sin descargar todavía el
conjunto completo**.

1. **Conjunto de datos.gov.co**: «Operación de pasajeros y despacho de vehículos en la modalidad de transporte de pasajeros
   por carretera», publicado por la Superintendencia de Transporte. Encuentra y verifica abriendo las páginas:
   - identificador del conjunto en datos.gov.co (código de 4x4 caracteres de Socrata), URL de la página y del endpoint de la API
     (`https://www.datos.gov.co/resource/<id>.json`) y de la vista de metadatos (`/api/views/<id>.json`);
   - entidad que publica, licencia, frecuencia de actualización, fecha de última actualización;
   - **diccionario**: nombre de cada columna (campo de la API), tipo y la descripción **literal** que da la fuente;
   - número de filas (consulta `$select=count(*)`), rango de fechas (`min`/`max` del campo de fecha) y, si es razonable, número
     de pares origen–destino distintos;
   - si las columnas traen códigos de municipio (y si parecen DIVIPOLA de 5 dígitos), terminal de origen, clase de vehículo,
     número de pasajeros y de despachos. Toma una muestra de 1.000 filas con la API y guárdala en
     `data/raw/m1/muestra_1000.json` (la carpeta `data/raw/` no se versiona) para mirar valores reales.
   - Si encuentras más de un conjunto con nombre parecido, lístalos todos y explica cuál coincide con el enunciado.
2. **DIVIPOLA**: la fuente oficial del DANE para los códigos de departamentos y municipios: URL, nombre del archivo o servicio,
   versión o fecha, formato y cómo descargarlo. Cita APA 7.
3. Recomendación de **cómo descargar** el conjunto (agregación en el servidor con SoQL `group by` por origen, destino y fecha vs.
   descarga completa): tamaño estimado, límites de la API (paginación, `$limit`), y la consulta SoQL exacta que propondrías para
   obtener pasajeros y despachos por (origen, destino, fecha). Pruébala con un `$limit` pequeño y reporta si funciona.

## Reglas
- Nada de memoria: todo dato con URL abierta por ti y fecha de consulta (hoy, 2026-11-24). Si no lo encuentras, `TODO(cita)`.
- No inventes nombres de columnas: cópialos de la API o de los metadatos.
- No modifiques archivos fuera de `data/raw/m1/` y del informe.
- Si algo contradice lo que una IA suele decir de este conjunto o del DANE, anótalo como CANDIDATO A HALLAZGO.

## Salida
Escribe el informe en `docs/investigacion/DA-2_fuentes_m1.md` con: tabla de columnas (campo, tipo, descripción literal, ejemplo
de la muestra), conteos medidos, rango de fechas, identificadores y URL, DIVIPOLA, consulta SoQL propuesta y probada, riesgos e
inconsistencias vistas entre diccionario y muestra, y citas APA 7. Responde con un resumen de 10–15 líneas.
