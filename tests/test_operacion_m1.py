"""CA-3 (rondas 2–3, prompts CA-3b y CA-3c): `dimensionar()` y conductores (núcleo §5.4; spec de Camila §3.3). Casos hechos a mano.

Fórmula [DECIDIDO, Camila, 26-nov]; r' = ruta de regreso de r (`rutas.yaml`), {r, r'} = corredor:
    (1)  cap_ef(r)  = Σ_c π(r, c) · cap(c)
    (2)  desp(r, d) = ⌈ f(r) · D(r, d) / (cap_ef(r) · ρ) ⌉
    (3)  v(r)       = H / T_ciclo(r)                                   (fracción, sin piso ni mínimo)
    (4)  veh(r, d)  = ⌈ max(desp(r, d), desp(r', d)) / v(r) ⌉
    (5a) P          = 2 · max(desp(r, d), desp(r', d))                   piernas del corredor (con las vacías)
         h_r        = t_r / k_r,  k_r = 2 si t_r > 8 h (Res. 315/2013 art. 6)   horas al volante por conductor y pierna
         L_r        = max(1, ⌊ J_ef / h_r ⌋)                             piernas (indivisibles) por conductor y día
         C_serv     = ⌈ k_r · P / L_r ⌉
    (5b) C_nom      = ⌈ C_serv / (1 − a) · 7 / (7 − s) ⌉,                s = 1 (día de descanso, art. 161 CST)
Calibración con train: f(r) (últimos meses de train), cap(c) (máximo observado recortado al rango del Decreto 1079/2015)
y ρ* = Σ f·D/cap_ef ÷ Σ despachos ORIGEN, en la misma ventana que f. Cada prueba lleva sus cuentas en el comentario. Ninguna usa internet.
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
DIARIA = ROOT / "data" / "processed" / "m1" / "demanda_diaria.parquet"
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
    # f = 1, cap_ef = 27, ρ = 0,8 → 21,6 pasajeros útiles por despacho; 100 / 21,6 = 4,63 → ⌈4,63⌉ = 5
    assert op.despachos_dia(100, 27.0, 0.8, 1.0) == 5
    # 43,2 / 21,6 = 2 exacto → 2 (no 3)
    assert op.despachos_dia(43.2, 27.0, 0.8, 1.0) == 2
    # 21,7 / 21,6 = 1,0046 → 2: basta un pasajero de más para un despacho más
    assert op.despachos_dia(21.7, 27.0, 0.8, 1.0) == 2


def test_despachos_no_suman_uno_por_ruido_de_coma_flotante():
    # 56,7 / (27 · 0,7) = 3 exacto, pero en coma flotante da 3,0000000000000004; sin tolerancia sería ⌈·⌉ = 4.
    assert 56.7 / (27.0 * 0.7) > 3
    assert op.despachos_dia(56.7, 27.0, 0.7, 1.0) == 3


def test_despachos_con_demanda_cero_y_fraccion_en_origen():
    assert op.despachos_dia(0, 27.0, 0.8, 1.0) == 0
    # f = 0,5: 0,5 · 100 / 21,6 = 2,31 → 3
    assert op.despachos_dia(100, 27.0, 0.8, 0.5) == 3


def test_vueltas_son_fraccion_sin_piso_ni_minimo():
    # (3) v = H / T: 18 / 9 = 2;  18 / 10 = 1,8 (antes ⌊·⌋ = 1);  18 / 22 = 0,818… (antes max(1, 0) = 1)
    assert op.vueltas_dia(18, 9) == pytest.approx(2.0)
    assert op.vueltas_dia(18, 10) == pytest.approx(1.8)
    assert op.vueltas_dia(18, 22) == pytest.approx(18 / 22)


def test_vehiculos_usan_el_maximo_de_los_dos_sentidos():
    # ida 5, regreso 7, 2 vueltas: ⌈max(5, 7) / 2⌉ = ⌈3,5⌉ = 4. Con solo la ida serían ⌈5/2⌉ = 3 (fórmula sin regreso).
    assert op.vehiculos_dia(5, 7, 2) == 4
    assert op.vehiculos_dia(7, 5, 2) == 4  # simétrica
    # 6 y 6 con 3 vueltas: ⌈6/3⌉ = 2 exacto
    assert op.vehiculos_dia(6, 6, 3) == 2
    # vueltas fraccionarias: ⌈7 / (18/22)⌉ = ⌈7 · 22 / 18⌉ = ⌈8,56⌉ = 9;  18/10 = 1,8 → ⌈7 / 1,8⌉ = ⌈3,89⌉ = 4
    assert op.vehiculos_dia(7, 3, 18 / 22) == 9
    assert op.vehiculos_dia(7, 3, 1.8) == 4
    assert op.vehiculos_dia(0, 0, 2) == 0


def test_vehiculos_toleran_ruido_de_coma_flotante():
    # 0,7 / 0,1 = 7 exacto, pero en coma flotante da 6,999999999999999 → 7 / v = 1,0000000000000002; sin tolerancia ⌈·⌉ = 2.
    v = op.vueltas_dia(0.7, 0.1)
    assert v < 7 and 7 / v > 1
    assert op.vehiculos_dia(7, 0, v) == 1


def test_tripulacion_solo_con_recorrido_estrictamente_mayor_al_umbral():
    # Res. 315/2013 art. 6: «duración superior a ocho (8) horas de recorrido» → k = 2 solo si t > 8.
    assert op.tripulacion(10, umbral_h=8) == 2
    assert op.tripulacion(8.5, umbral_h=8) == 2
    assert op.tripulacion(8, umbral_h=8) == 1     # 8 no es «superior a» 8
    assert op.tripulacion(4, umbral_h=8) == 1


def test_piernas_cuentan_las_vacias_de_reposicion():
    # P = 2 · max(n, n'): 2 · max(5, 8) = 16 (no 5 + 8 = 13); un sentido vacío: 2 · max(0, 8) = 16; 0 y 0 → 0
    assert op.piernas_dia(5, 8) == 16
    assert op.piernas_dia(0, 8) == 16
    assert op.piernas_dia(0, 0) == 0


def test_piernas_por_conductor_indivisibles():
    # L = max(1, ⌊ J_ef / (t / k) ⌋) con J_ef = 7:
    assert op.piernas_por_conductor(10, 2, 7) == 1    # Bogotá–Cali: h = 10/2 = 5;  ⌊7/5⌋ = ⌊1,4⌋ = 1
    assert op.piernas_por_conductor(4, 1, 7) == 1     # Bogotá–Sogamoso: ⌊7/4⌋ = ⌊1,75⌋ = 1 (no 1,75 «continuas»)
    assert op.piernas_por_conductor(1.5, 1, 7) == 4   # Pasto–Ipiales: ⌊7/1,5⌋ = ⌊4,67⌋ = 4
    assert op.piernas_por_conductor(2, 1, 7) == 3     # ⌊7/2⌋ = ⌊3,5⌋ = 3
    assert op.piernas_por_conductor(7.5, 1, 7) == 1   # h = 7,5 > J_ef = 7 (pero ≤ 8 h): ⌊0,93⌋ = 0 → mínimo 1


def test_piernas_por_conductor_toleran_ruido_de_coma_flotante():
    # 0,3 / 0,1 = 3 exacto, pero en coma flotante da 2,9999999999999996; sin tolerancia ⌊·⌋ = 2.
    assert 0.3 / 0.1 < 3
    assert op.piernas_por_conductor(0.1, 1, 0.3) == 3


def test_conductores_en_servicio_por_piernas():
    # (5a) C_serv = ⌈ k · 2 · max(n, n') / L ⌉ con J_ef = 7 y despachos 5 y 8 (P = 16):
    assert op.conductores_servicio(5, 8, 10, 2, 7) == 32   # Bogotá–Cali: k = 2, L = 1 → ⌈2 · 16 / 1⌉ = 32
    assert op.conductores_servicio(5, 8, 4, 1, 7) == 16    # Bogotá–Sogamoso: L = 1 → ⌈16 / 1⌉ = 16
    assert op.conductores_servicio(5, 8, 1.5, 1, 7) == 4   # Pasto–Ipiales: L = 4 → ⌈16 / 4⌉ = 4
    assert op.conductores_servicio(5, 7, 1.5, 1, 7) == 4   # P = 14, L = 4 → ⌈3,5⌉ = 4
    assert op.conductores_servicio(0, 8, 4, 1, 7) == 16    # un sentido vacío: las 8 piernas vacías también se manejan
    assert op.conductores_servicio(0, 0, 4, 1, 7) == 0


def test_contraejemplo_del_verificador_un_despacho_por_sentido():
    # 1 despacho por sentido, T = 4 h (t = 2 h), H = 18: la ec. (5) original daba ⌈1 · 18 / 7 / 0,91⌉ = 3 conductores.
    # (5a): P = 2 · max(1, 1) = 2; L = ⌊7/2⌋ = 3 → ⌈2 / 3⌉ = 1 conductor en servicio (4 h de conducción ≤ 7 h).
    assert op.conductores_servicio(1, 1, 2, 1, 7) == 1


def test_conductores_en_servicio_toleran_ruido_de_coma_flotante():
    # P = 2 · 3 = 6; L = ⌊0,3 / 0,1⌋ = 3 con tolerancia (2 sin ella) → ⌈6 / 3⌉ = 2 (sin tolerancia ⌈6/2⌉ = 3).
    assert op.conductores_servicio(3, 0, 0.1, 1, 0.3) == 2


def test_conductores_de_nomina_con_ausentismo_y_descanso_semanal():
    # (5b) 8 / (1 − 0,09) · 7 / (7 − 1) = 8 / 0,91 · 7/6 = 56 / 5,46 = 10,26 → 11
    assert op.conductores_nomina(8, 0.09, 1) == 11
    # sin ausentismo: 8 · 7/6 = 9,33 → 10
    assert op.conductores_nomina(8, 0.0, 1) == 10
    # 38 / 0,91 · 7/6 = 266 / 5,46 = 48,72 → 49
    assert op.conductores_nomina(38, 0.09, 1) == 49
    assert op.conductores_nomina(0, 0.09, 1) == 0


# -------------------------------------------------------------------------------------------- dimensionar()

def _params(**globales) -> dict:
    """Parámetros de prueba (valores ya resueltos) para el par A-B / B-A."""
    g = {
        "ocupacion_objetivo": 0.8, "cuantil": 0.9, "horas_operacion_h": 18.0, "jornada_efectiva_h": 7.0,
        "jornada_max_diaria_h": 8.0, "jornada_max_semanal_h": 42.0, "ausentismo": 0.09,
        "umbral_segundo_conductor_h": 8.0, "dias_descanso_semana": 1,
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


def _ida_y_regreso(ida=100, regreso=150) -> pd.DataFrame:
    return _demanda([("A-B", "2022-12-01", ida), ("B-A", "2022-12-01", regreso)])


def test_dimensionar_caso_a_mano_ida_y_regreso():
    # A-B: cap_ef = 1·30 = 30; útiles 24; 100/24 = 4,17 → 5 despachos
    # B-A: cap_ef = 0,5·30 + 0,5·18 = 24; útiles 19,2; 150/19,2 = 7,81 → 8 despachos
    # vueltas = 18/9 = 2; vehículos del corredor = ⌈max(5, 8)/2⌉ = 4 en las dos filas
    # k = 1 (4 h ≤ 8 h); P = 2 · max(5, 8) = 16; L = ⌊7/4⌋ = 1 → C_serv = 16; C_nom = ⌈16 / 0,91 · 7/6⌉ = ⌈20,51⌉ = 21
    out = op.dimensionar(_ida_y_regreso(), _params()).set_index("ruta_id")
    assert out.loc["A-B", "capacidad_efectiva"] == pytest.approx(30.0)
    assert out.loc["B-A", "capacidad_efectiva"] == pytest.approx(24.0)
    assert out.loc["A-B", "despachos"] == 5 and out.loc["B-A", "despachos"] == 8
    assert out.loc["A-B", "despachos_regreso"] == 8 and out.loc["B-A", "despachos_regreso"] == 5
    assert list(out["vueltas"]) == pytest.approx([2.0, 2.0])
    assert list(out["vehiculos"]) == [4, 4]
    assert list(out["tripulacion"]) == [1, 1]
    assert list(out["piernas"]) == [16, 16]
    assert list(out["piernas_por_conductor"]) == [1, 1]
    assert list(out["conductores_servicio"]) == [16, 16]
    assert list(out["conductores"]) == [21, 21]
    # la flota es del corredor (no se suma dos veces): misma etiqueta en las dos filas
    assert out.loc["A-B", "corredor"] == out.loc["B-A", "corredor"]


def test_dimensionar_segundo_conductor_por_norma_en_recorridos_largos():
    # t = 10 h > 8 h → k = 2 (Res. 315/2013 art. 6), sin bandera. T = 22 h, H = 18 → v = 18/22 = 0,818
    # despachos 5 y 8 (como arriba) → veh = ⌈8 / 0,818⌉ = ⌈9,78⌉ = 10
    # h = 10/2 = 5; L = ⌊7/5⌋ = 1; C_serv = ⌈2 · 16 / 1⌉ = 32; C_nom = ⌈32 / 0,91 · 7/6⌉ = ⌈41,03⌉ = 42
    p = _params()
    for r in ("A-B", "B-A"):
        p["por_ruta"][r].update(tiempo_recorrido_h=10.0, tiempo_ciclo_h=22.0)
    out = op.dimensionar(_ida_y_regreso(), p)
    assert list(out["vueltas"]) == pytest.approx([18 / 22, 18 / 22])
    assert list(out["vehiculos"]) == [10, 10]
    assert list(out["tripulacion"]) == [2, 2]
    assert list(out["conductores_servicio"]) == [32, 32]
    assert list(out["conductores"]) == [42, 42]


def test_dimensionar_corredor_corto_varias_piernas_por_conductor():
    # Pasto–Ipiales: t = 1,5, T = 3,5; despachos 5 y 8 → P = 16; L = ⌊7/1,5⌋ = 4 → C_serv = 4;
    # C_nom = ⌈4 / 0,91 · 7/6⌉ = ⌈5,13⌉ = 6. Vueltas 18/3,5 = 5,14 → veh = ⌈8 / 5,14⌉ = ⌈1,56⌉ = 2.
    p = _params()
    for r in ("A-B", "B-A"):
        p["por_ruta"][r].update(tiempo_recorrido_h=1.5, tiempo_ciclo_h=3.5)
    out = op.dimensionar(_ida_y_regreso(), p)
    assert list(out["vehiculos"]) == [2, 2]
    assert list(out["piernas_por_conductor"]) == [4, 4]
    assert list(out["conductores_servicio"]) == [4, 4]
    assert list(out["conductores"]) == [6, 6]


def test_conductores_no_dependen_de_las_horas_de_operacion():
    # Error de la ec. (5) anterior: cond ∝ veh · H no es monótona en H. Ahora C_serv y C_nom no dependen de H;
    # los vehículos no crecen con H: H = 18 → v = 2 → 4 veh; H = 9 → v = 1 → 8 veh; H = 24 → v = 2,67 → ⌈3,0⌉ = 3 veh.
    conductores, vehiculos = set(), []
    for h in (9.0, 18.0, 24.0):
        out = op.dimensionar(_ida_y_regreso(), _params(horas_operacion_h=h))
        conductores.add((int(out["conductores_servicio"].iloc[0]), int(out["conductores"].iloc[0])))
        vehiculos.append(int(out["vehiculos"].iloc[0]))
    assert conductores == {(16, 21)}
    assert vehiculos == [8, 4, 3]


def test_dimensionar_conserva_columnas_y_orden_de_entrada():
    entrada = _demanda([("B-A", "2022-12-02", 0), ("A-B", "2022-12-02", 0), ("A-B", "2022-12-01", 10),
                        ("B-A", "2022-12-01", 10)])
    out = op.dimensionar(entrada, _params())
    assert list(out.columns[:3]) == ["ruta_id", "fecha", "demanda"]
    assert {"despachos", "vehiculos", "conductores_servicio", "conductores"} <= set(out.columns)
    pd.testing.assert_frame_equal(out[["ruta_id", "fecha", "demanda"]], entrada)
    for col in ("despachos", "vehiculos", "conductores_servicio", "conductores"):
        assert pd.api.types.is_integer_dtype(out[col])


def test_dimensionar_conserva_columnas_extra_de_la_entrada():
    out = op.dimensionar(_ida_y_regreso().assign(tipo_demanda="EJEMPLO"), _params())
    assert list(out.columns[:4]) == ["ruta_id", "fecha", "demanda", "tipo_demanda"]


def test_dimensionar_demanda_cero_da_cero():
    out = op.dimensionar(_ida_y_regreso(0, 0), _params())
    assert (out[["despachos", "vehiculos", "conductores_servicio", "conductores"]] == 0).all().all()


def test_dimensionar_un_sentido_vacio_igual_necesita_flota():
    # A-B con 0 pasajeros y B-A con 150: los vehículos que vuelven de B deben haber ido; veh = ⌈max(0, 8)/2⌉ = 4.
    # Conductores: 8 piernas cargadas B→A + 8 vacías A→B de reposición = P = 2 · max(0, 8) = 16; L = 1 → C_serv = 16
    # (con desp + desp' serían solo 8 piernas).
    out = op.dimensionar(_ida_y_regreso(0, 150), _params())
    assert list(out["vehiculos"]) == [4, 4]
    assert list(out["piernas"]) == [16, 16]
    assert list(out["conductores_servicio"]) == [16, 16]


def test_flota_monotona_en_la_demanda():
    # Invariante: la salida es monótona no decreciente en la demanda (q0.9 ≥ q0.5 ⇒ flota(q0.9) ≥ flota(q0.5)).
    cols = ("despachos", "vehiculos", "conductores_servicio", "conductores")
    previo = None
    for escala in (0.0, 0.5, 0.9, 1.0, 1.1, 1.5, 3.0):
        out = op.dimensionar(_ida_y_regreso(100 * escala, 150 * escala), _params())
        if previo is not None:
            for col in cols:
                assert (out[col].to_numpy() >= previo[col].to_numpy()).all(), (escala, col)
        previo = out


def test_dimensionar_exige_la_demanda_del_regreso_el_mismo_dia():
    with pytest.raises(ValueError, match="regreso"):
        op.dimensionar(_demanda([("A-B", "2022-12-01", 100)]), _params())
    with pytest.raises(ValueError, match="regreso"):
        op.dimensionar(_demanda([("A-B", "2022-12-01", 100), ("B-A", "2022-12-02", 100)]), _params())


@pytest.mark.parametrize(
    ("clave", "valor", "mensaje"),
    [
        ("ocupacion_objetivo", 0.0, "ocupacion_objetivo"),
        ("ocupacion_objetivo", 1.2, "ocupacion_objetivo"),
        ("cuantil", 0.8, "cuantil"),            # no es un cuantil del arnés (núcleo §5.3)
        ("cuantil", 1.0, "cuantil"),
        ("ausentismo", 1.0, "ausentismo"),
        ("ausentismo", -0.1, "ausentismo"),
        ("horas_operacion_h", 0.0, "horas_operacion_h"),
        ("horas_operacion_h", 25.0, "horas_operacion_h"),
        ("jornada_efectiva_h", 9.0, "jornada_efectiva_h"),  # > jornada_max_diaria_h = 8
        ("jornada_efectiva_h", 7.5, "jornada_max_semanal_h"),  # 7,5 · 6 = 45 > 42
        ("jornada_max_semanal_h", 0.0, "jornada_max_semanal_h"),
        ("dias_descanso_semana", 0, "dias_descanso_semana"),  # la norma garantiza el día de descanso
        ("dias_descanso_semana", 7, "dias_descanso_semana"),
        ("dias_descanso_semana", 1.5, "dias_descanso_semana"),
        ("umbral_segundo_conductor_h", 0.0, "umbral_segundo_conductor_h"),
    ],
)
def test_parametros_fuera_de_rango_dan_error_claro(clave, valor, mensaje):
    p = _params()
    p["globales"][clave] = valor
    with pytest.raises(ValueError, match=mensaje):
        op.dimensionar(_ida_y_regreso(), p)


@pytest.mark.parametrize("q", [0.5, 0.75, 0.9, 0.95])
def test_cuantiles_del_arnes_son_validos(q):
    op.dimensionar(_ida_y_regreso(), _params(cuantil=q))


def test_semana_justa_en_el_limite_es_valida():
    # J_ef · (7 − s) = 7 · 6 = 42 ≤ 42 (igualdad permitida); 6 · 5 = 30 con s = 2 también.
    op.dimensionar(_ida_y_regreso(), _params(jornada_efectiva_h=7.0, dias_descanso_semana=1))
    op.dimensionar(_ida_y_regreso(), _params(jornada_efectiva_h=6.0, dias_descanso_semana=2))


def test_pierna_que_un_conductor_no_puede_cubrir_da_error():
    # t = 18 h > 8 h → k = 2; t / k = 9 h > jornada máxima diaria (8 h): ni con dos conductores se cubre la pierna.
    p = _params()
    for r in ("A-B", "B-A"):
        p["por_ruta"][r].update(tiempo_recorrido_h=18.0, tiempo_ciclo_h=40.0)
    with pytest.raises(ValueError, match="jornada_max_diaria_h"):
        op.dimensionar(_ida_y_regreso(), p)
    # t = 8 h → k = 1 y t / k = 8 ≤ 8: válido (borde incluido)
    for r in ("A-B", "B-A"):
        p["por_ruta"][r].update(tiempo_recorrido_h=8.0, tiempo_ciclo_h=17.0)
    op.dimensionar(_ida_y_regreso(), p)


def test_errores_de_ruta_clase_y_composicion():
    d = _ida_y_regreso()
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


# --------------------------------------------------------------------------------------- tabla por corredor

def test_flota_por_corredor_cuenta_cada_corredor_una_vez():
    # dos días; el corredor A-B | B-A aparece en 2 filas por día en `dimensionar` y en 1 fila por día aquí.
    entrada = _demanda([("A-B", "2022-12-01", 100), ("B-A", "2022-12-01", 150),
                        ("A-B", "2022-12-02", 0), ("B-A", "2022-12-02", 0)])
    tabla = op.dimensionar(entrada, _params())
    corr = op.flota_por_corredor(tabla)
    assert len(corr) == 2
    fila = corr.set_index("fecha").loc[pd.Timestamp("2022-12-01")]
    assert fila["corredor"] == "A-B | B-A"
    assert (fila["ruta_ida"], fila["ruta_regreso"]) == ("A-B", "B-A")
    assert (fila["despachos_ida"], fila["despachos_regreso"]) == (5, 8)
    assert (fila["vehiculos"], fila["conductores_servicio"], fila["conductores"]) == (4, 16, 21)
    # sumar la tabla por ruta daría el doble: 8 vehículos-día; la del corredor da los 4 reales
    assert tabla["vehiculos"].sum() == 2 * corr["vehiculos"].sum() == 8


def test_flota_por_corredor_detecta_filas_inconsistentes():
    tabla = op.dimensionar(_ida_y_regreso(), _params())
    tabla.loc[tabla["ruta_id"] == "B-A", "vehiculos"] = 99
    with pytest.raises(ValueError, match="corredor"):
        op.flota_por_corredor(tabla)


# ------------------------------------------------------------------------- calibración (solo train, sin fuga)

def _detalle() -> pd.DataFrame:
    # ruta R1 (ORIGEN salvo donde se indica):
    #   2021-05-15 BUS 100 despachos          → antes del inicio de entrenamiento: fuera
    #   2021-06-01 BUS 6, MICROBUS 2          → dentro (borde inferior incluido)
    #   2022-11-15 BUS 1                      → dentro (y en los 2 últimos meses de train)
    #   2022-12-31 BUS 3, MICROBUS 1          → dentro (borde superior incluido)
    #   2023-01-01 MICROBUS 1000              → después del fin de entrenamiento: fuera (sería fuga)
    #   2022-06-01 TRANSITO MICROBUS 500      → tránsito: fuera de composición y capacidad (100 pas./desp.)
    #   2022-12-01 TRANSITO BUS 1             → tránsito en los últimos 2 meses (cuenta para f)
    # composición = BUS 10/13; MICROBUS 3/13; BUSETA (en config, no en datos) = 0
    filas = [
        ("R1", "2021-05-15", "ORIGEN", "BUS", 1000, 100),
        ("R1", "2021-06-01", "ORIGEN", "BUS", 60, 6),
        ("R1", "2021-06-01", "ORIGEN", "MICROBUS", 20, 2),
        ("R1", "2022-11-15", "ORIGEN", "BUS", 25, 1),
        ("R1", "2022-12-31", "ORIGEN", "BUS", 90, 3),
        ("R1", "2022-12-31", "ORIGEN", "MICROBUS", 10, 1),
        ("R1", "2023-01-01", "ORIGEN", "MICROBUS", 99999, 1000),
        ("R1", "2022-06-01", "TRANSITO", "MICROBUS", 50000, 500),
        ("R1", "2022-12-01", "TRANSITO", "BUS", 375, 1),
    ]
    d = pd.DataFrame(filas, columns=["ruta_id", "fecha", "tipo_despacho", "clase_vehiculo", "pasajeros", "despachos"])
    d["fecha"] = pd.to_datetime(d["fecha"]).dt.date  # mismo tipo que demanda_detalle.parquet (date)
    return d


CLASES = ["BUS", "BUSETA", "MICROBUS"]


def test_composicion_solo_origen_y_solo_train():
    comp = op.estimar_composicion(_detalle(), "2021-06-01", "2022-12-31", CLASES)
    assert comp == {"R1": pytest.approx({"BUS": 10 / 13, "BUSETA": 0.0, "MICROBUS": 3 / 13})}


def _alterar_despues(d: pd.DataFrame, fin: str) -> pd.DataFrame:
    """Cambia TODO lo posterior a `fin` y agrega filas nuevas posteriores (invariante contra fuga)."""
    otro = d.copy()
    despues = pd.to_datetime(otro["fecha"]) > pd.Timestamp(fin)
    otro.loc[despues, "despachos"] = 7_777_777
    otro.loc[despues, "pasajeros"] = 1
    otro.loc[despues, "clase_vehiculo"] = "BUSETA"
    extra = pd.DataFrame([("R1", date(2023, 6, 1), "ORIGEN", "BUS", 999_999, 1),
                          ("R1", date(2023, 6, 2), "TRANSITO", "BUS", 999_999, 1)], columns=d.columns)
    return pd.concat([otro, extra], ignore_index=True)


def test_calibracion_no_cambia_con_datos_posteriores_al_fin_de_entrenamiento():
    # Invariante contra fuga: alterar TODO lo posterior al corte no puede mover composición, f, capacidad ni despachos.
    d, otro = _detalle(), _alterar_despues(_detalle(), "2022-12-31")
    args = ("2021-06-01", "2022-12-31")
    assert op.estimar_composicion(otro, *args, CLASES) == op.estimar_composicion(d, *args, CLASES)
    assert op.fraccion_pasajeros_origen(otro, *args) == op.fraccion_pasajeros_origen(d, *args)
    pd.testing.assert_frame_equal(op.capacidad_observada(otro, *args), op.capacidad_observada(d, *args))
    pd.testing.assert_frame_equal(op.despachos_origen_diarios(otro, *args), op.despachos_origen_diarios(d, *args))


def test_composicion_rechaza_clase_desconocida_y_ruta_sin_despachos():
    with pytest.raises(ValueError, match="MICROBUS"):
        op.estimar_composicion(_detalle(), "2021-06-01", "2022-12-31", ["BUS"])
    with pytest.raises(ValueError, match="R1"):
        op.estimar_composicion(_detalle(), "2021-06-02", "2021-06-03", CLASES)


def test_capacidad_observada_es_el_maximo_en_origen_y_train():
    # ORIGEN en [2021-06-01, 2022-12-31], pasajeros por despacho: BUS 60/6 = 10, 25/1 = 25, 90/3 = 30 → máx. 30;
    # MICROBUS 20/2 = 10, 10/1 = 10 → máx. 10. Fuera: 2021-05-15 (10), 2023 (≈ 100) y TRANSITO (100 y 375).
    obs = op.capacidad_observada(_detalle(), "2021-06-01", "2022-12-31").set_index("clase_vehiculo")
    assert obs.loc["BUS", "maximo"] == pytest.approx(30.0)
    assert obs.loc["MICROBUS", "maximo"] == pytest.approx(10.0)
    assert obs.loc["BUS", "n_dias"] == 3


def test_capacidad_supuesta_recorta_al_rango_del_decreto_1079():
    # cap = min(máx. del grupo, max(mín. del grupo, ⌈máximo observado⌉)); grupos A 4–9, B 10–19, C ≥ 20.
    assert op.capacidad_supuesta("BUS", 40.0) == 40          # C sin tope
    assert op.capacidad_supuesta("BUS", 12.3) == 20          # sube al mínimo del grupo C («más de 19»)
    assert op.capacidad_supuesta("MICROBUS", 18.66) == 19    # ⌈18,66⌉ = 19
    assert op.capacidad_supuesta("MICROBUS", 25.0) == 19     # recorta al máximo del grupo B
    assert op.capacidad_supuesta("AUTOMOVIL", 2.5) == 4      # sube al mínimo del grupo A
    assert op.capacidad_supuesta("CAMPERO", 8.15) == 9
    assert op.capacidad_supuesta("CAMIONETA", 9.0) == 9      # 9 exacto no sube a 10 (tolerancia del techo)
    with pytest.raises(ValueError, match="TRACTOMULA"):
        op.capacidad_supuesta("TRACTOMULA", 3.0)


def test_fraccion_de_pasajeros_en_origen_solo_train():
    # ventana completa: ORIGEN 60 + 20 + 25 + 90 + 10 = 205; TRANSITO 50000 + 375 → 205 / 50580
    assert op.fraccion_pasajeros_origen(_detalle(), "2021-06-01", "2022-12-31") == {"R1": pytest.approx(205 / 50580)}
    # últimos 2 meses [2022-11-01, 2022-12-31]: ORIGEN 25 + 90 + 10 = 125; TRANSITO 375 → 125 / 500 = 0,25
    assert op.fraccion_pasajeros_origen(_detalle(), "2022-11-01", "2022-12-31") == {"R1": pytest.approx(0.25)}


def test_fraccion_sin_pasajeros_en_la_ventana_da_error_claro():
    d = _detalle()
    d.loc[len(d)] = ("R2", date(2021, 6, 1), "ORIGEN", "BUS", 0, 1)  # R2 existe pero no lleva pasajeros
    with pytest.raises(ValueError, match="R2"):
        op.fraccion_pasajeros_origen(d, "2021-06-01", "2022-12-31")
    with pytest.raises(ValueError, match="R1"):  # R1 sin filas en la ventana
        op.fraccion_pasajeros_origen(_detalle(), "2021-07-01", "2021-07-31")


def test_ventana_reciente_son_los_ultimos_meses_de_train():
    # fin 2022-12-31, 2 meses → [2022-11-01, 2022-12-31] (fin + 1 día − 2 meses = 2022-11-01)
    assert op.ventana_reciente("2021-06-01", "2022-12-31", 2) == (date(2022, 11, 1), date(2022, 12, 31))
    # fin a mitad de mes: 2022-12-15 + 1 día − 2 meses = 2022-10-16
    assert op.ventana_reciente("2021-06-01", "2022-12-15", 2) == (date(2022, 10, 16), date(2022, 12, 15))
    # nunca antes del inicio de entrenamiento: 60 meses → recorta a 2021-06-01
    assert op.ventana_reciente("2021-06-01", "2022-12-31", 60) == (date(2021, 6, 1), date(2022, 12, 31))
    with pytest.raises(ValueError, match="meses_fraccion"):
        op.ventana_reciente("2021-06-01", "2022-12-31", 0)


def test_despachos_origen_diarios_suman_clases_solo_en_origen():
    # 2021-06-01: 6 + 2 = 8; 2022-11-15: 1; 2022-12-31: 3 + 1 = 4. El tránsito y lo de fuera de la ventana no cuentan.
    obs = op.despachos_origen_diarios(_detalle(), "2021-06-01", "2022-12-31")
    assert list(obs.columns) == ["ruta_id", "fecha", "despachos"]
    assert obs["despachos"].tolist() == [8, 1, 4]


def test_ocupacion_calibrada_a_mano():
    # R1: f = 0,5, cap_ef = 20, D = 400 → 0,5 · 400 / 20 = 10 cargas llenas; R2: f = 1, cap_ef = 10, D = 50 → 5.
    # Despachos ORIGEN observados 20 + 5 = 25 → ρ* = (10 + 5) / 25 = 0,6.
    # El día 2022-12-02 de R2 no está en la demanda (p. ej. sin registro): su despacho observado no entra.
    demanda = _demanda([("R1", "2022-12-01", 400), ("R2", "2022-12-01", 50)])
    obs = _demanda([("R1", "2022-12-01", 20), ("R2", "2022-12-01", 5), ("R2", "2022-12-02", 99)]).rename(
        columns={"demanda": "despachos"})
    rho = op.ocupacion_calibrada(demanda, obs, {"R1": 0.5, "R2": 1.0}, {"R1": 20.0, "R2": 10.0})
    assert rho == pytest.approx(0.6)


def test_ocupacion_calibrada_reproduce_los_despachos_en_agregado():
    # Con ρ = ρ*, Σ f·D / (cap_ef · ρ*) = Σ despachos observados exactamente (antes del techo).
    demanda = _demanda([("R1", "2022-12-01", 400), ("R1", "2022-12-02", 260), ("R2", "2022-12-01", 50)])
    obs = _demanda([("R1", "2022-12-01", 20), ("R1", "2022-12-02", 11), ("R2", "2022-12-01", 5)]).rename(
        columns={"demanda": "despachos"})
    f, cap = {"R1": 0.5, "R2": 1.0}, {"R1": 20.0, "R2": 10.0}
    rho = op.ocupacion_calibrada(demanda, obs, f, cap)
    continuo = sum(f[r] * dem / (cap[r] * rho) for r, dem in zip(demanda["ruta_id"], demanda["demanda"], strict=True))
    assert continuo == pytest.approx(obs["despachos"].iloc[:3].sum())


def test_reproduccion_de_despachos_por_ruta_y_total():
    # modelo R1: 5 + 3 = 8 vs observado 10 → 80 %; R2: 6 vs 4 → 150 %; total 14 / 14 = 100 %
    tabla = _demanda([("R1", "2022-12-01", 0), ("R1", "2022-12-02", 0), ("R2", "2022-12-01", 0)]).assign(
        despachos=[5, 3, 6])
    obs = _demanda([("R1", "2022-12-01", 6), ("R1", "2022-12-02", 4), ("R2", "2022-12-01", 4)]).rename(
        columns={"demanda": "despachos"})
    rep = op.reproduccion_despachos(tabla, obs)
    assert rep["R1"] == {"modelo": 8, "observado": 10, "porcentaje": pytest.approx(80.0)}
    assert rep["R2"]["porcentaje"] == pytest.approx(150.0)
    assert rep["total"] == {"modelo": 14, "observado": 14, "porcentaje": pytest.approx(100.0)}


# --------------------------------------------------------------------------------- demanda de ejemplo (train)

def _diaria() -> pd.DataFrame:
    # Corredor A-B | B-A en diciembre de 2022 (3 días) y un día de enero de 2023 (posterior al train).
    # 2022-12-02: B-A sin registro → se excluye el DÍA DEL CORREDOR (ambos sentidos), porque dimensionar necesita los dos.
    filas = [
        ("A-B", "2022-12-01", 100, False), ("B-A", "2022-12-01", 150, False),
        ("A-B", "2022-12-02", 120, False), ("B-A", "2022-12-02", 0, True),
        ("A-B", "2022-12-03", 90, False), ("B-A", "2022-12-03", 80, False),
        ("A-B", "2023-01-01", 999, False), ("B-A", "2023-01-01", 999, False),
    ]
    d = pd.DataFrame(filas, columns=["ruta_id", "fecha", "pasajeros", "sin_registro"])
    d["fecha"] = pd.to_datetime(d["fecha"]).dt.date
    return d


REGRESOS = {"A-B": "B-A", "B-A": "A-B"}


def test_demanda_ejemplo_excluye_dias_sin_registro_del_corredor():
    ej = op.demanda_ejemplo(_diaria(), "2022-12", REGRESOS, "2021-06-01", "2022-12-31")
    assert sorted(ej["fecha"].dt.day.unique()) == [1, 3]
    assert len(ej) == 4 and (ej["tipo_demanda"] == op.TIPO_EJEMPLO).all()
    assert list(ej.columns) == ["ruta_id", "fecha", "demanda", "tipo_demanda"]


@pytest.mark.parametrize(
    ("mes", "inicio", "fin", "mensaje"),
    [
        ("2023-01", "2021-06-01", "2022-12-31", "fin_entrenamiento"),   # después del train
        ("2022-12", "2021-06-01", "2022-12-15", "fin_entrenamiento"),   # el mes termina después del fin
        ("2022-12", "2022-12-02", "2022-12-31", "inicio_entrenamiento"),  # el mes empieza antes del inicio
        ("2022-10", "2021-06-01", "2022-12-31", "no hay datos"),
    ],
)
def test_demanda_ejemplo_valida_la_ventana_de_train(mes, inicio, fin, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        op.demanda_ejemplo(_diaria(), mes, REGRESOS, inicio, fin)


def test_demanda_observada_en_train_excluye_sin_registro():
    obs = op.demanda_observada(_diaria(), "2021-06-01", "2022-12-31", REGRESOS, "2021-06-01", "2022-12-31")
    assert len(obs) == 4 and obs["fecha"].max() <= pd.Timestamp("2022-12-31")


# ------------------------------------------------------------------------------------- configs/m1/operacion.yaml

@pytest.fixture(scope="module")
def cfg_operacion() -> dict:
    return load_config(CONFIG)


@pytest.fixture(scope="module")
def calibracion(cfg_operacion) -> dict:
    return op.calibrar(cfg_operacion, pd.read_parquet(DETALLE), pd.read_parquet(DIARIA), op.leer_regresos(RUTAS))


def _hojas(valores: dict) -> list[tuple[str, ...]]:
    """Rutas (grupo, …, clave) de los parámetros de `operacion` (meta de por_ruta por clave, compartida)."""
    out = []
    for k, v in valores.items():
        if k == "por_ruta":
            out += sorted({("por_ruta", kk) for d in v.values() for kk in d})
        elif k == "por_clase":
            out += [("por_clase", sub, kk) for sub, d in v.items() for kk in d]
        else:
            out.append(("globales", k))
    return out


def test_cada_parametro_tiene_unidad_y_fuente_xor_supuesto(cfg_operacion):
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
        if m.get("supuesto") is True:
            assert isinstance(m.get("nota"), str) and m["nota"].strip(), f"{ruta}: un supuesto lleva nota"
    # y ninguna meta sobra
    n_meta = len(meta["globales"]) + len(meta["por_ruta"]) + sum(len(v) for v in meta["por_clase"].values())
    assert n_meta == len(hojas)


def test_valores_normativos_llevan_fuente_verificada(cfg_operacion):
    # CA-2_verificacion.md §7: estos cuatro pasan de supuesto a fuente.
    g, meta = cfg_operacion["operacion"], cfg_operacion["meta"]["globales"]
    esperado = {
        "jornada_max_diaria_h": (8, "Ley 2466 de 2025"),
        "umbral_segundo_conductor_h": (8, "Resolución 315 de 2013"),
        "dias_descanso_semana": (1, "Ley 2466 de 2025"),
        "jornada_max_semanal_h": (42, "Ley 2101 de 2021"),
    }
    for clave, (valor, norma) in esperado.items():
        assert g[clave] == valor, clave
        assert norma in meta[clave]["fuente"], clave
        assert "supuesto" not in meta[clave], clave
    # y la semana del conductor cabe en la jornada semanal: 7 · (7 − 1) = 42 ≤ 42
    assert g["jornada_efectiva_h"] * (7 - g["dias_descanso_semana"]) <= g["jornada_max_semanal_h"]


def test_yaml_sin_banderas_opcionales_ni_fraccion_escrita_a_mano(cfg_operacion):
    o = cfg_operacion["operacion"]
    for quitada in ("segundo_conductor_activo", "vueltas_fraccionarias"):
        assert quitada not in o and quitada not in cfg_operacion["meta"]["globales"]
    for r, p in o["por_ruta"].items():
        assert "fraccion_demanda_en_origen" not in p, r  # f se calcula con train al ejecutar
    assert "fraccion_demanda_en_origen" not in cfg_operacion["meta"]["por_ruta"]
    assert cfg_operacion["calibracion"]["meses_fraccion"] == 2
    # la nota de los costos debe decir que dimensionar no los usa
    for k in ("costo_pasajero_sin_atender", "costo_vehiculo_dia_sobrante"):
        assert "no los usa" in cfg_operacion["meta"]["globales"][k]["nota"]


def test_yaml_sin_anclas_ni_alias():
    # Eventos del parser: un ancla (&x) deja `anchor` en el nodo y un alias (*x) es un AliasEvent.
    eventos = list(yaml.parse(CONFIG.read_text(encoding="utf-8")))
    assert not [e for e in eventos if isinstance(e, yaml.AliasEvent) or getattr(e, "anchor", None)]
    # la prueba detecta un ancla si la hubiera
    assert any(getattr(e, "anchor", None) for e in yaml.parse("a: &x {b: 1}\nc: *x\n"))


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


# Rangos del Decreto 1079 de 2015, arts. 2.2.1.4.7.3–2.2.1.4.7.4 (compila el Decreto 171/2001, arts. 50–51), verificados
# en docs/investigacion/CA-2_verificacion.md §6: Grupo A «4 a 9 pasajeros» (automóvil, campero, camioneta); B «10 a 19»
# (microbús); C «más de 19» (buseta, bus). Copia independiente de la del módulo, a propósito.
RANGO_DECRETO_1079 = {"AUTOMOVIL": (4, 9), "CAMPERO": (4, 9), "CAMIONETA": (4, 9), "MICROBUS": (10, 19),
                      "BUSETA": (20, math.inf), "BUS": (20, math.inf)}


def test_capacidades_del_yaml_son_el_maximo_de_train_recortado(cfg_operacion):
    # cap(c) = min(máx. del grupo, max(mín. del grupo, ⌈máximo de pasajeros/despacho ORIGEN en train⌉)).
    d = cfg_operacion["datos"]
    obs = op.capacidad_observada(pd.read_parquet(DETALLE), d["inicio_entrenamiento"],
                                 d["fin_entrenamiento"]).set_index("clase_vehiculo")
    assert op.RANGO_CAPACIDAD == RANGO_DECRETO_1079
    for clase, (lo, hi) in RANGO_DECRETO_1079.items():
        cap = cfg_operacion["operacion"]["por_clase"][clase]["capacidad_pasajeros"]
        assert lo <= cap <= hi, clase
        maximo = obs.loc[clase, "maximo"]
        esperado = min(hi, max(lo, math.ceil(maximo - 1e-9)))
        assert cap == esperado, (clase, maximo)


def test_ocupacion_por_defecto_es_rho_estrella_redondeado(cfg_operacion, calibracion):
    # ρ por defecto = ρ* (calibrado con train) a dos decimales.
    rho = calibracion["ocupacion_calibrada"]
    assert 0 < rho <= 1
    assert cfg_operacion["operacion"]["ocupacion_objetivo"] == pytest.approx(round(rho, 2), abs=1e-12)


def test_calibracion_con_los_datos_reales(cfg_operacion, calibracion):
    # f se calcula con los 2 últimos meses de train; queda en (0, 1] para todas las rutas.
    assert calibracion["ventana_fraccion"] == (date(2022, 11, 1), date(2022, 12, 31))
    assert set(calibracion["fraccion"]) == set(cfg_operacion["operacion"]["por_ruta"])
    assert all(0 < f <= 1 for f in calibracion["fraccion"].values())
    # el régimen reciente de 11001-15759 (tránsito alto desde nov-2022) baja f frente a todo el train (0,417)
    assert calibracion["fraccion"]["11001-15759"] < 0.35


def test_rho_estrella_usa_la_misma_ventana_que_f(calibracion):
    # [DECIDIDO, Camila, 26-nov, CA-3c] ρ* con los (r, d) de train dentro de la ventana de f (2022-11-01..2022-12-31),
    # recalculado aquí por separado: Σ f·D/cap_ef ÷ Σ despachos ORIGEN de esos mismos días.
    ini, fin = (pd.Timestamp(x) for x in calibracion["ventana_fraccion"])
    dem = calibracion["demanda_train"]
    dem = dem[(dem["fecha"] >= ini) & (dem["fecha"] <= fin)]
    assert dem["fecha"].min() == ini and dem["fecha"].max() == fin
    obs = dem.merge(calibracion["despachos_origen_train"], on=["ruta_id", "fecha"], how="left")["despachos"].fillna(0)
    f, cap = calibracion["fraccion"], calibracion["capacidad_efectiva"]
    num = sum(f[r] * d / cap[r] for r, d in zip(dem["ruta_id"], dem["demanda"], strict=True))
    assert calibracion["ocupacion_calibrada"] == pytest.approx(num / obs.sum(), rel=1e-12)
    # y difiere de la de todo el train (diagnóstico), que mezcla regímenes con la f reciente
    assert abs(calibracion["ocupacion_calibrada"] - calibracion["ocupacion_calibrada_todo_train"]) > 0.01


def test_notas_del_yaml_declaran_las_limitaciones(cfg_operacion):
    g = cfg_operacion["meta"]["globales"]
    assert "por ruta" in g["ocupacion_objetivo"]["nota"]                      # desajuste por ruta de ρ global
    assert "relevo" in g["jornada_efectiva_h"]["nota"]                        # supuesto de (5a)
    assert "disposición del empleador" in g["jornada_efectiva_h"]["nota"]     # la pausa no es tiempo a disposición
    assert "cota baja" in cfg_operacion["meta"]["por_clase"]["BUS"]["capacidad_pasajeros"]["nota"]


def test_fin_de_entrenamiento_propuesto_no_pasa_de_2023_01_01(cfg_operacion):
    d = cfg_operacion["datos"]
    assert date.fromisoformat(d["inicio_entrenamiento"]) == date(2021, 6, 1)  # núcleo §5.1
    assert date.fromisoformat(d["fin_entrenamiento"]) <= date(2023, 1, 1)


def test_parametros_al_formato_del_contrato_de_la_app(cfg_operacion, calibracion):
    # Núcleo §5.4: {valor, unidad, fuente | supuesto: true, nota?} en globales, por_ruta, por_clase y composicion_clases.
    d = cfg_operacion["datos"]
    c = op.parametros_contrato(cfg_operacion, calibracion)
    assert set(c) == {"globales", "por_ruta", "por_clase", "composicion_clases"}
    assert {"ocupacion_objetivo", "cuantil"} <= set(c["globales"])
    pars = list(c["globales"].values())
    pars += [p for g in ("por_ruta", "por_clase", "composicion_clases") for sub in c[g].values() for p in sub.values()]
    for p in pars:
        assert set(p) <= {"valor", "unidad", "fuente", "supuesto", "nota"}
        assert isinstance(p["valor"], (int, float)) and not isinstance(p["valor"], bool)
        assert isinstance(p["unidad"], str)
        assert ("fuente" in p) != (p.get("supuesto") is True)
    for ruta, pr in c["por_ruta"].items():  # f sale de los datos de train: fuente con la ventana reciente
        f = pr["fraccion_demanda_en_origen"]
        assert f["valor"] == calibracion["fraccion"][ruta]
        assert "2022-11-01" in f["fuente"] and d["fin_entrenamiento"] in f["fuente"]
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
    assert (tabla["tipo_demanda"] == op.TIPO_EJEMPLO).all()
    assert {"despachos", "vehiculos", "conductores_servicio", "conductores"} <= set(tabla.columns)
    fechas = pd.to_datetime(tabla["fecha"])
    assert fechas.max() <= pd.Timestamp(cfg["datos"]["fin_entrenamiento"])  # el ejemplo no sale del train
    corr = pd.read_csv(tmp_path / "flota_por_corredor.csv")
    assert not corr.duplicated(["corredor", "fecha"]).any()  # una fila por corredor y día
    assert len(corr) * 2 == len(tabla)
    comp = pd.read_csv(tmp_path / "composicion_clases.csv")
    assert comp.groupby("ruta_id")["participacion"].sum().round(9).eq(1).all()
    resumen = yaml.safe_load((tmp_path / "resumen.json").read_text(encoding="utf-8"))
    assert resumen["parametros"]["globales"]["ocupacion_objetivo"]["valor"] == 0.8
    assert 0 < resumen["calibracion"]["ocupacion_calibrada"] <= 1
    for clave in ("reproduccion_despachos_calibracion", "reproduccion_despachos_train"):
        assert set(resumen["calibracion"][clave]) == {*cfg["operacion"]["por_ruta"], "total"}
    for v in resumen["maximo_diario_por_corredor"].values():
        assert {"vehiculos", "conductores_servicio", "conductores"} == set(v)
