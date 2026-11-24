// PROVISIONAL (juguete). Réplica de `recomendar_perfil_juguete` de scripts/generar_juguetes_app.py: regla de juguete
// para el perfil nuevo de M3. La regla real la define Juan José (núcleo §5.8) y se porta en DA-8. Dominio puro.
import type { DestinoM3, RecomendacionM3 } from "./contratos";

/**
 * puntaje = promedio del atributo de cada preferencia elegida + peso · popularidad. Orden: puntaje descendente y, en
 * empate, id ascendente. Las preferencias se recorren en el orden de `preferenciasIds` (no en el de selección) para que la
 * suma en coma flotante coincida con la de Python.
 */
export function recomendarPerfilJuguete(
  seleccion: string[],
  destinos: DestinoM3[],
  preferenciasIds: string[],
  k: number,
  pesoPopularidad: number,
): RecomendacionM3[] {
  const elegidas = preferenciasIds.filter((p) => seleccion.includes(p));
  if (elegidas.length === 0) throw new Error("seleccione al menos una preferencia");
  if (!Number.isInteger(k) || k < 1) throw new Error("k debe ser un entero >= 1");
  const filas = destinos.map((d) => {
    let suma = 0;
    for (const p of elegidas) suma += d.atributos[p];
    return { destino_id: d.id, puntaje: suma / elegidas.length + pesoPopularidad * d.popularidad };
  });
  filas.sort((a, b) => b.puntaje - a.puntaje || (a.destino_id < b.destino_id ? -1 : a.destino_id > b.destino_id ? 1 : 0));
  return filas.slice(0, k);
}
