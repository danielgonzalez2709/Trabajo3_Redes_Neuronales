// Función de dimensionamiento PROVISIONAL (juguete) y su paridad con Python (casos de operacion.json del fixture de juguete).
// La paridad contra el M1 SERVIDO está en servido.test.ts (solo si declara esta función).
import { describe, expect, it } from "vitest";
import { validarOperacion, validarPronosticos } from "../lib/contratos";
import { demandaDelCuantil, dimensionarJuguete, parametrosBase, tablaOperacion } from "../lib/dimensionar";
import { leerJuguete } from "./ayuda";

const operacion = validarOperacion(leerJuguete("m1/operacion.json"));
const pronosticos = validarPronosticos(leerJuguete("m1/pronosticos.json"));
const ruta = pronosticos.rutas[0];
const base = parametrosBase(operacion.parametros, ruta.ruta_id);

describe("dimensionarJuguete", () => {
  it("coincide con Python en todos los casos de paridad (despachos, vehículos, conductores y pasos)", () => {
    expect(operacion.casos_paridad.length).toBeGreaterThanOrEqual(10);
    for (const c of operacion.casos_paridad) {
      const r = dimensionarJuguete(c.entrada.demanda, c.entrada.parametros);
      const { despachos, vehiculos, conductores } = r;
      expect({ despachos, vehiculos, conductores }, JSON.stringify(c.entrada)).toEqual({
        despachos: c.salida.despachos, vehiculos: c.salida.vehiculos, conductores: c.salida.conductores,
      });
      expect(c.salida.pasos).toBeDefined();
      for (const [clave, v] of Object.entries(c.salida.pasos ?? {})) expect(r.pasos[clave], clave).toBeCloseTo(v, 9);
    }
  });

  it("los casos de paridad cubren varias rutas y los parámetros efectivos son los de cada ruta", () => {
    expect(new Set(operacion.casos_paridad.map((c) => c.entrada.ruta_id)).size).toBeGreaterThan(1);
    for (const c of operacion.casos_paridad) {
      expect(Object.keys(c.entrada.parametros).sort()).toEqual(Object.keys(parametrosBase(operacion.parametros, c.entrada.ruta_id)).sort());
    }
  });

  it("demanda cero no pide nada", () => {
    expect(dimensionarJuguete(0, base)).toMatchObject({ despachos: 0, vehiculos: 0, conductores: 0 });
  });

  it("una demanda exacta no sube de despacho por ruido de coma flotante", () => {
    const util = dimensionarJuguete(1, base).pasos.asientos_utiles; // asientos útiles por despacho de la primera ruta
    expect(dimensionarJuguete(util, base).despachos).toBe(1);
    expect(dimensionarJuguete(util * 3, base).despachos).toBe(3);
    expect(dimensionarJuguete(util * 3 + 0.01, base).despachos).toBe(4);
  });

  it("los supuestos de vehículos y conductores son parámetros: moverlos cambia el resultado", () => {
    const a = dimensionarJuguete(1500, { ...base, "globales.viajes_por_vehiculo_dia": 1, "por_ruta.tiempo_ciclo_h": 2 });
    const b = dimensionarJuguete(1500, { ...base, "globales.viajes_por_vehiculo_dia": 2, "por_ruta.tiempo_ciclo_h": 2 });
    expect(a.despachos).toBe(b.despachos);
    expect(a.vehiculos).toBeGreaterThan(b.vehiculos);
    const c = dimensionarJuguete(1500, { ...base, "globales.conductores_por_vehiculo": 3 });
    expect(c.conductores).toBeGreaterThan(dimensionarJuguete(1500, base).conductores);
  });

  it("los viajes por vehículo no pasan de lo que cabe en las horas de operación según el tiempo de ciclo", () => {
    const largo = dimensionarJuguete(1500, { ...base, "globales.viajes_por_vehiculo_dia": 4, "globales.horas_operacion_dia": 8, "por_ruta.tiempo_ciclo_h": 8 });
    expect(largo.pasos.viajes_efectivos).toBe(1);
    const corto = dimensionarJuguete(1500, { ...base, "globales.viajes_por_vehiculo_dia": 4, "globales.horas_operacion_dia": 16, "por_ruta.tiempo_ciclo_h": 2 });
    expect(corto.pasos.viajes_efectivos).toBe(4);
  });

  it("más ocupación objetivo nunca pide más despachos", () => {
    let anterior = Infinity;
    for (const o of [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]) {
      const d = dimensionarJuguete(1500, { ...base, "globales.ocupacion_objetivo": o }).despachos;
      expect(d).toBeLessThanOrEqual(anterior);
      anterior = d;
    }
  });

  it("rechaza parámetros que faltan, fuera de rango o una demanda negativa", () => {
    expect(() => dimensionarJuguete(10, {})).toThrow(/faltan las composiciones/);
    const sinOcupacion = { ...base };
    delete sinOcupacion["globales.ocupacion_objetivo"];
    expect(() => dimensionarJuguete(10, sinOcupacion)).toThrow(/falta el parámetro/);
    expect(() => dimensionarJuguete(10, { ...base, "globales.ocupacion_objetivo": 0 })).toThrow(/fuera de rango/);
    expect(() => dimensionarJuguete(-1, base)).toThrow(/demanda/);
    expect(() => dimensionarJuguete(NaN, base)).toThrow(/demanda/);
  });
});

describe("parámetros base por ruta", () => {
  it("usa los parámetros de la ruta pedida", () => {
    const otra = pronosticos.rutas[2];
    expect(parametrosBase(operacion.parametros, otra.ruta_id)["por_ruta.tiempo_ciclo_h"]).not.toBe(base["por_ruta.tiempo_ciclo_h"]);
    expect(base["globales.cuantil"]).toBe(0.9);
  });

  it("rechaza una ruta que no existe", () => {
    expect(() => parametrosBase(operacion.parametros, "99999-99998")).toThrow(/99999-99998/);
  });
});

describe("demanda por cuantil y tabla por día", () => {
  it("elige el valor del cuantil pedido y rechaza uno que no existe", () => {
    const dia = ruta.pronostico[0];
    pronosticos.cuantiles.forEach((q, i) => expect(demandaDelCuantil(dia, pronosticos.cuantiles, q)).toBe(dia.q[i]));
    expect(() => demandaDelCuantil(dia, pronosticos.cuantiles, 0.99)).toThrow(/cuantil/);
  });

  it("un cuantil más alto pide al menos la misma flota", () => {
    const flota = (q: number) => tablaOperacion(ruta.pronostico, pronosticos.cuantiles, { ...base, "globales.cuantil": q }).map((f) => f.vehiculos);
    const bajo = flota(0.5);
    const alto = flota(0.95);
    alto.forEach((v, i) => expect(v).toBeGreaterThanOrEqual(bajo[i]));
  });

  it("devuelve una fila por día pronosticado, en orden, con los pasos intermedios", () => {
    const filas = tablaOperacion(ruta.pronostico, pronosticos.cuantiles, base);
    expect(filas.map((f) => f.fecha)).toEqual(ruta.pronostico.map((d) => d.fecha));
    expect(filas[0].pasos.asientos_utiles).toBeGreaterThan(0);
  });
});
