"""Pruebas de los JSON y el ONNX de juguete de la app (DA-5; núcleo §5.4, §5.6 y §5.8).

Regeneran los juguetes en una carpeta temporal, comprueban que todo lleva ``juguete: true``, que el ONNX coincide con
PyTorch (probabilidades y mapas) y que el fixture versionado en ``app/tests/fixtures/juguete`` es exactamente lo que genera
el script. Lo que sirve la app (``app/public/model``) puede ser juguete o real: por módulo no se mezclan, y si es de juguete
debe coincidir con el fixture.
"""

import json
import math
import os
from pathlib import Path

import numpy as np
import pytest

import generar_juguetes_app as g  # scripts/ está en sys.path (conftest)

ARCHIVOS_JSON = [
    "m1/pronosticos.json", "m1/operacion.json", "m2/meta.json",
    "m3/destinos.json", "m3/usuarios.json", "m3/perfil_nuevo.json", "m3/casos_paridad.json",
]
FIXTURE = g.SALIDA_POR_DEFECTO  # app/tests/fixtures/juguete
# Lo que sirve la app. MODELO_SERVIDO_DIR existe SOLO para simular en una copia temporal la llegada de un modelo real.
SERVIDO = Path(os.environ.get("MODELO_SERVIDO_DIR") or g.RAIZ / "app" / "public" / "model")


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
    assert (salida / "m2" / "casos" / "caso_2.json").is_file()


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


def test_el_fixture_versionado_coincide_con_lo_que_genera_el_script(salida):
    """Si cambia el generador hay que volver a correrlo y versionar el resultado en app/tests/fixtures/juguete."""
    for ruta in ARCHIVOS_JSON:
        assert _casi_igual(_leer(FIXTURE, ruta), _leer(salida, ruta)), f"{ruta} del fixture está desactualizado: corre el script"
    assert (FIXTURE / "m2" / "modelo.onnx").is_file()
    assert sorted(p.name for p in (FIXTURE / "m2" / "ejemplos").glob("*.png")) == sorted(p.name for p in (salida / "m2" / "ejemplos").glob("*.png"))
    assert (FIXTURE / "m2" / "casos" / "caso_2.json").is_file()


def _modulo_servido(modulo):
    """`juguete` de cada JSON servido del módulo (los que existan)."""
    return {r: _leer(SERVIDO, r)["juguete"] for r in ARCHIVOS_JSON if r.startswith(f"{modulo}/") and (SERVIDO / r).is_file()}


@pytest.mark.parametrize("modulo", ["m1", "m2", "m3"])
def test_lo_servido_no_mezcla_juguete_y_real_dentro_de_un_modulo(modulo):
    valores = _modulo_servido(modulo)
    assert valores, f"{modulo}: no hay JSON servidos en app/public/model"
    assert all(isinstance(v, bool) for v in valores.values()), valores
    assert len(set(valores.values())) == 1, f"{modulo}: mezcla juguete y real: {valores}"


@pytest.mark.parametrize("modulo", ["m1", "m2", "m3"])
def test_si_el_modulo_servido_es_de_juguete_coincide_con_el_fixture(modulo):
    """Detecta juguetes servidos desactualizados. Un módulo real no se compara con nada aquí."""
    valores = _modulo_servido(modulo)
    if not valores or not all(valores.values()):
        pytest.skip(f"{modulo} servido es real (juguete: false): no se compara con el fixture")
    for ruta in (r for r in ARCHIVOS_JSON if r.startswith(f"{modulo}/")):
        assert _casi_igual(_leer(SERVIDO, ruta), _leer(FIXTURE, ruta)), f"{ruta} servido está desactualizado frente al fixture"
    if modulo == "m2":
        assert (SERVIDO / "m2" / "modelo.onnx").read_bytes() == (FIXTURE / "m2" / "modelo.onnx").read_bytes()


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


def _ruta(p, i=0):
    return p["rutas"][i]["ruta_id"]


