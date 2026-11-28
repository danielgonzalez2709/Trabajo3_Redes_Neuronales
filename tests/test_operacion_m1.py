"""CA-3 (prompts CA-3b a CA-3e): `dimensionar()` y conductores (núcleo §5.4; spec de Camila §3.3).

Fórmula [DECIDIDO, Camila, 26-nov]; r' = ruta de regreso de r (`rutas.yaml`), {r, r'} = corredor:
    (1)  cap_ef(r)  = Σ_c π(r, c) · cap(c)
    (2)  desp(r, d) = ⌈ f(r) · D(r, d) / (cap_ef(r) · ρ_r) ⌉,  ρ_r = min(1, ρ · m_r)      (m: CA-3d y CA-3e)
    (3)  v(r)       = H / T_ciclo(r)                                   (fracción, sin piso ni mínimo)
    (4)  veh(r, d)  = ⌈ max(desp(r, d), desp(r', d)) / v(r) ⌉
    (5a) P          = 2 · max(desp(r, d), desp(r', d))                   piernas del corredor (con las vacías)
         k_r        = max(k_norma(t_r), ⌈ t_r / J_ef ⌉),  k_norma = 2 si t_r > 8 h (Res. 315/2013 art. 6)
         h_r        = t_r / k_r ≤ J_ef                                    horas al volante por conductor y pierna
         L_r        = ⌊ J_ef / h_r ⌋ ≥ 1                                 piernas (indivisibles) por conductor y día
         C_serv     = ⌈ k_r · P / L_r ⌉
    (5b) C_nom      = ⌈ C_serv / (1 − a) · 7 / (7 − s) ⌉,                s = 1 (día de descanso, art. 161 CST)
         N*(semana) = ⌈ max(max_d C_serv, Σ_d C_serv / (7 − s)) / (1 − a) ⌉   nómina semanal factible
Calibración con train: f(r) (últimos meses de train), cap(c) (máximo observado recortado al rango del Decreto 1079/2015),
ρ* = Σ f·D/cap_ef ÷ Σ despachos ORIGEN y m = ρ_obs / ρ* (por ruta, defecto, o por corredor: `calibracion.multiplicador`),
en la misma ventana que f. Cada prueba lleva sus cuentas en el comentario. Ninguna usa internet.
"""

from __future__ import annotations

import itertools
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
    # (3) v = H / T: 18 / 9 = 2;  18 / 10 = 1,8 (sin ⌊·⌋);  18 / 22 = 0,818… (sin mínimo de 1 vuelta)
    assert op.vueltas_dia(18, 9) == pytest.approx(2.0)
    assert op.vueltas_dia(18, 10) == pytest.approx(1.8)
    assert op.vueltas_dia(18, 22) == pytest.approx(18 / 22)


def test_vehiculos_usan_el_maximo_de_los_dos_sentidos():
    # ida 5, regreso 7, 2 vueltas: ⌈max(5, 7) / 2⌉ = ⌈3,5⌉ = 4 (con solo la ida serían ⌈5/2⌉ = 3).
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


def test_tripulacion_norma_solo_con_recorrido_estrictamente_mayor_al_umbral():
    # Res. 315/2013 art. 6: «duración superior a ocho (8) horas de recorrido» → k_norma = 2 solo si t > 8.
    assert op.tripulacion_norma(10, umbral_h=8) == 2
    assert op.tripulacion_norma(8.5, umbral_h=8) == 2
    assert op.tripulacion_norma(8, umbral_h=8) == 1     # 8 no es «superior a» 8
    assert op.tripulacion_norma(4, umbral_h=8) == 1


def test_tripulacion_es_el_maximo_entre_la_norma_y_la_jornada_efectiva():
    # (5a) k = max(k_norma(t), ⌈t / J_ef⌉) con umbral 8 h y J_ef = 7 h:
    assert op.tripulacion(10, 8, 7) == 2     # Bogotá–Cali: max(2, ⌈1,43⌉ = 2) = 2
    assert op.tripulacion(4, 8, 7) == 1      # Bogotá–Sogamoso: max(1, ⌈0,57⌉ = 1) = 1
    assert op.tripulacion(1.5, 8, 7) == 1    # Pasto–Ipiales: max(1, ⌈0,21⌉ = 1) = 1
    # t = 7,5 ≤ 8 → k_norma = 1, pero con k = 1 un conductor manejaría 7,5 h > J_ef = 7 h (7,5 · 6 = 45 h/semana > 42):
    # max(1, ⌈7,5/7⌉ = ⌈1,07⌉ = 2) = 2.
    assert op.tripulacion(7.5, 8, 7) == 2
    # Sin salto artificial en el umbral de la norma: t = 8 → max(1, ⌈1,14⌉ = 2) = 2; t = 8,01 → max(2, 2) = 2.
    assert op.tripulacion(8, 8, 7) == op.tripulacion(8.01, 8, 7) == 2
    assert op.tripulacion(7, 8, 7) == 1      # ⌈7/7⌉ = 1 exacto: un conductor justo en J_ef
    assert op.tripulacion(18, 8, 7) == 3     # max(2, ⌈2,57⌉ = 3) = 3: h = 6 ≤ 7


def test_tripulacion_de_tres_solo_por_encima_de_dos_jornadas_efectivas():
    # SUPUESTO k ≥ 3 [DECIDIDO, Camila, 27-nov] (nota de jornada_efectiva_h en el YAML), J_ef = 7, umbral 8:
    # t = 14    → max(2, ⌈14/7⌉ = 2) = 2: dos conductores justo en J_ef (h = 7).
    # t = 14,01 → max(2, ⌈2,0014⌉ = 3) = 3: con 2 cada uno manejaría 7,005 h > 7.
    # t = 15    → max(2, ⌈2,14⌉ = 3) = 3; h = 15/3 = 5; L = ⌊7/5⌋ = ⌊1,4⌋ = 1.
    assert op.tripulacion(14, 8, 7) == 2
    assert op.tripulacion(14.01, 8, 7) == 3
    assert op.tripulacion(15, 8, 7) == 3
    assert 15 / op.tripulacion(15, 8, 7) == pytest.approx(5.0)
    assert op.piernas_por_conductor(15, 3, 7) == 1


