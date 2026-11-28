# CA-1 — Verificación adversarial del calendario exógeno de M1

Cazador de alucinaciones (Opus) · consulta de todas las fuentes: **2026-11-26** · prompt: `alucinaciones/prompts/CA-1-verificacion.md`.
Objeto: `docs/investigacion/CA-1_fuentes_calendario.md` (informe de IA, prompt `CA-1a.md`), `data/externos/m1/calendario_fuentes.yaml`,
`src/m1_demanda/calendario.py` y `data/processed/m1/calendario.parquet` (prompt `CA-1b.md`).
Método: cada fuente se descargó con `curl` (HTML) o como PDF; el texto se extrajo con PDFKit (PDF digitales) o con OCR de macOS
Vision (escaneados, marcado [OCR]); las tablas clave se miraron también como imagen ([vista]). Evidencias en
`alucinaciones/evidencias/CA-1/` (fragmentos, capturas y dos scripts reproducibles). No se modificó código, datos ni `registro.md`.

Veredicto global: **el parquet está bien**. Los 72 festivos y los 90 rangos de receso pasan sin diferencias de informe → YAML → parquet, y
todas las fechas de la muestra coinciden con los actos oficiales. Encontré **un error de razonamiento de la IA** (Sogamoso 2022) que
se copió al YAML y a `data/fuentes.md`, dos imprecisiones menores del informe y algunos problemas de las fuentes que conviene anotar.
Ninguno cambia un valor del parquet.

---------------------------------------------------------------------------------------------------

## 1. Ley 51 de 1983

| # | Afirmación del informe | Veredicto | Evidencia |
|---|---|---|---|
| 1.1 | Art. 1 num. 1 fija 1-ene, 6-ene, 19-mar, 1-may, 29-jun, 20-jul, 7-ago, 15-ago, 12-oct, 1-nov, 11-nov, 8-dic, 25-dic + Jueves y Viernes Santo, Ascensión, Corpus Christi, Sagrado Corazón | **CONFIRMADA** | Alcaldía de Bogotá: «primero de enero, seis de enero, diecinueve de marzo, primero de mayo, veintinueve de junio, veinte de julio, siete de agosto, quince de agosto, doce de octubre, primero de noviembre, once de noviembre, ocho de diciembre y veinticinco de diciembre, además de los días Jueves y Viernes Santos, Ascensión del Señor, Corpus Christi y Sagrado Corazón de Jesús». El mismo texto aparece en las sentencias C-107/94 y C-568/93. |
| 1.2 | Num. 2: se trasladan 6-ene, 19-mar, 29-jun, 15-ago, 12-oct, 1-nov, 11-nov, Ascensión, Corpus y Sagrado Corazón «cuando no caigan en día lunes»; los demás no se trasladan | **CONFIRMADA** | Procuraduría, Cancillería, Alcaldía de Bogotá y C-107/94 coinciden literalmente: «…cuando no caigan en día lunes se trasladarán al lunes siguiente a dicho día. Cuando las mencionadas festividades caigan en domingo, el descanso remunerado, igualmente se trasladará al lunes». |
| 1.3 | La copia de la Procuraduría omite «seis de enero» en el num. 1 | **CONFIRMADA** (y la de Cancillería también) | Las dos copias de Avance Jurídico dicen «primero de enero, diecinueve de marzo, primero de mayo…». La Alcaldía de Bogotá, la C-107/94 y la C-568/93 sí lo incluyen. El num. 2 lo trae en todas las copias, así que la regla no cambia. |
| 1.4 | «Discrepancia de fecha entre espejos»: 22-dic (Procuraduría/Cancillería) vs 6-dic (Alcaldía de Bogotá) | **CONFIRMADA, pero mal explicada** | No son dos versiones de un mismo dato. La propia copia de la Procuraduría trae las dos fechas: «Dada en Bogotá, D.E., a los seis días del mes de diciembre de mil novecientos ochenta y tres» (firma de los presidentes del Congreso) y «Publíquese y ejecútese. Bogotá D.E., 22 de diciembre de 1983. BELISARIO BETANCUR» (sanción). El art. 4 dice «rige desde la fecha de su sanción», así que la cita con 22-dic-1983 (D. O. 36.428, 30-dic-1983) es la correcta. La ficha de Bogotá usa la fecha del «Dada en» («(Diciembre 06)», «Fecha de Expedición: 06/12/1983»). No es un error de IA: es un dato que conviene aclarar en `data/fuentes.md`. |
| 1.5 | Vigencia: arts. 1 y 2 exequibles en C-568 del 9-dic-1993; la C-107 del 10-mar-1994 ordenó «estarse a lo resuelto» | **CONFIRMADA** | C-568/93 (M. P. Fabio Morón Díaz, «diciembre nueve (9) de … (1993)»): «Primero.- Declarar EXEQUIBLES … los artículos 1o. y 2o. de la Ley 51 de 1983». C-107/94 (M. P. **Carlos Gaviria Díaz**, «diez (10) de marzo de … (1994)»): «ESTAR A LO RESUELTO EN LA SENTENCIA No. C-568 del 9 de diciembre de 1993». Esto cierra el `TODO(cita)` del ponente. |
| 1.6 | «No encontré nota de derogatoria ni modificación» | **NO VERIFICABLE** (sin contradicción) | Función Pública no abre por un error de certificado TLS (no lo salté). Secretaría del Senado da `ECONNREFUSED` y SUIN-Juriscol carga por JavaScript. Ninguna de las copias abiertas trae notas de modificación. |
| 1.7 | Num. 2: el informe cita «los que caigan en domingo también pasan al lunes» como «resumen de la copia de Bogotá» | **IMPRECISA** (no es hallazgo) | Esa frase no está en la página. Es la paráfrasis del resumidor de la herramienta de lectura. El informe sí la presenta como «resumen», y el texto literal dice lo mismo (fila 1.2). |

