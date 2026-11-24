// Inferencia de M2 en el navegador con ONNX Runtime Web (solo cliente). Los .wasm se sirven desde la propia app
// (public/ort/), sin CDN: la app funciona en local sin internet.
import type { InferenceSession } from "onnxruntime-web/wasm";
import { calcularCam, indiceMaximo, preprocesar, softmax } from "./clasificar";
import type { MetaM2 } from "./contratos";
import { urlModelo } from "./datos";

/** Carpeta pública con los archivos de onnxruntime-web (copiados de node_modules/onnxruntime-web/dist). */
export const RUTA_ORT = "/ort/";

type Ort = typeof import("onnxruntime-web/wasm");
let ortPromesa: Promise<Ort> | null = null;
const sesiones = new Map<string, Promise<InferenceSession>>();

function cargarOrt(): Promise<Ort> {
  ortPromesa ??= import("onnxruntime-web/wasm").then((ort) => {
    ort.env.wasm.wasmPaths = RUTA_ORT;
    ort.env.wasm.numThreads = 1; // un hilo: no exige aislamiento de origen cruzado (cabeceras COOP/COEP)
    return ort;
  });
  return ortPromesa;
}

function sesionDe(meta: MetaM2): Promise<InferenceSession> {
  const url = urlModelo(`m2/${meta.archivo_modelo}`);
  let s = sesiones.get(url);
  if (!s) {
    s = cargarOrt().then((ort) => ort.InferenceSession.create(url, { executionProviders: ["wasm"] }));
    s.catch(() => sesiones.delete(url)); // si falla, que el siguiente intento reintente
    sesiones.set(url, s);
  }
  return s;
}

export interface SalidaModelo {
  logits: number[];
  probabilidades: number[];
  claseIndice: number;
  /** Forma de las activaciones: [canales, alto, ancho]. */
  formaMapas: [number, number, number];
  /** Activaciones de la última capa convolucional, aplanadas (C·H·W). */
  mapas: Float32Array;
  /** CAM de la clase asignada (H·W); se pinta en DA-7. */
  cam: number[];
}

/** Corre el ONNX sobre una imagen RGB uint8 ya al tamaño de entrada del modelo (alto·ancho·3). */
export async function ejecutarModelo(meta: MetaM2, rgb: ArrayLike<number>): Promise<SalidaModelo> {
  const [ort, sesion] = await Promise.all([cargarOrt(), sesionDe(meta)]);
  const { alto, ancho } = meta.tamano_entrada;
  const entrada = new ort.Tensor("float32", preprocesar(rgb, meta), [1, 3, alto, ancho]);
  const salidas = await sesion.run({ [meta.entrada_onnx]: entrada });
  const logitsT = salidas[meta.salidas_onnx.logits];
  const mapasT = salidas[meta.salidas_onnx.mapas];
  if (!logitsT || !mapasT) throw new Error("El modelo no devolvió las salidas esperadas (logits y mapas).");
  const logits = Array.from(logitsT.data as Float32Array);
  const dims = mapasT.dims;
  if (dims.length !== 4) throw new Error("La salida «mapas» debe tener forma [lote, canales, alto, ancho].");
  const forma: [number, number, number] = [dims[1], dims[2], dims[3]];
  const mapas = mapasT.data as Float32Array;
  const claseIndice = indiceMaximo(logits);
  return {
    logits,
    probabilidades: softmax(logits),
    claseIndice,
    formaMapas: forma,
    mapas,
    cam: calcularCam(mapas, forma, meta.pesos_cabeza[claseIndice]),
  };
}
