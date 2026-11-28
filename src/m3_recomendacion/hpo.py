"""M3 — búsqueda de hiperparámetros (JJ-4; D9, D13). ``run.py m3-hpo``.

Optuna (``TPESampler`` con semilla fija, en memoria: sin ``.db``), ``busqueda.n_ensayos`` ensayos (D13: 20), objetivo NDCG@5
medio en VALIDACIÓN con candidatos = catálogo − train (D10). El modelo se ajusta solo con train y la búsqueda **nunca lee
prueba**: ``evaluar_configuracion`` descarta las filas de prueba antes de hacer nada (D9). En todos los ensayos el modelo y
el desempate usan ``make_rng(base_seed, 0)``, así que solo cambian los hiperparámetros.

Registro de búsquedas: ``BUSQUEDAS = {nombre_de_familia: buscar(cfg, inter, catalogo) -> familia}``. Una familia tiene
``n_ensayos``, ``mejor = {numero, params, valor}``, ``tiempo_total_s`` y ``objetivo_nombre`` (p. ej. «ndcg@5»). **JJ-5 agrega la
suya a ``BUSQUEDAS`` con el mismo nombre con que registra su modelo en ``referencias.MODELOS``**: el arnés (``experimento.py``) le
asigna entonces sus hiperparámetros, ``n_configuraciones_busqueda`` y ``tiempo_busqueda_s`` desde ``familias.<nombre>`` de
``hpo_ensayos.json`` (o de la búsqueda corrida en el propio experimento si ``busqueda.ejecutar_en_experimento``).

Escribe ``<salida.carpeta>/hpo_ensayos.json`` = ``{evidencia, familias: {<nombre>: {...}}}``. Si el archivo ya existe con la
misma huella de partición conserva las familias que no se corrieron; si la huella es otra, lo reemplaza. Espacio de la MF:
``busqueda.espacio`` de ``configs/m3/hpo.yaml`` [PROPUESTO por JJ-4].
"""

from __future__ import annotations

import copy
import time
from pathlib import Path

import numpy as np

from src.comun.results import load_json, save_json
from src.comun.seeds import make_rng, validar_entero
from src.m3_recomendacion import metricas, particion
from src.m3_recomendacion.referencias import MFImplicitaALS, sigma_max_train

OBJETIVOS = ("ndcg", "recall")
PARAMETROS_MF = ("factores", "regularizacion", "alfa", "iteraciones")
ARCHIVO = "hpo_ensayos.json"
NOTA_COTA = ("La condición λ ≥ (1 + α)·σ_max(P_train) ⇔ «X = Y = 0 es el único mínimo global» es exacta (si y solo si): "
             "L(X, Y) − L(0, 0) ≥ (λ − (1 + α)σ_max)(‖X‖² + ‖Y‖²), con σ_max la norma espectral (mayor valor singular) de la "
             "matriz binaria usuario × destino de TRAIN, y si λ < (1 + α)σ_max el origen es un punto de silla y existe un mínimo "
             "no nulo. Lo «suficiente, no necesario» es solo el tope del espacio: con α ≥ alfa_min, (1 + α)σ_max ≥ cota = "
             "(1 + alfa_min)·σ_max, así que lambda_max < cota garantiza que ningún punto del espacio colapsa, aunque para α "
             "grandes λ podría llegar más arriba. Además, MFImplicitaALS marca como degenerada la factorización que cumple la "
             "condición exacta, una pérdida final ≥ L(0, 0) o puntajes bajo mf_als.tolerancia_degenerado.")
NOTA_DEGENERADOS = ("Ensayo degenerado (X = Y = 0 o equivalente): λ ≥ (1 + α)σ_max(P_train), o pérdida final ≥ L(0, 0), o "
                    "max|XYᵀ| < mf_als.tolerancia_degenerado; `motivo_degenerado` dice cuál. Se registra, cuenta en el "
                    "presupuesto y nunca es el mejor.")


