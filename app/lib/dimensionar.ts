// PROVISIONAL (juguete). Réplica en TypeScript de `dimensionar_juguete` de scripts/generar_juguetes_app.py.
// La función real de dimensionamiento es la de Camila (núcleo §5.4) y se porta en DA-6 con prueba de paridad contra Python.
// Dominio puro.
import type { DiaPronostico, SalidaDimensionamiento } from "./contratos";

/** Se resta antes de `ceil` para que el ruido de coma flotante no cambie el resultado (igual que en Python). */
const EPS = 1e-9;

/** ceil(x - EPS) sin el -0 que JavaScript devuelve para valores en (-1, 0]. */
const techo = (x: number): number => Math.ceil(x - EPS) + 0;

export type ParametrosOperacion = Record<string, number>;

const exigir = (p: ParametrosOperacion, clave: string): number => {
  const v = p[clave];
  if (typeof v !== "number" || !Number.isFinite(v)) throw new Error(`falta el parámetro «${clave}»`);
  return v;
};

/**
 * despachos = ceil(demanda / (capacidad · ocupación)); vehículos = ceil(despachos / viajes por vehículo y día);
 * conductores = ceil(vehículos · conductores por vehículo). Lanza error si un parámetro falta o no es positivo.
 */
export function dimensionarJuguete(demanda: number, params: ParametrosOperacion): SalidaDimensionamiento {
  const capacidad = exigir(params, "capacidad_pasajeros");
  const ocupacion = exigir(params, "ocupacion_objetivo");
  const viajes = exigir(params, "viajes_por_vehiculo_dia");
  const porVehiculo = exigir(params, "conductores_por_vehiculo");
  if (!(capacidad > 0 && ocupacion > 0 && viajes > 0 && porVehiculo >= 0)) throw new Error("parámetros fuera de rango");
  if (!Number.isFinite(demanda) || demanda < 0) throw new Error("la demanda debe ser un número >= 0");
  const despachos = Math.max(0, techo(demanda / (capacidad * ocupacion)));
  const vehiculos = techo(despachos / viajes);
  const conductores = techo(vehiculos * porVehiculo);
  return { despachos, vehiculos, conductores };
}

/** Demanda de un día para el cuantil elegido (`cuantil` debe ser uno de `cuantiles`; si no, error). */
export function demandaDelCuantil(dia: DiaPronostico, cuantiles: number[], cuantil: number): number {
  const i = cuantiles.indexOf(cuantil);
  if (i < 0) throw new Error(`el cuantil ${cuantil} no está entre los cuantiles del pronóstico`);
  return dia.q[i];
}

export interface FilaOperacion {
  fecha: string;
  demanda: number;
  despachos: number;
  vehiculos: number;
  conductores: number;
}

/** Tabla por día: demanda del cuantil elegido y lo que requiere la operación. */
export function tablaOperacion(dias: DiaPronostico[], cuantiles: number[], params: ParametrosOperacion): FilaOperacion[] {
  return dias.map((d) => {
    const demanda = demandaDelCuantil(d, cuantiles, params.cuantil);
    return { fecha: d.fecha, demanda, ...dimensionarJuguete(demanda, params) };
  });
}
