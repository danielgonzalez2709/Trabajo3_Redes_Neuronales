// Contratos de los archivos de app/public/model/ (núcleo §5.4, §5.6 y §5.8): tipos y validadores.
//
// Cada archivo lo produce su dueño (M1: Camila; M2: José; M3: Juan José) y la app lo valida al cargarlo: un archivo que no
// cumple el contrato falla con un mensaje claro («archivo: ruta.del.campo: problema»), nunca se muestra a medias.
// Los archivos de DA-5 son de JUGUETE (`"juguete": true`, scripts/generar_juguetes_app.py); los reales usan el mismo esquema
// con `"juguete": false`. Si un contrato debe cambiar, se cambia aquí, en el generador y en el Spec con aviso al dueño.
// Dominio puro: sin React ni acceso a red.

// ------------------------------------------------------------------------------------------------ errores y lector

export class ErrorContrato extends Error {
  constructor(
    public readonly archivo: string,
    public readonly ruta: string,
    public readonly problema: string,
  ) {
    super(`${archivo}: ${ruta}: ${problema}`);
    this.name = "ErrorContrato";
  }
}

type Obj = Record<string, unknown>;

/** Lector con comprobaciones mínimas: cada método devuelve el valor ya tipado o lanza `ErrorContrato`. */
class Lector {
  constructor(private readonly archivo: string) {}

  falla(ruta: string, problema: string): never {
    throw new ErrorContrato(this.archivo, ruta, problema);
  }

  objeto(x: unknown, ruta: string): Obj {
    if (typeof x !== "object" || x === null || Array.isArray(x)) this.falla(ruta, "debe ser un objeto");
    return x as Obj;
  }

  texto(x: unknown, ruta: string): string {
    if (typeof x !== "string" || x.length === 0) this.falla(ruta, "debe ser un texto no vacío");
    return x as string;
  }

  textoOpcional(x: unknown, ruta: string): string | undefined {
    return x === undefined ? undefined : this.texto(x, ruta);
  }

  numero(x: unknown, ruta: string): number {
    if (typeof x !== "number" || !Number.isFinite(x)) this.falla(ruta, "debe ser un número finito");
    return x as number;
  }

  entero(x: unknown, ruta: string, minimo = Number.NEGATIVE_INFINITY): number {
    const n = this.numero(x, ruta);
    if (!Number.isInteger(n) || n < minimo) this.falla(ruta, `debe ser un entero >= ${minimo}`);
    return n;
  }

  booleano(x: unknown, ruta: string): boolean {
    if (typeof x !== "boolean") this.falla(ruta, "debe ser verdadero o falso");
    return x as boolean;
  }

  arreglo(x: unknown, ruta: string, minimo = 0): unknown[] {
    if (!Array.isArray(x)) this.falla(ruta, "debe ser una lista");
    if ((x as unknown[]).length < minimo) this.falla(ruta, `debe tener al menos ${minimo} elementos`);
    return x as unknown[];
  }

  numeros(x: unknown, ruta: string, largo?: number): number[] {
    const a = this.arreglo(x, ruta);
    if (largo !== undefined && a.length !== largo) this.falla(ruta, `debe tener ${largo} elementos (tiene ${a.length})`);
    return a.map((v, i) => this.numero(v, `${ruta}[${i}]`));
  }

  textos(x: unknown, ruta: string): string[] {
    return this.arreglo(x, ruta).map((v, i) => this.texto(v, `${ruta}[${i}]`));
  }

  fecha(x: unknown, ruta: string): string {
    const t = this.texto(x, ruta);
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(t);
    const d = m ? new Date(Date.UTC(+m[1], +m[2] - 1, +m[3])) : null;
    if (!m || !d || d.getUTCFullYear() !== +m[1] || d.getUTCMonth() !== +m[2] - 1 || d.getUTCDate() !== +m[3]) {
      this.falla(ruta, `debe ser una fecha AAAA-MM-DD válida (llegó «${t}»)`);
    }
    return t;
  }

  /** Encabezado común: `version` (entero >= 1), `juguete` (booleano) y `aviso` opcional. */
  base(raiz: unknown): Base {
    const o = this.objeto(raiz, "$");
    return {
      version: this.entero(o.version, "version", 1),
      juguete: this.booleano(o.juguete, "juguete"),
      aviso: this.textoOpcional(o.aviso, "aviso"),
    };
  }
}

export interface Base {
  /** Versión del esquema del archivo (entero >= 1). */
  version: number;
  /** true si el archivo es de juguete (datos ficticios): la app muestra el aviso «Datos de juguete». */
  juguete: boolean;
  /** Texto opcional que explica de dónde salen los datos. */
  aviso?: string;
}

