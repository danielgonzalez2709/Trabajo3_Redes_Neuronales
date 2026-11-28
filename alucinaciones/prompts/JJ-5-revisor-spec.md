# JJ-5 — prompt literal del orquestador (Opus 5.5) al revisor-spec (Sonnet), 2026-11-27

Eres el revisor-spec de la tarea JJ-5 del Trabajo 3 (M3: red neuronal recomendadora de dos torres). Repositorio
`C:\Repositorios\Trabajo3_Redes_Neuronales`, rama `dev/juanjose`. Revisas que la implementación cumpla EXACTAMENTE el Spec y el
enunciado, ni más ni menos. No modificas nada; puedes correr `.venv\Scripts\python` para leer JSON y correr pruebas (un solo proceso
de Python con torch a la vez: la máquina tiene poca memoria). Sin commits.

## Fuente de verdad
- `docs/spec/SPEC.md`: §0, §4.1 (comandos; claves de cambio en vivo de M3: `modelo.dim_embedding`, `modelo.negativos_por_positivo`,
  `perdida.tipo`, `evaluacion.k`, y `semillas.n`), §5.7, §5.8 (contrato de la app: dos torres lineal/MLP, `torre_usuario` con capas
  `W` salida × entrada, `activacion` ∈ {relu, ninguna}, puntaje producto punto + sesgo), §5.9 (resultados), §6 (comparación
  justa), §7.1, y el Anexo «Módulo 3» (tarea 5, fundamentación), «Aplicación web», «Regla de comparación justa» y «Figuras mínimas
  comunes» (Entregables → 1).
- `docs/spec/partes/juanjose.md` §3.0 (contrato con la app) y §3.2: D15–D19 y «Implementación de JJ-5» [DECIDIDO, Juan José, 27-nov].
- Contrato ejecutable de la app: `app/lib/contratos.ts` (validadores M3, ~737–990) y `app/lib/recomendar.ts`.

## Qué revisar
1. **Tarea 5 del Anexo**: recomendador neuronal de dos torres que usa al menos una variable de contenido (usuario: preferencias;
   destino: tipo) y justifica dimensión de embeddings, muestreo de negativos y pérdida (en `blog/secciones/07-m3-recomendacion.md`,
   sección «### Red neuronal de dos torres», y en el código/config).
2. **D15–D19 + «Implementación de JJ-5»** contra `src/m3_recomendacion/red.py`, `contenido.py`, `hpo.py` (`buscar_red`,
   `evaluar_configuracion_red`, `_sugerir`), `experimento.py` (solo el reordenamiento de `_presupuesto`), `referencias.py`
   (registro de `red`), `configs/m3/{base,hpo,demo}.yaml`. Señala cualquier cosa de más o de menos.
3. **Núcleo §5.9 y §6**: `results/data/m3/summary.json` (bloque `red`: métricas con media/desviación/mejor/peor, `n_parametros`,
   `n_configuraciones_busqueda` = 20, `tiempo_total_s`, `device`, `evidencia` con la huella de la partición),
   `semillas/red_seed<k>.json` (30), `curvas/red.json` (pérdida de train y val por época, `epoca_parada`), `arquitectura/red.json`
   (capas, formas, activaciones, parámetros), `hpo_ensayos.json` (familias `mf_als` y `red`, 20 ensayos cada una).
4. **Figuras comunes** del Anexo para la red final, en `blog/docs/figures/m3/` (`red_arquitectura.png`, `red_curvas.png`,
   `busqueda_m3.png`, `cajas_m3.png`; míralas): arquitectura con capas, dimensiones, activaciones y parámetros; curvas con la
   parada temprana señalada; desempeño en validación de las configuraciones probadas; comparación de modelos con la variabilidad de
   las 30 semillas. Que el blog las numere, les ponga título y fuente y las cite en el texto (sin figuras huérfanas).
5. **Claves de §4.1**: comprueba (lee `tests/test_red_m3.py` y, si quieres, corre `.venv\Scripts\python run.py m3 --config
   configs/m3/demo.yaml --set semillas.n=1 --set modelo.dim_embedding=8`) que `modelo.dim_embedding`,
   `modelo.negativos_por_positivo`, `perdida.tipo`, `evaluacion.k` y `semillas.n` funcionan con `--set` sin editar código; y que la
   limitación documentada (con `base.yaml` el mejor ensayo va encima de los bloques, hay que agregar `--set
   red.hiperparametros_desde=config`) está escrita donde un usuario la vea.
6. **Exportable según el contrato M3 de la app**: ¿la torre de usuario con índice 0 es una secuencia de `Linear` con ReLU / sin
   activación que se puede volcar como `torre_usuario`? ¿(v_i, b_i) de cada destino se pueden precalcular como `embedding` y
   `sesgo`? ¿`models/m3/red.json` trae lo necesario (orden de las columnas one-hot de preferencias, d, mapas de id)? No hay que
   exportar todavía (es JJ-7); solo que el diseño lo permita.
7. **Comparación justa**: misma partición (huella), mismo objetivo y presupuesto de búsqueda (20) para la red y la MF, 30 semillas
   `base_seed + 0…29`, tiempos y parámetros reportados también para las referencias.

## Reporte
Veredicto APROBADO / RECHAZADO; tabla requisito → dónde se cumple (`archivo:línea`) → cumple / no cumple / parcial; desvíos del Spec
(de más o de menos) con la corrección exacta; y lo que deba decidir Juan José.
