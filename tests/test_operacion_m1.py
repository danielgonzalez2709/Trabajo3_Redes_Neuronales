"""CA-3: `dimensionar()` y conductores (núcleo §5.4; spec de Camila §3.3). Casos hechos a mano.

Fórmula (spec de Camila §3.3, [PROPUESTO]); r' = ruta de regreso de r (`rutas.yaml`):
    cap_ef(r)  = Σ_c π(r, c) · cap(c)
    desp(r, d) = ⌈ f(r) · D(r, d) / (cap_ef(r) · ρ) ⌉                          (f = 1 por defecto)
    v(r)       = max(1, ⌊ H / T_ciclo(r) ⌋)                                    (ciclo = ida + regreso)
    veh(r, d)  = ⌈ max(desp(r, d), desp(r', d)) / v(r) ⌉
    cond(r, d) = ⌈ veh · H · k / J_ef · 1/(1 − a) · 7/(7 − s) ⌉                 (k = 1, s = 0 por defecto)
Cada prueba lleva sus cuentas en el comentario. Ninguna usa internet.
"""

from __future__ import annotations

import math
import socket
from datetime import date
from pathlib import Path

import pandas as pd
import pytest
import yaml

from src.comun import cli
from src.comun.config import apply_overrides, load_config
from src.m1_demanda import operacion as op

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "m1" / "operacion.yaml"
DETALLE = ROOT / "data" / "processed" / "m1" / "demanda_detalle.parquet"
RUTAS = ROOT / "data" / "processed" / "m1" / "rutas.yaml"
COMANDO = [
    "m1-operacion", "--config", "configs/m1/operacion.yaml",
    "--set", "operacion.ocupacion_objetivo=0.8", "--set", "operacion.cuantil=0.9",
]


# ------------------------------------------------------------------------------------------ funciones escalares

def test_capacidad_efectiva_ponderada_por_composicion():
    # 0,75 · 30 + 0,25 · 18 = 22,5 + 4,5 = 27
    assert op.capacidad_efectiva({"BUS": 0.75, "MICROBUS": 0.25}, {"BUS": 30, "MICROBUS": 18}) == pytest.approx(27.0)
    # una clase con participación 0 no aporta aunque tenga capacidad: 1 · 30 + 0 · 18 = 30
    assert op.capacidad_efectiva({"BUS": 1.0, "MICROBUS": 0.0}, {"BUS": 30, "MICROBUS": 18}) == pytest.approx(30.0)


def test_capacidad_efectiva_exige_capacidad_de_cada_clase_de_la_composicion():
    with pytest.raises(ValueError, match="AUTOMOVIL"):
        op.capacidad_efectiva({"BUS": 0.5, "AUTOMOVIL": 0.5}, {"BUS": 30})


def test_despachos_son_el_techo():
    # cap_ef = 27, ρ = 0,8 → 21,6 pasajeros útiles por despacho; 100 / 21,6 = 4,63 → ⌈4,63⌉ = 5
    assert op.despachos_dia(100, 27.0, 0.8) == 5
    # 43,2 / 21,6 = 2 exacto → 2 (no 3)
    assert op.despachos_dia(43.2, 27.0, 0.8) == 2
    # 21,7 / 21,6 = 1,0046 → 2: basta un pasajero de más para un despacho más
    assert op.despachos_dia(21.7, 27.0, 0.8) == 2


def test_despachos_no_suman_uno_por_ruido_de_coma_flotante():
    # 56,7 / (27 · 0,7) = 3 exacto, pero en coma flotante da 3,0000000000000004; sin tolerancia sería ⌈·⌉ = 4.
    assert 56.7 / (27.0 * 0.7) > 3
    assert op.despachos_dia(56.7, 27.0, 0.7) == 3


def test_despachos_con_demanda_cero_y_fraccion_en_origen():
    assert op.despachos_dia(0, 27.0, 0.8) == 0
    # f = 0,5: 0,5 · 100 / 21,6 = 2,31 → 3
    assert op.despachos_dia(100, 27.0, 0.8, fraccion_origen=0.5) == 3


