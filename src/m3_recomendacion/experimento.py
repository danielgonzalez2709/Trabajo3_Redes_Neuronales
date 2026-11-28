"""M3 — arnés de evaluación de los modelos (JJ-4; D9–D14). ``run.py m3``.

Para cada modelo de ``cfg["modelos"]`` y cada ``run_id`` en ``range(semillas.n)``: ``rng = make_rng(base_seed, run_id)``;
ajusta con la tabla completa de interacciones (el modelo usa solo ``split == "train"``, D9), puntúa a los usuarios de prueba,
ordena con ``metricas.ordenar_candidatos`` (candidatos D10: catálogo − train − validación; empates al azar con ese mismo
``rng``) y evalúa UNA vez contra los relevantes de prueba. Las mismas métricas y el mismo desempate para todos los modelos.

Punto de extensión (el arnés NO tiene casos especiales por nombre de modelo): **JJ-5 agrega su modelo en ``referencias.MODELOS``
(con ``diagnosticos()``, ``guardar()`` y ``descripcion_frios``; ver ``referencias.Recomendador``) y, si tiene búsqueda de
hiperparámetros, su función en ``hpo.BUSQUEDAS`` con el mismo nombre; luego lo nombra en ``cfg["modelos"]``.** Reglas únicas:
  - Un modelo CON búsqueda toma sus hiperparámetros, ``n_configuraciones_busqueda`` y ``tiempo_busqueda_s`` de
    ``familias.<nombre>`` de ``hpo_ensayos.json`` (o de la búsqueda corrida aquí si ``busqueda.ejecutar_en_experimento``); si su
    bloque de la config trae ``hiperparametros_desde: config`` (que gana a ``ejecutar_en_experimento``) usa los de la config y,
    si son EXACTAMENTE el mejor ensayo de ``hpo_ensayos.json`` de la misma partición, reporta el presupuesto de esa búsqueda
    (origen ``ORIGEN_CONFIG_HPO``); si no, 1 configuración y 0 s. La igualdad se mide solo sobre los hiperparámetros BUSCADOS
    (las claves de ``mejor.params``): un ``--set`` sobre un fijo no buscado no resetea el presupuesto (``hpo_ensayos.json`` no
    guarda los fijos).
    Un modelo SIN búsqueda tiene presupuesto 1 y 0 s. La fábrica lee ``cfg[nombre]["hiperparametros"]``.
  - Si ``modelo.diagnosticos()["degenerado"]`` es verdadero, el experimento se detiene con un error claro.
  - ``diagnosticos()`` se guarda por semilla y se resume entre semillas en ``summary.json``; ``guardar()`` se llama con la
    primera semilla y escribe en ``salida.modelos``.

Salidas en ``salida.carpeta`` (núcleo §5.9): ``summary.json``, ``semillas/<modelo>_seed<k>.json`` (k = semilla efectiva; antes de
escribir se borran los de corridas anteriores de los modelos que se corren), ``metricas_por_k.json``,
``metricas_por_grupo.json`` y ``recomendaciones_prueba.parquet`` (top-``top_guardar`` por usuario, modelo y semilla; permite
recalcular las métricas). De ``resumen.json`` solo se lee el bloque ``sha256`` (evidencia); el arnés comprueba que la huella de
la partición y el SHA-256 del parquet recalculados coinciden con él.

Los grupos «pocas» / «muchas» usan el total de interacciones del usuario (train + validación + prueba) SOLO para estratificar
el reporte (enunciado, tarea 6); ningún modelo los recibe (D9). Un grupo sin usuarios de prueba se reporta con
``n_usuarios = 0`` y sin métricas (no hay nada que promediar) y no tiene esperado analítico.
"""

from __future__ import annotations

import copy
import hashlib
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.comun.results import load_json, save_json
from src.comun.seeds import make_rng, seeds_for_runs, validar_entero
from src.m3_recomendacion import hpo, metricas, particion
from src.m3_recomendacion.referencias import MODELOS

