# Video promocional — guion (borrador para revisar con el equipo)

> Enunciado (Anexo, Entregables 5): video de 2 a 3 minutos que presente la aplicación como la solución a un problema de la
> empresa de transporte y genere entusiasmo por usarla. Aparecen los 5 integrantes, cada uno presentando lo suyo.
> Estética: fondo oscuro, tipografía grande, una idea por plano, la app dentro de un dispositivo, transiciones lentas.
> Remotion para lo animado; los clips de cada integrante se graban el **sáb 28** (coordina Daniel).
> **Duración total: 2:30** (rango permitido 2:00–3:00; objetivo 2:00–2:50).
> Reglas: ninguna cifra de resultados todavía. Donde irá una se marca `[CIFRA: …]` y se llena con los resultados reales
> antes de editar. Frases cortas, en español. "Pantalla" = grabación de la app en 1920×1080; "Remotion" = animación;
> "Clip" = persona del equipo a cámara.

| # | Tiempo | Dur. | Qué se ve | Qué se dice | Quién |
|---|---|---|---|---|---|
| 1 | 0:00–0:10 | 10 s | Remotion: negro; aparece letra por letra **"¿Cuántos viajarán mañana?"**, luego un bus que cruza una ruta en un mapa simple | (solo música) | Remotion |
| 2 | 0:10–0:25 | 15 s | Clip: Daniel a cámara. Remotion superpone tres tarjetas, una por reto: **Demanda**, **Seguridad**, **Destinos** | "Una empresa de transporte de pasajeros tiene tres retos. Saber cuántas personas viajarán y con qué flota atenderlas. Detectar conductores distraídos. Y ofrecer a sus clientes destinos que les gusten." | Daniel |
| 3 | 0:25–0:35 | 10 s | Pantalla: página de inicio de la app con las tres tarjetas de módulos; el cursor pasa por cada una | "Los tres retos caben en una sola aplicación. Corre en tu navegador. Te la mostramos." | Daniel (voz en off) |
| 4 | 0:35–1:05 | 30 s | Pantalla: módulo **Demanda y operación**. Se elige una ruta; aparece el pronóstico a 30 días con su banda de incertidumbre; se mueven los supuestos (cuantil y otro parámetro operativo) y cambian despachos, vehículos y conductores. Remotion resalta la banda. Cierra con un clip corto de Camila | Andrés: "Elige una ruta y mira cuántos pasajeros se esperan en los próximos 30 días, con su banda de incertidumbre." Camila: "¿Prefieres no dejar a nadie en la terminal? Sube el cuantil y mira cuánta flota y cuántos conductores harían falta. [CIFRA: dato de operación, si aplica]" | Andrés (pronóstico), Camila (operación) |
| 5 | 1:05–1:30 | 25 s | Pantalla: módulo **Conducción distractiva**. Se elige una imagen de ejemplo y se sube otra; aparecen la clase, la probabilidad de cada clase, la decisión de alerta y el mapa de interpretabilidad; se mueve el umbral y la alerta cambia | "Sube una foto de la cabina. El modelo dice qué está haciendo el conductor y qué tan seguro está. Tú eliges el umbral: más sensible o más tranquilo. Y el mapa te muestra dónde miró la red para decidir. [CIFRA: desempeño del modelo]" | José |
| 6 | 1:30–1:55 | 25 s | Pantalla: módulo **Recomendación de destinos**. Se elige un usuario existente y se ven su historial y sus K destinos; luego se pasa a perfil nuevo, se marcan preferencias y aparece la lista | "Elige un usuario y mira su historial y los destinos que le recomendamos. ¿Un cliente nuevo? Marca lo que le gusta y su lista aparece al instante. [CIFRA: desempeño del recomendador]" | Juan José |
| 7 | 1:55–2:15 | 20 s | Remotion: texto grande **"¿Por qué confiar?"**; filas animadas "red neuronal" frente a "modelo de referencia", mismas reglas para ambos, con cajas de variabilidad entre semillas (figura del reporte); sin ganador anunciado | Camila: "No te prometemos magia. Cada red compite contra un modelo de referencia, con los mismos datos y el mismo presupuesto de búsqueda." Andrés: "Repetimos cada entrenamiento con [CIFRA: número de semillas] semillas, para ver cuánto varía. Y te contamos qué ganó y qué no." | Camila, Andrés |
| 8 | 2:15–2:25 | 10 s | Clip grupal: los 5 a cámara, nombres en pantalla | Todos: "Somos Daniel, Camila, Andrés, José y Juan José, de la Universidad Nacional." Daniel: "Pruébala." | Todos / Daniel |
| 9 | 2:25–2:30 | 5 s | Remotion: URL de la app + QR + enlaces al reporte y al repositorio + "UNAL · Redes neuronales · 2026-02" | (música final) | Remotion |

