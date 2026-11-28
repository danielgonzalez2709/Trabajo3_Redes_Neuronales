# CA-6 (verificación) — Marco legal y costos para flota propia, arrendada o convenios (M1, pregunta 4)

Verificador: cazador-alucinaciones (Opus). Prompt: `alucinaciones/prompts/CA-6a-verificacion.md`. Fecha de consulta de **todas**
las fuentes: **2026-11-27**. Objeto: `docs/investigacion/CA-6_costos_flota.md` (investigador-fuentes, Sonnet, prompt literal
`alucinaciones/prompts/CA-6a.md`). No se editó ese informe, ni `registro.md`, ni código o configs. Sin `git add/commit/push`.

Evidencia: `alucinaciones/evidencias/CA-6/` (copias HTML/PDF y su texto). Comprobación reproducible:
`alucinaciones/evidencias/CA-6/verificar.py` busca cada fragmento literal en las copias → `salida.txt` (40/40 fragmentos
encontrados, 2/2 ausencias confirmadas, código de salida 0). Los buscadores solo sirvieron para localizar URL; ninguna afirmación
de esta nota sale de un resumen de buscador. PDF extraídos con PDFKit; HTML convertido a texto.

Clasificación: CONFIRMADA / INCORRECTA / NO VERIFICABLE (con matiz *imprecisa* u *omisión* cuando corresponde).

## Veredicto global

**El informe es confiable en lo literal**: los 9 artículos citados del Decreto 1079 de 2015 existen con ese número, dicen
exactamente lo que el informe les atribuye y su procedencia del Decreto 171 de 2001 es correcta (contrastado con una segunda copia
oficial, SISJUR, del Decreto 171). Las cifras y frases del DANE (ICTIP) son exactas. **Ningún dato inventado.**
Fallas encontradas:
1. **Una inferencia incorrecta** (§8, punto 3): que «arrendar, no comprar» mueve «~un tercio de la estructura» de costos. Los
   costos fijos del ICTIP incluyen la mano de obra de conductores, que es casi toda su variación en 2026. → candidato a hallazgo
   (categoría Conceptos), abajo.
2. **Una omisión material** frente a lo que pedía el prompt CA-6a (puntos 1b y 1d): el informe no vio el art. 2.2.1.6.3.5 del
   mismo Decreto 1079 (contratos de servicio especial con empresas de pasajeros por carretera «en períodos de alta demanda»),
   modificado por el **Decreto 1048 de 2026** (5-ago-2026), ni la **Resolución 264 de 2020** de MinTransporte, que fija los
   periodos de alta demanda y los requisitos de convenios y contratos. Con eso se cierra el `TODO(cita)` T-6 y se precisa T-5.
   No es una afirmación falsa (el informe dejó T-6 abierto), pero su «no mezclar» con el capítulo de servicio especial es un
   consejo equivocado para esta pregunta.
3. **Dos imprecisiones menores** en el DANE (periodo del año corrido y fecha base) y una en la lectura del tope del 20 %.

Vigencia: el **Decreto 1017 de 2025 solo toca el Capítulo 7 (carga)**; ningún decreto de 2025–2026 hallado modifica el Capítulo 4
(pasajeros por carretera). Los artículos citados siguen vigentes, hasta donde se pudo comprobar (ver §2 y su límite).

## Tabla resumen

