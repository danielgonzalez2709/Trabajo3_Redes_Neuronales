"""M1 — hipótesis (sección 5) e implicaciones para el modelado (sección 6) del análisis descriptivo (CA-4, Camila).

Cada hipótesis tiene dos piezas separadas: una función `_calc_*` que CALCULA las cifras a partir de `res` (las tablas de
`eda.calcular_resultados`) y una función `_texto_*` que las convierte en el texto de `resultado`. Los veredictos son siempre
`pendiente` hasta modelar (núcleo §5.12, sección 7). Este módulo no lee archivos ni escribe nada; `eda.py` lo importa.

También guarda las constantes y utilidades compartidas con `eda.py` (umbrales con nombre, periodos, columnas de calendario).
"""

from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------------------------------------- constantes compartidas
SEMANAL = 7  # periodo semanal del MSTL (días)
ANUAL = 365  # periodo anual del MSTL (días)
MIN_VENTANA_REZAGOS_SEMANAS = 4  # ventana mínima de rezagos propuesta: 4 semanas (28 días)

# Umbrales de la spec de Camila §3.0 (hipótesis H-M1-1, 7): los textos y las comparaciones salen de aquí.
UMBRAL_TRANSITO_PCT = 50.0  # tránsito > origen
UMBRAL_SIN_TRANSITO_PCT = 6.0  # «casi sin tránsito»
TRANSITO_ESPERADO_MIN_PCT = 40.0
TRANSITO_ESPERADO_MAX_PCT = 70.0
UMBRAL_RAZON_SEMANAL = 1.2  # razón máx/mín del perfil semanal que se espera superar

# hipótesis → (columnas de calendario.parquet, ¿la columna es por ciudad de origen: `<columna>_<DIVIPOLA origen>`?)
COLUMNAS_CALENDARIO: dict[str, tuple[tuple[str, ...], bool]] = {
    "festivos y puentes": (("festivo", "puente"), False),
    "vacaciones escolares": (("vacaciones_escolares",), True),  # Camila 26-nov: ciudad de origen de cada ruta
    "Semana Santa": (("semana_santa",), False),
}
FALTA_CALENDARIO = "falta el calendario de CA-1"
EV = "results/data/m1/eda/"


