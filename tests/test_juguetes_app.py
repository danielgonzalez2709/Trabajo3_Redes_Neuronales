"""Pruebas de los JSON y el ONNX de juguete de la app (DA-5; núcleo §5.4, §5.6 y §5.8).

Regeneran los juguetes en una carpeta temporal, comprueban que todo lleva ``juguete: true``, que el ONNX coincide con
PyTorch (probabilidades y mapas) y que lo versionado en ``app/public/model`` es exactamente lo que genera el script.
"""

import json
import math

import numpy as np
import pytest

import generar_juguetes_app as g  # scripts/ está en sys.path (conftest)

ARCHIVOS_JSON = [
    "m1/pronosticos.json", "m1/operacion.json", "m2/meta.json",
    "m3/destinos.json", "m3/usuarios.json", "m3/perfil_nuevo.json",
]


@pytest.fixture(scope="module")
def salida(tmp_path_factory):
    carpeta = tmp_path_factory.mktemp("juguetes")
    g.generar(carpeta)
    return carpeta


def _leer(carpeta, ruta):
    return json.loads((carpeta / ruta).read_text(encoding="utf-8"))


def test_genera_todos_los_archivos(salida):
    for ruta in ARCHIVOS_JSON + ["m2/modelo.onnx"]:
        assert (salida / ruta).is_file(), ruta
    assert len(list((salida / "m2" / "ejemplos").glob("*.png"))) >= 2


@pytest.mark.parametrize("ruta", ARCHIVOS_JSON)
def test_todo_es_de_juguete(salida, ruta):
    datos = _leer(salida, ruta)
    assert datos["juguete"] is True
    assert isinstance(datos["version"], int) and datos["version"] >= 1


