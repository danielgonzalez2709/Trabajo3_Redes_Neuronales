"use client";
// Demanda y operación (M1): pronóstico a 30 días con banda del cuantil elegido y flota/conductores por día.
// Los parámetros salen de operacion.json (cada uno con su fuente o marcado como supuesto) y la función de dimensionamiento
// de esta etapa es PROVISIONAL (juguete): la real es la de Camila (núcleo §5.4), en DA-6.
import { useMemo, useState } from "react";
import { ControlNumerico } from "../../components/ControlNumerico";
import { GraficoSerie } from "../../components/GraficoSerie";
import { Aviso, AvisoJuguete, Encabezado, Pagina, Pie, Provisional } from "../../components/Marco";
import { Segmentado } from "../../components/Segmentado";
import { FilaTarjetas, TarjetaResultado } from "../../components/TarjetaResultado";
import { useCarga } from "../../hooks/useCarga";
import {
  resolverParametro, validarCoherenciaM1, validarOperacion, validarPronosticos, type OperacionJson, type Parametro, type Pronosticos,
} from "../../lib/contratos";
import { cargarJson } from "../../lib/datos";
import { parametrosBase, tablaOperacion } from "../../lib/dimensionar";
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

/** Los parámetros por ruta y la composición por clase cambian con la ruta: su cambio se guarda aparte para cada ruta. */
const claveCambio = (ref: string, rutaId: string): string => (ref.startsWith("por_ruta.") || ref.startsWith("composicion_clases.") ? `${ref}@${rutaId}` : ref);

/** Texto de ayuda de un parámetro: qué es, de dónde sale (la cita de la fuente) o que es un supuesto. */
function textoAyuda(ayuda: string, par: Parametro): string {
  const origen = par.fuente !== undefined ? `Fuente: ${par.fuente}` : "Es un supuesto, sin fuente.";
  return [ayuda, origen, par.nota].filter(Boolean).join(" ");
}

const nombrePaso = (clave: string): string => clave.replaceAll("_", " ");

