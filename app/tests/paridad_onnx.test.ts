// Paridad de M2 con Python: el ONNX corrido con onnxruntime-web (en Node, con el mismo .wasm que sirve la app) reproduce las
// probabilidades, los mapas y el CAM de PyTorch, y el preprocesado desde un ARCHIVO de imagen (redimensionado en TypeScript)
// reproduce el de Python dentro de una tolerancia documentada.
//
// Tolerancias:
// - desde una entrada ya al tamaño del modelo (casos 1 y 2): 1e-4 en probabilidades y mapas (solo difiere la aritmética en
//   float32 entre PyTorch y onnxruntime-web);
// - desde un archivo de imagen (caso 3): el redimensionado de Python (PIL BILINEAR, aritmética de punto fijo) y el de
//   `redimensionarBilineal` (coma flotante y redondeo a uint8 entre pasadas) pueden diferir en ±1 nivel de color por píxel; y
//   el decodificador del navegador, además, puede diferir del de PIL en JPEG. Se exige que ningún píxel difiera más de
//   NIVEL_MAX_PIXEL niveles y que las probabilidades difieran menos de TOL_PROB_ARCHIVO (un cambio de ±1 nivel mueve
//   las probabilidades del modelo del orden de 1e-3 por la escala de la normalización).
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { describe, expect, it } from "vitest";
import { calcularCam, indiceMaximo, preprocesar, softmax } from "../lib/clasificar";
import { validarEntradaCaso, validarMetaM2, type CasoParidadM2 } from "../lib/contratos";
import { redimensionarBilineal } from "../lib/imagen";
import { decodificarPng, leerModelo, rutaPublica } from "./ayuda";

const NIVEL_MAX_PIXEL = 1; // en la imagen de ejemplo coinciden exactamente (0 niveles); 1 deja margen para otras imágenes
const TOL_PROB_ARCHIVO = 0.01;
const TOL_ONNX = 1e-4;

const meta = validarMetaM2(leerModelo("m2/meta.json"));
const { alto, ancho } = meta.tamano_entrada;

const entradaDe = (c: CasoParidadM2): number[] =>
  c.entrada_rgb ?? validarEntradaCaso(leerModelo(`m2/${c.entrada_archivo}`), meta.tamano_entrada, `m2/${c.entrada_archivo}`);

async function sesion() {
  const ort = await import("onnxruntime-web/wasm");
  ort.env.wasm.wasmPaths = pathToFileURL(rutaPublica("ort/")).href; // en Node el cargador exige una URL file://
  ort.env.wasm.numThreads = 1;
  const modelo = await ort.InferenceSession.create(new Uint8Array(readFileSync(rutaPublica(`model/m2/${meta.archivo_modelo}`))), { executionProviders: ["wasm"] });
  const correr = async (rgb: ArrayLike<number>) => {
    const entrada = new ort.Tensor("float32", preprocesar(rgb, meta), [1, 3, alto, ancho]);
    const s = await modelo.run({ [meta.entrada_onnx]: entrada });
    return { logits: Array.from(s[meta.salidas_onnx.logits].data as Float32Array), mapas: s[meta.salidas_onnx.mapas].data as Float32Array };
  };
  return correr;
}

describe("M2: el ONNX en onnxruntime-web reproduce a PyTorch", () => {
  it("probabilidades, clase, mapas y CAM de cada caso", async () => {
    const correr = await sesion();
    for (const c of meta.casos_paridad) {
      const { logits, mapas } = await correr(entradaDe(c));
      softmax(logits).forEach((p, i) => expect(p, `${c.id} prob ${i}`).toBeCloseTo(c.probabilidades[i], 4));
      expect(indiceMaximo(logits), c.id).toBe(c.clase_predicha);
      expect(mapas.length).toBe(c.mapas.length);
      mapas.forEach((v, i) => expect(Math.abs(v - c.mapas[i]), `${c.id} mapa ${i}`).toBeLessThan(TOL_ONNX));
      calcularCam(mapas, c.forma_mapas, meta.pesos_cabeza[c.clase_predicha]).forEach((v, i) =>
        expect(Math.abs(v - c.cam_clase_predicha[i]), `${c.id} cam ${i}`).toBeLessThan(TOL_ONNX * 10),
      );
    }
  }, 60_000);

  it("desde un archivo de imagen (sin redimensionar): el redimensionado de la app reproduce al de Python con tolerancia", async () => {
    const delArchivo = meta.casos_paridad.filter((c) => c.imagen !== undefined);
    expect(delArchivo.length).toBeGreaterThan(0);
    const correr = await sesion();
    for (const c of delArchivo) {
      const png = decodificarPng(new Uint8Array(readFileSync(rutaPublica(`model/m2/ejemplos/${c.imagen}`))));
      expect(Math.max(png.alto, png.ancho), "la imagen de partida debe ser mayor que la entrada").toBeGreaterThan(Math.max(alto, ancho));
      const propio = redimensionarBilineal(png, alto, ancho);
      const esperado = entradaDe(c);
      const dif = Array.from(propio, (v, i) => Math.abs(v - esperado[i]));
      expect(Math.max(...dif), `${c.id}: píxel más lejano`).toBeLessThanOrEqual(NIVEL_MAX_PIXEL);
      const { logits } = await correr(propio);
      softmax(logits).forEach((p, i) => expect(Math.abs(p - c.probabilidades[i]), `${c.id} prob ${i}`).toBeLessThan(TOL_PROB_ARCHIVO));
      expect(indiceMaximo(logits), c.id).toBe(c.clase_predicha);
    }
  }, 60_000);
});
