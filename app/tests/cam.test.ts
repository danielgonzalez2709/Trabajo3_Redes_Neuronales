// CAM para pintar (DA-7, lib/clasificar.ts): ReLU + normalización, remuestreo bilineal, mapa de color viridis y mezcla con
// la imagen. Casos hechos a mano; la paridad del CAM mismo con Python está en paridad_onnx.test.ts y la equivalencia
// CAM ≡ Grad-CAM, en tests/test_juguetes_app.py.
import { describe, expect, it } from "vitest";
import { calcularCam, camParaPintar, colorViridis, normalizarCam, remuestrearBilineal, superponerCam, VIRIDIS } from "../lib/clasificar";

const lista = (xs: ArrayLike<number>) => Array.from(xs);

describe("normalizarCam (ReLU + normalización a [0, 1] por imagen)", () => {
  it("un mapa constante positivo queda todo en 1", () => {
    expect(lista(normalizarCam([2.5, 2.5, 2.5, 2.5]))).toEqual([1, 1, 1, 1]);
  });

  it("un solo máximo: vale 1 ahí y el resto se escala por ese máximo; los negativos quedan en 0", () => {
    expect(lista(normalizarCam([0, 1, 4, -3]))).toEqual([0, 0.25, 1, 0]);
  });

  it("un mapa todo negativo (o todo cero) queda todo en cero, sin NaN", () => {
    for (const m of [[-1, -0.5, -7, -2], [0, 0, 0, 0], [-0, -1e-30]]) {
      const r = lista(normalizarCam(m));
      expect(r.every((v) => v === 0)).toBe(true);
      expect(r.some(Number.isNaN)).toBe(false);
    }
  });

  it("ignora valores no finitos (NaN, ±Infinity) sin propagarlos", () => {
    const r = lista(normalizarCam([NaN, 2, Infinity, -Infinity, 1]));
    expect(r).toEqual([0, 1, 0, 0, 0.5]);
  });

  it("es invariante a la escala positiva (por eso es relativa a cada imagen)", () => {
    const m = [0.3, -0.2, 1.1, 0.7, 0];
    const a = lista(normalizarCam(m));
    const b = lista(normalizarCam(m.map((v) => v * 37)));
    a.forEach((v, i) => expect(b[i]).toBeCloseTo(v, 6));
  });
});

describe("remuestrearBilineal (centros de píxel, como align_corners=False)", () => {
  it("un mapa constante sigue constante al ampliar y al reducir", () => {
    const c = new Array(3 * 5).fill(0.4);
    for (const [a, b] of [[32, 32], [2, 2], [7, 11]]) {
      const r = remuestrearBilineal(c, 3, 5, a, b);
      expect(r).toHaveLength(a * b);
      r.forEach((v) => expect(v).toBeCloseTo(0.4, 6));
    }
  });

  it("al ampliar, las cuatro esquinas de la salida son las cuatro esquinas del mapa", () => {
    const m = [1, 2, 3, 4, 5, 6]; // 2 × 3
    const r = remuestrearBilineal(m, 2, 3, 8, 12);
    expect(r[0]).toBe(1);
    expect(r[11]).toBe(3);
    expect(r[7 * 12]).toBe(4);
    expect(r[7 * 12 + 11]).toBe(6);
  });

  it("2 × 2 → 4 × 4 a mano: posiciones de origen −0.25 (recortada a 0), 0.25, 0.75, 1.25 (recortada a 1)", () => {
    // m = [[0, 1], [2, 3]] → por fila: u ∈ {0, 0.25, 0.75, 1}; valor = 0.75·izq + 0.25·der, etc.
    const r = lista(remuestrearBilineal([0, 1, 2, 3], 2, 2, 4, 4));
    const fila = (base: number) => [0, 0.25, 0.75, 1].map((u) => base + u);
    const esperado = [...fila(0), ...fila(0.5), ...fila(1.5), ...fila(2)];
    r.forEach((v, i) => expect(v).toBeCloseTo(esperado[i], 6));
  });

  it("un solo máximo en el centro se reparte en una zona con el pico en el centro y nunca supera al máximo", () => {
    const m = [0, 0, 0, 0, 1, 0, 0, 0, 0]; // 3 × 3
    const r = lista(remuestrearBilineal(m, 3, 3, 9, 9));
    expect(r[4 * 9 + 4]).toBeCloseTo(1, 6); // el centro de la salida cae justo en el centro del píxel del máximo
    expect(Math.max(...r)).toBeLessThanOrEqual(1);
    expect(Math.min(...r)).toBeGreaterThanOrEqual(0);
    expect(r[0]).toBe(0);
  });

  it("al mismo tamaño devuelve el mismo mapa", () => {
    const m = [0.1, 0.9, 0.3, 0.4, 0.5, 0.6];
    lista(remuestrearBilineal(m, 2, 3, 2, 3)).forEach((v, i) => expect(v).toBeCloseTo(m[i], 6));
  });

  it("rechaza tamaños que no cuadran", () => {
    expect(() => remuestrearBilineal([1, 2, 3], 2, 2, 4, 4)).toThrow();
    expect(() => remuestrearBilineal([1], 1, 1, 0, 4)).toThrow();
  });
});

