"""Auditoría adversarial de fuga de la partición de M2 (JO-3, auditor-fugas, 28-nov).

Complementa ``tests/test_fuga_m2.py`` sin modificarlo. Cada prueba documenta un camino de fuga revisado:

  A1 completitud del criterio coseno en los datos reales: la CI solo recalcula el pHash; aquí se recalcula el coseno de TODAS
     las parejas con la caché de características (se omite si la caché no existe, p. ej. en la CI).
  A2 ráfagas casi iguales entre splits: ``origen.csv`` conserva el nombre original de 404 fotos con marca de tiempo de la
     cámara (``IMG_AAAAMMDD_HHMMSSmmm``); la ampliación de D9 agrega 183 PNG ``AAAA-MM-DDhh-mm-ss`` y 11
     ``photo_AAAA-MM-DD_hh-mm-ss`` (598 en total). Fotos tomadas con pocos segundos de diferencia son la misma escena (el mismo
     conductor, casi la misma pose). Antes de D9 había 9 pares a < 3 s en splits distintos (marcada xfail strict); con la
     arista por marca de tiempo (D9, ``tiempo.umbral_segundos`` = 10 en la config) la prueba pasa y se extendió a ≤ 10 s.
  A3 caché obsoleta: antes ``cache_valida`` no comparaba la normalización (``media``/``desviacion``) ni la red; corregido en
     la 4.ª vuelta de JO-3 (ya no es xfail).
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from src.m2_conduccion import duplicados, particion

RAIZ = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load((RAIZ / "configs" / "m2" / "particion.yaml").read_text(encoding="utf-8"))
PROC = RAIZ / "data" / "processed" / "m2"
INDICE = PROC / "indice.csv"
ORIGEN = PROC / "origen.csv"
PARES = RAIZ / "results" / "data" / "m2" / "particion" / "pares_cercanos.csv"
CACHE = RAIZ / CFG["caracteristicas"]["cache"]
SEGUNDOS_RAFAGA = float(CFG["tiempo"]["umbral_segundos"])   # D9: 10 s (antes de D9 esta prueba usaba 3 s)
PATRON_MARCA = re.compile(r"IMG_(\d{8})_(\d{9})")
# Ampliación de D9 (José, 28-nov): los otros dos formatos con hora (resolución de segundos). Parseo independiente del código
# de src (expresión + formato estricto de pandas), como el de IMG_.
FORMATOS_EXTRA = [(re.compile(r"^(\d{4}-\d{2}-\d{2})(\d{2}-\d{2}-\d{2})\.[^.]+$"), "%Y-%m-%d%H-%M-%S"),
                  (re.compile(r"^photo_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})"), "%Y-%m-%d%H-%M-%S")]


def _leer(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(ruta, dtype=str, keep_default_na=False)


# --------------------------------------------------------------------------- A1
@pytest.mark.skipif(not (CACHE.is_file() and INDICE.is_file() and PARES.is_file()),
                    reason="sin caché de características (no versionada) o sin resultados reales")
def test_auditoria_real_coseno_recalculado_completo_y_sin_cruces():
    """Todas las parejas con cos ≥ τ_c (recalculado desde la caché) están en pares_cercanos.csv y ninguna cruza splits."""
    d = _leer(INDICE)
    c = duplicados.leer_cache(CACHE)
    huella = duplicados.huella_imagenes(PROC, d["archivo"].tolist())
    car = CFG["caracteristicas"]
    assert duplicados.cache_valida(CACHE, d["id"].tolist(), car["sha256_pesos"], huella, red=car["red"], media=car["media"],
                                   desviacion=car["desviacion"])
    zn = duplicados.normalizar_filas(c["caracteristicas"])
    tau = float(CFG["grafo"]["umbral_coseno"])
    ids, split = d["id"].to_numpy(), d["split"].to_numpy()
    recalculados, cruces = set(), 0
    n = len(d)
    for ini in range(0, n, 1024):
        fin = min(n, ini + 1024)
        cos = zn[ini:fin] @ zn.T
        sup = np.arange(n)[None, :] > np.arange(ini, fin)[:, None]
        fi, j = np.nonzero((cos >= tau + 1e-6) & sup)          # margen: el CSV redondea a 6 decimales
        recalculados |= {(ids[ini + a], ids[b]) for a, b in zip(fi, j)}
        fi, j = np.nonzero((cos >= tau) & sup)
        cruces += int((split[ini + fi] != split[j]).sum())
    p = _leer(PARES)
    versionados = set(zip(p.loc[p["criterio"].isin(["coseno", "ambos"]), "id_a"],
                          p.loc[p["criterio"].isin(["coseno", "ambos"]), "id_b"]))
    assert recalculados <= versionados
    assert cruces == 0


# --------------------------------------------------------------------------- A2
def _fotos_con_marca() -> pd.DataFrame:
    o = _leer(ORIGEN).merge(_leer(INDICE)[["id", "split", "clase", "grupo_duplicado"]], on="id")
    nombre = o["archivo_original"].str.split("/").str[-1]
    m = nombre.str.extract(PATRON_MARCA)
    o["t"] = pd.to_datetime(m[0] + m[1], format="%Y%m%d%H%M%S%f", errors="coerce")
    for patron, formato in FORMATOS_EXTRA:
        m = nombre.str.extract(patron)
        o["t"] = o["t"].fillna(pd.to_datetime(m[0] + m[1], format=formato, errors="coerce"))
    return o[o["t"].notna()].sort_values("t").reset_index(drop=True)


def _rafagas_que_cruzan(fotos: pd.DataFrame, segundos: float) -> pd.DataFrame:
    seg = (fotos["t"] - fotos["t"].min()).dt.total_seconds().to_numpy()
    filas = []
    for a in range(len(fotos)):
        for b in range(a + 1, len(fotos)):
            if seg[b] - seg[a] > segundos:
                break
            if fotos.at[a, "split"] != fotos.at[b, "split"]:
                filas.append({"id_a": fotos.at[a, "id"], "id_b": fotos.at[b, "id"], "segundos": seg[b] - seg[a],
                              "split_a": fotos.at[a, "split"], "split_b": fotos.at[b, "split"]})
    return pd.DataFrame(filas)


@pytest.mark.skipif(not (ORIGEN.is_file() and INDICE.is_file()), reason="faltan origen.csv o indice.csv")
def test_auditoria_marcas_de_tiempo_existen_y_son_rafagas():
    """La evidencia de A2 es real: 598 fotos con marca de tiempo (404 IMG_ + 183 PNG + 11 photo_) y la mediana entre fotos
    consecutivas es de segundos."""
    f = _fotos_con_marca()
    assert len(f) == 598
    assert float(f["t"].diff().dt.total_seconds().median()) < 10.0


@pytest.mark.skipif(not (ORIGEN.is_file() and INDICE.is_file()), reason="faltan origen.csv o indice.csv")
def test_auditoria_ninguna_rafaga_de_hasta_10_s_cruza_splits():
    cruzan = _rafagas_que_cruzan(_fotos_con_marca(), SEGUNDOS_RAFAGA)
    assert len(cruzan) == 0, cruzan.to_string()


# --------------------------------------------------------------------------- A3
def test_auditoria_cache_se_invalida_si_cambia_la_normalizacion(tmp_path):
    """Caché guardada con la red y la normalización de la config: con esos valores SÍ se usa (no hacen falta los pesos);
    cambiando solo ``media``, la caché deja de valer y se intenta cargar la red (FileNotFoundError: pesos ausentes)."""
    ids = ["a", "b"]
    ruta = tmp_path / "cache.npz"
    car = CFG["caracteristicas"]
    duplicados.guardar_cache(ruta, ids, np.ones((2, 4), dtype=np.float32), "sha", "huella", red=car["red"],
                             media=car["media"], desviacion=car["desviacion"])
    cfg = {"caracteristicas": {"red": car["red"], "cache": str(ruta), "sha256_pesos": "sha",
                               "pesos": str(tmp_path / "no_existe.pth"), "media": list(car["media"]),
                               "desviacion": list(car["desviacion"]), "lote": 2, "dispositivo": "cpu"}}
    indice = pd.DataFrame({"id": ids, "archivo": ["a.jpg", "b.jpg"]})
    z, desde_cache, _ = particion._caracteristicas(cfg, tmp_path, indice, "huella")
    assert desde_cache and z.shape == (2, 4)
    cfg["caracteristicas"]["media"] = [0.0, 0.0, 0.0]
    with pytest.raises(FileNotFoundError):
        particion._caracteristicas(cfg, tmp_path, indice, "huella")
