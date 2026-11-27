## M3 — Recomendación de destinos

<!-- JJ-2 (redactor-tecnico, Sonnet) para Juan José. Toda cifra sale de results/data/m3/eda/ (ruta entre paréntesis o en la fuente de cada tabla/figura). Las subsecciones «Implicaciones» y «Veredicto» son parciales hasta JJ-5/JJ-6/JJ-10. -->

**Caso de uso.** La empresa lanza una línea de turismo internacional con destinos en India. La recomendación se muestra en la
aplicación web de la empresa, en la sección de esa línea, cuando el cliente entra a explorar viajes; opcionalmente podría
repetirse en un correo de campaña. Se muestran **K = 5 destinos por defecto** (`k_defecto` = 5 y `k_max` = 10 en el contrato de la
aplicación, `app/public/model/m3/perfil_nuevo.json`; núcleo §5.8) y las métricas se evalúan para K ∈ {1, 3, 5, 10}. Al momento de
recomendar se dispone del historial de interacciones previas del cliente (visitas y reseñas), de las preferencias que declara al
registrarse y de datos demográficos básicos (género, número de adultos y número de niños). No se usan el nombre ni el correo
(decisión D6, `docs/spec/partes/juanjose.md` §3.1). Un cliente nuevo solo tiene sus preferencias (y, si las declara, su demografía).

<!-- revisar: Juan José — el canal (app web, correo opcional) y el momento («cuando explora viajes») son descripción nuestra del caso de uso; el Spec solo fija K por defecto (§5.8) y K ∈ {1, 3, 5, 10} es [PROPUESTO] en tu spec §3.3. Además, `perfil_nuevo.json` es hoy un JUGUETE con opciones de preferencia que no existen en el conjunto real (p. ej. «gastronomía», «montaña»): la lista real son las 5 opciones de Preferences. -->

### Análisis descriptivo

Los datos de M3 son **generados, no observados** (véase la Ficha). Ninguna frase de esta sección atribuye un patrón al comportamiento
de turistas reales: describe el conjunto de Kaggle y lo que implica para evaluar métodos de recomendación.

#### Ficha del conjunto

El conjunto es el que pide el enunciado: *Travel Recommendation Dataset* (India Travel Recommender System Dataset), publicado en
Kaggle por Aman Mehra [@mehra2024] (`results/data/m3/eda/ficha.json`, campos `fuente`, `cita` y `url`). La descarga fue manual el
**25 de noviembre de 2026** (`ficha.json`, `fecha_descarga`); el archivo `archive.zip` y los cuatro CSV quedan registrados con su
SHA-256 (`ficha.json`, campo `sha256`). La fecha **2024-01-23** que aparece en los análisis es la **creación de la versión 1 en
Kaggle**, no una fecha de publicación del conjunto (`ficha.json`, `periodo` y `real_o_sintetico.senales_medidas.visit_date`).

**Tamaño.** Hay **999 usuarios**, **1 000 destinos** y **1 998 interacciones**, que son la unión de 999 reseñas y 999 registros de
historial; los dos archivos no comparten ningún par (usuario, destino) y por eso se unen como una sola interacción implícita
(decisión D1; `ficha.json`, `conteos.interacciones`). Los 1 000 destinos son en realidad **5 lugares** repetidos 200 veces cada uno
(`ficha.json`, `conteos.lugares` y `real_o_sintetico.senales_medidas.destinos`). No todos los usuarios y destinos aparecen en alguna
interacción ([[tab:m3-ficha]]).

::: tabla m3-ficha
Título: Ficha del conjunto Travel Recommendation Dataset tal como entra a M3
Fuente: `results/data/m3/eda/ficha.json` (`conteos.interacciones`, `conteos.usuarios_que_aparecen`, `conteos.destinos_que_aparecen`, `conteos.escala_calificacion`, `conteos.densidad`, `conteos.variables_por_archivo`, `n_variables`); `results/data/m3/eda/calificaciones.csv` (media y desviación). Datos de [@mehra2024], descarga del 2026-11-25.

| Concepto | Reseñas | Historial | Unión (interacciones del modelo) |
|---|---:|---:|---:|
| Interacciones | 999 | 999 | 1 998 |
| Usuarios que aparecen (de 999) | 624 | 642 | 858 |
| Destinos que aparecen (de 1 000) | 651 | 638 | 866 |
| Escala de la calificación | 1 a 5, enteros | 1 a 5, enteros | 1 a 5, enteros |
| Calificación: media (desviación) | 3,023 (1,419) | 2,905 (1,398) | 2,964 (1,409) |
| Densidad con las matrices completas (999 × 1 000 = 999 000 pares) | 0,001 | 0,001 | 0,002 (0,2 %) |
| Densidad con los usuarios y destinos que aparecen | 0,00246 | 0,00244 | 0,00269 |
| Denominador de esta segunda densidad | 406 224 | 409 596 | 743 028 |
:::

La unidad de observación es el par (usuario, destino) con una interacción implícita; la calificación es un atributo de la
interacción, no el objetivo del modelo (`ficha.json`, `unidad_de_observacion`). La densidad de la matriz usuario–destino es de
**0,2 %** si se cuenta sobre todos los usuarios y destinos del catálogo (`ficha.json`, `conteos.densidad.union.maestras` = 0,002) y
de 0,269 % si se cuenta solo sobre los que aparecen en alguna interacción (`los_que_aparecen` = 0,00269, redondeado a tres cifras
significativas). La calificación va de 1 a 5, con valores enteros, y en la unión sus frecuencias son 404, 427, 386, 399 y 382 para
las calificaciones 1 a 5 (`results/data/m3/eda/calificaciones.csv`, origen `union`).

