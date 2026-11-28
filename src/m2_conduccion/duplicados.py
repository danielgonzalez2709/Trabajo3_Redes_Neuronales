"""M2 — casi duplicados (JO-3; docs/spec/partes/jose.md §3.2, D1–D3): hashes perceptuales, características congeladas, grafo y
grupos. Funciones puras; todo parámetro llega por argumento (desde ``configs/m2/particion.yaml``).

Formulación implementada (se explica en vivo):

  D1 · pHash de 64 bits (imagehash.phash, tam_hash = 8, factor_alta_frecuencia = 4):
        x → gris → 32x32 (Lanczos) → C = DCT-II(DCT-II(x, eje 0), eje 1) → B = C[0:8, 0:8] → h(x)_k = [B_k > mediana(B)]
      Distancia entre dos imágenes a y b, con f = espejo horizontal:
        d_H(a, b) = mín( H(h(a), h(b)),  H(h(a), h(f(b))),  H(h(f(a)), h(b)) ),   H(u, v) = Σ_k [u_k ≠ v_k] = popcount(u XOR v)
      El tercer término hace d_H simétrica: el espejo invierte el signo de las columnas impares de C y cambia la mediana, así
      que h(f(b)) no es una permutación de los bits de h(b) y H(a, f(b)) ≠ H(f(a), b) en general.
  D2 · z(x) ∈ R^512 = GAP(layer4(ResNet-18 ImageNet congelada)((x/255 − μ)/σ)),  μ, σ de ImageNet (config)
        cos(a, b) = z_a·z_b / (‖z_a‖ ‖z_b‖)   (z ≥ 0 tras la ReLU, así que cos ∈ [0, 1])
      La entrada es la imagen 224x224 versionada tal cual (sin el «resize 256 + recorte 224» de torchvision: ya está estirada a
      224x224 como en la app).
  D9 · t(x) = marca de tiempo en milisegundos (entero), leída del nombre original con el primer formato de la config que
      coincide: IMG_AAAAMMDD_HHMMSSmmm (ms), AAAA-MM-DDhh-mm-ss.png y photo_AAAA-MM-DD_hh-mm-ss (segundos, ms = 0);
      indefinida si ningún formato coincide o la fecha es imposible. Formatos distintos se comparan en la misma escala.
        arista_t(a, b) ⇔ t(a), t(b) definidas  ∧  |t(a) − t(b)| ≤ 1000 · umbral_segundos   (en ms enteros: sin error de redondeo)
  D3 · arista(a, b) ⇔ d_H(a, b) ≤ τ_H  ∨  cos(a, b) ≥ τ_c  ∨  arista_t(a, b);   grupo = componente conexa (union-find).
      Guarda: si la componente más grande supera fraccion_maxima · N, se detiene sin escribir nada.

Fuga: el grafo NO usa la clase ni el split (la marca de tiempo es un metadato del archivo, no la etiqueta); ninguna transformación se ajusta con los datos (pHash es fijo y la red está
congelada con pesos de ImageNet), así que agrupar con todas las imágenes no filtra información de prueba hacia train.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import imagehash
import numpy as np
from PIL import Image, ImageOps

from src.m2_conduccion.datos import sha256_archivo

BITS = 64
BINS_COSENO = 100                 # histograma del coseno en [0, 1]: bins de 0,01


class GrupoDemasiadoGrande(ValueError):
    """La componente conexa más grande supera la fracción máxima de la config (D3): no se escribe la partición."""


@dataclass(frozen=True)
class Par:
    """Par (i < j) con su distancia de Hamming con espejo, su coseno, la diferencia de marca de tiempo (segundos; None si
    alguna foto no tiene marca) y si cumple cada criterio de arista."""
    i: int
    j: int
    hamming: int
    coseno: float
    por_hamming: bool
    por_coseno: bool
    por_tiempo: bool = False
    segundos: float | None = None

    @property
    def arista(self) -> bool:
        return self.por_hamming or self.por_coseno or self.por_tiempo


# --------------------------------------------------------------------------- D1: pHash con espejo
def _phash_bits(img: Image.Image, tam_hash: int, factor_alta_frecuencia: int) -> np.ndarray:
    return imagehash.phash(img, hash_size=tam_hash, highfreq_factor=factor_alta_frecuencia).hash.flatten()


def hashes_de_imagenes(imagenes: Iterable[Image.Image], tam_hash: int, factor_alta_frecuencia: int, espejo: bool
                       ) -> tuple[np.ndarray, np.ndarray | None]:
    """(h, h_espejo): matrices booleanas (N, tam_hash²) con el pHash de cada imagen y, solo si ``espejo``, de su espejo
    horizontal (si no, ``None``)."""
    h, hf = [], []
    for img in imagenes:
        img = img.convert("RGB")
        h.append(_phash_bits(img, tam_hash, factor_alta_frecuencia))
        if espejo:
            hf.append(_phash_bits(ImageOps.mirror(img), tam_hash, factor_alta_frecuencia))
    return np.array(h, dtype=bool), (np.array(hf, dtype=bool) if espejo else None)


def hashes_de_archivos(rutas: Sequence[Path], tam_hash: int, factor_alta_frecuencia: int, espejo: bool
                       ) -> tuple[np.ndarray, np.ndarray | None]:
    """``hashes_de_imagenes`` leyendo cada archivo (se abre y se cierra uno a uno)."""
    def leer():
        for ruta in rutas:
            with Image.open(ruta) as img:
                yield img.convert("RGB")
    return hashes_de_imagenes(leer(), tam_hash, factor_alta_frecuencia, espejo)


def empaquetar(bits: np.ndarray) -> np.ndarray:
    """(N, 64) booleano → (N,) uint64 (bit k del hash = bit k del entero; el orden es irrelevante para Hamming)."""
    bits = np.asarray(bits, dtype=bool)
    if bits.ndim != 2 or bits.shape[1] != BITS:
        raise ValueError(f"se esperan hashes de {BITS} bits con forma (N, {BITS}); llegó {bits.shape}")
    pesos = np.left_shift(np.uint64(1), np.arange(BITS, dtype=np.uint64))
    return (bits.astype(np.uint64) * pesos).sum(axis=1, dtype=np.uint64)


def hamming_matriz(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """H(u, v) = popcount(u XOR v) para todo u de ``a`` y v de ``b`` (uint64 empaquetados) → (len a, len b) int."""
    return np.bitwise_count(a[:, None] ^ b[None, :]).astype(np.int64)


def distancia_hamming_espejo(ha: np.ndarray, hfa: np.ndarray | None, hb: np.ndarray, hfb: np.ndarray | None) -> np.ndarray:
    """d_H = mín(H(a, b), H(a, f(b)), H(f(a), b)); con ``hfa``/``hfb`` = None es el pHash simple H(a, b)."""
    d = hamming_matriz(ha, hb)
    if hfa is None or hfb is None:
        return d
    return np.minimum(d, np.minimum(hamming_matriz(ha, hfb), hamming_matriz(hfa, hb)))


# --------------------------------------------------------------------------- D2: coseno
def normalizar_filas(z: np.ndarray) -> np.ndarray:
    """z / ‖z‖ por fila (float64). Un vector nulo no tiene coseno definido: error."""
    z = np.asarray(z, dtype=np.float64)
    normas = np.linalg.norm(z, axis=1, keepdims=True)
    if (normas == 0).any():
        raise ValueError(f"hay {int((normas == 0).sum())} vectores de características nulos: el coseno no está definido")
    return z / normas


def coseno_matriz(an: np.ndarray, bn: np.ndarray) -> np.ndarray:
    """cos(a, b) = â·b̂ con filas ya normalizadas."""
    return an @ bn.T


# --------------------------------------------------------------------------- D3: pares, grafo y grupos
def _bloques(n: int, bloque: int):
    if bloque < 1:
        raise ValueError(f"bloque debe ser >= 1 (recibido {bloque})")
    for ini in range(0, n, bloque):
        yield ini, min(n, ini + bloque)


def pares_cercanos(h: np.ndarray, hf: np.ndarray | None, zn: np.ndarray, umbral_hamming: int, umbral_coseno: float,
                   bloque: int, margen_hamming: int = 0, margen_coseno: float = 0.0) -> list[Par]:
    """Todos los pares i < j con d_H ≤ τ_H + margen_hamming o cos ≥ τ_c − margen_coseno, recorriendo por bloques de filas.

    Los indicadores ``por_hamming`` / ``por_coseno`` usan los umbrales estrictos (sin margen). El margen sirve para el barrido
    de umbrales candidatos de ``resumen.json`` y para ver los pares justo fuera de la frontera (figura). El criterio de tiempo
    se agrega aparte (``unir_pares_por_tiempo``).
    """
    n = len(h)
    if len(zn) != n or (hf is not None and len(hf) != n):
        raise ValueError("hashes y características deben tener el mismo número de filas")
    pares: list[Par] = []
    for ini, fin in _bloques(n, bloque):
        hf_blq = None if hf is None else hf[ini:fin]
        d = distancia_hamming_espejo(h[ini:fin], hf_blq, h, hf)
        c = coseno_matriz(zn[ini:fin], zn)
        filas = np.arange(ini, fin)[:, None]
        cerca = ((d <= umbral_hamming + margen_hamming) | (c >= umbral_coseno - margen_coseno)) & (np.arange(n)[None, :] > filas)
        for fi, j in zip(*np.nonzero(cerca)):
            dij, cij = int(d[fi, j]), float(c[fi, j])
            pares.append(Par(int(ini + fi), int(j), dij, cij, dij <= umbral_hamming, cij >= umbral_coseno))
    return pares


def estadisticas_vecinos(h: np.ndarray, hf: np.ndarray | None, zn: np.ndarray, bloque: int) -> dict:
    """Distribuciones para elegir umbrales: por imagen, d_H al vecino más cercano y coseno máximo con otra imagen; sobre
    todos los pares i < j, histograma de d_H (0..64) y del coseno (``BINS_COSENO`` bins iguales en [0, 1])."""
    n = len(h)
    nn_h = np.full(n, BITS + 1, dtype=np.int64)
    nn_c = np.full(n, -np.inf)
    hist_h = np.zeros(BITS + 1, dtype=np.int64)
    bordes_c = np.linspace(0.0, 1.0, BINS_COSENO + 1)
    hist_c = np.zeros(BINS_COSENO, dtype=np.int64)
    for ini, fin in _bloques(n, bloque):
        d = distancia_hamming_espejo(h[ini:fin], None if hf is None else hf[ini:fin], h, hf)
        c = coseno_matriz(zn[ini:fin], zn)
        filas = np.arange(ini, fin)
        sup = np.arange(n)[None, :] > filas[:, None]
        hist_h += np.bincount(d[sup], minlength=BITS + 1)
        hist_c += np.histogram(np.clip(c[sup], 0.0, 1.0), bins=bordes_c)[0]
        d[np.arange(fin - ini), filas] = BITS + 1          # sin la propia imagen
        c[np.arange(fin - ini), filas] = -np.inf
        nn_h[ini:fin] = d.min(axis=1)
        nn_c[ini:fin] = c.max(axis=1)
    return {"nn_hamming": nn_h, "nn_coseno": nn_c, "hist_hamming": hist_h, "hist_coseno": hist_c,
            "bordes_coseno": bordes_c}


def marca_de_tiempo(nombre: str, patron: str) -> int | None:
    """D9: milisegundos desde 1970 de la marca en el nombre base ``nombre``. ``patron`` tiene grupos de ancho fijo: año, mes,
    día, hora, minuto, segundo y, opcionalmente, milisegundos (6 o 7 grupos; con 6, ms = 0). None si no coincide o la
    fecha/hora es imposible (no se usa ``strptime``, que acepta campos de ancho variable).

    Escala: el reloj de pared del nombre leído como UTC nominal (sin zona: solo sirve para restar). Dos marcas de formatos
    distintos están en la misma escala de unidades, pero NO se sabe si sus cámaras comparten reloj o zona; se comparan igual
    (unir de más solo agranda grupos). Con resolución de segundos la marca es el segundo registrado: la diferencia real entre
    dos fotos puede ser hasta 1 s mayor o menor que la registrada; la regla se aplica a lo registrado."""
    m = re.match(patron, Path(nombre).name)
    if m is None:
        return None
    partes = [int(g) for g in m.groups()]
    if len(partes) not in (6, 7):
        raise ValueError(f"el patrón {patron!r} debe tener 6 o 7 grupos (fecha, hora y milisegundos opcionales)")
    anio, mes, dia, hora, minuto, segundo = partes[:6]
    ms = partes[6] if len(partes) == 7 else 0
    try:
        t = dt.datetime(anio, mes, dia, hora, minuto, segundo, ms * 1000, tzinfo=dt.timezone.utc)
    except ValueError:
        return None
    return int(round(t.timestamp() * 1000))


def marca_y_formato(nombre: str, formatos: Sequence[tuple[str, str]]) -> tuple[str, int] | None:
    """(nombre del formato, ms) con el primer formato de ``formatos`` = [(nombre, patrón)] que da una marca; si no, None."""
    for etiqueta, patron in formatos:
        t = marca_de_tiempo(nombre, patron)
        if t is not None:
            return etiqueta, t
    return None


def dentro_del_umbral(diferencia_ms: int, umbral_segundos: float) -> bool:
    """Única regla «dentro del umbral de tiempo» (D9): |Δt| ≤ umbral, inclusivo, en milisegundos enteros."""
    return abs(int(diferencia_ms)) <= int(round(umbral_segundos * 1000))


def pares_por_tiempo(marcas: Sequence[int | None], umbral_segundos: float) -> list[tuple[int, int, float]]:
    """Pares i < j con ambas marcas definidas y |t_i − t_j| ≤ umbral (ms enteros), por barrido sobre las marcas ordenadas.
    Devuelve (i, j, segundos) ordenados por (i, j)."""
    con = sorted((t, k) for k, t in enumerate(marcas) if t is not None)
    pares = []
    for a in range(len(con)):
        for b in range(a + 1, len(con)):
            dif = con[b][0] - con[a][0]
            if not dentro_del_umbral(dif, umbral_segundos):
                break
            i, j = sorted((con[a][1], con[b][1]))
            pares.append((i, j, dif / 1000))
    return sorted(pares)


def unir_pares_por_tiempo(pares: list[Par], marcas: Sequence[int | None], umbral_segundos: float, h: np.ndarray,
                          hf: np.ndarray | None, zn: np.ndarray, umbral_hamming: int, umbral_coseno: float) -> list[Par]:
    """Agrega el criterio de tiempo (D9): marca ``por_tiempo`` en los pares ya listados y añade los que solo cumple el tiempo
    (con su d_H y coseno calculados). Todo par listado con ambas marcas lleva ``segundos``."""
    def dif_ms(i, j):
        return None if marcas[i] is None or marcas[j] is None else abs(marcas[i] - marcas[j])

    def seg(i, j):
        d = dif_ms(i, j)
        return None if d is None else d / 1000

    def con_tiempo(p: Par) -> Par:
        d = dif_ms(p.i, p.j)
        return Par(p.i, p.j, p.hamming, p.coseno, p.por_hamming, p.por_coseno,
                   d is not None and dentro_del_umbral(d, umbral_segundos), seg(p.i, p.j))

    por_clave = {(p.i, p.j): con_tiempo(p) for p in pares}
    for i, j, _ in pares_por_tiempo(marcas, umbral_segundos):
        if (i, j) not in por_clave:
            d = int(distancia_hamming_espejo(h[[i]], None if hf is None else hf[[i]], h[[j]],
                                             None if hf is None else hf[[j]])[0, 0])
            c = float(zn[i] @ zn[j])
            por_clave[(i, j)] = Par(i, j, d, c, d <= umbral_hamming, c >= umbral_coseno, True, seg(i, j))
    return [por_clave[k] for k in sorted(por_clave)]


def componentes(n: int, pares: Iterable[tuple[int, int]]) -> np.ndarray:
    """Componentes conexas por union-find (reducción a la mitad del camino, «path halving»); etiqueta = menor índice."""
    padre = list(range(n))

    def raiz(x: int) -> int:
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    for i, j in pares:
        ri, rj = raiz(int(i)), raiz(int(j))
        if ri != rj:
            padre[max(ri, rj)] = min(ri, rj)            # la raíz es siempre el menor índice
    return np.array([raiz(x) for x in range(n)], dtype=np.int64)


def nombrar_grupos(ids: Sequence[str], etiquetas: np.ndarray) -> list[str]:
    """``g_00001``, ``g_00002``… numerados por la primera aparición en el orden de ``ids`` (el de indice.csv)."""
    nombres: dict[int, str] = {}
    for e in etiquetas:
        nombres.setdefault(int(e), f"g_{len(nombres) + 1:05d}")
    return [nombres[int(e)] for e in etiquetas]


def verificar_tamano_maximo(etiquetas: np.ndarray, fraccion_maxima: float) -> None:
    """D3: falla si la componente más grande tiene más de ``fraccion_maxima`` de las imágenes."""
    _, tam = np.unique(etiquetas, return_counts=True)
    n, mayor = len(etiquetas), int(tam.max())
    if mayor > fraccion_maxima * n:
        raise GrupoDemasiadoGrande(
            f"La componente más grande tiene {mayor} de {n} imágenes ({100 * mayor / n:.1f} %), más que el máximo de "
            f"{100 * fraccion_maxima:g} % (grafo.fraccion_maxima_grupo). No se escribe la partición: revisar los umbrales "
            f"con José (D3).")


# --------------------------------------------------------------------------- D2: red congelada y caché
def huella_imagenes(carpeta: Path, archivos: Sequence[str]) -> str:
    """SHA-256 de la concatenación de los bytes de cada imagen en el orden dado (misma definición que ``procesado.json``)."""
    h = hashlib.sha256()
    for a in archivos:
        h.update((Path(carpeta) / a).read_bytes())
    return h.hexdigest()


def cargar_resnet18(ruta_pesos: Path, sha256_esperado: str):
    """ResNet-18 con los pesos ImageNet del ARCHIVO LOCAL (nunca de internet), ``fc`` = identidad → salida = GAP de layer4
    (512); ``eval()`` y sin gradientes. Falla si el archivo no existe o su SHA-256 no es el de la config."""
    import torch
    import torchvision

    ruta = Path(ruta_pesos)
    if not ruta.is_file():
        raise FileNotFoundError(f"Faltan los pesos {ruta}. Bájalos una vez con: .venv/bin/python scripts/descargar_pesos_m2.py")
    medido = sha256_archivo(ruta)
    if medido != sha256_esperado:
        raise ValueError(f"El SHA-256 de {ruta.name} es {medido} y la config espera {sha256_esperado}")
    modelo = torchvision.models.resnet18(weights=None)
    modelo.load_state_dict(torch.load(ruta, map_location="cpu", weights_only=True))
    modelo.fc = torch.nn.Identity()            # forward: ... layer4 → AdaptiveAvgPool2d(1) (GAP) → flatten → identidad
    modelo.eval()
    for p in modelo.parameters():
        p.requires_grad_(False)
    return modelo


def caracteristicas(rutas: Sequence[Path], modelo, media: Sequence[float], desviacion: Sequence[float], lote: int,
                    dispositivo: str) -> np.ndarray:
    """z = modelo((x/255 − μ)/σ) por lotes, sin gradientes; x en RGB sin redimensionar. Devuelve (N, D) float32."""
    import torch

    if lote < 1:
        raise ValueError(f"lote debe ser >= 1 (recibido {lote})")
    mu = torch.tensor(media, dtype=torch.float32).view(1, 3, 1, 1)
    sd = torch.tensor(desviacion, dtype=torch.float32).view(1, 3, 1, 1)
    modelo = modelo.to(dispositivo).eval()
    salida = []
    with torch.no_grad():
        for ini in range(0, len(rutas), lote):
            imgs = []
            for ruta in rutas[ini:ini + lote]:
                with Image.open(ruta) as img:
                    imgs.append(np.asarray(img.convert("RGB"), dtype=np.float32))
            x = torch.from_numpy(np.stack(imgs)).permute(0, 3, 1, 2) / 255.0
            x = ((x - mu) / sd).to(dispositivo)
            salida.append(modelo(x).detach().cpu().numpy().astype(np.float32))
    return np.concatenate(salida, axis=0)


def guardar_cache(ruta: Path, ids: Sequence[str], z: np.ndarray, sha256_pesos: str, huella_imagenes: str, *,
                  red: str | None = None, media: Sequence[float] | None = None,
                  desviacion: Sequence[float] | None = None) -> None:
    """Caché no versionada (``.npz`` con ids, características, huellas, red y normalización). Deja un ``.gitignore`` con
    ``*`` en la carpeta. Sin red/media/desviación, la caché no vale para ninguna config (``cache_valida``)."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ignorar = ruta.parent / ".gitignore"
    if not ignorar.exists():
        ignorar.write_text("# caché de características de M2 (JO-3/JO-4): se regenera, no se versiona\n*\n", encoding="utf-8")
    np.savez(ruta, ids=np.array(ids, dtype=str), caracteristicas=np.asarray(z, dtype=np.float32),
             sha256_pesos=np.array(sha256_pesos), huella_imagenes=np.array(huella_imagenes), red=np.array(red or ""),
             media=np.array(media if media is not None else [], dtype=np.float64),
             desviacion=np.array(desviacion if desviacion is not None else [], dtype=np.float64))


