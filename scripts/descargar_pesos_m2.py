"""Descarga UNA vez los pesos ImageNet de ResNet-18 para M2 (JO-3, D2; único código con red de la partición).

- Destino y SHA-256 completo: ``caracteristicas.pesos`` y ``caracteristicas.sha256_pesos`` de ``configs/m2/particion.yaml``
  (no se duplican aquí).
- URL: la que expone torchvision (``ResNet18_Weights.IMAGENET1K_V1.url``); su nombre de archivo debe ser el del destino.
- Verificación: el nombre trae un prefijo del SHA-256 (convención de ``torch.hub``: ``resnet18-<prefijo>.pth``, misma
  expresión ``-([a-f0-9]*)\\.``) que debe coincidir con el inicio del SHA-256 de la config, y el archivo descargado debe tener
  EXACTAMENTE el SHA-256 completo de la config. Si el archivo ya existe con ese SHA-256, no se vuelve a bajar.

Los experimentos (``src/m2_conduccion/duplicados.py``) cargan los pesos desde ese archivo local; nunca desde internet.

Uso: .venv/bin/python scripts/descargar_pesos_m2.py [--timeout 120] [--reintentos 3]
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import requests
import yaml

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:  # el script se corre como `python scripts/descargar_pesos_m2.py`: la raíz no está en sys.path
    sys.path.insert(0, str(RAIZ))
from src.m2_conduccion.datos import sha256_archivo  # noqa: E402  (un solo origen; también lo usa la partición)

CONFIG = RAIZ / "configs" / "m2" / "particion.yaml"
PATRON_PREFIJO = re.compile(r"-([a-f0-9]*)\.")   # misma expresión que torch.hub.HASH_REGEX
BLOQUE = 1024 * 1024


def url_pesos() -> str:
    """URL de los pesos ImageNet de ResNet-18 según la versión instalada de torchvision."""
    from torchvision.models import ResNet18_Weights

    return ResNet18_Weights.IMAGENET1K_V1.url


def leer_config(ruta: Path = CONFIG) -> tuple[Path, str]:
    """(destino absoluto, SHA-256 completo esperado) desde ``caracteristicas`` de la config de la partición."""
    c = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))["caracteristicas"]
    return RAIZ / c["pesos"], str(c["sha256_pesos"]).lower()


def prefijo_de(nombre: str) -> str:
    """Prefijo del SHA-256 que trae el nombre del archivo (``resnet18-f37072fd.pth`` → ``f37072fd``)."""
    m = PATRON_PREFIJO.search(nombre)
    if m is None or not m.group(1):
        raise ValueError(f"el nombre {nombre!r} no trae un prefijo de SHA-256 con la convención de torch.hub")
    return m.group(1)


def descargar(url: str, destino: Path, sha256_esperado: str, timeout: float, reintentos: int) -> str:
    """Baja ``url`` a ``destino`` (vía un ``.part``) y devuelve el SHA-256 medido; falla si no es ``sha256_esperado``."""
    if reintentos < 1:
        raise ValueError(f"reintentos debe ser al menos 1 (recibido {reintentos})")
    prefijo = prefijo_de(destino.name)
    if not sha256_esperado.startswith(prefijo):
        raise ValueError(f"config incoherente: el prefijo {prefijo} del nombre {destino.name} no es el inicio del SHA-256 "
                         f"esperado {sha256_esperado}")
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.is_file() and sha256_archivo(destino) == sha256_esperado:
        print(f"{destino.name} ya existe con el SHA-256 de la config: no se descarga")
        return sha256_esperado
    tmp = destino.with_suffix(destino.suffix + ".part")
    for intento in range(1, reintentos + 1):
        try:
            with requests.get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                with open(tmp, "wb") as f:
                    for bloque in r.iter_content(BLOQUE):
                        f.write(bloque)
            break
        except requests.RequestException as e:
            print(f"intento {intento} fallido: {type(e).__name__}: {str(e)[:150]}", file=sys.stderr)
            if intento == reintentos:
                raise
            time.sleep(5 * intento)
    medido = sha256_archivo(tmp)
    if medido != sha256_esperado:
        raise SystemExit(f"SHA-256 NO COINCIDE: medido {medido}, la config espera {sha256_esperado}; se deja {tmp}")
    tmp.replace(destino)
    return medido


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--reintentos", type=int, default=3)
    args = ap.parse_args(argv)
    destino, esperado = leer_config()
    url = url_pesos()
    if url.rsplit("/", 1)[-1] != destino.name:
        raise SystemExit(f"la URL de torchvision ({url}) no corresponde al destino de la config ({destino.name})")
    medido = descargar(url, destino, esperado, args.timeout, args.reintentos)
    print(f"URL: {url}")
    print(f"OK {destino.relative_to(RAIZ).as_posix()}  tamaño {destino.stat().st_size} B")
    print(f"prefijo del nombre: {prefijo_de(destino.name)}  SHA-256 medido = config: {medido}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
