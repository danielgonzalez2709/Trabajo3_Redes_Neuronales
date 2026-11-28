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

## M2 — Clasificación de imágenes (comportamiento del conductor)

### Conjunto principal
| Dato | Valor |
|---|---|
| Conjunto | «Multi-Class Driver Behavior Image Dataset» (Mendeley Data), versión 1 |
| DOI | 10.17632/mzb4b6dff3.1 (https://doi.org/10.17632/mzb4b6dff3.1) |
| API pública consultada | https://data.mendeley.com/public-api/datasets/mzb4b6dff3/files?folder_id=root&version=1 (devuelve un único archivo; la API da `size` y `sha256_hash`, con los que el script verifica la descarga) |
| Archivo | `Multi-Class Driver Behavior Image Dataset.zip` |
| Tamaño | 2 556 850 881 bytes |
| SHA-256 | `427fec9d689a22856c51c7773adc6024158d5b228e36b2c9b58a13ce9af41c8c` (igual al de la API y al medido localmente por `docs/investigacion/JO-1_inventario.py`) |
| Fecha de descarga | 2026-11-27 (hora local de la máquina; la descarga terminó a las 22:11 locales del 27-nov; la segunda ejecución, que solo verificó, a las 2026-11-28 03:11 UTC) |
| Descargó | José, vía `scripts/descargar_m2.py` (streaming; verifica tamaño y SHA-256 contra la API; no extrae el .zip) |
| Ubicación | `data/raw/m2/` (no versionado; está en `.gitignore`) |
| Licencia | **CC BY 4.0** según el campo de licencia de la página de Mendeley (versión 1); el artículo también es CC BY 4.0. Exige atribución, enlace a la licencia e indicar si se hicieron cambios (aquí: redimensionado a 224×224 y recompresión JPEG). **Contradicción sin resolver (C-6 de `docs/investigacion/JO-1_fuentes_m2.md`):** el depósito de Zenodo del mismo conjunto trae un `DATA USE AGREEMENT.docx` (plantilla con campos en blanco) que pide uso no comercial y no redistribuir sin permiso escrito de DIU; `TODO(dato-faltante)`: si aplica a quien descarga de Mendeley. Relevante porque `data/processed/m2/` versiona las imágenes procesadas (decisión de José) |
| Autores | Afridi, A. S.; Kafy, A.; Moon, N. N.; Shakil, M. S. (Department of Computer Science and Engineering, Daffodil International University, Dhaka, Bangladesh, según el artículo). Ortografía distinta de los nombres entre Mendeley, el artículo y Zenodo (`JO-1_fuentes_m2.md` §1 y C-11) |
| Cita (APA 7) | Afridi, A. S., Kafy, A., Moon, N. N., & Shakil, M. S. (2024). *Multi-class driver behavior image dataset* (Version 1) [Data set]. Mendeley Data. https://doi.org/10.17632/mzb4b6dff3.1 |
| Artículo del conjunto | Afridi, A. S., Kafy, A., Moon, N. N., & Shakil, M. S. (2025). A multi-class driver behavior dataset for real-time detection and road safety enhancement. *Data in Brief, 60*, Article 111529. https://doi.org/10.1016/j.dib.2025.111529 |

### Cómo regenerar
1. `.venv/bin/python scripts/descargar_m2.py` (con red; si el archivo ya existe con el SHA-256 correcto no lo vuelve a bajar).
2. Sin red: `.venv/bin/python -I docs/investigacion/JO-1_inventario.py` (lee el .zip sin extraerlo; escribe
   `docs/investigacion/JO-1_inventario_salida.txt`).
3. Sin red: `.venv/bin/python run.py m2-datos --config configs/m2/datos.yaml` (lee el .zip sin extraerlo; escribe
   `data/processed/m2/` y `results/data/m2/eda/`).

## M3 — Recomendación de destinos

### Conjunto principal
| Dato | Valor |
|---|---|
| Conjunto | «Travel Recommendation Dataset» (la descripción lo titula «India Travel Recommender System Dataset»), Aman Mehra, usuario `amanmehra23` en Kaggle (ref. `amanmehra23/travel-recommendation-dataset`, id 4345382) |
| URL | https://www.kaggle.com/datasets/amanmehra23/travel-recommendation-dataset |
| Versión | 1 («Initial release»), creada el 2024-01-23T17:07:26.487Z; sin actualizaciones posteriores |
| DOI | No hay |
| Licencia | **Contradictoria** (D5, `docs/spec/partes/juanjose.md` §3.1): el campo formal de Kaggle dice «MIT»; la sección «License» de la descripción dice «CC0: Public Domain - The dataset is in the public domain and can be used without restrictions.»; la sección «Usage» dice «This dataset is free to use for non-commercial purposes. For commercial use, please contact the dataset provider. Remember to cite the source when using this dataset in your projects.». Los textos oficiales de MIT (https://opensource.org/license/mit) y CC0 (https://creativecommons.org/publicdomain/zero/1.0/) permiten el uso comercial; «Usage» lo restringe. Para este trabajo académico no comercial las tres permiten el uso; solo la sección «Usage» pide citar la fuente (`docs/investigacion/JJ-1_fuentes_m3.md` §3.2) |
| Fecha de descarga | 2026-11-25 |
| Descargó | Juan José, a mano desde la página de Kaggle con su cuenta (botón Download → `archive.zip`); sin clave de API |
| Cita (APA 7) | Mehra, A. (2024). *Travel recommendation dataset* (Versión 1) [Conjunto de datos]. Kaggle. https://www.kaggle.com/datasets/amanmehra23/travel-recommendation-dataset |
| ¿Real o sintético? | La fuente dice «generated for educational and research purposes»; no usa la palabra «synthetic». Señales medidas y conclusión (D4): `results/data/m3/eda/ficha.json` → `real_o_sintetico` |

### Archivos (`data/raw/m3/`, no versionado)
| Archivo | Bytes | SHA-256 |
|---|---|---|
| `archive.zip` | 34 679 | `117e3135b2fb8ff1ecb1e3a2d4b57315273f7954520567bbb5663af2912d004d` |
| `Expanded_Destinations.csv` | 60 768 | `5e311d3df9ebd626df28c90060b4804cfaeaee11012e1ffcfcc27c1817179766` |
| `Final_Updated_Expanded_Reviews.csv` | 33 710 | `bd9a10fb063592418511fa05350862fc6e8e81d6ab087422992ce64a066aca48` |
| `Final_Updated_Expanded_UserHistory.csv` | 24 683 | `df8a5b21e0c1f45ca9e48dfe98db83ae291a45ee0f8be800bd4274a81ac7307b` |
| `Final_Updated_Expanded_Users.csv` | 58 535 | `a3c51b1583ed727fed42278af77bde007aeba2a71fc1fd17c477080e275aaeac` |

Los 4 CSV sueltos son idénticos byte a byte a los miembros del .zip. Los mismos SHA-256 están en `configs/m3/datos.yaml`
(`sha256_esperado`): el comando se detiene si algún archivo no coincide.

### Metadatos de la fuente
Respuestas crudas de la API pública de Kaggle (sin credenciales), consultadas el 2026-11-25 a las 23:16 UTC y guardadas en
`docs/investigacion/JJ-1_kaggle_metadata.json`; de ahí salen la descripción, el campo formal de licencia, la fecha de la
versión y la lista de archivos (con `columns` vacío: la fuente no documenta columnas). Verificación independiente:
`docs/investigacion/JJ-1_verificacion_A3.md`.

### Cómo regenerar
1. Descargar `archive.zip` desde la página del conjunto en Kaggle (con sesión iniciada) y guardarlo en `data/raw/m3/`.
2. Descomprimirlo ahí mismo (quedan los 4 CSV junto al .zip).
3. Sin red: `.venv\Scripts\python run.py m3-datos --config configs/m3/datos.yaml`. Escribe `data/processed/m3/{destinos,usuarios,
   interacciones}.parquet` y `results/data/m3/eda/{ficha.json,calidad.csv,diccionario.json}`. `Name`, `Email` y `ReviewText` no
   pasan a ninguna salida (D6).