SPLIT_EVALUADO = particion.PRUEBA
GRUPOS = ("pocas", "muchas")
METRICAS = ("precision", "recall", "ndcg", "acierto", "cobertura")
ARCHIVO_HPO = hpo.ARCHIVO
ORIGENES_HIPERPARAMETROS = ("hpo", "config")
ORIGEN_CONFIG_HPO = "config (igual al mejor ensayo de hpo)"   # config = mejor ensayo: se reporta el presupuesto de la búsqueda
_FALTA = object()
PRESUPUESTO_SIN_BUSQUEDA ={"hiperparametros": None, "n_configuraciones": 1, "tiempo_s": 0.0, "origen": "ninguno"}


# =========================================================================== datos y evidencia
def _sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def cargar_datos(cfg: dict) -> dict:
    """Lee los tres parquet y comprueba contra ``resumen.json`` (solo su bloque ``sha256``) que son la misma partición.

    Devuelve ``inter`` (con ``split``), ``destinos``, ``catalogo`` (ids en el orden del parquet), ``lugar_de`` y ``evidencia``.
    Error claro si la huella recalculada o el SHA-256 del parquet no coinciden (D8)."""
    d = cfg["datos"]
    carpeta = Path(d["carpeta"])
    rutas = {"interacciones": carpeta / d["interacciones"], "destinos": carpeta / d["destinos"],
             "usuarios": carpeta / d["usuarios"]}
    inter = pd.read_parquet(rutas["interacciones"])
    destinos = pd.read_parquet(rutas["destinos"])
    bloque_sha = load_json(d["resumen_particion"])["sha256"]                    # solo el bloque sha256 (evidencia)
    huella = particion.huella(inter)
    if huella != bloque_sha["huella"]:
        raise ValueError(f"la huella de la partición ({huella}) no coincide con la de {d['resumen_particion']} "
                         f"({bloque_sha['huella']}): no es la misma partición; vuelve a correr m3-datos")
    sha = {nombre: _sha256(ruta) for nombre, ruta in rutas.items()}
    if sha["interacciones"] != bloque_sha["interacciones_parquet"]:
        raise ValueError(f"el SHA-256 de {rutas['interacciones']} ({sha['interacciones']}) no coincide con el de "
                         f"{d['resumen_particion']} ({bloque_sha['interacciones_parquet']})")
    evidencia = {"particion_huella": huella, "particion_huella_formato": bloque_sha["huella_formato"], "sha256_parquet": sha}
    return {"inter": inter, "destinos": destinos, "catalogo": destinos["destino_id"].to_numpy(dtype="int64"),
            "evidencia": evidencia, "lugar_de": {int(i): str(g) for i, g in zip(destinos["destino_id"], destinos["lugar"])}}


# =========================================================================== contexto de la evaluación
def _normalizar(cfg: dict) -> dict:
    """Opciones validadas de ``evaluacion``, ``semillas`` y ``modelos``."""
    ev = cfg["evaluacion"]
    modelos = list(cfg["modelos"])
    desconocidos = [m for m in modelos if m not in MODELOS]
    if desconocidos:
        raise ValueError(f"modelos desconocidos {desconocidos}; registrados en referencias.MODELOS: {sorted(MODELOS)}")
    ks = metricas.normalizar_k(ev["k"], "evaluacion.k")
    top_guardar = validar_entero(ev["top_guardar"], "evaluacion.top_guardar", minimo=1)
    return {"ks": ks, "k_lugar": metricas.normalizar_k(ev["k_lugar"], "evaluacion.k_lugar"), "modelos": modelos,
            "top_guardar": top_guardar, "k_max": max(max(ks), top_guardar),
            "umbral": validar_entero(ev["umbral_pocas_max"], "evaluacion.umbral_pocas_max", minimo=1),
            "n": validar_entero(cfg["semillas"]["n"], "semillas.n", minimo=1),
            "base_seed": validar_entero(cfg["semillas"]["base_seed"], "semillas.base_seed"),
            "salida": Path(cfg["salida"]["carpeta"]), "carpeta_modelos": Path(cfg["salida"]["modelos"])}