def leer_cache(ruta: Path) -> dict:
    """Contenido de la caché; ``red``/``media``/``desviacion`` son None si la caché es de antes de guardarlos."""
    with np.load(ruta, allow_pickle=False) as d:
        claves = set(d.files)
        return {"ids": d["ids"].tolist(), "caracteristicas": d["caracteristicas"],
                "sha256_pesos": str(d["sha256_pesos"]), "huella_imagenes": str(d["huella_imagenes"]),
                "red": str(d["red"]) if "red" in claves else None,
                "media": d["media"].tolist() if "media" in claves else None,
                "desviacion": d["desviacion"].tolist() if "desviacion" in claves else None}


def cache_valida(ruta: Path, ids: Sequence[str], sha256_pesos: str, huella: str, *, red: str,
                 media: Sequence[float], desviacion: Sequence[float]) -> bool:
    """La caché vale si existe y coincide en ids (y su orden), SHA-256 de los pesos, huella de las imágenes, red y
    normalización (media y desviación) con que se extrajeron las características."""
    ruta = Path(ruta)
    if not ruta.is_file():
        return False
    c = leer_cache(ruta)
    return (c["ids"] == list(ids) and c["sha256_pesos"] == sha256_pesos and c["huella_imagenes"] == huella
            and c["red"] == red and c["media"] == [float(x) for x in media]
            and c["desviacion"] == [float(x) for x in desviacion])
