"""Verifica el comentario «(R1: 15,5 / 0,6 · … ≠ 31)» de tests/test_operacion_m1.py en el commit 1a27df7.

Recalcula, a mano y sin importar src/, la carga de R1 del caso de la prueba
`test_multiplicadores_reproducen_cada_ruta` (mismos números que el código de esa prueba).
Uso: .venv/bin/python alucinaciones/evidencias/CA-3d/verificar_comentario_R1.py
"""
import subprocess

COMMIT = "1a27df7"
texto = subprocess.run(["git", "show", f"{COMMIT}:tests/test_operacion_m1.py"],
                       capture_output=True, text=True, check=True).stdout
linea = next(l for l in texto.splitlines() if "15,5 / 0,6" in l)
print(f"Comentario en {COMMIT}: {linea.strip()}")

# Datos de la prueba (mismo commit): f y cap_ef por ruta; demanda y despachos observados.
f = {"R1": 0.5, "R2": 1.0}
cap = {"R1": 20.0, "R2": 10.0}
D = {"R1": [400, 260], "R2": [50]}
O = {"R1": 20 + 11, "R2": 5}

A = {r: sum(f[r] * d / cap[r] for d in D[r]) for r in D}  # cargas llenas Σ f·D / cap_ef
rho = sum(A.values()) / sum(O.values())
print(f"Carga llena de R1, Σ f·D/cap_ef = 0,5·(400+260)/20 = {A['R1']:.4g}  (el comentario dice 15,5)")
print(f"ρ* = Σ A / Σ O = {sum(A.values()):.4g} / {sum(O.values())} = {rho:.4f}")
print(f"Con ρ = 0,6: A_R1/0,6 = {A['R1'] / 0.6:.4g} ≠ {O['R1']}")
print(f"Con ρ = ρ*: A_R1/ρ* = {A['R1'] / rho:.4g} ≠ {O['R1']}")
print(f"Con 15,5 (cifra del comentario): 15,5/0,6 = {15.5 / 0.6:.4g}")