def _contexto(cfg: dict) -> dict:
    """Todo lo que comparten las corridas: opciones, datos, usuarios de prueba (D10), relevantes, grupos y destinos fríos
    (diagnóstico de evaluación: usa prueba, ningún modelo lo recibe)."""
    ctx = {**_normalizar(cfg), **cargar_datos(cfg)}
    inter, catalogo = ctx["inter"], ctx["catalogo"]
    ctx["cands"] = particion.candidatos(inter, catalogo, SPLIT_EVALUADO)
    ctx["rel"] = particion.relevantes(inter, SPLIT_EVALUADO)
    ctx["usuarios"] = np.array(sorted(ctx["cands"]), dtype="int64")
    total = inter.groupby("usuario_id").size().reindex(ctx["usuarios"])
    ctx["grupo"] = np.where(total.to_numpy() <= ctx["umbral"], GRUPOS[0], GRUPOS[1])
    pop = particion.popularidad_train(inter, catalogo)
    ctx["frios_ids"] = set(pop.index[pop.to_numpy() == 0].astype(int).tolist())
    ctx["objetivo_frio"] = np.array([all(int(d) in ctx["frios_ids"] for d in ctx["rel"][int(u)]) for u in ctx["usuarios"]])
    ctx["min_no_frios"] = int(min(int((pop.reindex(c).to_numpy() > 0).sum()) for c in ctx["cands"].values()))
    return ctx


# =========================================================================== hiperparámetros y presupuesto de búsqueda
def _leer_familia(nombre: str, ctx: dict) -> dict:
    ruta = ctx["salida"] / ARCHIVO_HPO
    if not ruta.is_file():
        raise FileNotFoundError(f"falta {ruta}: corre primero `python run.py m3-hpo --config configs/m3/hpo.yaml`, o usa "
                                f"{nombre}.hiperparametros_desde=config, o busqueda.ejecutar_en_experimento=true")
    previo = load_json(ruta)
    if previo["evidencia"]["particion_huella"] != ctx["evidencia"]["particion_huella"]:
        raise ValueError(f"{ruta} se calculó con otra partición; vuelve a correr m3-hpo")
    if nombre not in previo["familias"]:
        raise ValueError(f"{ruta} no tiene la familia {nombre}; vuelve a correr m3-hpo")
    return previo["familias"][nombre]


def _valor_en_config(nombre: str, clave: str, cfg: dict):
    """Valor efectivo de un hiperparámetro en la config: ``<nombre>.hiperparametros[clave]`` si está ahí; si no y la clave tiene
    punto (la red: «modelo.dim_embedding»), el bloque de primer nivel. ``_FALTA`` si no existe."""
    hp = cfg.get(nombre, {}).get("hiperparametros", {})
    if clave in hp:
        return hp[clave]
    x = cfg
    for parte in clave.split("."):
        if not isinstance(x, dict) or parte not in x:
            return _FALTA
        x = x[parte]
    return x if "." in clave else _FALTA


def _presupuesto_config(nombre: str, cfg: dict, ctx: dict) -> dict:
    """Origen «config». Si ``hpo_ensayos.json`` (misma partición) trae la familia y su mejor ensayo coincide EXACTAMENTE con los
    valores efectivos de la config (decisión de Juan José, 27-nov: base.yaml copia el mejor ensayo), se reporta el presupuesto
    real de esa búsqueda (núcleo §6); si no (o un --set en vivo cambió algo), 1 configuración y 0 s."""
    hiper = dict(cfg[nombre]["hiperparametros"])
    ruta = ctx["salida"] / ARCHIVO_HPO
    if ruta.is_file():
        previo = load_json(ruta)
        familia = previo.get("familias", {}).get(nombre)
        if familia and previo.get("evidencia", {}).get("particion_huella") == ctx["evidencia"]["particion_huella"]:
            if all(_valor_en_config(nombre, k, cfg) == v for k, v in familia["mejor"]["params"].items()):
                return {"hiperparametros": hiper, "n_configuraciones": int(familia["n_ensayos"]),
                        "tiempo_s": float(familia["tiempo_total_s"]), "origen": ORIGEN_CONFIG_HPO}
    return {"hiperparametros": hiper, "n_configuraciones": 1, "tiempo_s": 0.0, "origen": "config"}