URLs: https://apps.procuraduria.gov.co/gd_1952/docs/l0051_83.htm · https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=4954 ·
https://cancilleria.gov.co/sites/default/files/Normograma/docs/ley_0051_1983.htm · https://www.corteconstitucional.gov.co/relatoria/1994/C-107-94.htm ·
https://www.corteconstitucional.gov.co/relatoria/1993/C-568-93.htm. Fragmentos: `alucinaciones/evidencias/CA-1/fragmentos_fuentes.txt`.

## 2. Las 72 fechas de festivos 2021–2024

| # | Afirmación | Veredicto | Evidencia |
|---|---|---|---|
| 2.1 | Las tablas del informe §2 (18 × 4) = el parquet (`festivo`, `festivo_nombre`) | **CONFIRMADA** | `comparar_informe_yaml_parquet.py`: informe 72, parquet 72, 0 fechas de más o de menos y 0 nombres distintos. Los días de la semana del informe también están bien. |
| 2.2 | Las fechas salen de la regla de la Ley 51 | **CONFIRMADA** (experimento reproducible) | `recalculo_festivos.py` recalcula todo sin `dateutil` ni el código del repo: Pascua con el algoritmo gregoriano anónimo, escrito aparte, y la regla del num. 1–2. Pascuas 2021-04-04, 2022-04-17, 2023-04-09, 2024-03-31. Resultado: «esperado 72 parquet 72 · solo esperado: [] · solo parquet: []». |
| 2.3 | Pascua de cada año, contrastada con los actos escolares | **CONFIRMADA** | Sogamoso Dec. 326/2020 [OCR]: «Semana Santa del 29 de marzo al 04 de Abril de 2021». Dec. 333/2021 [vista]: «Semana Santa del 11 al 17 de Abril de 2022». Bogotá Res. 3947/2023 [OCR]: «Del 25 al 31 de marzo de 2024». Los domingos coinciden con el cálculo. |
| 2.4 | ¿Existe una lista anual **oficial** de festivos? | **NO VERIFICABLE** (no la encontré) | Dos búsquedas restringidas a `gov.co` no la devuelven. Contraste secundario (medio público, no normativo): Radio Nacional de Colombia (26-ene-2022) lista los 18 de 2022 y RTVC Noticias (1-ago-2024) los de 2024. Las **36/36** fechas coinciden con el parquet, incluidas Ascensión 30-may-2022 y 13-may-2024, Corpus 20-jun-2022 y 3-jun-2024, y Sagrado Corazón 27-jun-2022 y 10-jun-2024. https://radionacional.co/cultura/ferias-y-fiestas/dias-festivos-en-colombia-2022 · https://www.rtvcnoticias.com/festivos-2024-puentes-feriados-colombia-cuando |
| 2.5 | Ascensión = Pascua+39 (jueves) → lunes Pascua+43 | **CONFIRMADA** (copia no vaticana) | *Normas universales sobre el año litúrgico*, n. 25: «On the fortieth day after Easter the Ascension of the Lord is celebrated» (contando el domingo como día 1, es P+39). n. 6: «the Sunday after Pentecost is the Solemnity of the Most Holy Trinity». https://www.catholicculture.org/culture/library/view.cfm?id=10842 |
| 2.6 | Corpus Christi = P+60; Sagrado Corazón = P+68 | **NO VERIFICABLE en fuente primaria** (se mantiene `TODO(cita)`) | No encontré el *Calendarium Romanum Generale* en vatican.va. El motu proprio *Mysterii Paschalis* abierto en vatican.va no trae las fechas. Las fechas que resultan sí coinciden con los dos medios públicos de 2.4 en 2022 y 2024. |
| 2.7 | `festivo_trasladado`, `semana_santa` (28 días), `jueves_viernes_santo` (8 días) | **CONFIRMADA** (coherentes con la regla) | Se revisaron los 36 festivos no trasladados (p. ej. 1-nov-2021 y 15-ago-2022 caen en lunes y quedan en `False`). `puente` es un supuesto declarado y no tiene fuente que verificar. |

