## Introducción y caso de negocio

<!-- borrador DA-9a (redactor-tecnico, Sonnet); pendiente de revisión de Daniel (DA-9). Sin cifras de resultados: aún no existen. -->

Una empresa de transporte intermunicipal de pasajeros enfrenta tres retos, y este trabajo les responde con redes neuronales y
con una pregunta incómoda: ¿cuándo una red neuronal es de verdad la mejor herramienta?

1. **Saber cuántas personas viajarán y con qué recursos atenderlas.** La empresa necesita conocer la demanda de cada ruta durante
   los próximos 30 días para decidir cuántos vehículos despachar y con cuántos conductores. Un pronóstico que se queda corto
   deja pasajeros en la terminal; uno que se pasa deja vehículos y conductores ociosos.
2. **Detectar conductores que manejan distraídos.** La empresa quiere instalar cámaras en sus vehículos y generar una alerta
   cuando el conductor se distrae. Una alerta que no se dispara deja pasar un riesgo; una que se dispara sin motivo hace que los
   conductores dejen de prestarle atención.
3. **Ofrecer a sus clientes destinos de viaje acordes con sus preferencias.** Como valor agregado, la empresa lanzará una línea
   de turismo internacional con operadores turísticos, que empezará con destinos en India. Una buena recomendación genera un viaje
   y fideliza al cliente; una mala hace que ignore las siguientes.

(Los tres retos y su descripción vienen del apartado «Propósito» y de los tres módulos del enunciado, transcrito en el Anexo del
Spec, `docs/spec/SPEC.md`.)

### Qué resuelve cada módulo

| Reto | Módulo | Problema de aprendizaje | Qué entrega |
|---|---|---|---|
| Demanda y operación | **M1** | Series de tiempo: pronóstico de pasajeros por ruta a 30 días | Pronóstico con un cuantil alto y su traducción a flota y conductores por día |
| Seguridad vial | **M2** | Clasificación de imágenes de conductores | Clase de comportamiento, probabilidad por clase y alerta según un umbral |
| Oferta a clientes | **M3** | Sistema de recomendación | Los K destinos recomendados a cada usuario, existente o nuevo |

- **M1 (demanda y operación).** Con los datos abiertos de la Superintendencia de Transporte, se construyen series diarias de
  pasajeros por ruta, se comparan modelos de referencia (un pronóstico ingenuo estacional y un modelo estadístico o lineal) con
  perceptrones multicapa y arquitecturas secuenciales, y el pronóstico se convierte en decisiones: cuántos despachos y
  vehículos por ruta y por día, cuántos conductores, qué conviene hacer en una temporada alta y si dimensionar con el pronóstico
  puntual o con un cuantil alto. Los datos y su análisis descriptivo se presentan en la sección «M1 — Demanda de pasajeros: datos
  y análisis descriptivo».
- **M2 (conducción distractiva).** Se clasifican imágenes de conductores en cinco clases de comportamiento y se decide cuándo
  alertar, con un mapa de interpretabilidad que muestra en qué parte de la imagen se apoya la decisión.
- **M3 (recomendación de destinos).** Se recomienda a cada usuario un conjunto de destinos a partir de su historial y de las
  preferencias de otros usuarios, y se estudia qué pasa con un cliente sin historial y si las recomendaciones concentran a los
  clientes en pocos destinos populares.

<!-- pendiente: las secciones de M2 y M3 (José, Juan José) pueden afinar estas descripciones; aquí solo se resume el enunciado. -->

Los tres módulos se integran en una aplicación web publicada que usa los modelos ya entrenados (no reentrena), y todo el trabajo
se documenta en este reporte reproducible, con su repositorio y su video promocional (enlaces al inicio del reporte).

### Las redes neuronales no siempre son la mejor herramienta

El enunciado lo dice sin rodeos: las redes neuronales no siempre son la mejor herramienta, y parte del reto es averiguar, con
evidencia y comparaciones justas, qué aporta cada una en cada problema, qué no, y cuánto vale esa diferencia para la empresa. Por eso
en cada módulo la red se compara con un modelo de referencia bajo condiciones explícitas y equivalentes (núcleo §6 del Spec,
que concreta la «Regla de comparación justa» del enunciado):

- **Mismos datos:** el mismo preprocesamiento y las mismas particiones para todos los modelos del módulo.
- **Presupuesto de búsqueda explícito:** cuántas configuraciones se probaron por familia de modelos, también para los de
  referencia, y el tiempo de cómputo total; una red que «gana» tras muchos intentos contra un modelo ajustado una sola vez no
  es una comparación justa sin esa aclaración.
- **Varias corridas independientes:** la configuración final de cada red se entrena con al menos 30 semillas distintas, y se
  reportan media, desviación estándar, mejor y peor valor de cada métrica.
- **Complejidad:** el número de parámetros entrenables (o estimados) de cada modelo.

La discusión final de cada módulo responde qué aportó la red frente al modelo de referencia con base en las métricas, su
variabilidad entre semillas, el costo de cómputo, la interpretabilidad y las consecuencias para el negocio. Este reporte puede
concluir que, para alguno de los problemas, una referencia sencilla es suficiente; esa conclusión sería un resultado válido, no
un fracaso.

<!-- revisar: Daniel — la última frase es una postura editorial del redactor; confirma que quieres mantenerla en la introducción. -->

### Cómo se trabajó

El trabajo es de un equipo de cinco personas y se hizo con herramientas de inteligencia artificial, que se equivocan, a veces con
total seguridad. Por eso el reporte documenta cómo se usó la IA (sección «Uso de IA»), qué errores se cazaron (sección
«Cacería de la alucinación») y cómo reproducir cada resultado (sección «Reproducibilidad»).
