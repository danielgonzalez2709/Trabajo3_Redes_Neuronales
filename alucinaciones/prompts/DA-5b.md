# Prompt DA-5b — implementador-web (Sonnet) — 2026-11-24 — orquesta: Daniel

Actúa como el agente definido en `.claude/agents/implementador-web.md` (léelo primero). Repositorio:
`C:\Users\danie\dev\Trabajo 3 Redes Neuronales\Trabajo3_Redes_Neuronales` (rama `dev/daniel`, commit «DA-5: esqueleto de la
app…»; **no hagas commit ni push**). Next.js ya está en 16.4.6: no cambies versiones. No toques `docs/`.

Contexto: DA-5 pasó por revisor-spec (aprobado con observaciones sobre los contratos) y revisor-calidad (2 bloqueantes). Los
contratos de `app/lib/contratos.ts` son los que usarán Camila y Andrés (M1), José (M2) y Juan José (M3) para exportar, así que
deben servir para los modelos **reales**, no solo para el juguete. Aplica estas decisiones (de Daniel) y regenera los juguetes:

## A. M1 `operacion.json` (para la función real de Camila, núcleo §5.4)
- Cada parámetro es `{valor, unidad, fuente | supuesto: true, nota?}` (la `fuente` es la cita textual; la UI la muestra en una
  ayuda junto al parámetro). Agrupados en `globales`, `por_ruta[ruta_id]` (p. ej. tiempo de ciclo) y `por_clase[clase]`
  (p. ej. capacidad) y `composicion_clases[ruta_id]` (participación de cada clase de vehículo, estimada con train).
- `controles` referencian una ruta de parámetro (p. ej. `globales.ocupacion_objetivo`). **Claves obligatorias** documentadas en
  el contrato: `globales.ocupacion_objetivo` y `globales.cuantil` (lo pide el Anexo: «al menos dos parámetros»).
- `casos_paridad[].entrada` incluye `ruta_id`, `fecha`, `demanda` y los parámetros efectivos; `salida` trae `despachos`,
  `vehiculos`, `conductores` y los pasos intermedios que la función exponga (para depurar en vivo).
- La función de juguete se adapta a este formato y **todos** sus supuestos son parámetros visibles (bloqueante 1 de calidad):
  viajes por vehículo al día y conductores por vehículo con `supuesto: true`, mostrados en la página.
- Prueba de que `ruta_regreso_id` de `pronosticos.json` existe entre las rutas.

## B. M3 `perfil_nuevo.json` (para un recomendador real de Juan José, núcleo §5.8)
- Formato general de **dos torres lineal/MLP**: `preferencias` (lista con `id`, `etiqueta`, `opciones`), una codificación
  documentada de la selección a un vector de entrada (one-hot por opción, en un orden fijo), `torre_usuario` como lista de capas
  `{W (salida × entrada, como torch.nn.Linear.weight), b, activacion: "relu"|"ninguna"}`, y en `destinos.json` un `embedding`
  por destino más un `sesgo` opcional. Puntaje = ⟨u, v_d⟩ + sesgo_d; se excluyen del top-K los destinos ya vistos (si aplica).
- `usuarios.json` agrega `modelo` (cómo se produjo el top-K precomputado).
- Los `casos_paridad` van en **`m3/casos_paridad.json`** aparte (como dice §5.8) con selección → top-K y puntajes.
- El juguete usa este formato con pesos aleatorios con semilla; la «regla de afinidad» desaparece. Mantén `embedding_2d` para
  la figura.
- Prueba: usuario sin historial (revisor-calidad 7).

## C. M2 `meta.json` (núcleo §5.6)
- Campo `preprocesado`: `{redimensionado: "estirar", interpolacion: "bilineal", canales: "RGB", escala: "0-1", luego media y
  desviación}`. `app/lib/imagen.ts` y el generador de Python deben hacer **lo mismo** y decirlo en un comentario.
- Un caso de paridad **desde un archivo de imagen** de ejemplo (no ya redimensionado): probabilidades esperadas calculadas en
  Python con el mismo preprocesado; la prueba de la app lo compara con tolerancia razonable (documenta cuál y por qué: el
  redimensionado del navegador puede diferir levemente).
- `entrada_rgb` de los casos grandes puede ir en un archivo aparte (`m2/casos/<id>.json`); máximo 3 casos.
- El contrato del mapa es **CAM** (Σ w_c·mapa, sin sesgo) mientras DA-7 demuestra la equivalencia con Grad-CAM de PyTorch;
  dilo en el comentario del contrato.

## D. Calidad (revisor-calidad)
1. (bloqueante) Supuestos de vehículos y conductores visibles (ver A).
2. (bloqueante) La tarjeta «Pasajeros en 30 días» muestra la demanda al cuantil elegido: rotúlala «Demanda en 30 días al
   cuantil X» y muestra aparte el pronóstico puntual.
3. Revocar las `URL.createObjectURL` al reemplazar la imagen.
4. Quitar los `eslint-disable` sin efecto (no hay ESLint) o configurarlo; prefiero quitarlos.
5. Quitar props sin uso de `Segmentado` (`leyendaVisible`, `ayudaId`, `extra`).
6. `recomendacion/page.tsx`: acotar `k` a `kMax` en todos los usos.
7. Marca «provisional» también en las tarjetas de vehículos y conductores mientras la función sea de juguete.
8. `aria-live` solo en el texto de estado de conducción.
9. Nits: `set(seleccion)` fuera de la comprensión; `Image.fromarray` sin `mode`; comentario vs. código de
   `conductores_por_vehiculo`; `Object.hasOwn` en lugar de `in`; quitar la comprobación repetida de `pesos_cabeza.length`;
   `if` en vez de `&&` como sentencia en `useCarga`; estilos en línea a CSS.
10. `fecha_origen` de juguete: usa la última fecha de la serie sintética y di en el `aviso` que el real será el origen del
    pronóstico de Andrés.

## Aceptación
`npm --prefix app test` y `npm --prefix app run build` en verde; `.venv\Scripts\python -m pytest -q` en verde; regenera los
juguetes con `scripts/generar_juguetes_app.py` y comprueba con `npm --prefix app run dev` + peticiones HTTP que las 4 páginas y
los JSON cargan (y, si puedes, en un navegador sin errores de consola); deja el servidor apagado. Entrega: resumen final de
cada contrato (campos), archivos cambiados, salidas reales, dudas.
