"""M1 — dimensionamiento de flota y conductores (CA-3; núcleo §5.4; spec de Camila §3.3, fórmula [PROPUESTO]).

Notación (r = ruta, r' = su regreso según `rutas.yaml`, d = día, c = clase de vehículo):

    (1) cap_ef(r)  = Σ_c π(r, c) · cap(c)
            π(r, c): participación de la clase c en los despachos de ORIGEN de r, estimada SOLO con train
            (núcleo §5.1 y §5.4: los despachos en tránsito repiten el mismo vehículo en otra terminal).
    (2) desp(r, d) = ⌈ f(r) · D(r, d) / (cap_ef(r) · ρ) ⌉
            D: demanda (punto o cuantil) en pasajeros/día; ρ: ocupación objetivo ∈ (0, 1];
            f(r) ∈ (0, 1]: fracción de la demanda que sube en el origen (1 = fórmula del Spec, ver riesgo en el reporte).
    (3) v(r)       = max(1, ⌊ H / T_ciclo(r) ⌋)
            H: horas de operación al día; T_ciclo: ida + regreso + alistamiento (horas). Si T_ciclo > H el piso da 0 y el
            Spec fija 1: queda MARCADO (`ciclo_excede_horas`). Con `vueltas_fraccionarias = 1` (desactivado por defecto)
            se usa v = H / T_ciclo < 1 (un vehículo tarda más de un día de operación en cerrar el ciclo).
    (4) veh(r, d)  = ⌈ max(desp(r, d), desp(r', d)) / v(r) ⌉
            Cada vuelta es una ida Y un regreso: el sentido más cargado manda. Es la flota del CORREDOR {r, r'}: la fila de
            r y la de r' dan el mismo número y NO se suman.
    (5) cond(r, d) = ⌈ veh · H · k(r) / J_ef · 1 / (1 − a) · 7 / (7 − s) ⌉
            J_ef: horas efectivas por conductor y día (descansos dentro de la jornada); a: ausentismo ∈ [0, 1);
            k(r) = 2 si la regla de segundo conductor está activa y el recorrido de un sentido supera el umbral (Res. 315
            de 2013, art. 6, según el informe CA-2 §1.3; desactivada por defecto), si no 1;
            s: días de descanso semanal por conductor (0 = no se modela; desactivado por defecto).

Redondeo: ⌈x⌉ se calcula como ceil(x − ε) y ⌊x⌋ como floor(x + ε) con ε = 1e-9, igual que la app (dimensionar.ts), para
que el ruido de coma flotante (p. ej. 56,7 / (27 · 0,7) = 3,0000000000000004) no agregue un despacho.
"""

from __future__ import annotations

import math
import time
from collections.abc import Mapping
from pathlib import Path

import pandas as pd
import yaml

from src.comun.results import save_json

EPS = 1e-9
COLUMNAS_ENTRADA = ("ruta_id", "fecha", "demanda")
TIPO_EJEMPLO = "EJEMPLO: observada en train, no es pronóstico"
ORIGEN = "ORIGEN"
GRUPOS = ("por_ruta", "por_clase")


def _techo(x: float) -> int:
    return int(math.ceil(x - EPS))


def _piso(x: float) -> int:
    return int(math.floor(x + EPS))


# ------------------------------------------------------------------------------------------- ecuaciones (1)–(5)

def capacidad_efectiva(composicion: Mapping[str, float], capacidades: Mapping[str, float]) -> float:
    """(1) cap_ef = Σ_c π(c) · cap(c). Clases en orden alfabético (mismo orden que la app)."""
    faltan = sorted(c for c in composicion if c not in capacidades)
    if faltan:
        raise ValueError(f"falta capacidad_pasajeros para las clases {faltan}")
    return float(sum(composicion[c] * capacidades[c] for c in sorted(composicion)))


def despachos_dia(demanda: float, cap_ef: float, ocupacion: float, fraccion_origen: float = 1.0) -> int:
    """(2) desp = ⌈ f · D / (cap_ef · ρ) ⌉."""
    return max(0, _techo(fraccion_origen * demanda / (cap_ef * ocupacion)))


def vueltas_dia(horas: float, ciclo: float, fraccionarias: bool = False) -> tuple[float, bool]:
    """(3) v = max(1, ⌊H / T_ciclo⌋). Devuelve (v, ciclo_excede_horas)."""
    excede = _piso(horas / ciclo) == 0
    if excede:
        return (horas / ciclo if fraccionarias else 1), True
    return _piso(horas / ciclo), False


