# CA-2 (verificación) — Normativa y parámetros operativos de M1

Verificador: cazador-alucinaciones (Opus). Prompt: `alucinaciones/prompts/CA-2-verificacion.md`. Fecha de consulta de **todas**
las fuentes: **2026-11-26**. Objeto: el informe generado por IA `docs/investigacion/CA-2_normativa_operacion.md` (prompt
`alucinaciones/prompts/CA-2a.md`, investigador-fuentes, Sonnet) y su uso en `configs/m1/operacion.yaml` (prompt `CA-3a.md`).
Evidencias (copias y extractos de lo abierto): `alucinaciones/evidencias/CA-2/`. No se tocó código, configs ni `registro.md`.

Cómo se abrió cada fuente: descarga directa con `curl` y lectura del texto completo (HTML convertido a texto; PDF extraído con
PDFKit). Ninguna afirmación de esta nota sale de un resumen de buscador: los buscadores solo se usaron para localizar URLs.
A diferencia del informe original, **Senado y Función Pública sí abrieron** desde aquí.

Clasificación: CONFIRMADA / REFUTADA / NO VERIFICABLE (y, para el informe, correcta / imprecisa / incorrecta / desactualizada).

---

## 1. Ley 2101 de 2021, arts. 2–3 y cronograma derivado — CONFIRMADA

Fuentes primarias abiertas:
- Secretaría del Senado: http://www.secretariasenado.gov.co/senado/basedoc/ley_2101_2021.html (actualización del sitio:
  15-nov-2026). Evidencia: `ley_2101_2021_senado.txt`.
- Función Pública, Gestor Normativo: https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=166506 («Fecha de
  Expedición: 15 de julio de 2021»; «Vigencias(0)»). Evidencia: `funcionpublica_ley_2101_2021.html`.

Fragmentos literales (Senado):
- Encabezado: «LEY 2101 DE 2021 (julio 15) Diario Oficial No. 51.736 de 15 de julio de 2021».
- Art. 2: «Artículo 161. Duración. <Artículo CONDICIONALMENTE exequible> La duración máxima de la jornada ordinaria de
  trabajo es de cuarenta y dos (42) horas a la semana, que podrán ser distribuidas, de común acuerdo, entre empleador y
  trabajador, en 5 o 6 días a la semana, garantizando siempre el día de descanso, salvo las siguientes excepciones: …»
- Art. 3: «Transcurridos dos (2) años a partir de la entrada en vigencia de la ley, se reducirá una (1) hora de la jornada
  laboral semanal, quedando en 47 horas semanales. Pasados tres (3) años de la entrada en vigencia de la ley, se reducirá otra
  hora de la jornada laboral semanal, quedando en 46 horas semanales. A partir del cuarto año de la entrada en vigencia de la
  ley, se reducirán dos (2) horas cada año hasta llegar a las cuarenta y dos (42) horas semanales…»
- Art. 8: «La presente ley empezará a regir a partir de la fecha de su publicación…»

