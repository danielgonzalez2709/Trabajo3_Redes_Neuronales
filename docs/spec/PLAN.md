# PLAN — tablero global (Spec v0.1)

> Una línea por tarea. El detalle (aceptación, agente, verificador) está en la spec de cada persona (`docs/spec/partes/`).
> Pipeline por tarea: **implementador → revisor-spec → revisor-calidad → (+ verificador) → PR → Daniel fusiona**.
> Estado: ⬜ pendiente · 🟨 en curso · ✅ hecho · ⛔ bloqueado. 🧠 = tarea para `implementador-experto` (Opus).
> Entrega: **mar 1-dic** (hora por confirmar).

**Ruta crítica:** DA-1 (mar 24, 12 m.) → DA-3 series reales de M1 (mié 25, 2 p. m.) → AN-4/AN-5 búsqueda y 30 semillas
(jue 26–sáb 28, 12 m.) → CA-6 negocio y DA-6 app M1 (sáb 28) → blog (lun 30).
**Nadie espera:** antes de cada entrega se trabaja con la serie sintética o con los JSON de juguete (núcleo §5.11).

| Día | Daniel | Camila | Andrés | José | Juan José |
|---|---|---|---|---|---|
| **Lun 23** | ✅ DA-0 spec, repo, ruleset, ramas | Lee núcleo + su spec | Lee núcleo + su spec | Lee núcleo + su spec | Lee núcleo + su spec |
| **Mar 24** | ✅ **DA-1** infraestructura (PR #1) · ✅ DA-2 crudo M1 + DIVIPOLA · ✅ **DA-3** series reales (adelantado; PR #2) · ✅ DA-4 ficha, calidad y diccionario de M1 | ⬜ CA-1 calendario · ⬜ CA-2 normativa y `operacion.yaml` | ⬜ AN-1 🧠 partición, origen rodante, métricas (sintéticos) | ⬜ JO-1 descarga, ficha, artículo | ⬜ JJ-1 descarga, ficha, ¿real o sintético? |
| **Mié 25** | (DA-3 y DA-4 entregados el mar 24) · revisión de PR · adelantar DA-5 | ⬜ CA-3 🧠 `dimensionar()` · ⬜ CA-4 descriptivo M1 (desde las 2 p. m.) | ⬜ AN-2 🧠 pérdidas · AN-1 entregado a Camila (noche) | ⬜ JO-2 descriptivo · ⬜ JO-3 🧠 partición sin fuga | ⬜ JJ-2 descriptivo · ⬜ JJ-3 🧠 partición · inicia JJ-8 |
| **Jue 26** | 🟨 DA-5 app (lista el mar 24; falta Vercel) · ✅ guion del video (mar 24) · revisión de PR | ⬜ CA-4 cierre · ⬜ CA-5 modelos de referencia | ⬜ AN-3 MLP + secuencial · ⬜ AN-4 búsqueda | ⬜ JO-4 logística · ⬜ JO-5 CNN + ajuste fino | ⬜ JJ-4 popularidad + FC · ⬜ JJ-5 🧠 red |
| **Vie 27** | Revisión de PR · app con contratos de juguete | Apoyo a AN-5 (referencias en el mismo arnés) · hipótesis | ⬜ AN-5 30 semillas (noche) | ⬜ JO-5 búsqueda · ⬜ JO-6 30 semillas (GPU) | ⬜ JJ-5 30 semillas · lista de activaciones de todos |
| **Sáb 28** | ⬜ DA-6 app M1 · ⬜ DA-7 🧠 app M2 · **grabación del video** | ⬜ CA-6 negocio 1, 2, 4 · ⬜ CA-7 figuras · ⬜ CA-8 export | ⬜ AN-5 entregado (12 m.) · ⬜ AN-6 figuras · ⬜ AN-7 negocio 3 · ⬜ AN-8 export | ⬜ JO-7 🧠 Grad-CAM · ⬜ JO-8 alertas · ⬜ JO-9 ONNX | ⬜ JJ-6 negocio · ⬜ JJ-7 export |
| **Dom 29** | ⬜ DA-7/DA-8 app M2 y M3 · ⬜ DA-11 notebook 00 · ⬜ DA-12 uso de IA | ⬜ CA-9 notebooks · ⬜ CA-10 blog + ética (8 p. m.) | ⬜ AN-9 blog (8 p. m.) · ⬜ AN-10 cacería | ⬜ JO-10 demo · ⬜ JO-11 blog (8 p. m.) | ⬜ JJ-8 fundamentación · ⬜ JJ-9 APA · ⬜ JJ-10 (8 p. m.) |
| **Lun 30** | ⬜ DA-9 blog publicado · app final · ⬜ DA-10 video | Video individual · fichas | AN-10 cierre · video individual | Video individual · fichas | ⬜ **JJ-11 clon limpio** · video individual |
| **Mar 1** | **Entrega** | | | | |

**Hasta el dom 29 a las 8 p. m., todos:** ≥ 1 hallazgo (o verificación documentada) en `alucinaciones/registro.md`, ética de su
módulo a Camila, secciones del blog a Daniel.

## Cierre (todos)
| ID | Tarea | Fecha | Responsable | Estado |
|---|---|---|---|---|
| T.1 | Cacería: ≥ 5 hallazgos, ≥ 3 categorías, ≥ 1 por módulo | dom 29 | Andrés + cazador-alucinaciones | ⬜ |
| T.2 | Auditoría de entregables contra el Anexo | lun 30 | Daniel + auditor-entregables | ⬜ |
| T.3 | Clon limpio en otra máquina | lun 30 | Juan José + auditor-reproducibilidad | ⬜ |
| T.4 | Videos individuales (2–3 min con evidencia) | lun 30 | cada uno | ⬜ |
| T.5 | Fichas de estudio + predicciones verificadas | lun 30 | tutor-sustentacion + todos | ⬜ |
| T.6 | **Entrega** | **mar 1-dic** | todos | ⬜ |
| T.7 | Simulacro de sustentación | antes de la sustentación | todos | ⬜ |
