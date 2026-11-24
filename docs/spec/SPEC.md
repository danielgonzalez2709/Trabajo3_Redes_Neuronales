# SPEC (núcleo) — Trabajo 3: Redes neuronales para series de tiempo, imágenes y recomendación

| | |
|---|---|
| Curso | Redes neuronales y algoritmos bioinspirados — UNAL, Facultad de Minas, 2026-02 |
| Versión | **0.5** — 2026-11-24 (§5.3 reglas contra fuga del arnés de M1: lista blanca de columnas, test sin excluir anómalos, ventanas desde el 2021-06-01, rejilla de orígenes anclada al 2023-12-01; §5.4 composición por clase solo con train; §5.1 marcas solo descriptivas y `marcas_anomalos.parquet`; afecta a Andrés y Camila; Daniel, a partir de auditor-fugas) · 0.4 — 2026-11-24 (§5.1: mayo de 2021 se conserva con marcas y los modelos entrenan desde el 2021-06-01 (`datos.inicio_entrenamiento`); la flota usa despachos de ORIGEN; afecta a Camila y Andrés; Daniel) · 0.3 — 2026-11-24 (§5.1: periodo 2021–2023, `pasajeros` incluye origen y tránsito, nueva tabla `demanda_detalle.parquet` por tipo de despacho y clase de vehículo; afecta a Camila y Andrés; Daniel) · 0.2 — 2026-11-24 (DA-1: §5.11 la serie sintética usa picos de temporada como proxy de festivos y códigos del departamento `00`; §5.12 agrega el veredicto `pendiente`; los JSON de juguete de la app pasan a DA-5; Daniel) · 0.1 — 2026-11-23 (borrador inicial a partir del enunciado y de la estructura del Trabajo 2; Daniel) |
| Entrega | **mar 1-dic-2026** (hora por confirmar [VERIFICAR]) |
| Repositorio | https://github.com/danielgonzalez2709/Trabajo3_Redes_Neuronales |

### Cómo se lee este Spec

| Documento | Qué contiene | Quién lo lee |
|---|---|---|
| `docs/spec/SPEC.md` (este) | Reglas, equipo, dependencias, decisiones, estructura, comandos, **contratos**, plantilla común de análisis descriptivo, comparación justa, Git, cacería, hitos | **Todos** los humanos y subagentes |
| `docs/spec/partes/daniel.md` | Plataforma, datos crudos de M1, app, blog, video | Daniel y sus subagentes |
| `docs/spec/partes/camila.md` | M1: análisis descriptivo, calendario, modelos de referencia, operación (flota y conductores), ética | Camila y sus subagentes |
| `docs/spec/partes/andres.md` | M1: redes, pérdidas, origen rodante, valor del pronóstico, cacería | Andrés y sus subagentes |
| `docs/spec/partes/jose.md` | M2: conducción distractiva completo | José y sus subagentes |
| `docs/spec/partes/juanjose.md` | M3: recomendación completo, fundamentación común, bibliografía, clon limpio | Juan José y sus subagentes |
| `docs/spec/PLAN.md` | Tablero global: una línea por tarea, fecha y estado | Todos |
| **Anexo** de este archivo | **Enunciado literal del trabajo** | **Todos**; es el contexto de base de cualquier sesión |

**Regla de oro:** los **contratos (§5) viven solo aquí**. Las specs de cada persona los referencian (`núcleo §5.x`), nunca
los copian. Si alguien necesita cambiar un contrato, abre un PR que modifique este archivo y sube la versión.

Marcas: **[DECIDIDO]** (se cumple), **[PROPUESTO]** (lo decide el dueño; si no dice nada, queda así), **[PENDIENTE]**
(falta decidir), **[VERIFICAR]** (dato que se debe medir o comprobar antes de usarlo).

---

## 0. Reglas (humanos y subagentes)

1. **Cualquier integrante puede cambiar el Spec (núcleo o su spec personal) bajo su criterio**, incluido lo [DECIDIDO]:
   por PR, subiendo la versión, con una línea en el historial de la cabecera (qué, por qué, quién). Si toca un contrato (§5),
   un hito (§11) o algo que otra persona consume, el PR **nombra a los afectados** y se les avisa antes de fusionar.
   El Anexo (enunciado) **no se edita**, salvo para corregir un error de transcripción.
2. **El Spec es la fuente de verdad** después del enunciado. Si el código o un subagente lo contradice, gana el Spec o se cambia el
   Spec explícitamente.
3. Los **subagentes** no cambian el Spec ni resuelven [PENDIENTE]/[PROPUESTO]: **escalan** al humano que los dirige.
4. **Prohibido inventar datos, constantes, normas, significados de variables, códigos DIVIPOLA, referencias o resultados.**
   Si falta algo: `TODO(dato-faltante)` / `TODO(cita)` y se reporta. Un dato inventado es peor que uno faltante.
5. El significado de las variables se cita del **diccionario oficial de cada conjunto** (datos.gov.co, artículo de Data in
   Brief / Mendeley, página de Kaggle), nunca de una IA. Toda norma colombiana se cita desde su **fuente oficial**.
6. Todo prompt enviado a una IA (incluidos los del orquestador a un subagente) se guarda **literal** en
   `alucinaciones/prompts/<ID>.md` **antes** de enviarlo (§9).
7. Toda cifra del blog sale de un archivo de `results/` o `data/processed/` y se regenera con un comando.
8. Los datos sintéticos (§5.11) son solo para desarrollar. Ninguna cifra, figura o conclusión del blog sale de ellos.
9. **Ninguna variable de M1 puede depender de información que no se conozca 30 días antes** (enunciado, M1 tarea 1).

---

## 1. Contexto, equipo y responsables

Una empresa de transporte intermunicipal quiere (M1) pronosticar la demanda por ruta a 30 días y dimensionar flota y
conductores, (M2) detectar conducción distractiva con cámaras y (M3) recomendar destinos de viaje. En cada módulo las redes se
comparan con modelos de referencia bajo una **comparación justa** (§6). Todo se integra en una **app web publicada**.

Pesos (enunciado): reporte 20 %, repositorio 5 %, app 10 %, video promocional 5 %, ejecución y modificación en vivo 10 %,
cacería 15 %, video individual 5 % (individual), sustentación 30 % (individual).

### 1.1 Responsables [PROPUESTO, Daniel, 23-nov]

| Persona | Alcance | Spec | Rama |
|---|---|---|---|
| **Daniel** | Plataforma (E0), **descarga y construcción de las series de M1** (primeras tareas de M1, luego pasa a Camila), app, blog, uso de IA, video promocional, revisión y fusión de PR | `partes/daniel.md` | `dev/daniel` |
| **Camila** | M1: calendario exógeno, normativa y parámetros operativos, análisis descriptivo, modelos de referencia, flota y conductores (negocio 1, 2 y 4), limitaciones; ética (consolida) | `partes/camila.md` | `dev/camila` |
| **Andrés** | M1: origen rodante y métricas, pérdidas de conteo y cuantílica, MLP y red secuencial, búsqueda, 30 semillas, valor del pronóstico (negocio 3), fundamentación de M1; Cacería (consolida) | `partes/andres.md` | `dev/andres` |
| **José** | M2 completo, incluida su fundamentación matemática y la exportación del modelo a la app | `partes/jose.md` | `dev/jose` |
| **Juan José** | M3 completo, fundamentación matemática común, bibliografía APA verificada, clon limpio | `partes/juanjose.md` | `dev/juanjose` |

Integrantes: Edinson **Andrés** Ariza Mendoza, Maria **Camila** Agudelo Espinosa, **Daniel** Gonzalez Henao, **Jose** Miguel
Pulgarin Agudelo, **Juan José** González Morales.

**Obligaciones de todos:** sus secciones del blog con la fundamentación matemática de lo suyo, la parte de ética de su módulo,
≥ 1 hallazgo genuino de la cacería, sus prompts guardados, su video individual y poder explicar **todo** el trabajo
(fichas del `tutor-sustentacion`).

### 1.2 Mapa de dependencias (quién le entrega qué a quién)

```
DA-1 infraestructura + contratos + serie sintética de M1 (mar 24, mediodía) ──► todos arrancan sin esperar
DA-3 series reales de M1 (mié 25, 2 p. m.) ──► Camila (análisis descriptivo, referencias) · Andrés (redes)
CA-1 calendario exógeno (mié 25) ──► Andrés (variables de calendario de las redes)
AN-1 origen rodante + métricas (mié 25) ──► Camila (evalúa sus modelos de referencia con el mismo arnés)
CA-3 función dimensionar() (jue 26) ──► Andrés (negocio 3) · Daniel (app, paridad TS)
AN-5 pronósticos de test con cuantiles (sáb 28, mediodía) ──► Camila (negocio 1, 2, 4) · Daniel (app M1)
JO-9 modelo ONNX + metadatos (sáb 28, noche) ──► Daniel (app M2)
JJ-7 exportación del recomendador (sáb 28, noche) ──► Daniel (app M3)
todos ──funciones de activación, optimizador y regularización usados (vie 27)──► Juan José (fundamentación común)
todos ──referencias nuevas──► Juan José (verificación APA, continuo)
todos ──hallazgos de la cacería (dom 29, 8 p. m.)──► Andrés (consolida)
todos ──ética de su módulo (dom 29, 8 p. m.)──► Camila (consolida)
todos ──secciones del blog (dom 29, 8 p. m.)──► Daniel (publicación, lun 30)
todo en main (lun 30) ──► Juan José (clon limpio en otra máquina)
```