**¿Real o sintético?** La documentación de la fuente dice que el conjunto fue «generated for educational and research purposes» y
«enriched with gender diversity» (`ficha.json`, `real_o_sintetico.citas_literales`). La fuente **no usa la palabra «synthetic»** ni
dice con qué método se generó (`palabra_synthetic_en_la_fuente` = false). Además, los datos muestran señales medidas que son
compatibles con generación por programa (`real_o_sintetico.senales_medidas`):

- Los 1 000 destinos son 5 lugares con 200 ids cada uno (`destinos`).
- Las 999 reseñas tienen solo 3 textos distintos (333 cada uno), sin relación con el lugar del destino reseñado: V de Cramér = 0,043
  y p del χ² = 0,884 (`resenas`).
- `VisitDate` toma 3 valores (2024-01-01, 2024-02-15 y 2024-03-20) y 666 de 999 filas son posteriores a la creación de la versión
  1 en Kaggle (2024-01-23) (`visit_date`).
- Los 999 usuarios tienen solo 20 nombres distintos y 3 combinaciones de preferencias (`usuarios`).
- Los nombres de destino (5), los textos de reseña (3), las fechas (3) y las preferencias (3) son periódicos en el identificador
  (`periodicidad_con_el_id`).

La conclusión de `ficha.json` (`real_o_sintetico.conclusion`) es: **datos generados, no observados**. Lo que implica es que las
conclusiones valen para comparar **métodos de recomendación** sobre este conjunto, pero no dicen cómo se comportarían turistas
reales; y que, si los datos se generaron sin estructura, es esperable que ningún modelo supere por mucho a la línea base de azar.

**Licencia.** El campo formal de licencia de Kaggle es **MIT**, pero la descripción del conjunto dice en su sección «License»:
«CC0: Public Domain - The dataset is in the public domain and can be used without restrictions.» y, en «Usage», «This dataset is
free to use for non-commercial purposes. For commercial use, please contact the dataset provider. Remember to cite the source when
using this dataset in your projects.» (`ficha.json`, `licencia`). Las declaraciones son distintas entre sí. Aquí se cita la fuente en
cualquier caso, que es lo único que las tres piden en común; la contradicción queda documentada para la sección de ética (decisión
D5).

<!-- revisar: Juan José — «las tres piden citar la fuente» es candidato de cacería (JJ-1b, ver docs/MEMORIA.md): la cita literal de «Usage» sí lo pide; para CC0 y MIT no está medido que lo exijan. Considera quitar esa frase o redactarla solo sobre «Usage». -->

#### Diccionario y calidad

**La fuente no documenta ninguna columna**: la revisión de los metadatos de Kaggle (`datasetFiles[].columns` e `info.description`)
encontró 0 columnas documentadas y solo una descripción narrativa de cada componente (`results/data/m3/eda/diccionario.json`,
campos `fuente_del_diccionario` y `columnas_documentadas_por_la_fuente`). Por eso el significado de **cada** variable aparece en el
diccionario como «no documentado por la fuente», y la correspondencia entre archivos y componentes de la descripción es inferencia
nuestra (`diccionario.json`, `variables[*].nota_correspondencia`). La [[tab:m3-diccionario]] lista las variables y el nombre con
que pasan a los archivos procesados.

::: tabla m3-diccionario
Título: Variables de M3, con su nombre procesado (el significado no está documentado por la fuente)
Fuente: `results/data/m3/eda/diccionario.json`, campo `variables` (`columna_original`, `nombre_procesado`, `tipo`, `columnas_derivadas`, `excluida_motivo`). Los tipos de `n_categorias` salen de `results/data/m3/eda/ficha.json`, `conteos.variables_de_contenido`.

| Archivo de la fuente | Columna original | Nombre procesado | Tipo | Observación |
|---|---|---|---|---|
| Expanded_Destinations.csv | DestinationID | `destinos.destino_id` | entero | 1 000 valores únicos |
| Expanded_Destinations.csv | Name | `destinos.nombre` | texto | 5 valores; de aquí se deriva `destinos.lugar` (5 lugares) |
| Expanded_Destinations.csv | State | `destinos.estado` | texto | 5 valores |
| Expanded_Destinations.csv | Type | `destinos.tipo` | texto | 5 valores |
| Expanded_Destinations.csv | Popularity | `destinos.popularidad` | decimal | 1 000 valores distintos, de 7,504 a 9,500 |
| Expanded_Destinations.csv | BestTimeToVisit | `destinos.mejor_epoca` | texto | 5 valores |
| Final_Updated_Expanded_Users.csv | UserID | `usuarios.usuario_id` | entero | 999 valores únicos |
| Final_Updated_Expanded_Users.csv | Preferences | `usuarios.preferencias` | texto | 3 combinaciones; de aquí se derivan `pref_adventure`, `pref_beaches`, `pref_city`, `pref_historical` y `pref_nature` |
| Final_Updated_Expanded_Users.csv | Gender | `usuarios.genero` | texto | 2 valores |
| Final_Updated_Expanded_Users.csv | NumberOfAdults | `usuarios.n_adultos` | entero | 2 valores |
| Final_Updated_Expanded_Users.csv | NumberOfChildren | `usuarios.n_ninos` | entero | 3 valores |
| Final_Updated_Expanded_Users.csv | Name, Email | no pasan a lo procesado | texto | Privacidad (D6): se describen solo con conteos |
| Final_Updated_Expanded_Reviews.csv | ReviewID, UserID, DestinationID, Rating | `interacciones.id_origen`, `usuario_id`, `destino_id`, `calificacion` | entero | Origen `resena` |
| Final_Updated_Expanded_Reviews.csv | ReviewText | no pasa a lo procesado | texto | 3 textos distintos (D6) |
| Final_Updated_Expanded_UserHistory.csv | HistoryID, UserID, DestinationID, ExperienceRating | `interacciones.id_origen`, `usuario_id`, `destino_id`, `calificacion` | entero | Origen `historial` |
| Final_Updated_Expanded_UserHistory.csv | VisitDate | `interacciones.fecha_visita` | texto con forma AAAA-MM-DD | 3 valores; solo descriptiva (D3) |
:::