Suma: 10 + 15 + 10 + 30 + 25 + 25 + 20 + 10 + 5 = 150 s = **2:30**.

## Quién habla (reparto)
- Daniel: el problema y la presentación de la app (escenas 2 y 3) y el llamado final ("Pruébala").
- Andrés: pronóstico de demanda (4) y la mitad de "por qué confiar" (7).
- Camila: operación de flota (4) y comparación justa (7).
- José: conducción distractiva (5).
- Juan José: recomendación de destinos (6).
- Los 5 juntos: escena 8.

## Notas del guion
- Hoy la app usa datos y modelos de juguete (hay un aviso visible en la interfaz). **No se graba la pantalla con datos de
  juguete como si fueran resultados**: las escenas 4 a 6 se graban cuando la app tenga los modelos reales o, si no llegan,
  se avisa al equipo y se decide.
- El mapa de interpretabilidad (escena 5) llega con DA-7. Si no está listo el sáb 28, la escena 5 se acorta.
- Todo `[CIFRA: …]` se llena con valores de `results/data/` o se elimina la frase; nunca se inventa.
- No se afirma que la red gane: la escena 7 dice qué se compara y cómo, no el resultado.

## Tomas a grabar — sáb 28
| Toma | Quién | Qué | Dónde | Duración |
|---|---|---|---|---|
| T1 | Daniel | Escena 2 a cámara, 3 repeticiones (natural, lenta, con energía) | Luz natural de frente, fondo liso | ~15 s por toma |
| T2 | Daniel | Voz en off de la escena 3 | Lugar silencioso, micrófono cerca | ~10 s |
| T3 | Andrés | Línea de la escena 4 y frase de la escena 7 | Mismo set de T1 | ~10 s + ~10 s |
| T4 | Camila | Línea de la escena 4 y frase de la escena 7, a cámara | Mismo set | ~12 s + ~10 s |
| T5 | José | Escena 5 a cámara o voz en off | Mismo set | ~25 s |
| T6 | Juan José | Escena 6 a cámara o voz en off | Mismo set | ~25 s |
| T7 | Los 5 | Plano grupal de la escena 8, caminando hacia la cámara; Daniel dice "Pruébala" | Exterior o salón amplio, luz natural | ~15 s |
| T8 | Todos | Cada quien, 5 s mirando a cámara sin hablar (plano de recurso) | Mismo set | 5 s por persona |
| P1 | Daniel | Grabación de pantalla: página de inicio | Navegador, 1920×1080, cursor lento | ~15 s |
| P2 | Camila | Grabación de pantalla: módulo de demanda (ruta, banda, cuantil y otro parámetro) | Ídem | ~40 s |
| P3 | José | Grabación de pantalla: módulo de conducción (ejemplo, subir imagen, mapa, umbral) | Ídem | ~35 s |
| P4 | Juan José | Grabación de pantalla: módulo de recomendación (existente y perfil nuevo) | Ídem | ~35 s |

Formato: celular horizontal en 4K/30 si se puede; micrófono de solapa o el del celular cerca; audio aparte si se puede.

## Se arma en Remotion (sin grabar)
- Escena 1: gancho con texto y animación de la ruta.
- Escena 2: las tres tarjetas (Demanda, Seguridad, Destinos) sobre el clip de Daniel.
- Escenas 4 a 6: marcos de dispositivo para la pantalla grabada, resaltados y rótulos.
- Escena 7: animación de comparación (figura de cajas de las semillas, con los datos reales del reporte).
- Escenas 8 y 9: nombres en pantalla, tarjeta final con URL y QR.
- Música: libre de derechos, con licencia verificada (pendiente).

## Pendiente
- Cifras `[CIFRA: …]` con los resultados reales de los tres módulos.
- QR y tarjeta final: app https://trabajo3-redes-neuronales.vercel.app/ · reporte https://danielgonzalez2709.github.io/Trabajo3_Redes_Neuronales/
- Música con licencia verificada.
- Revisión del guion por el equipo (jue 26).