| # | Afirmación del informe | Veredicto | Evidencia (archivo en `evidencias/CA-6/`) | Corrección propuesta |
|---|---|---|---|---|
| V-1 | L-1: art. 2.2.1.4.7.1 (Dec. 171, art. 48): mínimo 3 % «de capacidad transportadora mínima» propia o de socios, ≥ 1 vehículo, incluye leasing; art. 2.2.1.4.8.3: vehículos propios se entienden vinculados sin contrato | CONFIRMADA (cita literal exacta). Matiz: el resumen §1 dice «3 % de la capacidad transportadora»; la norma dice «de capacidad transportadora **mínima**» | `fp_decreto1079.txt`; 2.ª copia `sisjur_decreto171_2001.txt` (arts. 48 y 54) | En el resumen escribir «3 % de la capacidad transportadora **mínima**» |
| V-2 | L-2: arts. 2.2.1.4.8.1–8.3 (arts. 52–54) y 2.2.1.4.9.2 (art. 62): solo equipos registrados; vinculación = contrato + tarjeta de operación; tarjeta según la capacidad fijada | CONFIRMADA | `fp_decreto1079.txt`; `sisjur_decreto171_2001.txt` | — |
| V-3 | L-3: art. 2.2.1.4.7.2 (art. 49): máxima ≤ mínima + 20 %; parque dentro de [mínima, máxima] | CONFIRMADA (literal) | ídem | — |
| V-3b | L-3/§8.2 (lectura): «un pico de más de +20 % sobre la mínima no se cubre con flota propia o vinculada» y «la brecha solo se cubre vía convenio o servicio especial» | IMPRECISA. El límite que ata es la capacidad **máxima fijada** por MinTransporte, que puede ser menor que mínima + 20 %. El mismo artículo prevé fijar nueva capacidad mínima «por el otorgamiento de nuevos servicios» con revisión del plan de rodamiento (vía lenta, no de temporada). Que el convenio sirva para cubrir la brecha no lo dice la norma: el convenio racionaliza equipos sobre rutas ya autorizadas (Res. 264/2020 art. 4 par. 1 exige incluir «la totalidad de la frecuencia u horario de la ruta») | `fp_decreto1079.txt`; `res_264_2020_mintransporte.txt` | «El parque propio + vinculado no puede pasar la capacidad **máxima fijada** a la empresa (≤ mínima + 20 %). El refuerzo de temporada previsto por la norma es el contrato con servicio especial (V-6, V-7); el convenio es una figura estable (≤ 2 años, ruta completa), no un refuerzo de pico» |
| V-4 | L-4: art. 2.2.1.4.6.8 (art. 42): convenios autorizados por MinTransporte entre empresas habilitadas, solo sobre servicios ya autorizados | CONFIRMADA. Se refuerza: Res. 264/2020 arts. 3–5 (trámite, vigencia ≤ 2 años prorrogable, autorización en 15 días hábiles) respalda «no es una compra de capacidad por un día» | `fp_decreto1079.txt`; `sisjur_decreto171_2001.txt`; `res_264_2020_mintransporte.txt` | Añadir la Res. 264/2020 como reglamentación del convenio |
| V-5 | L-5: parágrafo del art. 2.2.1.4.6.8: en temporada alta, contratos con empresas de servicio especial, solo en rutas autorizadas; única mención literal de «temporada alta» en el Decreto 1079 | CONFIRMADA (1 sola mención; `verificar.py` la cuenta). 2.ª copia: Dec. 171 art. 42 parágrafo (SISJUR) y el considerando de la Res. 264/2020 lo transcribe | `fp_decreto1079.txt`; `sisjur_decreto171_2001.txt`; `res_264_2020_mintransporte.txt` | — |
| V-6 | (omisión) El Decreto 1079 no regula el lado del servicio especial ni define «temporada alta» (T-6 abierto); «no mezclar» el Cap. 6 | OMISIÓN MATERIAL. Art. 2.2.1.6.3.5 (ya estaba en la versión FP que el investigador descargó): servicio especial puede «suplir las necesidades de parque automotor» de pasajeros por carretera «en períodos de alta demanda que defina el Ministerio de Transporte». **Modificado por el Decreto 1048 de 2026, art. 7** (5-ago-2026): exige planilla de despacho de la empresa de carretera, reporte a Supertransporte y MinTransporte, y remite a la Res. 264 de 2020 | `fp_decreto1079.txt` (texto anterior); `sisjur_decreto1048_2026.txt` y `runt_decreto1048_2026.txt` (texto nuevo) | Añadir L-10: art. 2.2.1.6.3.5 (mod. Dec. 1048/2026, art. 7) como el otro lado del refuerzo de temporada; retirar el «no mezclar» para este artículo |
| V-7 | T-6: falta la norma que defina temporada alta | Resuelto: **Res. 264 de 2020, art. 8** («Periodos de alta demanda para la definición de contratos»): Semana Santa (del viernes anterior al domingo de ramos al lunes de pascua); 5-jun a 31-jul; semana de receso escolar de octubre; **10-dic a 15-ene**; puentes festivos de lunes (viernes a martes). Arts. 6–7: contenido del contrato, reporte, listado de Supertransporte ≥ 1 día antes; art. 6 par. 3 permite ampliar el número de vehículos si sigue la demanda insatisfecha. Límite: copia firmada escaneada (OCR) alojada en bogota.gov.co; la fecha exacta no es legible en el OCR → fecha NO VERIFICABLE; su vigencia en 2026 se infiere de que el Dec. 1048/2026 la cita como vigente («o la norma que la modifique o sustituya»), no de un normograma | `res_264_2020_mintransporte.{pdf,txt}`; `sisjur_decreto1048_2026.txt` | Cerrar T-6 con la Res. 264/2020 art. 8 (buscar copia en el normograma de MinTransporte para fecha y vigencia). Útil para M1: el horizonte de prueba de dic-2023 cae en «10-dic a 15-ene» |
| V-8 | Arriendo simple: el Cap. 4 no tiene esa figura; solo leasing (T-5) | CONFIRMADA como ausencia en el Cap. 4 (todas las menciones de «arrend» en el Cap. 4 son leasing). Ley 336/1996 art. 22 delega en el reglamento «la forma de vinculación de los equipos» y «las formas alternas»; art. 23: solo equipos registrados. El Cap. 6 (servicio especial) sí admite **renting** como forma de tenencia de los vehículos de la empresa especial (art. 2.2.1.6.8.1). No hallé norma que regule o prohíba el arriendo simple entre empresas de carretera; la vía regulada de «uso temporal de vehículos de otra empresa» es el contrato con servicio especial (V-6, V-7) | `fp_decreto1079.txt`; `senado_ley_336_1996.txt`; `sisjur_decreto1048_2026.txt` | En el informe: «arrendada» = contrato con empresa de servicio especial en periodos de alta demanda (art. 2.2.1.6.3.5 + Res. 264/2020), no arriendo simple. T-5 queda «sin norma específica encontrada; no se revisaron conceptos de MinTransporte» |
| V-9 | L-6 (art. 2.2.1.4.1.1, Dec. 171 art. 8; art. 2.2.1.4.6.5, art. 39) y L-7 (art. 2.2.1.4.6.3, art. 37) | CONFIRMADA (literal y procedencia) | `fp_decreto1079.txt` | — |
| V-10 | Nota de alcance: en servicio especial el contrato de vinculación de flota ≤ 2 años y sin renovaciones automáticas | CONFIRMADA pero con texto **desactualizado**: el art. 2.2.1.6.8.1 fue sustituido por el Dec. 1048/2026, art. 15; la regla sigue («no podrá ser superior a dos (2) años»; «No podrá pactarse … las renovaciones automáticas») y ahora exige pactar la prórroga por escrito | `sisjur_decreto1048_2026.txt` | Citar «art. 2.2.1.6.8.1, mod. Dec. 1048/2026, art. 15» |
| V-11 | Vigencia: cabecera FP «Adicionado y modificado por el Decreto 1017 de 2025», actualizada al 21-sep-2025; 39 vigencias | CONFIRMADA. Observación: la misma página FP dice en el resumen «ÚLTIMA FECHA DE ACTUALIZACIÓN: 24 DE FEBRERO DE 2023» y su lista de 39 vigencias no incluye el 1017 (solo llega al Dec. 402/2025): la página es internamente inconsistente | `fp_decreto1079.txt` (líneas 38–48) | — |
| V-12 | (T-2) ¿El Decreto 1017 de 2025 u otro posterior cambia los artículos citados? | **No los cambia.** Dec. 1017/2025 (21-sep-2025, Diario Oficial 53.250): «modifican, adicionan y derogan unos artículos del Capítulo 7» (carga); cero menciones de «2.2.1.4.». Decretos de 2025–2026 en el compilatorio SISJUR del 1079: 402/2025 (bicicleta), 1017/2025 (carga), 770/2026 (infraestructura logística), 998/2026 (fluvial), 999/2026 (educación–transporte escolar), 1000/2026 (Título 8), 1001/2026 (taxi), **1048/2026 (Cap. 6, servicio especial; ver V-6)**, 1529/2026 (puertos). Ninguno, por su epígrafe, toca el Cap. 4. Límite: el compilatorio SISJUR es informativo; SUIN-Juriscol no respondió (timeout); no revisé el texto completo de 998–1001 ni 1529, solo su epígrafe | `fp_decreto1017_2025.txt`; `ramajudicial_decreto1017_2025.txt`; `sisjur_decreto1079_compilatorio.txt` | Cerrar T-2: «Cap. 4 sin cambios hasta el Dec. 1529/2026 (14-oct-2026) según SISJUR; el Dec. 1048/2026 modifica el art. 2.2.1.6.3.5 relacionado» |
| V-13 | C-1: pesos ICTIP (31,00 / 8,78 / 32,99 / 20,39 / 6,84; total 100,00), boletín del 22-oct-2026, URL | CONFIRMADA (Tabla 1, pág. 3; portada «22 de octubre de 2026») | `ictip_bol_IIItrim2026.{pdf,txt}` | — |
| V-13b | C-1: «ponderaciones … indexadas a dic-2015» | IMPRECISA: «La base del índice es el cuarto trimestre de 2015» (boletín pág. 2; metodología: «IV trimestre de 2015=100») | ídem; `ictip_met_v2.txt` | «base IV trimestre de 2015 = 100» |
| V-14 | C-2: variación trimestral −0,13 %; año corrido 7,77 %; mano de obra de conductores y ayudantes 22,11 % (año corrido) | CONFIRMADA (págs. 3, 5 y 6; Tabla 4: «22,11 4,72») | `ictip_bol_IIItrim2026.txt` | — |
| V-14b | C-2: «año corrido (sep-2026 vs. dic-2025)» | IMPRECISA: el DANE lo define como «tercer trimestre (julio-septiembre) de 2026 en comparación al último trimestre de 2025 (octubre-diciembre)» | ídem (pág. 5) | «III trim. 2026 vs. IV trim. 2025» |
| V-15 | C-3: frase literal «ausencia de un mercado establecido de alquiler de vehículos de pasajeros», DSO-ICTIP-MET-001 v2, pág. 10 | CONFIRMADA (pág. 10 del PDF; v2, fecha 26/Feb/2018). Matiz: es la conclusión sobre la pregunta de la encuesta básica de **2015** «¿En cuánto alquilaría su vehículo mensualmente?» (solo uso del vehículo, sin conductor ni combustible); no es una afirmación sobre el mercado actual ni sobre contratos con conductor como los de la Res. 264 | `ictip_met_v2.{pdf,txt}` | Decir «según la encuesta básica de 2015 (DANE, 2018)» y acotar a alquiler del vehículo sin conductor |
| V-16 | C-4 (§2.1.3: excluye costos de la empresa) y C-5 (pág. 11: valor residual 20 %) | CONFIRMADAS | `ictip_met_v2.txt` | — |
| V-17 | C-1 «Total nacional; se publica también por clase: automóvil, campero, camioneta, microbús, buseta y bus» | CONFIRMADA (metodología: «automóvil, campero, camioneta, microbús, buseta y bus»; boletín pág. 12 remite al Anexo4 por clase de vehículo) | `ictip_met_v2.txt`; `ictip_bol_IIItrim2026.txt` | — |
| V-18 | §4 Límite: «el DANE advierte que se actualiza solo cuando se rehace la encuesta básica» | CONFIRMADA: «únicamente puede ser actualizada a partir de la aplicación y procesamiento de información de una encuesta básica» (nivel fijo) | `ictip_met_v2.txt` | — |
| V-19 | §8.3: «costos fijos ~33 % (incluye conductores)» | CONFIRMADA: «costos fijos (parqueaderos, seguros, costo del vehículo, impuestos y mano de obra)» | `ictip_met_v2.txt` | — |
| V-20 | §8.3: «una opción que reduzca costos fijos (arrendar, no comprar) mueve ~un tercio de la estructura» | **INCORRECTA (inferencia)**. Arrendar en vez de comprar solo sustituye la clase «Costo del vehículo y su apalancamiento», no los 32,99 % de costos fijos, que incluyen mano de obra, seguros, impuestos y parqueaderos. En el año corrido 2026 los costos fijos aportaron 4,83 p.p. y **solo la mano de obra aportó 4,72 p.p.** (Tablas 3 y 4): conductores son la parte principal de ese grupo. El peso de la clase «costo del vehículo» no está en el boletín (Anexo no abierto) | `ictip_met_v2.txt`; `ictip_bol_IIItrim2026.txt` | «Arrendar en vez de comprar sustituye el componente de capital (costo del vehículo y su apalancamiento), cuyo peso no conocemos (T-9); los costos de conductores, combustible y peajes se mantienen» → candidato CA6-1 |
| V-21 | §8.3: «el costo de conductores sube más rápido que el promedio (22,11 % vs. 7,77 %)» | CONFIRMADA | `ictip_bol_IIItrim2026.txt` | — |
| V-22 | §7: la página DANE de la encuesta dice «(ICTC)» por ICTIP | CONFIRMADA: «Índice de Costos de Transporte Intermunicipal de Pasajeros (ICTC)» | `dane_encuesta_costos_vinculados.txt` | — |
| V-23 | §5 (cifras de medios N-1…N-5) | NO VERIFICABLE y no se usan; el informe ya las marca como no citables y no abiertas. No las abrí | — | Mantener fuera |
| V-24 | §3: el YAML cita «arts. 2.2.1.4.7.3–2.2.1.4.7.4 (compila Decreto 171/2001, arts. 50–51)» | CONFIRMADA en sustancia (`configs/m1/operacion.yaml` línea 215: «…que compilan el Decreto 171/2001, arts. 50–51») | repo | — |

