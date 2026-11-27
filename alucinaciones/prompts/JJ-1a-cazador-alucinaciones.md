# Prompt JJ-1a (A3) — cazador-alucinaciones (Opus) — 2026-11-25 — orquesta: Juan José

Actúa como el agente definido en `.claude/agents/cazador-alucinaciones.md` (léelo primero). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales` (rama `dev/juanjose`). **No hagas commit, ni push, ni PR.**
Usa siempre `.venv\Scripts\python` (Python 3.12, Windows) y ejecútalo con `-I` desde la raíz del repo; no instales nada.

Lee antes: `docs/spec/SPEC.md` §0, §5.7, §5.12 y §9, y del Anexo de ese archivo «Módulo 3 → Datos» y «Cacería de la
alucinación»; `docs/spec/partes/juanjose.md` §3.1 y §5 (puntos calientes); `alucinaciones/registro.md` (solo para ver la
plantilla de 6 puntos). Nada de otras partes.

## Contexto
JJ-1 fase A: inventario y documentación del conjunto de M3 («Travel Recommendation Dataset», Kaggle,
`amanmehra23/travel-recommendation-dataset`), descargado a mano por Juan José el 2026-11-25 en `data/raw/m3/` (`archive.zip` +
4 CSV). Dos subagentes ya trabajaron; tú verificas lo que afirmaron:

- **A1 — curador-datos (Sonnet).** Prompt literal: `alucinaciones/prompts/JJ-1a-curador-datos.md`. Respuesta literal:
  `alucinaciones/evidencias/JJ-1a/respuesta-curador-datos.md` (afirmaciones `[A1-n]`). Produjo
  `docs/investigacion/JJ-1_inventario.py` y `docs/investigacion/JJ-1_inventario_salida.txt`.
- **A2 — investigador-fuentes (Sonnet).** Prompt literal: `alucinaciones/prompts/JJ-1a-investigador-fuentes.md`. Respuesta
  literal: `alucinaciones/evidencias/JJ-1a/respuesta-investigador-fuentes.md` (afirmaciones `[A2-n]`). Produjo
  `docs/investigacion/JJ-1_kaggle_metadata.json` (respuestas crudas de la API pública de Kaggle).

## Tarea A3 — verificación adversarial
1. **Cada afirmación `[A1-n]`** contra los archivos de `data/raw/m3/`, con **tu propio código independiente** (no importes ni
   copies `JJ-1_inventario.py`; recalcula desde los CSV). Además, lee `JJ-1_inventario.py` buscando errores de implementación
   (fórmulas de densidad, χ², índice de dispersión, tasa esperada de coincidencia preferencia–tipo, conteos «< k» que incluyan
   o no a los usuarios sin interacciones, etc.) y comprueba que la salida guardada corresponde al script actual (vuelve a
   ejecutarlo y compara el SHA-256 de la salida).
2. **Cada afirmación `[A2-n]`** contra `docs/investigacion/JJ-1_kaggle_metadata.json`: que el `sha256_cuerpo` corresponda a
   `cuerpo_crudo`, que cada fragmento citado como literal aparezca **exactamente** en el cuerpo crudo y en el campo indicado,
   y que las ausencias afirmadas («no aparece "synthetic"», «no hay DOI», «no hay columnas documentadas») se comprueben con una
   búsqueda programática sin distinguir mayúsculas. Contrasta también los tamaños y fechas que da la fuente con los archivos
   locales. Si lo consideras necesario, vuelve a consultar los mismos endpoints públicos y guarda lo que obtengas en
   `alucinaciones/evidencias/JJ-1a/` (no sobrescribas `JJ-1_kaggle_metadata.json`).
3. **Afirmaciones interpretativas o no pedidas**: señala toda frase de A1 o A2 que vaya más allá de lo medido o de lo citado
   (conclusiones, recomendaciones, significados de columnas, «es real/sintético», formato de la cita APA 7, correspondencia
   entre archivos y componentes de la descripción) y di si está respaldada, es razonable pero inferida, o no tiene respaldo.
4. Clasifica cada afirmación: **correcta / incorrecta / imprecisa / no verificable / inferencia no respaldada**.
5. **Candidatos a hallazgo**: si un subagente afirmó algo falso o no respaldado (una columna que no existe, un significado
   inventado, un número que no se reproduce, una cita que no está literal en la fuente, «es sintético/real» sin cita), redacta
   el candidato con la plantilla de 6 puntos (prompt literal → enlace al archivo de prompt; respuesta relevante citada; cómo se
   sospechó; evidencia reproducible guardada en `alucinaciones/evidencias/JJ-1a/`; corrección; lección). **No lo numeres (no
   uses H-xx) y no edites `alucinaciones/registro.md`**: la numeración la coordina Andrés. Nunca inventes ni exageres un
   hallazgo; un error de redacción menor o una inferencia razonable bien marcada no es una alucinación. Registra también las
   verificaciones que salieron correctas.

## Reglas
- Prohibido inventar: todo veredicto con evidencia ejecutada o con el fragmento literal de la respuesta cruda.
- Crea solo: `alucinaciones/evidencias/JJ-1a/verificar_A3.py`, su salida `alucinaciones/evidencias/JJ-1a/verificar_A3_salida.txt`,
  lo que vuelvas a descargar (en esa misma carpeta) y tu informe `docs/investigacion/JJ-1_verificacion_A3.md`. No modifiques los
  archivos de A1 ni de A2, ni nada en `src/`, `configs/`, `data/`, `results/`, `tests/`, `blog/`, ni `alucinaciones/registro.md`.
- No leas los CSV con nada que ejecute su contenido; solo pandas/csv.

## Entrega
`docs/investigacion/JJ-1_verificacion_A3.md` con: (1) tabla de verificación de todas las `[A1-n]` y `[A2-n]` (id, afirmación
resumida, veredicto, valor verificado, evidencia: sección de tu salida o campo JSON); (2) errores encontrados en el script de A1;
(3) afirmaciones interpretativas; (4) candidatos a hallazgo con la plantilla de 6 puntos, sin numerar; (5) verificaciones
correctas. En tu mensaje final: resumen de los veredictos (cuántas de cada clase), los candidatos y los archivos creados.
