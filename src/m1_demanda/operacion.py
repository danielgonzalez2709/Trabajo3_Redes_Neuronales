"""M1 — dimensionamiento de flota y conductores (CA-3; núcleo §5.4; spec de Camila §3.3; decisiones de Camila, 26-nov).

Notación: r = ruta, r' = su regreso según `rutas.yaml`, {r, r'} = corredor, d = día, c = clase de vehículo.
Las ecuaciones van en el mismo orden que el blog; cada una tiene su caso a mano en tests/test_operacion_m1.py.

    (1) cap_ef(r)  = Σ_c π(r, c) · cap(c)
            π(r, c): participación de la clase c en los despachos de ORIGEN de r en train (los de tránsito repiten el
            mismo vehículo en otra terminal, núcleo §5.1). cap(c): capacidad física SUPUESTA (ver calibración).
            Caso: 0,75 · 30 + 0,25 · 18 = 27.
    (2) desp(r, d) = ⌈ f(r) · D(r, d) / (cap_ef(r) · ρ_r) ⌉,     ρ_r = min(1, ρ · m_r)
            D: demanda (punto o cuantil) en pasajeros/día de la serie (ORIGEN + tránsito, núcleo §5.1).
            f(r): parte de D que sube en la terminal de origen y ocupa silla desde la salida (calibrada).
            ρ ∈ (0, 1]: ocupación objetivo, UN escalar (control de la app y `--set`); por defecto ρ* (calibrada).
            m_r > 0: multiplicador de ocupación POR RUTA (calibrado al ejecutar, no se escribe a mano) [DECIDIDO, Camila,
            26-nov, CA-3d, O1]. El tope 1 impide planear por encima de la capacidad cuando ρ · m_r > 1 (p. ej. --set 0,8).
            Caso: f = 1, m = 1, 100 / (27 · 0,8) = 4,63 → 5;  m = 0,5: 100 / (30 · 0,4) = 8,33 → 9.
    (3) v(r)       = H / T_ciclo(r)
            H: horas de operación al día; T_ciclo = ida + regreso + alistamiento. Es una fracción, sin piso ni mínimo:
            con T_ciclo > H un vehículo cierra menos de un ciclo por día (18 / 22 = 0,818).
    (4) veh(r, d)  = ⌈ max(desp(r, d), desp(r', d)) / v(r) ⌉
            Cada vuelta es una ida Y un regreso: el sentido más cargado manda. Es la flota del CORREDOR: las filas de r
            y r' dan el mismo número y NO se suman (usar `flota_por_corredor`). Caso: ⌈max(5, 8) / 2⌉ = 4.
    (5a) conductores en servicio por piernas, por corredor y día [DECIDIDO, Camila, 26-nov, CA-3c y CA-3d]:
             P_r    = 2 · max(desp(r, d), desp(r', d))
                 piernas del corredor: cada vehículo de (4) hace ida y regreso, así que se cuentan también las piernas
                 VACÍAS de reposición del sentido menos cargado. Caso: 2 · max(5, 8) = 16 (no 5 + 8 = 13).
             k_r    = max(k_norma(t_r), ⌈ t_r / J_ef ⌉),   k_norma = 2 si t_r > 8 h (Res. 315/2013 art. 6), si no 1
                 conductores a bordo (CA-3d, E1). El segundo término asegura h_r ≤ J_ef: sin él, t = 7,5 h daba k = 1 y un
                 conductor manejaba 7,5 h > J_ef = 7 h (7,5 · 6 = 45 h/semana > 42). Casos con J_ef = 7: t = 10 → 2;
                 t = 4 → 1; t = 1,5 → 1; t = 7,5 → 2; t = 8 → 2 y t = 8,01 → 2 (sin salto en el umbral de la norma).
             h_r    = t_r / k_r ≤ J_ef
                 horas al volante de cada conductor en una pierna. SUPUESTO: el relevo que descansa a bordo no consume
                 jornada.
             L_r    = ⌊ J_ef / h_r ⌋ ≥ 1
                 piernas por conductor y día; las piernas son INDIVISIBLES (nadie entrega el bus a mitad de camino).
                 L_r ≥ 1 se sigue de h_r ≤ J_ef (se comprueba como aserción, sin max(1, ·)).
                 Casos con J_ef = 7: Bogotá–Cali h = 5 → 1; Bogotá–Sogamoso h = 4 → 1; Pasto–Ipiales h = 1,5 → 4.
             C_serv = ⌈ k_r · P_r / L_r ⌉
                 Cuenta conducción, no disponibilidad del vehículo: no depende de H. El alistamiento NO se cuenta como
                 trabajo del conductor: es el tiempo del vehículo en terminal entre piernas, que en este supuesto
                 coincide con su descanso; la hora que separa J_ef = 7 de la jornada de 8 h cubre pausas y tareas en
                 terminal. Caso: ⌈1 · 16 / 1⌉ = 16; Bogotá–Cali ⌈2 · 16 / 1⌉ = 32.
    (5b) nómina (a: ausentismo ∈ [0, 1); s = 1 día de descanso semanal, art. 161 CST; se exige J_ef · (7 − s) ≤ jornada
         máxima semanal):
             diaria   C_nom(d) = ⌈ C_serv(d) / (1 − a) · 7 / (7 − s) ⌉
                 columna `conductores` del contrato §5.4 (no cambia). Equivale a suponer que el día d se repite los 7 días
                 de la semana. Caso: ⌈16 / 0,91 · 7/6⌉ = ⌈20,51⌉ = 21.
             semanal  N*(w)    = ⌈ max( max_{d∈w} C_serv(d), Σ_{d∈w} C_serv(d) / (7 − s) ) / (1 − a) ⌉
                 por corredor y semana w (lunes a domingo) [DECIDIDO, Camila, 26-nov, CA-3d, O3]. Es la MENOR nómina con
                 la que hay turnos que cubren cada día y dan s días libres a cada conductor: hace falta N ≥ C_serv(d) cada
                 día y N · (7 − s) ≥ Σ_d C_serv(d); y basta (asignación envolvente de McNaughton de los huecos libres).
                 Caso: C_serv = [10, 10, 10, 10, 10, 10, 0], a = 0 → max(10, 60/6 = 10) = 10 (la diaria da 12).
                 Semanas incompletas (al borde del periodo o con días sin registro): se calcula con los días que hay y es
                 una COTA INFERIOR (los días que faltan solo pueden subir el máximo y la suma).

Calibración con train (nada posterior a `datos.fin_entrenamiento`, núcleo §5.4). Ventana W = últimos
`calibracion.meses_fraccion` meses de train, días con registro en los dos sentidos del corredor:
    f(r)  = Σ_W pasajeros ORIGEN(r) / Σ_W pasajeros (ORIGEN + TRÁNSITO)(r)
    cap(c) = min(máx. del grupo, max(mín. del grupo, ⌈máximo de pasajeros por despacho ORIGEN en train⌉)), grupos del
             Decreto 1079/2015 arts. 2.2.1.4.7.3–4 (está en el YAML; una prueba la recalcula).
    ρ*    = Σ_{r, d∈W} f(r) · D(r, d) / cap_ef(r)  ÷  Σ_{r, d∈W} despachos ORIGEN observados(r, d)
            [DECIDIDO, Camila, 26-nov, CA-3c]. Caso: (0,5 · 400 / 20 + 1 · 50 / 10) / (20 + 5) = 15 / 25 = 0,6.
    ρ_r^obs = Σ_{d∈W} f(r) · D(r, d) / cap_ef(r)  ÷  Σ_{d∈W} despachos ORIGEN observados(r, d)       (misma cuenta, por ruta)
    m_r   = ρ_r^obs / ρ*                                                       [DECIDIDO, Camila, 26-nov, CA-3d, O1]
            Como Σ_d f · D ≈ pasajeros ORIGEN de r en W, ρ_r^obs = pax_ORIGEN / (cap_ef · desp_obs). Con ρ = ρ* cada
            ruta reproduce sus despachos ORIGEN de W (antes del techo) y Σ_r obs_r · m_r = Σ_r obs_r.
            Caso: ρ_R1 = 10/20 = 0,5, ρ_R2 = 5/5 = 1 → m = 0,833 y 1,667.
            POR RUTA y no por corredor: (4) y (5a) ya toman max(desp_r, desp_r') y cuentan las piernas vacías de
            reposición, así que cada sentido debe reproducir SUS despachos; con un m por corredor el sentido cargado
            hereda la baja ocupación del otro (11001-15759 ρ^obs = 0,28 y 15759-11001 0,39): fuera de ventana un m por
            corredor dio 128 % y 133 % (cálculo exploratorio de CA-3d, no se guarda) frente a 172 % y 103 % por ruta
            (resumen.json, validacion_fuera_de_ventana).
Validación fuera de ventana (`calibracion.validacion`): se recalibra TODO (π, cap, f, ρ*, m_r) solo con fecha ≤ fin de la
ventana `calibrar` y se mide la reproducción de despachos ORIGEN en la ventana `probar`, con ρ global y con ρ · m_r.

Redondeo: ⌈x⌉ se calcula como ceil(x − ε) y ⌊x⌋ como floor(x + ε) con ε = 1e-9, igual que la app (dimensionar.ts), para
que el ruido de coma flotante (p. ej. 56,7 / (27 · 0,7) = 3,0000000000000004) no agregue un despacho.
Costos (`costo_pasajero_sin_atender`, `costo_vehiculo_dia_sobrante`): §5.4 los exige y los usa negocio 3; `dimensionar`
no los usa.
"""

