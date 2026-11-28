# Prompt CA-3c — implementador-experto (Opus, continuación del agente de CA-3b) — 2026-11-26 — orquesta: Camila

Decisiones de Camila (26-nov) sobre tus «Decisiones que te tocan». Aplica con prueba primero (caso a mano en el comentario),
mismos archivos (`src/m1_demanda/operacion.py`, `configs/m1/operacion.yaml`, `tests/test_operacion_m1.py`,
`results/data/m1/operacion/`). **Prohibido `git commit` / `git push`.**

1. **Conductores por piernas (reemplaza (5a))**, resuelve tus puntos 1, 2 y 3:
   - piernas(corredor, d) = 2 · max(desp_r, desp_r') (cuenta las piernas vacías de reposición, coherente con la ec. (4));
   - horas de conducción por conductor y pierna = t_r / k_r, con k_r = 2 si t_r > 8 h (Res. 315/2013 art. 6). Supuesto declarado
     (`supuesto: true` con nota): el relevo que descansa a bordo no consume jornada;
   - error claro si t_r / k_r > jornada máxima diaria;
   - piernas por conductor y día = max(1, ⌊ J_ef / (t_r / k_r) ⌋) (piernas indivisibles);
   - C_serv = ⌈ k_r · piernas / piernas_por_conductor ⌉; la nómina (5b) no cambia: ⌈ C_serv/(1−a) · 7/(7−s) ⌉.
   Casos a mano mínimos: Bogotá–Cali (t = 10, k = 2 → 1 pierna por conductor), Bogotá–Sogamoso (t = 4, J_ef = 7 → 1),
   Pasto–Ipiales (t = 1,5 → 4), corredor con un sentido en 0 (las piernas vacías cuentan), y que C_serv siga sin depender de H.
2. **ρ\* global calculado en la misma ventana que f** (últimos `calibracion.meses_fraccion` meses de train; tú mediste 0,606).
   Actualiza el valor por defecto de `operacion.ocupacion_objetivo` y su prueba de consistencia con los datos. El desajuste por ruta
   (tasa de reproducción de despachos ORIGEN por ruta) va a `resumen.json` y a la nota del YAML como limitación.
3. Puntos 5 y 6 (capacidad por máximo; J_ef = 7 h): sin cambio de fórmula; deja en las notas del YAML la limitación que describiste
   (atípicos, máximo de promedios diarios = cota baja; la hora de pausa no debe ser tiempo a disposición del empleador).
4. Actualiza el encabezado de `operacion.py` (ecuaciones en el orden del blog) y corre `.venv/bin/python -m pytest -q`, el comando
   con `--set operacion.ocupacion_objetivo=0.8 --set operacion.cuantil=0.9` y al final sin `--set`.

Reporta: salida real, tabla del máximo diario por corredor (vehículos, en servicio, nómina) antes (ronda 2) y ahora, ρ\* y la tasa
de reproducción por ruta.