# =========================================================================== evaluación de una configuración (validación)
def _opciones(cfg: dict) -> tuple[str, int]:
    b = cfg["busqueda"]
    if b["objetivo"] not in OBJETIVOS:
        raise ValueError(f"busqueda.objetivo debe ser uno de {list(OBJETIVOS)}; se recibió {b['objetivo']!r}")
    return b["objetivo"], validar_entero(b["objetivo_k"], "busqueda.objetivo_k", minimo=1)


def evaluar_configuracion(inter, catalogo, params: dict, cfg: dict) -> dict:
    """Ajusta la MF con ``params`` solo con train y mide NDCG@K y Recall@K medios en validación (candidatos = catálogo − train).

    Devuelve ``{"ndcg@K": …, "recall@K": …, "valor": objetivo, "n_usuarios": …, "degenerado": …, "max_abs_puntaje": …,
    "motivo_degenerado": …, "condiciones_degenerado": …}`` para K en ``evaluacion.k`` y en ``busqueda.objetivo_k``
    (``degenerado``: la factorización colapsó a X = Y = 0; ver ``MFImplicitaALS``). Las filas de prueba se descartan al
    entrar: el resultado es idéntico si se alteran o se eliminan (D9: la búsqueda nunca lee prueba)."""
    objetivo, objetivo_k = _opciones(cfg)
    if "split" not in inter.columns:
        raise ValueError("evaluar_configuracion: ``inter`` debe traer la columna split (train / validacion / prueba)")
    inter = inter[inter["split"] != particion.PRUEBA]
    base_seed = cfg["semillas"]["base_seed"]
    ks = sorted(set(metricas.normalizar_k(cfg["evaluacion"]["k"])) | {objetivo_k})
    modelo = MFImplicitaALS(escala_inicial=cfg["mf_als"]["escala_inicial"],
                            tolerancia_degenerado=cfg["mf_als"]["tolerancia_degenerado"], **params)
    modelo.ajustar(inter, catalogo, make_rng(base_seed, 0))
    cands = particion.candidatos(inter, catalogo, particion.VALIDACION)
    rel = particion.relevantes(inter, particion.VALIDACION)
    usuarios = sorted(cands)
    tops = metricas.rankear_usuarios(modelo.puntuar(usuarios), usuarios, catalogo, cands, max(ks), make_rng(base_seed, 0))
    out: dict = {}
    for k in ks:
        out[f"ndcg@{k}"] = metricas.ndcg_medio(tops, rel, usuarios, k)
        out[f"recall@{k}"] = float(np.mean([metricas.recall_en_k(tops[u][0], rel[u], k) for u in usuarios]))
    out["valor"] = out[f"{objetivo}@{objetivo_k}"]
    out["n_usuarios"] = len(usuarios)
    diag = modelo.diagnosticos()
    out["degenerado"], out["max_abs_puntaje"] = bool(diag["degenerado"]), float(diag["max_abs_puntaje"])
    out["motivo_degenerado"], out["condiciones_degenerado"] = diag["motivo_degenerado"], diag["condiciones_degenerado"]
    return out


# =========================================================================== cota de la solución nula
def cota_solucion_nula(inter, catalogo, espacio: dict) -> dict:
    """Cota del tope de λ bajo la cual ningún punto del espacio colapsa a X = Y = 0 (ver ``NOTA_COTA``). Usa SOLO train (D9):
    σ_max = ``referencias.sigma_max_train`` (mayor valor singular de la matriz binaria usuarios-con-train × catálogo);
    alfa_min y lambda_max salen de ``busqueda.espacio``. La derivación completa está en el docstring de ``MFImplicitaALS``."""
    sigma = sigma_max_train(inter, catalogo)
    alfa_min, lambda_max = espacio["alfa"]["min"], espacio["regularizacion"]["max"]
    cota = (1.0 + alfa_min) * sigma
    return {"sigma_max_train": sigma, "alfa_min": alfa_min, "lambda_max": lambda_max, "cota": cota,
            "lambda_max_bajo_la_cota": bool(lambda_max < cota), "nota": NOTA_COTA}


