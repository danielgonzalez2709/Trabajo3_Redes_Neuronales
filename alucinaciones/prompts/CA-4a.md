# Prompt CA-4a — analista-experimentos (Sonnet) — 2026-11-26 — orquesta: Camila

Actúa como el agente definido en `.claude/agents/analista-experimentos.md` (léelo primero). Repositorio:
`/Users/softwaresolenium/CoursesExercises/Trabajo3_Redes_Neuronales` (rama `dev/camila`). Python: `.venv/bin/python`
(3.12, dependencias ya instaladas). **Prohibido hacer `git commit`, `git push` o cualquier operación que cambie el historial:
Camila revisa todo antes. Deja los cambios en el árbol de trabajo.**

Lee: `docs/spec/SPEC.md` §0, §3, §4.1, §5.1, §5.2 (calendario, aún no existe), §5.12 (plantilla común) y el Anexo
(«Módulo 1 → Tareas 1, 2 y 3», «Limitaciones», «Figuras mínimas del módulo»: series de demanda y descomposición);
`docs/spec/partes/camila.md` §1, §3.0, §3.4 y §5; `docs/MEMORIA.md` («Avisos para el equipo» de M1);
`docs/investigacion/DA-3_auditoria_fugas.md`; `src/comun/eda.py` (validación y escritura de `hipotesis.json`),
`src/viz/estilo.py` (estilo y `guardar_figura`), `src/comun/cli.py` (`run.py m1-eda` llama `src.m1_demanda.eda:main(cfg)`;
`run.py figures` llama `generar()` de cada `src/viz/figs_*.py`), `configs/m1/datos.yaml` y lo ya producido en
`results/data/m1/eda/` (secciones 1–2, de Daniel).

## Tarea CA-4: análisis descriptivo de M1, secciones 3–7 de la plantilla común
Archivos tuyos (solo estos): `src/m1_demanda/eda.py`, `tests/test_eda_m1.py`, `src/viz/figs_m1_datos.py`,
`tests/test_figs_m1_datos.py`, y salidas en `results/data/m1/eda/` (no sobrescribas `ficha.json`, `calidad.csv` ni
`diccionario.json`).

1. **Prueba primero** con la serie sintética (`data/sintetico/m1/demanda_diaria.parquet`, núcleo §5.11) o con fixtures pequeños:
   esquema de cada tabla, `hipotesis.json` válido según `src/comun/eda.py`, que la descomposición recupere un periodo semanal
   conocido en un sintético, y que `generar()` escriba las figuras esperadas.
2. **`eda.py` → `main(cfg)`** para `python run.py m1-eda --config configs/m1/datos.yaml`. Lee `data/processed/m1/` y escribe en
   `results/data/m1/eda/` tablas y JSON (los modelos **no dibujan**: las figuras salen de `src/viz/figs_m1_datos.py` leyendo esos
   archivos). Si necesitas parámetros nuevos, no los quemes en el código: propón un bloque `eda:` y repórtalo (el archivo
   `configs/m1/datos.yaml` es de Daniel; no lo modifiques sin que Camila lo apruebe — usa valores por defecto en el código
   documentados y lista lo que debería ir a config).
   - Sección 3 **Variable objetivo**: pasajeros por ruta y día; ceros, `sin_registro`, `anomalo` (por regla, de
     `marcas_anomalos.parquet`); proporción en tránsito vs. origen por ruta y año (`demanda_detalle.parquet`).
   - Sección 4 **Estructura y heterogeneidad**: tendencia; estacionalidad semanal (perfil por día de la semana) y anual (perfil
     mensual); **descomposición STL o MSTL con periodos 7 y 365** de al menos una ruta (todas si es barato), desde el
     2021-06-01 para no contaminar con mayo-2021 y sin días `sin_registro` (justifica cómo los tratas); diferencias entre rutas;
     tendencia 2021–2023 como proxy de pospandemia (la caída de 2020 no está en los datos, núcleo §5.1); los hallazgos de la
     spec §3.0 (tránsito ≈ origen; salto del tránsito 11001-15759 desde nov-2022; MICROBUS desaparece en 11001-76001 en 2023;
     asimetría de clases en Pasto–Ipiales) con cifras.
   - Sección 5 **Hipótesis explícitas** `H-M1-1…`: día de la semana, festivos y puentes, temporada escolar, Semana Santa, fin de
     año, pospandemia (y las que salgan de los datos). Cada una con `enunciado, justificacion, evidencia_esperada,
     figura_o_tabla, resultado, veredicto, evidencia` (núcleo §5.12).
   - Sección 6 **Implicaciones para el modelado**: ventana, variables de calendario, pérdida de conteo, partición, cambio de
     régimen, qué hacer con mayo-2021 y tránsito.
   - Sección 7 **Veredicto**: por norma `pendiente` hasta modelar. **El calendario exógeno (`data/processed/m1/calendario.parquet`,
     CA-1) aún no existe**: el código debe usarlo si existe y, si no, dejar las hipótesis de festivos, puentes, temporada escolar
     y Semana Santa en `pendiente` con `resultado` = «falta el calendario de CA-1». **No escribas fechas de festivos ni de Semana
     Santa a mano ni de memoria.** Día de la semana, fin de año (diciembre–enero por fecha, sin calendario externo) y tendencia sí
     se pueden evaluar ya; aun así deja `veredicto` según la plantilla y pon la evidencia descriptiva en `resultado`.
3. **`src/viz/figs_m1_datos.py` → `generar()`**: figuras mínimas que te tocan — series de demanda de las 6 rutas (marcando
   mayo-2021 / anómalos) y descomposición en tendencia + estacionalidad semanal + anual de al menos una ruta; más las que
   sostengan cada hipótesis. Estilo de `src/viz/estilo.py`; títulos y ejes en español; guarda donde lo hagan las figuras
   existentes del proyecto (revisa `blog/docs/figures/` y `src/viz/estilo.py`) y reporta la ruta.
4. Corre `python run.py m1-eda --config configs/m1/datos.yaml` y `python run.py figures` sobre los datos reales y reporta
   cifras clave (sin interpretar más allá de lo que muestran los números).

## Aceptación
`hipotesis.json` válido (pasa `validar_hipotesis`); figuras de series y descomposición generadas; pruebas nuevas y suite completa
pasan (`.venv/bin/python -m pytest -q`).

## Reglas
Prueba primero. Toda cifra sale de `data/processed/m1/`; nada de datos sintéticos en resultados reales. Nada de internet. Prohibido
inventar fechas, normas o significados (`TODO(dato-faltante)`). Ninguna marca `anomalo` / `sin_registro` como variable de un
modelo. No toques archivos fuera de los tuyos (ni `src/comun/`, `run.py`, el Spec, `configs/m1/datos.yaml`). Nada de commits.
Reporta al final: archivos creados, salida real de pytest y de los comandos, cifras clave por hipótesis, decisiones [PROPUESTO]
para Camila y cualquier resultado sospechoso.