## 3. Recesos escolares (muestra: los 18 actos abiertos, con énfasis en los cuatro casos pedidos)

| # | Ciudad / año | Lo que dicen el informe y el YAML | Veredicto | Fragmento literal de la fuente |
|---|---|---|---|---|
| 3.1 | **Bogotá 2022**, Res. 2204/2021 | 13 semanas: 10–23 ene, 11–17 abr, 20 jun–10 jul, 10–16 oct, 5 dic–15 ene 2023. Encabezado 29-oct vs «Dada» 24-oct | **CONFIRMADA** (en dos copias) | Registro Distrital 7288 (texto digital) y MEN `articles-408776_ab_10.pdf` [OCR]: «Artículo 5. Receso estudiantil. Las trece (13) semanas calendario de receso estudiantil se distribuirán así: Del 10 al 23 de enero de 2022 (dos semanas). Del 11 al 17 de abril de 2022 (una semana). … Del 20 de junio al 10 de julio de 2022 (tres semanas). Del 10 al 16 de octubre de 2022 (una semana). Del 05 de diciembre de 2022 al 15 de enero de 2023». «RESOLUCIÓN N° 2204 (29 de octubre de 2021)» … «Dada en Bogotá, D. C., a los veinticuatro (24) días del mes de octubre de dos mil veintiuno (2021)». |
| 3.2 | Bogotá 2021, 2023, 2024 | Rangos del YAML | **CONFIRMADA** | 2021 (digital): «Del 29 de noviembre de 2021 al 9 de enero de 2022 (seis semanas)», y en el considerando: «… del receso estudiantil es el 10 de enero de 2021». 2023 y 2024 [OCR]: las cinco líneas de receso de cada año coinciden con el YAML. |
| 3.3 | **Cali 2022**, Res. 06395/2021 | 4 semanas del 27 jun al 24 jul | **CONFIRMADA** | Texto digital: «27 de junio de 2022 24 de julio de 2022 04 semana · 10 de octubre de 2022 16 de octubre de 2022 01 semana · 12 de diciembre de 2022 15 de enero de 2023 05 semanas · TOTAL 12 semanas»; «( 29 OCTUBRE DE 2021 )». |
| 3.4 | Cali 2021 | Receso; «Cinco (6) semanas» | **CONFIRMADA** | «06 de diciembre de 2021 16 de enero de 2022 Cinco (6) semanas». El considerando explica el vacío del 1 al 17 de enero: «el calendario escolar oficial 2020 finalizará el día l7de enero de 2021». |
| 3.5 | Cali 2021: modificaciones (informe §5, punto 4) | «Res. 06575 y 0002 (vacaciones docentes; no afectan receso según el texto de la Res. 06395…)» | **IMPRECISA** | La Res. 06395 dice que la 06575 ajustó «las vacaciones de los docentes», pero que la **0002** de 4-ene-2021 modificó el calendario «convirtiendo la semana lectiva del 25 al 31 de enero de 2021 en semana de desarrollo institucional». Esa semana quedó sin clases para los estudiantes. Sin efecto en el parquet: se usa la versión original, la 0002 salió 21 días antes (no era conocible con 30 días) y la fecha es anterior al 2021-06-01. |
| 3.6 | Cali 2023 (afiche) | «16 al 30 de enero»… 85 días | **CONFIRMADA la transcripción; la fuente es incoherente** | [vista] Afiche p. 4: «16 al 30 de enero · 3 al 9 de abril · 3 al 23 de julio · 9 al 15 de octubre · 11 de diciembre al 14 de enero de 2024». p. 3: lectivas «30 de enero al 2 de abril · 10 de abril al 25 de junio · 24 de julio al 08 de octubre · 16 de octubre al 10 de diciembre». El 30-ene sale a la vez como receso y como primer día lectivo. Además las lectivas suman 9+11+11+8 = 39 semanas y la semana del 26 jun al 2 jul no tiene rótulo. El informe y el YAML no lo notaron (confianza «media», ya marcada). |
| 3.7 | Sogamoso 2021, Dec. 326/2020 | Receso + 18–24 ene como sin clases | **CONFIRMADA** (con un supuesto ya declarado) | [OCR] «Una (1) semana del 29 de marzo al 04 abril del 2021, Tres (3) semanas del 21 de Junio al 11 de Julio 2021, una (1) semana del 11 al 17 de octubre de 2021 y siete (7) semanas a partir del 06 de Diciembre de 2021 al 23 de enero de 2022». «Primera (1) semana de actividades de Planeación y Organización institucional del 18 al 24 de Enero de 2021»; «Iniciación de clases … 25 de Enero de 2021»; «Dado en Sogamoso, a los, 22 OCT 2020». Que la semana del 18 al 24 de enero cuente como receso es una inferencia (desarrollo institucional, sin estudiantes), y la nota del YAML ya lo dice. |
| 3.8 | **Sogamoso 2022**, Dec. 333/2021 | Rangos de receso | **CONFIRMADA** | [vista] «Doce (12) semanas de receso estudiantil distribuidas así: Una (1) semana del 17 al 23 de enero del 2022, Una (1) semana del 11 al 17 de abril de 2022, Tres (3) semanas del 04 al 24 Julio de 2022, Una (1) semana del 10 al 16 de octubre de 2022 y Seis (6) semanas a partir del 05 de Diciembre de 2022 al 15 de enero de 2023»; «(28 de Octubre de 2021)». |
| 3.9 | **Sogamoso 2022**: «el 2.º semestre va del 20-jun al 4-dic, **contradictorio** con el receso de julio: error del acto» (informe §3.2 y §6; YAML; `data/fuentes.md`) | | **REFUTADA** | [vista] «Cuarenta (40) semanas lectivas … primer semestre del 24 de Enero al 19 de Junio y segundo semestre del 20 de Junio al 04 de Diciembre de 2022». Los semestres son lapsos de calendario que incluyen recesos. El primero (24 ene–19 jun) tiene 21 semanas e incluye la de Semana Santa: 21 − 1 = 20. El segundo (20 jun–4 dic) tiene 24: 24 − 3 (julio) − 1 (octubre) = 20. Total 40, tal como dice el acto. Bogotá hace lo mismo en 2022: «Primer periodo semestral: del 24 de enero al 19 de junio de 2022 (20 semanas)» incluye el receso del 11 al 17 de abril. **El acto no tiene ninguna contradicción.** Ver candidato C-1. |
| 3.10 | **Pasto**: todo lo que no es «Desarrollo Académico» = sin clases | Inferencia aritmética | **CONFIRMADA** (y además con texto) | Res. 3085/2022 (digital): «los estudiantes tendrán cuarenta (40) semanas mínimo de actividades pedagógicas … y doce (12) semanas de receso estudiantil». La tabla da Desarrollo Académico 23 + 10 + 7 = 40, y las 12 semanas restantes son vacaciones o desarrollo institucional. El mismo acto exige que una semana de desarrollo institucional coincida con «la semana del mes de octubre en la que los estudiantes tienen receso estudiantil». La Res. 2706/2021 [OCR] trae el mismo texto. En 2021 (Res. 0064, digital) son 2 + 3 + 3 + 1 + 2 + 2 = 13 semanas sin clases, porque una semana académica pasó a desarrollo institucional («del 1 al 7 de febrero del año 2021», por la Directiva 18). |
| 3.11 | Pasto 2022: Res. 2706 del 7-dic-2021 | Fecha y rangos | **CONFIRMADA** | [vista] «RESOLUCIÓN 2706 DE 2021 ( 07 DIC 2021 )». [OCR] «Vacaciones 3 enero del 2022 al 16 enero 2022 · Desarrollo 17 a 30 enero · … Vacaciones 11 a 31 julio · … 10 al 16 octubre · … 5 al 18 diciembre · Vacaciones 19 diciembre del 2022 al 1 enero 2023». También confirma que es un caso dudoso de conocibilidad: la Circular 30 exigía expedirla «Antes del primero (1°) de noviembre de 2021». |
| 3.12 | **Ipiales 2023**, Res. 1078 | Receso de octubre del 16 al 22 | **CONFIRMADA** | [vista] «ARTÍCULO TERCERO. RECESO ESTUDIANTIL … 02 DE ENERO DE 2023 – 29 DE ENERO DE 2023 4 SEMANAS · 10 DE JULIO DE 2023 – 30 DE JULIO DE 2023 3 SEMANAS · 16 DE OCTUBRE DE 2023 – 22 DE OCTUBRE DE 2023 1 SEMANA · 04 DE DICIEMBRE DE 2023 – 31 DE DICEMBRE DE 2023 4 SEMANAS · TOTAL 12 SEMANAS»; «(26 de agosto del 2022)». Las lectivas («23 DE OCTUBRE DE 2023») cuadran. Que la semana sea la posterior al festivo y no la anterior, como pide el art. 2.3.3.1.11.1, es asunto del acto, no de la IA. |
| 3.13 | Ipiales 2021, 2022, 2024; Cali 2024 | Rangos del YAML | **CONFIRMADA** | [OCR] Ipiales 2021: «trece (13)» semanas, 7 rangos que coinciden con el YAML. 2022: 4 rangos y «12 SEMANAS». 2024: 6 rangos y «12 Semanas». Cali 2024: «( 31 OCTUBRE 2023 )», duraciones 02/01/03/01/05 y fechas finales que coinciden. |

