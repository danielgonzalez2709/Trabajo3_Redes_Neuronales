// Carga de los archivos de public/model/ con su validación de contrato. Todo se sirve desde la propia app (sin CDN).
import { ErrorContrato } from "./contratos";

/** Ruta absoluta de un archivo dentro de public/model/ (`ruta` sin barra inicial, p. ej. "m1/pronosticos.json"). */
export const urlModelo = (ruta: string): string => `/model/${ruta}`;

/** Descarga un JSON y lo valida; los errores de red, de formato y de contrato llegan como `Error` con un mensaje en español. */
export async function cargarJson<T>(ruta: string, validar: (raiz: unknown, archivo: string) => T): Promise<T> {
  let respuesta: Response;
  try {
    respuesta = await fetch(urlModelo(ruta));
  } catch {
    throw new Error(`No se pudo leer ${ruta} (sin conexión con la app).`);
  }
  if (!respuesta.ok) throw new Error(`No se pudo leer ${ruta} (HTTP ${respuesta.status}).`);
  let raiz: unknown;
  try {
    raiz = await respuesta.json();
  } catch {
    throw new Error(`${ruta} no es un JSON válido.`);
  }
  try {
    return validar(raiz, ruta);
  } catch (e) {
    if (e instanceof ErrorContrato) throw new Error(`Contrato incumplido en ${e.message}`);
    throw e;
  }
}
