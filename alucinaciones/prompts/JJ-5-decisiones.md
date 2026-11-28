# JJ-5 — prompt literal de Juan José a la sesión principal (Opus 5.5), decisiones de cierre, 2026-11-27

Juan José decide sobre JJ-5:
1. En configs/m3/base.yaml usa hiperparametros_desde: config para la red Y para la MF (los valores ya son copia del mejor ensayo; la prueba que vigila que coincidan con hpo_ensayos.json debe seguir pasando). Verifica que run.py m3 --config configs/m3/base.yaml da EXACTAMENTE las mismas métricas que antes y que --set modelo.dim_embedding=8 con base.yaml ahora sí cambia la red (basta con una corrida de 2 semillas: --set semillas.n=2).
2. Todo lo [PROPUESTO] de JJ-5 en juanjose.md §3.2 pasa a [DECIDIDO, Juan José, 27-nov].
3. Las recomendaciones R-1 a R-19 del revisor-calidad NO se aplican; anótalas como pendientes no bloqueantes en MEMORIA.
4. Corrige docs/MEMORIA.md: JJ-1, JJ-2 y JJ-3 ya están fusionadas en main (PR #6, 27-nov); lo pendiente de PR es JJ-4 + JJ-5.
Luego corre .venv\Scripts\python -m pytest -q -m "not lento" y pega el resultado. No hagas commit.

(Respuesta de Juan José a la pregunta del orquestador sobre el choque con el núcleo §6: «config + presupuesto de hpo»: con
origen config, si hpo_ensayos.json trae la familia con mejor.params igual a la config, se reportan sus ensayos y su tiempo.)