def test_horas_al_volante_nunca_superan_la_jornada_efectiva_ni_la_semanal():
    # Invariante de (5a) en una rejilla fina de t ∈ (0, 24] h: h = t/k ≤ J_ef, L = ⌊J_ef/h⌋ ≥ 1, y lo que maneja un conductor
    # en un día (h · L) cabe en J_ef, así que en la semana h · L · (7 − s) ≤ J_ef · 6 = 42 h.
    for j_ef in (7.0, 6.0):
        for i in range(1, 2401):
            t = i / 100
            k = op.tripulacion(t, 8, j_ef)
            h = t / k
            n_piernas = op.piernas_por_conductor(t, k, j_ef)
            assert h <= j_ef + 1e-9 and n_piernas >= 1, (t, j_ef)
            assert h * n_piernas <= j_ef + 1e-9, (t, j_ef)
            assert h * n_piernas * (7 - 1) <= 42 + 1e-9, (t, j_ef)
            assert k >= op.tripulacion_norma(t, 8), t   # nunca menos tripulación de la que pide la norma


def test_piernas_cuentan_las_vacias_de_reposicion():
    # P = 2 · max(n, n'): 2 · max(5, 8) = 16 (no 5 + 8 = 13); un sentido vacío: 2 · max(0, 8) = 16; 0 y 0 → 0
    assert op.piernas_dia(5, 8) == 16
    assert op.piernas_dia(0, 8) == 16
    assert op.piernas_dia(0, 0) == 0


def test_piernas_por_conductor_indivisibles():
    # L = ⌊ J_ef / (t / k) ⌋ con J_ef = 7 (con k de `tripulacion`, h ≤ J_ef y L ≥ 1 siempre):
    assert op.piernas_por_conductor(10, 2, 7) == 1    # Bogotá–Cali: h = 10/2 = 5;  ⌊7/5⌋ = ⌊1,4⌋ = 1
    assert op.piernas_por_conductor(4, 1, 7) == 1     # Bogotá–Sogamoso: ⌊7/4⌋ = ⌊1,75⌋ = 1 (no 1,75 «continuas»)
    assert op.piernas_por_conductor(1.5, 1, 7) == 4   # Pasto–Ipiales: ⌊7/1,5⌋ = ⌊4,67⌋ = 4
    assert op.piernas_por_conductor(2, 1, 7) == 3     # ⌊7/2⌋ = ⌊3,5⌋ = 3
    assert op.piernas_por_conductor(7.5, 2, 7) == 1   # t = 7,5 con k = 2: h = 3,75; ⌊1,87⌋ = 1


def test_piernas_por_conductor_rechaza_pierna_mas_larga_que_la_jornada_efectiva():
    # h = 7,5 / 1 = 7,5 > J_ef = 7 → ⌊0,93⌋ = 0 piernas: un conductor no cubre la pierna. Con k de `tripulacion` nunca
    # ocurre; si alguien pasa otro k, error claro.
    with pytest.raises(ValueError, match="jornada_efectiva_h"):
        op.piernas_por_conductor(7.5, 1, 7)
    with pytest.raises(ValueError, match="jornada_efectiva_h"):
        op.piernas_por_conductor(8, 1, 7)             # t = 8 con k = 1: 8 h > 7 h


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


def test_un_despacho_por_sentido_lo_cubre_un_conductor():
    # 1 despacho por sentido, t = 2 h: P = 2 · max(1, 1) = 2; L = ⌊7/2⌋ = 3 → ⌈2 / 3⌉ = 1 conductor en servicio
    # (4 h de conducción ≤ 7 h).
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


def test_nomina_semanal_caso_a_mano():
    # (5b) N* = ⌈ max(max_d C, Σ_d C / (7 − s)) / (1 − a) ⌉, s = 1:
    # C = [10, 10, 10, 10, 10, 10, 0], a = 0: max = 10; 60 / 6 = 10 → N* = 10 (la diaria (5b) da ⌈10 · 7/6⌉ = 12).
    assert op.nomina_semanal_minima([10, 10, 10, 10, 10, 10, 0], 0.0, 1) == 10
    assert op.conductores_nomina(10, 0.0, 1) == 12
    # 7 días de 10: 70 / 6 = 11,67 → 12 (aquí coincide con la diaria: la semana está llena)
    assert op.nomina_semanal_minima([10] * 7, 0.0, 1) == 12
    # pico de un día: max = 20 domina a 50 / 6 = 8,33 → 20 (todos trabajan ese día)
    assert op.nomina_semanal_minima([20, 5, 5, 5, 5, 5, 5], 0.0, 1) == 20
    # con ausentismo a = 0,09: 10 / 0,91 = 10,99 → 11
    assert op.nomina_semanal_minima([10, 10, 10, 10, 10, 10, 0], 0.09, 1) == 11
    # s = 2: 60 / 5 = 12 > 10 → 12
    assert op.nomina_semanal_minima([10, 10, 10, 10, 10, 10, 0], 0.0, 2) == 12
    assert op.nomina_semanal_minima([0] * 7, 0.09, 1) == 0
    # semana incompleta (4 días con datos): se calcula con lo que hay → 40 / 6 = 6,67; max 10 → 10 (cota inferior)
    assert op.nomina_semanal_minima([10, 10, 10, 10], 0.0, 1) == 10
    with pytest.raises(ValueError, match="7"):
        op.nomina_semanal_minima([1] * 8, 0.0, 1)


