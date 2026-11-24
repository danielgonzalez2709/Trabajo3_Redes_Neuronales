# DA-3 — Auditoría de fugas de M1 (auditor-fugas, Opus) — 2026-11-24

Prompt: `alucinaciones/prompts/DA-3-revision.md` (R2). Scripts y salidas: `alucinaciones/evidencias/DA-3_auditoria_fugas/`
(se corren desde la raíz del repo con `PYTHONIOENCODING=utf-8 .venv\Scripts\python <script>`).
Supuestos de la auditoría: test = 2023-07-01..2023-12-31, orígenes cada 7 días, horizonte 30, MASE con ingenuo estacional de 7
días. Verificación previa: `marcar_anomalos` sobre la serie publicada reproduce exactamente `marcas_anomalos.parquet`.

**Conclusión:** ninguna fuga activa en los datos de DA-3/DA-4. Tres riesgos que el arnés de AN-1 y `tests/test_fuga_m1.py` deben
cerrar (ya están en el núcleo §5.3, v0.5): lista blanca de columnas, no excluir anómalos del test (y recalcular marcas con datos
≤ origen si se filtra el train) y rejilla de orígenes anclada al 2023-12-01.

| # | Riesgo | Evidencia | Veredicto | Recomendación |
|---|---|---|---|---|
| 1 | `anomalo` / marcas como variable de entrada | Prohibido en docstring, `NOTA_FUGA` y Spec, pero la columna está en `demanda_diaria` y `select_dtypes(number\|bool)` la devuelve (E6) | Sin fuga hoy; aislamiento solo por documentación | Lista blanca en `ajustar()` + `test_fuga_m1.py` (núcleo §5.3) |
| 2 | Marcas que miran el futuro usadas para filtrar el train | Con datos < 2023-07-01: 0 cambios en train y en los 22 orígenes de test (1a, 1b). Con todos los orígenes desde 2021-02-01: 93 de 148 tienen 1–8 días ≤ t con marca distinta (E1). Con umbral 4 MAD habría 124 marcas (E2) | Fuga pequeña y real si se filtra el train con las marcas publicadas; inocua con umbrales 10/8 | Recalcular marcas con datos ≤ t; no bajar umbrales sin rehacer la prueba |
| 3 | Excluir `anomalo` del test | Hoy 0 anómalos y 0 `sin_registro` en test (1c, 1d); con umbral 4 habría 10 | Sin fuga hoy; sesgo optimista posible | Evaluar sobre todos los días con registro (núcleo §5.3) |
| 4 | Umbrales elegidos mirando 2021–2023 | `configs/m1/datos.yaml` | Fuga de diseño menor sin efecto | Mencionarlo en el blog |
| 5 | `sin_registro` = 0 en rezagos y normalización | 82 días, todos en mayo de 2021; ninguno en test (2c). Normalizar log1p con esos ceros infla la desviación hasta 2,8× (E4) | Sin fuga; contaminación grave sin máscara | Ventanas desde el 2021-06-01; estadísticas sin `sin_registro` (núcleo §5.3) |
| 6 | Escala de MASE con ceros imputados | Razón 0,984–1,020 por ruta (2b) | Despreciable | Escala con train y sin `sin_registro` |
| 7 | Columnas no conocibles 30 días antes | Con `despachos` del día objetivo el MAE de test baja de 281 a 109 (52001-52356) y de 856 a 531 (15759-11001) (3a) | Fuga grave si se usa; hoy nadie lo hace | `despachos`/detalle solo como rezagos ≥ 30; composición por clase de train (núcleo §5.3 y §5.4) |
| 8 | Cambio de tránsito en 11001-15759 desde ~2022-11-08 | Pasajeros de tránsito/día 1.027 → 2.714 (train) → 3.125 (test); despachos casi iguales; MICROBUS en tránsito 30 → 293/día (E3). La inversa no cambia | Sin fuga; no estacionariedad (¿cambio de reporte? no verificado) | Indicadora de régimen solo con datos de train; discutir en el blog |
| 9 | Escala de MASE mezcla regímenes en 11001-15759 | Escala 392 antes y 780 después; MASE del ingenuo 1,56 vs. 1,18 con los últimos 12 meses (E5) | Sin fuga; infla el MASE de la ruta | [PROPUESTO] escala alternativa con los últimos 12 meses de train |
| 10 | El test no cubre el fin de año | Con orígenes 2023-07-01 + 7k, nadie pronostica del 26 al 31-dic-2023 (4d) | Riesgo para «temporada alta en prueba» | Anclar el último origen al 2023-12-01 (núcleo §5.3) |
| 11 | Anómalos que quedan en train/val tras 2021-06-01 | 2021-06-01 (Bogotá–Cali), 15759-11001 el 2023-05-21 (0 pasajeros con 214 despachos) y 22, 52356-52001 el 2023-01-01 | Sin fuga | Enmascarar `despachos_sin_pasajeros` en pérdida y validación |
| 12 | Rutas elegidas con miércoles de 2021–2023 | Criterio de completitud, no de demanda | Despreciable | Documentado |
| 13 | Versión de los datos | La fuente se actualizó el 3-may-2026; reportes tardíos posibles | No verificable | Limitación en el blog |

Candidatos a hallazgo de la cacería: ninguno (el código hace lo que dicen el docstring y el Spec).
