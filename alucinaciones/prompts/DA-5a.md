# Prompt DA-5a — implementador-web (Sonnet) — 2026-11-24 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/implementador-web.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`; **no hagas commit ni push**).
Referencia para portar (solo lectura, app del Trabajo 2 del mismo equipo, Next.js estático en Vercel):
`C:\Users\danie\AppData\Local\Temp\claude\4dc77ad0ee14e84c\6f603fae-d809-443f-a910-1822e4048a3e\scratchpad\t2repo\app`
(lee también su `AGENTS.md`: esta versión de Next.js tiene cambios; consulta `node_modules/next/dist/docs/` antes de escribir).

Lee antes: `docs/spec/SPEC.md` §3 (filas App e Interpretabilidad M2), §5.3, §5.4, §5.6, §5.8, §8 y el Anexo («Aplicación web»);
`docs/spec/partes/daniel.md` §3.3 y la fila DA-5.

## Tarea DA-5 — esqueleto de la app con datos de juguete (la lógica real llega en DA-6, DA-7 y DA-8)
1. **`app/`** portada del Trabajo 2: `package.json` con las **mismas versiones fijas** (next, react, react-dom, typescript,
   vitest, @types) + `onnxruntime-web` (versión fija), `package-lock.json`, `next.config.mjs` con `output: "export"`,
   `tsconfig.json`, `vercel.json` (Root Directory = `app`), `.gitignore`, `app/layout.tsx`, `app/globals.css` y los componentes
   genéricos reutilizables (`Marco`, `Info`, `Segmentado`, `ControlNumerico`, `TarjetaResultado` o los que sirvan), sin nada
   del dominio de crédito del Trabajo 2. Mismo sistema visual del Trabajo 2, textos en español, usable en celular.
