"""M1 — construcción de las series diarias (DA-3) y secciones 1–2 de la plantilla común (DA-4). Sin red.

Entrada: ``data/raw/m1/rutas/AAAA-MM.parquet`` (``scripts/descargar_m1.py descargar``: filas ya agregadas en el servidor
por origen, destino, fecha, ``tipo_despacho`` y ``clase_vehiculo``) y ``data/processed/m1/divipola.csv``.
Salida (núcleo §5.1): ``demanda_detalle.parquet``, ``demanda_diaria.parquet``, ``marcas_anomalos.parquet``, ``rutas.yaml``,
``resumen_datos.json``; y en ``results/data/m1/eda/`` (núcleo §5.12): ``ficha.json``, ``calidad.csv``, ``diccionario.json``.

Formulación (r = ruta dirigida origen→destino, t = día, k = (tipo_despacho, clase_vehiculo)):

    detalle   P[r,t,k] = Σ pasajeros de las filas crudas con esa clave;  D[r,t,k] = Σ despachos
    serie     P[r,t]   = Σ_k P[r,t,k]   (origen + tránsito, núcleo §5.1 v0.3);   D[r,t] = Σ_k D[r,t,k]
    rejilla   t ∈ {inicio, …, fin} completo para cada r (sin huecos)
    sin_registro[r,t] = (ninguna fila cruda para (r,t))  →  se imputa P = D = 0 con la marca (no se borra la fila;
                        el modelo decide qué hacer con esos días: el 0 NO es una observación)
    R1 despachos_sin_pasajeros[r,t] = ¬sin_registro ∧ D[r,t] > 0 ∧ P[r,t] = 0               (enunciado, M1 tarea 2)
    R2–R4 atípicos robustos, misma ruta, solo días con registro. Para una serie transformada y_t:
        m_t = mediana{ y_s : |s − t| ≤ h, s con registro },  h = (ventana − 1)/2, con al menos `min_periodos` valores
        e_t = y_t − m_t;   σ̂_r = c · mediana_t |e_t − mediana(e)|   (MAD escalado; c = 1.4826)
        R2 caida_robusta:               y_t = log(1 + P[r,t]),                  marca si e_t < −u·σ̂_r
        R3 pico_robusto:                y_t = log(1 + P[r,t]),                  marca si e_t > +u·σ̂_r
        R4 pasajeros_por_despacho_bajo: y_t = log((1 + P[r,t]) / (1 + D[r,t])), marca si e_t < −u·σ̂_r
           (pasajeros sub-reportados frente a los despachos del mismo día; compara la ruta consigo misma: no usa
           ninguna capacidad de vehículo)
    anomalo[r,t] = R1 ∨ R2 ∨ R3 ∨ R4 (las reglas activas)

Las marcas son DESCRIPTIVAS: la ventana es centrada y el MAD usa la serie completa de la ruta (miran el futuro), así que
**no** pueden usarse como variable de entrada de los modelos (regla 0.9); sirven para describir la calidad y para que
cada dueño decida si excluye esos días de la evaluación. No se usa ninguna capacidad de vehículo.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.comun.eda import escribir_ficha, tabla_calidad
from src.comun.results import save_json

CLAVES_CRUDO = ["municipio_origen_ruta", "municipio_destino_ruta", "fecha_despacho", "tipo_despacho", "clase_vehiculo"]
COLUMNAS_CRUDO = [*CLAVES_CRUDO, "pasajeros", "despachos"]
COLUMNAS_DETALLE = ["ruta_id", "origen_divipola", "destino_divipola", "fecha", "tipo_despacho", "clase_vehiculo",
                    "pasajeros", "despachos"]
COLUMNAS_DIARIA = ["ruta_id", "origen_divipola", "destino_divipola", "fecha", "pasajeros", "despachos", "sin_registro",
                   "anomalo"]
REGLAS = ["despachos_sin_pasajeros", "caida_robusta", "pico_robusto", "pasajeros_por_despacho_bajo"]
REGLAS_ROBUSTAS = {  # regla: (transformación, signo del lado que se marca)
    "caida_robusta": ("log1p_pasajeros", -1),
    "pico_robusto": ("log1p_pasajeros", +1),
    "pasajeros_por_despacho_bajo": ("log_pasajeros_por_despacho", -1),
}
TIPOS_DESPACHO = ("ORIGEN", "TRANSITO")
PATRON_CODIGO = re.compile(r"^\d{5}$")
TODO_DIVIPOLA = "TODO(dato-faltante): código no está en DIVIPOLA"
N_EJEMPLOS = 5
PORCENTAJE = 100.0

DESCRIPCION_SIN_REGISTRO = (
    "Día sin ninguna fila en la fuente para esa ruta. Se conserva la fila con pasajeros = 0 y despachos = 0 y "
    "sin_registro = true: el 0 es una imputación, no una observación; cada modelo decide (excluirlo de la pérdida, "
    "interpolarlo con información pasada o tratarlo como cero). Nunca se marca como anómalo."
)
DESCRIPCION_REGLAS = {
    "despachos_sin_pasajeros": (
        "Día con registros, despachos > 0 y pasajeros = 0 (lo pide el enunciado, M1 tarea 2). La fuente no tiene filas "
        "con despachos = 0, así que un día así indica que no se reportaron los pasajeros."),
    "caida_robusta": (
        "Día con registros cuyo log(1 + pasajeros) queda más de `umbral_mad` MAD escalados por debajo de la mediana "
        "móvil centrada de la misma ruta (ventana `ventana_dias`). Detecta días con reporte parcial u operación muy "
        "reducida; con un umbral bajo también marcaría festivos de demanda baja (efecto de calendario, no error)."),
    "pico_robusto": (
        "Ídem, por encima de la mediana móvil: valores excepcionalmente altos para la ruta (posible doble reporte o "
        "evento). Un pico de temporada (festivo, fin de año) puede caer aquí: es descriptivo, no se corrige."),
    "pasajeros_por_despacho_bajo": (
        "Día con registros cuyo log((1 + pasajeros) / (1 + despachos)) queda más de `umbral_mad` MAD escalados por "
        "debajo de la mediana móvil centrada de la misma ruta: pocos pasajeros para los despachos reportados ese día "
        "(sub-reporte de pasajeros). No usa capacidades de vehículo: compara la ruta consigo misma."),
}
NOTA_FUGA = (
    "Las marcas `anomalo`, `sin_registro` y las de marcas_anomalos.parquet son descriptivas: la regla de atípicos usa una "
    "ventana centrada y el MAD de la serie completa de la ruta (mira el futuro). No deben usarse como variable de entrada "
    "de ningún modelo (núcleo regla 0.9); a lo sumo para excluir días de la pérdida o de la evaluación."
)


# --------------------------------------------------------------------------- utilidades
def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _fecha(texto) -> dt.date:
    return texto if isinstance(texto, dt.date) else dt.date.fromisoformat(str(texto))


def rutas_de_config(pares: list[dict]) -> list[dict]:
    """Cada par {a, b, descripcion} da dos rutas dirigidas a→b y b→a, recíprocas. Error si un código no tiene 5 dígitos,
    si a = b o si un par se repite (en cualquier orden)."""
    rutas, vistos = [], set()
    for p in pares:
        a, b = str(p["a"]), str(p["b"])
        if not (PATRON_CODIGO.match(a) and PATRON_CODIGO.match(b)) or a == b:
            raise ValueError(f"par de códigos DIVIPOLA no válido: {a!r}, {b!r}")
        clave = frozenset((a, b))
        if clave in vistos:
            raise ValueError(f"par repetido: {a}-{b}")
        vistos.add(clave)
        for o, d in ((a, b), (b, a)):
            rutas.append({"ruta_id": f"{o}-{d}", "origen": o, "destino": d, "ruta_regreso_id": f"{d}-{o}",
                          "descripcion": p.get("descripcion", "")})
    return rutas


# --------------------------------------------------------------------------- lectura y agregación
def leer_crudo(carpeta: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    """Concatena los parquets mensuales y devuelve también {archivo: SHA-256}."""
    archivos = sorted(Path(carpeta).glob("*.parquet"))
    if not archivos:
        raise FileNotFoundError(f"No hay parquets crudos en {carpeta}: corre scripts/descargar_m1.py descargar")
    partes = []
    for f in archivos:
        df = pd.read_parquet(f)
        faltan = [c for c in COLUMNAS_CRUDO if c not in df.columns]
        if faltan:
            raise ValueError(f"{f.name}: faltan columnas {faltan}")
        partes.append(df[COLUMNAS_CRUDO])
    crudo = pd.concat(partes, ignore_index=True)
    return crudo, {f.name: sha256(f) for f in archivos}


def construir_detalle(crudo: pd.DataFrame, rutas_ids: list[str], inicio, fin) -> pd.DataFrame:
    """P[r,t,k] y D[r,t,k]: suma por (ruta, fecha, tipo_despacho, clase_vehiculo) de las rutas configuradas y dentro
    del periodo. Las demás filas se descartan (se cuentan en el resumen)."""
    c = crudo.copy()
    c["ruta_id"] = c["municipio_origen_ruta"].astype(str) + "-" + c["municipio_destino_ruta"].astype(str)
    c["fecha"] = pd.to_datetime(c["fecha_despacho"]).dt.date
    c = c[c["ruta_id"].isin(rutas_ids) & (c["fecha"] >= _fecha(inicio)) & (c["fecha"] <= _fecha(fin))]
    tipos = set(c["tipo_despacho"].unique())
    if not tipos <= set(TIPOS_DESPACHO):
        raise ValueError(f"tipo_despacho inesperado: {sorted(tipos - set(TIPOS_DESPACHO))}")
    det = (c.groupby(["ruta_id", "fecha", "tipo_despacho", "clase_vehiculo"], as_index=False)[["pasajeros", "despachos"]]
           .sum())
    det["origen_divipola"] = det["ruta_id"].str[:5]
    det["destino_divipola"] = det["ruta_id"].str[6:]
    for col in ("pasajeros", "despachos"):
        det[col] = det[col].astype("int64")
    det = det[COLUMNAS_DETALLE].sort_values(["ruta_id", "fecha", "tipo_despacho", "clase_vehiculo"], kind="stable")
    return det.reset_index(drop=True)


def construir_diaria(detalle: pd.DataFrame, rutas: list[dict], inicio, fin) -> pd.DataFrame:
    """Serie §5.1 sin huecos: P[r,t] = Σ_k P[r,t,k]; los días sin filas quedan con 0 y ``sin_registro = True``.
    ``anomalo`` queda en False (lo llena ``aplicar_marcas``)."""
    fechas = [d.date() for d in pd.date_range(_fecha(inicio), _fecha(fin), freq="D")]
    rejilla = pd.DataFrame([(r["ruta_id"], f) for r in rutas for f in fechas], columns=["ruta_id", "fecha"])
    suma = detalle.groupby(["ruta_id", "fecha"], as_index=False)[["pasajeros", "despachos"]].sum()
    d = rejilla.merge(suma, on=["ruta_id", "fecha"], how="left", validate="one_to_one")
    d["sin_registro"] = d["pasajeros"].isna()
    for col in ("pasajeros", "despachos"):
        d[col] = d[col].fillna(0).astype("int64")
    d["origen_divipola"] = d["ruta_id"].str[:5]
    d["destino_divipola"] = d["ruta_id"].str[6:]
    d["anomalo"] = False
    return d[COLUMNAS_DIARIA].reset_index(drop=True)


# --------------------------------------------------------------------------- reglas de anómalos
def transformar(g: pd.DataFrame, transformacion: str) -> pd.Series:
    """y_t de cada regla robusta; los días sin registro quedan en NaN (no entran en la mediana ni en el MAD)."""
    p = g["pasajeros"].astype(float).where(~g["sin_registro"])
    if transformacion == "log1p_pasajeros":
        return np.log1p(p)
    if transformacion == "log_pasajeros_por_despacho":
        return np.log1p(p) - np.log1p(g["despachos"].astype(float))
    raise ValueError(f"transformación desconocida: {transformacion}")


def residuo_robusto(y: pd.Series, ventana: int, min_periodos: int) -> pd.Series:
    """e_t = y_t − mediana de y_s en la ventana centrada |s − t| ≤ (ventana − 1)/2. Los NaN (días sin registro) no
    entran en la mediana; si hay menos de ``min_periodos`` valores en la ventana, e_t = NaN."""
    if ventana < 1 or ventana % 2 == 0:
        raise ValueError(f"ventana_dias debe ser un entero impar ≥ 1 (centrada); se recibió {ventana}")
    y = pd.Series(y, dtype=float)
    m = y.rolling(window=ventana, center=True, min_periods=min_periodos).median()
    return y - m


def mad_escalado(residuos: pd.Series, escala: float) -> float:
    """σ̂ = escala · mediana |e − mediana(e)| (sin NaN)."""
    e = residuos.dropna()
    if e.empty:
        return float("nan")
    return float(escala * np.median(np.abs(e - np.median(e))))


def _validar_params(params: dict) -> None:
    desconocidas = sorted(set(params) - set(REGLAS))
    faltan = [r for r in REGLAS if r not in params]
    if desconocidas or faltan:
        raise ValueError(f"anomalos: reglas desconocidas {desconocidas}, faltantes {faltan}; se esperan {REGLAS}")


def marcar_anomalos(diaria: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, dict]:
    """Una columna booleana por regla (``REGLAS``) por (ruta, fecha). Los días sin registro nunca se marcan.
    Devuelve también, por ruta y regla robusta, σ̂ y el umbral usado (para el resumen)."""
    _validar_params(params)
    marcas = diaria[["ruta_id", "fecha"]].copy()
    for r in REGLAS:
        marcas[r] = False
    con = ~diaria["sin_registro"]
    if params["despachos_sin_pasajeros"].get("activa", True):
        marcas["despachos_sin_pasajeros"] = con & (diaria["despachos"] > 0) & (diaria["pasajeros"] == 0)
    detalles: dict = {}
    for regla, (transformacion, signo) in REGLAS_ROBUSTAS.items():
        p = params[regla]
        if not p.get("activa", True):
            continue
        for ruta, idx in diaria.groupby("ruta_id", sort=False).groups.items():
            g = diaria.loc[idx].sort_values("fecha")
            e = residuo_robusto(transformar(g, transformacion), int(p["ventana_dias"]), int(p["min_periodos"]))
            sigma = mad_escalado(e, float(p["escala_mad"]))
            umbral = float(p["umbral_mad"]) * sigma
            if not np.isfinite(sigma) or sigma == 0:
                detalles.setdefault(ruta, {})[regla] = {"sigma_mad": sigma, "umbral_log": None,
                                                        "nota": "MAD = 0 o sin datos: la regla no marca"}
                continue
            marca = (signo * e > umbral).fillna(False) & ~g["sin_registro"]
            marcas.loc[g.index, regla] = marca.to_numpy()
            detalles.setdefault(ruta, {})[regla] = {"sigma_mad": round(sigma, 6), "umbral_log": round(umbral, 6)}
    for r in REGLAS:
        marcas[r] = marcas[r].astype(bool)
    return marcas, detalles


def aplicar_marcas(diaria: pd.DataFrame, marcas: pd.DataFrame) -> pd.DataFrame:
    d = diaria.copy()
    d["anomalo"] = marcas[REGLAS].any(axis=1).to_numpy() & ~d["sin_registro"].to_numpy()
    return d


# --------------------------------------------------------------------------- DIVIPOLA y rutas.yaml
def leer_divipola(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(ruta, dtype=str)


def validar_codigos(codigos, divipola: pd.DataFrame) -> list[str]:
    """Códigos que no están en ``cod_mpio`` de DIVIPOLA (ordenados)."""
    return sorted(set(codigos) - set(divipola["cod_mpio"]))


def tabla_rutas(rutas: list[dict], divipola: pd.DataFrame, criterio: str) -> list[dict]:
    """Por ruta: códigos, municipio y departamento tal cual DIVIPOLA, regreso y criterio de selección."""
    nom = divipola.drop_duplicates("cod_mpio").set_index("cod_mpio")

    def campo(cod, col):
        return str(nom.at[cod, col]) if cod in nom.index else f"{TODO_DIVIPOLA} ({cod})"

    salida = []
    for r in rutas:
        o, d = r["origen"], r["destino"]
        salida.append({
            "ruta_id": r["ruta_id"], "origen_divipola": o, "destino_divipola": d,
            "origen_municipio": campo(o, "nom_mpio"), "origen_departamento": campo(o, "dpto"),
            "destino_municipio": campo(d, "nom_mpio"), "destino_departamento": campo(d, "dpto"),
            "ruta_regreso_id": r["ruta_regreso_id"],
            "criterios_seleccion": f"{criterio.strip()} Par: {r['descripcion']}." if r["descripcion"] else criterio.strip(),
        })
    return salida


# --------------------------------------------------------------------------- diccionario (DA-4)
def leer_diccionario(metadatos: Path) -> list[dict]:
    """Las columnas del conjunto tal cual ``columns[]`` de los metadatos oficiales (/api/views/<id>.json)."""
    vista = json.loads(Path(metadatos).read_text(encoding="utf-8"))
    return [{"campo": c["fieldName"], "nombre_portal": c.get("name"), "tipo_socrata": c.get("dataTypeName"),
             "descripcion_literal": c.get("description")} for c in vista["columns"]]


def leer_inconsistencias(informe: Path) -> list[dict]:
    """Filas de la tabla de la sección «### 1.7 Inconsistencias diccionario vs. datos» del informe DA-2 (literal)."""
    texto = Path(informe).read_text(encoding="utf-8")
    m = re.search(r"^### 1\.7 Inconsistencias diccionario vs\. datos.*?$(.*?)(?=^#{1,3} )", texto + "\n# fin",
                  flags=re.M | re.S)
    if m is None:
        raise ValueError(f"{informe}: no se encontró la sección 1.7 de inconsistencias")
    filas = []
    for linea in m.group(1).splitlines():
        linea = linea.strip()
        if not linea.startswith("|"):
            continue
        celdas = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", linea.strip("|"))]
        if len(celdas) != 3 or not celdas[0].isdigit():
            continue  # encabezado o separador
        filas.append({"n": celdas[0], "diccionario_dice": celdas[1], "datos_muestran": celdas[2]})
    return filas