def test_vueltas_usan_piso():
    # 18 / 9 = 2 → 2;  18 / 3,5 = 5,14 → 5;  18 / 6 = 3 exacto → 3;  18 / 10 = 1,8 → 1 (no 2)
    assert op.vueltas_dia(18, 9) == (2, False)
    assert op.vueltas_dia(18, 3.5) == (5, False)
    assert op.vueltas_dia(18, 6) == (3, False)
    assert op.vueltas_dia(18, 10) == (1, False)


def test_vueltas_piso_tolera_ruido_de_coma_flotante():
    # 2,4 / 0,8 = 3 exacto, pero en coma flotante da 2,9999999999999996; sin tolerancia sería ⌊·⌋ = 2.
    assert 2.4 / 0.8 < 3
    assert op.vueltas_dia(2.4, 0.8) == (3, False)


def test_ciclo_mas_largo_que_las_horas_se_marca():
    # 18 / 22 = 0,82 → ⌊·⌋ = 0 → el Spec fija el mínimo en 1 y la función lo MARCA (excede = True).
    assert op.vueltas_dia(18, 22) == (1, True)
    # con la bandera de vueltas fraccionarias (desactivada por defecto) quedan 18 / 22 = 0,818…
    v, excede = op.vueltas_dia(18, 22, fraccionarias=True)
    assert excede and v == pytest.approx(18 / 22)
    # la bandera no cambia nada si el ciclo cabe en las horas: 18 / 9 → 2
    assert op.vueltas_dia(18, 9, fraccionarias=True) == (2, False)


def test_vehiculos_usan_el_maximo_de_los_dos_sentidos():
    # ida 5, regreso 7, 2 vueltas: ⌈max(5, 7) / 2⌉ = ⌈3,5⌉ = 4. Con solo la ida serían ⌈5/2⌉ = 3 (fórmula sin regreso).
    assert op.vehiculos_dia(5, 7, 2) == 4
    assert op.vehiculos_dia(7, 5, 2) == 4  # simétrica
    # 6 y 6 con 3 vueltas: ⌈6/3⌉ = 2 exacto
    assert op.vehiculos_dia(6, 6, 3) == 2
    # vueltas fraccionarias: ⌈7 / (18/22)⌉ = ⌈7 · 22 / 18⌉ = ⌈8,56⌉ = 9
    assert op.vehiculos_dia(7, 3, 18 / 22) == 9
    assert op.vehiculos_dia(0, 0, 2) == 0


def test_conductores_con_jornada_y_ausentismo():
    # 4 vehículos · 18 h / 7 h = 10,29 conductores-turno; / (1 − 0,09) = 11,30 → 12
    assert op.conductores_dia(4, 18, 7, 0.09) == 12
    # sin ausentismo: ⌈10,29⌉ = 11 (el ausentismo agrega uno)
    assert op.conductores_dia(4, 18, 7, 0.0) == 11
    assert op.conductores_dia(0, 18, 7, 0.09) == 0


def test_conductores_segundo_conductor_y_descanso_semanal():
    # tripulación 2 (Res. 315/2013 art. 6 si se activa): 4 · 18 · 2 / 7 / 0,91 = 22,61 → 23
    assert op.conductores_dia(4, 18, 7, 0.09, tripulacion=2) == 23
    # 1 día de descanso a la semana: · 7/6 → 4 · 18 / 7 · 7/6 / 0,91 = 12 / 0,91 = 13,19 → 14
    assert op.conductores_dia(4, 18, 7, 0.09, dias_descanso_semana=1) == 14


def test_tripulacion_solo_con_recorrido_estrictamente_mayor_al_umbral():
    # Res. 315/2013 art. 6 (según informe CA-2 §1.3): «duración superior a ocho (8) horas de recorrido».
    assert op.tripulacion(10, activo=False, umbral_h=8) == 1   # desactivado por defecto
    assert op.tripulacion(10, activo=True, umbral_h=8) == 2
    assert op.tripulacion(8, activo=True, umbral_h=8) == 1     # 8 no es «superior a» 8
    assert op.tripulacion(4, activo=True, umbral_h=8) == 1