**Faltantes y duplicados.** Las tres tablas procesadas no tienen filas duplicadas por clave ni faltantes, salvo `fecha_visita`, que
no existe en las reseñas: 999 de 1 998 interacciones (50,0 %) no la tienen, y las demás toman 3 valores distintos
(`results/data/m3/eda/calidad.csv`, columnas `duplicados_clave`, `faltantes` y `pct_faltantes`; tablas `destinos`, `usuarios` e
`interacciones`).

**Inconsistencias del diccionario** (`diccionario.json`, campo `inconsistencias`; todas con `se_presenta` = true):

- **1 000 ids, 5 lugares.** Los 1 000 `DestinationID` corresponden a 5 lugares (`goa_beaches`, `jaipur_city`, `kerala_backwaters`,
  `leh_ladakh`, `taj_mahal`) con 200 ids cada uno, que comparten nombre, estado, tipo y temporada (`ids_vs_lugares`).
- **«mountain» no existe.** La descripción menciona destinos de tipo «mountain»; los valores de `Type` son solo `Adventure`, `Beach`,
  `City`, `Historical` y `Nature` (`tipo_buscado_ausente`).
- **`VisitDate`.** Solo 3 valores, función exacta de `HistoryID` módulo 3, y 666 de 999 posteriores a la creación de la versión 1
  en Kaggle: no es una fecha real y queda solo descriptiva (`visitdate_periodica_y_posterior`).
- **Texto de las reseñas.** `ReviewText` solo toma 3 valores, función exacta de `ReviewID` módulo 3 (`reviewtext_plantilla`).
- **Vocabularios distintos.** 4 de las 5 opciones de `Preferences` coinciden con valores de `Type`; solo está en preferencias
  «Beaches» y solo en el tipo «Beach». Cruzarlos exige un emparejamiento **nuestro**, no de la fuente
  (`vocabularios_preferencias_vs_type`).
- **Licencia.** El campo formal (MIT) no aparece en la sección «License» de la descripción (`licencias_contradictorias`).

**Qué no pasa a lo procesado (D6).** `Name` y `Email` identifican a la persona y no pasan a `data/processed/` ni a `results/` (20
nombres distintos y 20 correos distintos en 999 usuarios; los 999 correos tienen la forma «nombre en minúsculas + dominio»).
`ReviewText` tampoco pasa, por ser 3 textos sin relación con el destino (`diccionario.json`, `variables[*].excluida_motivo`).

#### Variable objetivo

El objetivo de los modelos es la **interacción implícita**: dado un usuario, ordenar los destinos con los que probablemente
interactuará. La calificación (1 a 5) se conserva como atributo con su origen (reseña o historial), pero no es el objetivo
(decisión D1; `ficha.json`, `unidad_de_observacion`).

**Interacciones por usuario y por destino.** [[fig:m3-cola-larga]] compara la distribución observada con la que resultaría de
repartir las mismas 1 998 interacciones al azar y de forma uniforme (2 000 simulaciones; `results/data/m3/eda/distribucion_actividad.json`).
Por usuario, 141 de 999 no tienen ninguna interacción, 252 tienen una, 280 tienen dos, 195 tienen tres, 79 tienen cuatro y 52 tienen
cinco o más, con un máximo observado de 7. Por destino, 134 de 1 000 no tienen ninguna, 271 tienen una, 270 dos, 184 tres, 89 cuatro,
37 cinco y 15 seis o más, con un máximo observado de 7 (`distribucion_actividad.json`, `usuarios.observado` y `destinos.observado`).
Esas cifras caen dentro de las bandas del reparto al azar en casi todos los casos; ver «Estructura y heterogeneidad».

::: figura m3-cola-larga
Título: Distribución de interacciones por usuario y por destino frente al reparto uniforme al azar
Fuente: Elaboración propia a partir de results/data/m3/eda/distribucion_actividad.json; datos generados de [@mehra2024].
![Histogramas del número de usuarios y de destinos según su número de interacciones, con la media y el intervalo de 95 % del reparto uniforme al azar](figures/m3/cola_larga.png)
:::

**Calificaciones por origen.** La [[fig:m3-calificaciones]] y la [[tab:m3-calificaciones]] muestran que las calificaciones se
reparten casi uniformemente entre 1 y 5 en los dos orígenes; la media es 3,023 en reseñas y 2,905 en historial
(`calificaciones.csv`). Si esa diferencia importa para unir los dos orígenes se prueba en H-M3-6.

::: figura m3-calificaciones
Título: Distribución de las calificaciones por origen de la interacción (reseña o historial)
Fuente: Elaboración propia a partir de results/data/m3/eda/calificaciones.csv; datos generados de [@mehra2024].
![Barras agrupadas con la proporción de cada calificación de 1 a 5 en reseñas y en historial](figures/m3/calificaciones_origen.png)
:::

::: tabla m3-calificaciones
Título: Frecuencia de cada calificación por origen de la interacción
Fuente: `results/data/m3/eda/calificaciones.csv` (columna `conteo`; media y desviación en `media_origen` y `desviacion_origen`).

| Calificación | Reseñas | Historial | Unión |
|---|---:|---:|---:|
| 1 | 198 | 206 | 404 |
| 2 | 199 | 228 | 427 |
| 3 | 185 | 201 | 386 |
| 4 | 216 | 183 | 399 |
| 5 | 201 | 181 | 382 |
| **Total** | **999** | **999** | **1 998** |
| Media (desviación) | 3,023 (1,419) | 2,905 (1,398) | 2,964 (1,409) |
:::

#### Estructura y heterogeneidad

