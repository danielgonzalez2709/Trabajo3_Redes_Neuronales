# Prompt JJ-1b (R3) — cazador-alucinaciones (Opus) — 2026-11-25 — orquesta: Juan José

Actúa como el agente definido en `.claude/agents/cazador-alucinaciones.md` (léelo primero). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales` (rama `dev/juanjose`). **No hagas commit, ni push, ni PR.** Usa
`.venv\Scripts\python -I` desde la raíz; no instales nada.

Lee antes: `docs/spec/SPEC.md` §0, §5.7, §5.12 y §9, y del Anexo «Módulo 3 → Datos» y «Cacería de la alucinación»;
`docs/spec/partes/juanjose.md` §3.1 (D1–D7) y §5; `alucinaciones/registro.md` (plantilla y formato). Nada de otras partes.

## Contexto
JJ-1 fase B construyó los datos de M3 con `src/m3_recomendacion/datos.py` (`run.py m3-datos --config configs/m3/datos.yaml`),
ya aprobado por el revisor-spec y el revisor-calidad. Prompts literales en `alucinaciones/prompts/JJ-1b*.md`; respuestas
literales de los subagentes en `alucinaciones/evidencias/JJ-1b/respuesta-*.md`. Fuente primaria local:
`docs/investigacion/JJ-1_kaggle_metadata.json` (respuestas crudas de la API de Kaggle, re-descargadas e idénticas en la fase A)
y los CSV de `data/raw/m3/`.

## Tarea R3
1. **Cada cifra y cada cita** de `results/data/m3/eda/ficha.json`, `results/data/m3/eda/diccionario.json`, la sección
   «## M3» de `data/fuentes.md` y la entrada `mehra2024` de `blog/references.bib`, contra los CSV (con **tu propio código
   independiente**, sin importar `src/m3_recomendacion/datos.py`) y contra `JJ-1_kaggle_metadata.json` (cada cita literal debe
   ser subcadena exacta del campo indicado). Incluye: usuarios, destinos, lugares, interacciones por origen y unión, usuarios y
   destinos que aparecen, escalas y frecuencias, densidades con los dos denominadores, usuarios por número de interacciones,
   señales medidas (periodicidad, fechas posteriores a la creación de la versión, nombres y correos, V de Cramér y p), tipos
   de columna, inconsistencias, SHA-256 y tamaños de `fuentes.md`, autor, año, versión, título y URL de la cita.
2. **Los tres parquet** de `data/processed/m3/`: columnas y conteos según D1, D2 y D6 (sin `Name`, `Email` ni `ReviewText`;
   sin `split`), y que cada fila corresponde a una fila cruda (`origen` + `id_origen`).
3. **Afirmaciones normativas sobre licencias** que quedaron en el repo tras la corrección de la revisión 1:
   `docs/investigacion/JJ-1_fuentes_m3.md` §3.2 y la fila Licencia de `data/fuentes.md` dicen que la sección «License» (CC0) no
   exige atribución, que la MIT pide conservar el aviso de copyright y de permiso en las copias y que solo «Usage» pide citar.
   Contrástalas con los textos oficiales: https://opensource.org/license/mit y
   https://creativecommons.org/publicdomain/zero/1.0/ (y su código legal si hace falta). Guarda solo fragmentos citados y la
   URL con la fecha y hora de consulta en `alucinaciones/evidencias/JJ-1b/` (no guardes los textos completos de las licencias).
4. **Candidatos a hallazgo.** Hay uno ya detectado y documentado en `alucinaciones/evidencias/JJ-1b/licencia_citar/`
   (`README.md`, `verificar.py`, `salida.txt`): «las tres licencias piden citar la fuente», afirmado por la sesión orquestadora
   (Opus) en la fase A y copiado y ampliado por el implementador (Sonnet). Verifícalo de forma independiente y, si se sostiene,
   **regístralo en `alucinaciones/registro.md` como candidato, SIN número** (encabezado `### H-?? (JJ-1b) — …`; la numeración
   la coordina Andrés), con la plantilla de 6 puntos y las rutas de prompt, respuesta y evidencia. El implementador además
   reportó que se le coló un carácter de retroceso (`\x08`) en una regex de `datos.py` y que lo corrigió (ver
   `respuesta-implementador.md` §4.7): comprueba si hay evidencia reproducible; si no la hay, no lo registres como hallazgo y
   dilo. Si en tu verificación aparece otro error de un subagente, regístralo igual (sin número) con su evidencia. No
   registres el candidato débil de A1 sobre «independencia» (D7). No numeres nada ni cambies los hallazgos existentes.
5. Registra en `alucinaciones/registro.md` § «Verificaciones que salieron correctas» un resumen corto de lo que verificaste
   y salió bien en JJ-1 (fase A y fase B), con rutas.

## Reglas
- Prohibido inventar; nunca exageres un hallazgo. Todo veredicto con evidencia ejecutada o fragmento literal.
- Crea solo: `alucinaciones/evidencias/JJ-1b/verificar_R3.py`, su salida `verificar_R3_salida.txt`, los fragmentos de
  licencias en esa carpeta y tu informe `docs/investigacion/JJ-1_verificacion_R3.md`; edita solo `alucinaciones/registro.md`
  (agregar). No modifiques nada más.

## Entrega
`docs/investigacion/JJ-1_verificacion_R3.md` con la tabla de verificación (afirmación, archivo, veredicto: correcta /
incorrecta / imprecisa / no verificable / inferencia no respaldada, evidencia) y los candidatos. En tu mensaje final: el
recuento de veredictos, los candidatos registrados (y los descartados, con el porqué) y la cobertura de la cacería.
