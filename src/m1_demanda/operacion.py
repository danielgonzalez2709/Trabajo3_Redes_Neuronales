"""M1 — dimensionamiento de flota y conductores (CA-3; núcleo §5.4; spec de Camila §3.3; decisiones de Camila, 26-nov).

Notación: r = ruta, r' = su regreso según `rutas.yaml`, {r, r'} = corredor, d = día, c = clase de vehículo.
Las ecuaciones van en el mismo orden que el blog; cada una tiene su caso a mano en tests/test_operacion_m1.py.

    (1) cap_ef(r)  = Σ_c π(r, c) · cap(c)
            π(r, c): participación de la clase c en los despachos de ORIGEN de r en train (los de tránsito repiten el
            mismo vehículo en otra terminal, núcleo §5.1). cap(c): capacidad física SUPUESTA = máximo observado de
            pasajeros por despacho ORIGEN en train, recortado al rango del Decreto 1079/2015 arts. 2.2.1.4.7.3–4.
            Caso: 0,75 · 30 + 0,25 · 18 = 27.
    (2) desp(r, d) = ⌈ f(r) · D(r, d) / (cap_ef(r) · ρ) ⌉
            D: demanda (punto o cuantil) en pasajeros/día de la serie (ORIGEN + tránsito, núcleo §5.1).
            f(r) = Σ pasajeros ORIGEN / Σ pasajeros (ORIGEN + TRÁNSITO) en los últimos `calibracion.meses_fraccion`
            meses de train: la parte de D que sube en la terminal de origen y ocupa silla desde la salida.
            ρ ∈ (0, 1]: ocupación objetivo; por defecto ρ* (calibrada en train, abajo).
            Caso: f = 1, 100 / (27 · 0,8) = 4,63 → 5.
    (3) v(r)       = H / T_ciclo(r)
            H: horas de operación al día; T_ciclo = ida + regreso + alistamiento. Es una fracción, sin piso ni mínimo:
            con T_ciclo > H un vehículo cierra menos de un ciclo por día (18 / 22 = 0,818).
    (4) veh(r, d)  = ⌈ max(desp(r, d), desp(r', d)) / v(r) ⌉
            Cada vuelta es una ida Y un regreso: el sentido más cargado manda. Es la flota del CORREDOR: las filas de r
            y r' dan el mismo número y NO se suman (usar `flota_por_corredor`). Caso: ⌈max(5, 8) / 2⌉ = 4.
    (5') conductores por piernas, también por corredor y día [DECIDIDO, Camila, 26-nov, CA-3c]:
        (5a) P_r    = 2 · max(desp(r, d), desp(r', d))
                 piernas del corredor: cada vehículo de (4) hace ida y regreso, así que se cuentan también las piernas
                 VACÍAS de reposición del sentido menos cargado. Caso: 2 · max(5, 8) = 16 (no 5 + 8 = 13).
             h_r    = t_r / k_r,   k_r = 2 si t_r > 8 h (Res. 315/2013 art. 6, segundo conductor), si no 1
                 horas al volante de cada conductor en una pierna. SUPUESTO: el relevo que descansa a bordo no consume
                 jornada. Se exige h_r ≤ jornada máxima diaria.
             L_r    = max(1, ⌊ J_ef / h_r ⌋)
                 piernas por conductor y día; las piernas son INDIVISIBLES (nadie entrega el bus a mitad de camino).
                 Casos con J_ef = 7: Bogotá–Cali h = 5 → 1; Bogotá–Sogamoso h = 4 → 1; Pasto–Ipiales h = 1,5 → 4.
             C_serv = ⌈ k_r · P_r / L_r ⌉
                 Cuenta conducción, no disponibilidad del vehículo: no depende de H. El alistamiento NO se cuenta como
                 trabajo del conductor: es el tiempo del vehículo en terminal entre piernas, que en este supuesto
                 coincide con su descanso; la hora que separa J_ef = 7 de la jornada de 8 h cubre pausas y tareas en
                 terminal. Caso: ⌈1 · 16 / 1⌉ = 16; Bogotá–Cali ⌈2 · 16 / 1⌉ = 32.
        (5b) C_nom  = ⌈ C_serv / (1 − a) · 7 / (7 − s) ⌉
            a: ausentismo ∈ [0, 1); s = 1 día de descanso semanal (art. 161 CST). Se exige J_ef · (7 − s) ≤ jornada
            máxima semanal. `conductores` (= nómina) es la columna que pide §5.4. Caso: ⌈16 / 0,91 · 7/6⌉ = ⌈20,51⌉ = 21.

Calibración con train (nada posterior a `datos.fin_entrenamiento`, núcleo §5.4):
    ρ* = Σ_{r,d} f(r) · D(r, d) / cap_ef(r)  ÷  Σ_{r,d} despachos ORIGEN observados(r, d)
         sobre los días de la MISMA ventana que f (últimos `calibracion.meses_fraccion` meses de train) con registro en
         los dos sentidos del corredor [DECIDIDO, Camila, 26-nov, CA-3c]. Con ρ = ρ*, el modelo sin techo reproduce en
         agregado los despachos observados de esa ventana; por ruta no (un solo ρ global: ver resumen.json).
         Caso: (0,5 · 400 / 20 + 1 · 50 / 10) / (20 + 5) = 15 / 25 = 0,6.

Redondeo: ⌈x⌉ se calcula como ceil(x − ε) con ε = 1e-9, igual que la app (dimensionar.ts), para que el ruido de coma
flotante (p. ej. 56,7 / (27 · 0,7) = 3,0000000000000004) no agregue un despacho.
Costos (`costo_pasajero_sin_atender`, `costo_vehiculo_dia_sobrante`): §5.4 los exige y los usa negocio 3; `dimensionar`
no los usa.
"""

