## M1 — Demanda de pasajeros: datos y análisis descriptivo

<!-- pendiente: Daniel y Camila (DA-4, CA-4) -->

### Análisis descriptivo

#### Ficha del conjunto

<!-- borrador DA-9a (redactor-tecnico, Sonnet) para Daniel; las demás subsecciones son de Camila (CA-4). -->

El conjunto de M1 es el que pide el enunciado: «Operación de pasajeros y despacho de vehículos en la modalidad de transporte de
pasajeros por carretera», publicado por la Superintendencia de Transporte en el portal de datos abiertos del Estado colombiano
(datos.gov.co, identificador `eh75-8ah6`) [@supertransporte2026]. La fuente lo describe como los datos de movilidad de pasajeros
y de despachos de vehículos desde las terminales terrestres de pasajeros habilitadas u homologadas del país, y lo licencia con
Creative Commons Atribución-CompartirIgual 4.0 (CC BY-SA 4.0), que exige citar la fuente y compartir igual lo derivado
(`docs/investigacion/DA-2_fuentes_m1.md` §1.1). La consulta se hizo el 24 de noviembre de 2026; según los metadatos de la
fuente, sus filas se actualizaron por última vez el 3 de mayo de 2026 (`results/data/m1/eda/ficha.json`, campos `cita` y
`fecha_descarga`). Los municipios se identifican con la codificación DIVIPOLA del DANE, tomada de la publicación del propio DANE
en datos.gov.co (identificador `gdxc-w37w`, «actualización a corte 30 diciembre 2024», 1 122 filas, licencia CC BY-SA 4.0)
[@dane2024] (`data/fuentes.md`, sección DIVIPOLA).

**Tamaño del conjunto completo.** Tiene **49 202 812 registros y 10 variables**, con fechas de despacho desde el 2019-08-04 hasta
el 2026-04-07 una vez excluidas tres fechas imposibles (años 2202, 2222 y 6202) (`data/processed/m1/resumen_datos.json`,
bloque `conjunto_crudo`; cifras medidas con SoQL el 2026-11-24, `docs/investigacion/DA-2_fuentes_m1.md` §1.4). Cada registro es
un agregado por terminal, clase de vehículo, nivel de servicio, ruta, fecha, hora y tipo de despacho, no un viaje individual
(`ficha.json`, campo `unidad_de_observacion`).

**Periodo usado: 2021-01-01 a 2023-12-31** (36 meses continuos, 1 095 días). La fuente cubre más años, pero el volumen real es
muy desigual (`DA-2_fuentes_m1.md` §1.4):

- 2019 tiene 77 filas y 2020 tiene 14 265, frente a 9 959 766 en 2021, 12 018 845 en 2022 y 12 306 865 en 2023. Por eso
  **la caída de la pandemia (2020) no está en los datos**, y la hipótesis sobre la recuperación posterior a la pandemia se
  analiza como tendencia 2021–2023, no como un antes y un después.
- 2024 casi no tiene datos: 106 498 filas en todo el año. Enero de 2024 no tiene ninguna y de febrero a octubre hay entre 1 704
  y 3 873 filas por mes, frente a 801 799 en enero de 2021 o 1 106 919 en diciembre de 2022.
- Hay datos abundantes de nuevo en 2025 (11 667 035 filas) y 2026 (hasta el 7 de abril), pero quedan separados de 2021–2023 por el
  hueco de 2024, y el informe de fuentes cuenta solo 15 meses útiles allí (enero de 2025 a marzo de 2026), contra los 36 de
  2021–2023 (`DA-2_fuentes_m1.md` §5). Daniel decidió el periodo 2021–2023 el 24 de noviembre (núcleo §5.1 del Spec).

<!-- revisar: Daniel — el 'por qué' del periodo es una decisión tuya; confirma que la redacción refleja tu criterio. -->

**Rutas analizadas.** Son seis series, tres pares de ida y regreso, con códigos DIVIPOLA y nombres tomados del DANE
(`data/processed/m1/rutas.yaml`, construido con `divipola.csv`). Una ruta es un sentido: Bogotá–Cali y Cali–Bogotá son dos series
distintas ([[tab:m1-rutas]]).

