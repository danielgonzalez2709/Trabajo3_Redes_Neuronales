# JJ-5 — prompt literal del orquestador (Opus 5.5) al revisor-spec (Sonnet), 2.ª vuelta, 2026-11-27

Revisión acotada (repositorio `C:\Repositorios\Trabajo3_Redes_Neuronales`, rama `dev/juanjose`). No modifiques nada; puedes leer
JSON con `.venv\Scripts\python` (no corras experimentos ni pytest: lo hace el orquestador). Sin commits.

Decisión de Juan José (27-nov; `alucinaciones/prompts/JJ-5-decisiones.md` y `docs/spec/partes/juanjose.md` §3.2, «Configuración
final»): `configs/m3/base.yaml` usa `hiperparametros_desde: config` para la red y la MF, con los valores copiados del mejor ensayo.
Para no perder el presupuesto de búsqueda, el orquestador cambió `src/m3_recomendacion/experimento.py` (`_valor_en_config`,
`_presupuesto_config`, `ORIGEN_CONFIG_HPO`, docstring del módulo): con origen config, si `hpo_ensayos.json` (misma partición) trae la
familia y su `mejor.params` coincide EXACTAMENTE con los valores efectivos de la config, se reportan `n_ensayos` y `tiempo_total_s`
de la búsqueda; si no, 1 configuración y 0 s. `demo.yaml` fija `mf_als.hiperparametros_desde: hpo` (la demo sigue buscando la MF).

Revisa SOLO esto, contra el núcleo `docs/spec/SPEC.md` §6 (regla de comparación justa: presupuesto explícito `n_configuraciones_busqueda`
y `tiempo_total_s` por familia, también para las referencias) y §4.1 (claves en vivo de M3: `modelo.dim_embedding`,
`modelo.negativos_por_positivo`, `perdida.tipo`, `evaluacion.k`, `semillas.n`), y el Anexo «Regla de comparación justa»:
1. `git diff src/m3_recomendacion/experimento.py` y las pruebas nuevas en `tests/test_red_m3.py` (`test_config_igual_al_mejor_ensayo_...`,
   `test_config_distinta_del_mejor_ensayo_...`, `test_base_yaml_usa_config_...`, `test_la_demo_sigue_buscando_la_mf_en_vivo`): ¿la regla
   reporta el presupuesto real sin atribuir búsqueda a una config que no salió de ella? ¿Algún caso en que se atribuya mal?
2. `results/data/m3/summary.json`: `n_configuraciones_busqueda`, `tiempo_busqueda_s`, `tiempo_total_s` e `hiperparametros_origen` de los
   4 modelos, coherentes con `hpo_ensayos.json`.
3. `configs/m3/base.yaml` y `demo.yaml`: comentarios coherentes con el comportamiento; claves en vivo de §4.1 utilizables con los dos.
4. `blog/secciones/07-m3-recomendacion.md`: que lo que dice del presupuesto, los tiempos y el origen de los hiperparámetros coincida
   con `summary.json` (los tiempos se resincronizaron tras la última corrida) y que no afirme que `base.yaml` lee los hiperparámetros
   de la búsqueda si ya no es así.

Reporte: APROBADO / RECHAZADO; por punto, cumple / no cumple con `archivo:línea`; y la corrección exacta de lo que no cumpla.