from __future__ import annotations

import copy
import math
import time
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from src.comun.results import save_json

EPS = 1e-9
COLUMNAS_ENTRADA = ("ruta_id", "fecha", "demanda")
TIPO_EJEMPLO = "EJEMPLO: observada en train, no es pronóstico"
ORIGEN = "ORIGEN"
GRUPOS = ("por_ruta", "por_clase")
CUANTILES_ARNES = (0.5, 0.75, 0.9, 0.95)  # núcleo §5.3: q0.5, q0.75, q0.9, q0.95
DIAS_SEMANA = 7
# Decreto 1079 de 2015, arts. 2.2.1.4.7.3 y 2.2.1.4.7.4 (compila el Decreto 171 de 2001, arts. 50–51), verificado en
# docs/investigacion/CA-2_verificacion.md §6: «GRUPO A: 4 a 9 pasajeros - GRUPO B: 10 a 19 pasajeros - GRUPO C: más de 19
# pasajeros»; «Automóvil-Campero-Camioneta Grupo A / Microbús-Vans Grupo B / Buseta-Bus Grupo C». «Más de 19» = ≥ 20.
RANGO_CAPACIDAD = {
    "AUTOMOVIL": (4, 9), "CAMPERO": (4, 9), "CAMIONETA": (4, 9),
    "MICROBUS": (10, 19),
    "BUSETA": (20, math.inf), "BUS": (20, math.inf),
}


def _techo(x: float) -> int:
    return int(math.ceil(x - EPS))


def _piso(x: float) -> int:
    return int(math.floor(x + EPS))


# ------------------------------------------------------------------------------------------ ecuaciones (1)–(5b)

def capacidad_efectiva(composicion: Mapping[str, float], capacidades: Mapping[str, float]) -> float:
    """(1) cap_ef = Σ_c π(c) · cap(c). Clases en orden alfabético (mismo orden que la app)."""
    faltan = sorted(c for c in composicion if c not in capacidades)
    if faltan:
        raise ValueError(f"falta capacidad_pasajeros para las clases {faltan}")
    return float(sum(composicion[c] * capacidades[c] for c in sorted(composicion)))


def ocupacion_ruta(ocupacion: float, multiplicador: float) -> float:
    """(2) ρ_r = min(1, ρ · m_r): ocupación objetivo de la ruta; nunca por encima de la capacidad."""
    return min(1.0, ocupacion * multiplicador)


def despachos_dia(demanda: float, cap_ef: float, ocupacion: float, fraccion_origen: float) -> int:
    """(2) desp = ⌈ f · D / (cap_ef · ρ_r) ⌉ (`ocupacion` = ρ_r de la ruta)."""
    return max(0, _techo(fraccion_origen * demanda / (cap_ef * ocupacion)))


def vueltas_dia(horas: float, ciclo: float) -> float:
    """(3) v = H / T_ciclo (fracción; sin piso ni mínimo)."""
    return horas / ciclo


def vehiculos_dia(desp_ida: int, desp_regreso: int, vueltas: float) -> int:
    """(4) veh = ⌈ max(desp_ida, desp_regreso) / v ⌉."""
    return max(0, _techo(max(desp_ida, desp_regreso) / vueltas))


def tripulacion_norma(recorrido_h: float, umbral_h: float) -> int:
    """k_norma = 2 si el recorrido de un sentido es ESTRICTAMENTE mayor que el umbral (Res. 315/2013 art. 6: «duración
    superior a ocho (8) horas de recorrido»); si no, 1."""
    return 2 if recorrido_h > umbral_h else 1


def tripulacion(recorrido_h: float, umbral_h: float, jornada_efectiva: float) -> int:
    """(5a) k = max(k_norma(t), ⌈ t / J_ef ⌉): conductores a bordo, para que nadie maneje más de J_ef en una pierna."""
    return max(tripulacion_norma(recorrido_h, umbral_h), _techo(recorrido_h / jornada_efectiva))


def piernas_dia(desp_ida: int, desp_regreso: int) -> int:
    """(5a) P = 2 · max(desp_ida, desp_regreso): piernas del corredor, incluidas las vacías de reposición."""
    return 2 * max(desp_ida, desp_regreso)


def piernas_por_conductor(recorrido_h: float, k: int, jornada_efectiva: float) -> int:
    """(5a) L = ⌊ J_ef / h ⌋ con h = t / k: piernas indivisibles que un conductor maneja en un día. Con k de `tripulacion`
    h ≤ J_ef y L ≥ 1; con otro k que deje h > J_ef, error (antes se escondía con max(1, ·))."""
    horas = recorrido_h / k
    if horas > jornada_efectiva + EPS:
        raise ValueError(f"tiempo_recorrido_h / k = {recorrido_h:g} / {k} = {horas:g} h supera jornada_efectiva_h = "
                         f"{jornada_efectiva:g} h: un conductor no cubre la pierna (use k = tripulacion(...))")
    return _piso(jornada_efectiva / horas)


def conductores_servicio(desp_ida: int, desp_regreso: int, recorrido_h: float, k: int, jornada_efectiva: float) -> int:
    """(5a) C_serv = ⌈ k · P / L ⌉: cada pierna lleva k conductores y cada conductor cubre L piernas al día."""
    return max(0, _techo(k * piernas_dia(desp_ida, desp_regreso) / piernas_por_conductor(recorrido_h, k, jornada_efectiva)))