Fragmentos completos: `alucinaciones/evidencias/CA-1/fragmentos_calendarios_escolares.txt`. Capturas: `ipiales_res1078_2022_art3_receso.png`,
`sogamoso_dec333_2021_p5.png`, `pasto_res2706_2021_encabezado.png`, `cali_afiche2023_p3_lectivas.png`, `cali_afiche2023_p4_receso.png`.
PDF: los del inventario §3.1 del informe, más https://www.redjurista.com/Compilaciones2018/tablas_GacetasBogota/2021/11/7288/r_seducacionbog_2204_2021.pdf.

## 4. Transcripción informe → YAML → parquet (`.venv/bin/python`)

Script: `alucinaciones/evidencias/CA-1/comparar_informe_yaml_parquet.py`; salida en `comparar_salida.txt`.

| # | Comparación | Resultado |
|---|---|---|
| 4.1 | Festivos del informe §2 vs parquet | 72 = 72, sin diferencias de fecha, nombre ni día de la semana. |
| 4.2 | Rangos del informe §3.3 vs YAML | 89 vs 90. El YAML tiene uno más, `sogamoso 2022-01-17..2022-01-23`, que **sí** está en el texto del Decreto 333 (fila 3.8) y en el propio §3.2 del informe, pero falta en la tabla §3.3. El implementador lo detectó y lo corrigió. Efecto nulo en el parquet porque el rango de 2021 (`2021-12-06..2022-01-23`) ya cubre esos días. |
| 4.3 | YAML vs parquet (5 columnas por ciudad) | 0 diferencias. Se cumple la regla «fuera de `cobertura` = nulo» (Cali 17 nulos, Sogamoso 369, Pasto 3, Ipiales 3). `vacaciones_escolares` es idéntica a `_11001`. |
| 4.4 | Semanas por año lectivo (días/7) | 12 en todos los casos salvo los que el acto declara distintos: Bogotá 2022 = 13 (literal), Ipiales 2021 = 13 (literal), Pasto 2021 = 13 (fila 3.10), Sogamoso 2021 = 13 (12 literales + la semana 18–24 ene inferida), Bogotá 2021 = 13,4 (incluye el supuesto del 1 al 10 de enero, sustentado en el considerando). Cali 2023 = 12,1 por el 30-ene del afiche, y Pasto e Ipiales 2024 por el borde del 1-ene. |