- **M2 (José) y M3 (Juan José) no dependen de nadie para avanzar**: solo entregan a la app, al blog y a la fundamentación común.
- **M1 es la ruta crítica**: DA-3 → AN-4/AN-5 → CA-6 y app M1 → blog. Por eso existe la serie sintética (§5.11): Andrés y
  Camila construyen y prueban todo desde el martes; cambiar a lo real es cambiar `datos.ruta` en la config.
- Las flechas son **puntos de integración, no bloqueos**: quien recibe trabaja con el contrato y datos de juguete hasta que
  llegue lo real.

---

## 2. Alcance

**Incluido:** todo lo exigido por el enunciado (Anexo).
**Opcional (solo si sobra tiempo):** una segunda arquitectura secuencial en M1; una segunda red preentrenada en M2.
**Fuera de alcance:** entrenamiento en la nube de pago, bases de datos en la app, datos externos que no cumplan M1 tarea 4.

---

## 3. Decisiones

| Tema | Decisión |
|---|---|
| Git [DECIDIDO, Daniel] | `main` protegida; cada integrante en su **rama personal** `dev/<nombre>` y PR; **solo Daniel aprueba y fusiona** (§7.2). |
| Metodología [DECIDIDO] | Spec Driven + Subagent Driven Development, como en los Trabajos 1 y 2 (§10). |
| Spec por persona [DECIDIDO, Daniel, 23-nov] | Núcleo único con contratos + una spec por persona (rama). Cada quien la cambia según avance (regla 0.1). |
| Entorno [PROPUESTO] | **Python 3.12**, `requirements.txt` con versiones fijas. Node 22 LTS para `app/` y `video/`. |
| Redes [PROPUESTO] | **PyTorch** + torchvision, bucle de entrenamiento propio (semillas, parada temprana, regularización y exportación bajo control). Estilo de los notebooks de clase (`nn.Module`, `train_loop`, `val_loop`). |
| Modelos de referencia [PROPUESTO] | M1: `statsmodels` (SARIMA o ETS) y regresión lineal con rezagos y calendario. M2: `scikit-learn` (logística multinomial sobre características congeladas). M3: popularidad + factorización de matrices o vecinos más cercanos. |
| Métricas [PROPUESTO] | Implementadas en `src/comun/metricas.py` y por módulo, contrastadas contra sklearn/scipy o un cálculo a mano en pruebas. |
| Búsqueda [PROPUESTO] | **Optuna, TPE con semilla fija**, número de ensayos fijo y declarado por familia (§6). |
| Reutilización [PROPUESTO] | Se adaptan del Trabajo 2: `src/common/{config,cli,seeds,results,torch_utils,notebooks}.py` y sus pruebas, `test_no_network.py`, `blog/hooks/reporte.py`, `blog/apa.csl`, CI y plantilla de PR. |
| Blog [PROPUESTO] | **Material for MkDocs 1.6.x + hook `reporte.py`** del Trabajo 2, en GitHub Pages. |
| App [PROPUESTO] | **Next.js (TypeScript) exportado como sitio estático, en Vercel**, como en el Trabajo 2. Inferencia **en el navegador**: M1 y M3 desde JSON; M2 con **ONNX Runtime Web**. Prueba de paridad TS vs. Python en CI. |
| Interpretabilidad M2 en la app [PROPUESTO] | Cabeza de la red = *global average pooling* + capa lineal. Con esa cabeza, Grad-CAM sobre la última capa convolucional coincide (salvo escala) con CAM y se calcula en el navegador con los mapas de activación que exporta el ONNX y los pesos de la capa lineal. La equivalencia la demuestra el `verificador-matematico` y la prueba la paridad contra Grad-CAM de PyTorch. |
| Video [PROPUESTO] | Remotion en `video/` + clips de los 5, como en el Trabajo 2. |
| Notebooks [DECIDIDO, consejo del profesor] | Capa delgada sobre `src/` (§5.10): primera celda = parámetros con las mismas claves de `--set`; cero lógica propia. El CLI se mantiene. |
| GPU [PROPUESTO] | Código agnóstico al dispositivo (`device: auto | cpu | cuda`). Demos en CPU. Las 30 semillas de M2 en GPU local o Colab/Kaggle; los resultados registran el dispositivo. |
| Datos crudos | No se versionan; URL, fecha, SHA-256 y tamaño en `data/fuentes.md`. Se versionan los **procesados** (< 100 MB por archivo; Git LFS si hace falta). |
| Arquitectura | Los modelos **no dibujan**: escriben en `results/`; las figuras se construyen con `run.py figures`. Los experimentos **no usan internet**. |

---

## 4. Estructura del repositorio y comandos [PROPUESTO; lo cierra DA-1]

```
Trabajo3_Redes_Neuronales/
├── README.md · CLAUDE.md · requirements.txt · run.py
├── .github/        CODEOWNERS, pull_request_template.md, workflows/{ci,blog}.yml
├── configs/        m1/{datos,base,demo,hpo,operacion}.yaml · m2/{datos,base,demo,hpo,alertas}.yaml · m3/{datos,base,demo,hpo}.yaml
├── src/
│   ├── comun/      config.py, cli.py, seeds.py, results.py, torch_utils.py, eda.py, metricas.py, notebooks.py   (Daniel)
│   ├── m1_demanda/       datos.py (Daniel) · calendario.py, eda.py, referencia.py, operacion.py (Camila) ·
│   │                     evaluacion.py, perdidas.py, redes.py, hpo.py, experimento.py (Andrés)
│   ├── m2_conduccion/    datos.py, duplicados.py, particion.py, eda.py, referencia.py, redes.py, gradcam.py,
│   │                     alertas.py, hpo.py, experimento.py, exportar.py (José)
│   ├── m3_recomendacion/ datos.py, particion.py, eda.py, referencia.py, redes.py, metricas.py, negocio.py,
│   │                     hpo.py, experimento.py, exportar.py (Juan José)
│   └── viz/        estilo.py (Daniel) · figs_m1_*.py (Camila, Andrés) · figs_m2.py (José) · figs_m3.py (Juan José)
├── data/           raw/ (no versionado) · processed/{m1,m2,m3}/ · sintetico/m1/ · fuentes.md
├── models/         {m1,m2,m3}/ modelos entrenados versionados
├── results/        data/{m1,m2,m3}/ · tables/
├── notebooks/      00_sustentacion, 01_m1_datos, 02_m1_redes, 03_m1_operacion, 04_m2, 05_m3 (.py fuente + .ipynb)
├── blog/           mkdocs.yml, secciones/, docs/figures/, hooks/, references.bib, apa.csl
├── app/            Next.js; app/public/model/{m1,m2,m3}/ lo genera `run.py export`
├── video/          Remotion
├── tests/
├── alucinaciones/  registro.md, prompts/, evidencias/
├── docs/           MEMORIA.md, spec/{SPEC.md, PLAN.md, partes/}, sustentacion/
└── .claude/agents/
```
El enunciado pide «una carpeta por módulo»: cada `src/m*_*/` lleva un `README.md` corto que apunta a sus configs, datos,
resultados, notebook y comandos. Cada persona toca **solo sus archivos**. `src/comun/`, `run.py`, `requirements.txt` y el README
raíz son compartidos: se cambian solo con un PR dedicado (§7.2).

### 4.1 Comandos (contrato con el usuario final)

```bash
python run.py m1-datos --config configs/m1/datos.yaml      # crudo → data/processed/m1 (Daniel)
python run.py m1-eda   --config configs/m1/datos.yaml      # plantilla común de análisis descriptivo (Camila)
python run.py m1       --config configs/m1/demo.yaml       # DEMO M1 (< 2 min, CPU)
python run.py m1       --config configs/m1/base.yaml       # M1 completo: referencias + redes finales con 30 semillas
python run.py m1-hpo   --config configs/m1/hpo.yaml        # búsqueda Optuna de las redes de M1
python run.py m1-operacion --config configs/m1/operacion.yaml --set operacion.ocupacion_objetivo=0.8 --set operacion.cuantil=0.9
python run.py m2-datos / m2-eda / m2 / m2-hpo / m2-alertas  (mismo patrón, configs/m2/)
python run.py m3-datos / m3-eda / m3 / m3-hpo               (mismo patrón, configs/m3/)
python run.py export          # modelos → app/public/model/{m1,m2,m3}/ + casos de paridad
python run.py figures         # regenera todas las figuras desde results/
python run.py notebooks       # .py → .ipynb y los ejecuta en modo demo
npm --prefix app run dev      # app local (un solo comando)
mkdocs serve -f blog/mkdocs.yml
```
- Overrides con `--set clave.subclave=valor` (repetible), mismo cargador del Trabajo 2: clave inexistente = error, herencia
  con `hereda: base.yaml`.