def vehiculos_dia(desp_ida: int, desp_regreso: int, vueltas: float) -> int:
    """(4) veh = ⌈ max(desp_ida, desp_regreso) / v ⌉."""
    return max(0, _techo(max(desp_ida, desp_regreso) / vueltas))


def tripulacion(recorrido_h: float, activo: bool, umbral_h: float) -> int:
    """k = 2 si la regla está activa y el recorrido de un sentido es ESTRICTAMENTE mayor que el umbral; si no, 1."""
    return 2 if activo and recorrido_h > umbral_h else 1


def conductores_dia(vehiculos: int, horas: float, jornada_efectiva: float, ausentismo: float,
                    tripulacion: int = 1, dias_descanso_semana: int = 0) -> int:
    """(5) cond = ⌈ veh · H · k / J_ef · 1/(1 − a) · 7/(7 − s) ⌉."""
    horas_conductor = vehiculos * horas * tripulacion  # conductor-horas que pide la flota en el día
    return max(0, _techo(horas_conductor / jornada_efectiva / (1 - ausentismo) * 7 / (7 - dias_descanso_semana)))


# --------------------------------------------------------------------------------------------- validación

def _en(valor, nombre: str, lo: float, hi: float, lo_abierto: bool = False, hi_abierto: bool = False) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
        raise ValueError(f"{nombre} debe ser un número finito (vale {valor!r})")
    fuera = (valor <= lo if lo_abierto else valor < lo) or (valor >= hi if hi_abierto else valor > hi)
    if fuera:
        a, b = ("(" if lo_abierto else "["), (")" if hi_abierto else "]")
        raise ValueError(f"{nombre} = {valor} fuera de rango; debe estar en {a}{lo}, {hi}{b}")
    return float(valor)


def _bandera(valor, nombre: str) -> bool:
    if isinstance(valor, bool) or valor not in (0, 1):
        raise ValueError(f"{nombre} debe ser 0 (desactivado) o 1 (activado); vale {valor!r}")
    return bool(valor)


def validar_parametros(params: dict) -> None:
    """Rangos de dominio de las ecuaciones (1)–(5); error claro con el nombre del parámetro."""
    g = params["globales"]
    _en(g["ocupacion_objetivo"], "ocupacion_objetivo", 0, 1, lo_abierto=True)
    _en(g["cuantil"], "cuantil", 0, 1, lo_abierto=True, hi_abierto=True)
    _en(g["horas_operacion_h"], "horas_operacion_h", 0, 24, lo_abierto=True)
    jmax = _en(g["jornada_max_diaria_h"], "jornada_max_diaria_h", 0, 24, lo_abierto=True)
    _en(g["jornada_efectiva_h"], "jornada_efectiva_h", 0, jmax, lo_abierto=True)
    _en(g["ausentismo"], "ausentismo", 0, 1, hi_abierto=True)
    _bandera(g["segundo_conductor_activo"], "segundo_conductor_activo")
    _bandera(g["vueltas_fraccionarias"], "vueltas_fraccionarias")
    _en(g["umbral_segundo_conductor_h"], "umbral_segundo_conductor_h", 0, 24, lo_abierto=True)
    s = _en(g["dias_descanso_semana"], "dias_descanso_semana", 0, 6)
    if not s.is_integer():
        raise ValueError(f"dias_descanso_semana debe ser entero en 0..6 (vale {s})")
    for k in ("costo_pasajero_sin_atender", "costo_vehiculo_dia_sobrante"):
        if k in g:
            _en(g[k], k, 0, math.inf)
    for clase, p in params["por_clase"].items():
        _en(p["capacidad_pasajeros"], f"por_clase.{clase}.capacidad_pasajeros", 0, math.inf, lo_abierto=True)
    for ruta, p in params["por_ruta"].items():
        ciclo = _en(p["tiempo_ciclo_h"], f"por_ruta.{ruta}.tiempo_ciclo_h", 0, math.inf, lo_abierto=True)
        rec = _en(p["tiempo_recorrido_h"], f"por_ruta.{ruta}.tiempo_recorrido_h", 0, math.inf, lo_abierto=True)
        _en(p["fraccion_demanda_en_origen"], f"por_ruta.{ruta}.fraccion_demanda_en_origen", 0, 1, lo_abierto=True)
        if ciclo < 2 * rec:
            raise ValueError(f"por_ruta.{ruta}.tiempo_ciclo_h = {ciclo} < 2 · tiempo_recorrido_h = {2 * rec}: "
                             "el ciclo debe cubrir la ida y el regreso")
        regreso = params["ruta_regreso"].get(ruta)
        if regreso in params["por_ruta"]:
            pr = params["por_ruta"][regreso]
            for k in ("tiempo_ciclo_h", "tiempo_recorrido_h"):
                if pr[k] != p[k]:
                    raise ValueError(f"por_ruta.{ruta}.{k} ({p[k]}) ≠ por_ruta.{regreso}.{k} ({pr[k]}): el corredor "
                                     "comparte vehículos, así que ciclo y recorrido deben ser iguales en los dos sentidos")
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

