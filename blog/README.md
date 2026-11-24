# Blog del reporte — guía para redactar

El reporte es **una sola entrada de blog** (`docs/index.md`) que une las secciones de `secciones/`. Cada integrante escribe
**solo sus archivos** de `secciones/` (el comentario `pendiente` del inicio de cada archivo dice quién es el dueño y su ID de tarea).

## Ver el blog mientras se escribe

```bash
.venv\Scripts\mkdocs serve -f blog/mkdocs.yml
```
Abre <http://127.0.0.1:8000> y se recarga al guardar. Antes de hacer commit:

```bash
.venv\Scripts\mkdocs build --strict -f blog/mkdocs.yml
```
Si falla, el mensaje dice qué regla se rompió. **No se fusiona un PR con el build en rojo.**

## Sintaxis

| Qué | Cómo se escribe |
|---|---|
| Ecuación en línea | `$f(\mathbf{x})$` |
| Ecuación en bloque | `$$ ... $$` en líneas aparte |
| Figura (APA) | ver abajo |
| Tabla (APA) | igual que la figura, con `::: tabla <id>` y una tabla Markdown dentro |
| Citar una figura o tabla | `[[fig:<id>]]` o `[[tab:<id>]]` → se convierte en "Figura N" / "Tabla N" con enlace |
| Cita entre paréntesis | `[@clave]` → (Autor, año), la clave es `apellidoAÑO` y debe existir en `references.bib` |
| Cita narrativa | `@clave define…` → Autor (año) define… |
| Varias citas / página | `[@a2020; @b2021]`, `[@a2020, p. 3]` |
| Nota para el equipo (no se publica) | `<!-- … -->` (las citas dentro de comentarios no cuentan) |

Figura (la numeración es automática; **título y fuente son obligatorios**):

```text
::: figura <id>
Título: ...
Fuente: Elaboración propia a partir de results/....
![Texto alternativo](figures/<archivo>.png)
:::
```
- Las imágenes van en `docs/figures/` y las genera el código: **no se editan a mano**.
- Para una figura interactiva de Plotly: dentro del bloque, `incluir: figures/<archivo>.html`.
- El `id` usa minúsculas, números y guiones.
- Toda cifra del blog sale de un archivo de `results/` o `data/processed/` (nunca de datos sintéticos).

## Plantilla común de análisis descriptivo (núcleo §5.12)
Las secciones 03 (M1), 06 (M2) y 07 (M3) abren con «Análisis descriptivo» y estas siete subsecciones, en este orden:
Ficha del conjunto · Diccionario y calidad · Variable objetivo · Estructura y heterogeneidad · Hipótesis explícitas ·
Implicaciones para el modelado · Veredicto de las hipótesis. `tests/test_blog.py` lo verifica.

## Bibliografía
`references.bib` está vacío al inicio. Toda entrada se copia del BibTeX oficial del DOI (`https://doi.org/<doi>` con
`Accept: application/x-bibtex`) y se contrasta con Crossref. Si necesitas una referencia nueva, pídela a quien lleva la
bibliografía (Juan José) o al `cazador-alucinaciones`; **nunca de memoria**.