def _cubre_con_descansos(c: tuple[int, ...], n: int, s: int) -> bool:
    """Construye turnos para n conductores con s días libres cada uno (asignación «envolvente» de McNaughton: se reparten
    los huecos libres n − C_d de cada día, en orden, entre los conductores 0, 1, …, n−1, 0, 1, …) y comprueba que cada
    conductor descansa s días DISTINTOS y que cada día trabajan al menos C_d.

    Verifica la fórmula de N* contra una construcción explícita: si devuelve True, los turnos existen (suficiencia, por
    construcción). Las dos ramas que devuelven False antes de construir son justo las dos condiciones necesarias
    (n ≥ max_d C_d y n · s ≤ Σ_d (n − C_d), es decir n · (7 − s) ≥ Σ_d C_d con 7 días), así que un False con N* − 1
    prueba que N* − 1 es infactible."""
    if n < max(c):
        return False
    libres = [d for d in range(len(c)) for _ in range(n - c[d])]   # huecos libres, día por día
    if len(libres) < n * s:
        return False
    descansos = [set() for _ in range(n)]
    for i, dia in enumerate(libres[: n * s]):
        descansos[i % n].add(dia)
    trabajan = [sum(dia not in descansos[j] for j in range(n)) for dia in range(len(c))]
    return all(len(dd) == s for dd in descansos) and all(t >= cd for t, cd in zip(trabajan, c, strict=True))


def test_nomina_semanal_es_la_minima_factible_en_todas_las_semanas_pequenas():
    # Invariante (a = 0): para TODAS las semanas con C_d ∈ {0, …, 3} (4^7 = 16.384 casos) y s ∈ {1, 2}, con N* hay turnos
    # que dan a cada conductor s días libres y cubren cada día, y con N* − 1 no. N* ≤ nómina diaria (5b) con C = max_d C_d.
    for s in (1, 2):
        for c in itertools.product(range(4), repeat=7):
            n = op.nomina_semanal_minima(list(c), 0.0, s)
            assert _cubre_con_descansos(c, n, s), (c, s, n)
            if n > 0:
                assert not _cubre_con_descansos(c, n - 1, s), (c, s, n)
            assert n <= op.conductores_nomina(max(c), 0.0, s)


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
    ruta = {"tiempo_ciclo_h": 9.0, "tiempo_recorrido_h": 4.0, "fraccion_demanda_en_origen": 1.0,
            "multiplicador_ocupacion": 1.0}
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
    assert list(out["conductores_servicio"]) == [16, 16]
    assert list(out["conductores"]) == [21, 21]
    # pasos de (5a) con las funciones (no son columnas de la salida): k = 1, P = 16, L = 1
    assert (op.tripulacion(4.0, 8.0, 7.0), op.piernas_dia(5, 8), op.piernas_por_conductor(4.0, 1, 7.0)) == (1, 16, 1)
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
    assert op.tripulacion(10.0, 8.0, 7.0) == 2
    assert list(out["conductores_servicio"]) == [32, 32]
    assert list(out["conductores"]) == [42, 42]


def test_dimensionar_ocupacion_por_ruta_con_multiplicador_y_tope_1():
    # (2) ρ_r = min(1, ρ · m_r), ρ = 0,8:
    # A-B: m = 0,5 → ρ_r = 0,4; cap_ef 30 → 12 útiles; 100 / 12 = 8,33 → 9 despachos
    # B-A: m = 1,5 → 0,8 · 1,5 = 1,2 → tope 1 (no se planea por encima de la capacidad); cap_ef 24; 150 / 24 = 6,25 → 7
    # vehículos ⌈max(9, 7) / 2⌉ = ⌈4,5⌉ = 5
    p = _params()
    p["por_ruta"]["A-B"]["multiplicador_ocupacion"] = 0.5
    p["por_ruta"]["B-A"]["multiplicador_ocupacion"] = 1.5
    assert op.ocupacion_ruta(0.8, 0.5) == pytest.approx(0.4)
    assert op.ocupacion_ruta(0.8, 1.5) == 1.0
    assert op.ocupacion_ruta(0.8, 1.0) == pytest.approx(0.8)
    out = op.dimensionar(_ida_y_regreso(), p).set_index("ruta_id")
    assert (out.loc["A-B", "despachos"], out.loc["B-A", "despachos"]) == (9, 7)
    assert list(out["vehiculos"]) == [5, 5]


def test_dimensionar_no_expone_columnas_intermedias():
    # Contrato §5.4: la salida es la entrada + capacidad, despachos, vehículos y conductores; k, P, L y ρ_r se quedan
    # dentro de las funciones [DECIDIDO, Camila, 27-nov].
    out = op.dimensionar(_ida_y_regreso(), _params())
    assert not {"tripulacion", "piernas", "piernas_por_conductor", "ocupacion_ruta"} & set(out.columns)
    corr = op.flota_por_corredor(out)
    assert not {"piernas", "piernas_por_conductor"} & set(corr.columns)


@pytest.mark.parametrize("m", [0.0, -1.0, float("nan"), float("inf")])
def test_multiplicador_de_ocupacion_fuera_de_rango_da_error(m):
    p = _params()
    p["por_ruta"]["A-B"]["multiplicador_ocupacion"] = m
    with pytest.raises(ValueError, match="multiplicador_ocupacion"):
        op.dimensionar(_ida_y_regreso(), p)


def test_dimensionar_recorrido_de_7_5_h_lleva_dos_conductores():
    # (5a) t = 7,5, T = 16, J_ef = 7: k = max(1, ⌈7,5/7⌉) = 2; h = 3,75; L = ⌊7/3,75⌋ = 1; despachos 5 y 8 → P = 16
    # C_serv = ⌈2 · 16 / 1⌉ = 32.
    p = _params()
    for r in ("A-B", "B-A"):
        p["por_ruta"][r].update(tiempo_recorrido_h=7.5, tiempo_ciclo_h=16.0)
    out = op.dimensionar(_ida_y_regreso(), p)
    assert list(out["conductores_servicio"]) == [32, 32]