---------------------------------------------------------------------------------------------------

## 5. Candidatos a hallazgo (cacería, núcleo §9)

Solo cuentan errores de una IA con prompt literal guardado. Los presento con su peso real: **ninguno cambia un dato del parquet**.

### C-1 — Una «contradicción» inexistente en el Decreto 333 de 2021 de Sogamoso (M1 · Datos del mundo real)
- **1. Prompt literal:** `alucinaciones/prompts/CA-1a.md` (investigador-fuentes, Sonnet, 26-nov-2026). Pedía fragmentos literales y
  marcar contradicciones entre fuentes. Se propagó con `CA-1b.md` (implementador), que copió la nota al YAML y a `data/fuentes.md`.
- **2. Respuesta relevante de la IA:** informe §3.2: «(el mismo texto dice que el 2.º semestre va "del 20 de Junio al 04 de Diciembre",
  contradictorio con el receso de julio: error del acto; se toma la lista de receso.)». En §6 lo lista como discrepancia entre fuentes.
  En el YAML: «El acto dice que el 2.º semestre va del 20-jun al 4-dic, contradictorio con el receso de julio». En `data/fuentes.md`,
  bajo «Discrepancias entre fuentes»: «Sogamoso 2022: segundo semestre "del 20 de junio al 4 de diciembre" frente al receso del 4 al 24 de julio».
