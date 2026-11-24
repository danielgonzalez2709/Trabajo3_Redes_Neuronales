# Registro de la Cacería de la alucinación

Meta: ≥ 5 hallazgos genuinos, ≥ 3 categorías (Matemáticas, Código, Datos del mundo real, Bibliografía, Conceptos),
≥ 1 por módulo (M1, M2, M3) y ≥ 1 por persona. Consolida: Andrés. **Nunca inventar:** un hallazgo sin prompt literal o sin
evidencia no cuenta.

## Cobertura
| Módulo / categoría | Matemáticas | Código | Datos del mundo real | Bibliografía | Conceptos |
|---|---|---|---|---|---|
| M1 | | | | | |
| M2 | | | | | |
| M3 | | | | | |
| Común | | H-01 (candidato) | | | |

## Hallazgos

### H-01 — La marca `\bibliografia` del blog se guardó con un carácter de control
- **Módulo / categoría / quién lo encontró:** Común (blog) / **Código** / Daniel (lo detectó el subagente `redactor-tecnico`
  de DA-9a al citar la primera referencia; lo confirmó Daniel con los bytes del commit).
- **1. Prompt literal:** `alucinaciones/prompts/DA-1b.md` (subagente `implementador`, Sonnet, 24-nov-2026), que pedía portar
  `blog/docs/index.md` del Trabajo 2 con la marca de bibliografía.
- **2. Respuesta relevante de la IA:** el archivo `blog/docs/index.md` del commit `ba19487` contiene los bytes
  `\n\x08ibliografia` (backspace, 0x08) donde debía ir `\bibliografia`, y el agente reportó «`mkdocs build --strict` termina con
  código 0 … No hay WARNING ni ERROR».
- **3. Cómo se sospechó:** en DA-9a, al agregar la primera cita (`[@supertransporte2026]`), el build estricto falló con
  «citas sin marca de bibliografía»; el agente encontró el byte 0x08 al inspeccionar la marca.
- **4. Evidencia:** `alucinaciones/evidencias/H-01_backspace/verificar.py` y `salida.txt`: en `ba19487` la marca es
  `b'\n\x08ibliografia'` (contiene 0x08: True); en el árbol corregido es `b'\\bibliografia'` (0x08: False). El build pasaba
  porque el hook solo exige la marca cuando hay citas, y en DA-1b el blog no tenía ninguna.
- **5. Corrección:** se reescribió la marca como `\bibliografia` (DA-9a) y se agregaron dos pruebas en `tests/test_blog.py`
  (`test_fuentes_del_blog_sin_caracteres_de_control`, `test_la_marca_de_bibliografia_esta_bien_escrita`) que fallan con la
  versión de `ba19487` y pasan con la corregida.
- **6. Lección aprendida:** «el build pasa» no prueba que una marca funcione si el caso que la ejercita no existe todavía.
  Una prueba con una cita de prueba (o que busque caracteres de control) lo habría atrapado en DA-1. Al escribir archivos con
  barras invertidas desde código (`"\b"` en Python es backspace), usar cadenas crudas o verificar los bytes.
- **Estado:** candidato (falta revisión de Andrés como consolidador). Nota: es un error de escritura de código de la IA, no
  una afirmación falsa; Andrés decide si cuenta en la categoría Código.

## Plantilla (copiar por hallazgo)
### H-XX — título corto
- **Módulo / categoría / quién lo encontró:**
- **1. Prompt literal:** enlace a `alucinaciones/prompts/<ID>.md`
- **2. Respuesta relevante de la IA:**
- **3. Cómo se sospechó:**
- **4. Evidencia** (derivación, experimento o fuente primaria): enlace a `alucinaciones/evidencias/`
- **5. Corrección:**
- **6. Lección aprendida** (qué verificación lo habría evitado):
- **Estado:** candidato / confirmado / descartado

## Verificaciones que salieron correctas
<!-- El enunciado permite documentarlas si faltan hallazgos. -->