def test_dimensionar_sin_salto_entre_8_y_8_01_horas():
    # t = 8 (k_norma = 1, pero ⌈8/7⌉ = 2) y t = 8,01 (k_norma = 2): mismo k = 2, mismo L = 1, mismos conductores.
    # Mismo ciclo (18 h) para aislar el efecto del recorrido.
    salidas = []
    for t in (8.0, 8.01):
        p = _params()
        for r in ("A-B", "B-A"):
            p["por_ruta"][r].update(tiempo_recorrido_h=t, tiempo_ciclo_h=18.0)
        out = op.dimensionar(_ida_y_regreso(), p)
        salidas.append(out[["vehiculos", "conductores_servicio", "conductores"]])
    pd.testing.assert_frame_equal(salidas[0], salidas[1])
    assert list(salidas[0]["conductores_servicio"]) == [32, 32]   # ⌈2 · 16 / 1⌉


def test_dimensionar_corredor_corto_varias_piernas_por_conductor():
    # Pasto–Ipiales: t = 1,5, T = 3,5; despachos 5 y 8 → P = 16; L = ⌊7/1,5⌋ = 4 → C_serv = 4;
    # C_nom = ⌈4 / 0,91 · 7/6⌉ = ⌈5,13⌉ = 6. Vueltas 18/3,5 = 5,14 → veh = ⌈8 / 5,14⌉ = ⌈1,56⌉ = 2.
    p = _params()
    for r in ("A-B", "B-A"):
        p["por_ruta"][r].update(tiempo_recorrido_h=1.5, tiempo_ciclo_h=3.5)
    out = op.dimensionar(_ida_y_regreso(), p)
    assert list(out["vehiculos"]) == [2, 2]
    assert list(out["conductores_servicio"]) == [4, 4]
    assert list(out["conductores"]) == [6, 6]


def test_conductores_no_dependen_de_las_horas_de_operacion():
    # C_serv y C_nom cuentan conducción, no dependen de H; los vehículos no crecen con H: H = 18 → v = 2 → 4 veh; H = 9 → v = 1 → 8 veh; H = 24 → v = 2,67 → ⌈3,0⌉ = 3 veh.
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
    # J_ef · (7 − s) = 7 · 6 = 42 ≤ 42 (igualdad permitida).
    op.dimensionar(_ida_y_regreso(), _params(jornada_efectiva_h=7.0, dias_descanso_semana=1))


def test_dos_dias_de_descanso_por_debajo_del_limite_son_validos():
    # s = 2: 6 · 5 = 30 h < 42 h.
    op.dimensionar(_ida_y_regreso(), _params(jornada_efectiva_h=6.0, dias_descanso_semana=2))


def test_tripulacion_cubre_cualquier_pierna_dentro_de_la_jornada_efectiva():
    # t = 8 → k = 2, h = 4 (con k = 1 serían 8 h > J_ef = 7 y 8 · 6 = 48 > 42 h/semana); t = 18 → k = 3, h = 6 ≤ 7.
    # Despachos 5 y 8 → P = 16; L = ⌊7/4⌋ = 1 y ⌊7/6⌋ = 1 → C_serv = ⌈2 · 16⌉ = 32 y ⌈3 · 16⌉ = 48.
    for t, ciclo, k, h, c_serv in ((8.0, 17.0, 2, 4.0, 32), (18.0, 40.0, 3, 6.0, 48)):
        p = _params()
        for r in ("A-B", "B-A"):
            p["por_ruta"][r].update(tiempo_recorrido_h=t, tiempo_ciclo_h=ciclo)
        out = op.dimensionar(_ida_y_regreso(), p)
        assert op.tripulacion(t, 8.0, 7.0) == k
        assert t / k == pytest.approx(h) and h <= p["globales"]["jornada_efectiva_h"]
        assert list(out["conductores_servicio"]) == [c_serv, c_serv]


def test_tripulacion_y_piernas_de_la_config_actual(cfg_operacion):
    # J_ef = 7, umbral 8: Bogotá–Cali t = 10 → k = 2, h = 5, L = 1; Bogotá–Sogamoso t = 4 → k = 1, L = ⌊1,75⌋ = 1;
    # Pasto–Ipiales t = 1,5 → k = 1, L = ⌊4,67⌋ = 4.
    esperado = {10: (2, 1), 4: (1, 1), 1.5: (1, 4)}
    g = cfg_operacion["operacion"]
    for ruta, p in g["por_ruta"].items():
        t = p["tiempo_recorrido_h"]
        k = op.tripulacion(t, g["umbral_segundo_conductor_h"], g["jornada_efectiva_h"])
        assert (k, op.piernas_por_conductor(t, k, g["jornada_efectiva_h"])) == esperado[t], ruta


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


