"use client";
// Recomendación (M3): usuario existente (historial + top-K precomputado) o perfil nuevo armado con una lista de preferencias.
// En DA-5 la regla del perfil nuevo es de JUGUETE (lib/recomendar.ts); la real llega en DA-8.
import { useMemo, useState } from "react";
import { ControlNumerico } from "../../components/ControlNumerico";
import { Aviso, AvisoJuguete, Encabezado, Pagina, Pie, Provisional } from "../../components/Marco";
import { Segmentado } from "../../components/Segmentado";
import { useCarga } from "../../hooks/useCarga";
import {
  validarCoherenciaM3, validarDestinos, validarPerfilNuevo, validarUsuarios, type DestinosJson, type PerfilNuevoJson,
  type RecomendacionM3, type UsuariosJson,
} from "../../lib/contratos";
import { cargarJson } from "../../lib/datos";
import { formatearNumero } from "../../lib/formato";
import { recomendarPerfilJuguete } from "../../lib/recomendar";
import estilos from "../modulo.module.css";

interface DatosM3 {
  destinos: DestinosJson;
  usuarios: UsuariosJson;
  perfil: PerfilNuevoJson;
}

const cargar = async (): Promise<DatosM3> => {
  const [destinos, usuarios, perfil] = await Promise.all([
    cargarJson("m3/destinos.json", validarDestinos),
    cargarJson("m3/usuarios.json", validarUsuarios),
    cargarJson("m3/perfil_nuevo.json", validarPerfilNuevo),
  ]);
  validarCoherenciaM3(destinos, usuarios, perfil);
  return { destinos, usuarios, perfil };
};

export default function Recomendacion() {
  const carga = useCarga(cargar);
  return (
    <Pagina>
      <Encabezado
        titulo="Recomendación de destinos"
        descripcion="Mira qué destinos recomendamos a un usuario que ya conocemos, o cuéntanos qué te gusta y arma un perfil nuevo."
      />
      {carga.estado === "cargando" && <Aviso tipo="carga">Cargando los destinos…</Aviso>}
      {carga.estado === "error" && <Aviso tipo="error">{carga.mensaje}</Aviso>}
      {carga.estado === "listo" && <Contenido {...carga.datos} />}
      <Pie />
    </Pagina>
  );
}

function Contenido({ destinos, usuarios, perfil }: DatosM3) {
  const [modo, setModo] = useState<"existente" | "nuevo">("existente");
  const [usuarioId, setUsuarioId] = useState(usuarios.usuarios[0].id);
  const [elegidas, setElegidas] = useState<string[]>([]);
  const [k, setK] = useState(perfil.k_defecto);
  const nombre = useMemo(() => new Map(destinos.destinos.map((d) => [d.id, d.nombre])), [destinos]);
  const usuario = usuarios.usuarios.find((u) => u.id === usuarioId) ?? usuarios.usuarios[0];
  const kMax = Math.min(perfil.k_max, usuarios.k_max);

  const recomendaciones: RecomendacionM3[] | null = useMemo(() => {
    if (modo === "existente") return usuario.top_k.slice(0, k);
    if (elegidas.length === 0) return null;
    return recomendarPerfilJuguete(elegidas, destinos.destinos, perfil.preferencias.map((p) => p.id), k, perfil.regla.peso_popularidad);
  }, [modo, usuario, elegidas, k, destinos, perfil]);

  const alternar = (id: string) => setElegidas((e) => (e.includes(id) ? e.filter((x) => x !== id) : [...e, id]));
  const juguete = destinos.juguete || usuarios.juguete || perfil.juguete;

  return (
    <>
      {juguete && <AvisoJuguete detalle="Los destinos y los usuarios son ficticios y las recomendaciones salen de reglas de prueba; no son resultados del recomendador real." />}
      <div className={`${estilos.rejilla} ${estilos.conControles}`}>
        <aside className={estilos.panel} aria-label="Quién recibe la recomendación">
          <Segmentado
            nombre="modo"
            leyenda="¿Para quién?"
            opciones={[
              { valor: "existente", etiqueta: "Usuario existente" },
              { valor: "nuevo", etiqueta: "Perfil nuevo" },
            ]}
            valor={modo}
            onCambio={(v) => setModo(v as "existente" | "nuevo")}
          />
          {modo === "existente" ? (
            <div style={{ marginTop: "1rem" }}>
              <label className={estilos.etiquetaCampo} htmlFor="usuario">
                Usuario
              </label>
              <select id="usuario" className={estilos.selector} value={usuarioId} onChange={(e) => setUsuarioId(e.target.value)}>
                {usuarios.usuarios.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.nombre}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <fieldset className={estilos.grupoCampos} style={{ marginTop: "1rem" }}>
              <legend className={estilos.etiquetaCampo}>
                ¿Qué te gusta? <Provisional>regla de juguete</Provisional>
              </legend>
              <div className={estilos.opciones}>
                {perfil.preferencias.map((p) => (
                  <label key={p.id} className={estilos.opcion}>
                    <input type="checkbox" checked={elegidas.includes(p.id)} onChange={() => alternar(p.id)} />
                    <span>
                      {p.etiqueta}
                      <small>{p.descripcion}</small>
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>
          )}
          <ControlNumerico
            etiqueta="Destinos a recomendar (K)"
            ayuda="Cuántos destinos mostrar en la lista de recomendaciones."
            minimo={1}
            maximo={kMax}
            paso={1}
            valor={Math.min(k, kMax)}
            onCambio={setK}
          />
        </aside>

        <div className={estilos.bloque}>
          {modo === "existente" && (
            <section aria-labelledby="historial" className={estilos.bloque}>
              <h2 id="historial" className={estilos.subtitulo}>
                Historial de {usuario.nombre}
              </h2>
              <ul className={estilos.lista}>
                {usuario.historial.map((h) => (
                  <li key={h.destino_id} className={estilos.item}>
                    <span className={estilos.itemNombre}>{nombre.get(h.destino_id)}</span>
                    <span className={estilos.itemDato}>Calificación: {h.calificacion} de 5</span>
                  </li>
                ))}
              </ul>
            </section>
          )}
          <section aria-labelledby="recomendados" className={estilos.bloque}>
            <h2 id="recomendados" className={estilos.subtitulo}>
              Destinos recomendados
            </h2>
            {recomendaciones === null ? (
              <p className={estilos.nota}>Elige al menos una preferencia para ver recomendaciones.</p>
            ) : (
              <ol className={estilos.lista}>
                {recomendaciones.map((r, i) => (
                  <li key={r.destino_id} className={estilos.item}>
                    <span className={estilos.puesto}>{i + 1}</span>
                    <span className={estilos.itemNombre}>{nombre.get(r.destino_id)}</span>
                    <span className={estilos.itemDato}>Puntaje {formatearNumero(r.puntaje, 2)}</span>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </div>
      </div>
    </>
  );
}
