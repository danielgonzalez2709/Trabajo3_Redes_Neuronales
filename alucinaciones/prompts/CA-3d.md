# Prompt CA-3d — implementador-experto (Opus, continuación del agente de CA-3b/CA-3c) — 2026-11-26 — orquesta: Camila

La segunda verificación matemática de CA-3 dio APROBADO CON OBSERVACIONES. Camila decidió (26-nov) aplicar estas tres. Mismos
archivos (`src/m1_demanda/operacion.py`, `configs/m1/operacion.yaml`, `tests/test_operacion_m1.py`, `results/data/m1/operacion/`).
Prueba primero, con el caso a mano en el comentario. **Prohibido `git commit` / `git push`.**

1. **E1 — tripulación**: k_r = max(k_norma(t_r), ⌈t_r / J_ef⌉), con k_norma = 2 si t_r > umbral (Res. 315/2013 art. 6), si no 1.
   Así h_r = t_r / k_r ≤ J_ef siempre; L_r = ⌊J_ef / h_r⌋ (≥ 1 sin necesidad del `max(1, ·)`; quítalo o déjalo solo como
   aserción). La comprobación de jornada máxima diaria compara h_r con `jornada_efectiva_h` (que ya cumple ≤ jornada máxima diaria
   y la cota semanal J_ef·(7−s) ≤ 42). Corrige la prueba de `tests/test_operacion_m1.py:341-351` que da t = 8 por válido.
   Contraejemplos que deben quedar probados: t = 7,5 → k = 2 (antes 1, 45 h/semana); t = 8 y t = 8,01 sin salto artificial más allá
   del que impone la norma; con la config actual (t = 10, 4, 1,5) las salidas no cambian.
2. **O1 — multiplicador por corredor**: ρ_r = ρ · m_r, con m_r calibrado en train en la misma ventana que f y ρ\* (m_r = ρ_r_obs/ρ\*,
   ρ_r_obs = pax_ORIGEN / (cap_ef · desp_obs) del corredor; define si m_r es por ruta o por corredor y justifícalo con ida y regreso).
   `operacion.ocupacion_objetivo` sigue siendo un solo escalar (control de la app y `--set`). m_r se calcula al ejecutar (como f),
   no se escribe a mano; se reporta en `resumen.json`. Validación fuera de ventana (calibrar en sep–oct 2022, probar en nov–dic
   2022) en `resumen.json`: reproducción por ruta con ρ global y con ρ·m_r (el verificador midió 66–141 % vs 101–107 % en 5 de 6;
   11001-15759 172 % por su cambio de régimen). Nota del YAML: limitación (ρ\* incluye el pico de diciembre; demanda censurada).
3. **O3 — nómina semanal factible**: además de la columna diaria `conductores` (contrato §5.4, no cambia), una salida semanal por
   corredor `results/data/m1/operacion/nomina_semanal.csv` con N\* = ⌈ max(max_d C_serv, Σ_d C_serv / (7 − s)) / (1 − a) ⌉ por semana
   (lunes–domingo; documenta las semanas incompletas). Caso a mano: C_serv = [10,10,10,10,10,10,0], a = 0 → N\* = 10 (la diaria da 12).
4. Actualiza el encabezado de `operacion.py` con las ecuaciones finales (1)–(5b) en el orden del blog, incluida la de N\*.
5. Corre `.venv/bin/python -m pytest -q`, el comando con `--set operacion.ocupacion_objetivo=0.8 --set operacion.cuantil=0.9` y al
   final sin `--set`.

Reporta: salida real; tabla del máximo diario por corredor (vehículos, en servicio, nómina diaria) antes y ahora; m_r por ruta;
reproducción dentro y fuera de ventana; N\* semanal vs. máximo diario.