def test_m1_dimensionar_juguete_casos_a_mano(salida):
    o = _leer(salida, "m1/operacion.json")
    ruta = _ruta(_leer(salida, "m1/pronosticos.json"))
    p = g.parametros_efectivos(o["parametros"], ruta)  # 0,7 bus de 40 + 0,3 buseta de 24, ocupación 0,8, 2 viajes, 1,5 cond.
    assert g.dimensionar_juguete(0, p)["despachos"] == 0
    util = (0.7 * 40 + 0.3 * 24) * 0.8  # 27,84 asientos útiles por despacho
    assert math.isclose(g.dimensionar_juguete(1, p)["pasos"]["asientos_utiles"], util)
    assert g.dimensionar_juguete(util * 3, p)["despachos"] == 3  # exacto: no sube por ruido de coma flotante
    r = g.dimensionar_juguete(util * 10, p)  # 10 despachos, 2 viajes por vehículo -> 5 vehículos, ceil(7,5) = 8 conductores
    assert (r["despachos"], r["vehiculos"], r["conductores"]) == (10, 5, 8)
    # un tiempo de ciclo largo limita los viajes por vehículo: 16 h / 9 h = 1 viaje -> 10 vehículos, 15 conductores
    r = g.dimensionar_juguete(util * 10, {**p, "por_ruta.tiempo_ciclo_h": 9.0})
    assert (r["pasos"]["viajes_efectivos"], r["vehiculos"], r["conductores"]) == (1, 10, 15)


def test_m1_parametros_con_fuente_o_supuesto_y_claves_obligatorias(salida):
    o = _leer(salida, "m1/operacion.json")
    pr = o["parametros"]
    todos = list(pr["globales"].values())
    for grupo in ("por_ruta", "por_clase", "composicion_clases"):
        todos += [par for d in pr[grupo].values() for par in d.values()]
    for par in todos:
        assert ("fuente" in par) != (par.get("supuesto") is True), par  # una cosa o la otra
        assert isinstance(par["valor"], (int, float)) and isinstance(par["unidad"], str)
    # los supuestos de vehículos y conductores son parámetros visibles (y con control)
    refs = {c["ref"] for c in o["controles"]}
    for clave in ("viajes_por_vehiculo_dia", "conductores_por_vehiculo", "ocupacion_objetivo", "cuantil"):
        assert pr["globales"][clave]["supuesto"] is True and f"globales.{clave}" in refs
    for comp in pr["composicion_clases"].values():
        assert math.isclose(sum(par["valor"] for par in comp.values()), 1.0)


def test_m1_la_ruta_de_regreso_existe_y_el_origen_es_el_ultimo_dia_de_la_serie(salida):
    p = _leer(salida, "m1/pronosticos.json")
    ids = {r["ruta_id"] for r in p["rutas"]}
    assert all(r["ruta_regreso_id"] in ids for r in p["rutas"])
    assert all(r["historia"][-1]["fecha"] == p["fecha_origen"] for r in p["rutas"])
    assert "origen del pronóstico de Andrés" in p["aviso"]


def test_m1_los_casos_de_paridad_se_pueden_reproducir(salida):
    o = _leer(salida, "m1/operacion.json")
    assert len(o["casos_paridad"]) >= 10
    assert len({c["entrada"]["ruta_id"] for c in o["casos_paridad"]}) > 1
    for c in o["casos_paridad"]:
        e = c["entrada"]
        assert set(e) == {"ruta_id", "fecha", "demanda", "parametros"}
        assert g.dimensionar_juguete(e["demanda"], e["parametros"]) == c["salida"]
        assert set(e["parametros"]) == set(g.parametros_efectivos(o["parametros"], e["ruta_id"]))


def test_m1_rechaza_parametros_invalidos(salida):
    o = _leer(salida, "m1/operacion.json")
    p = g.parametros_efectivos(o["parametros"], _ruta(_leer(salida, "m1/pronosticos.json")))
    with pytest.raises(ValueError):
        g.dimensionar_juguete(-1, p)
    with pytest.raises(ValueError):
        g.dimensionar_juguete(10, {**p, "globales.conductores_por_vehiculo": 0})


def _entrada(carpeta, caso):
    """La imagen del caso: dentro del meta (`entrada_rgb`) o en un archivo aparte (`entrada_archivo`)."""
    if "entrada_archivo" in caso:
        return _leer(carpeta / "m2", caso["entrada_archivo"])["entrada_rgb"]
    return caso["entrada_rgb"]


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
        rgb = np.array(_entrada(salida, caso), dtype=np.uint8).reshape(alto, ancho, 3)
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


