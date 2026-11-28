# CA-6 (investigación) — Marco legal y costos para flota propia, arrendada o convenios (M1, pregunta de negocio 4)

Fecha de consulta de todas las fuentes: **2026-11-27**. Investigador: `investigador-fuentes` (prompt literal en `alucinaciones/prompts/CA-6a.md`).
Nivel de confianza: **alto** = texto leído en la fuente primaria; **medio** = fuente primaria abierta pero la vigencia artículo por
artículo no está probada; **bajo** = solo se vio en un resumen del buscador (no cuenta como verificado).

## Fe de erratas (verificación CA-6, 2026-11-27)

Correcciones de `docs/investigacion/CA-6_verificacion.md` (cazador-alucinaciones, prompt `alucinaciones/prompts/CA-6a-verificacion.md`;
evidencia en `alucinaciones/evidencias/CA-6/`). El texto original se conserva sin cambios más abajo, como evidencia de la cacería.
Decisiones de Camila del 27-nov al final.

| # | Sección afectada | Dice | Corrección | Sustento |
|---|---|---|---|---|
| E-1 | §8.3 | Arrendar en vez de comprar «mueve ~un tercio de la estructura» (costos fijos 32,99 %) | Arrendar sustituye solo el componente de capital («costo del vehículo y su apalancamiento»), cuyo peso no está en el boletín (T-9); conductores, combustible, peajes y seguros se mantienen. No se cuantifica el ahorro con el 32,99 %: en el año corrido los costos fijos aportaron 4,83 p.p. y la mano de obra sola 4,72 | V-20; candidato H-?? (CA-6a) en `alucinaciones/registro.md` |
| E-2 | Marco legal (omisión), T-2, T-5, T-6, consejo de «no mezclar» el Cap. 6 | No aparece la norma del refuerzo de temporada | **L-10**: Decreto 1079/2015, art. 2.2.1.6.3.5, modificado por el Decreto 1048 de 2026, art. 7 (5-ago-2026): el servicio especial puede suplir el parque de las empresas de pasajeros por carretera «en períodos de alta demanda». **L-11**: Resolución 264 de 2020 de MinTransporte: arts. 3–5 (convenios, ≤ 2 años, ruta completa), arts. 6–7 (contratos con servicio especial y su reporte), art. 8 (periodos de alta demanda: Semana Santa, 5-jun a 31-jul, receso escolar de octubre, 10-dic a 15-ene, puentes festivos). Cierra T-6; T-2: el Decreto 1017/2025 solo cambia el Cap. 7 (carga); T-5: sin norma de arriendo simple encontrada. Límite: la copia de la Res. 264 es un escaneo (fecha del acto no legible, `TODO(cita)`) | V-6, V-7, V-8, V-12 |
| E-3 | §1 y L-3/§8.2 | «3 % de la capacidad transportadora»; el tope es «mínima + 20 %» y el convenio cubre la brecha | 3 % de la capacidad transportadora **mínima**. El límite que ata es la capacidad **máxima fijada** por MinTransporte (≤ mínima + 20 %); el convenio es una figura estable (≤ 2 años, ruta completa), no un refuerzo de pico | V-1, V-3b |
| E-4 | C-1, C-2 | «indexadas a dic-2015»; «año corrido (sep-2026 vs. dic-2025)» | Base IV trimestre de 2015 = 100; año corrido = III trimestre 2026 frente a IV trimestre 2025 | V-13b, V-14b |
| E-5 | C-3 | «ausencia de un mercado establecido de alquiler de vehículos de pasajeros» como afirmación general | Es la conclusión del DANE sobre la encuesta básica de **2015** y sobre alquiler del vehículo **sin conductor** ni combustible | V-15 |
| E-6 | Nota de alcance (art. 2.2.1.6.8.1) | Cita el texto anterior | Sustituido por el Decreto 1048 de 2026, art. 15; la regla de ≤ 2 años sin renovaciones automáticas se mantiene | V-10 |

