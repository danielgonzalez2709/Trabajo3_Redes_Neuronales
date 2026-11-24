// Inicio: qué resuelve la app para la empresa de transporte, los tres módulos y los enlaces del proyecto.
import Link from "next/link";
import { Encabezado, Pagina, Pie } from "../components/Marco";
import { URL_REPORTE_TECNICO, URL_REPOSITORIO, URL_VIDEO_PROMOCIONAL, URL_VIDEOS_INDIVIDUALES } from "../lib/enlaces";
import estilos from "./page.module.css";

const MODULOS = [
  {
    ruta: "/demanda",
    modulo: "m1",
    nombre: "Demanda y operación",
    pregunta: "¿Cuántos pasajeros habrá y cuánta flota necesito?",
    texto: "Elige una ruta y mira el pronóstico a 30 días con su banda de incertidumbre, y cuántos despachos, vehículos y conductores hacen falta según tus supuestos.",
  },
  {
    ruta: "/conduccion",
    modulo: "m2",
    nombre: "Conducción distractiva",
    pregunta: "¿El conductor está distraído?",
    texto: "Sube una foto de la cabina: un modelo de visión corre en tu navegador y decide si se dispara una alerta, con el umbral que tú elijas.",
  },
  {
    ruta: "/recomendacion",
    modulo: "m3",
    nombre: "Recomendación de destinos",
    pregunta: "¿A dónde le sugiero viajar?",
    texto: "Mira lo que recomendamos a un usuario existente o arma un perfil nuevo con tus preferencias de viaje.",
  },
];

interface Enlace {
  etiqueta: string;
  url: string | null;
}

const ENLACES: Enlace[] = [
  { etiqueta: "Reporte técnico (blog)", url: URL_REPORTE_TECNICO },
  { etiqueta: "Repositorio", url: URL_REPOSITORIO },
  { etiqueta: "Video promocional", url: URL_VIDEO_PROMOCIONAL },
  { etiqueta: "Videos de contribución individual", url: URL_VIDEOS_INDIVIDUALES },
];

export default function Inicio() {
  return (
    <Pagina>
      <Encabezado
        titulo="Planea la operación de tu empresa de transporte con redes neuronales"
        descripcion="Una empresa de transporte intermunicipal necesita anticipar la demanda, cuidar la seguridad en carretera y ofrecer mejores viajes. Esta aplicación reúne tres herramientas que corren en tu navegador, sin enviar datos a ningún servidor."
      />
      <ul className={estilos.modulos}>
        {MODULOS.map((m) => (
          <li key={m.ruta}>
            <Link href={m.ruta} className={`${estilos.tarjeta} ${estilos[m.modulo]}`}>
              <h2 className={estilos.nombre}>{m.nombre}</h2>
              <p className={estilos.pregunta}>{m.pregunta}</p>
              <p className={estilos.texto}>{m.texto}</p>
              <span className={estilos.ir}>
                Abrir <span aria-hidden="true">→</span>
              </span>
            </Link>
          </li>
        ))}
      </ul>

      <section aria-labelledby="mas">
        <h2 id="mas" className={estilos.subtitulo}>
          Más sobre el proyecto
        </h2>
        <ul className={estilos.enlaces}>
          {ENLACES.map((e) => (
            <li key={e.etiqueta}>
              {e.url ? (
                <a className={estilos.enlace} href={e.url} target="_blank" rel="noopener noreferrer">
                  {e.etiqueta}
                  <span aria-hidden="true">↗</span>
                  <span className="oculta"> (se abre en otra pestaña)</span>
                </a>
              ) : (
                <span className={estilos.pendiente} aria-disabled="true">
                  {e.etiqueta} (pendiente)
                </span>
              )}
            </li>
          ))}
        </ul>
      </section>
      <Pie />
    </Pagina>
  );
}
