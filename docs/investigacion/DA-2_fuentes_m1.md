# DA-2 (investigación) — Fuentes del Módulo 1: conjunto de datos.gov.co y DIVIPOLA

Fecha de consulta de todo lo de este informe: **2026-11-24**. Agente: investigador-fuentes (Sonnet). Prompt: `alucinaciones/prompts/DA-2a.md`.
Todas las cifras "medidas" salen de consultas SoQL contra la API pública (sin token) ejecutadas hoy; las que no se pudieron medir
están marcadas `TODO(dato-faltante)`. No se descargó el conjunto completo.

## 1. Conjunto de datos de M1

### 1.1 Identificación

| Dato | Valor (fuente: `/api/views/eh75-8ah6.json`, abierta hoy) |
|---|---|
| Nombre | Operación de pasajeros y despacho de vehículos en la modalidad de transporte de pasajeros por carretera |
| Identificador Socrata | `eh75-8ah6` |
| Página | https://www.datos.gov.co/d/eh75-8ah6 (también `https://www.datos.gov.co/resource/eh75-8ah6`) |
| API de datos | https://www.datos.gov.co/resource/eh75-8ah6.json |
| Metadatos | https://www.datos.gov.co/api/views/eh75-8ah6.json (copia guardada en `data/raw/m1/views_eh75-8ah6.json`) |
| Entidad que publica | «Superintendencia de Transporte - SUPERTRANSPORTE, Bogotá D.C.» (contacto: datosabiertos@supertransporte.gov.co) |
| Licencia | `CC_40_BY_SA`: «Creative Commons Attribution \| Share Alike 4.0 International» (http://creativecommons.org/licenses/by-sa/4.0/legalcode) |
| Frecuencia de actualización (campo de metadatos) | «Mensual» |
| Cobertura geográfica | «Nacional» |
| Categoría / etiquetas | Transporte / terminales, pasajeros, supertransporte, tppc |
| Procedencia | `official` |
| Creado / publicado | 2021-03-16 / 2021-03-19 |
| Última actualización de **filas** (`rowsUpdatedAt`) | 2026-05-03 06:06:51 UTC |
| Última modificación de la vista (`viewLastModified`) | 2026-05-18 18:47:25 UTC |
| Descripción literal | «Corresponde a los datos de movilidad de pasajeros y despachos de vehículos desde las terminales terrestres de pasajeros habilitadas y/o homologadas del país,  presentados en el tablero de control publicado en el portal logístico de Colombia del Ministerio de Transporte.  Datos disponibles desde 1 de enero de 2021.» |

### 1.2 ¿Hay más de un conjunto con nombre parecido?
Búsqueda en el catálogo de datos.gov.co (`api.us.socrata.com/api/catalog/v1?domains=www.datos.gov.co&q=...`, hoy). Solo **uno** coincide con
el nombre del enunciado. Otros con tema cercano pero **distintos**:

| Id | Nombre | Entidad | Por qué no es |
|---|---|---|---|
| `eh75-8ah6` | Operación de pasajeros y despacho de vehículos en la modalidad de transporte de pasajeros por carretera | Supertransporte | **Es el del enunciado** (nombre idéntico, publicador idéntico) |
| `vn9u-yhwq` | Registro Nacional de Despachos de Carga por Carretera | MinTransporte | Carga, no pasajeros |
| `aesn-q83n`, `a45t-7a3r`, `pfsr-mdyi` | Salidas y llegadas de vehículos y pasajeros / de vehículos, Terminales de Medellín | Terminales de Transportes de Medellín | Una sola terminal |
| `iktk-yz4g` | Histórico Estadísticas Operativas | Terminal de Pereira | Una sola terminal |
| `7atu-2b28` | Tráfico de pasajeros y carga férreo en Colombia | Supertransporte | Ferrocarril |

### 1.3 Diccionario (copiado de `columns[]` de `/api/views/eh75-8ah6.json`; ejemplos de `data/raw/m1/muestra_1000.json`)

Son **10 columnas**. Todas llegan como cadena de texto en el JSON de la API, incluidas las numéricas.

| Campo API | Nombre en el portal | Tipo (Socrata) | Descripción literal de la fuente | Ejemplo en la muestra |
|---|---|---|---|---|
| `terminal` | TERMINAL | text | «Corresponde a la sede de la terminal desde donde se realizan y reportan los despachos» | `T.T. DE CALI` |
| `clase_vehiculo` | CLASE_VEHICULO | text | «Identificador numérico dado por el RUNT» | `BUSETA` |
| `nivel_servicio` | NIVEL_SERVICIO | text | «1 BASICO - CORRIENTE 2 LUJO 3 CORRIENTE DIRECTO» | `BASICO` |
| `municipio_origen_ruta` | MUNICIPIO_ORIGEN_RUTA | text | «Código Divipola del municipio de origen de la ruta» | `76001` |
| `municipio_destino_ruta` | MUNICIPIO_DESTINO_RUTA | text | «Código Divipola del departamento de destino de la ruta» | `76306` |
| `fecha_despacho` | FECHA_DESPACHO | calendar_date | «Fecha de realización del despacho. date (DD/MM/YYYY)» | `2022-06-14T00:00:00.000` |
| `hora_despacho` | HORA_DESPACHO | text | «Hora 24H (hh)» | `13` |
| `tipo_despacho` | TIPO_DESPACHO | text | «1 = Si el despacho de la ruta es en origen, y 2 = Si el despacho de la ruta es en transito» | `ORIGEN` |
| `despachos` | DESPACHOS | number | «Número vehículos de transporte de pasajeros por carretera que salen desde la terminal» | `1` |
| `pasajeros` | PASAJEROS | number | «Número de pasajeros que abordaron viaje desde la terminal de transporte. Las terminales en tránsito sólo deben reportar los pasajeros que abordaron el vehículo en dicha terminal.» | `4` |

No existe columna de identificador de fila (`rowIdentifierColumnId = null`) ni código DIVIPOLA de la terminal (solo su nombre).

### 1.4 Conteos medidos (hoy)

| Medida | Valor | Consulta |
|---|---|---|
| Filas | **49 202 812** | `$select=count(*)` |
| Variables | 10 | metadatos |
| Fecha mínima / máxima **bruta** | 2019-08-04 / **6202-04-13** | `min/max(fecha_despacho)` |
| Fecha mínima / máxima excluyendo 3 fechas absurdas | 2019-08-04 (mín. con `>= 2020-01-01`: 2020-01-01) / **2026-04-07** | `where fecha_despacho < "2100-01-01"` |
| Suma de pasajeros / de despachos | 420 494 779 / 50 839 100 | `sum()` |
| `pasajeros` mín / máx | 0 / 640 | `min/max` |
| `despachos` mín / máx | 1 / 20 | `min/max` |
| Filas con `pasajeros = 0` | 6 576 784 (13,4 %) | `where pasajeros=0` (149 s) |
| Filas con `despachos = 0`, con `pasajeros` nulo, o con negativos | 0, 0, 0 | `count(*) where ...` |
| Terminales distintas | 52 | `group by terminal` |
| `clase_vehiculo` | BUS 17 791 956; MICROBUS 17 751 532; BUSETA 5 568 838; CAMIONETA 5 542 894; AUTOMOVIL 1 680 520; CAMPERO 867 072 | `group by` |
| `nivel_servicio` | LUJO 30 643 075; BASICO 18 554 259; PREFERENCIAL DE LUJO 5 478 | `group by` |
| `tipo_despacho` | ORIGEN 39 124 098; TRANSITO 10 078 714 (20,5 %) | `group by` |
| Pares origen–destino distintos | `TODO(dato-faltante)`: `count(distinct ...)` y `group by origen,destino` sobre todo el conjunto (y sobre un mes) superan 280 s y caducan | ver §3 |
| Municipios de origen / destino distintos | `TODO(dato-faltante)`; en la muestra de 1 000 filas: 72 orígenes y 271 destinos (no es representativa) | muestra |

Filas por año (`date_extract_y`): 2019: 77 · 2020: 14 265 · 2021: 9 959 766 · 2022: 12 018 845 · 2023: 12 306 865 · **2024: 106 498** ·
2025: 11 667 035 · 2026 (hasta 7-abr): 3 129 458 · 2202: 1 · 2222: 1 · 6202: 1 (suma = 49 202 812).

Filas por mes (selección; `date_trunc_ym`): ene-2021 801 799 · dic-2021 1 023 317 · dic-2022 1 106 919 · dic-2023 1 071 531 ·
**ene-2024: sin filas** · feb–oct-2024: 1 704–3 873 al mes · nov-2024: 28 903 · dic-2024: 47 679 · ene-2025: 1 120 212 ·
nov-2025: 1 013 617 · **dic-2025: 13 286** · ene-2026: 1 082 851 · mar-2026: 1 006 152 · abr-2026: 97 163 (parcial).
Antes de 2021 hay muy pocas filas: 2019 (77), 2020 (14 265; entre 1 y 8 344 filas por mes; sin filas en may-2020).

### 1.5 Códigos de municipio, terminal, clase, pasajeros y despachos
- **Códigos de municipio:** sí. `municipio_origen_ruta` y `municipio_destino_ruta` traen 5 dígitos en las 1 000 filas de la muestra
  (longitud 5 en todas) y **todos los códigos de las 1 000 filas de la muestra están presentes en DIVIPOLA** (tabla de §2). Falta validar
  sobre el conjunto completo (`TODO(dato-faltante)`, DA-3).
- **Terminal de origen:** es un **nombre** (`T.T. DE CALI`), no un código. No hay código DIVIPOLA de la terminal; el municipio de la terminal
  solo se puede inferir del nombre (a verificar en DA-3).
- **Clase de vehículo:** texto (BUS, BUSETA, MICROBUS, CAMIONETA, AUTOMOVIL, CAMPERO), no el «identificador numérico» del diccionario.
- **Pasajeros y despachos:** enteros no negativos en forma de texto; a nivel de fila `despachos` va de 1 a 20 y `pasajeros` de 0 a 640.
  Cada fila es un agregado por (terminal, clase, nivel, ruta, fecha, hora, tipo), no un viaje individual.

### 1.6 Muestra
`data/raw/m1/muestra_1000.json` (1 000 filas, `GET /resource/eh75-8ah6.json?$limit=1000`, sin `$order`; SHA-256
`413291ccb64f2de82192ef8359161874d48c80a5aa68167ae27355618dd6d8ac`). **Aviso:** no es aleatoria ni ordenada por fecha: abarca
2022-01-03 a 2023-08-28; sirve para ver el formato, no para estimar proporciones (en ella `pasajeros = 0` es 17,9 % frente a 13,4 % del total;
media de pasajeros por fila 8,65 frente a 8,27 del total). Contiene las 10 columnas en las 1 000 filas.
También se guardó `data/raw/m1/divipola_gdxc-w37w.json` (SHA-256 `1028ab04c10a08fa860dd89e621de1eb9246710a56102c915f0988ae9e10d63d`).

### 1.7 Inconsistencias diccionario vs. datos (para el apartado de datos del enunciado)

| # | Diccionario dice | Datos muestran |
|---|---|---|
| 1 | `clase_vehiculo`: «Identificador numérico dado por el RUNT» | Texto: BUS, BUSETA, MICROBUS, CAMIONETA, AUTOMOVIL, CAMPERO |
| 2 | `nivel_servicio`: «1 BASICO - CORRIENTE 2 LUJO 3 CORRIENTE DIRECTO» | Texto: BASICO, LUJO, PREFERENCIAL DE LUJO (5 478 filas, valor que el diccionario no lista); no aparece CORRIENTE DIRECTO como categoría |
| 3 | `tipo_despacho`: «1 = ... origen, y 2 = ... en transito» | Texto: ORIGEN, TRANSITO |
| 4 | `municipio_destino_ruta`: «Código Divipola del departamento de destino de la ruta» | Códigos de **municipio** de 5 dígitos (p. ej. `76306`, Ginebra), no de departamento (2 dígitos) |
| 5 | `fecha_despacho`: «date (DD/MM/YYYY)» | Marca ISO `2022-06-14T00:00:00.000` |
| 6 | Descripción: «Datos disponibles desde 1 de enero de 2021» | Hay 77 filas de 2019 y 14 265 de 2020, desde 2019-08-04 |
| 7 | Frecuencia de actualización «Mensual» | Última fecha de despacho real: 2026-04-07, y la última actualización de filas fue 2026-05-03: a 2026-11-24 el conjunto lleva ~7 meses sin cargar datos (no se verificó si hay un nuevo corte que aún no esté publicado) |
| 8 | Sin mención de fechas inválidas | 3 filas con fecha 2202-02, 2222-09 y 6202-04 (años imposibles) |
| 9 | Sin mención de huecos | 2024 casi vacío (ver §1.4): ene-2024 sin filas; feb–oct-2024 con 0,3 % del volumen normal; dic-2025 con ~1 % del volumen normal |
| 10 | `pasajeros`/`despachos` descritos como «Número» | 13,4 % de filas con `pasajeros = 0` pese a `despachos ≥ 1` (candidato a regla de anómalos de DA-3) |

## 2. DIVIPOLA (DANE)

**Fuente oficial del DANE.** Página oficial de la nomenclatura: https://www.dane.gov.co/index.php/sistema-estadistico-nacional-sen/normas-y-estandares/nomenclaturas-y-clasificaciones/nomenclaturas/codificacion-de-la-division-politica-administrativa-de-colombia-divipola
(abierta hoy). Define DIVIPOLA como «Es una nomenclatura estandarizada, diseñada por el DANE para la identificación de Entidades Territoriales»;
cubre departamentos, distritos, municipios, áreas no municipalizadas y centros poblados, con códigos numéricos únicos. La página ofrece el
geovisor (https://geoportal.dane.gov.co/geovisores/territorio/consulta-divipola-division-politico-administrativa-de-colombia/, responde HTTP 200),
la app Android y un manual. **Esa página no enlaza un archivo descargable (xlsx/csv) ni indica versión o fecha de actualización** (lo que pude leer).
`TODO(cita)`: localizar en el sitio del DANE el archivo oficial de descarga (Excel/CSV) con su fecha de corte; no se encontró hoy.

**Publicación oficial utilizable por API (la que se propone usar).** El propio DANE la publica en datos.gov.co:

| Dato | Valor (de `/api/views/gdxc-w37w.json` y `/resource/gdxc-w37w.json`) |
|---|---|
| Nombre / id | «DIVIPOLA- Códigos municipios» / `gdxc-w37w` |
| Entidad | Departamento Administrativo Nacional de Estadística - DANE |
| Descripción literal | «Código de la división Político Administrativa del país, Actualización a corte 30 diciembre 2024.» |
| Licencia / frecuencia | CC_40_BY_SA / «Semestral» |
| Publicado / filas actualizadas | 2025-01-24 / 2025-01-24 20:44:32 UTC (vista modificada 2026-09-24) |
| Formato | JSON/CSV vía API: https://www.datos.gov.co/resource/gdxc-w37w.json (sin límite práctico: 1 122 filas) |
| Columnas | `cod_dpto`, `dpto`, `cod_mpio`, `nom_mpio`, `tipo_municipio`, `longitud`, `latitud` (todas text; coordenadas con coma decimal) |
| Contenido medido | 1 122 filas = 1 103 «Municipio» + 18 «Área no municipalizada» + 1 «Isla»; 33 códigos de departamento; todos los `cod_mpio` tienen 5 caracteres |

Ejemplos: Medellín `05001`; Bogotá D.C. `11001`; Sogamoso `15759`; Santiago de Cali `76001`; Ginebra `76306`. Los 5 dígitos son 2 de departamento + 3 de municipio.
Cómo descargar: `curl "https://www.datos.gov.co/resource/gdxc-w37w.json?$limit=2000"`.
Corte 30-dic-2024: los municipios de las rutas cuyo código haya cambiado después, o creado después, pueden no figurar (validar en DA-3).

## 3. Cómo descargar el conjunto (recomendación)

**Hechos medidos.** 49,2 millones de filas; el JSON de la API pesa ~271 KB por 1 000 filas (muestra), es decir, estimado **~13 GB** de JSON si se descargara completo
(estimación, no medida; el CSV será menor). `$limit` por defecto 1 000; probé `$limit=50001` en `$select=terminal` y devolvió 50 001 filas (el resource endpoint
no capa en 50 000; la documentación de Socrata dice: «Version 2.0 endpoints have a maximum `$limit` of 50,000» y «Version 2.1 and 3.0 endpoints have no maximum»; advierte de timeouts). Las consultas agregadas sobre todo el
conjunto tardan **~120–280 s** (algunas, p. ej. `group by origen,destino` con `$limit=50000` sobre un mes, caducaron a 280 s). Esto es sin token de aplicación; los tiempos
aumentan al lanzar varias en paralelo. `https://www.datos.gov.co/api/views/eh75-8ah6/rows.csv?accessType=DOWNLOAD` responde 200 (`text/csv`) pero **con cabeceras
`Deprecation` y `Sunset: Tue, 22 Dec 2026`** (https://support.socrata.com/hc/en-us/articles/43491231777047); no depender de ese endpoint para el flujo reproducible.

**Recomendación.** Agregar en el servidor con SoQL `group by` (descartar la descarga completa: ~13 GB y 49 M de filas), **por trozos mensuales** (≈ 64 meses con datos) para
evitar el timeout, y concatenar. Para el contrato §5.1 se necesitan `pasajeros` y `despachos` por (origen, destino, fecha); las dimensiones `terminal`, `clase_vehiculo`,
`nivel_servicio`, `tipo_despacho` y `hora_despacho` se pierden al agregar: si Camila las necesita (p. ej. capacidad por clase de vehículo, preguntas de negocio),
conviene agregar **también** por `clase_vehiculo` (y quizá `tipo_despacho`) en la misma consulta; decisión del humano.

**Consulta SoQL propuesta (probada con `$limit=5`; HTTP 200 en ~149 s):**
```
GET https://www.datos.gov.co/resource/eh75-8ah6.json
  $select = municipio_origen_ruta as origen, municipio_destino_ruta as destino, fecha_despacho as fecha,
            sum(pasajeros) as pasajeros, sum(despachos) as despachos
  $where  = fecha_despacho between "2022-01-01T00:00:00" and "2022-01-31T23:59:59"     (iterar por mes)
  $group  = origen,destino,fecha
  $order  = origen,destino,fecha
  $limit  = 5          (en producción: 50000 con $offset, o más; el orden hace estable la paginación)
```
Resultado real de la prueba:
`[{"origen":"05001","destino":"05001","fecha":"2022-01-16T00:00:00.000","pasajeros":"15","despachos":"1"}, {"origen":"05001","destino":"05002","fecha":"2022-01-01T00:00:00.000","pasajeros":"157","despachos":"16"}, ...]`.
Notas: (a) en SoQL los alias llevan `as` (sin él, error 400 `query.compiler.malformed`); (b) los valores salen como cadenas; (c) hay rutas
intra-municipales (`05001`→`05001`); (d) el filtro `fecha_despacho < "2100-01-01"` excluye las 3 fechas absurdas; (e) **no probé la corrida completa** de un mes con `$limit` grande
ni el tiempo total; (f) `TIPO_DESPACHO = TRANSITO` (20,5 % de filas): en esas filas la terminal no es el origen de la ruta; el contrato §5.1 define `pasajeros` como los que abordan **en la terminal de origen**:
decidir en DA-3 si se filtra `tipo_despacho = "ORIGEN"` (esto requiere el filtro en el `where`).

## 4. Candidatos a hallazgo (para `alucinaciones/registro.md`)
1. **Cobertura temporal** — Si una IA describe el conjunto como una serie continua que cubre la pandemia (2020) y llega al presente, la fuente dice lo contrario: «Datos disponibles desde 1 de enero de 2021»;
   las filas de 2019–2020 son 14 342 en total; el último día real es 2026-04-07. Evidencia: §1.1 y §1.4. (Incide en la tarea M1 «recuperación posterior a la pandemia»: **la caída de 2020 no está en los datos**.)
2. **Hueco de 2024** — ene-2024 no tiene filas y feb–oct-2024 tienen ~0,3 % del volumen normal (1 704–3 873 filas/mes frente a ~1 M); dic-2025 con 13 286 filas (~1 %). Ninguna descripción del conjunto lo menciona.
3. **Fechas imposibles** (2202, 2222, 6202).
4. **Códigos categóricos** — el diccionario dice numéricos (clase de vehículo, nivel de servicio, tipo de despacho) y los datos traen texto; `PREFERENCIAL DE LUJO` no está en el diccionario.
5. **Campo «destino»** — el diccionario lo llama «departamento de destino» y los datos son de municipio (5 dígitos).
6. DIVIPOLA: la página oficial del DANE no enlaza archivo ni versión; el conjunto oficial utilizable es `gdxc-w37w` con corte 30-dic-2024, no una «versión 2025/2026».

## 5. Riesgos
- Series con huecos largos (2024, dic-2025): afecta partición temporal, rutas con «historial completo» y la prueba con una temporada alta; el contrato exige «sin huecos» (§5.1): hay que decidir (con Camila) el periodo útil (p. ej. feb-2025 → mar-2026 o 2021–2023) y la imputación de `sin_registro`.
- Dos periodos buenos están separados por el hueco 2024: 2021-ene → 2023-dic (36 meses) y 2025-ene → 2026-mar (15 meses), sin cubrir la pandemia.
- Timeouts de la API: troceo mensual, reintentos, posiblemente token de aplicación.
- El endpoint `rows.csv` tiene `Sunset` 2026-12-22.
- Terminal ≠ origen en despachos en tránsito; no hay código de terminal.
- El conjunto sigue actualizándose; registrar fecha de consulta, URL, SHA-256 y tamaño en `data/fuentes.md` (spec §3.2).
- La licencia CC BY-SA 4.0 exige atribución y compartir igual: citar en el blog.

## 6. Referencias (APA 7)

Departamento Administrativo Nacional de Estadística. (2024). *DIVIPOLA- Códigos municipios* [Conjunto de datos; actualización a corte 30 de diciembre de 2024]. Datos Abiertos Colombia. https://www.datos.gov.co/d/gdxc-w37w (consultado el 24 de noviembre de 2026).

Departamento Administrativo Nacional de Estadística. (s. f.). *Codificación de la división político administrativa de Colombia - DIVIPOLA*. https://www.dane.gov.co/index.php/sistema-estadistico-nacional-sen/normas-y-estandares/nomenclaturas-y-clasificaciones/nomenclaturas/codificacion-de-la-division-politica-administrativa-de-colombia-divipola (consultado el 24 de noviembre de 2026). `TODO(cita)`: fecha/versión del archivo oficial.

Superintendencia de Transporte. (2026). *Operación de pasajeros y despacho de vehículos en la modalidad de transporte de pasajeros por carretera* [Conjunto de datos]. Datos Abiertos Colombia. https://www.datos.gov.co/d/eh75-8ah6 (consultado el 24 de noviembre de 2026; filas actualizadas el 3 de mayo de 2026).

Tyler Technologies. (s. f.). *Paging through data: $limit*. Socrata Developer Portal. https://dev.socrata.com/docs/queries/limit (consultado el 24 de noviembre de 2026). `TODO(cita)`: confirmar autor/año del portal.

## 7. Archivos generados
`data/raw/m1/muestra_1000.json`, `data/raw/m1/views_eh75-8ah6.json`, `data/raw/m1/divipola_gdxc-w37w.json` (no versionados).
