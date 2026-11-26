# Respuesta literal de R1 (revisor-spec, Sonnet), primera revisión — JJ-1b — 2026-11-25

Prompt: `alucinaciones/prompts/JJ-1b-revisor-spec.md`. Copiado sin cambios del informe final del subagente.

---

**Veredicto: RECHAZADO.** Hay 2 hallazgos bloqueantes, ambos de una línea de texto. La estructura, D1–D7, el contrato §5.12, la privacidad y las pruebas están bien. Con esas dos correcciones y la nota sobre §5.7 se aprobaría sin repetir la implementación.

## Ejecución (sin cambiar nada)
- `.venv\Scripts\python -m pytest -q tests/test_datos_m3.py` da `35 passed in 6.43s`.
- La suite completa `pytest -q -m "not lento"` da `364 passed in 32.60s`.
- `.venv\Scripts\python run.py m3-datos --config configs/m3/datos.yaml` tardó 1.6 s y devolvió 999 usuarios, 1000 destinos, 5 lugares, interacciones resena 999, historial 999, union 1998 y densidad de la unión 0.002000 (maestras) y 0.002689 (los que aparecen).
- Los 6 SHA-256 de las salidas coinciden con los del implementador (`064bd2db…`, `c55e0981…`, `8135ee4a…`, `7e217a72…`, `9856d77852…`, `76791bbf…`).
- Probé una vez `--set ficha.k_max_periodicidad=5`: sobrescribe bien, pero cambió `ficha.json`. Volví a correr con la config por defecto y quedaron los hashes originales. No queda nada modificado.
- Recálculo propio con un script en el scratchpad:
  - La unión da 1 998 pares y la intersección Reviews ∩ UserHistory es 0.
  - Hay 606 usuarios con ≥ 2 interacciones y 858 aparecen.
  - Busqué los 20 nombres, los correos y los 3 textos de reseña en `data/processed/m3/` y `results/data/m3/eda/`: 0 coincidencias (D6 se cumple).
  - Las citas literales (`generated for…`, `enriched with gender diversity`, `Remember to cite the source`) son subcadenas de `JJ-1_kaggle_metadata.json`.

## Bloqueantes

**B-1. Afirmación normativa sin verificar y que no pide el Spec (núcleo §0.4 y §0.5; D5).**
- Dónde: `configs/m3/datos.yaml:37-40` (`lectura_licencia`), que `datos.py:443-444` copia a `licencia.contradiccion` de `ficha.json`. También `data/fuentes.md:150` y `docs/investigacion/JJ-1_fuentes_m3.md:225`.
- Qué dice: «las tres [declaraciones] permiten el uso y todas piden citar la fuente».
- Por qué falla:
  - La sección «License» de la descripción no pide citar.
  - CC0 no exige atribución.
  - MIT exige conservar el aviso de copyright, que no es lo mismo que «citar la fuente».
  - Solo «Usage» pide citar.
  - A3 verificó únicamente que MIT y CC0 permiten el uso comercial (`JJ-1_verificacion_A3.md:134`), no esto.
- D5 solo pide citar la MIT del campo formal y documentar la contradicción. `lectura_licencia` no sale de la decisión: es un añadido del implementador (su §4.1).
- Corrección: borrar «y todas piden citar la fuente» en esos 4 sitios. Dejar «las tres permiten el uso no comercial» y «Usage» pide citar. Registrar el caso como candidato en `alucinaciones/registro.md`.

**B-2. El texto de una inconsistencia contradice su propia medición (núcleo §0.4; prompt B3.7).**
- Dónde: `src/m3_recomendacion/datos.py:418-419`, id `vocabularios_preferencias_vs_type`, que sale en `diccionario.json`.
- Qué dice: «Las opciones de Preferences y los valores de Type **no comparten vocabulario**».
- Lo que mide `medido` en la misma entrada: 4 de 5 coinciden. Solo `Beaches` (Preferences) y `Beach` (Type) difieren.
- Corrección: derivar la frase de las diferencias medidas. Por ejemplo, «los vocabularios coinciden salvo `Beaches` ↔ `Beach`: cruzarlos exige un emparejamiento supuesto». Esa frase debe depender de `solo_en_preferencias` y `solo_en_type`.

## Menores (no bloquean, pero conviene cerrarlos)

**M-1. Contrato §5.7 no coincide con las columnas reales.**
- §5.7 dice `usuario_id, destino_id, calificacion, [fecha], split`. El parquet trae `usuario_id, destino_id, origen, id_origen, calificacion, fecha_visita`.
- `origen` lo pide D1, y la ausencia de `split` es correcta (D3: lo crea JJ-3).
- `fecha_visita` en vez de `fecha` e `id_origen` son añadidos del diseño del orquestador. D1 no menciona `id_origen`. Su único uso es la trazabilidad a la fila cruda.
- Acción: o se ajusta §5.7 por PR con subida de versión y avisando (§0.1; Juan José es el único consumidor), o se renombra a `fecha`. Decidir también si `id_origen` se queda.