def _miles(n) -> str:
    return f"{int(n):,}".replace(",", " ")


def composicion_anual(detalle: pd.DataFrame, columna: str) -> pd.DataFrame:
    """% de pasajeros de cada categoría de ``columna`` por (ruta, año): filas (ruta, año), columnas categorías."""
    d = detalle.assign(anio=pd.to_datetime(detalle["fecha"]).dt.year)
    t = d.groupby(["ruta_id", "anio", columna])["pasajeros"].sum().unstack(fill_value=0)
    return PORCENTAJE * t.div(t.sum(axis=1).where(lambda x: x > 0), axis=0)


def cambios_de_composicion(detalle: pd.DataFrame, umbral_pp: float) -> list[dict]:
    """Por ruta, categorías de ``tipo_despacho`` o ``clase_vehiculo`` cuya participación en los pasajeros cambia más de
    ``umbral_pp`` puntos porcentuales entre dos años del periodo (posible cambio de reporte, no de demanda)."""
    out = []
    for columna in ("tipo_despacho", "clase_vehiculo"):
        comp = composicion_anual(detalle, columna)
        for ruta, g in comp.groupby(level="ruta_id"):
            g = g.droplevel("ruta_id")
            for cat in g.columns:
                serie = g[cat].fillna(0.0)
                if serie.max() - serie.min() > umbral_pp:
                    anios = ", ".join(f"{a}: {v:.1f} %" for a, v in serie.items())
                    out.append({"ruta_id": ruta, "columna": columna, "categoria": str(cat), "pct_por_anio": anios})
    return out


