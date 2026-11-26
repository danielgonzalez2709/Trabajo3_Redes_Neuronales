# MEMORIA — estado del Trabajo 3 (≤ 150 líneas)

## Estado
- Spec v0.7. `main` protegida (ruleset `proteger-main`: PR + Code Owners + check `pruebas`; Daniel fusiona). Ramas `dev/*`.
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

## Avisos para el equipo
- Windows: clonar en una ruta corta (p. ej. `C:\proy\`); en rutas profundas `pip install` falla por el límite de 260 caracteres.
- Usar siempre `.venv\Scripts\python` (el `python` del PATH puede ser 3.13).
- M1 (Camila, Andrés): `sin_registro` vale 0 pero no es demanda (enmascarar); `anomalo` nunca como entrada; salto del tránsito
  en 11001-15759 desde nov-2022; 2021 muy por debajo de 2022–2023. Ver `docs/investigacion/DA-3_auditoria_fugas.md`.

## Pendientes
1. Hora de la entrega y fecha de la sustentación.
2. GPU para las 30 semillas de M2.
3. Daniel: DA-11 (notebook 00), DA-6/DA-7/DA-8 cuando lleguen las exportaciones reales (sáb 28), grabación del video.

## Cacería
- Hallazgos confirmados: 0 / meta ≥ 5 (≥ 3 categorías, ≥ 1 por módulo). Candidatos: H-01 (Código, común: la marca
  `\bibliografia` del blog guardada con un backspace por el agente de DA-1b; evidencia y pruebas listas).
- Las inconsistencias del diccionario de M1 son hallazgos de datos para el blog, no alucinaciones, salvo que una IA haya
  afirmado lo contrario con prompt literal guardado.

## Bitácora (más reciente arriba)
- 2026-11-26 · Daniel · DA-7 CAM pintado en la app y CAM ≡ Grad-CAM verificado (verificador-matematico: aprobado con
  observaciones, aplicadas); DA-11 esqueleto del notebook 00; borrador del blog 08; condiciones del ONNX real en la spec de José.
- 2026-11-26 · Daniel · DA-5c (aviso de Juan José): juguete como fixture (`app/tests/fixtures/juguete/`), pruebas de lo
  servido válidas para modelos reales, nombres repetidos de M3 como «Nombre (#id)»; Spec v0.7 (§5.7 columnas reales de M3).
- 2026-11-24 · Daniel · PR #3 fusionado; app publicada en Vercel (DA-5 ✅); URL en README, blog y guion.
- 2026-11-24 · Daniel · DA-5 app con contratos (Spec v0.6) y PR #3; blog 01/03/11/13 y guion del video adelantados; H-01.
- 2026-11-24 · Daniel · DA-2/DA-3/DA-4 terminados (series reales de M1) y en PR #2; Spec v0.3–v0.5 (periodo, tránsito,
  mayo-2021, reglas contra fuga); Pages activo; check `pruebas` obligatorio en `main`.
- 2026-11-24 · Daniel · DA-1 fusionado en `main` (PR #1); Spec v0.2.
- 2026-11-23 · Daniel · Spec v0.1, PLAN, agentes y plantillas del Trabajo 3.