def _presupuesto(nombre: str, cfg: dict, ctx: dict) -> dict:
    """Hiperparámetros y presupuesto de búsqueda de un modelo (una sola regla para todos; ver el docstring del módulo)."""
    if nombre not in hpo.BUSQUEDAS:
        return dict(PRESUPUESTO_SIN_BUSQUEDA)
    bloque = cfg.get(nombre, {})
    origen = bloque.get("hiperparametros_desde", "hpo")
    if origen not in ORIGENES_HIPERPARAMETROS:
        raise ValueError(f"{nombre}.hiperparametros_desde debe ser uno de {list(ORIGENES_HIPERPARAMETROS)}; "
                         f"se recibió {origen!r}")
    if origen == "config":           # JJ-5: «config» gana a busqueda.ejecutar_en_experimento (no se corre ninguna búsqueda)
        return _presupuesto_config(nombre, cfg, ctx)
    if cfg.get("busqueda", {}).get("ejecutar_en_experimento", False):
        familia = hpo.BUSQUEDAS[nombre](cfg, ctx["inter"], ctx["catalogo"])
        hpo.escribir_familia(ctx["salida"], ctx["evidencia"], nombre, familia)
    else:
        familia = _leer_familia(nombre, ctx)
    return {"hiperparametros": dict(familia["mejor"]["params"]), "n_configuraciones": int(familia["n_ensayos"]),
            "tiempo_s": float(familia["tiempo_total_s"]), "origen": "hpo"}


def _preparar_modelos(cfg: dict, ctx: dict) -> tuple[dict, dict]:
    """(config con los hiperparámetros resueltos en ``cfg[nombre]["hiperparametros"]``, presupuesto por modelo)."""
    cfg_modelos, presupuestos = copy.deepcopy(cfg), {}
    for nombre in ctx["modelos"]:
        presupuestos[nombre] = _presupuesto(nombre, cfg, ctx)
        if presupuestos[nombre]["hiperparametros"] is not None:
            cfg_modelos.setdefault(nombre, {})["hiperparametros"] = presupuestos[nombre]["hiperparametros"]
    return cfg_modelos, presupuestos


# =========================================================================== métricas de una corrida
def clave_metrica(nombre: str, k: int) -> str:
    """«ndcg@5», «cobertura@10»…: la clave con que las métricas aparecen en los JSON."""
    return f"{nombre}@{k}"


def _medias(pu: dict, tops: dict, mascara: np.ndarray, ctx: dict) -> dict:
    """Métricas medias de los usuarios de ``mascara``; la cobertura es la de las listas de ese subconjunto."""
    out = {}
    sub = {int(u): tops[int(u)] for u in ctx["usuarios"][mascara]}
    for k in ctx["ks"]:
        for nombre in ("precision", "recall", "ndcg", "acierto"):
            out[clave_metrica(nombre, k)] = float(pu[nombre][k][mascara].mean())
        out[clave_metrica("cobertura", k)] = metricas.cobertura(sub, len(ctx["catalogo"]), k)
    for k in pu["lugar"]:
        out[clave_metrica("acierto_por_lugar", k)] = float(pu["lugar"][k][mascara].mean())
    return out


def _concentracion(tops: dict, ctx: dict) -> dict:
    out = {}
    for k in ctx["ks"]:
        e = metricas.exposiciones(tops, ctx["catalogo"], k)
        out[clave_metrica("gini", k)] = metricas.gini_exposiciones(e)
        out[clave_metrica("hhi", k)] = metricas.hhi_exposiciones(e)
    return out


def _por_grupo(pu: dict, tops: dict, ctx: dict) -> dict:
    out = {}
    for g in GRUPOS:
        mascara = ctx["grupo"] == g
        out[g] = {"n_usuarios": int(mascara.sum()), **(_medias(pu, tops, mascara, ctx) if mascara.any() else {})}
    return out


