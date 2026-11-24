// Lógica de M2 que no depende del navegador: preprocesamiento, softmax, decisión de alerta y CAM. Dominio puro.
// En DA-5 el CAM queda sin pintar (DA-7); aquí solo está el cálculo con su prueba de paridad contra `meta.json`.
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