**M-2. `real_o_sintetico` y `licencia` están como claves de primer nivel de la ficha. No contradice §5.12.**
- §5.12 pide 10 claves (todas presentes, `validar_ficha` pasa) y que los *conteos* vayan bajo `conteos`.
- Esas dos claves no son conteos. La fila M3 de la plantilla exige «¿real o sintético?» en la ficha, y el validador no prohíbe claves extra.
- La ficha de M1 tiene solo las 10 claves, así que M3 no queda estrictamente «igual en los tres módulos». Basta una línea en `juanjose.md` §3.1 o en §5.12 que registre esas dos claves.

**M-3. D4 enumera «3 textos de reseña sin relación con el destino», pero la ficha no lo mide.**
- `ficha.json` → `senales_medidas.resenas` solo trae `textos_distintos: 3`. La V de Cramér = 0.043 y p = 0.884 están únicamente en `diccionario.json`.
- El implementador omitió el adjetivo «sin relación» a propósito. Es defendible y honesto, pero D4 y B3.7 lo piden como señal.
- Sugerencia: copiar `asociacion_con_el_lugar_del_destino` a `senales_medidas.resenas`.

**M-4. Texto fijo de la conclusión sin enlace con la medición.**
- `configs/m3/datos.yaml:70` dice «no usa la palabra synthetic ni dice con qué método», pero `palabra_synthetic_en_la_fuente` se calcula aparte. Si la fuente cambiara, el texto quedaría obsoleto. Hoy es correcto.

**M-5. El texto de D4 en el Spec dice «3 fechas posteriores a la publicación».**
- Lo medido es 3 valores distintos de `VisitDate`, de los cuales 2 son posteriores (666 de 999 filas). El código es correcto; la redacción del Spec (`juanjose.md` §3.1 D4) está floja. No se registra en el diccionario.

**M-6. `diccionario.json` repite el mismo párrafo del componente en cada columna.**
- Pasa en las 23 columnas, con `significado: «no documentado por la fuente»`. Es honesto, porque la fuente no documenta columnas (`columns` vacío).
- La descripción menciona explícitamente «popularity», «best time to visit», «type of destination», «preferences» y el número de adultos y niños. Podría decir qué frase cubre qué variable. No hace falta para aprobar.

## Cumplimiento por punto pedido
1. **§5.7:**
   - `destinos.parquet` trae `destino_id, nombre, lugar, estado, tipo, mejor_epoca, popularidad`.
   - `usuarios.parquet` trae `usuario_id, preferencias, pref_*` (5 opciones medidas), `genero, n_adultos, n_ninos`.
   - `interacciones.parquet` no tiene `split`. Ver M-1.
2. **§5.12:** `ficha.json` pasa `validar_ficha`. `calidad.csv` tiene `tabla, filas, duplicados_clave` más las columnas de `tabla_calidad`, igual que M1. `diccionario.json` trae variables citadas de la fuente, faltantes (0) y 6 inconsistencias calculadas. Ver B-2.
3. **Anexo M3 «Datos»:** completo.
   - Usuarios, destinos e interacciones: 999, 1 000 y 1 998.
   - Escala 1–5 con frecuencias.
   - Densidad con dos denominadores.
   - Variables de usuarios y destinos.
   - Real o sintético, con cita, señales medidas, conclusión e implicación.
   - Todo sale de la salida regenerable por `run.py m3-datos`.
4. **D1–D7:**
   - D1, D2, D3, D4, D6 cumplen. `fecha_visita` solo descriptiva y sin partición.
   - D5 cita MIT y la contradicción, pero añade el texto malo de B-1.
   - D7: no se registró el candidato débil en ningún archivo revisado.
5. **Diseño B1–B7:** B1 a B6 cumplidos. B7: `licencia_mit.html` y `licencia_cc0.html` borrados, `indice_licencias.txt` con la línea nueva, y `JJ-1_verificacion_A3.md` (líneas 15 y 134) y `JJ-1_fuentes_m3.md` §3.2 apuntan a las URL oficiales. Los `respuesta-*.md` no se tocaron.
   - De las desviaciones del §4 del implementador, ninguna contradice el Spec ni D1–D7, salvo `lectura_licencia` (B-1).
   - `licencia` y `real_o_sintetico` fuera de `conteos`: ver M-2.
6. **Reglas:**
   - Sin red en `datos.py`: solo stdlib, pandas y scipy.
   - Config sin semillas.
   - Cifras calculadas, no copiadas.
   - Citas verificadas como subcadenas en tiempo de ejecución, con test de fallo.
   - Salidas deterministas.
   - `mehra2024` en `blog/references.bib` coincide con el JSON (autor, 2024, versión 1, URL).
   - Los comentarios de `data/fuentes.md` y de `src/m3_recomendacion/README.md` coinciden con la realidad.

## Archivos relevantes
- `C:\Repositorios\Trabajo3_Redes_Neuronales\src\m3_recomendacion\datos.py`
- `C:\Repositorios\Trabajo3_Redes_Neuronales\configs\m3\datos.yaml`
- `C:\Repositorios\Trabajo3_Redes_Neuronales\results\data\m3\eda\{ficha.json,calidad.csv,diccionario.json}`
- `C:\Repositorios\Trabajo3_Redes_Neuronales\data\fuentes.md` (línea 150)
- `C:\Repositorios\Trabajo3_Redes_Neuronales\docs\investigacion\JJ-1_fuentes_m3.md` (línea 225)
- `C:\Repositorios\Trabajo3_Redes_Neuronales\tests\test_datos_m3.py`