::: tabla m1-rutas
Título: Las seis rutas dirigidas de M1 y sus registros crudos, 2021–2023
Fuente: `data/processed/m1/rutas.yaml` (códigos, nombres y tipo de corredor) y `results/data/m1/eda/ficha.json`, `conteos.registros_crudos_por_ruta` (registros crudos, consulta del 2026-11-24).

| Ruta (`ruta_id`) | Origen (DIVIPOLA, nombre DANE) | Destino (DIVIPOLA, nombre DANE) | Regreso | Corredor | Registros crudos |
|---|---|---|---|---|---:|
| 11001-76001 | 11001, BOGOTÁ, D.C. | 76001, SANTIAGO DE CALI (Valle del Cauca) | 76001-11001 | largo, el de mayor volumen | 297 559 |
| 76001-11001 | 76001, SANTIAGO DE CALI | 11001, BOGOTÁ, D.C. | 11001-76001 | largo, el de mayor volumen | 201 801 |
| 11001-15759 | 11001, BOGOTÁ, D.C. | 15759, SOGAMOSO (Boyacá) | 15759-11001 | medio | 362 258 |
| 15759-11001 | 15759, SOGAMOSO | 11001, BOGOTÁ, D.C. | 11001-15759 | medio | 258 171 |
| 52001-52356 | 52001, PASTO (Nariño) | 52356, IPIALES (Nariño) | 52356-52001 | regional y de frontera, fuera de Bogotá | 119 609 |
| 52356-52001 | 52356, IPIALES | 52001, PASTO | 52001-52356 | regional y de frontera, fuera de Bogotá | 133 348 |
:::

**Criterio de selección.** Se ordenaron los pares de municipios por el mínimo de los dos sentidos, usando una muestra de 36
miércoles (uno por mes entre 2021 y 2023), y se exigió que ambos sentidos tuvieran registros en 35 o 36 de esos 36 días
(`data/processed/m1/rutas.yaml`, campo `criterios_seleccion`; `data/fuentes.md`, «Consulta del ranking de rutas»). La muestra
produjo 2 099 pares dirigidos (origen, destino). De ese orden se escogieron tres pares que representan tres situaciones:
un corredor largo y de mayor volumen, uno medio con Bogotá y uno regional y de frontera fuera de Bogotá. El criterio mide
completitud de la serie y volumen, no el comportamiento de la demanda en el tiempo.

<!-- revisar: Daniel — confirma que 'tres situaciones' resume bien por qué escogiste estos tres pares (daniel.md §3.2). -->

**Cuatro conteos que no son comparables entre sí.** Para no confundir «registros» con «filas», se reportan cuatro números con
su definición ([[tab:m1-conteos]]).

::: tabla m1-conteos
Título: Los cuatro conteos de registros y filas de M1
Fuente: `data/processed/m1/resumen_datos.json`, bloque `conteos_de_registros` (definiciones) y `results/data/m1/eda/ficha.json`, bloque `conteos`; `data/processed/m1/conteo_registros.csv` para los registros crudos de las rutas (`scripts/descargar_m1.py contar`, 2026-11-24).

| Conteo | Valor | Qué es |
|---|---:|---|
| Registros del conjunto completo | 49 202 812 | Registros de la fuente, de todas las rutas y fechas, medidos con SoQL (`count(*)`) |
| Registros crudos de las 6 rutas | 1 372 746 | Registros de la fuente, sin agrupar, de las rutas elegidas entre 2021-01-01 y 2023-12-31 |
| Filas agregadas descargadas | 25 248 | Filas que devolvió el servidor al agrupar por ruta, fecha, `tipo_despacho` y `clase_vehiculo` (base de la tabla de detalle) |
| Filas de la serie | 6 570 | Una por ruta dirigida y día: 6 rutas × 1 095 días (`demanda_diaria.parquet`) |
:::