- Todo comando imprime la configuración resuelta antes de ejecutar (sirve para la predicción en vivo) y el tiempo total.
- Cambios en vivo que deben funcionar sin tocar código (mínimo): M1 `modelo.tipo`, `modelo.ventana`, `modelo.unidades`,
  `modelo.capas`, `entrenamiento.lr`, `entrenamiento.max_epocas`, `regularizacion.dropout`, `perdida.cuantil`,
  `operacion.ocupacion_objetivo`; M2 `modelo.arquitectura`, `entrenamiento.lr`, `aumento.*`, `regularizacion.*`,
  `alerta.umbral`; M3 `modelo.dim_embedding`, `modelo.negativos_por_positivo`, `perdida.tipo`, `evaluacion.k`;
  todos `semillas.n`.

---

## 5. Contratos (interfaces) — se congelan en DA-1 (mar 24, mediodía)

Los nombres de columnas y claves de esta sección son la propuesta inicial; el dueño de cada contrato puede ajustarlos por PR
**antes** de que otro los consuma.

### 5.1 M1 — series diarias (produce: Daniel · consumen: Camila, Andrés)
`data/processed/m1/demanda_diaria.parquet`, una fila por `(ruta_id, fecha)`, **sin huecos** de fecha:

| Columna | Tipo | Significado |
|---|---|---|
| `ruta_id` | str | `"<origen_divipola>-<destino_divipola>"` |
| `origen_divipola`, `destino_divipola` | str(5) | Código DIVIPOLA del municipio, citado del DANE |
| `fecha` | date | Día de despacho |
| `pasajeros` | int ≥ 0 | Pasajeros que abordan la ruta ese día, en la terminal de origen **y** en terminales en tránsito (suma de registros; [DECIDIDO, Daniel, 24-nov]) |
| `despachos` | int ≥ 0 | Despachos registrados ese día |
| `sin_registro` | bool | El día no tenía registros en la fuente (cómo se imputó: DA-3) |
| `anomalo` | bool | Marcado por alguna regla de anómalos de DA-3 (OR de las reglas) |

`sin_registro` y `anomalo` son **solo descriptivas**: las reglas de anómalos usan una ventana centrada y la escala de toda la
serie (miran el futuro), así que **nunca** son variable de entrada de un modelo. `data/processed/m1/marcas_anomalos.parquet`
(`ruta_id, fecha` + una columna por regla) permite auditar qué regla marcó cada día.

`data/processed/m1/demanda_detalle.parquet` [DECIDIDO, Daniel, 24-nov]: misma granularidad más `tipo_despacho` (ORIGEN /
TRANSITO) y `clase_vehiculo`, con `pasajeros` y `despachos`; la serie de arriba es su suma. Sirve para la capacidad por clase
(Camila) y para reportar la proporción en tránsito.
**Fuente y periodo [DECIDIDO, Daniel, 24-nov]:** datos.gov.co `eh75-8ah6` (Supertransporte), **2021-01-01 a 2023-12-31**
(36 meses continuos). 2024 está casi vacío en la fuente y 2020 casi no tiene filas, así que la caída de la pandemia no está en
los datos: la hipótesis de pospandemia se analiza como tendencia 2021–2023. Investigación: `docs/investigacion/DA-2_fuentes_m1.md`.
**Mayo de 2021 [DECIDIDO, Daniel, 24-nov]:** casi vacío en la fuente (p. ej. Bogotá→Cali 261 pasajeros y 26 días sin registro;
es el único hueco del periodo). La serie se mantiene completa con las marcas (`sin_registro`, `anomalo`) para el análisis
descriptivo; **los modelos (referencias y redes) entrenan desde el 2021-06-01** por defecto, con la clave
`datos.inicio_entrenamiento` en sus configs. Las marcas `anomalo` miran la serie completa: nunca son variable de entrada.
**Flota:** para despachos y vehículos se usan los despachos de **ORIGEN** del detalle (los de tránsito cuentan el mismo vehículo
en cada terminal).
`data/processed/m1/rutas.yaml`: por ruta `ruta_id`, nombres de municipios, `ruta_regreso_id`, criterios de selección.
`data/processed/m1/resumen_datos.json`: registros y variables del crudo, periodo, rutas, conteos de anómalos y días sin registro.

### 5.2 M1 — calendario exógeno (produce: Camila · consume: Andrés)
`data/processed/m1/calendario.parquet`, una fila por `fecha` (todo el periodo + 30 días): `festivo`, `puente`, `semana_santa`,
`vacaciones_escolares`, `fin_de_anio`, `dia_semana`, … (bool/int). Cada columna con su **fuente primaria** en `data/fuentes.md`.
Todas son conocibles con 30 días de anticipación (regla 0.9).

### 5.3 M1 — arnés de evaluación (produce: Andrés · consumen: Camila, Andrés)
```python
class Pronosticador(Protocol):
    nombre: str
    def ajustar(self, serie: pd.DataFrame, calendario: pd.DataFrame) -> None: ...
    def pronosticar(self, origen: date, horizonte: int, cuantiles: list[float]) -> pd.DataFrame: ...
    # columnas: ruta_id, fecha, h (1..30), punto, q<cuantil> (p. ej. q0.9)

def evaluar_origen_rodante(modelo, serie, calendario, origenes: list[date], horizonte: int = 30) -> pd.DataFrame
```
Salida: `results/data/m1/pred_test_<modelo>.parquet` con `origen, ruta_id, fecha, h, y, punto, q0.5, q0.75, q0.9, q0.95`
[PROPUESTO: los cuatro cuantiles permiten que la app cambie el cuantil usado].
Métricas (Andrés, AN-1): MAE, RMSE, MASE (escala: ingenuo estacional de 7 días en train), cobertura y pérdida cuantílica;
por ruta, agregadas y por horizonte (1–7, 8–14, 15–30 y día a día).

**Reglas contra fuga del arnés [DECIDIDO, Daniel, 24-nov, a partir de la auditoría de DA-3]:**
1. `ajustar()` recibe una **lista blanca** de columnas: `ruta_id, fecha, pasajeros` + calendario (§5.2). Nunca `anomalo`,
   `sin_registro`, `despachos` del día objetivo ni el detalle por tipo/clase de ese día. `despachos` o el detalle solo como
   rezagos ≥ 30 días. `tests/test_fuga_m1.py` lo prueba.
2. El test se evalúa sobre **todos** los días con registro: no se excluyen días `anomalo` (una versión sin anómalos solo como
   adicional). Si se excluyen días de la pérdida de entrenamiento, las marcas se recalculan con datos ≤ origen.
3. `inicio_entrenamiento` (2021-06-01) aplica también a las ventanas de entrada: el primer origen usable es
   2021-06-01 + longitud de ventana. Media, desviación y escala de MASE con train y sin días `sin_registro`.
4. La rejilla de orígenes de test se **ancla al final**: último origen = 2023-12-01 (fin − 30 días) y los demás cada 7 días
   hacia atrás, para que el fin de año de 2023 (temporada alta) quede pronosticado.
5. [PROPUESTO, Andrés decide] Reportar además una MASE con la escala de los últimos 12 meses de train: 11001-15759 cambia de
   régimen en nov-2022 (el tránsito pasa de ~1.000 a ~2.700 pasajeros/día) y la escala de todo el train infla su MASE.
Auditoría completa: `docs/investigacion/DA-3_auditoria_fugas.md`.

### 5.4 M1 — operación (produce: Camila · consumen: Andrés, Daniel)
`configs/m1/operacion.yaml`: capacidad por clase de vehículo, ocupación objetivo, tiempo de ciclo por ruta, horas de
operación, jornada máxima y descansos de conductores, ausentismo, costos (quedarse corto vs. sobrar), cuantil usado.
**Cada valor tomado de una norma lleva `fuente:` con la cita primaria**; los supuestos llevan `supuesto: true`.
```python
def dimensionar(demanda: pd.DataFrame, params: dict) -> pd.DataFrame
# entrada: ruta_id, fecha, demanda (punto o cuantil); salida: + despachos, vehiculos, conductores
```
La app reimplementa `dimensionar` en TypeScript; `run.py export` genera casos de paridad.
La composición por clase de vehículo y la razón de despachos de ORIGEN que use `dimensionar` se estiman **solo con train**
(no con `resumen_datos.json`, que resume 2021–2023 completo) [DECIDIDO, Daniel, 24-nov].