// ------------------------------------------------------------------------------------------------------- M1 §5.4

/** Un municipio. */
export interface Lugar {
  /** Código DIVIPOLA (5 dígitos); en el juguete, código ficticio del departamento 00. */
  codigo: string;
  /** Nombre del municipio. */
  nombre: string;
}

export interface PuntoHistoria {
  /** Día (AAAA-MM-DD). */
  fecha: string;
  /** Pasajeros observados ese día (entero >= 0). */
  pasajeros: number;
}

export interface DiaPronostico {
  /** Día pronosticado (AAAA-MM-DD). */
  fecha: string;
  /** Pasos adelante desde `fecha_origen` (1 = el día siguiente al origen). */
  h: number;
  /** Pronóstico puntual de pasajeros (>= 0). */
  punto: number;
  /** Un valor por cada cuantil de `Pronosticos.cuantiles`, en el mismo orden y no decreciente (>= 0). */
  q: number[];
}

export interface RutaPronostico {
  /** Identificador `"<origen>-<destino>"`. */
  ruta_id: string;
  origen: Lugar;
  destino: Lugar;
  /** `ruta_id` del sentido contrario. */
  ruta_regreso_id: string;
  /** Últimos ~90 días observados, en orden cronológico; el último es `fecha_origen`. */
  historia: PuntoHistoria[];
  /** `horizonte` días pronosticados, `h` = 1..horizonte. */
  pronostico: DiaPronostico[];
}

/** `m1/pronosticos.json`. */
export interface Pronosticos extends Base {
  /** Nombre del modelo que produjo el pronóstico. */
  modelo: string;
  /** Último día con información (AAAA-MM-DD). */
  fecha_origen: string;
  /** Número de días pronosticados (30). */
  horizonte: number;
  /** Cuantiles del pronóstico, estrictamente crecientes en (0, 1), p. ej. [0.5, 0.75, 0.9, 0.95]. */
  cuantiles: number[];
  rutas: RutaPronostico[];
}

export function validarPronosticos(raiz: unknown, archivo = "m1/pronosticos.json"): Pronosticos {
  const r = new Lector(archivo);
  const base = r.base(raiz);
  const o = raiz as Obj;
  const horizonte = r.entero(o.horizonte, "horizonte", 1);
  const cuantiles = r.numeros(o.cuantiles, "cuantiles");
  if (cuantiles.length === 0) r.falla("cuantiles", "debe tener al menos un cuantil");
  cuantiles.forEach((c, i) => {
    if (c <= 0 || c >= 1) r.falla(`cuantiles[${i}]`, "debe estar entre 0 y 1 (sin incluirlos)");
    if (i > 0 && c <= cuantiles[i - 1]) r.falla(`cuantiles[${i}]`, "los cuantiles deben ser estrictamente crecientes");
  });
  const lugar = (x: unknown, ruta: string): Lugar => {
    const l = r.objeto(x, ruta);
    return { codigo: r.texto(l.codigo, `${ruta}.codigo`), nombre: r.texto(l.nombre, `${ruta}.nombre`) };
  };
  const ids = new Set<string>();
  const rutas = r.arreglo(o.rutas, "rutas", 1).map((x, i): RutaPronostico => {
    const p = `rutas[${i}]`;
    const e = r.objeto(x, p);
    const ruta_id = r.texto(e.ruta_id, `${p}.ruta_id`);
    if (ids.has(ruta_id)) r.falla(`${p}.ruta_id`, `ruta repetida: ${ruta_id}`);
    ids.add(ruta_id);
    const historia = r.arreglo(e.historia, `${p}.historia`, 1).map((h, j): PuntoHistoria => {
      const q = r.objeto(h, `${p}.historia[${j}]`);
      return { fecha: r.fecha(q.fecha, `${p}.historia[${j}].fecha`), pasajeros: r.entero(q.pasajeros, `${p}.historia[${j}].pasajeros`, 0) };
    });
    historia.forEach((h, j) => {
      if (j > 0 && h.fecha <= historia[j - 1].fecha) r.falla(`${p}.historia[${j}].fecha`, "las fechas deben ser crecientes");
    });
    if (historia[historia.length - 1].fecha !== r.fecha(o.fecha_origen, "fecha_origen")) {
      r.falla(`${p}.historia`, "el último día de la historia debe ser fecha_origen");
    }
    const pronostico = r.arreglo(e.pronostico, `${p}.pronostico`).map((d, j): DiaPronostico => {
      const q = r.objeto(d, `${p}.pronostico[${j}]`);
      const dia: DiaPronostico = {
        fecha: r.fecha(q.fecha, `${p}.pronostico[${j}].fecha`),
        h: r.entero(q.h, `${p}.pronostico[${j}].h`, 1),
        punto: r.numero(q.punto, `${p}.pronostico[${j}].punto`),
        q: r.numeros(q.q, `${p}.pronostico[${j}].q`, cuantiles.length),
      };
      if (dia.h !== j + 1) r.falla(`${p}.pronostico[${j}].h`, `debe ser ${j + 1} (llegó ${dia.h})`);
      if (dia.punto < 0 || dia.q.some((v) => v < 0)) r.falla(`${p}.pronostico[${j}]`, "los pronósticos no pueden ser negativos");
      if (dia.q.some((v, k) => k > 0 && v < dia.q[k - 1])) r.falla(`${p}.pronostico[${j}].q`, "los cuantiles deben ser no decrecientes");
      return dia;
    });
    if (pronostico.length !== horizonte) {
      r.falla(`${p}.pronostico`, `debe tener ${horizonte} días (tiene ${pronostico.length})`);
    }
    return {
      ruta_id,
      origen: lugar(e.origen, `${p}.origen`),
      destino: lugar(e.destino, `${p}.destino`),
      ruta_regreso_id: r.texto(e.ruta_regreso_id, `${p}.ruta_regreso_id`),
      historia,
      pronostico,
    };
  });
  return { ...base, modelo: r.texto(o.modelo, "modelo"), fecha_origen: r.fecha(o.fecha_origen, "fecha_origen"), horizonte, cuantiles, rutas };
}