describe("mapa de color viridis", () => {
  it("tiene 256 entradas con los extremos de matplotlib (#440154 y #fde725)", () => {
    expect(VIRIDIS).toHaveLength(256);
    expect(VIRIDIS[0]).toEqual([0x44, 0x01, 0x54]);
    expect(VIRIDIS[255]).toEqual([0xfd, 0xe7, 0x25]);
    expect(colorViridis(0)).toEqual(VIRIDIS[0]);
    expect(colorViridis(1)).toEqual(VIRIDIS[255]);
    expect(colorViridis(NaN)).toEqual(VIRIDIS[0]);
    expect(colorViridis(-3)).toEqual(VIRIDIS[0]);
    expect(colorViridis(7)).toEqual(VIRIDIS[255]);
  });

  // Al redondear a 8 bits, dos entradas vecinas pueden invertirse por milésimas (pasa en la 95): se exige crecimiento
  // estricto cada 4 entradas y, entre vecinas, que no baje más de 1e-3.
  it("es perceptualmente ordenado: la luminancia relativa crece de 0 a 1", () => {
    const lineal = (c: number) => {
      const s = c / 255;
      return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
    };
    const lum = VIRIDIS.map(([r, g, b]) => 0.2126 * lineal(r) + 0.7152 * lineal(g) + 0.0722 * lineal(b));
    for (let i = 4; i < lum.length; i += 4) expect(lum[i], `entrada ${i}`).toBeGreaterThan(lum[i - 4]);
    for (let i = 1; i < lum.length; i++) expect(lum[i] - lum[i - 1], `entrada ${i}`).toBeGreaterThan(-1e-3);
    expect(lum[255] / lum[0]).toBeGreaterThan(20);
  });
});

describe("superponerCam", () => {
  const rgb = [10, 20, 30, 200, 100, 50];
  it("opacidad 0 deja la imagen; opacidad 1 deja solo el color del mapa; siempre opaco", () => {
    expect(lista(superponerCam(rgb, [0, 1], 0))).toEqual([10, 20, 30, 255, 200, 100, 50, 255]);
    expect(lista(superponerCam(rgb, [0, 1], 1))).toEqual([0x44, 0x01, 0x54, 255, 0xfd, 0xe7, 0x25, 255]);
  });

  it("opacidad 0.5 promedia imagen y color", () => {
    const r = lista(superponerCam([0, 0, 0], [1], 0.5));
    expect(r).toEqual([Math.round(0xfd / 2), Math.round(0xe7 / 2), Math.round(0x25 / 2), 255]);
  });

  it("rechaza tamaños distintos", () => {
    expect(() => superponerCam([1, 2, 3], [0, 1], 0.5)).toThrow();
  });
});

describe("camParaPintar", () => {
  it("encadena CAM, ReLU + normalización y remuestreo, y queda en [0, 1] al tamaño pedido", () => {
    // 2 canales de 2 × 2; pesos [1, −1] → CAM = [1−0, 0−2, 3−1, −1−0] = [1, −2, 2, −1] → [0.5, 0, 1, 0].
    const mapas = [1, 0, 3, -1, 0, 2, 1, 0];
    const forma: [number, number, number] = [2, 2, 2];
    expect(calcularCam(mapas, forma, [1, -1])).toEqual([1, -2, 2, -1]);
    const r = lista(camParaPintar(mapas, forma, [1, -1], 2, 2));
    expect(r).toEqual([0.5, 0, 1, 0]);
    const grande = lista(camParaPintar(mapas, forma, [1, -1], 6, 6));
    expect(grande).toHaveLength(36);
    expect(Math.min(...grande)).toBeGreaterThanOrEqual(0);
    expect(Math.max(...grande)).toBeLessThanOrEqual(1);
    expect(grande[0]).toBe(0.5);
    expect(grande[30]).toBe(1);
  });
});
