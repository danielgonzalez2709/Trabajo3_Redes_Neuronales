# JJ-5 — prompt literal del orquestador (Opus 5.5) al implementador-experto (Opus), 2.ª vuelta, 2026-11-27

Segunda vuelta de JJ-5. Mismas reglas que en tu primer encargo (`alucinaciones/prompts/JJ-5-implementador-experto.md`): prueba
primero, `.venv\Scripts\python`, sin internet, sin commits, solo tus archivos. La máquina tiene ~0,8 GB libres: un solo proceso de
Python con torch a la vez.

Estado: el orquestador ya corrió `m3-hpo` (red: mejor ensayo 18, NDCG@5 de validación 0,0067; MF idéntica a JJ-4), copió el mejor
ensayo a los bloques de `configs/m3/base.yaml`, corrió `run.py m3 --config configs/m3/base.yaml` (las 3 referencias dan métricas
idénticas a JJ-4), la demo (26 s), los 3 cambios en vivo y `run.py figures`. No vuelvas a correr `m3-hpo`.

El verificador-matematico aprobó con observaciones. Corrige:

1. **`personalizacion` (`red.py` ~541) no mide personalización del ranking.** s_ui = ⟨u, v̄⟩ + ⟨u, v_i − v̄⟩ + b_i: el término ⟨u, v̄⟩ es
   un desplazamiento propio de cada usuario que infla la desviación entre usuarios sin cambiar ningún orden (semilla 8: la medida
   más alta, 0,242, pero el mismo top-1 para 606/606 usuarios). Reemplázala por la desviación entre usuarios de la matriz doble
   centrada `E = S - S.mean(1, keepdims=True) - S.mean(0, keepdims=True) + S.mean()`, `personalizacion = E.std(axis=0).mean()`,
   y corrige el comentario («la parte de s_ui que cambia el orden: sin b_i ni el desplazamiento propio de cada usuario»).
   Agrega además dos diagnósticos que se reportan (no declaran degenerada la corrida): `fraccion_varianza_interaccion` (‖E‖²/‖S −
   S.mean()‖²) y `listas_top10_distintas` (número de listas top-10 distintas entre los usuarios del diagnóstico, catálogo completo),
   y `fraccion_mismo_top1` (fracción de usuarios cuyo top-1 es el top-1 más frecuente). Pruebas: una matriz con solo efecto de
   usuario + efecto de destino da personalización 0 y 1 lista distinta; una con interacción pura da > 0.
2. **`descripcion_frios` (`red.py` ~367):** que diga que los fríos reciben puntaje solo por su tipo (índice 0) y que **en la
   práctica** quedan por debajo de los destinos con train (se mide en `frios_por_lista`), sin afirmar que entran al top-K.
3. **Figuras (`src/viz/figs_m3.py`):** en `red_curvas.png` el eje de la pérdida repite la etiqueta «0,64» (usa más decimales) y la
   leyenda tapa la curva de validación (muévela fuera del área de datos o abajo); en `cajas_m3.png` la leyenda tapa un punto atípico
   arriba (muévela); en `cajas_m3.png` el eje de Recall@10 muestra 0,013 y 0,015 donde los ticks son 0,0125 y 0,0150 (usa 4
   decimales o ticks redondos).
4. Corre las pruebas de M3 (`tests/test_red_m3.py tests/test_fuga_m3.py tests/test_metricas_m3.py`), luego
   `.venv\Scripts\python run.py m3 --config configs/m3/base.yaml` (los diagnósticos cambian; las métricas de los 4 modelos deben
   quedar idénticas a las de ahora: compruébalo contra una copia de `results/data/m3/summary.json` hecha antes) y
   `.venv\Scripts\python run.py figures`.

Reporte: cambios (archivo:línea), salida real de las pruebas y de los comandos, comparación de métricas antes/después y los nuevos
diagnósticos de la red resumidos sobre las 30 semillas.