**Decisiones de Camila (27-nov):** (a) opciones de la pregunta 4: «propia» = propia o vinculada, hasta la capacidad máxima
fijada; «arrendada» = contrato con empresa de servicio especial en periodos de alta demanda (art. 2.2.1.6.3.5 mod. Dec. 1048/2026
y Res. 264/2020); «convenio» = figura estable entre empresas de carretera (≤ 2 años, ruta completa). (b) `fin_de_anio` del
calendario de M1 pasa a 10-dic a 15-ene con la Res. 264/2020, art. 8, como fuente (CA-1c).

## 1. Resumen

- **Marco legal: encontrado y leído en fuente primaria** (Decreto 1079 de 2015, versión integrada de Función Pública con
  actualización al 21-sep-2025). Los artículos relevantes son todos del Cap. 4 (pasajeros por carretera), con procedencia
  Decreto 171 de 2001. Lo que dice la norma, en una línea cada uno:
  - **Propia**: un vehículo de la empresa se entiende vinculado sin contrato; hay un mínimo de 3 % de la capacidad transportadora
    que debe ser de propiedad de la empresa o de sus socios (art. 2.2.1.4.7.1, 2.2.1.4.8.3).
  - **Vinculada** (de terceros): contrato de vinculación + tarjeta de operación; solo equipos registrados en el servicio público
    (arts. 2.2.1.4.8.1–8.3, 2.2.1.4.9.2).
  - **Arrendada**: **no encontré** en el capítulo una figura de arriendo simple (sin vinculación) de buses de otra empresa. Solo
    aparece el arrendamiento **financiero** (leasing) como forma de adquirir el vehículo. Esto es una ausencia dentro de lo
    buscado en el texto del Decreto 1079, no una prohibición expresa. Queda como `TODO(cita)` (ver §6).
  - **Convenio**: autorizado por el Ministerio (consorcio, unión temporal o asociación entre empresas habilitadas), solo sobre
    servicios ya autorizados a alguna de ellas (art. 2.2.1.4.6.8).
  - **Temporada alta**: el parágrafo del mismo artículo permite contratar con empresas de **servicio especial**, exclusivamente en
    las rutas autorizadas. Es la única mención literal de «temporada alta» en el Decreto 1079.
  - **Tope a la flota**: la capacidad transportadora máxima no puede superar la mínima en más de 20 % y el parque automotor no
    puede salirse de esos límites (art. 2.2.1.4.7.2). Es la restricción más relevante para «¿cuántos vehículos adicionales?».
- **Costos: no hay cifra absoluta citable** de costo por vehículo-día o por km, precio de compra, tarifa de alquiler ni costo de
  convenio, en las fuentes oficiales/institucionales que pude abrir. Lo oficial que sí existe es el **ICTIP del DANE**, que
  publica **índices y ponderaciones (pesos relativos)**, no pesos colombianos por vehículo. De ahí sale una estructura relativa de
  costos citable (combustibles 31,00 %, costos fijos 32,99 %, peajes y terminales 20,39 %, insumos 8,78 %, partes y
  mantenimiento 6,84 %).
- El propio DANE documenta que **no hay un mercado establecido de alquiler de vehículos de pasajeros** (cita en §4, fila C-3).
  Eso respalda que no se defienda una tarifa de alquiler de mercado.
- Cifras de medios o comerciales: no citables; en §5 (con la advertencia de que ni siquiera abrí esas páginas).
- **Candidatos a hallazgo (IA contradiciendo la fuente): ninguno.** Observación menor en §7.

## 2. Marco legal vigente (norma, fragmento literal, vigencia)

Fuente común de la tabla: Presidencia de la República de Colombia. (2015). *Decreto 1079 de 2015, por medio del cual se expide el
Decreto Único Reglamentario del Sector Transporte* (versión integrada con sus modificaciones, última actualización 21-sep-2025).
Función Pública, Gestor Normativo. https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=77889 (consultado el
2026-11-27). Ubicación: Libro 2, Parte 2, Título 1, Capítulo 4.

