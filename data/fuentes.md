# Fuentes de datos

Registro de cada archivo/consulta: URL, fecha, licencia, SHA-256 y quién descargó (núcleo §3, regla 0.7). Los datos crudos
(`data/raw/`) no se versionan; aquí queda cómo regenerarlos.

## M1 — Demanda de pasajeros por carretera

### Conjunto principal
| Dato | Valor |
|---|---|
| Conjunto | «Operación de pasajeros y despacho de vehículos en la modalidad de transporte de pasajeros por carretera», Superintendencia de Transporte (identificador Socrata `eh75-8ah6`) |
| URL | https://www.datos.gov.co/d/eh75-8ah6 · API: https://www.datos.gov.co/resource/eh75-8ah6.json |
| Licencia | CC BY-SA 4.0 (`CC_40_BY_SA`, http://creativecommons.org/licenses/by-sa/4.0/legalcode); exige atribución y compartir igual |
| Fecha de consulta | 2026-11-24 (filas actualizadas por la fuente el 2026-05-03; ver `docs/investigacion/DA-2_fuentes_m1.md`) |
| Descargó | Daniel (agente curador-datos, Sonnet), con `scripts/descargar_m1.py` |
| Descarga | Agregada en el servidor (SoQL `group by`), nunca el conjunto completo. Log de cada consulta (URL completa, duración, filas): `data/raw/m1/consultas_log.jsonl` (no versionado) |
| Filtro fijo | `fecha_despacho < "2100-01-01"` (excluye 3 fechas imposibles) |

### Consulta del ranking de rutas (DA-3a)
Muestra de un día por mes, el **segundo miércoles** de cada mes de 2021-01 a 2023-12 (36 días: 2021-01-13, 02-10, 03-10, 04-14,
05-12, 06-09, 07-14, 08-11, 09-08, 10-13, 11-10, 12-08; 2022-01-12, 02-09, 03-09, 04-13, 05-11, 06-08, 07-13, 08-10, 09-14, 10-12,
11-09, 12-14; 2023-01-11, 02-08, 03-08, 04-12, 05-10, 06-14, 07-12, 08-09, 09-13, 10-11, 11-08, 12-13). Una consulta por día:

```
GET https://www.datos.gov.co/resource/eh75-8ah6.json
  $select = municipio_origen_ruta, municipio_destino_ruta, sum(pasajeros) as pasajeros, sum(despachos) as despachos, count(*) as filas
  $where  = fecha_despacho = "<AAAA-MM-DD>T00:00:00" AND fecha_despacho < "2100-01-01"
  $group  = municipio_origen_ruta, municipio_destino_ruta
  $order  = municipio_origen_ruta, municipio_destino_ruta
  $limit  = 50000
```
Todos los `tipo_despacho` (origen y tránsito), todas las clases de vehículo. Se excluyen las rutas intramunicipales (origen = destino).
Resultado: 36 de 36 días obtenidos; 2 099 pares dirigidos (origen, destino). Salida: `data/raw/m1/ranking_rutas.csv`
(SHA-256 `ad65c38a6c7951f0eb54b5be94f40a2746ed7820aedc625c440402c9fd9fc355`), `ranking_top15_pares.csv` y las respuestas
diarias en `ranking_dias.json` (no versionados). Las cifras son de una **muestra de 36 días**, no del periodo completo.
Regenerar: `.venv\Scripts\python scripts/descargar_m1.py ranking`.

### Descarga de las series de las rutas elegidas (DA-3b)
| Dato | Valor |
|---|---|
| Fecha | 2026-11-24 (consultas entre 16:44 y 16:50 UTC; log en `data/raw/m1/consultas_log.jsonl`, no versionado) |
| Descargó | Daniel (agente implementador-experto, Opus), con `scripts/descargar_m1.py descargar` |
| Rutas (6 dirigidas) | `11001-76001, 76001-11001, 11001-15759, 15759-11001, 52001-52356, 52356-52001` (daniel.md §3.2) |
| Periodo | 2021-01-01 a 2023-12-31: 36 consultas, una por mes; 4 meses a la vez (4 procesos del script, cada uno con un mes por llamada) |
| Resultado | 36 de 36 meses; 25 248 filas en total. 37 peticiones: una falló por conexión (`RemoteDisconnected`, mes 2022-03) y el reintento automático la completó |
| `tipo_despacho` | ORIGEN y TRANSITO, sin filtro (núcleo §5.1 v0.3: `pasajeros` = origen + tránsito) |

Consulta (una por mes; `<ini>` = primer día del mes, `<fin>` = primer día del mes siguiente):
```
GET https://www.datos.gov.co/resource/eh75-8ah6.json
  $select = municipio_origen_ruta, municipio_destino_ruta, fecha_despacho, tipo_despacho, clase_vehiculo,
            sum(pasajeros) as pasajeros, sum(despachos) as despachos
  $where  = fecha_despacho >= "<ini>T00:00:00" AND fecha_despacho < "<fin>T00:00:00" AND fecha_despacho < "2100-01-01"
            AND ((municipio_origen_ruta='11001' AND municipio_destino_ruta='76001') OR (... las otras 5 rutas ...))
  $group  = municipio_origen_ruta, municipio_destino_ruta, fecha_despacho, tipo_despacho, clase_vehiculo
  $order  = municipio_origen_ruta, municipio_destino_ruta, fecha_despacho, tipo_despacho, clase_vehiculo
  $limit  = 50000   ($offset de 50 000 en 50 000; ningún mes pasó de una página)
```
Regenerar (reanudable: salta los meses ya descargados):
`.venv\Scripts\python scripts/descargar_m1.py descargar --rutas 11001-76001,76001-11001,11001-15759,15759-11001,52001-52356,52356-52001 --desde 2021-01-01 --hasta 2023-12-31`.
Después, sin red: `.venv\Scripts\python run.py m1-datos --config configs/m1/datos.yaml` (los SHA-256 también quedan en
`data/processed/m1/resumen_datos.json` y en `results/data/m1/eda/ficha.json`).

### Conteo de registros crudos de las 6 rutas (DA-3c)
| Dato | Valor |
|---|---|
| Fecha de consulta | 2026-11-24 (log en `data/raw/m1/consultas_log.jsonl`, no versionado) |
| Hecho con | `scripts/descargar_m1.py contar` (reanudable; 36 consultas, una por mes) |
| Qué mide | `count(*)` en la fuente, sin agrupar, por mes y ruta dirigida, con el mismo filtro de la descarga (rutas, mes, `fecha_despacho < 2100-01-01`) |
| Resultado | **1 372 746 registros crudos** en 2021-2023; por ruta: `11001-15759` 362 258, `11001-76001` 297 559, `15759-11001` 258 171, `52356-52001` 133 348, `52001-52356` 119 609, `76001-11001` 201 801 |
| Archivo | `data/processed/m1/conteo_registros.csv` (se versiona; columnas `mes, ruta_id, registros, fecha_consulta`; 216 filas) |

Consulta (una por mes):
```
GET https://www.datos.gov.co/resource/eh75-8ah6.json
  $select = municipio_origen_ruta, municipio_destino_ruta, count(*) as registros
  $where  = (el mismo de la descarga mensual)
  $group  = $order = municipio_origen_ruta, municipio_destino_ruta
```
Regenerar: `.venv\Scripts\python scripts/descargar_m1.py contar --rutas 11001-76001,76001-11001,11001-15759,15759-11001,52001-52356,52356-52001 --desde 2021-01-01 --hasta 2023-12-31`.
Los cuatro números del resumen no son comparables entre sí: 49 202 812 (registros del conjunto completo), 1 372 746 (registros
crudos de las 6 rutas), 25 248 (filas agregadas por el servidor que se descargaron) y 6 570 (filas de la serie diaria).
`fecha_descarga` de `ficha.json` sale de la última descarga mensual exitosa del log (`momento`), no del mtime de los parquets.

Parquets crudos (`data/raw/m1/rutas/`, no versionados):

| Archivo | Filas | Tamaño (B) | SHA-256 |
|---|---|---|---|
| `2021-01.parquet` | 701 | 9645 | `90f6e3393c728c4eee1267cf05996bf1d70fd39458bd0308074e3007f65b829b` |
| `2021-02.parquet` | 650 | 9336 | `b928a724fcc8ea19463ea9465b3eec9f8d665a207408debafdbb38a4cbae7f56` |
| `2021-03.parquet` | 708 | 9910 | `c96dd7f083402a80ac7abfaaa83b7c70e73dfd45df078bb400772217c59b3c5b` |
| `2021-04.parquet` | 657 | 9595 | `f1469d20dd128d2776868f1fcb82292da988c84df6dcefff3d05d5b1d5d7ae8d` |
| `2021-05.parquet` | 349 | 7461 | `ca480435d55b96c4099c2730f39098c233181891b3fa421a2b2abae7ce5aba2a` |
| `2021-06.parquet` | 677 | 9531 | `955bbb75a481993738e07646831db80adf7affbfd68b69fefe9e6a615c8ba53c` |
| `2021-07.parquet` | 731 | 10016 | `1b805931491b0650da44219363cdb68e23f7a9fbd606ea503b5032fab751cb88` |
| `2021-08.parquet` | 737 | 10156 | `85a7c1c826e16f3c9485639704f80ac23f18e0851c10ed9eb67f74889a28c86a` |
| `2021-09.parquet` | 707 | 9941 | `7d1cb92818643290e941fb6f76ab350ec2d5e9c3a5f2d2227dd6016f9487edd1` |
| `2021-10.parquet` | 734 | 10134 | `d7f373ffe27ad6e74675f074470a91ffbe25eb10d19d46c1e15b78417113aa95` |
| `2021-11.parquet` | 692 | 9974 | `8676294c2fd0b29d0906a320c6d158b30ac81d12f9f787c8707a6891f74c2f1b` |
| `2021-12.parquet` | 746 | 10445 | `4fe8d8412e3134b12ee5d868e2977aa109bc6ebdccc29140bd4d2b41c2c7a5bc` |
| `2022-01.parquet` | 714 | 10198 | `4918f03b72ad49843696a5ff36f3307443c0b8cb1ffb2dbf1917eb691a06db4b` |
| `2022-02.parquet` | 654 | 9710 | `416d64de904e9b19219543e8d1174fbdad0df0058c7607de7a078984765632d7` |
| `2022-03.parquet` | 869 | 10813 | `bbb5f5412a62aa82663c189ffe3f2fd132cfc322ad51fbe0750d8d608ed100bf` |
| `2022-04.parquet` | 893 | 10891 | `09835a3669b26cf20d696e289db2240ef561fa89b99ecca3189c3ea78db49de0` |
| `2022-05.parquet` | 875 | 10834 | `b745e326fd7fdb8183bd1bc2f73533b821459fb53fad8c7572656bd403eac815` |
| `2022-06.parquet` | 865 | 10661 | `f8ca0bd3d368140e07c4f9a27ef4007516fe7f63f35ec58358a759e34c5329c7` |
| `2022-07.parquet` | 729 | 10282 | `9c1418fbd7ebf6a55e1b39c7f9a1df87778471cbbe19a38a1871614052b9c20e` |
| `2022-08.parquet` | 751 | 10200 | `7612664bb6fa42c09269d5eb0598043743951efefd9a1f229340b506fe6f403b` |
| `2022-09.parquet` | 671 | 9827 | `dd3c658ab1b38e58ed589e982687120623649fa1fdbf5c8b59dabce87c23354f` |
| `2022-10.parquet` | 700 | 9965 | `cc7f9c48a6a5682462ed9bd9956ca9ebb8b8c92a5250ca8d2b45f786988cd4c5` |
| `2022-11.parquet` | 669 | 9887 | `6b25eeecee94c3e6ad1e98891229eb81bd0a82a0a6cc9e365eee97db5637d3b9` |
| `2022-12.parquet` | 698 | 10119 | `15fbd13e8417d4f1f4134aa5c915e567dc71a1403f73ecb06350c68b42534619` |
| `2023-01.parquet` | 687 | 10083 | `ab17bf4aa61e034c41211293c8ec2caa03bafcddf1db214af4a2878b926fe27e` |
| `2023-02.parquet` | 634 | 9703 | `6d577704600375714fab4ab73922ab6aa0737c82c5675c0195ce939bcde32b51` |
| `2023-03.parquet` | 701 | 10024 | `d5eacb84258d26fc53b21d0fd0861333cdac4290d701711618c5e7a1e4f5fd02` |
| `2023-04.parquet` | 668 | 9881 | `01d27ab3d1e4d8e2eaa906d4ac1a8cc25a9f5c50f1dfa4198df13a368d8bfae4` |
| `2023-05.parquet` | 685 | 9967 | `c436a1cff11ed400ea0724960b7e9005ef454b3fedc0932874582faf3ad07117` |
| `2023-06.parquet` | 667 | 9892 | `5295f60f6648bb4c80f503af773655432714b18dad6f6bdc6f67e1b151a4c921` |
| `2023-07.parquet` | 685 | 9965 | `577316b9cb59e3fcb238781055eb354e90bf26b18ea5ac331d51f79f786aa77e` |
| `2023-08.parquet` | 681 | 10025 | `2d5528eb8f05e2db4136d397a8f36975b29ff174d185672421fb565f5fbac4cd` |
| `2023-09.parquet` | 633 | 9765 | `142553d501a4b7554be69ce783322f092ee60d671b34945c2546239cb04d560c` |
| `2023-10.parquet` | 675 | 10087 | `62502441d126af44af3fdcd1d7e8ddd995b7abf66c3d0dd4211d5a14a17d2bc8` |
| `2023-11.parquet` | 662 | 9891 | `5fda846d4b320b7a53cef8a14a28870cb4d6b6e989c3e0e02c789c4aab4a75df` |
| `2023-12.parquet` | 693 | 10310 | `916ea7ab64a511983dd0ccac59dfa809a219e98b2f4b27bc0f49b0b847b70e28` |

### DIVIPOLA (DANE)
| Dato | Valor |
|---|---|
| Conjunto | «DIVIPOLA- Códigos municipios», DANE (`gdxc-w37w`) |
| URL | https://www.datos.gov.co/d/gdxc-w37w · API: https://www.datos.gov.co/resource/gdxc-w37w.json |
| Corte | «Actualización a corte 30 diciembre 2024» (descripción literal de la fuente) |
| Licencia | CC BY-SA 4.0 |
| Fecha de descarga | 2026-11-24 |
| Archivo | `data/processed/m1/divipola.csv` (se versiona): 1 122 filas, columnas `cod_dpto, dpto, cod_mpio, nom_mpio, tipo_municipio, longitud, latitud` tal cual la API |
| SHA-256 | `abc2608f58363cfadfdf91a56a53b944d2aa7784e200aa742c8171a2733da081` |
| Regenerar | `.venv\Scripts\python scripts/descargar_m1.py divipola` |

`TODO(cita)`: la página oficial del DANE (nomenclatura DIVIPOLA) no enlaza un archivo descargable ni su fecha de corte; se usa la
publicación del propio DANE en datos.gov.co.

## Calendario exógeno de M1 (CA-1)

Salida: `data/processed/m1/calendario.parquet` (1 461 filas, 2021-01-01..2024-12-31, una por `fecha`), generada con
`.venv/bin/python -m src.m1_demanda.calendario` (sin red). Tablas de recesos y supuestos: `data/externos/m1/calendario_fuentes.yaml`
(cada bloque con acto, fecha del acto, URL y fecha de consulta). Investigación de fuentes: `docs/investigacion/CA-1_fuentes_calendario.md`
(investigador-fuentes, consulta 2026-11-26). Todo es conocible 30 días antes (regla 0.9): ley de 1983, cálculo determinista de la
Pascua y calendarios escolares expedidos, por regla, antes del 1-nov del año anterior (versión **original** de cada acto; las
modificaciones posteriores solo se documentan aquí). Excepciones que este mismo archivo documenta: Pasto 2021 (Res. 0064, 15-ene-2021) e Ipiales 2021 (Res. 00023, 14-ene-2021), Pasto 2022 (Res. 2706, 7-dic-2021) y Cali 2023 (afiche, posible versión modificada por la Res. 00011 del 3-ene-2023).

| Columna | Fuente / regla | Tipo de dato |
|---|---|---|
| `fecha`, `dia_semana` (0 = lunes) | calendario gregoriano | derivada |
| `festivo`, `festivo_nombre`, `festivo_trasladado` | Ley 51 de 1983 (sancionada el 22-dic-1983; Diario Oficial 36.428, 30-dic-1983; rige desde la sanción, art. 4; el «Dada en Bogotá» del 6-dic-1983 es la firma de los presidentes del Congreso), art. 1 num. 1–2. Fijos sin traslado: 1-ene, 1-may, 20-jul, 7-ago, 8-dic, 25-dic, Jueves y Viernes Santo. Con traslado al lunes siguiente si no caen en lunes (incluidos los sábados y domingos): 6-ene, 19-mar, 29-jun, 15-ago, 12-oct, 1-nov, 11-nov, Ascensión, Corpus Christi, Sagrado Corazón. Copias: https://apps.procuraduria.gov.co/gd_1952/docs/l0051_83.htm · https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=4954 · https://www.corteconstitucional.gov.co/relatoria/1994/C-107-94.htm | norma + cálculo (la prueba compara contra las 4 × 18 fechas de la tabla del informe §2) |
| Pascua y desfases | `dateutil.easter.easter`. Jueves Santo = Pascua−3, Viernes Santo = Pascua−2, Ascensión (jueves) = Pascua+39, Corpus Christi (jueves) = Pascua+60, Sagrado Corazón (viernes) = Pascua+68; estos tres, trasladados al lunes. Ascensión: «On the fortieth day after Easter…» (Normas universales sobre el año litúrgico, n. 25; copia https://www.catholicculture.org/culture/library/view.cfm?id=10842, confianza media) | `TODO(cita)`: fuente primaria de los desfases de Corpus Christi y Sagrado Corazón, texto vaticano de la norma 25 y tabla oficial de Pascua |
| `semana_santa` | lunes a domingo que termina en el Domingo de Pascua (así la fijan los decretos de Sogamoso 2021–2023; Bogotá 2024 coincide). Pascua: 2021-04-04, 2022-04-17, 2023-04-09, 2024-03-31 | norma escolar + cálculo; el informe no usa «Domingo de Ramos», sino esta ventana |
| `jueves_viernes_santo` | Pascua−3 y Pascua−2 (Ley 51) | norma + cálculo |
| `puente` | **Supuesto del equipo** (no es término legal; Camila, 26-nov): sábado, domingo y lunes de un fin de semana cuyo lunes es festivo (incluidos los trasladados); viernes, sábado y domingo si el festivo cae en viernes (incluido el Viernes Santo). Festivos en martes o jueves no generan puente | supuesto |
| `fin_de_anio` | **Supuesto del equipo** (no hay definición oficial de temporada alta; búsqueda negativa, confianza baja-media): del 15-dic al 15-ene, ambos inclusive | supuesto |
| `vacaciones_escolares_11001/_76001/_15759/_52001/_52356` | Receso estudiantil del calendario A de colegios oficiales de la secretaría certificada de cada ciudad (Bogotá, Cali, Sogamoso, Pasto, Ipiales). Actos y URL en el yaml (listados MEN: https://www.mineducacion.gov.co/1780/w3-article-402903.html · `-408776` · `-413526` · `-419296`). Marco: Decreto 1075 de 2015, art. 2.4.3.4.1 (calendario antes del 1-nov) | calendarios oficiales; transcripción por OCR en parte (ver confianza por bloque en el yaml) |
| `vacaciones_escolares` | = `vacaciones_escolares_11001` (Bogotá), por compatibilidad con núcleo §5.2 | derivada |

### Supuestos y decisiones declaradas
1. Calendario B y colegios privados no cubiertos. Se supone que la demanda responde a la ciudad de origen o destino.
2. **Pasto**: su acto lista «Vacaciones» y «Desarrollo Institucional» (solo 2024 rotula «Receso Estudiantil»); se trata como sin clases todo lo que
   no es «Desarrollo Académico». Es inferencia aritmética (23+10+7 = 40 semanas académicas en 2022–2023; 39 en 2021), no texto literal. Pasto no tiene receso de Semana Santa.
3. **Bogotá 2021-01-01..10**: el inicio del receso es supuesto (continuidad con el calendario 2020); el fin sale del considerando de la Res. 1739/2020.
4. **Vacíos sin fuente = nulo (`boolean` anulable), no se imputa:** Cali y Sogamoso 2021-01-01..17 (17 días cada una; calendario 2020 no recuperado);
   Pasto e Ipiales 2021-01-01..03 (3 días; Res. 1588 y 0916 de 2020 no obtenidas); Sogamoso desde 2024-01-15 hasta 2024-12-31 (352 días; decreto
   de 2024 no encontrado). Los modelos entrenan desde el 2021-06-01 (núcleo §5.1), así que enero de 2021 no los afecta; **Sogamoso 2024 sí** quedaría con
   nulos si se usara 2024 (la serie de M1 llega a 2023-12-31, y el calendario va hasta 2024-12-31).
5. 1-ene-2024 en Pasto e Ipiales (festivo): ningún acto lo cubre (el calendario 2023 termina el 31-dic y el de 2024 empieza el 2-ene). Por la regla de vacíos sin fuente
   (punto 4) vale **nulo** (clave `vacios` del yaml). Antes valía falso, un falso «hay clases» en un festivo (corrección de la verificación CA-1). Por eso Pasto e Ipiales tienen 4 nulos, no 3.
5b. **Cali 2023**: el afiche se contradice (30-ene-2023 es a la vez el último día del receso, p. 4, y el primer día de clases, p. 3; las semanas lectivas suman 9+11+11+8 = 39; la semana del 26-jun al 2-jul no tiene rótulo). Se mantiene el valor literal del cuadro de receso (2023-01-30 = receso). **Decisión pendiente de Camila.**
6. Los rangos que cruzan el fin del periodo (p. ej. 2024-12-02..2025-01-12) se recortan a 2024-12-31.

### Modificaciones posteriores (solo documentadas; no entran en la columna) y casos dudosos de conocibilidad (informe §5)
- Pasto 2021: Res. 0064 (2021-01-15) modifica la Res. 1588 (2020-11-13, no obtenida); Ipiales 2021: Res. 00023 (2021-01-14) modifica la Res. 0916
  (2020-10-30, no obtenida). Lo vigente 30 días antes puede diferir del usado. `TODO(cita)`.
- Pasto 2022: Res. 2706 expedida el 2021-12-07, 27 días antes de las vacaciones del 3-ene-2022 (el receso de enero dependía del calendario previo).
- Cali 2021: modificada por Res. 06575 (2020-12-15; ajustó las vacaciones de los docentes) y Res. 0002 (2021-01-04; convirtió la semana lectiva del 25 al 31 de enero de 2021 en semana de desarrollo institucional, sin clases; según los considerandos de la Res. 06395/2021). La 0002 no era conocible 30 días antes y es anterior al 2021-06-01; no entra en la columna. Cali 2023: la Res. 4143.010.21.0.06455 (2022-10-25) no se obtuvo;
  se usa el afiche oficial de la Secretaría de Educación, que podría ser la versión modificada por la Res. 00011 (2023-01-03). `TODO(cita)`.
- Sogamoso 2022: Decreto 333 modificado parcialmente por el Decreto 026 (2022-01-20), no obtenido. `TODO(cita)`.
- Sogamoso 2024: decreto de calendario no encontrado. `TODO(cita)`.
- Boyacá y Nariño (departamentos) no se extrajeron: los cinco extremos de las rutas son entidades certificadas.

### Discrepancias entre fuentes (datos, no alucinaciones)
- Ley 51: no son dos versiones de un dato. La copia de la Procuraduría trae ambas fechas: «Dada en Bogotá, D.E., a los seis días del mes de diciembre de 1983» (firma del Congreso) y «22 de diciembre de 1983» (sanción de Belisario Betancur). Rige desde la sanción (art. 4), por eso se cita 22-dic con el Diario Oficial; la ficha de la Alcaldía de Bogotá usa la fecha del «Dada en».
- Bogotá Res. 2204/2021: encabezado 29-oct frente a «veinticuatro (24) días del mes de octubre»; trece semanas de receso en lugar de doce.
- Cali 2021: «Cinco (6) semanas».
- Cali 2023: contradicción interna del afiche (ver punto 5b).

### Lista de `TODO(cita)` abiertos de este bloque
Lista anual oficial de festivos 2021–2024 (contraste); fuente primaria de Corpus Christi (+60) y Sagrado Corazón (+68); tabla oficial de Pascua;
Sogamoso 2024; Cali 2023 (resolución) y 2021; Decreto 026/2022 de Sogamoso, Res. 1588/2020 de Pasto, Res. 0916/2020 de Ipiales, Res. 06575/2020 y 0002/2021 de Cali;
definición oficial de temporada alta; Boyacá y Nariño; concepto de Función Pública sobre el traslado; vigencia de la Ley 51 en Función Pública o SUIN (no accesibles).
Cerrados por la verificación CA-1 (2026-11-26): sentencia C-568/1993 (M. P. Fabio Morón Díaz, 9-dic-1993, arts. 1 y 2 de la Ley 51 exequibles; https://www.corteconstitucional.gov.co/relatoria/1993/C-568-93.htm) y ponente de la C-107/1994 (Carlos Gaviria Díaz, 10-mar-1994, «estarse a lo resuelto» en la C-568;
https://www.corteconstitucional.gov.co/relatoria/1994/C-107-94.htm). Detalle: `docs/investigacion/CA-1_verificacion.md`.
