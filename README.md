# Trabajo 3 — Redes neuronales para series de tiempo, imágenes y recomendación

Tres módulos: M1 pronóstico de demanda y planeación de la operación (transporte intermunicipal), M2 clasificación de
conducción distractiva (imágenes) y M3 recomendación de destinos de viaje; más aplicación web, blog y video. Curso Redes
neuronales y algoritmos bioinspirados, UNAL 2026-02.

- Spec (fuente de verdad, con el enunciado en el Anexo): [`docs/spec/SPEC.md`](docs/spec/SPEC.md) · specs personales en
  [`docs/spec/partes/`](docs/spec/partes/) · tablero: [`docs/spec/PLAN.md`](docs/spec/PLAN.md)
- Estado actual: [`docs/MEMORIA.md`](docs/MEMORIA.md)
- Reporte (blog): pendiente
- Aplicación web: pendiente
- Video promocional: pendiente

## Instalación (Python 3.12)

Windows:

```bash
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

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
«pendiente: <dueño> (<tarea>)» y sale con código 2.

```bash
python run.py m1-datos --config configs/m1/datos.yaml      # crudo → data/processed/m1
python run.py m1-eda   --config configs/m1/datos.yaml      # análisis descriptivo (plantilla común)
python run.py m1       --config configs/m1/demo.yaml       # demo M1 (< 2 min, CPU)
python run.py m1       --config configs/m1/base.yaml       # M1 completo (30 semillas)
python run.py m1-hpo   --config configs/m1/hpo.yaml        # búsqueda Optuna
python run.py m1-operacion --config configs/m1/operacion.yaml --set operacion.ocupacion_objetivo=0.8 --set operacion.cuantil=0.9
python run.py m2-datos / m2-eda / m2 / m2-hpo / m2-alertas   # mismo patrón, configs/m2/
python run.py m3-datos / m3-eda / m3 / m3-hpo                # mismo patrón, configs/m3/
python run.py export       # modelos → app/public/model/{m1,m2,m3}/ + casos de paridad
python run.py figures      # regenera todas las figuras desde results/
python run.py notebooks    # .py → .ipynb y los ejecuta en modo demo
```
`--set clave.subclave=valor` es repetible; una clave inexistente es un error; las configs heredan con `hereda: base.yaml`.
Todos los parámetros se cambian así, sin tocar código. La app (`npm --prefix app run dev`) y el blog
(`mkdocs serve -f blog/mkdocs.yml`) llegan después: pendiente.

## Pruebas

```bash
python -m pytest -q
```
Las pruebas lentas llevan el marcador `lento`; la CI corre `pytest -q -m "not lento"`.

## Semillas
Semilla efectiva = `base_seed + run_id` (`src/comun/seeds.py`); `base_seed` está en cada archivo de `configs/`.