| # | Tema | Artículo (procedencia) | Fragmento literal | Qué implica para la pregunta 4 | Confianza |
|---|---|---|---|---|---|
| L-1 | Propia: vehículos de la empresa y mínimo de propiedad | 2.2.1.4.8.3 (Dec. 171/2001, art. 54) y 2.2.1.4.7.1 (art. 48) | «Los vehículos que sean de propiedad de la empresa habilitada, se entenderán vinculados a la misma sin que para ello sea necesario la celebración del contrato de vinculación.» / «Las empresas deberán acreditar como mínimo el 3% de capacidad transportadora mínima de su propiedad y/o de sus socios, que en ningún caso podrá ser inferior a un (1) vehículo, incluyéndose dentro de este porcentaje los vehículos adquiridos bajo arrendamiento financiero.» | La flota propia es una opción legal directa. La norma exige solo un mínimo de 3 % propio; el resto puede ser vinculado. | Medio-alto |
| L-2 | Vinculada (de terceros) | 2.2.1.4.8.1, 8.2, 8.3 (arts. 52–54) y 2.2.1.4.9.2 (art. 62) | «Las empresas habilitadas … sólo podrán hacerlo con equipos registrados en el servicio público.» / «La vinculación de un vehículo a una empresa de transporte público es la incorporación de éste al parque automotor de dicha empresa. Se formaliza con la celebración del respectivo contrato entre el propietario del vehículo y la empresa y se oficializa con la expedición de la tarjeta de operación por parte del Ministerio de Transporte.» / «El Ministerio de Transporte expedirá la tarjeta de operación únicamente a los vehículos legalmente vinculados a las empresas de transporte público debidamente habilitadas, de acuerdo con la capacidad transportadora fijada a cada una de ellas.» | Meter un vehículo de otro dueño al servicio exige vinculación formal y tarjeta de operación, es decir, un trámite ante el Ministerio y no una decisión de la semana. El contrato se rige por derecho privado (art. 2.2.1.4.8.3). | Medio-alto |
| L-3 | Tope de flota (capacidad transportadora) | 2.2.1.4.7.2 (art. 49) | «La capacidad transportadora máxima no podrá ser superior a la capacidad mínima incrementada en un veinte por ciento (20%). El parque automotor no podrá estar por fuera de los límites de la capacidad transportadora mínima y máxima fijada a la empresa.» | Un pico que pida más de +20 % sobre la capacidad mínima autorizada no se puede cubrir con flota propia o vinculada propia; hay que ir por convenio o por contratos con servicio especial. Este número 20 % viene de la norma, pero **no se sabe** cuál es la capacidad mínima autorizada de la empresa del caso (dato no disponible). | Medio-alto |
| L-4 | Convenios de colaboración empresarial | 2.2.1.4.6.8 (art. 42) | «El Ministerio de Transporte, por intermedio de la Subdirección de Transporte autorizará convenios de colaboración empresarial bajo las figuras del consorcio, unión temporal o asociación entre empresas habilitadas, encaminados a la racionalización del uso del equipo automotor … Los convenios se efectuarán exclusivamente sobre servicios previamente autorizados a alguna de las empresas involucradas, quien para todos los efectos continuará con la responsabilidad acerca de su adecuada prestación.» | Convenio = solo entre empresas **habilitadas**, con autorización previa del Ministerio y solo sobre rutas ya autorizadas. No es una compra de capacidad por un día. | Medio-alto |
| L-5 | Temporada alta / refuerzos | 2.2.1.4.6.8, parágrafo (art. 42) | «PARÁGRAFO. En épocas de temporada alta, las empresas de transporte de pasajeros por carretera podrán celebrar contratos con empresas de servicio especial para prestar el servicio exclusivamente en las rutas autorizadas.» | Es el mecanismo literal para el refuerzo de temporada alta. No define qué es «temporada alta» ni su duración (no inventar fechas). | Medio-alto |
| L-6 | Viajes ocasionales (otra modalidad, no refuerzo regular) | 2.2.1.4.1.1 (art. 8) y 2.2.1.4.6.5 (art. 39) | «Ocasional (o Expreso). Cuando el Ministerio de Transporte autoriza a las empresas habilitadas en esta modalidad la realización de un viaje dentro o fuera de sus rutas autorizadas, para transportar un grupo homogéneo de pasajeros …» | Un viaje ocasional es para un grupo homogéneo, no para vender tiquetes sueltos en la terminal. No sirve como refuerzo de demanda del tipo de `demanda_diaria`. Lectura mía; el texto no lo dice con esas palabras. | Medio |
| L-7 | Reestructuración de horarios entre empresas | 2.2.1.4.6.3 (art. 37) | «El acuerdo, que bajo ninguna circunstancia implica incremento de las capacidades transportadoras de las empresas, debe garantizar que la demanda será suficiente Y debidamente atendida …» | Otra vía de cooperación; no aumenta capacidad. Solo contexto. | Medio |
| L-8 | Grupos por capacidad (ya verificado en CA-2) | 2.2.1.4.7.3 y 2.2.1.4.7.4 | Ver `docs/investigacion/CA-2_verificacion.md` §6. | Sin cambios. | Alto (CA-2) |
| L-9 | Segundo conductor si el recorrido pasa de 8 h | Resolución 315 de 2013, art. 6 | Ver `docs/investigacion/CA-2_verificacion.md` §3. Citado solo para recordar que más vehículos de largo recorrido implican más conductores. | Sin cambios. | Alto (CA-2) |