# =========================================================================== búsqueda de la MF
def _validar_espacio(espacio: dict) -> dict:
    faltan, sobran = set(PARAMETROS_MF) - set(espacio), set(espacio) - set(PARAMETROS_MF)
    if faltan or sobran:
        raise ValueError(f"busqueda.espacio debe declarar exactamente {list(PARAMETROS_MF)}; "
                         f"faltan {sorted(faltan)}, sobran {sorted(sobran)}")
    return espacio


def _sugerir(trial, nombre: str, spec: dict):
    """Un parámetro del espacio: ``entero`` / ``real`` (``min``, ``max``, ``log``) o ``categorico`` (``valores``, JJ-5)."""
    tipo = spec["tipo"]
    if tipo == "categorico":
        valores = spec.get("valores")
        if not isinstance(valores, list) or not valores:
            raise ValueError(f"busqueda.espacio.{nombre}: el tipo 'categorico' necesita una lista no vacía `valores`")
        return trial.suggest_categorical(nombre, valores)
    if tipo not in ("entero", "real"):
        raise ValueError(f"busqueda.espacio.{nombre}.tipo debe ser 'entero', 'real' o 'categorico'; se recibió {tipo!r}")
    minimo, maximo, log = spec["min"], spec["max"], bool(spec.get("log", False))
    if tipo == "entero":
        return int(trial.suggest_int(nombre, int(minimo), int(maximo), log=log))
    return float(trial.suggest_float(nombre, float(minimo), float(maximo), log=log))


def _correr_ensayos(cfg: dict, inter, catalogo) -> list[dict]:
    """Los ``busqueda.n_ensayos`` ensayos de Optuna (TPE con semilla fija, en memoria), ordenados por número. Un ensayo
    degenerado se registra y se poda: Optuna lo trata como malo y nunca puede ser el mejor."""
    import optuna

    b = cfg["busqueda"]
    espacio = b["espacio"]
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    sampler = optuna.samplers.TPESampler(seed=validar_entero(b["semilla_sampler"], "busqueda.semilla_sampler"))
    estudio = optuna.create_study(direction="maximize", sampler=sampler)        # sin storage: nada se escribe en disco
    ensayos: list[dict] = []

    def funcion(trial) -> float:
        params = {n: _sugerir(trial, n, espacio[n]) for n in PARAMETROS_MF}
        t = time.perf_counter()
        r = evaluar_configuracion(inter, catalogo, params, cfg)
        ensayos.append({"numero": trial.number, "params": params, "valor": r["valor"], "tiempo_s": time.perf_counter() - t,
                        "degenerado": r["degenerado"], "motivo_degenerado": r["motivo_degenerado"],
                        "condiciones_degenerado": r["condiciones_degenerado"], "max_abs_puntaje": r["max_abs_puntaje"],
                        **{k: v for k, v in r.items() if k.startswith(("ndcg@", "recall@"))}})
        if r["degenerado"]:
            raise optuna.TrialPruned()
        return r["valor"]

    estudio.optimize(funcion, n_trials=validar_entero(b["n_ensayos"], "busqueda.n_ensayos", minimo=1), show_progress_bar=False)
    return sorted(ensayos, key=lambda e: e["numero"])