# -------------------------------------------------------------------------------------------- dimensionar()

def _params(**globales) -> dict:
    """Parámetros de prueba (valores ya resueltos) para el par A-B / B-A."""
    g = {
        "ocupacion_objetivo": 0.8, "cuantil": 0.9, "horas_operacion_h": 18.0, "jornada_efectiva_h": 7.0,
        "jornada_max_diaria_h": 8.0, "ausentismo": 0.09, "segundo_conductor_activo": 0, "umbral_segundo_conductor_h": 8.0,
        "dias_descanso_semana": 0, "vueltas_fraccionarias": 0,
        "costo_pasajero_sin_atender": 1.0, "costo_vehiculo_dia_sobrante": 1.0,
    }
    g.update(globales)
    ruta = {"tiempo_ciclo_h": 9.0, "tiempo_recorrido_h": 4.0, "fraccion_demanda_en_origen": 1.0}
    return {
        "globales": g,
        "por_ruta": {"A-B": dict(ruta), "B-A": dict(ruta)},
        "por_clase": {"BUS": {"capacidad_pasajeros": 30.0}, "MICROBUS": {"capacidad_pasajeros": 18.0}},
        "composicion_clases": {"A-B": {"BUS": 1.0, "MICROBUS": 0.0}, "B-A": {"BUS": 0.5, "MICROBUS": 0.5}},
        "ruta_regreso": {"A-B": "B-A", "B-A": "A-B"},
    }


def _demanda(filas: list[tuple[str, str, float]]) -> pd.DataFrame:
    return pd.DataFrame(filas, columns=["ruta_id", "fecha", "demanda"]).assign(fecha=lambda d: pd.to_datetime(d.fecha))


def test_dimensionar_caso_a_mano_ida_y_regreso():
    # A-B: cap_ef = 1·30 = 30; útiles 24; 100/24 = 4,17 → 5 despachos
    # B-A: cap_ef = 0,5·30 + 0,5·18 = 24; útiles 19,2; 150/19,2 = 7,81 → 8 despachos
    # vueltas = ⌊18/9⌋ = 2; vehículos del corredor = ⌈max(5, 8)/2⌉ = 4 en las dos filas
    # conductores = ⌈4 · 18 / 7 / 0,91⌉ = ⌈11,30⌉ = 12
    out = op.dimensionar(_demanda([("A-B", "2022-12-01", 100), ("B-A", "2022-12-01", 150)]), _params())
    out = out.set_index("ruta_id")
    assert out.loc["A-B", "capacidad_efectiva"] == pytest.approx(30.0)
    assert out.loc["B-A", "capacidad_efectiva"] == pytest.approx(24.0)
    assert out.loc["A-B", "despachos"] == 5 and out.loc["B-A", "despachos"] == 8
    assert out.loc["A-B", "despachos_regreso"] == 8 and out.loc["B-A", "despachos_regreso"] == 5
    assert list(out["vueltas"]) == [2, 2]
    assert list(out["vehiculos"]) == [4, 4]
    assert list(out["conductores"]) == [12, 12]
    # la flota es del corredor (no se suma dos veces): misma etiqueta en las dos filas
    assert out.loc["A-B", "corredor"] == out.loc["B-A", "corredor"]


def test_dimensionar_conserva_columnas_y_orden_de_entrada():
    entrada = _demanda([("B-A", "2022-12-02", 0), ("A-B", "2022-12-02", 0), ("A-B", "2022-12-01", 10),
                        ("B-A", "2022-12-01", 10)])
    out = op.dimensionar(entrada, _params())
    assert list(out.columns[:3]) == ["ruta_id", "fecha", "demanda"]
    assert {"despachos", "vehiculos", "conductores"} <= set(out.columns)
    pd.testing.assert_frame_equal(out[["ruta_id", "fecha", "demanda"]], entrada)
    for col in ("despachos", "vehiculos", "conductores"):
        assert pd.api.types.is_integer_dtype(out[col])