**Vigencia.** La versión integrada de Función Pública que abrí no trae notas de modificación ni derogatoria al pie de los arts.
2.2.1.4.6.8, 2.2.1.4.7.1, 2.2.1.4.7.2, 2.2.1.4.8.1–8.3 ni 2.2.1.4.9.2; el texto es el compilado del Decreto 171 de 2001. La
cabecera de la página indica «Adicionado y modificado por el Decreto 1017 de 2025» (versión actualizada al 21-sep-2025) y una
lista de 39 vigencias a nivel de decreto, y la propia página advierte: «El Departamento Administrativo de la Función Pública no se
hace responsable de la vigencia de la presente norma». **No abrí** el Decreto 1017 de 2025 ni los decretos posteriores a
sep-2025, por lo que no descarto una modificación posterior. Tarea: `TODO(cita)` T-2.

**Nota de alcance.** El capítulo de **servicio especial** (art. 2.2.1.6.x) tiene sus propias reglas (p. ej. el contrato de
vinculación de flota no puede pasar de dos años y no admite renovaciones automáticas). No las apliqué al servicio de pasajeros por
carretera; no mezclar.

## 3. Cómo se citan las normas en el YAML (para mantener el estilo)

`configs/m1/operacion.yaml` cita «Decreto 1079 de 2015, arts. 2.2.1.4.7.3–2.2.1.4.7.4 (compila Decreto 171/2001, arts. 50–51)» y
remite a `docs/investigacion/CA-2_verificacion.md`. Si Camila incorpora L-1 a L-5, el formato análogo sería «Decreto 1079 de 2015,
art. 2.2.1.4.7.2 (compila Decreto 171/2001, art. 49)». Este informe no modifica el YAML.

## 4. Costos citables

