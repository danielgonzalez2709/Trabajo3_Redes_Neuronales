## Reproducibilidad

<!-- borrador DA-9a (redactor-tecnico, Sonnet); pendiente de revisión de Daniel (DA-9). Describe lo que funciona al 2026-11-24; lo que falta está marcado con «pendiente». -->

El enunciado exige un repositorio que se pueda clonar y ejecutar sin depender de internet ni de servicios externos. Esta sección
dice cómo instalar el entorno, qué comandos funcionan hoy, cómo se fijan las semillas, qué datos van en el repositorio y cómo se
reconstruyen los que no, y qué verifica la integración continua (README del repositorio y núcleo §7.1 del Spec).

### Instalación

El proyecto fija Python 3.12 y las versiones exactas de todas las dependencias en `requirements.txt` (generado con `pip freeze`,
incluye las transitivas). En Windows (PowerShell o Git Bash):

```bash
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Dos cuidados que salieron de la revisión de DA-1 (sección «Uso de IA»):

- **Clonar en una ruta corta**, por ejemplo `C:\proy\Trabajo3_Redes_Neuronales`. En una ruta profunda `pip install` falla por el
  límite de 260 caracteres de Windows, porque algunos paquetes traen rutas muy largas. La alternativa es habilitar las rutas largas
  de Windows (`LongPathsEnabled`, requiere administrador y reiniciar la sesión).
- **Usar siempre `.venv\Scripts\python`** (o activar el entorno). El `python` del PATH puede ser otra versión, por ejemplo 3.13,
  y no la 3.12 que fija el proyecto.

En Linux, la rueda de torch de PyPI trae CUDA (varios GB), así que primero se instala la de CPU y luego el resto, que es lo mismo
que hace la integración continua:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install -r requirements.txt
```

En macOS la rueda de PyPI ya es de CPU y el primer `pip` se puede omitir. Con GPU NVIDIA es opcional reinstalar torch desde
pytorch.org; las demos están pensadas para CPU. La aplicación web necesita Node 22.

### Comandos que funcionan hoy

```bash
.venv\Scripts\python run.py --help                              # lista de subcomandos
.venv\Scripts\python -m pytest -q                               # pruebas
.venv\Scripts\python -m mkdocs build --strict -f blog/mkdocs.yml   # este reporte
.venv\Scripts\python -m src.m1_demanda.sintetico                # serie sintética de M1 (solo desarrollo)
.venv\Scripts\python run.py m1-datos --config configs/m1/datos.yaml   # crudo → data/processed/m1 (sin red)
npm --prefix app ci && npm --prefix app run dev                 # la app en http://localhost:3000
```

`mkdocs build` imprime un aviso informativo de Material sobre MkDocs 2.0 que se silencia con `NO_MKDOCS_2_WARNING=1`. Los
parámetros de cada comando se cambian con `--set clave.subclave=valor` (repetible) o en su archivo de `configs/`, sin editar
código; una clave inexistente es un error. Cada comando imprime la configuración resuelta y el tiempo total. Un subcomando cuyo
módulo aún no existe responde `pendiente: <dueño> (<tarea>)` y sale con código 2.

<!-- pendiente: comandos de M1 (modelos, búsqueda, operación), M2 y M3 con su demo de menos de 2 minutos: los habilita cada dueño al entregar su tarea (tabla de comandos del README). -->

### Semillas

La semilla efectiva de cada corrida es `base_seed + run_id` (`src/comun/seeds.py`). El código con numpy recibe su propio
`np.random.Generator` por corrida (`make_rng`) y está prohibido `np.random.seed` global; el código con PyTorch fija `torch` y
`random` con `fijar_semillas(seed)` y recibe el generador de numpy de esa misma semilla, de modo que todo lo aleatorio de una
corrida sale de un único número. Cada resultado documenta la semilla efectiva. La configuración final de cada red se entrena con
30 semillas (`base_seed + 0` a `base_seed + 29`, núcleo §6). La construcción de las series de M1 no usa números aleatorios: su
configuración (`configs/m1/datos.yaml`) no tiene `base_seed`.

<!-- pendiente: `base_seed` de cada módulo (lo declara cada dueño en su config) -->

