"""Pruebas sin red de la partición de M3 (JJ-3; núcleo §8 ``test_fuga_m3.py``): ninguna interacción de prueba en train.

Regla (D3, docs/spec/partes/juanjose.md §3.1), para cada usuario u con n_u interacciones:
    n_u >= 2 → 1 al azar en prueba;  n_u >= 3 → 1 más al azar en validación;  el resto, train;  n_u = 1 → solo train.
D9: toda estadística derivada de las interacciones (p. ej. la popularidad) se calcula SOLO con train.
D10: candidatos de prueba = catálogo − (train ∪ validación) del usuario; de validación = catálogo − train.

Dónde podría colarse una fuga y qué prueba la descarta:
  F1 una interacción (o un par usuario–destino) en dos particiones  → test_particiones_disjuntas_y_union_exacta, invariantes
  F2 popularidad calculada con validación o prueba                  → test_popularidad_train_es_invariante_a_val_y_prueba
  F3 un destino ya conocido entre los candidatos (acierto trivial)  → test_candidatos_*
  F4 la validación «ve» la prueba (excluye su destino)              → test_candidatos_de_validacion_solo_excluyen_train
  F5 la partición depende del orden de entrada o del estado global  → test_independiente_del_orden, test_no_toca_el_azar_global
  F6 el parquet versionado no corresponde a la regla ni a la semilla → pruebas con los datos reales (skipif si no están)
  F7 (JJ-5) la red usa validación o prueba para entrenar, para sus negativos o para sus índices de id
      → AJUSTES_SOLO_TRAIN (negativos, entrenamiento a épocas fijas), AJUSTES_SIN_PRUEBA (ajuste completo con parada temprana
        y búsqueda), test_la_validacion_solo_elige_la_epoca_de_parada, test_los_indices_de_id_y_el_dropout_de_id_solo_usan_train
  F8 (JJ-5) el contenido de la red lee interacciones o estadísticas calculadas con ellas → test_contenido_no_lee_interacciones_ni_salidas
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from src.comun.seeds import make_rng
from src.comun.config import apply_overrides, load_config
from src.m3_recomendacion import contenido
from src.m3_recomendacion import datos as dm
from src.m3_recomendacion import hpo, particion, red, referencias
from test_datos_m3 import montar, salidas

RAIZ = Path(__file__).resolve().parents[1]
PROCESADOS = RAIZ / "data" / "processed" / "m3"
RESUMEN_REAL = RAIZ / "results" / "data" / "m3" / "particion" / "resumen.json"
ACTIVIDAD_REAL = RAIZ / "results" / "data" / "m3" / "eda" / "actividad_usuarios.json"
CFG_DATOS = RAIZ / "configs" / "m3" / "datos.yaml"
CFG_EDA = RAIZ / "configs" / "m3" / "eda.yaml"
TRAIN, VAL, PRUEBA = "train", "validacion", "prueba"
BASE = ["usuario_id", "destino_id", "origen", "id_origen", "calificacion", "fecha_visita"]


# --------------------------------------------------------------------------- tablas sintéticas hechas a mano
def tabla(conteos: dict[int, int], n_destinos: int = 30) -> pd.DataFrame:
    """Interacciones sintéticas: el usuario u tiene ``conteos[u]`` destinos distintos (u, u+1, … mod n_destinos, +1).
    ``origen`` alterna reseña/historial y ``id_origen`` se numera por origen desde 1, de modo que ReviewID e HistoryID se
    solapan como en los datos reales (la clave es el par)."""
    filas, contador = [], {"resena": 0, "historial": 0}
    for u, n in conteos.items():
        for k in range(n):
            origen = "resena" if (u + k) % 2 == 0 else "historial"
            contador[origen] += 1
            filas.append((u, (u + k) % n_destinos + 1, origen, contador[origen], 1 + (u + k) % 5,
                          pd.NaT if origen == "resena" else pd.Timestamp("2024-01-01")))
    df = pd.DataFrame(filas, columns=BASE)
    df["fecha_visita"] = df["fecha_visita"].astype("datetime64[ns]")
    return df


def catalogo(n: int = 30, n_lugares: int = 5) -> pd.DataFrame:
    """Catálogo sintético: destinos 1..n; ``lugar`` = destino_id mod n_lugares (como los 5 lugares reales)."""
    ids = np.arange(1, n + 1)
    return pd.DataFrame({"destino_id": ids, "lugar": [f"lugar_{i % n_lugares}" for i in ids]})


CONTEOS_A_MANO = {10: 1, 11: 2, 12: 3, 13: 6, 14: 1, 15: 2}   # usuarios con 1, 2, 3 y 6 interacciones
MAESTROS_A_MANO = [9, 10, 11, 12, 13, 14, 15, 16]              # 9 y 16 sin interacciones


def esperado_por_usuario(n: int) -> dict[str, int]:
    return {PRUEBA: int(n >= 2), VAL: int(n >= 3), TRAIN: n - int(n >= 2) - int(n >= 3)}


def verificar_d3(original: pd.DataFrame, con_split: pd.DataFrame) -> None:
    """Invariantes de D3 y de F1; sirve para las tablas sintéticas, los fixtures y los datos reales."""
    # la unión de las tres particiones es exactamente la tabla original: mismas filas, orden y columnas
    assert list(con_split.columns) == [*original.columns, "split"]
    pd.testing.assert_frame_equal(con_split.drop(columns="split"), original)
    assert set(con_split["split"]) <= {TRAIN, VAL, PRUEBA}
    assert con_split["split"].notna().all()
    # F1: ninguna clave (origen, id_origen) ni par (usuario, destino) en dos particiones
    for clave in (["origen", "id_origen"], ["usuario_id", "destino_id"]):
        assert not con_split.duplicated(clave).any()
        assert (con_split.groupby(clave)["split"].nunique() == 1).all()
    pares = {s: set(map(tuple, con_split.loc[con_split["split"] == s, ["usuario_id", "destino_id"]].to_numpy().tolist()))
             for s in (TRAIN, VAL, PRUEBA)}
    assert not (pares[TRAIN] & pares[VAL]) and not (pares[TRAIN] & pares[PRUEBA]) and not (pares[VAL] & pares[PRUEBA])
    # conteo exacto por usuario
    n = original.groupby("usuario_id").size()
    por = con_split.groupby(["usuario_id", "split"]).size().unstack(fill_value=0).reindex(
        columns=[TRAIN, VAL, PRUEBA], fill_value=0)
    for u, nu in n.items():
        assert por.loc[u].to_dict() == esperado_por_usuario(int(nu)), f"usuario {u} con {nu} interacciones"
    assert (por[TRAIN] >= 1).all()                          # todo usuario con interacciones tiene >= 1 en train
    assert set(con_split["usuario_id"]) == set(original["usuario_id"])


# --------------------------------------------------------------------------- regla D3 a mano
@pytest.mark.parametrize("semilla", range(20))
def test_regla_d3_a_mano_con_usuarios_de_1_2_3_y_6(semilla):
    original = tabla(CONTEOS_A_MANO)
    con_split = particion.asignar_split(original, semilla)
    verificar_d3(original, con_split)
    totales = con_split["split"].value_counts().to_dict()
    # a mano: train 1+1+1+4+1+1 = 9, validación 2 (usuarios 12 y 13), prueba 4 (usuarios 11, 12, 13 y 15)
    assert totales == {TRAIN: 9, VAL: 2, PRUEBA: 4}


def test_la_eleccion_es_uniforme_dentro_del_usuario():
    """Con n_u = 6, cada interacción cae en prueba con prob. 1/6 y en validación con prob. 1/6. 600 semillas: esperado 100
    por interacción y desviación ≈ 9,1; la tolerancia de ±45 (≈ 5 σ) detecta una elección fija o sesgada."""
    original = tabla({1: 6})
    en_prueba, en_val = np.zeros(6), np.zeros(6)
    for s in range(600):
        sp = particion.asignar_split(original, s)["split"].to_numpy()
        en_prueba += sp == PRUEBA
        en_val += sp == VAL
    assert np.all(np.abs(en_prueba - 100) < 45), en_prueba
    assert np.all(np.abs(en_val - 100) < 45), en_val


def test_particiones_disjuntas_y_union_exacta():
    original = tabla({u: 1 + u % 7 for u in range(1, 80)})
    assert original.duplicated("id_origen").any()          # id_origen solo NO es clave (como en los datos reales)
    verificar_d3(original, particion.asignar_split(original, 3))


def test_usuarios_sin_interacciones_no_aparecen_ni_se_evaluan():
    con_split = particion.asignar_split(tabla(CONTEOS_A_MANO), 0)
    for u in (9, 16):
        assert u not in set(con_split["usuario_id"])
        assert u not in particion.candidatos(con_split, catalogo()["destino_id"], PRUEBA)
        assert u not in particion.historial_conocido(con_split, PRUEBA)
    # el usuario con 1 interacción no se evalúa (no tiene prueba ni validación)
    assert 10 not in particion.candidatos(con_split, catalogo()["destino_id"], PRUEBA)
    assert 10 not in particion.candidatos(con_split, catalogo()["destino_id"], VAL)
    assert 11 not in particion.candidatos(con_split, catalogo()["destino_id"], VAL)   # n = 2: sin validación


# --------------------------------------------------------------------------- determinismo y orden
def _cuenta_por_usuario_y_split(df: pd.DataFrame) -> dict:
    return df.groupby(["usuario_id", "split"]).size().to_dict()


def test_misma_semilla_mismo_split_y_semilla_distinta_mismas_cantidades():
    original = tabla({u: 1 + u % 7 for u in range(1, 60)})
    a, b = particion.asignar_split(original, 7), particion.asignar_split(original, 7)
    assert a["split"].equals(b["split"])
    assert particion.huella(a) == particion.huella(b)
    c = particion.asignar_split(original, 8)
    assert not a["split"].equals(c["split"])
    assert _cuenta_por_usuario_y_split(a) == _cuenta_por_usuario_y_split(c)
    assert a["split"].value_counts().to_dict() == c["split"].value_counts().to_dict()


def test_independiente_del_orden_de_entrada():
    original = tabla({u: 1 + u % 7 for u in range(1, 60)})
    revuelta = original.sample(frac=1.0, random_state=np.random.RandomState(5)).reset_index(drop=True)
    a = particion.asignar_split(original, 11).set_index(["origen", "id_origen"])["split"]
    b = particion.asignar_split(revuelta, 11).set_index(["origen", "id_origen"])["split"]
    assert a.sort_index().equals(b.sort_index())
    # y conserva el orden de la tabla de entrada (no la reordena)
    pd.testing.assert_frame_equal(particion.asignar_split(revuelta, 11).drop(columns="split"), revuelta)


def test_no_toca_el_azar_global():
    """El estado global de numpy no cambia; la prueba lo guarda y lo deja como estaba (no deja np.random sembrado)."""
    original = np.random.get_state()
    try:
        np.random.seed(123)
        antes = np.random.get_state()
        particion.asignar_split(tabla(CONTEOS_A_MANO), 0)
        despues = np.random.get_state()
        assert np.array_equal(despues[1], antes[1]) and despues[2] == antes[2]
    finally:
        np.random.set_state(original)


def test_el_azar_sale_de_make_rng_con_la_semilla_efectiva():
    """La semilla efectiva es semilla + run_id (src/comun/seeds.py): (0, 5) y (5, 0) dan la misma partición."""
    original = tabla({u: 1 + u % 7 for u in range(1, 60)})
    assert particion.asignar_split(original, 0, run_id=5)["split"].equals(particion.asignar_split(original, 5, run_id=0)["split"])


# --------------------------------------------------------------------------- errores claros
def test_errores_claros_de_asignar_split():
    original = tabla(CONTEOS_A_MANO)
    with pytest.raises(ValueError, match="faltan.*id_origen"):
        particion.asignar_split(original.drop(columns="id_origen"), 0)
    repetido = pd.concat([original, original.iloc[[0]].assign(origen="historial", id_origen=999)], ignore_index=True)
    with pytest.raises(ValueError, match=r"pares \(usuario_id, destino_id\) repetidos"):
        particion.asignar_split(repetido, 0)
    clave_rep = original.copy()
    clave_rep.loc[1, ["origen", "id_origen"]] = clave_rep.loc[0, ["origen", "id_origen"]].to_numpy()
    with pytest.raises(ValueError, match=r"\(origen, id_origen\) repetid"):
        particion.asignar_split(clave_rep, 0)
    with pytest.raises(ValueError, match="ya tiene.*split"):
        particion.asignar_split(particion.asignar_split(original, 0), 0)
    with pytest.raises(ValueError, match="semilla"):
        particion.asignar_split(original, -1)
    with pytest.raises(TypeError, match="semilla"):
        particion.asignar_split(original, "7")
    with pytest.raises(ValueError, match="vacía"):
        particion.asignar_split(original.iloc[0:0], 0)
    with pytest.raises(ValueError, match="split_objetivo"):
        particion.historial_conocido(particion.asignar_split(original, 0), TRAIN)


# --------------------------------------------------------------------------- popularidad solo con train (D9)
def test_popularidad_train_a_mano():
    con_split = pd.DataFrame({"usuario_id": [1, 1, 2, 2, 3], "destino_id": [4, 5, 4, 6, 5],
                              "split": [TRAIN, PRUEBA, TRAIN, VAL, TRAIN]})
    pop = particion.popularidad_train(con_split, [1, 2, 3, 4, 5, 6, 7])
    assert pop.to_dict() == {1: 0, 2: 0, 3: 0, 4: 2, 5: 1, 6: 0, 7: 0}
    assert list(pop.index) == [1, 2, 3, 4, 5, 6, 7] and pop.dtype == "int64"
    with pytest.raises(ValueError, match="split"):
        particion.popularidad_train(con_split.drop(columns="split"), [1, 2])
    with pytest.raises(ValueError, match="catálogo"):
        particion.popularidad_train(con_split, [4, 5])          # el 6 no está en el catálogo


def test_popularidad_train_es_invariante_a_val_y_prueba():
    cat = catalogo(45)["destino_id"]                          # 41..45 nunca aparecen en las interacciones
    con_split = particion.asignar_split(tabla({u: 1 + u % 7 for u in range(1, 60)}, n_destinos=40), 2)
    base = particion.popularidad_train(con_split, cat)
    assert len(base) == len(cat) and (base >= 0).all() and int(base.sum()) == int((con_split["split"] == TRAIN).sum())
    assert base.loc[41:45].tolist() == [0] * 5                # cubre todo el catálogo (0 si no aparece en train)
    for s in (VAL, PRUEBA):
        i = con_split.index[con_split["split"] == s][0]
        u = con_split.loc[i, "usuario_id"]
        libre = sorted(set(cat) - set(con_split.loc[con_split["usuario_id"] == u, "destino_id"]))[0]
        alterada = con_split.copy()
        alterada.loc[i, "destino_id"] = libre                  # otro destino en val/prueba
        assert particion.popularidad_train(alterada, cat).equals(base)
        assert particion.popularidad_train(con_split[con_split["split"] != s], cat).equals(base)   # eliminarlas
    # y SÍ cambia si se altera una de train (la prueba puede fallar)
    i = con_split.index[con_split["split"] == TRAIN][0]
    u = con_split.loc[i, "usuario_id"]
    libre = sorted(set(cat) - set(con_split.loc[con_split["usuario_id"] == u, "destino_id"]))[0]
    alterada = con_split.copy()
    alterada.loc[i, "destino_id"] = libre
    assert not particion.popularidad_train(alterada, cat).equals(base)


# --------------------------------------------------------------------------- candidatos (D10)
def _por_split(con_split: pd.DataFrame, u: int, splits) -> set[int]:
    m = (con_split["usuario_id"] == u) & con_split["split"].isin(splits)
    return set(con_split.loc[m, "destino_id"].astype(int))


def test_candidatos_de_prueba_excluyen_el_historial_conocido_y_contienen_el_objetivo():
    cat = catalogo(30)["destino_id"]
    con_split = particion.asignar_split(tabla({u: 1 + u % 7 for u in range(1, 60)}), 4)
    cand = particion.candidatos(con_split, cat, PRUEBA)
    rel = particion.relevantes(con_split, PRUEBA)
    conocido = particion.historial_conocido(con_split, PRUEBA)
    evaluables = set(con_split.loc[con_split["split"] == PRUEBA, "usuario_id"])
    assert set(cand) == set(rel) == evaluables
    for u, c in cand.items():
        c = set(c.tolist())
        assert conocido[u] == _por_split(con_split, u, [TRAIN, VAL])
        assert not (c & conocido[u])                        # F3: nada conocido entre los candidatos
        assert rel[u] == _por_split(con_split, u, [PRUEBA]) and rel[u] <= c
        assert len(c) == len(cat) - len(conocido[u])
        assert c <= set(cat)
    assert all(np.all(np.diff(c) > 0) for c in cand.values())   # ordenados y sin repetidos


def test_candidatos_de_validacion_solo_excluyen_train():
    cat = catalogo(30)["destino_id"]
    con_split = particion.asignar_split(tabla({u: 1 + u % 7 for u in range(1, 60)}), 4)
    cand = particion.candidatos(con_split, cat, VAL)
    assert set(cand) == set(con_split.loc[con_split["split"] == VAL, "usuario_id"])
    for u, c in cand.items():
        c = set(c.tolist())
        assert not (c & _por_split(con_split, u, [TRAIN]))
        assert _por_split(con_split, u, [VAL]) <= c
        assert _por_split(con_split, u, [PRUEBA]) <= c      # F4: validar no usa la prueba para excluir
        assert len(c) == len(cat) - len(_por_split(con_split, u, [TRAIN]))


def test_candidatos_a_mano():
    con_split = pd.DataFrame({"usuario_id": [1, 1, 1, 2, 2], "destino_id": [1, 2, 3, 2, 4],
                              "split": [TRAIN, VAL, PRUEBA, TRAIN, PRUEBA]})
    cand = particion.candidatos(con_split, [1, 2, 3, 4, 5], PRUEBA)
    assert {u: c.tolist() for u, c in cand.items()} == {1: [3, 4, 5], 2: [1, 3, 4, 5]}
    cand = particion.candidatos(con_split, [1, 2, 3, 4, 5], VAL)
    assert {u: c.tolist() for u, c in cand.items()} == {1: [2, 3, 4, 5]}
    with pytest.raises(ValueError, match="catálogo"):
        particion.candidatos(con_split, [1, 2, 3], PRUEBA)


# --------------------------------------------------------------------------- huella y resumen
def test_huella_a_mano():
    df = pd.DataFrame({"usuario_id": [2, 1], "destino_id": [5, 3], "split": [PRUEBA, TRAIN], "otra": ["x", "y"]})
    texto = "usuario_id,destino_id,split\n1,3,train\n2,5,prueba\n"
    assert particion.huella(df) == hashlib.sha256(texto.encode("utf-8")).hexdigest()
    assert particion.huella(df.iloc[::-1]) == particion.huella(df)                    # no depende del orden ni de otras columnas
    assert particion.huella(df.drop(columns="otra")) == particion.huella(df)
    assert particion.huella(df.assign(split=[VAL, TRAIN])) != particion.huella(df)    # sí del split


def test_resumen_y_diagnosticos_a_mano():
    """Catálogo 1..10 con lugar = id mod 5 ({1, 6}, {2, 7}, {3, 8}, {4, 9}, {5, 10}). Train de todos = {1, 2, 9, 4}.
    Usuario 1: train {1, 2}, val {3}, prueba {6}: 6 comparte lugar con 1 (conocido) → mismo lugar; 6 no está en train → frío.
    Usuario 2: train {9}, prueba {2}: el lugar de 2 es {2, 7} y 9 no es de él → no; 2 está en train (usuario 1) → no frío.
    Usuario 3: train {4}. Usuario 4: sin interacciones. Validación: destino 3 → frío; su lugar {3, 8} no está en el train
    del usuario 1 → no. Grupos con umbral 2: pocas = usuarios 2 (n=2) y 3 (n=1); muchas = usuario 1 (n=4).
    Esperado por azar del mismo lugar (5 lugares): prueba → usuario 1 conoce {1, 2, 3} = 3 lugares, usuario 2 conoce {9} = 1
    lugar → (3 + 1) / 5 = 0,8; validación → usuario 1 conoce en train {1, 2} = 2 lugares → 2 / 5 = 0,4."""
    con_split = pd.DataFrame({"usuario_id": [1, 1, 1, 1, 2, 2, 3], "destino_id": [1, 2, 3, 6, 9, 2, 4],
                              "origen": ["resena"] * 7, "id_origen": range(1, 8),
                              "split": [TRAIN, TRAIN, VAL, PRUEBA, TRAIN, PRUEBA, TRAIN]})
    r = particion.resumen_particion(con_split, catalogo(10), [1, 2, 3, 4], semilla=5, umbral_pocas_max=2,
                             sha256_parquet="abc")
    assert r["semilla"] == 5 and r["run_id"] == 0 and r["semilla_efectiva"] == 5
    c = r["conteos"]
    assert c["interacciones"] == {TRAIN: 4, VAL: 1, PRUEBA: 2, "total": 7}
    assert c["usuarios"] == {TRAIN: 3, VAL: 1, PRUEBA: 2, "con_interacciones": 3}
    assert c["usuarios_maestros"] == 4 and c["usuarios_sin_interacciones_no_evaluables"] == 1
    g = r["por_grupo_de_actividad"]
    assert g["umbral_pocas_max"] == 2 and "total" in g["nota"]
    assert g["pocas"]["n_usuarios"] == 2 and g["pocas"]["usuarios_con_prueba"] == 1
    assert g["pocas"]["interacciones"] == {TRAIN: 2, VAL: 0, PRUEBA: 1}
    assert g["muchas"]["n_usuarios"] == 1 and g["muchas"]["usuarios_con_validacion"] == 1
    assert g["muchas"]["interacciones"] == {TRAIN: 2, VAL: 1, PRUEBA: 1}
    d = r["diagnosticos"]
    assert d["items_frios"][PRUEBA] == {"interacciones": 2, "interacciones_con_destino_sin_train": 1,
                                        "destinos_distintos": 2, "destinos_distintos_sin_train": 1}
    assert d["items_frios"][VAL] == {"interacciones": 1, "interacciones_con_destino_sin_train": 1,
                                     "destinos_distintos": 1, "destinos_distintos_sin_train": 1}
    ml = d["mismo_lugar_en_historial_conocido"]
    assert ml[PRUEBA] == {"usuarios": 2, "con_otro_id_del_mismo_lugar": 1, "n_lugares": 5,
                          "esperado_por_azar": pytest.approx(0.8)}
    assert ml[VAL] == {"usuarios": 1, "con_otro_id_del_mismo_lugar": 0, "n_lugares": 5,
                       "esperado_por_azar": pytest.approx(0.4)}
    assert "esperable por azar" in ml["definicion"] and "esperado_por_azar" in ml["definicion"]
    assert "uniforme" in ml["supuesto_esperado_por_azar"]
    assert r["sha256"]["interacciones_parquet"] == "abc" and r["sha256"]["huella"] == particion.huella(con_split)
    assert "usuario_id,destino_id,split" in r["sha256"]["huella_formato"]


def test_esperado_por_azar_del_mismo_lugar_cuenta_lugares_distintos_no_destinos():
    """Catálogo 1..10, lugar = id mod 5. Usuario 1: train {1, 6, 2} (lugares {1, 2}: 2 lugares con 3 destinos), prueba {3}
    (lugar 3: no coincide). Usuario 2: train {4}, prueba {9} (lugar 4: coincide). Observado 1; esperado (2 + 1) / 5 = 0,6
    (contar destinos en vez de lugares daría (3 + 1) / 5 = 0,8)."""
    con_split = pd.DataFrame({"usuario_id": [1, 1, 1, 1, 2, 2], "destino_id": [1, 6, 2, 3, 4, 9],
                              "origen": ["resena"] * 6, "id_origen": range(1, 7),
                              "split": [TRAIN, TRAIN, TRAIN, PRUEBA, TRAIN, PRUEBA]})
    r = particion.resumen_particion(con_split, catalogo(10), [1, 2], semilla=0, umbral_pocas_max=2, sha256_parquet="x")
    ml = r["diagnosticos"]["mismo_lugar_en_historial_conocido"]
    assert ml[PRUEBA] == {"usuarios": 2, "con_otro_id_del_mismo_lugar": 1, "n_lugares": 5,
                          "esperado_por_azar": pytest.approx(0.6)}
    assert ml[VAL] == {"usuarios": 0, "con_otro_id_del_mismo_lugar": 0, "n_lugares": 5, "esperado_por_azar": 0.0}
    # la línea base supone un objetivo por usuario (D3): dos en prueba es error claro
    dos = con_split.assign(split=[TRAIN, TRAIN, PRUEBA, PRUEBA, TRAIN, PRUEBA])
    with pytest.raises(ValueError, match="un objetivo por usuario"):
        particion.resumen_particion(dos, catalogo(10), [1, 2], semilla=0, umbral_pocas_max=2, sha256_parquet="x")


# --------------------------------------------------------------------------- integración con m3-datos (fixtures)
def _resumen(tmp_path: Path) -> Path:
    return tmp_path / "part" / "resumen.json"


def test_main_escribe_split_y_resumen_con_los_fixtures(tmp_path):
    cfg = montar(tmp_path)
    assert dm.main(cfg) == 0
    inter = pd.read_parquet(salidas(tmp_path)["interacciones"])
    assert list(inter.columns) == [*BASE, "split"]
    verificar_d3(inter.drop(columns="split"), inter)
    # a mano (test_datos_m3.py): usuarios 1..5 con 3, 2, 2, 1, 0 → train 1+1+1+1, validación 1, prueba 3
    assert inter["split"].value_counts().to_dict() == {TRAIN: 4, VAL: 1, PRUEBA: 3}
    r = json.loads(_resumen(tmp_path).read_text(encoding="utf-8"))
    assert r["sha256"]["interacciones_parquet"] == hashlib.sha256(salidas(tmp_path)["interacciones"].read_bytes()).hexdigest()
    assert r["sha256"]["huella"] == particion.huella(inter)
    assert r["conteos"]["usuarios_sin_interacciones_no_evaluables"] == 1
    assert r["semilla"] == cfg["particion"]["semilla"]
    # la calidad y la ficha describen las columnas de la fuente; split no entra en ellas
    cal = pd.read_csv(salidas(tmp_path)["calidad"])
    assert "split" not in set(cal["columna"])


def test_main_es_determinista_con_la_particion(tmp_path):
    cfg = montar(tmp_path)
    dm.main(cfg)
    rutas = [*salidas(tmp_path).values(), _resumen(tmp_path)]
    primera = {p: p.read_bytes() for p in rutas}
    dm.main(cfg)
    assert {p: p.read_bytes() for p in rutas} == primera
    texto = _resumen(tmp_path).read_text(encoding="utf-8")
    assert str(tmp_path) not in texto and str(tmp_path.as_posix()) not in texto   # sin rutas absolutas


def test_main_sin_bloque_particion_es_error_claro(tmp_path):
    cfg = montar(tmp_path, cfg_extra=lambda c: c.pop("particion"))
    with pytest.raises(ValueError, match="particion"):
        dm.main(cfg)
    assert not (tmp_path / "proc").exists()


@pytest.mark.parametrize("cambio, error, patron", [
    (lambda c: c["particion"].pop("semilla"), ValueError, "faltan las claves.*semilla"),
    (lambda c: c["particion"].update(semilla="7"), TypeError, "particion.semilla"),
    (lambda c: c["particion"].update(semilla=-1), ValueError, "particion.semilla"),
    (lambda c: c["salida"].pop("particion"), ValueError, "salida.particion"),
], ids=["falta_semilla", "semilla_texto", "semilla_negativa", "falta_salida_particion"])
def test_leer_config_particion_da_errores_claros(tmp_path, cambio, error, patron):
    cfg = montar(tmp_path, cfg_extra=cambio)
    with pytest.raises(error, match=patron):
        dm.leer_config_particion(cfg)
    with pytest.raises(error, match=patron):
        dm.main(cfg)
    assert not (tmp_path / "proc").exists()               # se valida antes de escribir nada


def test_main_con_umbral_invalido_es_error_claro(tmp_path):
    cfg = montar(tmp_path, cfg_extra=lambda c: c["particion"].update(umbral_pocas_max=0))
    with pytest.raises(ValueError, match="umbral_pocas_max"):
        dm.main(cfg)


def test_semilla_distinta_en_main_cambia_la_huella_no_las_cantidades(tmp_path):
    r = {}
    for s in (0, 1, 2, 3):
        d = tmp_path / str(s)
        d.mkdir()
        dm.main(montar(d, cfg_extra=lambda c, s=s: c["particion"].update(semilla=s)))
        r[s] = json.loads(_resumen(d).read_text(encoding="utf-8"))
    assert len({x["sha256"]["huella"] for x in r.values()}) > 1
    assert len({json.dumps(x["conteos"], sort_keys=True) for x in r.values()}) == 1


# --------------------------------------------------------------------------- configs
def test_el_umbral_de_la_particion_es_el_mismo_del_descriptivo():
    datos = yaml.safe_load(CFG_DATOS.read_text(encoding="utf-8"))
    eda = yaml.safe_load(CFG_EDA.read_text(encoding="utf-8"))
    assert datos["particion"]["umbral_pocas_max"] == eda["actividad"]["pocas_max"]
    assert isinstance(datos["particion"]["semilla"], int) and not isinstance(datos["particion"]["semilla"], bool)
    assert datos["salida"]["particion"] == "results/data/m3/particion"


# --------------------------------------------------------------------------- datos reales (si están)
REQUERIDOS_REALES = [PROCESADOS / "interacciones.parquet", PROCESADOS / "usuarios.parquet", PROCESADOS / "destinos.parquet",
                     RESUMEN_REAL, ACTIVIDAD_REAL]
FALTANTES_REALES = [r.relative_to(RAIZ).as_posix() for r in REQUERIDOS_REALES if not r.exists()]
real = pytest.mark.skipif(bool(FALTANTES_REALES), reason=f"faltan archivos de los datos reales: {FALTANTES_REALES}")
# Cifras escritas en la spec (docs/spec/partes/juanjose.md §3.1) que las pruebas reales contrastan con lo medido:
DESTINOS_CATALOGO_D2 = 1000           # D2: «Destino = los 1 000 DestinationID»
USUARIOS_SIN_INTERACCIONES_D10 = 141  # D10: «Los usuarios sin interacciones (141 de 999) no se evalúan»


@real
def test_real_el_parquet_cumple_d3_y_corresponde_a_la_semilla_de_la_config():
    inter = pd.read_parquet(PROCESADOS / "interacciones.parquet")
    assert "split" in inter.columns
    original = inter.drop(columns="split")
    verificar_d3(original, inter)
    semilla = yaml.safe_load(CFG_DATOS.read_text(encoding="utf-8"))["particion"]["semilla"]
    assert particion.asignar_split(original, semilla)["split"].equals(inter["split"])


@real
def test_real_los_conteos_coinciden_con_particion_d3_del_descriptivo():
    inter = pd.read_parquet(PROCESADOS / "interacciones.parquet")
    act = json.loads(ACTIVIDAD_REAL.read_text(encoding="utf-8"))
    d3, p_max = act["particion_d3"], act["umbral"]["pocas_max"]
    nombres = {"entrenamiento": TRAIN, "validacion": VAL, "prueba": PRUEBA}
    assert inter["split"].value_counts().to_dict() == {nombres[k]: v for k, v in d3["total"].items()}
    n = inter.groupby("usuario_id").size()
    grupo = inter["usuario_id"].map(lambda u: "pocas" if n[u] <= p_max else "muchas")
    for g in ("pocas", "muchas"):
        sub = inter[grupo == g]
        cuenta = sub["split"].value_counts().reindex([TRAIN, VAL, PRUEBA], fill_value=0).to_dict()
        assert cuenta == {nombres[k]: v for k, v in d3[g]["interacciones"].items()}
        assert sub.loc[sub["split"] == PRUEBA, "usuario_id"].nunique() == d3[g]["usuarios_con_prueba"]
        assert sub.loc[sub["split"] == VAL, "usuario_id"].nunique() == d3[g]["usuarios_con_validacion"]


@real
def test_real_el_resumen_coincide_con_lo_recalculado_desde_el_parquet():
    ruta = PROCESADOS / "interacciones.parquet"
    inter = pd.read_parquet(ruta)
    cfg = yaml.safe_load(CFG_DATOS.read_text(encoding="utf-8"))["particion"]
    r = json.loads(RESUMEN_REAL.read_text(encoding="utf-8"))
    sha_parquet = hashlib.sha256(ruta.read_bytes()).hexdigest()
    assert r["sha256"]["interacciones_parquet"] == sha_parquet
    assert r["sha256"]["huella"] == particion.huella(inter)
    usuarios = pd.read_parquet(PROCESADOS / "usuarios.parquet")["usuario_id"]
    destinos = pd.read_parquet(PROCESADOS / "destinos.parquet")
    recalculado = particion.resumen_particion(inter, destinos, usuarios, semilla=cfg["semilla"],
                                       umbral_pocas_max=cfg["umbral_pocas_max"], sha256_parquet=sha_parquet)
    assert json.loads(json.dumps(recalculado)) == r
    # n_lugares y esperado_por_azar, recalculados aquí sin pasar por particion.py
    lugar = destinos.set_index("destino_id")["lugar"]
    n_lugares = lugar.nunique()
    for s, conocidos in ((PRUEBA, [TRAIN, VAL]), (VAL, [TRAIN])):
        ml = r["diagnosticos"]["mismo_lugar_en_historial_conocido"][s]
        evaluables = inter.loc[inter["split"] == s, "usuario_id"].unique()
        conocido = inter[inter["split"].isin(conocidos)]
        lugares = conocido.assign(lugar=conocido["destino_id"].map(lugar)).groupby("usuario_id")["lugar"].nunique()
        assert ml["n_lugares"] == n_lugares
        assert ml["esperado_por_azar"] == pytest.approx(lugares.reindex(evaluables, fill_value=0).sum() / n_lugares)


@real
def test_real_popularidad_y_candidatos_sin_fuga():
    inter = pd.read_parquet(PROCESADOS / "interacciones.parquet")
    cat = pd.read_parquet(PROCESADOS / "destinos.parquet")["destino_id"]
    pop = particion.popularidad_train(inter, cat)
    assert len(pop) == len(cat) == DESTINOS_CATALOGO_D2 and int(pop.sum()) == int((inter["split"] == TRAIN).sum())
    assert pop.equals(particion.popularidad_train(inter[inter["split"] == TRAIN], cat))
    cand, conocido = particion.candidatos(inter, cat, PRUEBA), particion.historial_conocido(inter, PRUEBA)
    rel = particion.relevantes(inter, PRUEBA)
    for u, c in cand.items():
        c = set(c.tolist())
        assert not (c & conocido[u]) and rel[u] <= c and len(c) == len(cat) - len(conocido[u])


# --------------------------------------------------------------------------- guardas para JJ-4 / JJ-5 (auditor-fugas, JJ-3)
# Cualquier ajuste de un modelo de M3 (popularidad, FC clásico, red, muestreo de negativos…) recibe la tabla CON ``split`` y
# el catálogo y devuelve algo comparable con ``==`` tras ``np.asarray`` (vector de puntajes, embeddings con semilla fija,
# negativos muestreados con un generador fijo…). JJ-4 y JJ-5 AGREGAN aquí sus funciones de ajuste: la prueba exige que la
# salida no cambie si se alteran o se eliminan las interacciones de validación y de prueba (D9: «solo con train»).
def _ajuste_popularidad(inter, cat):
    """JJ-4: puntajes de ``referencias.Popularidad`` (semilla fija) para un usuario cualquiera."""
    return referencias.Popularidad().ajustar(inter, cat, make_rng(0, 0)).puntuar([1])


def _ajuste_mf_als(inter, cat):
    """JJ-4: factores (usuarios y destinos) de ``referencias.MFImplicitaALS`` con semilla fija y pocos hiperparámetros."""
    m = referencias.MFImplicitaALS(factores=4, regularizacion=0.1, alfa=10.0, iteraciones=3, escala_inicial=0.01)
    m.ajustar(inter, cat, make_rng(0, 0))
    return np.concatenate([m.X.ravel(), m.Y.ravel()])


def _ajuste_aleatorio(inter, cat):
    """JJ-4: puntajes de ``referencias.Aleatorio`` (semilla fija); hoy no lee ``inter``, la guarda vigila que siga así."""
    return referencias.Aleatorio().ajustar(inter, cat, make_rng(0, 0)).puntuar([1, 2])


# ---- JJ-5: la red de dos torres. Contenido sintético (tipo de destino y preferencias del usuario); no depende de las
# interacciones, así que no puede filtrar validación ni prueba.
TIPOS_SINT = ["Adventure", "Beach", "City", "Historical", "Nature"]
COMBOS_SINT = [("pref_beaches", "pref_historical"), ("pref_adventure", "pref_nature"), ("pref_city", "pref_historical")]
HP_RED = {"modelo.dim_embedding": 4, "modelo.capas_usuario": 1, "modelo.unidades_usuario": 8, "modelo.capas_destino": 1,
          "modelo.unidades_destino": 8, "modelo.usar_id_usuario": True, "modelo.usar_id_destino": True,
          "modelo.dropout_id": 0.2, "modelo.negativos_por_positivo": 2, "modelo.usar_demografia": False,
          "perdida.tipo": "bce", "entrenamiento.lr": 0.01, "entrenamiento.max_epocas": 4, "entrenamiento.paciencia": 2,
          "entrenamiento.tam_lote": 32, "regularizacion.weight_decay": 1e-4, "regularizacion.dropout": 0.1}


def _destinos_sint(n: int = 45) -> pd.DataFrame:
    ids = np.arange(1, n + 1)
    return pd.DataFrame({"destino_id": ids, "lugar": [f"lugar_{i % 5}" for i in ids], "tipo": [TIPOS_SINT[i % 5] for i in ids]})


def _usuarios_sint(n: int = 70) -> pd.DataFrame:
    ids = np.arange(1, n + 1)
    df = pd.DataFrame({"usuario_id": ids})
    for col in contenido.COLUMNAS_PREFERENCIAS:
        df[col] = [col in COMBOS_SINT[u % 3] for u in ids]
    return df


def _red(usar_validacion: bool, **hp) -> red.RedDosTorres:
    return red.RedDosTorres({**HP_RED, **hp}, contenido.contenido_usuarios(_usuarios_sint()),
                            contenido.contenido_destinos(_destinos_sint()), usar_validacion=usar_validacion)


def _ajuste_red_negativos(inter, cat):
    """JJ-5 (D17): negativos de una época por el MISMO camino de ajustar (preparar_train + sortear_epoca), generador fijo."""
    usuarios, positivos, negativos = red.negativos_train(inter, cat, 3, make_rng(0, 0))
    return np.concatenate([usuarios, positivos, negativos.ravel()])


def _pesos(m: red.RedDosTorres) -> np.ndarray:
    return np.concatenate([v.detach().numpy().ravel() for v in m.red.state_dict().values()])


def _ajuste_red_epocas_fijas(inter, cat):
    """JJ-5 (D19): la red entrenada a épocas fijas, SIN parada temprana (semilla fija): sus pesos solo dependen de train."""
    return _pesos(_red(usar_validacion=False).ajustar(inter, cat, make_rng(0, 0)))


AJUSTES_SOLO_TRAIN = {
    "popularidad_train": lambda inter, cat: particion.popularidad_train(inter, cat),
    "referencias.popularidad": _ajuste_popularidad,
    "referencias.mf_als": _ajuste_mf_als,
    "referencias.aleatorio": _ajuste_aleatorio,
    "red.negativos": _ajuste_red_negativos,
    "red.entrenamiento_epocas_fijas": _ajuste_red_epocas_fijas,
}


def _alterar_no_train(con_split: pd.DataFrame, cat: pd.Series, split: str) -> pd.DataFrame:
    """Cambia el destino de TODAS las interacciones de ``split`` por otro libre del mismo usuario (pares siguen únicos)."""
    alterada = con_split.copy()
    for i in alterada.index[alterada["split"] == split]:
        u = alterada.loc[i, "usuario_id"]
        libres = sorted(set(cat) - set(alterada.loc[alterada["usuario_id"] == u, "destino_id"]))
        alterada.loc[i, "destino_id"] = libres[-1]
    return alterada


@pytest.mark.parametrize("nombre", sorted(AJUSTES_SOLO_TRAIN))
def test_todo_ajuste_de_modelo_es_invariante_a_validacion_y_prueba(nombre):
    ajustar = AJUSTES_SOLO_TRAIN[nombre]
    cat = catalogo(45)["destino_id"]
    con_split = particion.asignar_split(tabla({u: 1 + u % 7 for u in range(1, 60)}, n_destinos=40), 2)
    base = np.asarray(ajustar(con_split, cat))
    for s in (VAL, PRUEBA):
        assert np.array_equal(np.asarray(ajustar(_alterar_no_train(con_split, cat, s), cat)), base), f"{nombre} usa {s}"
        assert np.array_equal(np.asarray(ajustar(con_split[con_split["split"] != s], cat)), base), f"{nombre} usa {s}"


ARCHIVOS_DESCRIPTIVOS_M3 = {"datos.py", "eda.py", "eda_estadistica.py", "eda_hipotesis.py", "particion.py", "__init__.py"}
# Salidas que se calculan con TODAS las interacciones (train + validación + prueba): son descriptivas (JJ-2) o diagnósticos de
# la partición (JJ-3) y ningún modelo puede leerlas (D9). resumen.json solo puede leerse por su bloque ``sha256`` (evidencia).
PROHIBIDAS_PARA_MODELOS = ("results/data/m3/eda", "interacciones_por_destino", "interacciones_por_usuario",
                           "interacciones_por_lugar", "distribucion_actividad", "actividad_usuarios", "concentracion.json",
                           "particion_d3", "grupo_actividad", "items_frios", "mismo_lugar_en_historial_conocido")


def test_ningun_modelo_de_m3_lee_estadisticas_calculadas_con_todas_las_interacciones():
    """Guarda estática: hoy no hay modelos y pasa trivialmente; desde JJ-4 vigila cada archivo nuevo de src/m3_recomendacion."""
    carpeta = RAIZ / "src" / "m3_recomendacion"
    infractores = {}
    for f in sorted(carpeta.rglob("*.py")):
        if f.name in ARCHIVOS_DESCRIPTIVOS_M3:
            continue
        texto = f.read_text(encoding="utf-8")
        malas = [p for p in PROHIBIDAS_PARA_MODELOS if p in texto]
        if malas:
            infractores[f.relative_to(RAIZ).as_posix()] = malas
    assert not infractores, f"modelos que leen estadísticas con validación/prueba: {infractores}"


# Guarda propuesta por el auditor-fugas en JJ-4: los modelos reciben todo por ``ajustar(inter, catalogo, rng)``; no abren
# parquet ni JSON (la fábrica recibe el cfg completo, con rutas) ni leen salidas de evaluación calculadas con prueba (D9).
# No va en PROHIBIDAS_PARA_MODELOS porque experimento.py escribe esas salidas con razón.
ARCHIVOS_DE_MODELO_M3 = {"referencias.py", "red.py"}   # JJ-5: la red (su contenido lo lee contenido.py, ver abajo)
SALIDAS_DE_EVALUACION_M3 = ("recomendaciones_prueba", "summary.json", "metricas_por_k.json", "metricas_por_grupo.json",
                            "semillas/")
LECTURAS_DE_ARCHIVOS = ("read_parquet", "load_json", "open(", "read_csv", "np.load", "read_text", "read_bytes", "torch.load")


def test_los_modelos_no_leen_archivos_ni_salidas_de_evaluacion():
    carpeta = RAIZ / "src" / "m3_recomendacion"
    for nombre in sorted(ARCHIVOS_DE_MODELO_M3):
        texto = (carpeta / nombre).read_text(encoding="utf-8")
        assert not [p for p in SALIDAS_DE_EVALUACION_M3 if p in texto], f"{nombre} lee salidas de evaluación"
        assert not [p for p in LECTURAS_DE_ARCHIVOS if p in texto], f"{nombre} abre archivos por su cuenta"


@real
def test_real_usuarios_sin_interacciones_o_con_una_no_se_evaluan():
    inter = pd.read_parquet(PROCESADOS / "interacciones.parquet")
    cat = pd.read_parquet(PROCESADOS / "destinos.parquet")["destino_id"]
    maestros = set(pd.read_parquet(PROCESADOS / "usuarios.parquet")["usuario_id"])
    n = inter.groupby("usuario_id").size()
    sin = maestros - set(n.index)
    resumen = json.loads(RESUMEN_REAL.read_text(encoding="utf-8"))
    assert len(sin) == USUARIOS_SIN_INTERACCIONES_D10 == resumen["conteos"]["usuarios_sin_interacciones_no_evaluables"]
    cand_p, cand_v = particion.candidatos(inter, cat, PRUEBA), particion.candidatos(inter, cat, VAL)
    assert not (sin & set(cand_p)) and not (sin & set(cand_v))
    assert set(cand_p) == set(n[n >= 2].index) and set(cand_v) == set(n[n >= 3].index)


# --------------------------------------------------------------------------- guardas de la red (JJ-5)
# AJUSTES_SIN_PRUEBA: ajustes que SÍ usan validación (solo para la parada temprana y para elegir hiperparámetros, D9) y por
# eso no están en AJUSTES_SOLO_TRAIN; su salida no puede cambiar si se alteran o se eliminan las interacciones de PRUEBA.
def _escribir_contenido(carpeta: Path) -> dict:
    carpeta.mkdir(parents=True, exist_ok=True)
    _destinos_sint().to_parquet(carpeta / "destinos.parquet", index=False)
    _usuarios_sint().to_parquet(carpeta / "usuarios.parquet", index=False)
    cfg = load_config(CFG_DATOS.parent / "hpo.yaml")
    sets = [f"datos.carpeta={carpeta.as_posix()}", "busqueda.n_ensayos=2", "entrenamiento.max_epocas=3",
            "entrenamiento.paciencia=1", "evaluacion.k=[5, 10]"]
    return apply_overrides(cfg, sets)


def _ajuste_red_completo(inter, cat, carpeta):
    """La red con parada temprana por NDCG@5 de validación: puntajes de 3 usuarios y curvas."""
    m = _red(usar_validacion=True).ajustar(inter, cat, make_rng(0, 0))
    curvas = [x for clave in ("perdida_train", "perdida_validacion", "ndcg5_validacion") for x in m.curvas[clave]]
    return np.concatenate([m.puntuar([1, 2, 3]).ravel(), np.asarray(curvas, dtype=float), [m.curvas["mejor_epoca"]]])


def _busqueda_red(inter, cat, carpeta):
    """La búsqueda Optuna de la red (2 ensayos): parámetros y métricas de validación de cada ensayo (sin tiempos)."""
    fam = hpo.buscar_red(_escribir_contenido(carpeta), inter, cat)
    return np.asarray([json.dumps({k: v for k, v in e.items() if k != "tiempo_s"}, sort_keys=True) for e in fam["ensayos"]])


AJUSTES_SIN_PRUEBA = {
    "red.ajuste_con_parada_temprana": _ajuste_red_completo,
    "hpo.buscar_red": _busqueda_red,
}


@pytest.mark.parametrize("nombre", sorted(AJUSTES_SIN_PRUEBA))
def test_la_red_y_su_busqueda_son_invariantes_a_prueba(nombre, tmp_path):
    ajustar = AJUSTES_SIN_PRUEBA[nombre]
    cat = catalogo(45)["destino_id"]
    con_split = particion.asignar_split(tabla({u: 1 + u % 7 for u in range(1, 60)}, n_destinos=40), 2)
    base = np.asarray(ajustar(con_split, cat, tmp_path / "a"))
    assert np.array_equal(np.asarray(ajustar(_alterar_no_train(con_split, cat, PRUEBA), cat, tmp_path / "b")), base)
    assert np.array_equal(np.asarray(ajustar(con_split[con_split["split"] != PRUEBA], cat, tmp_path / "c")), base)


def test_la_validacion_solo_elige_la_epoca_de_parada():
    """D9: la validación entra a la red SOLO por la parada temprana. Los pesos del ajuste completo (con validación) son
    exactamente los de un entrenamiento sin validación con max_epocas = mejor época: validación no toca el gradiente, los
    negativos ni el dropout; solo decide en qué época se queda la red."""
    cat = catalogo(45)["destino_id"]
    con_split = particion.asignar_split(tabla({u: 1 + u % 7 for u in range(1, 60)}, n_destinos=40), 2)
    completo = _red(usar_validacion=True, **{"entrenamiento.max_epocas": 12}).ajustar(con_split, cat, make_rng(0, 0))
    mejor = completo.curvas["mejor_epoca"]
    fijo = _red(usar_validacion=False, **{"entrenamiento.max_epocas": mejor}).ajustar(con_split, cat, make_rng(0, 0))
    assert np.array_equal(_pesos(completo), _pesos(fijo))
    assert np.array_equal(completo.puntuar([1, 2, 3]), fijo.puntuar([1, 2, 3]))


def test_los_indices_de_id_y_el_dropout_de_id_solo_usan_train():
    """El índice de id (y por lo tanto el «dropout de id», que solo pone índices en 0) sale solo de train: un usuario o un
    destino que solo aparece en validación o prueba recibe 0, y alterar o eliminar esos splits no cambia ningún índice."""
    cat = catalogo(45)["destino_id"]
    con_split = particion.asignar_split(tabla({u: 1 + u % 7 for u in range(1, 60)}, n_destinos=40), 2)
    mapa, idx = red.indices_de_id(con_split, cat)
    train = con_split[con_split["split"] == TRAIN]
    assert set(mapa) == set(train["usuario_id"].astype(int)) and sorted(mapa.values()) == list(range(1, len(mapa) + 1))
    con_train = set(train["destino_id"].astype(int))
    assert all((idx[j] > 0) == (int(d) in con_train) for j, d in enumerate(cat))
    for s in (VAL, PRUEBA):
        for otra in (_alterar_no_train(con_split, cat, s), con_split[con_split["split"] != s]):
            m2, i2 = red.indices_de_id(otra, cat)
            assert m2 == mapa and np.array_equal(i2, idx), f"los índices de id usan {s}"
    extra = pd.concat([con_split, pd.DataFrame({"usuario_id": [900, 901], "destino_id": [44, 45], "split": [VAL, PRUEBA]})])
    m3, i3 = red.indices_de_id(extra, cat)
    assert 900 not in m3 and 901 not in m3 and i3[list(cat).index(44)] == 0 and i3[list(cat).index(45)] == 0
    out = red.aplicar_dropout_id(np.array(sorted(mapa.values())), 0.5, make_rng(0, 0))
    assert set(out.tolist()) <= {0} | set(mapa.values())


def test_contenido_no_lee_interacciones_ni_salidas():
    """contenido.py lee SOLO destinos y usuarios (atributos de la fuente): ninguna interacción, ningún resultado ni ninguna
    estadística calculada con todas las interacciones (D9, D15)."""
    texto = (RAIZ / "src" / "m3_recomendacion" / "contenido.py").read_text(encoding="utf-8")
    prohibidas = ("interacciones", "results/", "popularidad", *PROHIBIDAS_PARA_MODELOS, *SALIDAS_DE_EVALUACION_M3)
    assert not [p for p in prohibidas if p in texto]


# --------------------------------------------------------------------------- guardas dinámicas (auditor-fugas, JJ-5)
# Las guardas de arriba sobre el texto de red.py y contenido.py se evaden con una cadena partida («inter" "acciones»,
# «recomendaciones" + "_prueba») o con un lector que no está en la lista (``pyarrow.parquet.read_table``) envuelto en
# try/except. Estas dos pruebas miran lo que el código HACE, no lo que dice.
def _inter_con_split_en(carpeta: Path, con_split: pd.DataFrame, nombre: str = "interacciones.parquet") -> Path:
    ruta = carpeta / nombre
    con_split.to_parquet(ruta, index=False)
    return ruta


def test_contenido_es_invariante_a_las_interacciones_de_su_misma_carpeta(tmp_path, monkeypatch):
    """F8 dinámica: con un ``interacciones.parquet`` real (con ``split``) en la carpeta y la ruta en ``cfg["datos"]``, el
    contenido no cambia si se alteran sus filas de prueba o de validación o si el archivo desaparece, y ``cargar_contenido``
    solo pide a pandas los dos archivos de contenido."""
    carpeta = tmp_path / "proc"
    carpeta.mkdir()
    _destinos_sint().to_parquet(carpeta / "destinos.parquet", index=False)
    _usuarios_sint().to_parquet(carpeta / "usuarios.parquet", index=False)
    cfg = {"datos": {"carpeta": carpeta.as_posix(), "destinos": "destinos.parquet", "usuarios": "usuarios.parquet",
                     "interacciones": "interacciones.parquet"}}
    cat = _destinos_sint()["destino_id"]
    con_split = particion.asignar_split(tabla({u: 1 + u % 7 for u in range(1, 60)}, n_destinos=40), 2)

    def foto():
        cu, ci = contenido.cargar_contenido(cfg, usar_demografia=False)
        return [cu.ids.tolist(), cu.X.tolist(), list(cu.columnas), ci.ids.tolist(), ci.X.tolist(), list(ci.columnas)]

    ruta = _inter_con_split_en(carpeta, con_split)
    leidos: list[str] = []
    original = pd.read_parquet

    def espia(path, *a, **k):
        leidos.append(Path(path).name)
        return original(path, *a, **k)

    monkeypatch.setattr(pd, "read_parquet", espia)
    base = foto()
    assert sorted(leidos) == ["destinos.parquet", "usuarios.parquet"], leidos
    for s in (VAL, PRUEBA):
        _inter_con_split_en(carpeta, _alterar_no_train(con_split, cat, s))
        assert foto() == base, f"el contenido cambia al alterar {s}"
    ruta.unlink()
    assert foto() == base, "el contenido cambia si no está el archivo de interacciones"


def test_la_red_no_abre_archivos_al_ajustar_puntuar_ni_diagnosticar(monkeypatch):
    """La red recibe todo por ``ajustar(inter, catalogo, rng)``: durante ajustar, puntuar, diagnosticos, n_parametros y
    arquitectura no abre ningún archivo del repositorio (open / io.open / Path.open) ni llama a un lector de pandas, pyarrow,
    numpy o torch. Cada intento se REGISTRA (y además falla), así que un ``try/except`` en el código no lo esconde."""
    import builtins
    import io

    import pyarrow.parquet as pq
    import torch

    intentos: list[str] = []
    venv = (RAIZ / ".venv").resolve()
    abrir, abrir_io = builtins.open, io.open

    def vigilar(real):
        def envoltura(archivo, *a, **k):
            if isinstance(archivo, (str, Path)):
                p = Path(archivo).resolve()
                if p.is_relative_to(RAIZ) and not p.is_relative_to(venv):
                    intentos.append(f"open {p}")
                    raise PermissionError(f"la red intentó abrir {p}")
            return real(archivo, *a, **k)
        return envoltura

    def prohibido(nombre):
        def lector(*a, **k):
            intentos.append(nombre)
            raise PermissionError(f"la red llamó a {nombre}")
        return lector

    cat = catalogo(45)["destino_id"]
    con_split = particion.asignar_split(tabla({u: 1 + u % 7 for u in range(1, 60)}, n_destinos=40), 2)
    m = _red(usar_validacion=True)
    monkeypatch.setattr(builtins, "open", vigilar(abrir))
    monkeypatch.setattr(io, "open", vigilar(abrir_io))
    for modulo, nombre in ((pd, "read_parquet"), (pd, "read_csv"), (pd, "read_json"), (pd, "read_pickle"),
                           (pq, "read_table"), (np, "load"), (np, "loadtxt"), (torch, "load")):
        monkeypatch.setattr(modulo, nombre, prohibido(f"{modulo.__name__}.{nombre}"))
    m.ajustar(con_split, cat, make_rng(0, 0))
    m.puntuar([1, 2, 3])
    m.diagnosticos()
    m.n_parametros()
    m.arquitectura()
    monkeypatch.undo()
    assert not intentos, f"la red abrió archivos por su cuenta: {intentos}"