**Cola larga y concentración en populares.** Para medir la concentración se usan tres cantidades, definidas en
`results/data/m3/eda/concentracion.json` (campo `definiciones`) y calculadas en `src/m3_recomendacion/eda.py`. Para $n$ entidades con
$x_{(1)} \le \dots \le x_{(n)}$ interacciones ordenadas de menos a más y cuotas $s_i = x_i / \sum_j x_j$:

$$
\text{Gini} = \frac{2 \sum_{i=1}^{n} i\, x_{(i)}}{n \sum_{i=1}^{n} x_{(i)}} - \frac{n+1}{n}, \qquad
\text{HHI} = \sum_{i=1}^{n} s_i^2 ,
$$

y la **cuota top** $f$ es la fracción de las interacciones que acumulan las $\lceil f\,n \rceil$ entidades con más interacciones (con
$f = 0{,}1$ y $f = 0{,}2$). El Gini es el «sin corrección» (su máximo es $(n-1)/n$) y el HHI va de $1/n$ a 1.

<!-- TODO(cita): Gini, HHI, delta de Cliff, V de Cramér con corrección de sesgo y el ajuste de Holm necesitan referencia verificada en blog/references.bib; no se citan de memoria. -->

Un reparto uniforme ya produce desigualdad por azar (unos destinos reciben 0 interacciones y otros varias). Por eso cada medida se
compara con su valor bajo el reparto uniforme simulado de las mismas 1 998 interacciones (2 000 simulaciones; la referencia es una
multinomial con probabilidad $1/n$ que no impone pares usuario–destino únicos) y no con 0 (`concentracion.json`,
`niveles.*.azar_uniforme`). Se miden a nivel de `destino_id` (1 000 entidades) y de `lugar` (5 entidades) ([[tab:m3-concentracion]]
y [[fig:m3-lorenz]]).

::: tabla m3-concentracion
Título: Concentración de las interacciones por destino y por lugar frente al reparto uniforme al azar
Fuente: `results/data/m3/eda/concentracion.json`, `niveles.<nivel>.observado` y `niveles.<nivel>.azar_uniforme` (media, `ic95` y `p_observado_mayor_o_igual`; 2 000 simulaciones). Valores redondeados a tres cifras decimales (cinco para el HHI de destinos). Para `lugar`, el 10 % y el 20 % más popular son el mismo lugar (1 de 5).

| Nivel | Medida | Observado | Azar: media | Azar: IC 95 % | p (azar ≥ observado) |
|---|---|---:|---:|---|---:|
| `destino_id` (1 000) | Gini | 0,383 | 0,386 | 0,370 a 0,401 | 0,624 |
| `destino_id` (1 000) | HHI | 0,00149 | 0,00150 | 0,00146 a 0,00154 | 0,676 |
| `destino_id` (1 000) | Cuota del 10 % más popular | 0,236 | 0,238 | 0,229 a 0,247 | 0,672 |
| `destino_id` (1 000) | Cuota del 20 % más popular | 0,406 | 0,409 | 0,396 a 0,421 | 0,679 |
| `lugar` (5) | Gini | 0,025 | 0,023 | 0,008 a 0,040 | 0,383 |
| `lugar` (5) | HHI | 0,200 | 0,200 | 0,200 a 0,201 | 0,388 |
| `lugar` (5) | Cuota del 10 % y del 20 % más popular | 0,211 | 0,212 | 0,204 a 0,223 | 0,526 |
:::

La concentración observada **no supera a la del azar**: a nivel de `destino_id` el Gini (0,383) está dentro de la banda del reparto
uniforme (media 0,386, IC 95 % de 0,370 a 0,401); lo mismo vale para el HHI (0,00149 frente a 0,00150) y para la cuota del 10 % más
popular (0,236 frente a 0,238). Los destinos populares no aparecen: 134 destinos (13,4 %) no tienen ninguna interacción y el máximo
es 7 (`concentracion.json`, `entidades_con_cero`; `distribucion_actividad.json`, `max_interacciones_observado`), igual que
esperaría un reparto uniforme (máximo medio del azar: 7,915). Por lugar, las proporciones de interacciones van de 0,188
(`jaipur_city`, 376 interacciones) a 0,211 (`leh_ladakh`, 422), con un Gini de 0,025 frente a 0,023 del azar
(`interacciones_por_lugar.csv`). Por eso la curva de Lorenz observada se confunde con la del azar en ambos niveles.

::: figura m3-lorenz
Título: Curva de Lorenz de las interacciones por destino y por lugar frente al reparto uniforme al azar
Fuente: Elaboración propia a partir de results/data/m3/eda/concentracion.json (`lorenz`, observada y del azar uniforme); datos generados de [@mehra2024].
![Curvas de Lorenz observadas y del reparto uniforme al azar, con su intervalo de 95 %, a nivel de destino y de lugar](figures/m3/lorenz.png)
:::

La región plana al inicio de la curva de Lorenz de destinos corresponde a los 134 destinos sin ninguna interacción; la curva
casi no se separa de la banda del azar.

**Usuarios con pocas interacciones.** Se llama «pocas» a **1 o 2 interacciones** y «muchas» a 3 o más; los usuarios con 0
interacciones no son un grupo evaluable y se reportan aparte (`results/data/m3/eda/actividad_usuarios.json`, `umbral`). La
justificación sale de la partición por usuario (D3): quien tiene 1 o 2 interacciones aporta a lo sumo una interacción de prueba y
ninguna de validación, y quien tiene 3 o más aporta además validación. La [[tab:m3-actividad]] da la proporción de cada grupo y la
sensibilidad al umbral.

::: tabla m3-actividad
Título: Usuarios por grupo de actividad y sensibilidad del umbral de «pocas interacciones»
Fuente: `results/data/m3/eda/actividad_usuarios.json`, `grupos`, `proporcion_pocas` y `sensibilidad_umbral`. Proporciones redondeadas a un decimal (en %).

