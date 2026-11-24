// Lectura de una imagen en el navegador y reducción al tamaño de entrada del modelo (solo cliente).

/** Carga un archivo o una URL como imagen decodificada. */
export function cargarImagen(origen: File | string): Promise<HTMLImageElement> {
  return new Promise((resolver, rechazar) => {
    const img = new Image();
    const url = typeof origen === "string" ? origen : URL.createObjectURL(origen);
    img.onload = () => {
      if (typeof origen !== "string") URL.revokeObjectURL(url);
      resolver(img);
    };
    img.onerror = () => {
      if (typeof origen !== "string") URL.revokeObjectURL(url);
      rechazar(new Error("No se pudo leer la imagen: use un archivo PNG, JPG o WebP."));
    };
    img.src = url;
  });
}

/** Dibuja la imagen en un lienzo de alto×ancho (se estira) y devuelve el RGB uint8 aplanado (alto, ancho, canal). */
export function aRgb(img: CanvasImageSource, alto: number, ancho: number): Uint8ClampedArray {
  const lienzo = document.createElement("canvas");
  lienzo.width = ancho;
  lienzo.height = alto;
  const ctx = lienzo.getContext("2d", { willReadFrequently: true });
  if (!ctx) throw new Error("Este navegador no permite leer imágenes.");
  ctx.imageSmoothingQuality = "high";
  ctx.drawImage(img, 0, 0, ancho, alto);
  const rgba = ctx.getImageData(0, 0, ancho, alto).data;
  const rgb = new Uint8ClampedArray(alto * ancho * 3);
  for (let i = 0, j = 0; i < rgba.length; i += 4, j += 3) {
    rgb[j] = rgba[i];
    rgb[j + 1] = rgba[i + 1];
    rgb[j + 2] = rgba[i + 2];
  }
  return rgb;
}
