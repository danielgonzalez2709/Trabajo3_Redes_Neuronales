import { describe, expect, it } from "vitest";
import {
  ErrorContrato, resolverParametro, validarCasosM3, validarCoherenciaM1, validarCoherenciaM3, validarDestinos, validarEntradaCaso,
  validarMetaM2, validarOperacion, validarPerfilNuevo, validarPronosticos, validarUsuarios,
} from "../lib/contratos";
import { copia, leerModelo } from "./ayuda";

type Cualquiera = Record<string, any>;

const pronosticos = () => leerModelo("m1/pronosticos.json") as Cualquiera;
const operacion = () => leerModelo("m1/operacion.json") as Cualquiera;
const meta = () => leerModelo("m2/meta.json") as Cualquiera;
const destinos = () => leerModelo("m3/destinos.json") as Cualquiera;
const usuarios = () => leerModelo("m3/usuarios.json") as Cualquiera;
const perfil = () => leerModelo("m3/perfil_nuevo.json") as Cualquiera;
const casosM3 = () => leerModelo("m3/casos_paridad.json") as Cualquiera;

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
      expect(p.rutas.map((x) => x.ruta_id)).toContain(r.ruta_regreso_id); // el sentido contrario existe entre las rutas
    }
    expect(() => validarCoherenciaM1(p, o)).not.toThrow();
  });

  it("M1: los supuestos de vehículos y conductores son parámetros visibles con `supuesto: true`", () => {
    const o = validarOperacion(operacion());
    for (const ref of ["globales.viajes_por_vehiculo_dia", "globales.conductores_por_vehiculo"]) {
      const par = resolverParametro(o.parametros, ref, Object.keys(o.parametros.composicion_clases)[0]);
      expect(par?.supuesto, ref).toBe(true);
      expect(par?.fuente).toBeUndefined();
      expect(o.controles.some((c) => c.ref === ref), ref).toBe(true);
    }
    expect(o.controles.slice(0, 2).map((c) => c.ref)).toEqual(["globales.ocupacion_objetivo", "globales.cuantil"]);
  });

  it("M2: meta.json", () => {
    const m = validarMetaM2(meta());
    expect(m.juguete).toBe(true);
    expect(m.clases).toHaveLength(5);
    expect(m.casos_paridad.length).toBeGreaterThan(0);
  });

  it("M3: destinos, usuarios, perfil nuevo y casos de paridad, y su coherencia", () => {
    const d = validarDestinos(destinos());
    const u = validarUsuarios(usuarios());
    const p = validarPerfilNuevo(perfil());
    const c = validarCasosM3(casosM3(), p);
    expect([d.juguete, u.juguete, p.juguete, c.juguete]).toEqual([true, true, true, true]);
    expect(() => validarCoherenciaM3(d, u, p, c)).not.toThrow();
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

  it("la ruta de regreso no existe entre las rutas", () => {
    const x = copia(pronosticos());
    x.rutas[0].ruta_regreso_id = "99999-99998";
    rechaza(() => validarPronosticos(x), "rutas[0].ruta_regreso_id");
  });

  it("la historia no termina en fecha_origen", () => {
    const x = copia(pronosticos());
    x.fecha_origen = "2024-12-30";
    rechaza(() => validarPronosticos(x), "rutas[0].historia");
  });
});