from __future__ import annotations

import math
import time
from collections.abc import Mapping
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


# ------------------------------------------------------------------------------------------ ecuaciones (1)–(5')

def capacidad_efectiva(composicion: Mapping[str, float], capacidades: Mapping[str, float]) -> float:
    """(1) cap_ef = Σ_c π(c) · cap(c). Clases en orden alfabético (mismo orden que la app)."""
    faltan = sorted(c for c in composicion if c not in capacidades)
    if faltan:
        raise ValueError(f"falta capacidad_pasajeros para las clases {faltan}")
    return float(sum(composicion[c] * capacidades[c] for c in sorted(composicion)))


def despachos_dia(demanda: float, cap_ef: float, ocupacion: float, fraccion_origen: float) -> int:
    """(2) desp = ⌈ f · D / (cap_ef · ρ) ⌉."""
    return max(0, _techo(fraccion_origen * demanda / (cap_ef * ocupacion)))


def vueltas_dia(horas: float, ciclo: float) -> float:
    """(3) v = H / T_ciclo (fracción; sin piso ni mínimo)."""
    return horas / ciclo


def vehiculos_dia(desp_ida: int, desp_regreso: int, vueltas: float) -> int:
    """(4) veh = ⌈ max(desp_ida, desp_regreso) / v ⌉."""
    return max(0, _techo(max(desp_ida, desp_regreso) / vueltas))


def tripulacion(recorrido_h: float, umbral_h: float) -> int:
    """k = 2 si el recorrido de un sentido es ESTRICTAMENTE mayor que el umbral (Res. 315/2013 art. 6: «duración
    superior a ocho (8) horas de recorrido»); si no, 1."""
    return 2 if recorrido_h > umbral_h else 1


def piernas_dia(desp_ida: int, desp_regreso: int) -> int:
    """(5a) P = 2 · max(desp_ida, desp_regreso): piernas del corredor, incluidas las vacías de reposición."""
    return 2 * max(desp_ida, desp_regreso)


def piernas_por_conductor(recorrido_h: float, k: int, jornada_efectiva: float) -> int:
    """(5a) L = max(1, ⌊ J_ef / (t / k) ⌋): piernas indivisibles que un conductor maneja en un día."""
    return max(1, _piso(jornada_efectiva / (recorrido_h / k)))


def conductores_servicio(desp_ida: int, desp_regreso: int, recorrido_h: float, k: int, jornada_efectiva: float) -> int:
    """(5a) C_serv = ⌈ k · P / L ⌉: cada pierna lleva k conductores y cada conductor cubre L piernas al día."""
    return max(0, _techo(k * piernas_dia(desp_ida, desp_regreso) / piernas_por_conductor(recorrido_h, k, jornada_efectiva)))