def _n(x: float | None, d: int = 2) -> str:
    """Número con coma decimal (texto en español)."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/d"
    return f"{x:.{d}f}".replace(".", ",")


def _g(x: float) -> str:
    """Umbral sin ceros sobrantes y con coma decimal (50 → «50», 1.2 → «1,2»)."""
    return f"{x:g}".replace(".", ",")


def _hipotesis(*, id_: int, enunciado: str, justificacion: str, esperada: str, figura: str, resultado: str,
               evidencia: str) -> dict:
    return {
        "id": f"H-M1-{id_}",
        "enunciado": enunciado,
        "justificacion": justificacion,
        "evidencia_esperada": esperada,
        "figura_o_tabla": figura,
        "resultado": resultado,
        "veredicto": "pendiente",  # §5.12: se cierra después de modelar
        "evidencia": evidencia,
    }


# ---------------------------------------------------------------------------------------------- cálculo por hipótesis
def _calc_semana(res: dict) -> dict:
    ps, rs = res["perfil_semanal"], res["descomposicion_resumen"]
    rutas = []
    for ruta, g in ps.groupby("ruta_id"):
        pico, valle = g.loc[g["media"].idxmax()], g.loc[g["media"].idxmin()]
        rutas.append({"ruta": ruta, "pico_dia": pico["dia"], "pico_razon": pico["razon_vs_media_semanal"],
                      "valle_dia": valle["dia"], "valle_razon": valle["razon_vs_media_semanal"]})
    return {"rutas": rutas, "fuerza_min": rs["fuerza_semanal"].min(), "fuerza_max": rs["fuerza_semanal"].max(),
            "razon_min": rs["razon_max_min_semanal"].min(), "razon_max": rs["razon_max_min_semanal"].max()}


def _calc_calendario(res: dict, nombre: str) -> dict:
    """Estado de una hipótesis de calendario: sin calendario, columna faltante, o cifras por columna."""
    if res["calendario"] is None:
        return {"estado": "sin_calendario"}
    cols, por_origen = COLUMNAS_CALENDARIO[nombre]
    faltan = [c for c in cols if c in res["calendario_faltan"]]
    faltan += [f for f in res["calendario_faltan"] if por_origen and f.startswith(cols[0] + "_")]
    if faltan:
        return {"estado": "falta_columna", "columnas": faltan}
    por_columna, vacias = {}, []
    for c in cols:
        e = res["efectos"][c]
        if e.empty:
            vacias.append(c)
            continue
        por_columna[c] = {
            "dias_max": int(e["n_dias"].max()), "mediana_min": e["razon_mediana"].min(),
            "mediana_max": e["razon_mediana"].max(),
            "ponderada": float(np.average(e["razon_mediana"], weights=e["n_dias"])),
            "nulos_excluidos": int(e["n_nulos_excluidos"].sum()),
        }
    return {"estado": "ok", "por_columna": por_columna, "vacias": vacias, "por_origen": por_origen,
            "ventana": res["params"]["ventana_calendario_dias"], "sha256": res.get("calendario_sha256")}


def _calc_fin_de_anio(res: dict) -> dict:
    pm, hall = res["perfil_mensual"], res["hallazgos"]
    comp = pm[pm["anio_completo"]]
    por_mes = comp[comp["mes"].isin([1, 12])].groupby(["ruta_id", "mes"])["razon_vs_media_anual"].mean().unstack()
    if not ({1, 12} <= set(por_mes.columns) and len(por_mes)):
        return {"disponible": False}
    cons = hall["consistencia_anual"]
    return {"disponible": True, "anios": sorted(int(a) for a in comp["anio"].unique()),
            "dic": (por_mes[12].min(), por_mes[12].max()), "ene": (por_mes[1].min(), por_mes[1].max()),
            "anios_correlacion": cons["anios"], "corr_por_ruta": cons["corr_por_ruta"]}


def _calc_pospandemia(res: dict) -> dict:
    ten = res["tendencia"]
    var_jd = ten.dropna(subset=["variacion_pct_jun_dic"])
    var_ea = ten.dropna(subset=["variacion_pct_ene_abr"])
    if not len(var_jd):
        return {"disponible": False}
    rango = lambda g, col: (g[col].min(), g[col].max())  # noqa: E731
    return {"disponible": True,
            "jun_dic": [(int(a), rango(g, "variacion_pct_jun_dic")) for a, g in var_jd.groupby("anio")],
            "ene_abr": [(int(a), rango(g, "variacion_pct_ene_abr")) for a, g in var_ea.groupby("anio")]}


def _calc_transito(res: dict) -> dict:
    tr = res["transito_anio"]
    return {"min": tr["pct_transito"].min(), "max": tr["pct_transito"].max(),
            "superan": int((tr["pct_transito"] > UMBRAL_TRANSITO_PCT).sum()), "combinaciones": len(tr),
            "casi_sin": sorted(set(tr.loc[tr["pct_transito"] < UMBRAL_SIN_TRANSITO_PCT, "ruta_id"])),
            "con_transito": int((tr["pasajeros_transito"] > 0).sum())}


def _calc_clases(res: dict) -> dict:
    m, a = res["hallazgos"]["microbus"], res["hallazgos"]["asimetria_clases"]
    ultimo: list[dict] = []
    if a.get("disponible"):
        filas = a["pct_por_ruta_anio_clase"]
        for ruta in a["rutas"]:
            de_ruta = [x for x in filas if x["ruta_id"] == ruta]
            if not de_ruta:
                continue
            anio = max(x["anio"] for x in de_ruta)
            top = sorted((x for x in de_ruta if x["anio"] == anio), key=lambda x: -x["pct"])[:4]
            ultimo.append({"ruta": ruta, "clases": [(x["clase_vehiculo"], x["pct"]) for x in top]})
    return {"microbus": m, "asimetria": a, "ultimo_anio": ultimo}


# ---------------------------------------------------------------------------------------------- texto por hipótesis
def _texto_semana(c: dict, inicio: str) -> str:
    partes = [f"{r['ruta']}: pico {r['pico_dia']} ({_n(r['pico_razon'])}×), valle {r['valle_dia']} ({_n(r['valle_razon'])}×)"
              for r in c["rutas"]]
    return (f"Desde {inicio}, razón día/media semanal por ruta: " + "; ".join(partes)
            + f". Fuerza de la estacionalidad semanal (MSTL sobre log(1+y)) entre {_n(c['fuerza_min'])} y {_n(c['fuerza_max'])}; "
              f"razón máx/mín del ciclo semanal entre {_n(c['razon_min'])} y {_n(c['razon_max'])}.")


def _texto_calendario(c: dict) -> tuple[str, str]:
    if c["estado"] == "sin_calendario":
        return FALTA_CALENDARIO, "data/processed/m1/calendario.parquet no existe (CA-1 pendiente)"
    if c["estado"] == "falta_columna":
        return f"falta la columna {', '.join(c['columnas'])} en calendario.parquet", "calendario.parquet sin esa columna"
    partes = []
    for col, v in c["por_columna"].items():
        sufijo = " (por ciudad de origen de cada ruta)" if c["por_origen"] else ""
        partes.append(
            f"{col}{sufijo}: {v['dias_max']} días marcados como máximo por ruta; razón mediana contra el mismo día de la "
            f"semana ±{c['ventana']} días entre {_n(v['mediana_min'])} y {_n(v['mediana_max'])} según ruta "
            f"(promedio ponderado {_n(v['ponderada'])})"
        )
        if v["nulos_excluidos"]:
            n = v["nulos_excluidos"]
            partes.append(f"se excluyeron {n} {'día' if n == 1 else 'días'}-ruta con marca nula de {col} (vacío sin fuente)")
    if c["vacias"]:
        partes.append(f"sin días marcados o sin vecinos suficientes en: {', '.join(c['vacias'])}")
    sha = c["sha256"]
    origen = f"data/processed/m1/calendario.parquet (CA-1, sha256 {sha})" if sha else "data/processed/m1/calendario.parquet (CA-1)"
    return "; ".join(partes), EV + "efectos_calendario.csv sobre " + origen


def _texto_fin_de_anio(c: dict) -> str:
    if not c["disponible"]:
        return "no hay años completos para comparar diciembre y enero"
    anios = c["anios_correlacion"]
    corr = ""
    if len(anios) >= 2:
        corr = (f" Correlación del perfil mensual entre {anios[0]} y {anios[1]} por ruta: "
                + ", ".join(f"{k} {_n(v)}" for k, v in c["corr_por_ruta"].items()) + ".")
    return (f"Media diaria del mes / media diaria del año (años completos {', '.join(map(str, c['anios']))}, promedio de años): "
            f"diciembre entre {_n(c['dic'][0])} y {_n(c['dic'][1])}; enero entre {_n(c['ene'][0])} y {_n(c['ene'][1])} "
            f"según ruta.{corr} La tendencia no está separada ({len(c['anios'])} años completos).")


def _texto_pospandemia(c: dict) -> str:
    if not c["disponible"]:
        return "no hay dos años comparables"
    partes = [f"jun-dic {a} vs {a - 1}: de {_n(lo, 1)} % a {_n(hi, 1)} % según ruta" for a, (lo, hi) in c["jun_dic"]]
    partes += [f"ene-abr {a} vs {a - 1}: de {_n(lo, 1)} % a {_n(hi, 1)} %" for a, (lo, hi) in c["ene_abr"]]
    return "Variación de la media diaria entre ventanas equivalentes: " + "; ".join(partes) + ". 2020 no está en los datos."


def _texto_transito(c: dict) -> str:
    return (f"Proporción de tránsito sobre el total por ruta y año: entre {_n(c['min'], 1)} % y {_n(c['max'], 1)} %; en "
            f"{c['superan']} de {c['combinaciones']} combinaciones ruta-año el tránsito supera al origen. Casi sin tránsito "
            f"(< {_g(UMBRAL_SIN_TRANSITO_PCT)} %): " + (", ".join(c["casi_sin"]) or "ninguna")
            + f". Con tránsito > 0: {c['con_transito']} filas.")


def _texto_salto(s: dict) -> str:
    if not s.get("disponible"):
        return s["motivo"]
    return (
        f"{s['ruta_id']}: tránsito/día {_n(s['transito_dia_antes'], 0)} ({s['meses_antes'][0]} a {s['meses_antes'][1]}) → "
        f"{_n(s['transito_dia_despues'], 0)} ({s['meses_despues'][0]} a {s['meses_despues'][1]}), razón {_n(s['razon_transito'])}; "
        f"origen/día {_n(s['origen_dia_antes'], 0)} → {_n(s['origen_dia_despues'], 0)} (razón {_n(s['razon_origen'])}); "
        f"despachos de tránsito/día {_n(s['despachos_transito_dia_antes'], 1)} → {_n(s['despachos_transito_dia_despues'], 1)}; "
        f"MICROBUS en tránsito/día {_n(s['microbus_transito_dia_antes'], 0)} → {_n(s['microbus_transito_dia_despues'], 0)}."
    )


def _texto_clases(c: dict) -> str:
    m, a = c["microbus"], c["asimetria"]
    partes = []
    if m.get("disponible"):
        partes.append(f"{m['clase']} en {m['ruta_id']}, % de pasajeros por año: "
                      + ", ".join(f"{k}: {_n(v, 1)}" for k, v in m["pct_por_anio"].items()))
    else:
        partes.append(m["motivo"])
    if a.get("disponible"):
        partes += [f"{u['ruta']} (último año): " + ", ".join(f"{cl} {_n(p, 1)} %" for cl, p in u["clases"])
                   for u in c["ultimo_anio"]]
    else:
        partes.append(a["motivo"])
    return " | ".join(partes)


def _texto_escala(esc: dict) -> str:
    return (f"Media diaria jun-dic {esc['anio']} por ruta: " + "; ".join(f"{k}: {_n(v, 0)}" for k, v in esc["por_ruta"].items()) + ".")


# ---------------------------------------------------------------------------------------------- hipótesis
def construir_hipotesis(res: dict) -> list[dict]:
    """H-M1-1…10 (sección 5). Todas con veredicto `pendiente`; la evidencia descriptiva va en `resultado`."""
    p, hall = res["params"], res["hallazgos"]
    inicio, ventana = p["inicio_analisis"], p["ventana_calendario_dias"]
    r2, e2 = _texto_calendario(_calc_calendario(res, "festivos y puentes"))
    r3, e3 = _texto_calendario(_calc_calendario(res, "vacaciones escolares"))
    r4, e4 = _texto_calendario(_calc_calendario(res, "Semana Santa"))
    return [
        _hipotesis(
            id_=1,
            enunciado="La demanda depende del día de la semana: el perfil semanal tiene una razón máximo/mínimo claramente "
                      "mayor que 1 en las seis rutas, y esa estructura se repite cada siete días.",
            justificacion="Viaje intermunicipal por trabajo, estudio y ocio concentra la demanda en ciertos días (supuesto a contrastar).",
            esperada=f"Razón máx/mín del perfil semanal > {_g(UMBRAL_RAZON_SEMANAL)} en las seis rutas y fuerza de estacionalidad "
                     "semanal alta; se refutaría con perfiles planos.",
            figura="perfil_semanal.csv; descomposicion_resumen.csv; figuras m1_perfil_semanal.png y m1_descomposicion_*.png",
            resultado=_texto_semana(_calc_semana(res), inicio),
            evidencia=EV + "perfil_semanal.csv; " + EV + "descomposicion_resumen.csv"),
        _hipotesis(
            id_=2,
            enunciado="Los festivos y los puentes (festivo trasladado a lunes) aumentan la demanda de salida y retorno "
                      "respecto del mismo día de la semana en días vecinos.",
            justificacion="Los días de descanso prolongado concentran viajes; calendario conocible con meses de antelación (regla 0.9).",
            esperada=f"Razón mediana > 1 en días marcados, contra el mismo día de la semana ±{ventana} días sin marca.",
            figura="efectos_calendario.csv", resultado=r2, evidencia=e2),
        _hipotesis(
            id_=3,
            enunciado="Las vacaciones escolares elevan la demanda frente a los mismos días de la semana fuera de ellas; cada "
                      "ruta usa el calendario de su ciudad de origen.",
            justificacion="Calendario escolar como determinante de viajes familiares (supuesto a contrastar); se usa la columna "
                          "vacaciones_escolares_<DIVIPOLA de origen> de cada ruta (decisión de Camila, 26-nov).",
            esperada=f"Razón mediana > 1 en días de vacaciones escolares de la ciudad de origen (ventana ±{ventana} días).",
            figura="efectos_calendario.csv", resultado=r3, evidencia=e3),
        _hipotesis(
            id_=4,
            enunciado="Semana Santa modifica la demanda respecto del mismo día de la semana en semanas vecinas, con un "
                      "patrón distinto entre días de la semana (salida y regreso).",
            justificacion="Festividad móvil con puentes largos; su fecha cambia cada año, por eso se toma del calendario.",
            esperada="Razón mediana ≠ 1 en días de Semana Santa, con signos distintos por día.",
            figura="efectos_calendario.csv", resultado=r4, evidencia=e4),
        _hipotesis(
            id_=5,
            enunciado="Diciembre y enero tienen una demanda diaria superior a la media del año en las rutas con mayor "
                      "tránsito de pasajeros, y esa temporada no se explica solo por la tendencia.",
            justificacion="Fin de año como temporada alta (viajes de vacaciones y reuniones familiares). Por decisión de Camila "
                          "(26-nov) la hipótesis se mide solo con el perfil mensual (media del mes / media del año); el "
                          "calendario ya existe y su columna fin_de_anio es la variable de fin de año que usan los modelos.",
            esperada="Razón mes/año > 1 en diciembre o enero en la mayoría de las rutas; refutada si todas quedan por debajo de 1.",
            figura="perfil_mensual.csv; figura m1_perfil_mensual.png",
            resultado=_texto_fin_de_anio(_calc_fin_de_anio(res)), evidencia=EV + "perfil_mensual.csv"),
        _hipotesis(
            id_=6,
            enunciado="La demanda de 2021 a 2023 crece en todas las rutas respecto del año previo (recuperación posterior a "
                      "la pandemia, medida como tendencia).",
            justificacion="La caída de 2020 no está en los datos; solo se observa la tendencia 2021-2023, que mezcla recuperación "
                          "y cambios de reporte (núcleo §5.1).",
            esperada="Variación positiva de la media de jun-dic 2022 vs 2021 y 2023 vs 2022 en las seis rutas.",
            figura="tendencia_anual.csv; figuras m1_tendencia_anual.png y m1_series_rutas.png",
            resultado=_texto_pospandemia(_calc_pospandemia(res)), evidencia=EV + "tendencia_anual.csv"),
        _hipotesis(
            id_=7,
            enunciado="En las rutas desde y hacia Bogotá el tránsito (pasajeros que suben en terminales intermedias) pesa "
                      "tanto como el origen; en Pasto-Ipiales casi no hay tránsito.",
            justificacion="El conjunto registra pasajeros por terminal y tipo de despacho; la serie suma origen y tránsito (núcleo §5.1).",
            esperada=f"Proporción de tránsito entre {_g(TRANSITO_ESPERADO_MIN_PCT)} % y {_g(TRANSITO_ESPERADO_MAX_PCT)} % en los "
                     f"corredores de Bogotá y < {_g(UMBRAL_SIN_TRANSITO_PCT)} % en Pasto-Ipiales.",
            figura="transito_por_ruta_anio.csv; figura m1_transito_origen.png",
            resultado=_texto_transito(_calc_transito(res)), evidencia=EV + "transito_por_ruta_anio.csv"),
        _hipotesis(
            id_=8,
            enunciado="La demanda de tránsito de Bogotá→Sogamoso cambia de régimen desde noviembre de 2022 (el origen no).",
            justificacion="Auditoría de DA-3: salto del tránsito con despachos casi constantes; causa no verificada (¿cambio de reporte?).",
            esperada="Razón tránsito después/antes claramente mayor que 1 con razón de origen cercana a 1.",
            figura="transito_mensual.csv; hallazgos.json; figura m1_transito_mensual.png",
            resultado=_texto_salto(hall["salto_transito"]), evidencia=EV + "transito_mensual.csv; " + EV + "hallazgos.json"),
        _hipotesis(
            id_=9,
            enunciado="La composición por clase de vehículo cambia con el tiempo y entre sentidos: MICROBUS desaparece de "
                      "Bogotá→Cali en 2023 y Pasto-Ipiales es asimétrica entre ida y regreso.",
            justificacion="Afecta capacidad por clase y dimensionamiento de flota (CA-3); puede ser cambio de reporte.",
            esperada="Participación de MICROBUS = 0 en 2023 en 11001-76001; clases distintas en cada sentido de Pasto-Ipiales.",
            figura="clases_por_ruta_anio.csv; figura m1_clases_rutas.png",
            resultado=_texto_clases(_calc_clases(res)), evidencia=EV + "clases_por_ruta_anio.csv"),
        _hipotesis(
            id_=10,
            enunciado="Las rutas difieren en escala entre sí y entre sentidos, así que un modelo único exige normalizar por ruta.",
            justificacion="Volúmenes distintos por corredor y asimetría ida/regreso (Anexo, limitaciones).",
            esperada="Razón entre la mayor y la menor media diaria de las seis rutas claramente mayor que 1.",
            figura="objetivo_por_ruta.csv; figura m1_series_rutas.png",
            resultado=_texto_escala(hall["escala_entre_rutas"]),
            evidencia=EV + "objetivo_por_ruta.csv; " + EV + "tendencia_anual.csv"),
    ]


# ---------------------------------------------------------------------------------------------- sección 6
def _calc_implicaciones(res: dict) -> dict:
    """Cifras que respaldan cada implicación (sin texto)."""
    obj, rs, ten, tr = res["objetivo"], res["descomposicion_resumen"], res["tendencia"], res["transito_anio"]
    serie = res["serie"]
    var = ten.dropna(subset=["variacion_pct_jun_dic"])
    obs = int(rs["observaciones"].min())
    sin = serie[serie["sin_registro"]]
    return {
        "fuerza_semanal": (rs["fuerza_semanal"].min(), rs["fuerza_semanal"].max()),
        "fuerza_anual": (rs["fuerza_anual"].min(), rs["fuerza_anual"].max()),
        "observaciones": obs, "ciclos_anuales": obs / ANUAL,
        "puntos_por_dia_anual_min": obs // ANUAL, "puntos_por_dia_anual_max": -(-obs // ANUAL),
        "media_diaria": (obj["media_diaria"].min(), obj["media_diaria"].max()),
        "ceros": int(obj["ceros"].sum()), "sin_registro": int(obj["sin_registro"].sum()),
        "ultimo_sin_registro": None if sin.empty else sin["fecha"].max().strftime("%Y-%m-%d"),
        "imputados": int(rs["sin_registro_imputados"].sum()),
        "variacion_jun_dic": (var["variacion_pct_jun_dic"].min(), var["variacion_pct_jun_dic"].max()) if len(var) else None,
        "transito_superan": int((tr["pct_transito"] > UMBRAL_TRANSITO_PCT).sum()), "transito_filas": len(tr),
    }


def construir_implicaciones(res: dict) -> dict:
    """Implicaciones para el modelado (sección 6) con la cifra que respalda cada una. Todas [PROPUESTO] (Camila decide)."""
    p, s, c = res["params"], res["hallazgos"]["salto_transito"], _calc_implicaciones(res)
    inicio, ultimo_origen = p["inicio_analisis"], p["ultimo_origen_test"]
    salto = (f"{s['ruta_id']} razón de tránsito {_n(s['razon_transito'])} entre {s['meses_antes'][1]} y {s['meses_despues'][0]}"
             if s.get("disponible") else s["motivo"])
    antes_inicio = (f"todos antes de {inicio}" if c["ultimo_sin_registro"] and c["ultimo_sin_registro"] < inicio
                    else f"el último el {c['ultimo_sin_registro']}")
    var = c["variacion_jun_dic"]
    return {
        "ventana": {
            "decision": f"Ventanas de rezagos múltiplos de {SEMANAL} días (mínimo {MIN_VENTANA_REZAGOS_SEMANAS * SEMANAL}) y una "
                        f"variante de {ANUAL} para la estacionalidad anual; el horizonte de 30 días obliga a pronosticar directo o "
                        "recursivo sin covariables observadas.",
            "base": f"Estacionalidad semanal con fuerza {_n(c['fuerza_semanal'][0])}-{_n(c['fuerza_semanal'][1])} (MSTL) y anual con "
                    f"{_n(c['fuerza_anual'][0])}-{_n(c['fuerza_anual'][1])}, sobre {c['observaciones']} días "
                    f"({_n(c['ciclos_anuales'], 1)} ciclos anuales: la fuerza anual queda sesgada hacia arriba con "
                    f"{c['puntos_por_dia_anual_min']}-{c['puntos_por_dia_anual_max']} puntos por día del año; ver `descomposicion`).",
            "estado": "[PROPUESTO]",
        },
        "variables_calendario": {
            "decision": "Día de la semana y mes por fecha; festivo, puente, Semana Santa, vacaciones escolares y fin_de_anio solo "
                        "desde calendario.parquet (CA-1), conocibles 30 días antes.",
            "base": "H-M1-1 y H-M1-5 se evalúan por fecha; H-M1-2, 3 y 4 dependen del calendario: "
                    + ("pendientes (falta CA-1)." if res["calendario"] is None else "evaluadas con calendario.parquet."),
            "estado": "[PROPUESTO]",
        },
        "perdida_conteo": {
            "decision": "Pérdida de conteo (Poisson o binomial negativa) o MAE sobre log1p; cuantil alto con pérdida pinball. "
                        "Enmascarar `sin_registro` y `despachos_sin_pasajeros`.",
            "base": f"Variable entera ≥ 0 con media diaria entre {_n(c['media_diaria'][0], 0)} y {_n(c['media_diaria'][1], 0)} "
                    f"pasajeros; {c['ceros']} ceros, de los cuales {c['sin_registro']} son `sin_registro`.",
            "estado": "[PROPUESTO]",
        },
        "particion": {
            "decision": f"Partición temporal con origen rodante desde {inicio}, último origen anclado al {ultimo_origen} para que "
                        "el test cubra el fin de año; escalas de normalización solo con train.",
            "base": (f"Variación de la media jun-dic entre años de {_n(var[0], 1)} % a {_n(var[1], 1)} %: hay tendencia, así que "
                     "ninguna partición aleatoria.") if var else "sin años comparables",
            "estado": "[PROPUESTO]",
        },
        "cambio_de_regimen": {
            "decision": "Indicadora de régimen solo con datos de train o ventana reciente para el escalado; reportar el MASE "
                        f"de {s.get('ruta_id', 'la ruta con salto')} con y sin el cambio.",
            "base": salto,
            "estado": "[PROPUESTO]",
        },
        "mayo_2021": {
            "decision": f"Mantener la serie completa para el descriptivo con marcas; entrenar desde {inicio} y no usar los ceros de "
                        "mayo-2021 como demanda.",
            "base": f"{c['sin_registro']} días-ruta `sin_registro` ({antes_inicio}); la descomposición desde {inicio} imputó "
                    f"{c['imputados']} días.",
            "estado": "[PROPUESTO]",
        },
        "transito": {
            "decision": "Modelar la serie total (origen + tránsito) como define el núcleo §5.1, pero usar despachos de ORIGEN para "
                        "flota; explorar tránsito y origen por separado como entrada auxiliar solo si se conoce 30 días antes.",
            "base": f"El tránsito supera al origen en {c['transito_superan']} de {c['transito_filas']} combinaciones ruta-año "
                    "(pct_transito en transito_por_ruta_anio.csv).",
            "estado": "[PROPUESTO]",
        },
    }