def _familia(cfg: dict, ensayos: list[dict], cota: dict, tiempo_total_s: float) -> dict:
    """Familia lista para ``hpo_ensayos.json``; error claro si todos los ensayos fueron degenerados."""
    validos = [e for e in ensayos if not e["degenerado"]]
    if not validos:
        raise ValueError(f"los {len(ensayos)} ensayos dieron una factorización degenerada (X = Y = 0, "
                         "λ ≥ (1 + α)·σ_max(P_train), etc.); baja el tope de busqueda.espacio.regularizacion")
    mejor = max(validos, key=lambda e: (e["valor"], -e["numero"]))              # empate: el primero que apareció
    objetivo, objetivo_k = _opciones(cfg)
    b = cfg["busqueda"]
    return {"n_ensayos": len(ensayos), "objetivo_nombre": f"{objetivo}@{objetivo_k}",
            "objetivo": f"{objetivo}@{objetivo_k} medio en validación (candidatos = catálogo − train)",
            "espacio": b["espacio"], "sampler": "TPESampler", "semilla_sampler": b["semilla_sampler"],
            "cota_solucion_nula": cota, "n_degenerados": len(ensayos) - len(validos), "nota_degenerados": NOTA_DEGENERADOS,
            "ensayos": ensayos, "mejor": {"numero": mejor["numero"], "params": mejor["params"], "valor": mejor["valor"]},
            "tiempo_total_s": tiempo_total_s}


def buscar_mf(cfg: dict, inter, catalogo) -> dict:
    """Corre la búsqueda de Optuna de la MF y devuelve la familia ``mf_als`` lista para ``hpo_ensayos.json``."""
    _opciones(cfg)
    espacio = _validar_espacio(cfg["busqueda"]["espacio"])
    cota = cota_solucion_nula(inter, catalogo, espacio)
    if not cota["lambda_max_bajo_la_cota"]:
        print(f"ADVERTENCIA: busqueda.espacio.regularizacion.max = {cota['lambda_max']} ≥ cota {cota['cota']:.4g} = "
              f"(1 + {cota['alfa_min']})·σ_max(P_train) = (1 + {cota['alfa_min']})·{cota['sigma_max_train']:.4g}: "
              "parte del espacio puede colapsar a X = Y = 0 (la guarda de degeneración descarta esos ensayos).")
    inicio = time.perf_counter()
    ensayos = _correr_ensayos(cfg, inter, catalogo)
    return _familia(cfg, ensayos, cota, time.perf_counter() - inicio)


# =========================================================================== búsqueda de la red (JJ-5; D18, D19)
NOTA_DEGENERADOS_RED = ("Ensayo degenerado de la red: puntajes no finitos, puntajes de validación constantes por usuario o "
                        "max‖u‖·max‖v_i‖ < red.tolerancia_degenerado (ver red.diagnostico_degeneracion); `motivo_degenerado` "
                        "dice cuál. Se registra, cuenta en el presupuesto y nunca es el mejor.")


def evaluar_configuracion_red(inter, catalogo, params: dict, cfg: dict) -> dict:
    """Ajusta la red con ``params`` (claves con punto, encima de los bloques de la config) solo con train y parada temprana
    con validación, y mide NDCG@K y Recall@K medios en validación (candidatos = catálogo − train). Igual que la MF: las filas
    de prueba se descartan al entrar y el modelo y el desempate usan ``make_rng(base_seed, 0)`` (D9)."""
    from src.m3_recomendacion.red import fabrica_red               # import tardío: la MF no necesita torch

    objetivo, objetivo_k = _opciones(cfg)
    if "split" not in inter.columns:
        raise ValueError("evaluar_configuracion_red: ``inter`` debe traer la columna split (train / validacion / prueba)")
    inter = inter[inter["split"] != particion.PRUEBA]
    base_seed = cfg["semillas"]["base_seed"]
    ks = sorted(set(metricas.normalizar_k(cfg["evaluacion"]["k"])) | {objetivo_k})
    cfg_ensayo = copy.deepcopy(cfg)
    cfg_ensayo["red"]["hiperparametros"] = dict(params)
    cfg_ensayo["red"]["hiperparametros_desde"] = "ensayo"   # el ensayo manda a propósito: no es un reemplazo que avisar
    modelo = fabrica_red(cfg_ensayo).ajustar(inter, catalogo, make_rng(base_seed, 0))
    cands = particion.candidatos(inter, catalogo, particion.VALIDACION)
    rel = particion.relevantes(inter, particion.VALIDACION)
    usuarios = sorted(cands)
    tops = metricas.rankear_usuarios(modelo.puntuar(usuarios), usuarios, catalogo, cands, max(ks), make_rng(base_seed, 0))
    out: dict = {}
    for k in ks:
        out[f"ndcg@{k}"] = metricas.ndcg_medio(tops, rel, usuarios, k)
        out[f"recall@{k}"] = float(np.mean([metricas.recall_en_k(tops[u][0], rel[u], k) for u in usuarios]))
    out["valor"] = out[f"{objetivo}@{objetivo_k}"]
    out["n_usuarios"] = len(usuarios)
    d = modelo.diagnosticos()
    out.update(degenerado=bool(d["degenerado"]), motivo_degenerado=d["motivo_degenerado"],
               condiciones_degenerado=d["condiciones_degenerado"], mejor_epoca=d["mejor_epoca"],
               epoca_parada=d["epoca_parada"], ndcg5_validacion_mejor=d["ndcg5_validacion_mejor"],
               n_parametros=modelo.n_parametros())
    return out