def conductores_nomina(c_serv: int, ausentismo: float, dias_descanso_semana: int) -> int:
    """(5b) C_nom = ⌈ C_serv / (1 − a) · 7 / (7 − s) ⌉."""
    return max(0, _techo(c_serv / (1 - ausentismo) * DIAS_SEMANA / (DIAS_SEMANA - dias_descanso_semana)))


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
    if ciclo < 2 * rec:
        raise ValueError(f"por_ruta.{ruta}.tiempo_ciclo_h = {ciclo} < 2 · tiempo_recorrido_h = {2 * rec}: "
                         "el ciclo debe cubrir la ida y el regreso")
    k = tripulacion(rec, g["umbral_segundo_conductor_h"])
    if rec / k > g["jornada_max_diaria_h"] + EPS:
        raise ValueError(f"por_ruta.{ruta}: tiempo_recorrido_h / k = {rec} / {k} = {rec / k:g} h supera "
                         f"jornada_max_diaria_h = {g['jornada_max_diaria_h']:g} h: los conductores no cubren la pierna")
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
    fraccion_demanda_en_origen}}, `por_clase` {clase: {capacidad_pasajeros}}, `composicion_clases` {ruta: {clase: π}} y
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
    out["despachos"] = [                                                                                     # (2)
        despachos_dia(dem, cap, g["ocupacion_objetivo"], f)
        for dem, cap, f in zip(out["demanda"], out["capacidad_efectiva"], out["fraccion_origen"], strict=True)
    ]
    out["despachos_regreso"] = _despachos_del_regreso(out)
    out["vueltas"] = [vueltas_dia(g["horas_operacion_h"], por_ruta[r]["tiempo_ciclo_h"]) for r in rutas]      # (3)
    out["vehiculos"] = [vehiculos_dia(a, b, v) for a, b, v in                                                 # (4)
                        zip(out["despachos"], out["despachos_regreso"], out["vueltas"], strict=True)]
    recorrido = [por_ruta[r]["tiempo_recorrido_h"] for r in rutas]
    out["tripulacion"] = [tripulacion(t, g["umbral_segundo_conductor_h"]) for t in recorrido]
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


def calibrar(cfg: dict, detalle: pd.DataFrame, diaria: pd.DataFrame, regresos: Mapping[str, str]) -> dict:
    """Todo lo que se estima con train: π, f, capacidad observada, cap_ef y ρ* (más las tablas para reproducirlos).
    f y ρ* usan la misma ventana: los últimos `calibracion.meses_fraccion` meses de train."""
    datos = cfg["datos"]
    inicio, fin = datos["inicio_entrenamiento"], datos["fin_entrenamiento"]
    capacidades = {c: p["capacidad_pasajeros"] for c, p in cfg["operacion"]["por_clase"].items()}
    composicion = estimar_composicion(detalle, inicio, fin, list(capacidades))
    ventana_f = ventana_reciente(inicio, fin, cfg["calibracion"]["meses_fraccion"])
    fraccion = fraccion_pasajeros_origen(detalle, *ventana_f)
    cap_ef = {r: capacidad_efectiva(comp, capacidades) for r, comp in composicion.items()}
    demanda_train = demanda_observada(diaria, inicio, fin, regresos, inicio, fin)
    desp_train = despachos_origen_diarios(detalle, inicio, fin)
    return {
        "composicion": composicion,
        "ventana_fraccion": ventana_f,
        "fraccion": fraccion,
        "fraccion_todo_train": fraccion_pasajeros_origen(detalle, inicio, fin),  # diagnóstico
        "capacidad_observada": capacidad_observada(detalle, inicio, fin),
        "capacidad_efectiva": cap_ef,
        "ocupacion_calibrada": ocupacion_calibrada(_ventana(demanda_train, *ventana_f), desp_train, fraccion, cap_ef),
        "ocupacion_calibrada_todo_train": ocupacion_calibrada(demanda_train, desp_train, fraccion, cap_ef),  # diagnóstico
        "demanda_train": demanda_train,
        "despachos_origen_train": desp_train,
    }


def parametros_desde_config(cfg: dict, calibracion: dict, ruta_regreso: Mapping[str, str]) -> dict:
    """Valores de `cfg["operacion"]` + lo calibrado con train, en el formato que recibe `dimensionar`."""
    o = cfg["operacion"]
    return {
        "globales": {k: v for k, v in o.items() if k not in GRUPOS},
        "por_ruta": {r: {**p, "fraccion_demanda_en_origen": calibracion["fraccion"][r]} for r, p in o["por_ruta"].items()},
        "por_clase": {c: dict(p) for c, p in o["por_clase"].items()},
        "composicion_clases": calibracion["composicion"],
        "ruta_regreso": dict(ruta_regreso),
    }