def test_dimensionar_demanda_cero_da_cero():
    out = op.dimensionar(_demanda([("A-B", "2022-12-01", 0), ("B-A", "2022-12-01", 0)]), _params())
    assert (out[["despachos", "vehiculos", "conductores"]] == 0).all().all()


def test_dimensionar_un_sentido_vacio_igual_necesita_flota():
    # A-B con 0 pasajeros y B-A con 150: los vehículos que vuelven de B deben haber ido; veh = ⌈max(0, 8)/2⌉ = 4.
    out = op.dimensionar(_demanda([("A-B", "2022-12-01", 0), ("B-A", "2022-12-01", 150)]), _params())
    assert list(out["vehiculos"]) == [4, 4]


def test_dimensionar_cuantil_mayor_nunca_pide_menos():
    # Invariante: la salida es monótona no decreciente en la demanda (q0.9 ≥ q0.5 ⇒ flota(q0.9) ≥ flota(q0.5)).
    base = op.dimensionar(_demanda([("A-B", "2022-12-01", 100), ("B-A", "2022-12-01", 150)]), _params())
    alta = op.dimensionar(_demanda([("A-B", "2022-12-01", 110), ("B-A", "2022-12-01", 165)]), _params())
    for col in ("despachos", "vehiculos", "conductores"):
        assert (alta[col] >= base[col]).all()


def test_dimensionar_segundo_conductor_se_activa_por_ruta():
    # recorrido de 10 h > 8 h y regla activa → tripulación 2: ⌈4 · 18 · 2 / 7 / 0,91⌉ = 23
    p = _params(segundo_conductor_activo=1)
    for r in ("A-B", "B-A"):
        p["por_ruta"][r].update(tiempo_recorrido_h=10.0, tiempo_ciclo_h=22.0)
    p["globales"]["horas_operacion_h"] = 18.0
    out = op.dimensionar(_demanda([("A-B", "2022-12-01", 100), ("B-A", "2022-12-01", 150)]), p)
    # ciclo 22 > 18 h → vueltas = 1 (mínimo del Spec) y queda marcado; veh = ⌈8/1⌉ = 8
    assert list(out["ciclo_excede_horas"]) == [True, True]
    assert list(out["vehiculos"]) == [8, 8]
    assert list(out["tripulacion"]) == [2, 2]
    # ⌈8 · 18 · 2 / 7 / 0,91⌉ = ⌈45,21⌉ = 46
    assert list(out["conductores"]) == [46, 46]


def test_dimensionar_exige_la_demanda_del_regreso_el_mismo_dia():
    with pytest.raises(ValueError, match="regreso"):
        op.dimensionar(_demanda([("A-B", "2022-12-01", 100)]), _params())
    with pytest.raises(ValueError, match="regreso"):
        op.dimensionar(_demanda([("A-B", "2022-12-01", 100), ("B-A", "2022-12-02", 100)]), _params())


@pytest.mark.parametrize(
    ("grupo", "clave", "valor", "mensaje"),
    [
        ("globales", "ocupacion_objetivo", 0.0, "ocupacion_objetivo"),
        ("globales", "ocupacion_objetivo", 1.2, "ocupacion_objetivo"),
        ("globales", "cuantil", 1.0, "cuantil"),
        ("globales", "ausentismo", 1.0, "ausentismo"),
        ("globales", "ausentismo", -0.1, "ausentismo"),
        ("globales", "horas_operacion_h", 0.0, "horas_operacion_h"),
        ("globales", "horas_operacion_h", 25.0, "horas_operacion_h"),
        ("globales", "jornada_efectiva_h", 9.0, "jornada_efectiva_h"),  # > jornada_max_diaria_h = 8
        ("globales", "segundo_conductor_activo", 2, "segundo_conductor_activo"),
        ("globales", "dias_descanso_semana", 7, "dias_descanso_semana"),
        ("globales", "vueltas_fraccionarias", 0.5, "vueltas_fraccionarias"),
    ],
)
def test_parametros_fuera_de_rango_dan_error_claro(grupo, clave, valor, mensaje):
    p = _params()
    p[grupo][clave] = valor
    with pytest.raises(ValueError, match=mensaje):
        op.dimensionar(_demanda([("A-B", "2022-12-01", 100), ("B-A", "2022-12-01", 150)]), p)