def test_nomina_semanal_por_corredor_lunes_a_domingo():
    # Corredor A-B | B-A del jueves 2022-12-01 al domingo 2022-12-11 (11 días). Demanda 100/150 → C_serv = 16 por día;
    # demanda 0 → 0. Semana 1 (lun 28-nov..dom 4-dic): solo 4 días con datos (jue–dom) → incompleta;
    # semana 2 (lun 5..dom 11): C = [16, 16, 16, 16, 16, 16, 0] → max 16; 96 / 6 = 16 → N* = ⌈16 / 0,91⌉ = ⌈17,58⌉ = 18
    # (nómina diaria (5b) = 21). Semana 1: C = [16, 16, 16, 16]: max 16; 64/6 = 10,67 → ⌈16 / 0,91⌉ = 18 (cota inferior).
    filas = []
    for dia in pd.date_range("2022-12-01", "2022-12-11"):
        cero = dia == pd.Timestamp("2022-12-11")
        filas += [("A-B", dia, 0 if cero else 100), ("B-A", dia, 0 if cero else 150)]
    corr = op.flota_por_corredor(op.dimensionar(_demanda(filas), _params()))
    sem = op.nomina_semanal(corr, ausentismo=0.09, dias_descanso_semana=1).set_index("semana_inicio")
    assert list(sem.index) == [pd.Timestamp("2022-11-28"), pd.Timestamp("2022-12-05")]
    s1, s2 = sem.loc[pd.Timestamp("2022-11-28")], sem.loc[pd.Timestamp("2022-12-05")]
    assert (s1["dias_con_datos"], bool(s1["semana_completa"])) == (4, False)
    assert (s2["dias_con_datos"], bool(s2["semana_completa"])) == (7, True)
    assert s2["semana_fin"] == pd.Timestamp("2022-12-11")
    assert (s2["max_conductores_servicio"], s2["suma_conductores_servicio"]) == (16, 96)
    assert s2["nomina_semanal"] == 18 and s2["max_nomina_diaria"] == 21
    assert s1["nomina_semanal"] == 18
    assert (sem["nomina_semanal"] <= sem["max_nomina_diaria"]).all()


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
    assert op.capacidad_supuesta("CAMIONETA", 9.0) == 9      # ⌈9⌉ = 9: no sube a 10
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


def test_multiplicadores_de_ocupacion_por_ruta_a_mano():
    # Mismo caso que ρ*: R1 10 cargas llenas / 20 observados → ρ_R1 = 0,5; R2 5 / 5 → ρ_R2 = 1,0; ρ* = 15/25 = 0,6.
    # m_r = ρ_r_obs / ρ*: m_R1 = 0,5 / 0,6 = 0,8333; m_R2 = 1 / 0,6 = 1,6667.
    demanda = _demanda([("R1", "2022-12-01", 400), ("R2", "2022-12-01", 50)])
    obs = _demanda([("R1", "2022-12-01", 20), ("R2", "2022-12-01", 5), ("R2", "2022-12-02", 99)]).rename(
        columns={"demanda": "despachos"})
    f, cap = {"R1": 0.5, "R2": 1.0}, {"R1": 20.0, "R2": 10.0}
    m = op.multiplicadores_ocupacion(demanda, obs, f, cap, 0.6)
    assert m == {"R1": pytest.approx(0.5 / 0.6), "R2": pytest.approx(1 / 0.6)}


def test_multiplicadores_reproducen_cada_ruta():
    # Invariante: con ρ_r = ρ* · m_r, Σ_d f·D / (cap_ef · ρ_r) = despachos observados de CADA ruta (antes del techo).
    # Cargas llenas: R1 0,5 · 400 / 20 + 0,5 · 260 / 20 = 10 + 6,5 = 16,5; R2 1 · 50 / 10 = 5; ρ* = 21,5 / 36 = 0,5972.
    # Con ρ* global solo el total coincide: R1 16,5 / 0,5972 = 27,63 ≠ 31 y R2 5 / 0,5972 = 8,37 ≠ 5 (suman 36).
    demanda = _demanda([("R1", "2022-12-01", 400), ("R1", "2022-12-02", 260), ("R2", "2022-12-01", 50)])
    obs = _demanda([("R1", "2022-12-01", 20), ("R1", "2022-12-02", 11), ("R2", "2022-12-01", 5)]).rename(
        columns={"demanda": "despachos"})
    f, cap = {"R1": 0.5, "R2": 1.0}, {"R1": 20.0, "R2": 10.0}
    rho = op.ocupacion_calibrada(demanda, obs, f, cap)
    m = op.multiplicadores_ocupacion(demanda, obs, f, cap, rho)
    for r, observados in (("R1", 31), ("R2", 5)):
        g = demanda[demanda["ruta_id"] == r]
        continuo = sum(f[r] * d / (cap[r] * rho * m[r]) for d in g["demanda"])
        assert continuo == pytest.approx(observados)
    # Identidad: la media de m_r ponderada por despachos observados es 1, porque obs_r · ρ* · m_r = cargas_r y
    # Σ_r cargas_r = ρ* · Σ_r obs_r  ⇒  Σ_r obs_r · m_r = Σ_r obs_r (31 · m_R1 + 5 · m_R2 = 36).
    assert 31 * m["R1"] + 5 * m["R2"] == pytest.approx(36.0)
    assert 16.5 / rho == pytest.approx(27.628, abs=1e-3) and 5 / rho == pytest.approx(8.372, abs=1e-3)


# Dos corredores: {R1, R2} y {R3, R4}.
REGRESOS_4 = {"R1": "R2", "R2": "R1", "R3": "R4", "R4": "R3"}


def _caso_corredores():
    # Cargas llenas A = f · D / cap_ef y despachos ORIGEN observados O, un día:
    #   R1: 0,5 · 400 / 20 = 10, O = 20;  R2: 1 · 50 / 10 = 5, O = 5    → corredor 1: 15 / 25 = 0,6
    #   R3: 1 · 90 / 10 = 9,    O = 10;  R4: 1 · 30 / 10 = 3, O = 5    → corredor 2: 12 / 15 = 0,8
    #   ρ* = (15 + 12) / (25 + 15) = 27 / 40 = 0,675
    demanda = _demanda([("R1", "2022-12-01", 400), ("R2", "2022-12-01", 50), ("R3", "2022-12-01", 90),
                        ("R4", "2022-12-01", 30)])
    obs = _demanda([("R1", "2022-12-01", 20), ("R2", "2022-12-01", 5), ("R3", "2022-12-01", 10),
                    ("R4", "2022-12-01", 5)]).rename(columns={"demanda": "despachos"})
    f = {"R1": 0.5, "R2": 1.0, "R3": 1.0, "R4": 1.0}
    cap = {"R1": 20.0, "R2": 10.0, "R3": 10.0, "R4": 10.0}
    return demanda, obs, f, cap


