// Geometría del gráfico SVG propio (sin librerías de gráficos). Dominio puro.

/** Escala lineal de [d0, d1] a [r0, r1]; si el dominio es un punto, devuelve el centro del rango. */
export function escalaLineal(d0: number, d1: number, r0: number, r1: number): (x: number) => number {
  if (d1 === d0) return () => (r0 + r1) / 2;
  return (x) => r0 + ((x - d0) / (d1 - d0)) * (r1 - r0);
}

/** Marcas «redondas» (1, 2, 5 × 10^n) para el eje de valores: de 0 hasta un tope >= `max`, con unas `n` marcas. */
export function marcasEje(max: number, n = 4): number[] {
  if (!(max > 0)) return [0, 1];
  const bruto = max / n;
  const potencia = 10 ** Math.floor(Math.log10(bruto));
  const f = bruto / potencia;
  const paso = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * potencia;
  const marcas: number[] = [];
  for (let v = 0; v < max + paso; v += paso) marcas.push(Number(v.toPrecision(12)));
  return marcas;
}

/** "M x,y L x,y …" para una polilínea; lista vacía → cadena vacía. */
export function trazoLinea(puntos: [number, number][]): string {
  return puntos.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
}

/** Polígono cerrado de una banda: borde superior de izquierda a derecha y borde inferior de derecha a izquierda. */
export function trazoBanda(superior: [number, number][], inferior: [number, number][]): string {
  if (superior.length === 0 || inferior.length === 0) return "";
  const recorrido = [...superior, ...[...inferior].reverse()];
  return `${trazoLinea(recorrido)} Z`;
}
