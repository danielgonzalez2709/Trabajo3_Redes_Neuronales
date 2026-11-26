## Aplicación web

<!-- borrador DA-9b (redactor-tecnico, Sonnet) a partir de alucinaciones/prompts/DA-9b.md; pendiente de revisión de Daniel (DA-9). Sin cifras de resultados: los modelos reales llegan el sáb 28. -->

La aplicación es el punto donde los tres módulos dejan de ser experimentos y se vuelven herramientas que una persona de la
empresa puede usar sin saber programar. Está publicada en <https://trabajo3-redes-neuronales.vercel.app/> y su código vive en la
carpeta `app/` del repositorio. El enunciado la pide intuitiva para un usuario nuevo, con enlaces al reporte, al video
promocional y a los videos de contribución, y construida sobre los modelos ya guardados, sin reentrenar (apartado «Aplicación
web» del Anexo del Spec). La página de inicio presenta los tres módulos y trae esos enlaces; el del video promocional y el de los
videos individuales siguen en «pendiente» hasta que existan (`app/lib/enlaces.ts`).

<!-- pendiente: al momento de escribir esto la app sirve archivos de juguete (marcados con "juguete": true, y cada página lo avisa) y las capturas y cifras de este apartado deben salir de los modelos reales. -->

### Para qué sirve y quién la usa

La usa el personal de planeación, de seguridad vial y de producto de una empresa de transporte intermunicipal de pasajeros.
Cada módulo responde una pregunta de negocio distinta (textos de `app/app/page.tsx`):

- **Demanda y operación (M1):** «¿Cuántos pasajeros habrá y cuánta flota necesito?». Quien planea la operación elige una ruta,
  ve el pronóstico a 30 días y lo traduce en despachos, vehículos y conductores según sus supuestos.
- **Conducción distractiva (M2):** «¿El conductor está distraído?». Quien cuida la seguridad vial sube una imagen de la cabina y
  ve si el modelo dispararía una alerta con el umbral que prefiera.
- **Recomendación de destinos (M3):** «¿A dónde le sugiero viajar?». Quien atiende clientes consulta lo que se recomienda a un
  usuario existente o arma un perfil nuevo con las preferencias de viaje del cliente.

### Arquitectura

La app es un sitio **estático**: Next.js (TypeScript) configurado con `output: "export"` (`app/next.config.mjs`), que se publica
en Vercel con la carpeta `app` como raíz del proyecto. No hay servidor propio ni base de datos. Toda la inferencia ocurre en el
navegador de quien la usa:

- **M1 y M3** se calculan desde archivos JSON: el pronóstico de M1 ya viene calculado y el dimensionamiento de flota se recalcula
  en el navegador cuando el usuario cambia un supuesto; el recomendador de M3 aplica en el navegador la torre de usuario sobre
  las preferencias elegidas.
- **M2** corre un modelo en formato ONNX con ONNX Runtime Web, en su variante WebAssembly. Los archivos `.wasm` se sirven desde
  la propia app (`app/public/ort/`), sin CDN, de modo que la app también funciona en local sin internet (`app/lib/onnx.ts`).
- **Ningún dato del usuario sale del navegador:** la imagen que se sube a M2 se procesa en el cliente, y el código de la app no
  envía los perfiles ni las imágenes a ningún servicio.
- **La app nunca reentrena.** Solo lee los modelos guardados que exporta cada dueño de módulo (núcleo §3 del Spec, fila «App»).

Para levantarla en local basta un comando después de instalar las dependencias: `npm --prefix app run dev` (instrucciones
completas en la sección «App en local» del `README.md`).

<!-- revisar: Daniel — confirma que "no envía datos a ningún servicio" es correcto también para Vercel (analítica, registros): lo afirmo por lo que hace el código de la app, no por la configuración de la cuenta. -->

### Contratos de exportación

Cada módulo tiene un dueño distinto (M1: Camila, M2: José, M3: Juan José) y la app es de otra persona. Para que cada dueño exporte
sin tocar la app, el Spec fija en los apartados 5.4, 5.6 y 5.8 qué archivos deja cada módulo en `app/public/model/` y con qué
estructura. El esquema ejecutable es `app/lib/contratos.ts`: al cargar un archivo, la app lo valida y, si no cumple, falla con
un mensaje claro («archivo: ruta.del.campo: problema») en lugar de mostrar datos a medias. [[tab:app-contratos]] resume los
archivos de cada módulo.

::: tabla app-contratos
Título: Archivos que cada módulo exporta a la app
Fuente: núcleo §5.4, §5.6 y §5.8 del Spec (`docs/spec/SPEC.md`) y validadores de `app/lib/contratos.ts`.

