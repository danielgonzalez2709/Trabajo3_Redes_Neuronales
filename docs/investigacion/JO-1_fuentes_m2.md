# JO-1 (A2) — Fuentes del Módulo 2: Multi-Class Driver Behavior Image Dataset

Fecha de consulta de todas las fuentes: **2026-11-27**. Orquesta: José (rama `dev/jose`). Prompt: `alucinaciones/prompts/JO-1a-investigador-fuentes.md`.
Este documento recoge **lo que dicen las fuentes**, no mediciones sobre las imágenes (las hace otro agente). Las citas están en
inglés, tal como aparecen; el comentario va en español. Cuando algo no está en las fuentes: `TODO(dato-faltante)`.

## 0. Fuentes consultadas y cómo se accedió

| Id | Fuente | Tipo | URL | Cómo se leyó |
|---|---|---|---|---|
| M | Página del conjunto en Mendeley Data, versión 1 | Primaria (descripción y licencia) | https://data.mendeley.com/datasets/mzb4b6dff3/1 | HTML de la página (descripción, licencia y metadatos `citation_*` y JSON-LD) |
| A | Artículo de Data in Brief 60, 111529 | Primaria | https://doi.org/10.1016/j.dib.2025.111529 | **ScienceDirect/Elsevier no se abrió** (el DOI redirige a `linkinghub.elsevier.com`). Texto completo de la versión de acceso abierto en PubMed Central, PMC12019831 (https://pmc.ncbi.nlm.nih.gov/articles/PMC12019831/), descargado vía E-utilities (`efetch` db=pmc, XML), porque la página web de PMC mostró un reCAPTCHA. Las secciones y tablas citadas son las del XML de PMC. Las figuras y la Tabla 2 son imágenes y no se leyeron |
| C | Metadatos de Crossref del DOI del artículo | Primaria (registro del DOI) | https://api.crossref.org/works/10.1016/j.dib.2025.111529 | JSON |
| Z | Registro de Zenodo 14908802 (repositorio que el **artículo** declara como fuente de los datos) | Primaria para el depósito citado por el artículo | https://zenodo.org/records/14908802 (API: https://zenodo.org/api/records/14908802) | JSON del registro y archivo `DATA USE AGREEMENT.docx` |

Limitación: la lista de archivos de la página de Mendeley se carga con JavaScript y no se pudo leer (`TODO(dato-faltante)`:
estructura de carpetas y tamaño del depósito de Mendeley). Verificar contra el artículo en ScienceDirect, que no se abrió, queda como paso manual.

## 1. Referencias APA 7

**Conjunto (Mendeley Data).** Autores, año, título y versión según la página de Mendeley (`citation_author`, `citation_publication_date`
= «15 November 2024», `citation_volume` = «1»):

> Afridi, A. S., Kafy, A., Moon, N. N., & Shakil, M. S. (2024). *Multi-class driver behavior image dataset* (Version 1) [Data set]. Mendeley Data. https://doi.org/10.17632/mzb4b6dff3.1

Cita que ofrece la propia página («citation» del JSON-LD): «Sahin Afridi, Arafat; Kafy, Arafath ; Nessa Moon, Ms. Nazmun; Shakil, Md.
Shahriar (2024), 'Multi-Class Driver Behavior Image Dataset ', Mendeley Data, v1, http://doi.org/10.17632/mzb4b6dff3.1».
Nota: Mendeley escribe «Sahin Afridi, Arafat» y «Nessa Moon, Ms. Nazmun» (con «Ms.» dentro del nombre); el artículo y Crossref escriben
Afridi / Moon con apellido simple. La forma APA de arriba sigue el artículo y Crossref (`family` = Afridi, Kafy, Moon, Shakil). Decisión de formato de quien cite.

**Artículo (Data in Brief).** Según Crossref (`volume` 60, `page` 111529, `published-print` 2025-06, `title`, 4 autores) y PMC:

> Afridi, A. S., Kafy, A., Moon, N. N., & Shakil, M. S. (2025). A multi-class driver behavior dataset for real-time detection and road safety enhancement. *Data in Brief, 60*, Article 111529. https://doi.org/10.1016/j.dib.2025.111529