| # | Dato | Valor | Unidad / alcance | Año | Clase de vehículo | Cita APA 7 y URL | Fragmento literal | Confianza |
|---|---|---|---|---|---|---|---|---|
| C-1 | Estructura relativa de costos del transporte intermunicipal de pasajeros (ponderaciones del ICTIP) | Combustibles 31,00 %; Insumos 8,78 %; Costos fijos 32,99 %; Peajes y uso de terminales 20,39 %; Partes, piezas y mantenimiento 6,84 %; Total 100 % | Peso relativo en el costo de **propietarios de vehículos** (no de la empresa), total nacional | Boletín del 3.er trim. 2026 (ponderaciones fijas con base en una encuesta de 2015, indexadas a dic-2015) | Total nacional (el índice se publica también por clase: automóvil, campero, camioneta, microbús, buseta y bus, pero no tengo los pesos por clase) | DANE. (2026, 22 de octubre). *Boletín técnico: Índice de Costos del Transporte Intermunicipal de Pasajeros (ICTIP), tercer trimestre 2026*. https://www.dane.gov.co/files/operaciones/ICTIP/bol-ICTIP-IIItrim2026.pdf | Tabla 1: «Combustibles 31,00 … Insumos 8,78 … Costos fijos 32,99 … Peajes y uso de terminales 20,39 … Partes, piezas, servicios de mantenimiento y reparación del vehículo 6,84 … Total 100,00» (texto extraído del PDF; no vi la imagen de la tabla) | Medio-alto |
| C-2 | Variación de costos (no nivel) | Trimestral III-2026: -0,13 %; año corrido (sep-2026 vs. dic-2025): 7,77 %; mano de obra de conductores y ayudantes, año corrido: 22,11 % | Variación porcentual de precios de la canasta | 2026 | Total nacional | Misma fuente que C-1 | «el ICTIP obtuvo una variación trimestral de -0,13 %»; «variación año corrido de 7,77 %»; «Mano de obra conductor(es) y ayudante(s) (22,11 %)» | Medio-alto |
| C-3 | Hecho: el DANE no pudo usar tarifas de alquiler como costo de capital porque no hay mercado establecido de alquiler de vehículos de pasajeros | (cualitativo) | Metodología del índice | 2018 (v2) | Intermunicipal | DANE. (2018). *Metodología general. Índice de Costos del Transporte Intermunicipal de Pasajeros (ICTIP)* (DSO-ICTIP-MET-001, v. 2). https://www.dane.gov.co/files/investigaciones/fichas/transporte/DSO-ICTIP-MET-001-V2.pdf, pág. 10 del documento | «la ausencia de un mercado establecido de alquiler de vehículos de pasajeros, repercutió en que la respuesta de los encuestados refiriera valores que incluían otros costos ya contabilizados previamente … Dada esta situación el cálculo de ponderaciones del ICTIP no utilizó este enfoque.» | Alto (documento leído completo) |
| C-4 | Qué incluye y qué excluye el índice | Incluye costos del propietario del vehículo (combustibles, insumos, costos fijos con mano de obra de conductores y auxiliares, peajes y terminales, partes y mantenimiento, costo de capital con depreciación). **Excluye** costos y gastos de la empresa de transporte. | Alcance | 2018 | Intermunicipal | Misma fuente que C-3, §2.1.3 | «Excluye los costos y los gastos asumidos por las empresas de transporte, debido a que no es posible asignar un costo (gasto) específico al vehículo.» | Alto |
| C-5 | Costo de capital: supuesto de valor residual | 20 % del valor de compra tras depreciación (supuesto de DANE, no precio de mercado) | Depreciación geométrica | 2018 | Intermunicipal | Misma fuente que C-3, pág. 11 | «para este caso se calcula como el 20% del valor de compra promedio del vehículo» | Alto |

**Límite de C-1 a C-5.** Son **índices y pesos**, no pesos colombianos. Con ellos se puede decir «el combustible pesa ~31 % del
costo de operar un vehículo» o «el costo de conductores creció 22,11 % en lo corrido de 2026», pero **no** «un bus-día cuesta X
COP». Además la estructura es de propietarios (incluye depreciación y costo de capital) y está fijada con una encuesta de 2015;
el DANE advierte que se actualiza solo cuando se rehace la encuesta básica.

## 5. Cifras NO citables (solo para que el equipo sepa que existen; no usarlas como dato)

Ninguna de estas páginas fue **abierta**; lo que sigue viene de títulos y resúmenes del buscador. No presentar como dato.