| Grupo (umbral `pocas_max` = 2) | Usuarios | % de los 999 usuarios | Interacciones | Media de interacciones |
|---|---:|---:|---:|---:|
| Sin interacciones (0) | 141 | 14,1 | 0 | 0,00 |
| Pocas (1 a 2) | 532 | 53,3 | 812 | 1,53 |
| Muchas (3 o más) | 326 | 32,6 | 1 186 | 3,64 |

| `pocas_max` | Usuarios «pocas» | Usuarios «muchas» | % «pocas» de los 999 | % «pocas» de los 858 que aparecen |
|---|---:|---:|---:|---:|
| 1 | 252 | 606 | 25,2 | 29,4 |
| **2 (elegido)** | **532** | **326** | **53,3** | **62,0** |
| 3 | 727 | 131 | 72,8 | 84,7 |
| 4 | 806 | 52 | 80,7 | 93,9 |
:::

Con el umbral elegido, **532 usuarios (53,3 % de los 999, o 62,0 % de los 858 que aparecen en alguna interacción)** tienen pocas
interacciones (`actividad_usuarios.json`, `proporcion_pocas`). Es la mayoría: un recomendador colaborativo tendrá poca información
sobre más de la mitad de los usuarios. El umbral es una propuesta de esta tarea y debe confirmarse (la tabla muestra que, con
`pocas_max` entre 1 y 4, «pocas» va del 25,2 % al 80,7 % de los usuarios).

<!-- revisar: Juan José — el umbral «pocas = 1 o 2» está marcado como [PROPUESTO por esta tarea, a confirmar] en configs/m3/eda.yaml y en actividad_usuarios.json; confírmalo o cámbialo y regenera. -->

#### Hipótesis explícitas

Se formulan nueve hipótesis sobre qué explica las preferencias y cómo se comportarán los modelos. Las seis primeras se prueban aquí
con los datos; las tres últimas se cierran al modelar (JJ-10). Los enunciados, justificaciones y evidencias esperadas están en
`results/data/m3/eda/hipotesis.json` ([[tab:m3-hipotesis]]).

::: tabla m3-hipotesis
Título: Hipótesis de M3, justificación, evidencia esperada y dónde se ven
Fuente: `results/data/m3/eda/hipotesis.json` (campos `enunciado`, `justificacion`, `evidencia_esperada` y `figura_o_tabla`; resumidos). Los umbrales de «evidencia esperada» son convención nuestra, de `configs/m3/eda.yaml`.

| Id | Enunciado (resumido) | Justificación (resumida) | Evidencia esperada si es cierta | Figura o tabla |
|---|---|---|---|---|
| H-M3-1 | Las preferencias del usuario explican el **tipo** de destino con el que interactúa: su tasa de coincidencia supera la del azar | `Preferences` y `Type` son las variables de contenido que podrían relacionarse; el emparejamiento opción→tipo es léxico y nuestro | Tasa mayor que la línea base exacta en al menos 0,050 y p ajustado < 0,05 | [[fig:m3-preferencias-tipo]]; `matriz_preferencias_tipo.csv` |
| H-M3-2 | La calificación es mayor cuando el tipo del destino está cubierto por las preferencias | Si las preferencias reflejaran gusto, lo preferido se calificaría mejor | Delta de Cliff ≥ 0,147 y p ajustado < 0,05 | `calificaciones.csv`; `pruebas_hipotesis.json` |
| H-M3-3 | La popularidad del destino (`Popularity`) se relaciona con su número de interacciones | Es la única variable del destino que cambia entre los 1 000 ids | \|ρ de Spearman\| ≥ 0,100 y p ajustado < 0,05 | `interacciones_por_destino.csv` |
| H-M3-4 | La demografía (género, adultos, niños) se relaciona con el tipo de destino | Hipótesis de sentido común sobre quién va adónde | V de Cramér ≥ 0,100 y p ajustado < 0,05 en al menos una variable | `demografia_tipo.csv` |
| H-M3-5 | Las interacciones se concentran en pocos destinos más de lo esperado por azar | El enunciado pide la concentración en populares; se compara contra el reparto uniforme | Gini observado ≥ media del azar + 0,050, fuera de su IC 95 % | [[fig:m3-cola-larga]]; [[fig:m3-lorenz]]; [[tab:m3-concentracion]] |
| H-M3-6 | Reseñas e historial se comportan distinto (tipos y calificaciones) | La unión de D1 solo es inocua si los dos orígenes se parecen | V de Cramér ≥ 0,100 o delta de Cliff ≥ 0,147 | [[fig:m3-calificaciones]] |
| H-M3-7 | Una red con contenido no supera a la línea base de popularidad por más que la variabilidad entre semillas (NDCG@5, 30 semillas) | Con relación preferencias–tipo débil o nula, el contenido puede no aportar | Falsable: si la diferencia de medias supera la desviación entre las 30 semillas de la red, se refuta | Se cierra al modelar (JJ-10) |
| H-M3-8 | El acierto por lugar (5) es mucho mayor que por `destino_id` (1 000) en todos los modelos | Acertar el lugar es un problema de 5 clases; acertar el id, de 1 000 (D2) | Falsable: Recall@K por lugar ≤ por id en algún modelo y K refuta | Se cierra al modelar |
| H-M3-9 | Los usuarios con pocas interacciones (1 a 2) obtienen menor NDCG@5 que los de muchas (3 o más) en popularidad y en la red | Con D3 tienen una sola interacción de entrenamiento | Falsable: NDCG@5 de «pocas» ≥ el de «muchas» en algún modelo refuta | Se cierra al modelar |
:::

