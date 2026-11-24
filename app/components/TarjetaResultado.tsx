// Tarjeta genérica de resultado: título, cifra principal, una línea de contexto y contenido opcional debajo.
import type { ReactNode } from "react";
import estilos from "./TarjetaResultado.module.css";

interface Props {
  titulo: string;
  /** Cifra o frase principal. */
  valor: string;
  /** Línea de contexto bajo la cifra. */
  detalle?: string;
  /** Color de apoyo (acento por defecto); el significado nunca se transmite solo con el color. */
  tono?: "neutro" | "alerta" | "ok";
  children?: ReactNode;
}

export function TarjetaResultado({ titulo, valor, detalle, tono = "neutro", children }: Props) {
  return (
    <section className={`${estilos.tarjeta} ${estilos[tono]}`} aria-label={titulo}>
      <h2 className={estilos.titulo}>{titulo}</h2>
      <p className={estilos.valor}>{valor}</p>
      {detalle && <p className={estilos.detalle}>{detalle}</p>}
      {children}
    </section>
  );
}

/** Fila de tarjetas: una columna en celular, varias en pantallas anchas. */
export function FilaTarjetas({ children }: { children: ReactNode }) {
  return <div className={estilos.fila}>{children}</div>;
}
