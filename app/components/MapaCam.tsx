"use client";
// Mapa de interpretabilidad (CAM) de M2 pintado sobre la imagen PREPROCESADA, la que ve la red (tamano_entrada del meta).
// El cálculo es puro y está probado en lib/clasificar.ts:
//   CAM_c = Σ_k w_{c,k} · A_k  →  ReLU y normalización a [0, 1] por imagen (solo para pintar)  →  remuestreo bilineal de
//   H × W al tamaño de la imagen  →  viridis  →  mezcla con la imagen: (1 − α)·imagen + α·color.
// Aquí solo se elige la clase y la opacidad y se vuelca el resultado en un lienzo.
import { useEffect, useId, useMemo, useRef, useState } from "react";
import { camParaPintar, superponerCam, VIRIDIS } from "../lib/clasificar";
import type { MetaM2 } from "../lib/contratos";
import { ControlNumerico } from "./ControlNumerico";
import estilos from "./MapaCam.module.css";

interface Props {
  meta: Pick<MetaM2, "clases" | "pesos_cabeza" | "tamano_entrada">;
  /** RGB uint8 aplanado (alto, ancho, canal) al tamaño de entrada: la imagen que entró a la red. */
  rgb: ArrayLike<number>;
  /** Activaciones de la última convolución (C·H·W) y su forma [C, H, W]. */
  mapas: ArrayLike<number>;
  formaMapas: [number, number, number];
  claseAsignada: number;
  opacidad: number;
  onOpacidad: (v: number) => void;
}

/** Degradado CSS de la leyenda con 9 paradas de la misma tabla viridis que pinta el lienzo. */
const DEGRADADO = `linear-gradient(to right, ${Array.from({ length: 9 }, (_, i) => {
  const [r, g, b] = VIRIDIS[Math.round((i / 8) * 255)];
  return `rgb(${r} ${g} ${b}) ${(i / 8) * 100}%`;
}).join(", ")})`;

export function MapaCam({ meta, rgb, mapas, formaMapas, claseAsignada, opacidad, onOpacidad }: Props) {
  const id = useId();
  const lienzo = useRef<HTMLCanvasElement>(null);
  const [clase, setClase] = useState(claseAsignada); // el padre remonta el componente (key) con cada resultado nuevo
  const { alto, ancho } = meta.tamano_entrada;

  const mapa01 = useMemo(
    () => camParaPintar(mapas, formaMapas, meta.pesos_cabeza[clase], alto, ancho),
    [mapas, formaMapas, meta.pesos_cabeza, clase, alto, ancho],
  );

  useEffect(() => {
    const ctx = lienzo.current?.getContext("2d");
    if (!ctx) return;
    ctx.putImageData(new ImageData(superponerCam(rgb, mapa01, opacidad), ancho, alto), 0, 0);
  }, [rgb, mapa01, opacidad, alto, ancho]);

  const nombre = meta.clases[clase]?.nombre ?? "";
  const asignada = clase === claseAsignada;
  const plano = mapa01.every((v) => v === 0);

  return (
    <figure className={estilos.figura} aria-labelledby={`${id}-pie`}>
      <canvas
        ref={lienzo}
        className={estilos.lienzo}
        width={ancho}
        height={alto}
        role="img"
        aria-label={`Mapa CAM de la clase «${nombre}»${asignada ? " (la asignada)" : ""} sobre la imagen que ve la red, de ${ancho} × ${alto} píxeles. Las zonas amarillas son las que más empujan el modelo hacia esa clase; las moradas, las que menos.${plano ? " En esta imagen ninguna zona empuja hacia esa clase." : ""}`}
      />
      <div className={estilos.leyenda} aria-hidden="true">
        <span className={estilos.barra} style={{ backgroundImage: DEGRADADO }} />
        <span className={estilos.extremos}>
          <span>menos influencia</span>
          <span>más influencia</span>
        </span>
      </div>
      <figcaption id={`${id}-pie`} className={estilos.pie}>
        <strong>Mapa de interpretabilidad (CAM): {nombre}</strong>
        {asignada ? " — clase asignada." : "."} Muestra en qué zonas de la imagen (tal como la ve la red, {ancho} × {alto}) se
        apoya el modelo para esa clase. La escala es relativa a cada imagen: el amarillo es el máximo de esta imagen, no un
        valor absoluto.
        {plano && " En esta imagen ninguna zona empuja hacia esa clase: el mapa queda en el mínimo."}
      </figcaption>
      <div className={estilos.controles}>
        <label className={estilos.etiqueta} htmlFor={`${id}-clase`}>
          Clase del mapa
        </label>
        <select id={`${id}-clase`} className={estilos.selector} value={clase} onChange={(e) => setClase(Number(e.target.value))}>
          {meta.clases.map((c, i) => (
            <option key={c.id} value={i}>
              {c.nombre}
              {i === claseAsignada ? " (asignada)" : ""}
            </option>
          ))}
        </select>
        <ControlNumerico
          etiqueta="Opacidad del mapa"
          ayuda="0 muestra solo la imagen; 1 muestra solo el mapa de color."
          minimo={0}
          maximo={1}
          paso={0.05}
          valor={opacidad}
          onCambio={onOpacidad}
        />
      </div>
    </figure>
  );
}