| Módulo | Archivos en `app/public/model/` | Qué traen |
|---|---|---|
| M1 | `m1/pronosticos.json` | Fecha de origen, horizonte de 30 días, cuantiles y, por ruta, la historia y el pronóstico (punto y cuantiles) |
| M1 | `m1/operacion.json` | Parámetros de operación (cada uno con su fuente o marcado como supuesto), los controles que ve el usuario y casos de paridad |
| M2 | `m2/modelo.onnx` | La red, con dos salidas: `logits` y `mapas` (activaciones de la última capa convolucional) |
| M2 | `m2/meta.json` | Clases, agrupación en con alerta y sin alerta, umbral por defecto, tamaño de entrada, media y desviación, pesos de la cabeza para el mapa CAM y casos de paridad |
| M2 | `m2/ejemplos/`, `m2/casos/` | Imágenes de ejemplo de la página y entradas de los casos de paridad |
| M3 | `m3/destinos.json`, `m3/usuarios.json` | Destinos con su vector (*embedding*); usuarios con su historial y su top-K ya calculado |
| M3 | `m3/perfil_nuevo.json` | Lista de preferencias, codificación y capas de la torre de usuario, K por defecto y K máximo |
| M3 | `m3/casos_paridad.json` | Selecciones de ejemplo con el vector de usuario y el top-K esperados |
:::

**Por qué existen.** Hay dos razones. La primera es la **paridad entre Python y el navegador**: los modelos se entrenan en
Python y la app reimplementa su inferencia en TypeScript (el dimensionamiento de M1, el preprocesado y el mapa CAM de M2, la
torre de usuario de M3). Para que las dos implementaciones den lo mismo, cada archivo trae `casos_paridad` con entradas y
salidas calculadas en Python, y las pruebas de la app comprueban que el código TypeScript los reproduce; en M2, además, que el
ONNX ejecutado en ONNX Runtime Web reproduce a PyTorch (`app/tests/paridad_onnx.test.ts`). La segunda es el **desacople**: si
cada dueño respeta su contrato, puede reemplazar sus archivos por los reales sin editar la app.

Las pruebas de la app (`npm --prefix app test`) y su compilación (`npm --prefix app run build`) corren en el mismo trabajo de
integración continua que las pruebas de Python, el trabajo `pruebas`, que es obligatorio para fusionar a `main`
(`.github/workflows/ci.yml`); la paridad de los ONNX de juguete contra PyTorch está además en `tests/test_juguetes_app.py`. Las
pruebas de lo servido (`app/tests/servido.test.ts`) valen tanto para el juguete como para los modelos reales.

### Página «Demanda y operación»

Controles y resultados (`app/app/demanda/page.tsx`):

- **Ruta:** un selector con las rutas del archivo de pronósticos, mostradas como «origen → destino».
- **Pronóstico a 30 días con banda:** gráfico con la historia reciente, el pronóstico puntual y una banda hasta el cuantil
  elegido.
- **Flota y conductores:** tarjetas con la demanda total en 30 días al cuantil elegido, el pronóstico puntual, los despachos en
  30 días y los máximos diarios de vehículos y de conductores, más una tabla día a día.
- **Parámetros operativos:** los controles que declara `operacion.json`; el contrato exige como mínimo la **ocupación objetivo**
  y el **cuantil usado**, que son los dos parámetros que pide el enunciado. Cada control muestra de dónde sale su valor (una
  fuente citada o la etiqueta de supuesto), y hay un detalle desplegable con el cálculo del día de mayor demanda y otro con todos
  los parámetros.

Al cambiar el cuantil o la ocupación, el dimensionamiento se recalcula en el navegador sin volver a pronosticar.

<!-- figura: captura de la página de demanda con una ruta real, el cuantil por defecto y la banda de incertidumbre. -->
<!-- pendiente: captura y cifras con el modelo real (sáb 28) -->
<!-- pendiente: la función de dimensionamiento de la app es hoy un juguete (la real es la de Camila, núcleo §5.4, y se porta con su prueba de paridad en DA-6); no se citan despachos, vehículos ni conductores hasta entonces. -->

### Página «Conducción distractiva»

Controles y resultados (`app/app/conduccion/page.tsx`):

- **Imagen:** se elige una de las imágenes de ejemplo o se sube una propia. Al abrir la página se clasifica el primer ejemplo,
  para que haya algo que ver desde el principio.
- **Probabilidades y clase:** la clase con mayor probabilidad y la barra de probabilidad de cada una de las cinco clases,
  indicando a qué grupo (con alerta o sin alerta) pertenece cada una.
