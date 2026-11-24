# Trabajo 3 — Redes neuronales para series de tiempo, imágenes y recomendación

Tres módulos: M1 pronóstico de demanda y planeación de la operación (transporte intermunicipal), M2 clasificación de
conducción distractiva (imágenes) y M3 recomendación de destinos de viaje; más aplicación web, blog y video. Curso Redes
neuronales y algoritmos bioinspirados, UNAL 2026-02.

- Spec (fuente de verdad, con el enunciado en el Anexo): [`docs/spec/SPEC.md`](docs/spec/SPEC.md) · specs personales en
  [`docs/spec/partes/`](docs/spec/partes/) · tablero: [`docs/spec/PLAN.md`](docs/spec/PLAN.md)
- Estado actual: [`docs/MEMORIA.md`](docs/MEMORIA.md)
- Reporte (blog): pendiente
- Aplicación web: esqueleto con datos de juguete (DA-5); sin publicar todavía
- Video promocional: pendiente

## Instalación (Python 3.12)

Windows (PowerShell o Git Bash):

```bash
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

- **Clona el repositorio en una ruta corta**, p. ej. `C:\proy\Trabajo3_Redes_Neuronales`. En una ruta profunda `pip install`
  falla por el límite de 260 caracteres de Windows (algunos paquetes traen rutas muy largas). La alternativa es habilitar las
  rutas largas de Windows (`LongPathsEnabled`; requiere administrador y reiniciar la sesión).
- Usa siempre `.venv\Scripts\python` (o activa el entorno con `.venv\Scripts\activate`): el `python` del PATH puede ser otra
  versión (p. ej. 3.13) y no la 3.12 que fija el proyecto. En Linux y macOS, `.venv/bin/python`.

Linux y macOS: en Linux, la rueda de torch de PyPI trae CUDA (varios GB), así que primero se instala la de CPU desde el
índice de PyTorch y después el resto (es lo mismo que hace el CI en `.github/workflows/ci.yml`; la versión de torch es la
que fija `requirements.txt`):

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install -r requirements.txt
```
En macOS la rueda de PyPI ya es de CPU; el primer comando de pip se puede omitir.

Con GPU NVIDIA (opcional): reinstalar torch desde https://pytorch.org con la versión de CUDA de su equipo. Las demos corren
en CPU (`device: auto | cpu | cuda` en las configs).

## Datos
Los datos crudos no se versionan (URL, fecha, SHA-256 y tamaño en `data/fuentes.md`); los procesados sí, en
`data/processed/`. Ningún experimento descarga nada.

## Comandos (núcleo §4.1)
Cada comando imprime la configuración resuelta y el tiempo total. Un subcomando cuyo módulo aún no existe imprime
«pendiente: <dueño> (<tarea>)» y sale con código 2. `--set clave.subclave=valor` es repetible; una clave inexistente es un
error; las configs heredan con `hereda: base.yaml`. Todos los parámetros se cambian así, sin tocar código.

### Lo que funciona hoy
```bash
.venv\Scripts\python run.py --help                         # lista de subcomandos
.venv\Scripts\python run.py m1 --help                      # ayuda de un subcomando (--config, --set)
.venv\Scripts\python -m pytest -q                          # pruebas
.venv\Scripts\mkdocs build --strict -f blog/mkdocs.yml     # blog (reporte técnico)
.venv\Scripts\python -m src.m1_demanda.sintetico           # serie sintética de M1 (solo desarrollo)
```
`export`, `figures` y `notebooks` (sin `--config`) recorren lo que exista y omiten lo que falta.
`mkdocs build` imprime un aviso informativo de Material sobre MkDocs 2.0; se silencia con `NO_MKDOCS_2_WARNING=1`
(PowerShell: `$env:NO_MKDOCS_2_WARNING = "1"`).

### Se habilita cuando el dueño entrega su tarea
Las configs (`configs/`) las crea cada dueño en su tarea; hasta entonces estos comandos responden «pendiente».

