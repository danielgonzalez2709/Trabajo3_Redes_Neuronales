"""Pruebas de la partición sin fuga de M2 (JO-3; núcleo §8 ``test_fuga_m2.py``): ningún grupo de casi duplicados en dos
particiones y ningún par con arista entre particiones distintas.

Formulación (docs/spec/partes/jose.md §3.2, D1–D5):
  h(x) ∈ {0,1}^64 = pHash de 64 bits (imagehash.phash: gris, 32x32, DCT-II 2D, bloque 8x8 de baja frecuencia, bit = coef > mediana)
  d_H(a, b) = mín( H(h(a), h(b)), H(h(a), h(espejo(b))), H(h(espejo(a)), h(b)) ),  H = número de bits distintos
      (los dos últimos términos hacen d_H simétrica: el pHash del espejo no es una permutación de bits del original)
  z(x) ∈ R^512 = GAP de la última capa convolucional de ResNet-18 ImageNet congelada; cos(a, b) = z_a·z_b / (‖z_a‖ ‖z_b‖)
  arista(a, b)  ⇔  d_H(a, b) ≤ τ_H  ∨  cos(a, b) ≥ τ_c;     grupo_duplicado = componente conexa del grafo
  partición (D7): 70/15/15 por grupo; con d_kc = p_k·N_c − n_kc (déficit de la clase c en el split k) y v_g = conteo de
      clases del grupo g, cada grupo (de mayor a menor, empates barajados con la semilla) va a k* = argmax_k Σ_c v_gc·d_kc

Dónde podría colarse una fuga y qué prueba la descarta:
  F1 dos casi duplicados (aumento, espejo, ráfaga) en particiones distintas
       → test_variantes_*, test_invariantes_*, test_real_ningun_par_cruza_splits, test_real_phash_recalculado_*
  F2 una componente partida entre splits (se parte por imagen y no por grupo)
       → test_ningun_grupo_en_dos_splits, mutante test_mutante_particion_por_imagen_*
  F3 el espejo no se detecta (volteos del aumento previo)  → test_espejo_*, mutante test_mutante_sin_espejo_*
  F4 el CSV versionado de pares no corresponde a la partición o está incompleto
       → test_real_huellas_coinciden, test_real_phash_recalculado_coincide_con_pares (completitud del criterio hash)
  F5 los umbrales o la partición dependen de las etiquetas o del orden de las filas
       → test_grupos_no_dependen_de_la_clase, test_split_independiente_del_orden
  No descartable con estas pruebas: misma persona en splits distintos sin ser casi duplicado (no hay id de conductor; D5).
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import socket
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from PIL import Image, ImageOps

from src.m2_conduccion import duplicados
from src.m2_conduccion import particion

RAIZ = Path(__file__).resolve().parents[1]
CFG_PARTICION = RAIZ / "configs" / "m2" / "particion.yaml"
PROCESADO_REAL = RAIZ / "data" / "processed" / "m2"
INDICE_REAL = PROCESADO_REAL / "indice.csv"
RES_REAL = RAIZ / "results" / "data" / "m2" / "particion"
RESUMEN_REAL = RES_REAL / "resumen.json"
PARES_REAL = RES_REAL / "pares_cercanos.csv"
SPLITS = ("train", "validacion", "prueba")       # mismos nombres que M3
PROPORCIONES = {"train": 0.70, "validacion": 0.15, "prueba": 0.15}
CLASES = ["other_activities", "safe_driving", "talking_phone", "texting_phone", "turning"]
COLUMNAS_INDICE = ["id", "archivo", "clase", "grupo_duplicado", "split", "ancho", "alto"]
COLUMNAS_PARES = ["id_a", "id_b", "hamming", "coseno", "segundos", "criterio", "clase_a", "clase_b"]
# nombres originales con marca de tiempo en el fixture de _montar (clase, posición en la clase) → nombre; D9
MARCAS_FIXTURE = {("other_activities", 0): "IMG_20240101_000000000.jpg",      # base de las variantes (R5: hash y tiempo)
                  ("other_activities", 1): "IMG_20240101_000003000.jpg",      # su espejo, 3 s después → criterio hamming
                  ("safe_driving", 8): "IMG_20240930_132316665_HDR.jpg",      # t0
                  ("turning", 9): "IMG_20240930_132321000.jpg",              # t0 + 4,335 s → arista por tiempo
                  ("talking_phone", 10): "IMG_20240930_132340000_BURST.jpg"}  # t0 + 23,335 s (19 s del anterior) → sin arista
CFG_REAL = yaml.safe_load(CFG_PARTICION.read_text(encoding="utf-8"))
FORMATOS_T = particion.formatos_tiempo(CFG_REAL)        # [(nombre del formato, patrón)] resueltos desde la config
PATRON_T = dict(FORMATOS_T)["IMG_AAAAMMDD_HHMMSSmmm"]
MARCAS_POR_FORMATO_REAL = {"IMG_AAAAMMDD_HHMMSSmmm": 404, "AAAA-MM-DDhh-mm-ss": 183, "photo_AAAA-MM-DD_hh-mm-ss": 11}
TAU_H, TAU_C = 10, 0.95                           # umbrales SOLO de estas pruebas sintéticas (no los de la config real)


def _leer(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(ruta, dtype=str, keep_default_na=False)


def _sha(ruta: Path) -> str:
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- imágenes sintéticas
def campo(semilla: int, tam: int = 224) -> Image.Image:
    """Imagen RGB suave y asimétrica: ruido 6x6 en [40, 200] ampliado con bicúbica (sin saturar: el brillo +25 no recorta)."""
    r = np.random.default_rng(semilla)
    return Image.fromarray(r.uniform(40, 200, (6, 6, 3)).astype(np.uint8)).resize((tam, tam), Image.Resampling.BICUBIC)


def variantes(base: Image.Image) -> dict[str, Image.Image]:
    brillo = Image.fromarray(np.clip(np.asarray(base).astype(int) + 25, 0, 255).astype(np.uint8))
    w, h = base.size
    recorte = base.crop((w // 20, h // 20, w - w // 20, h - h // 20)).resize((w, h), Image.Resampling.BILINEAR)
    return {"copia": base.copy(), "espejo": ImageOps.mirror(base), "brillo": brillo, "recorte": recorte}


@pytest.fixture(scope="module")
def conjunto_sintetico():
    """0 = base, 1..4 = copia, espejo, brillo, recorte; 5..10 = imágenes distintas."""
    base = campo(1)
    imgs = [base, *variantes(base).values()] + [campo(s) for s in range(2, 8)]
    nombres = ["base", "copia", "espejo", "brillo", "recorte"] + [f"distinta_{s}" for s in range(2, 8)]
    return imgs, nombres


def _feats_inyectadas(n: int, iguales_a_base: list[int], dim: int = 16, semilla: int = 0) -> np.ndarray:
    """Características inyectadas (sin pesos): las de ``iguales_a_base`` son la base + ruido pequeño (cos ≈ 1); las demás
    son vectores no negativos al azar (cos lejos de 1 en dim 16 con ese ruido)."""
    r = np.random.default_rng(semilla)
    z = r.uniform(0, 1, (n, dim)) ** 4                           # ^4: vectores dispersos, cosenos bajos entre sí
    for i in iguales_a_base:
        z[i] = z[0] + r.normal(0, 1e-3, dim)
    return z


# --------------------------------------------------------------------------- casos a mano
def test_hamming_a_mano():
    a = np.zeros((1, 64), dtype=bool)
    b = a.copy()
    b[0, [0, 17, 63]] = True
    assert duplicados.hamming_matriz(duplicados.empaquetar(a), duplicados.empaquetar(b)).tolist() == [[3]]
    assert duplicados.hamming_matriz(duplicados.empaquetar(b), duplicados.empaquetar(b)).tolist() == [[0]]
    todos = np.ones((1, 64), dtype=bool)
    assert duplicados.hamming_matriz(duplicados.empaquetar(a), duplicados.empaquetar(todos)).tolist() == [[64]]


def test_empaquetar_exige_64_bits():
    with pytest.raises(ValueError, match="64"):
        duplicados.empaquetar(np.zeros((2, 63), dtype=bool))


def test_distancia_con_espejo_a_mano():
    """d_H = mín(H(a,b), H(a,fb), H(fa,b)); simétrica aunque H(a,fb) ≠ H(fa,b)."""
    def bits(*pos):
        v = np.zeros(64, dtype=bool)
        v[list(pos)] = True
        return v
    h = np.stack([bits(), bits(0, 1, 2, 3, 4, 5)])        # a, b
    hf = np.stack([bits(0, 1, 2, 3), bits(0, 1, 2, 3, 4, 5, 6, 7, 8)])   # espejo(a), espejo(b)
    H, Hf = duplicados.empaquetar(h), duplicados.empaquetar(hf)
    # H(a,b)=6, H(a,fb)=9, H(fa,b)=2 → d=2 en ambos órdenes
    d = duplicados.distancia_hamming_espejo(H, Hf, H, Hf)
    assert d[0, 1] == d[1, 0] == 2
    sin = duplicados.distancia_hamming_espejo(H, None, H, None)
    assert sin[0, 1] == sin[1, 0] == 6


def test_coseno_a_mano():
    z = np.array([[1.0, 0.0], [1.0, 1.0], [0.0, 3.0]])
    c = duplicados.coseno_matriz(duplicados.normalizar_filas(z), duplicados.normalizar_filas(z))
    assert c[0, 1] == pytest.approx(1 / np.sqrt(2)) and c[0, 2] == pytest.approx(0.0) and c[1, 2] == pytest.approx(1 / np.sqrt(2))
    assert np.allclose(np.diag(c), 1.0)


def test_normalizar_filas_rechaza_vector_nulo():
    with pytest.raises(ValueError, match="nul"):
        duplicados.normalizar_filas(np.array([[0.0, 0.0], [1.0, 0.0]]))


def test_componentes_a_mano():
    """(0,1),(1,2),(4,5) en 7 nodos → {0,1,2}, {3}, {4,5}, {6}; etiqueta = menor índice de la componente."""
    etq = duplicados.componentes(7, [(0, 1), (2, 1), (4, 5)])
    assert etq.tolist() == [0, 0, 0, 3, 4, 4, 6]
    assert duplicados.componentes(3, []).tolist() == [0, 1, 2]


def test_componentes_coincide_con_networkx():
    nx = pytest.importorskip("networkx")
    r = np.random.default_rng(3)
    n = 200
    pares = [tuple(sorted(map(int, r.choice(n, 2, replace=False)))) for _ in range(150)]
    etq = duplicados.componentes(n, pares)
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(pares)
    esperado = {frozenset(c) for c in nx.connected_components(g)}
    obtenido = {frozenset(np.flatnonzero(etq == e).tolist()) for e in np.unique(etq)}
    assert obtenido == esperado


def test_nombres_de_grupo_deterministas():
    ids = ["m2_00001", "m2_00003", "m2_00004", "m2_00009"]
    assert duplicados.nombrar_grupos(ids, np.array([0, 1, 0, 3])) == ["g_00001", "g_00002", "g_00001", "g_00003"]


def test_pares_por_bloques_igual_a_fuerza_bruta():
    """Los pares que devuelve el barrido por bloques son exactamente los de la matriz completa (i < j)."""
    r = np.random.default_rng(5)
    n = 37
    h, hf = r.random((n, 64)) < 0.5, r.random((n, 64)) < 0.5
    h[1], h[2] = h[0], ~h[0]                                    # un duplicado exacto y un opuesto
    z = r.uniform(0, 1, (n, 8))
    z[3] = z[4] * 2                                             # coseno 1
    H, Hf, Zn = duplicados.empaquetar(h), duplicados.empaquetar(hf), duplicados.normalizar_filas(z)
    pares = duplicados.pares_cercanos(H, Hf, Zn, umbral_hamming=20, umbral_coseno=0.9, bloque=8)
    D = duplicados.distancia_hamming_espejo(H, Hf, H, Hf)
    C = duplicados.coseno_matriz(Zn, Zn)
    esperado = {(i, j) for i in range(n) for j in range(i + 1, n) if D[i, j] <= 20 or C[i, j] >= 0.9}
    assert {(p.i, p.j) for p in pares} == esperado
    for p in pares:
        assert p.hamming == D[p.i, p.j] and p.coseno == pytest.approx(C[p.i, p.j])
        assert p.por_hamming == (D[p.i, p.j] <= 20) and p.por_coseno == (C[p.i, p.j] >= 0.9)


# --------------------------------------------------------------------------- variantes sintéticas (hash real + características inyectadas)
def test_variantes_caen_en_el_mismo_grupo_y_las_distintas_no(conjunto_sintetico):
    imgs, nombres = conjunto_sintetico
    h, hf = duplicados.hashes_de_imagenes(imgs, tam_hash=8, factor_alta_frecuencia=4, espejo=True)
    # el recorte no lo junta el pHash (≈16 bits) sino las características: se inyecta cos ≈ 1 con la base
    z = _feats_inyectadas(len(imgs), iguales_a_base=[nombres.index("recorte")])
    pares = duplicados.pares_cercanos(duplicados.empaquetar(h), duplicados.empaquetar(hf), duplicados.normalizar_filas(z), TAU_H, TAU_C, bloque=4)
    etq = duplicados.componentes(len(imgs), [(p.i, p.j) for p in pares])
    assert len(set(etq[:5])) == 1, dict(zip(nombres, etq.tolist()))
    assert len(set(etq[5:])) == 6 and not set(etq[5:]) & {etq[0]}


def test_espejo_lo_detecta_el_hash_con_espejo_y_no_el_phash_simple(conjunto_sintetico):
    imgs, nombres = conjunto_sintetico
    h, hf = duplicados.hashes_de_imagenes(imgs, tam_hash=8, factor_alta_frecuencia=4, espejo=True)
    H, Hf = duplicados.empaquetar(h), duplicados.empaquetar(hf)
    i, j = nombres.index("base"), nombres.index("espejo")
    simple = duplicados.hamming_matriz(H[[i]], H[[j]])[0, 0]
    con_espejo = duplicados.distancia_hamming_espejo(H[[i]], Hf[[i]], H[[j]], Hf[[j]])[0, 0]
    assert simple > TAU_H and con_espejo <= TAU_H, (simple, con_espejo)
    assert con_espejo == 0


def test_brillo_y_copia_a_distancia_cero_y_recorte_lejos_para_el_hash(conjunto_sintetico):
    """Documenta por qué hacen falta los dos criterios: el pHash no ve el recorte del 5 % por lado."""
    imgs, nombres = conjunto_sintetico
    h, hf = duplicados.hashes_de_imagenes(imgs, tam_hash=8, factor_alta_frecuencia=4, espejo=True)
    D = duplicados.distancia_hamming_espejo(*(duplicados.empaquetar(x) for x in (h, hf, h, hf)))
    assert D[0, nombres.index("copia")] == 0 and D[0, nombres.index("brillo")] == 0
    assert D[0, nombres.index("recorte")] > TAU_H
    assert min(D[0, k] for k in range(5, 11)) > TAU_H


def test_hash_de_imagen_igual_a_imagehash(conjunto_sintetico):
    imagehash = pytest.importorskip("imagehash")
    imgs, _ = conjunto_sintetico
    h, hf = duplicados.hashes_de_imagenes(imgs[:3], tam_hash=8, factor_alta_frecuencia=4, espejo=True)
    for k, img in enumerate(imgs[:3]):
        assert (h[k] == imagehash.phash(img).hash.flatten()).all()
        assert (hf[k] == imagehash.phash(ImageOps.mirror(img)).hash.flatten()).all()


def test_sin_espejo_no_se_calcula_el_hash_del_espejo(conjunto_sintetico, monkeypatch):
    """R9: con espejo = False no se invoca ImageOps.mirror y h_espejo es None."""
    imgs, _ = conjunto_sintetico

    def prohibido(*a, **k):
        raise AssertionError("no debe calcularse el espejo")
    monkeypatch.setattr(duplicados.ImageOps, "mirror", prohibido)
    h, hf = duplicados.hashes_de_imagenes(imgs[:2], tam_hash=8, factor_alta_frecuencia=4, espejo=False)
    assert hf is None and h.shape == (2, 64)


def test_estadisticas_vecinos_igual_a_fuerza_bruta():
    """Vecino más cercano (d_H mínima y coseno máximo sin la propia imagen) e histogramas de los pares i < j."""
    r = np.random.default_rng(8)
    n = 29
    h, hf = r.random((n, 64)) < 0.5, r.random((n, 64)) < 0.5
    h[3] = h[7]
    z = r.uniform(0, 1, (n, 6))
    H, Hf, Zn = duplicados.empaquetar(h), duplicados.empaquetar(hf), duplicados.normalizar_filas(z)
    est = duplicados.estadisticas_vecinos(H, Hf, Zn, bloque=5)
    D = duplicados.distancia_hamming_espejo(H, Hf, H, Hf)
    C = duplicados.coseno_matriz(Zn, Zn)
    otros = ~np.eye(n, dtype=bool)
    assert est["nn_hamming"].tolist() == [int(D[i][otros[i]].min()) for i in range(n)]
    assert np.allclose(est["nn_coseno"], [C[i][otros[i]].max() for i in range(n)])
    sup = np.triu(np.ones((n, n), dtype=bool), k=1)
    assert est["hist_hamming"].tolist() == np.bincount(D[sup], minlength=65).tolist()
    assert est["hist_coseno"].tolist() == np.histogram(np.clip(C[sup], 0, 1), bins=est["bordes_coseno"])[0].tolist()
    assert est["hist_hamming"].sum() == est["hist_coseno"].sum() == n * (n - 1) // 2


def test_mutante_sin_espejo_deja_el_espejo_fuera_del_grupo(conjunto_sintetico):
    """Mutante «se quita el espejo»: con hf=None el espejo queda solo y la verificación de grupos lo detecta."""
    imgs, nombres = conjunto_sintetico
    h, hf = duplicados.hashes_de_imagenes(imgs, tam_hash=8, factor_alta_frecuencia=4, espejo=True)
    z = _feats_inyectadas(len(imgs), iguales_a_base=[nombres.index("recorte")])
    zn, H, Hf = duplicados.normalizar_filas(z), duplicados.empaquetar(h), duplicados.empaquetar(hf)
    pares_buenos = duplicados.pares_cercanos(H, Hf, zn, TAU_H, TAU_C, bloque=4)
    pares_mutante = duplicados.pares_cercanos(H, None, zn, TAU_H, TAU_C, bloque=4)
    etq_mutante = duplicados.componentes(len(imgs), [(p.i, p.j) for p in pares_mutante])
    assert etq_mutante[nombres.index("espejo")] != etq_mutante[0]
    # la prueba de invariantes (todo par con arista dentro de un grupo) atrapa al mutante
    assert particion.pares_fuera_de_grupo(etq_mutante, [(p.i, p.j) for p in pares_buenos]) >= 1
    etq_buena = duplicados.componentes(len(imgs), [(p.i, p.j) for p in pares_buenos])
    assert particion.pares_fuera_de_grupo(etq_buena, [(p.i, p.j) for p in pares_buenos]) == 0


def test_guarda_del_grupo_mas_grande_dispara():
    etq = np.array([0] * 16 + list(range(16, 100)))           # componente de 16 de 100 = 16 % > 15 %
    with pytest.raises(duplicados.GrupoDemasiadoGrande, match=r"16 de 100"):
        duplicados.verificar_tamano_maximo(etq, fraccion_maxima=0.15)
    duplicados.verificar_tamano_maximo(np.array([0] * 15 + list(range(15, 100))), fraccion_maxima=0.15)   # 15 % exacto: pasa


# --------------------------------------------------------------------------- D9: marca de tiempo de la cámara
def test_marca_de_tiempo_formato_y_milisegundos():
    import datetime as dt
    ms = duplicados.marca_de_tiempo("raiz/clase/IMG_20240930_132316665_HDR_AE.jpg", PATRON_T)
    esperado = dt.datetime(2024, 9, 30, 13, 23, 16, 665000, tzinfo=dt.timezone.utc).timestamp() * 1000
    assert ms == int(round(esperado))
    otro = duplicados.marca_de_tiempo("IMG_20240930_132316666_BURST000_COVER.jpg", PATRON_T)
    assert otro - ms == 1                                          # el último grupo de 3 dígitos son milisegundos


@pytest.mark.parametrize("nombre", ["img_43513.jpg", "IMG_3748.JPG", "2019-04-2416-05-13.png",
                                    "photo_2024-09-14_14-51-03 (3).jpg", "IMG_20241330_132316665.jpg",
                                    "IMG_20240930_256316665.jpg", "xIMG_20240930_132316665.jpg",
                                    "IMG_20240230_132316665.jpg", "IMG_2024093_1323166650.jpg",
                                    "IMG_20240930_1323166650.jpg"])
def test_marca_de_tiempo_ausente_o_invalida_es_none(nombre):
    """Sin la forma IMG_AAAAMMDD_HHMMSSmmm (o con fecha u hora imposibles) no hay marca: D9 solo usa ese patrón."""
    assert duplicados.marca_de_tiempo(nombre, PATRON_T) is None


def test_formatos_de_la_config_reutilizan_los_patrones_de_jo1():
    """PNG y photo_ se toman de PATRONES_NOMBRE de datos.py (sin duplicarlos); IMG_ es propio porque el de JO-1 no captura
    los milisegundos."""
    from src.m2_conduccion.datos import PATRONES_NOMBRE
    f = dict(FORMATOS_T)
    assert f["AAAA-MM-DDhh-mm-ss"] == PATRONES_NOMBRE["AAAA-MM-DDhh-mm-ss"].pattern          # ya termina en «$»
    assert f["photo_AAAA-MM-DD_hh-mm-ss"] == PATRONES_NOMBRE["photo_AAAA-MM-DD_hh-mm-ss"].pattern + r"(?!\d)"
    assert f["IMG_AAAAMMDD_HHMMSSmmm"] != PATRONES_NOMBRE["IMG_AAAAMMDD_hhmmss"].pattern


@pytest.mark.parametrize("nombre, formato, fecha", [
    ("raiz/turning/2019-04-2416-05-13.png", "AAAA-MM-DDhh-mm-ss", (2019, 4, 24, 16, 5, 13, 0)),
    ("photo_2024-09-14_14-51-03 (3).jpg", "photo_AAAA-MM-DD_hh-mm-ss", (2024, 9, 14, 14, 51, 3, 0)),
    ("IMG_20240930_132316665_HDR.jpg", "IMG_AAAAMMDD_HHMMSSmmm", (2024, 9, 30, 13, 23, 16, 665000))])
def test_marca_y_formato_de_cada_formato(nombre, formato, fecha):
    import datetime as dt
    esperado = int(round(dt.datetime(*fecha, tzinfo=dt.timezone.utc).timestamp() * 1000))
    assert duplicados.marca_y_formato(nombre, FORMATOS_T) == (formato, esperado)


@pytest.mark.parametrize("nombre", ["2019-02-3016-05-13.png", "2019-04-2425-05-13.png", "2019-04-2416-60-13.png",
                                    "2019-04-2416-05-13", "photo_2024-13-14_14-51-03.jpg", "photo_2024-09-14_14-61-03.jpg",
                                    "photo_2024-9-14_14-51-03.jpg", "img_43513.jpg", "IMG_3748.JPG",
                                    "IMG_20240930_1323166650.jpg", "photo_2024-09-14_14-51-031.jpg"])
def test_marca_y_formato_ausente_o_imposible(nombre):
    assert duplicados.marca_y_formato(nombre, FORMATOS_T) is None


def test_umbral_inclusivo_con_resolucion_de_segundos_y_mezcla_de_formatos():
    """PNG a 10 s exactos → arista; a 11 s → no. Mezcla IMG_ (ms) con PNG (s): misma escala (ms desde 1970, UTC
    nominal), se comparan: 10,000 s → arista; 10,500 s → no."""
    nombres = ["2019-04-2416-05-13.png", "2019-04-2416-05-23.png", "2019-04-2416-05-34.png",
               "IMG_20190424_160544000.jpg", "IMG_20190424_160555500.jpg"]
    t = [duplicados.marca_y_formato(n, FORMATOS_T)[1] for n in nombres]
    assert duplicados.pares_por_tiempo(t, umbral_segundos=10) == [(0, 1, 10.0), (2, 3, 10.0)]


def test_formatos_de_tiempo_vacios_fallan():
    cfg = copy.deepcopy(CFG_REAL)
    cfg["tiempo"]["formatos"] = []
    with pytest.raises(ValueError, match="tiempo.formatos"):
        particion._validar_cfg(cfg)


def test_patron_de_tiempo_mal_formado_en_la_config_falla():
    cfg = copy.deepcopy(CFG_REAL)
    cfg["tiempo"]["formatos"][0]["patron"] = r"^IMG_(\d{8})_(\d{9})"        # 2 grupos, no 6 ni 7
    with pytest.raises(ValueError, match="grupos"):
        particion._validar_cfg(cfg)
    cfg = copy.deepcopy(CFG_REAL)
    cfg["tiempo"]["formatos"][1]["patron_jo1"] = "no_existe"
    with pytest.raises(ValueError, match="patron_jo1"):
        particion._validar_cfg(cfg)


def test_pares_por_tiempo_a_mano():
    """Umbral 10 s, inclusivo, en milisegundos enteros. Entrada desordenada; None no participa; otro día no se une."""
    dia = 86_400_000
    t = [10_000, None, 0, 20_001, dia + 5, 10_000, dia]
    pares = duplicados.pares_por_tiempo(t, umbral_segundos=10)
    # (0,2): 10 000 ms → sí (inclusivo); (0,3) y (3,5): 10 001 ms → no; (0,5): 0; (2,5): 10 000; (4,6): 5 ms
    assert pares == [(0, 2, 10.0), (0, 5, 0.0), (2, 5, 10.0), (4, 6, 0.005)]
    assert all(i < j for i, j, _ in pares)


def test_arista_por_tiempo_en_main_y_sin_clase(tmp_path):
    """Dos imágenes distintas (clases distintas, hash y coseno lejos) a 4,335 s quedan en el mismo grupo con criterio
    «tiempo»; la de 19 s después no se une. Los conteos de tiempo van a resumen.json."""
    cfg = _montar(tmp_path)
    particion.main(cfg)
    d = _leer(Path(cfg["entrada"]["carpeta"]) / "indice.csv")
    pos = {(c, m): d[d["clase"] == c].iloc[m]["id"] for (c, m) in MARCAS_FIXTURE}
    v0, v1 = pos[("other_activities", 0)], pos[("other_activities", 1)]
    a, b, c = pos[("safe_driving", 8)], pos[("turning", 9)], pos[("talking_phone", 10)]
    g = d.set_index("id")["grupo_duplicado"]
    assert g[a] == g[b] != g[c]
    p = _leer(Path(cfg["salida"]["carpeta"]) / "pares_cercanos.csv").set_index(["id_a", "id_b"])
    assert p.loc[(a, b), "criterio"] == "tiempo" and float(p.loc[(a, b), "segundos"]) == pytest.approx(4.335)
    # R5: un par que cumple hash y tiempo a la vez lleva el criterio del hash y la columna segundos llena
    assert p.loc[(v0, v1), "criterio"] == "hamming" and p.loc[(v0, v1), "segundos"] == "3.000"
    r = json.loads((Path(cfg["salida"]["carpeta"]) / "resumen.json").read_text(encoding="utf-8"))
    assert r["tiempo_camara"]["fotos_con_marca"] == 5 and r["tiempo_camara"]["pares_por_tiempo"] == 2
    assert r["tiempo_camara"]["pares_solo_por_tiempo"] == 1
    assert r["tiempo_camara"]["fotos_con_marca_por_formato"] == {"IMG_AAAAMMDD_HHMMSSmmm": 5}
    assert r["tiempo_camara"]["pares_por_tiempo_entre_formatos"] == 0
    assert r["pares_por_criterio"]["tiempo"] == 1


def test_fuga_residual_en_resumen(tmp_path):
    cfg = _montar(tmp_path)
    particion.main(cfg)
    r = json.loads((Path(cfg["salida"]["carpeta"]) / "resumen.json").read_text(encoding="utf-8"))
    fr = r["fuga_residual"]
    d = _leer(Path(cfg["entrada"]["carpeta"]) / "indice.csv")
    for sp in ("validacion", "prueba"):
        b = fr[sp]
        assert b["n"] == int((d["split"] == sp).sum())
        assert b["vecino_en_train_coseno_ge_umbral"] == 0                     # lo garantiza la partición
        assert b["vecino_en_train_coseno_lt_0_90"] + b["vecino_en_train_coseno_0_90_a_0_95"] == b["n"]
        assert 0 <= b["vecino_en_train_coseno_0_94_a_0_95"] <= b["vecino_en_train_coseno_0_90_a_0_95"]
        assert b["fotos_con_marca_y_una_de_train_a_le_10_s"] == 0
        assert b["fotos_con_marca_y_una_de_train_a_le_60_s"] <= b["fotos_con_marca"]


# --------------------------------------------------------------------------- caché (A3) y config
def test_cache_se_invalida_si_cambian_red_media_o_desviacion(tmp_path):
    ruta = tmp_path / "c.npz"
    base = {"red": "resnet18", "media": [0.485, 0.456, 0.406], "desviacion": [0.229, 0.224, 0.225]}
    duplicados.guardar_cache(ruta, ["a"], np.ones((1, 3), np.float32), "sha", "h", **base)
    assert duplicados.cache_valida(ruta, ["a"], "sha", "h", **base)
    for clave, otro in [("red", "resnet50"), ("media", [0.5, 0.5, 0.5]), ("desviacion", [0.2, 0.2, 0.2])]:
        assert not duplicados.cache_valida(ruta, ["a"], "sha", "h", **{**base, clave: otro}), clave
    np.savez(ruta, ids=np.array(["a"]), caracteristicas=np.ones((1, 3), np.float32), sha256_pesos=np.array("sha"),
             huella_imagenes=np.array("h"))                               # caché de antes de A3, sin esos campos
    assert not duplicados.cache_valida(ruta, ["a"], "sha", "h", **base)


@pytest.mark.parametrize("ruta, valor, mensaje", [
    (("grafo", "umbral_coseno"), 1.5, "umbral_coseno"), (("grafo", "umbral_coseno"), -0.1, "umbral_coseno"),
    (("hash", "tam_hash"), 7, "tam_hash"), (("hash", "espejo"), "si", "espejo"),
    (("caracteristicas", "red"), "resnet50", "red"), (("grafo", "fraccion_maxima_grupo"), 0.0, "fraccion_maxima_grupo"),
    (("tiempo", "umbral_segundos"), -1, "umbral_segundos")])
def test_validar_cfg_rechaza(ruta, valor, mensaje):
    cfg = copy.deepcopy(CFG_REAL)
    cfg[ruta[0]][ruta[1]] = valor
    with pytest.raises(ValueError, match=mensaje):
        particion._validar_cfg(cfg)
    assert particion._validar_cfg(copy.deepcopy(CFG_REAL)) is None


def test_datos_main_con_etapa_particion_delega(monkeypatch):
    """B2: run.py m2-datos con configs/m2/particion.yaml llega a particion.main (datos.main no exige el .zip)."""
    from src.m2_conduccion import datos
    recibido = {}

    def main_falso(cfg):
        recibido["cfg"] = cfg
        return 0
    monkeypatch.setattr(particion, "main", main_falso)
    cfg = copy.deepcopy(CFG_REAL)
    assert datos.main(cfg) == 0 and recibido["cfg"] is cfg


def test_si_falla_un_renombre_no_quedan_temporales(tmp_path, monkeypatch):
    """R3: si ``os.replace`` falla a mitad, se borran los temporales que quedaban (los ya renombrados no se deshacen)."""
    cfg = _montar(tmp_path)
    original, llamadas = particion.os.replace, []

    def falla_en_el_segundo(origen, destino):
        # save_json también usa os.replace (hacia «*.tmp»): solo se cuentan los renombres finales temporal → salida
        if not str(destino).endswith(".tmp"):
            llamadas.append(destino)
            if len(llamadas) == 2:
                raise OSError("renombre fallido (simulado)")
        return original(origen, destino)
    monkeypatch.setattr(particion.os, "replace", falla_en_el_segundo)
    with pytest.raises(OSError, match="simulado"):
        particion.main(cfg)
    assert len(llamadas) == 2 and not list(tmp_path.rglob("*.tmp"))


def test_escritura_por_temporales_si_falla_no_cambia_ninguna_salida(tmp_path, monkeypatch):
    """C5: todo se escribe primero a temporales y después se renombra; si falla un temporal no cambia ninguna salida ni
    quedan temporales."""
    cfg = _montar(tmp_path)
    indice = Path(cfg["entrada"]["carpeta"]) / "indice.csv"
    antes = {p: p.read_bytes() for p in (indice, Path(cfg["salida"]["calidad"]), Path(cfg["salida"]["procesado"]))}
    original = particion.save_json

    def falla_en_resumen(ruta, obj, *a, **k):
        if "resumen" in Path(ruta).name:
            raise OSError("disco lleno (simulado)")
        return original(ruta, obj, *a, **k)
    monkeypatch.setattr(particion, "save_json", falla_en_resumen)
    with pytest.raises(OSError, match="simulado"):
        particion.main(cfg)
    assert {p: p.read_bytes() for p in antes} == antes
    assert not list(tmp_path.rglob("*.tmp"))


# --------------------------------------------------------------------------- partición por grupos
def tabla_grupos(n_grupos: int = 400, semilla: int = 11, tam_max: int = 5) -> pd.DataFrame:
    """Imágenes sintéticas en grupos de tamaño 1..tam_max (sesgo a 1), con alguna clase mezclada dentro de un grupo."""
    r = np.random.default_rng(semilla)
    filas, k = [], 1
    for g in range(n_grupos):
        tam = int(min(tam_max, r.geometric(0.6)))
        clase = CLASES[int(r.integers(len(CLASES)))]
        for m in range(tam):
            c = CLASES[int(r.integers(len(CLASES)))] if (m == tam - 1 and tam > 2 and g % 7 == 0) else clase
            filas.append({"id": f"m2_{k:05d}", "grupo_duplicado": f"g_{g + 1:05d}", "clase": c})
            k += 1
    return pd.DataFrame(filas)


def test_regla_vectorial_a_mano():
    """Clases a, b; N = (10, 9); objetivos p·N: train (7; 6,3), val (1,5; 1,35), prueba (1,5; 1,35). Tamaños distintos: la
    semilla no influye. G1 (7,1): puntajes 55,3 / 11,85 / 11,85 → train. G2 (0,6): 31,8 / 8,1 / 8,1 → train (déficit de
    train queda (0; −0,7)). G3 (2,1): −0,7 / 4,35 / 4,35 → validacion (empate: el primero). G4 (1,1): −0,7 / −0,15 / 2,85 → prueba."""
    filas = [("G1", "a", 7), ("G1", "b", 1), ("G2", "b", 6), ("G3", "a", 2), ("G3", "b", 1), ("G4", "a", 1), ("G4", "b", 1)]
    df = pd.DataFrame([{"grupo_duplicado": g, "clase": c} for g, c, n in filas for _ in range(n)])
    s = particion.asignar_split(df, PROPORCIONES, semilla=0)
    assert pd.DataFrame({"g": df["grupo_duplicado"], "s": s}).groupby("g")["s"].first().to_dict() == {
        "G1": "train", "G2": "train", "G3": "validacion", "G4": "prueba"}


def _desviacion_en_sigmas(clases: pd.Series, split: pd.Series) -> float:
    """Envoltorio de ``particion._desviacion_en_sigmas`` (máx_{c,k} |n_kc/N_c − p_k| / sqrt(p_k(1−p_k)/N_c)). Tolerancia de
    las pruebas = 1σ: «tan balanceada como lo sería típicamente una partición al azar por imagen» (criterio empírico, no
    una cota demostrada para grupos mixtos)."""
    return particion._desviacion_en_sigmas(pd.DataFrame({"clase": clases.to_numpy(), "split": split.to_numpy()}),
                                          PROPORCIONES)


def sesiones(n: int = 150, semilla: int = 6) -> pd.DataFrame:
    """Grupos tipo «sesión» con clases mezcladas, como en los datos reales: tamaño de cola pesada (≤ 150) y mezcla de clases
    Dirichlet(0,6) por grupo."""
    r = np.random.default_rng(semilla)
    filas, k = [], 1
    for g in range(n):
        tam = int(min(150, 1 + r.pareto(1.2) * 8))
        for ci, m in enumerate(r.multinomial(tam, r.dirichlet([0.6] * len(CLASES)))):
            for _ in range(m):
                filas.append({"id": f"m2_{k:05d}", "grupo_duplicado": f"g_{g + 1:05d}", "clase": CLASES[ci]})
                k += 1
    return pd.DataFrame(filas)


def _asignar_por_mayoritaria(df: pd.DataFrame, proporciones: dict, semilla: int) -> pd.Series:
    """MUTANTE (método anterior a D7): estrato = clase mayoritaria del grupo; voraz por déficit del estrato."""
    p = np.array(list(proporciones.values()))
    rng = np.random.default_rng(semilla)
    tam = df.groupby("grupo_duplicado").size()
    n = df.groupby(["grupo_duplicado", "clase"]).size().rename("n").reset_index()
    n = n.sort_values(["grupo_duplicado", "n", "clase"], ascending=[True, False, True], kind="stable")
    cg = n.drop_duplicates("grupo_duplicado").set_index("grupo_duplicado")["clase"]
    destino = {}
    for c in sorted(cg.unique()):
        grupos = np.array(sorted(cg.index[cg == c]))
        grupos = grupos[rng.permutation(len(grupos))]
        grupos = grupos[np.argsort(-tam[grupos].to_numpy(), kind="stable")]
        obj, asig = p * int(tam[grupos].sum()), np.zeros(3)
        for g in grupos:
            k = int(np.argmax(obj - asig))
            asig[k] += tam[g]
            destino[g] = SPLITS[k]
    return df["grupo_duplicado"].map(destino)


def test_d7_regresion_caso_fijo_semilla_6_grupos_mixtos_dentro_de_1_sigma_y_la_mayoritaria_no():
    """D7: con grupos de clases mezcladas, cada clase queda a ≤ 1σ de 70/15/15; el método por clase mayoritaria no.
    (Caso fijo: semilla 6 del generador. Con la semilla 7 el método nuevo da 1,22σ: no hay garantía, ver docstring del módulo.)"""
    df = sesiones()
    nuevo = particion.asignar_split(df, PROPORCIONES, semilla=2026)
    assert (pd.DataFrame({"g": df["grupo_duplicado"], "s": nuevo}).groupby("g")["s"].nunique() == 1).all()
    assert _desviacion_en_sigmas(df["clase"], nuevo) <= 1.0
    assert _desviacion_en_sigmas(df["clase"], _asignar_por_mayoritaria(df, PROPORCIONES, 2026)) > 1.0


def tabla_grupos_puros(n_grupos: int = 1500, semilla: int = 11, tam_max: int = 5) -> pd.DataFrame:
    """Grupos de una sola clase: ahí la regla vectorial se reduce al voraz por déficit de esa clase."""
    df = tabla_grupos(n_grupos, semilla, tam_max)
    df["clase"] = df.groupby("grupo_duplicado")["clase"].transform("first")
    return df


def test_grupos_puros_dentro_de_la_cota_demostrada():
    """Con grupos de una sola clase vale la cota demostrada en particion.py: |n_kc − p_k·N_c| ≤ 2·s_max(c)."""
    df = tabla_grupos_puros()
    s = particion.asignar_split(df, PROPORCIONES, semilla=2026)
    tam = df.groupby("grupo_duplicado").size()
    clase_g = df.groupby("grupo_duplicado")["clase"].first()
    for c in CLASES:
        m = df["clase"] == c
        s_max = int(tam[clase_g == c].max())
        for sp, p in PROPORCIONES.items():
            assert abs(int((s[m] == sp).sum()) - p * int(m.sum())) <= 2 * s_max, (c, sp)


def test_ningun_grupo_en_dos_splits_y_todos_asignados():
    df = tabla_grupos()
    s = particion.asignar_split(df, PROPORCIONES, semilla=2026)
    assert list(s.index) == list(df.index) and set(s) <= set(SPLITS) and s.notna().all() and (s != "").all()
    assert (pd.DataFrame({"g": df["grupo_duplicado"], "s": s}).groupby("g")["s"].nunique() == 1).all()


def test_determinismo_y_otra_semilla_otra_particion():
    df = tabla_grupos()
    a, b = particion.asignar_split(df, PROPORCIONES, 2026), particion.asignar_split(df, PROPORCIONES, 2026)
    c = particion.asignar_split(df, PROPORCIONES, 7)
    assert a.equals(b)
    assert not a.equals(c)
    assert (pd.DataFrame({"g": df["grupo_duplicado"], "s": c}).groupby("g")["s"].nunique() == 1).all()


def test_split_independiente_del_orden():
    df = tabla_grupos()
    a = particion.asignar_split(df, PROPORCIONES, 2026)
    barajada = df.sample(frac=1.0, random_state=0)
    b = particion.asignar_split(barajada, PROPORCIONES, 2026)
    assert a.to_dict() == b.reindex(a.index).to_dict()


def test_no_toca_el_azar_global():
    np.random.seed(123)
    antes = np.random.random()
    np.random.seed(123)
    particion.asignar_split(tabla_grupos(), PROPORCIONES, 2026)
    assert np.random.random() == antes


def test_proporciones_invalidas_fallan():
    df = tabla_grupos(50)
    with pytest.raises(ValueError):
        particion.asignar_split(df, {"train": 0.7, "validacion": 0.2, "prueba": 0.2}, 1)
    with pytest.raises(ValueError):
        particion.asignar_split(df, {"train": 0.85, "prueba": 0.15}, 1)


def test_mutante_particion_por_imagen_es_detectada():
    """Mutante: split al azar por imagen ignorando grupos → hay grupos en dos splits y pares que cruzan."""
    df = tabla_grupos()
    r = np.random.default_rng(0)
    mutante = pd.Series(r.choice(SPLITS, size=len(df), p=[0.7, 0.15, 0.15]), index=df.index)
    assert particion.grupos_en_varios_splits(df["grupo_duplicado"], mutante) > 0
    pares = [(i, j) for _, g in df.groupby("grupo_duplicado") for i, j in zip(g.index[:-1], g.index[1:])]
    assert particion.pares_que_cruzan(mutante, pares) > 0
    buena = particion.asignar_split(df, PROPORCIONES, 2026)
    assert particion.grupos_en_varios_splits(df["grupo_duplicado"], buena) == 0 and particion.pares_que_cruzan(buena, pares) == 0


def test_huella_particion_a_mano():
    df = pd.DataFrame({"id": ["m2_00002", "m2_00001"], "grupo_duplicado": ["g_00002", "g_00001"],
                       "split": ["prueba", "train"]})
    texto = "id,grupo_duplicado,split\nm2_00001,g_00001,train\nm2_00002,g_00002,prueba\n"
    assert particion.huella_particion(df) == hashlib.sha256(texto.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- características (sin pesos)
def test_caracteristicas_con_modelo_inyectado_y_normalizacion(tmp_path):
    torch = pytest.importorskip("torch")

    class Media(torch.nn.Module):                       # GAP sobre la entrada normalizada: comprobable a mano
        def forward(self, x):
            return x.mean(dim=(2, 3))

    rutas = []
    for k, color in enumerate([(255, 0, 0), (0, 128, 255)]):
        ruta = tmp_path / f"{k}.png"
        Image.new("RGB", (8, 8), color).save(ruta)
        rutas.append(ruta)
    media, desv = [0.5, 0.5, 0.5], [0.25, 0.5, 1.0]
    z = duplicados.caracteristicas(rutas, Media(), media, desv, lote=1, dispositivo="cpu")
    esperado = (np.array([[255, 0, 0], [0, 128, 255]]) / 255.0 - np.array(media)) / np.array(desv)
    assert z.shape == (2, 3) and z.dtype == np.float32
    assert np.allclose(z, esperado, atol=1e-6)


def test_normalizacion_de_la_config_igual_a_torchvision():
    """media/desviación de la config = las de ResNet18_Weights.IMAGENET1K_V1 (metadatos locales de torchvision, sin red)."""
    tv = pytest.importorskip("torchvision")
    t = tv.models.ResNet18_Weights.IMAGENET1K_V1.transforms()
    cfg = yaml.safe_load(CFG_PARTICION.read_text(encoding="utf-8"))
    assert cfg["caracteristicas"]["media"] == list(t.mean) and cfg["caracteristicas"]["desviacion"] == list(t.std)


def _pesos_locales() -> Path | None:
    cfg = yaml.safe_load(CFG_PARTICION.read_text(encoding="utf-8"))
    ruta = RAIZ / cfg["caracteristicas"]["pesos"]
    return ruta if ruta.is_file() else None


@pytest.mark.skipif(_pesos_locales() is None, reason="sin pesos locales (scripts/descargar_pesos_m2.py)")
def test_resnet18_local_da_el_gap_de_layer4_sin_red(monkeypatch):
    """El vector de 512 es la media espacial de layer4 (GAP), se carga desde el archivo local y no usa la red."""
    torch = pytest.importorskip("torch")

    def bloqueado(*a, **k):
        raise RuntimeError("red bloqueada")
    monkeypatch.setattr(socket.socket, "connect", bloqueado)
    monkeypatch.setattr(socket, "getaddrinfo", bloqueado)
    cfg = yaml.safe_load(CFG_PARTICION.read_text(encoding="utf-8"))
    modelo = duplicados.cargar_resnet18(_pesos_locales(), cfg["caracteristicas"]["sha256_pesos"])
    assert not modelo.training and not any(p.requires_grad for p in modelo.parameters())
    x = torch.randn(2, 3, 224, 224, generator=torch.Generator().manual_seed(0))
    with torch.no_grad():
        z = modelo(x)
        m = modelo
        y = m.maxpool(m.relu(m.bn1(m.conv1(x))))
        y = m.layer4(m.layer3(m.layer2(m.layer1(y))))
        gap = y.mean(dim=(2, 3))
    assert z.shape == (2, 512) and torch.allclose(z, gap, atol=1e-5)


@pytest.mark.skipif(_pesos_locales() is None, reason="sin pesos locales")
def test_pesos_con_sha_distinto_fallan(tmp_path):
    falso = tmp_path / "resnet18-00000000.pth"
    falso.write_bytes(b"no son pesos")
    with pytest.raises(ValueError, match="SHA-256"):
        duplicados.cargar_resnet18(falso, "f" * 64)


# --------------------------------------------------------------------------- main de punta a punta (sin pesos: caché inyectada)
def _montar(tmp_path: Path, n_por_clase: int = 12, semilla_feats: int = 0, variantes_de: int = 3) -> dict:
    """Carpeta procesada mínima con la forma de JO-1 + caché de características válida; devuelve la config."""
    proc, eda, res = tmp_path / "processed", tmp_path / "eda", tmp_path / "particion"
    filas, origen, k = [], [], 0
    for c_i, clase in enumerate(CLASES):
        for m in range(n_por_clase):
            k += 1
            i = f"m2_{k:05d}"
            # las primeras «variantes_de» imágenes de cada clase son variantes de una misma base (espejo, brillo, copia)
            base = campo(1000 + c_i)
            if m < variantes_de:
                img = [base, ImageOps.mirror(base), variantes(base)["brillo"]][m % 3]
            else:
                img = campo(10_000 + k)
            archivo = f"imagenes/{clase}/{i}.jpg"
            (proc / archivo).parent.mkdir(parents=True, exist_ok=True)
            img.save(proc / archivo, "JPEG", quality=95)
            filas.append({"id": i, "archivo": archivo, "clase": clase, "grupo_duplicado": "", "split": "",
                          "ancho": 640, "alto": 480})
            origen.append({"id": i, "archivo_original": f"raiz/{clase}/" + MARCAS_FIXTURE.get((clase, m), f"img_{k}.jpg"),
                           "sha256_original": "0" * 64, "formato": "JPEG", "modo": "RGB", "orientacion_exif": ""})
    indice = pd.DataFrame(filas, columns=COLUMNAS_INDICE)
    proc.mkdir(parents=True, exist_ok=True)
    indice.to_csv(proc / "indice.csv", index=False, encoding="utf-8", lineterminator="\n")
    pd.DataFrame(origen).to_csv(proc / "origen.csv", index=False, encoding="utf-8", lineterminator="\n")
    eda.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"categoria": "ilegible", "elemento": "x", "valor": "OSError", "detalle": "d"}]).to_csv(
        eda / "calidad.csv", index=False, encoding="utf-8", lineterminator="\n")
    (eda / "procesado.json").write_text(json.dumps({"n_imagenes": len(indice), "sha256_indice": _sha(proc / "indice.csv")}),
                                        encoding="utf-8")
    cfg = yaml.safe_load(CFG_PARTICION.read_text(encoding="utf-8"))
    cfg["entrada"]["carpeta"] = str(proc)
    cfg["salida"]["carpeta"] = str(res)
    cfg["salida"]["calidad"] = str(eda / "calidad.csv")
    cfg["salida"]["procesado"] = str(eda / "procesado.json")
    cfg["grafo"]["umbral_hamming"] = TAU_H
    cfg["grafo"]["umbral_coseno"] = TAU_C
    cfg["caracteristicas"]["cache"] = str(tmp_path / "cache" / "caracteristicas.npz")
    ids = indice["id"].tolist()
    z = np.random.default_rng(semilla_feats).uniform(0, 1, (len(ids), 16)) ** 4
    _guardar_cache_cfg(cfg, ids, z.astype(np.float32), duplicados.huella_imagenes(proc, indice["archivo"].tolist()))
    return cfg


def _guardar_cache_cfg(cfg: dict, ids, z, huella: str) -> None:
    c = cfg["caracteristicas"]
    duplicados.guardar_cache(Path(c["cache"]), ids, z, sha256_pesos=c["sha256_pesos"], huella_imagenes=huella,
                             red=c["red"], media=c["media"], desviacion=c["desviacion"])


def test_main_llena_grupo_y_split_sin_tocar_lo_demas(tmp_path):
    cfg = _montar(tmp_path)
    proc = Path(cfg["entrada"]["carpeta"])
    antes = _leer(proc / "indice.csv")
    assert particion.main(cfg) == 0
    despues = _leer(proc / "indice.csv")
    assert list(despues.columns) == COLUMNAS_INDICE
    otras = [c for c in COLUMNAS_INDICE if c not in ("grupo_duplicado", "split")]
    assert despues[otras].equals(antes[otras])                       # mismas columnas, valores y orden de filas
    assert (despues["grupo_duplicado"] != "").all() and set(despues["split"]) <= set(SPLITS)
    assert (despues.groupby("grupo_duplicado")["split"].nunique() == 1).all()
    # las tres variantes (original, espejo, brillo) de cada clase quedan en un grupo
    for c in CLASES:
        assert despues[despues["clase"] == c]["grupo_duplicado"].iloc[:3].nunique() == 1
    res = Path(cfg["salida"]["carpeta"])
    r = json.loads((res / "resumen.json").read_text(encoding="utf-8"))
    assert r["pares_que_cruzan_splits"] == 0 and r["grupos_en_varios_splits"] == 0
    assert r["sha256_indice"] == _sha(proc / "indice.csv")
    assert r["huella_particion"] == particion.huella_particion(despues)
    assert json.loads(Path(cfg["salida"]["procesado"]).read_text(encoding="utf-8"))["sha256_indice"] == _sha(proc / "indice.csv")
    pares = _leer(res / "pares_cercanos.csv")
    assert list(pares.columns) == COLUMNAS_PARES and len(pares) == r["pares_por_criterio"]["total"]
    s = despues.set_index("id")["split"]
    assert (pares["id_a"].map(s) == pares["id_b"].map(s)).all()
    assert (res / "frontera.csv").is_file()


def test_main_dos_veces_mismo_indice_byte_a_byte_y_otra_semilla_cambia(tmp_path):
    cfg = _montar(tmp_path)
    indice = Path(cfg["entrada"]["carpeta"]) / "indice.csv"
    particion.main(cfg)
    primero = indice.read_bytes()
    calidad1 = Path(cfg["salida"]["calidad"]).read_bytes()
    particion.main(cfg)                                                  # idempotente: ignora grupo/split ya escritos
    assert indice.read_bytes() == primero
    assert Path(cfg["salida"]["calidad"]).read_bytes() == calidad1  # no duplica las filas de hallazgos
    otra = copy.deepcopy(cfg)
    otra["particion"]["semilla"] = cfg["particion"]["semilla"] + 1
    particion.main(otra)
    d = _leer(indice)
    assert indice.read_bytes() != primero
    assert (d.groupby("grupo_duplicado")["split"].nunique() == 1).all()


def test_main_guarda_15_por_ciento_no_escribe(tmp_path):
    cfg = _montar(tmp_path)
    cfg["grafo"]["umbral_coseno"] = 0.0                              # todo con todo → una componente del 100 %
    indice = Path(cfg["entrada"]["carpeta"]) / "indice.csv"
    antes = indice.read_bytes()
    with pytest.raises(duplicados.GrupoDemasiadoGrande, match="fraccion_maxima_grupo"):
        particion.main(cfg)
    assert indice.read_bytes() == antes
    assert not (Path(cfg["salida"]["carpeta"]) / "resumen.json").exists()


def test_main_cache_de_otras_imagenes_falla_sin_pesos(tmp_path):
    cfg = _montar(tmp_path)
    proc = Path(cfg["entrada"]["carpeta"])
    primera = next((proc / "imagenes").rglob("*.jpg"))
    campo(99).save(primera, "JPEG", quality=95)                     # cambian las imágenes → la caché ya no vale
    cfg["caracteristicas"]["pesos"] = str(tmp_path / "no_existe.pth")
    with pytest.raises(FileNotFoundError, match="descargar_pesos_m2"):
        particion.main(cfg)


def test_main_pares_entre_clases_van_a_calidad(tmp_path):
    cfg = _montar(tmp_path)
    proc = Path(cfg["entrada"]["carpeta"])
    idx = _leer(proc / "indice.csv")
    # copia exacta de una imagen de safe_driving dentro de turning → par entre clases
    a = idx[idx["clase"] == "safe_driving"].iloc[5]
    b = idx[idx["clase"] == "turning"].iloc[6]
    (proc / b["archivo"]).write_bytes((proc / a["archivo"]).read_bytes())
    z = duplicados.leer_cache(Path(cfg["caracteristicas"]["cache"]))["caracteristicas"]
    _guardar_cache_cfg(cfg, idx["id"].tolist(), z, duplicados.huella_imagenes(proc, idx["archivo"].tolist()))
    particion.main(cfg)
    cal = _leer(Path(cfg["salida"]["calidad"]))
    filas = cal[cal["categoria"] == "casi_duplicado_entre_clases"].set_index("elemento")
    pares = _leer(Path(cfg["salida"]["carpeta"]) / "pares_cercanos.csv")
    entre = pares[pares["clase_a"] != pares["clase_b"]]
    assert ((entre["id_a"] == a["id"]) & (entre["id_b"] == b["id"])).any()
    assert int(filas.loc["total", "valor"]) == len(entre) >= 1
    assert int(filas.loc["safe_driving|turning", "valor"]) == int(((entre["clase_a"] == "safe_driving")
                                                                    & (entre["clase_b"] == "turning")).sum())
    assert (cal["categoria"] == "ilegible").sum() == 1             # lo de JO-1 se conserva
    r = json.loads((Path(cfg["salida"]["carpeta"]) / "resumen.json").read_text(encoding="utf-8"))
    assert r["pares_entre_clases"]["total"] == len(entre)


def test_frontera_y_figura(tmp_path):
    """frontera.csv: «dentro» cumple el criterio de su panel; «fuera» no tiene arista; la figura se escribe."""
    from src.viz import figs_m2
    cfg = _montar(tmp_path)
    particion.main(cfg)
    res = Path(cfg["salida"]["carpeta"])
    f = _leer(res / "frontera.csv")
    ham, cos = f["hamming"].astype(int), f["coseno"].astype(float)
    dentro, fuera = f["lado"] == "dentro", f["lado"] == "fuera"
    assert (ham[dentro & (f["panel"] == "hamming")] <= TAU_H).all()
    assert (cos[dentro & (f["panel"] == "coseno")] >= TAU_C - 1e-6).all()
    assert (f.loc[fuera, "arista"] == "False").all() and (ham[fuera] > TAU_H).all() and (cos[fuera] < TAU_C + 1e-6).all()
    assert f.groupby(["panel", "lado"]).size().max() <= cfg["frontera"]["n_por_lado"]
    rutas = figs_m2.generar(carpeta_resultados=res, carpeta_figuras=tmp_path / "fig",
                            carpeta_procesada=Path(cfg["entrada"]["carpeta"]))
    assert [r.name for r in rutas] == ["frontera_duplicados.png"] and rutas[0].stat().st_size > 0
    with pytest.raises(FileNotFoundError, match="particion.yaml"):
        figs_m2.generar(carpeta_resultados=tmp_path / "no_existe", carpeta_figuras=tmp_path / "f")


def test_todo_o_nada_calidad_invalida_no_escribe_nada(tmp_path):
    """R1: se calcula y comprueba todo antes de escribir el primer archivo; un calidad.csv con otras columnas falla sin tocar
    indice.csv ni crear resultados."""
    cfg = _montar(tmp_path)
    indice = Path(cfg["entrada"]["carpeta"]) / "indice.csv"
    antes = indice.read_bytes()
    Path(cfg["salida"]["calidad"]).write_text("otra,cosa\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="columnas"):
        particion.main(cfg)
    assert indice.read_bytes() == antes and not Path(cfg["salida"]["carpeta"]).exists()


def test_todo_o_nada_sin_procesado_json_no_escribe_nada(tmp_path):
    cfg = _montar(tmp_path)
    indice = Path(cfg["entrada"]["carpeta"]) / "indice.csv"
    antes = indice.read_bytes()
    Path(cfg["salida"]["procesado"]).unlink()
    with pytest.raises(FileNotFoundError):
        particion.main(cfg)
    assert indice.read_bytes() == antes and not Path(cfg["salida"]["carpeta"]).exists()


def test_tiempo_sin_cache_queda_en_resumen_y_se_conserva_con_cache(tmp_path, monkeypatch):
    """B1: una corrida sin caché registra su tiempo y dispositivo; la corrida siguiente (con caché) los conserva junto a los
    suyos. La red se sustituye por un modelo inyectado (sin pesos)."""
    torch = pytest.importorskip("torch")

    class Media(torch.nn.Module):
        def forward(self, x):
            return x.mean(dim=(2, 3)) + 10.0          # positivo: el coseno está definido

    cfg = _montar(tmp_path)
    cfg["grafo"]["umbral_coseno"] = 1.0
    cache = Path(cfg["caracteristicas"]["cache"])
    cache.unlink()
    monkeypatch.setattr(particion.duplicados, "cargar_resnet18", lambda ruta, sha: Media())
    particion.main(cfg)
    res = Path(cfg["salida"]["carpeta"]) / "resumen.json"
    c1 = json.loads(res.read_text(encoding="utf-8"))["caracteristicas"]
    assert c1["esta_corrida"]["desde_cache"] is False and c1["esta_corrida"]["dispositivo"] == cfg["caracteristicas"]["dispositivo"]
    sin = c1["ultima_extraccion_sin_cache"]
    assert sin["dispositivo"] == cfg["caracteristicas"]["dispositivo"] and sin["tiempo_caracteristicas_s"] >= 0
    assert sin["tiempo_total_s"] >= sin["tiempo_caracteristicas_s"] and "JO-4" in c1["nota"]
    monkeypatch.setattr(particion.duplicados, "cargar_resnet18", lambda ruta, sha: pytest.fail("debe usar la caché"))
    particion.main(cfg)
    c2 = json.loads(res.read_text(encoding="utf-8"))["caracteristicas"]
    assert c2["esta_corrida"]["desde_cache"] is True and c2["ultima_extraccion_sin_cache"] == sin


def test_textos_vienen_de_la_config(tmp_path):
    """R4: el detalle de calidad.csv y el pie de la figura salen de configs/m2/particion.yaml (textos)."""
    from src.viz import figs_m2
    cfg = _montar(tmp_path)
    cfg["textos"]["detalle_entre_clases"] = "MARCA_DETALLE"
    cfg["textos"]["pie_figura_frontera"] = "MARCA_PIE"
    particion.main(cfg)
    cal = _leer(Path(cfg["salida"]["calidad"]))
    total = cal[(cal["categoria"] == "casi_duplicado_entre_clases") & (cal["elemento"] == "total")]
    assert total["detalle"].str.contains("MARCA_DETALLE").all()
    res = Path(cfg["salida"]["carpeta"])
    resumen = json.loads((res / "resumen.json").read_text(encoding="utf-8"))
    fig = figs_m2.figura_frontera(_leer(res / "frontera.csv"), resumen, Path(cfg["entrada"]["carpeta"]))
    assert any("MARCA_PIE" in x.get_text() for x in fig.texts)


def test_figura_con_frontera_vacia_da_error_claro(tmp_path):
    """R5: sin pares en frontera.csv, un error que lo dice (no un ValueError de NaN de matplotlib)."""
    from src.viz import figs_m2
    vacia = pd.DataFrame(columns=particion.COLUMNAS_FRONTERA)
    with pytest.raises(ValueError, match="no tiene pares"):
        figs_m2.figura_frontera(vacia, {"umbrales": {"hamming": 2, "coseno": 0.95}}, tmp_path)


def test_margenes_cubren_barrido_y_frontera():
    """R2: margen = lo que hay que mirar más allá de cada umbral para tener el barrido y los pares «justo fuera»."""
    cfg = {"grafo": {"umbral_hamming": 2, "umbral_coseno": 0.95},
           "barrido": {"hamming": [0, 2, 14], "coseno": [0.90, 0.98]},
           "frontera": {"margen_hamming": 4, "margen_coseno": 0.05}}
    mh, mc = particion._margenes(cfg)
    assert mh == 12 and mc == pytest.approx(0.05)
    cfg["barrido"] = {"hamming": [0, 2], "coseno": [0.97]}
    mh, mc = particion._margenes(cfg)
    assert mh == 4 and mc == pytest.approx(0.05)


def test_grupos_no_dependen_de_la_clase(tmp_path):
    """Las etiquetas no entran al grafo: barajar la columna clase no cambia los grupos (solo la estratificación)."""
    cfg = _montar(tmp_path)
    proc = Path(cfg["entrada"]["carpeta"])
    particion.main(cfg)
    g1 = _leer(proc / "indice.csv")["grupo_duplicado"].tolist()
    idx = _leer(proc / "indice.csv")
    idx["clase"] = idx["clase"].sample(frac=1.0, random_state=1).to_numpy()
    idx.to_csv(proc / "indice.csv", index=False, encoding="utf-8", lineterminator="\n")
    particion.main(cfg)
    assert _leer(proc / "indice.csv")["grupo_duplicado"].tolist() == g1


# --------------------------------------------------------------------------- datos reales versionados (lo que corre la CI)
reales = pytest.mark.skipif(not (RESUMEN_REAL.is_file() and PARES_REAL.is_file() and INDICE_REAL.is_file()),
                            reason="faltan los resultados reales de la partición de M2")


@pytest.fixture(scope="module")
def real():
    return {"indice": _leer(INDICE_REAL), "pares": _leer(PARES_REAL),
            "resumen": json.loads(RESUMEN_REAL.read_text(encoding="utf-8"))}


@reales
def test_real_todas_con_grupo_y_split(real):
    d = real["indice"]
    assert len(d) == 7276 and list(d.columns) == COLUMNAS_INDICE
    assert (d["grupo_duplicado"] != "").all() and set(d["split"]) == set(SPLITS)


@reales
def test_real_ningun_grupo_en_dos_splits(real):
    assert (real["indice"].groupby("grupo_duplicado")["split"].nunique() == 1).all()


@reales
def test_real_ningun_par_cruza_splits_y_cada_par_dentro_de_su_grupo(real):
    d, p = real["indice"].set_index("id"), real["pares"]
    assert list(p.columns) == COLUMNAS_PARES and len(p) > 0
    assert set(p["id_a"]) | set(p["id_b"]) <= set(d.index)
    assert (p["id_a"].map(d["split"]) == p["id_b"].map(d["split"])).all()
    assert (p["id_a"].map(d["grupo_duplicado"]) == p["id_b"].map(d["grupo_duplicado"])).all()
    assert (p["clase_a"] == p["id_a"].map(d["clase"])).all() and (p["clase_b"] == p["id_b"].map(d["clase"])).all()


@reales
def test_real_criterio_coherente_con_umbrales(real):
    p, r = real["pares"], real["resumen"]
    th, tc, ts = r["umbrales"]["hamming"], r["umbrales"]["coseno"], r["umbrales"]["segundos"]
    ham, cos = p["hamming"].astype(int), p["coseno"].astype(float)
    seg = pd.to_numeric(p["segundos"].replace("", np.nan))
    por_h, por_c, por_t = ham <= th, cos >= tc - 1e-6, seg <= ts         # el CSV redondea el coseno a 6 decimales
    assert (por_h | por_c | por_t).all()
    esperado = np.select([por_h & (cos >= tc + 1e-6), por_h, por_c, por_t], ["ambos", "hamming", "coseno", "tiempo"], "")
    ambiguos = (cos - tc).abs() < 1e-6
    assert ((p["criterio"] == esperado) | ambiguos).all()


@reales
def test_real_toda_rafaga_con_marca_a_le_umbral_esta_en_pares_y_no_cruza(real):
    """Completitud del criterio tiempo (D9) sin pesos: se recalculan las marcas desde origen.csv."""
    d, r = real["indice"], real["resumen"]
    o = _leer(PROCESADO_REAL / "origen.csv").set_index("id").loc[d["id"]]
    mf = [duplicados.marca_y_formato(n, FORMATOS_T) for n in o["archivo_original"]]
    t = [None if x is None else x[1] for x in mf]
    por_formato = pd.Series([x[0] for x in mf if x is not None]).value_counts().to_dict()
    assert por_formato == MARCAS_POR_FORMATO_REAL == r["tiempo_camara"]["fotos_con_marca_por_formato"]
    assert sum(x is not None for x in t) == r["tiempo_camara"]["fotos_con_marca"] == 598
    ids = d["id"].to_numpy()
    recalculados = {(ids[i], ids[j]) for i, j, _ in duplicados.pares_por_tiempo(t, r["umbrales"]["segundos"])}
    p = real["pares"]
    con_seg = p[p["segundos"] != ""]
    versionados = set(zip(con_seg.loc[con_seg["segundos"].astype(float) <= r["umbrales"]["segundos"], "id_a"],
                          con_seg.loc[con_seg["segundos"].astype(float) <= r["umbrales"]["segundos"], "id_b"]))
    assert recalculados == versionados and len(recalculados) == r["tiempo_camara"]["pares_por_tiempo"]
    s = d.set_index("id")["split"]
    assert all(s[a] == s[b] for a, b in recalculados)


@reales
def test_real_huellas_coinciden(real):
    r = real["resumen"]
    assert r["sha256_indice"] == _sha(INDICE_REAL)
    assert r["huella_particion"] == particion.huella_particion(real["indice"])
    assert r["sha256_pares_cercanos"] == _sha(PARES_REAL)
    assert r["pares_que_cruzan_splits"] == 0 and r["grupos_en_varios_splits"] == 0


@reales
def test_real_conteos_y_guarda(real):
    d, r = real["indice"], real["resumen"]
    tabla = d.groupby(["split", "clase"]).size()
    for sp, por_clase in r["conteos_split_clase"].items():
        for c, n in por_clase.items():
            assert int(tabla.get((sp, c), 0)) == n
    tam = d.groupby("grupo_duplicado").size()
    assert int(tam.max()) == r["grupo_mas_grande"]["tamano"] and tam.max() / len(d) <= r["umbrales"]["fraccion_maxima_grupo"]
    assert int(tam.size) == r["n_grupos"]


@reales
def test_real_proporciones_por_clase_dentro_de_1_sigma(real):
    """D7 sobre los datos reales: cada clase a ≤ 1σ de 70/15/15 (σ de una partición al azar por imagen; ≈ 1 pp en
    validación y prueba). Con el método por clase mayoritaria, other_activities quedaba en 75,5/11,3/13,2 %."""
    d = real["indice"]
    assert _desviacion_en_sigmas(d["clase"], d["split"]) <= 1.0
    assert _desviacion_en_sigmas(d["clase"], _asignar_por_mayoritaria(d, PROPORCIONES, 2026)) > 1.0


@reales
def test_real_mutante_por_imagen_seria_detectado(real):
    """Potencia de la prueba sobre los datos reales: un split al azar por imagen haría cruzar pares versionados."""
    d = real["indice"].reset_index(drop=True)
    pos = pd.Series(d.index, index=d["id"])
    pares = list(zip(real["pares"]["id_a"].map(pos), real["pares"]["id_b"].map(pos)))
    mutante = pd.Series(np.random.default_rng(0).choice(SPLITS, size=len(d), p=[0.7, 0.15, 0.15]))
    assert particion.pares_que_cruzan(mutante, pares) > 0
    assert particion.pares_que_cruzan(d["split"], pares) == 0


def _pares_hamming(h, hf, umbral: int, bloque: int) -> list[tuple[int, int, int]]:
    """Solo el criterio hash (sin pesos): pares i < j con d_H ≤ umbral, por bloques de filas."""
    n, pares = len(h), []
    for ini in range(0, n, bloque):
        fin = min(n, ini + bloque)
        d = duplicados.distancia_hamming_espejo(h[ini:fin], None if hf is None else hf[ini:fin], h, hf)
        cerca = (d <= umbral) & (np.arange(n)[None, :] > np.arange(ini, fin)[:, None])
        pares += [(int(ini + fi), int(j), int(d[fi, j])) for fi, j in zip(*np.nonzero(cerca))]
    return pares


@pytest.fixture(scope="module")
def hashes_reales(real):
    """pHash (y espejo) de las 7 276 imágenes versionadas, una sola vez por módulo (≈ 8 s)."""
    h = CFG_REAL["hash"]
    return duplicados.hashes_de_archivos([PROCESADO_REAL / a for a in real["indice"]["archivo"]], h["tam_hash"],
                                         h["factor_alta_frecuencia"], espejo=h["espejo"])


@reales
def test_real_todo_phash_tiene_32_unos(hashes_reales):
    """C4/R7: cada pHash de 64 bits umbralizado en la mediana tiene exactamente 32 unos, así que
    d_H = |a| + |b| − 2|a∧b| = 64 − 2|a∧b| es siempre par (base de los umbrales pares de D6)."""
    h, hf = hashes_reales
    assert (h.sum(axis=1) == 32).all() and (hf is None or (hf.sum(axis=1) == 32).all())


@reales
def test_real_phash_recalculado_coincide_con_pares(real, hashes_reales):
    """Recalcula el pHash (con espejo) de las 7 276 imágenes versionadas, sin pesos: el conjunto de pares con
    d_H ≤ τ_H es exactamente el de pares_cercanos.csv con criterio hamming/ambos, y ninguno cruza splits."""
    r = real["resumen"]
    d = real["indice"]
    h, hf = hashes_reales
    pares = _pares_hamming(duplicados.empaquetar(h), None if hf is None else duplicados.empaquetar(hf),
                           r["umbrales"]["hamming"], bloque=1024)
    ids = d["id"].to_numpy()
    recalculados = {(ids[i], ids[j]) for i, j, _ in pares}
    p = real["pares"]
    versionados = set(zip(p.loc[p["criterio"].isin(["hamming", "ambos"]), "id_a"],
                          p.loc[p["criterio"].isin(["hamming", "ambos"]), "id_b"]))
    assert recalculados == versionados
    assert all(dist % 2 == 0 for _, _, dist in pares)
    s = d.set_index("id")["split"]
    assert all(s[a] == s[b] for a, b in recalculados)
