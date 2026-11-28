# Prompt JO-1a (A2) — investigador-fuentes (Sonnet) — 2026-11-27 — orquesta: José

Actúa como el agente definido en `.claude/agents/investigador-fuentes.md` (léelo primero). Repositorio:
`/home/jose-miguel-pulgarin/Documents/projects/Trabajo3_Redes_Neuronales` (rama `dev/jose`, Linux). **No hagas commit, ni push,
ni PR.**

Lee antes: `docs/spec/SPEC.md` §0 y §5.12, y del Anexo de ese archivo el apartado «Módulo 2 → Datos»;
`docs/spec/partes/jose.md` §1, §3.1, la fila JO-1 de §4 y §5 (puntos calientes). Nada de otras partes. Como referencia de
formato (no de contenido), mira `docs/investigacion/JJ-1_fuentes_m3.md`.

## Contexto
Conjunto de M2: «Multi-Class Driver Behavior Image Dataset», Mendeley Data, DOI 10.17632/mzb4b6dff3.1 (versión 1); artículo de
datos en Data in Brief, DOI 10.1016/j.dib.2025.111529. El enunciado lo atribuye a «Afridi et al., 2024» — **verifica** autores y
años de ambos. Otro agente descarga y mide las imágenes en paralelo; tú **no** reportas conteos medidos, solo lo que **dicen las
fuentes**, y así lo rotulas («según el artículo…»).

## Tarea
Lee las fuentes primarias (página de Mendeley del conjunto —su descripción y licencia— y el artículo completo; si ScienceDirect
bloquea, busca la versión de acceso abierto del mismo DOI, p. ej. en PubMed Central, y dilo). Escribe
`docs/investigacion/JO-1_fuentes_m2.md` con, para cada punto, la **cita textual** (entre comillas, con sección o tabla del
artículo), la URL y la fecha de consulta:

1. Referencias en APA 7 del conjunto (Mendeley) y del artículo (Data in Brief): autores exactos, año, título, versión, DOI.
2. Licencia del conjunto y del artículo, y qué exige (atribución, etc.), citada.
3. Cómo se recolectaron las imágenes: lugar, periodo, dispositivos (cámaras/celulares), tipos de vehículo y cuántos, número de
   conductores o participantes, posición de la cámara, condiciones de iluminación, consentimiento/ética.
4. Las clases: nombres exactos que usan los autores, su definición y qué comportamientos agrupa cada una (en especial «otros
   comportamientos riesgosos»).
5. Conteos que **declaran** los autores: imágenes por clase, total, originales vs. aumentadas, por tipo de vehículo; resolución y
   formato declarados.
6. **Preprocesamiento y aumento de datos aplicado antes de publicar**: qué transformaciones (con sus parámetros si los dan),
   cuántas variantes por imagen original, si las originales están incluidas, si se puede identificar en los archivos qué imagen
   es aumentada y de cuál original proviene (nombres, carpetas), y si los autores proponen alguna partición.
7. Si los archivos traen etiquetas de tipo de vehículo (carro particular / bus) o de otra variable, según la fuente.
8. Limitaciones que declaran los autores y usos previstos.
9. Contradicciones: entre el artículo y la página de Mendeley, entre secciones del mismo artículo, o con el enunciado del curso
   (Anexo). Lístalas sin resolverlas.

## Reglas
- **Prohibido inventar**: si algo no está en las fuentes, escribe `TODO(dato-faltante)` y no lo completes con conocimiento
  general. No parafrasees números: cópialos tal cual con su cita.
- No uses fuentes secundarias (blogs, Kaggle, Papers with Code) como respaldo; si las consultas, márcalas como secundarias.
- No crees ni modifiques nada fuera de `docs/investigacion/JO-1_fuentes_m2.md`.

## Entrega (tu mensaje final, breve)
1. Archivo creado.
2. Lista numerada de **afirmaciones** con su cita y URL, formato `[F-n] afirmación — «cita textual» — fuente, sección`.
   Incluye al menos: autores y años, licencia, clases, conteos declarados, aumento previo (transformaciones y variantes por
   original), tipos de vehículo y dispositivos.
3. Contradicciones encontradas y `TODO(dato-faltante)`.
