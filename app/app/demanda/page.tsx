"use client";
// Demanda y operación (M1): pronóstico a 30 días con banda del cuantil elegido y flota/conductores por día.
// La función de dimensionamiento de esta etapa es PROVISIONAL (juguete): la real es la de Camila (núcleo §5.4), en DA-6.
import { useMemo, useState } from "react";
import { ControlNumerico } from "../../components/ControlNumerico";
import { GraficoSerie } from "../../components/GraficoSerie";
import { Aviso, AvisoJuguete, Encabezado, Pagina, Pie, Provisional } from "../../components/Marco";
import { Segmentado } from "../../components/Segmentado";
import { FilaTarjetas, TarjetaResultado } from "../../components/TarjetaResultado";
import { useCarga } from "../../hooks/useCarga";
import {
  validarCoherenciaM1, validarOperacion, validarPronosticos, type OperacionJson, type Pronosticos,
} from "../../lib/contratos";
import { cargarJson } from "../../lib/datos";
import { tablaOperacion } from "../../lib/dimensionar";
import { formatearCuantil, formatearFecha, formatearFechaLarga, formatearNumero } from "../../lib/formato";
import estilos from "../modulo.module.css";

interface DatosM1 {
  pronosticos: Pronosticos;
  operacion: OperacionJson;
}

const cargar = async (): Promise<DatosM1> => {
  const [pronosticos, operacion] = await Promise.all([
    cargarJson("m1/pronosticos.json", validarPronosticos),
    cargarJson("m1/operacion.json", validarOperacion),
  ]);
  validarCoherenciaM1(pronosticos, operacion);
  return { pronosticos, operacion };
};

export default function Demanda() {
  const carga = useCarga(cargar);
  return (
    <Pagina>
      <Encabezado
        titulo="Demanda y operación"
        descripcion="Elige una ruta para ver cuántos pasajeros se esperan en los próximos 30 días y cuánta flota y cuántos conductores harían falta. Cambia los supuestos y mira cómo se ajusta todo."
      />
      {carga.estado === "cargando" && <Aviso tipo="carga">Cargando el pronóstico…</Aviso>}
      {carga.estado === "error" && <Aviso tipo="error">{carga.mensaje}</Aviso>}
      {carga.estado === "listo" && <Contenido {...carga.datos} />}
      <Pie />
    </Pagina>
  );
}