def conductores_nomina(c_serv: int, ausentismo: float, dias_descanso_semana: int) -> int:
    """(5b) diaria: C_nom = ⌈ C_serv / (1 − a) · 7 / (7 − s) ⌉."""
    return max(0, _techo(c_serv / (1 - ausentismo) * DIAS_SEMANA / (DIAS_SEMANA - dias_descanso_semana)))


def nomina_semanal_minima(c_serv: Sequence[int], ausentismo: float, dias_descanso_semana: int) -> int:
    """(5b) semanal: N* = ⌈ max(max_d C_serv, Σ_d C_serv / (7 − s)) / (1 − a) ⌉ para los días de UNA semana (≤ 7).
    Con menos de 7 días (semana incompleta) es una cota inferior."""
    if len(c_serv) > DIAS_SEMANA:
        raise ValueError(f"una semana tiene a lo sumo {DIAS_SEMANA} días (llegaron {len(c_serv)})")
    if not c_serv:
        return 0
    necesidad = max(max(c_serv), sum(c_serv) / (DIAS_SEMANA - dias_descanso_semana))
    return max(0, _techo(necesidad / (1 - ausentismo)))


# --------------------------------------------------------------------------------------------- validación

def _en(valor, nombre: str, lo: float, hi: float, lo_abierto: bool = False, hi_abierto: bool = False) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
        raise ValueError(f"{nombre} debe ser un número finito (vale {valor!r})")
    fuera = (valor <= lo if lo_abierto else valor < lo) or (valor >= hi if hi_abierto else valor > hi)
    if fuera:
        a, b = ("(" if lo_abierto else "["), (")" if hi_abierto else "]")
        raise ValueError(f"{nombre} = {valor} fuera de rango; debe estar en {a}{lo}, {hi}{b}")
    return float(valor)


def _validar_globales(g: dict) -> None:
    _en(g["ocupacion_objetivo"], "ocupacion_objetivo", 0, 1, lo_abierto=True)
    q = _en(g["cuantil"], "cuantil", 0, 1, lo_abierto=True, hi_abierto=True)
    if not any(abs(q - c) < EPS for c in CUANTILES_ARNES):
        raise ValueError(f"cuantil = {q} no es un cuantil del arnés; debe ser uno de {list(CUANTILES_ARNES)} (núcleo §5.3)")
    _en(g["horas_operacion_h"], "horas_operacion_h", 0, 24, lo_abierto=True)
    jmax = _en(g["jornada_max_diaria_h"], "jornada_max_diaria_h", 0, 24, lo_abierto=True)
    jef = _en(g["jornada_efectiva_h"], "jornada_efectiva_h", 0, jmax, lo_abierto=True)
    jsem = _en(g["jornada_max_semanal_h"], "jornada_max_semanal_h", 0, 24 * DIAS_SEMANA, lo_abierto=True)
    s = _en(g["dias_descanso_semana"], "dias_descanso_semana", 1, DIAS_SEMANA - 1)
    if not s.is_integer():
        raise ValueError(f"dias_descanso_semana debe ser entero en 1..6 (vale {s}); la norma garantiza el día de descanso")
    if jef * (DIAS_SEMANA - s) > jsem + EPS:
        raise ValueError(f"jornada_efectiva_h · (7 − dias_descanso_semana) = {jef} · {7 - s:g} = {jef * (7 - s):g} h "
                         f"supera jornada_max_semanal_h = {jsem:g} h")
    _en(g["ausentismo"], "ausentismo", 0, 1, hi_abierto=True)
    _en(g["umbral_segundo_conductor_h"], "umbral_segundo_conductor_h", 0, 24, lo_abierto=True)
    for k in ("costo_pasajero_sin_atender", "costo_vehiculo_dia_sobrante"):
        if k in g:
            _en(g[k], k, 0, math.inf)


def _validar_ruta(ruta: str, p: dict, params: dict) -> None:
    g = params["globales"]
    ciclo = _en(p["tiempo_ciclo_h"], f"por_ruta.{ruta}.tiempo_ciclo_h", 0, math.inf, lo_abierto=True)
    rec = _en(p["tiempo_recorrido_h"], f"por_ruta.{ruta}.tiempo_recorrido_h", 0, math.inf, lo_abierto=True)
    _en(p["fraccion_demanda_en_origen"], f"por_ruta.{ruta}.fraccion_demanda_en_origen", 0, 1, lo_abierto=True)
    _en(p["multiplicador_ocupacion"], f"por_ruta.{ruta}.multiplicador_ocupacion", 0, math.inf, lo_abierto=True,
        hi_abierto=True)
    if ciclo < 2 * rec:
        raise ValueError(f"por_ruta.{ruta}.tiempo_ciclo_h = {ciclo} < 2 · tiempo_recorrido_h = {2 * rec}: "
                         "el ciclo debe cubrir la ida y el regreso")
    # Aserción (E1): con k = max(k_norma, ⌈t/J_ef⌉), h = t/k ≤ J_ef ≤ jornada_max_diaria_h; lanza error si no.
    piernas_por_conductor(rec, tripulacion(rec, g["umbral_segundo_conductor_h"], g["jornada_efectiva_h"]),
                          g["jornada_efectiva_h"])
    regreso = params["ruta_regreso"].get(ruta)
    if regreso in params["por_ruta"]:
        pr = params["por_ruta"][regreso]
        for clave in ("tiempo_ciclo_h", "tiempo_recorrido_h"):
            if pr[clave] != p[clave]:
                raise ValueError(f"por_ruta.{ruta}.{clave} ({p[clave]}) ≠ por_ruta.{regreso}.{clave} ({pr[clave]}): el "
                                 "corredor comparte vehículos, así que ciclo y recorrido deben ser iguales en los dos sentidos")


def validar_parametros(params: dict) -> None:
    """Rangos de dominio de las ecuaciones (1)–(5'); error claro con el nombre del parámetro."""
    _validar_globales(params["globales"])
    for clase, p in params["por_clase"].items():
        _en(p["capacidad_pasajeros"], f"por_clase.{clase}.capacidad_pasajeros", 0, math.inf, lo_abierto=True)
    for ruta, p in params["por_ruta"].items():
        _validar_ruta(ruta, p, params)
    for ruta, comp in params["composicion_clases"].items():
        for clase, v in comp.items():
            _en(v, f"composicion_clases.{ruta}.{clase}", 0, 1)
        suma = sum(comp.values())
        if abs(suma - 1) > 1e-6:
            raise ValueError(f"composicion_clases.{ruta}: las participaciones deben sumar 1 (suma {suma})")


def _validar_demanda(demanda: pd.DataFrame, params: dict) -> None:
    faltan = [c for c in COLUMNAS_ENTRADA if c not in demanda.columns]
    if faltan:
        raise ValueError(f"a la demanda le falta la columna {faltan} (se esperan {list(COLUMNAS_ENTRADA)})")
    d = pd.to_numeric(demanda["demanda"], errors="coerce")
    if d.isna().any() or (d < 0).any() or not d.map(math.isfinite).all():
        raise ValueError("la demanda debe ser un número finito >= 0 en todas las filas")
    if demanda.duplicated(["ruta_id", "fecha"]).any():
        raise ValueError("hay filas duplicadas de (ruta_id, fecha) en la demanda")
    for ruta in demanda["ruta_id"].unique():
        for grupo in ("por_ruta", "composicion_clases"):
            if ruta not in params[grupo]:
                raise ValueError(f"la ruta {ruta} no tiene parámetros en {grupo}")
        if ruta not in params["ruta_regreso"]:
            raise ValueError(f"la ruta {ruta} no tiene ruta de regreso (rutas.yaml)")


# ------------------------------------------------------------------------------------------------ dimensionar

