# MEMORIA — estado del Trabajo 3 (≤ 150 líneas)

## Estado
- Spec v0.6. `main` protegida (ruleset `proteger-main`: PR + Code Owners + check `pruebas`; Daniel fusiona). Ramas `dev/*`.
- Blog publicado en GitHub Pages: https://danielgonzalez2709.github.io/Trabajo3_Redes_Neuronales/ (esqueleto).
- DA-1 (infraestructura) en `main` (PR #1): `src/comun/`, `run.py` con 17 subcomandos, blog, serie sintética, CI.
- DA-2/DA-3/DA-4 terminados el mar 24 (PR #2): series reales de M1 en `data/processed/m1/` (6 series, 2021-01-01..2023-12-31),
  detalle por tipo de despacho y clase de vehículo, marcas de anómalos, ficha/calidad/diccionario en `results/data/m1/eda/`.
  Revisados por revisor-spec (APROBADO), auditor-fugas (sin fuga activa) y revisor-calidad (correcciones aplicadas).
  `run.py m1-datos` regenera todo desde `data/raw/m1/` (no versionado; se reconstruye con `scripts/descargar_m1.py`).
- DA-5 (app) en `main` (PR #3) y publicada en https://trabajo3-redes-neuronales.vercel.app/ (Vercel, cuenta
  danielgonzalez2709, Root Directory = `app`; producción desde `main`, vistas previas por rama): Next.js 16.4.6 estático,
  4 páginas con datos de juguete, ONNX de juguete con onnxruntime-web servido desde la app, contratos en
  `app/lib/contratos.ts` (núcleo §5.4, §5.6, §5.8, v0.6).
- JJ-1 (datos de M3) terminado en `dev/juanjose` el mié 25, pendiente de PR: `run.py m3-datos` construye
  `data/processed/m3/{destinos,usuarios,interacciones}.parquet` y `results/data/m3/eda/{ficha,calidad,diccionario}`
  desde `data/raw/m3/` (Kaggle `amanmehra23/travel-recommendation-dataset`, descarga manual del 25-nov; no versionado).
  999 usuarios, 1 000 destinos (5 lugares), 1 998 interacciones (999 reseñas + 999 historial), densidad 0,20 %.
  Revisado por revisor-spec y revisor-calidad (aprobados en la 2.ª vuelta) y cazador-alucinaciones (0 afirmaciones
  incorrectas vigentes). Investigación: `docs/investigacion/JJ-1_fuentes_m3.md`. Rótulo de fecha: «creación de la versión 1 en Kaggle (2024-01-23)».
- JJ-2 (descriptivo de M3 + caso de uso) terminado en `dev/juanjose` el jue 26, pendiente de PR junto con JJ-1: `run.py m3-eda --config configs/m3/eda.yaml` escribe en `results/data/m3/eda/` las tablas de actividad, concentración, calificaciones, coincidencia preferencia–tipo, pruebas e `hipotesis.json` (9 hipótesis: H-M3-1 y H-M3-4 no concluyentes, H-M3-2/3/5/6 refutadas, H-M3-7/8/9 pendientes para JJ-10); `run.py figures` genera 4 figuras en `blog/docs/figures/m3/` (cola larga, Lorenz, preferencias × tipo, calificaciones); blog 07 con caso de uso y las 7 subsecciones. Las interacciones se parecen a un reparto uniforme al azar (sin cola larga más allá del azar). Revisado por revisor-spec (aprobado), verificador-matematico (aprobado en la 2.ª vuelta), revisor-calidad (2 vueltas; el último bloqueante lo corrigió la sesión principal) y cazador-alucinaciones.
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
- Serie sintética: códigos ficticios del departamento `00`. JSON de juguete de la app: en DA-5.
- M3 [DECIDIDO, Juan José, 25-nov; `docs/spec/partes/juanjose.md` §3.1]: interacción = unión de Reviews y UserHistory
  como implícita (no comparten pares); destino = los 1 000 `DestinationID`, con `lugar` (5 lugares) para el análisis
  complementario; partición por usuario (JJ-3; `VisitDate` solo descriptiva: 3 valores ligados al número de fila y
  posteriores a la creación de la versión 1 en Kaggle, 2024-01-23); datos generados según la fuente («generated for educational and research purposes»);
  licencia MIT del campo formal con contradicción documentada; `Name`, `Email` y `ReviewText` no pasan a procesados ni a
  resultados.
- [PROPUESTO por el analista, pendiente de Juan José] umbral de actividad pocas ≤ 2 / muchas ≥ 3; efectos mínimos y criterio de
  veredicto en `configs/m3/eda.yaml` (convención nuestra); emparejamiento léxico preferencia→tipo (Beaches→Beach, etc.); K = 5 por
  defecto y K ∈ {1, 3, 5, 10}.

## Avisos para el equipo
- Windows: clonar en una ruta corta (p. ej. `C:\proy\`); en rutas profundas `pip install` falla por el límite de 260 caracteres.
- Usar siempre `.venv\Scripts\python` (el `python` del PATH puede ser 3.13).
- M1 (Camila, Andrés): `sin_registro` vale 0 pero no es demanda (enmascarar); `anomalo` nunca como entrada; salto del tránsito
  en 11001-15759 desde nov-2022; 2021 muy por debajo de 2022–2023. Ver `docs/investigacion/DA-3_auditoria_fugas.md`.
- M3: para que la CI pase, el PR de JJ-1 debe incluir `configs/m3/datos.yaml`, `docs/investigacion/JJ-1_kaggle_metadata.json`
  y `tests/fixtures/m3/` (las pruebas los leen).

## Pendientes
1. Hora de la entrega y fecha de la sustentación.
2. GPU para las 30 semillas de M2.
3. Daniel: DA-11 (notebook 00), DA-6/DA-7/DA-8 cuando lleguen las exportaciones reales (sáb 28), grabación del video.
4. Juan José: PR de JJ-1 + JJ-2 (incluir `results/data/m3/eda/*` y `blog/docs/figures/m3/*`, que la CI necesita); confirmar las
   columnas de `interacciones.parquet` frente a §5.7 (`fecha_visita`, `id_origen`, `origen`) y, si se confirman, PR dedicado al
   núcleo; confirmar umbral, efectos mínimos y criterio de `en_el_limite` de JJ-2; en JJ-9 verificar Bergsma (2013) y Romano et al.
   (2006) antes de citarlos; JJ-3, con una prueba que compare la partición real con `actividad_usuarios.json` → `particion_d3`.

## Cacería
- Hallazgos confirmados: 0 / meta ≥ 5 (≥ 3 categorías, ≥ 1 por módulo). Candidatos: H-01 (Código, común: la marca
  `\bibliografia` del blog guardada con un backspace por el agente de DA-1b; evidencia y pruebas listas); 2 candidatos de M3 (JJ-1b, sin número,
  Datos del mundo real): «las tres licencias piden citar la fuente» (orquestador Opus + implementador Sonnet) y «Preferences
  y Type no comparten vocabulario» (implementador Sonnet); 3 candidatos de M3 de JJ-2 (sin número): método de los p e IC mal descrito en el blog (redactor Sonnet,
  Matemáticas); regla de veredicto escrita distinta de la implementada (analista Sonnet, Código, menor); «no son umbrales de la
  literatura» (redactor Sonnet, Conceptos, condicionado a fuente primaria); evidencia en `alucinaciones/evidencias/JJ-2/`; ver
  `alucinaciones/registro.md`.
- Las inconsistencias del diccionario de M1 son hallazgos de datos para el blog, no alucinaciones, salvo que una IA haya
  afirmado lo contrario con prompt literal guardado.

## Bitácora (más reciente arriba)
- 2026-11-26 · Juan José · JJ-2 ✅: descriptivo de M3 (9 hipótesis, 4 figuras, blog 07 con caso de uso); corrección del rótulo
  de fecha de JJ-1; 3 candidatos a la cacería.
- 2026-11-25 · Juan José · JJ-1 ✅ (fases A y B): inventario y fuente de M3 verificados, datos procesados de M3,
  ficha/calidad/diccionario, D1–D7 en `juanjose.md` §3.1; 2 candidatos a la cacería.
- 2026-11-24 · Daniel · PR #3 fusionado; app publicada en Vercel (DA-5 ✅); URL en README, blog y guion.
- 2026-11-24 · Daniel · DA-5 app con contratos (Spec v0.6) y PR #3; blog 01/03/11/13 y guion del video adelantados; H-01.
- 2026-11-24 · Daniel · DA-2/DA-3/DA-4 terminados (series reales de M1) y en PR #2; Spec v0.3–v0.5 (periodo, tránsito,
  mayo-2021, reglas contra fuga); Pages activo; check `pruebas` obligatorio en `main`.
- 2026-11-24 · Daniel · DA-1 fusionado en `main` (PR #1); Spec v0.2.
- 2026-11-23 · Daniel · Spec v0.1, PLAN, agentes y plantillas del Trabajo 3.
