# Prompt CA-3e — implementador-experto (Opus) — 2026-11-27 — orquesta: Camila

Repo /Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales, rama dev/camila. Correcciones de CA-3d tras tres
revisiones (revisor-spec APROBADO con observaciones; revisor-calidad NO APROBADO; verificador-matematico APROBADO CON
OBSERVACIONES). Antes de tocar nada lee `alucinaciones/prompts/CA-3d.md` (lo pedido) y el estado actual de
`src/m1_demanda/operacion.py`, `configs/m1/operacion.yaml`, `tests/test_operacion_m1.py`. Toca solo esos archivos y
`results/data/m1/operacion/`. Prueba primero (caso a mano en el comentario). **Prohibido `git add`, `git commit`, `git push`,
`git stash`, `git checkout`.** Prohibido inventar valores normativos: usa los del YAML con su cita; si falta algo,
`TODO(dato-faltante)` y repórtalo. La columna diaria `conductores` (núcleo §5.4) no cambia de significado.

## Decisiones de Camila (27-nov)
A. **m_r: calcular las dos variantes.** Por defecto sigue m **por ruta** (ρ_r = min(1, ρ·m_r)); agrega m **por corredor**
   (m_c = ρ_c_obs/ρ\*, con ρ_c_obs = Σ_{r∈c} A_r / Σ_{r∈c} O_r en la misma ventana de train) y repórtalo en `resumen.json` como
   sensibilidad, sin cambiar la salida por defecto. En la validación fuera de ventana (calibrar sep–oct 2022, probar nov–dic
   2022) reporta para ρ global, ρ·m_ruta y ρ·m_corredor: (i) reproducción de despachos ORIGEN por ruta y total, y (ii) la
   cantidad que fija vehículos y conductores, Σ_d max(desp_r, desp_r') / Σ_d max(obs_r, obs_r') por corredor. El verificador
   midió para 11001-15759 (ii) 171,4 % por ruta frente a 135,2 % por corredor, y total (i) 115,8 % con ρ·m_ruta frente a 108,0 %
   con ρ global: tus números deben reproducirlos o explicar la diferencia. Actualiza la nota de `ocupacion_objetivo` del YAML
   con esas cifras (hoy dice «102–108 % en 5 de 6 rutas» y omite el total y la cantidad por corredor) y el encabezado de
   `operacion.py:68-72`, que hoy justifica «por ruta» con una cifra que la validación no sostiene. Etiqueta:
   [DECIDIDO, Camila, 27-nov]. Si se puede elegir la variante por config, que sea un parámetro del YAML con `por_ruta` por defecto.
B. **Quitar salidas que el contrato no pide:** en `resumen.json`, `ocupacion_por_ruta_usada` y `ocupacion_por_ruta_con_tope_1`;
   en la tabla de dimensionamiento, las columnas `tripulacion`, `piernas`, `piernas_por_conductor` y `ocupacion_ruta`. Los
   cálculos intermedios siguen dentro de las funciones; las pruebas que los necesiten llaman a las funciones, no leen columnas.
   El print de `main` puede seguir avisando del tope calculándolo al vuelo. **Se conserva**
   `max_nomina_semanal_semanas_completas` (lo necesita el punto C1).
C. **Todas las observaciones de revisor-calidad:**
   1. (BLOQUEANTE) `operacion.py:789-791`: el print «N\* máx.» toma el máximo de todas las semanas, incluidas las incompletas
      (cota inferior). Con la config por defecto imprime 539 para 11001-15759 (semana 26-dic→1-ene, 6 días) cuando la mayor
      semana completa es 442. Imprime `max_nomina_semanal_semanas_completas` y, aparte, el máximo de semanas incompletas
      marcado como cota inferior.
   2. Encabezado de `operacion.py:1-80`: dejar solo las ecuaciones (1)–(5b) con el nombre de la función que implementa cada una
      y sus supuestos en una línea; mover el registro de decisiones con fechas a las notas del YAML (si no está ya). Corrige el
      docstring de `validar_parametros` (~:255) que dice «(1)–(5')» → «(1)–(5b)».
   3. `main` (~:737-793): separar el print en `_imprimir_resumen(resumen)`.
   4. `_resumen` (~:693-695): no recalcular el tope (`rho * m > 1`); reutilizar `ocupacion_ruta`. Evitar la segunda llamada a
      `capacidad_supuesta` (~:686 y ~:612) si se puede pasar el resultado.
   5. `_resumen` (~:699): `reproduccion.pop("dentro_de_ventana")` muta el dict de entrada; pásalo como argumento.
   6. Separador `" | "` de corredor escrito a mano en ~:317 y ~:355: constante `SEP_CORREDOR`.
   7. `tests/test_operacion_m1.py:227-252`: el docstring de `_cubre_con_descansos` dice «independiente de la fórmula»; corrígelo:
      verifica la fórmula contra una construcción explícita (McNaughton); infactibilidad con N\*−1 vale porque las ramas que
      devuelven False son justo las dos condiciones necesarias.
   8. Comentarios que hablan de la versión anterior («antes», «como antes», «la ec. (5) anterior», «la prueba vieja») en
      ~:121-127, :162-163, :186-188, :348, :386, :486-487, :498: dejar solo el caso a mano y la regla vigente.
   9. ~:480-482 `test_semana_justa_en_el_limite_es_valida`: la segunda llamada (J=6, s=2 → 30 h) no está en el límite;
      renombrar o separar.
   10. ~:745-747: el comentario «(R1: 15,5 / 0,6 · … ≠ 31)» es ilegible: escribe el cálculo completo o quítalo.
   11. ~:893-897, :1058-1066: pruebas de prosa de notas del YAML (`"diciembre" in nota`, etc.): conservar solo las que protegen
       un contrato (p. ej. que la nota de costos diga que `dimensionar` no los usa), con comentario de por qué.
   12. ~:862 y ~:1087: la comprobación «fuente XOR supuesto» está duplicada; deja una.
   13. ~:126: quitar «tolerancia del techo» para 7/7 (es exacto).
D. **Prueba nueva del supuesto k ≥ 3** (decidido hoy, declarado en el YAML): con J_ef = 7, t = 14 → k = 2; t = 14,01 → k = 3;
   t = 15 → k = 3, h = 5, L = 1.

## Al terminar
Corre `.venv/bin/python -m pytest -q` (suite completa), el comando con `--set operacion.ocupacion_objetivo=0.8 --set
operacion.cuantil=0.9` y al final sin `--set` (que `results/data/m1/operacion/` quede con la config por defecto).

Reporta: salida real de pytest y del print; tabla de la validación fuera de ventana con las tres variantes (i) y (ii);
máximo diario por corredor y N\* (completas / cota de incompletas); qué cambió en cada archivo; lista de lo que no aplicaste y
por qué; TODO o supuestos nuevos.