- **3. Cómo se sospechó:** un semestre que contiene semanas de receso es lo normal. El primer semestre del mismo decreto contiene la
  Semana Santa y nadie lo llamó contradicción.
- **4. Evidencia:** captura `alucinaciones/evidencias/CA-1/sogamoso_dec333_2021_p5.png` (num. 4 y 5 del decreto) y la aritmética de la
  fila 3.9: (21 − 1) + (24 − 3 − 1) = 20 + 20 = 40 semanas lectivas, como dice el acto. El patrón se repite en Bogotá 2022
  (`fragmentos_calendarios_escolares.txt`: «del 24 de enero al 19 de junio de 2022 (20 semanas)», con receso del 11 al 17 de abril dentro).
- **5. Corrección:** quitar la «contradicción» del informe §3.2 y §6, de la nota del bloque Sogamoso 2022 en el YAML y de
  `data/fuentes.md` (Discrepancias). Si se quiere dejar una nota, que diga: «los semestres son lapsos de calendario que incluyen
  recesos; 20 + 20 = 40 semanas».
- **6. Lección:** antes de declarar «error del acto», hacer la cuenta de semanas que el propio acto permite. La IA vio dos rangos que se
  solapan e infirió una contradicción sin comprobar la definición. Una afirmación así iba a terminar en el blog como «hallazgo de
  datos».
