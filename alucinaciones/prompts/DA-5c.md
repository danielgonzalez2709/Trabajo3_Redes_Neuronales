# Prompt DA-5c — implementador-web (Sonnet) — 2026-11-26 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/implementador-web.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`, al día con `main`; **no hagas
commit ni push**). No cambies versiones de dependencias. No toques `docs/` ni `blog/`. Usa `.venv\Scripts\python` para Python.

## Contexto
DA-5 dejó en `app/public/model/{m1,m2,m3}/` los archivos **de juguete** (`"juguete": true`) que genera
`scripts/generar_juguetes_app.py`. Los dueños de módulo van a reemplazar esos archivos por sus exportaciones **reales**
(`"juguete": false`, mismo esquema de `app/lib/contratos.ts`): Juan José (M3, JJ-7), José (M2, JO-9), Camila/Andrés (M1, CA-8/AN-8),
el sáb 28. Hoy varias pruebas suponen que lo servido es el juguete, así que **fallarían en cuanto llegue un modelo real**:
- `tests/test_juguetes_app.py::test_lo_versionado_coincide_con_lo_que_genera_el_script` compara `app/public/model` con el generador.
- `app/tests/contratos.test.ts` exige `juguete: true` en lo servido y arma casos inválidos con ids del juguete (p. ej.
  `actividad`, `D99`).
- `app/tests/recomendar.test.ts` usa preferencias del juguete (`actividad`, `gastronomia`, `playa`) y exige un usuario sin
  historial (el contrato §5.8 dice que *puede* no haberlo).
- `app/tests/dimensionar.test.ts` prueba la función de juguete con los casos de `m1/operacion.json` servido.
Además, el generador escribe por defecto en `app/public/model`: si alguien lo corre después de exportar, **borra el modelo real**.

## Lo que hay que hacer (prueba primero, luego código)
1. **El juguete pasa a ser un fixture.** El generador escribe por defecto en `app/tests/fixtures/juguete/` (misma estructura
   m1/ m2/ m3/, incluidos `modelo.onnx`, `ejemplos/` y `casos/`), versionado. `--salida app/public/model` sigue disponible para
   volver a servir el juguete a propósito; documéntalo en el docstring/ayuda del script y en `app/README.md` si existe una
   sección de modelos. Copia hoy el resultado también a `app/public/model/` (debe quedar idéntico a lo actual).
2. **Pruebas Python** (`tests/test_juguetes_app.py`):
   - La comparación «versionado == generador» se hace contra `app/tests/fixtures/juguete/`.
   - Nueva prueba sobre lo servido en `app/public/model/`: por módulo, todos sus archivos JSON tienen el mismo valor de
     `juguete` (no se mezcla juguete y real dentro de un módulo); y si un módulo servido es de juguete, es idéntico (con la
     tolerancia existente) al fixture, para detectar juguetes desactualizados. Un módulo real no se compara con nada aquí.
3. **Pruebas de la app** (`app/tests/`): separa dos grupos.
   - **Lógica y contratos** (rechazos, casos inválidos, funciones de juguete, `dimensionar` de juguete, usuario sin historial,
     selección con ids concretos): leen el **fixture** (agrega en `ayuda.ts` un `leerJuguete(ruta)` y lo que haga falta para el
     ONNX y las imágenes del fixture). Aquí sí se puede exigir `juguete: true`.
   - **Lo servido** (`leerModelo`, `app/public/model`): solo comprobaciones que valen para juguete **y** real: cada archivo
     cumple su contrato; M3: los `casos_paridad` se reproducen con `recomendarPerfil` y los ids de historial/top-K existen;
     M2: la paridad ONNX existente (si ya es genérica, déjala sobre lo servido); M1: contrato y coherencia de rutas. Nada de ids,
     preferencias o nombres del juguete en este grupo (toma ids del propio archivo, p. ej. la primera opción de la primera
     preferencia). Si el usuario sin historial no existe en lo servido, esa comprobación no aplica (`it.skipIf` o filtro).
   - Paridad de `dimensionar` contra el M1 **servido**: solo si `operacion.json` servido declara la función que implementa
     `app/lib/dimensionar.ts` (hoy `dimensionar_juguete`); si no, se salta con un mensaje que diga que la paridad real llega en DA-6.
4. **Nombres repetidos en M3** (aviso de Juan José: en el conjunto real los 1 000 destinos son 5 lugares repetidos 200 veces).
   En `app/lib/recomendar.ts` agrega una función pura `nombresParaMostrar(destinos): Map<id, string>`: si un `nombre` aparece
   más de una vez en la lista, se muestra `«Nombre (#id)»` (p. ej. `Taj Mahal (#178)`); si es único, solo el nombre. Pruebas
   con una lista hecha a mano (únicos, repetidos, mezcla). Úsala en `app/app/recomendacion/page.tsx` en lugar del `Map` actual
   (historial y recomendados).

## Aceptación
- `.venv\Scripts\python -m pytest -q` en verde; `npm test` y `npm run build` en `app/` en verde.
- **Simulación de un modelo real**: en una copia temporal (no en el repo), cambia los JSON de `m3/` servidos a `juguete: false`
  con otros ids de preferencias y sin usuario sin historial (los puedes generar con el mismo generador cambiando la semilla y
  los ids, o editándolos y recalculando los casos de paridad con la lógica de Python), apunta las pruebas a esa copia (p. ej.
  variable de entorno documentada solo para pruebas, o una función parametrizable) y muestra que el grupo «lo servido» y las
  pruebas Python pasan. Explica en el informe cómo lo verificaste; si no lograste simularlo, dilo.
- `git status` muestra solo los archivos de esta tarea.

## Informe (≤ 40 líneas)
Archivos cambiados, decisiones, cómo se simuló el modelo real y resultados de las pruebas (conteos). Nada inventado.
