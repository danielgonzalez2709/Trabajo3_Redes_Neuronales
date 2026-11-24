"""Genera los JSON y el ONNX de JUGUETE de la app (DA-5; núcleo §5.4, §5.6 y §5.8).

Todo lo que escribe lleva ``"juguete": true``: son datos ficticios para desarrollar y probar la app, **no** resultados de
los modelos reales. Los entregables reales (Camila, José y Juan José) reemplazan estos archivos con el mismo esquema
(documentado en ``app/lib/contratos.ts``).

- M1: serie SINTÉTICA (``data/sintetico/m1``), pronóstico ingenuo estacional con cuantiles empíricos y la función de
  dimensionamiento PROVISIONAL (la real es la de Camila, §5.4).
- M2: CNN diminuta con la misma forma que tendrá la real (entrada RGB normalizada; salidas ``logits`` y ``mapas``; cabeza
  GAP + lineal), pesos aleatorios con semilla, exportada con ``torch.onnx.export`` y verificada con onnxruntime.
- M3: destinos y usuarios FICTICIOS y una regla de recomendación de juguete para el perfil nuevo.

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

VERSION = 1
SEMILLA = 20261124
SALIDA_POR_DEFECTO = RAIZ / "app" / "public" / "model"

# ----------------------------------------------------------------------------------------------------- M1
CUANTILES = [0.5, 0.75, 0.9, 0.95]
HORIZONTE = 30
DIAS_HISTORIA = 90
SEMANAS_BASE = 4  # semanas de la misma jornada que promedia el pronóstico ingenuo estacional

# Parámetros de la función de dimensionamiento PROVISIONAL (juguete; la real es la de Camila, núcleo §5.4).
PARAMETROS_OPERACION = {
    "capacidad_pasajeros": 40,  # asientos por vehículo (supuesto de juguete)
    "ocupacion_objetivo": 0.8,
    "cuantil": 0.9,
    "viajes_por_vehiculo_dia": 2,  # supuesto de juguete: ida y regreso en el día
    "conductores_por_vehiculo": 1.5,  # supuesto de juguete: relevos
}
EPS = 1e-9


def dimensionar_juguete(demanda: float, params: dict) -> dict:
    """PROVISIONAL (juguete). despachos = ceil(demanda / (capacidad * ocupación)); vehículos = ceil(despachos / viajes por
    vehículo y día); conductores = ceil(vehículos * conductores por vehículo). Se resta ``EPS`` antes de ``ceil`` para que
    el ruido de coma flotante no cambie el resultado; la versión de TypeScript hace exactamente lo mismo."""
    despachos = max(0, math.ceil(demanda / (params["capacidad_pasajeros"] * params["ocupacion_objetivo"]) - EPS))
    vehiculos = math.ceil(despachos / params["viajes_por_vehiculo_dia"] - EPS)
    conductores = math.ceil(vehiculos * params["conductores_por_vehiculo"] - EPS)
    return {"despachos": despachos, "vehiculos": vehiculos, "conductores": conductores}


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


def generar_m1(salida: Path) -> None:
    datos = pd.read_parquet(RAIZ / "data" / "sintetico" / "m1" / "demanda_diaria.parquet")
    datos["fecha"] = pd.to_datetime(datos["fecha"])
    rutas_yaml = yaml.safe_load((RAIZ / "data" / "sintetico" / "m1" / "rutas.yaml").read_text(encoding="utf-8"))
    nombres = {r["ruta_id"]: r for r in rutas_yaml["rutas"]}
    origen = datos["fecha"].max()
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
    pronosticos = {
        "version": VERSION,
        "juguete": True,
        "aviso": "Serie sintética y pronóstico ingenuo estacional: no son los modelos reales (núcleo §5.11).",
        "modelo": "ingenuo estacional (juguete)",
        "fecha_origen": origen.date().isoformat(),
        "horizonte": HORIZONTE,
        "cuantiles": CUANTILES,
        "rutas": rutas,
    }
    _escribir(salida / "m1" / "pronosticos.json", pronosticos, compacto=True)

    controles = [
        {"clave": "ocupacion_objetivo", "tipo": "numero", "etiqueta": "Ocupación objetivo", "minimo": 0.5, "maximo": 1.0,
         "paso": 0.05, "defecto": PARAMETROS_OPERACION["ocupacion_objetivo"], "unidad": "fracción de la capacidad",
         "ayuda": "Fracción de los asientos que se busca ocupar por despacho. Más alta: menos despachos, menos holgura."},
        {"clave": "cuantil", "tipo": "opciones", "etiqueta": "Cuantil usado", "opciones": CUANTILES,
         "defecto": PARAMETROS_OPERACION["cuantil"], "unidad": "",
         "ayuda": "Cuantil del pronóstico que se usa como demanda. Más alto: más prudente (más flota)."},
        {"clave": "capacidad_pasajeros", "tipo": "numero", "etiqueta": "Capacidad por vehículo", "minimo": 20, "maximo": 60,
         "paso": 1, "defecto": PARAMETROS_OPERACION["capacidad_pasajeros"], "unidad": "pasajeros",
         "ayuda": "Pasajeros que caben en un vehículo (supuesto de juguete)."},
    ]
    rng = make_rng(SEMILLA, 1)
    casos = []
    combos = [(0, 0.8), (1, 0.5), (39, 0.8), (40, 1.0), (1234.5, 0.65), (500, 0.9), (88.8, 0.75)]
    combos += [(float(round(rng.uniform(0, 3000), 1)), float(rng.choice([0.5, 0.6, 0.7, 0.8, 0.9, 1.0]))) for _ in range(5)]
    for demanda, ocupacion in combos:
        params = dict(PARAMETROS_OPERACION, ocupacion_objetivo=ocupacion)
        casos.append({"entrada": {"demanda": demanda, "parametros": params}, "salida": dimensionar_juguete(demanda, params)})
    operacion = {
        "version": VERSION,
        "juguete": True,
        "aviso": "Función de dimensionamiento PROVISIONAL de juguete; la real es la de Camila (núcleo §5.4), en DA-6.",
        "funcion": "dimensionar_juguete",
        "parametros": PARAMETROS_OPERACION,
        "controles": controles,
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

    fijar_semillas(SEMILLA)
    red, torch = _definir_red()
    red.eval()
    carpeta = salida / "m2"
    (carpeta / "ejemplos").mkdir(parents=True, exist_ok=True)

    ruta_onnx = carpeta / "modelo.onnx"
    muestra = torch.zeros(1, 3, TAMANO, TAMANO)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)  # exportador clásico (TorchScript), el estable aquí
        torch.onnx.export(
            red, (muestra,), str(ruta_onnx), input_names=["entrada"], output_names=["logits", "mapas"],
            dynamic_axes={"entrada": {0: "lote"}, "logits": {0: "lote"}, "mapas": {0: "lote"}},
            opset_version=17, dynamo=False,
        )

    rng = make_rng(SEMILLA, 2)
    media = np.array(MEDIA, dtype=np.float32)[:, None, None]
    desv = np.array(DESVIACION, dtype=np.float32)[:, None, None]

    def normalizar(rgb: np.ndarray) -> np.ndarray:  # (alto, ancho, 3) uint8 -> (1, 3, alto, ancho) float32
        x = rgb.astype(np.float32).transpose(2, 0, 1) / 255.0
        return ((x - media) / desv)[None].astype(np.float32)

    sesion = ort.InferenceSession(str(ruta_onnx), providers=["CPUExecutionProvider"])
    pesos = red.cabeza.weight.detach().numpy().astype(np.float64)
    sesgo = red.cabeza.bias.detach().numpy().astype(np.float64)
    casos = []
    for i in range(4):
        rgb = _imagen_sintetica(rng, TAMANO, i)
        x = normalizar(rgb)
        with torch.no_grad():
            logits_t, mapas_t = red(torch.from_numpy(x))
        probs_t = torch.softmax(logits_t, dim=1).numpy()[0]
        logits_o, mapas_o = sesion.run(["logits", "mapas"], {"entrada": x})
        e = np.exp(logits_o[0] - logits_o[0].max())
        probs_o = e / e.sum()
        if not (np.allclose(probs_t, probs_o, atol=1e-5) and np.allclose(mapas_t.numpy(), mapas_o, atol=1e-5)):
            raise AssertionError(f"el ONNX no coincide con PyTorch en el caso {i}")
        mapas = mapas_t.numpy()[0].astype(np.float64)  # (canales, h, w)
        k = int(np.argmax(probs_t))
        cam = np.tensordot(pesos[k], mapas, axes=(0, 0))  # CAM de la clase predicha: sum_c w_kc A_c (sin sesgo)
        casos.append({
            "id": f"caso_{i + 1}",
            "entrada_rgb": rgb.reshape(-1).tolist(),  # (alto, ancho, 3) aplanado, uint8
            "logits": [round(float(v), 6) for v in logits_t.numpy()[0]],
            "probabilidades": [round(float(v), 6) for v in probs_t],
            "clase_predicha": k,
            "forma_mapas": list(mapas.shape),
            "mapas": [round(float(v), 6) for v in mapas.reshape(-1)],
            "cam_clase_predicha": [round(float(v), 6) for v in cam.reshape(-1)],
        })

    ejemplos = []
    descripciones = ["Ejemplo sintético A", "Ejemplo sintético B", "Ejemplo sintético C"]
    for i, descripcion in enumerate(descripciones):
        rgb = _imagen_sintetica(make_rng(SEMILLA, 10 + i), 96, i)
        Image.fromarray(rgb, mode="RGB").save(carpeta / "ejemplos" / f"ejemplo_{i + 1}.png", optimize=True)
        ejemplos.append({"id": f"ejemplo_{i + 1}", "archivo": f"ejemplo_{i + 1}.png", "descripcion": descripcion})

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
PREFERENCIAS = [
    ("playa", "Playa y mar", "Sol, arena y agua tibia."),
    ("montana", "Montaña y senderismo", "Caminatas y paisajes de altura."),
    ("historia", "Historia y museos", "Centros históricos y patrimonio."),
    ("gastronomia", "Gastronomía", "Comida local y mercados."),
    ("aventura", "Aventura", "Deportes y actividades de adrenalina."),
    ("naturaleza", "Naturaleza y fauna", "Parques, selva y observación de aves."),
    ("vida_nocturna", "Vida nocturna", "Música, bares y fiesta."),
    ("descanso", "Descanso y spa", "Tranquilidad y bienestar."),
]
NOMBRES_DESTINOS = [
    "Bahía Cristal", "Cerro Alto", "Villa Antigua", "Puerto Sabor", "Cañón Bravo", "Selva Verde", "Ciudad Neón",
    "Lago Sereno", "Isla Coral", "Valle Niebla", "Fortaleza Vieja", "Costa Brisa", "Páramo Claro", "Mercado Grande",
    "Río Salto", "Termas Quietas",
]
K_MAX = 10
K_DEFECTO = 5
PESO_POPULARIDAD = 0.1


def recomendar_perfil_juguete(seleccion: list[str], destinos: list[dict], preferencias_ids: list[str], k: int,
                              peso_popularidad: float) -> list[dict]:
    """Regla de JUGUETE para el perfil nuevo: puntaje = promedio del atributo de cada preferencia elegida + peso *
    popularidad; orden por puntaje descendente y, en empate, por id ascendente. Las preferencias se recorren en el orden
    de ``preferencias_ids`` (no en el orden en que se eligieron), para que la suma en coma flotante sea reproducible."""
    elegidas = [p for p in preferencias_ids if p in set(seleccion)]
    if not elegidas:
        raise ValueError("seleccione al menos una preferencia")
    filas = []
    for d in destinos:
        suma = 0.0
        for p in elegidas:
            suma += d["atributos"][p]
        filas.append({"destino_id": d["id"], "puntaje": suma / len(elegidas) + peso_popularidad * d["popularidad"]})
    filas.sort(key=lambda f: (-f["puntaje"], f["destino_id"]))
    return filas[:k]


def generar_m3(salida: Path) -> None:
    rng = make_rng(SEMILLA, 3)
    ids_pref = [p[0] for p in PREFERENCIAS]
    destinos = []
    for i, nombre in enumerate(NOMBRES_DESTINOS):
        atributos = {p: round(float(rng.beta(0.7, 0.9)), 2) for p in ids_pref}
        destinos.append({
            "id": f"D{i + 1:02d}",
            "nombre": f"{nombre} (ficticio)",
            "atributos": atributos,
            "popularidad": round(float(rng.uniform(0.1, 1.0)), 2),
            "embedding_2d": [round(float(v), 3) for v in rng.normal(0, 1, 2)],
        })
    _escribir(salida / "m3" / "destinos.json", {
        "version": VERSION, "juguete": True,
        "aviso": "Destinos ficticios con atributos aleatorios (núcleo §5.8). No describen lugares reales.",
        "destinos": destinos,
    })

    por_id = {d["id"]: d for d in destinos}
    usuarios = []
    for u in range(8):
        n = int(rng.integers(3, 7))  # <= 6 vistos: quedan >= 10 candidatos (K_MAX)
        vistos = sorted(rng.choice(len(destinos), size=n, replace=False).tolist())
        historial = [{"destino_id": destinos[j]["id"], "calificacion": int(rng.integers(1, 6))} for j in vistos]
        # Perfil del usuario = atributos de lo que vio, ponderados por la calificación (regla de juguete).
        perfil = {p: sum(h["calificacion"] * por_id[h["destino_id"]]["atributos"][p] for h in historial)
                  / sum(h["calificacion"] for h in historial) for p in ids_pref}
        vistos_ids = {h["destino_id"] for h in historial}
        candidatos = []
        for d in destinos:
            if d["id"] in vistos_ids:
                continue
            candidatos.append({"destino_id": d["id"],
                               "puntaje": round(sum(perfil[p] * d["atributos"][p] for p in ids_pref) / len(ids_pref), 6)})
        candidatos.sort(key=lambda f: (-f["puntaje"], f["destino_id"]))
        usuarios.append({"id": f"U{u + 1:02d}", "nombre": f"Usuario ficticio {u + 1:02d}", "historial": historial,
                         "top_k": candidatos[:K_MAX]})
    _escribir(salida / "m3" / "usuarios.json", {
        "version": VERSION, "juguete": True,
        "aviso": "Usuarios ficticios; el top-K está precomputado con una regla de juguete (núcleo §5.8).",
        "k_max": K_MAX, "usuarios": usuarios,
    })

    casos = []
    rng2 = make_rng(SEMILLA, 4)
    for n in (1, 1, 2, 3, 3, 5, 8):
        seleccion = [ids_pref[j] for j in sorted(rng2.choice(len(ids_pref), size=n, replace=False).tolist())]
        k = int(rng2.integers(3, K_MAX + 1))
        casos.append({"preferencias": seleccion, "k": k,
                      "top_k": recomendar_perfil_juguete(seleccion, destinos, ids_pref, k, PESO_POPULARIDAD)})
    _escribir(salida / "m3" / "perfil_nuevo.json", {
        "version": VERSION, "juguete": True,
        "aviso": "Regla de recomendación de JUGUETE para el perfil nuevo; la real la define Juan José (JJ, núcleo §5.8).",
        "preferencias": [{"id": i, "etiqueta": e, "descripcion": d} for i, e, d in PREFERENCIAS],
        "regla": {"tipo": "afinidad_media_juguete", "peso_popularidad": PESO_POPULARIDAD,
                  "descripcion": "puntaje = promedio del atributo de cada preferencia elegida + peso_popularidad * popularidad"},
        "k_defecto": K_DEFECTO, "k_max": K_MAX,
        "casos_paridad": casos,
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
    parser.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO, help="carpeta que recibe m1/, m2/ y m3/")
    args = parser.parse_args(argv)
    generar(args.salida)
    print(f"Juguetes escritos en {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