- **Estado:** candidato. Es real y está bien documentado, pero su impacto es bajo: no cambia ninguna fecha del parquet.

### C-2 (débil) — La Res. 0002/2021 de Cali descrita como «vacaciones docentes» (M1 · Datos del mundo real)
- **1. Prompt:** `CA-1a.md`. **2. Respuesta:** informe §5, punto 4: «Cali 2021 — modificada por Res. 06575 del 15-dic-2020 y Res. 0002 del
  4-ene-2021 (vacaciones docentes; no afectan receso según el texto de la Res. 06395, pero no leí esas dos)». **3. Sospecha:** al
  releer la Res. 06395. **4. Evidencia:** `fragmentos_calendarios_escolares.txt`, Cali 2022, considerandos: la 0002 modificó
  «convirtiendo la semana lectiva del 25 al 31 de enero de 2021 en semana de desarrollo institucional». **5. Corrección:** en el
  informe y en `data/fuentes.md`, describir la 0002 como «convirtió la semana lectiva 25–31 ene 2021 en desarrollo institucional
  (sin clases); no conocible con 30 días (expedida el 4-ene); fuera del periodo de entrenamiento». **6. Lección:** parafrasear un
  considerando solo después de leerlo; la IA dijo apoyarse en un texto que contradice su resumen.
- **Estado:** candidato débil (imprecisión, impacto nulo). Andrés y Camila deciden si cuenta.

### C-3 (débil) — La tabla §3.3 del informe omite un rango que su propio §3.2 cita (M1 · Datos del mundo real)
- **1. Prompt:** `CA-1a.md` (pedía las tablas «en un formato fácil de pasar a código»). **2. Respuesta:** §3.2 cita «Una (1) semana del
  17 al 23 de enero del 2022» para Sogamoso, pero la tabla ISO §3.3 pasa de `sogamoso,2021-12-06,2022-01-23` a
  `sogamoso,2022-04-11,2022-04-17`. **3. Sospecha:** lo detectó el implementador de `CA-1b` (nota del YAML), y yo lo confirmé con la
  comparación 4.2. **4. Evidencia:** `comparar_salida.txt` («solo yaml [('sogamoso', '2022-01-17', '2022-01-23')]») y la captura del
  decreto. **5. Corrección:** ya está aplicada en el YAML; falta añadir la línea al §3.3 del informe. **6. Lección:** comparar por
  código la tabla «para código» contra los fragmentos literales del mismo informe.
- **Estado:** candidato débil (omisión de transcripción sin efecto en el parquet, porque el rango de 2021 cubre esos días).

