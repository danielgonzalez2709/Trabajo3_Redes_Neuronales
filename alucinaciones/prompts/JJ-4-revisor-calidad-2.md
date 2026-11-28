# JJ-4 — prompt del orquestador (Opus 5.5) al revisor-calidad (Haiku), 2.ª vuelta, 2026-11-27

Tu primera revisión de JJ-4 fue RECHAZADO con 2 bloqueantes (1: el arnés trataba `"mf_als"` como caso especial; 2: `main` de ~120
líneas) y 13 observaciones. El implementador refactorizó (resultados idénticos, comprobado): `Recomendador` con `diagnosticos()`,
`guardar(...)` y `descripcion_frios`; registro `hpo.BUSQUEDAS`; una sola regla de presupuesto e hiperparámetros por modelo
(`cfg[nombre]`); `main` partido en funciones; `metricas_por_grupo.json` con `resumir_semillas`; limpieza de `semillas/` por modelo;
validaciones de N_u y grupos vacíos; `objetivo_nombre`; pruebas de errores; YAML sin cifras a mano; pruebas redundantes quitadas;
`_ids`, renombres y `np.isin`. No se aplicaron, por decisión del orquestador: R4-5 (`models/m3/` SÍ se versiona, núcleo §4) ni
R4-12 (mover ayudantes de prueba; lo decide Juan José).

Mismas reglas (solo lees; no corras `run.py m3` con `base.yaml` ni `m3-hpo`: pisarían resultados versionados). Revisa
`src/m3_recomendacion/{metricas,referencias,experimento,hpo}.py`, `configs/m3/{base,hpo,demo}.yaml` y `tests/test_metricas_m3.py`.
Di si los dos bloqueantes quedaron cerrados (en particular: ¿JJ-5 puede agregar su red solo con una entrada en `MODELOS`, una en
`BUSQUEDAS` y un bloque de config, sin tocar `experimento.py`?) y el estado de cada observación. Corre
`.venv\Scripts\python -m pytest -q tests/test_metricas_m3.py tests/test_fuga_m3.py --durations=5`.
Informe: veredicto APROBADO / RECHAZADO; estado de cada hallazgo anterior; hallazgos nuevos (máx. 8) con archivo, línea y gravedad.