### 5.5 M2 — imágenes procesadas (produce y consume: José)
`data/processed/m2/indice.csv`: `id, archivo, clase, grupo_duplicado, split, ancho, alto, tipo_vehiculo` (si la fuente lo
trae [VERIFICAR]) + imágenes redimensionadas y comprimidas en `data/processed/m2/imagenes/`. La partición se hace **por
`grupo_duplicado`** (§5.9 del registro de fuga).

### 5.6 M2 — modelo para la app (produce: José · consume: Daniel)
`app/public/model/m2/modelo.onnx` con dos salidas: `logits` (5) y `mapas` (activaciones de la última capa convolucional);
`app/public/model/m2/meta.json`: `clases`, `grupo_alerta` (clase → sin alerta / con alerta), `umbral_por_defecto`,
`tamano_entrada`, `media`, `desviacion`, `pesos_cabeza` (para CAM) y `casos_paridad` (imagen pequeña → probabilidades y mapa).

### 5.7 M3 — datos (produce y consume: Juan José)
`data/processed/m3/interacciones.parquet` (`usuario_id, destino_id, calificacion, [fecha], split`), `usuarios.parquet`,
`destinos.parquet` con las variables de contenido. Ninguna interacción de prueba se usa para entrenar.

### 5.8 M3 — recomendador para la app (produce: Juan José · consume: Daniel)
`app/public/model/m3/`: `destinos.json` (id, nombre, atributos, embedding 2D para la figura), `usuarios.json` (historial y
top-K precomputado de usuarios existentes), `perfil_nuevo.json` (lista de preferencias seleccionables y los pesos o la regla con
que se recomienda a un perfil nuevo) y `casos_paridad.json`.

### 5.9 Resultados (producen: dueños de módulo · consumen: figuras, blog, app)
Por módulo, en `results/data/<m>/`:
- `summary.json`: por modelo, métricas con `media, desviacion, mejor, peor` sobre las semillas; `n_parametros`;
  `n_configuraciones_busqueda`; `tiempo_total_s`; `device`; `evidencia` (SHA-256 de la partición y del preprocesamiento).
- `semillas/<modelo>_seed<k>.json` (30 por red), `hpo_ensayos.json`, `curvas/<modelo>.json` (pérdida de train y val por época y
  `epoca_parada`), `arquitectura/<modelo>.json` (capas, formas de entrada/salida, activaciones, parámetros).

### 5.10 Notebooks (cada dueño el suyo · infraestructura: Daniel)
Igual que el Trabajo 2: fuente `notebooks/NN_nombre.py` en formato *percent*; `run.py notebooks` genera y ejecuta los
`.ipynb`. **Primera celda = parámetros**:
```python
CONFIG = "configs/m1/demo.yaml"
SET = {"modelo.tipo": "gru", "entrenamiento.lr": 5e-4}   # mismas claves que --set
```
Segunda celda: resuelve e **imprime** la config. Luego una celda markdown «Predicción antes de ejecutar» y la ejecución, que
compara contra la corrida de referencia guardada. Cero lógica en el notebook. Cada uno corre en < 2 min en CPU.
`00_sustentacion` (Daniel) tiene una celda por módulo, porque el profesor escoge el módulo en el momento.

### 5.11 Datos sintéticos (produce: Daniel en DA-1)
`data/sintetico/m1/demanda_diaria.parquet` con el esquema de §5.1: 4 rutas (2 pares ida/regreso), conteos Poisson con
estacionalidad semanal y anual, caída tipo pandemia, picos aleatorios de temporada alta (proxy de festivos: los festivos
reales vienen del calendario de §5.2) y algunos días anómalos o sin registro. Códigos de municipio ficticios (departamento
`00`). Generador: `python -m src.m1_demanda.sintetico`. Solo para desarrollo y pruebas.

### 5.12 Plantilla común de análisis descriptivo [DECIDIDO, Daniel, 23-nov]
**Los tres módulos siguen la misma estructura**, con los mismos nombres de sección en el notebook, en el blog y en los JSON:

| # | Sección | M1 — demanda | M2 — imágenes | M3 — recomendación |
|---|---|---|---|---|
| 1 | **Ficha del conjunto** | Fuente y cita, fecha de descarga, SHA-256, registros, variables, periodo, rutas | Fuente (Mendeley, DOI), imágenes, clases, resoluciones | Fuente (Kaggle), usuarios, destinos, interacciones, escala, densidad, ¿real o sintético? |
| 2 | **Diccionario y calidad** | Variables citadas del diccionario; faltantes, duplicados, inconsistencias diccionario vs. datos | Cómo se construyó el conjunto (artículo) y aumento previo; archivos corruptos | Variables de usuarios y destinos citadas de la fuente; faltantes |
| 3 | **Variable objetivo** | Pasajeros por ruta y día; ceros y anómalos | Imágenes por clase (balance) | Calificaciones e interacciones por usuario y por destino |
| 4 | **Estructura y heterogeneidad** | Tendencia, estacionalidad semanal y anual, diferencias entre rutas, pospandemia | Iluminación, ángulo, tipo de vehículo, duplicados y casi duplicados | Cola larga, concentración en populares, usuarios con pocas interacciones |
| 5 | **Hipótesis explícitas** | Día de la semana, festivos y puentes, temporada escolar, Semana Santa, fin de año, pospandemia | Qué clases serán difíciles de separar y por qué | Qué explica las preferencias |
| 6 | **Implicaciones para el modelado** | Ventana, variables de calendario, pérdida de conteo, partición | Partición por grupos, aumentos, resolución | Partición, negativos, variables de contenido |
| 7 | **Veredicto de las hipótesis** | Confirmada / refutada / no concluyente, con evidencia (se cierra después de modelar) | ídem | ídem |

Contratos de salida, iguales en los tres módulos (`results/data/<m>/eda/`):
- `ficha.json`: `fuente, cita, url, fecha_descarga, sha256, unidad_de_observacion, n_registros, n_variables, periodo` y los
  conteos propios del módulo bajo `conteos`.
- `hipotesis.json`: lista de `{id: "H-M1-1", enunciado, justificacion, evidencia_esperada, figura_o_tabla, resultado,
  veredicto, evidencia}`; `veredicto` ∈ {`pendiente`, `confirmada`, `refutada`, `no concluyente`} (`pendiente` hasta que se
  modela).
- Funciones comunes en `src/comun/eda.py` (ficha, tabla de calidad, escritura y validación de `hipotesis.json`) y estilo de
  figuras en `src/viz/estilo.py`. Cada módulo solo agrega lo específico de su sección 4.
- En el blog, cada módulo abre con la sección «Análisis descriptivo» y estas siete subsecciones, en este orden.

---

## 6. Regla de comparación justa (criterios verificables)

| Regla (enunciado) | Cómo se cumple | Evidencia |
|---|---|---|
| Mismos datos | Un preprocesamiento y una partición por módulo, compartidos por todos sus modelos | SHA-256 de la partición y del preprocesamiento en cada JSON (`evidencia`) |
| Presupuesto explícito | `n_configuraciones_busqueda` y `tiempo_total_s` por familia en `summary.json`, **también para los modelos de referencia** | Tabla del blog |
| ≥ 30 semillas | Configuración final de cada red con `base_seed + 0…29` | 30 archivos en `semillas/` por red |
| Complejidad | `n_parametros()` de cada modelo (para SARIMA/logística/MF: número de parámetros estimados) | Tabla del blog |

Presupuesto de búsqueda inicial [PROPUESTO, cada dueño lo fija en su spec]: M1 MLP 25 y secuencial 25 ensayos; M2 CNN propia
15 y ajuste fino 10; M3 red 20. Se reporta tal cual, aunque sea pequeño.

---

## 7. Requisitos no funcionales y flujo de trabajo

### 7.1 Reproducibilidad
| Requisito | Criterio verificable |
|---|---|
| Versiones fijas | `pip install -r requirements.txt` en venv limpio (Python 3.12); `npm ci` en `app/` |
| Semillas | Misma semilla y mismo dispositivo → mismas métricas (`src/comun/seeds.py`: numpy, torch, random) |
| Sin internet | Experimentos con la red bloqueada (`test_no_network.py`) |
| Un comando | Cada línea de §4.1 funciona desde un clon limpio |
| Parámetros sin editar código | Todo con `--set` o desde la primera celda del notebook |
| Demo < 2 min | `m1`, `m2` y `m3` demo medidos en CPU en una máquina distinta a la de desarrollo |
| Modelos guardados | La app y `run.py figures` funcionan sin reentrenar |
| Datos procesados en el repo | Ningún experimento descarga nada |
| Historial real | Commits frecuentes de las 5 cuentas |

### 7.2 Git y PR [DECIDIDO, Daniel]
- **Nadie hace push a `main`. A `main` solo se llega por PR, que Daniel aprueba y fusiona.**
- Cada integrante hace push libremente a su rama `dev/<nombre>` y, si lo necesita, **a otras ramas** (p. ej. para ayudar a un
  compañero), avisándole. Nunca a `main`.