Autores en PMC: «Afridi Arafat Sahin», «Kafy Arafath», «Moon Ms. Nazmun Nessa», «Shakil Md. Shahriar»; afiliación: «Department of Computer
Science and Engineering, Daffodil International University, Dhaka, Bangladesh». El artículo cita su propio conjunto así (ref. 3 del artículo): «Multi-class driver behavior dataset … Zenodo 2025 10.5281/zenodo.14908802».

**Verificación del «Afridi et al., 2024» del enunciado.** El primer autor es **Afridi** (confirmado en M, A y C). El año **2024** es el del
conjunto en Mendeley (publicado el 15-nov-2024); el **artículo es de 2025** (Crossref: 2025-06; PMC: publicado en línea el 2025-04-04). El
enunciado cita el conjunto, no el artículo; si se cita el artículo, el año es 2025.

**Registro de Zenodo (depósito que el artículo declara; no es el DOI que usa el enunciado).** Zenodo: título «Multi-Class Driver Behavior Image Dataset», DOI 10.5281/zenodo.14908802, publicado 2025-02-25, licencia `cc-by-4.0`,
archivos: `Multi-Class Driver Behavior Image Dataset.zip` (2 556 847 360 bytes) y `DATA USE AGREEMENT.docx`. Los creadores listados difieren en la ortografía de uno de los nombres: «Shakil, Shariear» (Zenodo) frente a «Shakil, Md. Shahriar» (Mendeley y artículo).

## 2. Licencia y qué exige

