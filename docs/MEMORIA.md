# MEMORIA — estado del Trabajo 3 (≤ 150 líneas)

## Estado
- Spec v0.7. `main` protegida (ruleset `proteger-main`: PR + Code Owners + check `pruebas`; Daniel fusiona). Ramas `dev/*`.
- Blog publicado en GitHub Pages: https://danielgonzalez2709.github.io/Trabajo3_Redes_Neuronales/ (esqueleto).
- Daniel en `main`: DA-1 infraestructura (PR #1); DA-2/3/4 series reales de M1 en `data/processed/m1/` (6 series,
  2021–2023, marcas de anómalos; `run.py m1-datos` desde `data/raw/m1/`, PR #2); DA-5 app en https://trabajo3-redes-neuronales.vercel.app/
  (Vercel, Root Directory `app`, producción desde `main`; contratos en `app/lib/contratos.ts`); DA-5c/DA-7/DA-11 (PR #5).
- JJ-1 (datos de M3) en `main` (PR #6, 27-nov): `run.py m3-datos` construye `data/processed/m3/*.parquet` y
  `results/data/m3/eda/` desde `data/raw/m3/` (Kaggle `amanmehra23/travel-recommendation-dataset`, no versionado). 999 usuarios,
  1 000 destinos (5 lugares), 1 998 interacciones (999 reseñas + 999 historial), densidad 0,20 %. Rótulo de fecha: «creación de
  la versión 1 en Kaggle (2024-01-23)». Investigación: `docs/investigacion/JJ-1_fuentes_m3.md`.
- JJ-2 (descriptivo de M3 + caso de uso) en `main` (PR #6, 27-nov): `run.py m3-eda` e `hipotesis.json` (9 hipótesis:
  H-M3-1 y H-M3-4 no concluyentes, H-M3-2/3/5/6 refutadas, H-M3-7/8/9 pendientes para JJ-10); `run.py figures` genera 4 figuras
  en `blog/docs/figures/m3/`; blog 07 con caso de uso. Las interacciones se parecen a un reparto uniforme al azar.
- JJ-3 (partición sin fuga de M3) en `main` (PR #6, 27-nov): `split` ∈ {train, validacion, prueba} en `interacciones.parquet`
  (semilla 2026; huella `b35cd70b…58e8b8` en `results/data/m3/particion/resumen.json`). 1 066 / 326 / 606; 858 usuarios con
  interacciones, 141 no evaluables. `src/m3_recomendacion/particion.py`; `tests/test_fuga_m3.py` (53 pruebas; SIN FUGA).
- JJ-4 (referencias + @K de M3) en PR #9 (con JJ-5): `run.py m3-hpo` (Optuna TPE, 20 ensayos, NDCG@5 en validación;
  mejor ensayo 19: f = 4, λ ≈ 0,0021, α ≈ 1,485, 9 barridos; 0 degenerados) y `run.py m3 --config configs/m3/base.yaml`
  (popularidad, MF-ALS y aleatorio; 30 semillas). Demo `configs/m3/demo.yaml` (< 2 min; `results/data/m3_demo/`).
  Recall@10: popularidad 0,0069, MF 0,0105, aleatorio 0,0096, esperado 0,0100 (diferencias menores que el error estándar de 606 usuarios);
  cobertura@10: 0,025 / 0,101 / 0,997. Blog 07: «Métricas de evaluación» y «Modelos de referencia».
- JJ-5 (red de dos torres de M3) en PR #9 (con JJ-4): `m3-hpo` busca MF y red (20 ensayos cada una);
  red: mejor ensayo 18, NDCG@5 de validación 0,0067; d = 32, MLP 64 (usuario) y 16 (destino), 2 negativos, BCE, lr ≈ 7,4e-4,
  weight decay ≈ 3,6e-4, dropout ≈ 0,25 (copiados a `base.yaml`). Red en prueba: NDCG@5 0,0026 ± 0,0010, Recall@10 0,0098 ± 0,0034
  (azar 0,0030 y 0,0100), cobertura@10 0,028, 52 192 parámetros; al nivel del azar. Archivos: `src/m3_recomendacion/{red,contenido}.py`,
  `tests/test_red_m3.py`; 4 figuras comunes (`red_arquitectura`, `red_curvas`, `busqueda_m3`, `cajas_m3`); blog 07 «Red neuronal de dos torres».
  Revisado por verificador-matematico (4.ª vuelta), auditor-fugas (SIN FUGA; 20/20 mutantes muertos), revisor-spec y revisor-calidad.
- CA-1..CA-4 ✅ y CA-5 🟨 de M1 en `main` (PR #7, 28-nov). CA-3 (flota y conductores): `run.py m1-operacion` escribe
  `results/data/m1/operacion/` (incluida `nomina_semanal.csv`); m_r por ruta (por corredor como sensibilidad,
  `calibracion.multiplicador`). Revisado por revisor-spec, verificador-matematico y revisor-calidad (2.ª vuelta), más R1/R2/R8/R10.
- Adelantado: blog 01, 03 (ficha y calidad), 11 (metodología de IA) y 13; guion del video (`video/guion.md`, 2:30).
- Entrega: mar 1-dic-2026 (hora por confirmar).

## Decisiones vigentes
- Git: solo Daniel fusiona a `main` por PR; cada quien en `dev/<nombre>`; push permitido a otras ramas, nunca a `main`.
- App en Vercel (Next.js estático). Blog en MkDocs Material + hook del Trabajo 2.
- Plantilla común de análisis descriptivo para los 3 módulos (núcleo §5.12); veredicto `pendiente` hasta modelar.
- M1: conjunto `eh75-8ah6` (Supertransporte); DIVIPOLA DANE `gdxc-w37w` (corte 30-dic-2024).
- M1: rutas 11001↔76001 (Bogotá–Cali), 11001↔15759 (Bogotá–Sogamoso), 52001↔52356 (Pasto–Ipiales); periodo 2021–2023
  (2024 casi vacío y 2020 sin datos en la fuente); `pasajeros` = origen + tránsito; flota con despachos de ORIGEN.
- M1: mayo de 2021 casi vacío → serie completa con marcas; los modelos entrenan desde el 2021-06-01 (`datos.inicio_entrenamiento`).
- M1: reglas contra fuga del arnés (núcleo §5.3): lista blanca de columnas; test sin excluir anómalos; ventanas desde
  2021-06-01; rejilla de orígenes anclada al 2023-12-01 para cubrir el fin de año; composición por clase solo con train.
- M1 negocio (CA-6) [DECIDIDO, Camila, 27-nov]: se implementa con la mejor red de Andrés (AN-5), no con las referencias;
  «próximos 30 días» = origen 2023-12-01; temporada alta = días `fin_de_anio` del horizonte frente a una semana normal sin
  festivos, puentes ni vacaciones escolares. Opciones de flota [DECIDIDO, 27-nov, tras CA-6a y su verificación]: propia =
  propia o vinculada hasta la capacidad máxima fijada (≤ mínima + 20 %, Dec. 1079 art. 2.2.1.4.7.2); arrendada = contrato con
  servicio especial en alta demanda (art. 2.2.1.6.3.5 mod. Dec. 1048/2026; Res. 264/2020); convenio = figura estable (≤ 2 años,
  ruta completa). Sin costos en pesos con fuente oficial: comparación cualitativa.
- M1 calendario [DECIDIDO, Camila, 27-nov]: `fin_de_anio` = 10-dic a 15-ene (Res. 264/2020 MinTransporte, art. 8); antes
  supuesto 15-dic. Cambia `calendario.parquet` (aviso a Andrés).
- Serie sintética: códigos ficticios del departamento `00`. JSON de juguete de la app: en DA-5.
- M3 [DECIDIDO, Juan José, 25-nov; `docs/spec/partes/juanjose.md` §3.1]: interacción = unión de Reviews y UserHistory
  como implícita (no comparten pares); destino = los 1 000 `DestinationID`, con `lugar` (5 lugares) para el análisis
  complementario; partición por usuario (JJ-3; `VisitDate` solo descriptiva: 3 valores ligados al número de fila, 2 de ellos
  (666 de 999 filas) posteriores a la creación de la versión 1 en Kaggle, 2024-01-23); datos generados según la fuente («generated for educational and research purposes»);
  licencia MIT del campo formal con contradicción documentada; `Name`, `Email` y `ReviewText` no pasan a procesados ni a
  resultados.
- M3 [DECIDIDO, Juan José, 26-nov; `juanjose.md` §3.1, D8–D10]: una sola partición en la columna `split` del parquet para
  todos los modelos, con su huella en la `evidencia`; HPO y parada temprana con validación, modelos finales solo con train y
  una evaluación en prueba; toda estadística de interacciones solo con train (`popularidad_train`); candidatos = catálogo
  menos historial conocido (prueba: train ∪ validación; validación: train); clave de una interacción = `(origen, id_origen)`.
- M3 [DECIDIDO, Juan José, 27-nov; `juanjose.md` §3.2–§3.3, D11–D14]: referencias = popularidad de train (empates al azar), MF
  implícita por ALS (Hu, Koren y Volinsky, 2008 [VERIFICAR en JJ-9]) y aleatorio con esperado analítico; Recall@K = acierto@K y
  Precision@K = acierto@K/K (1 relevante por usuario); cobertura /1 000; Gini y HHI de exposiciones; acierto por lugar solo
  K ∈ {1, 3} con línea base; búsqueda 20 ensayos NDCG@5 en validación; 30 semillas. λ ≥ (1 + α)σ_max(P_train) ⇔ X = Y = 0 es el
  único mínimo (tope λ ≤ 5,0 y guarda de degeneración de tres condiciones).
- M3 [DECIDIDO, Juan José, 27-nov; `juanjose.md` §3.2, D15–D19]: red de dos torres (usuario: 5 preferencias one-hot + id opcional;
  destino: `tipo` one-hot + id opcional; MLP con ReLU; ids sumados a la salida, índice 0 = «sin id» para perfiles nuevos y destinos
  fríos, «dropout de id»); ninguna popularidad en la red; pérdida `bce` o `bpr` (la búsqueda eligió BCE); negativos uniformes sobre
  catálogo − train; d ∈ {4, 8, 16, 32}; parada temprana por NDCG@5 de validación; la red lee los bloques
  `modelo/perdida/entrenamiento/regularizacion` y en `_presupuesto` «config» gana a `ejecutar_en_experimento`; guarda
  `AJUSTES_SIN_PRUEBA`; `contenido.py` solo lee destinos y usuarios.
- [PROPUESTO por el analista, pendiente de Juan José] umbral de actividad pocas ≤ 2 / muchas ≥ 3; efectos mínimos y criterio de
  veredicto en `configs/m3/eda.yaml` (convención nuestra); emparejamiento léxico preferencia→tipo (Beaches→Beach, etc.); K = 5 por
  defecto y K ∈ {1, 3, 5, 10}; diagnósticos de `resumen.json` (destinos fríos, coincidencia de lugar con su esperado por azar),
  guardas `AJUSTES_SOLO_TRAIN` para JJ-4/JJ-5 y nombre `particion.semilla` = 2026.

## Avisos para el equipo
- Windows: clonar en una ruta corta (p. ej. `C:\proy\`); en rutas profundas `pip install` falla por el límite de 260 caracteres.
- Usar siempre `.venv\Scripts\python` (el `python` del PATH puede ser 3.13).
- M1 (Camila, Andrés): `sin_registro` vale 0 pero no es demanda (enmascarar); `anomalo` nunca como entrada; salto del tránsito
  en 11001-15759 desde nov-2022; 2021 muy por debajo de 2022–2023. Ver `docs/investigacion/DA-3_auditoria_fugas.md`.
- M1 operación (Camila → Daniel, 27-nov): `dimensionar()` de Python (CA-3d) usa ρ_r = min(1, ρ·m_r) con m_r por ruta
  calibrado en train, tripulación k = max(k_norma, ⌈t/J_ef⌉), conductores por piernas y nómina semanal N\*; los parámetros
  por ruta llevan `multiplicador_ocupacion`. `app/lib/dimensionar.ts` sigue con la fórmula de juguete de DA-5: los casos de
  paridad (CA-8) fallarán hasta que DA-6 la actualice.
- M1 calendario (Camila → Andrés, 27-nov): `fin_de_anio` empieza el 10-dic (Res. 264/2020); nuevo SHA-256 de
  `calendario.parquet` `c29dc412…ae2fb9` (antes `7478d74a…baecec6`). Reentrenar o reevaluar lo que lo use.
- M3: la demo en vivo con otra semilla debe redirigir las salidas a `results/data/m3_demo/` (orden en `configs/m3/datos.yaml`);
  sin redirigir se pisan archivos versionados.
- M3/JJ-5: la red se agrega con una entrada en `referencias.MODELOS`, una en `hpo.BUSQUEDAS` y un bloque `<nombre>:` en la config,
  sin tocar `experimento.py`; su `diagnosticos()` debe traer `degenerado`; el bloque `busqueda:` es de la MF y la red tiene el suyo.
- M3, PR de JJ-4 y JJ-5 (juntos): incluir `results/data/m3/*` (incl. `curvas/`, `arquitectura/`, `semillas/red_seed*.json`),
  `models/m3/*` (incl. `red.{pt,json}`) y las 4 figuras nuevas; las pruebas y `run.py figures` los leen. `base.yaml` usa
  `hiperparametros_desde: config` (red y MF = mejor ensayo; las claves en vivo cambian el modelo; `summary.json` reporta los 20
  ensayos mientras sea el mejor ensayo; si se repite `m3-hpo`, volver a copiarlo: lo vigilan pruebas). Máquina de Juan José:
  ~0,8 GB libres; un solo proceso con torch a la vez.

## Pendientes
1. Hora de la entrega y fecha de la sustentación.
2. GPU para las 30 semillas de M2.
3. Daniel: DA-11 (notebook 00), DA-6/DA-7/DA-8 cuando lleguen las exportaciones reales (sáb 28), grabación del video.
4. Juan José:
   - PR de JJ-4 + JJ-5 (ver Avisos; JJ-1 a JJ-3 ya en `main`, PR #6). Confirmar columnas de `interacciones.parquet` frente a §5.7 (`fecha_visita`, `id_origen`,
     `origen`); si se confirman, PR dedicado al núcleo.
   - Decidir lo [PROPUESTO]: JJ-2 (umbral, efectos mínimos, `en_el_limite`); JJ-3 (diagnósticos, guardas, nombre de la semilla);
     JJ-4 (rangos, tope λ = 5,0, tolerancia 1e-8, semilla del sampler 2026, `n_parametros` = 1 000 conteos, respaldo MF 16/0,1/10/10,
     grupo vacío `{"n_usuarios": 0}`). Lo [PROPUESTO] de JJ-5 ya es [DECIDIDO, Juan José, 27-nov].
   - Alcance de D10 sobre los 141 usuarios sin interacciones (sin verdad de terreno: solo ejemplos; los nuevos de la pregunta de
     negocio 1 se simulan en JJ-6 y deben reentrenar sin sus interacciones: poner índice 0 no oculta el historial, auditor-fugas).
   - JJ-4/JJ-5: registrar cada ajuste en `AJUSTES_SOLO_TRAIN` y copiar la huella a `evidencia`; reportar el acierto por lugar
     frente al azar (K = 3: red 0,2308 frente a 0,4883). JJ-4: guarda de auditor-fugas en `test_fuga_m3.py` y `Aleatorio` en
     `AJUSTES_SOLO_TRAIN`; menores N1 (precedencia de `ejecutar_en_experimento` frente a `hiperparametros_desde`), N3
     (`diagnosticos["degenerado"]` obligatorio), N5, N6–N8; el mejor λ quedó cerca del límite inferior (1e-3).
   - JJ-5, no bloqueante (Juan José: no se aplican por ahora): R-1 a R-19 del revisor-calidad, 2.ª vuelta (`juanjose.md` §3.2).
   - JJ-9: verificar Bergsma (2013), Romano et al. (2006), Hu et al. (2008; DOI 10.1109/ICDM.2008.22 según el verificador),
     Rendle et al. (2009; BPR, `TODO(cita)`) y la cifra de páginas; `torch.optim.Adam` a la bibliografía si JJ-8 la cita.

## Cacería
- Hallazgos confirmados: 0 / meta ≥ 5 (≥ 3 categorías, ≥ 1 por módulo). Candidatos: H-01 (Código, común: la marca
  `\bibliografia` del blog guardada con un backspace por el agente de DA-1b; evidencia y pruebas listas).
- Candidatos de M3 (sin número; evidencia en `alucinaciones/evidencias/JJ-<n>/`):
  - JJ-1 (Datos del mundo real): «las tres licencias piden citar la fuente»; «Preferences y Type no comparten vocabulario».
  - JJ-2 (3): método de los p e IC mal descrito en el blog (Matemáticas); regla de veredicto distinta de la implementada (Código,
    menor); «no son umbrales de la literatura» (Conceptos, condicionado a fuente primaria).
  - JJ-3 (2): «acierto por lugar trivial» (Matemáticas; premisa del prompt humano convertida en hecho por orquestador e
    implementador-experto Opus; 204 observados frente a 198,0 por azar); «los 3 valores de VisitDate son posteriores» (Datos, menor).
  - JJ-4 (3): «la mejor MF era X = Y = 0» (Matemáticas; origen en el prompt del orquestador Opus); «la tolerancia 1e-8 detecta el
    colapso / la cota es suficiente, no necesaria» (Código, menor); afirmaciones numéricas del redactor en la lectura de resultados.
  - JJ-5 (3): «personalización = desviación entre usuarios de s_ui» (Matemáticas; origen en el prompt del orquestador Opus);
    «la fracción es 0 si S es constante / está en [0, 1]» en punto flotante (Código, menor); «los fríos quedan por debajo de los
    destinos con train» (Conceptos, menor).
  - Ver `alucinaciones/registro.md`.
- Las inconsistencias del diccionario de M1 son hallazgos de datos para el blog, no alucinaciones, salvo que una IA haya
  afirmado lo contrario con prompt literal guardado.

## Bitácora (más reciente arriba)
- 2026-11-28 · Daniel · PR #6, #10 y #7 fusionados; conflictos de #9 y #8 resueltos en sus ramas. Revisión de #7 y #8 → arreglos de infraestructura: CI con torchvision de
  CPU (fallaba el #8), `results/**` y `*.csv` byte a byte en `.gitattributes` (huellas SHA-256 en Windows) y `test_no_network`
  ya no reescribe las figuras versionadas. En clones de Windows existentes: `git checkout -- results tests/fixtures`.
- 2026-11-27 · Juan José · JJ-4 ✅ (referencias @K; MF colapsada a X = Y = 0 detectada y corregida; D11–D14) y JJ-5 ✅ (red de
  dos torres, BCE/BPR, 20 ensayos y 30 semillas, al nivel del azar; D15–D19; [PROPUESTO] → [DECIDIDO]); 6 candidatos.
- 2026-11-27 · Camila · CA-1, CA-2, CA-3 (CA-3d/e: tripulación, m_r por ruta, nómina N\*) y CA-4 ✅; CA-5 🟨 (falta arnés AN-1);
  CA-6/CA-6a (horizonte, temporada alta, costos y marco legal) y CA-1c (`fin_de_anio` desde el 10-dic); 2 candidatos.
- 2026-11-23..26 · Spec v0.1–v0.7; Daniel DA-1..DA-5c, DA-7 (CAM) y DA-11 (PR #1–#5); Juan José JJ-1..JJ-3 (PR #6, 27-nov).
  Detalle en `git log` y en la sección Estado.
