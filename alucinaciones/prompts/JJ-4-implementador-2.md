# JJ-4 — prompt del orquestador (Opus 5.5) al implementador (Sonnet), 2.ª vuelta, 2026-11-27

El verificador-matematico (R1) RECHAZÓ JJ-4 por un hallazgo bloqueante, que confirmé:

**H1. La factorización elegida por la búsqueda es la solución trivial X = Y = 0.** En `models/m3/mf_als.npz`, max|X| = 6,4e-23 y
max|Y| = 1,3e-23; la pérdida final es (1 + α)·1 066, la de X = Y = 0. Derivación (Z = XYᵀ, σ = σ_max(P_train) = 2,871): como
⟨P, Z⟩ ≤ σ‖Z‖_* y ‖Z‖_* ≤ ½(‖X‖² + ‖Y‖²), L(X, Y) − L(0, 0) ≥ (λ − (1 + α)σ)(‖X‖² + ‖Y‖²), así que si λ > (1 + α)σ el único
mínimo global es 0. Los ensayos 1, 3, 6, 11, 12, 14, 16 y 18 cumplen λ > (1 + α)·2,871 y colapsan; los 5 mejores (3, 14, 18, 11,
6) son todos colapsados: sus listas salen del residuo numérico de una iteración de potencias (por eso empatan 3, 14 y 18). El
rango λ ∈ [1e-3, 1e2] lo propuse yo en el primer prompt: el error es mío y tuyo por no detectar el colapso.

## Corrección (prueba primero)
1. **Espacio de λ** en `configs/m3/hpo.yaml`: tope superior `regularizacion` = 5.0 (rango [1e-3, 5.0], log). Comenta en el YAML
   la cota: con α ≥ 1 (mínimo del rango) y σ_max(P_train) medido solo con train, (1 + α)σ_max ≥ 2·σ_max ≈ 5,74 > 5,0, de modo que
   ningún punto del espacio está en la región donde X = Y = 0 es el único mínimo; que la cota es suficiente, no necesaria, y por
   eso existe además la guarda del punto 2. [PROPUESTO por el orquestador, a decidir por Juan José]. Ajusta también los
   hiperparámetros de respaldo de `base.yaml` si quedaran fuera de esa región segura (hoy 16, 0,1, 10, 10: está bien, compruébalo).
2. **Guarda de degeneración**: `MFImplicitaALS` expone tras `ajustar` un atributo (p. ej. `degenerado: bool` y
   `max_abs_puntaje: float` = max |x_uᵀ y_i| sobre usuarios de train × catálogo); `degenerado` = max_abs_puntaje <
   `mf_als.tolerancia_degenerado` (clave nueva en `base.yaml`, p. ej. 1e-8, comentada). En `hpo.py`, un ensayo degenerado se
   registra con estado «degenerado» (p. ej. `optuna.TrialPruned` o valor excluido) y **nunca puede ser el mejor**; si todos son
   degenerados, error claro. En `experimento.py`, si la MF final queda degenerada en cualquier semilla, error claro (no se
   reportan resultados de una factorización nula). `hpo_ensayos.json` dice por ensayo si fue degenerado y cuenta cuántos lo fueron.
   `n_configuraciones_busqueda` sigue contando todos los ensayos entrenados (presupuesto real).
3. **Pruebas nuevas** en `tests/test_metricas_m3.py`:
   - en un ejemplo pequeño con λ > (1 + α)·σ_max(P) la MF queda degenerada y el detector lo marca; con λ pequeño, no;
   - la búsqueda nunca elige un ensayo degenerado (p. ej. con un espacio forzado que incluya ambos regímenes);
   - el experimento falla si la configuración final es degenerada;
   - con los datos reales (skipif si faltan): el tope de λ de `hpo.yaml` es < (1 + α_min)·σ_max(P_train), con σ_max calculado
     SOLO con las interacciones de train (`scipy.sparse.linalg.svds` o `np.linalg.norm(·, 2)` de la matriz densa 858 × 1 000).
4. **n_parametros (observación H5)**: deja (n_usuarios_train + n_catálogo)·f como cifra principal y agrega en
   `summary.json` (bloque del modelo) `n_parametros_con_datos` = (n_usuarios_train + n_destinos_con_train)·f, explicando en el
   docstring que las filas de Y de los destinos sin train son 0 por construcción.
5. **Regenera** (en este orden) y pega la salida real: `run.py m3-hpo --config configs/m3/hpo.yaml`, `run.py m3 --config
   configs/m3/base.yaml`, `run.py m3 --config configs/m3/demo.yaml` (con tiempo), `run.py m3 --config configs/m3/demo.yaml --set
   evaluacion.k=3`, `pytest -q tests/test_metricas_m3.py tests/test_fuga_m3.py` y `pytest -q -m "not lento"`.
   Comprueba e informa: max|X|, max|Y| y max|XYᵀ| de la MF final; cuántos ensayos degenerados hubo; el mejor ensayo y sus
   parámetros; la nueva tabla por modelo y K (P / R / NDCG / cobertura, media ± desviación) frente al aleatorio analítico.

Mismas reglas de la primera vuelta (sin commits, sin tocar archivos compartidos, sin librerías nuevas, sin los textos prohibidos
por la guarda estática). No toques el blog.
