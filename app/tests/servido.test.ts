// Lo SERVIDO por la app (app/public/model/, o MODELO_SERVIDO_DIR en pruebas): puede ser el juguete o el modelo real de cada
// módulo, así que aquí solo van comprobaciones que valen para ambos. Nada de ids, preferencias o nombres del juguete: los ids
// salen del propio archivo. La lógica y los casos inválidos están en el fixture de juguete (contratos, recomendar, dimensionar,
// meta_m2). La paridad del ONNX de M2 (también sobre lo servido) está en paridad_onnx.test.ts.
import { describe, expect, it } from "vitest";
import {
  validarCasosM3, validarCoherenciaM1, validarCoherenciaM3, validarDestinos, validarMetaM2, validarOperacion, validarPerfilNuevo,
  validarPronosticos, validarUsuarios,
} from "../lib/contratos";
import { calcularCam, indiceMaximo, softmax } from "../lib/clasificar";
import { dimensionarJuguete, parametrosBase } from "../lib/dimensionar";
import { recomendarPerfil } from "../lib/recomendar";
import { existe, existeModelo, leerModelo } from "./ayuda";

describe("M1 servido: contrato y coherencia", () => {
  const pronosticos = validarPronosticos(leerModelo("m1/pronosticos.json"));
  const operacion = validarOperacion(leerModelo("m1/operacion.json"));

  it("pronosticos.json y operacion.json cumplen su contrato y son coherentes entre sí", () => {
    expect(pronosticos.rutas.length).toBeGreaterThan(0);
    expect(() => validarCoherenciaM1(pronosticos, operacion)).not.toThrow();
  });

  it("cada ruta tiene su historia hasta fecha_origen, su pronóstico de `horizonte` días y su ruta de regreso entre las rutas", () => {
    const ids = pronosticos.rutas.map((r) => r.ruta_id);
    for (const r of pronosticos.rutas) {
      expect(r.pronostico, r.ruta_id).toHaveLength(pronosticos.horizonte);
      expect(r.historia[r.historia.length - 1].fecha, r.ruta_id).toBe(pronosticos.fecha_origen);
      expect(ids, r.ruta_id).toContain(r.ruta_regreso_id);
    }
  });

  it("todas las rutas de los casos de paridad y de los parámetros existen en el pronóstico", () => {
    const ids = new Set(pronosticos.rutas.map((r) => r.ruta_id));
    for (const c of operacion.casos_paridad) expect(ids.has(c.entrada.ruta_id), c.entrada.ruta_id).toBe(true);
    for (const id of Object.keys(operacion.parametros.composicion_clases)) expect(ids.has(id), id).toBe(true);
  });

  // La paridad con la función real de Camila llega en DA-6; hoy solo se comprueba si lo servido declara la del juguete.
  const esJuguete = operacion.funcion === "dimensionar_juguete";
  it.skipIf(!esJuguete)("paridad de dimensionar con el M1 servido (declara `dimensionar_juguete`)", () => {
    for (const c of operacion.casos_paridad) {
      const r = dimensionarJuguete(c.entrada.demanda, c.entrada.parametros);
      expect({ despachos: r.despachos, vehiculos: r.vehiculos, conductores: r.conductores }, JSON.stringify(c.entrada)).toEqual({
        despachos: c.salida.despachos, vehiculos: c.salida.vehiculos, conductores: c.salida.conductores,
      });
      for (const [clave, v] of Object.entries(c.salida.pasos ?? {})) expect(r.pasos[clave], clave).toBeCloseTo(v, 9);
      expect(Object.keys(c.entrada.parametros).sort()).toEqual(Object.keys(parametrosBase(operacion.parametros, c.entrada.ruta_id)).sort());
    }
  });
  it.skipIf(esJuguete)(`paridad de dimensionar con el M1 servido: se salta, la función declarada («${operacion.funcion}») no es la de app/lib/dimensionar.ts; la paridad real llega en DA-6`, () => {
    expect(operacion.funcion).not.toBe("dimensionar_juguete");
  });
});

describe("M2 servido: contrato, archivos y casos de paridad", () => {
  const meta = validarMetaM2(leerModelo("m2/meta.json"));

  it("meta.json cumple su contrato y trae las 5 clases del enunciado con su grupo de alerta", () => {
    expect(meta.clases.map((c) => c.nombre)).toEqual([
      "Conducción segura", "Giro", "Escribir en el teléfono", "Hablar por teléfono", "Otros comportamientos riesgosos",
    ]);
    expect(meta.grupo_alerta.conduccion_segura).toBe("sin_alerta");
    expect(Object.values(meta.grupo_alerta).filter((g) => g === "con_alerta")).toHaveLength(4);
    expect(meta.pesos_cabeza).toHaveLength(meta.clases.length);
    expect(meta.sesgo_cabeza).toHaveLength(meta.clases.length);
    expect(meta.salidas_onnx).toEqual({ logits: "logits", mapas: "mapas" });
  });

  it("los archivos que nombra existen: modelo ONNX, ejemplos y los .wasm de onnxruntime servidos por la app", () => {
    expect(existeModelo(`m2/${meta.archivo_modelo}`)).toBe(true);
    for (const e of meta.ejemplos) expect(existeModelo(`m2/ejemplos/${e.archivo}`), e.archivo).toBe(true);
    for (const c of meta.casos_paridad) if (c.imagen) expect(existeModelo(`m2/ejemplos/${c.imagen}`), c.imagen).toBe(true);
    expect(existe("ort/ort-wasm-simd-threaded.wasm")).toBe(true);
    expect(existe("ort/ort-wasm-simd-threaded.mjs")).toBe(true);
  });

  it("los casos de paridad: softmax de los logits = probabilidades, CAM = Σ pesos · mapas y la cabeza reproduce los logits", () => {
    expect(meta.casos_paridad.length).toBeGreaterThan(0);
    for (const c of meta.casos_paridad) {
      softmax(c.logits).forEach((p, i) => expect(p).toBeCloseTo(c.probabilidades[i], 5));
      expect(indiceMaximo(c.probabilidades)).toBe(c.clase_predicha);
      calcularCam(c.mapas, c.forma_mapas, meta.pesos_cabeza[c.clase_predicha]).forEach((v, i) => expect(v).toBeCloseTo(c.cam_clase_predicha[i], 4));
      const [canales, alto, ancho] = c.forma_mapas;
      meta.clases.forEach((_, k) => {
        let logit = meta.sesgo_cabeza[k];
        for (let ch = 0; ch < canales; ch++) {
          let media = 0;
          for (let i = 0; i < alto * ancho; i++) media += c.mapas[ch * alto * ancho + i];
          logit += meta.pesos_cabeza[k][ch] * (media / (alto * ancho));
        }
        expect(logit).toBeCloseTo(c.logits[k], 4);
      });
    }
  });
});