## Detalle de lo que pedía el encargo

**1. Artículos del Decreto 1079.** Fuente: Función Pública, Gestor Normativo,
https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=77889 (versión integrada al 21-sep-2025) → `fp_decreto1079.{html,txt}`.
Segunda copia: Decreto 171 de 2001 en SISJUR (Secretaría Jurídica Distrital de Bogotá),
https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=4306 → `sisjur_decreto171_2001.{html,txt}` (arts. 42, 48, 49, 52–54, 62,
mismo texto; art. 42 con nota «Reglamentado por la Resolución … 1018 de 2009», que la Res. 264/2020 derogó en su art. 13).
SUIN-Juriscol no respondió (timeout de 60 s).

**2. Vigencia posterior a sep-2025.** Decreto 1017 de 2025: Función Pública https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=264276
y Diario Oficial 53.250 del 21-sep-2025 (copia en Rama Judicial, SIDN). Objeto: Capítulo 7 (carga). Artículo 26 deroga solo
artículos 2.2.1.7.x. Decreto 1048 de 2026 (5-ago-2026): SISJUR https://sisjur.bogotajuridica.gov.co/sisjur/normas/Norma1.jsp?i=193979
y PDF firmado en RUNT https://www.runt.gov.co/sites/default/files/normas/Decreto%201048%20de%202026.pdf (el PDF es un escaneo; su
OCR coincide en número, fecha «-5AGO2026», objeto y art. 29). Compilatorio de modificaciones: SISJUR
https://sisjur.bogotajuridica.gov.co/sisjur/normas/Norma1.jsp?dt=S&i=73843.