def inconsistencias_nuevas(crudo: pd.DataFrame, detalle: pd.DataFrame, diaria: pd.DataFrame, marcas: pd.DataFrame,
                           fuera_divipola: list[str], umbral_pp: float) -> list[dict]:
    """Hallazgos medidos en las rutas descargadas, además de los del informe DA-2. ``tipo``: «diccionario vs. datos»
    (la fuente dice algo y los datos otra cosa) o «calidad» (los datos no contradicen el texto, pero limitan su uso)."""
    out = []
    if fuera_divipola:
        out.append({"tipo": "diccionario vs. datos",
                    "diccionario_dice": "municipio_origen_ruta / municipio_destino_ruta: «Código Divipola»",
                    "datos_muestran": f"Códigos que no están en DIVIPOLA (corte 30-dic-2024): {', '.join(fuera_divipola)}"})
    dias_cero = diaria.loc[marcas["despachos_sin_pasajeros"].to_numpy()]
    for _, f in dias_cero.iterrows():
        out.append({"tipo": "diccionario vs. datos",
                    "diccionario_dice": ("pasajeros: «Número de pasajeros que abordaron viaje desde la terminal de "
                                         "transporte»; despachos: «Número vehículos ... que salen desde la terminal»"),
                    "datos_muestran": (f"Ruta {f['ruta_id']}, {f['fecha'].isoformat()}: {_miles(f['despachos'])} "
                                       "despachos y 0 pasajeros en todo el día.")})
    n_ceros = int((crudo["pasajeros"] == 0).sum())
    if n_ceros:
        out.append({"tipo": "calidad",
                    "diccionario_dice": "pasajeros / despachos descritos como «Número», sin restricciones",
                    "datos_muestran": (f"{_miles(n_ceros)} de {_miles(len(crudo))} filas descargadas (agregadas por ruta, "
                                       "fecha, tipo de despacho y clase) tienen pasajeros = 0 con despachos ≥ 1.")})
    tipos = detalle.groupby(["ruta_id", "tipo_despacho"])[["pasajeros", "despachos"]].sum().unstack(fill_value=0)
    for ruta, fila in tipos.iterrows():
        po, pt = fila.get(("pasajeros", "ORIGEN"), 0), fila.get(("pasajeros", "TRANSITO"), 0)
        do, dtr = fila.get(("despachos", "ORIGEN"), 0), fila.get(("despachos", "TRANSITO"), 0)
        if pt > po:
            out.append({"tipo": "calidad",
                        "diccionario_dice": ("tipo_despacho: «2 = Si el despacho de la ruta es en transito»; pasajeros: «Las "
                                             "terminales en tránsito sólo deben reportar los pasajeros que abordaron el "
                                             "vehículo en dicha terminal»"),
                        "datos_muestran": (f"Ruta {ruta}: pasajeros en terminales de tránsito {_miles(pt)} frente a "
                                           f"{_miles(po)} en la terminal de origen; despachos en tránsito {_miles(dtr)} "
                                           f"frente a {_miles(do)} en origen. La mayoría de los pasajeros reportados aborda "
                                           "en terminales de tránsito, no en la de origen, y la fuente no permite saber si un mismo "
                                           "vehículo se cuenta como despacho en el origen y en cada terminal de tránsito "
                                           "(no hay identificador de vehículo).")})
    for c in cambios_de_composicion(detalle, umbral_pp):
        out.append({"tipo": "calidad",
                    "diccionario_dice": f"{c['columna']}: sin mención de cambios de categoría o de reporte entre años",
                    "datos_muestran": (f"Ruta {c['ruta_id']}: la participación de {c['categoria']} en los pasajeros cambia "
                                       f"más de {umbral_pp:g} puntos entre años ({c['pct_por_anio']}); puede ser un cambio "
                                       "de reporte (terminales que reportan, clasificación) o de la operación: no verificado.")})
    sin = diaria.groupby("ruta_id")["sin_registro"].sum()
    if sin.any():
        detalle_sin = "; ".join(f"{r}: {int(n)}" for r, n in sin.items() if n)
        meses = sorted({f.strftime("%Y-%m") for f in diaria.loc[diaria["sin_registro"], "fecha"]})
        out.append({"tipo": "calidad",
                    "diccionario_dice": "Frecuencia de actualización «Mensual», sin mención de huecos",
                    "datos_muestran": (f"Días sin ningún registro en el periodo, por ruta: {detalle_sin} "
                                       f"(meses: {', '.join(meses)}).")})
    return out


