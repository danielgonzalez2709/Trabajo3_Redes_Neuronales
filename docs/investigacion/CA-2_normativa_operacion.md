# CA-2 (investigación) — Normativa y parámetros operativos de M1

## Fe de erratas (verificación CA-2, 2026-11-26)

Correcciones C-1 a C-9 de `docs/investigacion/CA-2_verificacion.md` (secciones 8 y 9). El texto original del informe se
conserva sin cambios más abajo, como evidencia de la cacería de alucinaciones. Las correcciones C-7 a C-9 conciernen a
`configs/m1/operacion.yaml` y a `src/m1_demanda/operacion.py` (las aplica otro agente).

| # | Sección afectada | Dice | Corrección | Sustento |
|---|---|---|---|---|
| C-1 | §6 punto 1 | «en esa fecha (7-may-2024) regían 46 h» | Regían **47 h** (Ley 2101, art. 3; 46 h solo desde el 15-jul-2024). Contradice la tabla del propio §1.1 | CA-2_verificacion.md §8 H-a |
| C-2 | §1.1 (tabla), §1.2 (Nota), §7 (fila de jornada diaria) | 48 h en 2021–2023 por «art. 161 CST según Ley 50/1990, art. 20»; 8 h/día antes de 2025 por la Ley 50/1990 | Ese texto fue sustituido por el art. 2 de la **Ley 2101 de 2021** (vigente desde el 15-jul-2021), que no trae tope diario. Las 48 h de 2021–2023 salen de la gradualidad del art. 3; el tope de 8 h/día en el art. 161 solo rige desde el 25-jun-2025 (Ley 2466, art. 11). Base legal 2021–2025: Ley 2101 (arts. 2–3), no la Ley 50 | CA-2_verificacion.md §1 y §8 H-b |
| C-3 | §1.2 y §2 (cita de la Ley 2466) | «[título a cotejar]» y URL de normogramas | Título literal: «por medio de la cual se modifica parcialmente normas laborales y se adopta una Reforma Laboral para el trabajo decente y digno en Colombia» (Diario Oficial 53.160, 25-jun-2025). Fuentes: Senado y Función Pública | CA-2_verificacion.md §2 |
| C-4 | §8 (`TODO(cita)` 1, 2, 3, 5, 6) | Abiertos | Cerrados con las fuentes de la verificación (Ley 2101 y cronograma, Ley 2466 completa, vigencia de la Res. 315/2013). El 4 (Decreto 1393/1970 art. 56: vigencia) sigue abierto; el 7 queda parcial (PESV sin cifras; circular de 2026 solo vía comunicado oficial) | CA-2_verificacion.md §1–§5 y §9 C-4 |
| C-5 | §2 (rango de capacidad) | Decreto 171 de 2001, arts. 50–51 | Compilado en el **Decreto 1079 de 2015**, arts. 2.2.1.4.7.3 y 2.2.1.4.7.4 (la cita vigente; procedencia: Decreto 171/2001, arts. 50–51). La norma no dice si el límite incluye al conductor | CA-2_verificacion.md §6 |
| C-6 | §6 punto 4 | El «16 de julio» lo usa «un diario» | También lo usó el MinTrabajo en su comunicado de 2023; el concepto jurídico del MinTrabajo y el comunicado de 2026 usan el 15 de julio | CA-2_verificacion.md §1 (matiz) |
| C-7 | `configs/m1/operacion.yaml` | `supuesto: true` en la jornada diaria y el umbral de segundo conductor | Pasan a `fuente` con las citas de la tabla del §7 de la verificación (la aplica otro agente) | CA-2_verificacion.md §7 y §9 |
| C-8 | coherencia, no alucinación | `segundo_conductor_activo = 0` con 10 h de recorrido Bogotá–Cali | La Res. 315/2013 art. 6 obliga a dos conductores (> 8 h); dejarlo en 0 es una cota baja | CA-2_verificacion.md §9 |
| C-9 | coherencia, no alucinación | 7 h efectivas × 7 días sin descanso | 49 h/semana, por encima de cualquier máximo semanal 2021–2026 (48 → 42 h) | CA-2_verificacion.md §9 |

Nota sobre H-a y H-b: son los candidatos a hallazgo de la verificación (§8 de `CA-2_verificacion.md`); aquí solo se corrige el informe.

---------------------------------------------------------------------------------------------------

