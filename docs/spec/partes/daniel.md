# Spec de Daniel — Plataforma, datos crudos de M1, app, blog y video

| | |
|---|---|
| Responsable | **Daniel** (también revisa y fusiona todos los PR a `main`) |
| Rama | `dev/daniel` |
| Archivos propios | `src/comun/`, `run.py`, `requirements.txt`, `README.md`, `.github/`, `configs/m1/datos.yaml`, `src/m1_demanda/datos.py`, `data/processed/m1/`, `data/sintetico/`, `data/fuentes.md` (sección M1), `src/viz/estilo.py`, `app/`, `blog/` (infraestructura y secciones de introducción, app, uso de IA y reproducibilidad), `video/`, `notebooks/00_sustentacion.py`, `notebooks/01_m1_datos.py` (secciones 1–2 de la plantilla) |
| Lee del núcleo | Todo. **Anexo:** M1 «Datos» y tareas 2; Aplicación web; Entregables 1 (uso de IA, enlaces), 2, 3, 4 y 5 |
| Ruta crítica | Sí: DA-1 (mar 24, mediodía) desbloquea a todos y DA-3 (mié 25, 2 p. m.) desbloquea a Camila y Andrés |

## 1. Lo que pide el enunciado (de lo mío)
- M1 «Datos»: conjunto de la Superintendencia de Transporte en datos.gov.co; municipios con **DIVIPOLA del DANE citado de la
  fuente oficial**; número de registros y variables, periodo, rutas analizadas; significado de las variables **del diccionario
  del conjunto**; inconsistencias diccionario vs. datos documentadas.
- M1 tarea 2: variable objetivo (pasajeros por ruta y día), cómo se agregan los registros, días sin registro, anómalos (p. ej.
  despachos con cero pasajeros).
- Aplicación web publicada con los tres módulos, enlaces al reporte, al video promocional y a los videos individuales, que use
  los modelos guardados sin reentrenar y se levante con un solo comando.
- Repositorio reproducible (Entregable 2) y todo corriendo en vivo (Entregable 3).
- Reporte publicado como blog con enlaces al repo, la app y el video; sección de uso de IA.
- Video promocional de 2 a 3 minutos.

## 2. Consumo / Entrego
| Entrego | A | Cuándo |
|---|---|---|
| DA-1: repo, `src/comun/`, CLI, CI, blog y notebooks vacíos, contratos §5 congelados, serie sintética §5.11 | todos | **mar 24, mediodía** |
| DA-3: `demanda_diaria.parquet`, `rutas.yaml`, `resumen_datos.json` (núcleo §5.1) | Camila, Andrés | **mié 25, 2 p. m.** |
| DA-4: secciones 1–2 de la plantilla de análisis descriptivo de M1 (`ficha.json`, calidad) | Camila (sigue con 3–7) | mié 25, noche |
| App publicada con los tres módulos | todos, profesor | lun 30 |
| Blog publicado | profesor | lun 30 |

| Consumo | De | Cuándo |
|---|---|---|
| Parámetros operativos y `dimensionar()` | Camila | jue 26 (juguete) / sáb 28 (final) |
| Pronósticos con cuantiles por ruta | Andrés | sáb 28, mediodía |
| ONNX + `meta.json` de M2 | José | sáb 28, noche |
| Exportación de M3 | Juan José | sáb 28, noche |
| Secciones del blog de todos | todos | dom 29, 8 p. m. |

## 3. Especificación

### 3.1 Infraestructura (DA-1) [PROPUESTO]
- Portar del Trabajo 2: `config.py`, `cli.py`, `seeds.py`, `results.py`, `torch_utils.py`, `notebooks.py` y sus pruebas;
  `test_no_network.py`; `blog/hooks/reporte.py` + `apa.csl`; `ci.yml`, `blog.yml`; plantilla de PR; CODEOWNERS.