function Contenido({ pronosticos, operacion }: DatosM1) {
  const [rutaId, setRutaId] = useState(pronosticos.rutas[0].ruta_id);
  const [params, setParams] = useState<Record<string, number>>(() => ({
    ...operacion.parametros,
    ...Object.fromEntries(operacion.controles.map((c) => [c.clave, c.defecto])),
  }));
  const ruta = pronosticos.rutas.find((r) => r.ruta_id === rutaId) ?? pronosticos.rutas[0];
  const filas = useMemo(() => tablaOperacion(ruta.pronostico, pronosticos.cuantiles, params), [ruta, pronosticos.cuantiles, params]);
  const cuantilTexto = formatearCuantil(params.cuantil);
  const total = filas.reduce((s, f) => s + f.demanda, 0);
  const despachos = filas.reduce((s, f) => s + f.despachos, 0);
  const maxVehiculos = Math.max(...filas.map((f) => f.vehiculos));
  const maxConductores = Math.max(...filas.map((f) => f.conductores));
  const cambiar = (clave: string, v: number) => setParams((p) => ({ ...p, [clave]: v }));
  const nombreRuta = (r: (typeof pronosticos.rutas)[number]) => `${r.origen.nombre} → ${r.destino.nombre}`;

  return (
    <>
      {pronosticos.juguete && <AvisoJuguete />}
      <div className={`${estilos.rejilla} ${estilos.conControles}`}>
        <aside className={estilos.panel} aria-label="Ruta y supuestos">
          <label className={estilos.etiquetaCampo} htmlFor="ruta">
            Ruta
          </label>
          <select id="ruta" className={`${estilos.selector}`} value={rutaId} onChange={(e) => setRutaId(e.target.value)}>
            {pronosticos.rutas.map((r) => (
              <option key={r.ruta_id} value={r.ruta_id}>
                {nombreRuta(r)}
              </option>
            ))}
          </select>
          <h2 className={estilos.panelTitulo} style={{ marginTop: "1rem" }}>
            Supuestos de operación <Provisional>función provisional</Provisional>
          </h2>
          {operacion.controles.map((c) =>
            c.tipo === "numero" ? (
              <ControlNumerico
                key={c.clave}
                etiqueta={c.etiqueta}
                ayuda={c.ayuda}
                unidad={c.unidad || undefined}
                minimo={c.minimo}
                maximo={c.maximo}
                paso={c.paso}
                valor={params[c.clave]}
                onCambio={(v) => cambiar(c.clave, v)}
              />
            ) : (
              <div key={c.clave} style={{ paddingTop: "0.9rem" }}>
                <Segmentado
                  nombre={c.clave}
                  leyenda={c.etiqueta}
                  opciones={c.opciones.map((q) => ({ valor: String(q), etiqueta: formatearCuantil(q) }))}
                  valor={String(params[c.clave])}
                  onCambio={(v) => cambiar(c.clave, Number(v))}
                />
                <p className={estilos.nota}>{c.ayuda}</p>
              </div>
            ),
          )}
        </aside>

        <div className={estilos.bloque}>
          <FilaTarjetas>
            <TarjetaResultado titulo="Pasajeros en 30 días" valor={formatearNumero(total)} detalle={`Con el cuantil ${cuantilTexto}.`} />
            <TarjetaResultado titulo="Despachos en 30 días" valor={formatearNumero(despachos)} />
            <TarjetaResultado titulo="Vehículos (máximo diario)" valor={formatearNumero(maxVehiculos)} />
            <TarjetaResultado titulo="Conductores (máximo diario)" valor={formatearNumero(maxConductores)} />
          </FilaTarjetas>
          <GraficoSerie
            historia={ruta.historia.map((p) => ({ fecha: p.fecha, valor: p.pasajeros }))}
            banda={ruta.pronostico.map((d, i) => ({ fecha: d.fecha, punto: d.punto, alto: filas[i].demanda }))}
            cuantilTexto={cuantilTexto}
            descripcion={`Pasajeros por día en la ruta ${nombreRuta(ruta)}: los últimos ${ruta.historia.length} días observados hasta el ${formatearFechaLarga(pronosticos.fecha_origen)} y el pronóstico de los siguientes ${pronosticos.horizonte} días con su banda hasta el cuantil ${cuantilTexto}.`}
          />
          <p className={estilos.nota}>
            Modelo: {pronosticos.modelo}. Último día con información: {formatearFechaLarga(pronosticos.fecha_origen)}. La demanda
            de cada día es el cuantil {cuantilTexto} del pronóstico; un cuantil más alto es más prudente y pide más flota.
          </p>
          <div className={estilos.tablaMarco}>
            <table className={estilos.tabla}>
              <caption>Operación día a día · {nombreRuta(ruta)}</caption>
              <thead>
                <tr>
                  <th scope="col">Día</th>
                  <th scope="col">Pasajeros ({cuantilTexto})</th>
                  <th scope="col">Despachos</th>
                  <th scope="col">Vehículos</th>
                  <th scope="col">Conductores</th>
                </tr>
              </thead>
              <tbody>
                {filas.map((f) => (
                  <tr key={f.fecha}>
                    <th scope="row">{formatearFecha(f.fecha)}</th>
                    <td>{formatearNumero(f.demanda)}</td>
                    <td>{formatearNumero(f.despachos)}</td>
                    <td>{formatearNumero(f.vehiculos)}</td>
                    <td>{formatearNumero(f.conductores)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