- **Conjunto (M):** campo de licencia «CC BY 4.0»; descripción de Mendeley de esa licencia: «You can share, copy and modify this dataset so long as you give appropriate credit, provide a link to the CC BY license, and indicate if changes were made, but you may not do so in a way that suggests the rights holder has endorsed you or your use of the dataset. Note that further permission may be required for any content within the dataset that is identified as belonging to a third party.»
- **Artículo (A y C):** «© 2025 The Author(s) … This is an open access article under the CC BY license (http://creativecommons.org/licenses/by/4.0/).» Crossref registra la licencia `creativecommons.org/licenses/by/4.0/` (versión de registro, desde 2025-03-26) y © «2025 The Author(s). Published by Elsevier Inc.».
- **Zenodo (Z):** licencia `cc-by-4.0`. Pero el mismo depósito incluye `DATA USE AGREEMENT.docx` (ver contradicción C-6) con otras condiciones: «The Dataset is intended for academic research and non-commercial use»; «Recipient shall not attempt to identify or re-identify any individuals depicted in the Dataset»; «Recipient shall not redistribute, sell, or otherwise share the Dataset with third parties without explicit written permission from DIU»; «Recipient agrees to acknowledge DIU in any publications …» (§7a, con la cita de Mendeley arriba) y «Recipient shall provide DIU with a copy of any proposed publication or presentation at least thirty (30) days prior to submission for review and comment» (§7b). Es una plantilla con campos en blanco ([RECIPIENT ORGANIZATION]); `TODO(dato-faltante)`: si se aplica a quien descarga de Mendeley.
- **Qué exige CC BY 4.0 en la práctica:** atribución (crédito apropiado), enlace a la licencia e indicar si se hicieron cambios (según la descripción de Mendeley citada arriba).

## 3. Cómo se recolectaron las imágenes (según las fuentes)

- **Lugar.** M: «Collected in Ashulia, Dhaka, Bangladesh, in October 2024». A, §2: «captured in Ashulia, Dhaka, Bangladesh». A, Tabla de especificaciones: «The photos were taken in Savar, Dhaka, Bangladesh»; fuente de datos «Daffodil International University, Birulia. Zone: Savar, Dhaka-1216 … Latitude: 23.5234° N, Longitude: 90.1915° E».
- **Periodo.** M y A (Tabla de especificaciones): «October 2024». A, §2: «Data collection spanned over a period of 30 days, with each driver being monitored for approximately 1–2 hours per day.»
- **Dispositivos.** A, Tabla de especificaciones: «using two separate personal cell phone cameras in both private vehicles and public buses». A, §3.1: «The dataset was collected using two smartphones: • iPhone 11: Equipped with a dual-lens camera system (12MP wide-angle and 12MP ultra-wide-angle lenses) … • Moto Edge 50 Fusion: Features a 50MP primary lens and a 13MP ultra-wide lens …». M: «The photos were taken using personal mobile phones».
- **Tipos de vehículo.** M: «within both private vehicles and public buses» / «personal cars». A: «both private vehicles and public buses». **Cuántos vehículos o buses: `TODO(dato-faltante)`** (no se declara).
- **Participantes.** A, §2: «The study involved 178 drivers aged 20–50 years».
- **Condiciones de iluminación.** A, §2: «images were captured from multiple angles and under different lighting conditions, such as daylight, low light, and nighttime»; «Data collection was conducted across a variety of settings, including urban roads and highways».
- **Posición de la cámara.** `TODO(dato-faltante)`: ninguna fuente dice dónde se colocó la cámara dentro del vehículo. Solo: «images were captured from multiple angles» (A, §2).
- **Consentimiento y ética.** A, «Ethics Statement»: «all participants provided informed consent before data collection. To ensure privacy and confidentiality, no identifiable or personal information was collected during image capture. With the help of the drivers, the photos were taken in a controlled and safe manner, with no one injured.» (Ver C-6 sobre rostros visibles.)
- **Anotación.** A, §2: «Each image was manually annotated into one of five behavior classes»; A, §5: «High-Quality Annotations: Expert-validated labels ensure robust dataset reliability.» `TODO(dato-faltante)`: quién anotó, cuántos anotadores, acuerdo entre anotadores.

## 4. Las clases (nombres y definiciones de los autores)

Artículo, Tabla 1 (nombres de la columna «Class Name» y su descripción):

| Nombre en Tabla 1 | Descripción citada |
|---|---|
| Safe Driving | «Driving with complete focus, no distractions. The driver maintains good posture and a firm grip on the steering wheel while paying close attention to the road.» |
| Talking phone | «The driver is using the phone in their hand or holding it to their ear while making a phone call. …» |
| Texting phone | «The driver is texting while driving, which significantly diverts their attention from the road.» |
| Turning | «The driver is turning the car, requiring full attention to ensure the maneuver is performed safely.» |
| Others | «This category covers various distracting behaviors, such as talking to passengers, eating, drinking, or sleeping while driving. …» |

Los nombres cambian según la sección del artículo: §2.1 usa «Safe Driving, Turning, Talking on the Phone, Texting on the Phone, Others»; §3.4 usa «Safe Driving, Turning, Texting, Talking Phone and Other»; el resumen usa «Safe Driving, Talking on the Phone, Texting, Turning, and Other Distracting Behaviors»; §3.3 usa «Other Distractions».

Mendeley (M), descripción: «I. Safe Driving: Images showing a driver who seems to be paying attention to the road, both hands on the wheel, and concentrated or 1 hand on the steering wheel and other on the gear stick. … II. Turning: Photographs that show drivers changing direction during turns by moving their heads or full bodies. … III. Texting Phone: Pictures of drivers using their phones, whether it is to type messages or to interact with the screen. … IV. Talking Phones: When drivers talk on their phones or hold them up to their ears while driving a vehicle. … V. Others: Contains any actions that go against safe driving practices, like drinking water or anything while driving, sleeping while driving, or talking with someone behind while driving.»

**«Otros comportamientos riesgosos» (clase «Others»)** agrupa, según el artículo: hablar con pasajeros, comer, beber, dormir; según Mendeley: beber agua u otra cosa, dormir, hablar con alguien de atrás. M además dice en su resumen: «other potentially risky behaviors, such as drowsy driving».

## 5. Conteos que declaran los autores

A, §2.1 «Dataset statistics»: «Safe Driving: 1679 images; Turning: 1343 images; Talking on the Phone: 1513 images; Texting on the Phone: 1561 images; Others: 1190 images». Total declarado: «7286 high-resolution images» (resumen y §2). La suma de las cinco clases es 1679 + 1343 + 1513 + 1561 + 1190 = 7286 (cálculo nuestro; coincide).
Resolución declarada: A, §2.1: «Each image has a resolution of 400 × 600 pixels». Formato: A, Tabla de especificaciones, «Type of data: JPEG». M dice «high-resolution photos» sin cifras.
- **Originales vs. aumentadas:** el artículo **no** dice si las 7286 son originales, aumentadas o mezcla; `TODO(dato-faltante)`. Ver §6 y C-2 a C-4.
- **Por tipo de vehículo:** `TODO(dato-faltante)` (no hay conteos).
- **Conteos de Mendeley:** `TODO(dato-faltante)` (la página no los da; la lista de archivos no se pudo leer).

## 6. Preprocesamiento y aumento de datos

Citas del artículo (A):
- §3.2 «Preprocessing steps»: «Noise Reduction: Impulse noise was removed using non-linear median filtering»; «Contrast Enhancement: Histogram equalization was used to adjust for irregular lighting and improve contrast»; «Image Resizing: All images were resized to a fixed dimension of 224 × 224 pixels to meet the input requirements of deep learning models.»
- §3.3 «Data augmentation techniques»: «Online data augmentation techniques were applied during the training process … Random Rotation (up to 15°) • Horizontal Flipping • Brightness Adjustment • Random Cropping. Augmentation was performed online to avoid introducing bias and to ensure that the dataset remains suitable for unbiased evaluation.»
- §3.3 (párrafo «Data Augmentation») y §3.4: «Each class was saved in a separate folder. Data augmentation was used to increase the variability of the dataset by simulating various real-world scenarios using techniques such as rotating, flipping, zooming, brightness adjustment, and cropping. … Extended images were stored in the same folder as their corresponding original class to ensure that they inherited the correct labels without requiring additional manual intervention.»
- §3.4: «The expansion process significantly expanded the data set by providing each class with a set of unique image variations.» Texto parecido en §3.1: «The expansion process significantly expanded the data set by providing each class with a set of unique image variations.»
- Fig. 2 (texto): «a confusion matrix for an augmented dataset … the top-left cell shows that 1450 instances of "Safe Driving" were correctly predicted as "Safe Driving," while 30 instances were incorrectly predicted as "Turning."»

Lo que el artículo **no** da (`TODO(dato-faltante)`): cuántas variantes por imagen original; parámetros de zoom, brillo y recorte (solo «up to 15°» para la rotación); si las originales siguen en las carpetas junto con las aumentadas; **cómo identificar en los archivos cuáles imágenes son aumentadas y de qué original provienen** (solo dice que se guardan «in the same folder as their corresponding original class»; no describe nombres de archivo); número de imágenes aumentadas por clase (la Tabla 2 «Augmented images of Driver behavior detection dataset» es una imagen que no se leyó).
**Partición propuesta por los autores:** ninguna encontrada en el texto (`TODO(dato-faltante)`); los autores no definen train/val/test. El artículo sí menciona CNN (VGG16, ResNet50, InceptionV3, Xception) como uso previsto (§ «Value of the Data», viñeta Machine learning).

Mendeley (M): «Because the images are unprocessed and unannotated, there is freedom in how machine learning applications pre-process them.»

## 7. Etiquetas de tipo de vehículo u otras variables

El artículo menciona «Vehicle classification» entre las palabras clave y que el conjunto «includes variations in lighting, vehicle type, and driving conditions» (§2.1), pero **no dice que haya una etiqueta de tipo de vehículo, ni de iluminación ni de ángulo** en los archivos. Lo único que describe es la organización «Each class was saved in a separate folder» (§3.3/§3.4), o sea, solo la etiqueta de clase por carpeta. M: «they differ in terms of vehicle type and illumination». `TODO(dato-faltante)`: metadatos por imagen; confirmar al abrir el archivo descargado.

## 8. Limitaciones declaradas y usos previstos

- Limitaciones (A, §6): «its geographic focus on Dhaka, Bangladesh, limits its global applicability»; «Behavioral Complexity: … it does not yet include more nuanced actions such as drowsiness, aggressive driving, and reckless lane changes»; «Limited Sensor Modalities: The dataset primarily relies on smartphone cameras … The absence of depth sensors, infrared cameras, or multi-modal data sources … may limit its applicability in low-light conditions or drowsiness detection.»
- Usos previstos (A, «Value of the Data»): «Improving road safety», «Real-time monitoring», «Machine learning and computer vision: … train and evaluate deep learning models … CNNs such as VGG16, ResNet50, InceptionV3, and Xception», «Public Safety». Resumen: «can be used to train and evaluate machine learning models for real-time driver behavior detection». Direcciones futuras (§7): modelos ligeros para «mobile and edge devices».

## 9. Contradicciones y diferencias (sin resolver)

- **C-1 Dónde están los datos.** A declara «Repository name: Zenodo Data … 10.5281/zenodo.14908802» y no cita el DOI de Mendeley; el enunciado (Anexo) y M usan Mendeley (10.17632/mzb4b6dff3.1). Zenodo es de 2025-02-25; Mendeley, de 2024-11-15. `TODO(dato-faltante)`: si ambos depósitos tienen idéntico contenido (no se descargó ninguno).
- **C-2 Anotado vs. sin anotar.** M: «the images are unprocessed and unannotated». A: «Each image was manually annotated into one of five behavior classes» y «Expert-validated labels».
- **C-3 Sin procesar vs. procesadas / resolución.** M: «unprocessed». A: se aplicó filtro de mediana, ecualización de histograma y redimensionado a «224 × 224 pixels» (§3.2), pero §2.1 declara «400 × 600 pixels» por imagen. A, «Data Availability»: «Multi-Class Driver Behavior Image Dataset (Original data)», mientras que §3.3/§3.4 dicen que las aumentadas están guardadas en las mismas carpetas.
- **C-4 Aumento «online» vs. guardado.** A, §3.3: «Augmentation was performed online» (durante el entrenamiento, no se guardan) frente a §3.3/§3.4: «Extended images were stored in the same folder as their corresponding original class» y «The expansion process significantly expanded the data set». No queda claro si las 7286 incluyen imágenes aumentadas. La Fig. 2 se describe como matriz de confusión «for an augmented dataset» con 1450 aciertos solo en Safe Driving (la clase tiene 1679 imágenes declaradas); el artículo no explica la partición usada.
- **C-5 «Others» y la somnolencia.** M y el enunciado hablan de somnolencia en «otros» («drowsy driving», «somnolencia»); A lista «sleeping» en Tabla 1, pero §6 dice que el conjunto «does not yet include … drowsiness». Enunciado: «beber, voltear hacia atrás o somnolencia». A menciona «talking to passengers» (hablar con pasajeros); M, «talking with someone behind»; «voltear hacia atrás» no aparece con esas palabras en ninguna fuente.
- **C-6 Rostros, consentimiento y redistribución.** A, Ethics: «no identifiable or personal information was collected». El `DATA USE AGREEMENT.docx` de Zenodo dice que el conjunto «contains high-resolution images of drivers, some of which include visible faces», prohíbe re-identificar, y «shall not redistribute, sell, or otherwise share the Dataset with third parties without explicit written permission from DIU»; la licencia declarada es CC BY 4.0 (que sí permite compartir). Relevante para guardar imágenes en el repositorio (núcleo §5.5) y para el blog/la app. Decisión de uso: humano.
- **C-7 Lugar.** «Ashulia» (M; A §2) frente a «Savar» y «Birulia» (A, Tabla de especificaciones). Son nombres de la misma zona de Dhaka según la propia tabla («Zone: Savar»), pero el artículo no lo aclara. `TODO(dato-faltante)`.
- **C-8 Nombres de clase** distintos entre secciones del artículo y entre A y M (ver §4).
- **C-9 «Controlada» vs. «real».** A, Ethics: fotos tomadas «in a controlled and safe manner» «with the help of the drivers»; A, §1/§4 insisten en «naturalistic» y «Unlike staged datasets». El artículo no explica si los comportamientos (p. ej. texting) fueron actuados.
- **C-10 Año.** Enunciado «Afridi et al., 2024» frente al artículo, de 2025 (ver §1).
- **C-11 Ortografía de autores:** «Shakil, Md. Shahriar» (M, A) frente a «Shakil, Shariear» (Zenodo); «Moon, Ms. Nazmun Nessa» (A) frente a «Nessa Moon, Ms. Nazmun» (M).

## 10. Candidatos a hallazgo para la cacería

Ninguna IA de este equipo se contrastó aquí con un prompt guardado afirmando lo contrario; **no se reporta como alucinación**. Pasar al
cazador-alucinaciones, como datos del mundo real, la tensión entre «aumento previo» (§3.3/§3.4 del artículo) y «originales sin procesar» (Mendeley, «Data Availability» del artículo): cualquier afirmación de una IA sobre «el conjunto contiene N imágenes originales» o «sin aumento» debe contrastarse con el archivo medido, no con estas fuentes, que se contradicen.

Nivel de confianza: alto para autores, año, licencias, conteos por clase, dispositivos y número de conductores (texto copiado del XML de PMC y del HTML de Mendeley); medio para la equivalencia PMC ≡ versión de ScienceDirect (no se abrió ScienceDirect); bajo para lo marcado `TODO(dato-faltante)`.