def _despachos_del_regreso(out: pd.DataFrame) -> pd.Series:
    """desp(r', d) para cada fila (r, d): el regreso el MISMO día; error si falta."""
    desp = pd.Series(out["despachos"].to_numpy(), index=pd.MultiIndex.from_arrays([out["ruta_id"], out["fecha"]]))
    buscado = pd.MultiIndex.from_arrays([out["ruta_regreso_id"], out["fecha"]])
    falta = ~buscado.isin(desp.index)
    if falta.any():
        i = int(falta.argmax())
        raise ValueError(f"falta la demanda del regreso {buscado[i][0]} el {buscado[i][1]} (para {out['ruta_id'].iloc[i]}); "
                         "dimensionar necesita los dos sentidos del corredor cada día")
    return pd.Series(desp.reindex(buscado).to_numpy(), index=out.index)


def dimensionar(demanda: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Núcleo §5.4. Entrada `ruta_id, fecha, demanda` (+ columnas extra, que se conservan); salida = entrada + pasos
    intermedios + despachos, vehiculos, conductores_servicio y conductores (= nómina). Para cada (r, d) debe venir también
    (r', d), con r' = `params["ruta_regreso"][r]`: vehículos y conductores son del corredor y se repiten en las dos filas.

    `params` (valores ya resueltos): `globales` {clave: valor}, `por_ruta` {ruta: {tiempo_ciclo_h, tiempo_recorrido_h,
    fraccion_demanda_en_origen, multiplicador_ocupacion}}, `por_clase` {clase: {capacidad_pasajeros}}, `composicion_clases` {ruta: {clase: π}} y
    `ruta_regreso` {ruta: ruta_regreso_id} (ver `parametros_desde_config`).
    """
    validar_parametros(params)
    _validar_demanda(demanda, params)
    g, por_ruta, regreso = params["globales"], params["por_ruta"], params["ruta_regreso"]
    capacidades = {c: p["capacidad_pasajeros"] for c, p in params["por_clase"].items()}

    out = demanda.copy()
    rutas = out["ruta_id"]
    out["ruta_regreso_id"] = rutas.map(regreso)
    out["corredor"] = [" | ".join(sorted((r, regreso[r]))) for r in rutas]
    out["fraccion_origen"] = [por_ruta[r]["fraccion_demanda_en_origen"] for r in rutas]
    out["capacidad_efectiva"] = [capacidad_efectiva(params["composicion_clases"][r], capacidades) for r in rutas]
    out["ocupacion_ruta"] = [ocupacion_ruta(g["ocupacion_objetivo"], por_ruta[r]["multiplicador_ocupacion"])  # ρ_r
                             for r in rutas]
    out["despachos"] = [                                                                                     # (2)
        despachos_dia(dem, cap, rho, f)
        for dem, cap, rho, f in zip(out["demanda"], out["capacidad_efectiva"], out["ocupacion_ruta"],
                                    out["fraccion_origen"], strict=True)
    ]
    out["despachos_regreso"] = _despachos_del_regreso(out)
    out["vueltas"] = [vueltas_dia(g["horas_operacion_h"], por_ruta[r]["tiempo_ciclo_h"]) for r in rutas]      # (3)
    out["vehiculos"] = [vehiculos_dia(a, b, v) for a, b, v in                                                 # (4)
                        zip(out["despachos"], out["despachos_regreso"], out["vueltas"], strict=True)]
    recorrido = [por_ruta[r]["tiempo_recorrido_h"] for r in rutas]
    out["tripulacion"] = [tripulacion(t, g["umbral_segundo_conductor_h"], g["jornada_efectiva_h"]) for t in recorrido]
    out["piernas"] = [piernas_dia(a, b) for a, b in zip(out["despachos"], out["despachos_regreso"], strict=True)]
    out["piernas_por_conductor"] = [piernas_por_conductor(t, k, g["jornada_efectiva_h"])
                                    for t, k in zip(recorrido, out["tripulacion"], strict=True)]
    out["conductores_servicio"] = [                                                                          # (5a)
        conductores_servicio(a, b, t, k, g["jornada_efectiva_h"])
        for a, b, t, k in zip(out["despachos"], out["despachos_regreso"], recorrido, out["tripulacion"], strict=True)
    ]
    out["conductores"] = [conductores_nomina(c, g["ausentismo"], int(g["dias_descanso_semana"]))           # (5b)
                          for c in out["conductores_servicio"]]
    for col in ("despachos", "despachos_regreso", "vehiculos", "tripulacion", "piernas", "piernas_por_conductor",
                "conductores_servicio", "conductores"):
        out[col] = out[col].astype("int64")
    return out


def flota_por_corredor(tabla: pd.DataFrame) -> pd.DataFrame:
    """Una fila por (corredor, fecha) a partir de la salida de `dimensionar`, para no sumar dos veces la flota y los
    conductores (las filas de r y r' los repiten). `ruta_ida` = la primera ruta del corredor en orden alfabético."""
    por_corredor = tabla.groupby(["corredor", "fecha"])
    for col in ("vehiculos", "conductores_servicio", "conductores"):
        if (por_corredor[col].nunique() > 1).any():
            raise ValueError(f"las dos filas de un corredor tienen distinto valor de {col}; la tabla no viene de dimensionar")
    ida = tabla[tabla["ruta_id"] == tabla["corredor"].str.split(" | ", regex=False).str[0]]
    columnas = {"corredor": "corredor", "fecha": "fecha", "ruta_id": "ruta_ida", "ruta_regreso_id": "ruta_regreso",
                "despachos": "despachos_ida", "despachos_regreso": "despachos_regreso", "vehiculos": "vehiculos",
                "piernas": "piernas", "piernas_por_conductor": "piernas_por_conductor",
                "conductores_servicio": "conductores_servicio", "conductores": "conductores"}
    return ida[list(columnas)].rename(columns=columnas).sort_values(["corredor", "fecha"]).reset_index(drop=True)


def nomina_semanal(corredores: pd.DataFrame, ausentismo: float, dias_descanso_semana: int) -> pd.DataFrame:
    """(5b) N* por corredor y semana (lunes a domingo) a partir de `flota_por_corredor`. `dias_con_datos` < 7 marca una
    semana incompleta (borde del periodo o días sin registro): su N* es una cota inferior. `max_nomina_diaria` es el
    máximo de la columna diaria `conductores` en la semana, para comparar."""
    fecha = pd.to_datetime(corredores["fecha"])
    t = corredores.assign(semana_inicio=(fecha - pd.to_timedelta(fecha.dt.day_of_week, unit="D")).dt.normalize())
    filas = []
    for (corredor, lunes), g in t.groupby(["corredor", "semana_inicio"], sort=True):
        c = [int(x) for x in g["conductores_servicio"]]
        filas.append({
            "corredor": corredor, "semana_inicio": lunes, "semana_fin": lunes + pd.Timedelta(days=DIAS_SEMANA - 1),
            "dias_con_datos": len(c), "semana_completa": len(c) == DIAS_SEMANA,
            "max_conductores_servicio": max(c), "suma_conductores_servicio": sum(c),
            "nomina_semanal": nomina_semanal_minima(c, ausentismo, dias_descanso_semana),
            "max_nomina_diaria": int(g["conductores"].max()),
        })
    return pd.DataFrame(filas)


# ------------------------------------------------------------------------- estimaciones con train (sin fuga)

def _ventana(tabla: pd.DataFrame, inicio, fin) -> pd.DataFrame:
    """Filas con inicio <= fecha <= fin (ambos incluidos). Nada posterior a `fin` sale de aquí (núcleo §5.4)."""
    f = pd.to_datetime(tabla["fecha"])
    return tabla[(f >= pd.Timestamp(inicio)) & (f <= pd.Timestamp(fin))]


def estimar_composicion(detalle: pd.DataFrame, inicio, fin, clases: list[str]) -> dict[str, dict[str, float]]:
    """π(r, c) = Σ despachos ORIGEN de clase c / Σ despachos ORIGEN de r, con inicio <= fecha <= fin (train)."""
    o = _ventana(detalle[detalle["tipo_despacho"] == ORIGEN], inicio, fin)
    desconocidas = sorted(set(o.loc[o["despachos"] > 0, "clase_vehiculo"]) - set(clases))
    if desconocidas:
        raise ValueError(f"clases con despachos en train que no están en por_clase: {desconocidas}")
    comp: dict[str, dict[str, float]] = {}
    for ruta in sorted(detalle["ruta_id"].unique()):
        por_clase = o[o["ruta_id"] == ruta].groupby("clase_vehiculo")["despachos"].sum()
        total = por_clase.sum()
        if total <= 0:
            raise ValueError(f"la ruta {ruta} no tiene despachos de ORIGEN entre {inicio} y {fin}")
        comp[ruta] = {c: float(por_clase.get(c, 0) / total) for c in sorted(clases)}
    return comp


def capacidad_observada(detalle: pd.DataFrame, inicio, fin) -> pd.DataFrame:
    """Máximo de pasajeros/despacho por clase en los días ORIGEN de train. Cada fila del detalle es la suma de un día,
    así que es un PROMEDIO diario por despacho: cota baja de la capacidad física de un vehículo."""
    o = _ventana(detalle[(detalle["tipo_despacho"] == ORIGEN) & (detalle["despachos"] > 0)], inicio, fin)
    ppd = (o["pasajeros"] / o["despachos"]).groupby(o["clase_vehiculo"])
    return pd.DataFrame({"maximo": ppd.max(), "n_dias": ppd.size()}).rename_axis("clase_vehiculo").reset_index()


def capacidad_supuesta(clase: str, maximo: float) -> int:
    """cap(c) = min(máx. del grupo, max(mín. del grupo, ⌈máximo observado⌉)), grupos del Decreto 1079/2015."""
    if clase not in RANGO_CAPACIDAD:
        raise ValueError(f"la clase {clase} no está en los grupos del Decreto 1079/2015 (RANGO_CAPACIDAD)")
    lo, hi = RANGO_CAPACIDAD[clase]
    return int(min(hi, max(lo, _techo(maximo))))


def fraccion_pasajeros_origen(detalle: pd.DataFrame, inicio, fin) -> dict[str, float]:
    """f(r) = pasajeros ORIGEN / (ORIGEN + TRANSITO) por ruta, con inicio <= fecha <= fin."""
    t = _ventana(detalle, inicio, fin)
    tot = t.groupby("ruta_id")["pasajeros"].sum()
    ori = t[t["tipo_despacho"] == ORIGEN].groupby("ruta_id")["pasajeros"].sum()
    out = {}
    for ruta in sorted(detalle["ruta_id"].unique()):
        if tot.get(ruta, 0) <= 0:
            raise ValueError(f"la ruta {ruta} no tiene pasajeros entre {inicio} y {fin}: no se puede calcular "
                             "fraccion_demanda_en_origen (división por cero)")
        out[ruta] = float(ori.get(ruta, 0) / tot[ruta])
    return out


def ventana_reciente(inicio, fin, meses: int) -> tuple[date, date]:
    """Últimos `meses` meses de train: [max(inicio, fin + 1 día − meses), fin]."""
    if isinstance(meses, bool) or not isinstance(meses, int) or meses < 1:
        raise ValueError(f"calibracion.meses_fraccion debe ser un entero >= 1 (vale {meses!r})")
    fin_ts = pd.Timestamp(fin)
    desde = fin_ts + pd.Timedelta(days=1) - pd.DateOffset(months=meses)
    return max(pd.Timestamp(inicio), desde).date(), fin_ts.date()


def despachos_origen_diarios(detalle: pd.DataFrame, inicio, fin) -> pd.DataFrame:
    """Despachos ORIGEN observados por (ruta_id, fecha) en la ventana (todas las clases)."""
    o = _ventana(detalle[detalle["tipo_despacho"] == ORIGEN], inicio, fin)
    out = o.groupby(["ruta_id", "fecha"], as_index=False)["despachos"].sum()
    out["fecha"] = pd.to_datetime(out["fecha"])
    return out.sort_values(["ruta_id", "fecha"]).reset_index(drop=True)


def ocupacion_calibrada(demanda: pd.DataFrame, despachos_origen: pd.DataFrame, fraccion: Mapping[str, float],
                        cap_ef: Mapping[str, float]) -> float:
    """ρ* = Σ f(r) · D(r, d) / cap_ef(r) ÷ Σ despachos ORIGEN(r, d), sobre los (r, d) de `demanda` (que ya viene
    recortada a train y sin días sin registro). Un día sin despachos ORIGEN observados aporta 0 al denominador."""
    m = demanda[["ruta_id", "fecha", "demanda"]].merge(despachos_origen, on=["ruta_id", "fecha"], how="left")
    cargas_llenas = sum(fraccion[r] * dem / cap_ef[r] for r, dem in zip(m["ruta_id"], m["demanda"], strict=True))
    observados = float(m["despachos"].fillna(0).sum())
    if observados <= 0:
        raise ValueError("no hay despachos de ORIGEN observados en la ventana: no se puede calibrar ocupacion_objetivo")
    return float(cargas_llenas / observados)


def multiplicadores_ocupacion(demanda: pd.DataFrame, despachos_origen: pd.DataFrame, fraccion: Mapping[str, float],
                              cap_ef: Mapping[str, float], rho: float) -> dict[str, float]:
    """m_r = ρ_r^obs / ρ*, con ρ_r^obs = la cuenta de ρ* restringida a los días de la ruta r en `demanda`."""
    out = {}
    for ruta in sorted(demanda["ruta_id"].unique()):
        try:
            out[ruta] = ocupacion_calibrada(demanda[demanda["ruta_id"] == ruta], despachos_origen, fraccion, cap_ef) / rho
        except ValueError as e:
            raise ValueError(f"la ruta {ruta}: {e}; no se puede calcular multiplicador_ocupacion") from e
    return out


def reproduccion_despachos(tabla: pd.DataFrame, despachos_origen: pd.DataFrame) -> dict[str, dict]:
    """Despachos del modelo vs. despachos ORIGEN observados en los mismos (ruta_id, fecha): por ruta y total (%)."""
    obs = despachos_origen.rename(columns={"despachos": "observado"})
    m = tabla[["ruta_id", "fecha", "despachos"]].merge(obs, on=["ruta_id", "fecha"], how="left").fillna({"observado": 0})

    def fila(modelo, observado) -> dict:
        return {"modelo": int(modelo), "observado": int(observado),
                "porcentaje": float(100 * modelo / observado) if observado else math.nan}

    out = {r: fila(g["despachos"].sum(), g["observado"].sum()) for r, g in m.groupby("ruta_id")}
    out["total"] = fila(m["despachos"].sum(), m["observado"].sum())
    return out


# --------------------------------------------------------------------------------------- demanda observada

def demanda_observada(diaria: pd.DataFrame, inicio, fin, regresos: Mapping[str, str], inicio_train,
                      fin_train) -> pd.DataFrame:
    """Pasajeros observados como `demanda` en [inicio, fin], que debe caber en el train. Excluye el día del CORREDOR si
    cualquiera de los dos sentidos está `sin_registro` (vale 0 pero no es demanda; dimensionar necesita los dos)."""
    if pd.Timestamp(inicio) < pd.Timestamp(inicio_train):
        raise ValueError(f"la ventana empieza el {inicio}, antes de inicio_entrenamiento ({inicio_train})")
    if pd.Timestamp(fin) > pd.Timestamp(fin_train):
        raise ValueError(f"la ventana termina el {fin}, después de fin_entrenamiento ({fin_train}); use datos de train")
    sel = _ventana(diaria, inicio, fin)
    if sel.empty:
        raise ValueError(f"no hay datos entre {inicio} y {fin}")
    sin_registro = set(zip(sel.loc[sel["sin_registro"], "ruta_id"], sel.loc[sel["sin_registro"], "fecha"], strict=True))
    excluir = [(r, f) in sin_registro or (regresos[r], f) in sin_registro
               for r, f in zip(sel["ruta_id"], sel["fecha"], strict=True)]
    out = sel.loc[~pd.Series(excluir, index=sel.index), ["ruta_id", "fecha", "pasajeros"]]
    out = out.rename(columns={"pasajeros": "demanda"}).reset_index(drop=True)
    out["fecha"] = pd.to_datetime(out["fecha"])
    return out


def demanda_ejemplo(diaria: pd.DataFrame, mes: str, regresos: Mapping[str, str], inicio_train, fin_train) -> pd.DataFrame:
    """Demanda de EJEMPLO mientras no hay pronósticos (AN-5): pasajeros observados de un mes COMPLETO de train."""
    periodo = pd.Period(mes, freq="M")
    out = demanda_observada(diaria, periodo.start_time.date(), periodo.end_time.date(), regresos, inicio_train, fin_train)
    return out.assign(tipo_demanda=TIPO_EJEMPLO)


# --------------------------------------------------------------------------------------------- configuración

def leer_regresos(ruta_yaml: Path) -> dict[str, str]:
    rutas = yaml.safe_load(Path(ruta_yaml).read_text(encoding="utf-8"))["rutas"]
    return {r["ruta_id"]: r["ruta_regreso_id"] for r in rutas}


def _calibrar_en(detalle: pd.DataFrame, diaria: pd.DataFrame, regresos: Mapping[str, str], inicio, fin,
                 ventana: tuple, capacidades: Mapping[str, float]) -> dict:
    """π con [inicio, fin]; f, ρ* y m_r con `ventana` ⊆ [inicio, fin]. Nada posterior a `fin` entra (núcleo §5.4)."""
    if not pd.Timestamp(inicio) <= pd.Timestamp(ventana[0]) <= pd.Timestamp(ventana[1]) <= pd.Timestamp(fin):
        raise ValueError(f"la ventana de calibración {ventana} debe caber en [{inicio}, {fin}]")
    composicion = estimar_composicion(detalle, inicio, fin, list(capacidades))
    fraccion = fraccion_pasajeros_origen(detalle, *ventana)
    cap_ef = {r: capacidad_efectiva(comp, capacidades) for r, comp in composicion.items()}
    demanda = demanda_observada(diaria, inicio, fin, regresos, inicio, fin)
    observados = despachos_origen_diarios(detalle, inicio, fin)
    demanda_w = _ventana(demanda, *ventana)
    rho = ocupacion_calibrada(demanda_w, observados, fraccion, cap_ef)
    return {
        "composicion": composicion,
        "ventana_fraccion": tuple(pd.Timestamp(x).date() for x in ventana),
        "fraccion": fraccion,
        "capacidad_efectiva": cap_ef,
        "ocupacion_calibrada": rho,
        "multiplicador_ocupacion": multiplicadores_ocupacion(demanda_w, observados, fraccion, cap_ef, rho),
        "demanda_train": demanda,
        "despachos_origen_train": observados,
    }


def calibrar(cfg: dict, detalle: pd.DataFrame, diaria: pd.DataFrame, regresos: Mapping[str, str]) -> dict:
    """Todo lo que se estima con train: π, f, capacidad observada, cap_ef, ρ* y m_r (más las tablas para reproducirlos).
    f, ρ* y m_r usan la misma ventana: los últimos `calibracion.meses_fraccion` meses de train."""
    datos = cfg["datos"]
    inicio, fin = datos["inicio_entrenamiento"], datos["fin_entrenamiento"]
    capacidades = {c: p["capacidad_pasajeros"] for c, p in cfg["operacion"]["por_clase"].items()}
    ventana = ventana_reciente(inicio, fin, cfg["calibracion"]["meses_fraccion"])
    cal = _calibrar_en(detalle, diaria, regresos, inicio, fin, ventana, capacidades)
    cal.update({
        "fraccion_todo_train": fraccion_pasajeros_origen(detalle, inicio, fin),  # diagnóstico
        "capacidad_observada": capacidad_observada(detalle, inicio, fin),
        "ocupacion_calibrada_todo_train": ocupacion_calibrada(cal["demanda_train"], cal["despachos_origen_train"],
                                                              cal["fraccion"], cal["capacidad_efectiva"]),  # diagnóstico
    })
    return cal


def parametros_desde_config(cfg: dict, calibracion: dict, ruta_regreso: Mapping[str, str],
                            con_multiplicador: bool = True) -> dict:
    """Valores de `cfg["operacion"]` + lo calibrado con train, en el formato que recibe `dimensionar`.
    `con_multiplicador=False` usa m_r = 1 (un solo ρ global; solo para comparar)."""
    o = cfg["operacion"]
    m = calibracion["multiplicador_ocupacion"]
    return {
        "globales": {k: v for k, v in o.items() if k not in GRUPOS},
        "por_ruta": {r: {**p, "fraccion_demanda_en_origen": calibracion["fraccion"][r],
                         "multiplicador_ocupacion": m[r] if con_multiplicador else 1.0}
                     for r, p in o["por_ruta"].items()},
        "por_clase": {c: dict(p) for c, p in o["por_clase"].items()},
        "composicion_clases": calibracion["composicion"],
        "ruta_regreso": dict(ruta_regreso),
    }


def reproduccion_global_y_por_ruta(cfg: dict, calibracion: dict, regresos: Mapping[str, str], demanda: pd.DataFrame,
                                   observados: pd.DataFrame) -> dict[str, dict]:
    """Despachos ORIGEN reproducidos con ρ = ρ* de `calibracion`: un ρ global (m_r = 1) y ρ · m_r."""
    cfg_rho = copy.deepcopy(cfg)
    cfg_rho["operacion"]["ocupacion_objetivo"] = calibracion["ocupacion_calibrada"]
    return {
        f"reproduccion_rho_{nombre}": reproduccion_despachos(
            dimensionar(demanda, parametros_desde_config(cfg_rho, calibracion, regresos, con_m)), observados)
        for nombre, con_m in (("global", False), ("por_ruta", True))
    }


def validar_fuera_de_ventana(cfg: dict, detalle: pd.DataFrame, diaria: pd.DataFrame,
                             regresos: Mapping[str, str]) -> dict:
    """Recalibra π, cap, f, ρ* y m_r SOLO con fecha ≤ fin de `calibracion.validacion.calibrar` (cap con la regla del
    Decreto 1079/2015 sobre esos datos, no la del YAML, que usa todo el train) y mide la reproducción de despachos ORIGEN
    en `calibracion.validacion.probar`, con ρ global y con ρ · m_r."""
    datos, v = cfg["datos"], cfg["calibracion"]["validacion"]
    inicio, fin_train = pd.Timestamp(datos["inicio_entrenamiento"]), pd.Timestamp(datos["fin_entrenamiento"])
    (c0, c1), (p0, p1) = ([pd.Timestamp(x) for x in v["calibrar"]], [pd.Timestamp(x) for x in v["probar"]])
    if not inicio <= c0 <= c1 < p0 <= p1 <= fin_train:
        raise ValueError(f"calibracion.validacion: se exige inicio_entrenamiento ≤ calibrar ≤ fin de calibrar < probar ≤ "
                         f"fin_entrenamiento (llegó calibrar {v['calibrar']}, probar {v['probar']})")
    obs = capacidad_observada(detalle, inicio, c1).set_index("clase_vehiculo")
    faltan = sorted(set(cfg["operacion"]["por_clase"]) - set(obs.index))
    if faltan:
        raise ValueError(f"clases sin despachos ORIGEN hasta {c1.date()}: {faltan}; no se puede fijar su capacidad")
    capacidades = {c: capacidad_supuesta(c, obs.loc[c, "maximo"]) for c in cfg["operacion"]["por_clase"]}
    cal = _calibrar_en(detalle, diaria, regresos, inicio, c1, (c0, c1), capacidades)
    cfg_v = copy.deepcopy(cfg)
    for c, cap in capacidades.items():
        cfg_v["operacion"]["por_clase"][c]["capacidad_pasajeros"] = cap
    demanda_p = demanda_observada(diaria, p0, p1, regresos, inicio, fin_train)
    return {
        "ventana_calibracion": [c0.date().isoformat(), c1.date().isoformat()],
        "ventana_prueba": [p0.date().isoformat(), p1.date().isoformat()],
        "capacidades": capacidades,
        **{k: cal[k] for k in ("composicion", "fraccion", "capacidad_efectiva", "ocupacion_calibrada",
                               "multiplicador_ocupacion")},
        **reproduccion_global_y_por_ruta(cfg_v, cal, regresos, demanda_p, despachos_origen_diarios(detalle, p0, p1)),
    }


def parametros_contrato(cfg: dict, calibracion: dict) -> dict:
    """Parámetros al formato `ParametrosOperacion` de la app (núcleo §5.4): {valor, unidad, fuente | supuesto, nota?}.
    Meta: `meta.globales.<clave>`, `meta.por_ruta.<clave>` (común a las rutas) y `meta.por_clase.<clase>.<clave>`.
    Lo calibrado con train (f, m_r y composición) lleva `fuente` con el conjunto y la ventana usada."""
    o, meta, datos = cfg["operacion"], cfg["meta"], cfg["datos"]

    def par(valor, m: dict) -> dict:
        p = {"valor": valor, "unidad": m["unidad"]}
        p.update({"fuente": m["fuente"]} if "fuente" in m else {"supuesto": True})
        if m.get("nota"):
            p["nota"] = m["nota"]
        return p

    fuente = cfg["calibracion"]["fuente_datos"]
    ini_f, fin_f = calibracion["ventana_fraccion"]
    fuente_f = (f"{fuente}; pasajeros ORIGEN / (ORIGEN + TRANSITO) entre {ini_f.isoformat()} y {fin_f.isoformat()} "
                f"(últimos {cfg['calibracion']['meses_fraccion']} meses de train)")
    fuente_comp = (f"{fuente}; despachos de ORIGEN entre {datos['inicio_entrenamiento']} y {datos['fin_entrenamiento']} "
                   "(train)")
    por_ruta = {}
    for r, p in o["por_ruta"].items():
        por_ruta[r] = {k: par(v, meta["por_ruta"][k]) for k, v in p.items()}
        por_ruta[r]["fraccion_demanda_en_origen"] = {"valor": calibracion["fraccion"][r],
                                                     "unidad": "fracción de los pasajeros", "fuente": fuente_f}
        por_ruta[r]["multiplicador_ocupacion"] = {
            "valor": calibracion["multiplicador_ocupacion"][r], "unidad": "múltiplo de ocupacion_objetivo",
            "fuente": (f"{fuente}; m_r = ρ_r observada / ρ* entre {ini_f.isoformat()} y {fin_f.isoformat()} (misma ventana "
                       "que fraccion_demanda_en_origen)"),
            "nota": "ρ_r = min(1, ocupacion_objetivo · m_r) (ec. (2)).",
        }
    return {
        "globales": {k: par(v, meta["globales"][k]) for k, v in o.items() if k not in GRUPOS},
        "por_ruta": por_ruta,
        "por_clase": {c: {k: par(v, meta["por_clase"][c][k]) for k, v in p.items()} for c, p in o["por_clase"].items()},
        "composicion_clases": {
            r: {c: {"valor": v, "unidad": "fracción de los despachos de ORIGEN", "fuente": fuente_comp}
                for c, v in comp.items()}
            for r, comp in calibracion["composicion"].items()
        },
    }


# ------------------------------------------------------------------------------------------------------- main

def _resumen(cfg: dict, calibracion: dict, corredores: pd.DataFrame, semanas: pd.DataFrame, reproduccion: dict,
             validacion: dict) -> dict:
    datos = cfg["datos"]
    capacidades = cfg["operacion"]["por_clase"]
    rho = cfg["operacion"]["ocupacion_objetivo"]
    obs = calibracion["capacidad_observada"].set_index("clase_vehiculo")
    return {
        "aviso": f"Demanda de EJEMPLO ({TIPO_EJEMPLO}); mes {cfg['ejemplo']['mes']}.",
        "ventana_train": [str(datos["inicio_entrenamiento"]), str(datos["fin_entrenamiento"])],
        "calibracion": {
            "ventana_fraccion": [d.isoformat() for d in calibracion["ventana_fraccion"]],
            "fraccion_demanda_en_origen": calibracion["fraccion"],
            "fraccion_todo_train": calibracion["fraccion_todo_train"],
            "capacidad": {c: {"maximo_observado": float(obs.loc[c, "maximo"]), "n_dias": int(obs.loc[c, "n_dias"]),
                              "capacidad_supuesta": capacidad_supuesta(c, obs.loc[c, "maximo"]),
                              "capacidad_usada": capacidades[c]["capacidad_pasajeros"]} for c in obs.index},
            "capacidad_efectiva": calibracion["capacidad_efectiva"],
            "ocupacion_calibrada": calibracion["ocupacion_calibrada"],
            "ocupacion_calibrada_todo_train": calibracion["ocupacion_calibrada_todo_train"],
            "ocupacion_usada": rho,
            "multiplicador_ocupacion": calibracion["multiplicador_ocupacion"],
            "ocupacion_por_ruta_usada": {r: ocupacion_ruta(rho, m) for r, m in calibracion["multiplicador_ocupacion"].items()},
            "ocupacion_por_ruta_con_tope_1": sorted(r for r, m in calibracion["multiplicador_ocupacion"].items()
                                                    if rho * m > 1),
            "limitacion_rho_global": ("Con un solo ρ global (m_r = 1) el total de despachos ORIGEN de la ventana se "
                                      "reproduce, pero cada ruta queda por encima o por debajo; m_r lo corrige por ruta "
                                      "(reproduccion_dentro_de_ventana y validacion_fuera_de_ventana)."),
            "reproduccion_dentro_de_ventana": reproduccion.pop("dentro_de_ventana"),
            "validacion_fuera_de_ventana": validacion,
            **{f"reproduccion_despachos_{k}": v for k, v in reproduccion.items()},
        },
        "maximo_diario_por_corredor": {
            c: {"vehiculos": int(g["vehiculos"].max()), "conductores_servicio": int(g["conductores_servicio"].max()),
                "conductores": int(g["conductores"].max())}
            for c, g in corredores.groupby("corredor")
        },
        "nomina_semanal_por_corredor": {
            c: {"max_nomina_semanal": int(g["nomina_semanal"].max()),
                "max_nomina_semanal_semanas_completas": (int(g.loc[g["semana_completa"], "nomina_semanal"].max())
                                                         if g["semana_completa"].any() else None),
                "max_nomina_diaria": int(g["max_nomina_diaria"].max()),
                "semanas": int(len(g)), "semanas_completas": int(g["semana_completa"].sum())}
            for c, g in semanas.groupby("corredor")
        },
        "nota_nomina_semanal": ("N* = ⌈max(max_d C_serv, Σ_d C_serv / (7 − s)) / (1 − a)⌉ por corredor y semana de lunes a "
                                "domingo (nomina_semanal.csv). En semanas incompletas (dias_con_datos < 7: borde del mes "
                                "o días sin registro) es una cota inferior."),
        "parametros": parametros_contrato(cfg, calibracion),
    }


def escribir_salidas(carpeta: Path, tabla: pd.DataFrame, corredores: pd.DataFrame, semanas: pd.DataFrame,
                     calibracion: dict, resumen: dict) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    tabla.assign(fecha=tabla["fecha"].dt.date).to_csv(carpeta / "dimensionamiento_ejemplo.csv", index=False)
    corredores.assign(fecha=corredores["fecha"].dt.date).to_csv(carpeta / "flota_por_corredor.csv", index=False)
    semanas.assign(semana_inicio=semanas["semana_inicio"].dt.date, semana_fin=semanas["semana_fin"].dt.date).to_csv(
        carpeta / "nomina_semanal.csv", index=False)
    pd.DataFrame([(r, c, v) for r, cc in calibracion["composicion"].items() for c, v in cc.items()],
                 columns=["ruta_id", "clase_vehiculo", "participacion"]).to_csv(carpeta / "composicion_clases.csv",
                                                                               index=False)
    calibracion["capacidad_observada"].to_csv(carpeta / "capacidad_observada.csv", index=False)
    save_json(carpeta / "resumen.json", resumen)


def main(cfg: dict) -> int:
    """`run.py m1-operacion`: calibración con train y dimensionamiento de una demanda de EJEMPLO."""
    inicio_t = time.perf_counter()
    datos = cfg["datos"]
    detalle = pd.read_parquet(datos["detalle"])
    diaria = pd.read_parquet(datos["diaria"])
    regresos = leer_regresos(Path(datos["rutas"]))
    calibracion = calibrar(cfg, detalle, diaria, regresos)
    params = parametros_desde_config(cfg, calibracion, regresos)

    print(f"AVISO: demanda de EJEMPLO = pasajeros observados de {cfg['ejemplo']['mes']} (train). No es un pronóstico: "
          f"los pronósticos con cuantiles llegan en AN-5; operacion.cuantil = {params['globales']['cuantil']} no se "
          "aplica a esta demanda.")
    ejemplo = demanda_ejemplo(diaria, cfg["ejemplo"]["mes"], regresos, datos["inicio_entrenamiento"],
                              datos["fin_entrenamiento"])
    tabla = dimensionar(ejemplo, params)
    corredores = flota_por_corredor(tabla)
    g = params["globales"]
    semanas = nomina_semanal(corredores, g["ausentismo"], int(g["dias_descanso_semana"]))
    despachos_train = dimensionar(calibracion["demanda_train"], params)
    despachos_calibracion = _ventana(despachos_train, *calibracion["ventana_fraccion"])
    observados = calibracion["despachos_origen_train"]
    reproduccion = {"calibracion": reproduccion_despachos(despachos_calibracion, observados),
                    "train": reproduccion_despachos(despachos_train, observados),
                    "ejemplo": reproduccion_despachos(tabla, observados),
                    "dentro_de_ventana": reproduccion_global_y_por_ruta(
                        cfg, calibracion, regresos, _ventana(calibracion["demanda_train"], *calibracion["ventana_fraccion"]),
                        observados)}
    validacion = validar_fuera_de_ventana(cfg, detalle, diaria, regresos)
    resumen = _resumen(cfg, calibracion, corredores, semanas, reproduccion, validacion)
    carpeta = Path(cfg["salida"]["carpeta"])
    escribir_salidas(carpeta, tabla, corredores, semanas, calibracion, resumen)

    cal = resumen["calibracion"]
    print(f"\nρ* ({' a '.join(cal['ventana_fraccion'])}) = {cal['ocupacion_calibrada']:.4f}; "
          f"ρ usada = {cal['ocupacion_usada']}")
    print("f por ruta (" + " a ".join(cal["ventana_fraccion"]) + "): " +
          ", ".join(f"{r} {f:.3f}" for r, f in cal["fraccion_demanda_en_origen"].items()))
    print("m_r por ruta: " + ", ".join(f"{r} {m:.3f}" for r, m in cal["multiplicador_ocupacion"].items()))
    if cal["ocupacion_por_ruta_con_tope_1"]:
        print(f"ρ · m_r > 1 → tope 1 en: {', '.join(cal['ocupacion_por_ruta_con_tope_1'])}")
    for clave, texto in (("calibracion", "ventana de calibración"), ("train", "todo el train")):
        print(f"Despachos ORIGEN reproducidos con la ρ usada ({texto}): " +
              ", ".join(f"{r} {v['porcentaje']:.0f} %" for r, v in cal[f"reproduccion_despachos_{clave}"].items()))
    for nombre, bloque in (("dentro de ventana", cal["reproduccion_dentro_de_ventana"]),
                           ("fuera de ventana", cal["validacion_fuera_de_ventana"])):
        for variante in ("global", "por_ruta"):
            print(f"Reproducción {nombre}, ρ* {variante}: " + ", ".join(
                f"{r} {v['porcentaje']:.1f} %" for r, v in bloque[f"reproduccion_rho_{variante}"].items()))
    print("\nMáximo diario por corredor (EJEMPLO) y nómina semanal N*:")
    for c, v in resumen["maximo_diario_por_corredor"].items():
        n = resumen["nomina_semanal_por_corredor"][c]
        print(f"  {c}: {v['vehiculos']} vehículos, {v['conductores_servicio']} conductores en servicio, "
              f"{v['conductores']} de nómina diaria; N* máx. {n['max_nomina_semanal']} "
              f"({n['semanas_completas']}/{n['semanas']} semanas completas)")
    print(f"Escrito en {carpeta.as_posix()} ({time.perf_counter() - inicio_t:.1f} s)")
    return 0


__all__ = [
    "calibrar", "capacidad_efectiva", "capacidad_observada", "capacidad_supuesta", "conductores_nomina",
    "conductores_servicio", "demanda_ejemplo", "demanda_observada", "despachos_dia", "despachos_origen_diarios",
    "dimensionar", "escribir_salidas", "estimar_composicion", "flota_por_corredor", "fraccion_pasajeros_origen",
    "leer_regresos", "main", "ocupacion_calibrada", "parametros_contrato", "parametros_desde_config", "piernas_dia",
    "piernas_por_conductor", "multiplicadores_ocupacion", "nomina_semanal", "nomina_semanal_minima", "ocupacion_ruta",
    "reproduccion_despachos", "reproduccion_global_y_por_ruta", "tripulacion", "tripulacion_norma",
    "validar_fuera_de_ventana", "vehiculos_dia", "ventana_reciente", "vueltas_dia",
]