- Flujo: commits frecuentes → push a la rama → pruebas y revisores → PR hacia `main` → Daniel fusiona → los demás actualizan
  su rama desde `main`.
- Ruleset en `main`: PR obligatorio, 1 aprobación, *Require review from Code Owners*, sin force push ni borrado.
  `.github/CODEOWNERS`: `* @danielgonzalez2709`.
- Las sesiones de Claude hacen commits frecuentes y el push a la rama **cuando el integrante lo indique**.
- Archivos compartidos (`src/comun/`, `run.py`, `requirements.txt`, README, este núcleo): solo por PR dedicado.
- Plantilla de PR: tarea, qué cambia, cómo se probó (salida real), revisiones de subagentes, prompts guardados, candidatos a la
  cacería y **la explicación del autor** (Daniel no fusiona lo que el autor no sabe explicar).
- Daniel revisa PR **al menos tres veces al día** (mañana, tarde, noche).

---

## 8. Pruebas mínimas (cada persona agrega las suyas en su spec)
`test_config.py`, `test_no_network.py`, `test_seeds.py`, `test_eda_comun.py` (esquema de `ficha.json` e `hipotesis.json`),
`test_fuga_m1.py` (ninguna variable posterior al origen del pronóstico), `test_fuga_m2.py` (ningún grupo de casi duplicados en
dos particiones), `test_fuga_m3.py` (ninguna interacción de prueba en train), `test_metricas_*.py`, `test_export.py`,
`test_notebooks.py` (lenta), `app/tests/paridad.test.ts` (M1 dimensionar, M2 probabilidades y CAM, M3 top-K).

---

## 9. Cacería de la alucinación (15 %)
- Registro: `alucinaciones/registro.md` (plantilla de 6 puntos del enunciado) + `evidencias/` + `prompts/`. Consolida Andrés.
- **Guardar prompts literales siempre**, incluidos los del orquestador a cada subagente.
- Meta: ≥ 5 hallazgos **genuinos**, ≥ 3 categorías, **≥ 1 por módulo** y ≥ 1 por persona. Nunca inventar.
- Cada spec personal trae su lista de «puntos calientes» (dónde una IA suele equivocarse en esa parte).
- Los rechazos del `revisor-spec`, del `verificador-matematico` y del `cazador-alucinaciones` sobre algo que generó otro agente
  son la fuente principal de candidatos: ya traen prompt literal y evidencia.

---

## 10. Spec Driven + Subagent Driven Development

### 10.1 Flujo por tarea
```
Responsable (orquesta su sesión de Claude Code, Opus)
  → implementador (Sonnet) o implementador-experto (Opus, tareas 🧠)   [prueba primero]
  → revisor-spec (Sonnet) → revisor-calidad (Haiku)
  → verificador indicado en la tarea (verificador-matematico / auditor-fugas / cazador-alucinaciones, Opus)
  → PR del responsable → Daniel revisa y fusiona → documentador (Haiku) actualiza MEMORIA y PLAN
```

### 10.2 Contexto de cada sesión y subagente
**Sesión principal de cada integrante:** lee este núcleo completo, **incluido el Anexo**, y su spec personal.
**Subagente (mínimo y suficiente):** este núcleo §0, §3, §4.1 y las secciones de §5 que la tarea consume o produce; los
apartados del Anexo que cubre la tarea; la sección de la tarea en la spec personal; el texto de la tarea y su prueba de
aceptación. Nada de otras partes. El prompt literal se guarda en `alucinaciones/prompts/<ID>.md` **antes** de enviarlo.

### 10.3 Agentes (`.claude/agents/`) y modelos
| Agente | Modelo | Para qué |
|---|---|---|
| `implementador` | Sonnet | Una tarea de código Python estándar, prueba primero |
| `implementador-experto` | **Opus** | Tareas 🧠: pérdidas, origen rodante, partición sin fuga, Grad-CAM/CAM, negativos y pérdida de M3, modelo de flota |
| `implementador-web` | Sonnet | App Next.js y video Remotion |
| `curador-datos` | Sonnet | Descarga, diccionario, conteos, fuentes, ficha |
| `analista-experimentos` | Sonnet | Corre búsquedas y 30 semillas, vigila la comparación justa, señala resultados sospechosos |
| `revisor-spec` | Sonnet | ¿Cumple exactamente el Spec y el enunciado? |
| `revisor-calidad` | Haiku | Claridad y pruebas del código (se explica en vivo) |
| `verificador-matematico` | **Opus** | Deriva y comprueba numéricamente cada fórmula (pérdidas, LSTM/GRU, softmax/entropía cruzada, CAM, métricas, flota) |
| `cazador-alucinaciones` | **Opus** | Contrasta afirmaciones de IA con fuentes primarias o experimentos; registra hallazgos |
| `redactor-tecnico` | Sonnet | Secciones del blog con figuras y tablas numeradas y citadas |
| `tutor-sustentacion` | Sonnet | Fichas, preguntas probables, predicciones verificadas para cambios en vivo |
| `auditor-reproducibilidad` | Haiku | Clon limpio, demos < 2 min, sin internet, un comando |
| `documentador` | Haiku | MEMORIA, PLAN, README, pies de figura, registro de prompts |
| **Nuevos en el Trabajo 3** | | |
| `auditor-fugas` | **Opus** | Auditoría adversarial de fuga en los tres módulos: variables de M1 no conocibles 30 días antes y ventanas que miran al futuro; casi duplicados de M2 entre particiones; interacciones de prueba de M3 en train o en la popularidad. Escribe la prueba que lo demuestra |
| `investigador-fuentes` | Sonnet (web) | Busca y cita la **fuente primaria** de lo que no sale de los datos: normativa de jornada de conductores, festivos y calendario escolar, DIVIPOLA, diccionario de datos.gov.co, artículo de Data in Brief, documentación de Kaggle. Entrega cita APA + URL + fecha de consulta, nunca de memoria |
| `auditor-entregables` | Haiku | Recorre el Anexo como lista de chequeo (figuras mínimas por módulo y comunes, métricas, preguntas de negocio, limitaciones, secciones del blog) y reporta qué existe, dónde y qué falta |

La sesión principal (orquestador) corre en **Opus**. Regla: Haiku para lo mecánico y fácil de verificar; Sonnet para
implementación con una spec clara; Opus para diseño, matemáticas, fugas y auditoría (donde un error suena convincente).

---

## 11. Hitos de integración

| Cuándo | Hito | De → a |
|---|---|---|
| **Lun 23, noche** | Spec v0.1 aprobado; repo con `main`, ruleset y ramas `dev/*` | Daniel → todos |
| **Mar 24, mediodía** | DA-1: infraestructura, contratos congelados, serie sintética de M1, CI | Daniel → todos |
| **Mar 24, noche** | Datos de M2 y M3 descargados con su ficha; crudo de M1 descargado | José, Juan José, Daniel |
| **Mié 25, 2 p. m.** | **Series reales de M1** (`demanda_diaria.parquet`, `rutas.yaml`) | Daniel → Camila, Andrés |
| **Mié 25, noche** | Arnés de origen rodante (Andrés) y calendario (Camila); particiones sin fuga de M2 y M3 | Andrés ↔ Camila; José; Juan José |
| **Jue 26, noche** | Modelos de referencia de los 3 módulos evaluados; búsquedas de las redes corriendo; app con contratos de juguete | todos |
| **Vie 27, noche** | 30 semillas lanzadas (M2 en GPU); lista de activaciones/optimizador/regularización a Juan José | todos |
| **Sáb 28, mediodía** | Pronósticos de test con cuantiles de M1 | Andrés → Camila, Daniel |
| **Sáb 28, tarde** | Grabación del video con los 5 | todos |
| **Sáb 28, noche** | Exportaciones reales de M1, M2 y M3 a la app | Camila/Andrés, José, Juan José → Daniel |
| **Dom 29, 8 p. m.** | Secciones del blog, ética y ≥ 1 hallazgo por persona | todos → Daniel, Camila, Andrés |
| **Lun 30** | Blog publicado, app final en Vercel, clon limpio en otra máquina, videos individuales, fichas de sustentación | todos |
| **Mar 1-dic** | Margen y **entrega** | todos |

Si un hito se atrasa, quien lo recibe sigue con los sintéticos o el contrato de juguete y avisa a Daniel.

---

