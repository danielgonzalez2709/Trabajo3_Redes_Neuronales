// Función de dimensionamiento PROVISIONAL (juguete) y su paridad con Python (casos de operacion.json).
import { describe, expect, it } from "vitest";
import { validarOperacion, validarPronosticos } from "../lib/contratos";
import { demandaDelCuantil, dimensionarJuguete, tablaOperacion } from "../lib/dimensionar";
import { leerModelo } from "./ayuda";

const operacion = validarOperacion(leerModelo("m1/operacion.json"));
const pronosticos = validarPronosticos(leerModelo("m1/pronosticos.json"));

describe("dimensionarJuguete", () => {
  it("coincide con Python en todos los casos de paridad", () => {
    expect(operacion.casos_paridad.length).toBeGreaterThanOrEqual(10);
    for (const c of operacion.casos_paridad) {
      expect(dimensionarJuguete(c.entrada.demanda, c.entrada.parametros), JSON.stringify(c.entrada)).toEqual(c.salida);
    }
  });

  it("demanda cero no pide nada", () => {
    expect(dimensionarJuguete(0, operacion.parametros)).toEqual({ despachos: 0, vehiculos: 0, conductores: 0 });
  });

  it("una demanda exacta no sube de despacho por ruido de coma flotante", () => {
    const p = { ...operacion.parametros, capacidad_pasajeros: 40, ocupacion_objetivo: 0.8 };
    expect(dimensionarJuguete(32, p).despachos).toBe(1); // 32 / (40 · 0,8) = 1 exacto
    expect(dimensionarJuguete(32.01, p).despachos).toBe(2);
  });

  it("más ocupación objetivo nunca pide más despachos", () => {
    let anterior = Infinity;
    for (const o of [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]) {
      const d = dimensionarJuguete(1500, { ...operacion.parametros, ocupacion_objetivo: o }).despachos;
      expect(d).toBeLessThanOrEqual(anterior);
      anterior = d;
    }
  });

  it("rechaza parámetros que faltan, fuera de rango o una demanda negativa", () => {
    expect(() => dimensionarJuguete(10, {})).toThrow(/falta el parámetro/);
    expect(() => dimensionarJuguete(10, { ...operacion.parametros, ocupacion_objetivo: 0 })).toThrow(/fuera de rango/);
    expect(() => dimensionarJuguete(-1, operacion.parametros)).toThrow(/demanda/);
    expect(() => dimensionarJuguete(NaN, operacion.parametros)).toThrow(/demanda/);
  });
});

describe("demanda por cuantil y tabla por día", () => {
  const ruta = pronosticos.rutas[0];

  it("elige el valor del cuantil pedido y rechaza uno que no existe", () => {
    const dia = ruta.pronostico[0];
    pronosticos.cuantiles.forEach((q, i) => expect(demandaDelCuantil(dia, pronosticos.cuantiles, q)).toBe(dia.q[i]));
    expect(() => demandaDelCuantil(dia, pronosticos.cuantiles, 0.99)).toThrow(/cuantil/);
  });

  it("un cuantil más alto pide al menos la misma flota", () => {
    const base = { ...operacion.parametros };
    const flota = (q: number) => tablaOperacion(ruta.pronostico, pronosticos.cuantiles, { ...base, cuantil: q }).map((f) => f.vehiculos);
    const bajo = flota(0.5);
    const alto = flota(0.95);
    alto.forEach((v, i) => expect(v).toBeGreaterThanOrEqual(bajo[i]));
  });

  it("devuelve una fila por día pronosticado, en orden", () => {
    const filas = tablaOperacion(ruta.pronostico, pronosticos.cuantiles, operacion.parametros);
    expect(filas.map((f) => f.fecha)).toEqual(ruta.pronostico.map((d) => d.fecha));
  });
});