def test_multiplicadores_por_corredor_a_mano():
    # m_c = (Σ_{r∈c} A_r / Σ_{r∈c} O_r) / ρ*: corredor 1 0,6 / 0,675 = 0,8889 (8/9); corredor 2 0,8 / 0,675 = 1,1852
    # (32/27); los dos sentidos de un corredor llevan el mismo m. Por ruta serían R1 0,5/0,675, R2 1/0,675, etc.
    demanda, obs, f, cap = _caso_corredores()
    rho = op.ocupacion_calibrada(demanda, obs, f, cap)
    assert rho == pytest.approx(0.675)
    m = op.multiplicadores_ocupacion_corredor(demanda, obs, f, cap, rho, REGRESOS_4)
    assert m == {"R1": pytest.approx(8 / 9), "R2": pytest.approx(8 / 9),
                 "R3": pytest.approx(32 / 27), "R4": pytest.approx(32 / 27)}
    # Identidad: Σ_c O_c · m_c = Σ O (25 · 8/9 + 15 · 32/27 = 22,22 + 17,78 = 40)
    assert 25 * m["R1"] + 15 * m["R3"] == pytest.approx(40.0)
    # Invariante: con ρ* · m_c cada CORREDOR reproduce la suma de sus despachos observados (no cada sentido):
    # corredor 1: (10 + 5) / (0,675 · 8/9) = 15 / 0,6 = 25 = 20 + 5; pero R1 solo 10 / 0,6 = 16,67 ≠ 20.
    assert (10 + 5) / (rho * m["R1"]) == pytest.approx(25.0)
    assert 10 / (rho * m["R1"]) == pytest.approx(16.667, abs=1e-3)


def test_multiplicador_por_corredor_exige_el_regreso():
    demanda, obs, f, cap = _caso_corredores()
    with pytest.raises(ValueError, match="R3"):
        op.multiplicadores_ocupacion_corredor(demanda, obs, f, cap, 0.675, {"R1": "R2", "R2": "R1"})

def test_multiplicador_sin_despachos_observados_da_error_claro():
    demanda = _demanda([("R1", "2022-12-01", 400), ("R2", "2022-12-01", 50)])
    obs = _demanda([("R1", "2022-12-01", 20)]).rename(columns={"demanda": "despachos"})
    with pytest.raises(ValueError, match="R2"):
        op.multiplicadores_ocupacion(demanda, obs, {"R1": 0.5, "R2": 1.0}, {"R1": 20.0, "R2": 10.0}, 0.6)


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


def test_reproduccion_de_la_flota_por_corredor_a_mano():
    # (ii) Σ_d max(desp_r, desp_r') / Σ_d max(obs_r, obs_r') por corredor: lo que fija vehículos y conductores.
    # Modelo (caso a mano de dimensionar): 1-dic A-B 5, B-A 8; 2-dic demanda 0 → 0 y 0.  Σ max = 8 + 0 = 8.
    # Observado: 1-dic A-B 6, B-A 4; 2-dic A-B 3, B-A sin fila (= 0).                  Σ max = 6 + 3 = 9.
    # → 8 / 9 = 88,9 %, aunque la suma de despachos coincide (5 + 8 = 13 = 6 + 4 + 3): (i) y (ii) son distintas.
    tabla = op.dimensionar(_demanda([("A-B", "2022-12-01", 100), ("B-A", "2022-12-01", 150),
                                     ("A-B", "2022-12-02", 0), ("B-A", "2022-12-02", 0)]), _params())
    obs = _demanda([("A-B", "2022-12-01", 6), ("B-A", "2022-12-01", 4), ("A-B", "2022-12-02", 3)]).rename(
        columns={"demanda": "despachos"})
    rep = op.reproduccion_flota_corredor(tabla, obs)
    assert rep == {"A-B | B-A": {"modelo": 8, "observado": 9, "porcentaje": pytest.approx(800 / 9)}}
    assert op.reproduccion_despachos(tabla, obs)["total"]["porcentaje"] == pytest.approx(100.0)


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
    # Contrato §5.4: los costos se exigen en los parámetros pero `dimensionar` no los usa (los usa negocio 3, CA-6); la
    # nota lo declara para que la app no los presente como entrada del dimensionamiento.
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


def test_multiplicadores_reales_reproducen_cada_ruta_en_la_ventana(cfg_operacion, calibracion):
    # (2) m_r se calcula al ejecutar (no está en el YAML) y, con ρ = ρ*, cada ruta reproduce sus despachos ORIGEN de la
    # ventana de calibración: 100 % + el efecto del techo diario (≤ 1 despacho por ruta y día → < 2 % aquí).
    assert set(calibracion["multiplicador_ocupacion"]) == set(cfg_operacion["operacion"]["por_ruta"])
    assert all(m > 0 and math.isfinite(m) for m in calibracion["multiplicador_ocupacion"].values())
    for p in cfg_operacion["operacion"]["por_ruta"].values():
        assert "multiplicador_ocupacion" not in p
    cfg = apply_overrides(cfg_operacion, [f"operacion.ocupacion_objetivo={calibracion['ocupacion_calibrada']}"])
    params = op.parametros_desde_config(cfg, calibracion, op.leer_regresos(RUTAS))
    tabla = op.dimensionar(op._ventana(calibracion["demanda_train"], *calibracion["ventana_fraccion"]), params)
    rep = op.reproduccion_despachos(tabla, calibracion["despachos_origen_train"])
    for r in cfg_operacion["operacion"]["por_ruta"]:
        assert 100.0 <= rep[r]["porcentaje"] < 102.0, (r, rep[r])


