// Utilidades de las pruebas. Hay DOS fuentes de archivos de modelo y las pruebas no deben confundirlas:
// - lo SERVIDO (`leerModelo`, `rutaModelo`): app/public/model/, lo que ve el usuario; puede ser el juguete o el modelo real
//   de cada módulo, así que las pruebas sobre esto solo comprueban lo que vale para ambos;
// - el JUGUETE (`leerJuguete`, `rutaJuguete`): el fixture versionado app/tests/fixtures/juguete/ (lo escribe
//   scripts/generar_juguetes_app.py), siempre `juguete: true` con ids y preferencias conocidos; aquí van la lógica, los
//   casos inválidos y las funciones de juguete.
// La variable de entorno MODELO_SERVIDO_DIR (SOLO para pruebas) apunta lo «servido» a otra carpeta con m1/, m2/ y m3/;
// sirve para simular en una copia temporal la llegada de un modelo real sin tocar el repositorio.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { inflateSync } from "node:zlib";

const raiz = (ruta: string) => fileURLToPath(new URL(`../public/${ruta}`, import.meta.url));
const carpetaJuguete = fileURLToPath(new URL("./fixtures/juguete/", import.meta.url));
const carpetaServida = (): string => {
  const alt = process.env.MODELO_SERVIDO_DIR;
  return alt ? alt.replace(/[\\/]+$/, "") + "/" : raiz("model/");
};

const leerJson = (ruta: string): unknown => JSON.parse(readFileSync(ruta, "utf-8"));
const hay = (ruta: string): boolean => {
  try {
    readFileSync(ruta);
    return true;
  } catch {
    return false;
  }
};

/** JSON servido (app/public/model/, o MODELO_SERVIDO_DIR): `ruta` como "m1/pronosticos.json". */
export const leerModelo = (ruta: string): unknown => leerJson(carpetaServida() + ruta);
/** Ruta en disco de un archivo servido de los modelos (p. ej. "m2/modelo.onnx"). */
export const rutaModelo = (ruta: string): string => carpetaServida() + ruta;
export const existeModelo = (ruta: string): boolean => hay(rutaModelo(ruta));

/** JSON del fixture de juguete (app/tests/fixtures/juguete/). */
export const leerJuguete = (ruta: string): unknown => leerJson(carpetaJuguete + ruta);
/** Ruta en disco de un archivo del fixture de juguete (el ONNX, las imágenes de ejemplo). */
export const rutaJuguete = (ruta: string): string => carpetaJuguete + ruta;
export const existeJuguete = (ruta: string): boolean => hay(rutaJuguete(ruta));

/** ¿Existe el archivo `ruta` dentro de public/ (p. ej. los .wasm de onnxruntime en "ort/")? */
export const existe = (ruta: string): boolean => hay(raiz(ruta));
/** Ruta en disco de un archivo de public/ (para los .wasm de onnxruntime). */
export const rutaPublica = raiz;
/** Copia profunda editable de un JSON para armar casos inválidos. */
export const copia = <T,>(x: T): T => structuredClone(x);

/**
 * Decodifica un PNG de 8 bits por canal, sin entrelazado, en escala de grises, RGB o RGBA (lo que escribe PIL para las
 * imágenes de ejemplo) a RGB uint8 aplanado (alto, ancho, canal). En el navegador esto lo hace el decodificador del navegador.
 */
export function decodificarPng(bytes: Uint8Array): { rgb: Uint8ClampedArray; alto: number; ancho: number } {
  const b = Buffer.from(bytes);
  if (b.subarray(0, 8).toString("hex") !== "89504e470d0a1a0a") throw new Error("no es un PNG");
  let ancho = 0;
  let alto = 0;
  let tipo = 0;
  const datos: Buffer[] = [];
  for (let i = 8; i < b.length; ) {
    const largo = b.readUInt32BE(i);
    const nombre = b.subarray(i + 4, i + 8).toString("latin1");
    const cuerpo = b.subarray(i + 8, i + 8 + largo);
    if (nombre === "IHDR") {
      ancho = cuerpo.readUInt32BE(0);
      alto = cuerpo.readUInt32BE(4);
      if (cuerpo[8] !== 8 || cuerpo[12] !== 0) throw new Error("solo PNG de 8 bits y sin entrelazado");
      tipo = cuerpo[9];
    } else if (nombre === "IDAT") {
      datos.push(cuerpo);
    }
    i += 12 + largo;
  }
  const canales = ({ 0: 1, 2: 3, 6: 4 } as Record<number, number>)[tipo];
  if (!canales) throw new Error(`tipo de color PNG no admitido: ${tipo}`);
  const crudo = inflateSync(Buffer.concat(datos));
  const fila = ancho * canales;
  const pix = new Uint8Array(alto * fila);
  for (let y = 0; y < alto; y++) {
    const filtro = crudo[y * (fila + 1)];
    for (let x = 0; x < fila; x++) {
      const v = crudo[y * (fila + 1) + 1 + x];
      const izq = x >= canales ? pix[y * fila + x - canales] : 0;
      const arr = y > 0 ? pix[(y - 1) * fila + x] : 0;
      const arrIzq = y > 0 && x >= canales ? pix[(y - 1) * fila + x - canales] : 0;
      let pred = 0;
      if (filtro === 1) pred = izq;
      else if (filtro === 2) pred = arr;
      else if (filtro === 3) pred = (izq + arr) >> 1;
      else if (filtro === 4) {
        const p = izq + arr - arrIzq;
        const [da, db, dc] = [Math.abs(p - izq), Math.abs(p - arr), Math.abs(p - arrIzq)];
        pred = da <= db && da <= dc ? izq : db <= dc ? arr : arrIzq;
      }
      pix[y * fila + x] = (v + pred) & 255;
    }
  }
  const rgb = new Uint8ClampedArray(alto * ancho * 3);
  for (let i = 0; i < alto * ancho; i++) {
    for (let c = 0; c < 3; c++) rgb[i * 3 + c] = pix[i * canales + (canales === 1 ? 0 : c)];
  }
  return { rgb, alto, ancho };
}