La fuente es demasiado grande para bajarla completa, así que la agregación se hizo en el servidor con SoQL (`group by`) y solo se
descargaron las seis rutas (`data/fuentes.md`). Cada descarga mensual queda registrada con su SHA-256 (36 archivos
`AAAA-MM.parquet`, en `ficha.json`, campo `sha256`); el SHA-256 de `divipola.csv` es
`abc2608f58363cfadfdf91a56a53b944d2aa7784e200aa742c8171a2733da081` (`data/fuentes.md`). En total las seis series suman
16 218 405 pasajeros en el periodo (`ficha.json`, `conteos.pasajeros_totales`).

#### Diccionario y calidad

<!-- borrador DA-9a (redactor-tecnico, Sonnet) para Daniel. -->

**Variables y su significado en la fuente.** El conjunto tiene 10 variables. Su descripción es la que publica la
Superintendencia en el diccionario del conjunto (`columns[]` de los metadatos de la API, copia en
`data/raw/m1/views_eh75-8ah6.json`), reproducida sin modificar en `results/data/m1/eda/diccionario.json` ([[tab:m1-diccionario]]).
Todas las variables llegan como texto en el JSON de la API, incluidas las numéricas (`DA-2_fuentes_m1.md` §1.3).

::: tabla m1-diccionario
Título: Variables del conjunto `eh75-8ah6` con su descripción literal de la fuente
Fuente: `results/data/m1/eda/diccionario.json`, campo `variables` (descripción literal de los metadatos de la API de datos.gov.co, consulta del 2026-11-24).

| Variable (campo API) | Tipo (Socrata) | Descripción literal de la fuente |
|---|---|---|
| `terminal` | texto | «Corresponde a la sede de la terminal desde donde se realizan y reportan los despachos» |
| `clase_vehiculo` | texto | «Identificador numérico dado por el RUNT» |
| `nivel_servicio` | texto | «1 BASICO - CORRIENTE 2 LUJO 3 CORRIENTE DIRECTO» |
| `municipio_origen_ruta` | texto | «Código Divipola del municipio de origen de la ruta» |
| `municipio_destino_ruta` | texto | «Código Divipola del departamento de destino de la ruta» |
| `fecha_despacho` | fecha | «Fecha de realización del despacho. date (DD/MM/YYYY)» |
| `hora_despacho` | texto | «Hora 24H (hh)» |
| `tipo_despacho` | texto | «1 = Si el despacho de la ruta es en origen, y 2 = Si el despacho de la ruta es en transito» |
| `despachos` | número | «Número vehículos de transporte de pasajeros por carretera que salen desde la terminal» |
| `pasajeros` | número | «Número de pasajeros que abordaron viaje desde la terminal de transporte. Las terminales en tránsito sólo deben reportar los pasajeros que abordaron el vehículo en dicha terminal.» |
:::

**Inconsistencias entre el diccionario y los datos.** El enunciado pide documentarlas. Las filas 1 a 10 salen de comparar el
diccionario con consultas al conjunto completo (`diccionario.json`, campo `inconsistencias_informe`; informe de fuentes §1.7);
las filas 11 a 14 resumen las que aparecen en las rutas descargadas (`diccionario.json`, campo `inconsistencias_nuevas`)
([[tab:m1-inconsistencias]]).

::: tabla m1-inconsistencias
Título: Inconsistencias entre el diccionario y los datos
Fuente: `results/data/m1/eda/diccionario.json` (`inconsistencias_informe` e `inconsistencias_nuevas`); `docs/investigacion/DA-2_fuentes_m1.md` §1.7. Filas 1–10: conjunto completo, consulta del 2026-11-24. Filas 11–14: seis rutas, 2021–2023.

