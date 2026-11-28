# JJ-4 — prompt del orquestador (Opus 5.5) al implementador (Sonnet), 5.ª vuelta, 2026-11-27

R3 (revisor-spec) APROBÓ con observaciones; R4 (revisor-calidad) RECHAZÓ con 2 bloqueantes. Es una refactorización: **las
métricas, las listas y los factores deben quedar idénticos** (compruébalo contra una copia de `results/data/m3/` y `models/m3/`
hecha antes de empezar, en el scratchpad; solo pueden cambiar tiempos y el formato pedido abajo). Prueba primero donde aplique.

## Bloqueantes de R4
1. **El arnés trata `"mf_als"` como caso especial** (`experimento.py` ~223, 241, 247-249, 260, 275, 283-287: presupuesto de
   búsqueda, factores guardados, `es_mf`, origen de hiperparámetros) y usa `getattr(modelo, "degenerado", False)` /
   `hasattr(...)`. Si JJ-5 agrega `"red"` en `MODELOS`, heredaría `n_configuraciones_busqueda = 1`, no leería su familia de
   `hpo_ensayos.json` y su degeneración no se comprobaría. Diseño pedido:
   - El `Protocol` `Recomendador` gana `diagnosticos() -> dict` (lo que hoy son `degenerado`, `motivo_degenerado`,
     `max_abs_puntaje`, `n_parametros_con_datos`…; `{}` si no aplica) y `guardar(carpeta) -> list[Path]` (la MF guarda su npz/json;
     los demás, nada). El arnés llama a esos métodos para todos los modelos, sin nombres propios.
   - Un registro de búsquedas por nombre de familia (p. ej. `hpo.BUSQUEDAS = {"mf_als": buscar_mf}`) y la regla: un modelo con
     búsqueda toma sus hiperparámetros, `n_configuraciones_busqueda` y `tiempo_busqueda_s` de `familias.<nombre>` de
     `hpo_ensayos.json` (o de la búsqueda en el experimento si `busqueda.ejecutar_en_experimento`); uno sin búsqueda, 1 y 0. Una
     sola regla para todos (el `hiperparametros_desde` de la config se generaliza o se mueve a cada modelo, documentado).
   - Un modelo degenerado (`diagnosticos()["degenerado"]` verdadero) detiene el experimento con error claro, sea cual sea.
   - Prueba con un modelo espía **con búsqueda registrada** que confirme que el arnés le asigna su presupuesto, sus
     hiperparámetros y que comprueba su degeneración, sin tocar `experimento.py`.
2. **`main` de ~120 líneas**: pártelo en funciones de una responsabilidad (p. ej. `_contexto`, `_correr_modelo`, `_resumen_modelos`,
   `_bloque_frios`, `_escribir_salidas`); `main` de ~20–30 líneas que se lea como el procedimiento. Igual para `hpo.buscar_mf`
   (`_validar_espacio`, `_familia`).

## Observaciones (aplícalas)
3. `metricas_por_grupo.json` (R3-4, R4-3): usa `metricas.resumir_semillas` (media, desviación, mejor, peor, n) en vez de calcular
   a mano.
4. `semillas/` (R3-2, R4-4): antes de escribir, borra `semillas/<modelo>_seed*.json` de cada modelo que se corre (solo de esos
   modelos), y pruébalo (correr con n = 3 y luego n = 2 deja exactamente 2 por modelo).
5. R4-6: validar N_u ≥ 1 con mensaje claro en los esperados analíticos; un grupo vacío no debe producir NaN en silencio (omitirlo
   con `n_usuarios = 0` o error claro; decide y documenta). Pruebas.
6. R4-7: guardar `objetivo_nombre` (p. ej. `"ndcg@5"`) en la familia y usarlo para imprimir, sin parsear texto.
7. R4-8: pruebas parametrizadas de los errores de `normalizar_k` (`[]`, `0`, `"3"`, `True`), espacio con claves faltantes o
   sobrantes, objetivo inválido, `hiperparametros_desde` (o su sustituto) inválido, y `evaluar_configuracion` sin columna `split`
   con mensaje claro (no `KeyError` pelado).
8. R4-9: en los YAML, no fijes «≈ 2,871» a mano: remite a `hpo_ensayos.json` → `familias.mf_als.cota_solucion_nula`. Una sola
   explicación larga de la cota (en el docstring de `referencias.py`); el resto, una línea que remita.
9. R4-10/11: elimina las pruebas redundantes o frágiles que señaló (la del demo con overrides que repite otra; la que repite el
   escaneo de `test_fuga_m3.py`; la de grep de «read_parquet») **solo si otra prueba cubre lo mismo**; quita el `if` que deja pasar
   en vacío (afirma siempre o explica); reescribe la expresión ilegible.
10. R4-13/14/15: helper `_ids(top, k)` en vez de repetir el `isinstance`; nombres explicables (`_plano` → `clave_metrica`,
    `glob` → `bloque`, `esperado` → `bloque_sha`…); vectoriza el acierto por lugar con `np.isin` o un vector de lugares; líneas
    ≤ 130 caracteres; sin líneas en blanco dobles dentro de clases.
- **No hagas**: R4-5 (`models/m3/` SÍ se versiona: núcleo §4 «models/{m1,m2,m3}/ modelos entrenados versionados»); R4-12 (mover
  ayudantes de prueba a otro módulo: toca `test_fuga_m3.py`/`test_datos_m3.py`; lo decide Juan José).

## Cierre
Regenera `m3-hpo` (hpo.yaml), `m3` (base.yaml), la demo (con tiempo) y la demo con `--set evaluacion.k=3`; compara con la copia
(métricas por semilla, `recomendaciones_prueba.parquet`, `mf_als.npz`: idénticos); `pytest -q -m "not lento"`. Pega la salida real
y lista lo que cambió en el formato de los JSON (para que el blog y JJ-5 lo sepan). Mismas reglas de siempre; no toques el blog.