| # | Qué sugiere | URL | Por qué no sirve |
|---|---|---|---|
| N-1 | Lista de precios de busetas intermunicipales (resumen del buscador: minisenior 20 pasajeros 119.000.000 COP y senior 24 pasajeros 145.000.000 COP, año 2010) | https://www.carroya.com/noticias/archivo/precios-de-los-vehiculos-de-pasajeros-en-colombia-1732 | Sitio comercial, cifras de 2010, no abierta. |
| N-2 | Titular de prensa: «Scania entregó flota de 25 buses a Rápido Ochoa con inversión de 42.000 millones» | https://www.larepublica.co/empresas/con-inversion-de-42-000-millones-scania-entrego-flota-de-25-buses-a-rapido-ochoa-3980599 | Medio, no abierta. Dividir 42.000/25 daría un promedio por bus, pero eso sería un cálculo mío sobre un titular sin verificar. No usar. |
| N-3 | Precios de buses articulados o eléctricos de TransMilenio (prensa) | https://www.portafolio.co/negocios/vehiculo/un-bus-articulado-electrico-para-tm-en-bogota-costaria-mas-de-2-000-millones-635227 | Otro tipo de vehículo (urbano masivo), prensa. |
| N-4 | Tarifas de alquiler de vans de comparadores de viaje (Kayak, Discover Cars) | https://www.es.kayak.com/Alquileres-Van-Bogota.52059.cva.ksp | Comparador comercial, vans sin conductor, no es bus intermunicipal. |
| N-5 | Declaración de MinTransporte sobre libertad tarifaria (El Colombiano, ene-2026) | https://www.elcolombiano.com/negocios/mintransporte-sanciones-alza-pasajes-intermunicipales-colombia-2026-FD32578049 | Prensa; además es sobre tarifas al usuario (ingreso), no sobre costos. Se vio solo el resumen. |

**Buscado y no encontrado en fuente institucional:** precio de compra de bus/buseta/microbús intermunicipal; costo por km o por
vehículo-día; tarifa de alquiler de bus con o sin conductor; costo de un convenio; ausentismo (ya en CA-2).
Un intento con Colombia Compra Eficiente (precios de referencia, acuerdos marco de vehículos) devolvió documentos genéricos de
estudios de mercado y de vehículos livianos; no encontré un precio de bus intermunicipal ahí. No lo descarto: no hice una búsqueda
exhaustiva en SECOP.

## 6. Lista de TODO

- `TODO(dato-faltante)` T-1: costo operativo por vehículo-día y por km de bus/buseta/microbús intermunicipal en COP (fuente oficial).
  Sin esto el costo relativo «propia vs. arrendada vs. convenio» queda como supuesto.
- `TODO(dato-faltante)` T-3: precio de compra de bus, buseta y microbús (idealmente SECOP II, ficha de proceso de una entidad
  pública, con número de proceso).
- `TODO(dato-faltante)` T-4: tarifa de alquiler/uso temporal de bus de servicio especial por día o km. No hay mercado establecido
  según el DANE (C-3); pedir cotizaciones a empresas habilitadas sería un supuesto, no una fuente.
- `TODO(cita)` T-2: verificar vigencia posterior a sep-2025: abrir Decreto 1017 de 2025 y consultar el normograma del Ministerio de
  Transporte para ver si modifican los arts. 2.2.1.4.6.8, 2.2.1.4.7.1–7.2, 2.2.1.4.8.x.
- `TODO(cita)` T-5: norma que regule expresamente el arriendo (no financiero) de vehículos entre empresas de pasajeros por
  carretera, o que lo prohíba. Mi búsqueda de «arrend» en el texto del Decreto 1079 no halló nada para este capítulo.
- `TODO(cita)` T-6: resolución del Ministerio de Transporte que defina «temporada alta» (fechas o criterios). El parágrafo del art.
  2.2.1.4.6.8 no la define.
- `TODO(cita)` T-7: capacidad transportadora mínima y máxima **autorizada** de la empresa del caso (dato de la empresa; no es
  público para este conjunto). Sin ella no se puede traducir el +20 % a número de vehículos.
- `TODO(cita)` T-8: ficha de la Encuesta de costos de vehículos vinculados del DANE: la página oficial describe su propósito, pero
  no vi microdatos ni cuadros de resultados en pesos. Verificar si existen anexos del ICTIP con valores absolutos (el boletín solo
  trae índices; el anexo en Excel no lo abrí).