### Datos: qué va en el repositorio y cómo se reconstruyen

Los datos que usan los modelos van **en el repositorio** para que ningún experimento descargue nada. Los datos crudos de M1 no
se versionan (son pesados); su origen queda registrado en `data/fuentes.md` con URL, fecha, licencia, SHA-256 y tamaño:

| Qué | Dónde | ¿Versionado? |
|---|---|---|
| Series diarias de las 6 rutas, detalle por tipo de despacho y clase, marcas de anómalos, rutas, resumen, DIVIPOLA, conteo de registros | `data/processed/m1/` | Sí |
| Ficha, calidad y diccionario de M1 | `results/data/m1/eda/` | Sí |
| Descargas mensuales de las 6 rutas (36 archivos `AAAA-MM.parquet`) y metadatos de la fuente | `data/raw/m1/` | No (se reconstruyen) |

Para reconstruir M1 desde la fuente hace falta red, y solo para este paso. `scripts/descargar_m1.py` es el único código del
proyecto que usa internet:

```bash
.venv\Scripts\python scripts/descargar_m1.py divipola
.venv\Scripts\python scripts/descargar_m1.py descargar --rutas 11001-76001,76001-11001,11001-15759,15759-11001,52001-52356,52356-52001 --desde 2021-01-01 --hasta 2023-12-31
.venv\Scripts\python scripts/descargar_m1.py contar --rutas 11001-76001,76001-11001,11001-15759,15759-11001,52001-52356,52356-52001 --desde 2021-01-01 --hasta 2023-12-31
.venv\Scripts\python run.py m1-datos --config configs/m1/datos.yaml    # sin red: arma las series
```

La descarga agrega en el servidor con SoQL (`group by`), nunca baja el conjunto completo, y se hace mes a mes y es reanudable
(`data/fuentes.md`). Además de `divipola`, `descargar` y `contar`, el script tiene el subcomando `ranking`, que reproduce la
muestra de 36 días con la que se escogieron las rutas. Cada consulta queda en un registro (`data/raw/m1/consultas_log.jsonl`) y los
SHA-256 de los archivos descargados quedan en `results/data/m1/eda/ficha.json` y `data/processed/m1/resumen_datos.json`.

Una advertencia honesta: el conjunto de datos.gov.co se sigue actualizando (`DA-2_fuentes_m1.md` §5), así que una descarga nueva podría
no dar los mismos bytes. Las cifras de este reporte corresponden a la consulta del 24 de noviembre de 2026; los SHA-256 permiten
comprobar si coinciden.

<!-- revisar: Daniel — confirma que reconstruir con una descarga nueva puede diferir (no se probó una segunda descarga). -->

### Integración continua

El repositorio tiene dos flujos de GitHub Actions (`.github/workflows/`):

- `ci.yml`, job `pruebas`, en cada pull request y en cada push a `main`: instala Python 3.12 y las dependencias fijadas, corre
  `pytest -q -m "not lento"` y, para la app, `npm ci`, `npm test` y `npm run build`. Es un check obligatorio para fusionar a `main`
  (`docs/MEMORIA.md`).
- `blog.yml`: cuando cambia `blog/` en `main`, construye este reporte con `mkdocs build --strict` y lo publica en GitHub Pages.

Las pruebas incluyen la del hook del reporte (`tests/test_blog.py`), que hace fallar el build si una figura o tabla no tiene
título o fuente, si no se cita en el texto, si una referencia cruzada no existe o si una cita no está en `references.bib`, y la
prueba de que los experimentos no usan la red (`tests/test_no_network.py`).

### Lo que falta por verificar

Al 2026-11-24 aún no se ha probado el clon limpio en una máquina distinta a la de desarrollo ni existen las demos de los modelos; esos puntos se completan al cierre.

<!-- pendiente: clon limpio en una máquina distinta a la de desarrollo (JJ-11), demos de cada módulo en menos de 2 minutos medidas en CPU, modelos entrenados guardados para que la app y las figuras no reentrenen, e historial de commits de las cinco cuentas. Hoy no existen todavía. -->
<!-- pendiente: enlaces definitivos a la aplicación publicada y al video promocional -->
