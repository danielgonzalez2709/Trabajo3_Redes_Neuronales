# Prompt DA-7a — implementador-experto (Opus) — 2026-11-26 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/implementador-experto.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`; **no hagas commit ni push**). No
cambies versiones de dependencias. Solo tocas: `app/app/conduccion/`, `app/lib/clasificar.ts`, `app/lib/imagen.ts` (si hace
falta), componentes nuevos en `app/components/`, `app/tests/`, `scripts/generar_juguetes_app.py` y
`tests/test_juguetes_app.py` (solo para la prueba de Grad-CAM). No toques `docs/`, `blog/`, `notebooks/`, `configs/` ni
`app/public/model/` salvo regenerar el juguete con el generador si cambias su salida (y entonces también
`app/tests/fixtures/juguete/`, ver README). Otros agentes trabajan a la vez en `notebooks/`, `configs/notebooks/` y
`blog/secciones/08-app.md`: no los toques. Antes de escribir código de Next.js lee la guía que corresponda en
`app/node_modules/next/dist/docs/` (ver `app/AGENTS.md`).

## Tarea DA-7 (spec de Daniel §3.3 «Conducción»; núcleo §3 «Interpretabilidad M2 en la app» y §5.6)
Página de conducción: subir imagen → ONNX Runtime Web → probabilidad por clase, clase asignada, decisión de alerta con umbral
ajustable **y mapa CAM sobre la imagen**. Imágenes de ejemplo precargadas. En DA-5 el CAM se calcula
(`app/lib/clasificar.ts`, con paridad contra `meta.json`) pero **no se pinta**. Hoy se trabaja con el ONNX de juguete (misma
forma que el real de José: salidas `logits` (5) y `mapas` de la última convolución; cabeza GAP + lineal con
`pesos_cabeza`/`sesgo_cabeza` en `meta.json`).

1. **Pintar el CAM** sobre la imagen preprocesada (la que ve la red, `tamano_entrada`): CAM de la clase asignada y selector
   para ver el de otra clase; ReLU y normalización a [0, 1] por imagen solo para pintar (documéntalo); remuestreo bilineal del
   mapa H×W al tamaño de la imagen; mapa de color perceptualmente uniforme, legible en modo claro y oscuro, con opacidad
   ajustable y leyenda («más influencia» / «menos»). Canvas accesible (texto alternativo con la clase mostrada). Sin
   dependencias nuevas.
2. **Funciones puras** en `app/lib/` (sin DOM) para: ReLU + normalización, remuestreo bilineal del mapa y mapa de color.
   Pruebas con casos hechos a mano (mapa constante, un solo máximo, mapa todo negativo → todo cero sin NaN, esquinas del
   remuestreo).
3. **Equivalencia CAM ≡ Grad-CAM** (núcleo §3): en Python, con el modelo de juguete de PyTorch del generador, calcula Grad-CAM
   de verdad (gradiente del logit de la clase respecto a las activaciones de la última convolución con autograd; α = promedio
   espacial del gradiente; Σ α·A; ReLU) y comprueba que coincide (salvo el factor 1/(H·W) y la ReLU) con el CAM Σ w·A de
   `meta.json`/la app, para todas las clases de los casos de paridad. Escribe la derivación corta en el docstring de la prueba
   (con GAP, ∂y_c/∂A_k(i,j) = w_{c,k}/(H·W)). La prueba va en `tests/test_juguetes_app.py` y corre en CPU en < 10 s.
4. La UI existente (probabilidades, umbral, alerta, aviso de juguete) no se rompe; mantén la estética actual (CSS modules,
   variables de color) y que funcione a 375 px de ancho.

## Aceptación
- `.venv\Scripts\python -m pytest -q`, y en `app/`: `npm test` y `npm run build`, en verde.
- Prueba Grad-CAM vs. CAM en verde con tolerancia relativa ≤ 1e-5 después de la ReLU y la escala.
- `git status` solo con archivos de esta tarea.

## Informe (≤ 40 líneas)
Archivos, decisiones (mapa de color, normalización, remuestreo), la derivación en 3–5 líneas, resultados de pruebas (conteos)
y lo que no pudiste verificar (p. ej. el aspecto en el navegador). Nada inventado.
