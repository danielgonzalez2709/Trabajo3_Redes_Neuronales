"""M2 — partición sin fuga por grupos de casi duplicados (JO-3; docs/spec/partes/jose.md §3.2, D3–D5; Anexo M2, tarea 3).

Uso: ``.venv/bin/python run.py m2-datos --config configs/m2/particion.yaml`` (``datos.main`` delega aquí cuando la config
trae ``etapa: particion``). Lee las imágenes 224x224 versionadas y ``indice.csv``; no necesita el .zip. Escribe:
  ``data/processed/m2/indice.csv``          mismas filas, columnas y orden; llena ``grupo_duplicado`` y ``split``
  ``results/data/m2/particion/resumen.json``  método, umbrales, conteos, huellas, versiones, tiempo; ``tiempo_camara``
        (marcas por formato, pares por tiempo) y ``fuga_residual`` (lo que la partición no separa, medido)
  ``results/data/m2/particion/pares_cercanos.csv``  todos los pares con arista (id_a, id_b, hamming, coseno, segundos,
        criterio ∈ {hamming, coseno, ambos, tiempo}, clases); ``segundos`` = diferencia de marcas de tiempo (vacío sin marca)
  ``results/data/m2/particion/frontera.csv``  pares justo dentro y justo fuera de cada umbral (figura de src/viz/figs_m2.py)
  ``results/data/m2/eda/calidad.csv``       + filas ``casi_duplicado_entre_clases`` (D4: misma escena, otra acción; no se corrige)
  ``results/data/m2/eda/procesado.json``    ``sha256_indice`` actualizado al nuevo indice.csv
  ``<caché>.tiempos.json``  (no versionado) tiempo y dispositivo de la última extracción sin caché

Partición (D4 + D7 [DECIDIDO, José, 28-nov]: estratificación por el CONTEO DE CLASES de cada grupo):
  N_c = imágenes de la clase c; p_k = proporción del split k; n_kc = imágenes de c ya asignadas a k;
  d_kc = p_k·N_c − n_kc  (déficit);   v_g = (v_g1, …, v_gC) = conteo de clases del grupo g.
  1. los grupos se barajan con ``make_rng(semilla, run_id)`` y se ordenan de mayor a menor tamaño (orden estable);
  2. cada grupo va a  k* = argmax_k Σ_c v_gc · d_kc  (empate: train, validacion, prueba) y se suma v_g a n_k*.
  Por qué: ‖d_k − v_g‖² − ‖d_k‖² = ‖v_g‖² − 2·v_g·d_k, así que k* es el split cuya asignación MENOS aumenta el error cuadrático
  total F = Σ_k Σ_c d_kc² (voraz sobre F).
  Lo que está demostrado:
    (a) Σ_k d_kc = r_c ≥ 0 (imágenes de c aún sin asignar), luego máx_k v_g·d_k ≥ v_g·r/3 ≥ 0: el split elegido nunca tiene
        déficit ponderado negativo.
    (b) Si todos los grupos son de una sola clase (v_g = s_g·e_c), la regla es k* = argmax_k d_kc y solo los grupos de c
        mueven d_·c; como Σ_k d_kc ≥ 0, el déficit máximo es ≥ 0 al asignar y queda ≥ −s_g; al final Σ_k d_kc = 0 y cada
        d_kc ≥ −s_max(c), luego  |n_kc − p_k·N_c| ≤ 2·s_max(c)  (cota de la versión anterior, independiente del orden).
  Con grupos de clases mezcladas NO hay una cota por clase demostrada: se comprueba empíricamente (tests/test_fuga_m2.py:
  desviación ≤ 1σ de una partición al azar por imagen, σ_kc = sqrt(p_k(1−p_k)/N_c)). En los datos reales se reporta la
  proporción obtenida por clase en ``resumen.json``.
  Se elige el voraz (y no StratifiedGroupKFold) porque 70/15/15 no es un número entero de pliegues iguales y los grupos tienen
  tamaños muy distintos (de 1 a cientos de imágenes).

Fuga: la semilla solo desempata grupos de igual tamaño; un grupo entero va a un único split, así que ningún par con arista
puede cruzar splits (se comprueba antes de escribir). No hay id de conductor (D5): la limitación queda en ``resumen.json``.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.comun.results import save_json
from src.comun.seeds import make_rng, validar_entero
from src.m2_conduccion import duplicados
from src.m2_conduccion.datos import PATRONES_NOMBRE

SPLITS = ("train", "validacion", "prueba")
COLUMNAS_INDICE = ["id", "archivo", "clase", "grupo_duplicado", "split", "ancho", "alto"]
COLUMNAS_PARES = ["id_a", "id_b", "hamming", "coseno", "segundos", "criterio", "clase_a", "clase_b"]
COLUMNAS_FRONTERA = ["panel", "lado", "id_a", "id_b", "hamming", "coseno", "arista", "clase_a", "clase_b", "archivo_a",
                     "archivo_b"]
COLUMNAS_HALLAZGOS = ["categoria", "elemento", "valor", "detalle"]
CATEGORIA_ENTRE_CLASES = "casi_duplicado_entre_clases"
DECIMALES_COSENO = 6
DECIMALES_SEGUNDOS = 3                 # las marcas de tiempo tienen milisegundos
TOLERANCIA_SUMA = 1e-9
SIN_DIGITO_SIGUIENTE = r"(?!\d)"        # fin de una marca de tiempo: no sigue otro dígito


# --------------------------------------------------------------------------- partición por grupo
def _validar_proporciones(proporciones: dict) -> np.ndarray:
    if list(proporciones) != list(SPLITS):
        raise ValueError(f"proporciones debe tener exactamente {list(SPLITS)} en ese orden; llegó {list(proporciones)}")
    p = np.array([float(proporciones[k]) for k in SPLITS])
    if (p <= 0).any() or abs(p.sum() - 1.0) > TOLERANCIA_SUMA:
        raise ValueError(f"las proporciones deben ser positivas y sumar 1; llegó {dict(zip(SPLITS, p))}")
    return p


def asignar_split(df: pd.DataFrame, proporciones: dict, semilla: int, run_id: int = 0) -> pd.Series:
    """Split de cada fila de ``df`` (columnas ``grupo_duplicado`` y ``clase``) por la regla vectorial de D7 (docstring del
    módulo): k* = argmax_k Σ_c v_gc·(p_k·N_c − n_kc). No usa el azar global; no depende del orden de las filas."""
    p = _validar_proporciones(proporciones)
    rng = make_rng(semilla, run_id)
    v = pd.crosstab(df["grupo_duplicado"], df["clase"])                    # v_gc: filas = grupos, columnas = clases
    v = v.reindex(index=sorted(v.index), columns=sorted(v.columns))
    tam = v.sum(axis=1).to_numpy()
    orden = rng.permutation(len(v))                                       # desempate al azar entre grupos de igual tamaño
    orden = orden[np.argsort(-tam[orden], kind="stable")]                 # de mayor a menor tamaño
    conteos = v.to_numpy().astype(float)
    objetivo = p[:, None] * conteos.sum(axis=0)[None, :]                  # p_k·N_c
    asignado = np.zeros_like(objetivo)                                    # n_kc
    destino = np.empty(len(v), dtype=object)
    for g in orden:
        k = int(np.argmax((objetivo - asignado) @ conteos[g]))            # Σ_c d_kc·v_gc; argmax: el primero si hay empate
        asignado[k] += conteos[g]
        destino[g] = SPLITS[k]
    return df["grupo_duplicado"].map(dict(zip(v.index, destino))).rename("split")


def _desviacion_en_sigmas(df: pd.DataFrame, proporciones: dict) -> float:
    """máx_{c,k} |n_kc/N_c − p_k| / sqrt(p_k(1−p_k)/N_c) (informativo para resumen.json)."""
    peor = 0.0
    for c, g in df.groupby("clase"):
        for k, prop in proporciones.items():
            peor = max(peor, abs(float((g["split"] == k).mean()) - prop) / float(np.sqrt(prop * (1 - prop) / len(g))))
    return peor


def grupos_en_varios_splits(grupos: pd.Series, split: pd.Series) -> int:
    return int((pd.DataFrame({"g": grupos.to_numpy(), "s": split.to_numpy()}).groupby("g")["s"].nunique() > 1).sum())


def pares_que_cruzan(split: pd.Series, pares) -> int:
    """Pares (etiquetas de índice de ``split``) cuyos dos miembros están en splits distintos."""
    pares = list(pares)
    if not pares:
        return 0
    a, b = zip(*pares)
    return int((split.loc[list(a)].to_numpy() != split.loc[list(b)].to_numpy()).sum())


def pares_fuera_de_grupo(etiquetas: np.ndarray, pares) -> int:
    """Pares con arista cuyos miembros quedaron en grupos distintos (debe ser 0 si los grupos son las componentes)."""
    return int(sum(etiquetas[i] != etiquetas[j] for i, j in pares))


def huella_particion(df: pd.DataFrame) -> str:
    """SHA-256 del texto ``id,grupo_duplicado,split`` + una línea ``id,grupo,split`` por imagen, ordenadas por id (``\\n``)."""
    filas = df[["id", "grupo_duplicado", "split"]].astype(str).sort_values("id")
    texto = "id,grupo_duplicado,split\n" + "".join(f"{a},{g},{s}\n" for a, g, s in filas.itertuples(index=False))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- config
def formatos_tiempo(cfg: dict) -> list[tuple[str, str]]:
    """[(nombre, patrón)] de ``tiempo.formatos``: ``patron`` propio o ``patron_jo1`` = clave de ``PATRONES_NOMBRE`` de
    ``datos.py`` (se reutiliza la expresión de JO-1 sin copiarla). A los patrones que no terminan en «$» se les agrega
    ``(?!\\d)``: la marca no puede seguir con otro dígito."""
    salida = []
    for f in cfg["tiempo"]["formatos"]:
        if "patron_jo1" in f:
            if f["patron_jo1"] not in PATRONES_NOMBRE:
                raise ValueError(f"tiempo.formatos: patron_jo1 {f['patron_jo1']!r} no está en PATRONES_NOMBRE de datos.py "
                                 f"({sorted(PATRONES_NOMBRE)})")
            patron = PATRONES_NOMBRE[f["patron_jo1"]].pattern
        else:
            patron = f["patron"]
        if not (patron.endswith("$") or patron.endswith(SIN_DIGITO_SIGUIENTE)):
            patron += SIN_DIGITO_SIGUIENTE
        salida.append((f["nombre"], patron))
    return salida


def _validar_cfg(cfg: dict) -> None:
    g, h, c, pa = cfg["grafo"], cfg["hash"], cfg["caracteristicas"], cfg["particion"]
    validar_entero(g["umbral_hamming"], "grafo.umbral_hamming")
    if not 0.0 <= float(g["umbral_coseno"]) <= 1.0:
        raise ValueError(f"grafo.umbral_coseno debe estar en [0, 1]; llegó {g['umbral_coseno']}")
    if not 0.0 < float(g["fraccion_maxima_grupo"]) <= 1.0:
        raise ValueError(f"grafo.fraccion_maxima_grupo debe estar en (0, 1]; llegó {g['fraccion_maxima_grupo']}")
    if h["tam_hash"] ** 2 != duplicados.BITS:
        raise ValueError(f"hash.tam_hash = {h['tam_hash']} no da {duplicados.BITS} bits (D1: pHash de 64 bits)")
    if not isinstance(h["espejo"], bool):
        raise ValueError("hash.espejo debe ser true o false")
    if c["red"] != "resnet18":
        raise ValueError(f"caracteristicas.red = {c['red']!r} no soportada (D2: resnet18)")
    validar_entero(pa["semilla"], "particion.semilla")
    validar_entero(pa["run_id"], "particion.run_id")
    validar_entero(cfg["frontera"]["semilla"], "frontera.semilla")
    validar_entero(cfg["frontera"]["run_id"], "frontera.run_id")
    _validar_proporciones(pa["proporciones"])
    if not cfg["tiempo"].get("formatos"):
        raise ValueError("tiempo.formatos debe tener al menos un formato de nombre con hora (D9)")
    for nombre, patron in formatos_tiempo(cfg):
        if re.compile(patron).groups not in (6, 7):
            raise ValueError(f"tiempo.formatos {nombre!r}: el patrón debe tener 6 o 7 grupos (fecha, hora y ms opcionales)")
    umbral_s = cfg["tiempo"]["umbral_segundos"]
    if isinstance(umbral_s, bool) or not isinstance(umbral_s, (int, float)) or umbral_s < 0:
        raise ValueError(f"tiempo.umbral_segundos debe ser un número >= 0; llegó {umbral_s!r}")


# --------------------------------------------------------------------------- etapas
def _caracteristicas(cfg: dict, carpeta: Path, indice: pd.DataFrame, huella: str) -> tuple[np.ndarray, bool, str]:
    """Desde la caché si vale (mismos ids, pesos e imágenes); si no, con la red congelada desde el archivo local."""
    c = cfg["caracteristicas"]
    ids = indice["id"].tolist()
    cache = Path(c["cache"])
    clave = {"red": c["red"], "media": c["media"], "desviacion": c["desviacion"]}
    if duplicados.cache_valida(cache, ids, c["sha256_pesos"], huella, **clave):
        return duplicados.leer_cache(cache)["caracteristicas"], True, "cache"
    modelo = duplicados.cargar_resnet18(Path(c["pesos"]), c["sha256_pesos"])
    rutas = [carpeta / a for a in indice["archivo"]]
    z = duplicados.caracteristicas(rutas, modelo, c["media"], c["desviacion"], c["lote"], c["dispositivo"])
    duplicados.guardar_cache(cache, ids, z, c["sha256_pesos"], huella, **clave)
    return z, False, c["dispositivo"]


def _criterio(p: duplicados.Par) -> str:
    """«ambos» = hash y coseno; «tiempo» = solo la marca de tiempo (D9). Si además cumple el tiempo, lo dice ``segundos``."""
    if p.por_hamming and p.por_coseno:
        return "ambos"
    if p.por_hamming or p.por_coseno:
        return "hamming" if p.por_hamming else "coseno"
    return "tiempo"


def _tabla_pares(pares: list[duplicados.Par], ids: np.ndarray, clases: np.ndarray) -> pd.DataFrame:
    filas = [{"id_a": ids[p.i], "id_b": ids[p.j], "hamming": p.hamming, "coseno": f"{p.coseno:.{DECIMALES_COSENO}f}",
              "segundos": "" if p.segundos is None else f"{p.segundos:.{DECIMALES_SEGUNDOS}f}", "criterio": _criterio(p), "clase_a": clases[p.i], "clase_b": clases[p.j]} for p in pares if p.arista]
    return pd.DataFrame(filas, columns=COLUMNAS_PARES).sort_values(["id_a", "id_b"], kind="stable").reset_index(drop=True)


def _frontera(pares: list[duplicados.Par], cfg: dict, ids, clases, archivos) -> pd.DataFrame:
    """~n pares justo dentro y ~n justo fuera de cada umbral; «fuera» = sin arista por ningún criterio. Empates: al azar."""
    n = cfg["frontera"]["n_por_lado"]
    rng = make_rng(cfg["frontera"]["semilla"], cfg["frontera"]["run_id"])
    clave = {(p.i, p.j): r for p, r in zip(pares, rng.random(len(pares)))}
    paneles = {
        ("hamming", "dentro"): sorted((p for p in pares if p.por_hamming), key=lambda p: (-p.hamming, clave[p.i, p.j])),
        ("hamming", "fuera"): sorted((p for p in pares if not p.arista), key=lambda p: (p.hamming, clave[p.i, p.j])),
        ("coseno", "dentro"): sorted((p for p in pares if p.por_coseno), key=lambda p: (p.coseno, clave[p.i, p.j])),
        ("coseno", "fuera"): sorted((p for p in pares if not p.arista), key=lambda p: (-p.coseno, clave[p.i, p.j])),
    }
    filas = []
    for (panel, lado), lista in paneles.items():
        for p in lista[:n]:
            filas.append({"panel": panel, "lado": lado, "id_a": ids[p.i], "id_b": ids[p.j], "hamming": p.hamming,
                          "coseno": f"{p.coseno:.{DECIMALES_COSENO}f}", "arista": p.arista, "clase_a": clases[p.i],
                          "clase_b": clases[p.j], "archivo_a": archivos[p.i], "archivo_b": archivos[p.j]})
    return pd.DataFrame(filas, columns=COLUMNAS_FRONTERA)


def _barrido(pares: list[duplicados.Par], n: int, cfg: dict) -> dict:
    """Cada criterio por separado sobre los umbrales candidatos: pares con arista, grupos y la componente más grande."""
    def resumen(aristas):
        etq = duplicados.componentes(n, aristas)
        tam = np.unique(etq, return_counts=True)[1]
        return {"pares": len(aristas), "grupos": int(len(tam)), "grupo_mas_grande": int(tam.max()),
                "imagenes_en_grupos_de_2_o_mas": int(tam[tam >= 2].sum())}
    b = cfg["barrido"]
    return {"hamming": {str(t): resumen([(p.i, p.j) for p in pares if p.hamming <= t]) for t in b["hamming"]},
            "coseno": {str(t): resumen([(p.i, p.j) for p in pares if p.coseno >= t]) for t in b["coseno"]}}


def _cuantiles(x: np.ndarray, qs) -> dict:
    return {str(q): float(np.quantile(x, q)) for q in qs}


def _distribucion(est: dict, cfg: dict) -> dict:
    qs = cfg["barrido"]["cuantiles"]
    nn_h, nn_c = est["nn_hamming"], est["nn_coseno"]
    return {
        "vecino_mas_cercano_hamming": {"cuantiles": _cuantiles(nn_h, qs),
                                       "conteo_por_distancia": {str(k): int(v) for k, v in
                                                                enumerate(np.bincount(nn_h, minlength=duplicados.BITS + 1)) if v}},
        "vecino_mas_cercano_coseno": {"cuantiles": _cuantiles(nn_c, qs),
                                      "conteo_por_bin_0_01": {f"{est['bordes_coseno'][k]:.2f}": int(v) for k, v in
                                                              enumerate(np.histogram(np.clip(nn_c, 0, 1),
                                                                                     bins=est["bordes_coseno"])[0]) if v}},
        "todos_los_pares_hamming": {str(k): int(v) for k, v in enumerate(est["hist_hamming"]) if v},
        "todos_los_pares_coseno_bin_0_01": {f"{est['bordes_coseno'][k]:.2f}": int(v)
                                            for k, v in enumerate(est["hist_coseno"]) if v},
    }


def _literal_sin_simetrizar(h, hf, pares: list[duplicados.Par], umbral: int) -> int:
    """Aristas por hash que la definición sin simetrizar mín(H(a,b), H(a,f(b))) con a < b NO daría (informativo)."""
    if hf is None:
        return 0
    n = 0
    for p in pares:
        if p.por_hamming:
            lit = min(int(np.bitwise_count(h[p.i] ^ h[p.j])), int(np.bitwise_count(h[p.i] ^ hf[p.j])))
            n += lit > umbral
    return n


def _calidad_con_pares_entre_clases(cal: pd.DataFrame, entre: pd.DataFrame, ruta_pares: Path, detalle: str) -> pd.DataFrame:
    """calidad.csv de JO-1 sin las filas ``casi_duplicado_entre_clases`` previas (idempotente) + las nuevas: una fila
    ``total`` y una por par de clases. La lista completa (decenas de miles de pares en los datos reales) vive en
    ``pares_cercanos.csv`` (clase_a ≠ clase_b), para no inundar la tabla de hallazgos."""
    cal = cal[cal["categoria"] != CATEGORIA_ENTRE_CLASES]
    lista = f"lista completa en {ruta_pares.as_posix()} (filas con clase_a distinta de clase_b)"
    filas = [{"categoria": CATEGORIA_ENTRE_CLASES, "elemento": "total", "valor": len(entre), "detalle": f"{detalle}; {lista}"}]
    for (a, b), g in entre.groupby(["clase_a", "clase_b"]):
        criterios = "; ".join(f"{k} {v}" for k, v in g["criterio"].value_counts().sort_index().items())
        filas.append({"categoria": CATEGORIA_ENTRE_CLASES, "elemento": f"{a}|{b}", "valor": len(g),
                      "detalle": f"por criterio: {criterios}; ejemplo {g.iloc[0]['id_a']}|{g.iloc[0]['id_b']}"})
    return pd.concat([cal, pd.DataFrame(filas, columns=COLUMNAS_HALLAZGOS)], ignore_index=True)


def _bytes_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, lineterminator="\n").encode("utf-8")


def _versiones() -> dict:
    import imagehash
    import PIL
    import torch
    import torchvision

    return {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "pillow": PIL.__version__,
            "imagehash": imagehash.__version__, "torch": torch.__version__, "torchvision": torchvision.__version__}


# --------------------------------------------------------------------------- principal
@dataclass
class Entrada:
    """Lo que se lee antes de calcular (si algo falta o no tiene el formato esperado, se falla aquí, sin escribir)."""
    carpeta: Path
    ruta_indice: Path
    indice: pd.DataFrame
    calidad: pd.DataFrame
    procesado: dict
    huella_imagenes: str
    marcas: list                           # D9: marca de tiempo (ms) por fila de indice.csv, o None
    formatos_marca: list                   # nombre del formato de cada marca, o None


@dataclass
class Calculo:
    """Hashes, características, pares cercanos, grupos y estadísticas; sin escribir nada salvo la caché de características."""
    h: np.ndarray
    hf: np.ndarray | None
    z: np.ndarray
    zn: np.ndarray
    desde_cache: bool
    pares: list
    aristas: list
    etiquetas: np.ndarray
    estadisticas: dict
    tiempos: dict


def _margenes(cfg: dict) -> tuple[int, float]:
    """Cuánto mirar más allá de τ_H y τ_c: lo suficiente para el umbral más laxo del barrido y para los pares «justo fuera»
    de la figura de la frontera (τ_H + margen_hamming, τ_c − margen_coseno)."""
    tau_h, tau_c = int(cfg["grafo"]["umbral_hamming"]), float(cfg["grafo"]["umbral_coseno"])
    b, f = cfg["barrido"], cfg["frontera"]
    margen_h = max(max(b["hamming"]), tau_h + f["margen_hamming"]) - tau_h
    margen_c = tau_c - min(min(b["coseno"]), tau_c - f["margen_coseno"])
    return int(margen_h), max(float(margen_c), 0.0)


def _leer_entradas(cfg: dict) -> Entrada:
    ent, sal = cfg["entrada"], cfg["salida"]
    carpeta = Path(ent["carpeta"])
    ruta_indice = carpeta / ent["indice"]
    indice = pd.read_csv(ruta_indice, dtype=str, keep_default_na=False)
    if list(indice.columns) != COLUMNAS_INDICE or not indice["id"].is_unique:
        raise ValueError(f"{ruta_indice}: columnas {list(indice.columns)} (se esperan {COLUMNAS_INDICE}) o ids repetidos")
    calidad = pd.read_csv(sal["calidad"], dtype=str, keep_default_na=False)
    if list(calidad.columns) != COLUMNAS_HALLAZGOS:
        raise ValueError(f"{sal['calidad']} no tiene las columnas {COLUMNAS_HALLAZGOS}")
    procesado = json.loads(Path(sal["procesado"]).read_text(encoding="utf-8"))
    origen = pd.read_csv(carpeta / ent["origen"], dtype=str, keep_default_na=False)
    if set(origen["id"]) != set(indice["id"]) or not origen["id"].is_unique:
        raise ValueError(f"{carpeta / ent['origen']}: sus ids no son exactamente los de {ruta_indice}")
    formatos = formatos_tiempo(cfg)
    nombres = origen.set_index("id").loc[indice["id"], "archivo_original"]
    mf = [duplicados.marca_y_formato(n, formatos) for n in nombres]
    return Entrada(carpeta, ruta_indice, indice, calidad, procesado,
                   duplicados.huella_imagenes(carpeta, indice["archivo"].tolist()),
                   [None if x is None else x[1] for x in mf], [None if x is None else x[0] for x in mf])


def _calcular_pares_y_grupos(cfg: dict, e: Entrada) -> Calculo:
    """Hashes → características → pares (con márgenes) + pares por marca de tiempo (D9) → componentes → guarda del 15 % →
    estadísticas para los umbrales."""
    g, hc = cfg["grafo"], cfg["hash"]
    t = time.perf_counter()
    hb, hfb = duplicados.hashes_de_archivos([e.carpeta / a for a in e.indice["archivo"]], hc["tam_hash"],
                                            hc["factor_alta_frecuencia"], hc["espejo"])
    h, hf = duplicados.empaquetar(hb), (None if hfb is None else duplicados.empaquetar(hfb))
    t_hash = time.perf_counter() - t
    t = time.perf_counter()
    z, desde_cache, _ = _caracteristicas(cfg, e.carpeta, e.indice, e.huella_imagenes)
    t_feat = time.perf_counter() - t
    t = time.perf_counter()
    zn = duplicados.normalizar_filas(z)
    margen_h, margen_c = _margenes(cfg)
    pares = duplicados.pares_cercanos(h, hf, zn, int(g["umbral_hamming"]), float(g["umbral_coseno"]), int(g["bloque"]),
                                      margen_hamming=margen_h, margen_coseno=margen_c)
    pares = duplicados.unir_pares_por_tiempo(pares, e.marcas, cfg["tiempo"]["umbral_segundos"], h, hf, zn,
                                             int(g["umbral_hamming"]), float(g["umbral_coseno"]))
    aristas = [(p.i, p.j) for p in pares if p.arista]
    etiquetas = duplicados.componentes(len(e.indice), aristas)
    duplicados.verificar_tamano_maximo(etiquetas, float(g["fraccion_maxima_grupo"]))
    est = duplicados.estadisticas_vecinos(h, hf, zn, int(g["bloque"]))
    return Calculo(h, hf, z, zn, desde_cache, pares, aristas, etiquetas, est,
                   {"hash": t_hash, "caracteristicas": t_feat, "grafo": time.perf_counter() - t})


def _comprobar_particion(nuevo: pd.DataFrame, c: Calculo) -> dict:
    """Ningún par con arista entre splits, ningún grupo en dos splits, todo par con arista dentro de un grupo."""
    r = {"pares_que_cruzan_splits": pares_que_cruzan(nuevo["split"], c.aristas),
         "grupos_en_varios_splits": grupos_en_varios_splits(nuevo["grupo_duplicado"], nuevo["split"]),
         "pares_fuera_de_grupo": pares_fuera_de_grupo(c.etiquetas, c.aristas)}
    if any(r.values()):
        raise RuntimeError(f"partición inválida: {r}")
    return r


def _asignar(cfg: dict, e: Entrada, c: Calculo) -> pd.DataFrame:
    pa = cfg["particion"]
    nuevo = e.indice.copy()
    nuevo["grupo_duplicado"] = duplicados.nombrar_grupos(nuevo["id"].tolist(), c.etiquetas)
    nuevo["split"] = asignar_split(nuevo, pa["proporciones"], pa["semilla"], pa["run_id"])
    return nuevo


def _preparar_salidas(cfg: dict, e: Entrada, c: Calculo, nuevo: pd.DataFrame) -> dict:
    """Contenido de cada archivo de salida, en memoria (bytes o dict), con sus huellas: nada se escribe todavía."""
    ids, clases, archivos = (e.indice[k].to_numpy() for k in ("id", "clase", "archivo"))
    res = Path(cfg["salida"]["carpeta"])
    tabla = _tabla_pares(c.pares, ids, clases)
    entre = tabla[tabla["clase_a"] != tabla["clase_b"]]
    b = {"indice": _bytes_csv(nuevo[COLUMNAS_INDICE]), "pares": _bytes_csv(tabla),
         "frontera": _bytes_csv(_frontera(c.pares, cfg, ids, clases, archivos)),
         "calidad": _bytes_csv(_calidad_con_pares_entre_clases(e.calidad, entre, res / "pares_cercanos.csv",
                                                               " ".join(cfg["textos"]["detalle_entre_clases"].split())))}
    sha_indice = hashlib.sha256(b["indice"]).hexdigest()
    procesado = {**e.procesado, "sha256_indice": sha_indice,
                 "sha256_indice_nota": " ".join(cfg["textos"]["nota_procesado"].split())}
    return {"bytes": b, "tabla": tabla, "entre": entre, "procesado": procesado, "sha256_indice": sha_indice,
            "sha256_pares": hashlib.sha256(b["pares"]).hexdigest()}


def _ruta_tiempos(cfg: dict) -> Path:
    cache = Path(cfg["caracteristicas"]["cache"])
    return cache.with_name(cache.name + ".tiempos.json")


def _ultima_sin_cache(cfg: dict, e: Entrada, c: Calculo, total: float) -> dict | None:
    """Tiempo y dispositivo de la última extracción SIN caché: los de esta corrida si no usó la caché; si la usó, los que
    guardó la corrida que la creó (si corresponden a las mismas imágenes y pesos)."""
    car = cfg["caracteristicas"]
    if not c.desde_cache:
        return {"tiempo_caracteristicas_s": round(c.tiempos["caracteristicas"], 1), "tiempo_total_s": round(total, 1),
                "dispositivo": car["dispositivo"], "huella_imagenes": e.huella_imagenes, "sha256_pesos": car["sha256_pesos"]}
    ruta = _ruta_tiempos(cfg)
    if not ruta.is_file():
        return None
    t = json.loads(ruta.read_text(encoding="utf-8"))
    return t if (t.get("huella_imagenes"), t.get("sha256_pesos")) == (e.huella_imagenes, car["sha256_pesos"]) else None


def _resumen_tiempo(cfg: dict, e: Entrada, c: Calculo) -> dict:
    por_t = [p for p in c.pares if p.por_tiempo]
    f = e.formatos_marca
    return {"formatos": dict(formatos_tiempo(cfg)), "fotos_con_marca": sum(t is not None for t in e.marcas),
            "fotos_con_marca_por_formato": {k: int(v) for k, v in Counter(x for x in f if x is not None).most_common()},
            "pares_por_tiempo": len(por_t), "pares_solo_por_tiempo": sum(not (p.por_hamming or p.por_coseno) for p in por_t),
            "pares_por_tiempo_entre_formatos": sum(f[p.i] != f[p.j] for p in por_t),
            "nota": " ".join(cfg["textos"]["nota_tiempo_camara"].split())}


def _etiqueta_decimal(x: float) -> str:
    """0.9 → «0_90»: un decimal de la config como parte de una clave de resumen.json."""
    return f"{x:.2f}".replace(".", "_")


def _fuga_residual_de_split(cfg: dict, e: Entrada, c: Calculo, q: np.ndarray, tr: np.ndarray,
                            marcas_tr: np.ndarray) -> dict:
    """Para las imágenes ``q`` de un split: coseno al vecino más cercano en train (por intervalos), d_H mínima a train y
    fotos con marca que tienen una de train a ≤ s segundos."""
    fr, tau_c, bloque = cfg["fuga_residual"], float(cfg["grafo"]["umbral_coseno"]), int(cfg["grafo"]["bloque"])
    hf_tr = None if c.hf is None else c.hf[tr]
    nn_c = np.concatenate([c.zn[q[a:a + bloque]] @ c.zn[tr].T for a in range(0, len(q), bloque)]).max(axis=1)
    nn_h = np.concatenate([duplicados.distancia_hamming_espejo(c.h[q[a:a + bloque]],
                                                                None if c.hf is None else c.hf[q[a:a + bloque]],
                                                                c.h[tr], hf_tr)
                           for a in range(0, len(q), bloque)]).min(axis=1)
    b = {"n": int(len(q)), "vecino_en_train_coseno_ge_umbral": int((nn_c >= tau_c).sum())}
    for lo, hi in fr["intervalos_coseno"]:
        b[f"vecino_en_train_coseno_{_etiqueta_decimal(lo)}_a_{_etiqueta_decimal(hi)}"] = int(((nn_c >= lo) & (nn_c < hi)).sum())
    b[f"vecino_en_train_coseno_lt_{_etiqueta_decimal(fr['coseno_bajo'])}"] = int((nn_c < fr["coseno_bajo"]).sum())
    b.update({"mediana_coseno_vecino_en_train": float(np.median(nn_c)), "maximo_coseno_vecino_en_train": float(nn_c.max()),
              "minimo_hamming_al_train": int(nn_h.min())})
    con_marca = [k for k in q if e.marcas[k] is not None]
    b["fotos_con_marca"] = len(con_marca)
    b["fotos_con_marca_por_formato"] = {k: int(v) for k, v in Counter(e.formatos_marca[k] for k in con_marca).most_common()}
    dist = [_distancia_a_conjunto(e.marcas[k], marcas_tr) for k in con_marca]
    for seg in fr["segundos_cercania"]:
        b[f"fotos_con_marca_y_una_de_train_a_le_{seg}_s"] = int(sum(d <= seg * 1000 for d in dist))
    return b


def _fuga_residual(cfg: dict, e: Entrada, c: Calculo, nuevo: pd.DataFrame) -> dict:
    """Lo que la partición NO separa, medido sobre validación y prueba (``_fuga_residual_de_split``)."""
    split = nuevo["split"].to_numpy()
    tr = np.flatnonzero(split == "train")
    marcas_tr = np.sort([e.marcas[k] for k in tr if e.marcas[k] is not None])
    salida = {sp: _fuga_residual_de_split(cfg, e, c, np.flatnonzero(split == sp), tr, marcas_tr)
              for sp in ("validacion", "prueba")}
    salida["nota"] = " ".join(cfg["textos"]["nota_fuga_residual"].split())
    return salida


def _distancia_a_conjunto(t: int, ordenadas: np.ndarray) -> float:
    """Menor |t − x| (ms) con x en ``ordenadas`` (inf si está vacío)."""
    if len(ordenadas) == 0:
        return float("inf")
    k = int(np.searchsorted(ordenadas, t))
    return float(min(abs(t - ordenadas[j]) for j in (k - 1, k) if 0 <= j < len(ordenadas)))


def _construir_resumen(cfg: dict, e: Entrada, c: Calculo, nuevo: pd.DataFrame, s: dict, comprobacion: dict,
                       t0: float) -> dict:
    g, pa, sal, car, tx = cfg["grafo"], cfg["particion"], cfg["salida"], cfg["caracteristicas"], cfg["textos"]
    tabla, entre = s["tabla"], s["entre"]
    tam = nuevo.groupby("grupo_duplicado").size()
    g_max = tam.idxmax()
    conteos = nuevo.groupby(["split", "clase"]).size()
    clases = sorted(nuevo["clase"].unique())
    total = time.perf_counter() - t0
    return {
        "tarea": "JO-3 · partición sin fuga por grupos de casi duplicados (Anexo M2, tarea 3; jose.md §3.2)",
        "metodo": " ".join(tx["metodo"].split()),
        "semilla": pa["semilla"], "run_id": pa["run_id"], "semilla_efectiva": pa["semilla"] + pa["run_id"],
        "proporciones": pa["proporciones"],
        "umbrales": {"hamming": int(g["umbral_hamming"]), "coseno": float(g["umbral_coseno"]),
                     "segundos": cfg["tiempo"]["umbral_segundos"],
                     "fraccion_maxima_grupo": float(g["fraccion_maxima_grupo"]),
                     "estado": " ".join(tx["estado_umbrales"].split()),
                     "como_se_eligieron": " ".join(tx["eleccion_umbrales"].split())},
        "hash": cfg["hash"],
        "n_imagenes": len(nuevo), "n_grupos": int(tam.size),
        "distribucion_tamanos": {str(k): int(v) for k, v in sorted(Counter(tam.to_numpy().tolist()).items())},
        "imagenes_en_grupos_de_2_o_mas": int(tam[tam >= 2].sum()),
        "grupo_mas_grande": {"grupo": g_max, "tamano": int(tam.max()), "fraccion": float(tam.max() / len(nuevo)),
                             "por_clase": {k: int(v) for k, v in
                                           nuevo.loc[nuevo["grupo_duplicado"] == g_max, "clase"].value_counts().sort_index().items()}},
        "pares_por_criterio": {"hamming": int((tabla["criterio"] == "hamming").sum()),
                               "coseno": int((tabla["criterio"] == "coseno").sum()),
                               "ambos": int((tabla["criterio"] == "ambos").sum()),
                               "tiempo": int((tabla["criterio"] == "tiempo").sum()), "total": len(tabla)},
        "tiempo_camara": _resumen_tiempo(cfg, e, c),
        "fuga_residual": _fuga_residual(cfg, e, c, nuevo),
        "aristas_hash_por_la_simetrizacion": _literal_sin_simetrizar(c.h, c.hf, c.pares, int(g["umbral_hamming"])),
        "pares_entre_clases": {"total": len(entre),
                               "por_par_de_clases": {f"{a}|{b}": int(v) for (a, b), v in
                                                     entre.groupby(["clase_a", "clase_b"]).size().items()},
                               "donde": f"{Path(sal['calidad']).as_posix()} (categoría {CATEGORIA_ENTRE_CLASES}) y pares_cercanos.csv"},
        "grupos_con_clases_mezcladas": int((nuevo.groupby("grupo_duplicado")["clase"].nunique() > 1).sum()),
        "pares_que_cruzan_splits": comprobacion["pares_que_cruzan_splits"],
        "grupos_en_varios_splits": comprobacion["grupos_en_varios_splits"],
        "conteos_split": {sp: int((nuevo["split"] == sp).sum()) for sp in SPLITS},
        "conteos_split_clase": {sp: {k: int(conteos.get((sp, k), 0)) for k in clases} for sp in SPLITS},
        "proporcion_split_por_clase": {k: {sp: float(conteos.get((sp, k), 0) / (nuevo["clase"] == k).sum()) for sp in SPLITS}
                                       for k in clases},
        "desviacion_maxima_por_clase_en_sigmas": _desviacion_en_sigmas(nuevo, pa["proporciones"]),
        "definicion_desviacion": ("máx_{c,k} |n_kc/N_c − p_k| / sqrt(p_k(1−p_k)/N_c): desviación de la proporción por clase "
                                  "en unidades de la desviación típica de una partición al azar por imagen"),
        "distribucion_para_umbrales": _distribucion(c.estadisticas, cfg),
        "barrido_umbrales": _barrido(c.pares, len(nuevo), cfg),
        "sha256_indice": s["sha256_indice"],
        "huella_particion": huella_particion(nuevo),
        "definicion_huella_particion": ("SHA-256 del texto 'id,grupo_duplicado,split\\n' seguido de una línea "
                                        "'id,grupo_duplicado,split\\n' por imagen, ordenadas por id (UTF-8)"),
        "sha256_pares_cercanos": s["sha256_pares"],
        "huella_imagenes": e.huella_imagenes, "sha256_pesos": car["sha256_pesos"],
        "caracteristicas": {
            "red": car["red"], "pesos": car["pesos"], "dimension": int(c.z.shape[1]), "cache": car["cache"],
            "esta_corrida": {"desde_cache": c.desde_cache, "tiempo_s": round(c.tiempos["caracteristicas"], 1),
                             "dispositivo": "cache" if c.desde_cache else car["dispositivo"]},
            "ultima_extraccion_sin_cache": _ultima_sin_cache(cfg, e, c, total),
            "nota": " ".join(tx["nota_cache"].split())},
        "versiones": _versiones(), "dispositivo": car["dispositivo"],
        "tiempo_s": {**{k: round(v, 1) for k, v in c.tiempos.items()}, "total": round(total, 1)},
        "pie_figura_frontera": " ".join(tx["pie_figura_frontera"].split()),
        "limitacion_conductor": " ".join(tx["limitacion_conductor"].split()),
        "fugas_descartadas": " ".join(tx["fugas_descartadas"].split()),
    }


def _temporal(ruta: Path) -> Path:
    return ruta.with_name(ruta.name + ".tmp")


def _escribir_salidas(cfg: dict, e: Entrada, s: dict, resumen: dict) -> Path:
    """Escribe lo ya calculado y comprobado en dos fases: (1) cada salida a un temporal ``<archivo>.tmp`` (si una falla, se
    borran los temporales y ninguna salida cambia); (2) se renombran los temporales sobre las salidas, uno tras otro
    (``os.replace`` es atómico por archivo, la secuencia de renombres no: si un renombre falla, se borran los temporales
    pendientes y los ya renombrados quedan). Si la corrida extrajo características, guarda
    también su tiempo junto a la caché."""
    res = Path(cfg["salida"]["carpeta"])
    res.mkdir(parents=True, exist_ok=True)
    binarios = {e.ruta_indice: s["bytes"]["indice"], res / "pares_cercanos.csv": s["bytes"]["pares"],
                res / "frontera.csv": s["bytes"]["frontera"], Path(cfg["salida"]["calidad"]): s["bytes"]["calidad"]}
    jsons = {Path(cfg["salida"]["procesado"]): s["procesado"], res / "resumen.json": resumen}
    if not resumen["caracteristicas"]["esta_corrida"]["desde_cache"]:
        jsons[_ruta_tiempos(cfg)] = resumen["caracteristicas"]["ultima_extraccion_sin_cache"]
    temporales: list[tuple[Path, Path]] = []
    try:
        for ruta, contenido in binarios.items():
            _temporal(ruta).write_bytes(contenido)
            temporales.append((_temporal(ruta), ruta))
        for ruta, obj in jsons.items():
            save_json(_temporal(ruta), obj)
            temporales.append((_temporal(ruta), ruta))
    except BaseException:
        for tmp, _ in temporales:
            tmp.unlink(missing_ok=True)
        raise
    for k, (tmp, ruta) in enumerate(temporales):
        try:
            os.replace(tmp, ruta)
        except BaseException:
            for pendiente, _ in temporales[k:]:          # los ya renombrados no se deshacen; los demás se borran
                pendiente.unlink(missing_ok=True)
            raise
    return res


def main(cfg: dict) -> int:
    """Leer → calcular (pares, grupos, guarda del 15 %) → partir → comprobar → preparar todo en memoria → escribir.
    «Todo o nada» cubre el cálculo y las comprobaciones: si algo falla antes de escribir, ninguna salida cambia (la caché de
    características sí se guarda al calcularse: no es una salida). La escritura va a temporales y luego renombra uno a uno
    (ver ``_escribir_salidas``)."""
    t0 = time.perf_counter()
    _validar_cfg(cfg)
    entrada = _leer_entradas(cfg)
    calculo = _calcular_pares_y_grupos(cfg, entrada)
    nuevo = _asignar(cfg, entrada, calculo)
    comprobacion = _comprobar_particion(nuevo, calculo)
    salidas = _preparar_salidas(cfg, entrada, calculo, nuevo)
    resumen = _construir_resumen(cfg, entrada, calculo, nuevo, salidas, comprobacion, t0)
    _imprimir(resumen, _escribir_salidas(cfg, entrada, salidas, resumen))
    return 0


def _imprimir(r: dict, res: Path) -> None:
    print(f"Imágenes {r['n_imagenes']} · grupos {r['n_grupos']} · mayor grupo {r['grupo_mas_grande']['tamano']} "
          f"({100 * r['grupo_mas_grande']['fraccion']:.2f} %) · umbrales d_H ≤ {r['umbrales']['hamming']}, "
          f"cos ≥ {r['umbrales']['coseno']}")
    print("Pares con arista: " + " · ".join(f"{k} {v}" for k, v in r["pares_por_criterio"].items())
          + f" · entre clases {r['pares_entre_clases']['total']} · cruzan splits {r['pares_que_cruzan_splits']}")
    print("Split: " + " · ".join(f"{k} {v}" for k, v in r["conteos_split"].items()))
    print(f"Huella de la partición {r['huella_particion']} · SHA-256 de indice.csv {r['sha256_indice']}")
    print(f"Tiempo {r['tiempo_s']} · resultados en {res.as_posix()}")
