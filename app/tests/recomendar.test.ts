// Recomendador de dos torres de M3 y su paridad con Python (m3/casos_paridad.json).
import { describe, expect, it } from "vitest";
import {
  validarCasosM3, validarCoherenciaM3, validarDestinos, validarPerfilNuevo, validarUsuarios, type CapaM3, type DestinoM3, type PreferenciaM3,
} from "../lib/contratos";
import { codificarSeleccion, puntuar, recomendarPerfil, torreUsuario } from "../lib/recomendar";
import { leerModelo } from "./ayuda";

const destinos = validarDestinos(leerModelo("m3/destinos.json")).destinos;
const perfil = validarPerfilNuevo(leerModelo("m3/perfil_nuevo.json"));
const casos = validarCasosM3(leerModelo("m3/casos_paridad.json"), perfil);
const usuarios = validarUsuarios(leerModelo("m3/usuarios.json"));

describe("paridad con Python", () => {
  it("selección → vector de usuario → top-K: mismos destinos, mismo orden y mismos puntajes", () => {
    expect(casos.casos.length).toBeGreaterThanOrEqual(5);
    for (const c of casos.casos) {
      const r = recomendarPerfil(c.seleccion, perfil.preferencias, perfil.torre_usuario, destinos, c.k, c.vistos);
      r.vector_usuario.forEach((v, i) => expect(v).toBeCloseTo(c.vector_usuario[i], 9));
      expect(r.top_k.map((f) => f.destino_id), JSON.stringify(c.seleccion)).toEqual(c.top_k.map((f) => f.destino_id));
      r.top_k.forEach((f, i) => expect(f.puntaje).toBeCloseTo(c.top_k[i].puntaje, 9));
    }
  });

  it("hay casos con destinos ya vistos y esos destinos no aparecen", () => {
    const conVistos = casos.casos.filter((c) => c.vistos.length > 0);
    expect(conVistos.length).toBeGreaterThan(0);
    for (const c of conVistos) {
      const r = recomendarPerfil(c.seleccion, perfil.preferencias, perfil.torre_usuario, destinos, c.k, c.vistos);
      expect(r.top_k.some((f) => c.vistos.includes(f.destino_id))).toBe(false);
    }
  });

  it("el archivo es coherente con destinos, usuarios y perfil", () => {
    const d = validarDestinos(leerModelo("m3/destinos.json"));
    expect(() => validarCoherenciaM3(d, usuarios, perfil, casos)).not.toThrow();
  });
});

describe("codificación de la selección", () => {
  const pref: PreferenciaM3[] = [
    { id: "a", etiqueta: "A", opciones: [{ id: "x", etiqueta: "X" }, { id: "y", etiqueta: "Y" }] },
    { id: "b", etiqueta: "B", opciones: [{ id: "z", etiqueta: "Z" }] },
  ];

  it("one-hot por opción en el orden de la lista, sin importar el orden en que se eligió", () => {
    expect(codificarSeleccion(pref, { b: ["z"], a: ["y"] })).toEqual([0, 1, 1]);
    expect(codificarSeleccion(pref, { a: ["y", "x"] })).toEqual([1, 1, 0]);
    expect(codificarSeleccion(pref, {})).toEqual([0, 0, 0]);
  });

  it("la dimensión coincide con la del contrato", () => {
    expect(codificarSeleccion(perfil.preferencias, {})).toHaveLength(perfil.codificacion.dimension);
  });

  it("rechaza preferencias y opciones que no existen", () => {
    expect(() => codificarSeleccion(pref, { c: ["x"] })).toThrow(/preferencia desconocida/);
    expect(() => codificarSeleccion(pref, { a: ["z"] })).toThrow(/opción desconocida/);
  });
});