Fechas calendario (el informe las **derivó**; aquí se confirman con la autoridad laboral):
- Ministerio del Trabajo, Oficina Asesora Jurídica, concepto 08SE20231203000000048585 (2023; respuesta al radicado
  05EE2023120300000060943), PDF oficial en mintrabajo.gov.co
  (https://www.mintrabajo.gov.co/documents/20147/74864900/05EE2023120300000060943+++REDUCCI%C3%93N+JORNADA++-TURNOS+DE+TRABAJO.pdf/0be54879-6e2f-a25f-a0cb-29b5c0668437),
  tabla literal: «A partir del 15 de julio de 2023 … Sería de 47 horas semanales / A partir del 15 de julio de 2024 … 46 horas
  / A partir del 15 de julio de 2025 … 44 horas / A partir del 15 de julio de 2026 … 42 horas». También: «máxima legal desde el
  15 de julio del 2023 y el 14 de julio del 2024» (47 h). Evidencia: `mintrabajo_concepto_08SE20231203000000048585.{pdf,txt}`.
- Comunicado MinTrabajo del 15-jul-2026 (https://www.mintrabajo.gov.co/web/guest/a-partir-de-hoy-la-jornada-laboral-m%C3%A1xima-en-colombia-queda-en-42-horas-semanales):
  «Bogotá, 15 de julio de 2026. Desde hoy entra en vigor la última etapa de la Ley 2101 de 2021, con la cual la jornada laboral
  máxima semanal en Colombia se reduce de 44 a 42 horas.» Evidencia: `mintrabajo_comunicado_2026-07-15.txt`.
- Matiz: el comunicado MinTrabajo del 10-jul-2023 dice «desde el próximo 16 de julio de 2023 … 16 de julio del año 2024 … 16
  de julio del año 2025 … 16 de julio de 2026» (`mintrabajo_comunicado_2023-07-10.txt`). El propio ministerio usó 15 y 16; el
  concepto jurídico y el comunicado de 2026 usan el **15**. El informe atribuyó el «16» solo a «un diario»: incompleto, no
  erróneo.

Vigencia: la condicionalidad del art. 2 viene de la **Sentencia C-507 de 2023** (Corte Constitucional, «Bogotá, D.C.,
veintidós (22) de noviembre», https://www.corteconstitucional.gov.co/relatoria/2023/C-507-23.htm), resuelve: «DECLARAR la
EXEQUIBILIDAD condicionada del artículo 2 de la Ley 2101 de 2021 … en el entendido que la jornada máxima laboral del servicio
doméstico interno se reducirá de 60 a 52,5 horas semanales». No afecta a conductores. Evidencia: `C-507-23_resuelve.txt`.
El art. 161 fue sustituido otra vez por la Ley 2466 de 2025, art. 11 (§2).

Veredicto sobre el informe: cronograma 48→47→46→44→42 con cortes el 15-jul de 2023–2026 **correcto**; C-507/2023 **correcto**.
Dos imprecisiones en la **base legal** citada (ver §8, candidato H-b): el informe dice que de 2021 a 2023 rige el «art. 161 CST
según Ley 50/1990, art. 20» y que antes de 2025 el tope diario de 8 h viene de la Ley 50/1990; ese texto fue **sustituido** el
15-jul-2021 por el art. 2 de la Ley 2101, que no trae tope diario (solo la jornada flexible de la lit. d: «mínimo cuatro (4)
horas continuas y máximo hasta nueve (9) horas diarias»). El valor de 48 h para 2021–2023 sí es correcto, pero por la
gradualidad del art. 3 (que el MinTrabajo confirma), no por la Ley 50.

## 2. Ley 2466 de 2025, arts. 11, 13 y 14 — CONFIRMADA (texto completo leído)

Fuentes: Senado http://www.secretariasenado.gov.co/senado/basedoc/ley_2466_2025.html («LEY 2466 DE 2025 (junio 25) Diario
Oficial No. 53.160 de 25 de junio de 2025») y Función Pública
https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=260676 («Fecha de Expedición: 25 de junio de 2025 / Fecha de
Entrada en Vigencia: 25 de junio de 2025»). Ambos textos completos, **incluido el último 20 %** que el informe no leyó.
Evidencias: `ley_2466_2025_senado.txt`, `ley_2466_2025_funcionpublica_arts10-14.txt`, `funcionpublica_ley_2466_2025.html`.

- Título literal: «por medio de la cual se modifica parcialmente normas laborales y se adopta una Reforma Laboral para el
  trabajo decente y digno en Colombia». El informe lo dejó «[título a cotejar]» con otra redacción → corregir la cita APA.
- Art. 11: «Modifíquese el artículo 161 del Código Sustantivo del Trabajo, modificado por la Ley 2101 de 2021, el cual quedará
  así: "Artículo 161. Duración. La duración máxima de la jornada ordinaria de trabajo es de ocho (8) horas al día, sin perjuicio
  de lo establecido en el artículo 3o de la Ley 2101 de 2021 sobre la aplicación gradual, y una jornada máxima de cuarenta y dos
  (42) horas a la semana. La jornada máxima semanal podrá ser distribuida … de cinco (5) a seis (6) días a la semana,
  garantizando siempre el día de descanso y sin afectar el salario."» Lit. a): flexible «mínimo cuatro (4) horas continuas y
  máximo hasta nueve (9) horas diarias»; lit. d): turnos sucesivos «no exceda de seis (6) horas al día y treinta y seis (36) a
  la semana». Coincide con el informe.
- Art. 13 (art. 22 Ley 50/1990): «En ningún caso las horas extras de trabajo, diurnas o nocturnas, podrán exceder de dos (2)
  horas diarias y doce (12) semanales.» Parágrafo: exceptúa sectores de seguridad y salud (no transporte). Coincide.
- Art. 14 (art. 179 CST): recargo del 100 %; parágrafo transitorio 80 % desde 1-jul-2025, 90 % desde 1-jul-2026, 100 % desde
  1-jul-2027. Coincide. Parágrafo 3: si no se pacta otro, «se presumirá como día de descanso obligatorio el domingo».
- Art. 10, parágrafo 2 (nocturno 19:00–06:00): «entrará en vigencia seis (6) meses después de la sanción». Coincide.
- Art. 70: «La presente ley rige a partir de su promulgación…». Sin notas de inexequibilidad sobre los arts. 11, 13 o 14 en
  el Senado (actualizado al 15-nov-2026); hay apartes inexequibles en otros artículos (p. ej. art. 15, num. 10).
- Lo no leído por el informe (≈ 24 000 caracteres finales): revisado; **no hay ninguna disposición sobre conductores ni sobre
  jornada de transporte** (búsqueda de «conductor» en el texto completo: 0 coincidencias).

## 3. Resolución 315 de 2013 (MinTransporte), art. 6 — CONFIRMADA (texto y vigencia)

Texto literal (normograma Colpensiones, compilación Avance Jurídico,
https://normativa.colpensiones.gov.co/compilacion/docs/resolucion_mintransporte_0315_2013.htm; idéntico en los dos conceptos
oficiales del MinTransporte en PDF y en SISJUR, https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=51704):
«RESOLUCIÓN 315 DE 2013 (febrero 6) Diario Oficial No. 48.697 de 7 de febrero de 2013 … ARTÍCULO 6o. SEGUNDO CONDUCTOR.
Todos los vehículos de servicio público de transporte terrestre de pasajeros y mixto, para la realización de operaciones de
transporte con una duración superior a ocho (8) horas de recorrido entre el lugar de origen y el lugar de destino, deberán
contar con un segundo conductor. Las empresas de transporte deberán adoptar las medidas conducentes para garantizar los
descansos necesarios de los conductores. PARÁGRAFO 1o. Contar con dos conductores … se entiende como una condición necesaria
para prestación del servicio. La inobservancia de esta medida dará lugar a la inmovilización del vehículo…»
Evidencias: `res_315_2013_colpensiones.txt`, `mintransporte_concepto_20241340513041.pdf` (p. 2),
`mintransporte_concepto_20251340607391.pdf` (p. 4).

Vigencia (lo que el informe dejó en `TODO(cita)`):
- El normograma solo anota una modificación: «ARTÍCULO 3o. … <Artículo modificado por el artículo 1 de la Resolución 378 de
  2013>». El art. 6 no tiene nota.
- **Resolución Única Compilatoria de Tránsito 20223040045295 de 2022**, art. 9.2.1 (derogatoria) leída completa
  (https://cancilleria.gov.co/sites/default/files/Normograma/docs/resolucion_mintransporte_45295_2022.htm): lista
  taxativa de resoluciones derogadas; **la 315 de 2013 no figura** y el texto compilado no contiene «segundo conductor» ni
  «315 de 2013». Cierra: «Las demás resoluciones que no hayan sido objeto de la derogatoria establecida en el presente artículo
  mantendrán su vigencia». Evidencia: `res_20223040045295_art_9.2.1_derogatoria.txt`.
- **Decreto 1079 de 2015**, art. 3.1.1 (Función Pública, https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=77889):
  deroga las disposiciones **reglamentarias** que versan sobre las mismas materias, pero «Los actos administrativos expedidos
  con fundamento en las disposiciones compiladas en el presente Decreto mantendrán su vigencia y ejecutoriedad». El Decreto
  1079 no regula el segundo conductor (0 coincidencias). La Res. 315 se expidió con base en el Decreto 087 de 2011 y las Leyes
  105/1993 y 336/1996. Evidencia: `decreto_1079_2015_funcionpublica_extractos.txt`.
- El MinTransporte la aplica como vigente en sus conceptos de 7-may-2024 y 16-may-2025 (leídos completos).
- Conclusión: vigente a la fecha de consulta; no hallé derogatoria ni compilación. (Límite: no existe un compilado oficial de
  resoluciones del MinTransporte en el Senado o Función Pública; la verificación es por ausencia en las dos normas
  compiladoras y por aplicación reciente del propio ministerio.)

## 4. Decreto 1393 de 1970, art. 56 (tope de 10 h) — EXISTENCIA Y TEXTO: CONFIRMADOS vía Corte Suprema; VIGENCIA: NO VERIFICABLE

- Texto, tal como lo transcribe la Corte Suprema de Justicia, Sala de Casación Laboral, rad. 22189, 4-ago-2004, M.P. Camilo
  Tarquino Gallego (copia en el normograma de Colpensiones,
  https://normativa.colpensiones.gov.co/colpensiones/docs/csj_scl_22189_2004.htm): «ART. 56.- Las empresas de transporte y por
  razones de seguridad pública, no podrán fijar a los conductores jornadas de trabajo diario superior a 10 horas». La Corte
  recoge su jurisprudencia de 1991: «las diez horas que fija son el número máximo de las que pueden trabajar, sin que sea dado
  distinguir entre jornada ordinaria y extraordinaria», y la aplicó en 2004 a un conductor de servicio público. La lectura del
  informe («tope, no jornada obligatoria») es **correcta**. Evidencia: `csj_scl_22189_2004.txt`.
- No pude abrir el **texto oficial** del decreto: Senado y Colpensiones devuelven 404, Cancillería 403; SUIN-Juriscol
  (https://www.suin-juriscol.gov.co/viewDocument.asp?id=1740361) ahora es una aplicación que no entrega el texto sin
  navegador, y WebFetch falla por certificado. Un resumen de buscador mencionó que SUIN lo marcaría «no vigente desde
  01/06/1988»: **no lo abrí y no lo uso**; queda como indicio contradictorio con la aplicación que hizo la Corte en 2004.
- La SL8675-2017 (rad. 47138, 8-mar-2017, M.P. Fernando Castillo Cadena; datos confirmados en la nota 1 del concepto
  MinTransporte de 2025) **no la encontré** en la relatoría de la Corte. El MinTransporte (2024 y 2025) no aplica el art. 56:
  remite al art. 161 CST y al art. 36 de la Ley 336 de 1996.
- Recomendación: **no usar** el tope de 10 h como `fuente`. Puede mencionarse en el blog como norma de vigencia discutida, con
  la cita de la CSJ 2004 y la aclaración de que no se verificó su vigencia actual.

## 5. Inexistencia de una norma vigente de tiempos máximos de conducción continua o diaria (pasajeros por carretera) — CONFIRMADA dentro de lo buscado (no se puede probar una ausencia de forma exhaustiva)

Revisado con texto completo:
- Res. 315/2013 (13 artículos): solo segundo conductor > 8 h de recorrido y «descansos necesarios», sin cifras.
- Res. 20223040045295/2022 (Resolución Única de Tránsito, ~6 800 líneas): sin horas de conducción ni pausas; solo aparece
  «Evidencia de fatiga» en un listado.
- Decreto 1079/2015 (compilado completo, Función Pública): sin «horas de conducción», «tiempo de conducción», «conducción
  continua» ni «horas continuas».
- Ley 769/2002, Código Nacional de Tránsito (Función Pública, i=5557): sin esas expresiones.
- Res. 40595/2022 (metodología PESV, https://cancilleria.gov.co/normograma/compilacion/docs/resolucion_mintransporte_40595_2022.htm):
  exige un «Programa de Prevención de la Fatiga: Procedimiento para controlar la jornada de trabajo, horas de conducción y
  descanso de los conductores» y un indicador de «excesos en la jornada diaria de trabajo de los conductores (eventos en los
  que los conductores han superado el tiempo máximo permitido en la legislación)». **Remite** a la legislación; no fija cifras.
  Evidencia: `res_40595_2022_pesv_fatiga.txt`.
- Circular conjunta MinTransporte–MinTrabajo 20261300000087 (marzo de 2026): el PDF oficial está tras un visor que no pude
  descargar. El comunicado oficial del MinTransporte (9-mar-2026,
  https://mintransporte.gov.co/publicaciones/12300/…) la dirige al **transporte de carga** y dice: «Esta circular no crea
  nuevas obligaciones…» y que «las empresas deben organizar la operación respetando los límites de la jornada laboral, los
  tiempos de descanso y las pausas necesarias». Sin cifras. Evidencia: `mintransporte_comunicado_circular_20261300000087.txt`.
  `TODO(cita)` si se quiere citar la circular misma.
- Conceptos MinTransporte 2024 y 2025: «las disposiciones que atañen la operación de vehículos de transporte publico
  terrestre, no contempla excepciones ni salvedades respecto de la jornada legal laboral de los conductores».
- No revisado: el Decreto 1048 de 2026 (según prensa, transporte **especial** y gestión de fatiga, con reglamentación
  pendiente); no es la modalidad de M1. `TODO(cita)` si se menciona.

Veredicto: el informe tiene razón; la conclusión de M1 debe decir «no hallamos norma que fije horas de conducción; rige la
jornada laboral general (art. 161 CST) más el segundo conductor de la Res. 315/2013».

## 6. Decreto 171 de 2001, arts. 50–51 y Decreto 1079 de 2015 — CONFIRMADA; la cita vigente es el Decreto 1079

- Decreto 171/2001 (SISJUR, https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=4306; «Diario Oficial 44318 de
  febrero 5 de 2001»; «por el cual se reglamenta el Servicio Público de Transporte Terrestre Automotor de Pasajeros por
  Carretera»): art. 50 «GRUPO A: 4 a 9 pasajeros / GRUPO B: 10 a 19 pasajeros / GRUPO C: más de 19 pasajeros»; art. 51
  «Automóvil - Campero - Camioneta Grupo A / Microbús - Vans Grupo B / Buseta - Bus Grupo C». Coincide con el informe.
- **Compilado** en el Decreto 1079 de 2015 (Función Pública, i=77889; Cancillería con notas al 30-sep-2024), Libro 2, Parte 2,
  Título 1, Capítulo 4 (pasajeros por carretera), Sección 7:
  - «ARTÍCULO 2.2.1.4.7.3. Racionalización. … se agrupará según su capacidad así: - GRUPO A: 4 a 9 pasajeros - GRUPO B: 10 a 19
    pasajeros - GRUPO C: más de 19 pasajeros … (Decreto 171 de 2001, artículo 50).»
  - «ARTÍCULO 2.2.1.4.7.4. Unificación automática. … Automóvil-Campero-Camioneta Grupo A / Microbús-Vans Grupo B /
    Buseta-Bus Grupo C … (Decreto 171 de 2001, artículo 51).»
  - Sin notas de modificación o derogatoria en la versión con notas de vigencia de Cancillería.
  - Por el art. 3.1.1 del Decreto 1079 («Derogatoria Integral»), el Decreto 171/2001 quedó derogado en lo compilado: **la cita
    correcta hoy es Decreto 1079 de 2015, arts. 2.2.1.4.7.3 y 2.2.1.4.7.4** (con la procedencia «Decreto 171 de 2001, arts.
    50–51»).
  - Ojo: el colectivo urbano (art. 2.2.1.1.9.3, del Decreto 170/2001) tiene **otros** grupos (C: 20 a 39, D: más de 40). No
    mezclar.
- ¿El rango incluye al conductor? **NO VERIFICABLE con el texto**: ni el art. 50 del Decreto 171 ni el 2.2.1.4.7.3 lo dicen.
  Otras normas del mismo sector sí lo explicitan cuando quieren (Decreto 1079, art. 2.2.1.6.15.4: «clase automóvil, campero o
  camioneta de no más de nueve (9) pasajeros, incluido el conductor»; Res. 20223040045295, art. 5.3.8.1 «(incluido el
  conductor)»). Eso sugiere que el límite de 9 del Grupo A podría leerse con el conductor incluido (8 pasajeros), pero es
  inferencia, no texto. Consecuencia práctica: CAMIONETA y CAMPERO con capacidad 9 en el YAML pueden quedar 1 por encima si la
  lectura es «incluido el conductor»; el p99 observado (8,27 y 8,12) es compatible con 8 o 9. Dejarlo como supuesto con esa
  nota.
- Evidencias: `decreto_171_2001_alcaldia_extractos.txt`, `decreto_1079_2015_funcionpublica_extractos.txt`.

## 7. Qué valores de `configs/m1/operacion.yaml` pueden pasar de `supuesto: true` a `fuente:`

| Clave | Valor actual | ¿Pasa a `fuente`? | Cita exacta propuesta |
|---|---|---|---|
| `jornada_max_diaria_h` | 8 | **Sí, con fecha** | Congreso de la República de Colombia (2025). Ley 2466 de 2025, art. 11 (art. 161 CST): «La duración máxima de la jornada ordinaria de trabajo es de ocho (8) horas al día…». Diario Oficial No. 53.160, 25-jun-2025. http://www.secretariasenado.gov.co/senado/basedoc/ley_2466_2025.html. **Nota obligatoria:** rige desde el 25-jun-2025; para fechas 15-jul-2021–24-jun-2025 el art. 161 vigente (Ley 2101, art. 2) no fija tope diario; no citar la Ley 50/1990. |
| `umbral_segundo_conductor_h` | 8 | **Sí** | Ministerio de Transporte (2013). Resolución 315 de 2013, art. 6: «…con una duración superior a ocho (8) horas de recorrido entre el lugar de origen y el lugar de destino, deberán contar con un segundo conductor». Diario Oficial No. 48.697, 7-feb-2013. Vigencia: no derogada por la Res. 20223040045295/2022 (art. 9.2.1) ni afectada por el Decreto 1079/2015 (art. 3.1.1). |
| `segundo_conductor_activo` | 0 | No (es interruptor de modelado) | Pero ver corrección C-3: con `tiempo_recorrido_h = 10` en Bogotá–Cali, la norma citada **obliga**; dejarlo en 0 contradice la `fuente` del umbral. |
| `dias_descanso_semana` | 0 | El valor **1** sí tendría `fuente`; el 0 es decisión de modelado | Ley 2466 de 2025, art. 11 (art. 161 CST): «…de cinco (5) a seis (6) días a la semana, garantizando siempre el día de descanso…» (igual en Ley 2101, art. 2). |
| Jornada semanal (no existe la clave) | — | **Agregar** `jornada_max_semanal_h` con `fuente` | Ley 2101 de 2021, art. 3 + Ley 2466 de 2025, art. 11. Valor según la fecha de operación: 48 h (hasta 14-jul-2023), 47, 46, 44 y 42 h desde el 15-jul-2026 (MinTrabajo, concepto 08SE20231203000000048585 y comunicado del 15-jul-2026). |
| `por_clase.*.capacidad_pasajeros` | 5, 31, 22, 9, 9, 19 | **No** (el valor es supuesto) | Sí cambia la nota: el **rango** se cita como Decreto 1079 de 2015, arts. 2.2.1.4.7.3–2.2.1.4.7.4 (compila Decreto 171/2001, arts. 50–51), en vez de «Decreto 171/2001». Quitar el `TODO(cita) vigencia en el Decreto 1079/2015`: queda cerrado. Agregar «la norma no dice si el rango incluye al conductor». |
| `jornada_efectiva_h` | 7 | No | Sin norma (§5). La nota actual es correcta. |
| `ausentismo`, `horas_operacion_h`, `tiempo_ciclo_h`, `tiempo_recorrido_h`, costos, `cuantil`, `ocupacion_objetivo`, `fraccion_demanda_en_origen` | — | No | No vienen de norma (el informe y la nota del YAML están bien). |

## 8. Candidatos a hallazgo (solo errores de una IA con prompt literal guardado)

Cobertura de la verificación: categoría **Datos del mundo real** (normativa de transporte), módulo **M1**. No propongo ningún
candidato por los puntos del informe que salieron correctos (la mayoría). No registré nada en `registro.md` (prohibido en esta
tarea).

### H-a (fuerte) — El informe CA-2 asigna 46 h a una fecha en la que regían 47 h
1. **Prompt literal:** `alucinaciones/prompts/CA-2a.md` (investigador-fuentes, Sonnet, 2026-11-26), en particular: «indica el
   cronograma de reducción si existe y qué valor rige en cada año 2021–2026» y «Si dos normas parecen contradecirse, cita ambas
   y explica cuál rige».
2. **Respuesta relevante** (`docs/investigacion/CA-2_normativa_operacion.md`, §6, punto 1): «concepto MinTransporte
   20241340513041 (7-may-2024) aplica art. 161 CST "Modificado por la Ley 50 de 1990… ocho (8) horas al día y cuarenta y ocho
   (48) a la semana" como vigente, cuando la Ley 2101 de 2021 (art. 2) ya había modificado ese artículo en 2021 y **en esa fecha
   regían 46 h (art. 3)**.»
3. **Cómo se sospechó:** la tabla del propio informe (§1.1) dice «15-jul-2023 a 14-jul-2024 | 47 h»; el 7-may-2024 cae en ese
   tramo. Contradicción interna.
4. **Evidencia:** Ley 2101, art. 3 («Transcurridos dos (2) años … quedando en 47 horas semanales. Pasados tres (3) años …
   46») con vigencia desde el 15-jul-2021 (art. 8; Diario Oficial 51.736); MinTrabajo, concepto 08SE20231203000000048585:
   «máxima legal desde el 15 de julio del 2023 y el 14 de julio del 2024» = 47 h; «A partir del 15 de julio de 2024 … 46
   horas». Archivos: `ley_2101_2021_senado.txt`, `mintrabajo_concepto_08SE20231203000000048585.{pdf,txt}`,
   `mintransporte_concepto_20241340513041.pdf`.
5. **Corrección:** «…en esa fecha (7-may-2024) regían 47 h (art. 3; 46 h solo desde el 15-jul-2024)». La crítica de fondo al
   concepto de 2024 (cita un art. 161 ya sustituido) sigue siendo válida.
6. **Lección:** toda fecha concreta que se ubique en un cronograma escalonado se cruza contra la tabla de cortes (fecha ≥
   corte) antes de escribirla; un test trivial `jornada_semanal(fecha)` con los cortes del MinTrabajo lo habría atrapado.
   Severidad: baja (no llegó al YAML), pero es un error factual genuino y verificable.

### H-b (media; Camila decide si cuenta) — Base legal desactualizada para 2021–2025: «art. 161 CST según Ley 50/1990»
1. **Prompt literal:** `alucinaciones/prompts/CA-2a.md`: «Busca la normativa colombiana **vigente** … Para cada norma: …
   **estado de vigencia** comprobado (busca derogatorias o modificaciones)».
2. **Respuesta relevante:** §1.1, tabla: «15-jul-2021 a 14-jul-2023 | 48 h (art. 161 CST según Ley 50/1990, art. 20 …)»;
   §1.2, Nota: «el valor diario de 8 h viene de aquí (rige desde 25-jun-2025) y de la Ley 50/1990 art. 20 antes (según el
   concepto MinTransporte 2024…)»; §7, fila «Jornada ordinaria máxima diaria»: «antes Ley 50/1990 art. 20 (según concepto
   MinTransporte 2024)».
3. **Cómo se sospechó:** el mismo informe (§6.1) señala que ese concepto de 2024 cita un texto ya sustituido, y aun así lo usa
   como base del tope diario anterior a 2025.
4. **Evidencia:** Ley 2101, art. 2: «Modifíquese el artículo 161 del Código Sustantivo del Trabajo, el cual quedará así:
   Artículo 161. Duración. … cuarenta y dos (42) horas a la semana …» (sin tope diario; la lit. d habla de «máximo hasta nueve
   (9) horas diarias» en jornada flexible), vigente desde el 15-jul-2021; Ley 2466, art. 11 modifica el art. 161
   «modificado por la Ley 2101 de 2021» (no por la Ley 50) y reintroduce «ocho (8) horas al día». Archivos:
   `ley_2101_2021_senado.txt`, `ley_2466_2025_senado.txt`.
5. **Corrección:** 48 h en 2021–2023 por la gradualidad del art. 3 de la Ley 2101 (no por la Ley 50); tope diario de 8 h en
   el art. 161 solo desde el 25-jun-2025 (Ley 2466, art. 11); entre el 15-jul-2021 y el 24-jun-2025 el art. 161 no traía tope
   diario. No afirmo que no hubiera ningún límite diario en todo el ordenamiento en ese periodo: solo que la cita del informe
   remite a un texto que ya no regía.
6. **Lección:** verificar la vigencia del **texto** que se cita, no solo del número de artículo: un artículo modificado dos
   veces (Ley 50 → Ley 2101 → Ley 2466) tiene tres textos distintos. Severidad: media; el YAML aún no usa el tope para fechas
   anteriores a 2025.

### H-c (débil; probablemente no conviene contarlo) — Resumen del buscador del propio cazador
- Prompt literal (consulta a WebSearch en esta verificación): «Colombia norma tiempos de conducción continua conductores
  transporte de pasajeros resolución Ministerio de Transporte 2025 2026 pausas activas fatiga». Respuesta: «una guía señala
  conducción continua máxima de 5 horas según la Resolución 315 de 2013, que es la norma de carga». La Res. 315 regula la
  seguridad del transporte público terrestre automotor (su art. 6, el único sobre conductores, es de pasajeros y mixto; el
  art. 4 sí menciona carga), y no contiene «5 horas». El error de fondo (5 h) es de la guía secundaria, no del resumidor; lo del
  resumidor es solo una imprecisión. Evidencia: `websearch_resumidor_res315_2026-11-26.txt`. El prompt no está en
  `alucinaciones/prompts/`: si se quiere registrar, hay que guardarlo allí; por su bajo peso recomiendo no contarlo.

No es hallazgo de IA: los conceptos del MinTransporte (cita desactualizada del art. 161 en 2024; «ocho (8) horas diarias» por
«ocho horas de recorrido» en 2025, p. 6) son errores de una **fuente oficial**, ya señalados por el informe. El «16 de julio»
del comunicado MinTrabajo de 2023 tampoco es de una IA.

## 9. Correcciones necesarias (no aplicadas)

En `docs/investigacion/CA-2_normativa_operacion.md`:
- C-1 (§6.1): «en esa fecha regían 46 h» → «47 h» (H-a).
- C-2 (§1.1 tabla, §1.2 Nota, §7 fila diaria): base legal de 2021–2025 según §8 H-b; el 8 h/día solo desde el 25-jun-2025.
- C-3 (§1.2): título literal de la Ley 2466 (§2) y Diario Oficial 53.160 confirmado; quitar «[título a cotejar]»; cambiar las
  URL de normogramas por Senado/Función Pública.
- C-4 (§1.1, §1.3, §1.5, §2): cerrar los `TODO(cita)` 1, 2, 3, 5 y 6 de su §8 con las fuentes de esta nota; el 4 (Decreto
  1393/1970) queda abierto: vigencia NO VERIFICABLE; el 7 queda parcialmente cerrado (PESV sin cifras; circular 2026 solo vía
  comunicado oficial).
- C-5 (§2): la cita del rango de capacidad es Decreto 1079/2015, arts. 2.2.1.4.7.3–2.2.1.4.7.4; añadir que la norma no dice
  si incluye al conductor.
- C-6 (§6.4): el «16 de julio» lo usó también el MinTrabajo en su comunicado de 2023; el concepto jurídico del MinTrabajo y
  su comunicado de 2026 usan el 15.

En `configs/m1/operacion.yaml` (decisiones de Camila):
- C-7: pasar a `fuente` `jornada_max_diaria_h` y `umbral_segundo_conductor_h` con las citas del §7; actualizar las notas de
  `por_clase` (Decreto 1079) y la de `dias_descanso_semana` («sin verificar» → verificado).
- C-8 (coherencia, no es alucinación): con `tiempo_recorrido_h = 10` en Bogotá–Cali y umbral 8 h, la Res. 315/2013 art. 6
  **obliga** a dos conductores; `segundo_conductor_activo = 0` por defecto deja la plantilla de esa ruta por debajo de lo legal.
  Si se mantiene en 0 para reproducir la fórmula del Spec, el blog debe decir que es una cota baja que incumple la norma.
- C-9 (coherencia, no es alucinación): `conductores_dia` (src/m1_demanda/operacion.py, l. 92) con los valores por defecto
  (`jornada_efectiva_h = 7`, `dias_descanso_semana = 0`) supone que cada conductor cubre 7 h los 7 días = **49 h/semana**,
  por encima de cualquier máximo semanal vigente entre 2021 y 2026 (48 → 42 h) y sin el día de descanso que exige el art. 161
  CST. Con `s = 1` y 7 h efectivas la carga es 42 h (dentro de las 8 h diarias y de las 42 h desde el 15-jul-2026; las horas
  de pausa dentro de la jornada también cuentan como jornada si son tiempo a disposición del empleador, lo que Camila debe
  decidir). Propuesta: agregar `jornada_max_semanal_h` con `fuente` y validar `(7 − s) · jornada_pagada ≤ jornada_max_semanal_h`.

## 10. Resumen por afirmación

| # | Afirmación | Veredicto | Fuente primaria abierta |
|---|---|---|---|
| 1 | Ley 2101, arts. 2–3; cronograma 15-jul 2023/24/25/26 = 47/46/44/42 h; vigente desde 15-jul-2021 | **CONFIRMADA** (base legal 2021–2025 del informe: imprecisa, H-b) | Senado; Función Pública; MinTrabajo (concepto 2023 y comunicado 15-jul-2026); C-507/2023 |
| 1b | «el 7-may-2024 regían 46 h» (informe §6.1) | **REFUTADA** (47 h) | Ídem |
| 2 | Ley 2466, art. 11 (8 h/día, 42 h/semana), art. 13 (2 h/día, 12 h/semana), art. 14 (recargo y gradualidad) | **CONFIRMADA**; sin nada sobre conductores en el 100 % del texto | Senado; Función Pública |
| 3 | Res. 315/2013, art. 6: texto literal y vigencia | **CONFIRMADA** | Normograma Colpensiones; SISJUR; conceptos MinTransporte 2024–2025; Res. 20223040045295/2022 art. 9.2.1; Decreto 1079/2015 art. 3.1.1 |
| 4 | Decreto 1393/1970, art. 56 (10 h) | Existencia y texto **CONFIRMADOS** (vía CSJ 2004); vigencia **NO VERIFICABLE** | CSJ SCL rad. 22189/2004 |
| 5 | No existe norma vigente de horas máximas de conducción continua/diaria para pasajeros por carretera | **CONFIRMADA** en el alcance revisado | Res. 315/2013; Res. 20223040045295/2022; Decreto 1079/2015; Ley 769/2002; Res. 40595/2022; comunicado oficial de la circular 20261300000087 |
| 6 | Decreto 171/2001, arts. 50–51: rangos por grupo; vigencia en el Decreto 1079/2015 | **CONFIRMADA** (hoy arts. 2.2.1.4.7.3–4 del Decreto 1079); inclusión del conductor **NO VERIFICABLE** | SISJUR; Función Pública; Cancillería |
