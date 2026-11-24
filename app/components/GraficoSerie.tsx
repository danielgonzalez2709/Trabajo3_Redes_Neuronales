// Gráfico SVG propio: historia reciente, pronóstico y banda entre el pronóstico puntual y el cuantil elegido.
// El eje horizontal es el índice de día (historia + pronóstico, todos consecutivos); los textos del eje salen de las fechas.
import { escalaLineal, marcasEje, trazoBanda, trazoLinea } from "../lib/grafico";
import { formatearFecha, formatearNumero } from "../lib/formato";
import estilos from "./GraficoSerie.module.css";

export interface PuntoSerie {
  fecha: string;
  valor: number;
}

export interface PuntoBanda {
  fecha: string;
  /** Pronóstico puntual (borde inferior de la banda). */
  punto: number;
  /** Valor del cuantil elegido (borde superior de la banda). */
  alto: number;
}

interface Props {
  historia: PuntoSerie[];
  banda: PuntoBanda[];
  /** Texto del cuantil elegido para la leyenda (p. ej. "90 %"). */
  cuantilTexto: string;
  /** Descripción accesible del gráfico. */
  descripcion: string;
}

const ANCHO = 720;
const ALTO = 300;
const M = { izq: 56, der: 12, sup: 14, inf: 34 };

export function GraficoSerie({ historia, banda, cuantilTexto, descripcion }: Props) {
  const n = historia.length + banda.length;
  const tope = Math.max(1, ...historia.map((p) => p.valor), ...banda.map((b) => b.alto));
  const marcas = marcasEje(tope);
  const maxY = marcas[marcas.length - 1];
  const x = escalaLineal(0, Math.max(1, n - 1), M.izq, ANCHO - M.der);
  const y = escalaLineal(0, maxY, ALTO - M.inf, M.sup);
  const iPron = historia.length; // índice del primer día pronosticado
  const ptsHist = historia.map((p, i): [number, number] => [x(i), y(p.valor)]);
  const ptsPunto = banda.map((b, i): [number, number] => [x(iPron + i), y(b.punto)]);
  const ptsAlto = banda.map((b, i): [number, number] => [x(iPron + i), y(b.alto)]);
  const fechas = [...historia.map((p) => p.fecha), ...banda.map((b) => b.fecha)];
  const idxEtiquetas = [0, Math.floor(iPron / 2), iPron, iPron + Math.floor(banda.length / 2), n - 1].filter(
    (i, k, a) => i >= 0 && i < n && a.indexOf(i) === k,
  );
  // La línea del pronóstico arranca en el último día de la historia para que no quede un hueco.
  const unido = historia.length > 0 && banda.length > 0 ? [ptsHist[ptsHist.length - 1], ...ptsPunto] : ptsPunto;

  return (
    <figure className={estilos.figura}>
      <svg className={estilos.svg} viewBox={`0 0 ${ANCHO} ${ALTO}`} role="img" aria-label={descripcion}>
        {marcas.map((v) => (
          <g key={v}>
            <line className={estilos.rejilla} x1={M.izq} x2={ANCHO - M.der} y1={y(v)} y2={y(v)} />
            <text className={estilos.texto} x={M.izq - 8} y={y(v)} textAnchor="end" dominantBaseline="middle">
              {formatearNumero(v)}
            </text>
          </g>
        ))}
        {banda.length > 0 && (
          <>
            <rect className={estilos.zonaPronostico} x={x(iPron)} y={M.sup} width={ANCHO - M.der - x(iPron)} height={ALTO - M.inf - M.sup} />
            <path className={estilos.banda} d={trazoBanda(ptsAlto, ptsPunto)} />
            <path className={estilos.lineaCuantil} d={trazoLinea(ptsAlto)} />
          </>
        )}
        <path className={estilos.lineaHistoria} d={trazoLinea(ptsHist)} />
        <path className={estilos.lineaPronostico} d={trazoLinea(unido)} />
        {idxEtiquetas.map((i) => (
          <text key={i} className={estilos.texto} x={x(i)} y={ALTO - 10} textAnchor={i === 0 ? "start" : i === n - 1 ? "end" : "middle"}>
            {formatearFecha(fechas[i])}
          </text>
        ))}
      </svg>
      <figcaption className={estilos.leyenda}>
        <span className={estilos.itemHistoria}>Historia reciente</span>
        <span className={estilos.itemPronostico}>Pronóstico puntual</span>
        <span className={estilos.itemBanda}>Banda hasta el cuantil {cuantilTexto}</span>
      </figcaption>
    </figure>
  );
}
