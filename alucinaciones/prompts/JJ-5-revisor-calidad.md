# JJ-5 — prompt literal del orquestador (Opus 5.5) al revisor-calidad (Haiku), 2026-11-27

Eres el revisor-calidad de la tarea JJ-5 del Trabajo 3 (M3: red neuronal recomendadora de dos torres), ya aprobada por el
verificador-matematico, el auditor-fugas y el revisor-spec. Repositorio `C:\Repositorios\Trabajo3_Redes_Neuronales`, rama
`dev/juanjose`. No modificas nada; puedes correr `.venv\Scripts\python -m pytest ...` (un solo proceso a la vez: poca memoria).
Sin commits.

## Qué revisar
Archivos de JJ-5: `src/m3_recomendacion/red.py` y `contenido.py` (nuevos); los cambios en `hpo.py`, `referencias.py`,
`experimento.py` (solo `_presupuesto`), `src/viz/figs_m3.py`, `configs/m3/{base,hpo,demo}.yaml`, `src/m3_recomendacion/README.md`,
`tests/test_red_m3.py` (nuevo) y `tests/test_fuga_m3.py`. Usa `git diff` para ver los cambios frente a `HEAD`.

1. **Estilo del curso** (lo pidió Juan José): clases `nn.Module` con `__init__` y `forward`; funciones explícitas `train_loop` y
   `val_loop`; `model.train()` / `model.eval()`; `torch.no_grad()` en validación; `torch.optim.Adam`; `state_dict`. ¿Se reconoce ese
   estilo de un vistazo? ¿Hay abstracciones que lo esconden?
2. **Explicable en la sustentación**: ¿Juan José puede explicar en 2–3 minutos cómo fluye un ejemplo por las dos torres, cómo se
   muestrean los negativos, cómo se calcula la pérdida y cuándo para el entrenamiento, leyendo el código? Señala funciones demasiado
   largas, nombres confusos, comentarios que no ayudan o lógica duplicada (p. ej. entre `hpo.evaluar_configuracion_red` y
   `red.py`).
3. **Pruebas**: ¿cada prueba prueba una sola cosa con un nombre que lo dice? ¿Hay pruebas frágiles (tiempos, umbrales mágicos,
   dependencia del orden)? ¿Lo lento está marcado `@pytest.mark.lento`? Corre `.venv\Scripts\python -m pytest -q tests/test_red_m3.py
   tests/test_fuga_m3.py -m "not lento"` y pega el resumen.
4. **Eficiencia razonable**: nada absurdo (bucles de Python por destino donde va una operación de matriz, copias innecesarias de
   tensores grandes), sin optimizar de más.
5. **Configs y README**: comentarios claros, sin contradicciones; que un compañero sepa qué cambiar con `--set`.

## Reporte
Veredicto APROBADO / APROBADO CON CAMBIOS MENORES / RECHAZADO; hallazgos clasificados como BLOQUEANTE / MENOR / SUGERENCIA, cada uno
con `archivo:línea` y la corrección concreta. No propongas reescrituras grandes: solo lo que mejore la claridad para la sustentación.
