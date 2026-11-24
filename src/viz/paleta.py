"""Paleta única de las figuras (portada del Trabajo 2, sin nada específico de ese trabajo).

Categórica de 8 tonos en orden fijo, rampa secuencial azul, tinta y superficie. Reglas:
- El color sigue a la ENTIDAD (modelo, ruta, clase), nunca a su posición en la figura.
- Un solo eje y; el texto va siempre en tinta (TINTA*), nunca en el color de la serie.
- Las figuras se dibujan siempre sobre SUPERFICIE clara.
- Aviso de contraste < 3:1 en aqua, amarillo y magenta (heredado de la validación previa): toda figura que use
  esos tonos lleva leyenda.
"""

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_TENUE = "#898781"  # ejes y etiquetas
CUADRICULA = "#e1e0d9"  # línea fina, sólida
EJE = "#c3c2b7"

CATEGORICA = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]

# Secuencial (magnitud: mapas de calor): un solo tono, claro → oscuro.
SECUENCIAL_AZUL = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
                   "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]

FUENTES = ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"]
ANCHO_LINEA = 2
TAMANO_MARCADOR = 8
