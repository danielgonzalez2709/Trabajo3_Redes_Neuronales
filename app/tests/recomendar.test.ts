// Regla de JUGUETE del perfil nuevo de M3 y su paridad con Python (casos de perfil_nuevo.json).
import { describe, expect, it } from "vitest";
import { validarDestinos, validarPerfilNuevo, type DestinoM3 } from "../lib/contratos";
import { recomendarPerfilJuguete } from "../lib/recomendar";
import { leerModelo } from "./ayuda";

const destinos = validarDestinos(leerModelo("m3/destinos.json")).destinos;
const perfil = validarPerfilNuevo(leerModelo("m3/perfil_nuevo.json"));
const ids = perfil.preferencias.map((p) => p.id);
const peso = perfil.regla.peso_popularidad;

describe("recomendarPerfilJuguete", () => {
  it("coincide con Python: mismo top-K, mismo orden y mismos puntajes", () => {
    expect(perfil.casos_paridad.length).toBeGreaterThanOrEqual(5);
    for (const c of perfil.casos_paridad) {
      const r = recomendarPerfilJuguete(c.preferencias, destinos, ids, c.k, peso);
      expect(r.map((f) => f.destino_id), JSON.stringify(c.preferencias)).toEqual(c.top_k.map((f) => f.destino_id));
      r.forEach((f, i) => expect(f.puntaje).toBeCloseTo(c.top_k[i].puntaje, 9));
    }
  });

  it("no depende del orden en que se eligieron las preferencias", () => {
    const a = recomendarPerfilJuguete(["playa", "historia", "aventura"], destinos, ids, 8, peso);
    const b = recomendarPerfilJuguete(["aventura", "playa", "historia"], destinos, ids, 8, peso);
    expect(b).toEqual(a);
  });

  it("devuelve K destinos distintos de mayor a menor puntaje", () => {
    const r = recomendarPerfilJuguete(["gastronomia"], destinos, ids, 7, peso);
    expect(r).toHaveLength(7);
    expect(new Set(r.map((f) => f.destino_id)).size).toBe(7);
    r.forEach((f, i) => i > 0 && expect(f.puntaje).toBeLessThanOrEqual(r[i - 1].puntaje));
  });

  it("en empate gana el id menor", () => {
    const iguales: DestinoM3[] = ["D3", "D1", "D2"].map((id) => ({
      id, nombre: id, atributos: { a: 0.5 }, popularidad: 0.5, embedding_2d: [0, 0],
    }));
    expect(recomendarPerfilJuguete(["a"], iguales, ["a"], 3, 0.1).map((f) => f.destino_id)).toEqual(["D1", "D2", "D3"]);
  });

  it("con más preferencias, un destino que cumple todas sube", () => {
    const d = (id: string, a: number, b: number): DestinoM3 => ({ id, nombre: id, atributos: { a, b }, popularidad: 0, embedding_2d: [0, 0] });
    const lista = [d("X", 1, 0), d("Y", 0.6, 0.6)];
    expect(recomendarPerfilJuguete(["a"], lista, ["a", "b"], 1, 0)[0].destino_id).toBe("X");
    expect(recomendarPerfilJuguete(["a", "b"], lista, ["a", "b"], 1, 0)[0].destino_id).toBe("Y");
  });

  it("rechaza una selección vacía y un K inválido", () => {
    expect(() => recomendarPerfilJuguete([], destinos, ids, 5, peso)).toThrow(/preferencia/);
    expect(() => recomendarPerfilJuguete(["playa"], destinos, ids, 0, peso)).toThrow(/k/);
    expect(() => recomendarPerfilJuguete(["playa"], destinos, ids, 2.5, peso)).toThrow(/k/);
  });
});
