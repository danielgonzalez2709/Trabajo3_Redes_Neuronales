import { describe, expect, it } from "vitest";
import { formatearCuantil, formatearFecha, formatearFechaLarga, formatearNumero, formatearPorcentaje } from "../lib/formato";
import { escalaLineal, marcasEje, trazoBanda, trazoLinea } from "../lib/grafico";

describe("formato", () => {
  it("números con coma decimal y punto de miles", () => {
    expect(formatearNumero(1234.5, 1)).toBe("1.234,5");
    expect(formatearNumero(1234567)).toBe("1.234.567");
    expect(formatearNumero(0)).toBe("0");
    expect(formatearNumero(-12.5, 1)).toBe("-12,5");
    expect(formatearNumero(-0.001, 1)).toBe("0,0");
  });

  it("porcentajes y cuantiles", () => {
    expect(formatearPorcentaje(0.1835)).toBe("18,4 %");
    expect(formatearPorcentaje(0.5, 0)).toBe("50 %");
    expect(formatearCuantil(0.9)).toBe("90 %");
    expect(formatearCuantil(0.95)).toBe("95 %");
    expect(formatearCuantil(0.975)).toBe("97,5 %");
  });

  it("fechas sin zonas horarias", () => {
    expect(formatearFecha("2025-01-03")).toBe("vie 3 ene");
    expect(formatearFechaLarga("2024-12-31")).toBe("31 dic 2024");
  });
});

describe("geometría del gráfico", () => {
  it("escala lineal y dominio degenerado", () => {
    const e = escalaLineal(0, 10, 100, 0);
    expect(e(0)).toBe(100);
    expect(e(10)).toBe(0);
    expect(e(5)).toBe(50);
    expect(escalaLineal(3, 3, 0, 10)(3)).toBe(5);
  });

  it("marcas del eje: redondas, desde 0 y cubren el máximo", () => {
    for (const max of [7, 99, 1234, 20_000]) {
      const m = marcasEje(max);
      expect(m[0]).toBe(0);
      expect(m[m.length - 1]).toBeGreaterThanOrEqual(max);
      expect(m.length).toBeLessThanOrEqual(8);
    }
    expect(marcasEje(1000)).toEqual([0, 500, 1000]);
    expect(marcasEje(0)).toEqual([0, 1]);
  });

  it("trazos de línea y de banda", () => {
    expect(trazoLinea([[0, 1], [2, 3]])).toBe("M0.0,1.0 L2.0,3.0");
    expect(trazoLinea([])).toBe("");
    expect(trazoBanda([[0, 0], [1, 0]], [[0, 1], [1, 1]])).toBe("M0.0,0.0 L1.0,0.0 L1.0,1.0 L0.0,1.0 Z");
    expect(trazoBanda([], [])).toBe("");
  });
});