Fecha de consulta de todo el informe: **2026-11-26**. Agente: investigador-fuentes (Sonnet). Prompt: `alucinaciones/prompts/CA-2a.md`.
Cómo se verificó: «**leído en el PDF**» = abrí el documento oficial y leí su texto; «**vía lector**» = abrí la página oficial con un lector que
resume (los fragmentos salen de su transcripción en segmentos cortos; hay que cotejar contra la URL antes de citar en el blog);
«**no abierta**» = solo la vi mencionada en una fuente secundaria (no es evidencia). Dos sitios oficiales (Función Pública
`funcionpublica.gov.co`, Senado `secretariasenado.gov.co`) no se pudieron abrir desde aquí (error de certificado / conexión rechazada); los
textos de las leyes se leyeron en normogramas de entidades públicas (Cancillería, Colpensiones, Alcaldía de Bogotá). `TODO(cita)`: cotejar
con Función Pública o Senado.

## 1. Jornada de los conductores

### 1.1 Ley 2101 de 2021 (jornada máxima semanal; reducción gradual)
- **Dato:** el máximo semanal baja gradualmente a 42 h; la ley rige desde su publicación (15-jul-2021).
- **Norma:** Ley 2101 de 2021 (julio 15), «Por medio de la cual se reduce la jornada laboral semanal de manera gradual, sin disminuir el salario
  de los trabajadores y se dictan otras disposiciones», Diario Oficial No. 51.736 del 15-jul-2021. Art. 2 modifica el art. 161 CST; art. 3
  gradualidad; art. 8 vigencia.
- **Fragmentos (vía lector, Cancillería):**
  - Art. 2: «La duración máxima de la jornada ordinaria de trabajo es de cuarenta y dos (42) horas a la semana» (el MinTransporte lo transcribe
    completo en el concepto de 2025, leído en el PDF: «…que podrán ser distribuidas, de común acuerdo, entre empleador y trabajador, en 5 o 6 días a la semana, garantizando siempre el día de descanso, salvo las siguientes excepciones»).
  - Art. 3: «Transcurridos dos (2) años a partir de la entrada en vigencia de la ley, se reducirá una (1) hora de la jornada laboral semanal, quedando en 47 horas semanales. Pasados tres (3) años de la entrada en vigencia de la ley, se reducirá otra hora de la jornada laboral semanal, quedando en 46 horas semanales. A partir del cuarto año de la entrada en vigencia de la ley, se reducirán dos (2) horas cada año hasta llegar a las cuarenta y dos (42) horas semanales».
  - Art. 8: «La presente ley empezará a regir a partir de la fecha de su publicación».
- **Cronograma (DERIVADO por mí del art. 3 y de la fecha de entrada en vigor; la ley no trae fechas calendario):**

| Periodo | Máximo semanal | Base |
|---|---|---|
| 15-jul-2021 a 14-jul-2023 | 48 h (art. 161 CST según Ley 50/1990, art. 20; el art. 3 permite al empleador adoptar antes las 42 h) | art. 3 + concepto MinTransporte 2024 (§1.4) |
| 15-jul-2023 a 14-jul-2024 | 47 h | art. 3, «transcurridos dos años» |
| 15-jul-2024 a 14-jul-2025 | 46 h | art. 3, «pasados tres años» (consistente con la consulta del concepto 20251340607391: «46 horas semanales para el año en curso 2024») |
| 15-jul-2025 a 14-jul-2026 | 44 h | art. 3, «a partir del cuarto año… dos horas cada año» (derivado) |
| desde 15-jul-2026 | 42 h | art. 3 (derivado). Prensa y Deloitte dicen 15-jul-2026 (secundarias); un diario dice 16-jul (ver §6, nota) |

  Por año calendario (para el periodo del trabajo 2021–2023, y el horizonte de prueba): 2021 y 2022 → 48; 2023 → 48 hasta el 14-jul y 47 después;
  2024 → 47 / 46; 2025 → 46 / 44; 2026 → 44 / 42. **Decisión para Camila:** el valor del periodo de prueba (¿cuándo cae el horizonte de 30 días?).