**No son candidatos** (son datos de las fuentes o ya los declaró la IA): las fechas 6-dic y 22-dic de la Ley 51 (fila 1.4), la omisión
de «seis de enero» en las copias de Avance Jurídico, las 13 semanas de Bogotá 2022, «Cinco (6) semanas» en Cali 2021, el 30-ene del
afiche de Cali 2023, Ipiales 2023 en la semana del 16 al 22 de octubre y la paráfrasis de la fila 1.7.

**Verificaciones correctas para la sección del registro:** regla y lista de la Ley 51 (1.1–1.2); vigencia (1.5); los 72 festivos por
recálculo independiente y por contraste con medios públicos (2.1–2.4); Ascensión (2.5); Bogotá 2021–2024, Cali 2021/2022/2024,
Sogamoso 2021/2022 (rangos), Pasto 2021–2023 e Ipiales 2021–2024 contra el acto (sección 3); la inferencia de Pasto (3.10); la
cadena informe → YAML → parquet (sección 4).

**Cobertura de la cacería** (según `registro.md` y esta verificación): Común–Código: H-01 (candidato). M1–Datos del mundo real: C-1
(y los débiles C-2 y C-3), todavía sin registrar. Con eso habría 2 categorías (Código y Datos del mundo real) y 1 de 3 módulos con
candidato. **Faltan** M2, M3 y una tercera categoría (Matemáticas, Bibliografía o Conceptos), y ninguno está confirmado todavía.

## 6. Correcciones necesarias (no aplicadas)

1. **YAML, Sogamoso 2022 (`nota`):** quitar «contradictorio con el receso de julio; se toma la lista de receso» (C-1).
2. **`data/fuentes.md`, «Discrepancias entre fuentes»:** quitar la línea de Sogamoso 2022 (C-1). En la de la Ley 51, aclarar que el
   6-dic es el «Dada en» del Congreso y el 22-dic la sanción, y que la ley rige desde la sanción (art. 4). Corregir la descripción de
   la Res. 0002/2021 de Cali (C-2).
3. **`data/fuentes.md` / lista de `TODO(cita)`:** cerrar «ponente de la C-107/1994» (Carlos Gaviria Díaz) y «sentencia C-568/1993
   abierta directamente» (abierta: M. P. Fabio Morón Díaz, 9-dic-1993, URL de la fila 1.5).
4. **YAML, Cali 2023:** añadir a la nota que el afiche se contradice (30-ene aparece como receso y como inicio de clases; lectivas = 39
   semanas; la semana del 26 jun al 2 jul queda sin rótulo). Camila decide si el 2023-01-30 queda `True` (literal del receso) o `False`
   (inicio de clases).
5. **Borde del 1-ene-2024 en Pasto e Ipiales:** hoy vale `False` aunque ningún acto lo cubre (el calendario 2023 termina el 31-dic y el
   2024 empieza el 2-ene). Según la decisión 5 de `CA-1b.md` («vacíos sin fuente → nulo»), debería ser `NA` (o `True` con un supuesto
   declarado). Ahora es un falso «hay clases» en un festivo. Bogotá, Cali y Sogamoso no tienen este problema.
6. **Informe CA-1, §3.3:** añadir `sogamoso,2022-01-17,2022-01-23` (C-3). En §1 (fila 1.4), cambiar «discrepancia entre espejos» por la
   explicación 6-dic/22-dic.
7. **Se mantienen abiertos:** `TODO(cita)` de las fuentes primarias de Corpus Christi (P+60) y Sagrado Corazón (P+68) (no encontré el
   *Calendarium Romanum* en vatican.va); lista anual oficial de festivos (no existe en `gov.co`, o no la encontré); vigencia de la Ley 51
   en Función Pública o SUIN (no accesibles).
8. Ningún cambio en `calendario.py`: la lógica de festivos, traslados, Semana Santa y cobertura reproduce la norma y el YAML sin
   diferencias. Solo la corrección 5 podría tocar el YAML (rangos o cobertura) o el código, según lo que decida Camila.