| Comando | Qué hace | Config | Dueño (ID) |
| --- | --- | --- | --- |
| `run.py m1-datos --config configs/m1/datos.yaml` | crudo → `data/processed/m1` | `configs/m1/datos.yaml` | Daniel (DA-3) |
| `run.py m1-eda --config configs/m1/datos.yaml` | análisis descriptivo (plantilla común) | `configs/m1/datos.yaml` | Camila (CA-4) |
| `run.py m1 --config configs/m1/demo.yaml` | demo M1 (< 2 min, CPU); con `base.yaml`, M1 completo (30 semillas) | `configs/m1/{demo,base}.yaml` | Andrés (AN-5) |
| `run.py m1-hpo --config configs/m1/hpo.yaml` | búsqueda Optuna | `configs/m1/hpo.yaml` | Andrés (AN-4) |
| `run.py m1-operacion --config configs/m1/operacion.yaml --set operacion.ocupacion_objetivo=0.8 --set operacion.cuantil=0.9` | dimensionamiento de la operación | `configs/m1/operacion.yaml` | Camila (CA-3) |
| `run.py m2-datos` | crudo → `data/processed/m2` | `configs/m2/` | José (JO-1) |
| `run.py m2-eda` | análisis descriptivo | `configs/m2/` | José (JO-2) |
| `run.py m2-hpo` | búsqueda Optuna | `configs/m2/` | José (JO-5) |
| `run.py m2` | demo o completo según la config | `configs/m2/` | José (JO-6) |
| `run.py m2-alertas` | política de alertas | `configs/m2/` | José (JO-8) |
| `run.py m3-datos` | datos → `data/processed/m3` | `configs/m3/` | Juan José (JJ-1) |
| `run.py m3-eda` | análisis descriptivo | `configs/m3/` | Juan José (JJ-2) |
| `run.py m3`, `run.py m3-hpo` | demo o completo; búsqueda Optuna | `configs/m3/` | Juan José (JJ-5) |

`export` (modelos → `app/public/model/{m1,m2,m3}/` + casos de paridad) y `figures` (regenera las figuras desde `results/`)
reciben sus módulos de cada dueño; `notebooks` (`.py` → `.ipynb` ejecutado en modo demo) espera los notebooks. La app
(ver «App en local») ya levanta con datos de juguete; el blog en vivo (`mkdocs serve -f blog/mkdocs.yml`) llega después.

## App en local
La app (`app/`) es un sitio estático de Next.js: los modelos corren en el navegador y no necesita internet ni servidor. Requiere
Node 22. Un solo comando para levantarla (tras instalar una vez):

```bash
npm --prefix app ci          # instala las dependencias con las versiones fijas (solo la primera vez)
npm --prefix app run dev     # http://localhost:3000
npm --prefix app test        # pruebas (vitest)
npm --prefix app run build   # sitio estático en app/out
```
Los archivos de los modelos viven en `app/public/model/{m1,m2,m3}/` y sus contratos (con un comentario por campo) en
`app/lib/contratos.ts`. Los `.wasm` de onnxruntime-web se sirven desde la propia app (`app/public/ort/`, copiados de
`node_modules/onnxruntime-web/dist`; si se cambia la versión de onnxruntime-web hay que volver a copiarlos).

**Datos de juguete (DA-5).** Mientras llegan los modelos reales, `app/public/model/` trae archivos ficticios con
`"juguete": true` y cada página lo avisa. Se regeneran (semilla fija, mismo resultado) con:

```bash
.venv\Scripts\python scripts/generar_juguetes_app.py     # reescribe app/public/model/{m1,m2,m3}
.venv\Scripts\python -m pytest -q tests/test_juguetes_app.py   # incluye la paridad ONNX vs. PyTorch
```
Los dueños de cada módulo reemplazan esos archivos con el mismo esquema y `"juguete": false`.

## Pruebas

```bash
.venv\Scripts\python -m pytest -q
```
Las pruebas lentas llevan el marcador `lento`; la CI corre `pytest -q -m "not lento"`.

## Semillas
Semilla efectiva = `base_seed + run_id` (`src/comun/seeds.py`); cada config declarará su `base_seed` cuando
el dueño la entregue (las tareas de la tabla de arriba).
