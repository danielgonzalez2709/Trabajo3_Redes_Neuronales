# JJ-3 — prompt del orquestador (Opus 5.5) al redactor-tecnico (Sonnet), 2026-11-26

Tarea JJ-3 (P5): subsección del blog sobre la **partición sin fuga de M3**. Directorio `C:\Repositorios\Trabajo3_Redes_Neuronales`,
rama `dev/juanjose`. NO hagas commits, push ni PR. Usa `.venv/Scripts/python` y `.venv/Scripts/mkdocs`. Sin internet.
Solo editas `blog/secciones/07-m3-recomendacion.md`. No inventes ninguna cifra: toda cifra sale de
`results/data/m3/particion/resumen.json` (o de los archivos de `results/data/m3/eda/` que ya cita la sección).

## Lee primero
- `blog/secciones/07-m3-recomendacion.md` completo (estilo, tablas `::: tabla <id>` con «Título:» y «Fuente:», referencias
  `[[tab:<id>]]`, comentarios `<!-- revisar: Juan José — … -->`).
- `blog/hooks/reporte.py` (cabecera: sintaxis de figuras, tablas y referencias).
- `results/data/m3/particion/resumen.json` (todas las cifras).
- `docs/spec/partes/juanjose.md` §3.1: D3 y D8–D10 [DECIDIDO, Juan José].
- Del enunciado (Anexo M3, tarea 3, literal): «**Partición.** Definan y justifiquen cómo separan los conjuntos de
  entrenamiento, validación y prueba (por ejemplo, por tiempo si hay fechas, o excluyendo interacciones por usuario). Ninguna
  interacción de prueba puede usarse para entrenar.» Regla de comparación justa: «todos los modelos de un módulo usan el mismo
  preprocesamiento y las mismas particiones».

## Qué escribir
1. Nueva subsección **«### Partición»** inmediatamente DESPUÉS de toda la sección «### Análisis descriptivo» (es decir, después
   de «#### Veredicto de las hipótesis» y su tabla, y antes de lo que siga), en palabras simples:
   - la regla (D3): por usuario; prueba = 1 interacción al azar de cada usuario con 2 o más; validación = 1 más de cada usuario
     con 3 o más; el resto, entrenamiento; con 1 interacción, solo entrenamiento; semilla fija (la de `resumen.json`);
   - por qué no es temporal: la fecha de visita no es una fecha real (3 valores ligados al número de fila, posteriores a la
     creación del conjunto; ya está explicado en la Ficha: remite a ella, no lo repitas entero);
   - una sola partición para todos los modelos (referencias y red), identificada por su huella SHA-256 (D8, núcleo §6);
   - D9: validación solo para elegir hiperparámetros y parar el entrenamiento; los modelos finales se entrenan solo con
     entrenamiento y se evalúan una vez en prueba; toda estadística sacada de las interacciones (popularidad, conteos,
     negativos por popularidad) sale solo de entrenamiento;
   - D10: al evaluar, para cada usuario se ordenan todos los destinos del catálogo excepto los que ya conoce (en prueba: los de
     entrenamiento y validación; en validación: los de entrenamiento); un destino ya visto nunca cuenta como acierto; los 141
     usuarios sin interacciones no se evalúan;
   - una tabla `::: tabla m3-particion-final` (Título y Fuente; Fuente: `results/data/m3/particion/resumen.json` con las claves
     usadas) con interacciones y usuarios por partición y por grupo de actividad (pocas = 1 a 2, muchas = 3 o más; aclara que el
     grupo se define con el total de interacciones y solo estratifica el reporte), citada en el texto con `[[tab:m3-particion-final]]`;
   - dos hechos medidos que condicionan la evaluación (de `diagnosticos`): (a) qué parte de las interacciones de prueba son de
     destinos sin ninguna interacción en entrenamiento («destinos fríos»: un filtrado colaborativo o la popularidad no tienen
     señal para ellos); (b) cuántos usuarios de prueba ya tienen en su historial otro id del mismo lugar que su destino de
     prueba (los 1 000 ids son 5 lugares: para ellos un «acierto por lugar» es trivial). Deja un comentario
     `<!-- revisar: Juan José — cómo se reporta el acierto por lugar lo propone el auditor-fugas y se decide en JJ-6. -->`.
   - Sin rutas de archivos dentro de las frases: las rutas van solo en la línea «Fuente:» de la tabla (o, si una cifra fuera
     de la tabla la necesita, nombra la clave del JSON sin la ruta).
2. Actualiza **«#### Implicaciones para el modelado»**, punto (a) y su tabla `m3-particion`, para que sea coherente: hoy dice que
   «la partición real, con semilla y pruebas de fuga, es de JJ-3». Ahora existe: di que las cifras de la regla coinciden con la
   partición final (compruébalo comparando `actividad_usuarios.json` → `particion_d3` con `resumen.json`; si no coinciden,
   detente y repórtalo) y remite a la subsección «Partición» con su tabla. Puedes conservar la tabla `m3-particion` o
   reemplazar su contenido por una remisión, pero no dejes dos tablas que digan lo mismo con títulos contradictorios; si
   eliminas `m3-particion`, busca y actualiza toda referencia `[[tab:m3-particion]]` del blog.
3. Si el comentario de cabecera de la sección (línea 3) queda desactualizado, ajústalo.

## Aceptación
`NO_MKDOCS_2_WARNING=1 .venv/Scripts/mkdocs build --strict -f blog/mkdocs.yml` sin errores ni avisos nuevos, y
`.venv/Scripts/python -m pytest -q tests/test_blog.py` en verde. Entrega: el texto nuevo, la salida real de los dos comandos y
la lista de cifras usadas con la clave del JSON de la que sale cada una.
