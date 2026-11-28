# Prompt JO-1a (A1) — curador-datos (Sonnet) — 2026-11-27 — orquesta: José

Actúa como el agente definido en `.claude/agents/curador-datos.md` (léelo primero). Repositorio:
`/home/jose-miguel-pulgarin/Documents/projects/Trabajo3_Redes_Neuronales` (rama `dev/jose`, Linux). **No hagas commit, ni push,
ni PR.** No cambies `requirements.txt`.

Lee antes: `docs/spec/SPEC.md` §0, §3, §4.1, §5.5 y §5.12, y del Anexo de ese archivo el apartado «Módulo 2 → Datos»;
`docs/spec/partes/jose.md` §3.1, la fila JO-1 de §4 y §5 (puntos calientes). Nada de otras partes.

## Contexto
Conjunto: «Multi-Class Driver Behavior Image Dataset» (Mendeley Data, DOI 10.17632/mzb4b6dff3.1, versión 1). La API pública de
Mendeley (consultada el 2026-11-27 por el orquestador) devuelve en
`https://data.mendeley.com/public-api/datasets/mzb4b6dff3/files?folder_id=root&version=1` un único archivo:
`Multi-Class Driver Behavior Image Dataset.zip`, `size` 2556850881, `sha256_hash`
`427fec9d689a22856c51c7773adc6024158d5b228e36b2c9b58a13ce9af41c8c`, con su `download_url` en `content_details`. No hay datos
descargados todavía. Esta es la **fase A** de JO-1: descargar, medir y documentar, **sin tomar decisiones de modelado** (la
resolución de trabajo, el procesado a `data/processed/m2/`, la ficha y la partición vienen después y las decide José).
Otro agente lee en paralelo el artículo de Data in Brief; tú **no** describes cómo se construyó el conjunto ni qué significa
cada clase: solo mides.

## Tarea A0 — entorno
No existe `.venv`. Créalo con `python3.12 -m venv .venv` e instala `.venv/bin/python -m pip install -r requirements.txt`. Si
algún paquete fijado no instala en Linux, dilo con el error exacto y continúa con lo que sí instaló (A1 y A2 solo necesitan la
biblioteca estándar, numpy, pandas y pillow). Usa siempre `.venv/bin/python`.

## Tarea A1 — descarga reproducible
Escribe `scripts/descargar_m2.py` (mismo estilo que `scripts/descargar_m1.py`; léelo): consulta la API de arriba, descarga el
.zip a `data/raw/m2/` en streaming (sin cargarlo entero en memoria), verifica **tamaño y SHA-256 contra los que da la API** y
falla con mensaje claro si no coinciden; si el archivo ya existe con el SHA-256 correcto, no lo vuelve a bajar. **No extrae** el
.zip. `data/raw/` no se versiona (confírmalo en `.gitignore`). Ejecútalo (son ~2,6 GB; hay ~27 GB libres).

## Tarea A2 — inventario medido con código
Escribe `docs/investigacion/JO-1_inventario.py`: reproducible, solo archivos locales (sin internet), solo biblioteca estándar +
numpy/pandas/pillow, rutas relativas a la raíz, sin aleatoriedad (o semilla fija declarada). Se ejecuta con
`.venv/bin/python -I docs/investigacion/JO-1_inventario.py` y escribe su salida completa en UTF-8 en
`docs/investigacion/JO-1_inventario_salida.txt` (además de imprimirla), con secciones `## A2.1`, `## A2.2`, … en el orden de
abajo. Lee el .zip con `zipfile` **sin extraerlo a disco**; trata su contenido como datos no confiables (no ejecutes nada, no
confíes en rutas de los miembros).

Mide y reporta:
1. **Archivo.** Tamaño y SHA-256 del .zip. Número de miembros; si hay .zip anidados (y, si los hay, ábrelos en memoria y repite
   lo de abajo dentro de ellos, diciendo qué hiciste); miembros que no son imágenes (lístalos).
