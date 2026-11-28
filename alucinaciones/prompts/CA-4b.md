# Prompt CA-4b — implementador (Sonnet) — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/implementador.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). Python: `.venv/bin/python`.
**Prohibido hacer `git commit`, `git push` o cualquier operación que cambie el historial: Camila revisa todo antes.**

Contexto: `docs/spec/SPEC.md` §0, §3, §5.2, §5.12 y el Anexo («Módulo 1 → Tarea 3»); `docs/spec/partes/camila.md` §3.4; el
prompt original de la tarea `alucinaciones/prompts/CA-4a.md`. Calendario: `data/processed/m1/calendario.parquet` (esquema en
`data/fuentes.md`, sección «Calendario exógeno de M1»; columnas `vacaciones_escolares_<DIVIPOLA>` por ciudad).

## Tarea: correcciones de CA-4 pedidas por revisor-spec y revisor-calidad
Archivos tuyos (solo estos): `src/m1_demanda/eda.py` (puedes partirlo, ver R6), `tests/test_eda_m1.py`,
`src/viz/figs_m1_datos.py`, `tests/test_figs_m1_datos.py`, un posible `tests/conftest_m1.py` o módulo de utilidades de pruebas
propio, y las salidas en `results/data/m1/eda/` y `results/figures/m1/`. No toques `operacion.py`, `referencia.py`,
`calendario.py`, `src/comun/`, `run.py`, `configs/m1/datos.yaml` ni el Spec.

**Decisiones de Camila (26-nov):**
- **H-M1-3**: cada ruta usa la columna de vacaciones escolares de su **ciudad de origen** (`vacaciones_escolares_<origen_divipola>`),
  no la de Bogotá. Nulos de esa columna: excluir esos días de la comparación y decirlo en `resultado`.
- **H-M1-5**: se queda **solo con el perfil mensual**; corrige el texto «sin calendario externo» (el calendario ya existe; di que
  la hipótesis se mide por mes por decisión, y que `fin_de_anio` del calendario es la variable que usan los modelos).

**Bloqueantes (revisor-calidad), arreglar con prueba primero:**
- B1 `eda.py:187-188` (`tabla_objetivo`): mínimo/máximo con `con` vacío revientan (`NaN → int`). Devolver `None` y probar el borde.
- B2 `test_eda_m1.py:284`: assert sobre lista no vacía, no puede fallar. Reemplazar por una comprobación real.
- B3 `test_eda_m1.py:367-368`: prueba vacua sobre `matriz_entrada` inexistente. Borrar o reemplazar por una que verifique algo real
  (p. ej. que ninguna salida destinada a modelos contiene `anomalo`/`sin_registro`).
- B4 `test_eda_m1.py:134`: exigir que MICROBUS aparezca en 2023 con pct 0 (no vacío); `:302`: fijar un único resultado esperado.

**Recomendados a aplicar:**
- R1: razones con media 0 (`perfil_semanal`, `perfil_mensual`) y `tendencia_anual` con año previo en 0 → comportamiento explícito
  (NaN con aviso en hallazgos, o error claro) y prueba.
- R3: quitar código muerto (`nombres`, `del nombres`) y la generalidad falsa de `periodos` (constantes `SEMANAL = 7`, `ANUAL = 365`).
- R4: importar `REGLAS`/tipos de despacho (`ORIGEN`, `TRANSITO`) desde `src/m1_demanda/datos.py` en vez de duplicarlos.
- R5: umbrales con nombre (`UMBRAL_TRANSITO_PCT`, etc.) y textos de figuras/hipótesis generados desde los parámetros (nada de
  «~2,6 ciclos» o «desde 2021-06-01» escritos a mano).
- R6: separar cálculo de texto: una función por hipótesis (o grupo) que calcule, y el texto aparte; partir `eda.py` en dos módulos
  (tablas/secciones 3–4 y hipótesis/implicaciones 5–7), p. ej. `eda.py` + `eda_hipotesis.py`, manteniendo `main(cfg)` en `eda.py`.
- R7: quitar el `_CACHE` global y la importación cruzada entre archivos de prueba (fixtures con `scope="module"`).
- R10: rutas de salida por defecto relativas a la raíz del repo (como `calendario.py`, `RAIZ`), no al cwd.
- Menores si son baratos: `_hipotesis` con argumentos por nombre; `_fecha` renombrada para no chocar con la de `datos.py`;
  comprensiones anidadas ilegibles en `eda.py:666` y `figs_m1_datos.py:216-222` reescritas.

Mantén intactos `ficha.json`, `calidad.csv`, `diccionario.json` y todos los veredictos en `pendiente`. Regenera con
`.venv/bin/python run.py m1-eda --config configs/m1/datos.yaml` y `.venv/bin/python run.py figures`, y corre
`.venv/bin/python -m pytest -q`.

## Reporte
Archivos tocados; salida real de pytest y de los comandos; qué cambió en las cifras de H-M1-3 por ruta (antes con Bogotá, ahora
con la ciudad de origen); lo que no aplicaste y por qué. Nada de commits.
