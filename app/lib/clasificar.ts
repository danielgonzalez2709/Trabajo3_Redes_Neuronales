// Lógica de M2 que no depende del navegador: preprocesamiento, softmax, decisión de alerta y CAM. Dominio puro.
// El CAM se calcula aquí (con prueba de paridad contra `meta.json`) y se prepara para pintarlo (DA-7): ReLU + normalización,
// remuestreo bilineal al tamaño de entrada, mapa de color viridis y mezcla con la imagen. El dibujo en el lienzo está en
// components/MapaCam.tsx; aquí no hay DOM.
import type { GrupoAlerta, MetaM2 } from "./contratos";

/** RGB uint8 aplanado (alto, ancho, canal) → tensor float32 [1, 3, alto, ancho] normalizado con la media y desviación del meta. */
export function preprocesar(rgb: ArrayLike<number>, meta: Pick<MetaM2, "tamano_entrada" | "media" | "desviacion">): Float32Array {
  const { alto, ancho } = meta.tamano_entrada;
  if (rgb.length !== alto * ancho * 3) throw new Error(`la imagen debe tener ${alto}×${ancho}×3 valores (tiene ${rgb.length})`);
  const salida = new Float32Array(3 * alto * ancho);
  for (let c = 0; c < 3; c++) {
    for (let i = 0; i < alto * ancho; i++) {
      salida[c * alto * ancho + i] = (rgb[i * 3 + c] / 255 - meta.media[c]) / meta.desviacion[c];
    }
  }
  return salida;
}

/** Softmax estable (resta el máximo). */
export function softmax(logits: ArrayLike<number>): number[] {
  const xs = Array.from(logits);
  const m = Math.max(...xs);
  const e = xs.map((x) => Math.exp(x - m));
  const s = e.reduce((a, b) => a + b, 0);
  return e.map((x) => x / s);
}

export function indiceMaximo(xs: ArrayLike<number>): number {
  let k = 0;
  for (let i = 1; i < xs.length; i++) if (xs[i] > xs[k]) k = i;
  return k;
}

/** P(con alerta) = suma de las probabilidades de las clases del grupo «con alerta». */
export function probabilidadConAlerta(probabilidades: number[], meta: Pick<MetaM2, "clases" | "grupo_alerta">): number {
  return meta.clases.reduce((s, c, i) => s + (meta.grupo_alerta[c.id] === "con_alerta" ? probabilidades[i] : 0), 0);
}

export interface DecisionAlerta {
  /** P(con alerta). */
  probabilidad: number;
  grupo: GrupoAlerta;
}

/** Hay alerta si P(con alerta) >= umbral. */
export function decidirAlerta(probabilidades: number[], meta: Pick<MetaM2, "clases" | "grupo_alerta">, umbral: number): DecisionAlerta {
  const probabilidad = probabilidadConAlerta(probabilidades, meta);
  return { probabilidad, grupo: probabilidad >= umbral ? "con_alerta" : "sin_alerta" };
}

/** CAM de una clase: Σ_c pesos[clase][c] · mapas[c] (sin sesgo). `mapas` va aplanado C·H·W; devuelve H·W. */
export function calcularCam(mapas: ArrayLike<number>, forma: [number, number, number], pesosClase: number[]): number[] {
  const [canales, alto, ancho] = forma;
  const cam = new Array<number>(alto * ancho).fill(0);
  for (let c = 0; c < canales; c++) {
    for (let i = 0; i < alto * ancho; i++) cam[i] += pesosClase[c] * mapas[c * alto * ancho + i];
  }
  return cam;
}

// ------------------------------------------------------------------------------------------------ CAM para pintar (DA-7)
// CAM_c(i, j) = Σ_k w_{c,k} · A_k(i, j), con A_k el mapa k de la última convolución (C × H × W) y w_c la fila c de
// `pesos_cabeza` (sin sesgo). Con cabeza GAP + lineal, el CAM coincide con Grad-CAM salvo el factor 1/(H·W) y la ReLU
// (prueba en tests/test_juguetes_app.py). Para PINTARLO (y solo para eso) se aplica:
//   1. ReLU: M(i, j) = max(CAM_c(i, j), 0)  — solo las zonas que empujan el logit de la clase hacia arriba;
//   2. normalización por imagen: M / max(M) ∈ [0, 1]; si max(M) ≤ 0 (o no es finito) el mapa es todo cero (nunca NaN).
// Esta escala es RELATIVA a cada imagen: dos imágenes con el mismo color no tienen la misma influencia absoluta.

