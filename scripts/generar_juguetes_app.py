"""Genera los JSON y el ONNX de JUGUETE de la app (DA-5; núcleo §5.4, §5.6 y §5.8).

Todo lo que escribe lleva ``"juguete": true``: son datos ficticios para desarrollar y probar la app, **no** resultados de
los modelos reales. Los entregables reales (Camila, José y Juan José) reemplazan estos archivos con el mismo esquema
(documentado en ``app/lib/contratos.ts``).

- M1: serie SINTÉTICA (``data/sintetico/m1``), pronóstico ingenuo estacional con cuantiles empíricos y la función de
  dimensionamiento PROVISIONAL (la real es la de Camila, §5.4) con parámetros ``{valor, unidad, supuesto | fuente}``.
- M2: CNN diminuta con la misma forma que tendrá la real (entrada RGB normalizada; salidas ``logits`` y ``mapas``; cabeza
  GAP + lineal), pesos aleatorios con semilla, exportada con ``torch.onnx.export`` y verificada con onnxruntime.
- M3: destinos y usuarios FICTICIOS y un recomendador de dos torres (MLP de usuario y embedding por destino) con pesos
  aleatorios con semilla, en el formato general que usará el real (§5.8).

Por defecto escribe en ``app/tests/fixtures/juguete/``: el juguete es un FIXTURE versionado de las pruebas de la app y
**no** toca ``app/public/model/``, donde viven los archivos que sirve la app (los dueños de módulo los reemplazan por sus
exportaciones reales). Para volver a servir el juguete a propósito (sobrescribe lo que haya ahí, sea real o no):
``--salida app/public/model``.

Uso: ``.venv\\Scripts\\python scripts/generar_juguetes_app.py [--salida app/public/model]``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.comun.seeds import fijar_semillas, make_rng  # noqa: E402

VERSION = 2  # versión del esquema de los archivos (2: parámetros con fuente, dos torres, preprocesado de M2)
SEMILLA = 20261124
SALIDA_POR_DEFECTO = RAIZ / "app" / "tests" / "fixtures" / "juguete"  # fixture de pruebas, NO lo que sirve la app

# ----------------------------------------------------------------------------------------------------- M1
CUANTILES = [0.5, 0.75, 0.9, 0.95]
HORIZONTE = 30
DIAS_HISTORIA = 90
SEMANAS_BASE = 4  # semanas de la misma jornada que promedia el pronóstico ingenuo estacional
EPS = 1e-9
NOTA_JUGUETE = "Supuesto de juguete: no viene de ninguna norma ni dato."


def _param(valor: float, unidad: str, nota: str = NOTA_JUGUETE) -> dict:
    """Parámetro del contrato §5.4: ``{valor, unidad, fuente | supuesto: true, nota?}``. En el juguete todos son supuestos
    (citar una fuente que no se ha leído sería inventarla); los reales de Camila llevan ``fuente`` con la cita textual."""
    return {"valor": valor, "unidad": unidad, "supuesto": True, "nota": nota}


# Clases de vehículo FICTICIAS del juguete (las reales salen de la columna de clase de vehículo de la fuente).
CLASES_VEHICULO = ["bus", "buseta"]
CAPACIDADES = {"bus": 40, "buseta": 24}
# Por ruta (en el orden de las rutas del pronóstico): tiempo de ciclo (ida + regreso + espera) y composición por clase.
TIEMPO_CICLO_H = [6.0, 6.0, 9.0, 9.0]
COMPOSICION = [(0.7, 0.3), (0.7, 0.3), (0.5, 0.5), (0.5, 0.5)]


def parametros_operacion(rutas_ids: list[str]) -> dict:
    """Estructura ``parametros`` de ``m1/operacion.json``: ``globales``, ``por_ruta``, ``por_clase`` y
    ``composicion_clases`` (participación de cada clase de vehículo por ruta; la real se estima solo con train)."""
    return {
        "globales": {
            "ocupacion_objetivo": _param(0.8, "fracción de la capacidad"),
            "cuantil": _param(0.9, "cuantil del pronóstico"),
            "viajes_por_vehiculo_dia": _param(
                2, "viajes por vehículo y día",
                "Supuesto de juguete: tope de viajes que hace un vehículo en el día (ida y regreso cuentan como dos)."),
            "conductores_por_vehiculo": _param(
                1.5, "conductores por vehículo",
                "Supuesto de juguete: relevos; conductores = ceil(vehículos · este valor)."),
            "horas_operacion_dia": _param(16, "horas", "Supuesto de juguete: horas al día en que opera la ruta."),
        },
        "por_ruta": {
            r: {"tiempo_ciclo_h": _param(TIEMPO_CICLO_H[i], "horas", "Supuesto de juguete: ida, regreso y esperas.")}
            for i, r in enumerate(rutas_ids)
        },
        "por_clase": {c: {"capacidad_pasajeros": _param(CAPACIDADES[c], "pasajeros")} for c in CLASES_VEHICULO},
        "composicion_clases": {
            r: {c: _param(COMPOSICION[i][j], "fracción de los despachos", "Supuesto de juguete (la real se estima con train).")
                for j, c in enumerate(CLASES_VEHICULO)}
            for i, r in enumerate(rutas_ids)
        },
    }


def parametros_efectivos(parametros: dict, ruta_id: str, cambios: dict[str, float] | None = None) -> dict[str, float]:
    """Aplana los parámetros de UNA ruta a ``{referencia: valor}`` con las referencias del contrato:
    ``globales.<clave>``, ``por_ruta.<clave>`` (de la ruta dada), ``por_clase.<clase>.<clave>`` y
    ``composicion_clases.<clase>`` (de la ruta dada). ``cambios`` pisa valores por referencia (lo que mueve el usuario)."""
    plano: dict[str, float] = {}
    for clave, par in parametros["globales"].items():
        plano[f"globales.{clave}"] = par["valor"]
    for clave, par in parametros["por_ruta"][ruta_id].items():
        plano[f"por_ruta.{clave}"] = par["valor"]
    for clase, pars in parametros["por_clase"].items():
        for clave, par in pars.items():
            plano[f"por_clase.{clase}.{clave}"] = par["valor"]
    for clase, par in parametros["composicion_clases"][ruta_id].items():
        plano[f"composicion_clases.{clase}"] = par["valor"]
    plano.update(cambios or {})
    return plano


def dimensionar_juguete(demanda: float, p: dict[str, float]) -> dict:
    """PROVISIONAL (juguete). Parámetros efectivos planos (ver ``parametros_efectivos``).

    capacidad_media = Σ_clase composición · capacidad (clases en orden alfabético, para que la suma en coma flotante sea
    reproducible); asientos_utiles = capacidad_media · ocupación objetivo; despachos = ceil(demanda / asientos_utiles);
    viajes_efectivos = max(1, min(viajes por vehículo y día, floor(horas de operación / tiempo de ciclo)));
    vehículos = ceil(despachos / viajes_efectivos); conductores = ceil(vehículos · conductores por vehículo).
    Se resta ``EPS`` antes de cada ``ceil`` (y se suma antes de cada ``floor``) para que el ruido de coma flotante no cambie
    el resultado; la versión de TypeScript hace exactamente lo mismo. Devuelve también los pasos intermedios."""
    clases = sorted(k.split(".", 1)[1] for k in p if k.startswith("composicion_clases."))
    if not clases:
        raise ValueError("faltan las composiciones por clase")
    ocupacion = p["globales.ocupacion_objetivo"]
    viajes = p["globales.viajes_por_vehiculo_dia"]
    por_vehiculo = p["globales.conductores_por_vehiculo"]
    horas = p["globales.horas_operacion_dia"]
    ciclo = p["por_ruta.tiempo_ciclo_h"]
    if not (ocupacion > 0 and viajes > 0 and por_vehiculo > 0 and horas > 0 and ciclo > 0):
        raise ValueError("parámetros fuera de rango")
    if not (math.isfinite(demanda) and demanda >= 0):
        raise ValueError("la demanda debe ser un número >= 0")
    capacidad_media = 0.0
    for c in clases:
        capacidad_media += p[f"composicion_clases.{c}"] * p[f"por_clase.{c}.capacidad_pasajeros"]
    if not capacidad_media > 0:
        raise ValueError("la capacidad media debe ser positiva")
    asientos_utiles = capacidad_media * ocupacion
    despachos = max(0, math.ceil(demanda / asientos_utiles - EPS))
    viajes_efectivos = max(1, min(math.floor(viajes + EPS), math.floor(horas / ciclo + EPS)))
    vehiculos = math.ceil(despachos / viajes_efectivos - EPS)
    conductores = math.ceil(vehiculos * por_vehiculo - EPS)
    return {
        "despachos": despachos, "vehiculos": vehiculos, "conductores": conductores,
        "pasos": {"capacidad_media": capacidad_media, "asientos_utiles": asientos_utiles, "viajes_efectivos": viajes_efectivos},
    }


def _pronostico_ingenuo(historia: pd.Series, origen: dt.date) -> list[dict]:
    """Ingenuo estacional: el punto de cada día es el promedio de ese mismo día de la semana en las últimas
    ``SEMANAS_BASE`` semanas. Cuantiles: ``punto`` + cuantil empírico de los residuos del mismo método sobre la historia."""
    y = historia.copy()
    y.index = pd.to_datetime(y.index)

    def punto_de(fecha: pd.Timestamp, corte: pd.Timestamp) -> float:
        """Promedio de las últimas SEMANAS_BASE ocurrencias de ese día de la semana conocidas hasta ``corte``."""
        m = max(1, math.ceil((fecha - corte).days / 7))
        previos = [y.get(fecha - pd.Timedelta(days=7 * (m + j))) for j in range(SEMANAS_BASE)]
        previos = [v for v in previos if v is not None and not math.isnan(v)]
        return float(np.mean(previos)) if previos else float("nan")

    residuos = []
    for fecha in y.index[7 * SEMANAS_BASE:]:
        p = punto_de(fecha, fecha - pd.Timedelta(days=1))
        if not math.isnan(p):
            residuos.append(float(y[fecha]) - p)
    cuantiles_res = np.quantile(residuos, CUANTILES)
    ultimo = pd.Timestamp(origen)
    filas = []
    for h in range(1, HORIZONTE + 1):
        fecha = ultimo + pd.Timedelta(days=h)
        p = punto_de(fecha, ultimo)  # solo información hasta el origen (no se realimenta con el propio pronóstico)
        filas.append({
            "fecha": fecha.date().isoformat(),
            "h": h,
            "punto": round(max(p, 0.0), 1),
            "q": [round(max(p + float(r), 0.0), 1) for r in cuantiles_res],
        })
    return filas


def _controles() -> list[dict]:
    """Controles de la interfaz: ``ref`` apunta a un parámetro (ver ``parametros_efectivos``); los dos primeros son
    obligatorios en el contrato (el Anexo pide al menos dos parámetros ajustables: ocupación objetivo y cuantil)."""
    return [
        {"ref": "globales.ocupacion_objetivo", "tipo": "numero", "etiqueta": "Ocupación objetivo", "minimo": 0.5, "maximo": 1.0,
         "paso": 0.05,
         "ayuda": "Fracción de los asientos que se busca ocupar por despacho. Más alta: menos despachos, menos holgura."},
        {"ref": "globales.cuantil", "tipo": "opciones", "etiqueta": "Cuantil usado", "opciones": CUANTILES,
         "ayuda": "Cuantil del pronóstico que se usa como demanda. Más alto: más prudente (más flota)."},
        {"ref": "globales.viajes_por_vehiculo_dia", "tipo": "numero", "etiqueta": "Viajes por vehículo al día", "minimo": 1,
         "maximo": 4, "paso": 1,
         "ayuda": "Tope de viajes que hace un vehículo en el día. Más viajes: menos vehículos para los mismos despachos."},
        {"ref": "globales.conductores_por_vehiculo", "tipo": "numero", "etiqueta": "Conductores por vehículo", "minimo": 1,
         "maximo": 3, "paso": 0.1, "ayuda": "Cuántos conductores hacen falta por vehículo para cubrir relevos."},
        {"ref": "globales.horas_operacion_dia", "tipo": "numero", "etiqueta": "Horas de operación al día", "minimo": 8,
         "maximo": 24, "paso": 1, "ayuda": "Horas al día en que opera la ruta; limita cuántos viajes completos caben."},
        {"ref": "por_ruta.tiempo_ciclo_h", "tipo": "numero", "etiqueta": "Tiempo de ciclo de la ruta", "minimo": 2, "maximo": 14,
         "paso": 0.5, "ayuda": "Horas que tarda un viaje completo (ida, regreso y esperas) en la ruta elegida."},
        {"ref": "por_clase.bus.capacidad_pasajeros", "tipo": "numero", "etiqueta": "Capacidad del bus", "minimo": 20,
         "maximo": 60, "paso": 1, "ayuda": "Pasajeros que caben en un bus."},
        {"ref": "por_clase.buseta.capacidad_pasajeros", "tipo": "numero", "etiqueta": "Capacidad de la buseta", "minimo": 10,
         "maximo": 40, "paso": 1, "ayuda": "Pasajeros que caben en una buseta."},
    ]


def generar_m1(salida: Path) -> None:
    datos = pd.read_parquet(RAIZ / "data" / "sintetico" / "m1" / "demanda_diaria.parquet")
    datos["fecha"] = pd.to_datetime(datos["fecha"])
    rutas_yaml = yaml.safe_load((RAIZ / "data" / "sintetico" / "m1" / "rutas.yaml").read_text(encoding="utf-8"))
    nombres = {r["ruta_id"]: r for r in rutas_yaml["rutas"]}
    origen = datos["fecha"].max()  # última fecha de la serie sintética
    rutas = []
    for ruta_id, grupo in datos.groupby("ruta_id", sort=True):
        serie = grupo.set_index("fecha")["pasajeros"].astype(float).sort_index()
        info = nombres[ruta_id]
        cod_o, cod_d = ruta_id.split("-")
        recientes = serie.iloc[-DIAS_HISTORIA:]
        rutas.append({
            "ruta_id": ruta_id,
            "origen": {"codigo": cod_o, "nombre": info["origen_municipio"]},
            "destino": {"codigo": cod_d, "nombre": info["destino_municipio"]},
            "ruta_regreso_id": info["ruta_regreso_id"],
            "historia": [{"fecha": f.date().isoformat(), "pasajeros": int(v)} for f, v in recientes.items()],
            "pronostico": _pronostico_ingenuo(serie, origen.date()),
        })
    ids = [r["ruta_id"] for r in rutas]
    if len(ids) != len(TIEMPO_CICLO_H) or any(r["ruta_regreso_id"] not in ids for r in rutas):
        raise AssertionError("la serie sintética no coincide con los supuestos por ruta del juguete")
    pronosticos = {
        "version": VERSION,
        "juguete": True,
        "aviso": "Serie sintética y pronóstico ingenuo estacional: no son los modelos reales (núcleo §5.11). "
                 "`fecha_origen` es la última fecha de la serie sintética; en la app real será el origen del pronóstico de Andrés.",
        "modelo": "ingenuo estacional (juguete)",
        "fecha_origen": origen.date().isoformat(),
        "horizonte": HORIZONTE,
        "cuantiles": CUANTILES,
        "rutas": rutas,
    }
    _escribir(salida / "m1" / "pronosticos.json", pronosticos, compacto=True)

    parametros = parametros_operacion(ids)
    rng = make_rng(SEMILLA, 1)
    por_id = {r["ruta_id"]: r for r in rutas}
    casos = []

    def agregar(ruta_id: str, h: int, indice_q: int, cambios: dict[str, float] | None = None, demanda: float | None = None) -> None:
        """Un caso de paridad: el día ``h`` de la ruta, con la demanda del cuantil ``indice_q`` (o una dada) y los parámetros
        efectivos con ``cambios`` encima (el cuantil del caso siempre coincide con ``globales.cuantil``)."""
        dia = por_id[ruta_id]["pronostico"][h - 1]
        d = float(dia["q"][indice_q]) if demanda is None else demanda
        efectivos = parametros_efectivos(parametros, ruta_id, {**(cambios or {}), "globales.cuantil": CUANTILES[indice_q]})
        entrada = {"ruta_id": ruta_id, "fecha": dia["fecha"], "demanda": d, "parametros": efectivos}
        casos.append({"entrada": entrada, "salida": dimensionar_juguete(d, efectivos)})

    agregar(ids[0], 1, 2, demanda=0.0)
    agregar(ids[0], 2, 2, demanda=1.0)
    agregar(ids[1], 3, 2, demanda=41.6)  # asientos útiles = (0,7·40 + 0,3·24) · 0,8 = 27,84: 41,6 -> 2 despachos
    agregar(ids[2], 4, 3, {"globales.ocupacion_objetivo": 1.0}, demanda=32.0)  # (0,5·40 + 0,5·24) · 1 = 32: justo 1 despacho
    for _ in range(10):
        agregar(
            ids[int(rng.integers(0, len(ids)))], int(rng.integers(1, HORIZONTE + 1)), int(rng.integers(0, len(CUANTILES))),
            {
                "globales.ocupacion_objetivo": float(rng.choice([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])),
                "globales.viajes_por_vehiculo_dia": float(rng.integers(1, 5)),
                "globales.conductores_por_vehiculo": float(rng.choice([1.0, 1.2, 1.5, 2.0, 2.5])),
                "por_clase.bus.capacidad_pasajeros": float(rng.integers(25, 56)),
                "por_ruta.tiempo_ciclo_h": float(rng.choice([4.0, 5.5, 6.0, 8.0, 12.0])),
            },
        )
    operacion = {
        "version": VERSION,
        "juguete": True,
        "aviso": "Función de dimensionamiento PROVISIONAL de juguete: todos sus supuestos son parámetros visibles. "
                 "La real es la de Camila (núcleo §5.4), en DA-6.",
        "funcion": "dimensionar_juguete",
        "parametros": parametros,
        "controles": _controles(),
        "casos_paridad": casos,
    }
    _escribir(salida / "m1" / "operacion.json", operacion)


# ----------------------------------------------------------------------------------------------------- M2
CLASES = [
    ("conduccion_segura", "Conducción segura", "sin_alerta"),
    ("giro", "Giro", "con_alerta"),
    ("escribir_telefono", "Escribir en el teléfono", "con_alerta"),
    ("hablar_telefono", "Hablar por teléfono", "con_alerta"),
    ("otros_riesgosos", "Otros comportamientos riesgosos", "con_alerta"),
]
TAMANO = 32  # la entrada real será mayor (p. ej. 224); el juguete es diminuto
CANALES = 8
MEDIA = [0.5, 0.5, 0.5]
DESVIACION = [0.25, 0.25, 0.25]
# Preprocesado declarado en meta.json (contrato §5.6). `preprocesar_imagen` (aquí) y `aRgb` + `redimensionarBilineal` +
# `preprocesar` (app/lib/imagen.ts y app/lib/clasificar.ts) deben hacer exactamente lo mismo.
PREPROCESADO = {
    "redimensionado": "estirar",  # al tamaño de entrada, sin conservar la proporción ni recortar
    "interpolacion": "bilineal",  # filtro triangular con ventana ampliada al reducir (PIL BILINEAR); ver app/lib/imagen.ts
    "canales": "RGB",  # la transparencia se ignora
    "escala": "0-1",  # v / 255
    "normalizacion": "media_desviacion",  # luego (v - media[c]) / desviacion[c] con la media y la desviación del meta
}
MAX_CASOS_M2 = 3


def preprocesar_imagen(imagen) -> np.ndarray:
    """Imagen de PIL -> RGB uint8 (alto, ancho, 3) al tamaño de entrada, como lo hace la app en el navegador:
    RGB (sin transparencia), estirada a TAMANO x TAMANO con interpolación bilineal (PIL BILINEAR, que al reducir promedia
    una ventana proporcional al factor de reducción). La escala 0-1 y la normalización las hace ``normalizar``.
    El mismo procedimiento está en app/lib/imagen.ts: si cambia uno, cambia el otro."""
    from PIL import Image

    return np.asarray(imagen.convert("RGB").resize((TAMANO, TAMANO), Image.Resampling.BILINEAR), dtype=np.uint8)


def _definir_red():
    import torch
    from torch import nn

    class RedJuguete(nn.Module):
        """Misma forma que la real: convoluciones -> mapas de la última convolución -> GAP -> lineal."""

        def __init__(self) -> None:
            super().__init__()
            self.convs = nn.Sequential(
                nn.Conv2d(3, CANALES, 3, stride=2, padding=1), nn.ReLU(),
                nn.Conv2d(CANALES, CANALES, 3, stride=2, padding=1), nn.ReLU(),
            )
            self.cabeza = nn.Linear(CANALES, len(CLASES))

        def forward(self, x):
            mapas = self.convs(x)
            logits = self.cabeza(mapas.mean(dim=(2, 3)))
            return logits, mapas

    return RedJuguete(), torch


def crear_red_juguete():
    """La red de juguete con sus pesos (semilla fija), en modo evaluación: la misma que exporta ``generar_m2``. La usa
    también la prueba CAM ≡ Grad-CAM de tests/test_juguetes_app.py."""
    fijar_semillas(SEMILLA)
    red, torch = _definir_red()
    red.eval()
    return red, torch


def _imagen_sintetica(rng: np.random.Generator, tamano: int, variante: int) -> np.ndarray:
    """Imagen RGB uint8 (alto, ancho, 3) sintética: degradado de fondo y figuras de color. No es una foto de nadie."""
    ys, xs = np.mgrid[0:tamano, 0:tamano] / (tamano - 1)
    base = rng.uniform(40, 215, size=3)
    pendiente = rng.uniform(-60, 60, size=(3, 2))
    img = np.stack([base[c] + pendiente[c, 0] * xs + pendiente[c, 1] * ys for c in range(3)], axis=-1)
    for _ in range(3 + variante):
        cx, cy = rng.uniform(0.15, 0.85, 2)
        r = rng.uniform(0.08, 0.22)
        color = rng.uniform(0, 255, size=3)
        if rng.random() < 0.5:
            mascara = (xs - cx) ** 2 + (ys - cy) ** 2 < r**2
        else:
            mascara = (np.abs(xs - cx) < r) & (np.abs(ys - cy) < r * 0.7)
        img[mascara] = color
    return np.clip(np.rint(img), 0, 255).astype(np.uint8)


def generar_m2(salida: Path) -> None:
    import onnxruntime as ort
    from PIL import Image

    red, torch = crear_red_juguete()
    carpeta = salida / "m2"
    (carpeta / "ejemplos").mkdir(parents=True, exist_ok=True)
    (carpeta / "casos").mkdir(parents=True, exist_ok=True)

    ruta_onnx = carpeta / "modelo.onnx"
    muestra = torch.zeros(1, 3, TAMANO, TAMANO)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)  # exportador clásico (TorchScript), el estable aquí
        torch.onnx.export(
            red, (muestra,), str(ruta_onnx), input_names=["entrada"], output_names=["logits", "mapas"],
            dynamic_axes={"entrada": {0: "lote"}, "logits": {0: "lote"}, "mapas": {0: "lote"}},
            opset_version=17, dynamo=False,
        )

    # Ejemplos de la app: imágenes sintéticas de 96 x 96 (mayores que la entrada: la app tiene que redimensionarlas).
    ejemplos = []
    for i, descripcion in enumerate(["Ejemplo sintético A", "Ejemplo sintético B", "Ejemplo sintético C"]):
        rgb = _imagen_sintetica(make_rng(SEMILLA, 10 + i), 96, i)
        Image.fromarray(rgb).save(carpeta / "ejemplos" / f"ejemplo_{i + 1}.png", optimize=True)
        ejemplos.append({"id": f"ejemplo_{i + 1}", "archivo": f"ejemplo_{i + 1}.png", "descripcion": descripcion})

    rng = make_rng(SEMILLA, 2)
    media = np.array(MEDIA, dtype=np.float32)[:, None, None]
    desv = np.array(DESVIACION, dtype=np.float32)[:, None, None]

    def normalizar(rgb: np.ndarray) -> np.ndarray:  # (alto, ancho, 3) uint8 -> (1, 3, alto, ancho) float32
        x = rgb.astype(np.float32).transpose(2, 0, 1) / 255.0
        return ((x - media) / desv)[None].astype(np.float32)

    sesion = ort.InferenceSession(str(ruta_onnx), providers=["CPUExecutionProvider"])
    pesos = red.cabeza.weight.detach().numpy().astype(np.float64)
    sesgo = red.cabeza.bias.detach().numpy().astype(np.float64)

    def caso(id_: str, rgb: np.ndarray, **extra) -> dict:
        x = normalizar(rgb)
        with torch.no_grad():
            logits_t, mapas_t = red(torch.from_numpy(x))
        probs_t = torch.softmax(logits_t, dim=1).numpy()[0]
        logits_o, mapas_o = sesion.run(["logits", "mapas"], {"entrada": x})
        e = np.exp(logits_o[0] - logits_o[0].max())
        probs_o = e / e.sum()
        if not (np.allclose(probs_t, probs_o, atol=1e-5) and np.allclose(mapas_t.numpy(), mapas_o, atol=1e-5)):
            raise AssertionError(f"el ONNX no coincide con PyTorch en el caso {id_}")
        mapas = mapas_t.numpy()[0].astype(np.float64)  # (canales, h, w)
        k = int(np.argmax(probs_t))
        cam = np.tensordot(pesos[k], mapas, axes=(0, 0))  # CAM de la clase predicha: sum_c w_kc A_c (sin sesgo)
        return {
            "id": id_,
            **extra,
            "logits": [round(float(v), 6) for v in logits_t.numpy()[0]],
            "probabilidades": [round(float(v), 6) for v in probs_t],
            "clase_predicha": k,
            "forma_mapas": list(mapas.shape),
            "mapas": [round(float(v), 6) for v in mapas.reshape(-1)],
            "cam_clase_predicha": [round(float(v), 6) for v in cam.reshape(-1)],
        }

    casos = []
    # caso_1: imagen ya al tamaño de entrada, dentro del propio meta.json.
    rgb1 = _imagen_sintetica(rng, TAMANO, 0)
    casos.append(caso("caso_1", rgb1, entrada_rgb=rgb1.reshape(-1).tolist()))
    # caso_2: ídem, pero la imagen va en un archivo aparte (m2/casos/caso_2.json), como harán los casos grandes.
    rgb2 = _imagen_sintetica(rng, TAMANO, 1)
    _escribir(carpeta / "casos" / "caso_2.json", {"entrada_rgb": rgb2.reshape(-1).tolist()}, compacto=True)
    casos.append(caso("caso_2", rgb2, entrada_archivo="casos/caso_2.json"))
    # caso_3: DESDE UN ARCHIVO DE IMAGEN (no redimensionado): ejemplos/ejemplo_1.png (96 x 96) -> preprocesar_imagen.
    # `entrada_rgb` es lo que resulta de redimensionar con PIL; las probabilidades salen de ahí. La app redimensiona por su
    # cuenta (app/lib/imagen.ts) y la prueba compara con tolerancia (ver app/tests/paridad_onnx.test.ts).
    rgb3 = preprocesar_imagen(Image.open(carpeta / "ejemplos" / "ejemplo_1.png"))
    casos.append(caso("caso_3", rgb3, imagen="ejemplo_1.png", entrada_rgb=rgb3.reshape(-1).tolist()))
    assert len(casos) <= MAX_CASOS_M2

    meta = {
        "version": VERSION,
        "juguete": True,
        "aviso": "CNN diminuta con pesos aleatorios: la forma es la del modelo real, las predicciones no significan nada.",
        "modelo": "cnn diminuta aleatoria (juguete)",
        "archivo_modelo": "modelo.onnx",
        "clases": [{"id": c, "nombre": n} for c, n, _ in CLASES],
        "grupo_alerta": {c: g for c, _, g in CLASES},
        "grupo_alerta_provisional": True,
        "umbral_por_defecto": 0.5,
        "tamano_entrada": {"alto": TAMANO, "ancho": TAMANO},
        "preprocesado": PREPROCESADO,
        "media": MEDIA,
        "desviacion": DESVIACION,
        "entrada_onnx": "entrada",
        "salidas_onnx": {"logits": "logits", "mapas": "mapas"},
        "pesos_cabeza": [[round(float(v), 8) for v in fila] for fila in pesos],
        "sesgo_cabeza": [round(float(v), 8) for v in sesgo],
        "ejemplos": ejemplos,
        "casos_paridad": casos,
    }
    _escribir(carpeta / "meta.json", meta, compacto=True)


# ----------------------------------------------------------------------------------------------------- M3
# Formato general del recomendador de dos torres (núcleo §5.8): la torre de usuario es una lista de capas lineales/MLP que
# transforma el vector de preferencias en un vector u; cada destino trae su embedding v_d y un sesgo opcional;
# puntaje(d) = <u, v_d> + sesgo_d. Aquí los pesos son aleatorios con semilla (juguete): no recomiendan nada con sentido.
PREFERENCIAS = [
    {"id": "actividad", "etiqueta": "¿Qué tipo de plan te atrae?", "opciones": [
        {"id": "playa", "etiqueta": "Playa y mar", "descripcion": "Sol, arena y agua tibia."},
        {"id": "montana", "etiqueta": "Montaña y senderismo", "descripcion": "Caminatas y paisajes de altura."},
        {"id": "historia", "etiqueta": "Historia y museos", "descripcion": "Centros históricos y patrimonio."},
        {"id": "gastronomia", "etiqueta": "Gastronomía", "descripcion": "Comida local y mercados."},
        {"id": "aventura", "etiqueta": "Aventura", "descripcion": "Deportes y actividades de adrenalina."},
        {"id": "naturaleza", "etiqueta": "Naturaleza y fauna", "descripcion": "Parques, selva y observación de aves."},
        {"id": "vida_nocturna", "etiqueta": "Vida nocturna", "descripcion": "Música, bares y fiesta."},
        {"id": "descanso", "etiqueta": "Descanso y spa", "descripcion": "Tranquilidad y bienestar."},
    ]},
    {"id": "ritmo", "etiqueta": "Ritmo del viaje", "opciones": [
        {"id": "tranquilo", "etiqueta": "Tranquilo"},
        {"id": "moderado", "etiqueta": "Moderado"},
        {"id": "intenso", "etiqueta": "Intenso"},
    ]},
    {"id": "compania", "etiqueta": "¿Con quién viajas?", "opciones": [
        {"id": "solo", "etiqueta": "Solo"},
        {"id": "pareja", "etiqueta": "En pareja"},
        {"id": "familia", "etiqueta": "En familia"},
        {"id": "amigos", "etiqueta": "Con amigos"},
    ]},
]
NOMBRES_DESTINOS = [
    "Bahía Cristal", "Cerro Alto", "Villa Antigua", "Puerto Sabor", "Cañón Bravo", "Selva Verde", "Ciudad Neón",
    "Lago Sereno", "Isla Coral", "Valle Niebla", "Fortaleza Vieja", "Costa Brisa", "Páramo Claro", "Mercado Grande",
    "Río Salto", "Termas Quietas",
]
K_MAX = 10
K_DEFECTO = 5
OCULTA = 16  # neuronas de la capa oculta de la torre de usuario
DIM_EMBEDDING = 8
DECIMALES_PESOS = 4  # los pesos se redondean ANTES de calcular, para que Python y TypeScript usen exactamente los mismos


def codificar_seleccion(seleccion: dict[str, list[str]], preferencias: list[dict]) -> np.ndarray:
    """Selección -> vector de entrada de la torre: one-hot por opción (varias a la vez si se eligen varias), preferencias
    en el orden de la lista y, dentro de cada una, opciones en el orden de la lista (la misma que ``app/lib/recomendar.ts``)."""
    conocidas = {p["id"]: {o["id"] for o in p["opciones"]} for p in preferencias}
    for pref_id, ops in seleccion.items():
        if pref_id not in conocidas:
            raise ValueError(f"preferencia desconocida: {pref_id}")
        for o in ops:
            if o not in conocidas[pref_id]:
                raise ValueError(f"opción desconocida en {pref_id}: {o}")
    x: list[float] = []
    for pref in preferencias:
        elegidas = set(seleccion.get(pref["id"], []))  # fuera de la comprensión: se construye una vez por preferencia
        x.extend(1.0 if o["id"] in elegidas else 0.0 for o in pref["opciones"])
    return np.array(x, dtype=np.float64)


def torre_usuario(x: np.ndarray, capas: list[dict]) -> np.ndarray:
    """Pasa ``x`` por las capas: ``h = W h + b`` (W es salida x entrada, como ``torch.nn.Linear.weight``) y ReLU si la
    activación es ``relu``."""
    h = np.asarray(x, dtype=np.float64)
    for capa in capas:
        h = np.asarray(capa["W"], dtype=np.float64) @ h + np.asarray(capa["b"], dtype=np.float64)
        if capa["activacion"] == "relu":
            h = np.maximum(h, 0.0)
    return h


def puntuar(u: np.ndarray, destinos: list[dict], k: int, vistos: set[str]) -> list[dict]:
    """Top-K por puntaje = <u, v_d> + sesgo_d (sesgo 0 si no hay), sin los destinos ``vistos``; empates: id ascendente."""
    filas = [
        {"destino_id": d["id"], "puntaje": float(np.dot(u, np.asarray(d["embedding"], dtype=np.float64))) + d.get("sesgo", 0.0)}
        for d in destinos if d["id"] not in vistos
    ]
    filas.sort(key=lambda f: (-f["puntaje"], f["destino_id"]))
    return filas[:k]


def generar_m3(salida: Path) -> None:
    rng = make_rng(SEMILLA, 3)
    n_entrada = sum(len(p["opciones"]) for p in PREFERENCIAS)
    capas = [
        {"W": np.round(rng.normal(0, 0.5, (OCULTA, n_entrada)), DECIMALES_PESOS).tolist(),
         "b": np.round(rng.normal(0, 0.1, OCULTA), DECIMALES_PESOS).tolist(), "activacion": "relu"},
        {"W": np.round(rng.normal(0, 0.5, (DIM_EMBEDDING, OCULTA)), DECIMALES_PESOS).tolist(),
         "b": np.round(rng.normal(0, 0.1, DIM_EMBEDDING), DECIMALES_PESOS).tolist(), "activacion": "ninguna"},
    ]
    destinos = []
    for i, nombre in enumerate(NOMBRES_DESTINOS):
        destinos.append({
            "id": f"D{i + 1:02d}",
            "nombre": f"{nombre} (ficticio)",
            "embedding": np.round(rng.normal(0, 0.6, DIM_EMBEDDING), DECIMALES_PESOS).tolist(),
            "sesgo": round(float(rng.normal(0, 0.1)), DECIMALES_PESOS),
            "embedding_2d": [round(float(v), 3) for v in rng.normal(0, 1, 2)],
        })
    _escribir(salida / "m3" / "destinos.json", {
        "version": VERSION, "juguete": True,
        "aviso": "Destinos ficticios con embeddings aleatorios (núcleo §5.8). No describen lugares reales.",
        "destinos": destinos,
    })

    por_id = {d["id"]: np.asarray(d["embedding"], dtype=np.float64) for d in destinos}
    usuarios = []
    for u in range(9):
        # El último usuario no tiene historial (arranque en frío): su vector es cero y el puntaje es solo el sesgo.
        n = 0 if u == 8 else int(rng.integers(3, 7))  # <= 6 vistos: quedan >= 10 candidatos (K_MAX)
        vistos = sorted(rng.choice(len(destinos), size=n, replace=False).tolist())
        historial = [{"destino_id": destinos[j]["id"], "calificacion": int(rng.integers(1, 6))} for j in vistos]
        vector = np.zeros(DIM_EMBEDDING)
        for h in historial:  # promedio de los embeddings de lo visto, ponderado por la calificación
            vector += h["calificacion"] * por_id[h["destino_id"]]
        if historial:
            vector /= sum(h["calificacion"] for h in historial)
        top = puntuar(vector, destinos, K_MAX, {h["destino_id"] for h in historial})
        usuarios.append({"id": f"U{u + 1:02d}", "nombre": f"Usuario ficticio {u + 1:02d}", "historial": historial,
                         "top_k": [{"destino_id": f["destino_id"], "puntaje": round(f["puntaje"], 6)} for f in top]})
    _escribir(salida / "m3" / "usuarios.json", {
        "version": VERSION, "juguete": True,
        "aviso": "Usuarios ficticios; el top-K está precomputado con un modelo de juguete (núcleo §5.8).",
        "modelo": "Juguete: el vector del usuario es el promedio de los embeddings de los destinos de su historial, "
                  "ponderado por la calificación (cero si no hay historial); puntaje = <u, v_d> + sesgo_d; el top-K excluye "
                  "los destinos ya vistos.",
        "k_max": K_MAX, "usuarios": usuarios,
    })

    _escribir(salida / "m3" / "perfil_nuevo.json", {
        "version": VERSION, "juguete": True,
        "aviso": "Recomendador de dos torres con pesos ALEATORIOS (juguete); el real lo entrena Juan José (núcleo §5.8).",
        "modelo": "Dos torres (juguete): torre de usuario MLP 15-16-8 con pesos aleatorios y embedding aleatorio por destino.",
        "preferencias": PREFERENCIAS,
        "codificacion": {
            "tipo": "one_hot_por_opcion",
            "dimension": n_entrada,
            "descripcion": "Un 1 por cada opción elegida y un 0 por las demás; las preferencias van en el orden de la lista y, "
                           "dentro de cada una, las opciones en el orden de la lista. Se pueden elegir varias opciones por "
                           "preferencia.",
        },
        "torre_usuario": capas,
        "puntaje": {
            "tipo": "producto_punto_mas_sesgo",
            "excluir_vistos": True,
            "descripcion": "puntaje = <u, v_d> + sesgo_d, con u la salida de la torre de usuario y v_d el embedding del destino; "
                           "el top-K excluye los destinos ya vistos (un perfil nuevo no tiene ninguno).",
        },
        "k_defecto": K_DEFECTO, "k_max": K_MAX,
    })

    rng2 = make_rng(SEMILLA, 4)
    casos = []
    ids_destinos = [d["id"] for d in destinos]
    for n_pref, con_vistos in [(1, False), (1, False), (2, False), (3, False), (3, True), (5, False), (8, True)]:
        seleccion: dict[str, list[str]] = {}
        planas = [(p["id"], o["id"]) for p in PREFERENCIAS for o in p["opciones"]]
        for j in sorted(rng2.choice(len(planas), size=n_pref, replace=False).tolist()):
            seleccion.setdefault(planas[j][0], []).append(planas[j][1])
        k = int(rng2.integers(3, K_MAX + 1))
        vistos = sorted(rng2.choice(ids_destinos, size=3, replace=False).tolist()) if con_vistos else []
        u = torre_usuario(codificar_seleccion(seleccion, PREFERENCIAS), capas)
        top = puntuar(u, destinos, k, set(vistos))
        casos.append({"seleccion": seleccion, "vistos": vistos, "k": k,
                      "vector_usuario": [float(v) for v in u], "top_k": top})
    _escribir(salida / "m3" / "casos_paridad.json", {
        "version": VERSION, "juguete": True,
        "aviso": "Casos selección -> vector de usuario -> top-K calculados con Python (núcleo §5.8).",
        "casos": casos,
    })


# ------------------------------------------------------------------------------------------------- utilidades
def _escribir(ruta: Path, obj: dict, compacto: bool = False) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if compacto:
        texto = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    else:
        texto = json.dumps(obj, ensure_ascii=False, indent=1, allow_nan=False)
    ruta.write_text(texto + "\n", encoding="utf-8", newline="\n")


def generar(salida: Path) -> None:
    """Escribe los juguetes de M1, M2 y M3 en ``salida/{m1,m2,m3}``."""
    salida = Path(salida)
    generar_m1(salida)
    generar_m2(salida)
    generar_m3(salida)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO, help="carpeta que recibe m1/, m2/ y m3/ (por defecto el fixture app/tests/fixtures/juguete; "
                        "app/public/model vuelve a servir el juguete y sobrescribe lo que haya ahí)")
    args = parser.parse_args(argv)
    generar(args.salida)
    print(f"Juguetes escritos en {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