def _sobre_destinos_frios(pu: dict, tops: dict, ctx: dict) -> dict:
    """Aciertos medios con objetivo frío / no frío y destinos fríos que entran a cada lista, por K."""
    frio = ctx["objetivo_frio"]
    out = {}
    for k in ctx["ks"]:
        en_lista = np.array([sum(int(d) in ctx["frios_ids"] for d in tops[int(u)][0][:k]) for u in ctx["usuarios"]], dtype=float)
        a = pu["acierto"][k]
        out[str(k)] = {"acierto_objetivo_frio": float(a[frio].mean()) if frio.any() else None,
                       "acierto_objetivo_no_frio": float(a[~frio].mean()) if (~frio).any() else None,
                       "frios_por_lista": float(en_lista.mean())}
    return out


def _evaluar_corrida(tops: dict, ctx: dict) -> dict:
    """Todas las métricas de una corrida: globales, concentración, por grupo y sobre destinos fríos."""
    pu = metricas.metricas_por_usuario(tops, ctx["rel"], ctx["lugar_de"], ctx["ks"], ctx["k_lugar"])
    todos = np.ones(len(ctx["usuarios"]), dtype=bool)
    return {"global": _medias(pu, tops, todos, ctx), "concentracion": _concentracion(tops, ctx),
            "por_grupo": _por_grupo(pu, tops, ctx), "frios": _sobre_destinos_frios(pu, tops, ctx)}


# =========================================================================== corridas de un modelo
def _exigir_no_degenerado(nombre: str, semilla: int, diagnosticos: dict) -> None:
    if diagnosticos.get("degenerado"):
        raise ValueError(f"{nombre} (semilla {semilla}) quedó degenerado (motivo: {diagnosticos.get('motivo_degenerado')}); "
                         f"no se reportan resultados de un modelo degenerado. Diagnósticos: {diagnosticos}. "
                         "Revisa sus hiperparámetros o corre m3-hpo de nuevo")


def _una_corrida(nombre: str, cfg_modelos: dict, ctx: dict, run_id: int):
    """Ajusta, puntúa, ordena y evalúa una vez. Devuelve (modelo, tops, corrida, tiempo_s)."""
    rng = make_rng(ctx["base_seed"], run_id)
    t = time.perf_counter()
    modelo = MODELOS[nombre](cfg_modelos).ajustar(ctx["inter"], ctx["catalogo"], rng)
    tops = metricas.rankear_usuarios(modelo.puntuar(ctx["usuarios"]), ctx["usuarios"], ctx["catalogo"], ctx["cands"],
                                     ctx["k_max"], rng)
    corrida = _evaluar_corrida(tops, ctx)
    return modelo, tops, corrida, time.perf_counter() - t


def _filas_recomendaciones(modelo: str, semilla: int, usuarios: np.ndarray, tops: dict, top_guardar: int) -> pd.DataFrame:
    ids = [tops[int(u)][0][:top_guardar] for u in usuarios]
    puntajes = [tops[int(u)][1][:top_guardar] for u in usuarios]
    largos = [len(x) for x in ids]
    return pd.DataFrame({
        "modelo": modelo, "semilla": np.int64(semilla),
        "usuario_id": np.repeat(usuarios, largos).astype("int64"),
        "rango": np.concatenate([np.arange(1, n + 1) for n in largos]).astype("int64"),
        "destino_id": np.concatenate(ids).astype("int64"),
        "puntaje": np.concatenate(puntajes).astype("float64")})


def _guardar_semilla(ctx: dict, nombre: str, run_id: int, modelo, corrida: dict, diagnosticos: dict, tiempo: float) -> None:
    semilla = ctx["base_seed"] + run_id
    save_json(ctx["salida"] / "semillas" / f"{nombre}_seed{semilla}.json", {
        "modelo": nombre, "semilla": semilla, "run_id": run_id, "split_evaluado": SPLIT_EVALUADO,
        "n_usuarios_evaluados": int(len(ctx["usuarios"])), "tiempo_s": tiempo,
        "hiperparametros": dict(modelo.hiperparametros), "n_parametros": modelo.n_parametros(), "diagnosticos": diagnosticos,
        "metricas": {"global": corrida["global"], "concentracion": corrida["concentracion"],
                     "por_grupo": corrida["por_grupo"], "destinos_frios": corrida["frios"]},
        "evidencia": ctx["evidencia"]})