- **Vigencia:** vigente. Art. 2 marcado «condicionalmente exequible» en el normograma; la sentencia es **C-507 de 2023** (22-nov-2023), cuyo
  condicionamiento se refiere al servicio doméstico interno (art. 162 CST), no a conductores (vía buscador; **no abierta** la sentencia:
  `TODO(cita)` abrir https://www.corteconstitucional.gov.co/relatoria/2023/C-507-23.htm).
- **URLs:** https://cancilleria.gov.co/sites/default/files/Normograma/docs/ley_2101_2021.htm (abierta, vía lector);
  https://funcionpublica.gov.co/eva/gestornormativo/norma.php?i=166506 (oficial; error de certificado desde aquí, `TODO(cita)` cotejar).
- **Cita APA 7:** Congreso de la República de Colombia. (2021, 15 de julio). *Ley 2101 de 2021: Por medio de la cual se reduce la jornada laboral semanal de manera gradual, sin disminuir el salario de los trabajadores y se dictan otras disposiciones*. Diario Oficial No. 51.736. https://cancilleria.gov.co/sites/default/files/Normograma/docs/ley_2101_2021.htm (consultado el 26 de noviembre de 2026).
- **Confianza:** alta para 42 h final y para 47/46 (texto de la ley); media para 44 h y las fechas exactas (derivadas).

### 1.2 Ley 2466 de 2025 (reforma laboral): nueva redacción del art. 161 CST, descanso obligatorio y horas extras
- **Dato:** el art. 161 CST vuelve a fijar 8 h diarias y 42 semanales, remitiendo a la gradualidad de la Ley 2101; jornada flexible 4–9 h/día; turnos sucesivos de
  máx. 6 h/día y 36 h/semana; horas extras máx. 2 diarias y 12 semanales; recargo del 100 % por trabajo en día de descanso obligatorio con aplicación gradual.
- **Norma:** Ley 2466 de 2025 (junio 25), Diario Oficial No. 53.160 del 25-jun-2025. Arts. 11 (modifica art. 161 CST), 13 (modifica art. 22 Ley 50/1990), 14 (modifica art. 179 CST).
- **Fragmentos (vía lector, Colpensiones):**
  - Art. 11: «La duración máxima de la jornada ordinaria de trabajo es de ocho (8) horas al día, sin perjuicio de lo establecido en el artículo 3o de la Ley 2101 de 2021 sobre la aplicación gradual, y una jornada máxima de cuarenta y dos (42) horas a la semana».
  - Art. 11, lit. a: «…jornadas diarias flexibles de trabajo, distribuidas en máximo seis días a la semana con un día de descanso obligatorio… teniendo como mínimo cuatro (4) horas continuas y máximo hasta nueve (9) horas diarias».
  - Art. 11, lit. d: «…el respectivo turno no exceda de seis (6) horas al día y treinta y seis (36) a la semana».
  - Art. 13: «En ningún caso las horas extras de trabajo, diurnas o nocturnas, podrán exceder de dos (2) horas diarias y doce (12) semanales».
  - Art. 14 (art. 179 CST): «El trabajo en día de descanso obligatorio, o días de fiesta se remunera con un recargo del ciento por ciento (100%)…»; parágrafo transitorio: 80 % desde 1-jul-2025, 90 % desde 1-jul-2026, 100 % desde 1-jul-2027.
  - El texto leído no regula expresamente la jornada de conductores.
- **Vigencia:** vigente a la fecha, salvo lo que no pude leer (el lector solo cubrió los primeros 100 000 de 124 208 caracteres; notas de vigencia de los arts. 11, 13 y 14: ninguna visible). El art. 10 (nocturno 19:00–06:00) entra seis meses después de la sanción.
- **URL:** https://normativa.colpensiones.gov.co/compilacion/docs/ley_2466_2025.htm (abierta, vía lector). Función Pública: https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=260676 (`TODO(cita)` cotejar).
- **Cita APA 7:** Congreso de la República de Colombia. (2025, 25 de junio). *Ley 2466 de 2025: Por medio de la cual se adopta una reforma laboral para el trabajo decente y digno en Colombia* [título a cotejar]. Diario Oficial No. 53.160. https://normativa.colpensiones.gov.co/compilacion/docs/ley_2466_2025.htm (consultado el 26 de noviembre de 2026). `TODO(cita)`: confirmar el título literal.
- **Confianza:** media-alta.
- **Nota:** art. 11 ya no es «solo 42 h/semana»: añade el tope diario de 8 h. Para M1 (jornada efectiva) el valor diario de 8 h viene de aquí (rige desde 25-jun-2025) y de la Ley 50/1990 art. 20 antes (según el concepto MinTransporte 2024, leído en el PDF).

### 1.3 Resolución 315 de 2013 (MinTransporte): segundo conductor y descansos
- **Dato:** en servicio público de pasajeros, si la operación dura más de 8 h de recorrido entre origen y destino debe haber segundo conductor; las empresas deben «garantizar los descansos necesarios». **No fija horas de conducción continua ni de pausa.**
- **Norma:** Resolución 315 de 2013 (febrero 6), Ministerio de Transporte, «Por la cual se adoptan unas medidas para garantizar la seguridad en el transporte público terrestre automotor y se dictan otras disposiciones». Diario Oficial No. 48.697 del 7-feb-2013. Art. 6.
- **Fragmento (leído en los dos conceptos del MinTransporte en PDF y vía lector en Alcaldía de Bogotá):** «Artículo 6°. Segundo conductor. Todos los vehículos de servicio público de transporte terrestre de pasajeros y mixto, para la realización de operaciones de transporte con una duración superior a ocho (8) horas de recorrido entre el lugar de origen y el lugar de destino, deberán contar con un segundo conductor. Las empresas de transporte deberán adoptar las medidas conducentes para garantizar los descansos necesarios de los conductores. Parágrafo 1°. Contar con dos conductores… se entiende como una condición necesaria para prestación del servicio. La inobservancia de esta medida dará lugar a la inmovilización del vehículo…».
- **Vigencia:** la página de la Alcaldía de Bogotá no muestra modificación ni derogatoria del art. 6 (solo «aclarado» el art. 3 por la Res. 378 de 2013), y el MinTransporte la aplica en conceptos de 2024 y 2025. **No encontré una derogatoria**; no pude revisar el Decreto 1079 de 2015 (compilación) ni la Resolución Única 20223040045295: `TODO(cita)` descartar derogatoria por compilación.
- **URLs:** https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=51704 ; https://normativa.colpensiones.gov.co/colpensiones/compilacion/docs/resolucion_mintransporte_0315_2013.htm ; transcripción en los PDF del §1.4.
- **Cita APA 7:** Ministerio de Transporte. (2013, 6 de febrero). *Resolución 315 de 2013: Por la cual se adoptan unas medidas para garantizar la seguridad en el transporte público terrestre automotor y se dictan otras disposiciones*. Diario Oficial No. 48.697. https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=51704 (consultado el 26 de noviembre de 2026).
- **Confianza:** alta para el texto del art. 6; media para la vigencia.

### 1.4 Conceptos del Ministerio de Transporte sobre la jornada de conductores (leídos en el PDF completo)
- **Concepto Radicado MT 20251340607391, 16-may-2025** (Oficina Asesora Jurídica; asunto «Horas laborales conductores de carga pesada»). Fragmentos:
  «la jornada laboral de los conductores en principio se regirá por lo pactado por las partes al momento de la suscripción del contrato de trabajo y, en su defecto, será la máxima legal, esto es, la prevista en el artículo 161 del Código Sustantivo del Trabajo, modificado por el artículo 2º de la Ley 2101 de julio 15 de 2021…, teniendo en cuenta la gradualidad establecida por el artículo 3º ibídem.»
  y «las disposiciones que atañen la operación de vehículos de transporte publico terrestre, no contempla excepciones ni salvedades respecto de la jornada legal laboral de los conductores».
  Cita también el art. 36 de la Ley 336 de 1996: «La jornada de trabajo de quienes tengan a su cargo la conducción u operación de los equipos destinados al servicio público de transporte será la establecida en las normas laborales y especiales correspondientes.»
  Cierra con: concepto «no es de obligatorio cumplimiento, ni tiene efectos vinculantes» (art. 28 CPACA).
  URL: https://mintransporte.gov.co/info/mintransporte/media/anexos/WOrLn9pt.pdf
- **Concepto Radicado MT 20241340513041, 7-may-2024** (asunto «Jornada laboral conductores»). Mismo marco; aplica «ocho (8) horas al día y cuarenta y ocho (48) a la semana» (art. 161 CST «Modificado por la Ley 50 de 1990») y concluye que operaciones de pasajeros de más de 8 h de recorrido exigen segundo conductor. URL: https://mintransporte.gov.co/info/mintransporte/media/anexos/hVsnRpHD.pdf
- **Cita APA 7 (modelo):** Ministerio de Transporte, Oficina Asesora de Jurídica. (2025, 16 de mayo). *Concepto sobre horas laborales de conductores de carga pesada* (Radicado MT No. 20251340607391). https://mintransporte.gov.co/info/mintransporte/media/anexos/WOrLn9pt.pdf (consultado el 26 de noviembre de 2026). Ídem para 20241340513041 (2024, 7 de mayo).
- **Vigencia:** son conceptos (orientación, no vinculantes); sirven para respaldar la lectura «no hay norma especial; rige la general», no como norma.
- **Confianza:** alta (texto leído).

### 1.5 Decreto 1393 de 1970, art. 56 (tope de 10 h diarias para conductores de empresas de transporte) — SIN VIGENCIA VERIFICADA
- **Dato:** una sentencia de la Corte Suprema (Sala de Casación Laboral, rad. 22189, 4-ago-2004, M.P. Camilo Tarquino Gallego) cita el art. 56: «ART. 56.- Las empresas de transporte y por razones de seguridad pública, no podrán fijar a los conductores jornadas de trabajo diario superior a 10 horas» y lo trata como tope, no como jornada obligatoria (vía lector, Colpensiones: https://normativa.colpensiones.gov.co/colpensiones/docs/csj_scl_22189_2004.htm).
- La consulta a la que responde el concepto de 2025 afirma que la sentencia SL8675-2017 declara vigente el art. 56 (**no abierta**; el concepto la cita solo en nota al pie para otra cosa: definición de jornada). El MinTransporte **no** aplica el art. 56 en su respuesta: remite a la regla general (arts. 161 CST / Ley 336/1996 art. 36).
- **No encontré** el texto oficial del Decreto 1393/1970 ni una nota de vigencia. `TODO(cita)`: abrir el decreto en el Gestor Normativo y la sentencia SL8675-2017 (Corte Suprema, rad. 47138, 8-mar-2017) y decidir si el tope de 10 h entra al YAML.
- **Confianza:** baja (vigencia sin comprobar). **No usar como valor de jornada hasta cerrar el TODO.**

### 1.6 Tiempos máximos de conducción continua/diaria, pausas, descanso entre jornadas y descanso semanal
- **Conducción continua/diaria/pausas:** **no encontré ninguna norma colombiana** que fije horas máximas de conducción continua o diaria ni pausas obligatorias para el servicio público de pasajeros. Lo único primario es el art. 6 de la Res. 315/2013 (§1.3: «descansos necesarios», sin cifra; segundo conductor > 8 h de recorrido). Una guía comercial (`logitools.co`, **fuente secundaria**) afirma que para carga «no hay hoy en Colombia un tope legal de horas de conducción» y que para pasajeros solo aplica el segundo conductor > 8 h y «garantizar los descansos de sus conductores»; menciona la Res. 40595 de 2022 (PESV, prevención de fatiga) y una circular conjunta MinTransporte–MinTrabajo 20261300000087 (9-mar-2026): **no abiertas**, `TODO(cita)`. Cualquier cifra de «5 h de conducción continua, 30 min de pausa, 10 h diarias, 8 h de descanso» que aparezca en blogs o en IAs **no tiene fuente primaria hallada** (la guía las marca como provisionales y la búsqueda las atribuyó a la Res. 315/2013, que no las contiene según su art. 6 leído).
- **Descanso entre jornadas:** sin norma específica hallada. `TODO(cita)`.
- **Descanso semanal obligatorio:** el art. 161 CST (según Ley 2101/2466) exige «garantizando siempre el día de descanso»; el art. 11 de la Ley 2466 dice «un día de descanso obligatorio, que podrá coincidir con el día domingo»; el art. 179 CST (modificado por Ley 2466 art. 14) regula el recargo. No abrí los arts. 172–178 CST: `TODO(cita)` si se quiere citar el descanso dominical remunerado.
- **Confianza:** alta en «no hay norma específica de horas de conducción hallada en las fuentes oficiales abiertas», sin garantía de exhaustividad (no consulté el Código Nacional de Tránsito ni la Resolución Única Compilatoria).

## 2. Capacidad por clase de vehículo
- **Clases en los datos:** conjunto completo (DA-2, medido 2026-11-24): BUS, MICROBUS, BUSETA, CAMIONETA, AUTOMOVIL, CAMPERO. `resumen_datos.json` las menciona todas. No pude leer `data/processed/m1/demanda_detalle.parquet` (el `.venv` no tiene pandas/pyarrow): `TODO(dato-faltante)` confirmar qué clases quedan en las 6 series de M1 y cuánto pesa cada una.
- **Norma:** Decreto 171 de 2001 (5-feb-2001, D.O. 44.318), reglamenta el servicio público de transporte terrestre automotor de pasajeros por carretera; arts. 50 y 51, leídos vía lector en Alcaldía de Bogotá (https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=4306). Fragmentos: art. 50: «GRUPO A: 4 a 9 pasajeros», «GRUPO B: 10 a 19 pasajeros», «GRUPO C: más de 19 pasajeros»; art. 51: «Automóvil - Campero - Camioneta Grupo A», «Microbús - Vans Grupo B», «Buseta - Bus Grupo C».
- **Conclusión: la norma da rangos, no una capacidad por clase.** BUS y BUSETA comparten el Grupo C («más de 19», sin tope), MICROBUS es 10–19, y el resto 4–9. **No hay capacidad fija en la norma: el valor por clase es supuesto** (puede apoyarse en el máximo/percentil de pasajeros por despacho observado en los datos, que es dato propio, no norma). Cualquier IA o blog que diga «un bus tiene 40 sillas por norma» sería hallazgo.
- **Vigencia:** el Decreto 171/2001 fue modificado por el Decreto 198 de 2013 (arts. de los capítulos II y III del Título IV, 43 y 44), con derogatoria parcial por el Decreto 2963 de 2002 (arts. 30–34, nivel preferencial de lujo) y nulidades del Consejo de Estado (art. 8 lit. c; partes de los arts. 54, 56, 57). Los arts. 50 y 51 no aparecen marcados. Está compilado en el Decreto 1079 de 2015 (según otra fuente secundaria; la página de Alcaldía no lo indica). `TODO(cita)`: localizar la numeración 2.2.1.4.x equivalente en el Decreto 1079 de 2015 y confirmar que el contenido de los arts. 50–51 sigue ahí; no pude abrir Cancillería (403) ni Función Pública.
- **Cita APA 7:** Presidencia de la República de Colombia. (2001, 5 de febrero). *Decreto 171 de 2001: Por el cual se reglamenta el Servicio Público de Transporte Terrestre Automotor de Pasajeros por Carretera* [título a cotejar]. Diario Oficial No. 44.318. https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=4306 (consultado el 26 de noviembre de 2026).
- **Confianza:** media-alta en que la norma da solo rangos; media en la vigencia. (Un resumen del Decreto 1079 de 2015 en un buscador devolvió la misma tabla; no es evidencia adicional.)

## 3. Diccionario del conjunto `eh75-8ah6` (datos.gov.co)
Reabierto hoy el JSON de metadatos (https://www.datos.gov.co/api/views/eh75-8ah6.json; `rowsUpdatedAt` = 1777788411 → 2026-05-03). Coincide con `docs/investigacion/DA-2_fuentes_m1.md` §1.3:
- `clase_vehiculo`: «Identificador numérico dado por el RUNT» (los datos traen texto: BUS, BUSETA, MICROBUS, CAMIONETA, AUTOMOVIL, CAMPERO). **El diccionario no da capacidad.**
- `despachos`: «Número vehículos de transporte de pasajeros por carretera que salen desde la terminal».
- `pasajeros`: «Número de pasajeros que abordaron viaje desde la terminal de transporte. Las terminales en tránsito sólo deben reportar los pasajeros que abordaron el vehículo en dicha terminal.»
- `tipo_despacho`: «1 = Si el despacho de la ruta es en origen, y 2 = Si el despacho de la ruta es en transito».
- Nada nuevo frente a DA-2. **Cita APA 7:** Superintendencia de Transporte. (2026). *Operación de pasajeros y despacho de vehículos en la modalidad de transporte de pasajeros por carretera* [Conjunto de datos]. Datos Abiertos Colombia. https://www.datos.gov.co/d/eh75-8ah6 (consultado el 26 de noviembre de 2026). **Confianza:** alta.

## 4. Tiempo de ciclo y horas de operación por ruta
- **No encontré fuente oficial** con distancia o tiempo de viaje para Bogotá–Cali, Bogotá–Sogamoso ni Pasto–Ipiales. La búsqueda devolvió solo medios y calculadoras (Portafolio: Bogotá–Cali 445–460 km; El País Cali: 465 km «según Google Maps»; Ruta0: 426 km; tiempos en bus de 9,5 a 13,5 h según blog/medio): **todo secundario, con cifras inconsistentes entre sí; no usar como cita.** Para Sogamoso, Pasto–Ipiales: nada. INVÍAS (portal Viajero Seguro) y la tabla de distancias del MinTransporte/INVÍAS no se pudieron abrir/localizar: `TODO(cita)`.
- **Consecuencia:** tiempo de ciclo y horas de operación son **supuesto** (o dato propio medido en la fuente, si Camila decide medir algo). Si se supone un viaje Bogotá–Cali de más de 8 h, la Res. 315/2013 art. 6 exige **segundo conductor** en esa ruta: afecta la fórmula de conductores (el «supuesto» de duración activa o no una obligación normativa; Camila debe decidirlo explícitamente).

## 5. Ausentismo y costos
- **Ausentismo:** **no hay cifra oficial** de DANE, MinTrabajo o Supertransporte aplicable a conductores de transporte de pasajeros (no encontrada). Lo hallado: un informe de la Secretaría Distrital de la Mujer (2025: 9,18 %, entidad distrital, no representativo), la Encuesta de Ausentismo de ANDI-Cestla (privada, cifra general **no vista**) y prensa. **Supuesto** con justificación; `TODO(cita)` opcional: abrir la encuesta ANDI-Cestla y citarla como referencia (no norma).
- **Costos (quedarse corto vs. sobrar):** no hay cifra oficial; es parámetro de decisión de negocio. **Supuesto** (y análisis de sensibilidad, que ya pide el enunciado).

## 6. Candidatos a hallazgo para la cacería
1. **CANDIDATO H-?? (Normativa, sin IA con prompt guardado todavía): concepto MinTransporte 20241340513041 (7-may-2024) aplica art. 161 CST «Modificado por la Ley 50 de 1990… ocho (8) horas al día y cuarenta y ocho (48) a la semana» como vigente**, cuando la Ley 2101 de 2021 (art. 2) ya había modificado ese artículo en 2021 y en esa fecha regían 46 h (art. 3). Evidencia: PDF p. 2–3 del concepto de 2024 frente a p. 2–3 del concepto de 2025 (que sí cita el art. 161 modificado por la Ley 2101) y el texto de la Ley 2101. Si un agente del equipo repitió «48 h» desde esa fuente, es hallazgo; verificar en los prompts guardados de `alucinaciones/prompts/`. (Es error de una fuente oficial no vinculante, no de IA; Camila decide si va a registro como hallazgo de fuente.)
2. **CANDIDATO: concepto 20251340607391, p. 6: «exceda las ocho (8) horas diarias»** frente al texto de la Res. 315/2013 art. 6 («duración superior a ocho (8) horas de recorrido entre el lugar de origen y el lugar de destino», p. 4 del mismo concepto). Parafrasear «8 horas diarias» cambia el sentido (recorrido vs. jornada). Citar el art. 6 literal, no el concepto.
3. **CANDIDATO (si una IA lo afirma): «el tope de conducción es 5 h continuas / 10 h diarias por la Res. 315/2013».** La Res. 315/2013 art. 6 (leído) solo dice «descansos necesarios» y segundo conductor > 8 h de recorrido; no trae esas cifras. La guía comercial que las menciona las marca provisionales. Pendiente: buscar si algún prompt/respuesta de una IA del equipo ya lo afirmó (no lo tengo, solo es un punto de revisión).
4. **Nota (no hallazgo):** una nota de prensa da inicio de las 42 h el «16 de julio de 2026»; otras y Deloitte, el 15. La ley no trae fecha calendario: el 15-jul-2026 es derivado (fecha de publicación + 5 años). No citar un día como si fuera de la ley.

## 7. Tabla final: parámetro → valor propuesto → `fuente` o `supuesto: true`

| Parámetro (`operacion.yaml`) | Valor propuesto | Origen | Nota |
|---|---|---|---|
| Jornada ordinaria máxima semanal | 2021–14-jul-2023: 48 h; luego 47, 46, 44 y 42 h desde 15-jul-2026 (cronograma §1.1) | **`fuente`:** Ley 2101 de 2021 arts. 2–3 (+ Ley 2466 de 2025 art. 11) | cronograma derivado del art. 3; elegir el valor según la fecha del horizonte de prueba (**Camila decide**) |
| Jornada ordinaria máxima diaria | 8 h | **`fuente`:** Ley 2466 de 2025 art. 11 (art. 161 CST); antes Ley 50/1990 art. 20 (según concepto MinTransporte 2024) | rige desde 25-jun-2025; texto vía lector |
| Horas extras máximas | 2/día y 12/semana | **`fuente`:** Ley 2466 de 2025 art. 13 | solo si el modelo usa extras |
| Jornada «efectiva» de conducción | a decidir | **`supuesto: true`** | no hay norma de horas de conducción (§1.6) |
| Tope de 10 h diarias (Decreto 1393/1970 art. 56) | no incluir aún | `TODO(cita)` | vigencia sin verificar (§1.5) |
| Pausas / descansos dentro de la jornada | sin cifra normativa | **`supuesto: true`** (cita solo el principio) | Res. 315/2013 art. 6: «descansos necesarios», sin horas |
| Descanso entre jornadas | sin cifra normativa | **`supuesto: true`** | `TODO(cita)` |
| Descanso semanal | 1 día obligatorio a la semana | **`fuente`:** art. 161 CST (Ley 2101 art. 2; Ley 2466 art. 11) | lectura literal: «garantizando siempre el día de descanso» |
| Segundo conductor | obligatorio si el recorrido origen–destino > 8 h | **`fuente`:** Res. 315 de 2013 art. 6 | aplica a Bogotá–Cali si el tiempo de ciclo supuesto > 8 h |
| Capacidad por clase (BUS, BUSETA, MICROBUS, etc.) | por decidir (rango normativo: Grupo C > 19; Grupo B 10–19; Grupo A 4–9) | **`supuesto: true`** (el rango sí lleva `fuente` Decreto 171/2001 arts. 50–51) | norma no fija capacidad exacta |
| Ocupación objetivo | por decidir | **`supuesto: true`** | sin norma hallada |
| Tiempo de ciclo por ruta; horas de operación | por decidir | **`supuesto: true`** | sin fuente oficial de distancia/tiempo (§4) |
| Ausentismo | por decidir | **`supuesto: true`** | sin cifra oficial (§5) |
| Costo de quedarse corto / de sobrar | por decidir | **`supuesto: true`** | decisión de negocio |
| Cuantil usado | por decidir | decisión de Camila / `supuesto: true` | no es de norma |

## 8. Lista de `TODO(cita)` abiertos
1. Cotejar Ley 2101/2021 (arts. 2, 3, 8) con Función Pública o Senado (error de certificado y conexión desde aquí).
2. Cotejar Ley 2466/2025 arts. 11, 13, 14 con Función Pública/Senado/Diario Oficial; leer el resto del texto (últimos 24 208 caracteres) y confirmar título literal.
3. Abrir sentencia C-507 de 2023 y confirmar que no afecta conductores.
4. Decreto 1393 de 1970 art. 56: texto oficial y vigencia; sentencia SL8675-2017 (rad. 47138). Decidir si se usa.
5. Resolución 315 de 2013 art. 6: descartar derogatoria por el Decreto 1079 de 2015 / Resolución 20223040045295 (Resolución Única Compilatoria).
6. Decreto 171 de 2001 arts. 50–51: equivalencia en el Decreto 1079 de 2015 y vigencia actual; título literal del decreto.
7. Res. 40595 de 2022 (PESV, fatiga) y Circular conjunta 20261300000087 (9-mar-2026): abrir y decidir si aportan una obligación citable.
8. Arts. 172–178 CST (descanso dominical remunerado), si se cita.
9. Distancia/tiempo de recorrido de las tres rutas (INVÍAS, Viajero Seguro, MinTransporte).
10. Ausentismo: opcional, encuesta ANDI-Cestla como referencia no normativa.
11. `TODO(dato-faltante)`: clases de vehículo y su peso en `demanda_detalle.parquet`, y máximo/percentil de pasajeros por despacho por clase (no pude leer el parquet; el `.venv` no trae pandas).

## 9. Decisiones que debe tomar Camila
1. **Qué valor semanal usar:** 2021–2023 es el periodo histórico, pero el horizonte de prueba/operación va a 2026: ¿se usa 42 h (vigente desde 15-jul-2026, derivado) o el valor del año del horizonte? Documentar la fecha.
2. **Jornada efectiva diaria vs. 8 h legales:** la norma solo da el tope de 8 h/día y 42 h/semana; las horas de conducción efectiva son supuesto.
3. **Segundo conductor:** si el ciclo supuesto de Bogotá–Cali supera 8 h de recorrido, la Res. 315/2013 art. 6 obliga a dos conductores por vehículo; eso cambia la fórmula (§3.3 de su spec). Decidir el tiempo de recorrido (supuesto) y cómo entra este factor.
4. **Capacidad por clase:** elegir supuestos dentro del rango del Decreto 171/2001 (o derivar de los datos); BUS y BUSETA comparten grupo y tope abierto.
5. **Tope de 10 h (Decreto 1393/1970):** incluir o no, solo tras cerrar el `TODO(cita)` 4.
6. Si va a registro de cacería lo señalado en §6 (puntos 1 y 2 son errores de una fuente oficial, no de IA).