/** Control de la interfaz de operación: un número con rango y paso, o una opción entre valores fijos. */
export type ControlOperacion = ControlNumero | ControlOpciones;

interface ControlComun {
  /** Clave del parámetro que modifica (existe en `OperacionJson.parametros`). */
  clave: string;
  /** Etiqueta en español. */
  etiqueta: string;
  /** Unidad a mostrar junto al valor ("" si no tiene). */
  unidad: string;
  /** Texto de ayuda (globo «i»). */
  ayuda: string;
}

export interface ControlNumero extends ControlComun {
  tipo: "numero";
  minimo: number;
  maximo: number;
  paso: number;
  /** Valor inicial, dentro de [minimo, maximo]. */
  defecto: number;
}

export interface ControlOpciones extends ControlComun {
  tipo: "opciones";
  /** Valores permitidos (p. ej. los cuantiles de `Pronosticos.cuantiles`). */
  opciones: number[];
  /** Valor inicial, uno de `opciones`. */
  defecto: number;
}

export interface SalidaDimensionamiento {
  /** Despachos del día (entero >= 0). */
  despachos: number;
  /** Vehículos requeridos (entero >= 0). */
  vehiculos: number;
  /** Conductores requeridos (entero >= 0). */
  conductores: number;
}

export interface CasoOperacion {
  /** `demanda` (pasajeros del día) y los `parametros` con que se dimensionó. */
  entrada: { demanda: number; parametros: Record<string, number> };
  /** Lo que devolvió la función de Python con esa entrada. */
  salida: SalidaDimensionamiento;
}

/** `m1/operacion.json`. */
export interface OperacionJson extends Base {
  /** Nombre de la función de dimensionamiento (el juguete es `dimensionar_juguete`). */
  funcion: string;
  /** Valores por defecto de todos los parámetros de la función. */
  parametros: Record<string, number>;
  /** Controles que se muestran al usuario (subconjunto de `parametros`). */
  controles: ControlOperacion[];
  /** Casos entrada → salida generados con la función de Python (prueba de paridad TS vs. Python). */
  casos_paridad: CasoOperacion[];
}