- **Alerta con umbral:** la alerta se dispara si la suma de las probabilidades de las clases del grupo «con alerta» es igual o
  mayor que el umbral elegido (`app/lib/clasificar.ts`). Un umbral más bajo da más alertas y más falsas alarmas; uno más alto da
  menos alertas y más distracciones sin detectar.
- **Mapa de interpretabilidad:** el mapa CAM de la clase asignada, calculado en el navegador como la suma de los mapas de
  activación ponderados con los pesos de la capa lineal de la clase (sin sesgo). El Spec decide que la cabeza de la red sea
  *global average pooling* más una capa lineal, de modo que CAM coincida con Grad-CAM salvo escala (núcleo §3 y §5.6). Con
  esa cabeza, $\partial y_c / \partial A_k(i,j) = w_{c,k}/(HW)$, así que Grad-CAM$_c$ = ReLU(CAM$_c$)$/(HW)$; una prueba
  automática lo comprueba con el gradiente calculado por PyTorch para todas las clases de los casos de paridad.

La página pinta el mapa sobre la imagen que ve la red: se aplica ReLU, se divide por el máximo de esa imagen (la escala es
relativa a cada imagen, solo para pintar), se amplía con interpolación bilineal y se colorea con viridis, con opacidad
ajustable y un selector para ver el mapa de otra clase.

<!-- figura: captura de la página de conducción con una imagen del conjunto real, las probabilidades, la alerta y el mapa CAM superpuesto. -->
<!-- pendiente: captura y cifras con el modelo real (sáb 28) -->
<!-- pendiente: el umbral por defecto y la agrupación de las cinco clases en con alerta y sin alerta vienen de José (meta.json); hoy la agrupación está marcada como provisional en la propia app. -->

### Página «Recomendación de destinos»

Controles y resultados (`app/app/recomendacion/page.tsx`):

- **Usuario existente:** se elige de una lista y se muestran su **historial** (destinos y calificación) y sus K destinos
  recomendados. Si el usuario no tiene historial, la página lo dice y las recomendaciones se calculan sin él.
- **Perfil nuevo:** una lista de preferencias con opciones para marcar (las define `perfil_nuevo.json`). La selección se
  codifica en un vector (una posición por opción), pasa por la torre de usuario y se puntúa contra los vectores de los destinos
  (producto punto más sesgo) (`app/lib/recomendar.ts`). Hasta que se marca al menos una opción, la página lo pide.
- **Top-K:** un control numérico de K, limitado por el máximo que declaran los archivos y por el número de destinos. Cada
  recomendación muestra su puesto y su puntaje.
- **Destinos con nombre repetido:** como en la fuente los destinos son pocos lugares repetidos muchas veces (núcleo §5.7 del
  Spec), cuando un nombre se repite la app lo muestra como «Nombre (#id)».

<!-- figura: captura de la página de recomendación con un perfil nuevo armado con las preferencias reales y su top-K. -->
<!-- pendiente: captura y cifras con el modelo real (sáb 28) -->
<!-- pendiente: las preferencias y los destinos reales llegan con los archivos de Juan José (DA-8). -->

### Limitaciones

- **M2 corre en la CPU del navegador.** El modelo se ejecuta con el proveedor WebAssembly y un solo hilo, que se eligió para no
  exigir cabeceras de aislamiento de origen cruzado (`app/lib/onnx.ts`). Eso lo hace independiente de la GPU, pero el tiempo de
  respuesta depende del equipo de quien la use y de qué tan grande sea la red exportada. <!-- pendiente: medir el tiempo por imagen con el modelo real (sáb 28) -->
- **El top-K de los usuarios existentes viene precalculado.** La app lee `top_k` de `usuarios.json`; solo el perfil nuevo se
  recalcula en el navegador. Por eso, cambiar K en un usuario existente solo recorta una lista ya calculada, que además tiene un
  tamaño máximo.
- **El pronóstico de M1 no se recalcula en la app.** Se exporta una vez desde Python con una fecha de origen fija; la app solo
  cambia el dimensionamiento a partir de él. Si cambian los datos o el modelo, hay que volver a exportar.
- **La imagen de M2 se redimensiona.** El preprocesado (estirar a un tamaño fijo, interpolación bilineal, RGB, escala de 0 a 1,
  normalización con media y desviación) debe ser idéntico al del entrenamiento (núcleo §5.6). Una foto con otra proporción o
  de una cámara distinta a las del conjunto de entrenamiento puede dar respuestas poco confiables.
- **Los supuestos operativos de M1 son del usuario.** Los parámetros sin fuente se muestran como supuestos; el resultado de
  flota y conductores es tan bueno como esos supuestos.

<!-- revisar: Daniel — las dos últimas limitaciones (imagen fuera del dominio de entrenamiento y supuestos operativos) son interpretación mía; las demás se desprenden del código y del Spec. -->