def _borrar_semillas_viejas(ctx: dict, nombre: str) -> None:
    """Borra ``semillas/<nombre>_seed*.json`` de corridas anteriores de ESTE modelo (los de otros modelos no se tocan)."""
    carpeta = ctx["salida"] / "semillas"
    carpeta.mkdir(parents=True, exist_ok=True)
    for viejo in carpeta.glob(f"{nombre}_seed*.json"):
        viejo.unlink()


def _correr_modelo(nombre: str, cfg_modelos: dict, ctx: dict) -> dict:
    """Las ``semillas.n`` corridas de un modelo: escribe sus JSON por semilla y devuelve lo que necesitan los resúmenes."""
    _borrar_semillas_viejas(ctx, nombre)
    r = {"corridas": [], "tiempos": [], "diagnosticos": [], "filas": [], "semillas": seeds_for_runs(ctx["base_seed"], ctx["n"])}
    for run_id, semilla in enumerate(r["semillas"]):
        modelo, tops, corrida, tiempo = _una_corrida(nombre, cfg_modelos, ctx, run_id)
        diagnosticos = modelo.diagnosticos()
        _exigir_no_degenerado(nombre, semilla, diagnosticos)
        r["corridas"].append(corrida)
        r["tiempos"].append(tiempo)
        r["diagnosticos"].append(diagnosticos)
        r["filas"].append(_filas_recomendaciones(nombre, semilla, ctx["usuarios"], tops, ctx["top_guardar"]))
        _guardar_semilla(ctx, nombre, run_id, modelo, corrida, diagnosticos, tiempo)
        if run_id == 0:
            modelo.guardar(ctx["carpeta_modelos"], semilla, ctx["evidencia"])
    r.update(n_parametros=modelo.n_parametros(), hiperparametros=dict(modelo.hiperparametros),
             descripcion_frios=modelo.descripcion_frios)
    return r


# =========================================================================== resúmenes entre semillas
def _agregar(corridas: list[dict], ruta: tuple[str, ...], resumir=metricas.resumir_semillas) -> dict:
    """{clave: resumen entre semillas} para el diccionario plano que está en ``corrida[ruta]`` de cada corrida."""
    planos = []
    for c in corridas:
        x = c
        for r in ruta:
            x = x[r]
        planos.append(x)
    return {clave: resumir([p[clave] for p in planos]) for clave in planos[0]}


def _agregar_grupo(corridas: list[dict], grupo: str) -> dict:
    """Resumen entre semillas de un grupo; sin usuarios, solo ``{"n_usuarios": 0}``."""
    planos = [c["por_grupo"][grupo] for c in corridas]
    n_usuarios = planos[0]["n_usuarios"]
    if n_usuarios == 0:
        return {"n_usuarios": 0}
    return {"n_usuarios": n_usuarios, **{clave: metricas.resumir_semillas([p[clave] for p in planos])
                                         for clave in planos[0] if clave != "n_usuarios"}}


def _resumir_diagnosticos(lista: list[dict]) -> dict:
    """Resumen entre semillas de ``modelo.diagnosticos()``: los números (no booleanos) como media/desviación/mínimo/máximo; el
    resto (booleanos, textos, diccionarios) tal cual si son iguales en todas las semillas, y si no, la lista por semilla."""
    out = {}
    for clave in lista[0]:
        valores = [d[clave] for d in lista]
        numerico = all(isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool) for v in valores)
        if numerico:
            out[clave] = metricas.resumir_concentracion(valores)
        else:
            out[clave] = valores[0] if all(v == valores[0] for v in valores) else valores
    return out


def _resumen_frios(corridas: list[dict], ks) -> dict:
    out = {}
    for k in ks:
        bloque = {}
        for clave in ("acierto_objetivo_frio", "acierto_objetivo_no_frio", "frios_por_lista"):
            vals = [c["frios"][str(k)][clave] for c in corridas]
            bloque[clave] = None if vals[0] is None else metricas.resumir_semillas(vals)
        out[str(k)] = bloque
    return out


