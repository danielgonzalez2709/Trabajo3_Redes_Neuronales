// Redimensionado bilineal del preprocesado de M2 (lib/imagen.ts), sin navegador. La paridad con PIL sobre un archivo de
// imagen real está en paridad_onnx.test.ts.
import { describe, expect, it } from "vitest";
import { redimensionarBilineal, type PixelesRgb } from "../lib/imagen";

const imagen = (alto: number, ancho: number, f: (y: number, x: number, c: number) => number): PixelesRgb => {
  const rgb = new Uint8ClampedArray(alto * ancho * 3);
  for (let y = 0; y < alto; y++) for (let x = 0; x < ancho; x++) for (let c = 0; c < 3; c++) rgb[(y * ancho + x) * 3 + c] = f(y, x, c);
  return { rgb, alto, ancho };
};

describe("redimensionarBilineal", () => {
  it("una imagen de un solo color sigue siendo de ese color, al reducir y al ampliar", () => {
    const plana = imagen(10, 14, (_y, _x, c) => [200, 100, 7][c]);
    for (const [a, b] of [[4, 5], [30, 31], [10, 14]]) {
      const r = redimensionarBilineal(plana, a, b);
      expect(r).toHaveLength(a * b * 3);
      for (let i = 0; i < r.length; i += 3) expect([r[i], r[i + 1], r[i + 2]]).toEqual([200, 100, 7]);
    }
  });

  it("al mismo tamaño devuelve la misma imagen", () => {
    const img = imagen(6, 7, (y, x, c) => (y * 31 + x * 17 + c * 5) % 256);
    expect(Array.from(redimensionarBilineal(img, 6, 7))).toEqual(Array.from(img.rgb));
  });

  it("al reducir usa una ventana ampliada: cada píxel de salida mezcla vecinos de la imagen original (filtro triangular)", () => {
    const img = imagen(4, 4, (y, x) => (x < 2 ? 0 : 200) + (y < 2 ? 0 : 40));
    const r = redimensionarBilineal(img, 2, 2);
    const [a, b, c, d] = [r[0], r[3], r[6], r[9]];
    expect(a).toBeLessThan(b);
    expect(a).toBeLessThan(c);
    expect(d).toBeGreaterThan(b);
    expect(a).toBeGreaterThan(0); // el borde mezcla con el lado de la derecha: no se salta píxeles
    expect(d).toBeLessThan(240);
  });

  it("ESTIRA: no conserva la proporción (alto y ancho se ajustan por separado)", () => {
    const img = imagen(2, 8, (_y, x) => x * 30);
    const r = redimensionarBilineal(img, 6, 3);
    expect(r).toHaveLength(6 * 3 * 3);
    expect(r[0]).toBeLessThan(r[3]); // crece de izquierda a derecha
    expect(r[3]).toBeLessThan(r[6]);
  });

  it("rechaza una imagen cuyo tamaño no coincide con sus píxeles", () => {
    expect(() => redimensionarBilineal({ rgb: new Uint8ClampedArray(10), alto: 2, ancho: 2 }, 1, 1)).toThrow(/no coincide/);
  });
});
