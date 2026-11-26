# Prompt DA-7-verificacion — verificador-matematico (Opus) — 2026-11-26 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/verificador-matematico.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`). **Solo lectura**: no edites
archivos del repositorio; si necesitas scripts, escríbelos fuera del repo (carpeta temporal) y dilo.

## Qué verificar (DA-7: CAM en la app de M2; núcleo §3 «Interpretabilidad M2 en la app» y §5.6)
1. La derivación CAM ≡ Grad-CAM para una cabeza GAP + lineal, en el docstring de
   `tests/test_juguetes_app.py::test_m2_cam_coincide_con_grad_cam`: dedúcela tú de forma independiente (definición de
   Grad-CAM de Selvaraju et al.: α_k^c = (1/Z) Σ_ij ∂y^c/∂A^k_ij, mapa = ReLU(Σ_k α_k^c A^k), y^c antes del softmax) y di si
   la igualdad, el factor 1/(H·W) y el papel de la ReLU están bien. ¿Qué pasa con el sesgo de la capa lineal? ¿Y si la red
   tuviera algo entre la última convolución y el GAP (p. ej. BN o ReLU después de los mapas exportados)? Revisa en
   `scripts/generar_juguetes_app.py` de qué tensor salen exactamente los `mapas` del ONNX y si es el mismo sobre el que se
   calcula el gradiente en la prueba.
2. Que la prueba realmente demuestra la equivalencia (no es tautológica): gradiente con autograd, tolerancias, clases y casos.
   Córrela (`.venv\Scripts\python -m pytest -q tests/test_juguetes_app.py -k grad_cam`).
3. Las funciones de `app/lib/clasificar.ts` (`calcularCam` o equivalente, `normalizarCam`, `remuestrearBilineal`,
   `colorViridis`, `superponerCam`, `camParaPintar`): que el CAM use `pesos_cabeza` sin sesgo con el orden de ejes correcto
   (C·H·W aplanado, W de forma clases × canales), que la ReLU y la normalización solo afecten al pintado, que el remuestreo
   bilineal con centros de píxel sea correcto (verifica a mano un caso 2×2 → 4×4 y las esquinas), y que la mezcla sea
   (1−α)·imagen + α·color. Compara con un cálculo independiente en Python (numpy) sobre un caso de `app/public/model/m2/meta.json`.
4. Qué tiene que cumplir el modelo **real** de José (JO-7/JO-9) para que la equivalencia siga valiendo; formúlalo como una
   lista corta de condiciones verificables.

## Informe (≤ 40 líneas)
Veredicto: APROBADO / APROBADO CON OBSERVACIONES / RECHAZADO. Cada hallazgo con archivo:línea, la cuenta que lo demuestra y su
gravedad. Lista de condiciones para el modelo real. Nada inventado; si algo no pudiste comprobar, dilo.