export function validarOperacion(raiz: unknown, archivo = "m1/operacion.json"): OperacionJson {
  const r = new Lector(archivo);
  const base = r.base(raiz);
  const o = raiz as Obj;
  const registro = (x: unknown, ruta: string): Record<string, number> => {
    const e = r.objeto(x, ruta);
    return Object.fromEntries(Object.entries(e).map(([k, v]) => [k, r.numero(v, `${ruta}.${k}`)]));
  };
  const parametros = registro(o.parametros, "parametros");
  const controles = r.arreglo(o.controles, "controles", 1).map((x, i): ControlOperacion => {
    const p = `controles[${i}]`;
    const c = r.objeto(x, p);
    const clave = r.texto(c.clave, `${p}.clave`);
    if (!(clave in parametros)) r.falla(`${p}.clave`, `«${clave}» no está en parametros`);
    const comun = {
      clave,
      etiqueta: r.texto(c.etiqueta, `${p}.etiqueta`),
      unidad: typeof c.unidad === "string" ? c.unidad : r.falla(`${p}.unidad`, "debe ser un texto (puede ser vacío)"),
      ayuda: r.texto(c.ayuda, `${p}.ayuda`),
    };
    const defecto = r.numero(c.defecto, `${p}.defecto`);
    if (c.tipo === "numero") {
      const minimo = r.numero(c.minimo, `${p}.minimo`);
      const maximo = r.numero(c.maximo, `${p}.maximo`);
      const paso = r.numero(c.paso, `${p}.paso`);
      if (!(minimo < maximo)) r.falla(`${p}.minimo`, "debe ser menor que maximo");
      if (!(paso > 0)) r.falla(`${p}.paso`, "debe ser positivo");
      if (defecto < minimo || defecto > maximo) r.falla(`${p}.defecto`, "debe estar entre minimo y maximo");
      return { ...comun, tipo: "numero", minimo, maximo, paso, defecto };
    }
    if (c.tipo === "opciones") {
      const opciones = r.numeros(c.opciones, `${p}.opciones`);
      if (opciones.length === 0) r.falla(`${p}.opciones`, "debe tener al menos una opción");
      if (!opciones.includes(defecto)) r.falla(`${p}.defecto`, "debe ser una de las opciones");
      return { ...comun, tipo: "opciones", opciones, defecto };
    }
    return r.falla(`${p}.tipo`, 'debe ser "numero" u "opciones"');
  });
  const casos = r.arreglo(o.casos_paridad, "casos_paridad", 1).map((x, i): CasoOperacion => {
    const p = `casos_paridad[${i}]`;
    const c = r.objeto(x, p);
    const entrada = r.objeto(c.entrada, `${p}.entrada`);
    const salida = r.objeto(c.salida, `${p}.salida`);
    return {
      entrada: { demanda: r.numero(entrada.demanda, `${p}.entrada.demanda`), parametros: registro(entrada.parametros, `${p}.entrada.parametros`) },
      salida: {
        despachos: r.entero(salida.despachos, `${p}.salida.despachos`, 0),
        vehiculos: r.entero(salida.vehiculos, `${p}.salida.vehiculos`, 0),
        conductores: r.entero(salida.conductores, `${p}.salida.conductores`, 0),
      },
    };
  });
  return { ...base, funcion: r.texto(o.funcion, "funcion"), parametros, controles, casos_paridad: casos };
}

// ------------------------------------------------------------------------------------------------------- M2 §5.6

export type GrupoAlerta = "sin_alerta" | "con_alerta";

export interface ClaseM2 {
  /** Identificador estable de la clase (minúsculas y guiones bajos). */
  id: string;
  /** Nombre en español para mostrar. */
  nombre: string;
}

export interface EjemploM2 {
  id: string;
  /** Archivo de imagen dentro de `m2/ejemplos/`. */
  archivo: string;
  /** Texto corto para el selector. */
  descripcion: string;
}

export interface CasoParidadM2 {
  id: string;
  /** Imagen ya al `tamano_entrada`: RGB uint8 en orden alto, ancho, canal, aplanada (largo = alto·ancho·3). */
  entrada_rgb: number[];
  /** Logits de PyTorch (uno por clase, en el orden de `clases`). */
  logits: number[];
  /** Softmax de los logits (suma 1). */
  probabilidades: number[];
  /** Índice de la clase con mayor probabilidad. */
  clase_predicha: number;
  /** Forma de `mapas`: [canales, alto, ancho]. */
  forma_mapas: [number, number, number];
  /** Activaciones de la última capa convolucional (salida `mapas` del ONNX, sin el lote), aplanadas en orden C·H·W. */
  mapas: number[];
  /** CAM de la clase predicha: Σ_c pesos_cabeza[clase][c] · mapas[c] (sin sesgo), aplanado en orden H·W. */
  cam_clase_predicha: number[];
}

