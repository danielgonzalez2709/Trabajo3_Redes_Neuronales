"use client";
// Deslizador + campo numérico con el mismo valor. El campo guarda un borrador local para poder escribir libremente;
// solo comunica valores dentro del rango y, al salir del campo, ajusta lo escrito al paso y al rango.
import { useId, useState } from "react";
import { formatearNumero } from "../lib/formato";
import estilos from "./Control.module.css";
import { Info } from "./Info";

interface Props {
  etiqueta: string;
  /** Texto de ayuda del globo «i» (y descripción para lectores de pantalla). */
  ayuda: string;
  unidad?: string;
  minimo: number;
  maximo: number;
  paso: number;
  valor: number;
  onCambio: (v: number) => void;
}

const decimalesDe = (paso: number): number => {
  const t = String(paso);
  const i = t.indexOf(".");
  return i < 0 ? 0 : t.length - i - 1;
};

export function ControlNumerico({ etiqueta, ayuda, unidad, minimo, maximo, paso, valor, onCambio }: Props) {
  const id = useId();
  const [borrador, setBorrador] = useState<string | null>(null);
  const d = decimalesDe(paso);
  const texto = (x: number) => `${formatearNumero(x, d)}${unidad ? ` ${unidad}` : ""}`;

  const alPaso = (x: number) => {
    const k = Math.round((x - minimo) / paso);
    return Number(Math.min(Math.max(minimo + k * paso, minimo), maximo).toFixed(Math.max(d, decimalesDe(minimo))));
  };

  const alEscribir = (t: string, x: number) => {
    setBorrador(t);
    if (Number.isFinite(x) && x >= minimo && x <= maximo) onCambio(x);
  };

  const alSalir = (x: number) => {
    setBorrador(null);
    if (Number.isFinite(x)) {
      const ajustado = alPaso(x);
      if (ajustado !== valor) onCambio(ajustado);
    }
  };

  return (
    <div className={estilos.control}>
      <div className={estilos.cabeza}>
        <span className={estilos.etiquetaFila}>
          <label className={estilos.etiqueta} id={`${id}-etiqueta`} htmlFor={`${id}-campo`}>
            {etiqueta}
          </label>
          <Info etiqueta={etiqueta} texto={ayuda} />
        </span>
        <span className={estilos.campoCaja}>
          <input
            id={`${id}-campo`}
            className={estilos.campo}
            type="number"
            inputMode="decimal"
            min={minimo}
            max={maximo}
            step={paso}
            value={borrador ?? String(valor)}
            aria-describedby={`${id}-ayuda ${id}-rango`}
            onChange={(ev) => alEscribir(ev.target.value, ev.target.valueAsNumber)}
            onBlur={(ev) => alSalir(ev.target.valueAsNumber)}
            onInvalid={(ev) => ev.preventDefault()}
          />
        </span>
      </div>
      <p className="oculta" id={`${id}-ayuda`}>
        {ayuda}
      </p>
      <div className={estilos.pista}>
        <input
          className={estilos.deslizador}
          type="range"
          min={minimo}
          max={maximo}
          step={paso}
          value={valor}
          aria-labelledby={`${id}-etiqueta`}
          aria-describedby={`${id}-ayuda`}
          aria-valuetext={texto(valor)}
          onChange={(ev) => {
            setBorrador(null);
            onCambio(Number(ev.target.value));
          }}
        />
      </div>
      <div className={estilos.extremos} id={`${id}-rango`}>
        <span aria-hidden="true">{formatearNumero(minimo, d)}</span>
        <span className={estilos.unidad}>{unidad}</span>
        <span className="oculta">{`Entre ${texto(minimo)} y ${texto(maximo)}.`}</span>
        <span aria-hidden="true">{formatearNumero(maximo, d)}</span>
      </div>
    </div>
  );
}