def _validar_espacio_red(cfg: dict) -> dict:
    """``red.busqueda.espacio`` de ``configs/m3/hpo.yaml``: claves con punto que existen en los bloques de la red."""
    from src.m3_recomendacion.red import BLOQUES

    espacio = cfg.get("red", {}).get("busqueda", {}).get("espacio")
    if not espacio:
        raise ValueError("falta red.busqueda.espacio (configs/m3/hpo.yaml) para la búsqueda de la red")
    validas = {f"{b}.{k}" for b in BLOQUES for k in cfg[b]}
    desconocidas = sorted(set(espacio) - validas)
    if desconocidas:
        raise ValueError(f"red.busqueda.espacio trae claves que no están en los bloques de la red: {desconocidas}")
    return espacio


def _correr_ensayos_red(cfg: dict, inter, catalogo, espacio: dict) -> list[dict]:
    """``busqueda.n_ensayos`` ensayos de Optuna (TPE con ``busqueda.semilla_sampler``, en memoria) sobre el espacio de la red.
    Un ensayo degenerado se registra y se poda (nunca puede ser el mejor)."""
    import optuna

    b = cfg["busqueda"]
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    sampler = optuna.samplers.TPESampler(seed=validar_entero(b["semilla_sampler"], "busqueda.semilla_sampler"))
    estudio = optuna.create_study(direction="maximize", sampler=sampler)
    ensayos: list[dict] = []

    def funcion(trial) -> float:
        params = {n: _sugerir(trial, n, espacio[n]) for n in espacio}
        t = time.perf_counter()
        r = evaluar_configuracion_red(inter, catalogo, params, cfg)
        ensayos.append({"numero": trial.number, "params": params, "valor": r["valor"], "tiempo_s": time.perf_counter() - t,
                        "degenerado": r["degenerado"], "motivo_degenerado": r["motivo_degenerado"],
                        "mejor_epoca": r["mejor_epoca"], "epoca_parada": r["epoca_parada"],
                        "ndcg5_validacion_mejor": r["ndcg5_validacion_mejor"], "n_parametros": r["n_parametros"],
                        **{k: v for k, v in r.items() if k.startswith(("ndcg@", "recall@"))}})
        if r["degenerado"]:
            raise optuna.TrialPruned()
        return r["valor"]

    estudio.optimize(funcion, n_trials=validar_entero(b["n_ensayos"], "busqueda.n_ensayos", minimo=1), show_progress_bar=False)
    return sorted(ensayos, key=lambda e: e["numero"])


