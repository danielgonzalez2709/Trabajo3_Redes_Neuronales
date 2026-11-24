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

  /** Clave de un parámetro, clase o preferencia: sin puntos (las referencias `grupo.clase.clave` usan el punto de separador). */
  clave(k: string, ruta: string): string {
    if (k.length === 0 || k.includes(".")) this.falla(ruta, `la clave «${k}» no puede estar vacía ni llevar puntos`);
    return k;
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

/** Propiedad propia (no heredada) de un objeto. */
const tiene = (o: object | undefined, k: string): boolean => o !== undefined && Object.hasOwn(o, k);

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
  /** `ruta_id` del sentido contrario; existe entre las rutas del archivo. */
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
  const fechaOrigen = r.fecha(o.fecha_origen, "fecha_origen");
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
    if (historia[historia.length - 1].fecha !== fechaOrigen) {
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
  rutas.forEach((e, i) => {
    if (!ids.has(e.ruta_regreso_id)) r.falla(`rutas[${i}].ruta_regreso_id`, `«${e.ruta_regreso_id}» no está entre las rutas del archivo`);
  });
  return { ...base, modelo: r.texto(o.modelo, "modelo"), fecha_origen: fechaOrigen, horizonte, cuantiles, rutas };
}

/**
 * Un parámetro del modelo de operación. Lleva la `fuente` (la cita textual de la norma o dato de donde sale, que la
 * interfaz muestra junto al parámetro) **o** `supuesto: true` si es un supuesto sin fuente (nunca las dos cosas ni ninguna).
 */
export interface Parametro {
  valor: number;
  /** Unidad para mostrar ("" si no tiene). */
  unidad: string;
  /** Cita textual de la fuente primaria. Excluyente con `supuesto`. */
  fuente?: string;
  /** `true` si es un supuesto sin fuente. Excluyente con `fuente`. */
  supuesto?: true;
  /** Aclaración opcional (alcance, cómo se estimó, advertencia). */
  nota?: string;
}

/**
 * Parámetros de la función de dimensionamiento, agrupados. Se señalan con **referencias** (`ref`) de punto:
 * - `globales.<clave>`: igual para todas las rutas (p. ej. `globales.ocupacion_objetivo`);
 * - `por_ruta.<clave>`: el de la ruta elegida (p. ej. `por_ruta.tiempo_ciclo_h`);
 * - `por_clase.<clase>.<clave>`: el de una clase de vehículo (p. ej. `por_clase.bus.capacidad_pasajeros`);
 * - `composicion_clases.<clase>`: participación de esa clase en los despachos de la ruta elegida (suma 1 por ruta;
 *   la real se estima solo con train, núcleo §5.4).
 * Las claves y las clases no llevan puntos. Los parámetros efectivos que recibe la función son `{ref: valor}`.
 */
export interface ParametrosOperacion {
  globales: Record<string, Parametro>;
  /** `ruta_id` → parámetros de esa ruta (todas las rutas con las mismas claves). */
  por_ruta: Record<string, Record<string, Parametro>>;
  /** clase de vehículo → parámetros de esa clase. */
  por_clase: Record<string, Record<string, Parametro>>;
  /** `ruta_id` → clase de vehículo → participación (en [0, 1]; suma 1). */
  composicion_clases: Record<string, Record<string, Parametro>>;
}

/** Referencias que todo `operacion.json` debe tener como parámetro y como control (el Anexo pide «al menos dos parámetros»). */
export const REFS_OBLIGATORIAS = ["globales.ocupacion_objetivo", "globales.cuantil"] as const;

/** Busca el parámetro de una referencia para la ruta dada (o `undefined`). Solo propiedades propias. */
export function resolverParametro(p: ParametrosOperacion, ref: string, rutaId: string): Parametro | undefined {
  const [grupo, a, b, ...sobra] = ref.split(".");
  if (sobra.length > 0 || a === undefined) return undefined;
  const de = (reg: Record<string, Parametro> | undefined, k: string | undefined): Parametro | undefined =>
    reg !== undefined && k !== undefined && Object.hasOwn(reg, k) ? reg[k] : undefined;
  const ruta = (reg: Record<string, Record<string, Parametro>>, k: string): Record<string, Parametro> | undefined =>
    Object.hasOwn(reg, k) ? reg[k] : undefined;
  switch (grupo) {
    case "globales":
      return b === undefined ? de(p.globales, a) : undefined;
    case "por_ruta":
      return b === undefined ? de(ruta(p.por_ruta, rutaId), a) : undefined;
    case "por_clase":
      return b === undefined ? undefined : de(ruta(p.por_clase, a), b);
    case "composicion_clases":
      return b === undefined ? de(ruta(p.composicion_clases, rutaId), a) : undefined;
    default:
      return undefined;
  }
}

/** Control de la interfaz de operación: un número con rango y paso, o una opción entre valores fijos. */
export type ControlOperacion = ControlNumero | ControlOpciones;

interface ControlComun {
  /** Parámetro que modifica (ver `ParametrosOperacion`); su valor inicial y su unidad salen del parámetro. */
  ref: string;
  /** Etiqueta en español. */
  etiqueta: string;
  /** Texto de ayuda (globo «i»); la interfaz le agrega la fuente o la marca de supuesto del parámetro. */
  ayuda: string;
}

export interface ControlNumero extends ControlComun {
  tipo: "numero";
  minimo: number;
  maximo: number;
  paso: number;
}

export interface ControlOpciones extends ControlComun {
  tipo: "opciones";
  /** Valores permitidos (p. ej. los cuantiles de `Pronosticos.cuantiles`). */
  opciones: number[];
}

export interface SalidaDimensionamiento {
  /** Despachos del día (entero >= 0). */
  despachos: number;
  /** Vehículos requeridos (entero >= 0). */
  vehiculos: number;
  /** Conductores requeridos (entero >= 0). */
  conductores: number;
  /** Pasos intermedios que la función exponga, `{nombre: valor}` (para depurar en vivo); opcional. */
  pasos?: Record<string, number>;
}

export interface CasoOperacion {
  /** Ruta, día, demanda (pasajeros del día) y los parámetros efectivos `{ref: valor}` con que se dimensionó. */
  entrada: { ruta_id: string; fecha: string; demanda: number; parametros: Record<string, number> };
  /** Lo que devolvió la función de Python con esa entrada. */
  salida: SalidaDimensionamiento;
}

/** `m1/operacion.json`. */
export interface OperacionJson extends Base {
  /** Nombre de la función de dimensionamiento (el juguete es `dimensionar_juguete`). */
  funcion: string;
  /** Valores por defecto de todos los parámetros de la función, con su fuente o su marca de supuesto. */
  parametros: ParametrosOperacion;
  /** Controles que se muestran al usuario; deben incluir `REFS_OBLIGATORIAS`. */
  controles: ControlOperacion[];
  /** Casos entrada → salida generados con la función de Python (prueba de paridad TS vs. Python). */
  casos_paridad: CasoOperacion[];
}

export function validarOperacion(raiz: unknown, archivo = "m1/operacion.json"): OperacionJson {
  const r = new Lector(archivo);
  const base = r.base(raiz);
  const o = raiz as Obj;

  const parametro = (x: unknown, ruta: string): Parametro => {
    const e = r.objeto(x, ruta);
    const fuente = r.textoOpcional(e.fuente, `${ruta}.fuente`);
    if (e.supuesto !== undefined && e.supuesto !== true) r.falla(`${ruta}.supuesto`, "debe ser true (o no estar)");
    if (fuente === undefined && e.supuesto !== true) r.falla(ruta, "debe traer `fuente` (la cita textual) o `supuesto: true`");
    if (fuente !== undefined && e.supuesto === true) r.falla(ruta, "no puede traer `fuente` y `supuesto: true` a la vez");
    return {
      valor: r.numero(e.valor, `${ruta}.valor`),
      unidad: typeof e.unidad === "string" ? e.unidad : r.falla(`${ruta}.unidad`, "debe ser un texto (puede ser vacío)"),
      ...(fuente !== undefined ? { fuente } : { supuesto: true as const }),
      ...(e.nota !== undefined ? { nota: r.texto(e.nota, `${ruta}.nota`) } : {}),
    };
  };
  const registro = (x: unknown, ruta: string): Record<string, Parametro> =>
    Object.fromEntries(Object.entries(r.objeto(x, ruta)).map(([k, v]) => [r.clave(k, `${ruta}.${k}`), parametro(v, `${ruta}.${k}`)]));
  const anidado = (x: unknown, ruta: string, clavesInternasSinPunto: boolean): Record<string, Record<string, Parametro>> =>
    Object.fromEntries(
      Object.entries(r.objeto(x, ruta)).map(([k, v]) => [clavesInternasSinPunto ? r.clave(k, `${ruta}.${k}`) : k, registro(v, `${ruta}.${k}`)]),
    );

  const pr = r.objeto(o.parametros, "parametros");
  const parametros: ParametrosOperacion = {
    globales: registro(pr.globales, "parametros.globales"),
    por_ruta: anidado(pr.por_ruta, "parametros.por_ruta", false),
    por_clase: anidado(pr.por_clase, "parametros.por_clase", true),
    composicion_clases: anidado(pr.composicion_clases, "parametros.composicion_clases", false),
  };
  const rutas = Object.keys(parametros.composicion_clases);
  if (rutas.length === 0) r.falla("parametros.composicion_clases", "debe tener al menos una ruta");
  const clases = Object.keys(parametros.por_clase);
  if (clases.length === 0) r.falla("parametros.por_clase", "debe tener al menos una clase de vehículo");
  const mismasClaves = (a: string[], b: string[]) => a.length === b.length && a.every((k) => b.includes(k));
  const clavesRuta = rutas.length > 0 ? Object.keys(parametros.por_ruta[rutas[0]] ?? {}) : [];
  for (const ruta of rutas) {
    if (!tiene(parametros.por_ruta, ruta)) r.falla(`parametros.por_ruta.${ruta}`, "falta la ruta (aunque sea con un objeto vacío)");
    if (!mismasClaves(Object.keys(parametros.por_ruta[ruta]), clavesRuta)) {
      r.falla(`parametros.por_ruta.${ruta}`, "todas las rutas deben tener los mismos parámetros");
    }
    const comp = parametros.composicion_clases[ruta];
    if (!mismasClaves(Object.keys(comp), clases)) r.falla(`parametros.composicion_clases.${ruta}`, "debe tener exactamente las clases de por_clase");
    let suma = 0;
    for (const [clase, par] of Object.entries(comp)) {
      if (par.valor < 0 || par.valor > 1) r.falla(`parametros.composicion_clases.${ruta}.${clase}.valor`, "debe estar entre 0 y 1");
      suma += par.valor;
    }
    if (Math.abs(suma - 1) > 1e-6) r.falla(`parametros.composicion_clases.${ruta}`, `las participaciones deben sumar 1 (suman ${suma})`);
  }
  for (const ruta of Object.keys(parametros.por_ruta)) {
    if (!tiene(parametros.composicion_clases, ruta)) r.falla(`parametros.por_ruta.${ruta}`, "ruta sin composicion_clases");
  }

  for (const ref of REFS_OBLIGATORIAS) {
    if (resolverParametro(parametros, ref, rutas[0]) === undefined) r.falla("parametros", `falta el parámetro obligatorio «${ref}»`);
  }

  const refs = new Set<string>();
  const controles = r.arreglo(o.controles, "controles", 1).map((x, i): ControlOperacion => {
    const p = `controles[${i}]`;
    const c = r.objeto(x, p);
    const ref = r.texto(c.ref, `${p}.ref`);
    if (refs.has(ref)) r.falla(`${p}.ref`, `control repetido: ${ref}`);
    refs.add(ref);
    // La referencia debe existir para todas las rutas (las de por_ruta y composicion_clases cambian con la ruta elegida).
    const valores = rutas.map((ruta) => {
      const par = resolverParametro(parametros, ref, ruta);
      return par === undefined ? r.falla(`${p}.ref`, `«${ref}» no es un parámetro de la ruta ${ruta}`) : par.valor;
    });
    const comun = { ref, etiqueta: r.texto(c.etiqueta, `${p}.etiqueta`), ayuda: r.texto(c.ayuda, `${p}.ayuda`) };
    if (c.tipo === "numero") {
      const minimo = r.numero(c.minimo, `${p}.minimo`);
      const maximo = r.numero(c.maximo, `${p}.maximo`);
      const paso = r.numero(c.paso, `${p}.paso`);
      if (!(minimo < maximo)) r.falla(`${p}.minimo`, "debe ser menor que maximo");
      if (!(paso > 0)) r.falla(`${p}.paso`, "debe ser positivo");
      if (valores.some((v) => v < minimo || v > maximo)) r.falla(`${p}.minimo`, "el valor del parámetro debe estar entre minimo y maximo");
      return { ...comun, tipo: "numero", minimo, maximo, paso };
    }
    if (c.tipo === "opciones") {
      const opciones = r.numeros(c.opciones, `${p}.opciones`);
      if (opciones.length === 0) r.falla(`${p}.opciones`, "debe tener al menos una opción");
      if (valores.some((v) => !opciones.includes(v))) r.falla(`${p}.opciones`, "el valor del parámetro debe ser una de las opciones");
      return { ...comun, tipo: "opciones", opciones };
    }
    return r.falla(`${p}.tipo`, 'debe ser "numero" u "opciones"');
  });
  for (const ref of REFS_OBLIGATORIAS) {
    if (!refs.has(ref)) r.falla("controles", `falta el control obligatorio de «${ref}»`);
  }

  const casos = r.arreglo(o.casos_paridad, "casos_paridad", 1).map((x, i): CasoOperacion => {
    const p = `casos_paridad[${i}]`;
    const c = r.objeto(x, p);
    const entrada = r.objeto(c.entrada, `${p}.entrada`);
    const salida = r.objeto(c.salida, `${p}.salida`);
    const demanda = r.numero(entrada.demanda, `${p}.entrada.demanda`);
    if (demanda < 0) r.falla(`${p}.entrada.demanda`, "no puede ser negativa");
    const ruta_id = r.texto(entrada.ruta_id, `${p}.entrada.ruta_id`);
    if (!rutas.includes(ruta_id)) r.falla(`${p}.entrada.ruta_id`, `«${ruta_id}» no está en composicion_clases`);
    const parEntrada = r.objeto(entrada.parametros, `${p}.entrada.parametros`);
    const pasos = salida.pasos === undefined ? undefined : r.objeto(salida.pasos, `${p}.salida.pasos`);
    return {
      entrada: {
        ruta_id,
        fecha: r.fecha(entrada.fecha, `${p}.entrada.fecha`),
        demanda,
        parametros: Object.fromEntries(Object.entries(parEntrada).map(([k, v]) => [k, r.numero(v, `${p}.entrada.parametros.${k}`)])),
      },
      salida: {
        despachos: r.entero(salida.despachos, `${p}.salida.despachos`, 0),
        vehiculos: r.entero(salida.vehiculos, `${p}.salida.vehiculos`, 0),
        conductores: r.entero(salida.conductores, `${p}.salida.conductores`, 0),
        ...(pasos ? { pasos: Object.fromEntries(Object.entries(pasos).map(([k, v]) => [k, r.numero(v, `${p}.salida.pasos.${k}`)])) } : {}),
      },
    };
  });
  return { ...base, funcion: r.texto(o.funcion, "funcion"), parametros, controles, casos_paridad: casos };
}

/**
 * Coherencia entre los dos archivos de M1: el cuantil por defecto y las opciones de cuantil existen en el pronóstico, y
 * todas las rutas del pronóstico tienen parámetros por ruta y composición por clase.
 */
export function validarCoherenciaM1(p: Pronosticos, o: OperacionJson): void {
  const falla = (ruta: string, problema: string): never => {
    throw new ErrorContrato("m1/operacion.json", ruta, problema);
  };
  const cuantil = o.parametros.globales.cuantil;
  if (!p.cuantiles.includes(cuantil.valor)) falla("parametros.globales.cuantil", `el cuantil ${cuantil.valor} no está en m1/pronosticos.json (cuantiles)`);
  for (const c of o.controles) {
    if (c.ref !== "globales.cuantil" || c.tipo !== "opciones") continue;
    for (const q of c.opciones) {
      if (!p.cuantiles.includes(q)) falla("controles.globales.cuantil", `el cuantil ${q} no está en m1/pronosticos.json (cuantiles)`);
    }
  }
  for (const r of p.rutas) {
    if (!tiene(o.parametros.composicion_clases, r.ruta_id)) falla("parametros.composicion_clases", `falta la ruta ${r.ruta_id} del pronóstico`);
    if (!tiene(o.parametros.por_ruta, r.ruta_id)) falla("parametros.por_ruta", `falta la ruta ${r.ruta_id} del pronóstico`);
  }
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

/**
 * Cómo se pasa una imagen cualquiera al tensor de entrada. Los valores admitidos son los únicos que la app sabe hacer; el
 * generador de Python (PIL) y `app/lib/imagen.ts` + `app/lib/clasificar.ts` deben hacer lo mismo:
 * 1. `redimensionado: "estirar"`: se estira al `tamano_entrada` sin conservar la proporción ni recortar;
 * 2. `interpolacion: "bilineal"`: filtro triangular (la ventana se ensancha al reducir, como `PIL.Image.BILINEAR`);
 * 3. `canales: "RGB"` (la transparencia se ignora); 4. `escala: "0-1"` (v / 255);
 * 5. `normalizacion: "media_desviacion"`: (v − media[c]) / desviacion[c] con `media` y `desviacion` del meta.
 */
export interface PreprocesadoM2 {
  redimensionado: "estirar";
  interpolacion: "bilineal";
  canales: "RGB";
  escala: "0-1";
  normalizacion: "media_desviacion";
}

/**
 * Un caso de paridad. La entrada es **o** `entrada_rgb` (en el propio meta) **o** `entrada_archivo` (un JSON aparte
 * `{"entrada_rgb": [...]}` bajo `m2/`, p. ej. `casos/caso_2.json`, para las imágenes grandes del modelo real). Si el caso trae
 * `imagen` (un archivo de `ejemplos/`), `entrada_rgb` es lo que salió de redimensionar ese archivo con el preprocesado
 * de Python y la app lo reproduce desde el archivo, con tolerancia (el redimensionado del navegador y el de PIL pueden diferir
 * en ±1 nivel por píxel; ver `app/tests/paridad_onnx.test.ts`).
 */
export interface CasoParidadM2 {
  id: string;
  /** Imagen ya al `tamano_entrada`: RGB uint8 en orden alto, ancho, canal, aplanada (largo = alto·ancho·3). */
  entrada_rgb?: number[];
  /** Ruta (bajo `m2/`) de un JSON con `entrada_rgb`, si es grande. */
  entrada_archivo?: string;
  /** Archivo de `ejemplos/` del que salió la entrada (caso «desde un archivo de imagen»). */
  imagen?: string;
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

/** Máximo de casos de paridad en `meta.json` (los grandes van en archivos aparte). */
export const MAX_CASOS_M2 = 3;

/**
 * `m2/meta.json` (junto a `m2/modelo.onnx`).
 *
 * El mapa de interpretabilidad del contrato es **CAM** (Σ_c w_c · mapa_c, sin sesgo, con los `pesos_cabeza` de la capa lineal
 * tras el GAP), que es lo que calcula la app. DA-7 demuestra que, para esta arquitectura (última convolución → GAP → lineal),
 * coincide con Grad-CAM de PyTorch salvo un factor constante por la clase; entonces los mapas son los mismos.
 */
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
  /** Cómo se pasa una imagen al tensor de entrada (ver `PreprocesadoM2`). */
  preprocesado: PreprocesadoM2;
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
  /** A lo sumo `MAX_CASOS_M2`. */
  casos_paridad: CasoParidadM2[];
}

/** Valida un archivo `m2/casos/<id>.json`: `{"entrada_rgb": [...]}` con alto·ancho·3 enteros entre 0 y 255. */
export function validarEntradaCaso(raiz: unknown, tamano: { alto: number; ancho: number }, archivo: string): number[] {
  const r = new Lector(archivo);
  return rgbValido(r, r.objeto(raiz, "$").entrada_rgb, "entrada_rgb", tamano.alto * tamano.ancho * 3);
}

function rgbValido(r: Lector, x: unknown, ruta: string, largo: number): number[] {
  const rgb = r.numeros(x, ruta, largo);
  rgb.forEach((v, j) => {
    if (!Number.isInteger(v) || v < 0 || v > 255) r.falla(`${ruta}[${j}]`, "debe ser un entero entre 0 y 255");
  });
  return rgb;
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
  for (const k of Object.keys(ga)) {
    if (!ids.includes(k)) r.falla(`grupo_alerta.${k}`, "no es una clase de `clases`");
  }
  const grupos = Object.values(grupo_alerta);
  if (!grupos.includes("sin_alerta") || !grupos.includes("con_alerta")) {
    r.falla("grupo_alerta", 'debe haber al menos una clase "sin_alerta" y una "con_alerta"');
  }

  const umbral = r.numero(o.umbral_por_defecto, "umbral_por_defecto");
  if (umbral < 0 || umbral > 1) r.falla("umbral_por_defecto", "debe estar entre 0 y 1");
  const t = r.objeto(o.tamano_entrada, "tamano_entrada");
  const alto = r.entero(t.alto, "tamano_entrada.alto", 1);
  const ancho = r.entero(t.ancho, "tamano_entrada.ancho", 1);
  const pp = r.objeto(o.preprocesado, "preprocesado");
  const exacto = <V extends string>(x: unknown, ruta: string, esperado: V): V => {
    if (x !== esperado) r.falla(ruta, `solo se admite «${esperado}» (llegó ${JSON.stringify(x)})`);
    return esperado;
  };
  const preprocesado: PreprocesadoM2 = {
    redimensionado: exacto(pp.redimensionado, "preprocesado.redimensionado", "estirar"),
    interpolacion: exacto(pp.interpolacion, "preprocesado.interpolacion", "bilineal"),
    canales: exacto(pp.canales, "preprocesado.canales", "RGB"),
    escala: exacto(pp.escala, "preprocesado.escala", "0-1"),
    normalizacion: exacto(pp.normalizacion, "preprocesado.normalizacion", "media_desviacion"),
  };
  const media = r.numeros(o.media, "media", 3);
  const desviacion = r.numeros(o.desviacion, "desviacion", 3);
  desviacion.forEach((d, i) => {
    if (!(d > 0)) r.falla(`desviacion[${i}]`, "debe ser positiva");
  });
  const so = r.objeto(o.salidas_onnx, "salidas_onnx");
  const salidas_onnx = { logits: r.texto(so.logits, "salidas_onnx.logits"), mapas: r.texto(so.mapas, "salidas_onnx.mapas") };

  const pesos_cabeza = r.arreglo(o.pesos_cabeza, "pesos_cabeza").map((f, i) => r.numeros(f, `pesos_cabeza[${i}]`));
  if (pesos_cabeza.length !== n) r.falla("pesos_cabeza", `debe tener una fila por clase (${n})`);
  const canales = pesos_cabeza[0].length;
  if (canales < 1 || pesos_cabeza.some((f) => f.length !== canales)) r.falla("pesos_cabeza", "todas las filas deben tener los mismos canales");
  const sesgo_cabeza = r.numeros(o.sesgo_cabeza, "sesgo_cabeza", n);

  const ejemplos = r.arreglo(o.ejemplos, "ejemplos").map((x, i): EjemploM2 => {
    const e = r.objeto(x, `ejemplos[${i}]`);
    return { id: r.texto(e.id, `ejemplos[${i}].id`), archivo: r.texto(e.archivo, `ejemplos[${i}].archivo`), descripcion: r.texto(e.descripcion, `ejemplos[${i}].descripcion`) };
  });

  const crudos = r.arreglo(o.casos_paridad, "casos_paridad", 1);
  if (crudos.length > MAX_CASOS_M2) r.falla("casos_paridad", `debe tener a lo sumo ${MAX_CASOS_M2} casos (tiene ${crudos.length}); las imágenes grandes van en archivos aparte`);
  const casos = crudos.map((x, i): CasoParidadM2 => {
    const p = `casos_paridad[${i}]`;
    const c = r.objeto(x, p);
    if ((c.entrada_rgb === undefined) === (c.entrada_archivo === undefined)) r.falla(p, "debe traer `entrada_rgb` o `entrada_archivo` (una de las dos)");
    const entrada_rgb = c.entrada_rgb === undefined ? undefined : rgbValido(r, c.entrada_rgb, `${p}.entrada_rgb`, alto * ancho * 3);
    let entrada_archivo: string | undefined;
    if (c.entrada_archivo !== undefined) {
      entrada_archivo = r.texto(c.entrada_archivo, `${p}.entrada_archivo`);
      if (entrada_archivo.startsWith("/") || entrada_archivo.includes("..") || !entrada_archivo.endsWith(".json")) {
        r.falla(`${p}.entrada_archivo`, "debe ser una ruta relativa a m2/ que termine en .json");
      }
    }
    const imagen = r.textoOpcional(c.imagen, `${p}.imagen`);
    if (imagen !== undefined && !ejemplos.some((e) => e.archivo === imagen)) r.falla(`${p}.imagen`, `«${imagen}» no es un archivo de \`ejemplos\``);
    const probabilidades = r.numeros(c.probabilidades, `${p}.probabilidades`, n);
    if (Math.abs(probabilidades.reduce((a, b) => a + b, 0) - 1) > 1e-4) r.falla(`${p}.probabilidades`, "deben sumar 1");
    const clase_predicha = r.entero(c.clase_predicha, `${p}.clase_predicha`, 0);
    if (clase_predicha >= n) r.falla(`${p}.clase_predicha`, "fuera del rango de clases");
    const forma = r.numeros(c.forma_mapas, `${p}.forma_mapas`, 3);
    if (forma[0] !== canales) r.falla(`${p}.forma_mapas`, `los canales (${forma[0]}) deben coincidir con pesos_cabeza (${canales})`);
    return {
      id: r.texto(c.id, `${p}.id`),
      ...(entrada_rgb ? { entrada_rgb } : {}),
      ...(entrada_archivo ? { entrada_archivo } : {}),
      ...(imagen ? { imagen } : {}),
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
    preprocesado,
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
//
// Recomendador de dos torres lineal/MLP:
// - la selección del usuario (opciones elegidas por preferencia) se codifica como un vector x de entrada, one-hot por
//   opción, preferencias en el orden de la lista y opciones en el orden de la lista (`codificacion`);
// - `torre_usuario` lleva x a u: capas `h ← W·h + b` (W es salida × entrada, como `torch.nn.Linear.weight`) con ReLU
//   si `activacion` es "relu";
// - cada destino trae un `embedding` v_d (misma dimensión que u) y un `sesgo` opcional (0 si falta);
// - puntaje(d) = ⟨u, v_d⟩ + sesgo_d; el top-K es de mayor a menor puntaje (empate: `id` ascendente) y, si
//   `puntaje.excluir_vistos`, sin los destinos que el usuario ya vio.

export interface DestinoM3 {
  /** Identificador estable del destino. */
  id: string;
  /** Nombre para mostrar (en el juguete lleva «(ficticio)»). */
  nombre: string;
  /** Embedding v_d: misma dimensión que la salida de `torre_usuario`. */
  embedding: number[];
  /** Sesgo del destino (popularidad, etc.); 0 si falta. */
  sesgo?: number;
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
  /** Destinos que el usuario calificó (1 a 5); puede estar vacío (usuario sin historial). */
  historial: { destino_id: string; calificacion: number }[];
  /** Top-K precomputado (K = `k_max`), sin destinos del historial, de mayor a menor puntaje. */
  top_k: RecomendacionM3[];
}

/** `m3/usuarios.json`. */
export interface UsuariosJson extends Base {
  /** Cómo se produjo el top-K precomputado (texto para mostrar). */
  modelo: string;
  /** K del top-K precomputado; la app muestra los primeros K <= k_max. */
  k_max: number;
  usuarios: UsuarioM3[];
}

export interface OpcionM3 {
  /** Identificador estable de la opción (único dentro de su preferencia). */
  id: string;
  etiqueta: string;
  descripcion?: string;
}

export interface PreferenciaM3 {
  /** Identificador estable de la preferencia. */
  id: string;
  /** Etiqueta en español (la pregunta). */
  etiqueta: string;
  /** Opciones entre las que se elige (una o varias). */
  opciones: OpcionM3[];
}

export interface CapaM3 {
  /** Pesos, salida × entrada (como `torch.nn.Linear.weight`). */
  W: number[][];
  /** Sesgo (uno por salida). */
  b: number[];
  activacion: "relu" | "ninguna";
}

/** `m3/perfil_nuevo.json`. */
export interface PerfilNuevoJson extends Base {
  /** Qué recomendador es (texto para mostrar). */
  modelo: string;
  /** Preferencias seleccionables, en el orden de la codificación. */
  preferencias: PreferenciaM3[];
  codificacion: {
    tipo: "one_hot_por_opcion";
    /** Número de entradas = total de opciones. */
    dimension: number;
    descripcion: string;
  };
  /** Torre de usuario: capas en orden; la primera recibe `codificacion.dimension` entradas. */
  torre_usuario: CapaM3[];
  puntaje: {
    tipo: "producto_punto_mas_sesgo";
    /** Si el top-K excluye los destinos ya vistos. */
    excluir_vistos: boolean;
    descripcion: string;
  };
  /** K inicial del control. */
  k_defecto: number;
  /** K máximo del control. */
  k_max: number;
}

/** Selección de opciones: `{preferencia_id: [opcion_id, ...]}` (una preferencia sin elegir puede faltar). */
export type SeleccionM3 = Record<string, string[]>;

export interface CasoPerfilM3 {
  seleccion: SeleccionM3;
  /** Destinos ya vistos que se excluyen del top-K (vacío si no aplica). */
  vistos: string[];
  k: number;
  /** Vector u que dio la torre de usuario con esa selección. */
  vector_usuario: number[];
  /** Top-K que devolvió Python con esa entrada. */
  top_k: RecomendacionM3[];
}

/** `m3/casos_paridad.json`. */
export interface CasosParidadM3 extends Base {
  casos: CasoPerfilM3[];
}

export function validarDestinos(raiz: unknown, archivo = "m3/destinos.json"): DestinosJson {
  const r = new Lector(archivo);
  const base = r.base(raiz);
  const ids = new Set<string>();
  let dimension = -1;
  const destinos = r.arreglo((raiz as Obj).destinos, "destinos", 1).map((x, i): DestinoM3 => {
    const p = `destinos[${i}]`;
    const d = r.objeto(x, p);
    const id = r.texto(d.id, `${p}.id`);
    if (ids.has(id)) r.falla(`${p}.id`, `destino repetido: ${id}`);
    ids.add(id);
    const embedding = r.numeros(d.embedding, `${p}.embedding`);
    if (embedding.length === 0) r.falla(`${p}.embedding`, "no puede estar vacío");
    if (dimension < 0) dimension = embedding.length;
    if (embedding.length !== dimension) r.falla(`${p}.embedding`, `debe tener ${dimension} elementos como los demás (tiene ${embedding.length})`);
    const e = r.numeros(d.embedding_2d, `${p}.embedding_2d`, 2);
    return {
      id,
      nombre: r.texto(d.nombre, `${p}.nombre`),
      embedding,
      ...(d.sesgo !== undefined ? { sesgo: r.numero(d.sesgo, `${p}.sesgo`) } : {}),
      embedding_2d: [e[0], e[1]],
    };
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
    top_k.forEach((f, j) => {
      if (vistos.has(f.destino_id)) r.falla(`${p}.top_k[${j}]`, "recomienda un destino que ya está en el historial");
    });
    return { id, nombre: r.texto(u.nombre, `${p}.nombre`), historial, top_k };
  });
  return { ...base, modelo: r.texto(o.modelo, "modelo"), k_max, usuarios };
}

export function validarPerfilNuevo(raiz: unknown, archivo = "m3/perfil_nuevo.json"): PerfilNuevoJson {
  const r = new Lector(archivo);
  const base = r.base(raiz);
  const o = raiz as Obj;
  const ids = new Set<string>();
  const preferencias = r.arreglo(o.preferencias, "preferencias", 1).map((x, i): PreferenciaM3 => {
    const p = `preferencias[${i}]`;
    const e = r.objeto(x, p);
    const id = r.texto(e.id, `${p}.id`);
    if (ids.has(id)) r.falla(`${p}.id`, `preferencia repetida: ${id}`);
    ids.add(id);
    const opIds = new Set<string>();
    const opciones = r.arreglo(e.opciones, `${p}.opciones`, 1).map((y, j): OpcionM3 => {
      const q = r.objeto(y, `${p}.opciones[${j}]`);
      const opId = r.texto(q.id, `${p}.opciones[${j}].id`);
      if (opIds.has(opId)) r.falla(`${p}.opciones[${j}].id`, `opción repetida: ${opId}`);
      opIds.add(opId);
      const descripcion = r.textoOpcional(q.descripcion, `${p}.opciones[${j}].descripcion`);
      return { id: opId, etiqueta: r.texto(q.etiqueta, `${p}.opciones[${j}].etiqueta`), ...(descripcion ? { descripcion } : {}) };
    });
    return { id, etiqueta: r.texto(e.etiqueta, `${p}.etiqueta`), opciones };
  });

  const cod = r.objeto(o.codificacion, "codificacion");
  if (cod.tipo !== "one_hot_por_opcion") r.falla("codificacion.tipo", 'solo se admite "one_hot_por_opcion"');
  const dimension = r.entero(cod.dimension, "codificacion.dimension", 1);
  const total = preferencias.reduce((s, p) => s + p.opciones.length, 0);
  if (dimension !== total) r.falla("codificacion.dimension", `debe ser el total de opciones (${total}); llegó ${dimension}`);

  let entradas = dimension;
  const torre_usuario = r.arreglo(o.torre_usuario, "torre_usuario", 1).map((x, i): CapaM3 => {
    const p = `torre_usuario[${i}]`;
    const c = r.objeto(x, p);
    const W = r.arreglo(c.W, `${p}.W`, 1).map((f, j) => r.numeros(f, `${p}.W[${j}]`, entradas));
    const b = r.numeros(c.b, `${p}.b`, W.length);
    if (c.activacion !== "relu" && c.activacion !== "ninguna") r.falla(`${p}.activacion`, 'debe ser "relu" o "ninguna"');
    entradas = W.length;
    return { W, b, activacion: c.activacion as "relu" | "ninguna" };
  });

  const pu = r.objeto(o.puntaje, "puntaje");
  if (pu.tipo !== "producto_punto_mas_sesgo") r.falla("puntaje.tipo", 'solo se admite "producto_punto_mas_sesgo"');
  const k_defecto = r.entero(o.k_defecto, "k_defecto", 1);
  const k_max = r.entero(o.k_max, "k_max", 1);
  if (k_defecto > k_max) r.falla("k_defecto", "no puede superar k_max");
  return {
    ...base,
    modelo: r.texto(o.modelo, "modelo"),
    preferencias,
    codificacion: { tipo: "one_hot_por_opcion", dimension, descripcion: r.texto(cod.descripcion, "codificacion.descripcion") },
    torre_usuario,
    puntaje: { tipo: "producto_punto_mas_sesgo", excluir_vistos: r.booleano(pu.excluir_vistos, "puntaje.excluir_vistos"), descripcion: r.texto(pu.descripcion, "puntaje.descripcion") },
    k_defecto,
    k_max,
  };
}

/** `m3/casos_paridad.json`: se valida contra el perfil nuevo (las opciones y la dimensión del vector deben existir). */
export function validarCasosM3(raiz: unknown, perfil: PerfilNuevoJson, archivo = "m3/casos_paridad.json"): CasosParidadM3 {
  const r = new Lector(archivo);
  const base = r.base(raiz);
  const salida = perfil.torre_usuario[perfil.torre_usuario.length - 1].W.length;
  const casos = r.arreglo((raiz as Obj).casos, "casos", 1).map((x, i): CasoPerfilM3 => {
    const p = `casos[${i}]`;
    const c = r.objeto(x, p);
    const sel = r.objeto(c.seleccion, `${p}.seleccion`);
    const seleccion: SeleccionM3 = {};
    for (const [prefId, ops] of Object.entries(sel)) {
      const pref = perfil.preferencias.find((q) => q.id === prefId);
      if (!pref) r.falla(`${p}.seleccion.${prefId}`, "no es una preferencia de perfil_nuevo.json");
      seleccion[prefId] = r.textos(ops, `${p}.seleccion.${prefId}`);
      seleccion[prefId].forEach((op, j) => {
        if (!pref!.opciones.some((q) => q.id === op)) r.falla(`${p}.seleccion.${prefId}[${j}]`, `«${op}» no es una opción de la preferencia`);
      });
    }
    if (Object.values(seleccion).every((v) => v.length === 0)) r.falla(`${p}.seleccion`, "debe elegir al menos una opción");
    const vistos = r.textos(c.vistos, `${p}.vistos`);
    const k = r.entero(c.k, `${p}.k`, 1);
    const top_k = validarTopK(r, c.top_k, `${p}.top_k`);
    if (top_k.length !== k) r.falla(`${p}.top_k`, `debe tener k (${k}) elementos`);
    top_k.forEach((f, j) => {
      if (vistos.includes(f.destino_id)) r.falla(`${p}.top_k[${j}]`, "recomienda un destino de `vistos`");
    });
    return { seleccion, vistos, k, vector_usuario: r.numeros(c.vector_usuario, `${p}.vector_usuario`, salida), top_k };
  });
  return { ...base, casos };
}

/**
 * Coherencia entre los archivos de M3: la dimensión de los embeddings es la salida de la torre de usuario y todo id
 * referenciado existe.
 */
export function validarCoherenciaM3(d: DestinosJson, u: UsuariosJson, p: PerfilNuevoJson, c?: CasosParidadM3): void {
  const ids = new Set(d.destinos.map((x) => x.id));
  const falla = (ruta: string, problema: string): never => {
    throw new ErrorContrato("m3", ruta, problema);
  };
  const salida = p.torre_usuario[p.torre_usuario.length - 1].W.length;
  d.destinos.forEach((x, i) => {
    if (x.embedding.length !== salida) falla(`destinos[${i}].embedding`, `debe tener ${salida} elementos (la salida de torre_usuario); tiene ${x.embedding.length}`);
  });
  u.usuarios.forEach((x, i) => {
    x.historial.forEach((h, j) => {
      if (!ids.has(h.destino_id)) falla(`usuarios[${i}].historial[${j}]`, `destino inexistente: ${h.destino_id}`);
    });
    x.top_k.forEach((f, j) => {
      if (!ids.has(f.destino_id)) falla(`usuarios[${i}].top_k[${j}]`, `destino inexistente: ${f.destino_id}`);
    });
  });
  c?.casos.forEach((x, i) => {
    [...x.vistos, ...x.top_k.map((f) => f.destino_id)].forEach((id) => {
      if (!ids.has(id)) falla(`casos_paridad.casos[${i}]`, `destino inexistente: ${id}`);
    });
  });
  if (p.k_max > d.destinos.length) falla("perfil_nuevo.k_max", "es mayor que el número de destinos");
}
