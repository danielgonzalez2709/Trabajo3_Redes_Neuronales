# JJ-5 — prompt literal del orquestador (Opus 5.5) al auditor-fugas (Opus), 2026-11-27

Eres el auditor-fugas de la tarea JJ-5 del Trabajo 3 (M3: red neuronal recomendadora de dos torres). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales`, rama `dev/juanjose`. Auditoría adversarial: busca cualquier vía por la que
información de PRUEBA (o, para el entrenamiento de los pesos, de VALIDACIÓN) llegue a la red, a su búsqueda o a su parada
temprana. Usa `.venv\Scripts\python`. Sin commits. Puedes **agregar pruebas** en `tests/test_fuga_m3.py` si encuentras un hueco
sin cubrir (no cambies código de `src/`; si hay una fuga, repórtala con la prueba que la demuestra, fallando).
La máquina tiene poca memoria libre: no corras varios procesos de Python con torch a la vez.

## Reglas que se auditan
- CLAUDE.md: «M3 ninguna interacción de prueba en train. Preprocesamiento ajustado solo con train.»
- `docs/spec/partes/juanjose.md` §3.1 D8–D10 (D9: búsqueda y parada temprana con validación; modelos finales solo con train;
  toda estadística de interacciones solo con train; D10: candidatos) y §3.2 D15–D19 + «Implementación de JJ-5» (índices de id
  solo con train, «dropout de id», negativos uniformes sobre catálogo − train del usuario, ninguna popularidad en la red, guarda
  `AJUSTES_SIN_PRUEBA`).
- Núcleo `docs/spec/SPEC.md` §5.7 (ninguna interacción de prueba se usa para entrenar) y §6.

## Qué auditar
1. `src/m3_recomendacion/red.py`: ¿`ajustar` descarta prueba al entrar? ¿Los índices de id, el conjunto «con train» y los
   negativos salen solo de train? ¿Validación entra solo para la parada temprana (pérdida y NDCG@5 de validación), nunca a los
   gradientes, ni a los negativos, ni a los índices? ¿El «dropout de id» filtra algo? ¿`puntuar` o `guardar` leen algo de
   prueba? ¿Los negativos de validación excluyen la prueba (eso usaría prueba)?
2. `src/m3_recomendacion/contenido.py`: solo `destinos.parquet` y `usuarios.parquet`; ninguna columna derivada de
   interacciones (ni `popularidad`).
3. `src/m3_recomendacion/hpo.py` (`evaluar_configuracion_red`, `buscar_red`): la búsqueda nunca lee prueba; candidatos de
   validación = catálogo − train.
4. `src/m3_recomendacion/experimento.py`: el único cambio de JJ-5 es el reordenamiento de `_presupuesto`; ¿abre alguna vía nueva?
5. Las guardas de `tests/test_fuga_m3.py` (`AJUSTES_SOLO_TRAIN`, `AJUSTES_SIN_PRUEBA`, `ARCHIVOS_DE_MODELO_M3`,
   `LECTURAS_DE_ARCHIVOS` con `np.load`, `read_text`, `read_bytes`, `torch.load`, y la guarda de `contenido.py`): ¿detectan de
   verdad una fuga? Aplica tú mismo mutantes (cópialos, aplícalos, corre la prueba, reviértelos; deja el código igual que lo
   encontraste) — p. ej. índices de id con train ∪ prueba, negativos que excluyen la prueba, parada temprana con prueba, búsqueda
   con prueba — y reporta cuáles mueren.
6. Resultados reales: comprueba con `results/data/m3/hpo_ensayos.json`, `summary.json`, `curvas/red.json`, `models/m3/red.json`
   (mapas id → índice) y `data/processed/m3/interacciones.parquet` que los usuarios y destinos con índice ≠ 0 son exactamente los
   que tienen interacciones en train, y que ningún resultado de la red depende de prueba fuera de la evaluación final.

## Reporte
Veredicto SIN FUGA / SIN FUGA CON OBSERVACIONES / FUGA; por punto, evidencia con `archivo:línea`; mutantes aplicados y si
murieron; pruebas que agregaste (nombre y qué demuestran); observaciones y recomendaciones.
