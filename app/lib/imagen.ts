// Lectura de una imagen en el navegador y reducción al tamaño de entrada del modelo.
//
// PREPROCESADO (contrato `preprocesado` de m2/meta.json; el generador de Python, `preprocesar_imagen` en
// scripts/generar_juguetes_app.py, hace exactamente lo mismo): RGB sin transparencia → ESTIRAR al tamaño de entrada sin
// conservar la proporción ni recortar, con interpolación BILINEAL (filtro triangular cuya ventana se ensancha al reducir,
// como `PIL.Image.BILINEAR`) → escala 0-1 y normalización por canal (`preprocesar` en clasificar.ts).
// El navegador solo DECODIFICA la imagen (al tamaño original); el redimensionado se hace aquí, en TypeScript, para que no
// dependa del navegador (el lienzo escala distinto en cada uno) y se pueda probar sin él. Lo que puede diferir levemente
// de PIL es el decodificador del navegador (JPEG, gestión de color) y el redondeo: ±1 nivel por píxel.

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

export interface PixelesRgb {
  /** RGB uint8 aplanado (alto, ancho, canal). */
  rgb: Uint8ClampedArray;
  alto: number;
  ancho: number;
}

/** Tope de píxeles que se aceptan de entrada (una foto de 50 megapíxeles no cabe cómodamente en memoria). */
const MAX_PIXELES = 40_000_000;

/** Dibuja la imagen en un lienzo de su tamaño natural (sin escalar) y devuelve su RGB (la transparencia se ignora). */
export function decodificarRgb(img: CanvasImageSource & { naturalWidth?: number; naturalHeight?: number }): PixelesRgb {
  const ancho = img.naturalWidth ?? (img as HTMLCanvasElement).width;
  const alto = img.naturalHeight ?? (img as HTMLCanvasElement).height;
  if (!(ancho > 0 && alto > 0)) throw new Error("La imagen está vacía.");
  if (ancho * alto > MAX_PIXELES) throw new Error("La imagen es demasiado grande: use una de menos de 40 megapíxeles.");
  const lienzo = document.createElement("canvas");
  lienzo.width = ancho;
  lienzo.height = alto;
  const ctx = lienzo.getContext("2d", { willReadFrequently: true });
  if (!ctx) throw new Error("Este navegador no permite leer imágenes.");
  ctx.drawImage(img, 0, 0);
  const rgba = ctx.getImageData(0, 0, ancho, alto).data;
  const rgb = new Uint8ClampedArray(alto * ancho * 3);
  for (let i = 0, j = 0; i < rgba.length; i += 4, j += 3) {
    rgb[j] = rgba[i];
    rgb[j + 1] = rgba[i + 1];
    rgb[j + 2] = rgba[i + 2];
  }
  return { rgb, alto, ancho };
}

/** Pesos del filtro triangular para pasar de `entrada` a `salida` posiciones (misma construcción que `PIL.Image.BILINEAR`). */
function pesosBilineales(entrada: number, salida: number): { inicio: Int32Array; pesos: Float64Array[] } {
  const escala = entrada / salida;
  const ventana = Math.max(escala, 1); // se ensancha al reducir
  const inicio = new Int32Array(salida);
  const pesos: Float64Array[] = [];
  for (let i = 0; i < salida; i++) {
    const centro = (i + 0.5) * escala;
    const desde = Math.max(Math.trunc(centro - ventana + 0.5), 0);
    const hasta = Math.min(Math.trunc(centro + ventana + 0.5), entrada);
    const w = new Float64Array(Math.max(hasta - desde, 0));
    let suma = 0;
    for (let x = 0; x < w.length; x++) {
      const d = Math.abs((x + desde - centro + 0.5) / ventana);
      w[x] = d < 1 ? 1 - d : 0;
      suma += w[x];
    }
    for (let x = 0; x < w.length; x++) w[x] /= suma;
    inicio[i] = desde;
    pesos.push(w);
  }
  return { inicio, pesos };
}

/** Redondeo a uint8 entre pasadas, como PIL (al entero más cercano, recortado a 0..255). */
const aByte = (x: number): number => Math.min(Math.max(Math.floor(x + 0.5), 0), 255);

/**
 * Estira `origen` (RGB uint8 aplanado, alto × ancho × 3) a `alto` × `ancho` con interpolación bilineal: primero horizontal y
 * luego vertical, redondeando a uint8 entre pasadas.
 */
export function redimensionarBilineal(origen: PixelesRgb, alto: number, ancho: number): Uint8ClampedArray {
  const { rgb, alto: altoO, ancho: anchoO } = origen;
  if (rgb.length !== altoO * anchoO * 3) throw new Error("el tamaño de la imagen no coincide con sus píxeles");
  const h = pesosBilineales(anchoO, ancho);
  const intermedio = new Uint8ClampedArray(altoO * ancho * 3);
  for (let y = 0; y < altoO; y++) {
    for (let x = 0; x < ancho; x++) {
      const w = h.pesos[x];
      for (let c = 0; c < 3; c++) {
        let s = 0;
        for (let k = 0; k < w.length; k++) s += w[k] * rgb[(y * anchoO + h.inicio[x] + k) * 3 + c];
        intermedio[(y * ancho + x) * 3 + c] = aByte(s);
      }
    }
  }
  const v = pesosBilineales(altoO, alto);
  const salida = new Uint8ClampedArray(alto * ancho * 3);
  for (let y = 0; y < alto; y++) {
    const w = v.pesos[y];
    for (let x = 0; x < ancho; x++) {
      for (let c = 0; c < 3; c++) {
        let s = 0;
        for (let k = 0; k < w.length; k++) s += w[k] * intermedio[((v.inicio[y] + k) * ancho + x) * 3 + c];
        salida[(y * ancho + x) * 3 + c] = aByte(s);
      }
    }
  }
  return salida;
}

/** Imagen del navegador → RGB uint8 aplanado (alto, ancho, canal) al tamaño de entrada del modelo (preprocesado del contrato). */
export function aRgb(img: CanvasImageSource & { naturalWidth?: number; naturalHeight?: number }, alto: number, ancho: number): Uint8ClampedArray {
  return redimensionarBilineal(decodificarRgb(img), alto, ancho);
}
