// Formato de lo que se muestra (no cambia ningún cálculo). Español de Colombia: coma decimal y punto de miles. Dominio puro.

/** Número con `decimales` decimales: 1234.5 → "1.234,5". */
export function formatearNumero(x: number, decimales = 0): string {
  const [entera, frac] = Math.abs(x).toFixed(decimales).split(".");
  const miles = entera.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${x < 0 && Number(x.toFixed(decimales)) !== 0 ? "-" : ""}${miles}${frac ? `,${frac}` : ""}`;
}

/** Porcentaje con un decimal: 0,1835 → "18,4 %". */
export function formatearPorcentaje(p: number, decimales = 1): string {
  return `${formatearNumero(p * 100, decimales)} %`;
}

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const DIAS = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];

/** "2025-01-03" → "vie 3 ene" (sin zonas horarias: la fecha se lee como calendario). */
export function formatearFecha(iso: string): string {
  const [a, m, d] = iso.split("-").map(Number);
  const dia = new Date(Date.UTC(a, m - 1, d)).getUTCDay();
  return `${DIAS[dia]} ${d} ${MESES[m - 1]}`;
}

/** "2025-01-03" → "3 ene 2025". */
export function formatearFechaLarga(iso: string): string {
  const [a, m, d] = iso.split("-").map(Number);
  return `${d} ${MESES[m - 1]} ${a}`;
}

/** Cuantil como texto: 0,9 → "90 %". */
export function formatearCuantil(q: number): string {
  return `${formatearNumero(q * 100, Number.isInteger(Math.round(q * 1000) / 10) ? 0 : 1)} %`;
}
