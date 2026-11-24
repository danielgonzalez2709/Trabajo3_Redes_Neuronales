// Lectura de m2/meta.json y la lógica de M2 que no necesita el navegador (preprocesado, softmax, alerta, CAM).
// La inferencia con el ONNX en el navegador se prueba contra estos mismos casos en DA-7.
import { describe, expect, it } from "vitest";
import { calcularCam, decidirAlerta, indiceMaximo, preprocesar, probabilidadConAlerta, softmax } from "../lib/clasificar";
import { MAX_CASOS_M2, validarEntradaCaso, validarMetaM2 } from "../lib/contratos";
import { existe, leerModelo } from "./ayuda";

const meta = validarMetaM2(leerModelo("m2/meta.json"));

describe("meta.json de M2", () => {
  it("trae las 5 clases del enunciado con su grupo de alerta", () => {
    expect(meta.clases.map((c) => c.nombre)).toEqual([
      "Conducción segura", "Giro", "Escribir en el teléfono", "Hablar por teléfono", "Otros comportamientos riesgosos",
    ]);
    expect(meta.grupo_alerta.conduccion_segura).toBe("sin_alerta");
    expect(Object.values(meta.grupo_alerta).filter((g) => g === "con_alerta")).toHaveLength(4);
    expect(meta.grupo_alerta_provisional).toBe(true);
  });

  it("declara entrada, salidas y pesos de la cabeza consistentes", () => {
    expect(meta.entrada_onnx).toBe("entrada");
    expect(meta.salidas_onnx).toEqual({ logits: "logits", mapas: "mapas" });
    expect(meta.pesos_cabeza).toHaveLength(meta.clases.length);
    expect(meta.sesgo_cabeza).toHaveLength(meta.clases.length);
    expect(meta.umbral_por_defecto).toBeGreaterThanOrEqual(0);
    expect(meta.umbral_por_defecto).toBeLessThanOrEqual(1);
  });

  it("los archivos que nombra existen: modelo ONNX, ejemplos y los .wasm de onnxruntime servidos por la app", () => {
    expect(existe(`model/m2/${meta.archivo_modelo}`)).toBe(true);
    for (const e of meta.ejemplos) expect(existe(`model/m2/ejemplos/${e.archivo}`), e.archivo).toBe(true);
    expect(existe("ort/ort-wasm-simd-threaded.wasm")).toBe(true);
    expect(existe("ort/ort-wasm-simd-threaded.mjs")).toBe(true);
  });

  it("declara el preprocesado y trae a lo sumo 3 casos, con uno desde un archivo de imagen y uno con la entrada en archivo aparte", () => {
    expect(meta.preprocesado).toEqual({
      redimensionado: "estirar", interpolacion: "bilineal", canales: "RGB", escala: "0-1", normalizacion: "media_desviacion",
    });
    expect(meta.casos_paridad.length).toBeLessThanOrEqual(MAX_CASOS_M2);
    const conImagen = meta.casos_paridad.filter((c) => c.imagen !== undefined);
    expect(conImagen.length).toBeGreaterThan(0);
    expect(meta.casos_paridad.some((c) => c.entrada_archivo !== undefined)).toBe(true);
    for (const c of meta.casos_paridad) {
      if (c.entrada_archivo) {
        const rgb = validarEntradaCaso(leerModelo(`m2/${c.entrada_archivo}`), meta.tamano_entrada, c.entrada_archivo);
        expect(rgb).toHaveLength(meta.tamano_entrada.alto * meta.tamano_entrada.ancho * 3);
      }
      if (c.imagen) expect(existe(`model/m2/ejemplos/${c.imagen}`), c.imagen).toBe(true);
    }
  });
});

describe("lógica de M2", () => {
  it("preprocesar: normaliza por canal y ordena como [canal, alto, ancho]", () => {
    const { alto, ancho } = meta.tamano_entrada;
    const rgb = new Uint8Array(alto * ancho * 3);
    for (let i = 0; i < alto * ancho; i++) rgb.set([0, 128, 255], i * 3);
    const t = preprocesar(rgb, meta);
    expect(t).toHaveLength(3 * alto * ancho);
    const esperado = [0, 128, 255].map((v, c) => (v / 255 - meta.media[c]) / meta.desviacion[c]);
    [0, 1, 2].forEach((c) => {
      expect(t[c * alto * ancho]).toBeCloseTo(esperado[c], 5);
      expect(t[(c + 1) * alto * ancho - 1]).toBeCloseTo(esperado[c], 5);
    });
  });

  it("preprocesar: rechaza una imagen del tamaño equivocado", () => {
    expect(() => preprocesar(new Uint8Array(10), meta)).toThrow(/debe tener/);
  });

  it("softmax: suma 1, es estable con logits enormes y conserva el orden", () => {
    const p = softmax([1000, 1001, 999]);
    expect(p.reduce((a, b) => a + b, 0)).toBeCloseTo(1, 12);
    expect(indiceMaximo(p)).toBe(1);
    expect(p.every(Number.isFinite)).toBe(true);
  });

  it("los casos de paridad: softmax de los logits = probabilidades de PyTorch", () => {
    for (const c of meta.casos_paridad) {
      softmax(c.logits).forEach((p, i) => expect(p).toBeCloseTo(c.probabilidades[i], 5));
      expect(indiceMaximo(c.probabilidades)).toBe(c.clase_predicha);
    }
  });

  it("los casos de paridad: CAM de la clase predicha = Σ pesos · mapas", () => {
    for (const c of meta.casos_paridad) {
      const cam = calcularCam(c.mapas, c.forma_mapas, meta.pesos_cabeza[c.clase_predicha]);
      expect(cam).toHaveLength(c.cam_clase_predicha.length);
      cam.forEach((v, i) => expect(v).toBeCloseTo(c.cam_clase_predicha[i], 4));
    }
  });

  it("la cabeza GAP + lineal reproduce los logits desde los mapas (base del CAM)", () => {
    for (const c of meta.casos_paridad) {
      const [canales, alto, ancho] = c.forma_mapas;
      meta.clases.forEach((_, k) => {
        let logit = meta.sesgo_cabeza[k];
        for (let ch = 0; ch < canales; ch++) {
          let media = 0;
          for (let i = 0; i < alto * ancho; i++) media += c.mapas[ch * alto * ancho + i];
          logit += meta.pesos_cabeza[k][ch] * (media / (alto * ancho));
        }
        expect(logit).toBeCloseTo(c.logits[k], 4);
      });
    }
  });

  it("decisión de alerta: P(con alerta) frente al umbral (>= dispara)", () => {
    const p = [0.5, 0.2, 0.1, 0.1, 0.1]; // la clase 0 es «sin alerta»
    expect(probabilidadConAlerta(p, meta)).toBeCloseTo(0.5, 12);
    expect(decidirAlerta(p, meta, 0.5).grupo).toBe("con_alerta"); // igual al umbral: alerta
    expect(decidirAlerta(p, meta, 0.51).grupo).toBe("sin_alerta");
    expect(decidirAlerta([1, 0, 0, 0, 0], meta, 0.01).grupo).toBe("sin_alerta");
    expect(decidirAlerta([0, 1, 0, 0, 0], meta, 1).grupo).toBe("con_alerta");
  });
});