| # | El diccionario dice | Los datos muestran |
|---|---|---|
| 1 | `clase_vehiculo`: «Identificador numérico dado por el RUNT» | Texto: BUS, BUSETA, MICROBUS, CAMIONETA, AUTOMOVIL, CAMPERO |
| 2 | `nivel_servicio`: «1 BASICO - CORRIENTE 2 LUJO 3 CORRIENTE DIRECTO» | Texto: BASICO, LUJO y PREFERENCIAL DE LUJO (5 478 filas), valor que el diccionario no lista; no aparece CORRIENTE DIRECTO |
| 3 | `tipo_despacho`: «1 = ... origen, y 2 = ... en transito» | Texto: ORIGEN, TRANSITO |
| 4 | `municipio_destino_ruta`: «Código Divipola del departamento de destino de la ruta» | Códigos de municipio de 5 dígitos (p. ej. `76306`, Ginebra), no de departamento (2 dígitos) |
| 5 | `fecha_despacho`: «date (DD/MM/YYYY)» | Marca ISO, p. ej. `2022-06-14T00:00:00.000` |
| 6 | Descripción: «Datos disponibles desde 1 de enero de 2021» | Hay 77 filas de 2019 y 14 265 de 2020, desde 2019-08-04 |
| 7 | Frecuencia de actualización «Mensual» | La última fecha de despacho real es 2026-04-07 y la última actualización de filas fue el 2026-05-03; a 2026-11-24 el conjunto lleva unos 7 meses sin cargar datos (no se verificó si hay un corte nuevo sin publicar) |
| 8 | Sin mención de fechas inválidas | 3 filas con fecha en los años 2202, 2222 y 6202 |
| 9 | Sin mención de huecos | 2024 casi vacío (enero sin filas; de febrero a octubre, 0,3 % del volumen normal); diciembre de 2025 con cerca del 1 % del volumen normal |
| 10 | `pasajeros` y `despachos` descritos como «Número» | 13,4 % de las filas tienen `pasajeros = 0` pese a `despachos ≥ 1` |
| 11 | `pasajeros`: «Número de pasajeros que abordaron viaje desde la terminal»; `despachos`: «Número vehículos ... que salen desde la terminal» | Ruta 11001-76001, 2021-05-03: 1 despacho y 0 pasajeros en todo el día. Ruta 15759-11001, 2023-05-21: 214 despachos y 0 pasajeros en todo el día |
| 12 | `pasajeros`: «Las terminales en tránsito sólo deben reportar los pasajeros que abordaron el vehículo en dicha terminal» | En las cuatro rutas con Bogotá, la mayoría de los pasajeros se reporta en terminales de tránsito, no en la de origen (p. ej. 11001-76001: 2 517 599 en tránsito frente a 1 333 474 en origen). No hay identificador de vehículo para saber si un mismo vehículo cuenta como despacho en el origen y en cada terminal de tránsito |
| 13 | `tipo_despacho` y `clase_vehiculo`: sin mención de cambios de categoría o de reporte entre años | Ruta 11001-15759: la participación de ORIGEN en los pasajeros baja de 47,1 % (2021) a 39,2 % (2022) y 27,3 % (2023). Ruta 11001-76001: BUS pasa de 85,6 % a 89,8 % y 100,0 %, y MICROBUS de 11,9 % a 8,7 % y 0,0 %. Puede ser un cambio de reporte o de la operación: no verificado |
| 14 | Frecuencia «Mensual», sin mención de huecos | Días sin ningún registro en el periodo, todos en mayo de 2021: 11001-15759, 3; 11001-76001, 26; 15759-11001, 4; 52001-52356, 9; 52356-52001, 14; 76001-11001, 26 |
:::

La fila 7 es una observación sobre la actualización de la fuente, no sobre la calidad de las series de 2021–2023 que se usan. Las
filas 11 y 12 importan para el modelado: la segunda implica que `pasajeros` no mide solo a quien aborda en la terminal de origen,
que es lo que supone el enunciado en su lista de limitaciones, y la primera, que existen días con despachos y ningún pasajero
reportado.

<!-- revisar: Daniel — la lectura de las filas 7, 11 y 12 como 'importan para el modelado' es una interpretación del redactor; valida o ajusta. -->