**3. Arriendo simple.** Ver V-8. Ley 336 de 1996 desde la Secretaría del Senado
(http://www.secretariasenado.gov.co/senado/basedoc/ley_0336_1996.html, actualización del sitio 15-nov-2026).

**4. DANE ICTIP.** Boletín https://www.dane.gov.co/files/operaciones/ICTIP/bol-ICTIP-IIItrim2026.pdf (16 págs.) y metodología
https://www.dane.gov.co/files/investigaciones/fichas/transporte/DSO-ICTIP-MET-001-V2.pdf (27 págs.). Todo confirmado salvo V-13b y
V-14b (imprecisiones de paráfrasis).

**5. Otras afirmaciones usadas por la conclusión.** V-3b, V-6/V-7 y V-20 son las que cambian la recomendación de negocio.

## Correcciones propuestas (para quien edite el informe CA-6 o redacte la respuesta a la pregunta 4)

1. Sustituir el punto 3 de «Defendible» (§8) por la redacción de V-20; no cuantificar el ahorro de «arrendar» con el 32,99 %.
2. Añadir a la tabla legal: **L-10** art. 2.2.1.6.3.5 (mod. Dec. 1048/2026, art. 7) y **L-11** Res. 264 de 2020 arts. 3–9
   (convenios; contratos de alta demanda; periodos del art. 8; despacho en terminales). Cerrar T-2 y T-6; reformular T-5.
3. Reescribir el tope (L-3, §8.1–8.2) en términos de la **capacidad máxima fijada** a la empresa (≤ mínima + 20 %), y presentar el
   convenio como figura estable de ruta completa (≤ 2 años), no como refuerzo de pico.
4. Mapeo sugerido de las tres opciones del enunciado (a decisión de Camila): **propia/vinculada** = dentro de la capacidad máxima
   fijada; **arrendada** = contrato con empresa de servicio especial en periodos de alta demanda (art. 2.2.1.6.3.5 + Res. 264/2020),
   no arriendo simple; **convenio** = art. 2.2.1.4.6.8 + Res. 264/2020 arts. 3–5.
5. Imprecisiones menores: «capacidad transportadora **mínima**» (V-1), «base IV trim. 2015» (V-13b), «III trim. 2026 vs. IV trim.
   2025» (V-14b), contexto 2015 y «sin conductor» de la frase del DANE (V-15), cita actualizada del art. 2.2.1.6.8.1 (V-10).
6. Si se usan las fechas de alta demanda de la Res. 264/2020 en M1, son reglas publicadas en 2020, conocibles con más de 30 días
   de antelación (no hay fuga), pero falta confirmar su vigencia en un normograma oficial de MinTransporte.

## Candidatos a hallazgo (plantilla de `alucinaciones/registro.md`; no se editó el registro)

### CA6-1 — «Arrendar en vez de comprar mueve ~un tercio de la estructura de costos»
- **Módulo / categoría / quién lo encontró:** M1 / **Conceptos** (interpretación de un índice de costos) / cazador-alucinaciones
  (Opus) en la verificación CA-6, 27-nov-2026. Dirige: Camila.
- **1. Prompt literal:** `alucinaciones/prompts/CA-6a.md` (investigador-fuentes, Sonnet, 27-nov-2026), sección «Entrega»: «una
  sección "Qué se puede concluir con esto" que diga qué comparación de costos es defendible y cuál no».
- **2. Respuesta relevante de la IA:** `docs/investigacion/CA-6_costos_flota.md` §8, «Defendible (con cita)», punto 3:
  «Estructura relativa de costos: combustible ~31 %, costos fijos ~33 % (incluye conductores), peajes y terminales ~20 %. Permite
  argumentar, por ejemplo, que una opción que reduzca costos fijos (arrendar, no comprar) mueve ~un tercio de la estructura».
- **3. Cómo se sospechó:** la misma frase reconoce que los costos fijos «incluye[n] conductores»; arrendar un vehículo no elimina
  el salario del conductor, así que el «tercio» no puede atribuirse a la decisión comprar/arrendar.
- **4. Evidencia:** DANE, metodología DSO-ICTIP-MET-001 v2 (2018): «costos fijos (parqueaderos, seguros, costo del vehículo,
  impuestos y mano de obra)» (`alucinaciones/evidencias/CA-6/ictip_met_v2.txt`). DANE, boletín ICTIP III-2026 (22-oct-2026),
  Tabla 3: «Costos fijos 32,99 14,07 4,83» y Tabla 4: «Mano de obra conductor(es) y ayudante(s) 22,11 4,72»
  (`ictip_bol_IIItrim2026.txt`): de los 4,83 p.p. que aportó el grupo en el año corrido, 4,72 vienen de la mano de obra.
  `verificar.py` → `salida.txt` (fragmentos CF, C-2c, C-2cf).
- **5. Corrección:** «Arrendar en vez de comprar sustituye solo el componente de capital ("Costo del vehículo y su
  apalancamiento"), cuyo peso no está en el boletín (T-9); conductores, combustible, peajes y seguros se mantienen. No se puede
  cuantificar el ahorro con el 32,99 %».
- **6. Lección aprendida:** un grupo de un índice de precios no es una palanca de decisión: antes de decir qué «mueve» una
  opción, bajar al nivel de clase de costo y comprobar qué componentes cambia realmente.
- **Estado:** candidato (no editado en el informe ni en el registro). Es un error de razonamiento, no un dato inventado:
  Andrés decide si cuenta en la categoría Conceptos.

**No propuestos como hallazgo** (no son afirmaciones falsas, o son de bajo peso): la omisión del art. 2.2.1.6.3.5 y de la
Res. 264/2020 (V-6/V-7: el informe dejó el `TODO` abierto honestamente); las paráfrasis de periodo y base del ICTIP (V-13b, V-14b);
la lectura del tope del 20 % (V-3b). Si el equipo quiere contar V-14b («sep-2026 vs. dic-2025» frente a «III trim. vs. IV trim.»),
la evidencia está en `ictip_bol_IIItrim2026.txt` pág. 5 (fragmento C-2per), pero su peso es menor.

## Verificaciones correctas (también para el registro)
Datos del mundo real (normas): V-1 a V-5, V-8, V-9, V-11, V-12, V-24. Datos del mundo real (DANE): V-13, V-14, V-15, V-16,
V-17, V-18, V-19, V-21, V-22.
