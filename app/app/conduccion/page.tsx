"use client";
// Conducción distractiva (M2): sube una imagen o elige un ejemplo; el ONNX corre en el navegador (onnxruntime-web, con los
// .wasm servidos desde la propia app). El mapa de interpretabilidad (CAM) llega en DA-7: aquí queda su espacio reservado.
import { useCallback, useEffect, useRef, useState } from "react";
import { ControlNumerico } from "../../components/ControlNumerico";
import { Aviso, AvisoJuguete, Encabezado, Pagina, Pie, Provisional } from "../../components/Marco";
import { FilaTarjetas, TarjetaResultado } from "../../components/TarjetaResultado";
import { useCarga } from "../../hooks/useCarga";
import { decidirAlerta } from "../../lib/clasificar";
import { validarMetaM2, type MetaM2 } from "../../lib/contratos";
import { cargarJson, urlModelo } from "../../lib/datos";
import { formatearPorcentaje } from "../../lib/formato";
import { aRgb, cargarImagen } from "../../lib/imagen";
import { ejecutarModelo, type SalidaModelo } from "../../lib/onnx";
import estilos from "../modulo.module.css";

const cargar = () => cargarJson("m2/meta.json", validarMetaM2);

export default function Conduccion() {
  const carga = useCarga(cargar);
  return (
    <Pagina>
      <Encabezado
        titulo="Conducción distractiva"
        descripcion="Sube una imagen de la cabina (o elige un ejemplo). El modelo estima qué está haciendo el conductor y decide si se dispara una alerta según el umbral que elijas. La imagen no sale de tu navegador."
      />
      {carga.estado === "cargando" && <Aviso tipo="carga">Cargando el modelo…</Aviso>}
      {carga.estado === "error" && <Aviso tipo="error">{carga.mensaje}</Aviso>}
      {carga.estado === "listo" && <Contenido meta={carga.datos} />}
      <Pie />
    </Pagina>
  );
}

type Estado = { fase: "inicio" } | { fase: "procesando" } | { fase: "error"; mensaje: string } | { fase: "listo"; salida: SalidaModelo };