describe("M3 servido: contrato, coherencia y paridad con Python", () => {
  const destinos = validarDestinos(leerModelo("m3/destinos.json"));
  const usuarios = validarUsuarios(leerModelo("m3/usuarios.json"));
  const perfil = validarPerfilNuevo(leerModelo("m3/perfil_nuevo.json"));
  const casos = validarCasosM3(leerModelo("m3/casos_paridad.json"), perfil);

  it("los cuatro archivos cumplen su contrato y son coherentes entre sí", () => {
    expect(() => validarCoherenciaM3(destinos, usuarios, perfil, casos)).not.toThrow();
  });

  it("los casos de paridad se reproducen con recomendarPerfil: mismo vector, mismos destinos, mismo orden y mismos puntajes", () => {
    expect(casos.casos.length).toBeGreaterThan(0);
    for (const c of casos.casos) {
      const r = recomendarPerfil(c.seleccion, perfil.preferencias, perfil.torre_usuario, destinos.destinos, c.k, c.vistos);
      r.vector_usuario.forEach((v, i) => expect(v).toBeCloseTo(c.vector_usuario[i], 9));
      expect(r.top_k.map((f) => f.destino_id), JSON.stringify(c.seleccion)).toEqual(c.top_k.map((f) => f.destino_id));
      r.top_k.forEach((f, i) => expect(f.puntaje).toBeCloseTo(c.top_k[i].puntaje, 9));
    }
  });

  it("los ids del historial y del top-K de cada usuario existen entre los destinos, y el top-K no repite lo ya visto", () => {
    const ids = new Set(destinos.destinos.map((d) => d.id));
    for (const u of usuarios.usuarios) {
      for (const h of u.historial) expect(ids.has(h.destino_id), `${u.id} historial ${h.destino_id}`).toBe(true);
      const vistos = new Set(u.historial.map((h) => h.destino_id));
      for (const f of u.top_k) {
        expect(ids.has(f.destino_id), `${u.id} top-K ${f.destino_id}`).toBe(true);
        expect(vistos.has(f.destino_id), `${u.id} recomienda lo ya visto ${f.destino_id}`).toBe(false);
      }
      expect(u.top_k.length).toBeGreaterThanOrEqual(usuarios.k_max);
    }
  });

  it("los casos de paridad usan preferencias y opciones del propio perfil, y los ids de los vistos existen", () => {
    const ids = new Set(destinos.destinos.map((d) => d.id));
    for (const c of casos.casos) {
      for (const [p, ops] of Object.entries(c.seleccion)) {
        const pref = perfil.preferencias.find((x) => x.id === p);
        expect(pref, p).toBeDefined();
        for (const o of ops) expect(pref!.opciones.some((x) => x.id === o), `${p}/${o}`).toBe(true);
      }
      for (const v of c.vistos) expect(ids.has(v), v).toBe(true);
    }
  });

  it("un perfil nuevo armado con la primera opción de la primera preferencia (ids tomados del archivo) recomienda K destinos", () => {
    const pref = perfil.preferencias[0];
    const r = recomendarPerfil({ [pref.id]: [pref.opciones[0].id] }, perfil.preferencias, perfil.torre_usuario, destinos.destinos, perfil.k_defecto);
    expect(r.top_k).toHaveLength(perfil.k_defecto);
    expect(new Set(r.top_k.map((f) => f.destino_id)).size).toBe(perfil.k_defecto);
  });

  // El contrato (§5.8) dice que un usuario sin historial PUEDE existir: si lo servido no trae ninguno, no aplica.
  const sin = usuarios.usuarios.filter((u) => u.historial.length === 0);
  it.skipIf(sin.length === 0)("un usuario sin historial (si lo hay) trae su top-K completo y ordenado", () => {
    for (const u of sin) {
      expect(u.top_k.length).toBeGreaterThanOrEqual(usuarios.k_max);
      u.top_k.forEach((f, i) => i > 0 && expect(f.puntaje).toBeLessThanOrEqual(u.top_k[i - 1].puntaje));
    }
  });
});