## 12. Riesgos y mitigaciones
| Riesgo | Mitigación |
|---|---|
| Solo 8 días | Contratos y sintéticos desde el martes; nadie espera; PR pequeños; Daniel revisa 3 veces al día |
| El conjunto de datos.gov.co es grande o lento de descargar | Agregación en el servidor (API Socrata) o descarga por partes; solo la serie procesada va al repo |
| Fuga en M2 por imágenes aumentadas antes de publicar | Hash perceptual + similitud de características, partición por grupos, `test_fuga_m2.py`, auditoría Opus |
| 30 semillas de ajuste fino no caben | Red base pequeña, resolución moderada, pocas épocas con parada temprana, GPU; se reporta el tiempo |
| Normativa de jornada, festivos o DIVIPOLA mal citados | Solo fuente oficial; `cazador-alucinaciones`; si una IA se equivoca, es hallazgo |
| Grad-CAM no corre en el navegador | Cabeza GAP + lineal (CAM ≡ Grad-CAM) y paridad; plan B: mapas precalculados para las imágenes de ejemplo + mapa en vivo solo con CAM |
| La app calcula distinto que Python | Contratos §5.4, §5.6, §5.8 + paridad en CI |
| La red no supera al modelo de referencia | Es un resultado válido y se reporta con honestidad (el enunciado lo anticipa) |
| Alguien no puede explicar lo que hizo un agente | El autor explica en el PR; `tutor-sustentacion`; simulacro |

---

## 13. Pendientes
1. Hora exacta de la entrega y fecha de la sustentación.
2. Aprobación del reparto (§1.1) y de los [PROPUESTO] de §3 por el equipo.
3. Rutas de M1 (cuántas y cuáles): Daniel y Camila en DA-3.
4. Quién tiene GPU local para M2.

---

## Anexo — Enunciado literal del trabajo

> Transcripción del PDF «Trabajo 03 Redes neuronales para series de tiempo, imágenes y recomendación». No se edita.

**Trabajo 3: Redes neuronales para series de tiempo, imágenes y recomendación**

Sistema inteligente integrado para pronóstico de demanda, seguridad vial y recomendación en una empresa de transporte

Profesor: Juan David Ospina Arango · Monitor: Andrés Mauricio Zapata Rincón · Universidad Nacional de Colombia, Facultad de
Minas, Departamento de Ciencias de la Computación y de la Decisión · Curso: Redes neuronales y algoritmos bioinspirados.
Semestre 2026-02 · Modalidad: trabajo en equipo, con sustentación oral y evaluación individual

### Propósito
Una empresa de transporte intermunicipal de pasajeros enfrenta tres retos: saber cuántas personas viajarán en sus rutas y con
qué recursos atenderlas, detectar conductores que manejan distraídos y ofrecer a sus clientes destinos de viaje acordes con sus
preferencias (en este caso, destinos en el extranjero). En este trabajo van a resolver tres problemas con redes neuronales: uno
de series de tiempo, otro de clasificación de imágenes y otro de sistemas de recomendación. Además, van a integrar sus modelos
en una aplicación web y traducir sus resultados en decisiones de negocio.

Las redes neuronales no siempre son la mejor herramienta. Parte del reto es averiguar, con evidencia y comparaciones justas,
qué aporta cada uno en cada problema y qué no, y cuánto vale esa diferencia para la empresa.

Pueden (y se espera) que usen herramientas de inteligencia artificial. Pero la IA se equivoca, a veces con total seguridad.
Parte del trabajo consiste en demostrar que ustedes entienden lo suficiente como para darse cuenta. Lo que se evalúa no es solo
lo que entregan, sino también lo que son capaces de explicar, modificar y defender en vivo.

#### Objetivo general
Desarrollar un sistema basado en redes neuronales que integre el pronóstico de la demanda de transporte y la planeación de la
operación, la clasificación de comportamientos distractores de los conductores a partir de imágenes y la recomendación
personalizada de destinos de viaje.

#### Objetivos específicos
1. Pronosticar la demanda de pasajeros por ruta para los próximos 30 días y dimensionar, en función de ella, la flota y los
   conductores requeridos.
2. Clasificar imágenes de conductores según su comportamiento al volante.
3. Recomendar destinos de viaje a partir del historial y de las preferencias de los usuarios.
4. Comparar cada red neuronal con un modelo de referencia en condiciones equivalentes.
5. Integrar los tres módulos en una aplicación web publicada.
6. Documentar el proceso en un reporte técnico reproducible.

### Módulo 1: Pronóstico de demanda y planeación de la operación
Una empresa de transporte intermunicipal necesita saber cuántas personas querrán viajar en cada una de sus rutas durante los
próximos 30 días y, con esa información, decidir cuántos vehículos despachar y con cuántos conductores. Un pronóstico que se
queda corto deja pasajeros en la terminal; uno que se pasa deja vehículos y conductores ociosos.

#### Datos
Usarán el conjunto de datos "Operación de pasajeros y despacho de vehículos en la modalidad de transporte de pasajeros por
carretera", publicado por la Superintendencia de Transporte en datos.gov.co (enlace).

Para identificar los municipios, usarán la codificación DIVIPOLA del DANE, citada de la fuente oficial. Reporten el número de
registros y de variables, el periodo que cubren y las rutas analizadas. Citen el significado de las variables del diccionario
del conjunto. Si encuentran inconsistencias entre el diccionario y los datos, documéntenlas.

#### Tareas
1. **Caso de uso.** Describan quién usa el pronóstico, para qué decisión, con cuánta anticipación y con qué información
   disponible en ese momento. Ninguna variable puede depender de información que no se conozca 30 días antes.
2. **Construcción de las series.** Definan la variable objetivo (pasajeros por ruta y por día) y documenten cómo agregan los
   registros, cómo manejan los días sin registros y cómo detectan y tratan los datos anómalos (por ejemplo, despachos con cero
   pasajeros).
3. **Análisis descriptivo.** Formulen hipótesis explícitas sobre qué determina la demanda: el día de la semana, los festivos y
   puentes, las temporadas escolares, Semana Santa, el fin de año y la recuperación posterior a la pandemia. Analicen la
   tendencia y la estacionalidad de cada ruta. Al final, digan qué hipótesis se confirmaron.
4. **Variables exógenas.** Pueden incorporar información externa (calendario de festivos, temporadas, eventos) si está
   disponible en el momento de la decisión, está guardada en el repositorio y se cita su fuente primaria.
5. **Modelos de referencia.** Ajusten un pronóstico ingenuo estacional (por ejemplo, el mismo día de la semana anterior) y un
   modelo estadístico o lineal (SARIMA, suavizamiento exponencial o regresión lineal con rezagos y calendario).
6. **Redes neuronales.** Construyan y optimicen un perceptrón multicapa con ventanas de rezagos y al menos una arquitectura
   secuencial (LSTM, GRU o convolucional 1D): longitud de ventana, capas, unidades, regularización, optimizador y tasa de
   aprendizaje. Justifiquen el método de búsqueda y si entrenan un modelo por ruta o uno global.
7. **Función de pérdida.** Justifiquen la pérdida a partir de la naturaleza de la variable objetivo, que es de conteo. Además
   del pronóstico puntual, estimen al menos un cuantil alto (por ejemplo, el P90).
8. **Evaluación.** Usen particiones temporales y evaluación con origen rodante para el horizonte de 30 días. Reporten MAE,
   RMSE y MASE por ruta y agregados; el error por horizonte (días 1–7, 8–14, 15–30); cobertura y pérdida cuantílica; y gráficas
   de pronóstico frente a la demanda real por ruta, con al menos una temporada alta en el conjunto de prueba.

#### Preguntas de negocio
Los parámetros operativos (capacidad por clase de vehículo, ocupación objetivo, tiempo de ciclo por ruta, horas de operación,
jornada de los conductores y costos) deben estar en un archivo de configuración. Todo valor tomado de una norma debe citarse a
partir de la fuente primaria.
1. **Dimensionamiento de flota.** ¿Cuántos despachos y cuántos vehículos se necesitan por ruta y por día durante los próximos
   30 días? Escriban la fórmula y justifiquen cada término: capacidad, ocupación objetivo, vueltas posibles por vehículo y día.
   Si la demanda real resulta un 10 % mayor o menor que el pronóstico, ¿cómo cambia la flota y qué parámetro afecta más el
   resultado?
2. **Conductores.** ¿Cuántos conductores se requieren para operar esa flota, considerando la jornada máxima, los descansos y el
   ausentismo? Citen la normativa colombiana vigente sobre la jornada de conductores desde su fuente oficial.
3. **Valor del pronóstico.** ¿Dimensionarían con el pronóstico puntual o con un cuantil alto? Para el periodo de prueba,
   cuantifiquen los pasajeros sin atender y los vehículos-día sobrantes con cada opción, usando la mejor red neuronal y el mejor
   modelo de referencia. ¿Cómo cambia la decisión según el costo relativo de quedarse corto frente al de sobrar? ¿Justifica la
   red neuronal su complejidad en términos operativos?
4. **Temporada alta.** Para la próxima temporada alta del horizonte de prueba (por ejemplo, un puente festivo o el fin de año),
   ¿cuántos vehículos y conductores adicionales se requieren en comparación con una semana normal? ¿Recomendarían flota propia,
   arrendada o convenios con otras empresas?

#### Limitaciones que deben discutir
- Los datos registran a los pasajeros que abordan en la terminal de origen, no a quienes suben en la vía.
- Cada ruta tiene un sentido de regreso que es otra serie; ¿cómo lo incorporan al cálculo de vueltas y flota?
- La demanda observada está limitada por la oferta: si no hay sillas, el pasajero no aparece.