def _linea_base_azar(ctx: dict) -> dict:
    """Esperados analíticos del aleatorio, globales y por grupo (un grupo sin usuarios no tiene esperado)."""
    args = (ctx["cands"], ctx["rel"], ctx["lugar_de"], ctx["catalogo"], ctx["ks"], ctx["k_lugar"])
    return {"global": metricas.esperados_aleatorio(*args),
            "por_grupo": {g: metricas.esperados_aleatorio(*args, usuarios=[int(u) for u in ctx["usuarios"][ctx["grupo"] == g]])
                          for g in GRUPOS if (ctx["grupo"] == g).any()}}


def _bloque_modelo(r: dict, presupuesto: dict, azar: dict, ctx: dict, device: str) -> dict:
    """Bloque de un modelo en ``summary.json``: métricas, complejidad, presupuesto de búsqueda y diagnósticos."""
    return {
        "metricas": _agregar(r["corridas"], ("global",)),
        "concentracion": _agregar(r["corridas"], ("concentracion",), metricas.resumir_concentracion),
        "n_parametros": r["n_parametros"], "diagnosticos": _resumir_diagnosticos(r["diagnosticos"]),
        "n_configuraciones_busqueda": presupuesto["n_configuraciones"],
        "tiempo_total_s": float(sum(r["tiempos"]) + presupuesto["tiempo_s"]),
        "tiempo_corridas_finales_s": float(sum(r["tiempos"])), "tiempo_busqueda_s": presupuesto["tiempo_s"],
        "hiperparametros": r["hiperparametros"], "hiperparametros_origen": presupuesto["origen"],
        "device": device, "semillas_efectivas": r["semillas"],
        "acierto_por_lugar_linea_base": {str(k): azar["global"][clave_metrica("acierto_por_lugar", k)]
                                         for k in ctx["k_lugar"] if k in ctx["ks"]}}


def _bloque_frios(ctx: dict, resultados: dict) -> dict:
    """Diagnóstico de destinos sin interacciones en train (D14): cuántos usuarios, techo y cómo los trata cada modelo."""
    n_frios, n_usuarios = int(ctx["objetivo_frio"].sum()), int(len(ctx["usuarios"]))
    return {
        "definicion": ("Usuarios de prueba cuyo destino objetivo no tiene ninguna interacción en train (D14). Diagnóstico de "
                       "evaluación: usa prueba, ningún modelo lo recibe."),
        "usuarios_prueba": n_usuarios, "usuarios_prueba_con_objetivo_frio": n_frios,
        "destinos_sin_train_en_catalogo": len(ctx["frios_ids"]),
        "techo_acierto_popularidad": float((n_usuarios - n_frios) / n_usuarios),
        "min_candidatos_no_frios": ctx["min_no_frios"], "popularidad_techo_valido": bool(ctx["min_no_frios"] >= max(ctx["ks"])),
        "tratamiento": {n: r["descripcion_frios"] for n, r in resultados.items()},
        "por_modelo": {n: _resumen_frios(r["corridas"], ctx["ks"]) for n, r in resultados.items()}}


def _resumen(cfg: dict, ctx: dict, resultados: dict, presupuestos: dict, azar: dict) -> dict:
    """Contenido de ``summary.json`` (núcleo §5.9)."""
    device = cfg.get("device", "cpu")
    return {"split_evaluado": SPLIT_EVALUADO, "k": ctx["ks"], "k_lugar": [k for k in ctx["k_lugar"] if k in ctx["ks"]],
            "n_usuarios_evaluados": int(len(ctx["usuarios"])), "semillas": {"base_seed": ctx["base_seed"], "n": ctx["n"]},
            "evidencia": ctx["evidencia"],
            "modelos": {n: _bloque_modelo(r, presupuestos[n], azar, ctx, device) for n, r in resultados.items()},
            "linea_base_aleatoria_analitica": {
                "nota": ("Valor esperado del recomendador aleatorio (top-K uniforme sin reemplazo entre los candidatos de "
                         "cada usuario), promediado sobre los usuarios evaluados; para acierto por lugar es la línea base "
                         "del azar que se compara con CADA modelo."), **azar},
            "destinos_frios": _bloque_frios(ctx, resultados)}


