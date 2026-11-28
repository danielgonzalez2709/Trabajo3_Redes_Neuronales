"""Pruebas sin red de la red de dos torres de M3 (JJ-5; D15–D19 de docs/spec/partes/juanjose.md §3.2; núcleo §5.9, §6).

Formulación que estas pruebas FIJAN (docstring de ``src/m3_recomendacion/red.py``):
  u = MLP_U(x_u) + E_U[k(u)] ∈ R^d;  [v_i; b_i] = MLP_I(x_i) + E_I[k(i)] ∈ R^{d+1};  s_ui = ⟨u, v_i⟩ + b_i  (logit)
  k(·) = índice de id construido SOLO con train (0 = «sin id», fila fija en cero).
  BCE = −1/(B(1+m)) [Σ_b log σ(s⁺_b) + Σ_{b,j} log(1 − σ(s⁻_bj))]  = media de softplus(−s⁺) y softplus(s⁻)
  BPR = −1/(B·m) Σ_{b,j} log σ(s⁺_b − s⁻_bj)                       = media de softplus(−(s⁺ − s⁻))

Cálculo a mano (con softplus(x) = log(1 + eˣ)) para s⁺ = [2, −1] y s⁻ = [[0,5, −0,5], [1, 0]] (B = 2, m = 2):
  BCE: softplus(−2) = 0,126928; softplus(1) = 1,313262; softplus(0,5) = 0,974077; softplus(−0,5) = 0,474077;
       softplus(1) = 1,313262; softplus(0) = 0,693147 → suma 4,894753 / 6 = 0,815792
  BPR: diferencias 1,5; 2,5; −2; −1 → softplus(−1,5) = 0,201413; softplus(−2,5) = 0,078890; softplus(2) = 2,126928;
       softplus(1) = 1,313262 → suma 3,720493 / 4 = 0,930123

Conteo a mano de parámetros (``test_n_parametros_contra_un_conteo_a_mano``): x_u de 5, 1 capa de 4 unidades, d = 3, 2 usuarios
con train; x_i de 5, 0 capas, 3 destinos con train:
  torre de usuario: Linear(5→4) = 5·4 + 4 = 24; Linear(4→3) = 4·3 + 3 = 15; Embedding(2+1, 3) = 9 − 3 (fila 0 fija) = 6
  torre de destino: Linear(5→4) = 5·4 + 4 = 24 (salida d + 1 = 4); Embedding(3+1, 4) = 16 − 4 (fila 0 fija) = 12
  total = 24 + 15 + 6 + 24 + 12 = 81
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from src.comun.config import apply_overrides, load_config
from src.comun.results import load_json
from src.comun.seeds import make_rng
from src.m3_recomendacion import contenido, experimento, hpo, particion, red
from test_fuga_m3 import tabla
from test_metricas_m3 import montar_sintetico

RAIZ = Path(__file__).resolve().parents[1]
CFG_BASE = RAIZ / "configs" / "m3" / "base.yaml"
CFG_HPO = RAIZ / "configs" / "m3" / "hpo.yaml"
CFG_DEMO = RAIZ / "configs" / "m3" / "demo.yaml"
TIPOS = ["Adventure", "Beach", "City", "Historical", "Nature"]
COMBOS = [("pref_beaches", "pref_historical"), ("pref_adventure", "pref_nature"), ("pref_city", "pref_historical")]

# Hiperparámetros pequeños para las pruebas (claves con punto, como en la config).
HP = {"modelo.dim_embedding": 4, "modelo.capas_usuario": 1, "modelo.unidades_usuario": 8, "modelo.capas_destino": 1,
      "modelo.unidades_destino": 8, "modelo.usar_id_usuario": True, "modelo.usar_id_destino": True, "modelo.dropout_id": 0.2,
      "modelo.negativos_por_positivo": 2, "modelo.usar_demografia": False, "perdida.tipo": "bce", "entrenamiento.lr": 0.01,
      "entrenamiento.max_epocas": 6, "entrenamiento.paciencia": 3, "entrenamiento.tam_lote": 32,
      "regularizacion.weight_decay": 1e-4, "regularizacion.dropout": 0.1}


# =========================================================================== datos sintéticos con contenido
def destinos_sinteticos(n: int = 45) -> pd.DataFrame:
    ids = np.arange(1, n + 1)
    return pd.DataFrame({"destino_id": ids, "nombre": [f"Destino {i}" for i in ids], "lugar": [f"lugar_{i % 5}" for i in ids],
                         "estado": "X", "tipo": [TIPOS[i % 5] for i in ids], "mejor_epoca": "Ene",
                         "popularidad": np.linspace(7.0, 9.0, n)})


def usuarios_sinteticos(n: int = 79) -> pd.DataFrame:
    ids = np.arange(1, n + 1)
    df = pd.DataFrame({"usuario_id": ids})
    for col in contenido.COLUMNAS_PREFERENCIAS:
        df[col] = [col in COMBOS[u % 3] for u in ids]
    df["genero"] = ["Female" if u % 2 else "Male" for u in ids]
    df["n_adultos"] = 1 + ids % 2
    df["n_ninos"] = ids % 3
    return df


def contenido_sintetico(n_usuarios: int = 79, n_destinos: int = 45, demografia: bool = False):
    return (contenido.contenido_usuarios(usuarios_sinteticos(n_usuarios), usar_demografia=demografia),
            contenido.contenido_destinos(destinos_sinteticos(n_destinos)))


def inter_sintetica(n_usuarios: int = 60, n_destinos: int = 40, semilla: int = 2) -> pd.DataFrame:
    return particion.asignar_split(tabla({u: 1 + u % 7 for u in range(1, n_usuarios)}, n_destinos=n_destinos), semilla)


def red_chica(hp=None, usar_validacion: bool = True, **kw) -> red.RedDosTorres:
    cu, ci = contenido_sintetico()
    return red.RedDosTorres({**HP, **(hp or {})}, cu, ci, usar_validacion=usar_validacion, **kw)


CAT = np.arange(1, 46, dtype="int64")


# =========================================================================== contenido
def test_contenido_de_destinos_es_tipo_one_hot_con_orden_fijo_y_no_mira_popularidad():
    d = pd.DataFrame({"destino_id": [3, 1, 2], "tipo": ["City", "Beach", "City"], "nombre": ["a", "b", "c"],
                      "lugar": ["x", "y", "z"], "popularidad": [1.0, 2.0, 3.0]})
    c = contenido.contenido_destinos(d)
    assert c.columnas == ("tipo=Beach", "tipo=City")                      # categorías ordenadas
    assert c.ids.tolist() == [3, 1, 2]                                    # filas en el orden de la tabla
    assert c.X.tolist() == [[0, 1], [1, 0], [0, 1]] and c.X.dtype == np.float32
    otra = d.assign(popularidad=[9.0, -1.0, 0.0], nombre=["q", "r", "s"], lugar=["1", "2", "3"])
    assert np.array_equal(contenido.contenido_destinos(otra).X, c.X)     # D15: ni popularidad, ni nombre, ni lugar
    assert c.filas([2, 3]).tolist() == [2, 0]
    with pytest.raises(ValueError, match="no están"):
        c.filas([99])
    with pytest.raises(ValueError, match="tipo"):
        contenido.contenido_destinos(d.assign(tipo=["City", None, "Beach"]))
    with pytest.raises(ValueError, match="repetid"):
        contenido.contenido_destinos(d.assign(destino_id=[1, 1, 2]))


def test_contenido_de_usuarios_son_las_5_preferencias_y_la_demografia_opcional():
    u = pd.DataFrame({"usuario_id": [7, 8], "pref_adventure": [True, False], "pref_beaches": [False, True],
                      "pref_city": [False, False], "pref_historical": [False, True], "pref_nature": [True, False],
                      "genero": ["Male", "Female"], "n_adultos": [2, 1], "n_ninos": [0, 2]})
    c = contenido.contenido_usuarios(u)
    assert c.columnas == contenido.COLUMNAS_PREFERENCIAS
    assert c.X.tolist() == [[1, 0, 0, 0, 1], [0, 1, 0, 1, 0]]
    d = contenido.contenido_usuarios(u, usar_demografia=True)
    assert d.columnas == (*contenido.COLUMNAS_PREFERENCIAS, "genero=Female", "genero=Male", "n_adultos=1", "n_adultos=2",
                          "n_ninos=0", "n_ninos=2")
    assert d.X[0].tolist() == [1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0] and d.X[1].tolist() == [0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1]
    with pytest.raises(ValueError, match="pref_city"):
        contenido.contenido_usuarios(u.drop(columns="pref_city"))


def test_cargar_contenido_lee_solo_destinos_y_usuarios_de_la_config(tmp_path):
    destinos_sinteticos().to_parquet(tmp_path / "d.parquet", index=False)
    usuarios_sinteticos().to_parquet(tmp_path / "u.parquet", index=False)
    cfg = {"datos": {"carpeta": tmp_path.as_posix(), "destinos": "d.parquet", "usuarios": "u.parquet",
                     "interacciones": "no_existe.parquet"}}
    cu, ci = contenido.cargar_contenido(cfg, usar_demografia=False)       # no abre el archivo de interacciones
    assert cu.X.shape == (79, 5) and ci.X.shape == (45, 5)


# =========================================================================== torres: formas y conteo de parámetros
def test_formas_de_entrada_y_salida_de_cada_torre():
    tu = red.TorreUsuario(n_entradas=5, capas=2, unidades=8, dim=3, dropout=0.0, n_ids=4, usar_id=True)
    td = red.TorreDestino(n_entradas=5, capas=1, unidades=6, dim=3, dropout=0.0, n_ids=7, usar_id=True)
    x_u, idx_u = torch.ones(10, 5), torch.zeros(10, dtype=torch.long)
    assert tu(x_u, idx_u).shape == (10, 3)
    v, b = td(torch.ones(12, 5), torch.zeros(12, dtype=torch.long))
    assert v.shape == (12, 3) and b.shape == (12,)
    m = red.DosTorres(tu, td)
    s = m(x_u, idx_u, torch.ones(10, 4, 5), torch.zeros(10, 4, dtype=torch.long))
    assert s.shape == (10, 4)
    assert m.puntuar_matriz(x_u, idx_u, torch.ones(12, 5), torch.zeros(12, dtype=torch.long)).shape == (10, 12)
    # solo ReLU como activación (contrato de la app, núcleo §5.8)
    activaciones = {type(c).__name__ for c in m.modules() if not isinstance(c, (torch.nn.Linear, torch.nn.Embedding,
                                                                                torch.nn.Dropout, torch.nn.Sequential))}
    assert activaciones <= {"ReLU", "TorreUsuario", "TorreDestino", "DosTorres"}


def test_el_puntaje_es_producto_punto_mas_sesgo():
    tu = red.TorreUsuario(5, 0, 8, 2, 0.0, 0, False)
    td = red.TorreDestino(5, 0, 8, 2, 0.0, 0, False)
    m = red.DosTorres(tu, td).eval()
    x_u, x_i = torch.eye(5)[:3], torch.eye(5)
    with torch.no_grad():
        u = tu(x_u, torch.zeros(3, dtype=torch.long))
        v, b = td(x_i, torch.zeros(5, dtype=torch.long))
        s = m.puntuar_matriz(x_u, torch.zeros(3, dtype=torch.long), x_i, torch.zeros(5, dtype=torch.long))
    assert torch.allclose(s, u @ v.T + b, atol=1e-6)


def test_n_parametros_contra_un_conteo_a_mano():
    tu = red.TorreUsuario(n_entradas=5, capas=1, unidades=4, dim=3, dropout=0.0, n_ids=2, usar_id=True)
    td = red.TorreDestino(n_entradas=5, capas=0, unidades=99, dim=3, dropout=0.0, n_ids=3, usar_id=True)
    m = red.DosTorres(tu, td)
    assert red.contar_parametros(m) == 81                                 # ver el docstring del módulo
    assert sum(p.numel() for p in m.parameters()) == 81 + 3 + 4          # las 2 filas padding_idx no cuentan
    sin_id = red.DosTorres(red.TorreUsuario(5, 1, 4, 3, 0.0, 2, False), red.TorreDestino(5, 0, 99, 3, 0.0, 3, False))
    assert red.contar_parametros(sin_id) == 24 + 15 + 24


def test_n_parametros_del_modelo_ajustado_y_arquitectura_suman_lo_mismo():
    m = red_chica().ajustar(inter_sintetica(), CAT, make_rng(0, 0))
    a = m.arquitectura()
    assert a["total_parametros"] == m.n_parametros() == sum(c["parametros"] for c in a["capas"])
    nu, ni = len(m.mapa_usuarios), int((m.indice_destinos > 0).sum())
    d = HP["modelo.dim_embedding"]
    a_mano = (5 * 8 + 8) + (8 * d + d) + nu * d + (5 * 8 + 8) + (8 * (d + 1) + d + 1) + ni * (d + 1)
    assert m.n_parametros() == a_mano
    assert {c["torre"] for c in a["capas"]} == {"usuario", "destino"}
    assert all(c["activacion"] in ("relu", "ninguna") for c in a["capas"])


# =========================================================================== pérdidas a mano y gradientes
S_POS = [2.0, -1.0]
S_NEG = [[0.5, -0.5], [1.0, 0.0]]


def test_bce_y_bpr_contra_el_calculo_a_mano():
    sp, sn = torch.tensor(S_POS), torch.tensor(S_NEG)
    assert red.perdida_bce(sp, sn).item() == pytest.approx(0.815792, abs=1e-6)
    assert red.perdida_bpr(sp, sn).item() == pytest.approx(0.930123, abs=1e-6)
    # un solo par: BPR = softplus(−(s⁺ − s⁻)) = log(1 + e^{−1}) = 0,313262; BCE = (softplus(−1) + softplus(0)) / 2
    assert red.perdida_bpr(torch.tensor([1.0]), torch.tensor([[0.0]])).item() == pytest.approx(math.log1p(math.exp(-1)), abs=1e-6)
    assert red.perdida_bce(torch.tensor([1.0]), torch.tensor([[0.0]])).item() == pytest.approx(
        (math.log1p(math.exp(-1)) + math.log(2)) / 2, abs=1e-6)


def test_bpr_tiene_el_signo_correcto_y_las_perdidas_son_estables():
    sn = torch.tensor([[0.0]])
    assert red.perdida_bpr(torch.tensor([3.0]), sn) < red.perdida_bpr(torch.tensor([-3.0]), sn)   # subir s⁺ baja la pérdida
    assert red.perdida_bce(torch.tensor([3.0]), sn) < red.perdida_bce(torch.tensor([-3.0]), sn)
    assert red.perdida_bce(torch.tensor([0.0]), torch.tensor([[3.0]])) > red.perdida_bce(torch.tensor([0.0]), torch.tensor([[-3.0]]))
    grande = torch.tensor([1000.0, -1000.0])
    for f in (red.perdida_bce, red.perdida_bpr):
        assert torch.isfinite(f(grande, -grande.reshape(2, 1))) and torch.isfinite(f(-grande, grande.reshape(2, 1)))


def test_gradiente_de_las_perdidas_contra_diferencias_finitas_y_contra_la_formula():
    torch.manual_seed(0)
    sp = torch.randn(4, dtype=torch.float64, requires_grad=True)
    sn = torch.randn(4, 3, dtype=torch.float64, requires_grad=True)
    assert torch.autograd.gradcheck(red.perdida_bce, (sp, sn))
    assert torch.autograd.gradcheck(red.perdida_bpr, (sp, sn))
    # BPR: ∂L/∂s⁺_b = −(1/(B·m)) Σ_j σ(−(s⁺_b − s⁻_bj));  BCE: ∂L/∂s⁺_b = −σ(−s⁺_b)/(B(1+m)), ∂L/∂s⁻_bj = σ(s⁻_bj)/(B(1+m))
    g_pos, = torch.autograd.grad(red.perdida_bpr(sp, sn), sp)
    esperado = -torch.sigmoid(-(sp[:, None] - sn)).sum(dim=1) / (4 * 3)
    assert torch.allclose(g_pos, esperado.detach())
    g_pos, g_neg = torch.autograd.grad(red.perdida_bce(sp, sn), (sp, sn))
    assert torch.allclose(g_pos, (-torch.sigmoid(-sp) / 16).detach()) and torch.allclose(g_neg, (torch.sigmoid(sn) / 16).detach())


# =========================================================================== negativos
def test_los_negativos_nunca_son_destinos_de_train_del_usuario_y_son_uniformes():
    inter = inter_sintetica()
    usuarios, positivos, negativos = red.negativos_train(inter, CAT, 4, make_rng(1, 0))
    train = inter[inter["split"] == "train"]
    assert len(usuarios) == len(positivos) == len(train) and negativos.shape == (len(train), 4)
    t = {(int(u), int(d)) for u, d in zip(train["usuario_id"], train["destino_id"])}
    assert {(int(u), int(d)) for u, d in zip(usuarios, positivos)} == t
    assert not any((int(u), int(j)) in t for u, fila in zip(usuarios, negativos) for j in fila)
    assert set(np.unique(negativos)) <= set(CAT.tolist())
    # uniformidad: un usuario con 1 de train tiene 44 permitidos; 20 000 sorteos → esperado 454,5 por destino (σ ≈ 21)
    filas = np.zeros(20000, dtype="int64")
    excl = np.array([0], dtype="int64")                                     # código fila 0 · 45 + columna 0
    neg = red.muestrear_negativos(filas, excl, 45, 1, make_rng(2, 0)).ravel()
    conteo = np.bincount(neg, minlength=45)
    assert conteo[0] == 0 and np.all(np.abs(conteo[1:] - 20000 / 44) < 5 * math.sqrt(20000 / 44))


def test_un_destino_de_validacion_si_puede_salir_como_negativo():
    """Excluir los destinos de validación de los negativos usaría validación para entrenar (D9)."""
    inter = inter_sintetica()
    val = inter[inter["split"] == "validacion"]
    vistos = set()
    for s in range(20):
        u, _, neg = red.negativos_train(inter, CAT, 4, make_rng(s, 0))
        vistos |= {(int(a), int(j)) for a, fila in zip(u, neg) for j in fila}
    assert {(int(a), int(d)) for a, d in zip(val["usuario_id"], val["destino_id"])} & vistos


def test_los_negativos_de_una_epoca_real_de_ajustar_nunca_son_de_train():
    """B1: el MISMO camino que usa ``ajustar`` en cada época (``preparar_train`` + ``sortear_epoca``): ninguna columna de
    negativos es un destino de train de su usuario y la columna 0 es el positivo."""
    inter = inter_sintetica()
    m = red_chica().ajustar(inter, CAT, make_rng(0, 0))
    prep, k = m._prep, HP["modelo.negativos_por_positivo"]
    train = inter[inter["split"] == "train"]
    t = {(int(u), int(d)) for u, d in zip(train["usuario_id"], train["destino_id"])}
    for s in range(5):
        perm, cols = red.sortear_epoca(prep, k, make_rng(s, 1), make_rng(s, 2))
        usuarios = prep["usuarios"][perm]
        assert cols.shape == (len(train), 1 + k)
        assert {(int(u), int(CAT[c])) for u, c in zip(usuarios, cols[:, 0])} == t
        assert not any((int(u), int(CAT[j])) in t for u, fila in zip(usuarios, cols[:, 1:]) for j in fila)
    assert m.diagnosticos()["negativos_por_epoca"] == k * len(train)


def test_muestrear_negativos_falla_si_un_usuario_no_tiene_destinos_permitidos():
    with pytest.raises(ValueError, match="permitido"):
        red.muestrear_negativos(np.array([0]), np.arange(3, dtype="int64"), 3, 1, make_rng(0, 0))


# =========================================================================== índices de id y dropout de id
def test_los_indices_de_id_salen_solo_de_train():
    inter = pd.DataFrame({"usuario_id": [5, 5, 6, 7, 8], "destino_id": [3, 1, 3, 2, 4],
                          "split": ["train", "validacion", "train", "prueba", "validacion"]})
    mapa_u, idx_d = red.indices_de_id(inter, np.array([4, 3, 2, 1]))
    assert mapa_u == {5: 1, 6: 2}                                         # 7 y 8 no tienen train → índice 0
    assert idx_d.tolist() == [0, 1, 0, 0]                                 # solo el destino 3 tiene train


def test_el_dropout_de_id_solo_pone_ceros():
    idx = np.arange(1, 10001)
    out = red.aplicar_dropout_id(idx, 0.3, make_rng(0, 0))
    assert set(np.unique(out[out != idx])) == {0} and np.all((out == idx) | (out == 0))
    assert abs((out == 0).mean() - 0.3) < 0.02
    assert np.array_equal(red.aplicar_dropout_id(idx, 0.0, make_rng(0, 0)), idx)


# =========================================================================== torre de usuario exportable (app)
def test_con_id_cero_la_torre_de_usuario_depende_solo_de_las_preferencias_y_coincide_con_la_app():
    m = red_chica({"modelo.capas_usuario": 2}).ajustar(inter_sintetica(), CAT, make_rng(0, 0))
    capas = m.capas_torre_usuario()
    assert [c["activacion"] for c in capas] == ["relu", "relu", "ninguna"]
    cu, _ = contenido_sintetico()
    for x in cu.X[:6]:
        h = x.astype(np.float64)
        for c in capas:                                                    # como app/lib/recomendar.ts: W·h + b, ReLU
            h = np.asarray(c["W"]) @ h + np.asarray(c["b"])
            if c["activacion"] == "relu":
                h = np.maximum(h, 0.0)
        assert np.allclose(m.vector_usuario_sin_id(x), h, atol=1e-5)
    # dos usuarios sin train con las mismas preferencias tienen el mismo vector y los mismos puntajes
    sin_train = [u for u in cu.ids if int(u) not in m.mapa_usuarios]
    a, b = [u for u in sin_train if u % 3 == sin_train[0] % 3][:2]
    s = m.puntuar([a, b])
    assert np.array_equal(s[0], s[1])


def test_puntuar_un_usuario_sin_train_no_falla_y_uno_sin_contenido_si():
    m = red_chica().ajustar(inter_sintetica(), CAT, make_rng(0, 0))
    assert m.puntuar([70]).shape == (1, 45)                               # 70 está en usuarios pero no en interacciones
    with pytest.raises(ValueError, match="no están"):
        m.puntuar([10_000])


def test_destinos_frios_del_mismo_tipo_reciben_el_mismo_puntaje():
    m = red_chica().ajustar(inter_sintetica(), CAT, make_rng(0, 0))
    frios = CAT[m.indice_destinos == 0]                                   # 41..45 no aparecen en las interacciones
    assert set(range(41, 46)) <= set(frios.tolist())
    s = m.puntuar([1, 2, 3])
    pos = {int(d): j for j, d in enumerate(CAT)}
    por_tipo: dict[str, list[int]] = {}
    for d in frios:
        por_tipo.setdefault(TIPOS[int(d) % 5], []).append(pos[int(d)])
    for cols in por_tipo.values():
        assert np.allclose(s[:, cols], s[:, cols[:1]], atol=1e-6)


def test_la_fila_cero_de_los_embeddings_queda_en_cero_tras_entrenar():
    m = red_chica({"regularizacion.weight_decay": 1e-2}).ajustar(inter_sintetica(), CAT, make_rng(0, 0))
    for emb in (m.red.torre_usuario.embedding, m.red.torre_destino.embedding):
        assert torch.count_nonzero(emb.weight[0]) == 0 and torch.count_nonzero(emb.weight[1:]) > 0


@pytest.mark.parametrize("metodo", ["ndcg5_validacion_actual", "vector_usuario_sin_id", "arquitectura",
                                    "capas_torre_usuario", "puntuar", "n_parametros", "diagnosticos"])
def test_sin_ajustar_cada_metodo_da_un_error_claro(metodo):
    m = red_chica()
    assert m._val is None
    args = {"vector_usuario_sin_id": (np.ones(5, np.float32),), "puntuar": ([1],)}.get(metodo, ())
    with pytest.raises(RuntimeError, match="ajustar"):
        getattr(m, metodo)(*args)


def test_contenido_filas_con_ids_vacios_y_tabla_vacia():
    c = contenido.contenido_destinos(destinos_sinteticos(5))
    vacio = c.filas([])
    assert vacio.shape == (0,) and vacio.dtype == np.int64
    tabla_vacia = contenido.Contenido(ids=np.array([], dtype="int64"), X=np.zeros((0, 5), np.float32), columnas=())
    assert tabla_vacia.filas([]).shape == (0,)
    with pytest.raises(ValueError, match="vacía"):
        tabla_vacia.filas([3])


def test_ndcg_medio_a_mano():
    from src.m3_recomendacion import metricas
    tops = {1: (np.array([7, 1]), None), 2: (np.array([1, 2]), None), 3: (np.array([4, 5]), None)}
    rel = {1: {7}, 2: {2}, 3: {9}}
    # usuario 1: rango 1 → 1; usuario 2: rango 2 → 1/log2(3); usuario 3: 0
    assert metricas.ndcg_medio(tops, rel, [1, 2, 3], 2) == pytest.approx((1 + 1 / math.log2(3)) / 3)
    assert metricas.ndcg_medio(tops, rel, [1, 2, 3], 1) == pytest.approx(1 / 3)


HPO_REAL = RAIZ / "results" / "data" / "m3" / "hpo_ensayos.json"


@pytest.mark.skipif(not HPO_REAL.is_file(), reason="falta results/data/m3/hpo_ensayos.json (corre m3-hpo)")
def test_los_bloques_de_base_yaml_son_el_mejor_ensayo_de_la_red():
    """R9: los valores buscados de los bloques de base.yaml son los de familias.red.mejor.params (sin copia a mano errada)."""
    familias = json.loads(HPO_REAL.read_text(encoding="utf-8"))["familias"]
    if "red" not in familias:
        pytest.skip("hpo_ensayos.json no tiene la familia red")
    cfg = load_config(CFG_BASE)
    for clave, valor in familias["red"]["mejor"]["params"].items():
        bloque, nombre = clave.split(".")
        assert cfg[bloque][nombre] == valor, f"{clave}: base.yaml {cfg[bloque][nombre]!r} ≠ mejor ensayo {valor!r}"


# =========================================================================== entrenamiento
def test_la_perdida_baja_en_un_ejemplo_pequeno_memorizable():
    inter = particion.asignar_split(tabla({u: 3 for u in range(1, 7)}, n_destinos=10), 0)
    inter["split"] = "train"
    cu = contenido.contenido_usuarios(usuarios_sinteticos(6))
    ci = contenido.contenido_destinos(destinos_sinteticos(10))
    hp = {**HP, "modelo.dim_embedding": 8, "modelo.dropout_id": 0.0, "regularizacion.dropout": 0.0,
          "regularizacion.weight_decay": 0.0, "entrenamiento.lr": 0.05, "entrenamiento.max_epocas": 150}
    m = red.RedDosTorres(hp, cu, ci, usar_validacion=False).ajustar(inter, np.arange(1, 11), make_rng(0, 0))
    c = m.curvas["perdida_train"]
    assert len(c) == 150 and c[-1] < 0.25 * c[0]


def test_misma_semilla_mismos_pesos_y_puntajes_otra_semilla_otros():
    inter = inter_sintetica()
    a = red_chica().ajustar(inter, CAT, make_rng(3, 0))
    b = red_chica().ajustar(inter, CAT, make_rng(3, 0))
    c = red_chica().ajustar(inter, CAT, make_rng(4, 0))
    assert np.array_equal(a.puntuar([1, 2, 3]), b.puntuar([1, 2, 3])) and a.curvas == b.curvas
    for k, v in a.red.state_dict().items():
        assert torch.equal(v, b.red.state_dict()[k])
    assert not np.array_equal(a.puntuar([1, 2, 3]), c.puntuar([1, 2, 3]))


def test_no_toca_el_azar_global_de_torch_ni_de_numpy():
    """Toda la aleatoriedad sale del ``rng`` recibido: el estado global de torch y de numpy no cambia."""
    original = np.random.get_state()
    try:
        antes_t, antes_n = torch.get_rng_state(), np.random.get_state()[1].copy()
        red_chica().ajustar(inter_sintetica(), CAT, make_rng(0, 0))
        assert torch.equal(torch.get_rng_state(), antes_t) and np.array_equal(np.random.get_state()[1], antes_n)
    finally:
        np.random.set_state(original)


def test_parada_temprana_restaura_la_mejor_epoca_y_registra_la_curva():
    m = red_chica({"entrenamiento.max_epocas": 40, "entrenamiento.paciencia": 2}).ajustar(inter_sintetica(), CAT, make_rng(0, 0))
    c = m.curvas
    n = len(c["epoca"])
    assert c["epoca"] == list(range(1, n + 1)) and c["epoca_parada"] == n and 1 <= c["mejor_epoca"] <= n
    assert len(c["perdida_train"]) == len(c["perdida_validacion"]) == len(c["ndcg5_validacion"]) == n
    mejor = c["ndcg5_validacion"][c["mejor_epoca"] - 1]
    assert mejor == max(c["ndcg5_validacion"]) and c["ndcg5_validacion"].index(mejor) == c["mejor_epoca"] - 1
    assert n < 40, "precondición: con max_epocas = 40 y paciencia 2 esta corrida debe parar antes"
    assert n - c["mejor_epoca"] == 2                                      # se detuvo tras «paciencia» épocas sin mejorar
    d = m.diagnosticos()
    assert d["mejor_epoca"] == c["mejor_epoca"] and d["epoca_parada"] == n and d["ndcg5_validacion_mejor"] == mejor
    # los pesos restaurados son los de la mejor época: su NDCG@5 de validación con el mismo desempate es el registrado
    assert m.ndcg5_validacion_actual() == pytest.approx(mejor)


def test_sin_validacion_entrena_las_epocas_fijas():
    m = red_chica(usar_validacion=False).ajustar(inter_sintetica(), CAT, make_rng(0, 0))
    assert m.curvas["epoca_parada"] == m.curvas["mejor_epoca"] == HP["entrenamiento.max_epocas"]
    assert all(v is None for v in m.curvas["perdida_validacion"])


# =========================================================================== diagnósticos de degeneración
def test_diagnostico_de_degeneracion_por_cada_motivo():
    sano = red.diagnostico_degeneracion(np.array([[0.1, 0.5], [0.3, -0.2]]), np.array([1.0, 2.0]), np.array([1.0, 0.5]), 1e-6)
    assert sano["degenerado"] is False and sano["motivo_degenerado"] is None
    assert sano["rango_max_por_usuario"] == pytest.approx(0.5) and sano["max_norma_u_por_norma_v"] == pytest.approx(2.0)
    nan = red.diagnostico_degeneracion(np.array([[np.nan, 0.0]]), np.ones(1), np.ones(2), 1e-6)
    assert nan["degenerado"] and nan["motivo_degenerado"] == "puntajes_no_finitos"
    constante = red.diagnostico_degeneracion(np.full((3, 4), 0.7), np.ones(3), np.ones(4), 1e-6)
    assert constante["motivo_degenerado"] == "puntajes_constantes_por_usuario"
    nulo = red.diagnostico_degeneracion(np.array([[0.0, 1.0]]), np.array([1e-4]), np.array([1e-4, 1e-3]), 1e-6)
    assert nulo["motivo_degenerado"] == "producto_de_normas_bajo_tolerancia"


def test_diagnosticos_del_modelo_ajustado():
    m = red_chica().ajustar(inter_sintetica(), CAT, make_rng(0, 0))
    d = m.diagnosticos()
    assert d["degenerado"] is False and d["motivo_degenerado"] is None
    assert {"mejor_epoca", "epoca_parada", "ndcg5_validacion_mejor", "personalizacion", "negativos_por_epoca",
            "rango_max_por_usuario", "max_norma_u_por_norma_v"} <= set(d)
    assert d["personalizacion"] > 0
    assert d["negativos_por_epoca"] == HP["modelo.negativos_por_positivo"] * int((inter_sintetica()["split"] == "train").sum())
    assert {"fraccion_varianza_interaccion", "listas_top10_distintas", "fraccion_mismo_top1"} <= set(d)
    assert 0.0 <= d["fraccion_varianza_interaccion"] <= 1.0 and 0.0 < d["fraccion_mismo_top1"] <= 1.0
    assert isinstance(d["listas_top10_distintas"], int) and d["listas_top10_distintas"] >= 1


# Personalización del ranking: S_ui = μ + α_u + β_i + E_ui (dos vías). α_u (desplazamiento propio del usuario) no cambia su
# orden y β_i (incluye b_i) da el mismo orden a todos: solo la interacción E personaliza. E = S − filas − columnas + media.
def test_personalizacion_es_cero_con_solo_efectos_de_usuario_y_de_destino():
    alfa = np.array([0.0, 5.0, -3.0, 10.0])                                # desplazamientos grandes por usuario
    beta = np.linspace(1.0, 0.0, 12)                                        # mismo orden para todos (sin empates)
    S = alfa[:, None] + beta[None, :]
    m = red.medidas_personalizacion(S)
    assert m["personalizacion"] == pytest.approx(0.0, abs=1e-12)
    assert m["fraccion_varianza_interaccion"] == pytest.approx(0.0, abs=1e-12)
    assert m["listas_top10_distintas"] == 1 and m["fraccion_mismo_top1"] == 1.0
    assert float(S.std(axis=0).mean()) > 4.0                                # la medida anterior lo confundía con personalización


def test_personalizacion_es_positiva_con_interaccion_pura():
    u = np.array([1.0, -1.0, 2.0, -2.0])
    v = np.linspace(-1.0, 1.0, 12)
    S = np.outer(u, v)                                                      # medias de filas y columnas = 0: todo es interacción
    m = red.medidas_personalizacion(S)
    # a mano: E = S; std entre usuarios de u_u·v_i = |v_i|·std(u) con std(u) = √2,5 (ddof 0) → media = √2,5 · mean|v_i|
    assert m["personalizacion"] == pytest.approx(math.sqrt(2.5) * np.abs(v).mean())
    assert m["fraccion_varianza_interaccion"] == pytest.approx(1.0)
    assert m["listas_top10_distintas"] == 2 and m["fraccion_mismo_top1"] == 0.5      # u > 0 ordena al revés que u < 0
    mezcla = S + 3.0 * np.linspace(0, 1, 12)[None, :]
    assert 0.0 < red.medidas_personalizacion(mezcla)["fraccion_varianza_interaccion"] < 1.0


@pytest.mark.parametrize("valor, forma", [(0.7, (5, 20)), (-0.2513, (606, 1000)), (0.3, (326, 1000))])
def test_personalizacion_con_puntajes_constantes_da_fraccion_cero(valor, forma):
    # verificador-matematico (JJ-5, 2.ª vuelta): con S constante en punto flotante ‖S − μ‖² no es 0 exacto (≈ 1e-30 a 1e-27) y el
    # cociente daba 2,25 o 1 089, fuera de [0, 1]. Con S constante no hay ninguna variación que repartir: la fracción es 0.
    m = red.medidas_personalizacion(np.full(forma, valor))
    assert m["fraccion_varianza_interaccion"] == 0.0
    assert m["personalizacion"] == pytest.approx(0.0, abs=1e-12)
    assert m["listas_top10_distintas"] == 1 and m["fraccion_mismo_top1"] == 1.0


def _casi_constante(caso: str) -> np.ndarray:
    S = np.full((606, 1000), 0.7)
    if caso == "una_celda":
        S[3, 7] = np.nextafter(0.7, np.inf)
    elif caso == "una_columna":
        S[:, 5] = np.nextafter(0.7, np.inf)
    else:                                                                    # ruido de ±3 ulp
        S = 0.7 + np.random.default_rng(0).integers(-3, 4, size=S.shape) * np.spacing(0.7)
    return S


@pytest.mark.parametrize("caso", ["una_celda", "una_columna", "ruido_3_ulp"])
def test_personalizacion_con_puntajes_casi_constantes_queda_en_cero_uno(caso):
    # verificador-matematico (JJ-5, 3.ª vuelta): con diferencias de pocos ulp ‖E‖² y ‖S − μ‖² son ruido de redondeo y el
    # cociente directo daba hasta 2,7e9. Con el denominador armado por la descomposición ortogonal queda en [0, 1].
    frac = red.medidas_personalizacion(_casi_constante(caso))["fraccion_varianza_interaccion"]
    assert 0.0 <= frac <= 1.0


def test_la_fraccion_con_la_descomposicion_es_la_misma_en_una_matriz_generica():
    S = np.random.default_rng(1).normal(size=(50, 80))
    E = S - S.mean(1, keepdims=True) - S.mean(0, keepdims=True) + S.mean()
    directa = float((E ** 2).sum() / ((S - S.mean()) ** 2).sum())
    assert red.medidas_personalizacion(S)["fraccion_varianza_interaccion"] == pytest.approx(directa, rel=1e-12)


# =========================================================================== hiperparámetros, fábrica y claves en vivo
@pytest.fixture(scope="module")
def proc(tmp_path_factory):
    """Carpeta de datos procesados sintéticos con contenido (destinos con tipo; usuarios con preferencias)."""
    tmp = tmp_path_factory.mktemp("m3_red")
    montar_sintetico(tmp / "proc", n_usuarios=60, n_catalogo=45)
    destinos_sinteticos(45).to_parquet(tmp / "proc" / "destinos.parquet", index=False)
    usuarios_sinteticos(79).to_parquet(tmp / "proc" / "usuarios.parquet", index=False)
    return tmp


def cfg_red(tmp: Path, extra=(), base: Path = CFG_DEMO, salida: str = "res") -> dict:
    p = (tmp / "proc").as_posix()
    sets = [f"datos.carpeta={p}", f"datos.resumen_particion={p}/resumen.json",
            f"salida.carpeta={(tmp / salida).as_posix()}", f"salida.modelos={(tmp / (salida + '_mod')).as_posix()}",
            "semillas.n=2", "busqueda.n_ensayos=2", "entrenamiento.max_epocas=5", "entrenamiento.paciencia=2",
            "modelo.dim_embedding=4", "modelo.unidades_usuario=8", "modelo.unidades_destino=8"]
    return apply_overrides(load_config(base), [*sets, *extra])


def test_hiperparametros_efectivos_son_los_bloques_con_el_mejor_ensayo_encima():
    cfg = load_config(CFG_BASE)
    hp = red.hiperparametros_efectivos(cfg)
    assert set(hp) == set(HP) and hp["modelo.dim_embedding"] == cfg["modelo"]["dim_embedding"]
    cfg["red"]["hiperparametros_desde"] = "hpo"                             # base.yaml usa config (27-nov); aquí se prueba hpo
    cfg["red"]["hiperparametros"] = {"modelo.dim_embedding": 32, "perdida.tipo": "bpr"}
    with pytest.warns(UserWarning, match="hiperparametros_desde"):          # con hpo: avisa qué se reemplaza
        cfg2 = apply_overrides(cfg, ["modelo.dim_embedding=8"])
        cfg2["red"]["hiperparametros"] = {"modelo.dim_embedding": 32}
        assert red.hiperparametros_efectivos(cfg2)["modelo.dim_embedding"] == 32
    hp = red.hiperparametros_efectivos(cfg)
    assert hp["modelo.dim_embedding"] == 32 and hp["perdida.tipo"] == "bpr"
    cfg["red"]["hiperparametros"] = {"modelo.no_existe": 1}
    with pytest.raises(ValueError, match="no_existe"):
        red.hiperparametros_efectivos(cfg)


@pytest.mark.parametrize("cambio, malo", [("perdida.tipo", "mse"), ("modelo.dim_embedding", 0),
                                          ("modelo.dropout_id", 1.5), ("entrenamiento.lr", -1.0),
                                          ("modelo.usar_id_usuario", "si"), ("modelo.capas_usuario", 2.5)])
def test_hiperparametros_invalidos_son_un_error_claro(cambio, malo):
    with pytest.raises((TypeError, ValueError), match=cambio.split(".")[1]):
        red_chica({cambio: malo})


def test_claves_en_vivo_con_el_cargador_real(proc):
    """Núcleo §4.1: --set modelo.dim_embedding / modelo.negativos_por_positivo / perdida.tipo cambian lo que deben."""
    inter = pd.read_parquet(proc / "proc" / "interacciones.parquet")
    base = red.fabrica_red(cfg_red(proc)).ajustar(inter, CAT, make_rng(0, 0))
    m = red.fabrica_red(cfg_red(proc, ["modelo.dim_embedding=8"])).ajustar(inter, CAT, make_rng(0, 0))
    assert m.hiperparametros["modelo.dim_embedding"] == 8 and m.vector_usuario_sin_id(np.ones(5, np.float32)).shape == (8,)
    assert base.vector_usuario_sin_id(np.ones(5, np.float32)).shape == (4,) and m.n_parametros() > base.n_parametros()
    n_train = int((inter["split"] == "train").sum())
    m = red.fabrica_red(cfg_red(proc, ["modelo.negativos_por_positivo=1"])).ajustar(inter, CAT, make_rng(0, 0))
    assert m.diagnosticos()["negativos_por_epoca"] == n_train
    m = red.fabrica_red(cfg_red(proc, ["modelo.negativos_por_positivo=8"])).ajustar(inter, CAT, make_rng(0, 0))
    assert m.diagnosticos()["negativos_por_epoca"] == 8 * n_train
    bpr = red.fabrica_red(cfg_red(proc, ["perdida.tipo=bpr"]))
    assert bpr.funcion_perdida is red.perdida_bpr and red.fabrica_red(cfg_red(proc)).funcion_perdida is red.perdida_bce
    with pytest.raises(ValueError, match="Clave inexistente"):
        cfg_red(proc, ["modelo.no_existe=1"])


def test_config_gana_a_ejecutar_en_experimento(tmp_path, monkeypatch):
    """JJ-5 (cierra N1 de JJ-4): con hiperparametros_desde: config no se corre ninguna búsqueda aunque
    busqueda.ejecutar_en_experimento sea true; con hpo, sí."""
    llamadas = []
    familia = {"n_ensayos": 3, "mejor": {"numero": 1, "params": {"modelo.dim_embedding": 16}, "valor": 0.1},
               "tiempo_total_s": 2.0}
    monkeypatch.setitem(hpo.BUSQUEDAS, "red", lambda cfg, inter, cat: llamadas.append(1) or dict(familia))
    ctx = {"inter": None, "catalogo": None, "salida": tmp_path, "evidencia": {"particion_huella": "h"}}
    cfg = {"busqueda": {"ejecutar_en_experimento": True},
           "red": {"hiperparametros_desde": "config", "hiperparametros": {"modelo.dim_embedding": 8}}}
    p = experimento._presupuesto("red", cfg, ctx)
    assert not llamadas and p == {"hiperparametros": {"modelo.dim_embedding": 8}, "n_configuraciones": 1, "tiempo_s": 0.0,
                                  "origen": "config"}
    cfg["red"]["hiperparametros_desde"] = "hpo"
    p = experimento._presupuesto("red", cfg, ctx)
    assert llamadas == [1] and p["origen"] == "hpo" and p["n_configuraciones"] == 3
    assert p["hiperparametros"] == {"modelo.dim_embedding": 16}


def _escribir_hpo(carpeta, huella, familias):
    (carpeta / experimento.ARCHIVO_HPO).write_text(json.dumps({"evidencia": {"particion_huella": huella},
                                                               "familias": familias}), encoding="utf-8")


def test_config_igual_al_mejor_ensayo_reporta_el_presupuesto_de_la_busqueda(tmp_path):
    """Decisión de Juan José (27-nov): base.yaml usa config con los valores copiados del mejor ensayo; si coinciden EXACTAMENTE
    con familias.<nombre>.mejor.params de hpo_ensayos.json (misma partición), se reporta el presupuesto real de la búsqueda
    (núcleo §6), no 1 configuración y 0 s."""
    _escribir_hpo(tmp_path, "h", {
        "red": {"n_ensayos": 20, "tiempo_total_s": 38.5, "mejor": {"params": {"modelo.dim_embedding": 32, "perdida.tipo": "bce"}}},
        "mf_als": {"n_ensayos": 20, "tiempo_total_s": 16.0, "mejor": {"params": {"factores": 4, "alfa": 1.5}}}})
    ctx = {"salida": tmp_path, "evidencia": {"particion_huella": "h"}}
    cfg = {"busqueda": {"ejecutar_en_experimento": True}, "modelo": {"dim_embedding": 32}, "perdida": {"tipo": "bce"},
           "red": {"hiperparametros_desde": "config", "hiperparametros": {}},
           "mf_als": {"hiperparametros_desde": "config", "hiperparametros": {"factores": 4, "alfa": 1.5}}}
    p = experimento._presupuesto("red", cfg, ctx)
    assert p == {"hiperparametros": {}, "n_configuraciones": 20, "tiempo_s": 38.5, "origen": experimento.ORIGEN_CONFIG_HPO}
    p = experimento._presupuesto("mf_als", cfg, ctx)
    assert p["n_configuraciones"] == 20 and p["tiempo_s"] == 16.0 and p["hiperparametros"] == {"factores": 4, "alfa": 1.5}


@pytest.mark.parametrize("cambio", ["valor", "huella", "sin_familia", "sin_archivo"])
def test_config_distinta_del_mejor_ensayo_es_una_sola_configuracion(tmp_path, cambio):
    """Si la config no es el mejor ensayo (p. ej. --set modelo.dim_embedding=8 en vivo), o no hay búsqueda de esa partición,
    el modelo se reporta como 1 configuración y 0 s de búsqueda: no se atribuye un presupuesto que no lo eligió."""
    if cambio != "sin_archivo":
        familias = {} if cambio == "sin_familia" else {
            "red": {"n_ensayos": 20, "tiempo_total_s": 38.5, "mejor": {"params": {"modelo.dim_embedding": 32}}}}
        _escribir_hpo(tmp_path, "otra" if cambio == "huella" else "h", familias)
    ctx = {"salida": tmp_path, "evidencia": {"particion_huella": "h"}}
    cfg = {"modelo": {"dim_embedding": 8 if cambio == "valor" else 32},
           "red": {"hiperparametros_desde": "config", "hiperparametros": {}}}
    p = experimento._presupuesto("red", cfg, ctx)
    assert p == {"hiperparametros": {}, "n_configuraciones": 1, "tiempo_s": 0.0, "origen": "config"}


def test_base_yaml_usa_config_y_la_mf_es_su_mejor_ensayo():
    """base.yaml: config para la red y la MF; el bloque de la MF es familias.mf_als.mejor.params (copia exacta)."""
    cfg = load_config(CFG_BASE)
    assert cfg["red"]["hiperparametros_desde"] == "config" and cfg["mf_als"]["hiperparametros_desde"] == "config"
    familias = json.loads(HPO_REAL.read_text(encoding="utf-8"))["familias"]
    if "mf_als" not in familias:
        pytest.skip("hpo_ensayos.json no tiene la familia mf_als")
    assert cfg["mf_als"]["hiperparametros"] == familias["mf_als"]["mejor"]["params"]


def test_la_demo_sigue_buscando_la_mf_en_vivo():
    cfg = load_config(RAIZ / "configs" / "m3" / "demo.yaml")
    assert cfg["mf_als"]["hiperparametros_desde"] == "hpo" and cfg["busqueda"]["ejecutar_en_experimento"] is True
    assert cfg["red"]["hiperparametros_desde"] == "config"


def test_registro_de_la_red_en_modelos_y_busquedas():
    from src.m3_recomendacion import referencias
    assert "red" in referencias.MODELOS and "red" in hpo.BUSQUEDAS
    assert "red" in load_config(CFG_BASE)["modelos"]
    assert load_config(CFG_DEMO)["red"]["hiperparametros_desde"] == "config"
    assert load_config(CFG_BASE)["red"]["hiperparametros_desde"] == "config"    # decisión de Juan José, 27-nov


def test_configs_de_la_red_cumplen_las_decisiones():
    base, hp = load_config(CFG_BASE), load_config(CFG_HPO)
    e = hp["red"]["busqueda"]["espacio"]
    assert e["modelo.dim_embedding"] == {"tipo": "categorico", "valores": [4, 8, 16, 32]}          # D18
    assert set(e["perdida.tipo"]["valores"]) == {"bce", "bpr"}                                      # D16
    assert set(e) <= set(red.hiperparametros_efectivos(base))
    assert hp["busqueda"]["n_ensayos"] == 20                                                        # D19: mismo presupuesto
    assert base["entrenamiento"]["max_epocas"] == 100 and base["entrenamiento"]["paciencia"] == 10
    assert base["modelo"]["usar_demografia"] is False


def test_sugerir_acepta_categorico_sin_romper_entero_ni_real():
    import optuna
    estudio = optuna.create_study(sampler=optuna.samplers.TPESampler(seed=0))
    t = estudio.ask()
    assert hpo._sugerir(t, "a", {"tipo": "categorico", "valores": [4, 8]}) in (4, 8)
    assert hpo._sugerir(t, "b", {"tipo": "categorico", "valores": [True, False]}) in (True, False)
    assert isinstance(hpo._sugerir(t, "c", {"tipo": "entero", "min": 1, "max": 3}), int)
    assert 0.1 <= hpo._sugerir(t, "d", {"tipo": "real", "min": 0.1, "max": 1.0, "log": True}) <= 1.0
    with pytest.raises(ValueError, match="tipo"):
        hpo._sugerir(t, "e", {"tipo": "categorico"})                     # sin valores
    with pytest.raises(ValueError, match="tipo"):
        hpo._sugerir(t, "f", {"tipo": "otro", "min": 0, "max": 1})


def test_la_busqueda_de_la_red_nunca_elige_un_ensayo_degenerado():
    ensayos = [{"numero": 0, "valor": 0.9, "degenerado": True}, {"numero": 1, "valor": 0.2, "degenerado": False, "params": {"a": 1}},
               {"numero": 2, "valor": 0.3, "degenerado": False, "params": {"a": 2}}]
    cfg = load_config(CFG_HPO)
    fam = hpo._familia_red(cfg, ensayos, 1.0)
    assert fam["mejor"]["numero"] == 2 and fam["n_degenerados"] == 1 and fam["n_ensayos"] == 3
    with pytest.raises(ValueError, match="degenerad"):
        hpo._familia_red(cfg, [ensayos[0]], 1.0)


# =========================================================================== punta a punta (datos pequeños)
@pytest.fixture(scope="module")
def corrida_red(proc):
    cfg_h = cfg_red(proc, ["modelos=[mf_als, red]"], base=CFG_HPO)
    t = time.perf_counter()
    assert hpo.main(cfg_h) == 0
    cfg = cfg_red(proc, ["red.hiperparametros_desde=hpo", "busqueda.ejecutar_en_experimento=false",
                         "modelos=[popularidad, mf_als, aleatorio, red]"])
    assert experimento.main(cfg) == 0
    return {"res": proc / "res", "mod": proc / "res_mod", "cfg": cfg, "segundos": time.perf_counter() - t}


def test_summary_trae_el_bloque_de_la_red_segun_el_nucleo_5_9(corrida_red):
    s = load_json(corrida_red["res"] / "summary.json")
    assert set(s["modelos"]) == {"popularidad", "mf_als", "aleatorio", "red"}
    r = s["modelos"]["red"]
    for k in s["k"]:
        for met in ("precision", "recall", "ndcg", "acierto", "cobertura"):
            assert set(r["metricas"][f"{met}@{k}"]) >= {"media", "desviacion", "mejor", "peor"}
    assert isinstance(r["n_parametros"], int) and r["n_parametros"] > 0
    assert r["n_configuraciones_busqueda"] == 2 and r["hiperparametros_origen"] == "hpo"
    assert r["tiempo_total_s"] == pytest.approx(r["tiempo_busqueda_s"] + r["tiempo_corridas_finales_s"])
    assert r["device"] == "cpu" and s["evidencia"]["particion_huella"]
    assert r["diagnosticos"]["degenerado"] is False and "personalizacion" in r["diagnosticos"]
    fam = load_json(corrida_red["res"] / "hpo_ensayos.json")["familias"]
    assert set(fam) == {"mf_als", "red"} and fam["red"]["n_ensayos"] == 2
    assert {k: r["hiperparametros"][k] for k in fam["red"]["mejor"]["params"]} == fam["red"]["mejor"]["params"]
    assert "red" in s["destinos_frios"]["por_modelo"] and "sin id" in s["destinos_frios"]["tratamiento"]["red"]


def test_archivos_de_la_red_semillas_curvas_arquitectura_y_modelo(corrida_red):
    res, mod = corrida_red["res"], corrida_red["mod"]
    for k in (0, 1):
        j = load_json(res / "semillas" / f"red_seed{k}.json")
        assert j["semilla"] == k and "metricas" in j and j["diagnosticos"]["degenerado"] is False
    c = load_json(res / "curvas" / "red.json")
    n = len(c["epoca"])
    assert len(c["perdida_train"]) == len(c["perdida_validacion"]) == len(c["ndcg5_validacion"]) == n
    assert c["epoca_parada"] == n and 1 <= c["mejor_epoca"] <= n and c["semilla"] == 0 and c["evidencia"]["particion_huella"]
    a = load_json(res / "arquitectura" / "red.json")
    s = load_json(res / "summary.json")["modelos"]["red"]
    assert a["total_parametros"] == s["n_parametros"] == sum(x["parametros"] for x in a["capas"])
    assert {"nombre", "tipo", "entrada", "salida", "activacion", "parametros"} <= set(a["capas"][0])
    meta = load_json(mod / "red.json")
    assert meta["semilla"] == 0 and meta["columnas_usuario"] == list(contenido.COLUMNAS_PREFERENCIAS)
    assert meta["columnas_destino"] == [f"tipo={t}" for t in TIPOS] and meta["n_parametros"] == s["n_parametros"]
    assert set(meta["mapa_ids"]) == {"usuario", "destino"} and min(meta["mapa_ids"]["usuario"].values()) == 1
    estado = torch.load(mod / "red.pt", weights_only=True)
    assert any("embedding" in k for k in estado)
    assert not any(str(corrida_red["res"]) in json.dumps(x) for x in (c, a))  # sin rutas absolutas


def test_las_referencias_no_cambian_al_agregar_la_red(corrida_red, proc):
    """La red no altera el azar ni las métricas de las referencias: mismo summary con y sin la red."""
    cfg = cfg_red(proc, ["red.hiperparametros_desde=hpo", "busqueda.ejecutar_en_experimento=false",
                         "modelos=[popularidad, mf_als, aleatorio]"], salida="res_sin_red")
    hpo.escribir_familia(proc / "res_sin_red", load_json(corrida_red["res"] / "hpo_ensayos.json")["evidencia"], "mf_als",
                         load_json(corrida_red["res"] / "hpo_ensayos.json")["familias"]["mf_als"])
    assert experimento.main(cfg) == 0
    a = load_json(corrida_red["res"] / "summary.json")["modelos"]
    b = load_json(proc / "res_sin_red" / "summary.json")["modelos"]
    for nombre in ("popularidad", "mf_als", "aleatorio"):
        assert a[nombre]["metricas"] == b[nombre]["metricas"]


def test_evaluacion_k_y_semillas_n_en_vivo_con_la_red(proc):
    cfg = cfg_red(proc, ["evaluacion.k=3", "semillas.n=1", "modelos=[red]"], salida="res_k3")
    assert experimento.main(cfg) == 0
    s = load_json(proc / "res_k3" / "summary.json")
    assert s["k"] == [3] and s["modelos"]["red"]["metricas"]["ndcg@3"]["n"] == 1
    assert s["modelos"]["red"]["hiperparametros_origen"] == "config"     # demo: config gana a ejecutar_en_experimento
    assert not (proc / "res_k3" / "hpo_ensayos.json").exists()           # ninguna búsqueda corrió
    assert sorted(p.name for p in (proc / "res_k3" / "semillas").glob("red_seed*.json")) == ["red_seed0.json"]


def test_figuras_de_la_red_y_de_la_comparacion(corrida_red, tmp_path):
    from src.viz import figs_m3
    rutas = figs_m3.generar_modelos(corrida_red["res"], tmp_path)
    assert {r.name for r in rutas} == {"red_arquitectura.png", "red_curvas.png", "busqueda_m3.png", "cajas_m3.png"}
    for r in rutas:
        assert r.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n" and r.stat().st_size > 5000


def test_figuras_sin_resultados_del_experimento_dicen_que_comando_correr(tmp_path):
    from src.viz import figs_m3
    with pytest.raises(FileNotFoundError, match="run.py m3"):
        figs_m3.generar_modelos(tmp_path / "no_existe", tmp_path / "f")