#### Fundamentación matemática del módulo
- Ecuaciones de la arquitectura secuencial utilizada.
- Derivación de la pérdida para conteos y de la pérdida cuantílica a partir de un modelo probabilístico.
- Definición de MASE, cobertura y pérdida cuantílica.
- Formulación del modelo de dimensionamiento de flota y conductores.

#### Figuras mínimas del módulo
- Series de demanda de las rutas analizadas.
- Descomposición en tendencia y estacionalidad (semanal y anual) de al menos una ruta.
- Pronóstico frente a demanda real por ruta, con la banda del cuantil alto.
- Error según el horizonte (días 1 a 30), para cada modelo.
- Flota y conductores requeridos por día durante los 30 días pronosticados.
- Sensibilidad de la flota requerida frente a variaciones de la demanda y del parámetro operativo más influyente.

### Módulo 2: Clasificación de conducción distractiva
La empresa quiere instalar cámaras en sus vehículos para detectar cuándo un conductor maneja distraído y generar una alerta.
Una alerta que no se dispara deja pasar un riesgo; una que se dispara sin motivo hace que los conductores dejen de prestarle
atención.

#### Datos
Usarán el conjunto Multi-Class Driver Behavior Image Dataset (Afridi et al., 2024), publicado en Mendeley Data
(DOI 10.17632/mzb4b6dff3.1) y descrito en Data in Brief (DOI 10.1016/j.dib.2025.111529). Contiene imágenes de conductores de
carros particulares y buses públicos tomadas con celulares en Dhaka (Bangladesh), clasificadas en cinco clases: conducción
segura, giro, escribir en el teléfono, hablar por teléfono y otros comportamientos riesgosos (por ejemplo, beber, voltear hacia
atrás o somnolencia).

Reporten el número de imágenes por clase y su resolución. Lean el artículo de los autores y expliquen cómo se construyó el
conjunto, incluido cualquier aumento de datos aplicado antes de la publicación.

#### Tareas
1. **Caso de uso.** Describan quién recibe la alerta, en qué momento, qué acción desencadena y qué restricciones impone el
   vehículo (cámara, cómputo disponible, latencia).
2. **Análisis descriptivo.** Analicen el balance de clases, la variabilidad de iluminación, ángulo y tipo de vehículo, y la
   presencia de imágenes duplicadas o casi idénticas. Formulen hipótesis sobre qué clases serán más difíciles de separar y por
   qué.
3. **Partición sin fuga de información.** Definan y justifiquen entrenamiento, validación y prueba. Demuestren que no hay
   imágenes iguales o casi iguales (por ejemplo, versiones aumentadas de una misma foto) en particiones distintas, y describan
   el método con que lo verificaron.
4. **Modelo de referencia.** Ajusten una regresión logística multinomial sobre características extraídas por una red
   preentrenada congelada.
5. **Redes neuronales.** Construyan y comparen: (a) una red convolucional diseñada y entrenada por ustedes desde cero, y (b) una
   red preentrenada con ajuste fino (transfer learning). Optimicen arquitectura, aumento de datos, regularización, optimizador
   y tasa de aprendizaje con un método de búsqueda justificado.
6. **Evaluación.** Reporten exactitud, F1 macro, precisión y sensibilidad por clase, y matriz de confusión sobre el conjunto de
   prueba. Muestren al menos 10 imágenes bien clasificadas y 10 mal clasificadas, y expliquen los errores.
7. **Interpretabilidad.** Usen un método justificado y citado (por ejemplo, Grad-CAM) para verificar en qué regiones de la
   imagen se apoya el modelo. ¿Mira al conductor y al teléfono, o al fondo del vehículo?

#### Preguntas de negocio
1. **Política de alertas.** Agrupen las clases en «sin alerta» y «con alerta» y justifiquen la agrupación. ¿Qué umbral de
   decisión usarían? Muestren cuántas falsas alarmas y cuántas distracciones no detectadas habría por cada 1.000 imágenes con
   distintos umbrales, y elijan uno según el costo relativo de cada error.
2. **Generalización.** Los datos provienen de otro país, de cámaras de celular y de condiciones de tráfico distintas. Formulen
   hipótesis sobre cómo cambiaría el desempeño en una flota colombiana y propongan cómo validarlo antes de una implementación
   real.
3. **Medidas preventivas.** Con base en las clases más frecuentes y los errores del modelo, ¿qué medidas preventivas
   recomendarían a la empresa, además de la alerta?

#### Fundamentación matemática del módulo
- Operaciones de convolución, *pooling* y normalización por lotes.
- Función *softmax* y derivación de la entropía cruzada a partir de la verosimilitud multinomial.
- Formulación del ajuste fino y de las transformaciones de aumento de datos usadas.
- Definición de las métricas de clasificación y del método de interpretabilidad.

#### Figuras mínimas del módulo
- Distribución de imágenes por clase y por partición.
- Ejemplos representativos de cada clase.
- Matriz de confusión del mejor modelo en el conjunto de prueba.
- Falsas alarmas y distracciones no detectadas por debajo del umbral de alerta.
- Mapas de interpretabilidad (por ejemplo, Grad-CAM) sobre aciertos y errores.

### Módulo 3: Recomendación de destinos de viaje
Como valor agregado para sus clientes, la empresa lanzará una línea de turismo internacional en alianza con operadores
turísticos, que comenzará con destinos en India. Quiere sugerir a cada cliente los destinos que probablemente le interesen, a
partir de datos históricos y de las preferencias de otros usuarios. Una buena recomendación genera un viaje y fideliza al
cliente a la marca; una mala hace que ignore las siguientes.

