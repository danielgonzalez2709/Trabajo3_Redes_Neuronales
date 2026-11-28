"""M3 — partición sin fuga (JJ-3). Funciones puras, sin estado global y sin red.

Decisiones [DECIDIDO, Juan José] (docs/spec/partes/juanjose.md §3.1):
  D3  partición por usuario (no por tiempo: ``fecha_visita`` no es una fecha real). Regla formal en ``asignar_split``.
  D8  una sola partición para todos los modelos de M3, en la columna ``split`` de ``interacciones.parquet``, con su SHA-256
      y el de la huella (``huella``) en ``results/data/m3/particion/resumen.json``.
  D9  HPO y parada temprana con validación; modelos finales solo con train. Toda estadística derivada de las interacciones
      (popularidad, conteos por destino, negativos por popularidad…) se calcula SOLO con train (``popularidad_train``).
  D10 candidatos al evaluar: prueba → catálogo − (train ∪ validación) del usuario; validación → catálogo − train.

La clave de una interacción es ``(origen, id_origen)``: ``id_origen`` solo no es único (ReviewID e HistoryID se solapan).
Cada par ``(usuario_id, destino_id)`` es único (D1), así que ningún par puede quedar en dos particiones.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from src.comun.seeds import make_rng, validar_entero

TRAIN, VALIDACION, PRUEBA = "train", "validacion", "prueba"
SPLITS = (TRAIN, VALIDACION, PRUEBA)
CONOCIDOS = {PRUEBA: (TRAIN, VALIDACION), VALIDACION: (TRAIN,)}   # D10: historial conocido al evaluar cada split
CLAVE = ["origen", "id_origen"]
PAR = ["usuario_id", "destino_id"]
COLUMNAS_REQUERIDAS = [*PAR, *CLAVE]
COLUMNAS_HUELLA = [*PAR, "split"]
RUN_ID = 0   # la partición usa make_rng(semilla, RUN_ID): semilla efectiva = semilla + 0
# Tipo de la columna ``split``: el mismo texto de pandas que ``origen`` en el parquet (así el parquet queda idéntico).
TIPO_SPLIT = pd.StringDtype(storage="pyarrow", na_value=np.nan)
REGLA = ("D3 (docs/spec/partes/juanjose.md §3.1): para cada usuario con n interacciones se ordenan sus interacciones por "
         "una clave U(0,1) independiente (permutación uniforme); si n >= 2, la primera va a prueba; si n >= 3, la segunda va "
         "a validación; el resto, a train (n = 1: solo train). Azar: make_rng(semilla, run_id), con las interacciones en "
         "orden canónico por (origen, id_origen).")
FORMATO_HUELLA = ("SHA-256 del texto UTF-8 «usuario_id,destino_id,split\\n» seguido de una línea «<usuario_id>,<destino_id>,"
                  "<split>\\n» por interacción (enteros en base 10, sin índice ni comillas), en orden ascendente de "
                  "(usuario_id, destino_id).")
NOTA_GRUPOS = ("El grupo se define con el total de interacciones del usuario (train + validación + prueba): pocas = 1 a "
               "umbral_pocas_max, muchas = más que umbral_pocas_max. Solo estratifica este reporte y la evaluación por grupos "
               "(enunciado, M3 tarea 6); no es una variable de los modelos (D9).")
NOTA_DIAGNOSTICOS = ("Medidos sobre la partición para leer la evaluación; usan prueba y validación y por eso ningún modelo "
                     "los usa como entrada (D9).")


# --------------------------------------------------------------------------- validaciones
def _validar_columnas(inter: pd.DataFrame, columnas: list[str], que: str) -> None:
    faltan = [c for c in columnas if c not in inter.columns]
    if faltan:
        raise ValueError(f"{que}: faltan las columnas {faltan}; hay {list(inter.columns)}")


def _validar_unicidad(inter: pd.DataFrame) -> None:
    rep = inter[inter.duplicated(PAR, keep=False)]
    if len(rep):
        pares = sorted(map(tuple, rep[PAR].drop_duplicates().to_numpy().tolist()))
        raise ValueError(f"pares (usuario_id, destino_id) repetidos ({len(pares)}): {pares[:10]}; D1 exige pares únicos")
    rep = inter[inter.duplicated(CLAVE, keep=False)]
    if len(rep):
        claves = sorted(map(tuple, rep[CLAVE].drop_duplicates().to_numpy().tolist()))
        raise ValueError(f"claves (origen, id_origen) repetidas ({len(claves)}): {claves[:10]}")


def _validar_split(inter: pd.DataFrame, que: str) -> None:
    _validar_columnas(inter, [*PAR, "split"], que)
    otros = sorted(set(inter["split"].astype(str)) - set(SPLITS))
    if otros or inter["split"].isna().any():
        raise ValueError(f"{que}: valores de split fuera de {list(SPLITS)}: {otros or ['<faltante>']}")


def _ids_catalogo(catalogo) -> np.ndarray:
    ids = np.asarray(catalogo, dtype="int64")
    if len(np.unique(ids)) != len(ids):
        raise ValueError("el catálogo tiene destino_id repetidos")
    return ids


def _destinos_en_catalogo(inter: pd.DataFrame, ids: np.ndarray) -> None:
    fuera = sorted(set(inter["destino_id"].astype("int64")) - set(ids.tolist()))
    if fuera:
        raise ValueError(f"destino_id que no están en el catálogo: {fuera[:10]}")


def _objetivo(split_objetivo: str) -> tuple[str, ...]:
    if split_objetivo not in CONOCIDOS:
        raise ValueError(f"split_objetivo debe ser {sorted(CONOCIDOS)}; se recibió {split_objetivo!r}")
    return CONOCIDOS[split_objetivo]


# --------------------------------------------------------------------------- partición (D3)
def asignar_split(inter: pd.DataFrame, semilla: int, run_id: int = RUN_ID) -> pd.DataFrame:
    """Copia de ``inter`` con la columna ``split`` al final (mismo orden de filas, mismo índice y demás columnas intactas).

    Regla formal (D3). Sea I_u el conjunto de interacciones del usuario u y n_u = |I_u|.
      1. Las interacciones se ponen en orden canónico por la clave (origen, id_origen) —así el resultado no depende del
         orden de entrada— y la i-ésima recibe ξ_i ~ U(0, 1) i.i.d. de ``make_rng(semilla, run_id)``.
      2. Dentro de cada usuario, ordenar I_u por ξ da i_(1), i_(2), …, i_(n_u): una permutación uniforme de I_u.
      3. split(i_(1)) = prueba      si n_u >= 2
         split(i_(2)) = validacion  si n_u >= 3
         split(i_(k)) = train       en los demás casos (n_u = 1 → solo train).
    Consecuencias: P(i ∈ prueba | n_u >= 2) = 1/n_u; P(i ∈ validacion | n_u >= 3) = 1/n_u;
    |train_u| = n_u − 1[n_u >= 2] − 1[n_u >= 3] >= 1. El sorteo no mira el destino, la calificación ni el origen.

    Error claro si la semilla no es un entero >= 0, si faltan columnas, si la tabla está vacía, si ya hay ``split``, o si
    se repite un par (usuario, destino) o una clave.
    """
    validar_entero(semilla, "semilla")          # antes de cualquier trabajo O(n)
    validar_entero(run_id, "run_id")
    _validar_columnas(inter, COLUMNAS_REQUERIDAS, "asignar_split")
    if inter.empty:
        raise ValueError("asignar_split: la tabla de interacciones está vacía; no hay nada que partir")
    if "split" in inter.columns:
        raise ValueError("asignar_split: la tabla ya tiene la columna split; la partición se asigna una sola vez")
    _validar_unicidad(inter)
    rng = make_rng(semilla, run_id)

    n = len(inter)
    # Paso 1: orden canónico por la clave; «pos» recuerda la fila de entrada. Cada ξ_i se reparte en ese orden.
    canonico = pd.DataFrame({"pos": np.arange(n), "usuario_id": inter["usuario_id"].to_numpy(),
                             "origen": inter["origen"].astype(str).to_numpy(), "id_origen": inter["id_origen"].to_numpy()})
    canonico = canonico.sort_values(CLAVE, kind="stable").reset_index(drop=True)
    canonico["xi"] = rng.random(n)
    # Paso 2: orden por ξ dentro de cada usuario. np.lexsort ordena por la última clave primero (usuario_id, luego ξ) y
    # desempata explícitamente por la posición canónica: un empate de ξ (probabilidad ~0 en float64) no queda al azar.
    canonico = canonico.iloc[np.lexsort((np.arange(n), canonico["xi"].to_numpy(), canonico["usuario_id"].to_numpy()))]
    por_usuario = canonico.groupby("usuario_id", sort=False)
    posicion_en_usuario = por_usuario.cumcount().to_numpy()          # k − 1 de i_(k): 0 = la de menor ξ
    n_u = por_usuario["xi"].transform("size").to_numpy()            # n_u repetido en cada fila del usuario
    # Paso 3: la primera (si n_u >= 2) va a prueba; la segunda (si n_u >= 3), a validación; el resto, a train.
    es_prueba = (n_u >= 2) & (posicion_en_usuario == 0)
    es_validacion = (n_u >= 3) & (posicion_en_usuario == 1)
    split_canonico = np.full(n, TRAIN, dtype=object)
    split_canonico[es_prueba] = PRUEBA
    split_canonico[es_validacion] = VALIDACION
    # De vuelta al orden de entrada: la fila «pos» recibe su split.
    columna = np.empty(n, dtype=object)
    columna[canonico["pos"].to_numpy()] = split_canonico
    out = inter.copy()
    out["split"] = pd.Series(columna, index=inter.index, dtype=TIPO_SPLIT)
    return out


# --------------------------------------------------------------------------- uso de la partición (D9, D10)
def popularidad_train(inter: pd.DataFrame, catalogo) -> pd.Series:
    """pop(d) = #{(u, d') ∈ train : d' = d} para cada d del catálogo (0 si no aparece en train), índice = ``destino_id``.

    Es la ÚNICA popularidad derivada de las interacciones que pueden usar los modelos (D9): validación y prueba no entran.
    (La columna ``popularidad`` de ``destinos.parquet`` es un atributo de la fuente, no un conteo de interacciones.)
    """
    _validar_split(inter, "popularidad_train")
    ids = _ids_catalogo(catalogo)
    _destinos_en_catalogo(inter, ids)
    train = inter.loc[inter["split"] == TRAIN, "destino_id"].astype("int64")
    pop = train.value_counts().reindex(ids, fill_value=0).astype("int64")
    pop.index.name, pop.name = "destino_id", "popularidad_train"
    return pop


def historial_conocido(inter: pd.DataFrame, split_objetivo: str) -> dict[int, set[int]]:
    """Por usuario, los destinos conocidos al evaluar ``split_objetivo``: prueba → train ∪ validación; validación → train.

    Solo aparecen usuarios con alguna interacción conocida (los que no tienen interacciones no aparecen).
    """
    conocidos = _objetivo(split_objetivo)
    _validar_split(inter, "historial_conocido")
    sub = inter[inter["split"].isin(conocidos)]
    return {int(u): set(g.astype("int64").tolist()) for u, g in sub.groupby("usuario_id")["destino_id"]}


def relevantes(inter: pd.DataFrame, split_objetivo: str) -> dict[int, set[int]]:
    """R_u = destinos del usuario u en ``split_objetivo`` (los «aciertos» posibles), para los usuarios evaluables."""
    _objetivo(split_objetivo)
    _validar_split(inter, "relevantes")
    sub = inter[inter["split"] == split_objetivo]
    return {int(u): set(g.astype("int64").tolist()) for u, g in sub.groupby("usuario_id")["destino_id"]}


def candidatos(inter: pd.DataFrame, catalogo, split_objetivo: str) -> dict[int, np.ndarray]:
    """D10: C_u = catálogo − historial_conocido(u), ordenado ascendente, para cada usuario evaluable en ``split_objetivo``
    (los que tienen al menos una interacción en él). Como los pares son únicos, R_u ⊂ C_u: el objetivo siempre es rankeable
    y un destino ya visto nunca cuenta como acierto. En validación la prueba NO se excluye (excluirla usaría la prueba)."""
    _objetivo(split_objetivo)
    _validar_split(inter, "candidatos")
    ids = np.sort(_ids_catalogo(catalogo))
    _destinos_en_catalogo(inter, ids)
    conocido = historial_conocido(inter, split_objetivo)
    evaluables = sorted(relevantes(inter, split_objetivo))
    return {u: np.setdiff1d(ids, np.fromiter(conocido.get(u, ()), dtype="int64"), assume_unique=True) for u in evaluables}


# --------------------------------------------------------------------------- huella y resumen (D8)
def huella(inter: pd.DataFrame) -> str:
    """SHA-256 de la partición, independiente del formato parquet y de las demás columnas (ver ``FORMATO_HUELLA``)."""
    _validar_split(inter, "huella")
    t = inter[COLUMNAS_HUELLA].sort_values(PAR, kind="stable")
    lineas = [",".join(COLUMNAS_HUELLA)] + [f"{int(u)},{int(d)},{s}" for u, d, s in t.itertuples(index=False, name=None)]
    return hashlib.sha256(("\n".join(lineas) + "\n").encode("utf-8")).hexdigest()


def _conteo_splits(s: pd.Series) -> dict[str, int]:
    return {k: int((s == k).sum()) for k in SPLITS}


def _items_frios(inter: pd.DataFrame, pop: pd.Series, split_objetivo: str) -> dict:
    destinos = inter.loc[inter["split"] == split_objetivo, "destino_id"].astype("int64")
    frio = pop.reindex(destinos).to_numpy() == 0
    distintos = destinos.unique()
    return {"interacciones": int(len(destinos)), "interacciones_con_destino_sin_train": int(frio.sum()),
            "destinos_distintos": int(len(distintos)),
            "destinos_distintos_sin_train": int((pop.reindex(distintos).to_numpy() == 0).sum())}


def _mismo_lugar(inter: pd.DataFrame, lugar: pd.Series, split_objetivo: str) -> dict:
    """Observado: #{u evaluable : lugar(objetivo_u) ∈ L(K_u)}, con K_u = historial conocido de u y L(K_u) sus lugares
    distintos. Línea base del azar (supuesto: el lugar del objetivo es uniforme sobre los n_lugares del catálogo e
    independiente del historial; un objetivo por usuario, D3):
        esperado_por_azar = Σ_u P(lugar(objetivo_u) ∈ L(K_u)) = Σ_u |L(K_u)| / n_lugares."""
    conocido = historial_conocido(inter, split_objetivo)
    rel = relevantes(inter, split_objetivo)
    varios = sorted(u for u, objetivos in rel.items() if len(objetivos) != 1)
    if varios:
        raise ValueError(f"mismo lugar: la línea base supone un objetivo por usuario (D3); usuarios con más: {varios[:10]}")
    n_lugares = int(lugar.nunique())
    lugares_conocidos = {u: {lugar[d] for d in conocido.get(u, set())} for u in rel}
    con = sum(1 for u, objetivos in rel.items() if {lugar[d] for d in objetivos} & lugares_conocidos[u])
    suma_lugares = sum(len(lugares_conocidos[u]) for u in rel)
    return {"usuarios": len(rel), "con_otro_id_del_mismo_lugar": int(con), "n_lugares": n_lugares,
            "esperado_por_azar": suma_lugares / n_lugares}


def resumen_particion(inter: pd.DataFrame, destinos: pd.DataFrame, usuarios_ids, semilla: int, umbral_pocas_max: int,
                      sha256_parquet: str, run_id: int = RUN_ID) -> dict:
    """Contenido de ``results/data/m3/particion/resumen.json``; toda cifra se calcula aquí desde ``inter`` (con ``split``)."""
    _validar_split(inter, "resumen_particion")
    umbral = validar_entero(umbral_pocas_max, "umbral_pocas_max", minimo=1)
    _validar_columnas(destinos, ["destino_id", "lugar"], "resumen_particion (destinos)")
    ids = _ids_catalogo(destinos["destino_id"])
    _destinos_en_catalogo(inter, ids)
    maestros = set(np.asarray(list(usuarios_ids), dtype="int64").tolist())
    activos = set(inter["usuario_id"].astype("int64").tolist())
    if activos - maestros:
        raise ValueError(f"usuario_id sin fila en la maestra: {sorted(activos - maestros)[:10]}")

    return {
        "semilla": validar_entero(semilla, "semilla"), "run_id": validar_entero(run_id, "run_id"),
        "semilla_efectiva": int(semilla) + int(run_id),
        "regla": REGLA,
        "clave_de_interaccion": CLAVE,
        "splits": list(SPLITS),
        "conteos": {
            "interacciones": {**_conteo_splits(inter["split"]), "total": int(len(inter))},
            "usuarios": {**{k: int(inter.loc[inter["split"] == k, "usuario_id"].nunique()) for k in SPLITS},
                         "con_interacciones": len(activos)},
            "usuarios_maestros": len(maestros),
            "usuarios_sin_interacciones_no_evaluables": len(maestros - activos),
        },
        "por_grupo_de_actividad": {"umbral_pocas_max": umbral, "nota": NOTA_GRUPOS, **_grupos_de_actividad(inter, umbral)},
        "diagnosticos": _diagnosticos(inter, destinos, ids),
        "sha256": {"interacciones_parquet": sha256_parquet, "huella": huella(inter), "huella_formato": FORMATO_HUELLA},
    }


def _grupos_de_actividad(inter: pd.DataFrame, umbral: int) -> dict:
    """Por grupo (pocas = 1..umbral interacciones en total; muchas = más), usuarios y conteos de cada split."""
    n = inter.groupby("usuario_id").size()
    grupo = inter["usuario_id"].map(n).le(umbral).map({True: "pocas", False: "muchas"})
    grupos = {}
    for g, regla in (("pocas", f"1 a {umbral} interacciones"), ("muchas", f"{umbral + 1} o más interacciones")):
        sub = inter[grupo == g]
        con_prueba = set(sub.loc[sub["split"] == PRUEBA, "usuario_id"])
        con_val = set(sub.loc[sub["split"] == VALIDACION, "usuario_id"])
        grupos[g] = {"regla": regla, "n_usuarios": int(sub["usuario_id"].nunique()),
                     "usuarios_con_prueba": len(con_prueba), "usuarios_con_validacion": len(con_val),
                     "usuarios_solo_train": int(sub["usuario_id"].nunique() - len(con_prueba | con_val)),
                     "interacciones": _conteo_splits(sub["split"])}
    return grupos


def _diagnosticos(inter: pd.DataFrame, destinos: pd.DataFrame, ids: np.ndarray) -> dict:
    """Destinos fríos (sin train) y coincidencia de lugar con el historial conocido, con su línea base del azar."""
    pop = popularidad_train(inter, ids)
    lugar = destinos.set_index("destino_id")["lugar"]
    return {
        "nota": NOTA_DIAGNOSTICOS,
        "items_frios": {
            "definicion": ("Interacciones (y destinos distintos) del split cuyo destino no tiene ninguna interacción en "
                           "train: su popularidad de train es 0 y un filtrado colaborativo no tiene señal para él."),
            PRUEBA: _items_frios(inter, pop, PRUEBA), VALIDACION: _items_frios(inter, pop, VALIDACION)},
        "mismo_lugar_en_historial_conocido": {
            "definicion": ("con_otro_id_del_mismo_lugar = usuarios evaluables del split con algún destino de su "
                           "historial conocido (prueba: train ∪ validación; validación: train) del mismo lugar que su "
                           f"destino objetivo. Los {len(ids)} ids del catálogo son {int(lugar.nunique())} lugares (D2): "
                           "con tan pocos lugares esa coincidencia es esperable por azar, y un modelo no sabe cuál de "
                           "los lugares conocidos es el del objetivo; por eso todo «acierto por lugar» debe compararse "
                           "con esperado_por_azar = Σ_u |lugares distintos del historial conocido de u| / n_lugares."),
            "supuesto_esperado_por_azar": ("El lugar del destino objetivo es uniforme sobre los n_lugares del catálogo "
                                           "e independiente del historial conocido; un objetivo por usuario (D3)."),
            PRUEBA: _mismo_lugar(inter, lugar, PRUEBA), VALIDACION: _mismo_lugar(inter, lugar, VALIDACION)},
    }
