Tarea JO-3 (M2): casi duplicados y partición sin fuga por grupos. Te dirige José (sesión principal en Opus); rama `dev/jose`.
Tarea 🧠. Prueba primero, luego código.

## Lee antes de empezar
- `docs/spec/SPEC.md`: §5.5 (contrato de `indice.csv`), §5.9 (la `evidencia` lleva el SHA-256 de la partición), §6 / Anexo
  «Regla de comparación justa» (todos los modelos de M2 usan la misma partición), §8 (`test_fuga_m2.py`), §5.12 fila 4
  (duplicados y casi duplicados) y el Anexo «Módulo 2 → Tareas → 3. Partición sin fuga de información».
- `docs/spec/partes/jose.md` §3.0 (preprocesado de la app), §3.1 (D1–D5 de JO-1) y **§3.2 (D1–D5 de JO-3, decididos: síguelos
  al pie de la letra)**.
- `docs/investigacion/JO-1_fuentes_m2.md` §6 y C-2 a C-4 (aumento de datos guardado junto a las originales, sin identificar).
- `src/m2_conduccion/datos.py`, `configs/m2/datos.yaml`, `tests/test_datos_m2.py`, `tests/fixtures/m2/generar.py`,
  `src/comun/seeds.py`, `src/comun/cli.py` (cómo `run.py m2-datos` llama a `datos.main(cfg)`), `tests/test_no_network.py`.
- Como referencia de estilo, la partición de M3: `src/m3_recomendacion/particion.py` y `tests/test_fuga_m3.py`
  (no los modifiques).

## Enunciado que cubre (Anexo M2, tarea 3, literal)
«Definan y justifiquen entrenamiento, validación y prueba. Demuestren que no hay imágenes iguales o casi iguales (por ejemplo,
versiones aumentadas de una misma foto) en particiones distintas, y describan el método con que lo verificaron.»

## Decisiones (resumen de `jose.md` §3.2; si algo contradice el Spec o lo medido, PARA y repórtalo)
- D1 pHash 64 bits (`imagehash`, ya en requirements) de la imagen y de su espejo horizontal; distancia = mín(Hamming(a, b),
  Hamming(a, espejo(b))). Sobre las 224×224 de `data/processed/m2/imagenes/`.
- D2 ResNet-18 ImageNet (torchvision) congelada, `eval()`, vector GAP de 512, normalización de ImageNet, similitud coseno.
  Pesos: un script nuevo `scripts/descargar_pesos_m2.py` los baja UNA vez a `data/raw/m2/pesos/` (no versionado) usando la URL
  que expone torchvision (`ResNet18_Weights.IMAGENET1K_V1.url`) y verificando la huella que torchvision trae en el nombre del
  archivo; calcula y registra el SHA-256 completo medido. **No escribas hashes de memoria.** Los experimentos cargan los pesos
  desde ese archivo local, nunca de internet. Características en caché no versionada (p. ej.
  `data/processed/m2/cache/caracteristicas_resnet18.npy` + ids, en `.gitignore` si hace falta) para que JO-4 las reutilice;
  el código debe aceptar las características como argumento para poder probarlo sin pesos.
- D3 Arista si Hamming ≤ `umbral_hamming` o coseno ≥ `umbral_coseno` (ambos en la config); `grupo_duplicado` = componente
  conexa (networkx o union-find). Elige los umbrales a partir de la distribución medida (p. ej. distancia al vecino más
  cercano) y deja una figura de pares en la frontera: ~8 pares justo dentro y ~8 justo fuera de cada umbral, lado a lado, con
  su distancia/coseno y clase. Si una componente supera el 15 % de las 7 276 imágenes (parámetro en la config), el comando
  falla con un mensaje claro y NO escribe la partición: repórtalo con cifras.
- D4 70/15/15 por grupo, estratificada por clase (clase del grupo = clase mayoritaria; justifica el método, p. ej.
  `StratifiedGroupKFold` o asignación voraz por grupo), semilla de la config vía `src/comun/seeds.py`. Valores de `split`:
  `train`, `validacion`, `prueba` (mismos nombres que M3). Pares de clases distintas unidos por arista: no se tocan; se listan
  como hallazgo (etiqueta dudosa). Mira el esquema de `results/data/m2/eda/calidad.csv` (`categoria,elemento,valor,detalle`):
  si encaja, agrégalos ahí con una categoría nueva sin romper `tests/test_datos_m2.py`; si no, archivo aparte, y dilo.