def _familia_red(cfg: dict, ensayos: list[dict], tiempo_total_s: float) -> dict:
    """Familia ``red`` lista para ``hpo_ensayos.json``; error claro si todos los ensayos fueron degenerados."""
    validos = [e for e in ensayos if not e["degenerado"]]
    if not validos:
        raise ValueError(f"los {len(ensayos)} ensayos de la red quedaron degenerados; revisa red.busqueda.espacio")
    mejor = max(validos, key=lambda e: (e["valor"], -e["numero"]))              # empate: el primero que apareció
    objetivo, objetivo_k = _opciones(cfg)
    b = cfg["busqueda"]
    return {"n_ensayos": len(ensayos), "objetivo_nombre": f"{objetivo}@{objetivo_k}",
            "objetivo": f"{objetivo}@{objetivo_k} medio en validación (candidatos = catálogo − train)",
            "espacio": cfg.get("red", {}).get("busqueda", {}).get("espacio"), "sampler": "TPESampler",
            "semilla_sampler": b["semilla_sampler"], "n_degenerados": len(ensayos) - len(validos),
            "nota_degenerados": NOTA_DEGENERADOS_RED,
            "nota_parada_temprana": ("Cada ensayo para por NDCG@5 de validación (paciencia de la config) y se evalúa con los "
                                     "pesos de su mejor época: validación elige la época y los hiperparámetros (D9, D19)."),
            "ensayos": ensayos, "mejor": {"numero": mejor["numero"], "params": mejor["params"], "valor": mejor["valor"]},
            "tiempo_total_s": tiempo_total_s}


def buscar_red(cfg: dict, inter, catalogo) -> dict:
    """Corre la búsqueda de Optuna de la red y devuelve la familia ``red`` lista para ``hpo_ensayos.json``."""
    _opciones(cfg)
    espacio = _validar_espacio_red(cfg)
    inicio = time.perf_counter()
    ensayos = _correr_ensayos_red(cfg, inter, catalogo, espacio)
    return _familia_red(cfg, ensayos, time.perf_counter() - inicio)


BUSQUEDAS = {"mf_als": buscar_mf, "red": buscar_red}        # nombre de familia → búsqueda


# =========================================================================== hpo_ensayos.json y comando
def escribir_familia(carpeta, evidencia: dict, nombre: str, familia: dict) -> Path:
    """Agrega/reemplaza la familia ``nombre`` en ``<carpeta>/hpo_ensayos.json``. Si el archivo ya existe con la misma huella
    de partición conserva las demás familias; si la huella es otra, lo reemplaza por completo."""
    ruta = Path(carpeta) / ARCHIVO
    familias: dict = {}
    if ruta.is_file():
        previo = load_json(ruta)
        if previo.get("evidencia", {}).get("particion_huella") == evidencia["particion_huella"]:
            familias = dict(previo.get("familias", {}))
    familias[nombre] = familia
    return save_json(ruta, {"evidencia": evidencia, "familias": familias})


def main(cfg: dict) -> int:
    """``run.py m3-hpo``: corre la búsqueda de cada modelo de ``cfg["modelos"]`` que tenga una registrada en ``BUSQUEDAS``."""
    from src.m3_recomendacion.experimento import cargar_datos            # import tardío: experimento importa este módulo

    nombres = [m for m in cfg["modelos"] if m in BUSQUEDAS]
    if not nombres:
        raise ValueError(f"ningún modelo de cfg['modelos'] = {list(cfg['modelos'])} tiene búsqueda registrada en "
                         f"hpo.BUSQUEDAS {sorted(BUSQUEDAS)}")
    datos = cargar_datos(cfg)
    for nombre in nombres:
        familia = BUSQUEDAS[nombre](cfg, datos["inter"], datos["catalogo"])
        ruta = escribir_familia(cfg["salida"]["carpeta"], datos["evidencia"], nombre, familia)
        print(f"Búsqueda {nombre}: {familia['n_ensayos']} ensayos ({familia.get('n_degenerados', 0)} degenerados) "
              f"en {familia['tiempo_total_s']:.1f} s")
        print(f"  mejor ensayo {familia['mejor']['numero']}: {familia['objetivo_nombre']} = "
              f"{familia['mejor']['valor']:.4f} con {familia['mejor']['params']}")
        print(f"  escrito: {ruta.as_posix()}")
    return 0
