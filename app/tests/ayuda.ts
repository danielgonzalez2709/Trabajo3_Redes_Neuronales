// Utilidades de las pruebas: lee los archivos de public/model/ tal como los sirve la app.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const raiz = (ruta: string) => fileURLToPath(new URL(`../public/${ruta}`, import.meta.url));

export const leerModelo = (ruta: string): unknown => JSON.parse(readFileSync(raiz(`model/${ruta}`), "utf-8"));
export const existe = (ruta: string): boolean => {
  try {
    readFileSync(raiz(ruta));
    return true;
  } catch {
    return false;
  }
};
/** Copia profunda editable de un JSON para armar casos inválidos. */
export const copia = <T,>(x: T): T => structuredClone(x);