#### Datos
Usarán el conjunto Travel Recommendation Dataset (India Travel Recommender System Dataset), publicado en Kaggle por Aman Mehra
(https://www.kaggle.com/datasets/amanmehra23/travel-recommendation-dataset). Reporten el número de usuarios, destinos e
interacciones, la escala de las calificaciones, la densidad de la matriz usuario–destino y las variables disponibles de
usuarios y destinos. Indiquen si los datos son reales o sintéticos, según la documentación de la fuente, y discutan qué implica
para sus conclusiones.

#### Tareas
1. **Caso de uso.** Describan en qué momento y en qué canal se muestra la recomendación, cuántos destinos se muestran (K) y qué
   información del usuario está disponible en ese momento.
2. **Análisis descriptivo.** Analicen la distribución de interacciones por usuario y por destino, la concentración en los
   destinos populares y la proporción de usuarios con pocas interacciones. Formulen hipótesis sobre qué explica las
   preferencias.
3. **Partición.** Definan y justifiquen cómo separan los conjuntos de entrenamiento, validación y prueba (por ejemplo, por
   tiempo si hay fechas, o excluyendo interacciones por usuario). Ninguna interacción de prueba puede usarse para entrenar.
4. **Modelos de referencia.** Ajusten una recomendación basada en popularidad y un filtrado colaborativo clásico (vecinos más
   cercanos o factorización de matrices).
5. **Red neuronal.** Construyan y optimicen un recomendador neuronal (por ejemplo, un modelo de filtrado colaborativo neuronal o
   un modelo de dos torres) que utilice, además de las interacciones, al menos una variable de contenido del usuario o del
   destino. Justifiquen la dimensión de los *embeddings*, el muestreo de negativos y la función de pérdida.
6. **Evaluación.** Reporten Precision, Recall y NDCG@K, además de la cobertura del catálogo y el desempeño separado para
   usuarios con pocas y muchas interacciones. Muestren las recomendaciones para al menos 5 usuarios con perfiles distintos,
   junto con su historial, y expliquen por qué tienen o no sentido.

#### Preguntas de negocio
1. **Usuarios nuevos.** ¿Qué recomendarían a un cliente sin historial? Comparen al menos dos estrategias y cuantifiquen su
   desempeño simulando usuarios nuevos en el conjunto de prueba.
2. **Concentración de la demanda.** ¿Sus recomendaciones concentran a los clientes en pocos destinos populares? Midan la
   concentración y discutan qué implicaría para la capacidad de las rutas si la empresa siguiera esas recomendaciones.
3. **Campaña.** Si la empresa pudiera promocionar un solo destino este mes, ¿a qué grupo de usuarios lo mostraría y cuántas
   conversiones esperaría según su modelo? Expliciten los supuestos.

#### Fundamentación matemática del módulo
- Formulación de la factorización de matrices y de la arquitectura de red neuronal usada.
- Derivación de la función de pérdida (por ejemplo, entropía cruzada binaria con muestreo de negativos o BPR) a partir de un
  modelo probabilístico.
- Definición de Precision, Recall, NDCG y cobertura.

#### Figuras mínimas del módulo
- Distribución de interacciones por usuario y por destino (cola larga).
- Precision, Recall y NDCG en función de K, para cada modelo.
- Cobertura del catálogo y concentración de las recomendaciones en función de la popularidad de los destinos.
- Proyección en dos dimensiones de los *embeddings* de los destinos (por ejemplo, con t-SNE o UMAP), con interpretación de los
  grupos que aparezcan.

### Aplicación web
Una aplicación publicada (link requerido) que integre los tres módulos, sea intuitiva para un usuario nuevo e incluya enlaces al
reporte técnico, al video promocional y video de contribuciones individuales. Como mínimo debe permitir:
- **Demanda y operación:** elegir una ruta y ver el pronóstico a 30 días con su banda de incertidumbre, la flota y los
  conductores requeridos, y cómo cambian al modificar al menos dos parámetros operativos (por ejemplo, ocupación objetivo y
  cuantil usado).
- **Conducción distractiva:** subir una imagen y obtener la clase asignada, la probabilidad de cada clase, la decisión de alerta
  según el umbral elegido y el mapa de interpretabilidad.
- **Recomendación:** elegir un usuario existente o crear un perfil nuevo y ver sus K destinos recomendados junto con su
  historial. Debe tener un listado de preferencias para elegir y que esto lleve a los recomendaciones de destinos de viaje.

La aplicación debe usar los modelos guardados, sin reentrenar, y poder levantarse localmente con un solo comando.

### Regla de comparación justa
En cada módulo, las redes neuronales se comparan con sus modelos de referencia bajo condiciones explícitas y equivalentes:
- **Mismos datos:** todos los modelos de un módulo usan el mismo preprocesamiento y las mismas particiones.
- **Presupuesto de búsqueda explícito:** reporten cuántas configuraciones entrenaron para cada familia de modelos y el tiempo de
  cómputo total. Una arquitectura que «gana» tras 200 intentos contra un modelo de referencia ajustado una sola vez no es una
  comparación justa sin esa aclaración.
- **Varias corridas independientes:** entrenen la configuración final de cada red con al menos 30 semillas distintas y reporten
  media, desviación estándar, mejor y peor valor de cada métrica.
- **Complejidad:** reporten el número de parámetros entrenables de cada modelo.

### Discusión
Para cada módulo: ¿qué aportó la red neuronal frente al modelo de referencia? Respondan con base en las métricas, su
variabilidad entre semillas, el costo de cómputo, la interpretabilidad y las consecuencias para el negocio. Incluyan un listado
de aprendizajes sobre cada problema que surgió del proceso de modelamiento.

### Entregables

#### 1. Reporte técnico publicado como entrada de blog
El reporte debe contener el entendimiento desarrollado, la metodología seguida y justificada, los resultados, las respuestas a
las preguntas de negocio y la discusión de cada módulo. Se exige:
- Bibliografía en formato APA (7.ª edición). Todas las referencias deben existir, ser verificables y estar citadas en el texto.
  Una referencia inexistente se penaliza.
- Figuras y tablas numeradas, con título y fuente, y todas citadas explícitamente en el texto. No se aceptan figuras huérfanas.
- Fundamentación matemática común: definición de neurona artificial y de cada función de activación utilizada; el algoritmo de
  *backpropagation* y las ecuaciones de actualización del optimizador utilizado; la formulación de cada técnica de
  regularización. Además, la fundamentación propia de cada módulo.
- Sección de ética: manejo de datos, privacidad de conductores y usuarios, sesgos de los conjuntos de datos y riesgos de cada
  sistema si se implementara.
- Sección de uso de IA: los principales prompts utilizados y una discusión de su impacto en el resultado final.
- Sección «Cacería de la alucinación».
- Enlaces al repositorio Git, a la aplicación web y al video promocional.

Figuras mínimas comunes, para cada red neuronal final de cada módulo (además de las figuras mínimas propias de cada módulo):
- Diagrama de la arquitectura: capas, dimensiones de entrada y salida, funciones de activación y número de parámetros
  entrenables.
- Curvas de aprendizaje: pérdida de entrenamiento y validación por época, señalando dónde actuó la parada temprana.
- Resultados de la búsqueda de hiperparámetros: desempeño en validación de las configuraciones probadas.
- Comparación entre modelos: la métrica principal de cada modelo con su variabilidad entre las 30 semillas (por ejemplo,
  diagramas de caja).

#### 2. Repositorio Git reproducible
- README con instrucciones de instalación y ejecución, y una carpeta por módulo.
- Entorno especificado con versiones fijas (requirements.txt, environment.yml o similar).
- Semillas aleatorias fijas y documentadas.
- Los datos procesados que usan los modelos deben estar en el repositorio para que la ejecución no dependa de internet ni de
  APIs externas. Si exceden los límites de tamaño, guarden una versión procesada y comprimida, y documenten cómo se obtuvo.
- Modelos entrenados guardados, de modo que la aplicación y las figuras no requieran reentrenar.
- Figuras regenerables desde el código.
- Historial de commits que refleje el trabajo real del equipo. Un único commit al final no es aceptable.

#### 3. Todo debe correr en vivo
- Cada experimento principal de cada módulo debe lanzarse con un solo comando.
- Los parámetros (arquitectura, tasa de aprendizaje, regularización, épocas, cuantil, parámetros operativos, umbral de alerta,
  K, etc.) deben poder cambiarse desde la línea de comandos o un archivo de configuración, sin editar el código fuente.
- Una corrida de demostración de cada módulo debe tardar menos de dos minutos. Si el entrenamiento completo tarda más, preparen
  un modo de demostración que se lance también con un solo comando.
- Antes de la sustentación, prueben todo en un clon limpio del repositorio en una máquina distinta a la de desarrollo.

#### 4. Aplicación web
Según lo descrito en la sección Aplicación web.

#### 5. Video promocional
Un video de 2 a 3 minutos que presente la aplicación como la solución a un problema de la empresa y genere entusiasmo por
usarla.

#### 6. Videos de contribución individual
Cada integrante graba un video de 2 a 3 minutos en primera persona, hablando sobre sus aportes específicos, con evidencia
concreta: un fragmento de código que escribió, un commit, una figura que elaboró o una sección del reporte que redactó, y una
explicación breve de cómo funciona. Lo que cada persona declare podrá ser preguntado en la sustentación.

### Cacería de la alucinación
Las herramientas de IA producen errores que suenan convincentes. Su misión es cazarlos. Documenten al menos cinco hallazgos en
los que una IA generó algo incorrecto, impreciso, desactualizado o subóptimo durante el trabajo, con al menos uno en cada
módulo. Deben cubrir al menos tres de estas categorías:
- **Matemáticas:** derivadas, funciones de pérdida, fórmulas de métricas o del dimensionamiento de flota.
- **Código:** errores de implementación, preprocesamiento defectuoso, fugas de información, métricas mal calculadas.
- **Datos del mundo real:** significado de las variables, códigos DIVIPOLA, normativa de transporte, características de los
  conjuntos de datos.
- **Bibliografía:** referencias inexistentes, autores o años equivocados, DOI que no resuelven.
- **Conceptos:** afirmaciones falsas sobre las redes neuronales, su entrenamiento o su desempeño frente a métodos clásicos.

Para cada hallazgo, reporten:
1. El prompt utilizado (literal).
2. La parte relevante de la respuesta de la IA.
3. Cómo sospecharon que había un error.
4. La evidencia que lo demuestra: una derivación, un experimento o una fuente primaria.
5. La corrección.
6. La lección aprendida: ¿qué verificación habría evitado el error?

Si no logran encontrar los hallazgos requeridos, documenten las verificaciones que hicieron y sus resultados. Un hallazgo
inventado o sin evidencia se penaliza más que un hallazgo faltante.

### Sustentación
Cada equipo tiene 10 minutos. El profesor escoge en el momento el módulo sobre el que se hace la demostración y la modificación.

| Momento | Contenido |
|---|---|
| Demostración | Ejecución en vivo de un experimento, con un solo comando. |
| Modificación en vivo | El profesor pide un cambio de parámetro o de configuración. Antes de ejecutarlo, el equipo predice qué ocurrirá y por qué. |
| Preguntas | El profesor pregunta a cualquier integrante, escogido al azar, sobre cualquier parte del trabajo, incluidas las preguntas de negocio y lo declarado en los videos individuales. |

Todos los integrantes deben estar en capacidad de explicar todo el trabajo, no solo su parte.

### Evaluación

| Componente | Peso | Tipo |
|---|---|---|
| Reporte técnico (rigor, APA, figuras y tablas, preguntas de negocio, discusión, ética) | 20 % | Grupal |
| Repositorio y reproducibilidad | 5 % | Grupal |
| Aplicación web | 10 % | Grupal |
| Video promocional | 5 % | Grupal |
| Ejecución y modificación en vivo | 10 % | Grupal |
| Cacería de la alucinación | 15 % | Grupal |
| Video de contribución individual | 5 % | Individual |
| Respuestas en la sustentación | 30 % | Individual |

La nota individual de la sustentación puede ajustar la nota grupal si un integrante no logra explicar un componente que
declaró como propio.
