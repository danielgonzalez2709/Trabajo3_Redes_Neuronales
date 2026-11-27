## M3 — Recomendación de destinos

<!-- JJ-2 y JJ-3 (redactor-tecnico, Sonnet) para Juan José. Toda cifra sale de results/data/m3/eda/ o de results/data/m3/particion/resumen.json (ruta entre paréntesis o en la fuente de cada tabla/figura). Las subsecciones «Implicaciones» y «Veredicto» son parciales hasta JJ-5/JJ-6/JJ-10. -->

**Caso de uso.** La empresa lanza una línea de turismo internacional con destinos en India. La recomendación se muestra en la
aplicación web de la empresa, en la sección de esa línea, cuando el cliente entra a explorar viajes; opcionalmente podría
repetirse en un correo de campaña. Se muestran **K = 5 destinos por defecto** (`k_defecto` = 5 y `k_max` = 10 en el contrato de la
aplicación, `app/public/model/m3/perfil_nuevo.json`; núcleo §5.8) y las métricas se evalúan para K ∈ {1, 3, 5, 10}. Al momento de
recomendar se dispone del historial de interacciones previas del cliente (visitas y reseñas), de las preferencias que declara al
registrarse y de datos demográficos básicos (género, número de adultos y número de niños). No se usan el nombre ni el correo
(decisión D6, `docs/spec/partes/juanjose.md` §3.1). Un cliente nuevo solo tiene sus preferencias.

<!-- revisar: Juan José — el canal (app web, correo opcional) y el momento («cuando explora viajes») son descripción nuestra del caso de uso; el Spec solo fija K por defecto (§5.8) y K ∈ {1, 3, 5, 10} es [PROPUESTO] en tu spec §3.3. También son diseño nuestro, no del Spec, que los datos demográficos (género, adultos, niños) estén disponibles al recomendar y el correo de campaña: §5.8 solo pone `preferencias` en el perfil nuevo. Además, `perfil_nuevo.json` es hoy un JUGUETE con opciones de preferencia que no existen en el conjunto real (p. ej. «gastronomía», «montaña»): la lista real son las 5 opciones de Preferences. -->

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
using this dataset in your projects.» (`ficha.json`, `licencia`). Las declaraciones son distintas entre sí. Aquí se cita la fuente, como pide
la sección «Usage» de la descripción, y la contradicción queda documentada para la sección de ética (decisión D5).

<!-- revisar: Juan José — se evitó a propósito afirmar que «las tres licencias piden citar la fuente» (candidato de cacería JJ-1b en docs/MEMORIA.md): solo la sección «Usage» lo pide en su cita literal. -->

#### Diccionario y calidad

**La fuente no documenta ninguna columna**: la revisión de los metadatos de Kaggle (`datasetFiles[].columns` e `info.description`)
encontró 0 columnas documentadas y solo una descripción narrativa de cada componente (`results/data/m3/eda/diccionario.json`,
campos `fuente_del_diccionario` y `columnas_documentadas_por_la_fuente`). Por eso el significado de **cada** variable aparece en el
diccionario como «no documentado por la fuente», y la correspondencia entre archivos y componentes de la descripción es inferencia
nuestra (`diccionario.json`, `variables[*].nota_correspondencia`). La [[tab:m3-diccionario]] lista las variables y el nombre con
que pasan a los archivos procesados.

::: tabla m3-diccionario
Título: Variables de M3, con su nombre procesado (el significado no está documentado por la fuente)
Fuente: `results/data/m3/eda/diccionario.json`, campo `variables` (`columna_original`, `nombre_procesado`, `tipo`, `columnas_derivadas`, `excluida_motivo`). Los conteos de valores distintos salen de `results/data/m3/eda/ficha.json`, `conteos.variables_de_contenido` (`n_categorias`) y de `calidad.csv` (`unicos`).

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
Todas las barras de los dos histogramas caen dentro del IC 95 % del reparto al azar (`distribucion_actividad.json`, `azar_ic95`); véase «Estructura y heterogeneidad».

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
$f = 0{,}1$ y $f = 0{,}2$). Este Gini no está reescalado (su máximo es $(n-1)/n$; el archivo también trae `gini_reescalado` = $G\,n/(n-1)$ en [0, 1], que **no** es una
corrección de sesgo y no se usa en las tablas) y el HHI va de $1/n$ a 1.


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
popular (0,236 frente a 0,238). Los destinos populares no aparecen: 134 de 1 000 destinos no tienen ninguna interacción y el máximo
es 7 (`concentracion.json`, `entidades_con_cero`; `distribucion_actividad.json`, `max_interacciones_observado`), compatible
con un reparto uniforme (máximo medio del azar: 7,915; `distribucion_actividad.json`, `destinos.max_interacciones_azar_media`).
Por lugar, las proporciones de interacciones van de 0,188 (`jaipur_city`, 376 interacciones) a 0,211 (`leh_ladakh`, 422)
(`interacciones_por_lugar.csv`), con un Gini de 0,025 frente a 0,023 del azar (`concentracion.json`,
`niveles.lugar.observado.gini` y `niveles.lugar.azar_uniforme.gini.media`). Por eso la curva de Lorenz observada se confunde con la del azar en ambos niveles. La banda gris de [[fig:m3-lorenz]] es el IC 95 %
**puntual** (calculado vértice a vértice sobre las 2 000 simulaciones), no una banda simultánea para toda la curva.

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
| H-M3-3 | La popularidad del destino (`Popularity`) se relaciona con su número de interacciones | Es la única variable del destino que cambia entre los 1 000 ids | ρ de Spearman en valor absoluto ≥ 0,100 y p ajustado < 0,05 | `interacciones_por_destino.csv` |
| H-M3-4 | La demografía (género, adultos, niños) se relaciona con el tipo de destino | Hipótesis de sentido común sobre quién va adónde | V de Cramér ≥ 0,100 y p ajustado < 0,05 en al menos una variable | `demografia_tipo.csv` |
| H-M3-5 | Las interacciones se concentran en pocos destinos más de lo esperado por azar, a nivel `destino_id` o `lugar` | El enunciado pide la concentración en populares; se compara contra el reparto uniforme | Gini observado ≥ media del azar + 0,050, fuera de su IC 95 % | [[fig:m3-cola-larga]]; [[fig:m3-lorenz]]; [[tab:m3-concentracion]] |
| H-M3-6 | Reseñas e historial se comportan distinto: difieren en los tipos de destino o en la distribución de las calificaciones | La unión de D1 solo es inocua si los dos orígenes se parecen | V de Cramér ≥ 0,100 o delta de Cliff ≥ 0,147 | [[fig:m3-calificaciones]] |
| H-M3-7 | Una red con contenido no supera a la línea base de popularidad por más que la variabilidad entre semillas (NDCG@5, 30 semillas) | Con relación preferencias–tipo débil o nula, el contenido puede no aportar | Falsable: si la diferencia de medias supera la desviación entre las 30 semillas de la red, se refuta | Se cierra al modelar (JJ-10) |
| H-M3-8 | El acierto por lugar (5) es mucho mayor que por `destino_id` (1 000) en todos los modelos | Acertar el lugar es un problema de 5 clases; acertar el id, de 1 000 (D2) | Falsable: Recall@K por lugar ≤ por id en algún modelo y K refuta | Se cierra al modelar |
| H-M3-9 | Los usuarios con pocas interacciones (1 a 2) obtienen menor NDCG@5 que los de muchas (3 o más) en popularidad y en la red | Con D3 tienen una sola interacción de entrenamiento | Falsable: NDCG@5 de «pocas» ≥ el de «muchas» en algún modelo refuta | Se cierra al modelar |
:::

**Criterio de veredicto (convención nuestra).** Se aplica a las 10 pruebas confirmatorias de
H-M3-1 a H-M3-6, con ajuste de Holm sobre esa familia (m = 10) y $\alpha = 0{,}05$ (`pruebas_hipotesis.json`, `alfa`, `ajuste`,
`m_familia` y `familia_confirmatoria`). Una prueba **cumple** si el p ajustado es menor que $\alpha$ y el efecto alcanza el mínimo
declarado; **refuta** si el p ajustado es mayor o igual que $\alpha$ y el IC 95 % del efecto contiene el 0 y queda por completo
dentro de (−mínimo, +mínimo) (en las pruebas «mayor», empieza en 0 o antes y termina por debajo del mínimo); en cualquier otro
caso, p. ej. un efecto detectable pero menor que el mínimo, queda **indeterminada** (`criterio_de_veredicto.regla`). Una hipótesis
con varias pruebas es confirmada si alguna cumple, refutada si todas refutan y, en otro caso, no concluyente; un efecto detectable
pero menor que el mínimo nunca confirma. Los efectos mínimos (0,05 de diferencia de tasa, V de Cramér 0,10, delta de Cliff 0,147,
ρ de Spearman 0,10 y exceso de Gini 0,05) son una **convención nuestra** declarada en `configs/m3/eda.yaml` (`efecto_minimo`) y
copiada en `pruebas_hipotesis.json` (`criterio_de_veredicto`). La marca `efecto.en_el_limite` indica que un límite del IC 95 % está
a menos de 0,005 del mínimo (`tolerancia_limite`): con esa cercanía el veredicto depende del ruido de Monte Carlo y no debe leerse
como hallazgo; no mueve ningún veredicto.

<!-- TODO(cita): el 0,147 de δ de Cliff se atribuye a Romano et al. (2006); verificar la fuente primaria en JJ-9 -->
<!-- TODO(cita): Bergsma (2013), doi 10.1016/j.jkss.2012.10.002 — verificar en JJ-9 (V de Cramér con corrección de sesgo) -->
<!-- TODO(cita): Gini, HHI y el ajuste de Holm necesitan referencia verificada en blog/references.bib; no se citan de memoria. -->
<!-- revisar: Juan José — confirma que los efectos mínimos (0,05; 0,10; 0,147; 0,10; 0,05) son los que quieres declarar como convención nuestra. -->

En la [[tab:m3-pruebas]], `H1_permutacion_tasa` y `H4_n_adultos` llevan `en_el_limite` = true.

El método del p depende de la prueba (`pruebas_hipotesis.json`, `metodo_p`, `n_permutaciones`, `n_bootstrap`, `n_simulaciones_azar`):