- D5 No hay id de conductor: no lo inventes. Deja la limitación escrita en `resumen.json` (campo de texto) para el blog.

## Qué construir
P1. `tests/test_fuga_m2.py` (primero, en rojo):
   - Sintéticos (genéralos en el test o amplía `tests/fixtures/m2/`): una imagen, su copia exacta, su espejo, una versión con
     más brillo, una recortada/reescalada y varias imágenes distintas. Con características inyectadas, comprueba que las
     variantes caen en el mismo grupo y las distintas no; que el espejo lo detecta el hash con espejo y NO el pHash simple.
   - Invariantes de la partición: ningún `grupo_duplicado` en dos splits; ningún par con arista (Hamming ≤ umbral o coseno ≥
     umbral) cruza splits; todas las imágenes tienen grupo y split; proporciones por clase cerca de 70/15/15 (tolerancia
     justificada); determinismo (misma semilla → mismo `indice.csv` byte a byte; otra semilla → otra partición, mismas reglas);
     la guarda del 15 % dispara.
   - Mutantes: demuestra que el test falla si la partición se hace por imagen al azar ignorando grupos, o si se quita el espejo.
   - Sobre los datos reales versionados (lo que corre la CI, sin pesos ni .zip): lee `data/processed/m2/indice.csv` y un CSV
     versionado de pares con arista (p. ej. `results/data/m2/particion/pares_cercanos.csv`: id_a, id_b, hamming, coseno,
     criterio, clase_a, clase_b) y comprueba que ningún par ni grupo cruza splits y que la huella de `resumen.json` coincide.
P2. `src/m2_conduccion/duplicados.py` (hashes, características, grafo, grupos) y `src/m2_conduccion/particion.py` (asignación
   por grupo). Funciones puras, docstrings breves en español, ningún parámetro fijo en el código.
P3. Integración en `run.py m2-datos` SIN tocar `run.py` ni `src/comun/`: propón la forma más simple (p. ej. un bloque
   `particion:` en la config y una config `configs/m2/particion.yaml` que ejecute solo la partición a partir de las imágenes
   procesadas, sin requerir el .zip). Las pruebas existentes de JO-1 deben seguir en verde.
P4. Salidas: `indice.csv` con `grupo_duplicado` y `split` llenos (no cambies las demás columnas ni el orden de filas);
   `results/data/m2/particion/resumen.json` (semilla, método, umbrales y cómo se eligieron, conteos por split × clase,
   número de grupos, distribución de tamaños, el grupo más grande, pares por criterio, pares entre clases, pares que cruzan
   splits = 0, SHA-256 de `indice.csv` y de una huella de la partición (id, grupo, split ordenados), SHA-256 de los pesos,
   versiones de torch/torchvision/imagehash, dispositivo, tiempo); `pares_cercanos.csv`; la figura de la frontera en
   `blog/docs/figures/m2/` desde `src/viz/figs_m2.py` (archivo de José; usa `src/viz/estilo.py`).

## Reglas
- Linux: usa siempre `.venv/bin/python`. Sin internet salvo `scripts/descargar_pesos_m2.py`. Si la red falla, repórtalo.
- No toques archivos compartidos (`src/comun/`, `run.py`, `requirements.txt`, README, `SPEC.md`) ni archivos de otros.
- No commits, no push. No marques nada en PLAN.md.
- Prohibido inventar datos, umbrales «de la literatura», citas o cifras. Todo número del reporte sale de una ejecución real.
- Si guardas una decisión técnica no obvia, `mem_save` en engram con project `trabajo3_redes_neuronales`.

## Entrega (pega la salida real)
1. `.venv/bin/python scripts/descargar_pesos_m2.py` y el SHA-256 medido.
2. El comando de la partición dos veces (mismo `indice.csv`, compáralo con sha256sum) y su tiempo.
3. `.venv/bin/python -m pytest -q tests/test_fuga_m2.py -v` y `.venv/bin/python -m pytest -q -m "not lento"`.
4. Cifras clave: umbrales elegidos y por qué, número de grupos, tamaño del más grande, pares por criterio, pares entre
   clases, conteos split × clase. Ruta de la figura de la frontera.
5. Todo lo que quede como [PROPUESTO] o `TODO(dato-faltante)` para que José decida.
