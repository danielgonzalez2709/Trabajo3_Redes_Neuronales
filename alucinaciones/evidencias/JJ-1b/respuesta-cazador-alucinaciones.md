# Respuesta literal de R3 (cazador-alucinaciones, Opus) — JJ-1b — 2026-11-25

Prompt: `alucinaciones/prompts/JJ-1b-cazador-alucinaciones.md`. Copiado sin cambios del informe final del subagente. Informe
completo: `docs/investigacion/JJ-1_verificacion_R3.md`.

---

## R3 de JJ-1b: 71 afirmaciones vigentes revisadas, ninguna incorrecta; registré 2 candidatos sin número

Las comprobé con código propio que no importa `datos.py`: 279 comprobaciones automáticas, las 279 iguales, y dos corridas dan la misma salida (SHA-256 `5f69e5ab…7c36`). No hice commit ni push. En el repo solo creé los archivos que permitías y agregué texto a `registro.md`.

### Recuento de veredictos
| Veredicto | Vigentes (01–71) | Históricas, ya corregidas |
|---|---|---|
| Correcta | 69 | — |
| Imprecisa | 1 | 1 (D) |
| No verificable | 1 | 1 (C) |
| Incorrecta | 0 | 2 (A, B) |
| Inferencia no respaldada | 0 | 0 |

- **Imprecisa (fila 24):** el rótulo «fecha de publicación (2024-01-23)» en `ficha.json` y `diccionario.json`. Kaggle no da una fecha de publicación, sino la de creación de la versión 1 y de cada archivo (2024-01-23, 17:07 UTC). El fondo se sostiene: 2 de los 3 valores de VisitDate son posteriores a la creación de los propios archivos. Bastaría decir «creación de la versión 1». El rótulo viene de D3, así que no es alucinación.
- **No verificable (fila 52):** «lo descargó Juan José a mano». Es una declaración del humano; coincide con el prompt `JJ-1a.md`.

### Lo que salió bien
- **Cifras y citas:** coinciden todas las de `ficha.json`, `diccionario.json`, la sección M3 de `fuentes.md` y `mehra2024`, incluidos el χ², gl, p y la V de Cramér, que recalculé a mano.
- **Los tres parquet:** tienen las columnas de D1, D2 y D6, sin `Name`, `Email`, `ReviewText` ni `split`. Cada interacción corresponde a su fila cruda por `origen` + `id_origen`, en ambos sentidos. No aparece ningún nombre, correo ni texto de reseña en las salidas.
- **Licencias:** contrasté con los textos oficiales lo que dicen `JJ-1_fuentes_m3.md` §3.2 y la fila Licencia de `fuentes.md`, y es correcto:
  - CC0 no exige atribución.
  - La única condición de la MIT es conservar el aviso de copyright y de permiso en las copias.
  - Solo «Usage» pide citar.
- **DOI:** no encontré ninguno ni en DataCite (con el prefijo de Kaggle, 10.34740) ni en Crossref. Por eso la regla de sacar el BibTeX del DOI no aplica a `mehra2024`; la contrasté con la metadata oficial de Kaggle.

### Candidatos registrados en `alucinaciones/registro.md`
Los dos van como `### H-?? (JJ-1b)`, con la plantilla de 6 puntos; la numeración queda para Andrés.
- **A. «Las tres licencias piden citar la fuente».** M3 / Datos del mundo real. Es incorrecta.
  - La escribió la orquestadora (Opus) en la fase A (prompt `JJ-1a.md`). El implementador (Sonnet) la copió y la amplió (prompt `JJ-1b-implementador.md`).
  - La evidencia es reproducible: solo «Usage» contiene «cite». Los fragmentos literales de MIT y CC0 están en `licencias_fragmentos.md` y el script los comprueba.
  - Límite: los archivos no estaban versionados. El texto original solo consta en la nota de corrección de §3.2, en el informe del revisor (B-1) y en el `README.md` de `licencia_citar`.
  - Posible origen: A2 cerró su respuesta con «Pide citar la fuente.», sin sujeto.
- **B. «Preferences y Type no comparten vocabulario».** M3 / Datos del mundo real (o Código). Es un candidato menor.
  - El implementador (Sonnet) la dejó como texto fijo en `datos.py`, y contradecía su propia medición. Lo detectó el revisor-spec (B-2).
  - Lo reproduje desde los CSV: 4 de 5 opciones coinciden y solo difieren `Beaches` y `Beach`.
  - Límite: el texto original solo consta en la cita literal del revisor; el `diccionario.json` de esa versión ya no existe. Decide Andrés.

También llené la celda M3 / Datos del mundo real de la tabla de cobertura y agregué un resumen de las fases A y B en «Verificaciones que salieron correctas».

### Descartados
- **C. El `\x08` en la regex de `datos.py`:** no lo registré porque no hay evidencia reproducible. Solo existe el autoinforme del implementador.
  - `datos.py` no está versionado y no queda copia de la versión defectuosa.
  - `grep -P "\x08"` no lo encuentra en ningún archivo de texto de M3.
  - El `.pyc` está compilado desde la fuente actual (misma fecha y tamaño en la cabecera) y no tiene 0x08 en ninguna constante.
  - La regex actual está bien escrita.
- **D. «La frase falsa nació en mi propio texto» (implementador, ronda 2):** es imprecisa, porque la frase ya estaba en §3.2 de la fase A. Es una atribución equivocada sobre el proceso, no sobre datos, normas ni código; solo explica de dónde vino A.
- **Candidato de A1 sobre «independencia» (D7):** no lo registré, como pediste.

### Cobertura de la cacería
- Confirmados: 0 de los 5 requeridos.
- Candidatos: H-01 (Común, Código) y los dos de JJ-1b (M3, Datos del mundo real).
- Categorías con candidato: 2 de 5; falta al menos una de Matemáticas, Bibliografía o Conceptos. Módulos: M3 y Común; faltan M1 y M2.
- En M3 quedan pendientes los puntos calientes de JJ-3 a JJ-5 y JJ-9: NDCG y Recall@K, el signo de BPR, «BCE ≡ BPR», la popularidad con fuga y las referencias de NCF, BPR y Adam.

### Notas para Juan José
- `data/processed/m3/` no está en `.gitignore`, así que los parquet derivados se versionarían. Con la lectura MIT irían acompañados del aviso de copyright, pero la fuente no publica ninguno concreto. Es un punto para la sección de ética, no un hallazgo.
- Al verificar volví a correr `licencia_citar/verificar.py`, que reescribe su `salida.txt`. El texto quedó igual; solo cambió la fecha de modificación.
- Los textos completos de las licencias están solo en el scratchpad, no en el repo. Para que el script repita la comprobación de las licencias hay que pasarle esa carpeta como argumento; sin ella omite esa parte.

### Archivos
- `docs/investigacion/JJ-1_verificacion_R3.md` (informe con la tabla completa)
- `alucinaciones/evidencias/JJ-1b/verificar_R3.py`
- `alucinaciones/evidencias/JJ-1b/verificar_R3_salida.txt`
- `alucinaciones/evidencias/JJ-1b/licencias_fragmentos.md` (fragmentos con URL y hora de consulta, 2026-11-26 00:36 UTC)
- `alucinaciones/registro.md` (dos candidatos, celda de cobertura M3 y verificaciones correctas)