# --------------------------------------------------------------------------- resumen
def _ejemplos(diaria: pd.DataFrame, marcas: pd.DataFrame, ruta: str, regla: str) -> list[dict]:
    m = marcas[(marcas["ruta_id"] == ruta) & marcas[regla]]
    d = diaria.set_index(["ruta_id", "fecha"])
    out = []
    for f in m["fecha"].head(N_EJEMPLOS):
        fila = d.loc[(ruta, f)]
        out.append({"fecha": f.isoformat(), "pasajeros": int(fila["pasajeros"]), "despachos": int(fila["despachos"])})
    return out


def resumen_por_ruta(diaria: pd.DataFrame, detalle: pd.DataFrame, marcas: pd.DataFrame, detalles: dict) -> dict:
    out = {}
    for ruta, g in diaria.groupby("ruta_id", sort=False):
        det = detalle[detalle["ruta_id"] == ruta]
        tot = int(det["pasajeros"].sum())
        tr = int(det.loc[det["tipo_despacho"] == "TRANSITO", "pasajeros"].sum())
        por_clase = det.groupby("clase_vehiculo")["pasajeros"].sum()
        m = marcas[marcas["ruta_id"] == ruta]
        con = g[~g["sin_registro"]]
        out[ruta] = {
            "dias": int(len(g)),
            "dias_con_registro": int(len(con)),
            "dias_sin_registro": int(g["sin_registro"].sum()),
            "dias_anomalos": int(g["anomalo"].sum()),
            "dias_anomalos_por_regla": {r: int(m[r].sum()) for r in REGLAS},
            "pasajeros_totales": tot,
            "despachos_totales": int(det["despachos"].sum()),
            "despachos_origen": int(det.loc[det["tipo_despacho"] == "ORIGEN", "despachos"].sum()),
            "pct_pasajeros_transito": PORCENTAJE * tr / tot if tot else None,
            "pct_pasajeros_por_clase": {str(k): PORCENTAJE * int(v) / tot for k, v in por_clase.items()} if tot else {},
            "pasajeros_dia_mediana": float(con["pasajeros"].median()) if len(con) else None,
            "pasajeros_dia_min": int(con["pasajeros"].min()) if len(con) else None,
            "pasajeros_dia_max": int(con["pasajeros"].max()) if len(con) else None,
            "fechas_sin_registro": [f.isoformat() for f in g.loc[g["sin_registro"], "fecha"]],
            "ejemplos_anomalos": {r: _ejemplos(diaria, marcas, ruta, r) for r in REGLAS},
            "parametros_robustos": detalles.get(ruta, {}),
        }
    return out


