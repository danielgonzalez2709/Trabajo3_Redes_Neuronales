"""M3 — análisis descriptivo (JJ-2): secciones 3–7 de la plantilla común (núcleo §5.12). Sin red; lee ``data/processed/m3/``.

Entrada: ``destinos.parquet``, ``usuarios.parquet`` e ``interacciones.parquet`` de ``m3-datos`` (núcleo §5.7).
Salida (``results/data/m3/eda/``; no se tocan ``ficha.json``, ``calidad.csv`` ni ``diccionario.json``):
  interacciones_por_{usuario,destino,lugar}.csv   conteo por entidad (incluidas las de 0)
  distribucion_actividad.json                     histograma de usuarios y de destinos vs. reparto uniforme al azar
  calificaciones.csv                              distribución 1–5 por origen, media y desviación
  concentracion.json                              Gini, HHI, cuota top, Lorenz (observado y azar) por nivel
  actividad_usuarios.json                         grupos «pocas» / «muchas», cuenta de la partición D3 y sensibilidad
  coincidencia_preferencias.json, matriz_preferencias_tipo.csv, demografia_tipo.csv
  pruebas_hipotesis.json                          pruebas confirmatorias (ajuste de Holm) y complementarias
  hipotesis.json                                  contrato de §5.12

Reparto del código: ``eda_estadistica.py`` (funciones estadísticas puras), ``eda_hipotesis.py`` (veredictos y textos) y
este archivo (lectura, ``Datos``, una función ``analizar_*`` por bloque y ``main``).

Definiciones (las fijan las pruebas de ``tests/test_eda_m3.py``):
  Gini            2·Σ i·x_(i) / (n·Σx) − (n+1)/n  (x ascendente, i = 1…n); máximo (n−1)/n; «reescalado» = Gini·n/(n−1)
  HHI             Σ s_i² con cuotas s_i en [0, 1]; normalizado (HHI − 1/n)/(1 − 1/n)
  cuota top f     suma de los ceil(f·n) mayores sobre el total
  p permutación   (1 + #{T* >= T_obs}) / (1 + B)
  Holm            p_(j) ajustado = max_{i<=j} min(1, (m − i + 1)·p_(i))

Toda aleatoriedad sale de ``make_rng(base_seed, run_id)`` con un ``run_id`` propio por uso (ver ``configs/m3/eda.yaml``).
Los datos son generados (D4): ningún resultado se atribuye a comportamiento real de turistas.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from src.comun.eda import escribir_hipotesis
from src.comun.results import load_json, save_json
from src.comun.seeds import make_rng
from src.m3_recomendacion.datos import chi2_y_v, separar_opciones, usuarios_por_numero  # noqa: F401  (usado por pruebas)
from src.m3_recomendacion.eda_estadistica import (  # noqa: F401  (se reexportan: las pruebas usan ``eda.<nombre>``)
    AJUSTES_MULTIPLES, TOLERANCIA_NUMERICA, _cuantiles, _histogramas_por_filas, _ic, _rho_por_filas,
    _tablas_de_grupos, _tablas_permutadas, ajustar_multiplicidad, aporte_al_chi2, chi2_por_lotes, cuota_top,
    delta_de_cliff, gini, gini_reescalado, histograma_de_actividad, hhi, hhi_normalizado, holm, lorenz,
    multiplicidades, n_top, p_permutacion, permutaciones, residuos_de_pearson, residuos_estandarizados, rho_de_spearman,
    simular_uniforme, v_corregida_por_lotes, v_de_cramer_por_lotes)
from src.m3_recomendacion.eda_hipotesis import (  # noqa: F401  (se reexportan: las pruebas usan ``eda.<nombre>``)
    buscar_prueba, construir_hipotesis, efecto_adicional, en_el_limite, frase_limite, veredicto_de_hipotesis,
    veredicto_de_prueba)

ORIGENES = ("resena", "historial")
NIVELES_CONCENTRACION = ("destino_id", "lugar")
METODO_IC_SIMULACION = ("observado menos los percentiles de {s} simulaciones del reparto uniforme: inversión aproximada "
                        "bajo un modelo de desplazamiento (el azar solo corre la distribución), no es un bootstrap")
COLUMNAS = {
    "destinos": ["destino_id", "lugar", "tipo", "popularidad"],
    "usuarios": ["usuario_id", "preferencias", "genero", "n_adultos", "n_ninos"],
    "interacciones": ["usuario_id", "destino_id", "origen", "calificacion"],
}
# (columna de usuarios, id de la prueba, sufijo del run_id en la config, nombre en los textos)
VARIABLES_DEMOGRAFICAS = (("genero", "H4_genero", "genero", "el género"),
                          ("n_adultos", "H4_n_adultos", "adultos", "n_adultos"),
                          ("n_ninos", "H4_n_ninos", "ninos", "n_ninos"))


# =========================================================================== configuración
def validar_config(cfg: dict) -> None:
    """Falla ANTES de calcular nada si la config pide algo que el código no soporta (mensaje con la clave)."""
    if cfg["ajuste_multiple"] not in AJUSTES_MULTIPLES:
        raise ValueError(f"ajuste_multiple {cfg['ajuste_multiple']!r} no está soportado; "
                         f"los posibles son {sorted(AJUSTES_MULTIPLES)}")
    niveles = cfg["niveles"]
    if not niveles or not set(niveles) <= set(NIVELES_CONCENTRACION):
        raise ValueError(f"niveles {niveles!r} inválido: debe ser una lista no vacía con valores de "
                         f"{list(NIVELES_CONCENTRACION)}")
    fracciones = cfg["fracciones_top"]
    if not fracciones or not all(isinstance(f, (int, float)) and 0 < f <= 1 for f in fracciones):
        raise ValueError(f"fracciones_top {fracciones!r} inválido: debe ser una lista no vacía de fracciones en (0, 1]")
    pocas_max = cfg["actividad"]["pocas_max"]
    if not isinstance(pocas_max, int) or pocas_max < 1:
        raise ValueError(f"actividad.pocas_max {pocas_max!r} inválido: debe ser un entero >= 1")
    for clave in ("n_permutaciones", "n_bootstrap", "n_simulaciones_azar"):
        if not isinstance(cfg[clave], int) or cfg[clave] < 1:
            raise ValueError(f"{clave} {cfg[clave]!r} inválido: debe ser un entero >= 1")


# =========================================================================== preferencias y tipo
def tipos_de_preferencias(texto: str, emparejamiento: dict) -> frozenset:
    """Tipos de destino que cubre una combinación de preferencias («Beaches, Historical» → {Beach, Historical})."""
    tipos = set()
    for opcion in separar_opciones(texto):
        if opcion not in emparejamiento:
            raise ValueError(f"la opción de preferencia {opcion!r} no está en emparejamiento_preferencia_tipo de la config")
        tipos.add(emparejamiento[opcion])
    return frozenset(tipos)


def coincidencia(catalogo_tipos, usuarios, tipos, preferidos_por_usuario: dict, marginal: pd.Series | None = None) -> dict:
    """Tasa de coincidencia preferencia–tipo y sus dos líneas base.

    ``usuarios`` y ``tipos``: usuario y tipo del destino de cada interacción. Coincide si el tipo está entre los que
    cubren sus preferencias. Línea base EXACTA: por interacción, la fracción de ids del catálogo cuyo tipo está en las
    preferencias del usuario (destino uniforme en el catálogo), promediada sobre las interacciones. Línea base MARGINAL:
    igual, pero con la distribución de tipos de las interacciones (o ``marginal``, si se pasa) en vez de la del catálogo."""
    if len(usuarios) == 0:
        raise ValueError("coincidencia: no hay interacciones (grupo sin interacciones); no se puede medir la tasa")
    cat = pd.Series(list(catalogo_tipos)).value_counts()
    fraccion = {u: float(sum(cat.get(t, 0) for t in p)) / float(cat.sum()) for u, p in preferidos_por_usuario.items()}
    q = pd.Series(list(tipos)).value_counts(normalize=True) if marginal is None else marginal
    coinciden = [t in preferidos_por_usuario[u] for u, t in zip(usuarios, tipos)]
    tasa = float(np.mean(coinciden))
    exacta = float(np.mean([fraccion[u] for u in usuarios]))
    marg = float(np.mean([sum(q.get(t, 0.0) for t in preferidos_por_usuario[u]) for u in usuarios]))
    return {"n": len(coinciden), "n_coinciden": int(sum(coinciden)), "tasa": tasa, "linea_base_exacta": exacta,
            "linea_base_marginal": marg, "diferencia_exacta": tasa - exacta, "diferencia_marginal": tasa - marg}


# =========================================================================== lectura y preparación
def _leer(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ent = cfg["entrada"]
    carpeta = Path(ent["carpeta"])
    tablas = {}
    for rol in ("destinos", "usuarios", "interacciones"):
        ruta = carpeta / ent[rol]
        if not ruta.is_file():
            raise FileNotFoundError(f"falta {ruta}: corre primero `python run.py m3-datos --config configs/m3/datos.yaml`")
        df = pd.read_parquet(ruta)
        faltan = [c for c in COLUMNAS[rol] if c not in df.columns]
        if faltan:
            raise ValueError(f"{ruta}: faltan las columnas {faltan}")
        tablas[rol] = df
    return tablas["destinos"], tablas["usuarios"], tablas["interacciones"]


def _validar(destinos: pd.DataFrame, usuarios: pd.DataFrame, inter: pd.DataFrame) -> None:
    if destinos["destino_id"].duplicated().any() or usuarios["usuario_id"].duplicated().any():
        raise ValueError("destino_id y usuario_id deben ser únicos")
    if inter.duplicated(["usuario_id", "destino_id"]).any():
        raise ValueError("hay pares (usuario, destino) repetidos en interacciones")
    if not (inter["usuario_id"].isin(usuarios["usuario_id"]).all() and inter["destino_id"].isin(destinos["destino_id"]).all()):
        raise ValueError("hay interacciones con un usuario o destino que no está en los maestros")
    if not set(inter["origen"]) <= set(ORIGENES):
        raise ValueError(f"origen inesperado en interacciones: {sorted(set(inter['origen']) - set(ORIGENES))}")
    if not len(inter):
        raise ValueError("no hay interacciones")


class Datos:
    """Vistas numéricas de los parquet (todo derivado de ellos; sin aleatoriedad).

    «Activo» = usuario con al menos una interacción. Formas: N interacciones, U usuarios activos (ordenados por id),
    G combinaciones de preferencias CON interacciones, T tipos de destino (ordenados), K valores de calificación,
    2 orígenes (reseña, historial).

    Por interacción (N): ``interacciones`` (tabla), ``usuario_de_interaccion`` (índice en 0..U-1),
    ``tipo_de_interaccion`` (0..T-1), ``calificacion_de_interaccion`` (0..K-1), ``origen_de_interaccion`` (0 o 1),
    ``interaccion_coincide`` (bool: el tipo está entre los que cubren las preferencias del usuario).
    Por usuario activo (U): ``combinacion_de_usuario_activo`` (0..G-1), ``n_interacciones_por_usuario_activo``,
    ``coincidencias_por_usuario``, ``linea_base_exacta_por_usuario`` y ``linea_base_marginal_por_usuario`` (sumas sobre
    sus interacciones), ``usuarios_activos`` (tabla).
    Matrices por usuario activo: ``conteos_tipo_por_usuario`` (U×T), ``suma_calificaciones_por_usuario_y_tipo`` (U×T),
    ``coincidencias_si_combinacion`` y ``suma_calificaciones_coincidentes_si_combinacion`` (U×G: qué pasaría si el
    usuario tuviera la combinación g), ``calificaciones_coincidentes_por_usuario`` y
    ``calificaciones_no_coincidentes_por_usuario`` (U×K), ``origen_y_tipo_por_usuario`` (U×2×T) y
    ``origen_y_calificacion_por_usuario`` (U×2×K).
    Por combinación (G): ``combinaciones`` (texto), ``tipos_cubiertos`` (G×T, 1 si la combinación cubre el tipo),
    ``fraccion_del_catalogo_por_combinacion`` y ``fraccion_marginal_por_combinacion``.
    Conteos por entidad maestra (incluidas las de 0): ``n_interacciones_por_usuario``, ``n_interacciones_por_destino``,
    ``n_interacciones_por_lugar``."""

    def __init__(self, destinos: pd.DataFrame, usuarios: pd.DataFrame, interacciones: pd.DataFrame, emparejamiento: dict):
        self.destinos = destinos
        self.tipos = sorted(destinos["tipo"].unique())
        sin_destinos = sorted(set(emparejamiento.values()) - set(self.tipos))
        if sin_destinos:
            raise ValueError(f"el emparejamiento menciona tipos que no existen en destinos: {sin_destinos}")
        usuarios = usuarios.copy()
        usuarios["combinacion"] = usuarios["preferencias"].map(lambda t: ", ".join(separar_opciones(t)))
        self.usuarios = usuarios
        todas = sorted(usuarios["combinacion"].unique())
        tipos_de_todas = {c: tipos_de_preferencias(c, emparejamiento) for c in todas}
        self.tipos_preferidos_por_usuario = {int(i): tipos_de_todas[c]
                                             for i, c in zip(usuarios["usuario_id"], usuarios["combinacion"])}
        unidas = interacciones.merge(usuarios[["usuario_id", "combinacion"]], on="usuario_id").merge(
            destinos[["destino_id", "lugar", "tipo"]], on="destino_id")
        self.interacciones = unidas.sort_values(["usuario_id", "destino_id"]).reset_index(drop=True)
        self.n_interacciones = len(self.interacciones)
        self.combinaciones = sorted(self.interacciones["combinacion"].unique())
        self.combinaciones_sin_interacciones = [c for c in todas if c not in set(self.combinaciones)]
        self.tipos_por_combinacion = {c: tipos_de_todas[c] for c in self.combinaciones}
        self.tipos_cubiertos = np.array([[t in self.tipos_por_combinacion[c] for t in self.tipos]
                                         for c in self.combinaciones], dtype=np.int64)
        self._indices_por_interaccion()
        self._matrices_por_usuario()
        self._lineas_base(destinos)
        self._conteos_por_entidad(destinos, usuarios)

    def _indices_por_interaccion(self) -> None:
        tabla = self.interacciones
        self.escala = list(range(int(tabla["calificacion"].min()), int(tabla["calificacion"].max()) + 1))
        self.ids_usuarios_activos = np.sort(tabla["usuario_id"].unique())
        self.n_usuarios_activos = len(self.ids_usuarios_activos)
        self.usuario_de_interaccion = np.searchsorted(self.ids_usuarios_activos, tabla["usuario_id"].to_numpy())
        self.tipo_de_interaccion = np.searchsorted(self.tipos, tabla["tipo"].to_numpy())
        self.calificacion_de_interaccion = (tabla["calificacion"].to_numpy() - self.escala[0]).astype(int)
        self.origen_de_interaccion = (tabla["origen"] != ORIGENES[0]).to_numpy().astype(int)
        self.usuarios_activos = self.usuarios.set_index("usuario_id").loc[self.ids_usuarios_activos]
        self.combinacion_de_usuario_activo = np.searchsorted(self.combinaciones,
                                                             self.usuarios_activos["combinacion"].to_numpy())
        self.interaccion_coincide = np.array([
            self.tipos[t] in self.tipos_preferidos_por_usuario[int(u)]
            for t, u in zip(self.tipo_de_interaccion, tabla["usuario_id"])])

    def _matrices_por_usuario(self) -> None:
        u, t, k = self.n_usuarios_activos, len(self.tipos), len(self.escala)
        usuario, tipo = self.usuario_de_interaccion, self.tipo_de_interaccion
        calif, origen = self.calificacion_de_interaccion, self.origen_de_interaccion
        coincide = self.interaccion_coincide
        self.conteos_tipo_por_usuario = np.zeros((u, t), dtype=np.int64)
        np.add.at(self.conteos_tipo_por_usuario, (usuario, tipo), 1)
        self.suma_calificaciones_por_usuario_y_tipo = np.zeros((u, t), dtype=np.int64)
        np.add.at(self.suma_calificaciones_por_usuario_y_tipo, (usuario, tipo), self.interacciones["calificacion"].to_numpy())
        self.coincidencias_si_combinacion = self.conteos_tipo_por_usuario @ self.tipos_cubiertos.T
        self.suma_calificaciones_coincidentes_si_combinacion = (
            self.suma_calificaciones_por_usuario_y_tipo @ self.tipos_cubiertos.T)
        self.n_interacciones_por_usuario_activo = self.conteos_tipo_por_usuario.sum(axis=1)
        self.coincidencias_por_usuario = self.coincidencias_si_combinacion[
            np.arange(u), self.combinacion_de_usuario_activo]
        self.calificaciones_coincidentes_por_usuario = np.zeros((u, k), dtype=np.int64)
        self.calificaciones_no_coincidentes_por_usuario = np.zeros((u, k), dtype=np.int64)
        np.add.at(self.calificaciones_coincidentes_por_usuario, (usuario[coincide], calif[coincide]), 1)
        np.add.at(self.calificaciones_no_coincidentes_por_usuario, (usuario[~coincide], calif[~coincide]), 1)
        self.origen_y_tipo_por_usuario = np.zeros((u, 2, t), dtype=np.int64)
        np.add.at(self.origen_y_tipo_por_usuario, (usuario, origen, tipo), 1)
        self.origen_y_calificacion_por_usuario = np.zeros((u, 2, k), dtype=np.int64)
        np.add.at(self.origen_y_calificacion_por_usuario, (usuario, origen, calif), 1)

    def _lineas_base(self, destinos: pd.DataFrame) -> None:
        """Línea base exacta (catálogo uniforme) y marginal (tipos observados) por combinación y por usuario activo."""
        en_catalogo = destinos["tipo"].value_counts()
        self.fraccion_del_catalogo_por_combinacion = np.array(
            [sum(en_catalogo.get(t, 0) for t in self.tipos_por_combinacion[c]) / len(destinos)
             for c in self.combinaciones])
        n_por_usuario = self.n_interacciones_por_usuario_activo
        por_combinacion = self.combinacion_de_usuario_activo
        self.linea_base_exacta_por_usuario = n_por_usuario * self.fraccion_del_catalogo_por_combinacion[por_combinacion]
        self.distribucion_marginal_de_tipos = pd.Series(self.interacciones["tipo"]).value_counts(normalize=True)
        self.fraccion_marginal_por_combinacion = np.array(
            [sum(self.distribucion_marginal_de_tipos.get(t, 0.0) for t in self.tipos_por_combinacion[c])
             for c in self.combinaciones])
        self.linea_base_marginal_por_usuario = n_por_usuario * self.fraccion_marginal_por_combinacion[por_combinacion]

    def _conteos_por_entidad(self, destinos: pd.DataFrame, usuarios: pd.DataFrame) -> None:
        tabla = self.interacciones
        self.n_interacciones_por_usuario = tabla.groupby("usuario_id").size().reindex(
            usuarios["usuario_id"], fill_value=0).to_numpy()
        self.n_interacciones_por_destino = tabla.groupby("destino_id").size().reindex(
            destinos["destino_id"], fill_value=0).to_numpy()
        self.lugares = sorted(destinos["lugar"].unique())
        self.lugar_de_cada_destino = np.searchsorted(self.lugares, destinos["lugar"].to_numpy())
        self.n_interacciones_por_lugar = np.bincount(
            self.lugar_de_cada_destino, weights=self.n_interacciones_por_destino, minlength=len(self.lugares))


# =========================================================================== análisis descriptivo
def analizar_actividad(d: Datos, cfg: dict) -> tuple[dict, np.ndarray]:
    """Histogramas observados y de la referencia uniforme (usuarios y destinos); devuelve (json, simulación de destinos)."""
    nivel, n_sim = cfg["nivel_ic"], cfg["n_simulaciones_azar"]
    out = {"n_interacciones": d.n_interacciones, "n_simulaciones": n_sim, "nivel_ic": nivel,
           "referencia": ("reparto uniforme al azar de las interacciones entre las entidades maestras "
                          "(multinomial con probabilidad 1/n; cada interacción elige una entidad al azar, sin respetar los "
                          "pares únicos); media e IC por percentiles sobre las simulaciones")}
    sim_dest = None
    for nombre, conteos, tope, run in (("usuarios", d.n_interacciones_por_usuario, cfg["tope_usuarios"], "simulacion_usuarios"),
                                       ("destinos", d.n_interacciones_por_destino, cfg["tope_destinos"], "simulacion_destinos")):
        rng = make_rng(cfg["base_seed"], cfg["run_id"][run])
        sim = simular_uniforme(rng, d.n_interacciones, len(conteos), n_sim)
        if nombre == "destinos":
            sim_dest = sim
        h = _histogramas_por_filas(sim, tope)
        claves = list(histograma_de_actividad(conteos, tope))
        lo, hi = _cuantiles(h, nivel)
        out[nombre] = {"n_entidades": int(len(conteos)), "tope": tope,
                       "observado": histograma_de_actividad(conteos, tope),
                       "azar_media": {k: float(v) for k, v in zip(claves, h.mean(axis=0))},
                       "azar_ic95": {k: [float(a), float(b)] for k, a, b in zip(claves, lo, hi)},
                       "max_interacciones_observado": int(np.max(conteos)),
                       "max_interacciones_azar_media": float(sim.max(axis=1).mean())}
    return out, sim_dest


def verificar_contra_ficha(observado: dict, carpeta_salida: Path) -> None:
    """Si ``ficha.json`` existe y usa el mismo tope, el histograma de usuarios debe ser igual al de la ficha."""
    ruta = carpeta_salida / "ficha.json"
    if not ruta.is_file():
        return
    ficha = load_json(ruta)
    union = ficha.get("conteos", {}).get("usuarios_por_numero_de_interacciones", {}).get("union")
    if not isinstance(union, dict) or list(union) != list(observado):
        return
    if union != observado:
        raise ValueError(f"el histograma de usuarios por interacciones no coincide con {ruta.as_posix()}: "
                         f"ficha.json {union} frente a lo calculado aquí {observado}; corre `m3-datos` y `m3-eda` otra vez")


def analizar_concentracion(d: Datos, cfg: dict, sim_dest: np.ndarray) -> dict:
    """Gini, HHI, cuota top y Lorenz por nivel, observados y bajo reparto uniforme (media, IC y p del observado)."""
    nivel, fracs = cfg["nivel_ic"], cfg["fracciones_top"]
    sims = {"destino_id": sim_dest.astype(float),
            "lugar": np.stack([np.bincount(d.lugar_de_cada_destino, weights=f, minlength=len(d.lugares)) for f in sim_dest])}
    obs_conteos = {"destino_id": d.n_interacciones_por_destino.astype(float), "lugar": d.n_interacciones_por_lugar.astype(float)}
    out = {"definiciones": {"gini": "2·Σ i·x_(i)/(n·Σx) − (n+1)/n, sin corrección (máximo (n−1)/n)",
                            "gini_reescalado": "gini·n/(n−1), en [0, 1]: reescala el máximo (n−1)/n a 1; NO es una corrección de sesgo",
                            "hhi": "Σ s_i² con cuotas en [0, 1]", "hhi_normalizado": "(HHI − 1/n)/(1 − 1/n)",
                            "cuota_top": "suma de las ceil(f·n) entidades con más interacciones sobre el total",
                            "lorenz": "vértices (j/n, suma de las j entidades con menos interacciones / total)",
                            "p_observado_mayor_o_igual": "(1 + #{simulaciones >= observado}) / (1 + simulaciones)"},
           "niveles": {}}

    def resumen(obs: float, sim: np.ndarray) -> dict:
        return {"observado": float(obs), "media": float(sim.mean()), "ic95": _ic(sim, nivel),
                "p_observado_mayor_o_igual": float((1 + (sim >= obs - TOLERANCIA_NUMERICA).sum()) / (1 + len(sim))),
                "percentil_observado": float((sim <= obs + TOLERANCIA_NUMERICA).mean())}

    for nombre in cfg["niveles"]:
        x, s = obs_conteos[nombre], sims[nombre]
        n = len(x)
        xs, ys = lorenz(x)
        _, ys_sim = lorenz(s)
        lo, hi = _cuantiles(ys_sim, nivel)
        medidas = {"gini": gini, "gini_reescalado": gini_reescalado, "hhi": hhi, "hhi_normalizado": hhi_normalizado}
        azar = {"n_simulaciones": int(len(s))}
        for clave, medida in medidas.items():
            azar[clave] = resumen(medida(x), medida(s))
        azar["cuota_top"] = {f"{f:g}": resumen(cuota_top(x, f), cuota_top(s, f)) for f in fracs}
        azar["lorenz"] = {"media": np.round(ys_sim.mean(axis=0), 6).tolist(), "ic95_inf": np.round(lo, 6).tolist(),
                          "ic95_sup": np.round(hi, 6).tolist()}
        out["niveles"][nombre] = {
            "n_entidades": n, "n_interacciones": int(x.sum()),
            "observado": {"gini": float(gini(x)), "gini_reescalado": float(gini_reescalado(x)), "hhi": float(hhi(x)),
                          "hhi_normalizado": float(hhi_normalizado(x)),
                          "cuota_top": {f"{f:g}": float(cuota_top(x, f)) for f in fracs},
                          "n_entidades_en_el_top": {f"{f:g}": n_top(n, f) for f in fracs},
                          "entidades_con_cero": int((x == 0).sum()),
                          "lorenz": {"x": np.round(xs, 6).tolist(), "y": np.round(ys, 6).tolist()}},
            "azar_uniforme": azar}
    return out


def _justificar_umbral(p_max: int) -> str:
    """Texto del umbral «pocas»/«muchas» generado desde ``pocas_max`` (la regla D3 cuenta 1 prueba con n >= 2, 1 validación
    con n >= 3)."""
    d3 = "(prueba = 1 interacción de cada usuario con >= 2; validación = 1 más con >= 3; el resto, entrenamiento)"
    if p_max == 1:
        efecto = ("los usuarios con 1 interacción solo aportan entrenamiento; los de 2 o más aportan además prueba (y los de "
                  "3 o más, validación)")
    elif p_max == 2:
        efecto = ("los usuarios con 1 o 2 interacciones aportan a lo sumo una interacción de prueba y ninguna de validación; "
                  "los de 3 o más aportan además validación")
    else:
        efecto = (f"los usuarios con 1 a {p_max} interacciones aportan a lo sumo una de prueba y una de validación (esta "
                  f"última solo si tienen 3 o más); los de {p_max + 1} o más también")
    return (f"Con la partición D3 {d3} {efecto}. Umbral PROPUESTO por esta tarea: Juan José debe confirmarlo. Los "
            "usuarios con exactamente 3 interacciones también quedan con una sola de entrenamiento: "
            "`sensibilidad_umbral` muestra qué pasa con otros umbrales.")


def analizar_actividad_usuarios(d: Datos, cfg: dict) -> dict:
    """Grupos «pocas» / «muchas», cuenta de la partición D3 (sin hacerla) y sensibilidad al umbral."""
    n = d.n_interacciones_por_usuario
    p_max = cfg["actividad"]["pocas_max"]
    aparecen = int((n >= 1).sum())

    def d3(ns: np.ndarray) -> dict:
        prueba, valid = (ns >= 2).astype(int), (ns >= 3).astype(int)
        entren = np.where(ns >= 1, ns - prueba - valid, 0)
        return {"usuarios_con_prueba": int(prueba.sum()), "usuarios_con_validacion": int(valid.sum()),
                "usuarios_solo_entrenamiento": int(((ns >= 1) & (prueba == 0)).sum()),
                "interacciones": {"entrenamiento": int(entren.sum()), "validacion": int(valid.sum()),
                                  "prueba": int(prueba.sum())},
                "entrenamiento_por_usuario": {"min": int(entren.min()) if len(ns) else None,
                                              "media": float(entren.mean()) if len(ns) else None,
                                              "max": int(entren.max()) if len(ns) else None}}

    grupos = {"sin_interacciones": n == 0, "pocas": (n >= 1) & (n <= p_max), "muchas": n > p_max}
    out = {"umbral": {"pocas_max": p_max, "regla": f"pocas = 1 a {p_max} interacciones; muchas = {p_max + 1} o más; "
                                                    "sin_interacciones = 0 (no evaluable)",
                      "justificacion": _justificar_umbral(p_max)},
           "grupos": {}, "particion_d3": {}}
    for g, mask in grupos.items():
        k = int(mask.sum())
        out["grupos"][g] = {"n_usuarios": k, "proporcion_de_maestros": float(k / len(n)),
                            "n_interacciones": int(n[mask].sum()),
                            "media_interacciones": float(n[mask].mean()) if k else None}
        if g != "sin_interacciones":
            out["particion_d3"][g] = d3(n[mask])
    out["particion_d3"]["regla"] = ("D3 (docs/spec/partes/juanjose.md §3.1): prueba = 1 interacción al azar de cada usuario con >= 2; "
                                    "validación = 1 más de cada usuario con >= 3; el resto, entrenamiento; con 1 solo entrenamiento. "
                                    "Esto solo CUENTA; la partición real es de JJ-3.")
    out["particion_d3"]["total"] = d3(n)["interacciones"]
    out["proporcion_pocas"] = {"sobre_usuarios_maestros": float(grupos["pocas"].sum() / len(n)),
                               "sobre_usuarios_que_aparecen": float(grupos["pocas"].sum() / aparecen)}
    out["sensibilidad_umbral"] = []
    for t in cfg["actividad"]["sensibilidad_pocas_max"]:
        k = int(((n >= 1) & (n <= t)).sum())
        out["sensibilidad_umbral"].append({"pocas_max": t, "n_pocas": k, "n_muchas": int((n > t).sum()),
                                           "proporcion_sobre_maestros": float(k / len(n)),
                                           "proporcion_sobre_los_que_aparecen": float(k / aparecen)})
    return out


def _entrada(nombre, hip, desc, estad, valor, p, alt, metodo, efecto, n, unidad, familia="confirmatoria", gl=None,
             **extra):
    return {"id_prueba": nombre, "hipotesis": hip, "familia": familia, "descripcion": desc,
            "estadistico": {"nombre": estad, "valor": valor}, "gl": gl, "alternativa": alt, "metodo_p": metodo,
            "p_crudo": float(p), "p_ajustado": None, "efecto": efecto, "n": int(n), "unidad_de_analisis": unidad, **extra}


def _efecto(nombre, valor, ic, metodo_ic, umbral):
    return {"nombre": nombre, "valor": float(valor), "ic95": [float(ic[0]), float(ic[1])], "metodo_ic": metodo_ic,
            "umbral": umbral}


def _efecto_v(tabla, tablas_boot: np.ndarray, nivel: float, n_boot: int) -> tuple[dict, list[dict]]:
    """Efecto V de Cramér CORREGIDA (valor e IC por percentiles de los remuestreos) y la V sin corregir como adicional."""
    obs = np.asarray(tabla, dtype=float)[None]
    efecto = _efecto("V de Cramér con corrección de sesgo", v_corregida_por_lotes(obs)[0],
                     _ic(v_corregida_por_lotes(tablas_boot), nivel),
                     f"percentiles de {n_boot} remuestreos de usuarios (V corregida en cada uno)", "v_de_cramer")
    return efecto, [{"nombre": "V de Cramér sin corregir", "valor": float(v_de_cramer_por_lotes(obs)[0])}]


def _h1_permutacion(d: Datos, cfg: dict) -> tuple[float, np.ndarray]:
    """p de la permutación de combinaciones entre usuarios activos y las coincidencias (conteo) de cada réplica."""
    rng = make_rng(cfg["base_seed"], cfg["run_id"]["permutacion_h1"])
    filas = np.arange(d.n_usuarios_activos)[None, :]
    nulos = np.concatenate([d.coincidencias_si_combinacion[filas, etiquetas].sum(axis=1) for etiquetas in
                            permutaciones(rng, d.combinacion_de_usuario_activo, cfg["n_permutaciones"])])
    p = p_permutacion(int(d.coincidencias_por_usuario.sum()), nulos, "mayor")
    return p, nulos


def _h1_tabla_combinacion_por_tipo(d: Datos, pesos: np.ndarray) -> np.ndarray:
    """Tabla(s) combinación × tipo de las interacciones, ponderando a los usuarios activos con ``pesos``."""
    return _tablas_de_grupos(pesos, d.conteos_tipo_por_usuario, d.combinacion_de_usuario_activo, len(d.combinaciones))


def _h1_bootstrap(d: Datos, cfg: dict) -> dict:
    """Remuestreo de usuarios: IC de la tasa y de las diferencias con las líneas base, y la V corregida de la tabla."""
    n_boot = cfg["n_bootstrap"]
    pesos = multiplicidades(make_rng(cfg["base_seed"], cfg["run_id"]["bootstrap_h1"]), d.n_usuarios_activos, n_boot)
    n = pesos @ d.n_interacciones_por_usuario_activo
    coincidencias = pesos @ d.coincidencias_por_usuario
    tabla = _h1_tabla_combinacion_por_tipo(d, np.ones((1, d.n_usuarios_activos), dtype=np.int64))[0]
    efecto_v, v_extra = _efecto_v(tabla, _h1_tabla_combinacion_por_tipo(d, pesos), cfg["nivel_ic"], n_boot)
    return {"tasa": coincidencias / n,
            "diferencia_exacta": (coincidencias - pesos @ d.linea_base_exacta_por_usuario) / n,
            "diferencia_marginal": (coincidencias - pesos @ d.linea_base_marginal_por_usuario) / n,
            "tabla": tabla, "efecto_v": efecto_v, "v_extra": v_extra}


def _h1_chi2_de_la_tabla(d: Datos, tabla: np.ndarray, chi: dict) -> dict:
    """χ² combinación × tipo: residuos (ajustados y de Pearson), el mayor y el aporte de las celdas coincidentes."""
    residuos, pearson = residuos_estandarizados(tabla), residuos_de_pearson(tabla)
    cubiertas = d.tipos_cubiertos.astype(bool)
    aporte_si, aporte_no = aporte_al_chi2(tabla, cubiertas)
    i, j = np.unravel_index(np.argmax(np.abs(residuos)), residuos.shape)

    def por_celda(r: np.ndarray) -> dict:
        return {c: {t: float(r[g, k]) for k, t in enumerate(d.tipos)} for g, c in enumerate(d.combinaciones)}

    return {
        "chi2": chi["chi2"], "gl": chi["gl"], "p_asintotico": chi["p"],
        "residuos_estandarizados": por_celda(residuos), "residuos_de_pearson": por_celda(pearson),
        "definicion_residuo": ("estandarizado ajustado = (O − E) / sqrt(E·(1 − fila/n)·(1 − columna/n)); de Pearson = "
                               "(O − E) / sqrt(E); |residuo| > 2 llama la atención. El ajustado es mayor en valor "
                               "absoluto"),
        "residuo_maximo_absoluto": {"combinacion": d.combinaciones[i], "tipo": d.tipos[j],
                                    "valor": float(residuos[i, j]), "valor_de_pearson": float(pearson[i, j])},
        "aporte": {"celdas_coincidentes": aporte_si, "celdas_no_coincidentes": aporte_no,
                   "n_celdas_coincidentes": int(cubiertas.sum()), "n_celdas_no_coincidentes": int((~cubiertas).sum()),
                   "definicion": ("suma de (O − E)²/E en las celdas cuyo tipo está cubierto por la combinación frente a "
                                  "las demás; suman el χ²")}}


def _h1_por_combinacion(d: Datos, tabla: np.ndarray) -> tuple[dict, pd.DataFrame]:
    """Tasa y líneas base de cada combinación con interacciones, y la matriz combinación × tipo (para la figura)."""
    tabla_inter = d.interacciones
    resumen, filas = {}, []
    for g, c in enumerate(d.combinaciones):
        de_la_combinacion = tabla_inter[tabla_inter["combinacion"] == c]
        r = coincidencia(d.destinos["tipo"], de_la_combinacion["usuario_id"].tolist(), de_la_combinacion["tipo"].tolist(),
                         d.tipos_preferidos_por_usuario, marginal=d.distribucion_marginal_de_tipos)
        n_usuarios = int((d.usuarios["combinacion"] == c).sum())
        resumen[c] = {"n": r["n"], "n_usuarios": n_usuarios,
                      "n_usuarios_con_interacciones": int((d.combinacion_de_usuario_activo == g).sum()),
                      "tipos_cubiertos": sorted(d.tipos_por_combinacion[c]), "tasa": r["tasa"],
                      "linea_base_exacta": r["linea_base_exacta"], "linea_base_marginal": r["linea_base_marginal"],
                      "diferencia_exacta": r["diferencia_exacta"]}
        for k, t in enumerate(d.tipos):
            n_celda = int(tabla[g, k])
            filas.append({"combinacion": c, "tipo": t, "conteo": n_celda, "proporcion_fila": n_celda / r["n"],
                          "n_interacciones_fila": r["n"], "n_usuarios_fila": n_usuarios,
                          "coincide": bool(d.tipos_cubiertos[g, k]),
                          "linea_base_fila": float(d.fraccion_del_catalogo_por_combinacion[g])})
    return resumen, pd.DataFrame(filas)


def analizar_h1(d: Datos, cfg: dict) -> tuple[dict, list[dict], pd.DataFrame, np.ndarray]:
    """H-M3-1: coincidencia preferencia–tipo, líneas base, permutación, χ² y bootstrap por usuarios.

    Devuelve (resumen para ``coincidencia_preferencias.json``, pruebas, matriz combinación × tipo y las réplicas
    bootstrap de la diferencia con la línea base exacta, que ``main`` usa para el IC ajustado por multiplicidad)."""
    n_perm, n_boot, nivel = cfg["n_permutaciones"], cfg["n_bootstrap"], cfg["nivel_ic"]
    tipos_de_interacciones = d.interacciones["tipo"].tolist()
    global_ = coincidencia(d.destinos["tipo"], d.interacciones["usuario_id"].tolist(), tipos_de_interacciones,
                           d.tipos_preferidos_por_usuario)
    p_perm, nulos = _h1_permutacion(d, cfg)
    boot = _h1_bootstrap(d, cfg)
    chi = chi2_y_v(boot["tabla"])
    por_combinacion, matriz = _h1_por_combinacion(d, boot["tabla"])
    resumen = {
        "emparejamiento_preferencia_tipo": cfg["emparejamiento_preferencia_tipo"],
        "nota_emparejamiento": ("Emparejamiento léxico NUESTRO (la fuente no documenta la correspondencia entre las "
                                "opciones de Preferences y los valores de Type); ver configs/m3/eda.yaml."),
        "tipos_del_catalogo": d.tipos,
        "ids_por_tipo": {t: int(v) for t, v in d.destinos["tipo"].value_counts().sort_index().items()},
        "global": {**global_, "tasa_ic95": _ic(boot["tasa"], nivel),
                   "diferencia_exacta_ic95": _ic(boot["diferencia_exacta"], nivel),
                   "diferencia_marginal_ic95": _ic(boot["diferencia_marginal"], nivel),
                   "metodo_ic": f"percentiles de {n_boot} remuestreos de usuarios (con sus interacciones)"},
        "distribucion_marginal_de_tipos": {str(k): float(v)
                                           for k, v in d.distribucion_marginal_de_tipos.sort_index().items()},
        "nulo_permutacion": {"n_permutaciones": n_perm, "tasa_media": float(nulos.mean() / d.n_interacciones),
                             "tasa_ic95": [float(x / d.n_interacciones) for x in _cuantiles(nulos, nivel)]},
        "chi2_combinacion_tipo": _h1_chi2_de_la_tabla(d, boot["tabla"], chi),
        "por_combinacion": por_combinacion}
    if d.combinaciones_sin_interacciones:
        resumen["combinaciones_sin_interacciones"] = d.combinaciones_sin_interacciones
    pruebas = [
        _entrada("H1_permutacion_tasa", "H-M3-1",
                 "Permutación de las combinaciones de preferencias entre usuarios con interacciones (se conserva "
                 "cuántas interacciones tiene cada uno y los tipos de sus destinos); estadístico = tasa de coincidencia",
                 "tasa_de_coincidencia", global_["tasa"], p_perm, "mayor",
                 f"permutación (B={n_perm}; p = (1 + #{{T* >= T_obs}}) / (1 + B))",
                 _efecto("tasa − línea base exacta (diferencia de proporciones)", global_["diferencia_exacta"],
                         _ic(boot["diferencia_exacta"], nivel), f"percentiles de {n_boot} remuestreos de usuarios",
                         "diferencia_tasa"),
                 d.n_interacciones, "interacciones", n_permutaciones=n_perm),
        _entrada("C_H1_chi2_combinacion_tipo", "H-M3-1",
                 "χ² de independencia en la tabla combinación de preferencias × tipo de destino (interacciones; supone "
                 "independencia entre interacciones, que no se cumple del todo: un usuario aporta varias)",
                 "chi2", chi["chi2"], chi["p"], "mayor", "asintótica (χ², cola derecha)", boot["efecto_v"],
                 d.n_interacciones, "interacciones", familia="complementaria", gl=chi["gl"],
                 efectos_adicionales=boot["v_extra"])]
    return resumen, pruebas, matriz, boot["diferencia_exacta"]


def analizar_h2(d: Datos, cfg: dict) -> list[dict]:
    """H-M3-2: calificación según coincida o no el tipo con las preferencias."""
    n_perm, n_boot, nivel, base = cfg["n_permutaciones"], cfg["n_bootstrap"], cfg["nivel_ic"], cfg["base_seed"]
    cal = d.interacciones["calificacion"].to_numpy()
    escala = np.array(d.escala, dtype=float)
    total_r, n_tot = int(cal.sum()), d.n_interacciones
    nm, rm = int(d.coincidencias_por_usuario.sum()), int(d.suma_calificaciones_coincidentes_si_combinacion[np.arange(d.n_usuarios_activos), d.combinacion_de_usuario_activo].sum())
    if nm in (0, n_tot):
        raise ValueError("H-M3-2 necesita interacciones que coinciden y que no coinciden")
    dif_obs = rm / nm - (total_r - rm) / (n_tot - nm)
    ar = np.arange(d.n_usuarios_activos)
    nulos = []
    for P in permutaciones(make_rng(base, cfg["run_id"]["permutacion_h2"]), d.combinacion_de_usuario_activo, n_perm):
        r_p, n_p = d.suma_calificaciones_coincidentes_si_combinacion[ar[None, :], P].sum(axis=1), d.coincidencias_si_combinacion[ar[None, :], P].sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            nulos.append(r_p / n_p - (total_r - r_p) / (n_tot - n_p))
    nulos = np.concatenate(nulos)
    p_perm = p_permutacion(dif_obs, nulos[np.isfinite(nulos)], "mayor")
    w = multiplicidades(make_rng(base, cfg["run_id"]["bootstrap_h2"]), d.n_usuarios_activos, n_boot)
    um, un = w @ d.calificaciones_coincidentes_por_usuario, w @ d.calificaciones_no_coincidentes_por_usuario
    dif_b = (um @ escala) / um.sum(axis=1) - (un @ escala) / un.sum(axis=1)
    delta_b, _ = delta_de_cliff(um, un)
    delta, ps = delta_de_cliff(d.calificaciones_coincidentes_por_usuario.sum(axis=0), d.calificaciones_no_coincidentes_por_usuario.sum(axis=0))
    x_si, x_no = cal[d.interaccion_coincide], cal[~d.interaccion_coincide]
    mw = stats.mannwhitneyu(x_si, x_no, alternative="greater", method="asymptotic")
    conf = _entrada("H2_permutacion_calificacion", "H-M3-2",
                    "Permutación de las combinaciones de preferencias entre usuarios; estadístico = media de la calificación de "
                    "las interacciones que coinciden − media de las que no coinciden",
                    "diferencia_de_medias", dif_obs, p_perm, "mayor", f"permutación (B={n_perm}; p = (1 + #{{T* >= T_obs}}) / (1 + B))",
                    _efecto("delta de Cliff (coincide vs. no coincide)", delta, _ic(delta_b, nivel),
                            f"percentiles de {n_boot} remuestreos de usuarios", "delta_de_cliff"), d.n_interacciones, "interacciones",
                    n_permutaciones=n_perm,
                    efectos_adicionales=[{**_efecto("diferencia de medias de calificación", dif_obs, _ic(dif_b, nivel),
                                                    f"percentiles de {n_boot} remuestreos de usuarios", "delta_de_cliff"),
                                          "umbral": None},
                                         {"nombre": "probabilidad de superioridad", "valor": float(ps)}],
                    medias={"coincide": float(x_si.mean()), "no_coincide": float(x_no.mean())},
                    n_por_grupo={"coincide": int(len(x_si)), "no_coincide": int(len(x_no))})
    comp = _entrada("C_H2_mann_whitney_calificacion", "H-M3-2",
                    "Mann–Whitney (unilateral: coincide > no coincide; supone independencia entre interacciones, que no se cumple "
                    "del todo: un usuario aporta varias)",
                    "U", mw.statistic, mw.pvalue, "mayor", "asintótica con corrección por empates",
                    _efecto("delta de Cliff (coincide vs. no coincide)", delta, _ic(delta_b, nivel),
                            f"percentiles de {n_boot} remuestreos de usuarios", "delta_de_cliff"), d.n_interacciones, "interacciones",
                    familia="complementaria")
    return [conf, comp]


def analizar_h3(d: Datos, cfg: dict) -> list[dict]:
    """H-M3-3: Spearman entre popularidad y número de interacciones de cada destino."""
    n_perm, n_boot, nivel, base = cfg["n_permutaciones"], cfg["n_bootstrap"], cfg["nivel_ic"], cfg["base_seed"]
    y = d.n_interacciones_por_destino.astype(float)
    pop = d.destinos["popularidad"].to_numpy(dtype=float)
    ry, rp = stats.rankdata(y), stats.rankdata(pop)
    rho = float(_rho_por_filas(ry, rp))
    nulos = np.concatenate([_rho_por_filas(ry[None, :], P) for P in
                            permutaciones(make_rng(base, cfg["run_id"]["permutacion_h3"]), rp, n_perm)])
    p_perm = p_permutacion(rho, nulos, "dos_colas")
    rng = make_rng(base, cfg["run_id"]["bootstrap_h3"])
    idx = rng.integers(0, len(y), size=(n_boot, len(y)))
    boots = _rho_por_filas(stats.rankdata(y[idx], axis=1), stats.rankdata(pop[idx], axis=1))
    sp = stats.spearmanr(pop, y)
    return [
        _entrada("H3_spearman_popularidad", "H-M3-3",
                 "Permutación de la popularidad entre los destinos; estadístico = ρ de Spearman entre popularidad y número de "
                 "interacciones (con empates, rangos medios)", "rho_de_spearman", rho, p_perm, "dos_colas",
                 f"permutación (B={n_perm}; p = (1 + #{{|T*| >= |T_obs|}}) / (1 + B))",
                 _efecto("ρ de Spearman", rho, _ic(boots, nivel), f"percentiles de {n_boot} remuestreos de destinos",
                         "rho_de_spearman"), len(y), "destinos", n_permutaciones=n_perm,
                 destinos_con_cero=int((y == 0).sum())),
        _entrada("C_H3_spearman_asintotico", "H-M3-3", "ρ de Spearman con el p asintótico de scipy (referencia; con empates es aproximado)",
                 "rho_de_spearman", float(sp.statistic), sp.pvalue, "dos_colas", "asintótica (t de Student)",
                 _efecto("ρ de Spearman", rho, _ic(boots, nivel), f"percentiles de {n_boot} remuestreos de destinos",
                         "rho_de_spearman"), len(y), "destinos", familia="complementaria")]


def analizar_h4(d: Datos, cfg: dict) -> tuple[list[dict], pd.DataFrame]:
    """H-M3-4: demografía × tipo (permutación de las etiquetas entre usuarios; V con bootstrap por usuarios)."""
    n_perm, n_boot, nivel, base = cfg["n_permutaciones"], cfg["n_bootstrap"], cfg["nivel_ic"], cfg["base_seed"]
    w = multiplicidades(make_rng(base, cfg["run_id"]["bootstrap_h4"]), d.n_usuarios_activos, n_boot)
    C32 = d.conteos_tipo_por_usuario.astype(np.float32)
    pruebas, filas = [], []
    for col, idp, run, etiqueta in VARIABLES_DEMOGRAFICAS:
        valores = d.usuarios_activos[col].to_numpy()
        niveles = sorted(pd.unique(valores))
        grupos = np.searchsorted(niveles, valores)
        k = len(niveles)
        obs = _tablas_de_grupos(np.ones((1, d.n_usuarios_activos), dtype=np.int64), d.conteos_tipo_por_usuario, grupos, k)
        chi_obs = float(chi2_por_lotes(obs)[0])
        nulos = np.concatenate([chi2_por_lotes(_tablas_permutadas(P, C32, k)) for P in
                                permutaciones(make_rng(base, cfg["run_id"][f"permutacion_h4_{run}"]), grupos, n_perm)])
        p_perm = p_permutacion(chi_obs, nulos, "mayor")
        efecto_v, v_extra = _efecto_v(obs[0], _tablas_de_grupos(w, d.conteos_tipo_por_usuario, grupos, k), nivel, n_boot)
        asint = chi2_y_v(obs[0])
        pruebas.append(_entrada(
            idp, "H-M3-4", f"Permutación de {etiqueta} entre usuarios con interacciones (se conservan los tipos de cada usuario); "
                           "estadístico = χ² de la tabla variable × tipo (interacciones)",
            "chi2", chi_obs, p_perm, "mayor", f"permutación (B={n_perm}; p = (1 + #{{T* >= T_obs}}) / (1 + B))",
            efecto_v, d.n_interacciones, "interacciones", gl=asint["gl"], n_permutaciones=n_perm,
            p_chi2_asintotico=asint["p"], niveles=[str(x) for x in niveles], efectos_adicionales=v_extra))
        for gi, nv in enumerate(niveles):
            tot = int(obs[0, gi].sum())
            for ti, t in enumerate(d.tipos):
                filas.append({"variable": col, "nivel": str(nv), "tipo": t, "conteo": int(obs[0, gi, ti]),
                              "proporcion_fila": float(obs[0, gi, ti] / tot) if tot else float("nan"),
                              "n_interacciones_fila": tot, "n_usuarios_fila": int((grupos == gi).sum())})
    return pruebas, pd.DataFrame(filas)


def analizar_h5(conc: dict, cfg: dict) -> list[dict]:
    """H-M3-5: Gini (confirmatoria) y HHI/cuota top (complementarias) frente al reparto uniforme simulado."""
    nivel = cfg["nivel_ic"]
    pruebas = []
    for nombre, info in conc["niveles"].items():
        az, obs = info["azar_uniforme"], info["observado"]
        g = az["gini"]
        pruebas.append(_entrada(
            f"H5_gini_{nombre}", "H-M3-5",
            f"Gini de las interacciones por {nombre} frente al reparto uniforme al azar de las mismas {info['n_interacciones']} "
            "interacciones (simulación multinomial)", "gini", obs["gini"], g["p_observado_mayor_o_igual"], "mayor",
            f"simulación uniforme (S={az['n_simulaciones']}; p = (1 + #{{sim >= obs}}) / (1 + S))",
            _efecto("Gini observado − media del Gini bajo azar", obs["gini"] - g["media"],
                    (obs["gini"] - g["ic95"][1], obs["gini"] - g["ic95"][0]),
                    METODO_IC_SIMULACION.format(s=az["n_simulaciones"]), "exceso_de_gini"),
            info["n_interacciones"], "interacciones", n_entidades=info["n_entidades"], referencia_azar_media=g["media"],
            referencia_azar_ic95=g["ic95"]))
        for clave in ("hhi", "hhi_normalizado"):
            r = az[clave]
            pruebas.append(_entrada(
                f"C_H5_{clave}_{nombre}", "H-M3-5", f"{clave} por {nombre} frente al reparto uniforme simulado", clave,
                obs[clave], r["p_observado_mayor_o_igual"], "mayor", f"simulación uniforme (S={az['n_simulaciones']})",
                _efecto(f"{clave} observado − media bajo azar", obs[clave] - r["media"],
                        (obs[clave] - r["ic95"][1], obs[clave] - r["ic95"][0]), METODO_IC_SIMULACION.format(s=az["n_simulaciones"]),
                        None),
                info["n_interacciones"], "interacciones", familia="complementaria"))
        for f, r in az["cuota_top"].items():
            pruebas.append(_entrada(
                f"C_H5_cuota_top_{f}_{nombre}", "H-M3-5",
                f"Cuota de interacciones del {float(f):.0%} de {nombre} más popular frente al reparto uniforme simulado",
                "cuota_top", obs["cuota_top"][f], r["p_observado_mayor_o_igual"], "mayor",
                f"simulación uniforme (S={az['n_simulaciones']})",
                _efecto("cuota observada − media bajo azar", obs["cuota_top"][f] - r["media"],
                        (obs["cuota_top"][f] - r["ic95"][1], obs["cuota_top"][f] - r["ic95"][0]),
                        METODO_IC_SIMULACION.format(s=az["n_simulaciones"]), None),
                info["n_interacciones"], "interacciones", familia="complementaria"))
    return pruebas


def analizar_calificaciones(d: Datos) -> pd.DataFrame:
    filas = []
    for origen, mask in (("resena", d.interacciones["origen"] == "resena"), ("historial", d.interacciones["origen"] == "historial"),
                         ("union", np.ones(len(d.interacciones), dtype=bool))):
        c = d.interacciones.loc[mask, "calificacion"]
        for k in d.escala:
            n_k = int((c == k).sum())
            filas.append({"origen": origen, "calificacion": k, "conteo": n_k, "proporcion": n_k / len(c),
                          "n_origen": int(len(c)), "media_origen": float(c.mean()), "desviacion_origen": float(c.std(ddof=1))})
    return pd.DataFrame(filas)


def analizar_h6(d: Datos, cfg: dict) -> list[dict]:
    """H-M3-6: reseñas vs. historial en tipos (χ², V) y calificaciones (Mann–Whitney, delta de Cliff)."""
    n_boot, nivel, base = cfg["n_bootstrap"], cfg["nivel_ic"], cfg["base_seed"]
    w = multiplicidades(make_rng(base, cfg["run_id"]["bootstrap_h6"]), d.n_usuarios_activos, n_boot)
    n_t, n_k = len(d.tipos), len(d.escala)
    tabla = d.origen_y_tipo_por_usuario.sum(axis=0)
    chi_v = chi2_y_v(tabla)
    tablas_b = (w @ d.origen_y_tipo_por_usuario.reshape(d.n_usuarios_activos, 2 * n_t)).reshape(n_boot, 2, n_t)
    efecto_v, v_extra = _efecto_v(tabla, tablas_b, nivel, n_boot)
    cr_b = (w @ d.origen_y_calificacion_por_usuario.reshape(d.n_usuarios_activos, 2 * n_k)).reshape(n_boot, 2, n_k)
    delta_b, _ = delta_de_cliff(cr_b[:, 0, :], cr_b[:, 1, :])
    delta, ps = delta_de_cliff(d.origen_y_calificacion_por_usuario.sum(axis=0)[0], d.origen_y_calificacion_por_usuario.sum(axis=0)[1])
    cal = d.interacciones["calificacion"].to_numpy()
    res, his = cal[d.origen_de_interaccion == 0], cal[d.origen_de_interaccion == 1]
    mw = stats.mannwhitneyu(res, his, alternative="two-sided", method="asymptotic")
    chi_cal = chi2_y_v(d.origen_y_calificacion_por_usuario.sum(axis=0))
    efecto_vc, v_extra_c = _efecto_v(d.origen_y_calificacion_por_usuario.sum(axis=0), cr_b, nivel, n_boot)
    return [
        _entrada("H6_chi2_origen_tipo", "H-M3-6",
                 "χ² de independencia en la tabla origen (reseña / historial) × tipo de destino (supone independencia entre "
                 "interacciones; la misma persona puede estar en ambos orígenes)", "chi2", chi_v["chi2"], chi_v["p"], "mayor",
                 "asintótica (χ²)", efecto_v, d.n_interacciones, "interacciones", gl=chi_v["gl"], efectos_adicionales=v_extra,
                 conteos={o: {t: int(tabla[i, j]) for j, t in enumerate(d.tipos)} for i, o in enumerate(ORIGENES)}),
        _entrada("H6_mann_whitney_calificacion", "H-M3-6",
                 "Mann–Whitney bilateral de la calificación de reseñas frente a la de historial (supone independencia entre "
                 "interacciones)", "U", mw.statistic, mw.pvalue, "dos_colas", "asintótica con corrección por empates",
                 _efecto("delta de Cliff (reseña vs. historial)", delta, _ic(delta_b, nivel),
                         f"percentiles de {n_boot} remuestreos de usuarios", "delta_de_cliff"),
                 d.n_interacciones, "interacciones", probabilidad_de_superioridad=float(ps),
                 medias={"resena": float(res.mean()), "historial": float(his.mean())}),
        _entrada("C_H6_chi2_origen_calificacion", "H-M3-6", "χ² de independencia origen × calificación (referencia)",
                 "chi2", chi_cal["chi2"], chi_cal["p"], "mayor", "asintótica (χ², cola derecha)", efecto_vc,
                 d.n_interacciones, "interacciones", familia="complementaria", gl=chi_cal["gl"], efectos_adicionales=v_extra_c)]


# =========================================================================== escritura
def _escribir_csv(df: pd.DataFrame, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    df.to_csv(tmp, index=False, encoding="utf-8", lineterminator="\n")
    tmp.replace(ruta)


def _tablas_por_entidad(d: Datos, grupo_de_usuario: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    m = d.interacciones
    por_usuario = m.groupby(["usuario_id", "origen"]).size().unstack(fill_value=0).reindex(d.usuarios["usuario_id"], fill_value=0)
    tabla_usuarios = pd.DataFrame({"usuario_id": d.usuarios["usuario_id"].to_numpy(),
                       "n_interacciones": d.n_interacciones_por_usuario,
                       "n_resenas": por_usuario.get("resena", pd.Series(0, index=por_usuario.index)).to_numpy(),
                       "n_historial": por_usuario.get("historial", pd.Series(0, index=por_usuario.index)).to_numpy(),
                       "grupo_actividad": grupo_de_usuario})
    por_destino = m.groupby(["destino_id", "origen"]).size().unstack(fill_value=0).reindex(d.destinos["destino_id"], fill_value=0)
    tabla_destinos = pd.DataFrame({"destino_id": d.destinos["destino_id"].to_numpy(), "lugar": d.destinos["lugar"].to_numpy(),
                        "tipo": d.destinos["tipo"].to_numpy(), "popularidad": d.destinos["popularidad"].to_numpy(),
                        "n_interacciones": d.n_interacciones_por_destino,
                        "n_resenas": por_destino.get("resena", pd.Series(0, index=por_destino.index)).to_numpy(),
                        "n_historial": por_destino.get("historial", pd.Series(0, index=por_destino.index)).to_numpy()})
    tabla_lugares = pd.DataFrame({"lugar": d.lugares})
    tipo_de_lugar = d.destinos.drop_duplicates("lugar").set_index("lugar")["tipo"]
    tabla_lugares["tipo"] = [tipo_de_lugar[x] for x in d.lugares]
    tabla_lugares["n_destinos"] = np.bincount(d.lugar_de_cada_destino, minlength=len(d.lugares))
    tabla_lugares["n_interacciones"] = d.n_interacciones_por_lugar.astype(int)
    tabla_lugares["proporcion_interacciones"] = tabla_lugares["n_interacciones"] / tabla_lugares["n_interacciones"].sum()
    tabla_lugares["media_por_destino"] = tabla_lugares["n_interacciones"] / tabla_lugares["n_destinos"]
    return tabla_usuarios, tabla_destinos, tabla_lugares


def _ajustar_y_marcar(todas: list[dict], cfg: dict, diferencias_h1: np.ndarray, h1: dict) -> tuple[list[dict], list[dict]]:
    """Ajuste por multiplicidad de la familia confirmatoria, marca ``en_el_limite`` e IC ajustado de H-M3-1.

    Devuelve (pruebas con la familia confirmatoria primero, familia confirmatoria)."""
    familia = [p for p in todas if p["familia"] == "confirmatoria"]
    for p, ajustado in zip(familia, ajustar_multiplicidad([p["p_crudo"] for p in familia], cfg["ajuste_multiple"])):
        p["p_ajustado"] = float(ajustado)
    for p in familia:
        p["efecto"]["en_el_limite"] = en_el_limite(tuple(p["efecto"]["ic95"]), cfg["efecto_minimo"][p["efecto"]["umbral"]],
                                                   cfg["tolerancia_limite"], p["alternativa"])
    nivel_ajustado = 1.0 - cfg["alfa"] / len(familia)
    ic_ajustado = [float(x) for x in _cuantiles(diferencias_h1, nivel_ajustado)]
    h1["global"]["diferencia_exacta_ic_ajustado"] = {
        "nivel": nivel_ajustado, "m_familia": len(familia), "ic": ic_ajustado,
        "metodo": ("percentiles de los mismos remuestreos de usuarios que el IC 95 %, con nivel 1 − alfa/m "
                   "(m = tamaño de la familia confirmatoria); coherente con la multiplicidad (Bonferroni)")}
    buscar_prueba(familia, "H1_permutacion_tasa")["efecto"]["ic_ajustado"] = ic_ajustado
    return familia + [p for p in todas if p["familia"] == "complementaria"], familia


def _resumen_de_pruebas(cfg: dict, familia: list[dict], pruebas: list[dict]) -> dict:
    return {
        "alfa": cfg["alfa"], "ajuste": cfg["ajuste_multiple"], "m_familia": len(familia),
        "familia_confirmatoria": [p["id_prueba"] for p in familia],
        "criterio_de_veredicto": {
            "efecto_minimo": cfg["efecto_minimo"], "regla": cfg["regla_de_veredicto"],
            "tolerancia_limite": cfg["tolerancia_limite"],
            "tolerancia_limite_descripcion": ("una prueba lleva `efecto.en_el_limite: true` si un límite de su IC 95 % "
                                              "está a menos de esta tolerancia del mínimo (+mínimo, y −mínimo si es "
                                              "bilateral): su veredicto depende del ruido de Monte Carlo")},
        "semillas": {"base_seed": cfg["base_seed"], "run_id": cfg["run_id"]},
        "n_permutaciones": cfg["n_permutaciones"], "n_bootstrap": cfg["n_bootstrap"],
        "n_simulaciones_azar": cfg["n_simulaciones_azar"], "nivel_ic": cfg["nivel_ic"], "pruebas": pruebas}


def main(cfg: dict) -> int:
    validar_config(cfg)
    destinos, usuarios, inter = _leer(cfg)
    _validar(destinos, usuarios, inter)
    d = Datos(destinos, usuarios, inter, cfg["emparejamiento_preferencia_tipo"])
    for combinacion in d.combinaciones_sin_interacciones:
        print(f"Aviso: la combinación de preferencias «{combinacion}» tiene usuarios pero sin interacciones; "
              "se omite de la coincidencia preferencia–tipo.")
    out = Path(cfg["salida"]["carpeta"])

    # Todo se calcula antes de escribir: si algo falla, no queda nada a medias.
    dist, simulacion_destinos = analizar_actividad(d, cfg)
    verificar_contra_ficha(dist["usuarios"]["observado"], out)
    conc = analizar_concentracion(d, cfg, simulacion_destinos)
    act = analizar_actividad_usuarios(d, cfg)
    n, pocas_max = d.n_interacciones_por_usuario, cfg["actividad"]["pocas_max"]
    grupo = np.where(n == 0, "sin_interacciones", np.where(n <= pocas_max, "pocas", "muchas"))
    tab_usuarios, tab_destinos, tab_lugares = _tablas_por_entidad(d, grupo)
    h1, pruebas_h1, matriz, diferencias_h1 = analizar_h1(d, cfg)
    demografia_pruebas, demografia = analizar_h4(d, cfg)
    todas = (pruebas_h1 + analizar_h2(d, cfg) + analizar_h3(d, cfg) + demografia_pruebas + analizar_h5(conc, cfg)
             + analizar_h6(d, cfg))
    pruebas, familia = _ajustar_y_marcar(todas, cfg, diferencias_h1, h1)
    hip = construir_hipotesis(cfg, pruebas, h1, conc)

    _escribir_csv(tab_usuarios, out / "interacciones_por_usuario.csv")
    _escribir_csv(tab_destinos, out / "interacciones_por_destino.csv")
    _escribir_csv(tab_lugares, out / "interacciones_por_lugar.csv")
    save_json(out / "distribucion_actividad.json", dist)
    _escribir_csv(analizar_calificaciones(d), out / "calificaciones.csv")
    save_json(out / "concentracion.json", conc)
    save_json(out / "actividad_usuarios.json", act)
    save_json(out / "coincidencia_preferencias.json", h1)
    _escribir_csv(matriz, out / "matriz_preferencias_tipo.csv")
    _escribir_csv(demografia, out / "demografia_tipo.csv")
    save_json(out / "pruebas_hipotesis.json", _resumen_de_pruebas(cfg, familia, pruebas))
    escribir_hipotesis(out / "hipotesis.json", hip)
    _imprimir(cfg, d, dist, conc, act, h1, pruebas, hip)
    return 0


def _imprimir(cfg, d, dist, conc, act, h1, pruebas, hip) -> None:
    print(f"Usuarios: {len(d.usuarios)} (con interacciones: {d.n_usuarios_activos}) · destinos: {len(d.destinos)} · "
          f"interacciones: {d.n_interacciones}")
    for nombre in ("usuarios", "destinos"):
        print(f"{nombre.capitalize()} por n.º de interacciones (observado | azar media): "
              + " · ".join(f"{k}: {v} | {dist[nombre]['azar_media'][k]:.1f}" for k, v in dist[nombre]["observado"].items()))
    for nombre, info in conc["niveles"].items():
        g = info["azar_uniforme"]["gini"]
        print(f"Gini {nombre}: {info['observado']['gini']:.4f} "
              f"(azar {g['media']:.4f}, IC 95 % [{g['ic95'][0]:.4f}; {g['ic95'][1]:.4f}])")
    a = act["grupos"]
    print(f"Actividad: pocas (<= {act['umbral']['pocas_max']}) {a['pocas']['n_usuarios']} · muchas "
          f"{a['muchas']['n_usuarios']} · sin interacciones {a['sin_interacciones']['n_usuarios']}")
    g = h1["global"]
    print(f"H-M3-1: tasa {g['tasa']:.4f} · línea base exacta {g['linea_base_exacta']:.4f} · "
          f"marginal {g['linea_base_marginal']:.4f}")
    for p in pruebas:
        if p["familia"] == "confirmatoria":
            print(f"  {p['id_prueba']}: p crudo {p['p_crudo']:.4g} · p ajustado {p['p_ajustado']:.4g} · "
                  f"efecto {p['efecto']['valor']:.4f} ({p['efecto']['nombre']})")
    print("Veredictos: " + " · ".join(f"{h['id']} {h['veredicto']}" for h in hip))
    print(f"Salida: {Path(cfg['salida']['carpeta']).as_posix()}")
