# Respuesta literal de A3 (cazador-alucinaciones, Opus) — JJ-1a — 2026-11-25

Prompt: `alucinaciones/prompts/JJ-1a-cazador-alucinaciones.md`. Copiado sin cambios del informe final del subagente. El informe
completo está en `docs/investigacion/JJ-1_verificacion_A3.md`.

---

## A3 (cazador-alucinaciones, JJ-1 fase A): resultado

A1 y A2 no inventaron nada. No hay columnas, significados ni citas inventadas, todos los números se reproducen y ninguno afirmó «real» o «sintético» sin cita. No hay ningún candidato sólido a hallazgo. Mi script hizo 140 comprobaciones automáticas: 137 coinciden y 3 difieren, y las 3 son redondeos menores de A1.

### Veredictos (63 afirmaciones numeradas)
| Clase | A1 (43) | A2 (20) | Total |
|---|---|---|---|
| Correcta | 39 | 20 | 59 |
| Imprecisa | 3 | 0 | 3 |
| Inferencia no respaldada | 1 | 0 | 1 |
| Incorrecta | 0 | 0 | 0 |
| No verificable | 0 | 0 | 0 |

Las cuatro que no son del todo correctas son de A1 y en todas el número de fondo está bien:
- **A1-22 (imprecisa):** dice que la pureza es 0.333 en los k que no son múltiplo de 3. En realidad va de 0.333 a 0.364 (k=52).
- **A1-37 (imprecisa):** da un p máximo de 0.83; el real es 0.8247, que redondea a 0.82.
- **A1-42 (imprecisa):** pone la cota «Kruskal-Wallis ≥ 0.26», pero el mínimo real es 0.2576.
- **A1-34 (inferencia no respaldada):** concluye que las variables «son independientes» porque todos los p son ≥ 0.20. No rechazar H0 no demuestra independencia, y la prueba tiene poca potencia (0.21 a 0.35 frente a una dependencia pequeña, w=0.05).

Fuera de la lista numerada hay dos imprecisiones de A2:
- **«Inconsistencia de tamaño» en Kaggle:** el 34679 de un endpoint es exactamente el tamaño del `archive.zip` descargado. Es casi seguro el tamaño comprimido frente a la suma sin comprimir, no una contradicción. Lo de «comprimido» es inferencia; la API no documenta el campo.
- **Cita APA 7:** APA escribe el título en minúscula de oración (`*Travel recommendation dataset*`), y la cita mezcla «Versión 1» con «[Data set]». La página oficial de APA bloqueó la descarga directa; el ejemplo oficial lo tomé del buscador.

También hay afirmaciones interpretativas de A1 que van más allá de lo medido:
- «Un modelo no puede aprender identidad de destino» no está respaldada. Es una afirmación de modelado, y A1 tenía orden de no decidir modelado.
- «Solo permitiría 3 cortes» es imprecisa: con 3 fechas hay a lo sumo 2 puntos de corte.

### Script de A1 y reproducibilidad
- No hay errores que cambien un número. Las fórmulas de densidad, los conteos «< k» con y sin ceros, el índice de dispersión (1−1/N exacto), la tasa esperada de coincidencia y el χ² están bien.
- Ejecuté el script original dos veces sin dejar que escribiera a disco. La salida es idéntica bit a bit a la guardada (SHA-256 `d3d258d7…88cb93`).
- Tres notas de método, ninguna cambia una afirmación de A1:
  - El p de la fila «Preferences (opciones separadas)» (6.959e-47) no es una prueba válida y no debe ir al blog.
  - El χ² no usa la corrección de Yates y no lo declara; solo afecta a una tabla 2×2 y la conclusión no cambia.
  - Hay más de 60 valores p, y los «significativos» (0.0074 a 0.033) no resisten una corrección de Bonferroni.

### Fuente de A2
- Los 5 hashes del JSON son correctos.
- Volví a descargar los 4 endpoints distintos y son idénticos byte a byte a lo que guardó A2, así que el JSON no fue fabricado ni editado.
- Las 10 citas que comprobé están literales en el campo indicado, y la descripción completa coincide exactamente con la fuente.
- Las ausencias (synthetic, DOI, columnas documentadas, fecha de publicación) las confirmé con búsqueda por código, sin distinguir mayúsculas.
- La contradicción de licencias se confirma con los textos oficiales: MIT y CC0 permiten el uso comercial y la sección «Usage» lo restringe.

### Dato nuevo para el blog (es un hallazgo de datos, no una alucinación)
666 de las 999 filas de UserHistory tienen `VisitDate` posterior al 2024-01-23, que es cuando se creó la versión 1 en Kaggle. Además, como `VisitDate` depende exactamente de `HistoryID mod 3`, partir «por tiempo» equivale a partir por el resto del id de fila.

### Candidatos a hallazgo
- **Sólidos:** ninguno.
- **Uno débil, sin numerar:** el de A1-34 («no significativo» presentado como «independientes»), en M3 / Matemáticas. Está redactado con la plantilla de 6 puntos en §4 del informe. **Recomiendo no contarlo**; lo decide Andrés.
- La cobertura de la cacería no cambia: sigue solo H-01 (Común / Código, candidato) y M3 sigue sin hallazgo. No edité `registro.md`.

### Archivos creados
- `C:\Repositorios\Trabajo3_Redes_Neuronales\docs\investigacion\JJ-1_verificacion_A3.md`: el informe, con la tabla completa de veredictos, la revisión del script, las interpretativas, el candidato y las verificaciones correctas.
- `C:\Repositorios\Trabajo3_Redes_Neuronales\alucinaciones\evidencias\JJ-1a\verificar_A3.py`: mi script independiente. Se corre con `.venv\Scripts\python -I alucinaciones/evidencias/JJ-1a/verificar_A3.py`, sin internet, y es determinista.
- `C:\Repositorios\Trabajo3_Redes_Neuronales\alucinaciones\evidencias\JJ-1a\verificar_A3_salida.txt`: su salida (SHA-256 `72613f12…28f0`).
- `C:\Repositorios\Trabajo3_Redes_Neuronales\alucinaciones\evidencias\JJ-1a\redescarga_A3\`: las respuestas re-descargadas de Kaggle (`r0..r3.body`, `indice.txt`) y los textos de las licencias (`licencia_mit.html`, `licencia_cc0.html`, `indice_licencias.txt`).

No toqué los archivos de A1 ni de A2, ni `registro.md`, `src/`, `data/`, `results/`, `tests/` o `blog/`. No hice commit, push ni PR.

Fuentes:
- [MIT License (opensource.org)](https://opensource.org/license/mit)
- [CC0 1.0 (creativecommons.org)](https://creativecommons.org/publicdomain/zero/1.0/)
- [APA Style: data set references](https://apastyle.apa.org/style-grammar-guidelines/references/examples/data-set-references) (descarga directa bloqueada; ejemplo tomado del buscador)