describe("torre de usuario", () => {
  const capas: CapaM3[] = [
    { W: [[1, -1], [0.5, 0.5]], b: [0, -1], activacion: "relu" },
    { W: [[2, 1]], b: [0.5], activacion: "ninguna" },
  ];

  it("aplica W·h + b y ReLU capa por capa (W es salida × entrada)", () => {
    // capa 1: [1·1 − 1·0, 0,5·1 + 0,5·0 − 1] = [1, −0,5] → ReLU → [1, 0]; capa 2: 2·1 + 1·0 + 0,5 = 2,5
    expect(torreUsuario([1, 0], capas)).toEqual([2.5]);
    expect(torreUsuario([0, 1], capas)).toEqual([0.5]); // [−1, −0,5] → [0, 0] → 0,5
  });

  it("rechaza una entrada de otra dimensión", () => {
    expect(() => torreUsuario([1, 2, 3], capas)).toThrow(/espera 2 entradas/);
  });
});

describe("puntaje y top-K", () => {
  const d = (id: string, embedding: number[], sesgo?: number): DestinoM3 => ({ id, nombre: id, embedding, ...(sesgo === undefined ? {} : { sesgo }), embedding_2d: [0, 0] });

  it("puntaje = producto punto + sesgo, de mayor a menor", () => {
    const lista = [d("A", [1, 0]), d("B", [0, 1], 5), d("C", [1, 1])];
    expect(puntuar([1, 2], lista, 3)).toEqual([
      { destino_id: "B", puntaje: 7 }, { destino_id: "C", puntaje: 3 }, { destino_id: "A", puntaje: 1 },
    ]);
  });

  it("en empate gana el id menor y los vistos se excluyen", () => {
    const lista = [d("D3", [1]), d("D1", [1]), d("D2", [1])];
    expect(puntuar([1], lista, 3).map((f) => f.destino_id)).toEqual(["D1", "D2", "D3"]);
    expect(puntuar([1], lista, 3, ["D1"]).map((f) => f.destino_id)).toEqual(["D2", "D3"]);
  });

  it("rechaza un K inválido y una selección vacía", () => {
    const sel = { actividad: ["playa"] };
    expect(() => recomendarPerfil(sel, perfil.preferencias, perfil.torre_usuario, destinos, 0)).toThrow(/k/);
    expect(() => recomendarPerfil(sel, perfil.preferencias, perfil.torre_usuario, destinos, 2.5)).toThrow(/k/);
    expect(() => recomendarPerfil({}, perfil.preferencias, perfil.torre_usuario, destinos, 3)).toThrow(/al menos una/);
    expect(() => recomendarPerfil({ actividad: [] }, perfil.preferencias, perfil.torre_usuario, destinos, 3)).toThrow(/al menos una/);
  });

  it("devuelve K destinos distintos con el K máximo del perfil", () => {
    const r = recomendarPerfil({ actividad: ["gastronomia"] }, perfil.preferencias, perfil.torre_usuario, destinos, perfil.k_max);
    expect(r.top_k).toHaveLength(perfil.k_max);
    expect(new Set(r.top_k.map((f) => f.destino_id)).size).toBe(perfil.k_max);
  });
});

describe("usuario sin historial", () => {
  it("está en los datos, no tiene historial y aun así trae su top-K completo", () => {
    const sin = usuarios.usuarios.filter((u) => u.historial.length === 0);
    expect(sin.length).toBeGreaterThan(0);
    for (const u of sin) {
      expect(u.top_k.length).toBeGreaterThanOrEqual(usuarios.k_max);
      u.top_k.forEach((f, i) => i > 0 && expect(f.puntaje).toBeLessThanOrEqual(u.top_k[i - 1].puntaje));
    }
  });

  it("su top-K sale solo del sesgo de los destinos (el vector de usuario es cero)", () => {
    const u = usuarios.usuarios.find((x) => x.historial.length === 0)!;
    const esperado = puntuar(new Array(destinos[0].embedding.length).fill(0), destinos, usuarios.k_max);
    expect(u.top_k.map((f) => f.destino_id)).toEqual(esperado.map((f) => f.destino_id));
  });
});