def test_errores_de_ruta_clase_y_composicion():
    d = _demanda([("A-B", "2022-12-01", 100), ("B-A", "2022-12-01", 150)])
    p = _params()
    p["composicion_clases"]["A-B"] = {"BUS": 0.7, "MICROBUS": 0.2}  # suma 0,9
    with pytest.raises(ValueError, match="suma"):
        op.dimensionar(d, p)
    p = _params()
    p["por_clase"]["BUS"]["capacidad_pasajeros"] = 0
    with pytest.raises(ValueError, match="capacidad_pasajeros"):
        op.dimensionar(d, p)
    p = _params()
    p["por_ruta"]["B-A"]["tiempo_ciclo_h"] = 10.0  # el ciclo del corredor debe ser el mismo en los dos sentidos
    with pytest.raises(ValueError, match="tiempo_ciclo_h"):
        op.dimensionar(d, p)
    p = _params()
    p["por_ruta"]["A-B"]["tiempo_recorrido_h"] = 5.0  # ciclo 9 < 2 · 5: el ciclo no alcanza para ida y regreso
    p["por_ruta"]["B-A"]["tiempo_recorrido_h"] = 5.0
    with pytest.raises(ValueError, match="tiempo_ciclo_h"):
        op.dimensionar(d, p)
    p = _params()
    p["por_ruta"]["A-B"]["fraccion_demanda_en_origen"] = 0.0
    with pytest.raises(ValueError, match="fraccion_demanda_en_origen"):
        op.dimensionar(d, p)
    with pytest.raises(ValueError, match="C-D"):
        op.dimensionar(_demanda([("C-D", "2022-12-01", 1)]), _params())
    with pytest.raises(ValueError, match="demanda"):
        op.dimensionar(_demanda([("A-B", "2022-12-01", -1), ("B-A", "2022-12-01", 1)]), _params())
    with pytest.raises(ValueError, match="demanda"):
        op.dimensionar(_demanda([("A-B", "2022-12-01", float("nan")), ("B-A", "2022-12-01", 1)]), _params())
    with pytest.raises(ValueError, match="duplicad"):
        op.dimensionar(_demanda([("A-B", "2022-12-01", 1), ("A-B", "2022-12-01", 2), ("B-A", "2022-12-01", 1)]),
                       _params())
    with pytest.raises(ValueError, match="columna"):
        op.dimensionar(pd.DataFrame({"ruta_id": ["A-B"], "fecha": [date(2022, 12, 1)]}), _params())


# ------------------------------------------------------------------------- composición (solo train, sin fuga)

def _detalle() -> pd.DataFrame:
    # ruta R1 (ORIGEN salvo donde se indica):
    #   2021-05-15 BUS 100 despachos          → antes del inicio de entrenamiento: fuera
    #   2021-06-01 BUS 6, MICROBUS 2          → dentro (borde inferior incluido)
    #   2022-12-31 BUS 3, MICROBUS 1          → dentro (borde superior incluido)
    #   2023-01-01 MICROBUS 1000              → después del fin de entrenamiento: fuera (sería fuga)
    #   2022-06-01 TRANSITO MICROBUS 500      → tránsito: fuera (cuenta el mismo vehículo en otra terminal)
    # composición = BUS 9/12 = 0,75; MICROBUS 3/12 = 0,25; BUSETA (en config, no en datos) = 0
    filas = [
        ("R1", "2021-05-15", "ORIGEN", "BUS", 1000, 100),
        ("R1", "2021-06-01", "ORIGEN", "BUS", 60, 6),
        ("R1", "2021-06-01", "ORIGEN", "MICROBUS", 20, 2),
        ("R1", "2022-12-31", "ORIGEN", "BUS", 90, 3),
        ("R1", "2022-12-31", "ORIGEN", "MICROBUS", 10, 1),
        ("R1", "2023-01-01", "ORIGEN", "MICROBUS", 99999, 1000),
        ("R1", "2022-06-01", "TRANSITO", "MICROBUS", 5000, 500),
    ]
    d = pd.DataFrame(filas, columns=["ruta_id", "fecha", "tipo_despacho", "clase_vehiculo", "pasajeros", "despachos"])
    d["fecha"] = pd.to_datetime(d["fecha"]).dt.date  # mismo tipo que demanda_detalle.parquet (date)
    return d