def parametros_contrato(cfg: dict, calibracion: dict) -> dict:
    """Parámetros al formato `ParametrosOperacion` de la app (núcleo §5.4): {valor, unidad, fuente | supuesto, nota?}.
    Meta: `meta.globales.<clave>`, `meta.por_ruta.<clave>` (común a las rutas) y `meta.por_clase.<clase>.<clave>`.
    Lo calibrado con train (f y composición) lleva `fuente` con el conjunto y la ventana usada."""
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

def _resumen(cfg: dict, calibracion: dict, corredores: pd.DataFrame, reproduccion: dict[str, dict]) -> dict:
    datos = cfg["datos"]
    capacidades = cfg["operacion"]["por_clase"]
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
            "ocupacion_usada": cfg["operacion"]["ocupacion_objetivo"],
            "limitacion_rho_global": ("ρ es uno solo para las seis rutas: con ρ = ρ* el total de despachos ORIGEN de la "
                                      "ventana de calibración se reproduce, pero cada ruta queda por encima o por debajo "
                                      "(reproduccion_despachos_calibracion, % por ruta)."),
            **{f"reproduccion_despachos_{k}": v for k, v in reproduccion.items()},
        },
        "maximo_diario_por_corredor": {
            c: {"vehiculos": int(g["vehiculos"].max()), "conductores_servicio": int(g["conductores_servicio"].max()),
                "conductores": int(g["conductores"].max())}
            for c, g in corredores.groupby("corredor")
        },
        "parametros": parametros_contrato(cfg, calibracion),
    }


def escribir_salidas(carpeta: Path, tabla: pd.DataFrame, corredores: pd.DataFrame, calibracion: dict,
                     resumen: dict) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    tabla.assign(fecha=tabla["fecha"].dt.date).to_csv(carpeta / "dimensionamiento_ejemplo.csv", index=False)
    corredores.assign(fecha=corredores["fecha"].dt.date).to_csv(carpeta / "flota_por_corredor.csv", index=False)
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
    despachos_train = dimensionar(calibracion["demanda_train"], params)
    despachos_calibracion = _ventana(despachos_train, *calibracion["ventana_fraccion"])
    observados = calibracion["despachos_origen_train"]
    reproduccion = {"calibracion": reproduccion_despachos(despachos_calibracion, observados),
                    "train": reproduccion_despachos(despachos_train, observados),
                    "ejemplo": reproduccion_despachos(tabla, observados)}
    resumen = _resumen(cfg, calibracion, corredores, reproduccion)
    carpeta = Path(cfg["salida"]["carpeta"])
    escribir_salidas(carpeta, tabla, corredores, calibracion, resumen)

    cal = resumen["calibracion"]
    print(f"\nρ* ({' a '.join(cal['ventana_fraccion'])}) = {cal['ocupacion_calibrada']:.4f}; "
          f"ρ usada = {cal['ocupacion_usada']}")
    print("f por ruta (" + " a ".join(cal["ventana_fraccion"]) + "): " +
          ", ".join(f"{r} {f:.3f}" for r, f in cal["fraccion_demanda_en_origen"].items()))
    for clave, texto in (("calibracion", "ventana de calibración"), ("train", "todo el train")):
        print(f"Despachos ORIGEN reproducidos ({texto}): " +
              ", ".join(f"{r} {v['porcentaje']:.0f} %" for r, v in cal[f"reproduccion_despachos_{clave}"].items()))
    print("\nMáximo diario por corredor (EJEMPLO):")
    for c, v in resumen["maximo_diario_por_corredor"].items():
        print(f"  {c}: {v['vehiculos']} vehículos, {v['conductores_servicio']} conductores en servicio, "
              f"{v['conductores']} de nómina")
    print(f"Escrito en {carpeta.as_posix()} ({time.perf_counter() - inicio_t:.1f} s)")
    return 0


__all__ = [
    "calibrar", "capacidad_efectiva", "capacidad_observada", "capacidad_supuesta", "conductores_nomina",
    "conductores_servicio", "demanda_ejemplo", "demanda_observada", "despachos_dia", "despachos_origen_diarios",
    "dimensionar", "escribir_salidas", "estimar_composicion", "flota_por_corredor", "fraccion_pasajeros_origen",
    "leer_regresos", "main", "ocupacion_calibrada", "parametros_contrato", "parametros_desde_config", "piernas_dia",
    "piernas_por_conductor",
    "reproduccion_despachos", "tripulacion", "vehiculos_dia", "ventana_reciente", "vueltas_dia",
]
