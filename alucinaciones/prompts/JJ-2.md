# Prompt JJ-2 — sesión orquestadora (Opus) — 2026-11-26 — orquesta: Juan José

Prompt literal recibido por la sesión principal (copiado sin cambios):

```text
Tarea JJ-2 (análisis descriptivo de M3 + caso de uso). Te dirige Juan José; rama dev/juanjose. JJ-1 ya está hecha y en GitHub (commit 94d8c83).

ANTES DE NADA
1. Guarda este prompt LITERAL en alucinaciones/prompts/JJ-2.md antes de despachar subagentes, y cada prompt a un subagente en alucinaciones/prompts/JJ-2-<agente>.md.
2. Lee: docs/spec/SPEC.md (§0, §5.7, §5.12, §6 y el Anexo "Módulo 3"), docs/spec/partes/juanjose.md (sobre todo §3.0 y las decisiones D1–D7 de §3.1), docs/MEMORIA.md, docs/investigacion/JJ-1_fuentes_m3.md, results/data/m3/eda/ficha.json y diccionario.json, src/comun/eda.py, src/viz/estilo.py, blog/hooks/reporte.py (sintaxis de figuras, tablas y citas) y blog/secciones/07-m3-recomendacion.md.
3. Reglas: NO commits, NI push, NI PR (los hace Juan José en GitHub Desktop). Siempre .venv\Scripts\python. Prohibido inventar: toda cifra del blog sale de un archivo generado por código (results/…). Prueba primero, luego código. Sin internet. No toques archivos compartidos (src/comun/, run.py, requirements.txt, SPEC.md, archivos de otros) salvo PLAN.md, MEMORIA.md y registro.md al cierre, como siempre.

QUÉ PIDE EL ENUNCIADO (Anexo M3, tareas 1 y 2) Y CÓMO LO CUMPLIMOS
- Tarea 1, caso de uso: momento y canal en que se muestra la recomendación, cuántos destinos (K) y qué información del usuario está disponible en ese momento.
- Tarea 2, descriptivo: distribución de interacciones por usuario y por destino, concentración en los destinos populares, proporción de usuarios con pocas interacciones, e hipótesis sobre qué explica las preferencias.
- Plantilla común §5.12: las 7 secciones en orden (Ficha del conjunto, Diccionario y calidad, Variable objetivo, Estructura y heterogeneidad, Hipótesis explícitas, Implicaciones para el modelado, Veredicto de las hipótesis) y results/data/m3/eda/hipotesis.json con el esquema de §5.12 (escrito con src/comun/eda.escribir_hipotesis).
- Figura mínima del módulo que corresponde aquí: distribución de interacciones por usuario y por destino (cola larga).

QUÉ CONSTRUIR (analista-experimentos, Sonnet; prueba primero)
E1. tests/test_eda_m3.py con los fixtures de tests/fixtures/m3/ (o datos mínimos construidos en la prueba): esquema de hipotesis.json válido; métricas de concentración (Gini, cuota del 10 % y 20 % de destinos más populares, HHI) verificadas contra un cálculo a mano en un ejemplo pequeño; la tasa de coincidencia preferencia–tipo y su línea base de azar calculadas bien en un ejemplo a mano; determinismo (misma semilla → mismos bytes).
E2. configs/m3/eda.yaml (comentado): rutas de entrada (data/processed/m3/), salida (results/data/m3/eda/), base_seed para las permutaciones, n_permutaciones, niveles de análisis (destino_id y lugar).
E3. src/m3_recomendacion/eda.py con main(cfg) (lo llama run.py m3-eda). Lee SOLO data/processed/m3/ (no data/raw) y escribe en results/data/m3/eda/:
   - tablas (CSV/JSON) de: interacciones por usuario (distribución y cuántos con 0, 1, 2, 3, 4, 5+), por destino_id y por lugar; calificaciones por origen (distribución 1–5); concentración (Gini, HHI, cuota del top 10 % y 20 %, curva de Lorenz) a nivel destino_id y lugar, comparadas con lo que daría una asignación uniforme al azar (simulada con la semilla); usuarios por grupo de actividad (pocas vs. muchas interacciones, con el umbral justificado y coherente con D3).
   - las pruebas de las hipótesis (ver E4) con estadístico, p-valor, tamaño de efecto (p. ej. V de Cramér, diferencia de tasas con intervalo) y, cuando haya varias pruebas, un ajuste por comparaciones múltiples declarado.
   - hipotesis.json con escribir_hipotesis.
   Debe terminar rápido (segundos) y ser determinista.
E4. Hipótesis explícitas (ids H-M3-1, H-M3-2, …), cada una con enunciado, justificación, evidencia esperada, figura/tabla, resultado y veredicto. Como mínimo:
   - Las preferencias declaradas del usuario explican el TIPO de destino con el que interactúa (tasa de coincidencia frente a la línea base de azar exacta según cuántos tipos cubre cada combinación de preferencias; prueba de independencia y prueba de permutación).
   - La calificación es mayor cuando el destino coincide con las preferencias.
   - La columna Popularity del destino se relaciona con su número de interacciones.
   - La demografía (género, número de adultos, número de niños) se relaciona con el tipo o lugar elegido (p. ej. familias con niños → playa).
   - Hay concentración en pocos destinos (cola larga) frente a lo esperado por azar.
   - Reviews e historial se comportan distinto (tipos, calificaciones).
   - Al menos una hipótesis que SOLO se puede cerrar al modelar (p. ej. «una red con variables de contenido no supera a la popularidad por más que la variabilidad entre semillas»), con veredicto «pendiente».
   Las hipótesis que se pueden contrastar con los datos quedan con veredicto (confirmada / refutada / no concluyente) y su evidencia ya medida; las que dependen de los modelos quedan «pendiente» (se cierran en JJ-10). No adelantes conclusiones que los números no respalden; si la evidencia es débil, «no concluyente».
E5. src/viz/figs_m3.py con generar() (lo llama run.py figures; debe funcionar SOLO desde results/, sin data/raw ni data/processed si es posible) usando src/viz/estilo.py y guardar_figura, con las figuras en blog/docs/figures/m3/: (a) cola larga: interacciones por usuario y por destino (obligatoria), con la referencia de lo esperado por azar; (b) curva de Lorenz o cuota acumulada por nivel (destino_id y lugar); (c) matriz preferencias × tipo de destino (proporciones) que muestre la evidencia de la primera hipótesis; (d) distribución de calificaciones por origen. Títulos y ejes en español.
E6. Corrige el rótulo impreciso que marcó R3 en JJ-1: donde diga «fecha de publicación» del conjunto (2024-01-23) debe decir «creación de la versión 1 en Kaggle (2024-01-23)» —Kaggle no da fecha de publicación—. Búscalo en configs/m3/, results/data/m3/eda/ (regenerando con run.py m3-datos, no a mano), data/fuentes.md, docs/spec/partes/juanjose.md (D3 y D4) y docs/investigacion/JJ-1_fuentes_m3.md.

BLOG (redactor-tecnico, Sonnet) — blog/secciones/07-m3-recomendacion.md
- Bajo el título del módulo, antes de «### Análisis descriptivo», un párrafo corto de CASO DE USO (sin encabezado nuevo, para que el módulo siga abriendo con el descriptivo según §5.12): la recomendación se muestra en la app/web de la empresa, en la sección de la nueva línea de turismo internacional, cuando el cliente entra a explorar viajes (y opcionalmente en un correo de campaña); K = 5 destinos por defecto (es el k_defecto del contrato de la app, app/public/model/m3/perfil_nuevo.json), y se evalúan K ∈ {1, 3, 5, 10}; información disponible en ese momento: su historial de interacciones previas (visitas y reseñas), las preferencias que declara al registrarse y datos demográficos básicos (género, número de adultos y de niños); NO se usan nombre ni correo (D6); un cliente nuevo solo tiene preferencias. Si algo de esto contradice el Spec o el contrato de la app, dímelo en vez de escribirlo.
- Llena las 7 subsecciones con las cifras de results/data/m3/eda/ (sin teclear números que no estén en esos archivos), con figuras y tablas en el formato ::: figura / ::: tabla del hook (título y fuente obligatorios, cada una citada en el texto con [[fig:…]] / [[tab:…]]) y la cita del conjunto con su clave de blog/references.bib. «Implicaciones para el modelado» debe cubrir: partición (D3), negativos (uniformes vs. por popularidad, a la luz de la concentración medida), variables de contenido disponibles (D2 y preferencias/demografía de usuario), el problema de los 1 000 ids = 5 lugares y qué se espera si los datos no tienen patrón (resultados cercanos al azar; por eso importa reportar la variabilidad entre semillas). «Veredicto de las hipótesis»: tabla con id, enunciado corto y veredicto (las pendientes, marcadas como tales).
- Tono: claro, en español, sin exagerar; cada afirmación respaldada por una cifra o figura.

REVISIÓN (en este orden; si alguno falla, vuelve al autor con los hallazgos)
R1. revisor-spec (Sonnet): ¿cumple tareas 1 y 2 del Anexo M3, la plantilla §5.12 (secciones, nombres, orden, hipotesis.json) y la figura de cola larga? ¿Respeta D1–D7?
R2. verificador-matematico (Opus): definiciones y cálculos de Gini, HHI, Lorenz, línea base de azar de la coincidencia, pruebas estadísticas, tamaños de efecto y ajuste por comparaciones múltiples; que las conclusiones no digan más de lo que muestran los p-valores.
R3. revisor-calidad (Haiku): código y pruebas.
R4. cazador-alucinaciones (Opus): cada cifra del blog contra results/data/m3/eda/; la cita del conjunto contra references.bib. Errores de un subagente → candidato con evidencia, sin numerar en registro.md (H-?? (JJ-2)).

CIERRE
- Corre y pega la salida real de: .venv\Scripts\python run.py m3-datos --config configs/m3/datos.yaml; .venv\Scripts\python run.py m3-eda --config configs/m3/eda.yaml (dos veces, mismas salidas); .venv\Scripts\python run.py figures; la construcción estricta del blog como indica blog/README.md; y .venv\Scripts\python -m pytest -q -m "not lento" (todo en verde).
- Marca JJ-2 ✅ en docs/spec/PLAN.md y en docs/spec/partes/juanjose.md; que el documentador actualice docs/MEMORIA.md sin borrar nada de otros.
- Muéstrame: archivos creados/modificados, salidas de los comandos, un resumen de cada hipótesis con su veredicto y cifra clave, veredictos de R1–R4, candidatos a la cacería y lo que deba decidir Juan José. Luego DETENTE.
```