CLASES = ["BUS", "BUSETA", "MICROBUS"]


def test_composicion_solo_origen_y_solo_train():
    comp = op.estimar_composicion(_detalle(), "2021-06-01", "2022-12-31", CLASES)
    assert comp == {"R1": pytest.approx({"BUS": 0.75, "BUSETA": 0.0, "MICROBUS": 0.25})}


def test_composicion_no_cambia_con_datos_posteriores_al_fin_de_entrenamiento():
    # Invariante contra fuga: alterar TODO lo posterior al corte no puede mover la composición.
    d = _detalle()
    base = op.estimar_composicion(d, "2021-06-01", "2022-12-31", CLASES)
    otro = d.copy()
    despues = pd.to_datetime(otro["fecha"]) > pd.Timestamp("2022-12-31")
    otro.loc[despues, "despachos"] = 7_777_777
    otro.loc[despues, "clase_vehiculo"] = "BUSETA"
    extra = pd.DataFrame([("R1", date(2023, 6, 1), "ORIGEN", "BUS", 1, 123456)], columns=d.columns)
    assert op.estimar_composicion(pd.concat([otro, extra]), "2021-06-01", "2022-12-31", CLASES) == base


def test_composicion_rechaza_clase_desconocida_y_ruta_sin_despachos():
    with pytest.raises(ValueError, match="MICROBUS"):
        op.estimar_composicion(_detalle(), "2021-06-01", "2022-12-31", ["BUS"])
    with pytest.raises(ValueError, match="R1"):
        op.estimar_composicion(_detalle(), "2021-06-02", "2021-06-03", CLASES)


def test_capacidad_observada_solo_origen_y_train():
    # ORIGEN en [2021-06-01, 2022-12-31], pasajeros por despacho: BUS 60/6 = 10 y 90/3 = 30; MICROBUS 20/2 = 10 y 10/1 = 10
    # percentil 50 (interpolación lineal): BUS (10 + 30)/2 = 20; MICROBUS 10. El de 2023 (99999/1000 ≈ 100) no entra.
    obs = op.capacidad_observada(_detalle(), "2021-06-01", "2022-12-31", 0.5).set_index("clase_vehiculo")
    assert obs.loc["BUS", "pasajeros_por_despacho"] == pytest.approx(20.0)
    assert obs.loc["MICROBUS", "pasajeros_por_despacho"] == pytest.approx(10.0)
    assert obs.loc["BUS", "n_dias"] == 2


def test_fraccion_de_pasajeros_en_origen_solo_train():
    # ORIGEN en la ventana: 60 + 20 + 90 + 10 = 180; TRANSITO en la ventana: 5000 → 180 / 5180
    frac = op.fraccion_pasajeros_origen(_detalle(), "2021-06-01", "2022-12-31")
    assert frac == {"R1": pytest.approx(180 / 5180)}


# ------------------------------------------------------------------------------------- configs/m1/operacion.yaml

@pytest.fixture(scope="module")
def cfg_operacion() -> dict:
    return load_config(CONFIG)


def _hojas(valores: dict) -> list[tuple[str, ...]]:
    """Rutas (grupo, …, clave) de los parámetros de `operacion`."""
    out = []
    for k, v in valores.items():
        if k == "por_ruta" or k == "por_clase":
            out += [(k, sub, kk) for sub, d in v.items() for kk in d]
        else:
            out.append(("globales", k))
    return out