- **H-M3-1, H-M3-2 y H-M3-4:** permutación de la variable del usuario **entre usuarios** (10 000 permutaciones,
  $p = (1+\#\{T^* \ge T_{obs}\})/(1+B)$), lo que respeta que un usuario aporta varias interacciones.
- **H-M3-3:** permutación de la popularidad **entre destinos** (10 000 permutaciones).
- **H-M3-5:** simulación del reparto uniforme de las mismas interacciones (2 000 simulaciones).
- **H-M3-6:** p **asintóticos** (χ² y Mann–Whitney con corrección por empates), que suponen independencia entre interacciones aunque
  una misma persona puede aparecer en reseñas y en historial (la unión de usuarios que aparecen, 858, es menor que la suma de los
  de cada origen, 624 y 642; `ficha.json`, `conteos.usuarios_que_aparecen`).

Los **IC 95 %** son por percentiles de 2 000 remuestreos de usuarios (por destinos en H-M3-3), con una excepción: en H-M3-5 son
«observado menos los percentiles de las 2 000 simulaciones», una inversión aproximada bajo un modelo de desplazamiento (el azar
solo corre la distribución), **no un bootstrap**. La [[tab:m3-pruebas]] reúne los resultados.

::: tabla m3-pruebas
Título: Resultados de las 10 pruebas confirmatorias de H-M3-1 a H-M3-6
Fuente: `results/data/m3/eda/pruebas_hipotesis.json`, `pruebas[*]` con `familia` = confirmatoria (`estadistico`, `p_crudo`, `p_ajustado`, `efecto`); criterio por prueba de `hipotesis.json` (`resultado`). Holm sobre m = 10. p y efectos redondeados a tres decimales; χ² a dos; U entero. Los IC de H-M3-5 son «observado menos percentiles de la simulación» (inversión aproximada, no bootstrap); los p de H-M3-6 son asintóticos. Marca `en_el_limite` = true en `H1_permutacion_tasa` y `H4_n_adultos`.

| Prueba (`id_prueba`) | Hip. | Estadístico | p crudo | p ajustado (Holm) | Efecto (IC 95 %) | Efecto mínimo | Criterio |
|---|---|---|---:|---:|---|---:|---|
| `H1_permutacion_tasa` | H-M3-1 | tasa de coincidencia = 0,423 | 0,020 | 0,200 | tasa − línea base exacta = 0,023 (0,001 a 0,047) | 0,050 | indeterminada (en el límite) |
| `H2_permutacion_calificacion` | H-M3-2 | diferencia de medias = −0,042 | 0,847 | 1,000 | delta de Cliff = −0,017 (−0,066 a 0,033) | 0,147 | refuta |
| `H3_spearman_popularidad` | H-M3-3 | ρ de Spearman = −0,011 | 0,720 | 1,000 | ρ = −0,011 (−0,073 a 0,051) | 0,100 | refuta |
| `H4_genero` | H-M3-4 | χ² = 0,40 (gl 4) | 0,982 | 1,000 | V corregida = 0,000 (0,000 a 0,065) | 0,100 | refuta |
| `H4_n_adultos` | H-M3-4 | χ² = 6,60 (gl 4) | 0,164 | 1,000 | V corregida = 0,036 (0,000 a 0,101) | 0,100 | indeterminada (en el límite) |
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
(`coincidencia_preferencias.json`, `global` y `nulo_permutacion`). El efecto es pequeño: unos 2,3 puntos porcentuales, menos que el
mínimo declarado de 5,0. El p crudo de la permutación es 0,020 y el p ajustado por Holm (m = 10) es 0,200. El IC 95 % sin ajustar
(0,001 a 0,047) excluye el 0 y excluye un efecto de 0,050 o más; pero el IC ajustado por multiplicidad, de nivel 99,5 %
($1-\alpha/m$ con m = 10, mismos remuestreos de usuarios), va de −0,010 a 0,058: **incluye el 0 y también incluye el mínimo 0,050**
(`coincidencia_preferencias.json`, `global.diferencia_exacta_ic_ajustado`; `pruebas_hipotesis.json`, `efecto.ic_ajustado`). Con
estos datos no se puede ni afirmar que las preferencias expliquen el tipo ni descartar un efecto del tamaño mínimo: la prueba es
indeterminada y la hipótesis queda **no concluyente**. Además, el resultado está marcado «en el límite» (`efecto.en_el_limite` =
true): el extremo que decide es el inferior del IC 95 % (0,0006), pegado al 0 —si fuera 0 o menos, la prueba refutaría—, y además
el superior (0,0469) está a menos de 0,005 del mínimo (`hipotesis.json`, `resultado` de H-M3-1). El veredicto depende del ruido de
Monte Carlo y no debe leerse como hallazgo.

Por combinación la tasa varía: 0,454 en «Adventure, Nature» (n = 659), 0,430 en «Beaches, Historical» (n = 684) y 0,386 en «City,
Historical» (n = 655), frente a 0,400 en cada una (`coincidencia_preferencias.json`, `por_combinacion`). La prueba complementaria
de independencia combinación × tipo da χ² = 18,35 (gl 8, p asintótico 0,019, sin ajustar y fuera de la familia de Holm) y una V de Cramér
corregida por sesgo de 0,051 (IC 95 % de 0,029 a 0,099, sin corregir 0,068) (`pruebas_hipotesis.json`, `C_H1_chi2_combinacion_tipo`):
es un **indicio de asociación débil** (p sin ajustar, prueba fuera de la familia de Holm, V por debajo del mínimo 0,10), y esa prueba
supone independencia entre interacciones, que no se cumple del todo porque cada usuario aporta varias. Además, en su mayor parte
**no está en las celdas que coinciden con las preferencias**: las 6 celdas coincidentes aportan 5,70 del χ² de 18,35 y las 9 no
coincidentes, 12,65. El residuo máximo en valor absoluto es −3,73 en «Beaches, Historical» × Nature (residuo estandarizado
ajustado; el de Pearson de esa celda es −2,70), es decir, hay menos interacciones con Nature de las esperadas para quien declara
playa e historia, y Nature no está cubierto por esas preferencias (`coincidencia_preferencias.json`, `chi2_combinacion_tipo`:
`aporte`, `residuo_maximo_absoluto`, `residuos_estandarizados`, `residuos_de_pearson`).

<!-- revisar: Juan José — «no concluyente» para H-M3-1 es el veredicto que sale de nuestro criterio; el emparejamiento léxico preferencia→tipo, el mínimo 0,050 y la lectura de que la asociación es «débil» y no está en las celdas coincidentes son decisiones/interpretación nuestras. -->

**H-M3-2 a H-M3-6.** La calificación media cuando el tipo coincide con las preferencias es 2,940 (n = 846) y 2,982 cuando no
coincide (n = 1 152); la diferencia es −0,042 (IC 95 % de −0,164 a 0,082) y el delta de Cliff −0,017: H-M3-2 se refuta (efecto
compatible con cero, IC por debajo de 0,147). La popularidad de la fuente no acompaña a la demanda: ρ de Spearman = −0,011 (IC 95 % de
−0,073 a 0,051) con 134 de 1 000 destinos sin interacciones, por lo que hay muchos empates (rangos medios) (H-M3-3 refutada). La
demografía: **no se detectó asociación** con el tipo de destino. Las V corregidas de género, número de adultos y número de niños son
0,000, 0,036 y 0,025; los IC excluyen V ≥ 0,10 para género (0,000 a 0,065) y niños (0,000 a 0,082), pero no para adultos (0,000 a
0,101), y por eso H-M3-4 queda no concluyente. El resultado de `n_adultos` está en el límite del criterio (`en_el_limite` = true,
tolerancia 0,005) y no debe leerse como hallazgo (`pruebas_hipotesis.json`, `H4_*`; `demografia_tipo.csv`). La concentración no
supera al azar (H-M3-5 refutada, [[tab:m3-concentracion]]). Reseñas e historial **no difieren en más que un efecto pequeño**
(|δ| < 0,147 y V corregida < 0,10): en el tipo de destino la V corregida es 0,000 (IC 95 % de 0,000 a 0,069) y en la calificación
el delta de Cliff es 0,047 (IC 95 % de −0,005 a 0,098; p ajustado 0,567) (H-M3-6 refutada). El δ mide un desplazamiento de las
calificaciones; la prueba complementaria sobre toda su distribución (χ² origen × calificación, fuera de la familia) da una
V corregida de 0,036 con IC 95 % de 0,000 a 0,102, que no excluye un efecto de 0,10 (`pruebas_hipotesis.json`,
`C_H6_chi2_origen_calificacion`). El IC de δ se obtiene remuestreando
usuarios, así que tiene en cuenta que un mismo usuario puede aportar interacciones en los dos orígenes; los p asintóticos (χ² y
Mann–Whitney) no lo hacen. Esto indica que la unión de D1 no oculta, en estos datos, una diferencia grande entre orígenes, pero no que sean
idénticos. Todo esto vale para estos datos generados (D4), no para turistas reales.

#### Implicaciones para el modelado

**(a) Partición por usuario (D3).** No se parte por tiempo porque `VisitDate` no es una fecha real. La regla es: prueba = 1
interacción al azar de cada usuario con 2 o más; validación = 1 más de cada usuario con 3 o más; el resto, entrenamiento (los
usuarios con 1 interacción quedan solo en entrenamiento). Contar esa regla sobre los datos da **1 066 interacciones de
entrenamiento, 326 de validación y 606 de prueba**, y esas cifras, también por grupo de actividad, **coinciden** con las de la
partición final construida con semilla y pruebas de fuga (véase la subsección «Partición» y la [[tab:m3-particion-final]], cuya
fuente incluye esa comprobación). Lo que importa para el modelado es que **el grupo «pocas» sí existe en
prueba** (280 usuarios), que **la validación solo contiene usuarios de «muchas»** y que los 252 usuarios con una sola interacción
nunca se evalúan.

**(b) Negativos: uniformes frente a por popularidad.** Un muestreo de negativos por popularidad tiene sentido si unos pocos destinos
concentran las interacciones: así los negativos «difíciles» son los populares que el usuario no tocó. Aquí la concentración **no supera
a la del azar**: Gini 0,383 frente a 0,386 y cuota del 10 % más popular 0,236 frente a 0,238 a nivel de `destino_id`
([[tab:m3-concentracion]]), y la popularidad de la fuente tiene ρ = −0,011 con las interacciones. Por lo tanto, muestrear negativos
por popularidad (sea por conteo de entrenamiento o por `Popularity`) es de esperar que aporte poco frente a hacerlo de forma uniforme: la «popularidad» que
un modelo estimaría con 1 066 interacciones de entrenamiento sería sobre todo ruido de muestreo. La elección debe justificarse con
esta medida y no con la intuición de que los datos de consumo suelen ser de cola larga.

<!-- revisar: Juan José — la conclusión «aporta poco» sale de la medición (concentración igual al azar); la decisión final de negativos y su justificación son de JJ-5. -->

**(c) Variables de contenido disponibles (D2).** Del destino: `tipo`, `estado`, `mejor_epoca`, `popularidad` y `lugar`. Del usuario:
`preferencias` (3 combinaciones, 333 usuarios cada una; `coincidencia_preferencias.json`, `por_combinacion`) y demografía (`genero`,
`n_adultos`, `n_ninos`). Como los 1 000 ids son 5 lugares, `tipo`, `estado` y `mejor_epoca` son constantes por lugar y no agregan información
frente a `lugar`; solo `popularidad` varía entre ids. Qué mostraron las hipótesis sobre su poder explicativo: las preferencias
apenas elevan la coincidencia con el tipo (0,423 frente a 0,400; no concluyente, efecto 0,023 por debajo de 0,050); en la demografía no se
detectó asociación con el tipo (V corregida de 0,000 a 0,036; no concluyente, porque el IC de los adultos no excluye V ≥ 0,10); la
popularidad no mostró relación con las interacciones (ρ = −0,011, IC 95 % de −0,073 a 0,051; refutada). Con esa evidencia el contenido tiene, en estos datos, un poder explicativo bajo; no es motivo para
omitirlo (el enunciado exige al menos una variable de contenido), pero sí para no esperar de él una mejora grande.

**(d) Los 1 000 ids son 5 lugares.** Un modelo que aprenda un parámetro por `destino_id` no puede distinguir dos ids del mismo lugar
más que por su `popularidad` (que no se relaciona con las interacciones, H-M3-3) y por el propio id. De ahí el **acierto por lugar**
(5 clases, D2) como evaluación complementaria al acierto por `destino_id` (1 000 clases): el primero responde si el modelo acierta el tipo de
destino que le interesa al usuario, el segundo, si acierta el id exacto. Las interacciones se reparten casi por igual entre los 5
lugares (de 376 a 422; `interacciones_por_lugar.csv`). H-M3-8 se cierra al modelar.

**(e) Qué esperar si los datos no tienen patrón.** Si los datos se generaron sin estructura que un modelo pueda aprender (D4;
concentración igual a la del azar, popularidad sin relación detectada con las interacciones, preferencias con efecto pequeño), lo esperable es que
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
| H-M3-1 | Las preferencias explican el tipo de destino | no concluyente | Tasa 0,423 frente a 0,400; efecto 0,023 (IC 95 % 0,001 a 0,047; IC ajustado −0,010 a 0,058), p ajustado 0,200; en el límite |
| H-M3-2 | Mayor calificación si el tipo está cubierto por las preferencias | refutada | Delta de Cliff −0,017 (IC 95 % −0,066 a 0,033); p ajustado 1,000 |
| H-M3-3 | La popularidad se relaciona con las interacciones | refutada | ρ = −0,011 (IC 95 % −0,073 a 0,051); p ajustado 1,000 |
| H-M3-4 | La demografía se relaciona con el tipo de destino | no concluyente | V corregida 0,000, 0,036 y 0,025; IC de género y niños bajo 0,10, el de adultos llega a 0,101 (en el límite) |
| H-M3-5 | Concentración mayor que la del azar (por `destino_id` o `lugar`) | refutada | Gini 0,383 frente a 0,386 del azar (IC 95 % 0,370 a 0,401) |
| H-M3-6 | Reseñas e historial difieren en tipos o en calificaciones | refutada | No difieren en más que un efecto pequeño: V corregida 0,000 (hasta 0,069); delta de Cliff 0,047 (−0,005 a 0,098) |
| H-M3-7 | La red con contenido no supera a la popularidad más que la variabilidad entre semillas | pendiente | Se cierra en JJ-10 (`results/data/m3/summary.json` aún no existe) |
| H-M3-8 | El acierto por lugar es mucho mayor que por `destino_id` | pendiente | Se cierra en JJ-10 |
| H-M3-9 | «Pocas» interacciones obtienen menor NDCG@5 que «muchas» | pendiente | Se cierra en JJ-10 |
:::

Lectura de conjunto ([[tab:m3-veredictos]]): de las seis hipótesis que se pueden cerrar con los datos, cuatro quedan refutadas y dos
no concluyentes; **ninguna se confirma**. En estos datos generados no se detectó un efecto del tamaño mínimo declarado de las preferencias sobre el tipo
(H-M3-1, no concluyente, con un efecto de 0,023 y IC ajustado hasta 0,058), de la demografía (H-M3-4, no concluyente: no se
excluye V ≥ 0,10 para adultos) ni de la popularidad de la fuente (H-M3-3); tampoco hay concentración mayor que la del azar (H-M3-5) ni
diferencias grandes entre reseñas e historial (H-M3-6). «Refutada» significa aquí, por nuestro criterio, que el efecto es
compatible con cero y que se excluye un efecto del tamaño mínimo declarado, no que se haya demostrado que no existe ningún efecto; y
«no concluyente» significa que los datos no permiten ni confirmar ni descartar un efecto de ese tamaño.

<!-- revisar: Juan José — la «lectura de conjunto» es interpretación del redactor sobre los veredictos de hipotesis.json; valida el tono y el alcance (son datos generados, D4). -->

### Partición

El enunciado pide definir y justificar cómo se separan entrenamiento, validación y prueba, con una condición: ninguna interacción de
prueba puede usarse para entrenar. Además, todos los modelos de un módulo deben usar el mismo preprocesamiento y las mismas
particiones. Esta subsección dice cuál es la partición de M3, por qué es esa y qué se mide sobre ella.

**La regla (D3).** La partición es **por usuario**. Para cada usuario se ordenan sus interacciones al azar; si tiene 2 o más, la
primera va a **prueba**; si tiene 3 o más, la segunda va a **validación**; el resto es **entrenamiento**. Un usuario con una sola
interacción queda solo en entrenamiento. El azar usa una semilla fija, 2026 ([[tab:m3-particion-final]]), y las
interacciones se toman en un orden canónico por origen e identificador de origen, de modo que repetir el proceso da exactamente la
misma partición. Una interacción se identifica por el par (origen, `id_origen`), porque los identificadores de reseña y de historial
se solapan.

**Por qué no es temporal.** La opción natural, partir por tiempo, no es posible: `VisitDate` no es una fecha real (3 valores ligados
al número de fila, 2 de ellos —666 de 999 filas— posteriores a la creación de la versión 1 en Kaggle; véase la Ficha y la
decisión D3). La fecha queda solo descriptiva.

**Una sola partición para todos los modelos (D8).** La partición se calcula una vez, en el paso de datos, y se guarda en la columna
`split` de las interacciones procesadas. La usan por igual las referencias y la red. Para poder comprobar que es la misma, se guarda
su huella SHA-256 (de la tabla `usuario_id, destino_id, split` ordenada), que irá en la evidencia de cada archivo de resultados
(núcleo §6): si dos corridas tienen huellas distintas, no son comparables.

**Cómo se usa cada conjunto (D9).** La validación sirve solo para elegir hiperparámetros y para parar el entrenamiento. Los modelos
finales (referencias y red, con sus 30 semillas) se entrenan **solo con entrenamiento** y se evalúan **una vez** en prueba. Toda
estadística sacada de las interacciones, como la popularidad, los conteos por destino o los negativos muestreados por popularidad,
se calcula **solo con entrenamiento**. Si se calcularan con todos los datos, la popularidad «sabría» qué destinos aparecen en prueba.

**Qué se ordena al evaluar (D10).** Para cada usuario se ordenan todos los destinos del catálogo **excepto los que ya conoce**: en
prueba, los de entrenamiento y validación; en validación, los de entrenamiento. Un destino ya visto nunca cuenta como acierto. Los
141 usuarios sin interacciones no se evalúan: no tienen
interacciones con qué medir. Como mucho sirven para mostrar recomendaciones sin métricas; cómo se mide el caso de usuarios nuevos
(pregunta de negocio 1) se decide en JJ-6.

<!-- revisar: Juan José — D10 dice que los 141 sirven para el escenario de usuario nuevo; sin interacciones no hay con qué medir; decidir en JJ-6. -->

**Qué quedó en cada conjunto.** La [[tab:m3-particion-final]] da las interacciones y los usuarios por partición y por grupo de
actividad. El grupo se define con el **total** de interacciones del usuario (entrenamiento, validación y prueba juntas): «pocas» es
1 a 2 y «muchas» es 3 o más. Solo sirve para estratificar el reporte; no es una variable de ningún modelo. Hay 858 usuarios con
alguna interacción, todos con al menos una en entrenamiento; 606 tienen una interacción de prueba y 326 una de validación. La
validación contiene únicamente usuarios de «muchas»; de los 532 usuarios de «pocas», 252 (con una sola interacción) nunca se
evalúan y los otros 280 sí tienen prueba, con una única interacción de entrenamiento cada uno.

::: tabla m3-particion-final
Título: Interacciones y usuarios por partición y grupo de actividad en la partición final de M3
Fuente: `results/data/m3/particion/resumen.json` (`conteos.interacciones`, `conteos.usuarios`, `por_grupo_de_actividad.<grupo>` con `n_usuarios`, `interacciones`, `usuarios_con_prueba`, `usuarios_con_validacion` y `usuarios_solo_train`; la semilla 2026 sale de `semilla` con `run_id` = 0 y la huella SHA-256 de la partición, de `sha256.huella`). Los 141 usuarios sin interacciones (`conteos.usuarios_sin_interacciones_no_evaluables`) no están en ningún grupo y no se evalúan; «Solo entrenamiento» cuenta usuarios cuya única interacción es de entrenamiento. Comprobación: `results/data/m3/eda/actividad_usuarios.json`, `particion_d3` (`interacciones`, `usuarios_con_prueba`, `usuarios_con_validacion`, `usuarios_solo_entrenamiento`, `total`) da las mismas cifras de la regla D3.

| Grupo | Usuarios | Interacciones de entrenamiento | Interacciones de validación | Interacciones de prueba | Usuarios con prueba | Usuarios con validación | Solo entrenamiento |
|---|---:|---:|---:|---:|---:|---:|---:|
| Pocas (1 a 2) | 532 | 532 | 0 | 280 | 280 | 0 | 252 |
| Muchas (3 o más) | 326 | 534 | 326 | 326 | 326 | 326 | 0 |
| **Total** | **858** | **1 066** | **326** | **606** | **606** | **326** | **252** |
:::

**Dos hechos medidos que condicionan la evaluación.** Se miden sobre la partición para leer los resultados; como usan prueba y
validación, ningún modelo los usa como entrada (D9). Las cifras están en la [[tab:m3-particion-diagnosticos]].

::: tabla m3-particion-diagnosticos
Título: Diagnósticos de la partición final de M3: destinos fríos y coincidencia de lugar con el historial conocido
Fuente: `results/data/m3/particion/resumen.json`, `diagnosticos.items_frios.<split>` (`interacciones`, `interacciones_con_destino_sin_train`, `destinos_distintos`, `destinos_distintos_sin_train`) y `diagnosticos.mismo_lugar_en_historial_conocido.<split>` (`usuarios`, `con_otro_id_del_mismo_lugar`, `n_lugares` y `esperado_por_azar`; el supuesto del azar está en `supuesto_esperado_por_azar`). Los porcentajes no están en el archivo: son la división de las dos cifras de cada celda (205/606, 111/326, 204/606, 198,0/606, 95/326 y 95,8/326).

| Medida | Prueba | Validación |
|---|---:|---:|
| Interacciones del conjunto | 606 | 326 |
| Interacciones con destino sin ninguna interacción en entrenamiento (destino frío) | 205 (33,8 %) | 111 (34,0 %) |
| Destinos distintos | 463 | 280 |
| Destinos distintos sin interacción en entrenamiento | 158 | 95 |
| Usuarios evaluables | 606 | 326 |
| Usuarios con otro id del mismo lugar en su historial conocido | 204 (33,7 %) | 95 (29,1 %) |
| Esperado por azar con 5 lugares | 198,0 (32,7 %) | 95,8 (29,4 %) |
:::

- **Destinos fríos.** De las 606 interacciones de prueba, **205 (33,8 %)** son de destinos que no tienen **ninguna** interacción en
  entrenamiento; en destinos distintos, son 158 de 463. Para esas 205 interacciones la popularidad de entrenamiento es 0 y un
  filtrado colaborativo no tiene señal. En validación son 111 de 326 (34,0 %).
- **Coincidencia de lugar con el historial conocido.** Se cuenta cuántos usuarios de prueba tienen en su historial conocido
  (entrenamiento o validación) algún otro id del **mismo lugar** que su destino de prueba: son **204 de 606 (33,7 %)**. Es **lo
  esperable por azar**: como los 1 000 ids son 5 lugares (D2), el azar predice **198,0 usuarios (32,7 %)**, bajo el supuesto de que
  el lugar del destino de prueba es uniforme sobre los 5 lugares e independiente del historial conocido, con un objetivo por
  usuario. En validación son 95 de 326 (29,1 %) frente a 95,8 esperados (29,4 %). Además, un modelo no sabe cuál de los lugares
  que el usuario ya conoce es el del destino que se busca, de modo que esa coincidencia no vuelve «trivial» ni «resuelto de
  antemano» el acierto por lugar.

Dos consecuencias para leer los resultados. Primera, un tercio de la prueba (destinos fríos) no tiene señal en las interacciones
de entrenamiento. Segunda, todo acierto por lugar debe compararse con su línea base del azar, y la métrica principal es la de
`destino_id`.

Como la validación solo tiene usuarios de «muchas», los hiperparámetros se eligen con ese grupo: es un sesgo de selección que hay
que tener en cuenta al comparar los grupos «pocas» y «muchas» en prueba.

<!-- revisar: Juan José — cómo se reporta el acierto por lugar lo propone el auditor-fugas y se decide en JJ-6. -->
<!-- revisar: Juan José — los porcentajes 33,8 %, 34,0 %, 33,7 %, 32,7 %, 29,1 % y 29,4 % son división del redactor sobre cifras del JSON; la lectura de que los destinos fríos «no tienen señal» en las interacciones es interpretación del redactor. -->

### Métricas de evaluación

<!-- JJ-4 (redactor-tecnico, Sonnet) para Juan José. Las ecuaciones siguen `src/m3_recomendacion/metricas.py` (y `eda_estadistica.py` para Gini y HHI); toda cifra sale de `results/data/m3/` (ruta o clave en la fuente de cada tabla). Las lecturas de resultados son interpretación del redactor y están marcadas. -->

El enunciado pide métricas @K, cobertura del catálogo, concentración de las recomendaciones y desempeño por grupo de actividad.
Esta subsección define cada una con la misma fórmula que usa el código; los resultados se leen en «Modelos de referencia». Los
candidatos de cada usuario y la partición son los de la subsección «Partición» (D8 a D10).

**Notación.** $\mathcal{U}$ es el conjunto de usuarios evaluados (606 en prueba) y $n$ el tamaño del catálogo (1 000 destinos). Para un usuario $u$: $C_u$ son sus **candidatos** (el
catálogo menos el historial conocido, D10) y $N_u = |C_u|$; $R_u \subset C_u$ son sus destinos **relevantes** (el destino de la
partición evaluada; en prueba y en validación $|R_u| = 1$, D3); y $L_u^K = (L_u(1), \dots, L_u(K))$ es la lista recomendada,
ordenada de mejor a peor, sin repetidos y contenida en $C_u$, donde $L_u(r)$ es el destino en el **rango** $r$ (1 es el primero).
En las intersecciones $L_u^K$ se trata como conjunto.

**Métricas por usuario.** Acierto, Precision y Recall en $K$:

$$
\text{Acierto@}K(u) = \mathbb{1}\!\left[\,|L_u^K \cap R_u| > 0\,\right], \qquad
\text{Precision@}K(u) = \frac{|L_u^K \cap R_u|}{K}, \qquad
\text{Recall@}K(u) = \frac{|L_u^K \cap R_u|}{|R_u|},
$$

donde Precision@$K$ divide por el $K$ nominal. NDCG@$K$ binario es el cociente entre la ganancia descontada de la lista y la de una
lista ideal:

$$
\text{DCG@}K(u) = \sum_{r=1}^{K} \frac{\mathbb{1}[L_u(r) \in R_u]}{\log_2(r+1)}, \qquad
\text{IDCG@}K(u) = \sum_{r=1}^{\min(|R_u|,\,K)} \frac{1}{\log_2(r+1)}, \qquad
\text{NDCG@}K(u) = \frac{\text{DCG@}K(u)}{\text{IDCG@}K(u)} .
$$

**Con un único relevante.** Como cada usuario de prueba tiene exactamente un destino relevante (D12), las fórmulas generales se
simplifican: $\text{Recall@}K(u) = \text{Acierto@}K(u)$, $\text{Precision@}K(u) = \text{Acierto@}K(u)/K$ e $\text{IDCG@}K(u) = 1$.
Por eso Precision@$K$ **tiene techo $1/K$** (0,1 con $K = 10$, aunque el usuario acierte siempre) y Recall@$K$ coincide con el
acierto. Siguen siendo tres métricas porque las fórmulas generales son las del enunciado y el módulo no cambia si algún día hay más
de un relevante. Con un relevante en el rango $r_u$, NDCG@$K$ vale $1/\log_2(r_u+1)$ si $r_u \le K$ y 0 si no (por ejemplo, 1 en el
rango 1, 0,631 en el 2, 0,387 en el 5 y 0,289 en el 10).

**Promedio sobre los usuarios evaluados.** Cada métrica por usuario $M_u$ (Acierto, Precision, Recall, NDCG y acierto por lugar) se
reporta como el promedio simple

$$
\overline{M}@K = \frac{1}{|\mathcal{U}|} \sum_{u \in \mathcal{U}} M_u@K ,
$$

y en cada una de las 30 semillas se calcula una vez ese promedio; las tablas dan la media y la desviación de esos 30 valores
(desviación muestral, con $n-1$ en el denominador).

**Cobertura, exposiciones y concentración.** La **cobertura** es la fracción del catálogo que aparece en alguna lista, y la
**exposición** $e_i$ de un destino es en cuántas listas entra:

$$
\text{Cobertura@}K = \frac{\left|\bigcup_{u \in \mathcal{U}} L_u^K\right|}{n}, \qquad
e_i = \#\{\,u \in \mathcal{U} : i \in L_u^K\,\}, \quad i = 1, \dots, n .
$$

Estas dos no se promedian por usuario: se calculan sobre todas las listas de una corrida. La concentración de las exposiciones usa
las mismas definiciones del análisis descriptivo (subsección «Estructura y heterogeneidad»), con $e_i$ en lugar del número de
interacciones $x_i$: con $e_{(1)} \le \dots \le e_{(n)}$ las exposiciones ordenadas de menos a más (los destinos con exposición 0
**cuentan**: son $n = 1\,000$ en total) y $s_i = e_i / \sum_j e_j$,

$$
\text{Gini} = \frac{2 \sum_{i=1}^{n} i\, e_{(i)}}{n \sum_{i=1}^{n} e_{(i)}} - \frac{n+1}{n}, \qquad
\text{HHI} = \sum_{i=1}^{n} s_i^2 .
$$

El Gini no está reescalado y, en general, va de 0 a $(n-1)/n = 0{,}999$; el HHI va de $1/n = 0{,}001$ a 1. Pero **los extremos
alcanzables dependen de $K$ y del número de usuarios**: cada lista tiene $K$ destinos distintos, así que un destino aparece a lo
sumo una vez por usuario y las exposiciones suman $\sum_i e_i = \sum_u |L_u^K|$ ($606\,K$ con listas completas). La mayor
concentración posible es que todos los usuarios reciban los mismos $K$ destinos, y entonces

$$
\text{Gini} \le 1 - \frac{K}{n}, \qquad \text{HHI} \le \frac{1}{K},
$$

es decir, Gini $\le$ 0,999, 0,997, 0,995 y 0,990 y HHI $\le$ 1, 0,333, 0,200 y 0,100 para $K = 1, 3, 5, 10$. En el otro extremo, con
$K = 1$ hay 606 exposiciones repartidas entre 1 000 destinos: al menos 394 destinos tienen $e_i = 0$ y HHI $\ge 1/606 = 0{,}0017$,
aunque las listas se sortearan sin ningún criterio. Por eso estas medidas se comparan con el máximo alcanzable para ese $K$ y con el
recomendador aleatorio, y no con 0 ni con 1. Son las que se usarán para la pregunta de negocio 2 (concentración de las
recomendaciones); aquí solo se miden.

<!-- revisar: Juan José — las cotas 1 − K/n y 1/K, «al menos 394 destinos con exposición 0» (1 000 − 606) y HHI ≥ 1/606 son aritmética del redactor (con la corrección de R1), no cifras de un JSON; el Gini y el HHI máximos son los de «todos reciben los mismos K destinos». -->

**Acierto por lugar.** Los 1 000 destinos son 5 lugares (decisión D2). Con $\ell(i)$ el lugar del destino $i$ y $o_u$ el destino
objetivo de $u$ (con $R_u = \{o_u\}$), el **acierto por lugar** es

$$
\text{Lugar@}K(u) = \mathbb{1}\!\left[\,\exists\, i \in L_u^K : \ell(i) = \ell(o_u)\,\right],
$$

que se promedia como las demás. Solo se calcula para $K \in \{1, 3\}$ (D12) y **siempre junto a su línea base del azar**, porque con
5 lugares acertar uno por casualidad es fácil (véase el diagnóstico de la partición en la [[tab:m3-particion-diagnosticos]]).

**El recomendador aleatorio como piso, con valores esperados.** El aleatorio recomienda, a cada usuario, un subconjunto uniforme de
$K'_u = \min(K, N_u)$ candidatos, en orden al azar. Su valor esperado para cada métrica tiene forma cerrada (aquí $|R_u| = 1$, y
como $N_u$ es cercano a 1 000 y $K \le 10$, $K'_u = K$):

$$
\mathbb{E}[\text{Acierto@}K] = 1 - \frac{\binom{N_u - |R_u|}{K'_u}}{\binom{N_u}{K'_u}} = \frac{K'_u}{N_u}, \qquad
\mathbb{E}[\text{Precision@}K] = \frac{|R_u|\,K'_u}{N_u\, K}, \qquad
\mathbb{E}[\text{Recall@}K] = \frac{K'_u}{N_u},
$$

$$
\mathbb{E}[\text{NDCG@}K] = \frac{1}{N_u} \sum_{r=1}^{K'_u} \frac{1}{\log_2(r+1)}, \qquad
\mathbb{E}[\text{Lugar@}K] = 1 - \frac{\binom{N_u - m_u}{K'_u}}{\binom{N_u}{K'_u}}, \quad
m_u = \#\{\,i \in C_u : \ell(i) = \ell(o_u)\,\},
$$

$$
\mathbb{E}[\text{Cobertura@}K] = \frac{1}{n} \sum_{i=1}^{n} \left[\, 1 - \prod_{u:\, i \in C_u} \left(1 - \frac{K'_u}{N_u}\right) \right],
$$

donde en NDCG el relevante está en cada rango con probabilidad $1/N_u$, $m_u$ incluye al propio objetivo y la cobertura supone
independencia entre usuarios (exacta, porque cada usuario sortea por separado). Los esperados de Acierto, Precision, Recall, NDCG y
Lugar se promedian sobre los usuarios evaluados con la ecuación de arriba; así, $\mathbb{E}[\text{Precision@}K]$ es la misma
constante para todo $K \le N_u$ (0,0010 en prueba) y $\mathbb{E}[\text{Recall@}K] \approx K/N_u$. Son el piso con el que se leen los
resultados: una métrica cercana a su esperado aleatorio no muestra nada que el azar no explique.

**Valores de $K$.** $K \in \{1, 3, 5, 10\}$ (`evaluacion.k`, D12); $K = 5$ es el valor por defecto del caso de uso (el que muestra la
aplicación) y $K = 10$ es el máximo del contrato.

**Resultados por grupo de actividad.** El grupo de un usuario se define con el **total** de sus interacciones (entrenamiento,
validación y prueba): «pocas» es 1 a 2 y «muchas» es 3 o más (véase «Partición»). Se reporta cada métrica por grupo, con los
usuarios de prueba de cada uno (280 y 326), **solo para estratificar**: el grupo no es entrada de ningún modelo. La validación
solo tiene usuarios de «muchas», así que los hiperparámetros de la factorización se eligieron con ese grupo.

<!-- revisar: Juan José — K ∈ {1, 3, 5, 10} sigue siendo [PROPUESTO por el enunciado («@K»)] en tu spec D12; confirma. La cobertura por grupo no se reporta: en el archivo se calcula solo con las listas de ese grupo y no es comparable con la global. -->
<!-- TODO(cita): NDCG, el acierto/recall@K y la cobertura/diversidad del catálogo necesitan referencia verificada en blog/references.bib (JJ-9); no se citan de memoria. -->

### Modelos de referencia

<!-- JJ-4 (redactor-tecnico, Sonnet) para Juan José. Cifras de results/data/m3/{summary.json, metricas_por_k.json, metricas_por_grupo.json, hpo_ensayos.json}; ecuaciones de src/m3_recomendacion/{referencias.py, hpo.py, metricas.py}. Sin conclusiones sobre la red (JJ-5, JJ-10) ni respuestas a las preguntas de negocio (JJ-6). -->

El enunciado pide comparar la red con al menos dos modelos de referencia bajo el mismo preprocesamiento y la misma partición. Los tres
de esta subsección usan la partición única de D8 (huella `b35cd70b…58e8b8`, la misma en todos los resultados),
se ajustan **solo con entrenamiento** (D9), se evalúan una vez en prueba con las 30 semillas $0, \dots, 29$ (`semillas.base_seed` =
0 y `semillas.n` = 30; D14) y reciben los mismos candidatos (D10). La [[tab:m3-presupuesto]] resume su presupuesto y su costo.

**Popularidad (D11 a).** El puntaje es el conteo de interacciones del destino en entrenamiento, igual para todos los usuarios:

$$
s^{\text{pop}}_{ui} = n_i = \#\{\,(u', i) \in \text{train}\,\} \quad \text{para todo } u .
$$

Un destino sin ninguna interacción en entrenamiento tiene puntaje 0 y queda al final; los empates se rompen al azar con la semilla de
la corrida (se permutan los candidatos de forma uniforme y se ordena de forma estable por puntaje descendente). **La columna
`popularidad` de la fuente no se usa**: es un atributo del destino y no un conteo de interacciones, y el descriptivo muestra que no
se relaciona con ellas (H-M3-3, ρ de Spearman = −0,011). No tiene hiperparámetros, pero estima un conteo por destino, así que
reporta 1 000 parámetros.

**Factorización de matrices implícita por ALS (D11 b).** Sigue la formulación de Hu, Koren y Volinsky (2008) para retroalimentación
implícita. <!-- TODO(cita): Hu, Koren y Volinsky (2008) [VERIFICAR en JJ-9]; pasar a [@clave] cuando esté en references.bib -->
Con $r_{ui} = 1$ si el par $(u, i)$ es una interacción de entrenamiento y 0 si no (la calificación no se usa, D1), se define la
preferencia $p_{ui} = r_{ui}$ y la confianza $c_{ui} = 1 + \alpha\, r_{ui}$. Cada usuario con al menos una interacción de
entrenamiento tiene un factor $x_u \in \mathbb{R}^f$ y cada destino del catálogo un factor $y_i \in \mathbb{R}^f$ (las sumas sobre
usuarios recorren solo a esos usuarios); el modelo minimiza, **sobre todos los pares usuario × destino** (no solo los observados),

$$
L(X, Y) = \sum_{u, i} c_{ui}\,\bigl(p_{ui} - x_u^\top y_i\bigr)^2 + \lambda \Bigl(\sum_{u} \lVert x_u \rVert^2 + \sum_{i} \lVert y_i \rVert^2\Bigr),
$$

y puntúa $s_{ui} = x_u^\top y_i$. Con $Y$ fija, $L$ se separa por usuario y cada $x_u$ resuelve un problema cuadrático estrictamente
convexo (la matriz $Y^\top C^u Y + \lambda I$ es definida positiva si $\lambda > 0$), cuyo minimizador es cerrado; lo mismo vale para
cada $y_i$ con $X$ fija. Con $C^u$ la matriz diagonal de las confianzas $c_{ui}$ de los destinos, $C^i$ la de las confianzas $c_{ui}$ de
los usuarios, $N(u)$ los destinos de entrenamiento de $u$ y $N(i)$ los usuarios de entrenamiento de $i$:

$$
x_u = \bigl(Y^\top C^u Y + \lambda I\bigr)^{-1} Y^\top C^u\, p(u), \qquad
y_i = \bigl(X^\top C^i X + \lambda I\bigr)^{-1} X^\top C^i\, p(i),
$$

y, como $C^u$ difiere de la identidad solo en los destinos de $N(u)$, la matriz del sistema se arma con la identidad que hace barato
el paso:

$$
Y^\top C^u Y = Y^\top Y + Y^\top (C^u - I)\, Y = Y^\top Y + \alpha \sum_{i \in N(u)} y_i y_i^\top, \qquad
Y^\top C^u\, p(u) = (1 + \alpha) \sum_{i \in N(u)} y_i ,
$$

y lo mismo para $y_i$ con los factores $x_u$, $u \in N(i)$. Así $Y^\top Y$ se calcula una vez por medio paso y por cada usuario
solo se suman sus destinos (sin armar la matriz usuario × destino por usuario). Como cada medio paso minimiza exactamente $L$ en
un bloque con el otro fijo, **la pérdida no aumenta en ningún medio paso** (salvo error de redondeo) y el algoritmo es
determinista dada la inicialización. **Inicialización:** las entradas de $X$ y de $Y$ se sortean de $\mathcal{N}(0, \sigma^2)$ con
$\sigma = 0{,}01$ (`escala_inicial`, valor fijo, no se busca) usando la semilla de la corrida, y las filas de $Y$ de destinos sin
interacciones de entrenamiento se ponen en 0. Cada barrido actualiza $X$ con $Y$ fija y luego $Y$ con $X$ fija, durante
`iteraciones` barridos. **Destinos sin entrenamiento:** su minimizador exacto es $y_i = 0$ (todos sus $p_{ui}$ valen 0 y
$\lambda > 0$) y así quedan; su puntaje es 0 para todos los usuarios y el modelo no tiene información de ellos. **Parámetros:**
$(n_{\text{usuarios}} + n_{\text{destinos}}) \cdot f$, con $n_{\text{usuarios}} = 858$ (los usuarios con alguna interacción de
entrenamiento, véase «Partición») y $n_{\text{destinos}} = 1\,000$, es decir $7\,432$ con $f = 4$. Esa cifra incluye las filas de
los 345 destinos sin entrenamiento, que valen 0 por construcción; sin ellas, los parámetros con datos son
$(858 + 655) \cdot 4 = 6\,052$. Cada medio paso cuesta del orden
de $(\text{filas del otro lado} + |\text{train}|)\, f^2 + \text{filas}\cdot f^3$ operaciones, porque se forma $F^\top F$ una vez, se
suman $|N(\cdot)|$ términos $f \times f$ por fila y se resuelve un sistema $f \times f$ por fila.

<!-- revisar: Juan José — (1) las ecuaciones son las de `referencias.py` (`perdida_als`, `actualizar_factores`); falta contrastar la notación con el artículo de Hu, Koren y Volinsky cuando JJ-9 lo verifique, y no se afirma aquí nada del artículo más allá de c = 1 + α·r y las actualizaciones cerradas que implementa el código. (2) El orden de costo por medio paso es lectura del redactor del código, no una medición. -->

**Aleatorio.** Piso de referencia: el puntaje de cada par es un número uniforme en (0, 1), independiente; con el desempate al azar
el top-$K$ entre los candidatos es un subconjunto uniforme sin reemplazo. No estima nada (0 parámetros) y su valor esperado es
analítico (ecuaciones de «Métricas de evaluación»). Las 30 semillas del aleatorio sirven para comprobar que el código de las
métricas coincide con ese esperado y para mostrar cuánto varían las métricas solo por azar.

**Búsqueda declarada (comparación justa).** Solo la factorización tiene hiperparámetros que buscar. Se usa Optuna con el muestreador
TPE (semilla 2026), **20 ensayos** (D13, el mismo presupuesto de la red, núcleo §6) y por objetivo el **NDCG@5 medio en
validación** (326 usuarios, candidatos = catálogo menos entrenamiento). Cada ensayo ajusta el modelo solo con entrenamiento, y en
todos el modelo y el desempate usan la misma semilla de corrida (la semilla 0), así que solo cambian los hiperparámetros. La
búsqueda no lee prueba. El espacio es elección del equipo, no de la literatura ([[tab:m3-hpo-espacio]]). Popularidad y aleatorio
tienen 0 hiperparámetros y 1 configuración. Recuérdese el sesgo anotado en «Partición»: como la
validación solo contiene usuarios de «muchas», la configuración elegida optimiza para ese grupo.

<!-- TODO(cita): Optuna y el muestreador TPE necesitan referencia verificada en blog/references.bib (JJ-9). -->

**Por qué se acota λ: la solución nula.** Con $\lambda$ grande, el único mínimo global de $L$ es $X = Y = 0$. Sea $P$ la matriz de
preferencias de entrenamiento ($p_{ui}$) y $\sigma_{\max}$ su mayor valor singular. En $(X, Y) = (0, 0)$ solo contribuyen los pares
observados, $L(0, 0) = (1 + \alpha)\,|\text{train}|$, y con $Z = XY^\top$ (de elementos $z_{ui} = x_u^\top y_i$) se tiene

$$
L(X, Y) - L(0, 0) = \sum_{u,i} c_{ui}\, z_{ui}^2 - 2(1 + \alpha)\,\langle P, Z \rangle + \lambda\bigl(\lVert X \rVert^2 + \lVert Y \rVert^2\bigr)
\;\ge\; \bigl(\lambda - (1 + \alpha)\,\sigma_{\max}\bigr)\bigl(\lVert X \rVert^2 + \lVert Y \rVert^2\bigr),
$$

porque $\sum c_{ui} z_{ui}^2 \ge 0$, $\langle P, Z \rangle \le \sigma_{\max} \lVert Z \rVert_*$ y $\lVert Z \rVert_* \le \tfrac{1}{2}
(\lVert X \rVert^2 + \lVert Y \rVert^2)$ (norma nuclear de $Z$; las normas de $X$ y $Y$ son de Frobenius). Si
$\lambda \ge (1 + \alpha)\,\sigma_{\max}$, entonces $X = Y = 0$ es el único mínimo global de $L$. La condición es **exacta**: si
$\lambda < (1 + \alpha)\,\sigma_{\max}$, el origen es un punto de silla (en la dirección de los primeros vectores singulares,
$L - L(0, 0) = 2t^2\,(\lambda - (1 + \alpha)\,\sigma_{\max}) + O(t^4) < 0$) y existe un mínimo no nulo. Con los datos de
entrenamiento, $\sigma_{\max} = 2{,}871$ y, como $\alpha \ge \alpha_{\min} = 1$ en el rango declarado,
$(1 + \alpha)\,\sigma_{\max} \ge (1 + \alpha_{\min})\,\sigma_{\max} = 5{,}742$. **En una primera corrida** el espacio permitía
$\lambda$ hasta 100 y la búsqueda eligió esa solución nula (los factores guardados eran del orden de $10^{-23}$ y la pérdida era
exactamente $L(0, 0)$): sus listas salían del residuo numérico y no de lo aprendido. Se detectó al verificar la pérdida de los
factores, y es parte de la metodología de este trabajo. Por eso el tope de $\lambda$ es **5,0**, por debajo de 5,742: ningún punto del espacio cae en la región degenerada. Lo que es solo **suficiente, no necesario**
es ese tope del espacio (para $\alpha$ grande, $\lambda$ podría llegar más arriba sin colapsar).

Además hay una guarda. Un ajuste de la factorización se marca como **degenerado** si se cumple cualquiera de estas tres condiciones:
$\lambda \ge (1 + \alpha)\,\sigma_{\max}(P_{\text{train}})$; la pérdida final es $\ge L(0, 0) = (1 + \alpha)\,|\text{train}|$; o
$\max_{u,i} |x_u^\top y_i| < 10^{-8}$ (`tolerancia_degenerado`). Un ensayo degenerado se registra, cuenta en el presupuesto y nunca puede
ser el mejor, y el experimento falla si la factorización final lo es; la tolerancia por sí sola no basta, porque solo detecta
puntajes numéricamente nulos. En la búsqueda actual hay 0 ensayos degenerados, y el puntaje máximo de las 30
factorizaciones finales es en media 0,805 (desviación 0,028), muy por encima de $10^{-8}$.

<!-- revisar: Juan José — σ_max, α_min, λ_max y la cota salen de `hpo_ensayos.json`, `familias.mf_als.cota_solucion_nula`. Los factores del orden de 1e-23 y la pérdida exactamente L(0, 0) de la primera corrida NO están en `results/` (la corrida se sobrescribió): vienen de la verificación (evidencia en `alucinaciones/evidencias/JJ-4/colapso_mf.md`) y se citan como hecho de la metodología, no como resultado regenerable. La desigualdad y la derivación (L(0,0) = (1+α)|train|) las revisé a mano; la exactitud de la condición λ ≥ (1+α)σ_max (si y solo si) y el punto de silla con L − L(0,0) = 2t²(λ − (1+α)σ_max) + O(t⁴) vienen de la verificación (R1) y de la `nota` de `cota_solucion_nula`; no los derivé yo, solo la desigualdad. Lo suficiente, no necesario, es el tope del espacio. Las tres condiciones de la guarda son las de `referencias.py` (`condiciones_degenerado`). El tope de λ = 5,0 y la tolerancia 1e-8 son [PROPUESTOS], a decidir por ti. -->

::: tabla m3-hpo-espacio
Título: Espacio de búsqueda de la factorización por ALS y mejor configuración (20 ensayos de Optuna, TPE)
Fuente: `results/data/m3/hpo_ensayos.json`, `familias.mf_als` (`espacio`, `mejor`, `n_degenerados`, `cota_solucion_nula` con `sigma_max_train`, `alfa_min`, `lambda_max`, `cota` y `lambda_max_bajo_la_cota`; `nota_degenerados`, `ensayos[*].valor`, `semilla_sampler`); `results/data/m3/summary.json`, `modelos.mf_als.diagnosticos.max_abs_puntaje` (`media` y `desviacion` entre 30 semillas, para el puntaje máximo de las factorizaciones finales); `configs/m3/hpo.yaml`, `busqueda.espacio`; `configs/m3/base.yaml`, `mf_als.tolerancia_degenerado`. Los rangos son elección del equipo [PROPUESTO por JJ-4]; el tope de λ sale de la cota de arriba. Valor del objetivo: NDCG@5 medio en validación de una sola semilla (la 0) con los 326 usuarios de «muchas», a cuatro cifras significativas.

| Hiperparámetro | Tipo | Rango | Escala | Mejor valor (ensayo 19) |
|---|---|---|---|---:|
| Factores f (`factores`) | entero | 4 a 64 | logarítmica | 4 |
| Regularización λ (`regularizacion`) | real | 0,001 a 5 | logarítmica | 0,002104 |
| Confianza α (`alfa`) | real | 1 a 100 | logarítmica | 1,485 |
| Barridos (`iteraciones`) | entero | 5 a 30 | lineal | 9 |
| Escala inicial σ (`escala_inicial`) | real | no se busca | no aplica | 0,01 (fijo) |
| **NDCG@5 en validación** | | | | **0,01015** |
:::

El mejor valor del objetivo es **0,01015** (ensayo 19; $f = 4$, $\lambda = 0{,}002104$, $\alpha = 1{,}485$, 9 barridos), con Recall@5 de
0,0184 en validación (6 de 326 usuarios; 0,0184 × 326, cálculo del redactor). Los valores de los 20 ensayos van de 0 (ensayo 7) a
0,01015, y ninguno es degenerado. Los cuatro hiperparámetros del mejor ensayo quedan en el extremo bajo o cerca de él: $f = 4$ es el
mínimo del rango, $\lambda = 0{,}0021$ queda cerca del mínimo (0,001) y $\alpha = 1{,}485$ cerca del suyo (1); los barridos (9) quedan
en el tramo bajo del rango.

<!-- revisar: Juan José — que los mejores valores queden en el extremo bajo de los rangos (f = 4 es el mínimo, λ y α cerca del mínimo) es observación del redactor sobre hpo_ensayos.json; sugiere que quizá habría que ampliar el rango hacia abajo, pero no se hizo ni se afirma que eso mejore algo. El 0,0184 × 326 ≈ 6 aciertos es cálculo del redactor. -->

::: tabla m3-presupuesto
Título: Presupuesto y costo de cómputo de los tres modelos de referencia
Fuente: `results/data/m3/summary.json`, `modelos.<modelo>` (`hiperparametros`, `n_parametros`, `n_configuraciones_busqueda`, `tiempo_busqueda_s`, `tiempo_corridas_finales_s`, `tiempo_total_s`, `device`; y `diagnosticos.n_parametros_con_datos`, resumido entre semillas con `media`, `desviacion`, `minimo`, `maximo` y `n`). Los tiempos son de pared, de una sola ejecución; las corridas finales son las 30 semillas juntas e incluyen el ajuste, la puntuación, el ordenamiento y las métricas de cada una. Dispositivo: CPU (`device` = cpu). Los parámetros de la factorización son (858 usuarios + 1 000 destinos) · f = 7 432 e incluyen las filas de los 345 destinos sin entrenamiento, que valen 0 por construcción; sin ellas son (858 + 655) · 4 = 6 052 (`modelos.mf_als.diagnosticos.n_parametros_con_datos`, `media`).

| Modelo | Hiperparámetros | Parámetros estimados | Configuraciones de la búsqueda | Búsqueda (s) | 30 corridas finales (s) | Total (s) |
|---|---|---:|---:|---:|---:|---:|
| Popularidad | ninguno | 1 000 | 1 | 0,00 | 5,65 | 5,65 |
| Factorización por ALS | f = 4, λ = 0,002104, α = 1,485, 9 barridos (los 4 buscados; σ = 0,01 fijo) | 7 432 (6 052 con datos) | 20 | 17,16 | 16,70 | 33,86 |
| Aleatorio | ninguno | 0 | 1 | 0,00 | 7,79 | 7,79 |
:::

<!-- TODO(dato-faltante): hardware de la máquina que midió los tiempos de la tabla m3-presupuesto (CPU, RAM, sistema); no está en summary.json. -->

**Resultados en prueba.** La [[tab:m3-resultados-k]] da la media y la desviación entre las 30 semillas de Precision, Recall, NDCG y
cobertura para cada $K$, junto con el esperado analítico del aleatorio. Recall@$K$ es igual al acierto@$K$ y Precision@$K$ es el
acierto dividido por $K$ (un relevante por usuario).

::: tabla m3-resultados-k
Título: Resultados en prueba por K de los tres modelos de referencia (media ± desviación entre 30 semillas) y esperado analítico del aleatorio
Fuente: `results/data/m3/summary.json`, `modelos.<modelo>.metricas` (`precision@K`, `recall@K`, `ndcg@K`, `cobertura@K`; `media` y `desviacion`, ddof = 1, n = 30) y `linea_base_aleatoria_analitica.global` (esperado del aleatorio). 606 usuarios de prueba. Las mismas cifras están en `results/data/m3/metricas_por_k.json`. Cuatro decimales.

| Métrica | K | Popularidad | Factorización por ALS | Aleatorio | Esperado del aleatorio |
|---|---:|---:|---:|---:|---:|
| Precision | 1 | 0,0000 ± 0,0000 | 0,0007 ± 0,0009 | 0,0010 ± 0,0015 | 0,0010 |
| Precision | 3 | 0,0006 ± 0,0003 | 0,0007 ± 0,0007 | 0,0009 ± 0,0008 | 0,0010 |
| Precision | 5 | 0,0007 ± 0,0000 | 0,0009 ± 0,0005 | 0,0010 ± 0,0007 | 0,0010 |
| Precision | 10 | 0,0007 ± 0,0002 | 0,0011 ± 0,0004 | 0,0010 ± 0,0004 | 0,0010 |
| Recall (= acierto) | 1 | 0,0000 ± 0,0000 | 0,0007 ± 0,0009 | 0,0010 ± 0,0015 | 0,0010 |
| Recall (= acierto) | 3 | 0,0017 ± 0,0010 | 0,0021 ± 0,0021 | 0,0028 ± 0,0023 | 0,0030 |
| Recall (= acierto) | 5 | 0,0033 ± 0,0000 | 0,0044 ± 0,0025 | 0,0048 ± 0,0034 | 0,0050 |
| Recall (= acierto) | 10 | 0,0069 ± 0,0020 | 0,0105 ± 0,0043 | 0,0096 ± 0,0040 | 0,0100 |
| NDCG | 1 | 0,0000 ± 0,0000 | 0,0007 ± 0,0009 | 0,0010 ± 0,0015 | 0,0010 |
| NDCG | 3 | 0,0010 ± 0,0006 | 0,0015 ± 0,0014 | 0,0021 ± 0,0019 | 0,0021 |
| NDCG | 5 | 0,0016 ± 0,0002 | 0,0024 ± 0,0015 | 0,0029 ± 0,0022 | 0,0030 |
| NDCG | 10 | 0,0028 ± 0,0007 | 0,0043 ± 0,0017 | 0,0044 ± 0,0022 | 0,0046 |
| Cobertura | 1 | 0,0037 ± 0,0006 | 0,0245 ± 0,0025 | 0,4561 ± 0,0084 | 0,4546 |
| Cobertura | 3 | 0,0050 ± 0,0000 | 0,0486 ± 0,0023 | 0,8398 ± 0,0090 | 0,8381 |
| Cobertura | 5 | 0,0183 ± 0,0015 | 0,0677 ± 0,0035 | 0,9523 ± 0,0067 | 0,9521 |
| Cobertura | 10 | 0,0250 ± 0,0000 | 0,1006 ± 0,0043 | 0,9974 ± 0,0018 | 0,9977 |
:::

**Por grupo de actividad.** La [[tab:m3-resultados-grupo]] repite NDCG@5 y Recall@10 para los usuarios de «pocas» y de «muchas».

::: tabla m3-resultados-grupo
Título: NDCG@5 y Recall@10 en prueba por grupo de actividad (media ± desviación entre 30 semillas) y esperado del aleatorio de cada grupo
Fuente: `results/data/m3/metricas_por_grupo.json`, `modelos.<modelo>.<grupo>` (`n_usuarios`, `ndcg@5`, `recall@10`; `media`, `desviacion`, `mejor`, `peor` y `n` = 30) y `aleatorio_analitico.<grupo>` (esperado del aleatorio, promediado sobre los usuarios del grupo). El grupo se define con el total de interacciones del usuario (pocas = 1 a 2; muchas = 3 o más). Cuatro decimales.

| Grupo | Usuarios de prueba | Métrica | Popularidad | Factorización por ALS | Aleatorio | Esperado del aleatorio |
|---|---:|---|---:|---:|---:|---:|
| Pocas (1 a 2) | 280 | NDCG@5 | 0,0035 ± 0,0004 | 0,0028 ± 0,0020 | 0,0027 ± 0,0024 | 0,0030 |
| Pocas (1 a 2) | 280 | Recall@10 | 0,0115 ± 0,0032 | 0,0115 ± 0,0061 | 0,0092 ± 0,0054 | 0,0100 |
| Muchas (3 o más) | 326 | NDCG@5 | 0,0000 ± 0,0000 | 0,0021 ± 0,0019 | 0,0031 ± 0,0029 | 0,0030 |
| Muchas (3 o más) | 326 | Recall@10 | 0,0030 ± 0,0031 | 0,0096 ± 0,0045 | 0,0099 ± 0,0056 | 0,0100 |
:::

**Concentración y acierto por lugar.** La [[tab:m3-exposiciones]] reúne el Gini y el HHI de las exposiciones para cada $K$ y el acierto
por lugar para $K \in \{1, 3\}$ con su línea base del azar (la línea base es la misma para los tres modelos).

::: tabla m3-exposiciones
Título: Concentración de las exposiciones (Gini y HHI) y acierto por lugar en prueba, con la línea base del azar
Fuente: `results/data/m3/summary.json`, `modelos.<modelo>.concentracion` (`gini@K`, `hhi@K`; `media` y `desviacion` entre 30 semillas), `modelos.<modelo>.metricas` (`acierto_por_lugar@K`) y `modelos.<modelo>.acierto_por_lugar_linea_base` (también `linea_base_aleatoria_analitica.global`). Las exposiciones son sobre los 1 000 destinos del catálogo y los 606 usuarios de prueba; Gini sin reescalar. Máximos alcanzables (aritmética del redactor, no están en el archivo): Gini ≤ 1 − K/1 000 y HHI ≤ 1/K, cuando todos los usuarios reciben los mismos K destinos; con K = 1, HHI ≥ 1/606. Cuatro decimales para las medias y las desviaciones.

| K | Gini: popularidad | Gini: factorización | Gini: aleatorio | Gini máximo alcanzable | HHI: popularidad | HHI: factorización | HHI: aleatorio | HHI máximo alcanzable |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0,9990 ± 0,0000 | 0,9893 ± 0,0013 | 0,6308 ± 0,0109 | 0,999 | 0,9869 ± 0,0000 | 0,0911 ± 0,0126 | 0,0026 ± 0,0001 | 1,000 |
| 3 | 0,9957 ± 0,0000 | 0,9790 ± 0,0012 | 0,4021 ± 0,0075 | 0,997 | 0,2217 ± 0,0001 | 0,0448 ± 0,0033 | 0,0016 ± 0,0000 | 0,333 |
| 5 | 0,9949 ± 0,0000 | 0,9694 ± 0,0015 | 0,3166 ± 0,0063 | 0,995 | 0,1972 ± 0,0000 | 0,0305 ± 0,0016 | 0,0013 ± 0,0000 | 0,200 |
| 10 | 0,9828 ± 0,0001 | 0,9494 ± 0,0016 | 0,2269 ± 0,0048 | 0,990 | 0,0620 ± 0,0000 | 0,0181 ± 0,0006 | 0,0012 ± 0,0000 | 0,100 |

| Acierto por lugar | Popularidad | Factorización por ALS | Aleatorio | Línea base del azar |
|---|---:|---:|---:|---:|
| K = 1 | 0,2017 ± 0,0007 | 0,2045 ± 0,0166 | 0,1999 ± 0,0179 | 0,2000 |
| K = 3 | 0,4756 ± 0,0093 | 0,5063 ± 0,0241 | 0,4876 ± 0,0219 | 0,4883 |
:::

**Destinos fríos (D14).** Un destino frío es uno sin ninguna interacción en entrenamiento. Entre los 606 usuarios de prueba, 205 tienen
un objetivo frío (ya contados en «Partición»), y 345 de los 1 000 destinos del catálogo son fríos. La popularidad los pone al final y
no puede acertar esos 205 usuarios mientras tenga al menos $K$ candidatos con conteo mayor que 0 (el mínimo entre usuarios es 649,
mayor que $K = 10$, así que la condición se cumple): su acierto tiene un techo de $(606 - 205)/606 = 0{,}6617$. La factorización les
da puntaje 0 a todos los destinos fríos y su posición depende del signo de los demás puntajes del usuario, así que se mide cuántas
veces entra un destino frío en la lista. El aleatorio no distingue entre destinos fríos y no fríos ([[tab:m3-frios-modelos]]).

::: tabla m3-frios-modelos
Título: Destinos fríos en prueba: techo de acierto de la popularidad y destinos fríos en las listas de cada modelo
Fuente: `results/data/m3/summary.json`, `destinos_frios` (`usuarios_prueba`, `usuarios_prueba_con_objetivo_frio`, `destinos_sin_train_en_catalogo`, `techo_acierto_popularidad`, `min_candidatos_no_frios`, `popularidad_techo_valido`) y `destinos_frios.por_modelo.<modelo>.<K>` (`frios_por_lista` y `acierto_objetivo_no_frio`; `media` y `desviacion` entre 30 semillas). «Fríos por lista» es el promedio, sobre los usuarios de prueba, de cuántos destinos fríos hay en su lista de K; «acierto con objetivo no frío» es el acierto@K de los 401 usuarios cuyo objetivo no es frío (606 − 205, cálculo del redactor). Techo de la popularidad = 0,6617 = 401/606.

| Concepto | Valor |
|---|---:|
| Usuarios de prueba | 606 |
| Usuarios de prueba con objetivo frío | 205 |
| Destinos fríos en el catálogo (de 1 000) | 345 |
| Techo de acierto de la popularidad | 0,6617 |
| Mínimo de candidatos no fríos por usuario (supera a K = 10) | 649 |

| K | Fríos por lista: popularidad | Fríos por lista: factorización | Fríos por lista: aleatorio | Acierto con objetivo no frío: popularidad | Acierto con objetivo no frío: factorización | Acierto con objetivo no frío: aleatorio |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0,000 ± 0,000 | 0,000 ± 0,000 | 0,342 ± 0,021 | 0,0000 ± 0,0000 | 0,0011 ± 0,0014 | 0,0012 ± 0,0022 |
| 3 | 0,000 ± 0,000 | 0,000 ± 0,000 | 1,039 ± 0,035 | 0,0026 ± 0,0015 | 0,0032 ± 0,0031 | 0,0033 ± 0,0033 |
| 5 | 0,000 ± 0,000 | 0,000 ± 0,000 | 1,726 ± 0,044 | 0,0050 ± 0,0000 | 0,0067 ± 0,0037 | 0,0053 ± 0,0043 |
| 10 | 0,000 ± 0,000 | 0,000 ± 0,000 | 3,429 ± 0,058 | 0,0105 ± 0,0030 | 0,0159 ± 0,0064 | 0,0101 ± 0,0058 |
:::

**Lectura de los resultados.** Todo lo que sigue es una lectura del redactor sobre las tablas.

1. **Los tres modelos quedan en torno al piso del azar.** En Recall@10 la factorización alcanza 0,0105, el aleatorio 0,0096 y el
   esperado del aleatorio es 0,0100; la popularidad, 0,0069. En NDCG@10 las medias son 0,0043, 0,0044 y 0,0028 frente a un esperado
   de 0,0046. En Recall@$K$ la factorización queda por debajo del esperado con $K = 1, 3, 5$ (por 0,0003, 0,0009 y 0,0006) y por
   encima con $K = 10$ (por 0,0005); la popularidad queda por debajo en los cuatro $K$ (por 0,0010, 0,0013, 0,0017 y 0,0031). La mayor
   diferencia con el esperado **en Recall@$K$** de la [[tab:m3-resultados-k]] es la de la popularidad con $K = 10$ (0,0069 frente a 0,0100) y equivale a
   **menos de dos aciertos** sobre 606 usuarios (0,0031 × 606 ≈ 1,9); las demás son de un acierto o menos (la popularidad con
   $K = 5$, ≈ 1,0). Como Precision@$K$ tiene techo $1/K$ y su esperado es 0,001, lo que se ve es el mismo hecho: acertar con un
   destino de 1 000 por casualidad ocurre rara vez.
2. **La desviación entre semillas no es la incertidumbre de la prueba.** Las desviaciones de la tabla recogen solo lo que cambia con
   la semilla (la inicialización de la factorización, los empates de la popularidad y el sorteo del aleatorio) con la prueba fija;
   **no** recogen que los 606 usuarios de prueba son una muestra. Para una proporción $\hat p$ medida sobre $n = 606$ usuarios, el
   error estándar es $\sqrt{\hat p (1 - \hat p)/n}$: en Recall@10 es 0,0041 para la factorización ($\hat p = 0{,}0105$, unos 6,4
   aciertos), 0,0034 para la popularidad ($\hat p = 0{,}0069$, 4,2 aciertos) y 0,0040 para el aleatorio ($\hat p = 0{,}0096$); en
   Recall@5, 0,0027, 0,0023 y 0,0028. La diferencia de dos modelos tiene error estándar $\sqrt{\text{SE}_1^2 + \text{SE}_2^2}$ (con
   la aproximación de tratarlos como independientes): para la factorización frente a la popularidad es 0,0053 en Recall@10, donde
   la diferencia es 0,0036, y 0,0036 en Recall@5, donde es 0,0011. Con unos pocos aciertos la aproximación normal es solo un orden de
   magnitud. Con estos datos **no se puede decir que algún modelo supere o quede por debajo del azar**, ni ordenar la
   factorización y la popularidad entre sí: ninguna diferencia de Recall@5 o Recall@10 entre modelos o con el esperado supera su
   error estándar. Para el acierto por lugar el error estándar con la línea base es 0,016 ($K = 1$) y 0,020 ($K = 3$), y la mayor
   diferencia con la línea base (factorización, $K = 3$, +0,0180) es de 0,9 error estándar.
3. **Lo que ya sabíamos del descriptivo.** El descriptivo mostró que las interacciones se parecen a un reparto uniforme al azar: la
   concentración no supera a la del azar y la popularidad de la fuente no se relaciona con ellas. Una popularidad calculada con
   1 066 interacciones de entrenamiento sería sobre todo ruido de muestreo, y una factorización con 858 usuarios y esas mismas
   interacciones tiene poco que aprender. Los resultados son los esperables de ese hecho, y las medias del aleatorio coinciden con su
   esperado analítico dentro de la desviación entre semillas. Esto vale para estos datos generados (D4), no para turistas reales.
4. **Por grupo, con pocos aciertos.** En «pocas» la popularidad llega a 0,0115 en Recall@10 y en «muchas» a 0,0030; la factorización,
   a 0,0115 y 0,0096; el aleatorio, a 0,0092 y 0,0099. Con 280 y 326 usuarios son de 1,0 a 3,2 aciertos medios por grupo (media ×
   usuarios del grupo), y los errores estándar de $\hat p$ van de 0,003 a 0,006, del mismo orden que las diferencias. La hipótesis
   H-M3-9 (pocas frente a muchas) se cierra en JJ-10 con todos los modelos.
5. **Los destinos fríos no explican el resultado.** La popularidad no puede acertar el tercio de usuarios con objetivo frío (techo
   0,6617), pero entre los 401 con objetivo no frío su acierto con $K = 10$ es 0,0105, muy por debajo de ese techo y del mismo orden
   que el del aleatorio en ese subgrupo (0,0101) y que el de la factorización (0,0159). La factorización no mete ningún destino frío
   en su lista; el aleatorio mete 3,43 por lista con $K = 10$, cerca de lo que daría la fracción de destinos fríos del catálogo
   (345 de 1 000).
6. **Concentración.** Frente a los máximos alcanzables de la [[tab:m3-exposiciones]], la popularidad está casi en el tope con
   $K = 1$ y $K = 5$: con $K = 5$ su Gini es 0,9949 (máximo 0,995) y su HHI 0,1972 (máximo 0,200), unos 5 destinos igualmente
   expuestos ($1/\text{HHI} \approx 5{,}1$), y con $K = 1$ el HHI es 0,9869 (máximo 1): casi todos reciben el mismo destino. Con
   $K = 3$ y $K = 10$ queda más lejos (HHI 0,2217 de 0,333 y 0,0620 de 0,100). La factorización queda en medio (con $K = 5$, Gini
   0,9694 y HHI 0,0305, unos 33 destinos equivalentes; cobertura 0,0677) y el aleatorio, que no tiene criterio, expone casi todo el
   catálogo (cobertura 0,9523 con $K = 5$; HHI 0,0013, unos 750 destinos equivalentes). Una concentración alta de la popularidad
   significa que a casi todos se les muestran los mismos destinos; que la de la factorización sea menor que la de la popularidad pero
   mucho mayor que la del aleatorio significa que sus listas se parecen entre sí mucho más que las de un recomendador sin criterio,
   aunque su acierto no sea mayor que el del azar. Qué implica eso para el negocio es la pregunta 2 y se responde en JJ-6.
7. **Costo.** La factorización cuesta 7 432 parámetros (6 052 con datos) y 33,86 s en total (17,16 s de búsqueda y 16,70 s de 30
   corridas), frente a 1 000 parámetros y 5,65 s de la popularidad. El único modelo con una configuración elegida con datos es la
   factorización, y su valor de validación (NDCG@5 = 0,01015) es mayor que su NDCG@5 en prueba (0,0024 ± 0,0015). Las dos cifras no
   son comparables sin cautela: la de validación es de **una sola semilla** y de **otra población** (los 326 usuarios de «muchas»),
   y es el máximo de 20 ensayos, así que es optimista por la propia selección; la de prueba es el promedio de 30 semillas sobre 606
   usuarios.

Estos resultados son solo de los tres modelos de referencia: no incluyen la red ni cierran ninguna de las hipótesis H-M3-7 a H-M3-9.

<!-- revisar: Juan José — las multiplicaciones (media × 606; media × 280 o 326; 606 − 205 = 401) y los errores estándar son cálculo del redactor con sqrt(p(1−p)/n) aplicada a la media entre semillas: Recall@10 factorización 0,0041, popularidad 0,0034, aleatorio 0,0040; Recall@5 0,0027, 0,0023, 0,0028; por lugar 0,0162 (K=1) y 0,0203 (K=3), con p = línea base; por grupo (Recall@10) 0,0064, 0,0064 y 0,0057 en «pocas» y 0,0030, 0,0054 y 0,0055 en «muchas». El error estándar de la diferencia factorización − popularidad (0,0053 en Recall@10; 0,0036 en Recall@5) supone independencia entre los dos modelos, aunque se evalúan sobre los mismos usuarios. Ninguno sale de un JSON. -->
<!-- revisar: Juan José — «1/HHI ≈ 5,1, 33 y 750 destinos equivalentes» (número equivalente de destinos igualmente expuestos) es una lectura del redactor, definición suya, no del Spec ni del enunciado. -->
<!-- revisar: Juan José — «cerca de lo que daría la fracción de destinos fríos» (345/1 000 × 10 = 3,45) es un cálculo aproximado del redactor: los candidatos excluyen el historial conocido y algunos destinos de validación también son fríos. -->
<!-- revisar: Juan José — «no se puede decir que algún modelo supere o quede por debajo del azar» y «el valor de validación es optimista» son interpretación del redactor; el segundo se apoya en que la configuración es el máximo de 20 ensayos (hpo_ensayos.json) y en que la validación es de una semilla y de otra población; no se afirma que haya sobreajuste. -->
<!-- revisar: Juan José — la lectura 3 (los resultados son los esperables del descriptivo) relaciona dos resultados; es interpretación del redactor, no está contrastada con una corrida sobre datos con estructura. También lo es que las listas de la factorización «se parezcan entre sí mucho más» que las de un recomendador sin criterio: no se midió la similitud entre listas, solo la concentración de las exposiciones. -->
<!-- revisar: Juan José — las comparaciones de la popularidad con el máximo alcanzable (casi en el tope con K = 1 y 5, más lejos con K = 3 y 10) son lectura del redactor sobre las cotas 1 − K/n y 1/K. -->