2. **Páginas** (rutas estáticas):
   - `/` Inicio: qué resuelve la app para la empresa de transporte, tarjetas a los 3 módulos y enlaces a reporte (blog:
     https://danielgonzalez2709.github.io/Trabajo3_Redes_Neuronales/), repositorio, video promocional y videos individuales
     (estos dos «pendiente», centralizados en `lib/enlaces.ts`).
   - `/demanda`: selector de ruta, gráfico SVG propio (sin librerías de gráficos) con la historia reciente, el pronóstico a 30
     días y la banda del cuantil elegido; controles de **ocupación objetivo** y **cuantil usado**; tabla por día de despachos,
     vehículos y conductores. La función de dimensionamiento de esta etapa es **provisional y de juguete** (la real es la de
     Camila, núcleo §5.4, y llega en DA-6): márcala así en el código y en la interfaz.
   - `/conduccion`: subir una imagen (o elegir un ejemplo), correr el ONNX en el navegador con `onnxruntime-web`, y mostrar la
     clase asignada, la probabilidad de cada clase, el control de umbral y la decisión de alerta (sin alerta / con alerta). El
     mapa de interpretabilidad (CAM) queda como espacio reservado con «llega en DA-7». Los archivos `.wasm` de onnxruntime se
     sirven **desde la propia app** (copiados a `public/`, con `ort.env.wasm.wasmPaths`), no desde un CDN: la app debe
     funcionar en local sin internet.
   - `/recomendacion`: elegir un usuario existente (ver su historial y su top-K) o armar un **perfil nuevo** desde una **lista
     de preferencias** seleccionables y ver un top-K; control de K. En esta etapa el top-K del perfil nuevo usa una regla de
     juguete marcada como tal.
   - Cada página muestra un aviso visible «Datos de juguete» cuando el JSON trae `"juguete": true`.
3. **Contratos de la app** en `app/lib/contratos.ts`: tipos TypeScript **y** funciones de validación (que fallen con mensaje
   claro) para cada archivo de `app/public/model/`. Propón esquemas concretos que cumplan §5.4, §5.6 y §5.8; como mínimo:
   - `m1/pronosticos.json`: `version`, `juguete`, `modelo`, `fecha_origen`, `horizonte`, `cuantiles` (p. ej.
     [0.5, 0.75, 0.9, 0.95]) y, por ruta: `ruta_id`, origen y destino (código y nombre), `ruta_regreso_id`, `historia` (últimos
     ~90 días) y `pronostico` (por día: `fecha`, `h`, `punto` y un valor por cuantil).
   - `m1/operacion.json`: parámetros por defecto, definición de los controles (clave, etiqueta, mínimo, máximo, paso, defecto,
     unidad) y `casos_paridad` (entrada → salida de la función de dimensionamiento).
   - `m2/meta.json` (+ `m2/modelo.onnx`): clases con su grupo de alerta, umbral por defecto, tamaño de entrada, media y
     desviación de normalización, nombres de las salidas del ONNX (`logits`, `mapas`), `pesos_cabeza` y `sesgo_cabeza` (para
     CAM en DA-7), imágenes de ejemplo y `casos_paridad`.
   - `m3/destinos.json`, `m3/usuarios.json` (historial y top-K precomputado) y `m3/perfil_nuevo.json` (lista de preferencias
     con opciones y lo necesario para recomendar a un perfil nuevo), con `casos_paridad`.
   Documenta cada esquema con un comentario por campo: estos contratos los usarán José, Juan José, Andrés y Camila.
4. **Datos de juguete** generados con un script Python **`scripts/generar_juguetes_app.py`** (usa `.venv\Scripts\python`):
   - M1 desde la serie **sintética** (`data/sintetico/m1/`), con un pronóstico ingenuo estacional y cuantiles empíricos simples.
   - M2: un `modelo.onnx` diminuto con la **misma forma** que tendrá el real (entrada RGB normalizada, salidas `logits` de 5
     clases y `mapas` de la última convolución, cabeza GAP + lineal), pesos aleatorios con semilla, exportado con
     `torch.onnx.export`; verifica con `onnxruntime` de Python que las probabilidades coinciden con PyTorch y guarda esos casos
     en `casos_paridad`. Las 5 clases con los nombres del enunciado y el grupo de alerta propuesto (conducción segura = sin
     alerta; el resto = con alerta) marcado como provisional. 2–3 imágenes de ejemplo **sintéticas** (generadas, no fotos
     reales de personas) en `public/model/m2/ejemplos/`.
   - M3: destinos y usuarios **ficticios** claramente marcados (`"juguete": true`), sin nombres de personas reales.
   - Todo con `"juguete": true`. Escribe en `app/public/model/{m1,m2,m3}/`.
5. **Pruebas** (`vitest`) en `app/tests/`: validación de los contratos contra los JSON de juguete y contra casos inválidos,
   la función provisional de M1 con sus casos de paridad, la regla de juguete de M3, y la lectura de `meta.json`. Además
   `tests/test_juguetes_app.py` (pytest) que regenere los juguetes en una carpeta temporal y compruebe la paridad ONNX vs.
   PyTorch.
6. **CI**: agrega a `.github/workflows/ci.yml`, en el mismo job `pruebas`, los pasos de la app como en el Trabajo 2
   (`setup-node` 22, `npm --prefix app ci`, `npm --prefix app test`, `npm --prefix app run build`).
7. `README.md`: sección «App en local» (`npm --prefix app ci` y `npm --prefix app run dev`) y cómo regenerar los juguetes.

## Aceptación
`npm --prefix app test` y `npm --prefix app run build` en verde; `.venv\Scripts\python -m pytest -q` en verde; `npm --prefix app
run dev` levanta y las 4 páginas cargan sus datos de juguete sin errores en consola (compruébalo con una petición HTTP a cada
ruta y a cada JSON; si puedes, en un navegador). Pega las salidas reales.

## Reglas
- Solo tocas `app/`, `scripts/generar_juguetes_app.py`, `tests/test_juguetes_app.py`, `.github/workflows/ci.yml` y la sección
  del README. No toques `docs/spec/` (los contratos se pasan al Spec después de la revisión).
- Nada de datos reales de personas; nada inventado presentado como real.
- No crees proyectos en Vercel ni despliegues: eso lo decide Daniel.

Entrega: archivos creados, esquemas propuestos (resumen), salidas reales, capturas si pudiste, dudas.