**Criterio de veredicto (convención nuestra, no una norma de la literatura).** Se aplica a las 10 pruebas confirmatorias de
H-M3-1 a H-M3-6, con ajuste de Holm sobre esa familia (m = 10) y $\alpha = 0{,}05$ (`pruebas_hipotesis.json`, `alfa`, `ajuste`,
`m_familia` y `familia_confirmatoria`). Una prueba **cumple** si el p ajustado es menor que $\alpha$ y el efecto alcanza el mínimo
declarado; **refuta** si el p ajustado es mayor o igual que $\alpha$ y el IC 95 % del efecto es compatible con cero y queda por
debajo del mínimo; si no, queda **indeterminada**. Una hipótesis con varias pruebas es confirmada si alguna cumple, refutada si
todas refutan y, en otro caso, no concluyente; un efecto detectable pero menor que el mínimo nunca confirma. Los efectos mínimos
(0,05 puntos de tasa, V de Cramér 0,10, delta de Cliff 0,147, ρ de Spearman 0,10 y exceso de Gini 0,05) son **convención nuestra**,
definida en `configs/m3/eda.yaml` (`efecto_minimo`) y copiada en `pruebas_hipotesis.json` (`criterio_de_veredicto`); no son umbrales
de la literatura.

Los p de H-M3-1 a H-M3-4 son por permutación entre usuarios (10 000 permutaciones, $p = (1+\#\{T^* \ge T_{obs}\})/(1+B)$); los
de H-M3-5, por simulación del reparto uniforme (2 000); los intervalos son por percentiles de 2 000 remuestreos de usuarios (o de
destinos en H-M3-3) (`pruebas_hipotesis.json`, `metodo_p`, `n_permutaciones`, `n_bootstrap`, `n_simulaciones_azar`). La [[tab:m3-pruebas]]
reúne los resultados.

::: tabla m3-pruebas
Título: Resultados de las 10 pruebas confirmatorias de H-M3-1 a H-M3-6
Fuente: `results/data/m3/eda/pruebas_hipotesis.json`, `pruebas[*]` con `familia` = confirmatoria (`estadistico`, `p_crudo`, `p_ajustado`, `efecto`); criterio por prueba de `hipotesis.json` (`resultado`). Holm sobre m = 10. Valores redondeados a tres decimales; el p ajustado de H-M3-6 (U) es 0,567.

| Prueba (`id_prueba`) | Hip. | Estadístico | p crudo | p ajustado (Holm) | Efecto (IC 95 %) | Efecto mínimo | Criterio |
|---|---|---|---:|---:|---|---:|---|
| `H1_permutacion_tasa` | H-M3-1 | tasa de coincidencia = 0,423 | 0,020 | 0,200 | tasa − línea base exacta = 0,023 (0,001 a 0,047) | 0,050 | indeterminada |
| `H2_permutacion_calificacion` | H-M3-2 | diferencia de medias = −0,042 | 0,847 | 1,000 | delta de Cliff = −0,017 (−0,066 a 0,033) | 0,147 | refuta |
| `H3_spearman_popularidad` | H-M3-3 | ρ de Spearman = −0,011 | 0,720 | 1,000 | ρ = −0,011 (−0,073 a 0,051) | 0,100 | refuta |
| `H4_genero` | H-M3-4 | χ² = 0,40 (gl 4) | 0,982 | 1,000 | V corregida = 0,000 (0,000 a 0,065) | 0,100 | refuta |
| `H4_n_adultos` | H-M3-4 | χ² = 6,60 (gl 4) | 0,164 | 1,000 | V corregida = 0,036 (0,000 a 0,101) | 0,100 | indeterminada |
| `H4_n_ninos` | H-M3-4 | χ² = 10,55 (gl 8) | 0,239 | 1,000 | V corregida = 0,025 (0,000 a 0,082) | 0,100 | refuta |
| `H5_gini_destino_id` | H-M3-5 | Gini = 0,383 | 0,624 | 1,000 | Gini − media del azar = −0,002 (−0,018 a 0,014) | 0,050 | refuta |
| `H5_gini_lugar` | H-M3-5 | Gini = 0,025 | 0,383 | 1,000 | Gini − media del azar = 0,002 (−0,015 a 0,017) | 0,050 | refuta |
| `H6_chi2_origen_tipo` | H-M3-6 | χ² = 1,05 (gl 4) | 0,902 | 1,000 | V corregida = 0,000 (0,000 a 0,069) | 0,100 | refuta |
| `H6_mann_whitney_calificacion` | H-M3-6 | U = 522 489 | 0,063 | 0,567 | delta de Cliff = 0,047 (−0,005 a 0,098) | 0,147 | refuta |
:::

**H-M3-1, preferencias y tipo de destino.** La [[fig:m3-preferencias-tipo]] muestra, para cada combinación de preferencias, la
proporción de interacciones con cada tipo de destino y recuadra los tipos cubiertos por esas preferencias. Como la fuente no
documenta la correspondencia entre las opciones de `Preferences` y los valores de `Type`, se empareja por nombre (Beaches→Beach,
Historical→Historical, City→City, Adventure→Adventure, Nature→Nature): es un **emparejamiento léxico nuestro** y, con otro, cambian
las conclusiones de H-M3-1 y H-M3-2 (`configs/m3/eda.yaml`, `emparejamiento_preferencia_tipo`).

::: figura m3-preferencias-tipo
Título: Tipo de destino de las interacciones por combinación de preferencias del usuario
Fuente: Elaboración propia a partir de results/data/m3/eda/matriz_preferencias_tipo.csv y coincidencia_preferencias.json; datos generados de [@mehra2024]. Emparejamiento preferencia–tipo léxico, nuestro.
![Mapa de calor con la proporción de interacciones de cada tipo de destino por combinación de preferencias, con recuadro en los tipos cubiertos](figures/m3/preferencias_tipo.png)
:::

La **tasa de coincidencia observada es 0,423** (846 de 1 998 interacciones), frente a una **línea base de azar exacta de 0,400**
(la fracción del catálogo cuyo tipo está en las preferencias, dado que hay 200 ids de cada uno de los 5 tipos) y de 0,401 con la
distribución marginal observada de tipos. La diferencia es 0,023 (IC 95 % de 0,001 a 0,047) con la línea exacta y 0,022 (de −0,001
a 0,045) con la marginal; bajo permutación, la tasa media es 0,401 (IC 95 % de 0,380 a 0,422)
(`coincidencia_preferencias.json`, `global` y `nulo_permutacion`). El p crudo de la permutación es 0,020, pero el p ajustado por
Holm es 0,200 y el efecto (0,023) está por debajo del mínimo declarado (0,050): la prueba es indeterminada y la hipótesis queda
**no concluyente**.

Por combinación la tasa varía: 0,454 en «Adventure, Nature» (n = 659), 0,430 en «Beaches, Historical» (n = 684) y 0,386 en «City,
Historical» (n = 655), frente a 0,400 en cada una (`coincidencia_preferencias.json`, `por_combinacion`). La prueba complementaria
de independencia combinación × tipo da χ² = 18,35 (gl 8, p asintótico 0,019, sin ajustar y fuera de la familia de Holm) y una V de Cramér
corregida por sesgo de 0,051 (IC 95 % de 0,029 a 0,099, sin corregir 0,068) (`pruebas_hipotesis.json`, `C_H1_chi2_combinacion_tipo`):
hay una asociación débil, por debajo del mínimo 0,10, y esa prueba supone independencia entre interacciones, que no se cumple del
todo porque cada usuario aporta varias.

<!-- revisar: Juan José — «no concluyente» para H-M3-1 es el veredicto que sale de nuestro criterio; el emparejamiento léxico preferencia→tipo, el mínimo 0,050 y la lectura de que la asociación es «débil» son decisiones/interpretación nuestras. -->

**H-M3-2 a H-M3-6.** La calificación media cuando el tipo coincide con las preferencias es 2,940 (n = 846) y 2,982 cuando no
coincide (n = 1 152); la diferencia es −0,042 (IC 95 % de −0,164 a 0,082) y el delta de Cliff −0,017: H-M3-2 se refuta (efecto
compatible con cero, IC por debajo de 0,147). La popularidad de la fuente no acompaña a la demanda: ρ de Spearman = −0,011 (IC 95 % de
−0,073 a 0,051) con 134 de 1 000 destinos sin interacciones, por lo que hay muchos empates (rangos medios) (H-M3-3 refutada). La
demografía no se asocia con el tipo de destino: las V corregidas de género, número de adultos y número de niños son 0,000, 0,036 y
0,025, aunque el IC de los adultos (0,000 a 0,101) no excluye por completo un efecto de 0,10, y por eso H-M3-4 queda no concluyente
(`pruebas_hipotesis.json`, `H4_*`; `demografia_tipo.csv`). La concentración no supera al azar (H-M3-5 refutada, [[tab:m3-concentracion]]).
Reseñas e historial se parecen en el tipo de destino (V corregida 0,000, IC 95 % de 0,000 a 0,069) y en la calificación (delta de
Cliff 0,047, IC 95 % de −0,005 a 0,098; p ajustado 0,567) (H-M3-6 refutada): la unión de D1 no parece ocultar dos comportamientos
distintos. Todo esto vale para estos datos generados (D4), no para turistas reales.

#### Implicaciones para el modelado

**(a) Partición por usuario (D3).** No se parte por tiempo porque `VisitDate` no es una fecha real. La regla es: prueba = 1
interacción al azar de cada usuario con 2 o más; validación = 1 más de cada usuario con 3 o más; el resto, entrenamiento (los
usuarios con 1 interacción quedan solo en entrenamiento). Contando esa regla sobre los datos (la partición real, con semilla y
pruebas de fuga, es de JJ-3) salen **1 066 interacciones de entrenamiento, 326 de validación y 606 de prueba**
(`results/data/m3/eda/actividad_usuarios.json`, `particion_d3.total`). Por grupo ([[tab:m3-particion]]), los usuarios con
«pocas» interacciones aportan 532 interacciones de entrenamiento, ninguna de validación y 280 de prueba; los de «muchas», 534, 326 y 326. Es decir,
**el grupo «pocas» sí existe en prueba** (280 usuarios), pero **la validación solo contiene usuarios de «muchas»**, y los 252
usuarios con una sola interacción nunca se evalúan.

::: tabla m3-particion
Título: Interacciones por partición y grupo de actividad con la regla D3 (conteo, no la partición final)
Fuente: `results/data/m3/eda/actividad_usuarios.json`, `particion_d3` (`interacciones`, `usuarios_con_prueba`, `usuarios_con_validacion`, `usuarios_solo_entrenamiento`, `total`). La partición real la hace JJ-3.

| Grupo | Entrenamiento | Validación | Prueba | Usuarios con prueba | Usuarios solo en entrenamiento |
|---|---:|---:|---:|---:|---:|
| Pocas (1 a 2) | 532 | 0 | 280 | 280 | 252 |
| Muchas (3 o más) | 534 | 326 | 326 | 326 | 0 |
| **Total** | **1 066** | **326** | **606** | 606 | 252 |
:::

**(b) Negativos: uniformes frente a por popularidad.** Un muestreo de negativos por popularidad tiene sentido si unos pocos destinos
concentran las interacciones: así los negativos «difíciles» son los populares que el usuario no tocó. Aquí la concentración **no supera
a la del azar**: Gini 0,383 frente a 0,386 y cuota del 10 % más popular 0,236 frente a 0,238 a nivel de `destino_id`
([[tab:m3-concentracion]]), y la popularidad de la fuente tiene ρ = −0,011 con las interacciones. Por lo tanto, muestrear negativos
por popularidad (sea por conteo de entrenamiento o por `Popularity`) aporta poco frente a hacerlo de forma uniforme: la «popularidad» que
un modelo estimaría con 1 066 interacciones de entrenamiento sería sobre todo ruido de muestreo. La elección debe justificarse con
esta medida y no con la intuición de que los datos de consumo suelen ser de cola larga.

<!-- revisar: Juan José — la conclusión «aporta poco» sale de la medición (concentración igual al azar); la decisión final de negativos y su justificación son de JJ-5. -->

**(c) Variables de contenido disponibles (D2).** Del destino: `tipo`, `estado`, `mejor_epoca`, `popularidad` y `lugar`. Del usuario:
`preferencias` (3 combinaciones, 333 usuarios cada una; `coincidencia_preferencias.json`, `por_combinacion`) y demografía (`genero`,
`n_adultos`, `n_ninos`). Como los 1 000 ids son 5 lugares, `tipo`, `estado` y `mejor_epoca` son constantes por lugar y no agregan información
frente a `lugar`; solo `popularidad` varía entre ids. Qué mostraron las hipótesis sobre su poder explicativo: las preferencias
apenas elevan la coincidencia con el tipo (0,423 frente a 0,400; no concluyente, efecto 0,023 por debajo de 0,050); la demografía no se
asocia con el tipo (V corregida de 0,000 a 0,036; no concluyente por el IC de los adultos); la popularidad no se relaciona con las
interacciones (ρ = −0,011; refutada). Con esa evidencia el contenido tiene, en estos datos, un poder explicativo bajo; no es motivo para
omitirlo (el enunciado exige al menos una variable de contenido), pero sí para no esperar de él una mejora grande.

**(d) Los 1 000 ids son 5 lugares.** Un modelo que aprenda un parámetro por `destino_id` no puede distinguir dos ids del mismo lugar
más que por su `popularidad` (que no se relaciona con las interacciones, H-M3-3) y por el propio id. De ahí el **acierto por lugar**
(5 clases, D2) como evaluación complementaria al acierto por `destino_id` (1 000 clases): el primero responde si el modelo acierta el tipo de
destino que le interesa al usuario, el segundo, si acierta el id exacto. Las interacciones se reparten casi por igual entre los 5
lugares (de 376 a 422; `interacciones_por_lugar.csv`). H-M3-8 se cierra al modelar.

**(e) Qué esperar si los datos no tienen patrón.** Si los datos se generaron sin estructura que un modelo pueda aprender (D4;
concentración igual al azar, popularidad sin relación con las interacciones, preferencias con efecto pequeño), lo esperable es que
las métricas de **todos** los modelos queden cerca de las de un recomendador al azar y que las **diferencias entre modelos sean menores que la variabilidad entre
semillas**. Por eso importan las 30 semillas y reportar media y desviación (núcleo §6), y por eso H-M3-7 se formula como
falsable contra esa desviación. Una diferencia pequeña entre la red y la popularidad no debería leerse como superioridad de ningún modelo.

#### Veredicto de las hipótesis

Los veredictos de H-M3-1 a H-M3-6 salen del criterio declarado arriba (convención nuestra) y de las 10 pruebas confirmatorias con ajuste
de Holm; los de H-M3-7 a H-M3-9 están **pendientes** y se cierran en JJ-10, cuando existan las métricas de los modelos (`hipotesis.json`,
campo `veredicto`).

::: tabla m3-veredictos
Título: Veredicto de las hipótesis de M3
Fuente: `results/data/m3/eda/hipotesis.json` (campos `enunciado` y `veredicto`; enunciados resumidos) y `pruebas_hipotesis.json` para la evidencia. El criterio es convención nuestra (`configs/m3/eda.yaml`).

| Id | Enunciado (corto) | Veredicto | Evidencia |
|---|---|---|---|
| H-M3-1 | Las preferencias explican el tipo de destino | no concluyente | Tasa 0,423 frente a 0,400; efecto 0,023 (IC 95 % 0,001 a 0,047), p ajustado 0,200 |
| H-M3-2 | Mayor calificación si el tipo está cubierto por las preferencias | refutada | Delta de Cliff −0,017 (IC 95 % −0,066 a 0,033); p ajustado 1,000 |
| H-M3-3 | La popularidad se relaciona con las interacciones | refutada | ρ = −0,011 (IC 95 % −0,073 a 0,051); p ajustado 1,000 |
| H-M3-4 | La demografía se relaciona con el tipo de destino | no concluyente | V corregida 0,000, 0,036 y 0,025; el IC de adultos llega a 0,101 |
| H-M3-5 | Concentración mayor que la del azar | refutada | Gini 0,383 frente a 0,386 del azar (IC 95 % 0,370 a 0,401) |
| H-M3-6 | Reseñas e historial se comportan distinto | refutada | V corregida 0,000 (hasta 0,069); delta de Cliff 0,047 (−0,005 a 0,098) |
| H-M3-7 | La red con contenido no supera a la popularidad más que la variabilidad entre semillas | pendiente | Se cierra en JJ-10 (`results/data/m3/summary.json` aún no existe) |
| H-M3-8 | El acierto por lugar es mucho mayor que por `destino_id` | pendiente | Se cierra en JJ-10 |
| H-M3-9 | «Pocas» interacciones obtienen menor NDCG@5 que «muchas» | pendiente | Se cierra en JJ-10 |
:::

Lectura de conjunto ([[tab:m3-veredictos]]): de las seis hipótesis que se pueden cerrar con los datos, cuatro quedan refutadas y dos
no concluyentes; **ninguna se confirma**. En estos datos generados, ni las preferencias, ni la demografía, ni la popularidad ni la
concentración explican de forma apreciable con quién interactúa un usuario. «Refutada» significa aquí, por nuestro criterio, que el
efecto es compatible con cero y que se excluye un efecto del tamaño mínimo declarado, no que se haya demostrado que no existe en
absoluto.

<!-- revisar: Juan José — la «lectura de conjunto» y la frase de que «ningún factor explica de forma apreciable» son interpretación del redactor sobre los veredictos de hipotesis.json; valida el tono y el alcance (son datos generados, D4). -->

\bibliografia