function Contenido({ pronosticos, operacion }: DatosM1) {
  const [rutaId, setRutaId] = useState(pronosticos.rutas[0].ruta_id);
  const [cambios, setCambios] = useState<Record<string, number>>({});
  const ruta = pronosticos.rutas.find((r) => r.ruta_id === rutaId) ?? pronosticos.rutas[0];
  const base = useMemo(() => parametrosBase(operacion.parametros, ruta.ruta_id), [operacion, ruta]);
  const efectivos = useMemo(() => {
    const e = { ...base };
    for (const c of operacion.controles) {
      const k = claveCambio(c.ref, ruta.ruta_id);
      if (Object.hasOwn(cambios, k)) e[c.ref] = cambios[k];
    }
    return e;
  }, [base, cambios, operacion, ruta]);
  const filas = useMemo(() => tablaOperacion(ruta.pronostico, pronosticos.cuantiles, efectivos), [ruta, pronosticos.cuantiles, efectivos]);
  const cuantilTexto = formatearCuantil(efectivos["globales.cuantil"]);
  const total = filas.reduce((s, f) => s + f.demanda, 0);
  const puntual = ruta.pronostico.reduce((s, d) => s + d.punto, 0);
  const despachos = filas.reduce((s, f) => s + f.despachos, 0);
  const maxVehiculos = Math.max(...filas.map((f) => f.vehiculos));
  const maxConductores = Math.max(...filas.map((f) => f.conductores));
  const pico = filas.reduce((a, f) => (f.demanda > a.demanda ? f : a), filas[0]);
  const cambiar = (ref: string, v: number) => setCambios((c) => ({ ...c, [claveCambio(ref, ruta.ruta_id)]: v }));
  const nombreRuta = (r: (typeof pronosticos.rutas)[number]) => `${r.origen.nombre} → ${r.destino.nombre}`;
  const etiquetaDe = (ref: string) => operacion.controles.find((c) => c.ref === ref)?.etiqueta ?? ref;
  const provisional = operacion.juguete ? <Provisional>función provisional</Provisional> : null;

  return (
    <>
      {pronosticos.juguete && <AvisoJuguete />}
      <div className={`${estilos.rejilla} ${estilos.conControles}`}>
        <aside className={estilos.panel} aria-label="Ruta y supuestos">
          <label className={estilos.etiquetaCampo} htmlFor="ruta">
            Ruta
          </label>
          <select id="ruta" className={estilos.selector} value={rutaId} onChange={(e) => setRutaId(e.target.value)}>
            {pronosticos.rutas.map((r) => (
              <option key={r.ruta_id} value={r.ruta_id}>
                {nombreRuta(r)}
              </option>
            ))}
          </select>
          <h2 className={`${estilos.panelTitulo} ${estilos.tituloSeparado}`}>
            Supuestos de operación {provisional}
          </h2>
          {operacion.controles.map((c) => {
            const par = resolverParametro(operacion.parametros, c.ref, ruta.ruta_id);
            if (!par) return null;
            const valor = efectivos[c.ref];
            return c.tipo === "numero" ? (
              <ControlNumerico
                key={c.ref}
                etiqueta={c.etiqueta}
                ayuda={textoAyuda(c.ayuda, par)}
                unidad={par.unidad || undefined}
                minimo={c.minimo}
                maximo={c.maximo}
                paso={c.paso}
                valor={valor}
                onCambio={(v) => cambiar(c.ref, v)}
              />
            ) : (
              <div key={c.ref} className={estilos.campoSeparado}>
                <Segmentado
                  nombre={c.ref}
                  leyenda={c.etiqueta}
                  opciones={c.opciones.map((q) => ({ valor: String(q), etiqueta: formatearCuantil(q) }))}
                  valor={String(valor)}
                  onCambio={(v) => cambiar(c.ref, Number(v))}
                />
                <p className={estilos.nota}>{textoAyuda(c.ayuda, par)}</p>
              </div>
            );
          })}
        </aside>

        <div className={estilos.bloque}>
          <FilaTarjetas>
            <TarjetaResultado
              titulo={`Demanda en 30 días al cuantil ${cuantilTexto}`}
              valor={formatearNumero(total)}
              detalle="Pasajeros: suma de la demanda de cada día al cuantil elegido; con ella se dimensiona."
            />
            <TarjetaResultado titulo="Pronóstico puntual en 30 días" valor={formatearNumero(puntual)} detalle="Pasajeros: el valor central del modelo." />
            <TarjetaResultado titulo="Despachos en 30 días" valor={formatearNumero(despachos)}>
              {provisional}
            </TarjetaResultado>
            <TarjetaResultado titulo="Vehículos (máximo diario)" valor={formatearNumero(maxVehiculos)}>
              {provisional}
            </TarjetaResultado>
            <TarjetaResultado titulo="Conductores (máximo diario)" valor={formatearNumero(maxConductores)}>
              {provisional}
            </TarjetaResultado>
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

          <details className={estilos.detalles}>
            <summary>Cómo se calculó el día de mayor demanda ({formatearFecha(pico.fecha)})</summary>
            <ul className={estilos.pasos}>
              <li>Demanda al cuantil {cuantilTexto}: {formatearNumero(pico.demanda)} pasajeros</li>
              {Object.entries(pico.pasos).map(([clave, v]) => (
                <li key={clave}>
                  {nombrePaso(clave)}: {formatearNumero(v, 2)}
                </li>
              ))}
              <li>Despachos: {formatearNumero(pico.despachos)}</li>
              <li>Vehículos: {formatearNumero(pico.vehiculos)}</li>
              <li>Conductores: {formatearNumero(pico.conductores)}</li>
            </ul>
          </details>

          <details className={estilos.detalles}>
            <summary>Todos los parámetros y de dónde salen</summary>
            <div className={estilos.tablaMarco}>
              <table className={`${estilos.tabla} ${estilos.tablaTexto}`}>
                <caption className="oculta">Parámetros de la ruta {nombreRuta(ruta)}</caption>
                <thead>
                  <tr>
                    <th scope="col">Parámetro</th>
                    <th scope="col">Valor</th>
                    <th scope="col">Origen</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(efectivos).map(([ref, valor]) => {
                    const par = resolverParametro(operacion.parametros, ref, ruta.ruta_id);
                    return (
                      <tr key={ref}>
                        <th scope="row">{etiquetaDe(ref)}</th>
                        <td>
                          {formatearNumero(valor, 2)} {par?.unidad}
                        </td>
                        <td>{par ? (par.fuente !== undefined ? `Fuente: ${par.fuente}` : `Supuesto. ${par.nota ?? ""}`) : ""}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </details>
        </div>
      </div>
    </>
  );
}
