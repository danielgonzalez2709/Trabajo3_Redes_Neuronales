# Prompt JJ-2 — redactor-tecnico (Sonnet) — 2026-11-26 — orquesta: Juan José

Actúa como el agente definido en `.claude/agents/redactor-tecnico.md` (léelo primero). Repositorio:
`C:\Repositorios\Trabajo3_Redes_Neuronales`, rama `dev/juanjose`. **No hagas commit, push ni PR.** Usa
`.venv/Scripts/python` y `.venv/Scripts/mkdocs`. Sin internet. Escribe SOLO en `blog/secciones/07-m3-recomendacion.md`.
No toques `blog/references.bib`, el hook, otras secciones ni código.

## Lee antes (y nada de otras partes)
- `docs/spec/SPEC.md` §0 (reglas 4, 7 y 8), §5.8 (contrato de la app de M3), §5.12 (plantilla común) y el Anexo «Módulo 3»
  (Datos, Tareas 1–2, Figuras mínimas).
- `docs/spec/partes/juanjose.md` §3.0, §3.1 (D1–D7) y §3.3.
- `blog/README.md` (sintaxis) y `blog/hooks/reporte.py` (reglas que rompen el build); `blog/secciones/03-m1-datos-descriptivo.md`
  como ejemplo de estilo (cifras con fuente entre paréntesis, separador de miles con espacio —«1 998»— y coma decimal
  —«0,423», «53 %»—, comentarios `<!-- revisar: Juan José — … -->` para lo que sea interpretación tuya).
- `app/public/model/m3/perfil_nuevo.json` (campos `k_defecto`, `k_max`, `preferencias`).
- Todos los archivos de `results/data/m3/eda/`: `ficha.json`, `calidad.csv`, `diccionario.json`,
  `distribucion_actividad.json`, `interacciones_por_{usuario,destino,lugar}.csv`, `calificaciones.csv`,
  `concentracion.json`, `actividad_usuarios.json`, `coincidencia_preferencias.json`, `matriz_preferencias_tipo.csv`,
  `demografia_tipo.csv`, `pruebas_hipotesis.json`, `hipotesis.json`; y `configs/m3/eda.yaml` (umbral, criterio de
  veredicto, emparejamiento, semillas).
- Figuras ya generadas en `blog/docs/figures/m3/`: `cola_larga.png` (obligatoria), `lorenz.png`, `preferencias_tipo.png`,
  `calificaciones_origen.png` (míralas). Se enlazan como `figures/m3/<archivo>.png`.
- Entrada bibliográfica del conjunto: clave `mehra2024` en `blog/references.bib`. No agregues otras citas: si un concepto
  necesitaría referencia (p. ej. la corrección de sesgo de la V de Cramér, marcada `TODO(cita)` en el código), deja
  `<!-- TODO(cita): … -->` y no cites de memoria.

## Regla dura
**Toda cifra que escribas debe estar literalmente (o redondeada, indicándolo) en un archivo de `results/data/m3/eda/`** y
llevar la ruta del archivo (y la clave, si ayuda) entre paréntesis o en la `Fuente:` de la tabla/figura. Nada de cifras de
memoria ni calculadas a mano en el texto; si necesitas un número que no está en los archivos, NO lo escribas: anótalo en tu
respuesta como faltante. Los datos son generados (D4): ninguna frase atribuye los patrones a turistas reales.

## Qué escribir en `blog/secciones/07-m3-recomendacion.md`
Conserva el título `## M3 — Recomendación de destinos`, `### Análisis descriptivo` y los siete `####` en el orden actual
(`tests/test_blog.py` lo verifica). Reemplaza los comentarios `pendiente` de JJ-2.

1. **Caso de uso** (párrafo corto, SIN encabezado nuevo, entre el título del módulo y `### Análisis descriptivo`): la
   recomendación se muestra en la app/web de la empresa, en la sección de la nueva línea de turismo internacional, cuando el
   cliente entra a explorar viajes (y opcionalmente en un correo de campaña); se muestran K = 5 destinos por defecto
   (`k_defecto` del contrato de la app, `app/public/model/m3/perfil_nuevo.json`; núcleo §5.8) y se evalúan K ∈ {1, 3, 5, 10};
   información disponible en ese momento: historial de interacciones previas (visitas y reseñas), las preferencias que
   declara al registrarse y datos demográficos básicos (género, número de adultos y de niños); no se usan nombre ni correo
   (D6); un cliente nuevo solo tiene preferencias. Si algo de esto contradice el Spec o el contrato, no lo escribas y dilo
   en tu respuesta.