function Contenido({ meta }: { meta: MetaM2 }) {
  const [umbral, setUmbral] = useState(meta.umbral_por_defecto);
  const [vista, setVista] = useState<string | null>(null); // URL de la imagen mostrada
  const [elegido, setElegido] = useState<string | null>(null); // id del ejemplo elegido
  const [estado, setEstado] = useState<Estado>({ fase: "inicio" });
  const ultimo = useRef(0);

  const clasificar = useCallback(
    async (origen: File | string, urlVista: string) => {
      const turno = ++ultimo.current;
      setVista(urlVista);
      setEstado({ fase: "procesando" });
      try {
        const img = await cargarImagen(origen);
        const rgb = aRgb(img, meta.tamano_entrada.alto, meta.tamano_entrada.ancho);
        const salida = await ejecutarModelo(meta, rgb);
        if (turno === ultimo.current) setEstado({ fase: "listo", salida });
      } catch (e) {
        if (turno === ultimo.current) setEstado({ fase: "error", mensaje: e instanceof Error ? e.message : String(e) });
      }
    },
    [meta],
  );

  const elegirEjemplo = useCallback(
    (id: string) => {
      const e = meta.ejemplos.find((x) => x.id === id);
      if (!e) return;
      const url = urlModelo(`m2/ejemplos/${e.archivo}`);
      setElegido(id);
      void clasificar(url, url);
    },
    [meta, clasificar],
  );

  // Al abrir la página se clasifica el primer ejemplo, para que haya algo que ver sin hacer nada.
  useEffect(() => {
    if (meta.ejemplos.length > 0) elegirEjemplo(meta.ejemplos[0].id);
  }, [meta, elegirEjemplo]);

  const alSubir = (archivo: File | undefined) => {
    if (!archivo) return;
    setElegido(null);
    void clasificar(archivo, URL.createObjectURL(archivo));
  };

  const salida = estado.fase === "listo" ? estado.salida : null;
  const decision = salida ? decidirAlerta(salida.probabilidades, meta, umbral) : null;
  const clase = salida ? meta.clases[salida.claseIndice] : null;

  return (
    <>
      {meta.juguete && <AvisoJuguete detalle="El modelo es una red diminuta con pesos aleatorios: la forma es la del modelo real, pero sus respuestas no significan nada." />}
      <div className={estilos.bloque}>
        <section className={estilos.panel} aria-labelledby="titulo-entrada">
          <h2 id="titulo-entrada" className={estilos.panelTitulo}>
            1. Elige una imagen
          </h2>
          <div className={estilos.miniaturas} role="group" aria-label="Imágenes de ejemplo">
            {meta.ejemplos.map((e) => (
              <button key={e.id} type="button" className={estilos.miniatura} aria-pressed={elegido === e.id} onClick={() => elegirEjemplo(e.id)}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={urlModelo(`m2/ejemplos/${e.archivo}`)} alt="" />
                {e.descripcion}
              </button>
            ))}
          </div>
          <p>
            <label className={estilos.etiquetaCampo} htmlFor="archivo">
              O sube la tuya
            </label>
            <input id="archivo" className={estilos.archivo} type="file" accept="image/*" onChange={(ev) => alSubir(ev.target.files?.[0])} />
          </p>
        </section>

        <section aria-labelledby="titulo-resultado" aria-live="polite" className={estilos.bloque}>
          <h2 id="titulo-resultado" className={estilos.subtitulo}>
            2. Resultado
          </h2>
          {estado.fase === "procesando" && <Aviso tipo="carga">Analizando la imagen…</Aviso>}
          {estado.fase === "error" && <Aviso tipo="error">{estado.mensaje}</Aviso>}
          <div className={estilos.vista}>
            {vista && (
              // eslint-disable-next-line @next/next/no-img-element
              <img className={estilos.imagen} src={vista} alt="Imagen analizada" />
            )}
            <div className={estilos.reservado} role="img" aria-label="Espacio reservado para el mapa de interpretabilidad">
              <p>
                <strong>Mapa de interpretabilidad (CAM)</strong>
                <br />
                Llega en DA-7: mostrará en qué zona de la imagen se apoya el modelo.
              </p>
            </div>
          </div>
          {salida && clase && decision && (
            <>
              <FilaTarjetas>
                <TarjetaResultado
                  titulo="Clase asignada"
                  valor={clase.nombre}
                  detalle={`Probabilidad ${formatearPorcentaje(salida.probabilidades[salida.claseIndice])}.`}
                />
                <TarjetaResultado
                  titulo="Decisión de alerta"
                  valor={decision.grupo === "con_alerta" ? "Con alerta" : "Sin alerta"}
                  tono={decision.grupo === "con_alerta" ? "alerta" : "ok"}
                  detalle={`Probabilidad de comportamiento de riesgo ${formatearPorcentaje(decision.probabilidad)}; umbral ${formatearPorcentaje(umbral, 0)}.`}
                />
              </FilaTarjetas>
              <div className={estilos.panel}>
                <h3 className={estilos.panelTitulo}>Probabilidad de cada clase</h3>
                <ul className={estilos.barras}>
                  {meta.clases.map((c, i) => (
                    <li key={c.id} className={`${estilos.barraFila} ${i === salida.claseIndice ? estilos.barraAsignada : ""}`}>
                      <span>
                        {c.nombre}
                        <br />
                        <span className={estilos.grupoTexto}>{meta.grupo_alerta[c.id] === "con_alerta" ? "con alerta" : "sin alerta"}</span>
                      </span>
                      <span className={estilos.barraPista} aria-hidden="true">
                        <span className={estilos.barraRelleno} style={{ display: "block", width: `${(salida.probabilidades[i] * 100).toFixed(1)}%` }} />
                      </span>
                      <span className={estilos.barraValor}>{formatearPorcentaje(salida.probabilidades[i])}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </section>

        <section className={estilos.panel} aria-labelledby="titulo-umbral">
          <h2 id="titulo-umbral" className={estilos.panelTitulo}>
            3. Umbral de alerta {meta.grupo_alerta_provisional && <Provisional>agrupación provisional</Provisional>}
          </h2>
          <ControlNumerico
            etiqueta="Umbral"
            ayuda="Se dispara la alerta si la probabilidad de que el conductor esté en una de las clases con alerta es igual o mayor que este valor. Más bajo: más alertas y más falsas alarmas; más alto: menos alertas y más distracciones sin detectar."
            minimo={0}
            maximo={1}
            paso={0.01}
            valor={umbral}
            onCambio={setUmbral}
          />
          <p className={estilos.nota}>
            Sin alerta: {meta.clases.filter((c) => meta.grupo_alerta[c.id] === "sin_alerta").map((c) => c.nombre).join(", ")}. Con
            alerta: {meta.clases.filter((c) => meta.grupo_alerta[c.id] === "con_alerta").map((c) => c.nombre).join(", ")}.
          </p>
        </section>
      </div>
    </>
  );
}