**Cómo se agregan los registros.** Para cada ruta dirigida $r$, día $t$ y clave
$k = (\text{tipo\_despacho},\ \text{clase\_vehiculo})$, el servidor suma los registros crudos y se obtiene el detalle $P_{r,t,k}$
(pasajeros) y $D_{r,t,k}$ (despachos). La serie diaria es su suma sobre $k$, es decir, **origen más tránsito**
(decisión de Daniel del 24 de noviembre, núcleo §5.1):

$$
P_{r,t} = \sum_{k} P_{r,t,k}, \qquad D_{r,t} = \sum_{k} D_{r,t,k}.
$$

La fuente no tiene filas con `despachos = 0`, con `pasajeros` nulo ni con valores negativos (`DA-2_fuentes_m1.md` §1.4).
La proporción de pasajeros reportados en tránsito varía mucho entre rutas: va de 0,93 % (52001-52356) y 2,63 % (52356-52001) a
56,73 % (76001-11001), 59,72 % (15759-11001), 65,36 % (11001-15759) y 65,37 % (11001-76001) (`resumen_datos.json`,
`por_ruta[*].pct_pasajeros_transito`). Para contar vehículos y despachos de flota se usan solo los despachos de ORIGEN del detalle,
porque los de tránsito cuentan el mismo vehículo en cada terminal (núcleo §5.1, «Flota»).

**Días sin registro.** La serie se arma con una rejilla completa de fechas para cada ruta, sin huecos: $t$ recorre todos los días
de 2021-01-01 a 2023-12-31. Si un día no tiene ninguna fila en la fuente para esa ruta, se conserva la fila con
$P_{r,t} = D_{r,t} = 0$ y la marca `sin_registro = true`. Ese 0 es una **imputación, no una observación**: cada modelo decide si
lo excluye de la pérdida, lo interpola con información pasada o lo trata como cero, y nunca se marca como anómalo
(`resumen_datos.json`, campo `regla_sin_registro`). Hay 82 días así entre las seis series, todos en mayo de 2021
(`demanda_diaria.parquet`, `resumen_datos.json`): mayo de 2021 está casi vacío en la fuente (por ejemplo, la ruta 11001-76001
suma 261 pasajeros en todo el mes, según `demanda_diaria.parquet`). Por eso las series se conservan completas para el análisis
descriptivo y los modelos entrenan desde el 2021-06-01 (núcleo §5.1, clave `datos.inicio_entrenamiento`).

**Datos anómalos.** Se usan cuatro reglas, definidas en `src/m1_demanda/datos.py` y parametrizadas en `configs/m1/datos.yaml`.
La primera es la que pide el enunciado (despachos con cero pasajeros):

$$
\text{R1}_{r,t} \;=\; \neg\,\text{sin\_registro}_{r,t} \;\wedge\; D_{r,t} > 0 \;\wedge\; P_{r,t} = 0 .
$$

Las otras tres son atípicos robustos de la misma ruta, calculados solo con los días con registro. Para una serie transformada
$y_t$ (más abajo) se define la mediana móvil centrada, el residuo y una escala robusta:

$$
m_t = \operatorname{mediana}\{\, y_s : |s - t| \le h,\ s \text{ con registro} \,\}, \qquad h = \tfrac{\text{ventana} - 1}{2},
$$

$$
e_t = y_t - m_t, \qquad \hat\sigma_r = c \cdot \operatorname{mediana}_t \,\bigl|\, e_t - \operatorname{mediana}(e) \,\bigr|, \qquad c = 1{,}4826 ,
$$

con al menos `min_periodos` valores en la ventana para calcular $m_t$. $\hat\sigma_r$ es el MAD escalado de la ruta. Si el MAD es
cero o la ruta no tiene días con registro, la regla queda desactivada para esa ruta (comentario en `datos.py`). Las reglas son:

- **R2, `caida_robusta`**: $y_t = \log(1 + P_{r,t})$; marca si $e_t < -u\,\hat\sigma_r$.
- **R3, `pico_robusto`**: $y_t = \log(1 + P_{r,t})$; marca si $e_t > +u\,\hat\sigma_r$.
- **R4, `pasajeros_por_despacho_bajo`**: $y_t = \log\dfrac{1 + P_{r,t}}{1 + D_{r,t}}$; marca si $e_t < -u\,\hat\sigma_r$. Compara la
  ruta consigo misma: no usa ninguna capacidad de vehículo.