/** `m2/meta.json` (junto a `m2/modelo.onnx`). */
export interface MetaM2 extends Base {
  /** Nombre del modelo. */
  modelo: string;
  /** Archivo ONNX dentro de `m2/`. */
  archivo_modelo: string;
  /** Las clases, en el orden de las salidas del modelo. */
  clases: ClaseM2[];
  /** Grupo de alerta de cada clase (clave = `ClaseM2.id`). */
  grupo_alerta: Record<string, GrupoAlerta>;
  /** true mientras el agrupamiento sea una propuesta sin justificar (lo cierra José, JO-8). */
  grupo_alerta_provisional: boolean;
  /** Umbral inicial de la decisión: hay alerta si P(con alerta) = Σ prob. de las clases «con alerta» >= umbral. */
  umbral_por_defecto: number;
  /** Tamaño de la imagen que espera el modelo. */
  tamano_entrada: { alto: number; ancho: number };
  /** Media por canal RGB (sobre valores en [0, 1]) con que se normalizó el entrenamiento. */
  media: number[];
  /** Desviación estándar por canal RGB de esa normalización. */
  desviacion: number[];
  /** Nombre de la entrada del ONNX (tensor float32 [lote, 3, alto, ancho]). */
  entrada_onnx: string;
  /** Nombres de las salidas del ONNX: `logits` [lote, clases] y `mapas` [lote, canales, alto', ancho']. */
  salidas_onnx: { logits: string; mapas: string };
  /** Pesos de la capa lineal tras el GAP: matriz [clases][canales] (para CAM). */
  pesos_cabeza: number[][];
  /** Sesgo de esa capa (uno por clase). */
  sesgo_cabeza: number[];
  ejemplos: EjemploM2[];
  casos_paridad: CasoParidadM2[];
}

export function validarMetaM2(raiz: unknown, archivo = "m2/meta.json"): MetaM2 {
  const r = new Lector(archivo);
  const base = r.base(raiz);
  const o = raiz as Obj;
  const clases = r.arreglo(o.clases, "clases", 2).map((x, i): ClaseM2 => {
    const c = r.objeto(x, `clases[${i}]`);
    return { id: r.texto(c.id, `clases[${i}].id`), nombre: r.texto(c.nombre, `clases[${i}].nombre`) };
  });
  const ids = clases.map((c) => c.id);
  if (new Set(ids).size !== ids.length) r.falla("clases", "los id de las clases deben ser únicos");
  const n = clases.length;

  const ga = r.objeto(o.grupo_alerta, "grupo_alerta");
  const grupo_alerta: Record<string, GrupoAlerta> = {};
  for (const id of ids) {
    const g = ga[id];
    if (g !== "sin_alerta" && g !== "con_alerta") r.falla(`grupo_alerta.${id}`, 'debe ser "sin_alerta" o "con_alerta"');
    grupo_alerta[id] = g as GrupoAlerta;
  }
  for (const k of Object.keys(ga)) if (!ids.includes(k)) r.falla(`grupo_alerta.${k}`, "no es una clase de `clases`");
  const grupos = Object.values(grupo_alerta);
  if (!grupos.includes("sin_alerta") || !grupos.includes("con_alerta")) {
    r.falla("grupo_alerta", 'debe haber al menos una clase "sin_alerta" y una "con_alerta"');
  }

  const umbral = r.numero(o.umbral_por_defecto, "umbral_por_defecto");
  if (umbral < 0 || umbral > 1) r.falla("umbral_por_defecto", "debe estar entre 0 y 1");
  const t = r.objeto(o.tamano_entrada, "tamano_entrada");
  const alto = r.entero(t.alto, "tamano_entrada.alto", 1);
  const ancho = r.entero(t.ancho, "tamano_entrada.ancho", 1);
  const media = r.numeros(o.media, "media", 3);
  const desviacion = r.numeros(o.desviacion, "desviacion", 3);
  desviacion.forEach((d, i) => d > 0 || r.falla(`desviacion[${i}]`, "debe ser positiva"));
  const so = r.objeto(o.salidas_onnx, "salidas_onnx");
  const salidas_onnx = { logits: r.texto(so.logits, "salidas_onnx.logits"), mapas: r.texto(so.mapas, "salidas_onnx.mapas") };

  const pesos_cabeza = r.arreglo(o.pesos_cabeza, "pesos_cabeza", n).map((f, i) => r.numeros(f, `pesos_cabeza[${i}]`));
  if (pesos_cabeza.length !== n) r.falla("pesos_cabeza", `debe tener una fila por clase (${n})`);
  const canales = pesos_cabeza[0].length;
  if (canales < 1 || pesos_cabeza.some((f) => f.length !== canales)) r.falla("pesos_cabeza", "todas las filas deben tener los mismos canales");
  const sesgo_cabeza = r.numeros(o.sesgo_cabeza, "sesgo_cabeza", n);

  const ejemplos = r.arreglo(o.ejemplos, "ejemplos").map((x, i): EjemploM2 => {
    const e = r.objeto(x, `ejemplos[${i}]`);
    return { id: r.texto(e.id, `ejemplos[${i}].id`), archivo: r.texto(e.archivo, `ejemplos[${i}].archivo`), descripcion: r.texto(e.descripcion, `ejemplos[${i}].descripcion`) };
  });

  const casos = r.arreglo(o.casos_paridad, "casos_paridad", 1).map((x, i): CasoParidadM2 => {
    const p = `casos_paridad[${i}]`;
    const c = r.objeto(x, p);
    const entrada_rgb = r.numeros(c.entrada_rgb, `${p}.entrada_rgb`, alto * ancho * 3);
    entrada_rgb.forEach((v, j) => {
      if (!Number.isInteger(v) || v < 0 || v > 255) r.falla(`${p}.entrada_rgb[${j}]`, "debe ser un entero entre 0 y 255");
    });
    const probabilidades = r.numeros(c.probabilidades, `${p}.probabilidades`, n);
    if (Math.abs(probabilidades.reduce((a, b) => a + b, 0) - 1) > 1e-4) r.falla(`${p}.probabilidades`, "deben sumar 1");
    const clase_predicha = r.entero(c.clase_predicha, `${p}.clase_predicha`, 0);
    if (clase_predicha >= n) r.falla(`${p}.clase_predicha`, "fuera del rango de clases");
    const forma = r.numeros(c.forma_mapas, `${p}.forma_mapas`, 3);
    if (forma[0] !== canales) r.falla(`${p}.forma_mapas`, `los canales (${forma[0]}) deben coincidir con pesos_cabeza (${canales})`);
    return {
      id: r.texto(c.id, `${p}.id`),
      entrada_rgb,
      logits: r.numeros(c.logits, `${p}.logits`, n),
      probabilidades,
      clase_predicha,
      forma_mapas: forma as [number, number, number],
      mapas: r.numeros(c.mapas, `${p}.mapas`, forma[0] * forma[1] * forma[2]),
      cam_clase_predicha: r.numeros(c.cam_clase_predicha, `${p}.cam_clase_predicha`, forma[1] * forma[2]),
    };
  });

  return {
    ...base,
    modelo: r.texto(o.modelo, "modelo"),
    archivo_modelo: r.texto(o.archivo_modelo, "archivo_modelo"),
    clases,
    grupo_alerta,
    grupo_alerta_provisional: r.booleano(o.grupo_alerta_provisional, "grupo_alerta_provisional"),
    umbral_por_defecto: umbral,
    tamano_entrada: { alto, ancho },
    media,
    desviacion,
    entrada_onnx: r.texto(o.entrada_onnx, "entrada_onnx"),
    salidas_onnx,
    pesos_cabeza,
    sesgo_cabeza,
    ejemplos,
    casos_paridad: casos,
  };
}

