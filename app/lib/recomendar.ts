// Recomendador de dos torres de M3 (núcleo §5.8), tal como lo describe el contrato en contratos.ts: selección → vector de
// entrada (one-hot por opción) → torre de usuario (capas lineales/MLP) → puntaje ⟨u, v_d⟩ + sesgo_d → top-K.
// Réplica de `codificar_seleccion`, `torre_usuario` y `puntuar` de scripts/generar_juguetes_app.py. Los pesos del
// juguete son aleatorios; los reales los entrena Juan José y usan este mismo formato. Dominio puro.
import type { CapaM3, DestinoM3, PreferenciaM3, RecomendacionM3, SeleccionM3 } from "./contratos";

/**
 * Selección → vector de entrada: un 1 por cada opción elegida y un 0 por las demás; preferencias en el orden de la lista
 * y, dentro de cada una, opciones en el orden de la lista. Lanza error si la selección nombra algo que no existe.
 */
export function codificarSeleccion(preferencias: PreferenciaM3[], seleccion: SeleccionM3): number[] {
  for (const [prefId, ops] of Object.entries(seleccion)) {
    const pref = preferencias.find((p) => p.id === prefId);
    if (!pref) throw new Error(`preferencia desconocida: ${prefId}`);
    for (const op of ops) {
      if (!pref.opciones.some((o) => o.id === op)) throw new Error(`opción desconocida en ${prefId}: ${op}`);
    }
  }
  const x: number[] = [];
  for (const pref of preferencias) {
    const elegidas = new Set(Object.hasOwn(seleccion, pref.id) ? seleccion[pref.id] : []);
    for (const o of pref.opciones) x.push(elegidas.has(o.id) ? 1 : 0);
  }
  return x;
}

/** Pasa `x` por las capas: `h = W·h + b` (W es salida × entrada) y ReLU si la activación es `relu`. */
export function torreUsuario(x: number[], capas: CapaM3[]): number[] {
  let h = x;
  for (const capa of capas) {
    if (capa.W[0].length !== h.length) throw new Error(`la capa espera ${capa.W[0].length} entradas y recibió ${h.length}`);
    h = capa.W.map((fila, i) => {
      let s = 0;
      for (let j = 0; j < fila.length; j++) s += fila[j] * h[j];
      s += capa.b[i];
      return capa.activacion === "relu" ? Math.max(s, 0) : s;
    });
  }
  return h;
}

/** Top-K por puntaje = ⟨u, v_d⟩ + sesgo_d (sesgo 0 si falta), sin los destinos `vistos`; en empate, id ascendente. */
export function puntuar(u: number[], destinos: DestinoM3[], k: number, vistos: string[] = []): RecomendacionM3[] {
  if (!Number.isInteger(k) || k < 1) throw new Error("k debe ser un entero >= 1");
  const excluidos = new Set(vistos);
  const filas = destinos
    .filter((d) => !excluidos.has(d.id))
    .map((d) => {
      let s = 0;
      for (let j = 0; j < u.length; j++) s += u[j] * d.embedding[j];
      return { destino_id: d.id, puntaje: s + (d.sesgo ?? 0) };
    });
  filas.sort((a, b) => b.puntaje - a.puntaje || (a.destino_id < b.destino_id ? -1 : a.destino_id > b.destino_id ? 1 : 0));
  return filas.slice(0, k);
}

export interface ResultadoPerfil {
  /** Vector u de la torre de usuario. */
  vector_usuario: number[];
  top_k: RecomendacionM3[];
}

/** Recomienda a un perfil nuevo: exige al menos una opción elegida. */
export function recomendarPerfil(
  seleccion: SeleccionM3,
  preferencias: PreferenciaM3[],
  capas: CapaM3[],
  destinos: DestinoM3[],
  k: number,
  vistos: string[] = [],
): ResultadoPerfil {
  if (Object.values(seleccion).every((v) => v.length === 0)) throw new Error("seleccione al menos una opción");
  const vector_usuario = torreUsuario(codificarSeleccion(preferencias, seleccion), capas);
  return { vector_usuario, top_k: puntuar(vector_usuario, destinos, k, vistos) };
}