def _casi_igual(a, b, tol=1e-4):
    """Igualdad estructural; los números se comparan con tolerancia (las redes pueden diferir en los últimos decimales
    entre sistemas operativos)."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_casi_igual(a[k], b[k], tol) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_casi_igual(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        return math.isclose(a, b, rel_tol=tol, abs_tol=tol)
    return a == b


def test_lo_versionado_coincide_con_lo_que_genera_el_script(salida):
    """Si cambia el generador hay que volver a correrlo y versionar el resultado."""
    for ruta in ARCHIVOS_JSON:
        assert _casi_igual(_leer(g.SALIDA_POR_DEFECTO, ruta), _leer(salida, ruta)), f"{ruta} está desactualizado: corre el script"


def test_m1_esquema_y_cuantiles(salida):
    p = _leer(salida, "m1/pronosticos.json")
    assert p["horizonte"] == 30 and p["cuantiles"] == sorted(set(p["cuantiles"]))
    for ruta in p["rutas"]:
        assert len(ruta["historia"]) == g.DIAS_HISTORIA
        assert ruta["historia"][-1]["fecha"] == p["fecha_origen"]
        assert [d["h"] for d in ruta["pronostico"]] == list(range(1, 31))
        for d in ruta["pronostico"]:
            assert len(d["q"]) == len(p["cuantiles"])
            assert d["q"] == sorted(d["q"]) and min(d["q"]) >= 0 and d["punto"] >= 0


def test_m1_dimensionar_juguete_casos_a_mano():
    p = dict(g.PARAMETROS_OPERACION)  # capacidad 40, ocupación 0,8, 2 viajes, 1,5 conductores por vehículo
    assert g.dimensionar_juguete(0, p) == {"despachos": 0, "vehiculos": 0, "conductores": 0}
    assert g.dimensionar_juguete(32, p) == {"despachos": 1, "vehiculos": 1, "conductores": 2}  # 32/(40·0,8) = 1 exacto
    assert g.dimensionar_juguete(33, p) == {"despachos": 2, "vehiculos": 1, "conductores": 2}
    assert g.dimensionar_juguete(320, p) == {"despachos": 10, "vehiculos": 5, "conductores": 8}  # ceil(7,5) = 8


def test_m1_los_casos_de_paridad_se_pueden_reproducir(salida):
    o = _leer(salida, "m1/operacion.json")
    assert len(o["casos_paridad"]) >= 10
    for c in o["casos_paridad"]:
        assert g.dimensionar_juguete(c["entrada"]["demanda"], c["entrada"]["parametros"]) == c["salida"]


def test_m2_onnx_coincide_con_pytorch(salida):
    """Reproduce cada caso con onnxruntime desde el archivo escrito y lo compara con lo que guardó PyTorch."""
    import onnxruntime as ort

    meta = _leer(salida, "m2/meta.json")
    sesion = ort.InferenceSession(str(salida / "m2" / "modelo.onnx"), providers=["CPUExecutionProvider"])
    assert [o.name for o in sesion.get_outputs()] == ["logits", "mapas"]
    alto, ancho = meta["tamano_entrada"]["alto"], meta["tamano_entrada"]["ancho"]
    media = np.array(meta["media"], dtype=np.float32)[:, None, None]
    desv = np.array(meta["desviacion"], dtype=np.float32)[:, None, None]
    pesos = np.array(meta["pesos_cabeza"])
    assert len(meta["casos_paridad"]) >= 3
    for caso in meta["casos_paridad"]:
        rgb = np.array(caso["entrada_rgb"], dtype=np.uint8).reshape(alto, ancho, 3)
        x = ((rgb.astype(np.float32).transpose(2, 0, 1) / 255.0 - media) / desv)[None].astype(np.float32)
        logits, mapas = sesion.run(["logits", "mapas"], {"entrada": x})
        e = np.exp(logits[0] - logits[0].max())
        probs = e / e.sum()
        np.testing.assert_allclose(probs, caso["probabilidades"], atol=1e-5)
        np.testing.assert_allclose(logits[0], caso["logits"], atol=1e-5)
        assert list(mapas.shape[1:]) == caso["forma_mapas"]
        np.testing.assert_allclose(mapas[0].reshape(-1), caso["mapas"], atol=1e-5)
        assert int(np.argmax(probs)) == caso["clase_predicha"]
        # CAM de la clase predicha = Σ_c w_kc · mapa_c (sin sesgo), y la cabeza GAP + lineal reproduce los logits.
        cam = np.tensordot(pesos[caso["clase_predicha"]], mapas[0], axes=(0, 0))
        np.testing.assert_allclose(cam.reshape(-1), caso["cam_clase_predicha"], atol=1e-4)
        logits_cabeza = pesos @ mapas[0].mean(axis=(1, 2)) + np.array(meta["sesgo_cabeza"])
        np.testing.assert_allclose(logits_cabeza, logits[0], atol=1e-4)


def test_m2_clases_y_grupo_de_alerta(salida):
    meta = _leer(salida, "m2/meta.json")
    assert [c["nombre"] for c in meta["clases"]] == [
        "Conducción segura", "Giro", "Escribir en el teléfono", "Hablar por teléfono", "Otros comportamientos riesgosos",
    ]
    assert meta["grupo_alerta"]["conduccion_segura"] == "sin_alerta"
    assert sum(v == "con_alerta" for v in meta["grupo_alerta"].values()) == 4
    assert meta["grupo_alerta_provisional"] is True
    assert set(meta["salidas_onnx"].values()) == {"logits", "mapas"}


def test_m2_la_generacion_es_determinista(salida, tmp_path):
    g.generar(tmp_path)
    assert _leer(tmp_path, "m2/meta.json") == _leer(salida, "m2/meta.json")
    assert (tmp_path / "m2" / "modelo.onnx").read_bytes() == (salida / "m2" / "modelo.onnx").read_bytes()


def test_m3_regla_de_juguete_y_casos(salida):
    d = _leer(salida, "m3/destinos.json")["destinos"]
    perfil = _leer(salida, "m3/perfil_nuevo.json")
    ids = [p["id"] for p in perfil["preferencias"]]
    peso = perfil["regla"]["peso_popularidad"]
    for c in perfil["casos_paridad"]:
        r = g.recomendar_perfil_juguete(c["preferencias"], d, ids, c["k"], peso)
        assert [f["destino_id"] for f in r] == [f["destino_id"] for f in c["top_k"]]
        assert all(math.isclose(a["puntaje"], b["puntaje"], rel_tol=1e-12) for a, b in zip(r, c["top_k"]))
    with pytest.raises(ValueError):
        g.recomendar_perfil_juguete([], d, ids, 3, peso)


def test_m3_todo_es_ficticio_y_coherente(salida):
    d = _leer(salida, "m3/destinos.json")["destinos"]
    u = _leer(salida, "m3/usuarios.json")
    assert all("(ficticio)" in x["nombre"] for x in d)
    assert all(x["nombre"].startswith("Usuario ficticio") for x in u["usuarios"])
    ids = {x["id"] for x in d}
    for x in u["usuarios"]:
        vistos = {h["destino_id"] for h in x["historial"]}
        assert vistos <= ids and not vistos & {f["destino_id"] for f in x["top_k"]}
        assert len(x["top_k"]) >= u["k_max"]