def test_multiplicador_por_defecto_es_por_ruta_y_el_de_corredor_se_reporta(cfg_operacion, calibracion):
    # [DECIDIDO, Camila, 27-nov] Defecto `calibracion.multiplicador: por_ruta`; m por corredor se calcula siempre como
    # sensibilidad. Las dos rutas de un corredor comparten m_c, y m_c queda entre los m_r de sus dos sentidos (es su
    # media ponderada por despachos observados: m_c = (O_r · m_r + O_r' · m_r') / (O_r + O_r')).
    assert cfg_operacion["calibracion"]["multiplicador"] == "por_ruta"
    m_r, m_c = calibracion["multiplicador_ocupacion_por_ruta"], calibracion["multiplicador_ocupacion_por_corredor"]
    assert calibracion["multiplicador_ocupacion"] == m_r
    regresos = op.leer_regresos(RUTAS)
    for r, r2 in regresos.items():
        assert m_c[r] == m_c[r2]
        assert min(m_r[r], m_r[r2]) - 1e-12 <= m_c[r] <= max(m_r[r], m_r[r2]) + 1e-12, r
    # y la variante se elige por config sin tocar la salida por defecto
    cfg = apply_overrides(cfg_operacion, ["calibracion.multiplicador=por_corredor"])
    otra = op.calibrar(cfg, pd.read_parquet(DETALLE), pd.read_parquet(DIARIA), regresos)
    assert otra["multiplicador_ocupacion"] == m_c
    params = op.parametros_desde_config(cfg, otra, regresos)
    assert {r: p["multiplicador_ocupacion"] for r, p in params["por_ruta"].items()} == m_c
    glob = op.parametros_desde_config(cfg, otra, regresos, variante="global")
    assert all(p["multiplicador_ocupacion"] == 1.0 for p in glob["por_ruta"].values())


def test_variante_de_multiplicador_desconocida_da_error(cfg_operacion):
    cfg = apply_overrides(cfg_operacion, ["calibracion.multiplicador=por_dia"])
    with pytest.raises(ValueError, match="calibracion.multiplicador"):
        op.calibrar(cfg, pd.read_parquet(DETALLE), pd.read_parquet(DIARIA), op.leer_regresos(RUTAS))


