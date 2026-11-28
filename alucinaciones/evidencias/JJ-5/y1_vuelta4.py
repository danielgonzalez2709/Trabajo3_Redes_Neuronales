import ast, numpy as np, re
R = r"C:\Repositorios\Trabajo3_Redes_Neuronales"
src = open(R + r"\src\m3_recomendacion\red.py", encoding="utf-8").read()
fn = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "medidas_personalizacion"][0]
def cargar(codigo):
    ns = {"np": np}; exec(codigo, ns); return ns["medidas_personalizacion"]
f = cargar(compile(ast.Module(body=[fn], type_ignores=[]), "m", "exec"))
seg = ast.get_source_segment(src, fn)
# mutantes: (a) cociente directo (vuelta 3), (b) n_destinos y n_usuarios intercambiados, (c) sin la guarda total==0 ni ptp
mut = {
 "directo": seg.replace("else e2 / total", "else e2 / float(((S - mu) ** 2).sum())"),
 "n_intercambiados": seg.replace("S.shape[1] * float((alfa", "S.shape[0] * float((alfa").replace("S.shape[0] * float((beta", "S.shape[1] * float((beta"),
 "sin_ptp": seg.replace("0.0 if constante or total == 0 else e2 / total", "(0.0 if total == 0 else e2 / total)"),
}
for k, v in mut.items(): assert v != seg, k
M = {k: cargar(v) for k, v in mut.items()}
rng = np.random.default_rng(0)
# --- los 75 casos de x1_frac.py (misma generación)
vals = []
for v in (0.7, -0.2513, 0.3, 123.456, 1e6):
    for sh in [(5, 20), (606, 1000), (326, 1000)]:
        for modo in ("ulp1", "ulp_rand", "una_celda", "fila", "col"):
            peor_hi, peor_lo = -np.inf, np.inf
            for rep in range(3):
                Sc = np.full(sh, v)
                if modo == "ulp1":
                    m = rng.random(sh) < 0.5; Sc[m] = np.nextafter(v, np.inf)
                elif modo == "ulp_rand":
                    Sc = v + rng.integers(-3, 4, size=sh) * np.spacing(v)
                elif modo == "una_celda":
                    Sc[rng.integers(sh[0]), rng.integers(sh[1])] = np.nextafter(v, np.inf)
                elif modo == "fila":
                    Sc[rng.integers(sh[0]), :] = np.nextafter(v, np.inf)
                else:
                    Sc[:, rng.integers(sh[1])] = np.nextafter(v, np.inf)
                r = f(Sc)["fraccion_varianza_interaccion"]; peor_hi = max(peor_hi, r); peor_lo = min(peor_lo, r)
            vals.append((v, sh, modo, peor_lo, peor_hi))
fuera = [x for x in vals if not (0 <= x[3] and x[4] <= 1)]
print("casos:", len(vals), " fuera de [0,1]:", len(fuera), " min", min(x[3] for x in vals), " max", max(x[4] for x in vals))
# ruido relativo y constantes exactas
for v in (0.7, -0.2513):
    print(v, [round(f(v + v*rel*rng.normal(size=(606, 1000)))["fraccion_varianza_interaccion"], 4) for rel in (1e-16, 1e-15, 1e-14, 1e-13, 1e-10)])
for v, sh in [(0.7, (5, 20)), (-0.2513, (606, 1000)), (0.3, (326, 1000))]:
    m = f(np.full(sh, v)); print("constante", v, sh, m, " sin_ptp:", M["sin_ptp"](np.full(sh, v))["fraccion_varianza_interaccion"])
# S genérica y S0
S = np.random.default_rng(1).normal(size=(50, 80)); E = S - S.mean(1, keepdims=True) - S.mean(0, keepdims=True) + S.mean()
directa = (E**2).sum() / ((S - S.mean())**2).sum()
print("genérica: nueva %.17g directa %.17g rel %.2e | n_intercambiados %.6g" % (f(S)["fraccion_varianza_interaccion"], directa, abs(f(S)["fraccion_varianza_interaccion"]/directa-1), M["n_intercambiados"](S)["fraccion_varianza_interaccion"]))
z = np.load(r"C:/Users/juanj/AppData/Local/Temp/claude/92481566dd5b376c/7690fb16-ed9d-4177-8666-ce080137b320/scratchpad/jj5/S0.npz", allow_pickle=True)
S0 = z["S"]; m0 = f(S0); print("S0 nueva:", m0, " (vuelta 3: 0.539799066873758, pers 0.04017946977213715, listas 176, top1 0.3415841584158416)")
Sn = rng.normal(size=(4, 6)); Sn[0, 0] = np.nan; print("NaN:", f(Sn)["fraccion_varianza_interaccion"])
# --- pruebas nuevas reproducidas con la función extraída y con los mutantes
def casi(caso):
    S = np.full((606, 1000), 0.7)
    if caso == "una_celda": S[3, 7] = np.nextafter(0.7, np.inf)
    elif caso == "una_columna": S[:, 5] = np.nextafter(0.7, np.inf)
    else: S = 0.7 + np.random.default_rng(0).integers(-3, 4, size=S.shape) * np.spacing(0.7)
    return S
for nombre, g in [("actual", f)] + list(M.items()):
    r = {c: g(casi(c))["fraccion_varianza_interaccion"] for c in ("una_celda", "una_columna", "ruido_3_ulp")}
    t1 = all(0 <= x <= 1 for x in r.values())
    t2 = abs(g(S)["fraccion_varianza_interaccion"] - directa) <= 1e-12 * abs(directa)
    t0 = all(g(np.full(sh, v))["fraccion_varianza_interaccion"] == 0.0 for v, sh in [(0.7, (5, 20)), (-0.2513, (606, 1000)), (0.3, (326, 1000))])
    print(f"{nombre:17s} casi_constantes {t1} {r} | genérica {t2} | constantes {t0}")
