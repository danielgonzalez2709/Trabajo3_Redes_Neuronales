"use client";
// Carga una vez, al montar, lo que devuelve `cargador` y expone el estado: cargando, error o datos.
import { useEffect, useState } from "react";

export type EstadoCarga<T> = { estado: "cargando" } | { estado: "error"; mensaje: string } | { estado: "listo"; datos: T };

export function useCarga<T>(cargador: () => Promise<T>): EstadoCarga<T> {
  const [resultado, setResultado] = useState<EstadoCarga<T>>({ estado: "cargando" });
  // `cargador` es estable por diseño (se define fuera del componente): se carga una sola vez, al montar.
  useEffect(() => {
    let vigente = true;
    cargador().then(
      (datos) => {
        if (vigente) setResultado({ estado: "listo", datos });
      },
      (e: unknown) => {
        if (vigente) setResultado({ estado: "error", mensaje: e instanceof Error ? e.message : String(e) });
      },
    );
    return () => {
      vigente = false;
    };
  }, []);
  return resultado;
}