// ------------------------------------------------------------------------------------------------------- M3 §5.8

export interface DestinoM3 {
  /** Identificador estable del destino. */
  id: string;
  /** Nombre para mostrar (en el juguete lleva «(ficticio)»). */
  nombre: string;
  /** Afinidad del destino con cada preferencia (clave = `PreferenciaM3.id`), entre 0 y 1. */
  atributos: Record<string, number>;
  /** Popularidad entre 0 y 1. */
  popularidad: number;
  /** Coordenadas 2D para la figura de destinos. */
  embedding_2d: [number, number];
}

/** `m3/destinos.json`. */
export interface DestinosJson extends Base {
  destinos: DestinoM3[];
}

export interface RecomendacionM3 {
  destino_id: string;
  /** Puntaje del recomendador (mayor = más recomendado); el top-K viene ordenado de mayor a menor. */
  puntaje: number;
}

export interface UsuarioM3 {
  id: string;
  /** Nombre para mostrar (en el juguete, «Usuario ficticio NN»: nunca personas reales). */
  nombre: string;
  /** Destinos que el usuario calificó (1 a 5). */
  historial: { destino_id: string; calificacion: number }[];
  /** Top-K precomputado (K = `k_max`), sin destinos del historial, de mayor a menor puntaje. */
  top_k: RecomendacionM3[];
}

/** `m3/usuarios.json`. */
export interface UsuariosJson extends Base {
  /** K del top-K precomputado; la app muestra los primeros K <= k_max. */
  k_max: number;
  usuarios: UsuarioM3[];
}