- Nuevo: `src/comun/eda.py` con la plantilla común de análisis descriptivo (núcleo §5.12): `escribir_ficha()`,
  `tabla_calidad()`, `escribir_hipotesis()` + validación de esquema y su prueba.
- `run.py` con los subcomandos de §4.1 (los de cada módulo quedan como esqueleto que el dueño completa).
- Serie sintética de M1 (§5.11). Los JSON de juguete para la app (M1, M2 y M3) se hacen en DA-5, junto con el esqueleto de la app.

### 3.2 Datos de M1 (DA-2, DA-3) [PROPUESTO]
- Identificar el conjunto exacto en datos.gov.co (identificador, URL, diccionario) [VERIFICAR con `investigador-fuentes`].
- Descarga: si es grande, agregación en el servidor con la API Socrata (SoQL `group by` ruta y fecha) y además una muestra cruda
  para documentar variables; registrar URL de la consulta, fecha, SHA-256 y tamaño en `data/fuentes.md`.
- DIVIPOLA: tabla oficial del DANE guardada en `data/processed/m1/divipola.csv` con su cita; validar que todo código de
  origen/destino exista en ella (los que no, se documentan como inconsistencia).
- **Selección de rutas [DECIDIDO, Daniel, 24-nov]:** 3 pares ida/regreso = 6 series: **Bogotá D.C. (11001) ↔ Santiago de
  Cali (76001)** (corredor largo, el de mayor volumen), **Bogotá D.C. (11001) ↔ Sogamoso (15759)** (corredor medio) y **Pasto
  (52001) ↔ Ipiales (52356)** (regional y de frontera, fuera de Bogotá). Criterio: ranking de pares por el mínimo de los dos
  sentidos en una muestra de 36 miércoles (uno por mes, 2021–2023), con 35–36 de 36 días con registros en ambos sentidos
  (`scripts/descargar_m1.py ranking`, `data/fuentes.md`). Periodo 2021–2023 (núcleo §5.1, v0.3); la temporada alta de prueba
  es el fin de año de 2023. Camila puede proponer cambios por PR.
- Agregación: suma de pasajeros y despachos por `(ruta_id, fecha)`; días sin registro → fila con `sin_registro = true` (regla
  de imputación documentada); anómalos → regla explícita (p. ej. despachos > 0 con pasajeros = 0, valores fuera de rango) y
  `anomalo = true`; nada se borra en silencio.

### 3.3 App (DA-5 a DA-8) [PROPUESTO]
Next.js estático en Vercel, como el Trabajo 2. Página de inicio con enlaces a blog, video promocional y videos individuales.
- **Demanda:** selector de ruta; pronóstico a 30 días con banda del cuantil; flota y conductores por día; controles de
  ocupación objetivo y cuantil usado (mínimo); `dimensionar()` en TS con paridad contra Python.
- **Conducción:** subir imagen → ONNX Runtime Web → probabilidad por clase, clase asignada, decisión de alerta con umbral
  ajustable y mapa CAM sobre la imagen (núcleo §3 y §5.6). Imágenes de ejemplo precargadas.
- **Recomendación:** usuario existente (historial + top-K) o perfil nuevo con **lista de preferencias** seleccionables → top-K.
- Pruebas de paridad en CI; la app nunca reentrena.

### 3.4 Blog (DA-9) y video (DA-10)
- MkDocs Material + hook del Trabajo 2. Estructura [PROPUESTO]: 00 resumen · 01 introducción y caso de negocio ·
  02 fundamentación común (Juan José) · 03–05 M1 (Daniel/Camila: datos y descriptivo; Andrés: redes; Camila: operación) ·
  06 M2 (José) · 07 M3 (Juan José) · 08 app · 09 discusión · 10 ética (Camila) · 11 uso de IA (Daniel) · 12 cacería (Andrés) ·
  13 reproducibilidad · referencias.
- Video: Remotion + clips de los 5; guion el jue 26, grabación sáb 28, publicado en YouTube (no listado) el lun 30.