describe("M1: operacion.json, casos inválidos con mensaje claro", () => {
  const rutaUno = () => Object.keys(operacion().parametros.composicion_clases)[0];

  it("un parámetro sin fuente ni supuesto", () => {
    const x = copia(operacion());
    delete x.parametros.globales.ocupacion_objetivo.supuesto;
    rechaza(() => validarOperacion(x), "parametros.globales.ocupacion_objetivo");
  });

  it("un parámetro con fuente Y supuesto", () => {
    const x = copia(operacion());
    x.parametros.globales.ocupacion_objetivo.fuente = "Resolución X, art. 1";
    rechaza(() => validarOperacion(x), "no puede traer `fuente` y `supuesto: true`");
  });

  it("un parámetro con fuente (sin supuesto) es válido y se resuelve con su cita", () => {
    const x = copia(operacion());
    const par = x.parametros.por_clase.bus.capacidad_pasajeros;
    delete par.supuesto;
    par.fuente = "Cita textual de prueba";
    const o = validarOperacion(x);
    expect(resolverParametro(o.parametros, "por_clase.bus.capacidad_pasajeros", rutaUno())?.fuente).toBe("Cita textual de prueba");
  });

  it("`supuesto` distinto de true", () => {
    const x = copia(operacion());
    x.parametros.globales.cuantil.supuesto = false;
    rechaza(() => validarOperacion(x), "parametros.globales.cuantil.supuesto");
  });

  it("falta un parámetro obligatorio", () => {
    const x = copia(operacion());
    delete x.parametros.globales.cuantil;
    rechaza(() => validarOperacion(x), "falta el parámetro obligatorio «globales.cuantil»");
  });

  it("falta un control obligatorio", () => {
    const x = copia(operacion());
    x.controles = x.controles.filter((c: Cualquiera) => c.ref !== "globales.ocupacion_objetivo");
    rechaza(() => validarOperacion(x), "falta el control obligatorio de «globales.ocupacion_objetivo»");
  });

  it("control con una referencia que no es un parámetro", () => {
    const x = copia(operacion());
    x.controles[0].ref = "globales.inventada";
    rechaza(() => validarOperacion(x), "controles[0].ref");
  });

  it("control con una referencia a algo heredado (no propio) del objeto", () => {
    const x = copia(operacion());
    x.controles[0].ref = "globales.constructor";
    rechaza(() => validarOperacion(x), "controles[0].ref");
  });

  it("valor del parámetro fuera del rango del control", () => {
    const x = copia(operacion());
    x.controles[0].maximo = 0.6;
    rechaza(() => validarOperacion(x), "controles[0].minimo");
  });

  it("tipo de control desconocido", () => {
    const x = copia(operacion());
    x.controles[0].tipo = "deslizador";
    rechaza(() => validarOperacion(x), "controles[0].tipo");
  });

  it("clave con punto", () => {
    const x = copia(operacion());
    x.parametros.globales["a.b"] = x.parametros.globales.cuantil;
    rechaza(() => validarOperacion(x), "parametros.globales.a.b");
  });

  it("composición por clase que no suma 1", () => {
    const x = copia(operacion());
    x.parametros.composicion_clases[rutaUno()].bus.valor = 0.1;
    rechaza(() => validarOperacion(x), "deben sumar 1");
  });

  it("rutas con distintos parámetros por ruta", () => {
    const x = copia(operacion());
    x.parametros.por_ruta[rutaUno()].extra = x.parametros.globales.cuantil;
    rechaza(() => validarOperacion(x), "los mismos parámetros");
  });

  it("caso de paridad con salida no entera", () => {
    const x = copia(operacion());
    x.casos_paridad[0].salida.vehiculos = 1.5;
    rechaza(() => validarOperacion(x), "casos_paridad[0].salida.vehiculos");
  });

  it("caso de paridad de una ruta desconocida", () => {
    const x = copia(operacion());
    x.casos_paridad[0].entrada.ruta_id = "otra";
    rechaza(() => validarOperacion(x), "casos_paridad[0].entrada.ruta_id");
  });

  it("coherencia: un cuantil de operacion que el pronóstico no tiene", () => {
    const p = validarPronosticos(pronosticos());
    const x = copia(operacion());
    x.controles.find((c: Cualquiera) => c.ref === "globales.cuantil").opciones.push(0.99);
    expect(() => validarCoherenciaM1(p, validarOperacion(x))).toThrow(/0\.99/);
  });

  it("coherencia: una ruta del pronóstico sin composición por clase", () => {
    const p = validarPronosticos(pronosticos());
    const x = copia(operacion());
    delete x.parametros.composicion_clases[rutaUno()];
    delete x.parametros.por_ruta[rutaUno()];
    x.casos_paridad = x.casos_paridad.filter((c: Cualquiera) => c.entrada.ruta_id !== rutaUno());
    expect(() => validarCoherenciaM1(p, validarOperacion(x))).toThrow(new RegExp(rutaUno()));
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

  it("pesos_cabeza con una fila de menos o de más", () => {
    const x = copia(meta());
    x.pesos_cabeza.pop();
    rechaza(() => validarMetaM2(x), "pesos_cabeza");
    const y = copia(meta());
    y.pesos_cabeza.push(y.pesos_cabeza[0]);
    rechaza(() => validarMetaM2(y), "pesos_cabeza");
  });

  it("falta el preprocesado o declara uno que la app no sabe hacer", () => {
    const x = copia(meta());
    delete x.preprocesado;
    rechaza(() => validarMetaM2(x), "preprocesado");
    const y = copia(meta());
    y.preprocesado.redimensionado = "recortar";
    rechaza(() => validarMetaM2(y), "preprocesado.redimensionado");
    const z = copia(meta());
    z.preprocesado.interpolacion = "bicubica";
    rechaza(() => validarMetaM2(z), "preprocesado.interpolacion");
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

  it("un caso sin entrada o con las dos entradas", () => {
    const x = copia(meta());
    delete x.casos_paridad[0].entrada_rgb;
    rechaza(() => validarMetaM2(x), "casos_paridad[0]");
    const y = copia(meta());
    y.casos_paridad[0].entrada_archivo = "casos/otro.json";
    rechaza(() => validarMetaM2(y), "casos_paridad[0]");
  });

  it("entrada en archivo con una ruta peligrosa", () => {
    const x = copia(meta());
    x.casos_paridad[1].entrada_archivo = "../../secreto.json";
    rechaza(() => validarMetaM2(x), "casos_paridad[1].entrada_archivo");
  });

  it("más de 3 casos de paridad", () => {
    const x = copia(meta());
    x.casos_paridad.push(copia(x.casos_paridad[0]));
    rechaza(() => validarMetaM2(x), "casos_paridad");
  });

  it("imagen de un caso que no es un ejemplo", () => {
    const x = copia(meta());
    x.casos_paridad[2].imagen = "inexistente.png";
    rechaza(() => validarMetaM2(x), "casos_paridad[2].imagen");
  });

  it("archivo aparte con la imagen del tamaño equivocado", () => {
    const m = validarMetaM2(meta());
    rechaza(() => validarEntradaCaso({ entrada_rgb: [1, 2, 3] }, m.tamano_entrada, "m2/casos/x.json"), "entrada_rgb");
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
  it("embedding con otra dimensión que los demás destinos", () => {
    const x = copia(destinos());
    x.destinos[3].embedding.pop();
    rechaza(() => validarDestinos(x), "destinos[3].embedding");
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

  it("un usuario sin historial es válido", () => {
    const x = copia(usuarios());
    x.usuarios[0].historial = [];
    expect(validarUsuarios(x).usuarios[0].historial).toEqual([]);
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

  it("usuarios sin `modelo`", () => {
    const x = copia(usuarios());
    delete x.modelo;
    rechaza(() => validarUsuarios(x), "modelo");
  });

  it("dimensión de la codificación distinta del total de opciones", () => {
    const x = copia(perfil());
    x.codificacion.dimension = 3;
    rechaza(() => validarPerfilNuevo(x), "codificacion.dimension");
  });

  it("opción repetida dentro de una preferencia", () => {
    const x = copia(perfil());
    x.preferencias[1].opciones[1].id = x.preferencias[1].opciones[0].id;
    rechaza(() => validarPerfilNuevo(x), "opción repetida");
  });

  it("capa de la torre con las columnas equivocadas", () => {
    const x = copia(perfil());
    x.torre_usuario[1].W[0].pop();
    rechaza(() => validarPerfilNuevo(x), "torre_usuario[1].W[0]");
  });

  it("activación desconocida", () => {
    const x = copia(perfil());
    x.torre_usuario[0].activacion = "tanh";
    rechaza(() => validarPerfilNuevo(x), "torre_usuario[0].activacion");
  });

  it("k_defecto mayor que k_max", () => {
    const x = copia(perfil());
    x.k_defecto = 99;
    rechaza(() => validarPerfilNuevo(x), "k_defecto");
  });

  it("caso de paridad con una opción que no existe", () => {
    const p = validarPerfilNuevo(perfil());
    const x = copia(casosM3());
    x.casos[0].seleccion = { actividad: ["inventada"] };
    rechaza(() => validarCasosM3(x, p), "casos[0].seleccion.actividad[0]");
  });

  it("caso de paridad con un top-K de largo distinto de k", () => {
    const p = validarPerfilNuevo(perfil());
    const x = copia(casosM3());
    x.casos[0].k += 1;
    rechaza(() => validarCasosM3(x, p), "casos[0].top_k");
  });

  it("coherencia: usuario con un destino que no existe", () => {
    const d = validarDestinos(destinos());
    const p = validarPerfilNuevo(perfil());
    const x = copia(usuarios());
    x.usuarios[0].historial[0].destino_id = "D99";
    expect(() => validarCoherenciaM3(d, validarUsuarios(x), p)).toThrow(/D99/);
  });

  it("coherencia: embeddings de otra dimensión que la salida de la torre", () => {
    const p = validarPerfilNuevo(perfil());
    const u = validarUsuarios(usuarios());
    const x = copia(destinos());
    x.destinos.forEach((d: Cualquiera) => d.embedding.pop());
    expect(() => validarCoherenciaM3(validarDestinos(x), u, p)).toThrow(/torre_usuario/);
  });
});
