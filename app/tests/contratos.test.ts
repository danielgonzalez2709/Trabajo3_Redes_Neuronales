import { describe, expect, it } from "vitest";
import {
  ErrorContrato, validarCoherenciaM1, validarCoherenciaM3, validarDestinos, validarMetaM2, validarOperacion, validarPerfilNuevo,
  validarPronosticos, validarUsuarios,
} from "../lib/contratos";
import { copia, leerModelo } from "./ayuda";

type Cualquiera = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any

const pronosticos = () => leerModelo("m1/pronosticos.json") as Cualquiera;
const operacion = () => leerModelo("m1/operacion.json") as Cualquiera;
const meta = () => leerModelo("m2/meta.json") as Cualquiera;
const destinos = () => leerModelo("m3/destinos.json") as Cualquiera;
const usuarios = () => leerModelo("m3/usuarios.json") as Cualquiera;
const perfil = () => leerModelo("m3/perfil_nuevo.json") as Cualquiera;

/** El validador debe lanzar un ErrorContrato cuyo mensaje contenga el fragmento (ruta del campo). */
const rechaza = (f: () => unknown, fragmento: string) => {
  let error: unknown;
  try {
    f();
  } catch (e) {
    error = e;
  }
  expect(error).toBeInstanceOf(ErrorContrato);
  expect((error as Error).message).toContain(fragmento);
};

describe("los JSON de juguete cumplen sus contratos", () => {
  it("M1: pronosticos.json y operacion.json", () => {
    const p = validarPronosticos(pronosticos());
    const o = validarOperacion(operacion());
    expect(p.juguete).toBe(true);
    expect(o.juguete).toBe(true);
    expect(p.horizonte).toBe(30);
    expect(p.rutas.length).toBeGreaterThan(1);
    for (const r of p.rutas) {
      expect(r.pronostico).toHaveLength(p.horizonte);
      expect(r.historia.length).toBe(90);
      expect(r.pronostico[0].q).toHaveLength(p.cuantiles.length);
    }
    expect(() => validarCoherenciaM1(p, o)).not.toThrow();
  });

  it("M2: meta.json", () => {
    const m = validarMetaM2(meta());
    expect(m.juguete).toBe(true);
    expect(m.clases).toHaveLength(5);
    expect(m.casos_paridad.length).toBeGreaterThan(0);
  });

  it("M3: destinos, usuarios y perfil nuevo, y su coherencia", () => {
    const d = validarDestinos(destinos());
    const u = validarUsuarios(usuarios());
    const p = validarPerfilNuevo(perfil());
    expect([d.juguete, u.juguete, p.juguete]).toEqual([true, true, true]);
    expect(() => validarCoherenciaM3(d, u, p)).not.toThrow();
  });
});

describe("M1: casos inválidos con mensaje claro", () => {
  it("no es un objeto", () => rechaza(() => validarPronosticos([]), "$: debe ser un objeto"));

  it("falta `juguete`", () => {
    const x = pronosticos();
    delete x.juguete;
    rechaza(() => validarPronosticos(x), "m1/pronosticos.json: juguete");
  });

  it("cuantiles no crecientes", () => {
    const x = copia(pronosticos());
    x.cuantiles = [0.5, 0.5, 0.9, 0.95];
    rechaza(() => validarPronosticos(x), "cuantiles[1]");
  });

  it("cuantil fuera de (0, 1)", () => {
    const x = copia(pronosticos());
    x.cuantiles[3] = 1;
    rechaza(() => validarPronosticos(x), "cuantiles[3]");
  });

  it("el pronóstico no tiene `horizonte` días", () => {
    const x = copia(pronosticos());
    x.rutas[0].pronostico.pop();
    rechaza(() => validarPronosticos(x), "rutas[0].pronostico");
  });

  it("`h` fuera de secuencia", () => {
    const x = copia(pronosticos());
    x.rutas[1].pronostico[4].h = 9;
    rechaza(() => validarPronosticos(x), "rutas[1].pronostico[4].h");
  });

  it("un día con menos valores que cuantiles", () => {
    const x = copia(pronosticos());
    x.rutas[0].pronostico[2].q = [1, 2];
    rechaza(() => validarPronosticos(x), "rutas[0].pronostico[2].q");
  });

  it("cuantiles decrecientes dentro de un día", () => {
    const x = copia(pronosticos());
    x.rutas[0].pronostico[0].q = [10, 9, 12, 13];
    rechaza(() => validarPronosticos(x), "no decrecientes");
  });

  it("fecha inexistente", () => {
    const x = copia(pronosticos());
    x.rutas[0].historia[3].fecha = "2024-02-31";
    rechaza(() => validarPronosticos(x), "rutas[0].historia[3].fecha");
  });

  it("pasajeros negativos", () => {
    const x = copia(pronosticos());
    x.rutas[0].historia[0].pasajeros = -1;
    rechaza(() => validarPronosticos(x), "rutas[0].historia[0].pasajeros");
  });

  it("ruta repetida", () => {
    const x = copia(pronosticos());
    x.rutas[1].ruta_id = x.rutas[0].ruta_id;
    rechaza(() => validarPronosticos(x), "ruta repetida");
  });

  it("la historia no termina en fecha_origen", () => {
    const x = copia(pronosticos());
    x.fecha_origen = "2024-12-30";
    rechaza(() => validarPronosticos(x), "fecha_origen");
  });

  it("operacion: control con clave que no es un parámetro", () => {
    const x = copia(operacion());
    x.controles[0].clave = "inventada";
    rechaza(() => validarOperacion(x), "controles[0].clave");
  });

  it("operacion: defecto fuera del rango", () => {
    const x = copia(operacion());
    x.controles[0].defecto = 5;
    rechaza(() => validarOperacion(x), "controles[0].defecto");
  });

  it("operacion: tipo de control desconocido", () => {
    const x = copia(operacion());
    x.controles[0].tipo = "deslizador";
    rechaza(() => validarOperacion(x), "controles[0].tipo");
  });

  it("operacion: caso de paridad con salida no entera", () => {
    const x = copia(operacion());
    x.casos_paridad[0].salida.vehiculos = 1.5;
    rechaza(() => validarOperacion(x), "casos_paridad[0].salida.vehiculos");
  });

  it("coherencia: un cuantil de operacion que el pronóstico no tiene", () => {
    const p = validarPronosticos(pronosticos());
    const x = copia(operacion());
    x.controles.find((c: Cualquiera) => c.clave === "cuantil").opciones.push(0.99);
    expect(() => validarCoherenciaM1(p, validarOperacion(x))).toThrow(/0\.99/);
  });
});