export interface PreferenciaM3 {
  /** Identificador estable; coincide con una clave de `DestinoM3.atributos`. */
  id: string;
  /** Etiqueta en español para la lista seleccionable. */
  etiqueta: string;
  descripcion: string;
}

export interface CasoPerfilM3 {
  /** Preferencias elegidas (ids). */
  preferencias: string[];
  k: number;
  /** Top-K que devolvió Python con esa entrada. */
  top_k: RecomendacionM3[];
}

/** `m3/perfil_nuevo.json`. */
export interface PerfilNuevoJson extends Base {
  /** Lista de preferencias seleccionables. */
  preferencias: PreferenciaM3[];
  /** Regla con que se recomienda a un perfil nuevo. El juguete usa `afinidad_media_juguete`. */
  regla: { tipo: string; peso_popularidad: number; descripcion: string };
  /** K inicial del control. */
  k_defecto: number;
  /** K máximo del control. */
  k_max: number;
  /** Casos preferencias → top-K generados con Python (prueba de paridad). */
  casos_paridad: CasoPerfilM3[];
}

export function validarDestinos(raiz: unknown, archivo = "m3/destinos.json"): DestinosJson {
  const r = new Lector(archivo);
  const base = r.base(raiz);
  const ids = new Set<string>();
  const destinos = r.arreglo((raiz as Obj).destinos, "destinos", 1).map((x, i): DestinoM3 => {
    const p = `destinos[${i}]`;
    const d = r.objeto(x, p);
    const id = r.texto(d.id, `${p}.id`);
    if (ids.has(id)) r.falla(`${p}.id`, `destino repetido: ${id}`);
    ids.add(id);
    const a = r.objeto(d.atributos, `${p}.atributos`);
    const atributos = Object.fromEntries(
      Object.entries(a).map(([k, v]) => {
        const n = r.numero(v, `${p}.atributos.${k}`);
        if (n < 0 || n > 1) r.falla(`${p}.atributos.${k}`, "debe estar entre 0 y 1");
        return [k, n];
      }),
    );
    const popularidad = r.numero(d.popularidad, `${p}.popularidad`);
    if (popularidad < 0 || popularidad > 1) r.falla(`${p}.popularidad`, "debe estar entre 0 y 1");
    const e = r.numeros(d.embedding_2d, `${p}.embedding_2d`, 2);
    return { id, nombre: r.texto(d.nombre, `${p}.nombre`), atributos, popularidad, embedding_2d: [e[0], e[1]] };
  });
  return { ...base, destinos };
}

function validarTopK(r: Lector, x: unknown, ruta: string): RecomendacionM3[] {
  const top = r.arreglo(x, ruta).map((f, i): RecomendacionM3 => {
    const e = r.objeto(f, `${ruta}[${i}]`);
    return { destino_id: r.texto(e.destino_id, `${ruta}[${i}].destino_id`), puntaje: r.numero(e.puntaje, `${ruta}[${i}].puntaje`) };
  });
  top.forEach((f, i) => {
    if (i > 0 && f.puntaje > top[i - 1].puntaje) r.falla(`${ruta}[${i}].puntaje`, "el top-K debe venir de mayor a menor puntaje");
  });
  return top;
}

export function validarUsuarios(raiz: unknown, archivo = "m3/usuarios.json"): UsuariosJson {
  const r = new Lector(archivo);
  const base = r.base(raiz);
  const o = raiz as Obj;
  const k_max = r.entero(o.k_max, "k_max", 1);
  const ids = new Set<string>();
  const usuarios = r.arreglo(o.usuarios, "usuarios", 1).map((x, i): UsuarioM3 => {
    const p = `usuarios[${i}]`;
    const u = r.objeto(x, p);
    const id = r.texto(u.id, `${p}.id`);
    if (ids.has(id)) r.falla(`${p}.id`, `usuario repetido: ${id}`);
    ids.add(id);
    const historial = r.arreglo(u.historial, `${p}.historial`).map((h, j) => {
      const e = r.objeto(h, `${p}.historial[${j}]`);
      const calificacion = r.entero(e.calificacion, `${p}.historial[${j}].calificacion`, 1);
      if (calificacion > 5) r.falla(`${p}.historial[${j}].calificacion`, "debe estar entre 1 y 5");
      return { destino_id: r.texto(e.destino_id, `${p}.historial[${j}].destino_id`), calificacion };
    });
    const top_k = validarTopK(r, u.top_k, `${p}.top_k`);
    if (top_k.length < k_max) r.falla(`${p}.top_k`, `debe tener al menos k_max (${k_max}) recomendaciones`);
    const vistos = new Set(historial.map((h) => h.destino_id));
    top_k.forEach((f, j) => vistos.has(f.destino_id) && r.falla(`${p}.top_k[${j}]`, "recomienda un destino que ya está en el historial"));
    return { id, nombre: r.texto(u.nombre, `${p}.nombre`), historial, top_k };
  });
  return { ...base, k_max, usuarios };
}

