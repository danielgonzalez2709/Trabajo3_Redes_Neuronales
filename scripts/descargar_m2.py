"""Descarga de los datos de M2 desde Mendeley Data (único código con red de M2; los experimentos no usan internet).

Conjunto: «Multi-Class Driver Behavior Image Dataset» (DOI 10.17632/mzb4b6dff3.1, versión 1).
Consulta la API pública, descarga el .zip a data/raw/m2/ en streaming y verifica tamaño y SHA-256 contra los de la API.
No extrae el .zip. Si el archivo ya existe con el SHA-256 correcto, no lo vuelve a bajar.

Uso: .venv/bin/python scripts/descargar_m2.py [--timeout 120] [--reintentos 3]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
ID_CONJUNTO = "mzb4b6dff3"
VERSION = 1
URL_API = f"https://data.mendeley.com/public-api/datasets/{ID_CONJUNTO}/files?folder_id=root&version={VERSION}"
URL_DOI = "https://doi.org/10.17632/mzb4b6dff3.1"
NOMBRE_ZIP = "Multi-Class Driver Behavior Image Dataset.zip"
RAW = RAIZ / "data" / "raw" / "m2"
BLOQUE = 1024 * 1024


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(BLOQUE), b""):
            h.update(bloque)
    return h.hexdigest()


def consultar_archivo(timeout: float, reintentos: int) -> dict:
    """Metadatos del .zip según la API: nombre, tamaño, SHA-256 y URL de descarga."""
    ultimo: Exception | None = None
    for intento in range(1, reintentos + 1):
        try:
            r = requests.get(URL_API, timeout=timeout)
            r.raise_for_status()
            archivos = [a for a in r.json() if a.get("filename") == NOMBRE_ZIP]
            if len(archivos) != 1:
                raise RuntimeError(f"la API no devolvió exactamente un archivo {NOMBRE_ZIP!r} (devolvió {len(archivos)})")
            a = archivos[0]
            cd = a["content_details"]
            return {"nombre": a["filename"], "tamano": int(cd["size"]), "sha256": cd["sha256_hash"].lower(),
                    "url": cd["download_url"]}
        except (requests.RequestException, ValueError, KeyError) as e:
            ultimo = e
            if intento < reintentos:
                time.sleep(5 * intento)
    assert ultimo is not None
    raise ultimo


def descargar(meta: dict, destino: Path, timeout: float, reintentos: int) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and destino.stat().st_size == meta["tamano"] and sha256(destino) == meta["sha256"]:
        print(f"{destino.name} ya existe con el SHA-256 correcto: no se descarga")
        return destino
    tmp = destino.with_suffix(destino.suffix + ".part")
    ultimo: Exception | None = None
    for intento in range(1, reintentos + 1):
        try:
            with requests.get(meta["url"], stream=True, timeout=timeout) as r:
                r.raise_for_status()
                with open(tmp, "wb") as f:
                    for bloque in r.iter_content(BLOQUE):
                        f.write(bloque)
            break
        except requests.RequestException as e:
            ultimo = e
            print(f"intento {intento} fallido: {type(e).__name__}: {str(e)[:150]}", file=sys.stderr)
            if intento == reintentos:
                raise
            time.sleep(5 * intento)
    tamano = tmp.stat().st_size
    if tamano != meta["tamano"]:
        raise SystemExit(f"TAMAÑO NO COINCIDE: descargado {tamano}, la API dice {meta['tamano']}; se deja {tmp}")
    obtenido = sha256(tmp)
    if obtenido != meta["sha256"]:
        raise SystemExit(f"SHA-256 NO COINCIDE: descargado {obtenido}, la API dice {meta['sha256']}; se deja {tmp}")
    tmp.replace(destino)
    return destino


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--reintentos", type=int, default=3)
    args = ap.parse_args(argv)
    meta = consultar_archivo(args.timeout, args.reintentos)
    print(f"API: {meta['nombre']}  tamaño {meta['tamano']}  SHA-256 {meta['sha256']}")
    destino = descargar(meta, RAW / NOMBRE_ZIP, args.timeout, args.reintentos)
    print(f"OK {destino}  tamaño {destino.stat().st_size}  SHA-256 verificado")
    print(f"URL API: {URL_API}  DOI: {URL_DOI}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
