"""M1 — modelos de referencia (CA-5; núcleo §5.3 y §6; spec de Camila §3.5).

Dos `Pronosticador` (protocolo del núcleo §5.3) para que el arnés común de Andrés (`evaluar_origen_rodante`, AN-1) los evalúe
sin cambios:

1. `IngenuoEstacional` (`nombre = "ingenuo_estacional"`). Para el origen t0 y el horizonte h, el pronóstico del día t0+h es el
   valor observado del mismo día de la semana en la última semana con dato <= t0: y(t0 + h − 7k) con k = ⌈h/7⌉ (el menor k
   tal que t0 + h − 7k <= t0). Si ese día no tiene dato (`sin_registro`) se retrocede una semana más (máximo configurable) y,
   en último caso, se usa la media de la historia <= t0. Cuantiles: el método no tiene distribución propia, así que se usan los
   cuantiles empíricos de SUS errores de train (y − punto), por ruta y por tramo de horizonte (1–7, 8–14, 15–30), sumados al
   punto y truncados en 0. Se separan por tramo porque el error crece con h (el dato base es cada vez más viejo) y por ruta
   porque las escalas difieren. Supuesto: los errores de train son una muestra representativa de los del test; con el
   cambio de régimen de 11001-15759 (nov-2022) ese supuesto es débil (se reporta, no se corrige).

2. `RegresionCalendario` (`nombre = "regresion_calendario"`) [DECIDIDO, Camila, 26-nov]: el modelo estadístico del enunciado
   (tarea 5). Un modelo DIRECTO por ruta (un ajuste para todos los h, con h como variable) sobre z = log1p(pasajeros). Para
   el origen t0 y la fecha objetivo T = t0 + h, las variables son solo información conocible en t0:
   (a) resúmenes de la serie hasta t0: media de log1p de los últimos 7 y 28 días y media del mismo día de la semana de T en
       las últimas 4 semanas con fecha <= t0 (ventanas configurables);
   (b) calendario de T: `dia_semana` en dummies (lunes = referencia), `festivo`, `puente`, `semana_santa`,
       `jueves_viernes_santo`, `fin_de_anio` y `vacaciones_escolares_<origen_divipola de la ruta>`;
   (c) h / horizonte_máximo.
   Regla 0.9 para (b): la variable de vacaciones del día objetivo vale 0 (sin receso; NO NaN) si el origen es anterior a la
   columna `vacaciones_escolares_<divipola>_conocible_desde` de esa fecha (el acto que la fija aún no existía). Vale 0 y no NaN
   porque es el mismo tratamiento que se da a un nulo al pronosticar (0 = sin receso) y porque descartar la fila haría el
   entrenamiento distinto del pronóstico; se aplica igual en train y en pronóstico. Si el calendario no trae la columna
   `_conocible_desde` (p. ej. datos sintéticos) no se anula nada; un `conocible_desde` nulo tampoco anula.
   Ridge de sklearn con alpha fijo (config; sin búsqueda: `n_configuraciones_busqueda` = 0; alpha = 0 es mínimos cuadrados).
   Cuantiles: se estima z_hat; los residuos de train (z − z_hat) se agrupan por tramo de horizonte y ruta; el cuantil q es
   expm1(z_hat + cuantil_q(residuos)) truncado en 0. El punto es expm1(z_hat). Sesgo de la retransformación: expm1(E[z]) es la
   mediana condicional (si los residuos son simétricos en escala log), no la media: tiende a quedar por DEBAJO de la media de
   pasajeros; no se aplica corrección de smearing. Los residuos son de ajuste (dentro de muestra), así que los cuantiles son
   algo estrechos respecto del test. Nulos del calendario: las filas de entrenamiento con algún nulo en una variable usada
   (Cali y Sogamoso tienen nulos solo en enero de 2021 y Sogamoso en 2024, ambos fuera del periodo) se descartan; al
   pronosticar un nulo cuenta como 0 (sin receso). Si la columna `vacaciones_escolares_<origen>` no existe en el calendario
   (p. ej. datos sintéticos), esa variable se omite.

Reglas contra fuga (núcleo §5.3), cada una probada en tests/test_referencia_m1.py:
- Regla 1 (lista blanca): solo se leen `ruta_id`, `fecha`, `pasajeros` y el calendario. Nunca `anomalo`, `despachos`, el
  detalle ni columnas extra. EXCEPCIÓN declarada: `sin_registro` se lee solo para enmascarar como NaN los días sin dato (valen
  0, pero no son demanda); nunca es variable de entrada y la máscara de cada día solo depende de ese día.
- Regla 3: la historia empieza en `inicio_entrenamiento` (2021-06-01): ningún dato anterior entra a ventanas ni a la
  estimación; el primer origen usable de la regresión es inicio + (ventana máxima − 1) días.
- `pronosticar(origen)` recorta la historia a fechas <= origen antes de calcular variables.
- Los parámetros (coeficientes y cuantiles de error) se estiman solo con fechas <= `fin_entrenamiento` (objetivo incluido).
- Días `sin_registro` excluidos de la estimación (son NaN en la historia y filas sin objetivo se descartan).

Ambigüedad del protocolo: `ajustar(serie, calendario)` recibe la serie y `pronosticar(origen, ...)` no; el modelo guarda la
historia en el objeto y la filtra por origen. Con un arnés que reajuste por origen habría que decidir si `ajustar` recibe la
serie completa (como aquí) o solo la parte <= origen: los resultados son idénticos por construcción (prueba de fuga).

Salida de `main`: `results/data/m1/pred_test_<modelo>.parquet` (`origen, ruta_id, fecha, h, y, punto, q0.5, q0.75, q0.9,
q0.95`; `y` = observado, `sin_registro` NO se enmascara aquí: lo hace el arnés) y
`results/data/m1/referencia/presupuesto.json` (núcleo §5.9 y §6). Determinista: no usa semillas. Sin red.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.linear_model import Ridge

from src.comun.config import apply_overrides, load_config
from src.comun.results import save_json

COLUMNAS_SERIE = ("ruta_id", "fecha", "pasajeros")  # lista blanca (§5.3 regla 1)
COLUMNA_MASCARA = "sin_registro"  # solo para enmascarar días sin dato (ver docstring)
COLUMNAS_CALENDARIO = ("festivo", "puente", "semana_santa", "jueves_viernes_santo", "fin_de_anio")
PREFIJO_VACACIONES = "vacaciones_escolares_"
SUFIJO_CONOCIBLE = "_conocible_desde"
DIAS_SEMANA = 7
COLUMNAS_PRED = ["origen", "ruta_id", "fecha", "h", "y", "punto"]
DEVICE = "cpu"


def _ts(x) -> pd.Timestamp:
    return pd.Timestamp(x).normalize()


def nombre_cuantil(q: float) -> str:
    return f"q{q:g}"


def _validar_tramos(tramos) -> list[tuple[int, int]]:
    t = [(int(a), int(b)) for a, b in tramos]
    vacio_o_no_empieza_en_1 = not t or t[0][0] != 1
    invertido = any(a > b for a, b in t)
    con_hueco_o_traslape = any(t[i][1] + 1 != t[i + 1][0] for i in range(len(t) - 1))
    if vacio_o_no_empieza_en_1 or invertido or con_hueco_o_traslape:
        raise ValueError(f"Los tramos de horizonte deben ser contiguos y empezar en 1: {tramos}")
    return t


def _nanmean(g: np.ndarray) -> np.ndarray:
    """Media por fila ignorando NaN (NaN si toda la fila lo es)."""
    ok = ~np.isnan(g)
    n = ok.sum(axis=1)
    s = np.where(ok, g, 0.0).sum(axis=1)
    return np.where(n > 0, s / np.maximum(n, 1), np.nan)


def _cuantiles_desplazados(muestras: list[np.ndarray], tramo: np.ndarray, q: float) -> np.ndarray:
    """Cuantil `q` de la muestra de errores (o residuos) del tramo de cada horizonte: el desplazamiento que se suma al punto."""
    por_tramo = [np.quantile(x, q) for x in muestras]
    return np.array([por_tramo[i] for i in tramo])


class _Base:
    """Lectura de la serie con lista blanca, historia por ruta y utilidades comunes de los dos modelos."""

    nombre: str

    def __init__(self, inicio, fin, tramos) -> None:
        self.inicio = _ts(inicio)
        self.fin = _ts(fin)
        if self.fin <= self.inicio:
            raise ValueError("fin_entrenamiento debe ser posterior a inicio_entrenamiento")
        self.tramos = _validar_tramos(tramos)
        self.hmax = self.tramos[-1][1]
        self._v: dict[str, np.ndarray] = {}
        self._cal: pd.DataFrame | None = None
        self._ajustado = False

    # --- lectura -------------------------------------------------------------------------------------------------
    def _leer(self, serie: pd.DataFrame, calendario: pd.DataFrame) -> None:
        self._leer_serie(serie)
        self._leer_calendario(calendario)

    def _leer_serie(self, serie: pd.DataFrame) -> None:
        faltan = [c for c in COLUMNAS_SERIE if c not in serie.columns]
        if faltan:
            raise KeyError(f"Faltan columnas en la serie: {faltan}")
        cols = list(COLUMNAS_SERIE) + ([COLUMNA_MASCARA] if COLUMNA_MASCARA in serie.columns else [])
        s = serie[cols].copy()  # lista blanca: nada más pasa de aquí
        s["fecha"] = pd.to_datetime(s["fecha"]).dt.normalize()
        s = s[s["fecha"] >= self.inicio]  # regla 3: nada anterior a inicio_entrenamiento
        s["pasajeros"] = s["pasajeros"].astype(float)
        if COLUMNA_MASCARA in s.columns:
            s.loc[s[COLUMNA_MASCARA].astype(bool), "pasajeros"] = np.nan
        self._ultima = s["fecha"].max()
        eje = pd.date_range(self.inicio, self._ultima, freq="D")
        self._v = {}
        for r, g in s.groupby("ruta_id", sort=True):
            self._v[str(r)] = g.set_index("fecha")["pasajeros"].reindex(eje).to_numpy(dtype=float)
        if not self._v:
            raise ValueError("La serie no tiene datos desde inicio_entrenamiento")
        self._n_fin = (self.fin - self.inicio).days  # posición de fin_entrenamiento
        if self._n_fin >= len(eje):
            raise ValueError("fin_entrenamiento está fuera de la serie")

    def _leer_calendario(self, calendario: pd.DataFrame) -> None:
        falta_cal = [c for c in ("fecha", "dia_semana", *COLUMNAS_CALENDARIO) if c not in calendario.columns]
        if falta_cal:
            raise KeyError(f"Faltan columnas en el calendario: {falta_cal}")
        usar = [c for c in calendario.columns if c in ("fecha", "dia_semana", *COLUMNAS_CALENDARIO)
                or c.startswith(PREFIJO_VACACIONES)]
        cal = calendario[usar].copy()
        cal["fecha"] = pd.to_datetime(cal["fecha"]).dt.normalize()
        for c in cal.columns:
            if c.endswith(SUFIJO_CONOCIBLE):
                cal[c] = pd.to_datetime(cal[c])
        self._cal = cal.set_index("fecha")

    def _tramo(self, h: np.ndarray) -> np.ndarray:
        idx = np.full(h.shape, -1, dtype=int)
        for i, (a, b) in enumerate(self.tramos):
            idx[(h >= a) & (h <= b)] = i
        return idx

    def _t0(self, origen, v_len: int, minimo: int = 0) -> int:
        t0 = (_ts(origen) - self.inicio).days
        if not self._ajustado:
            raise RuntimeError("Llama a ajustar() antes de pronosticar()")
        if t0 < minimo:
            raise ValueError(f"origen {origen} anterior al primer origen usable "
                             f"({(self.inicio + pd.Timedelta(days=minimo)).date()})")
        if t0 >= v_len:
            raise ValueError(f"origen {origen} posterior al último día con datos ({self._ultima.date()})")
        return t0

    def _salida(self, ruta, t0_ts, h, punto, cuantiles_val, cuantiles) -> pd.DataFrame:
        d = {"ruta_id": ruta, "fecha": [(t0_ts + pd.Timedelta(days=int(x))).date() for x in h], "h": h.astype(int),
             "punto": punto}
        for q, vals in zip(cuantiles, cuantiles_val):
            d[nombre_cuantil(q)] = vals
        return pd.DataFrame(d)

    # --- interfaz común ------------------------------------------------------------------------------------------
    def parametros(self) -> dict[str, dict[str, np.ndarray]]:  # pragma: no cover - lo definen las subclases
        raise NotImplementedError

    def n_configuraciones_busqueda(self) -> int:
        return 0

    def pronosticar(self, origen: date, horizonte: int, cuantiles: list[float]) -> pd.DataFrame:
        if horizonte < 1 or horizonte > self.hmax:
            raise ValueError(f"horizonte debe estar en 1..{self.hmax}")
        partes = [self._pronosticar_ruta(r, origen, horizonte, cuantiles) for r in self._v]
        return pd.concat(partes, ignore_index=True)

    def _pronosticar_ruta(self, ruta, origen, horizonte, cuantiles):  # pragma: no cover
        raise NotImplementedError


# ================================================================================================= ingenuo estacional

def _punto_ingenuo(v: np.ndarray, t0: np.ndarray, h: np.ndarray, retroceso: int) -> np.ndarray:
    """y(t0 + h − 7k) con k = ⌈h/7⌉; si es NaN retrocede semanas (hasta `retroceso` extra). NaN si no hay dato."""
    k = -(-h // DIAS_SEMANA)
    base = t0 + h - DIAS_SEMANA * k
    out = np.full(base.shape, np.nan)
    for e in range(retroceso + 1):
        idx = base - DIAS_SEMANA * e
        ok = (idx >= 0) & np.isnan(out)
        cand = np.full(base.shape, np.nan)
        cand[ok] = v[idx[ok]]
        out = np.where(np.isnan(out) & ~np.isnan(cand), cand, out)
    return out


class IngenuoEstacional(_Base):
    nombre = "ingenuo_estacional"

    def __init__(self, inicio, fin, tramos, max_semanas_retroceso: int) -> None:
        super().__init__(inicio, fin, tramos)
        self.retroceso = int(max_semanas_retroceso)
        self._err: dict[str, list[np.ndarray]] = {}

    def ajustar(self, serie: pd.DataFrame, calendario: pd.DataFrame) -> None:
        self._leer(serie, calendario)
        self._ajustado = True
        self._err = {}
        t0g, hg = np.meshgrid(np.arange(self._n_fin), np.arange(1, self.hmax + 1), indexing="ij")
        t0g, hg = t0g.ravel(), hg.ravel()
        ok = t0g + hg <= self._n_fin  # objetivo <= fin_entrenamiento
        t0g, hg = t0g[ok], hg[ok]
        tr = self._tramo(hg)
        for r, v in self._v.items():
            punto = _punto_ingenuo(v, t0g, hg, self.retroceso)
            y = v[t0g + hg]
            e = y - punto
            val = np.isfinite(e)
            self._err[r] = []
            for i in range(len(self.tramos)):
                x = np.sort(e[val & (tr == i)])
                if len(x) == 0:
                    raise ValueError(f"Sin errores de train para {r}, tramo {self.tramos[i]}: train demasiado corto")
                self._err[r].append(x)

    def parametros(self):
        return {r: {f"errores_tramo{i}": x for i, x in enumerate(xs)} for r, xs in self._err.items()}

    def n_parametros(self) -> int:
        """Sin parámetros estimados en el punto. Los desplazamientos de cuantiles son valores empíricos, no parámetros."""
        return 0

    def _pronosticar_ruta(self, ruta, origen, horizonte, cuantiles):
        vv = self._v[ruta]
        t0 = self._t0(origen, len(vv))
        vv = vv[: t0 + 1]  # solo fechas <= origen
        h = np.arange(1, horizonte + 1)
        punto = _punto_ingenuo(vv, np.full(h.shape, t0), h, self.retroceso)
        if np.isnan(punto).any():
            # Al pronosticar no se puede descartar el día (hay que entregar un valor): se usa la media de la historia <= origen.
            # En el ajuste, en cambio, los puntos sin base se excluyen de los errores (no hay error que medir).
            media = np.nanmean(vv)
            punto = np.where(np.isnan(punto), media, punto)
        tr = self._tramo(h)
        vals = [np.maximum(punto + _cuantiles_desplazados(self._err[ruta], tr, q), 0.0) for q in cuantiles]
        return self._salida(ruta, self.inicio + pd.Timedelta(days=t0), h, np.maximum(punto, 0.0), vals, cuantiles)


# ================================================================================================= regresión + calendario

class RegresionCalendario(_Base):
    nombre = "regresion_calendario"

    def __init__(self, inicio, fin, tramos, alpha: float, ventana_corta: int, ventana_larga: int,
                 semanas_mismo_dia: int) -> None:
        super().__init__(inicio, fin, tramos)
        self.alpha = float(alpha)
        self.vc, self.vl, self.sem = int(ventana_corta), int(ventana_larga), int(semanas_mismo_dia)
        self.ventana = max(self.vc, self.vl, DIAS_SEMANA * self.sem)
        self._modelo: dict[str, Ridge] = {}
        self._res: dict[str, list[np.ndarray]] = {}
        self._media: dict[str, float] = {}

    # --- variables -----------------------------------------------------------------------------------------------
    def _cols_calendario(self, ruta: str) -> list[str]:
        cols = list(COLUMNAS_CALENDARIO)
        vac = PREFIJO_VACACIONES + ruta.split("-")[0]
        if vac in self._cal.columns:
            cols.append(vac)
        return cols

    def _matriz(self, ruta: str, v: np.ndarray, t0: np.ndarray, h: np.ndarray) -> np.ndarray:
        """Variables (n, p) del par (t0, h) usando SOLO v[: t0 + 1] y el calendario de la fecha objetivo:
        (a) resúmenes de la historia, (b) calendario de T = t0 + h, (c) h / horizonte_máximo."""
        resumenes = self._resumenes_historia(v, t0, h)
        cal = self._variables_calendario(ruta, t0, h)
        return np.column_stack([resumenes, cal, h / self.hmax])

    def _resumenes_historia(self, v: np.ndarray, t0: np.ndarray, h: np.ndarray) -> np.ndarray:
        """(a) Medias de log1p de los últimos `vc` y `vl` días hasta t0 y del mismo día de la semana de T en las últimas
        `sem` semanas con fecha <= t0. Columnas: m_corta, m_larga, m_dia."""
        lz = pd.Series(np.log1p(v))
        m_corta = lz.rolling(self.vc, min_periods=1).mean().to_numpy()[t0]
        m_larga = lz.rolling(self.vl, min_periods=1).mean().to_numpy()[t0]
        k = -(-h // DIAS_SEMANA)
        idx = (t0 + h - DIAS_SEMANA * k)[:, None] - DIAS_SEMANA * np.arange(self.sem)[None, :]
        lv = np.log1p(v)
        g = np.where(idx >= 0, lv[np.clip(idx, 0, len(v) - 1)], np.nan)
        return np.column_stack([m_corta, m_larga, _nanmean(g)])

    def _variables_calendario(self, ruta: str, t0: np.ndarray, h: np.ndarray) -> np.ndarray:
        """(b) Dummies de día de la semana de T (lunes = referencia) y las columnas de `_cols_calendario`. Regla 0.9: la
        vacación de T vale 0 si el origen (inicio + t0 días) es anterior a su `conocible_desde` (ver docstring del módulo)."""
        fechas = self.inicio + pd.to_timedelta(t0 + h, unit="D")
        dow = np.asarray(fechas.day_of_week)
        dummies = np.stack([(dow == d).astype(float) for d in range(1, DIAS_SEMANA)], axis=1)
        if not fechas.isin(self._cal.index).all():
            raise ValueError("El calendario no cubre las fechas objetivo")
        cal = self._cal.reindex(fechas)
        cols = self._cols_calendario(ruta)
        cals = np.stack([cal[c].to_numpy(dtype=float, na_value=np.nan) for c in cols], axis=1)
        vac = PREFIJO_VACACIONES + ruta.split("-")[0]
        if vac in cols and vac + SUFIJO_CONOCIBLE in cal.columns:
            origen = (self.inicio + pd.to_timedelta(t0, unit="D")).to_numpy()
            aun_no_conocible = cal[vac + SUFIJO_CONOCIBLE].to_numpy() > origen  # NaT -> False: no se anula
            cals[aun_no_conocible, cols.index(vac)] = 0.0
        return np.column_stack([dummies, cals])

    # --- ajuste --------------------------------------------------------------------------------------------------
    def ajustar(self, serie: pd.DataFrame, calendario: pd.DataFrame) -> None:
        self._leer(serie, calendario)
        self._ajustado = True
        self._modelo, self._res, self._media = {}, {}, {}
        t0g, hg = np.meshgrid(np.arange(self.ventana - 1, self._n_fin), np.arange(1, self.hmax + 1), indexing="ij")
        t0g, hg = t0g.ravel(), hg.ravel()
        ok = t0g + hg <= self._n_fin
        t0g, hg = t0g[ok], hg[ok]
        tr = self._tramo(hg)
        for r, v in self._v.items():
            vt = v[: self._n_fin + 1]  # parámetros solo con fechas <= fin_entrenamiento
            X = self._matriz(r, vt, t0g, hg)
            z = np.log1p(vt[t0g + hg])
            # Solo se ajusta con filas completas: un NaN (día sin_registro, nulo del calendario) no es un valor que explicar.
            val = np.isfinite(X).all(axis=1) & np.isfinite(z)
            if val.sum() == 0:
                raise ValueError(f"Sin filas de entrenamiento para {r}")
            m = Ridge(alpha=self.alpha).fit(X[val], z[val])
            res = z[val] - m.predict(X[val])
            self._modelo[r] = m
            self._media[r] = float(np.nanmean(np.log1p(vt)))
            self._res[r] = []
            for i in range(len(self.tramos)):
                x = np.sort(res[tr[val] == i])
                if len(x) == 0:
                    raise ValueError(f"Sin residuos de train para {r}, tramo {self.tramos[i]}")
                self._res[r].append(x)

    def parametros(self):
        out = {}
        for r, m in self._modelo.items():
            out[r] = {"coef": np.asarray(m.coef_), "intercepto": np.atleast_1d(m.intercept_)}
            out[r].update({f"residuos_tramo{i}": x for i, x in enumerate(self._res[r])})
        return out

    def n_parametros(self) -> int:
        return int(sum(len(m.coef_) + 1 for m in self._modelo.values()))

    def _pronosticar_ruta(self, ruta, origen, horizonte, cuantiles):
        t0 = self._t0(origen, len(self._v[ruta]), minimo=self.ventana - 1)
        vv = self._v[ruta][: t0 + 1]  # solo fechas <= origen
        h = np.arange(1, horizonte + 1)
        X = self._matriz(ruta, vv, np.full(h.shape, t0), h)
        # nulos al pronosticar: medias sin dato -> media de train de la ruta; calendario nulo -> 0 (sin receso)
        X[:, :3] = np.where(np.isnan(X[:, :3]), self._media[ruta], X[:, :3])
        X = np.nan_to_num(X, nan=0.0)
        zhat = self._modelo[ruta].predict(X)
        tr = self._tramo(h)
        vals = [np.maximum(np.expm1(zhat + _cuantiles_desplazados(self._res[ruta], tr, q)), 0.0) for q in cuantiles]
        punto = np.maximum(np.expm1(zhat), 0.0)
        return self._salida(ruta, self.inicio + pd.Timedelta(days=t0), h, punto, vals, cuantiles)


# ================================================================================================= rejilla y main

def rejilla_origenes(ultimo, n: int, paso: int, fin_entrenamiento) -> list[date]:
    """Orígenes anclados al final (§5.3 regla 4): `ultimo` y los demás cada `paso` días hacia atrás, en orden ascendente.
    Las fechas se manejan como `Timestamp`; solo la salida (el protocolo `Pronosticador` recibe `date`) es `date`."""
    u, fin = _ts(ultimo), _ts(fin_entrenamiento)
    orig = [u - pd.Timedelta(days=int(paso) * i) for i in range(int(n))][::-1]
    if orig[0] < fin:
        raise ValueError(f"El origen {orig[0].date()} queda antes de fin_entrenamiento ({fin.date()}): "
                         "reduce n_origenes o paso_dias")
    return [o.date() for o in orig]


def construir_modelos(cfg: dict) -> list:
    d = cfg["datos"]
    base = dict(inicio=d["inicio_entrenamiento"], fin=d["fin_entrenamiento"], tramos=cfg["horizontes"]["tramos"])
    fabrica = {
        "ingenuo_estacional": lambda: IngenuoEstacional(
            **base, max_semanas_retroceso=cfg["ingenuo_estacional"]["max_semanas_retroceso"]),
        "regresion_calendario": lambda: RegresionCalendario(
            **base, alpha=cfg["regresion_calendario"]["alpha"], ventana_corta=cfg["regresion_calendario"]["ventana_corta"],
            ventana_larga=cfg["regresion_calendario"]["ventana_larga"],
            semanas_mismo_dia=cfg["regresion_calendario"]["semanas_mismo_dia"]),
    }
    desconocidos = [m for m in cfg["modelos"] if m not in fabrica]
    if desconocidos:
        raise ValueError(f"Modelos desconocidos: {desconocidos}; disponibles: {sorted(fabrica)}")
    return [fabrica[m]() for m in cfg["modelos"]]


def _sha256(ruta: Path) -> str:
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def sha256_particion(inicio, fin, origenes) -> str:
    """SHA-256 de la partición (§6): JSON ordenado y compacto de `inicio_entrenamiento`, `fin_entrenamiento` y la rejilla de
    orígenes (fechas ISO)."""
    cuerpo = json.dumps({"inicio_entrenamiento": str(_ts(inicio).date()), "fin_entrenamiento": str(_ts(fin).date()),
                         "origenes": [str(_ts(o).date()) for o in origenes]}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()


def _imprimir_config(cfg: dict) -> None:
    print(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True, explicit_start=True, explicit_end=True), end="")


def main(cfg: dict) -> int:
    """Ajusta los modelos con train, pronostica la rejilla de orígenes y escribe `pred_test_*.parquet` y el presupuesto."""
    _imprimir_config(cfg)
    d, rej = cfg["datos"], cfg["rejilla"]
    serie = pd.read_parquet(d["diaria"])
    cal = pd.read_parquet(d["calendario"])
    origenes = rejilla_origenes(rej["ultimo_origen"], rej["n_origenes"], rej["paso_dias"], d["fin_entrenamiento"])
    horizonte, cuantiles = int(rej["horizonte"]), [float(q) for q in rej["cuantiles"]]
    obs = serie[["ruta_id", "fecha", "pasajeros"]].assign(fecha=lambda x: pd.to_datetime(x["fecha"]).dt.normalize())
    evidencia = {"demanda_diaria_sha256": _sha256(d["diaria"]), "calendario_sha256": _sha256(d["calendario"]),
                 "particion_sha256": sha256_particion(d["inicio_entrenamiento"], d["fin_entrenamiento"], origenes)}
    carpeta, carpeta_ref = Path(cfg["salida"]["carpeta"]), Path(cfg["salida"]["carpeta_referencia"])
    carpeta.mkdir(parents=True, exist_ok=True)
    carpeta_ref.mkdir(parents=True, exist_ok=True)
    presupuesto: dict = {}
    for m in construir_modelos(cfg):
        t = time.perf_counter()
        m.ajustar(serie, cal)
        partes = []
        for o in origenes:
            p = m.pronosticar(o, horizonte, cuantiles)
            partes.append(p.assign(origen=o))
        df = pd.concat(partes, ignore_index=True)
        df = df.merge(obs.rename(columns={"pasajeros": "y"}).assign(fecha=lambda x: x["fecha"].dt.date),
                      on=["ruta_id", "fecha"], how="left")
        if df["y"].isna().any():
            raise ValueError("Hay fechas objetivo sin observación en la serie (rejilla fuera de la serie)")
        df["y"] = df["y"].astype(int)
        df = df[COLUMNAS_PRED + [nombre_cuantil(q) for q in cuantiles]]
        df.to_parquet(carpeta / f"pred_test_{m.nombre}.parquet", index=False)
        presupuesto[m.nombre] = {
            "n_parametros": m.n_parametros(),
            "n_configuraciones_busqueda": m.n_configuraciones_busqueda(),
            "tiempo_total_s": round(time.perf_counter() - t, 3),
            "device": DEVICE,
            "evidencia": evidencia,
            "n_origenes": len(origenes),
        }
        print(f"{m.nombre}: {len(df)} filas, n_parametros={m.n_parametros()}, "
              f"{presupuesto[m.nombre]['tiempo_total_s']} s")
    save_json(carpeta_ref / "presupuesto.json", {
        "modelos": presupuesto,
        "origenes": [str(o) for o in origenes],
        "ventana_train": [str(_ts(d["inicio_entrenamiento"]).date()), str(_ts(d["fin_entrenamiento"]).date())],
        "nota": "n_parametros del ingenuo = 0 (cuantiles = valores empíricos, no parámetros); regresión = coeficientes + "
                "intercepto por ruta. Sin búsqueda de hiperparámetros (alpha fijo en config).",
    })
    return 0


def _cli(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M1: modelos de referencia (CA-5)")
    ap.add_argument("--config", required=True)
    ap.add_argument("--set", dest="overrides", action="append", default=[], metavar="CLAVE.SUBCLAVE=VALOR")
    a = ap.parse_args(argv)
    return main(apply_overrides(load_config(a.config), a.overrides))


if __name__ == "__main__":
    raise SystemExit(_cli())
