"use client";
// Piezas fijas de cada página: encabezado con la navegación entre módulos, pie, avisos de carga o error y el aviso de
// «Datos de juguete». Los enlaces externos vienen de lib/enlaces.ts.
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { URL_REPORTE_TECNICO } from "../lib/enlaces";
import estilos from "./Marco.module.css";

export const SECCIONES = [
  { ruta: "/", etiqueta: "Inicio" },
  { ruta: "/demanda", etiqueta: "Demanda" },
  { ruta: "/conduccion", etiqueta: "Conducción" },
  { ruta: "/recomendacion", etiqueta: "Recomendación" },
] as const;

const NOMBRE_APP = "Operación inteligente de transporte";

export function Encabezado({ titulo, descripcion }: { titulo: string; descripcion: string }) {
  const actual = usePathname();
  return (
    <>
      <header className={estilos.barra}>
        <Link href="/" className={estilos.marca}>
          {NOMBRE_APP}
        </Link>
        <nav className={estilos.navegacion} aria-label="Módulos de la aplicación">
          {SECCIONES.map((s) => (
            <Link key={s.ruta} href={s.ruta} className={estilos.enlace} aria-current={actual === s.ruta ? "page" : undefined}>
              {s.etiqueta}
            </Link>
          ))}
          <a className={estilos.enlace} href={URL_REPORTE_TECNICO} target="_blank" rel="noopener noreferrer">
            Reporte técnico<span aria-hidden="true">↗</span>
            <span className="oculta"> (se abre en otra pestaña)</span>
          </a>
        </nav>
      </header>
      <h1 className={estilos.titulo}>{titulo}</h1>
      <p className={estilos.detalle}>{descripcion}</p>
    </>
  );
}

export function Pie() {
  return (
    <footer className={estilos.pie}>
      <p>
        Herramienta académica del Trabajo 3 (Redes neuronales y algoritmos bioinspirados, UNAL). Los modelos corren en tu
        navegador; nada de lo que subes sale de tu equipo.
      </p>
    </footer>
  );
}

export function Pagina({ children }: { children: ReactNode }) {
  return <main className={estilos.pagina}>{children}</main>;
}

export function Aviso({ tipo, children }: { tipo: "carga" | "error"; children: ReactNode }) {
  return (
    <div className={tipo === "error" ? estilos.error : estilos.carga} role={tipo === "error" ? "alert" : "status"}>
      {children}
    </div>
  );
}

/** Aviso visible en cada página cuyo JSON trae `"juguete": true` (nada que se vea es un resultado real). */
export function AvisoJuguete({ detalle }: { detalle?: string }) {
  return (
    <p className={estilos.juguete} role="note">
      <strong>Datos de juguete.</strong> {detalle ?? "Lo que ves aquí es ficticio y sirve para probar la aplicación; no son resultados de los modelos reales."}
    </p>
  );
}

/** Marca de lo provisional dentro de la interfaz (p. ej. la función de dimensionamiento de juguete). */
export function Provisional({ children }: { children: ReactNode }) {
  return <span className={estilos.provisional}>{children}</span>;
}