# --------------------------------------------------------------------------- escritura
def _escribir_parquet(df: pd.DataFrame, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    df.to_parquet(tmp, index=False)
    tmp.replace(ruta)


def _escribir_yaml(obj, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(yaml.safe_dump(obj, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")


def main(cfg: dict) -> int:
    per, ent, sal, fte = cfg["periodo"], cfg["entrada"], cfg["salida"], cfg["fuente"]
    inicio, fin = _fecha(per["inicio"]), _fecha(per["fin"])
    if fin < inicio:
        raise ValueError("periodo.fin es anterior a periodo.inicio")
    _validar_params(cfg["anomalos"])
    rutas = rutas_de_config(cfg["pares"])
    ids = [r["ruta_id"] for r in rutas]

    crudo, hashes = leer_crudo(Path(ent["crudo_rutas"]))
    divipola = leer_divipola(Path(ent["divipola"]))
    detalle = construir_detalle(crudo, ids, inicio, fin)
    diaria = construir_diaria(detalle, rutas, inicio, fin)
    marcas, detalles = marcar_anomalos(diaria, cfg["anomalos"])
    diaria = aplicar_marcas(diaria, marcas)

    codigos = {r["origen"] for r in rutas} | {r["destino"] for r in rutas}
    codigos |= set(crudo["municipio_origen_ruta"].astype(str)) | set(crudo["municipio_destino_ruta"].astype(str))
    fuera = validar_codigos(codigos, divipola)

    carpeta = Path(sal["carpeta"])
    _escribir_parquet(detalle, carpeta / sal["detalle"])
    _escribir_parquet(diaria, carpeta / sal["diaria"])
    _escribir_parquet(marcas, carpeta / sal["marcas"])
    _escribir_yaml({"fuente": fte["url"], "periodo": [inicio.isoformat(), fin.isoformat()],
                    "rutas": tabla_rutas(rutas, divipola, cfg["criterio_seleccion"])}, carpeta / sal["rutas"])

    por_ruta = resumen_por_ruta(diaria, detalle, marcas, detalles)
    n_dias = (fin - inicio).days + 1
    resumen = {
        "conjunto_crudo": {
            "fuente": fte["nombre"], "id_socrata": fte["id_socrata"], "url": fte["url"],
            "n_registros": fte["n_registros_medido"], "n_variables": fte["n_variables_medido"],
            "fecha_min": fte["fecha_min_medida"], "fecha_max_valida": fte["fecha_max_medida_valida"],
            "fecha_consulta": str(fte["fecha_consulta_informe"]),
            "origen_de_las_cifras": f"Medidas con SoQL sobre el conjunto completo; informe {ent['informe_fuentes']} §1.4",
        },
        "periodo": {"inicio": inicio.isoformat(), "fin": fin.isoformat(), "dias": n_dias},
        "rutas": ids,
        "filas_descargadas": int(len(crudo)),
        "archivos_crudos": hashes,
        "filas_fuera_de_rutas_o_periodo": int(len(crudo) - _filas_dentro(crudo, ids, inicio, fin)),
        "filas_detalle": int(len(detalle)),
        "filas_serie": int(len(diaria)),
        "pasajeros": "origen + tránsito (núcleo §5.1 v0.3)",
        "regla_sin_registro": DESCRIPCION_SIN_REGISTRO,
        "reglas_anomalos": {r: {"descripcion": DESCRIPCION_REGLAS[r], "parametros": cfg["anomalos"][r]} for r in REGLAS},
        "nota_fuga": NOTA_FUGA,
        "codigos_fuera_de_divipola": fuera,
        "por_ruta": por_ruta,
        "pct_pasajeros_por_anio": {
            col: {f"{r}|{a}": {str(k): round(float(v), 3) for k, v in fila.dropna().items()}
                  for (r, a), fila in composicion_anual(detalle, col).iterrows()}
            for col in ("tipo_despacho", "clase_vehiculo")},
    }
    save_json(carpeta / sal["resumen"], resumen)

    escribir_eda(cfg, crudo, detalle, diaria, marcas, hashes, fuera, por_ruta)
    _imprimir(resumen, carpeta, sal)
    return 0


def _filas_dentro(crudo: pd.DataFrame, ids: list[str], inicio: dt.date, fin: dt.date) -> int:
    rid = crudo["municipio_origen_ruta"].astype(str) + "-" + crudo["municipio_destino_ruta"].astype(str)
    f = pd.to_datetime(crudo["fecha_despacho"]).dt.date
    return int((rid.isin(ids) & (f >= inicio) & (f <= fin)).sum())


def escribir_eda(cfg: dict, crudo, detalle, diaria, marcas, hashes, fuera, por_ruta) -> None:
    """Secciones 1 (ficha) y 2 (diccionario y calidad) de la plantilla común (núcleo §5.12) para M1."""
    fte, ent, per = cfg["fuente"], cfg["entrada"], cfg["periodo"]
    destino = Path(cfg["salida"]["eda"])
    ficha = {
        "fuente": f"{fte['nombre']} ({fte['entidad']}, datos.gov.co {fte['id_socrata']})",
        "cita": fte["cita"],
        "url": fte["url"],
        "fecha_descarga": _fecha_descarga(ent),
        "sha256": hashes,
        "unidad_de_observacion": ("Crudo: fila agregada por terminal, clase, nivel de servicio, ruta, fecha, hora y tipo de "
                                  "despacho. Serie: pasajeros por ruta dirigida y día (origen + tránsito)."),
        "n_registros": fte["n_registros_medido"],
        "n_variables": fte["n_variables_medido"],
        "periodo": {"conjunto_crudo": [fte["fecha_min_medida"], fte["fecha_max_medida_valida"]],
                    "usado": [str(per["inicio"]), str(per["fin"])]},
        "conteos": {
            "fecha_consulta_cifras_conjunto": str(fte["fecha_consulta_informe"]),
            "rutas": len(por_ruta),
            "pares_ida_regreso": len(cfg["pares"]),
            "filas_descargadas": int(len(crudo)),
            "filas_detalle": int(len(detalle)),
            "filas_serie": int(len(diaria)),
            "dias_por_ruta": int(diaria.groupby("ruta_id").size().iloc[0]) if len(diaria) else 0,
            "dias_sin_registro": int(diaria["sin_registro"].sum()),
            "dias_anomalos": int(diaria["anomalo"].sum()),
            "pasajeros_totales": int(detalle["pasajeros"].sum()),
            "clases_vehiculo": sorted(map(str, detalle["clase_vehiculo"].unique())),
            "codigos_fuera_de_divipola": fuera,
        },
    }
    escribir_ficha(destino / "ficha.json", ficha)
    cal = pd.concat([tabla_calidad(detalle).assign(tabla="detalle", filas=len(detalle),
                                                   duplicados_clave=int(detalle.duplicated(
                                                       ["ruta_id", "fecha", "tipo_despacho", "clase_vehiculo"]).sum())),
                     tabla_calidad(diaria).assign(tabla="serie", filas=len(diaria),
                                                  duplicados_clave=int(diaria.duplicated(["ruta_id", "fecha"]).sum()))],
                    ignore_index=True)
    cal = cal[["tabla", "filas", "duplicados_clave", *[c for c in cal.columns if c not in ("tabla", "filas",
                                                                                          "duplicados_clave")]]]
    destino.mkdir(parents=True, exist_ok=True)
    cal.to_csv(destino / "calidad.csv", index=False, encoding="utf-8", lineterminator="\n")
    save_json(destino / "diccionario.json", {
        "fuente_del_diccionario": f"columns[] de {fte['url_api'].replace('/resource/', '/api/views/')} "
                                  f"(copia en {ent['metadatos_fuente']})",
        "variables": leer_diccionario(Path(ent["metadatos_fuente"])),
        "inconsistencias_informe": leer_inconsistencias(Path(ent["informe_fuentes"])),
        "origen_inconsistencias_informe": f"{ent['informe_fuentes']} §1.7 (consulta del {fte['fecha_consulta_informe']})",
        "inconsistencias_nuevas": inconsistencias_nuevas(crudo, detalle, diaria, marcas, fuera,
                                                         float(cfg["calidad"]["cambio_composicion_pp"])),
        "origen_inconsistencias_nuevas": "DA-3, medidas sobre las rutas descargadas (data/raw/m1/rutas/*.parquet)",
    })


def _fecha_descarga(ent: dict) -> str:
    """Fecha (UTC) de modificación más reciente de los parquets crudos: cuándo se descargaron."""
    archivos = sorted(Path(ent["crudo_rutas"]).glob("*.parquet"))
    ultimo = max(f.stat().st_mtime for f in archivos)
    return dt.datetime.fromtimestamp(ultimo, tz=dt.timezone.utc).date().isoformat()


def _imprimir(resumen: dict, carpeta: Path, sal: dict) -> None:
    print(f"Filas crudas: {resumen['filas_descargadas']} · detalle: {resumen['filas_detalle']} · "
          f"serie: {resumen['filas_serie']}")
    print(f"{'ruta':<12} {'días':>5} {'sin reg':>7} " + " ".join(f"{r[:14]:>14}" for r in REGLAS)
          + f" {'pasajeros':>10} {'% tráns':>7}")
    for ruta, r in resumen["por_ruta"].items():
        pct = r["pct_pasajeros_transito"]
        print(f"{ruta:<12} {r['dias']:>5} {r['dias_sin_registro']:>7} "
              + " ".join(f"{r['dias_anomalos_por_regla'][x]:>14}" for x in REGLAS)
              + f" {r['pasajeros_totales']:>10} {('%.1f' % pct) if pct is not None else '-':>7}")
    print("Códigos fuera de DIVIPOLA:", resumen["codigos_fuera_de_divipola"] or "ninguno")
    for clave in ("detalle", "diaria", "marcas", "rutas", "resumen"):
        f = carpeta / sal[clave]
        print(f"  {f.as_posix()} ({f.stat().st_size} B)")