2. **Ficha del conjunto**: fuente con cita `[@mehra2024]`, fecha de descarga, usuarios, destinos (y que son 5 lugares),
   interacciones por origen y unión (D1), escala de calificaciones, densidad, real o sintético (cita literal de la fuente y
   conclusión de D4, con lo que implica para las conclusiones), licencia con la contradicción (D5), y que la fecha
   2024-01-23 es la **creación de la versión 1 en Kaggle** (no «publicación»). Una tabla `::: tabla m3-ficha`.
3. **Diccionario y calidad**: variables de usuarios y destinos con su nombre procesado; la fuente documenta 0 columnas
   (significado «no documentado por la fuente»); faltantes (de `calidad.csv`); inconsistencias del diccionario (1 000 ids =
   5 lugares; «mountain» no existe; `VisitDate`; vocabularios distintos de preferencias y tipo); qué no pasa a procesados
   (D6).
4. **Variable objetivo**: interacción implícita (D1); interacciones por usuario y por destino (cita `[[fig:m3-cola-larga]]`,
   la figura mínima del enunciado) y calificaciones por origen (`[[fig:m3-calificaciones]]` y/o una tabla).
5. **Estructura y heterogeneidad**: cola larga y concentración en populares (Gini, HHI, cuota top 10 % y 20 %, a nivel
   `destino_id` y `lugar`, frente al azar uniforme simulado; `[[fig:m3-lorenz]]` y una tabla `m3-concentracion`);
   usuarios con pocas interacciones (umbral, su justificación con D3 y la proporción; tabla o cifras de
   `actividad_usuarios.json`).
6. **Hipótesis explícitas**: una tabla o lista con cada H-M3-n: enunciado, justificación, evidencia esperada y figura/tabla
   (de `hipotesis.json`), y los resultados medidos: estadístico, p crudo, p ajustado (Holm, familia declarada), tamaño de
   efecto con IC (de `pruebas_hipotesis.json`). Usa `[[fig:m3-preferencias-tipo]]` para H-M3-1 con la tasa observada, la
   línea base exacta y la marginal. Declara el criterio de veredicto y los efectos mínimos como **convención nuestra** (están
   en `configs/m3/eda.yaml`), sin presentarlos como norma de la literatura.
7. **Implicaciones para el modelado**: (a) partición por usuario según D3 (cifras de `actividad_usuarios.json`: cuántas
   interacciones van a entrenamiento, validación y prueba, y que el grupo «pocas» existe en prueba); (b) negativos:
   uniformes vs. por popularidad a la luz de la concentración medida (si la concentración no supera al azar, el muestreo
   por popularidad aporta poco: dilo con la cifra); (c) variables de contenido disponibles (D2: tipo, estado, mejor época,
   popularidad, lugar; de usuario: preferencias y demografía) y lo que mostraron las hipótesis sobre su poder explicativo;
   (d) el problema de los 1 000 ids = 5 lugares (un modelo por id no puede distinguir ids del mismo lugar más que por la
   popularidad y el id; por eso el acierto por lugar de D2); (e) qué esperar si los datos no tienen patrón: métricas
   cercanas al azar y diferencias entre modelos menores que la variabilidad entre semillas; por eso importan las 30
   semillas y reportar media y desviación (núcleo §6).
8. **Veredicto de las hipótesis**: tabla `m3-veredictos` con id, enunciado corto y veredicto; las `pendiente` marcadas como
   tales («se cierra en JJ-10»).

Formato de figuras y tablas (título y fuente obligatorios; cada una citada en el texto con `[[fig:…]]`/`[[tab:…]]`; ids en
minúsculas con guiones y con prefijo `m3-`):
```text
::: figura m3-cola-larga
Título: …
Fuente: Elaboración propia a partir de results/data/m3/eda/distribucion_actividad.json; datos de [@mehra2024].
![Texto alternativo](figures/m3/cola_larga.png)
:::
```
Tono: claro, en español, sin exagerar; cada afirmación con una cifra o figura. Extensión razonable (no un informe de 20
páginas: prioriza lo que pide el enunciado).

## Al terminar
1. Corre `.venv/Scripts/mkdocs build --strict -f blog/mkdocs.yml` y `.venv/Scripts/python -m pytest -q tests/test_blog.py`;
   pega las salidas (en verde).
2. Responde con: un resumen de lo escrito por subsección; la lista de cifras usadas con su archivo y clave (para el
   cazador de alucinaciones); cualquier cifra que te faltó; y lo que dejaste en `<!-- revisar: Juan José — … -->`.
