# JJ-3 — 2.ª vuelta del orquestador (Opus 5.5) al implementador-experto (Opus), 2026-11-26

El auditor-fugas dio SIN FUGA, con un hallazgo que debes corregir (mismas reglas que en la 1.ª vuelta: sin commits, solo tus
archivos `particion.py`, `datos.py`, `test_fuga_m3.py` y lo regenerado por `m3-datos`).

**Hallazgo (R14, Código, menor).** En `resumen.json`, `diagnosticos.mismo_lugar_en_historial_conocido.definicion` dice que para
esos usuarios «un "acierto por lugar" es trivial». Es falso: 204 de 606 usuarios de prueba tienen otro id del mismo lugar en
su historial conocido, y el azar predice 198,0 (lo verifiqué: Σ_u |lugares distintos del historial conocido de u| / 5 sobre los
usuarios de prueba = 198,0). Con 5 lugares la coincidencia es la esperable por azar y un modelo no sabe cuál de sus lugares
conocidos es el objetivo. La frase la sembró el prompt del orquestador; no es culpa tuya, pero hay que corregirla.

Qué hacer:
1. Reescribe la `definicion` sin «trivial»: qué se cuenta, y que con `n_lugares` lugares una coincidencia así es esperable por
   azar, de modo que el acierto por lugar debe compararse con su línea base del azar.
2. Agrega en ese bloque, para prueba y validación, `esperado_por_azar` = Σ_u |lugares distintos del historial conocido de u| /
   n_lugares (supuesto explícito en el JSON: el lugar del destino objetivo es uniforme sobre los lugares e independiente del
   historial) y `n_lugares`. Que lo calcule el código.
3. Ajusta las pruebas: un caso a mano del esperado por azar y que el resumen real coincida con lo recalculado (la prueba que
   ya compara `resumen.json` con lo recalculado debe cubrir las claves nuevas).
4. No toques las 3 pruebas que agregó el auditor en `test_fuga_m3.py` (`AJUSTES_SOLO_TRAIN`, la guarda estática y
   `test_real_usuarios_sin_interacciones_o_con_una_no_se_evaluan`) salvo para que sigan pasando.
5. Regenera con `.venv/Scripts/python run.py m3-datos --config configs/m3/datos.yaml` dos veces (idénticas byte a byte) y corre
   `.venv/Scripts/python -m pytest -q tests/test_fuga_m3.py` y `-m "not lento"`.

Entrega: diff resumido, valores nuevos de `resumen.json` y salida real de los comandos.
