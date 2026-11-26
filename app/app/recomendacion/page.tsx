"use client";
// Recomendación (M3): usuario existente (historial + top-K precomputado) o perfil nuevo armado con una lista de preferencias
// que pasa por la torre de usuario del recomendador (lib/recomendar.ts). En DA-5 los pesos son de JUGUETE; los reales llegan en DA-8.
import { useMemo, useState } from "react";
import { ControlNumerico } from "../../components/ControlNumerico";
import { Aviso, AvisoJuguete, Encabezado, Pagina, Pie, Provisional } from "../../components/Marco";
import { Segmentado } from "../../components/Segmentado";
import { useCarga } from "../../hooks/useCarga";
import {
  validarCasosM3, validarCoherenciaM3, validarDestinos, validarPerfilNuevo, validarUsuarios, type DestinosJson, type PerfilNuevoJson,
  type RecomendacionM3, type SeleccionM3, type UsuariosJson,
} from "../../lib/contratos";
import { cargarJson } from "../../lib/datos";
import { formatearNumero } from "../../lib/formato";
import { nombresParaMostrar, recomendarPerfil } from "../../lib/recomendar";
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
  const casos = await cargarJson("m3/casos_paridad.json", (raiz, archivo) => validarCasosM3(raiz, perfil, archivo));
  validarCoherenciaM3(destinos, usuarios, perfil, casos);
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
  const [seleccion, setSeleccion] = useState<SeleccionM3>({});
  const [k, setK] = useState(perfil.k_defecto);
  const nombre = useMemo(() => nombresParaMostrar(destinos.destinos), [destinos]);
  const usuario = usuarios.usuarios.find((u) => u.id === usuarioId) ?? usuarios.usuarios[0];
  const kMax = Math.min(perfil.k_max, usuarios.k_max, destinos.destinos.length);
  const kUso = Math.min(k, kMax); // el K que se usa en todo: nunca más que el máximo

  const recomendaciones: RecomendacionM3[] | null = useMemo(() => {
    if (modo === "existente") return usuario.top_k.slice(0, kUso);
    if (Object.values(seleccion).every((v) => v.length === 0)) return null;
    return recomendarPerfil(seleccion, perfil.preferencias, perfil.torre_usuario, destinos.destinos, kUso).top_k;
  }, [modo, usuario, seleccion, kUso, destinos, perfil]);

  const alternar = (prefId: string, opId: string) =>
    setSeleccion((s) => {
      const actual = Object.hasOwn(s, prefId) ? s[prefId] : [];
      return { ...s, [prefId]: actual.includes(opId) ? actual.filter((x) => x !== opId) : [...actual, opId] };
    });
  const juguete = destinos.juguete || usuarios.juguete || perfil.juguete;

  return (
    <>
      {juguete && <AvisoJuguete detalle="Los destinos y los usuarios son ficticios y el recomendador tiene pesos aleatorios; no son resultados del recomendador real." />}
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
            <div className={estilos.grupoSeparado}>
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
            <div className={estilos.grupoSeparado}>
              <p className={estilos.etiquetaCampo}>
                ¿Qué te gusta? {juguete && <Provisional>modelo de juguete</Provisional>}
              </p>
              {perfil.preferencias.map((pref) => (
                <fieldset key={pref.id} className={`${estilos.grupoCampos} ${estilos.opcionesGrupo}`}>
                  <legend className={estilos.nota}>{pref.etiqueta}</legend>
                  <div className={estilos.opciones}>
                    {pref.opciones.map((o) => (
                      <label key={o.id} className={estilos.opcion}>
                        <input
                          type="checkbox"
                          checked={Object.hasOwn(seleccion, pref.id) && seleccion[pref.id].includes(o.id)}
                          onChange={() => alternar(pref.id, o.id)}
                        />
                        <span>
                          {o.etiqueta}
                          {o.descripcion && <small>{o.descripcion}</small>}
                        </span>
                      </label>
                    ))}
                  </div>
                </fieldset>
              ))}
            </div>
          )}
          <ControlNumerico
            etiqueta="Destinos a recomendar (K)"
            ayuda="Cuántos destinos mostrar en la lista de recomendaciones."
            minimo={1}
            maximo={kMax}
            paso={1}
            valor={kUso}
            onCambio={setK}
          />
        </aside>

        <div className={estilos.bloque}>
          {modo === "existente" && (
            <section aria-labelledby="historial" className={estilos.bloque}>
              <h2 id="historial" className={estilos.subtitulo}>
                Historial de {usuario.nombre}
              </h2>
              {usuario.historial.length === 0 ? (
                <p className={estilos.nota}>Este usuario todavía no tiene historial: las recomendaciones se calculan sin él.</p>
              ) : (
                <ul className={estilos.lista}>
                  {usuario.historial.map((h) => (
                    <li key={h.destino_id} className={estilos.item}>
                      <span className={estilos.itemNombre}>{nombre.get(h.destino_id)}</span>
                      <span className={estilos.itemDato}>Calificación: {h.calificacion} de 5</span>
                    </li>
                  ))}
                </ul>
              )}
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
            <p className={estilos.nota}>{modo === "existente" ? usuarios.modelo : perfil.modelo}</p>
          </section>
        </div>
      </div>
    </>
  );
}