def test_cada_parametro_tiene_unidad_y_fuente_o_supuesto(cfg_operacion):
    meta = cfg_operacion["meta"]
    hojas = _hojas(cfg_operacion["operacion"])
    assert len(hojas) > 10
    for ruta in hojas:
        m = meta
        for parte in ruta:
            assert parte in m, f"falta meta de {'.'.join(ruta)}"
            m = m[parte]
        assert isinstance(m.get("unidad"), str), ruta
        assert ("fuente" in m) != (m.get("supuesto") is True), f"{ruta}: fuente XOR supuesto: true"
        # Spec de Camila §2: primero TODO como supuesto, con nota.
        assert m.get("supuesto") is True and isinstance(m.get("nota"), str) and m["nota"].strip(), ruta
    # y ninguna meta sobra
    n_meta = len(meta["globales"]) + sum(len(v) for v in meta["por_ruta"].values()) + sum(
        len(v) for v in meta["por_clase"].values())
    assert n_meta == len(hojas)


def test_valores_de_uso_son_escalares_y_aceptan_el_set_del_nucleo(cfg_operacion):
    o = cfg_operacion["operacion"]
    for k, v in o.items():
        if k not in ("por_ruta", "por_clase"):
            assert isinstance(v, (int, float)) and not isinstance(v, bool), k
    cfg = apply_overrides(cfg_operacion, ["operacion.ocupacion_objetivo=0.8", "operacion.cuantil=0.9"])
    assert cfg["operacion"]["ocupacion_objetivo"] == 0.8 and cfg["operacion"]["cuantil"] == 0.9


def test_rutas_y_clases_de_la_config_coinciden_con_los_datos(cfg_operacion):
    rutas = yaml.safe_load(RUTAS.read_text(encoding="utf-8"))["rutas"]
    assert set(cfg_operacion["operacion"]["por_ruta"]) == {r["ruta_id"] for r in rutas}
    for r in rutas:  # el ciclo del corredor es el mismo en los dos sentidos
        ida = cfg_operacion["operacion"]["por_ruta"][r["ruta_id"]]
        vuelta = cfg_operacion["operacion"]["por_ruta"][r["ruta_regreso_id"]]
        assert ida["tiempo_ciclo_h"] == vuelta["tiempo_ciclo_h"]
    clases = set(pd.read_parquet(DETALLE, columns=["clase_vehiculo"])["clase_vehiculo"])
    assert set(cfg_operacion["operacion"]["por_clase"]) == clases


# Rangos del Decreto 171 de 2001, arts. 50–51, según el informe CA-2 §2 (sin verificar aún por el cazador):
# Grupo A «4 a 9 pasajeros» (automóvil, campero, camioneta); B «10 a 19» (microbús); C «más de 19» (buseta, bus).
RANGO_DECRETO_171 = {"AUTOMOVIL": (4, 9), "CAMPERO": (4, 9), "CAMIONETA": (4, 9), "MICROBUS": (10, 19),
                     "BUSETA": (20, math.inf), "BUS": (20, math.inf)}


def test_capacidades_dentro_del_rango_y_regla_del_percentil(cfg_operacion):
    # Regla de los supuestos: cap(c) = min(máx. del grupo, max(mín. del grupo, ⌈p_alto de pasajeros/despacho ORIGEN⌉)),
    # con p_alto medido SOLO en la ventana de entrenamiento.
    d = cfg_operacion["datos"]
    obs = op.capacidad_observada(pd.read_parquet(DETALLE), d["inicio_entrenamiento"], d["fin_entrenamiento"],
                                 cfg_operacion["capacidad_observada"]["percentil"]).set_index("clase_vehiculo")
    for clase, (lo, hi) in RANGO_DECRETO_171.items():
        cap = cfg_operacion["operacion"]["por_clase"][clase]["capacidad_pasajeros"]
        assert lo <= cap <= hi, clase
        esperado = min(hi, max(lo, math.ceil(obs.loc[clase, "pasajeros_por_despacho"])))
        assert cap == esperado, (clase, obs.loc[clase, "pasajeros_por_despacho"])


def test_fin_de_entrenamiento_propuesto_no_pasa_de_2023_01_01(cfg_operacion):
    d = cfg_operacion["datos"]
    assert date.fromisoformat(d["inicio_entrenamiento"]) == date(2021, 6, 1)  # núcleo §5.1
    assert date.fromisoformat(d["fin_entrenamiento"]) <= date(2023, 1, 1)


