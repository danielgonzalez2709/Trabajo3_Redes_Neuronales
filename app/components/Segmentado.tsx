// Control segmentado accesible: un grupo de radios nativos (teclado y lector de pantalla sin trabajo extra).
import estilos from "./Segmentado.module.css";

export interface OpcionSegmentada {
  valor: string;
  etiqueta: string;
}

interface Props {
  nombre: string;
  leyenda: string;
  opciones: OpcionSegmentada[];
  valor: string;
  onCambio: (valor: string) => void;
}

export function Segmentado({ nombre, leyenda, opciones, valor, onCambio }: Props) {
  return (
    <fieldset className={estilos.grupo}>
      <legend className={estilos.leyenda}>{leyenda}</legend>
      <div className={estilos.pista}>
        {opciones.map((o) => (
          <label key={o.valor} className={estilos.opcion}>
            <input
              type="radio"
              className={estilos.radio}
              name={nombre}
              value={o.valor}
              checked={o.valor === valor}
              onChange={() => onCambio(o.valor)}
            />
            <span className={estilos.cara}>{o.etiqueta}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
