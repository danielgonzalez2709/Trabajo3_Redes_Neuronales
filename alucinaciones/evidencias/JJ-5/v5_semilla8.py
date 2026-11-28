import sys, json, os
R = r"C:\Repositorios\Trabajo3_Redes_Neuronales"; sys.path.insert(0, R); os.chdir(R)
import numpy as np
from src.comun.config import load_config, apply_overrides
from src.comun.seeds import make_rng
from src.m3_recomendacion import experimento, red, metricas
cfg = apply_overrides(load_config(R + r"\configs\m3\base.yaml"), ["red.hiperparametros_desde=config"])
cfg["salida"]["carpeta"] = r"C:/Users/juanj/AppData/Local/Temp/claude/92481566dd5b376c/7690fb16-ed9d-4177-8666-ce080137b320/scratchpad/jj5/out"
ctx = experimento.cargar_datos(cfg)
inter, cat = ctx["inter"], ctx["catalogo"]
up = np.sort(inter[inter.split == "prueba"].usuario_id.unique())
for s in (8, 0):
    rng = make_rng(0, s)
    m = red.fabrica_red(cfg)
    m.ajustar(inter, cat, rng)
    S = m.puntuar(up)
    dj = json.load(open(R + rf"\results\data\m3\semillas\red_seed{s}.json", encoding="utf-8"))["diagnosticos"]
    d = m.diagnosticos()
    print(f"semilla {s}: personalizacion reproducida {d['personalizacion']:.6f} (json {dj['personalizacion']:.6f}); mejor_epoca {d['mejor_epoca']} (json {dj['mejor_epoca']})")
    mu = S.mean(); fu = S.mean(1, keepdims=True) - mu; fi = S.mean(0, keepdims=True) - mu; E = S - mu - fu - fi; tot = ((S - mu) ** 2).sum()
    print("  fracción de varianza: usuario %.3f destino %.3f interacción %.3f" % ((fu**2).sum()*S.shape[1]/tot, (fi**2).sum()*S.shape[0]/tot, (E**2).sum()/tot))
    print("  personalizacion (std_u s_ui) en prueba %.4f ; sin el efecto de usuario (doble centrado) %.4f ; std del efecto de usuario %.4f" % (S.std(0).mean(), E.std(0).mean(), fu.std()))
    top = np.argsort(-S, 1)[:, :10]
    print("  listas top-10 (catálogo completo) distintas:", len({tuple(r) for r in top}), " top-1 más común:", np.bincount(top[:, 0]).max(), "/", len(up))
    del m