def test_parametros_al_formato_del_contrato_de_la_app(cfg_operacion):
    # Núcleo §5.4: {valor, unidad, fuente | supuesto: true, nota?} en globales, por_ruta, por_clase y composicion_clases.
    d = cfg_operacion["datos"]
    comp = op.estimar_composicion(pd.read_parquet(DETALLE), d["inicio_entrenamiento"], d["fin_entrenamiento"],
                                  list(cfg_operacion["operacion"]["por_clase"]))
    c = op.parametros_contrato(cfg_operacion, comp)
    assert set(c) == {"globales", "por_ruta", "por_clase", "composicion_clases"}
    assert {"ocupacion_objetivo", "cuantil"} <= set(c["globales"])
    pars = list(c["globales"].values())
    pars += [p for g in ("por_ruta", "por_clase", "composicion_clases") for sub in c[g].values() for p in sub.values()]
    for p in pars:
        assert set(p) <= {"valor", "unidad", "fuente", "supuesto", "nota"}
        assert isinstance(p["valor"], (int, float)) and not isinstance(p["valor"], bool)
        assert isinstance(p["unidad"], str)
        assert ("fuente" in p) != (p.get("supuesto") is True)
    for ruta, cl in c["composicion_clases"].items():
        assert set(cl) == set(c["por_clase"])
        assert sum(p["valor"] for p in cl.values()) == pytest.approx(1.0, abs=1e-9)
        for p in cl.values():  # la composición sale de los datos de train: fuente con la ventana
            assert d["fin_entrenamiento"] in p["fuente"]
    for k in (*c["por_ruta"], *c["por_clase"], *c["globales"]):
        assert "." not in k  # las referencias `grupo.clase.clave` usan el punto de separador


# ---------------------------------------------------------------------------------------------- comando §4.1

def test_comando_del_nucleo_se_acepta_tal_cual(monkeypatch, recibido, config_impresa, capsys):
    monkeypatch.chdir(ROOT)
    assert cli.main(COMANDO) == 0
    impreso = config_impresa(capsys.readouterr().out)
    assert impreso["operacion"]["ocupacion_objetivo"] == 0.8 and impreso["operacion"]["cuantil"] == 0.9
    assert recibido["m1-operacion"] == impreso


@pytest.fixture
def sin_red(monkeypatch):
    def _bloqueado(*a, **k):
        raise RuntimeError("intento de usar la red")

    for nombre in ("connect", "connect_ex"):
        monkeypatch.setattr(socket.socket, nombre, _bloqueado)
    monkeypatch.setattr(socket, "create_connection", _bloqueado)
    monkeypatch.setattr(socket, "getaddrinfo", _bloqueado)


def test_main_corre_sin_red_y_escribe_el_ejemplo_marcado(tmp_path, monkeypatch, sin_red, capsys):
    monkeypatch.chdir(ROOT)
    cfg = apply_overrides(load_config(CONFIG), [
        "operacion.ocupacion_objetivo=0.8", "operacion.cuantil=0.9", f"salida.carpeta={tmp_path.as_posix()}",
    ])
    assert op.main(cfg) == 0
    salida = capsys.readouterr().out
    assert "EJEMPLO" in salida
    tabla = pd.read_csv(tmp_path / "dimensionamiento_ejemplo.csv")
    assert (tabla["tipo_demanda"] == "EJEMPLO: observada en train, no es pronóstico").all()
    assert {"despachos", "vehiculos", "conductores"} <= set(tabla.columns)
    fechas = pd.to_datetime(tabla["fecha"])
    assert fechas.max() <= pd.Timestamp(cfg["datos"]["fin_entrenamiento"])  # el ejemplo no sale del train
    assert (tabla.groupby(["corredor", "fecha"])["vehiculos"].nunique() == 1).all()  # flota única por corredor
    comp = pd.read_csv(tmp_path / "composicion_clases.csv")
    assert comp.groupby("ruta_id")["participacion"].sum().round(9).eq(1).all()
    assert (tmp_path / "resumen.json").is_file()