Un día es anómalo si alguna regla activa lo marca: $\text{anomalo}_{r,t} = \text{R1} \vee \text{R2} \vee \text{R3} \vee \text{R4}$.
Los parámetros están en `resumen_datos.json` (`reglas_anomalos`): ventana de 29 días ($h = 14$), `min_periodos` = 15, $c = 1{,}4826$,
$u = 10$ para R2 y R3 y $u = 8$ para R4. La [[tab:m1-marcados]] muestra cuántos días marca cada regla en cada ruta.

::: tabla m1-marcados
Título: Días sin registro y días anómalos por ruta y regla, 2021-01-01 a 2023-12-31
Fuente: `data/processed/m1/resumen_datos.json`, `por_ruta[*].dias_sin_registro`, `dias_anomalos` y `dias_anomalos_por_regla`. «Anómalos» cuenta días distintos (unión de reglas); una columna por regla puede sumar más porque un día puede cumplir varias.

| Ruta | Días | Sin registro | Anómalos (unión) | R1 | R2 | R3 | R4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 11001-76001 | 1 095 | 26 | 5 | 1 | 5 | 0 | 1 |
| 76001-11001 | 1 095 | 26 | 5 | 0 | 5 | 0 | 1 |
| 11001-15759 | 1 095 | 3 | 1 | 0 | 1 | 0 | 0 |
| 15759-11001 | 1 095 | 4 | 3 | 1 | 3 | 0 | 2 |
| 52001-52356 | 1 095 | 9 | 10 | 0 | 10 | 0 | 2 |
| 52356-52001 | 1 095 | 14 | 5 | 0 | 5 | 0 | 1 |
| **Total** | **6 570** | **82** | **29** | **2** | **29** | **0** | **7** |
:::

Las marcas son pocas: 29 días de 6 570 (`ficha.json`, `conteos.dias_anomalos`). Los dos casos de R1 son los de la fila 11 de la
[[tab:m1-inconsistencias]]. De los 29 días marcados, 24 caen entre el 2021-04-28 y el 2021-06-01, alrededor del hueco de mayo de
2021; los otros cinco son el 2021-01-01 (rutas 52001-52356 y 52356-52001), el 2023-01-01 (52356-52001) y el 2023-05-21 y 2023-05-22
(15759-11001) (`demanda_diaria.parquet`, columna `anomalo`; `marcas_anomalos.parquet` dice qué regla marcó cada día). Nada se
borra: los días anómalos y sin registro siguen en la serie con su marca.

**Las marcas miran el futuro y no entran a los modelos.** Las reglas R2 a R4 usan una ventana centrada y un MAD calculado con la
serie completa de la ruta, es decir, con información posterior al día marcado. Por eso `anomalo` y `sin_registro` son solo
descriptivas: no pueden usarse como variable de entrada de ningún modelo (regla 0.9 del Spec: ninguna variable de M1 puede depender
de información que no se conozca 30 días antes), y a lo sumo sirven para decidir qué días excluir de la pérdida. La auditoría de
fugas de M1 encontró que filtrar el entrenamiento con las marcas publicadas sería una fuga pequeña pero real, que con los umbrales
actuales resulta inocua (`docs/investigacion/DA-3_auditoria_fugas.md`, riesgo 2); las reglas contra fuga del arnés están en el
núcleo §5.3.

#### Variable objetivo

<!-- pendiente: Daniel y Camila (DA-4, CA-4) -->

#### Estructura y heterogeneidad

<!-- pendiente: Daniel y Camila (DA-4, CA-4) -->

#### Hipótesis explícitas

<!-- pendiente: Daniel y Camila (DA-4, CA-4) -->

#### Implicaciones para el modelado

<!-- pendiente: Daniel y Camila (DA-4, CA-4) -->

#### Veredicto de las hipótesis

<!-- pendiente: Daniel y Camila (DA-4, CA-4) -->