## 4. Tareas
| ID | Tarea | Fecha | Agente (modelo) | + Verificador | Aceptación | Estado |
|---|---|---|---|---|---|---|
| DA-0 | Spec v0.1 aprobado, push inicial, ruleset de `main`, ramas `dev/*` | lun 23 | — | — | Las 5 ramas existen; `main` protegida | ✅ |
| DA-1 | Infraestructura (§3.1) | mar 24, 12 m. | implementador (Sonnet) + scaffolding | auditor-reproducibilidad (Haiku) | `pytest` y CI en verde; `python run.py --help` lista los subcomandos | ✅ |
| DA-2 | Descarga del crudo de M1 y DIVIPOLA | mar 24 | curador-datos (Sonnet) + investigador-fuentes (Sonnet) | cazador-alucinaciones (Opus) | `data/fuentes.md` completo; conteos medidos; diccionario citado | ✅ |
| DA-3 | Construcción de las series (§3.2) | **mié 25, 2 p. m.** | implementador-experto (Opus) 🧠 | auditor-fugas (Opus) | Esquema §5.1; sin huecos de fecha; reglas de anómalos con prueba | ✅ |
| DA-4 | Plantilla común secciones 1–2 para M1 | mié 25 | curador-datos (Sonnet) | revisor-spec (Sonnet) | `ficha.json` válido; inconsistencias diccionario vs. datos listadas | ✅ |
| DA-5 | Esqueleto de la app + Vercel con JSON de juguete de M1, M2 y M3 en el formato de §5.4, §5.6 y §5.8 | jue 26 | implementador-web (Sonnet) | revisor-calidad (Haiku) | Despliegue en Vercel; `npm test` y `npm run build` en verde | ✅ (https://trabajo3-redes-neuronales.vercel.app/) |
| DA-6 | Página de demanda con `dimensionar()` en TS | sáb 28 | implementador-web (Sonnet) | verificador-matematico (Opus) | Paridad TS vs. Python | ⬜ |
| DA-7 | Página de conducción (ONNX + CAM + umbral) | sáb 28–dom 29 | implementador-experto (Opus) 🧠 | verificador-matematico (Opus) | Paridad de probabilidades y mapa con los casos de `meta.json` | ⬜ |
| DA-8 | Página de recomendación (existente + perfil nuevo) | dom 29 | implementador-web (Sonnet) | revisor-spec (Sonnet) | Paridad del top-K | ⬜ |
| DA-9 | Blog: integración, secciones propias, publicación | lun 30 | redactor-tecnico (Sonnet) | auditor-entregables (Haiku) | `mkdocs build --strict` sin errores; sin figuras huérfanas | ⬜ |
| DA-10 | Video promocional | jue 26–lun 30 | implementador-web (Sonnet) | — | 2–3 min, publicado, enlazado en app y blog | 🟨 (guion listo) |
| DA-11 | Notebook `00_sustentacion` (una celda por módulo) | dom 29 | implementador (Sonnet) | tutor-sustentacion (Sonnet) | Corre completo en < 2 min por módulo | ⬜ |
| DA-12 | Sección uso de IA (prompts principales e impacto) | dom 29 | redactor-tecnico (Sonnet) | — | Prompts literales enlazados a `alucinaciones/prompts/` | ⬜ |

## 5. Puntos calientes de alucinación
- Identificador, columnas y significado de las variables del conjunto de datos.gov.co (una IA los inventa con facilidad).
- Códigos DIVIPOLA de municipios (5 dígitos: departamento + municipio); nombres parecidos entre departamentos.
- APIs de ONNX Runtime Web y de exportación de PyTorch a ONNX (opciones cambiadas entre versiones).
- Configuración de Vercel y de Next.js `output: "export"`.

## 6. Definición de terminado
Mis tareas ✅ en `PLAN.md`; app y blog publicados con enlaces cruzados; el clon limpio de Juan José pasa; ≥ 1 hallazgo propio;
video individual grabado.