/** ReLU y normalización a [0, 1] por imagen (solo para pintar). Mapa todo ≤ 0, vacío o sin máximo finito → todo cero. */
export function normalizarCam(cam: ArrayLike<number>): Float32Array {
  const salida = new Float32Array(cam.length);
  let maximo = 0;
  for (let i = 0; i < cam.length; i++) {
    const v = cam[i];
    if (Number.isFinite(v) && v > maximo) maximo = v;
  }
  if (!(maximo > 0) || !Number.isFinite(maximo)) return salida;
  for (let i = 0; i < cam.length; i++) {
    const v = cam[i];
    salida[i] = Number.isFinite(v) && v > 0 ? v / maximo : 0;
  }
  return salida;
}

/**
 * Remuestreo bilineal de un mapa (alto × ancho, aplanado por filas) a altoS × anchoS, con la convención de CENTROS de píxel
 * (la de `torch.nn.functional.interpolate(..., mode="bilinear", align_corners=False)`): el píxel de salida (y, x) toma la
 * posición de origen u = (x + 0.5)·ancho/anchoS − 0.5 (ídem para v), recortada a [0, ancho − 1], e interpola entre los
 * cuatro vecinos: (1−fy)(1−fx)·m[y0,x0] + (1−fy)fx·m[y0,x1] + fy(1−fx)·m[y1,x0] + fy·fx·m[y1,x1].
 * Al ampliar, las esquinas de la salida valen exactamente las esquinas del mapa; un mapa constante sigue constante.
 */
export function remuestrearBilineal(mapa: ArrayLike<number>, alto: number, ancho: number, altoS: number, anchoS: number): Float32Array {
  if (!(alto > 0 && ancho > 0 && altoS > 0 && anchoS > 0)) throw new Error("los tamaños del remuestreo deben ser positivos");
  if (mapa.length !== alto * ancho) throw new Error(`el mapa debe tener ${alto}×${ancho} valores (tiene ${mapa.length})`);
  const posiciones = (n: number, nS: number) => {
    const i0 = new Int32Array(nS);
    const i1 = new Int32Array(nS);
    const f = new Float64Array(nS);
    for (let s = 0; s < nS; s++) {
      const u = Math.min(Math.max((s + 0.5) * (n / nS) - 0.5, 0), n - 1);
      i0[s] = Math.floor(u);
      i1[s] = Math.min(i0[s] + 1, n - 1);
      f[s] = u - i0[s];
    }
    return { i0, i1, f };
  };
  const py = posiciones(alto, altoS);
  const px = posiciones(ancho, anchoS);
  const salida = new Float32Array(altoS * anchoS);
  for (let y = 0; y < altoS; y++) {
    const fy = py.f[y];
    const f0 = py.i0[y] * ancho;
    const f1 = py.i1[y] * ancho;
    for (let x = 0; x < anchoS; x++) {
      const fx = px.f[x];
      const a = mapa[f0 + px.i0[x]];
      const b = mapa[f0 + px.i1[x]];
      const c = mapa[f1 + px.i0[x]];
      const d = mapa[f1 + px.i1[x]];
      salida[y * anchoS + x] = (1 - fy) * ((1 - fx) * a + fx * b) + fy * ((1 - fx) * c + fx * d);
    }
  }
  return salida;
}