# =========================================================================== escritura
def _escribir_por_k(ctx: dict, resultados: dict, azar: dict) -> None:
    todas = (*METRICAS, "acierto_por_lugar")
    por_modelo = {}
    for nombre, r in resultados.items():
        bloque_global = _agregar(r["corridas"], ("global",))
        conc = _agregar(r["corridas"], ("concentracion",), metricas.resumir_concentracion)
        por_modelo[nombre] = {}
        for k in ctx["ks"]:
            bloque = {m: bloque_global[clave_metrica(m, k)] for m in todas if clave_metrica(m, k) in bloque_global}
            bloque["gini"], bloque["hhi"] = conc[clave_metrica("gini", k)], conc[clave_metrica("hhi", k)]
            por_modelo[nombre][str(k)] = bloque
    bloque_azar = {str(k): {m: azar["global"][clave_metrica(m, k)] for m in todas if clave_metrica(m, k) in azar["global"]}
                   for k in ctx["ks"]}
    save_json(ctx["salida"] / "metricas_por_k.json", {
        "split_evaluado": SPLIT_EVALUADO, "k": ctx["ks"], "semillas": ctx["n"], "evidencia": ctx["evidencia"],
        "nota": "Media, desviación (ddof = 1), mejor y peor entre semillas por modelo y K; Gini y HHI de las exposiciones.",
        "modelos": por_modelo, "aleatorio_analitico": bloque_azar})


def _escribir_por_grupo(ctx: dict, resultados: dict, azar: dict) -> None:
    modelos = {nombre: {g: _agregar_grupo(r["corridas"], g) for g in GRUPOS} for nombre, r in resultados.items()}
    save_json(ctx["salida"] / "metricas_por_grupo.json", {
        "split_evaluado": SPLIT_EVALUADO, "k": ctx["ks"], "semillas": ctx["n"], "umbral_pocas_max": ctx["umbral"],
        "nota": particion.NOTA_GRUPOS, "evidencia": ctx["evidencia"], "modelos": modelos,
        "aleatorio_analitico": azar["por_grupo"]})


def _escribir_salidas(ctx: dict, resumen: dict, resultados: dict, azar: dict) -> None:
    save_json(ctx["salida"] / "summary.json", resumen)
    _escribir_por_k(ctx, resultados, azar)
    _escribir_por_grupo(ctx, resultados, azar)
    filas = [f for r in resultados.values() for f in r["filas"]]
    pd.concat(filas, ignore_index=True).to_parquet(ctx["salida"] / "recomendaciones_prueba.parquet", index=False)


def _imprimir(modelos: dict, n_semillas: int, segundos: float) -> None:
    primero = next(iter(modelos.values()))["metricas"]
    preferidas = (clave_metrica("ndcg", 5), clave_metrica("recall", 10), clave_metrica("cobertura", 10))
    columnas = [c for c in preferidas if c in primero] or list(primero)[:3]
    print(f"\nResultados en prueba (media ± desviación sobre {n_semillas} semillas):")
    print(f"  {'modelo':<12}" + "".join(f"{c:>22}" for c in columnas))
    for nombre, m in modelos.items():
        celdas = []
        for c in columnas:
            r = m["metricas"][c]
            celdas.append(f"{r['media']:.4f} ± {r['desviacion']:.4f}" if r["desviacion"] is not None else f"{r['media']:.4f}")
        print(f"  {nombre:<12}" + "".join(f"{x:>22}" for x in celdas))
    print(f"Tiempo del arnés: {segundos:.1f} s")


def main(cfg: dict) -> int:
    """``run.py m3``: evalúa en prueba los modelos de ``cfg["modelos"]`` con ``semillas.n`` semillas (ver el docstring)."""
    inicio = time.perf_counter()
    ctx = _contexto(cfg)
    cfg_modelos, presupuestos = _preparar_modelos(cfg, ctx)
    resultados = {nombre: _correr_modelo(nombre, cfg_modelos, ctx) for nombre in ctx["modelos"]}
    azar = _linea_base_azar(ctx)
    resumen = _resumen(cfg, ctx, resultados, presupuestos, azar)
    _escribir_salidas(ctx, resumen, resultados, azar)
    _imprimir(resumen["modelos"], ctx["n"], time.perf_counter() - inicio)
    return 0
