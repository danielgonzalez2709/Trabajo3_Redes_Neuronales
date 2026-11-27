# Prompt JJ-2 — documentador (Sonnet) — 2026-11-26 — orquesta: Juan José

Actúa como el agente definido en `.claude/agents/documentador.md` (léelo primero). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales` (rama `dev/juanjose`). Edita SOLO `docs/MEMORIA.md` (con la herramienta Edit).
Sin commit ni push. **No borres nada de otros integrantes**; mantén el archivo en ≤ 150 líneas (cuenta las líneas al final).

Datos de cierre de JJ-2 (escríbelos tal cual, sin agregar cifras que no estén aquí):
- **Estado:** agrega, después de la viñeta de JJ-1, una viñeta: «JJ-2 (descriptivo de M3 + caso de uso) terminado en
  `dev/juanjose` el jue 26, pendiente de PR junto con JJ-1: `run.py m3-eda --config configs/m3/eda.yaml` escribe en
  `results/data/m3/eda/` las tablas de actividad, concentración, calificaciones, coincidencia preferencia–tipo, pruebas e
  `hipotesis.json` (9 hipótesis: H-M3-1 y H-M3-4 no concluyentes, H-M3-2/3/5/6 refutadas, H-M3-7/8/9 pendientes para JJ-10);
  `run.py figures` genera 4 figuras en `blog/docs/figures/m3/` (cola larga, Lorenz, preferencias × tipo, calificaciones);
  blog 07 con caso de uso y las 7 subsecciones. Las interacciones se parecen a un reparto uniforme al azar (sin cola larga
  más allá del azar). Revisado por revisor-spec (aprobado), verificador-matematico (aprobado en la 2.ª vuelta),
  revisor-calidad (2 vueltas; el último bloqueante lo corrigió la sesión principal) y cazador-alucinaciones.» Actualiza
  también la viñeta de JJ-1: el rótulo «fecha de publicación» pasó a «creación de la versión 1 en Kaggle (2024-01-23)».
- **Decisiones vigentes:** agrega en la viñeta de M3 (o una nueva) «[PROPUESTO por el analista, pendiente de Juan José]
  umbral de actividad pocas ≤ 2 / muchas ≥ 3; efectos mínimos y criterio de veredicto en `configs/m3/eda.yaml` (convención
  nuestra); emparejamiento léxico preferencia→tipo (Beaches→Beach, etc.); K = 5 por defecto y K ∈ {1, 3, 5, 10}».
- **Pendientes**, en el punto 4 de Juan José: reemplaza «JJ-2 y JJ-3» por «JJ-3», agrega «PR de JJ-1 + JJ-2 (incluir
  `results/data/m3/eda/*` y `blog/docs/figures/m3/*`, que la CI necesita); confirmar umbral, efectos mínimos y criterio de
  `en_el_limite` de JJ-2; en JJ-9 verificar Bergsma (2013) y Romano et al. (2006) antes de citarlos; en JJ-3, una prueba que
  compare la partición real con `actividad_usuarios.json` → `particion_d3`».
- **Cacería:** en la viñeta de candidatos agrega «3 candidatos de M3 de JJ-2 (sin número): método de los p e IC mal descrito
  en el blog (redactor Sonnet, Matemáticas); regla de veredicto escrita distinta de la implementada (analista Sonnet,
  Código, menor); «no son umbrales de la literatura» (redactor Sonnet, Conceptos, condicionado a fuente primaria);
  evidencia en `alucinaciones/evidencias/JJ-2/`».
- **Bitácora** (línea nueva arriba): «2026-11-26 · Juan José · JJ-2 ✅: descriptivo de M3 (9 hipótesis, 4 figuras, blog 07
  con caso de uso); corrección del rótulo de fecha de JJ-1; 3 candidatos a la cacería.»

Responde con el número de líneas final y el diff resumido.