def dimensionar(demanda: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Núcleo §5.4. Entrada `ruta_id, fecha, demanda`; salida = entrada + pasos intermedios + despachos, vehiculos,
    conductores. Para cada (r, d) debe venir también (r', d), con r' = `params["ruta_regreso"][r]` (ecuación (4)).

    `params` (valores ya resueltos): `globales` {clave: valor}, `por_ruta` {ruta: {clave: valor}}, `por_clase`
    {clase: {capacidad_pasajeros}}, `composicion_clases` {ruta: {clase: π}} (estimada con `estimar_composicion`) y
    `ruta_regreso` {ruta: ruta_regreso_id}.
    """
    validar_parametros(params)
    _validar_demanda(demanda, params)
    g = params["globales"]
    capacidades = {c: p["capacidad_pasajeros"] for c, p in params["por_clase"].items()}
    horas = g["horas_operacion_h"]

    out = demanda.copy()
    regreso = params["ruta_regreso"]
    out["ruta_regreso_id"] = out["ruta_id"].map(regreso)
    out["corredor"] = [" | ".join(sorted((r, regreso[r]))) for r in out["ruta_id"]]
    out["capacidad_efectiva"] = [capacidad_efectiva(params["composicion_clases"][r], capacidades) for r in out["ruta_id"]]
    out["despachos"] = [
        despachos_dia(dem, cap, g["ocupacion_objetivo"], params["por_ruta"][r]["fraccion_demanda_en_origen"])
        for r, dem, cap in zip(out["ruta_id"], out["demanda"], out["capacidad_efectiva"], strict=True)
    ]
    # Ecuación (4): despachos del regreso el MISMO día.
    clave = pd.MultiIndex.from_arrays([out["ruta_id"], out["fecha"]])
    desp = pd.Series(out["despachos"].to_numpy(), index=clave)
    buscado = pd.MultiIndex.from_arrays([out["ruta_regreso_id"], out["fecha"]])
    falta = ~buscado.isin(desp.index)
    if falta.any():
        i = int(falta.argmax())
        raise ValueError(f"falta la demanda del regreso {buscado[i][0]} el {buscado[i][1]} (para {out['ruta_id'].iloc[i]}); "
                         "dimensionar necesita los dos sentidos del corredor cada día")
    out["despachos_regreso"] = desp.reindex(buscado).to_numpy()

    vueltas = {r: vueltas_dia(horas, p["tiempo_ciclo_h"], bool(g["vueltas_fraccionarias"]))
               for r, p in params["por_ruta"].items()}
    out["vueltas"] = [vueltas[r][0] for r in out["ruta_id"]]
    out["ciclo_excede_horas"] = [vueltas[r][1] for r in out["ruta_id"]]
    out["vehiculos"] = [vehiculos_dia(a, b, v) for a, b, v in
                        zip(out["despachos"], out["despachos_regreso"], out["vueltas"], strict=True)]
    out["tripulacion"] = [tripulacion(params["por_ruta"][r]["tiempo_recorrido_h"], bool(g["segundo_conductor_activo"]),
                                      g["umbral_segundo_conductor_h"]) for r in out["ruta_id"]]
    out["conductores"] = [
        conductores_dia(v, horas, g["jornada_efectiva_h"], g["ausentismo"], k, int(g["dias_descanso_semana"]))
        for v, k in zip(out["vehiculos"], out["tripulacion"], strict=True)
    ]
    for col in ("despachos", "despachos_regreso", "vehiculos", "tripulacion", "conductores"):
        out[col] = out[col].astype("int64")
    return out


# ------------------------------------------------------------------------- estimaciones con train (sin fuga)

def _ventana(detalle: pd.DataFrame, inicio, fin) -> pd.DataFrame:
    """Filas con inicio <= fecha <= fin (ambos incluidos). Nada posterior a `fin` sale de aquí (núcleo §5.4)."""
    f = pd.to_datetime(detalle["fecha"])
    return detalle[(f >= pd.Timestamp(inicio)) & (f <= pd.Timestamp(fin))]


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


def capacidad_observada(detalle: pd.DataFrame, inicio, fin, percentil: float) -> pd.DataFrame:
    """Percentil de pasajeros/despacho por clase en los días ORIGEN de train (dato para justificar el supuesto de
    capacidad; cada fila del detalle es la suma de un día, así que es un promedio diario, no un vehículo)."""
    o = _ventana(detalle[(detalle["tipo_despacho"] == ORIGEN) & (detalle["despachos"] > 0)], inicio, fin)
    ppd = (o["pasajeros"] / o["despachos"]).groupby(o["clase_vehiculo"])
    return pd.DataFrame({
        "pasajeros_por_despacho": ppd.quantile(percentil), "n_dias": ppd.size(), "maximo": ppd.max(),
    }).rename_axis("clase_vehiculo").reset_index()


def fraccion_pasajeros_origen(detalle: pd.DataFrame, inicio, fin) -> dict[str, float]:
    """Diagnóstico: pasajeros ORIGEN / (ORIGEN + TRANSITO) por ruta en train (candidato para f(r), ec. (2))."""
    t = _ventana(detalle, inicio, fin)
    tot = t.groupby("ruta_id")["pasajeros"].sum()
    ori = t[t["tipo_despacho"] == ORIGEN].groupby("ruta_id")["pasajeros"].sum()
    return {r: float(ori.get(r, 0) / tot[r]) for r in sorted(tot.index)}


# --------------------------------------------------------------------------------------------- configuración

def parametros_desde_config(cfg: dict, composicion: dict, ruta_regreso: dict) -> dict:
    """Valores de `cfg["operacion"]` (+ composición y regresos) en el formato que recibe `dimensionar`."""
    o = cfg["operacion"]
    return {
        "globales": {k: v for k, v in o.items() if k not in GRUPOS},
        "por_ruta": {r: dict(p) for r, p in o["por_ruta"].items()},
        "por_clase": {c: dict(p) for c, p in o["por_clase"].items()},
        "composicion_clases": composicion,
        "ruta_regreso": dict(ruta_regreso),
    }


def parametros_contrato(cfg: dict, composicion: dict) -> dict:
    """Parámetros al formato `ParametrosOperacion` de la app (núcleo §5.4): {valor, unidad, fuente | supuesto, nota?}.
    La composición sale de los datos de train, así que lleva `fuente` con la ventana usada."""
    o, meta, d = cfg["operacion"], cfg["meta"], cfg["datos"]

    def par(valor, m: dict) -> dict:
        p = {"valor": valor, "unidad": m["unidad"]}
        p.update({"fuente": m["fuente"]} if "fuente" in m else {"supuesto": True})
        if m.get("nota"):
            p["nota"] = m["nota"]
        return p

    fuente_comp = (f"{cfg['composicion']['fuente']}; despachos de ORIGEN entre {d['inicio_entrenamiento']} y "
                   f"{d['fin_entrenamiento']} (train)")
    return {
        "globales": {k: par(v, meta["globales"][k]) for k, v in o.items() if k not in GRUPOS},
        "por_ruta": {r: {k: par(v, meta["por_ruta"][r][k]) for k, v in p.items()} for r, p in o["por_ruta"].items()},
        "por_clase": {c: {k: par(v, meta["por_clase"][c][k]) for k, v in p.items()} for c, p in o["por_clase"].items()},
        "composicion_clases": {
            r: {c: {"valor": v, "unidad": "fracción de los despachos de ORIGEN", "fuente": fuente_comp}
                for c, v in comp.items()}
            for r, comp in composicion.items()
        },
    }


# ------------------------------------------------------------------------------------------------------- main

def _leer_regresos(ruta_yaml: Path) -> dict[str, str]:
    rutas = yaml.safe_load(ruta_yaml.read_text(encoding="utf-8"))["rutas"]
    return {r["ruta_id"]: r["ruta_regreso_id"] for r in rutas}


def demanda_ejemplo(diaria: pd.DataFrame, mes: str, fin_entrenamiento) -> pd.DataFrame:
    """Demanda de EJEMPLO mientras no hay pronósticos (AN-5): pasajeros observados de un mes de train."""
    f = pd.to_datetime(diaria["fecha"])
    sel = diaria[f.dt.strftime("%Y-%m") == mes]
    if sel.empty:
        raise ValueError(f"ejemplo.mes = {mes}: no hay datos de ese mes")
    if pd.to_datetime(sel["fecha"]).max() > pd.Timestamp(fin_entrenamiento):
        raise ValueError(f"ejemplo.mes = {mes} pasa del fin de entrenamiento ({fin_entrenamiento}); use un mes de train")
    out = sel[["ruta_id", "fecha", "pasajeros"]].rename(columns={"pasajeros": "demanda"}).reset_index(drop=True)
    out["fecha"] = pd.to_datetime(out["fecha"])
    return out


def main(cfg: dict) -> int:
    """`run.py m1-operacion`: composición con train, capacidad observada y dimensionamiento de una demanda de EJEMPLO."""
    inicio_t = time.perf_counter()
    d = cfg["datos"]
    detalle = pd.read_parquet(d["detalle"])
    regresos = _leer_regresos(Path(d["rutas"]))
    clases = list(cfg["operacion"]["por_clase"])
    comp = estimar_composicion(detalle, d["inicio_entrenamiento"], d["fin_entrenamiento"], clases)
    params = parametros_desde_config(cfg, comp, regresos)

    ejemplo = demanda_ejemplo(pd.read_parquet(d["diaria"]), cfg["ejemplo"]["mes"], d["fin_entrenamiento"])
    print(f"AVISO: demanda de EJEMPLO = pasajeros observados de {cfg['ejemplo']['mes']} (train). No es un pronóstico: "
          f"los pronósticos con cuantiles llegan en AN-5; operacion.cuantil = {params['globales']['cuantil']} no se "
          "aplica a esta demanda.")
    tabla = dimensionar(ejemplo, params)
    tabla.insert(3, "tipo_demanda", TIPO_EJEMPLO)

    carpeta = Path(cfg["salida"]["carpeta"])
    carpeta.mkdir(parents=True, exist_ok=True)
    tabla.assign(fecha=tabla["fecha"].dt.date).to_csv(carpeta / "dimensionamiento_ejemplo.csv", index=False)
    pd.DataFrame([(r, c, v) for r, cc in comp.items() for c, v in cc.items()],
                 columns=["ruta_id", "clase_vehiculo", "participacion"]).to_csv(carpeta / "composicion_clases.csv",
                                                                               index=False)
    obs = capacidad_observada(detalle, d["inicio_entrenamiento"], d["fin_entrenamiento"],
                              cfg["capacidad_observada"]["percentil"])
    obs.to_csv(carpeta / "capacidad_observada.csv", index=False)

    por_corredor = tabla.drop_duplicates(["corredor", "fecha"])  # la flota del corredor se cuenta UNA vez
    resumen = {
        "aviso": f"Demanda de EJEMPLO ({TIPO_EJEMPLO}); mes {cfg['ejemplo']['mes']}.",
        "ventana_train": [str(d["inicio_entrenamiento"]), str(d["fin_entrenamiento"])],
        "fraccion_pasajeros_origen_train": fraccion_pasajeros_origen(detalle, d["inicio_entrenamiento"],
                                                                     d["fin_entrenamiento"]),
        "rutas_con_ciclo_mayor_que_horas": sorted(tabla.loc[tabla["ciclo_excede_horas"], "ruta_id"].unique()),
        "maximo_diario_por_corredor": {
            c: {"vehiculos": int(g["vehiculos"].max()), "conductores": int(g["conductores"].max())}
            for c, g in por_corredor.groupby("corredor")
        },
        "parametros": parametros_contrato(cfg, comp),
    }
    save_json(carpeta / "resumen.json", resumen)

    if resumen["rutas_con_ciclo_mayor_que_horas"]:
        print("AVISO: tiempo_ciclo_h > horas_operacion_h en", ", ".join(resumen["rutas_con_ciclo_mayor_que_horas"]),
              "→ vueltas = 1 (mínimo del Spec); con vueltas_fraccionarias = 1 serían H / T_ciclo.")
    print("\nMáximo diario por corredor (EJEMPLO):")
    for c, v in resumen["maximo_diario_por_corredor"].items():
        print(f"  {c}: {v['vehiculos']} vehículos, {v['conductores']} conductores")
    print(f"Escrito en {carpeta.as_posix()} ({time.perf_counter() - inicio_t:.1f} s)")
    return 0


__all__ = [
    "capacidad_efectiva", "capacidad_observada", "conductores_dia", "despachos_dia", "dimensionar", "estimar_composicion",
    "fraccion_pasajeros_origen", "main", "parametros_contrato", "parametros_desde_config", "tripulacion",
    "vehiculos_dia", "vueltas_dia",
]