- `TODO(cita)` T-9: pesos del ICTIP **por clase de vehículo** (bus, buseta, microbús). Están en los anexos de DANE, que no abrí.

## 7. Candidatos a hallazgo

Ninguno. No hay una afirmación de IA con prompt guardado que contradiga estas fuentes. Observaciones que **no** son hallazgo:

- La página de DANE «Encuesta de costos de vehículos vinculados de transporte intermunicipal de pasajeros» llama al índice
  «Índice de Costos de Transporte Intermunicipal de Pasajeros (ICTC)», mientras que la metodología y los boletines lo llaman
  **ICTIP** (el ICTC es el de carga). Es un error de la página del DANE. Citar siempre ICTIP.
  URL: https://www.dane.gov.co/index.php/estadisticas-por-tema/transporte/encuesta-de-costos-de-vehiculos-vinculados-de-transporte-intermunicipal-de-pasajeros
- El resumen del buscador repitió ese «ICTC». Es un eco de la página del DANE, no una alucinación.

## 8. Qué se puede concluir con esto

**Defendible (con cita):**
1. **Las tres opciones tienen base legal distinta y no son intercambiables.** Propia/vinculada: dentro del tope de capacidad
   transportadora (mínima +20 %). Convenio: solo entre empresas habilitadas, con autorización del Ministerio, sobre rutas ya
   autorizadas. Refuerzo de temporada alta: contratos con empresas de servicio especial en las rutas autorizadas (parágrafo,
   art. 2.2.1.4.6.8). Esto sí puede entrar al informe y al blog.
2. **Cualquier recomendación cuantitativa de «flota adicional» debe contrastarse con el tope del +20 %** (art. 2.2.1.4.7.2), y
   la brecha de picos mayores a ese tope solo se cubre vía convenio o servicio especial. Sirve la regla; el número depende del dato de la
   empresa (T-7).
3. **Estructura relativa de costos**: combustible ~31 %, costos fijos ~33 % (incluye conductores), peajes y terminales ~20 %.
   Permite argumentar, por ejemplo, que una opción que reduzca costos fijos (arrendar, no comprar) mueve ~un tercio de la
   estructura, y que el costo de conductores sube más rápido que el promedio (22,11 % vs. 7,77 % en lo corrido de 2026). Hay que decir
   que son pesos de propietarios, con base de 2015.

**No defendible hoy:**
1. **Una comparación en pesos** de comprar vs. arrendar vs. convenio por vehículo-día: no existe cifra citable de compra, alquiler ni
   convenio. Si el informe de CA-6 la hace, todos los valores deben ir como `supuesto: true` en el YAML, con un análisis de
   sensibilidad (razón de costos, no niveles), tal como ya se hace con `costo_pasajero_sin_atender` y `costo_vehiculo_dia_sobrante`.
2. **Decir que «arrendar» es legalmente equivalente a «convenio»**: la norma leída no regula el arriendo simple en este modo
   (T-5). Presentarlo como hipótesis, no como hecho.
3. **Usar cifras de medios** (§5) como costo unitario.

**Sugerencia de redacción para la pregunta 4 (a decisión de Camila):** recomendar por criterio legal-operativo (primero flota propia
y vinculada hasta el tope, luego convenio, y servicio especial para picos de corta duración), y dejar los costos como escenarios
con razones relativas, citando el ICTIP solo para la estructura de pesos y la evolución de los costos laborales.

## 9. Archivos y evidencia

- Descargas de trabajo (no versionadas; carpeta de sesión): copia en texto del Decreto 1079 de Función Pública
  (`.../scratchpad/n/fp.txt`), boletín ICTIP III-2026 (`ictip.pdf`) y metodología (`met.pdf`). Los fragmentos literales de §2 y §4
  se copiaron de esas descargas.
- Límite de lectura: el texto del boletín ICTIP se extrajo de los flujos del PDF; las tablas están en texto plano (no vi las imágenes).