export function validarPerfilNuevo(raiz: unknown, archivo = "m3/perfil_nuevo.json"): PerfilNuevoJson {
  const r = new Lector(archivo);
  const base = r.base(raiz);
  const o = raiz as Obj;
  const ids = new Set<string>();
  const preferencias = r.arreglo(o.preferencias, "preferencias", 1).map((x, i): PreferenciaM3 => {
    const p = r.objeto(x, `preferencias[${i}]`);
    const id = r.texto(p.id, `preferencias[${i}].id`);
    if (ids.has(id)) r.falla(`preferencias[${i}].id`, `preferencia repetida: ${id}`);
    ids.add(id);
    return { id, etiqueta: r.texto(p.etiqueta, `preferencias[${i}].etiqueta`), descripcion: r.texto(p.descripcion, `preferencias[${i}].descripcion`) };
  });
  const g = r.objeto(o.regla, "regla");
  const regla = {
    tipo: r.texto(g.tipo, "regla.tipo"),
    peso_popularidad: r.numero(g.peso_popularidad, "regla.peso_popularidad"),
    descripcion: r.texto(g.descripcion, "regla.descripcion"),
  };
  const k_defecto = r.entero(o.k_defecto, "k_defecto", 1);
  const k_max = r.entero(o.k_max, "k_max", 1);
  if (k_defecto > k_max) r.falla("k_defecto", "no puede superar k_max");
  const casos = r.arreglo(o.casos_paridad, "casos_paridad", 1).map((x, i): CasoPerfilM3 => {
    const p = `casos_paridad[${i}]`;
    const c = r.objeto(x, p);
    const prefs = r.textos(c.preferencias, `${p}.preferencias`);
    if (prefs.length === 0) r.falla(`${p}.preferencias`, "debe tener al menos una preferencia");
    prefs.forEach((id, j) => ids.has(id) || r.falla(`${p}.preferencias[${j}]`, `«${id}» no está en preferencias`));
    const k = r.entero(c.k, `${p}.k`, 1);
    const top_k = validarTopK(r, c.top_k, `${p}.top_k`);
    if (top_k.length !== k) r.falla(`${p}.top_k`, `debe tener k (${k}) elementos`);
    return { preferencias: prefs, k, top_k };
  });
  return { ...base, preferencias, regla, k_defecto, k_max, casos_paridad: casos };
}

/** Coherencia entre los tres archivos de M3: todo id referenciado existe y todo destino tiene todas las preferencias. */
export function validarCoherenciaM3(d: DestinosJson, u: UsuariosJson, p: PerfilNuevoJson): void {
  const ids = new Set(d.destinos.map((x) => x.id));
  const falla = (ruta: string, problema: string): never => {
    throw new ErrorContrato("m3", ruta, problema);
  };
  d.destinos.forEach((x, i) =>
    p.preferencias.forEach((pref) => {
      if (!(pref.id in x.atributos)) falla(`destinos[${i}].atributos`, `falta el atributo de la preferencia «${pref.id}»`);
    }),
  );
  u.usuarios.forEach((x, i) => {
    x.historial.forEach((h, j) => ids.has(h.destino_id) || falla(`usuarios[${i}].historial[${j}]`, `destino inexistente: ${h.destino_id}`));
    x.top_k.forEach((f, j) => ids.has(f.destino_id) || falla(`usuarios[${i}].top_k[${j}]`, `destino inexistente: ${f.destino_id}`));
  });
  if (p.k_max > d.destinos.length) falla("perfil_nuevo.k_max", "es mayor que el número de destinos");
}

/** Coherencia entre los dos archivos de M1: el cuantil por defecto y las opciones de cuantil existen en el pronóstico. */
export function validarCoherenciaM1(p: Pronosticos, o: OperacionJson): void {
  for (const c of o.controles) {
    if (c.clave !== "cuantil") continue;
    const validos = c.tipo === "opciones" ? c.opciones : [c.defecto];
    for (const q of validos) {
      if (!p.cuantiles.includes(q)) throw new ErrorContrato("m1/operacion.json", "controles.cuantil", `el cuantil ${q} no está en m1/pronosticos.json (cuantiles)`);
    }
  }
}