def test_m2_preprocesado_y_caso_desde_archivo_de_imagen(salida):
    """El meta declara el preprocesado y el caso `imagen` sale de redimensionar el archivo (96 x 96) con PIL."""
    from PIL import Image

    meta = _leer(salida, "m2/meta.json")
    assert meta["preprocesado"] == {
        "redimensionado": "estirar", "interpolacion": "bilineal", "canales": "RGB", "escala": "0-1",
        "normalizacion": "media_desviacion",
    }
    assert 1 <= len(meta["casos_paridad"]) <= g.MAX_CASOS_M2
    con_imagen = [c for c in meta["casos_paridad"] if "imagen" in c]
    assert con_imagen and any("entrada_archivo" in c for c in meta["casos_paridad"])
    for c in con_imagen:
        original = Image.open(salida / "m2" / "ejemplos" / c["imagen"])
        assert max(original.size) > g.TAMANO  # no viene ya redimensionada
        esperado = np.asarray(original.convert("RGB").resize((g.TAMANO, g.TAMANO), Image.Resampling.BILINEAR))
        assert np.array_equal(esperado, np.array(_entrada(salida, c), dtype=np.uint8).reshape(esperado.shape))
        assert np.array_equal(g.preprocesar_imagen(original), esperado)


def test_m2_la_generacion_es_determinista(salida, tmp_path):
    g.generar(tmp_path)
    assert _leer(tmp_path, "m2/meta.json") == _leer(salida, "m2/meta.json")
    assert (tmp_path / "m2" / "modelo.onnx").read_bytes() == (salida / "m2" / "modelo.onnx").read_bytes()


def test_m3_dos_torres_y_casos(salida):
    d = _leer(salida, "m3/destinos.json")["destinos"]
    perfil = _leer(salida, "m3/perfil_nuevo.json")
    casos = _leer(salida, "m3/casos_paridad.json")["casos"]
    assert "regla" not in perfil and "casos_paridad" not in perfil  # la regla de afinidad desapareció
    capas = perfil["torre_usuario"]
    assert perfil["codificacion"]["dimension"] == sum(len(p["opciones"]) for p in perfil["preferencias"]) == len(capas[0]["W"][0])
    assert all(len(x["embedding"]) == len(capas[-1]["W"]) for x in d)
    assert len(casos) >= 5 and any(c["vistos"] for c in casos)
    for c in casos:
        x = g.codificar_seleccion(c["seleccion"], perfil["preferencias"])
        u = g.torre_usuario(x, capas)
        assert np.allclose(u, c["vector_usuario"], atol=1e-12)
        r = g.puntuar(u, d, c["k"], set(c["vistos"]))
        assert [f["destino_id"] for f in r] == [f["destino_id"] for f in c["top_k"]]
        assert all(math.isclose(a["puntaje"], b["puntaje"], rel_tol=1e-12) for a, b in zip(r, c["top_k"]))
        assert not set(c["vistos"]) & {f["destino_id"] for f in c["top_k"]}


def test_m3_codificacion_one_hot_en_orden_fijo():
    pref = [{"id": "a", "opciones": [{"id": "x"}, {"id": "y"}]}, {"id": "b", "opciones": [{"id": "z"}]}]
    assert g.codificar_seleccion({"b": ["z"], "a": ["y"]}, pref).tolist() == [0, 1, 1]
    assert g.codificar_seleccion({"a": ["y", "x"]}, pref).tolist() == [1, 1, 0]
    with pytest.raises(ValueError):
        g.codificar_seleccion({"c": ["x"]}, pref)
    with pytest.raises(ValueError):
        g.codificar_seleccion({"a": ["z"]}, pref)


def test_m3_todo_es_ficticio_y_coherente(salida):
    d = _leer(salida, "m3/destinos.json")["destinos"]
    u = _leer(salida, "m3/usuarios.json")
    assert all("(ficticio)" in x["nombre"] for x in d)
    assert all(x["nombre"].startswith("Usuario ficticio") for x in u["usuarios"])
    assert u["modelo"]
    ids = {x["id"] for x in d}
    for x in u["usuarios"]:
        vistos = {h["destino_id"] for h in x["historial"]}
        assert vistos <= ids and not vistos & {f["destino_id"] for f in x["top_k"]}
        assert len(x["top_k"]) >= u["k_max"]


def test_m3_hay_un_usuario_sin_historial_con_top_k_completo(salida):
    u = _leer(salida, "m3/usuarios.json")
    sin = [x for x in u["usuarios"] if not x["historial"]]
    assert sin and all(len(x["top_k"]) >= u["k_max"] for x in sin)
