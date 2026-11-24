// PROVISIONAL (juguete). Réplica en TypeScript de `dimensionar_juguete` de scripts/generar_juguetes_app.py.
// La función real de dimensionamiento es la de Camila (núcleo §5.4) y se porta en DA-6 con prueba de paridad contra Python.
// Aquí queda lo que no cambia con la función real: aplanar los parámetros de una ruta a `{ref: valor}`, elegir la demanda
// del cuantil y armar la tabla por día. Dominio puro.
import type { DiaPronostico, ParametrosOperacion, SalidaDimensionamiento } from "./contratos";

/** Se resta antes de `ceil` (y se suma antes de `floor`) para que el ruido de coma flotante no cambie el resultado, igual que en Python. */
const EPS = 1e-9;

/** ceil(x - EPS) sin el -0 que JavaScript devuelve para valores en (-1, 0]. */
const techo = (x: number): number => Math.ceil(x - EPS) + 0;

/** Parámetros efectivos de UNA ruta: `{referencia: valor}` (ver `ParametrosOperacion` en contratos.ts). */
export type ParametrosEfectivos = Record<string, number>;

/** Resultado del juguete: el contrato más los pasos intermedios, siempre presentes. */
export interface ResultadoDimensionamiento extends SalidaDimensionamiento {
  pasos: Record<string, number>;
}

/** Aplana los parámetros de una ruta a `{referencia: valor}` (igual que `parametros_efectivos` de Python, sin cambios). */
export function parametrosBase(p: ParametrosOperacion, rutaId: string): ParametrosEfectivos {
  if (!Object.hasOwn(p.por_ruta, rutaId) || !Object.hasOwn(p.composicion_clases, rutaId)) {
    throw new Error(`la ruta ${rutaId} no tiene parámetros por ruta ni composición por clase`);
  }
  const plano: ParametrosEfectivos = {};
  for (const [k, par] of Object.entries(p.globales)) plano[`globales.${k}`] = par.valor;
  for (const [k, par] of Object.entries(p.por_ruta[rutaId])) plano[`por_ruta.${k}`] = par.valor;
  for (const [clase, pars] of Object.entries(p.por_clase)) {
    for (const [k, par] of Object.entries(pars)) plano[`por_clase.${clase}.${k}`] = par.valor;
  }
  for (const [clase, par] of Object.entries(p.composicion_clases[rutaId])) plano[`composicion_clases.${clase}`] = par.valor;
  return plano;
}

const exigir = (p: ParametrosEfectivos, ref: string): number => {
  const v = Object.hasOwn(p, ref) ? p[ref] : undefined;
  if (typeof v !== "number" || !Number.isFinite(v)) throw new Error(`falta el parámetro «${ref}»`);
  return v;
};

/**
 * capacidad_media = Σ_clase composición · capacidad (clases en orden alfabético); asientos_utiles = capacidad_media ·
 * ocupación objetivo; despachos = ceil(demanda / asientos_utiles); viajes_efectivos = max(1, min(viajes por vehículo y día,
 * floor(horas de operación / tiempo de ciclo))); vehículos = ceil(despachos / viajes_efectivos); conductores =
 * ceil(vehículos · conductores por vehículo). Lanza error si un parámetro falta o está fuera de rango.
 */
export function dimensionarJuguete(demanda: number, p: ParametrosEfectivos): ResultadoDimensionamiento {
  const clases = Object.keys(p)
    .filter((k) => k.startsWith("composicion_clases."))
    .map((k) => k.slice("composicion_clases.".length))
    .sort();
  if (clases.length === 0) throw new Error("faltan las composiciones por clase");
  const ocupacion = exigir(p, "globales.ocupacion_objetivo");
  const viajes = exigir(p, "globales.viajes_por_vehiculo_dia");
  const porVehiculo = exigir(p, "globales.conductores_por_vehiculo");
  const horas = exigir(p, "globales.horas_operacion_dia");
  const ciclo = exigir(p, "por_ruta.tiempo_ciclo_h");
  if (!(ocupacion > 0 && viajes > 0 && porVehiculo > 0 && horas > 0 && ciclo > 0)) throw new Error("parámetros fuera de rango");
  if (!Number.isFinite(demanda) || demanda < 0) throw new Error("la demanda debe ser un número >= 0");
  let capacidadMedia = 0;
  for (const c of clases) capacidadMedia += exigir(p, `composicion_clases.${c}`) * exigir(p, `por_clase.${c}.capacidad_pasajeros`);
  if (!(capacidadMedia > 0)) throw new Error("la capacidad media debe ser positiva");
  const asientosUtiles = capacidadMedia * ocupacion;
  const despachos = Math.max(0, techo(demanda / asientosUtiles));
  const viajesEfectivos = Math.max(1, Math.min(Math.floor(viajes + EPS), Math.floor(horas / ciclo + EPS)));
  const vehiculos = techo(despachos / viajesEfectivos);
  const conductores = techo(vehiculos * porVehiculo);
  return {
    despachos,
    vehiculos,
    conductores,
    pasos: { capacidad_media: capacidadMedia, asientos_utiles: asientosUtiles, viajes_efectivos: viajesEfectivos },
  };
}

/** Demanda de un día para el cuantil elegido (`cuantil` debe ser uno de `cuantiles`; si no, error). */
export function demandaDelCuantil(dia: DiaPronostico, cuantiles: number[], cuantil: number): number {
  const i = cuantiles.indexOf(cuantil);
  if (i < 0) throw new Error(`el cuantil ${cuantil} no está entre los cuantiles del pronóstico`);
  return dia.q[i];
}

export interface FilaOperacion extends ResultadoDimensionamiento {
  fecha: string;
  demanda: number;
}

/** Tabla por día: demanda del cuantil elegido (`globales.cuantil`) y lo que requiere la operación. */
export function tablaOperacion(dias: DiaPronostico[], cuantiles: number[], params: ParametrosEfectivos): FilaOperacion[] {
  const cuantil = exigir(params, "globales.cuantil");
  return dias.map((d) => {
    const demanda = demandaDelCuantil(d, cuantiles, cuantil);
    return { fecha: d.fecha, demanda, ...dimensionarJuguete(demanda, params) };
  });
}