// Mapa de color VIRIDIS (perceptualmente uniforme: la luminosidad crece de forma monótona de 0 a 1, se lee igual en
// escala de grises y con daltonismo frecuente). Las 256 entradas son las de `matplotlib.colormaps["viridis"]` (matplotlib
// 3.11.2), muestreadas en linspace(0, 1, 256) y redondeadas a 8 bits; van como hexadecimal RRGGBB seguido.
// 0 (menos influencia) = #440154, morado oscuro; 1 (más influencia) = #fde725, amarillo.
const VIRIDIS_HEX =
  "44015444025645045745055946075a46085c460a5d460b5e470d60470e61471063471164471365481467481668481769" +
  "48186a481a6c481b6d481c6e481d6f481f70482071482173482374482475482576482677482878482979472a7a472c7a" +
  "472d7b472e7c472f7d46307e46327e46337f463480453581453781453882443983443a83443b84433d84433e85423f85" +
  "4240864241864142874144874045884046883f47883f48893e49893e4a893e4c8a3d4d8a3d4e8a3c4f8a3c508b3b518b" +
  "3b528b3a538b3a548c39558c39568c38588c38598c375a8c375b8d365c8d365d8d355e8d355f8d34608d34618d33628d" +
  "33638d32648e32658e31668e31678e31688e30698e306a8e2f6b8e2f6c8e2e6d8e2e6e8e2e6f8e2d708e2d718e2c718e" +
  "2c728e2c738e2b748e2b758e2a768e2a778e2a788e29798e297a8e297b8e287c8e287d8e277e8e277f8e27808e26818e" +
  "26828e26828e25838e25848e25858e24868e24878e23888e23898e238a8d228b8d228c8d228d8d218e8d218f8d21908d" +
  "21918c20928c20928c20938c1f948c1f958b1f968b1f978b1f988b1f998a1f9a8a1e9b8a1e9c891e9d891f9e891f9f88" +
  "1fa0881fa1881fa1871fa28720a38620a48621a58521a68522a78522a88423a98324aa8325ab8225ac8226ad8127ad81" +
  "28ae8029af7f2ab07f2cb17e2db27d2eb37c2fb47c31b57b32b67a34b67935b77937b87838b9773aba763bbb753dbc74" +
  "3fbc7340bd7242be7144bf7046c06f48c16e4ac16d4cc26c4ec36b50c46a52c56954c56856c66758c7655ac8645cc863" +
  "5ec96260ca6063cb5f65cb5e67cc5c69cd5b6ccd5a6ece5870cf5773d05675d05477d1537ad1517cd2507fd34e81d34d" +
  "84d44b86d54989d5488bd6468ed64590d74393d74195d84098d83e9bd93c9dd93ba0da39a2da37a5db36a8db34aadc32" +
  "addc30b0dd2fb2dd2db5de2bb8de29bade28bddf26c0df25c2df23c5e021c8e020cae11fcde11dd0e11cd2e21bd5e21a" +
  "d8e219dae319dde318dfe318e2e418e5e419e7e419eae51aece51befe51cf1e51df4e61ef6e620f8e621fbe723fde725";

/** Tabla viridis de 256 colores, como [r, g, b] en 0..255. */
export const VIRIDIS: ReadonlyArray<readonly [number, number, number]> = Array.from({ length: 256 }, (_, i) => {
  const h = VIRIDIS_HEX.slice(i * 6, i * 6 + 6);
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)] as const;
});

/** Color viridis de un valor en [0, 1] (el más cercano de los 256; fuera de rango se recorta; NaN → 0). */
export function colorViridis(v: number): readonly [number, number, number] {
  const t = Number.isFinite(v) ? Math.min(Math.max(v, 0), 1) : 0;
  return VIRIDIS[Math.round(t * 255)];
}

/**
 * Mezcla la imagen preprocesada (RGB uint8 aplanado, alto × ancho × 3) con el mapa en [0, 1] (alto × ancho) coloreado con
 * viridis: salida = (1 − α)·imagen + α·color(mapa), con α = `opacidad` ∈ [0, 1] igual en todos los píxeles. Devuelve RGBA
 * (opaco) listo para `ImageData`.
 */
export function superponerCam(rgb: ArrayLike<number>, mapa01: ArrayLike<number>, opacidad: number): Uint8ClampedArray<ArrayBuffer> {
  if (rgb.length !== mapa01.length * 3) throw new Error("la imagen y el mapa deben tener el mismo tamaño");
  const a = Number.isFinite(opacidad) ? Math.min(Math.max(opacidad, 0), 1) : 0;
  const salida = new Uint8ClampedArray(mapa01.length * 4);
  for (let i = 0; i < mapa01.length; i++) {
    const color = colorViridis(mapa01[i]);
    for (let c = 0; c < 3; c++) salida[i * 4 + c] = Math.round((1 - a) * rgb[i * 3 + c] + a * color[c]);
    salida[i * 4 + 3] = 255;
  }
  return salida;
}

/** CAM de la clase → mapa en [0, 1] al tamaño de la imagen de entrada (ReLU + normalización, luego remuestreo bilineal). */
export function camParaPintar(
  mapas: ArrayLike<number>,
  forma: [number, number, number],
  pesosClase: number[],
  alto: number,
  ancho: number,
): Float32Array {
  const [, h, w] = forma;
  return remuestrearBilineal(normalizarCam(calcularCam(mapas, forma, pesosClase)), h, w, alto, ancho);
}