def _alterar_desde(detalle: pd.DataFrame, diaria: pd.DataFrame, desde: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cambia TODO lo de fecha >= `desde` en los datos reales (pasajeros, despachos, clase y sin_registro)."""
    det, dia = detalle.copy(), diaria.copy()
    m = pd.to_datetime(det["fecha"]) >= pd.Timestamp(desde)
    det.loc[m, "despachos"] = det.loc[m, "despachos"] * 7 + 3
    det.loc[m, "pasajeros"] = det.loc[m, "pasajeros"] * 11 + 5
    det.loc[m & (det["tipo_despacho"] == op.ORIGEN), "clase_vehiculo"] = "BUS"
    m = pd.to_datetime(dia["fecha"]) >= pd.Timestamp(desde)
    dia.loc[m, "pasajeros"] = dia.loc[m, "pasajeros"] * 13 + 1
    dia.loc[m, "sin_registro"] = False
    return det, dia


def _calibrado(c: dict) -> dict:
    claves = ("composicion", "fraccion", "capacidad_efectiva", "ocupacion_calibrada", "multiplicador_ocupacion",
              "multiplicador_ocupacion_por_ruta", "multiplicador_ocupacion_por_corredor")
    return {k: c[k] for k in claves if k in c}


def test_calibracion_real_no_cambia_con_datos_posteriores_al_fin_de_entrenamiento(cfg_operacion, calibracion):
    # Fuga: alterar TODO lo posterior a fin_entrenamiento (2023) no mueve π, f, cap_ef, ρ*, m_r ni m_c.
    det, dia = _alterar_desde(pd.read_parquet(DETALLE), pd.read_parquet(DIARIA), "2023-01-01")
    otra = op.calibrar(cfg_operacion, det, dia, op.leer_regresos(RUTAS))
    assert _calibrado(otra) == _calibrado(calibracion)


@pytest.fixture(scope="module")
def validacion(cfg_operacion) -> dict:
    return op.validar_fuera_de_ventana(cfg_operacion, pd.read_parquet(DETALLE), pd.read_parquet(DIARIA),
                                       op.leer_regresos(RUTAS))


def test_ventanas_de_validacion_no_se_solapan_y_caben_en_train(cfg_operacion):
    v = cfg_operacion["calibracion"]["validacion"]
    cal, prueba = [pd.Timestamp(x) for x in v["calibrar"]], [pd.Timestamp(x) for x in v["probar"]]
    assert cal[0] <= cal[1] < prueba[0] <= prueba[1] <= pd.Timestamp(cfg_operacion["datos"]["fin_entrenamiento"])
    assert cal[0] >= pd.Timestamp(cfg_operacion["datos"]["inicio_entrenamiento"])


def test_validacion_no_mira_la_ventana_de_prueba(cfg_operacion, validacion):
    # Fuga en la validación: lo calibrado (π, cap, f, ρ*, m_r, m_c) solo puede usar fecha <= fin de la ventana de
    # calibración.
    # Se alteran todos los datos desde el inicio de la ventana de prueba (nov-2022) y nada calibrado cambia.
    det, dia = _alterar_desde(pd.read_parquet(DETALLE), pd.read_parquet(DIARIA),
                              cfg_operacion["calibracion"]["validacion"]["probar"][0])
    otra = op.validar_fuera_de_ventana(cfg_operacion, det, dia, op.leer_regresos(RUTAS))
    assert _calibrado(otra) == _calibrado(validacion)
    assert set(_calibrado(validacion)) >= {"multiplicador_ocupacion_por_ruta", "multiplicador_ocupacion_por_corredor"}
    assert otra["capacidades"] == validacion["capacidades"]
    # y la reproducción sí cambia en las tres variantes (la prueba mira la ventana de prueba de verdad)
    for variante in ("global", "por_ruta", "por_corredor"):
        assert otra["reproduccion"][variante] != validacion["reproduccion"][variante], variante


def test_validacion_fuera_de_ventana_mejora_con_el_multiplicador(validacion):
    # Calibrado en sep–oct 2022, probado en nov–dic 2022. Salvo 11001-15759 (cambio de régimen del tránsito desde el
    # 8-nov-2022), ρ·m_r queda más cerca del 100 % que ρ global en cada ruta.
    glob = validacion["reproduccion"]["global"]["despachos"]
    por_ruta = validacion["reproduccion"]["por_ruta"]["despachos"]
    for r in glob:
        if r in ("total", "11001-15759"):
            continue
        assert abs(por_ruta[r]["porcentaje"] - 100) < abs(glob[r]["porcentaje"] - 100), r
        assert 95 <= por_ruta[r]["porcentaje"] <= 110, r
    assert validacion["ventana_calibracion"] == ["2022-09-01", "2022-10-31"]
    assert validacion["ventana_prueba"] == ["2022-11-01", "2022-12-31"]


def test_validacion_fuera_de_ventana_tres_variantes_reproduce_al_verificador(validacion):
    # Cifras medidas por separado por el verificador matemático de CA-3d (27-nov), con su propio script:
    # (i) total de despachos ORIGEN: ρ global 108,0 %, ρ · m_ruta 115,8 %;
    # (ii) Σ_d max(desp, desp') / Σ_d max(obs, obs') del corredor 11001-15759: ρ · m_ruta 171,4 %, ρ · m_corredor 135,2 %.
    rep = validacion["reproduccion"]
    assert set(rep) == {"global", "por_ruta", "por_corredor"}
    assert rep["global"]["despachos"]["total"]["porcentaje"] == pytest.approx(108.0, abs=0.05)
    assert rep["por_ruta"]["despachos"]["total"]["porcentaje"] == pytest.approx(115.8, abs=0.05)
    sog = "11001-15759 | 15759-11001"
    assert rep["por_ruta"]["flota_corredor"][sog]["porcentaje"] == pytest.approx(171.4, abs=0.05)
    assert rep["por_corredor"]["flota_corredor"][sog]["porcentaje"] == pytest.approx(135.2, abs=0.05)
    for variante in rep.values():
        assert set(variante["flota_corredor"]) == {"11001-15759 | 15759-11001", "11001-76001 | 76001-11001",
                                                   "52001-52356 | 52356-52001"}


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
    for ruta, pr in c["por_ruta"].items():  # f y m_r salen de los datos de train: fuente con la ventana reciente
        f = pr["fraccion_demanda_en_origen"]
        assert f["valor"] == calibracion["fraccion"][ruta]
        assert "2022-11-01" in f["fuente"] and d["fin_entrenamiento"] in f["fuente"]
        m = pr["multiplicador_ocupacion"]
        assert m["valor"] == calibracion["multiplicador_ocupacion"][ruta]
        assert "2022-11-01" in m["fuente"] and d["fin_entrenamiento"] in m["fuente"]
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
    cal = resumen["calibracion"]
    assert cal["variante_multiplicador"] == "por_ruta"
    for clave in ("multiplicador_ocupacion", "multiplicador_ocupacion_por_corredor"):
        assert set(cal[clave]) == set(cfg["operacion"]["por_ruta"])
    for bloque in ("reproduccion_dentro_de_ventana", "validacion_fuera_de_ventana"):
        rep = cal[bloque] if bloque == "reproduccion_dentro_de_ventana" else cal[bloque]["reproduccion"]
        for variante in ("global", "por_ruta", "por_corredor"):
            assert set(rep[variante]["despachos"]) == {*cfg["operacion"]["por_ruta"], "total"}
            assert set(rep[variante]["flota_corredor"]) == set(corr["corredor"])
    # [DECIDIDO, Camila, 27-nov] salidas que el contrato no pide
    assert not {"ocupacion_por_ruta_usada", "ocupacion_por_ruta_con_tope_1"} & set(cal)
    assert not {"tripulacion", "piernas", "piernas_por_conductor", "ocupacion_ruta"} & set(tabla.columns)
    # (5b) nómina semanal: una fila por corredor y semana (lunes a domingo); nunca más que la nómina diaria máxima
    sem = pd.read_csv(tmp_path / "nomina_semanal.csv", parse_dates=["semana_inicio", "semana_fin"])
    assert not sem.duplicated(["corredor", "semana_inicio"]).any()
    assert (sem["semana_inicio"].dt.day_of_week == 0).all() and (sem["semana_fin"].dt.day_of_week == 6).all()
    assert sem["dias_con_datos"].between(1, 7).all()
    assert (sem["semana_completa"] == (sem["dias_con_datos"] == 7)).all()
    assert (sem["nomina_semanal"] <= sem["max_nomina_diaria"]).all()
    assert sem.groupby("corredor")["dias_con_datos"].sum().mul(2).sum() == len(tabla)
    assert set(resumen["nomina_semanal_por_corredor"]) == set(corr["corredor"])
    # N* del resumen y del print: máximo de semanas COMPLETAS y, aparte, la cota inferior de las incompletas
    for c, g in sem.groupby("corredor"):
        n = resumen["nomina_semanal_por_corredor"][c]
        completas, incompletas = g.loc[g["semana_completa"], "nomina_semanal"], g.loc[~g["semana_completa"], "nomina_semanal"]
        assert n["max_nomina_semanal_semanas_completas"] == completas.max()
        assert n["cota_inferior_semanas_incompletas"] == incompletas.max()
        assert "max_nomina_semanal" not in n
        assert f"N* semanas completas {completas.max()}" in salida
        assert f"semanas incompletas ≥ {incompletas.max()} (cota inferior)" in salida