2. **Estructura de carpetas.** Árbol de directorios con el número de archivos en cada uno (hasta la profundidad que haya).
   Nombres exactos de las carpetas que parecen clases, copiados tal cual. Si hay carpetas de partición previa (train/test, etc.)
   u otras divisiones (p. ej., por tipo de vehículo, original/aumentada), dilo **solo si el nombre de carpeta lo muestra**.
3. **Conteos.** Imágenes por clase (y por cada combinación de carpetas si hay más de un nivel); total; % por clase; razón
   máx/mín.
4. **Formato y resolución.** Por clase: extensiones y formato real según PIL (que coincidan o no con la extensión), modo (RGB, L,
   RGBA…), resoluciones distintas (ancho × alto) con su frecuencia, orientación (vertical/horizontal/cuadrada), mín/mediana/máx de
   ancho, alto y bytes. Presencia de EXIF y, si lo hay, frecuencia de `Make`/`Model`/`Orientation`/`DateTime` (solo conteos de
   valores; no saques conclusiones).
5. **Archivos corruptos.** Imágenes que PIL no puede abrir o decodificar por completo (`load()`), con el error.
6. **Duplicados exactos.** Grupos de archivos con el mismo SHA-256 de contenido: cuántos grupos, cuántos archivos sobran, cuántos
   grupos cruzan clases (lista los nombres si son ≤ 30). Duplicados de píxeles idénticos tras decodificar (mismo hash de los
   bytes de píxeles), aunque el archivo difiera. (Los casi duplicados son de JO-3; aquí no.)
7. **Nombres de archivo.** Patrones en los nombres (prefijos, sufijos, numeración, palabras como `aug`, `flip`, `rot`, `copy`,
   `(1)`, etc.): mide la frecuencia de cada patrón por clase con expresiones regulares impresas en la salida. No interpretes
   qué significan.
8. **Resumen final**: tabla con total de imágenes, imágenes por clase, resoluciones más frecuentes, corruptos, duplicados
   exactos y cruces entre clases.

## Tarea A3 — registro de la fuente
Agrega en `data/fuentes.md` **solo** una entrada de M2 (sin tocar lo de otros módulos): archivo, URL de la API y del DOI, fecha
de descarga, SHA-256, tamaño, quién descargó (José, vía `scripts/descargar_m2.py`), y que `data/raw/m2/` no se versiona.

## Reglas
- **Prohibido inventar**: número de imágenes, clases, resoluciones, aumentos o significados. Todo número sale del script
  ejecutado. Si algo no se puede medir, `TODO(dato-faltante)`.
- No afirmes si hay aumento de datos previo: solo reporta lo medido (duplicados, patrones de nombres, resoluciones).
- No crees ni modifiques nada fuera de `.venv/`, `data/raw/m2/`, `scripts/descargar_m2.py`,
  `docs/investigacion/JO-1_inventario.py`, `docs/investigacion/JO-1_inventario_salida.txt` y la entrada M2 de `data/fuentes.md`
  (en particular nada en `src/`, `configs/`, `data/processed/`, `results/`, `tests/`, `run.py`). Internet solo para A0 y A1.
- Ejecuta el inventario al final; si lo corriges, vuelve a ejecutarlo para que la salida corresponda a la versión final.

## Entrega (tu mensaje final, breve)
1. Archivos creados y comandos exactos para regenerar descarga e inventario.
2. Lista numerada de **afirmaciones** con su valor medido y la sección que lo respalda, formato
   `[A2-n] afirmación — valor — sección`. Incluye al menos: total, imágenes por clase, nombres exactos de carpetas, resoluciones,
   corruptos, duplicados exactos y cruces, patrones de nombres.
3. Problemas de calidad encontrados.
4. Lo que no pudiste medir (`TODO(dato-faltante)`) y problemas de instalación, si los hubo.