describe("M2: casos inválidos con mensaje claro", () => {
  it("una clase sin grupo de alerta", () => {
    const x = copia(meta());
    delete x.grupo_alerta.giro;
    rechaza(() => validarMetaM2(x), "grupo_alerta.giro");
  });

  it("grupo de alerta desconocido", () => {
    const x = copia(meta());
    x.grupo_alerta.giro = "quizas";
    rechaza(() => validarMetaM2(x), "grupo_alerta.giro");
  });

  it("todas las clases con alerta", () => {
    const x = copia(meta());
    x.grupo_alerta.conduccion_segura = "con_alerta";
    rechaza(() => validarMetaM2(x), "grupo_alerta");
  });

  it("umbral fuera de [0, 1]", () => {
    const x = copia(meta());
    x.umbral_por_defecto = 1.5;
    rechaza(() => validarMetaM2(x), "umbral_por_defecto");
  });

  it("desviación no positiva", () => {
    const x = copia(meta());
    x.desviacion[1] = 0;
    rechaza(() => validarMetaM2(x), "desviacion[1]");
  });

  it("pesos_cabeza con una fila de menos", () => {
    const x = copia(meta());
    x.pesos_cabeza.pop();
    rechaza(() => validarMetaM2(x), "pesos_cabeza");
  });

  it("imagen del caso con el tamaño equivocado", () => {
    const x = copia(meta());
    x.casos_paridad[0].entrada_rgb.pop();
    rechaza(() => validarMetaM2(x), "casos_paridad[0].entrada_rgb");
  });

  it("píxel fuera de 0..255", () => {
    const x = copia(meta());
    x.casos_paridad[0].entrada_rgb[7] = 300;
    rechaza(() => validarMetaM2(x), "casos_paridad[0].entrada_rgb[7]");
  });

  it("probabilidades que no suman 1", () => {
    const x = copia(meta());
    x.casos_paridad[0].probabilidades = [0.5, 0.5, 0.5, 0, 0];
    rechaza(() => validarMetaM2(x), "probabilidades");
  });

  it("faltan las salidas del ONNX", () => {
    const x = copia(meta());
    delete x.salidas_onnx.mapas;
    rechaza(() => validarMetaM2(x), "salidas_onnx.mapas");
  });
});

describe("M3: casos inválidos con mensaje claro", () => {
  it("atributo fuera de [0, 1]", () => {
    const x = copia(destinos());
    x.destinos[0].atributos.playa = 1.2;
    rechaza(() => validarDestinos(x), "destinos[0].atributos.playa");
  });

  it("destino repetido", () => {
    const x = copia(destinos());
    x.destinos[1].id = x.destinos[0].id;
    rechaza(() => validarDestinos(x), "destino repetido");
  });

  it("calificación fuera de 1..5", () => {
    const x = copia(usuarios());
    x.usuarios[0].historial[0].calificacion = 6;
    rechaza(() => validarUsuarios(x), "calificacion");
  });

  it("top-K que recomienda algo ya visto", () => {
    const x = copia(usuarios());
    x.usuarios[0].top_k[0].destino_id = x.usuarios[0].historial[0].destino_id;
    rechaza(() => validarUsuarios(x), "historial");
  });

  it("top-K desordenado", () => {
    const x = copia(usuarios());
    x.usuarios[0].top_k[3].puntaje = 99;
    rechaza(() => validarUsuarios(x), "de mayor a menor");
  });

  it("preferencia de un caso que no existe", () => {
    const x = copia(perfil());
    x.casos_paridad[0].preferencias = ["inventada"];
    rechaza(() => validarPerfilNuevo(x), "casos_paridad[0].preferencias[0]");
  });

  it("k_defecto mayor que k_max", () => {
    const x = copia(perfil());
    x.k_defecto = 99;
    rechaza(() => validarPerfilNuevo(x), "k_defecto");
  });

  it("coherencia: usuario con un destino que no existe", () => {
    const d = validarDestinos(destinos());
    const p = validarPerfilNuevo(perfil());
    const x = copia(usuarios());
    x.usuarios[0].historial[0].destino_id = "D99";
    expect(() => validarCoherenciaM3(d, validarUsuarios(x), p)).toThrow(/D99/);
  });

  it("coherencia: un destino sin el atributo de una preferencia", () => {
    const p = validarPerfilNuevo(perfil());
    const u = validarUsuarios(usuarios());
    const x = copia(destinos());
    delete x.destinos[2].atributos.playa;
    expect(() => validarCoherenciaM3(validarDestinos(x), u, p)).toThrow(/playa/);
  });
});
