"""Adversarial leak audit for M2 partition (JO-3). Read-only on project outputs."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
import imagehash
from PIL import Image, ImageOps

RAIZ = Path("/home/jose-miguel-pulgarin/Documents/projects/Trabajo3_Redes_Neuronales")
sys.path.insert(0, str(RAIZ))
from src.m2_conduccion import duplicados as D  # noqa: E402

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
cfg = yaml.safe_load((RAIZ / "configs/m2/particion.yaml").read_text())
car = cfg["caracteristicas"]
proc = RAIZ / "data/processed/m2"
idx = pd.read_csv(proc / "indice.csv", dtype=str, keep_default_na=False)
cache = D.leer_cache(RAIZ / car["cache"])
huella = D.huella_imagenes(proc, idx["archivo"].tolist())
print("cache_valida:", D.cache_valida(RAIZ / car["cache"], idx["id"].tolist(), car["sha256_pesos"], huella))
z = cache["caracteristicas"].astype(np.float64)
zn = D.normalizar_filas(z)
split = idx["split"].to_numpy()
clase = idx["clase"].to_numpy()
N = len(idx)
res = {}

# 0. cache faithful: recompute features of 64 random images
modelo = D.cargar_resnet18(RAIZ / car["pesos"], car["sha256_pesos"])
mu = torch.tensor(car["media"]).view(1, 3, 1, 1)
sd = torch.tensor(car["desviacion"]).view(1, 3, 1, 1)


def feats(imgs):
    out = []
    with torch.no_grad():
        for i in range(0, len(imgs), 64):
            x = torch.from_numpy(np.stack([np.asarray(im.convert("RGB"), dtype=np.float32) for im in imgs[i:i + 64]]))
            x = x.permute(0, 3, 1, 2) / 255.0
            out.append(modelo((x - mu) / sd).numpy())
    return np.concatenate(out).astype(np.float64)


rng = np.random.default_rng(7)
muestra = rng.choice(N, 64, replace=False)
imgs_m = [Image.open(proc / idx["archivo"][i]).convert("RGB") for i in muestra]
zr = feats(imgs_m)
res["cache_max_abs_diff"] = float(np.abs(zr - z[muestra]).max())
print("cache max abs diff", res["cache_max_abs_diff"])

# 1. full recompute of cross-split nearest neighbours (cosine + hamming with mirror)
hb, hfb = D.hashes_de_archivos([proc / a for a in idx["archivo"]], 8, 4, True)
h, hf = D.empaquetar(hb), D.empaquetar(hfb)
tr = np.where(split == "train")[0]
cruces = {}
for s in ("validacion", "prueba"):
    q = np.where(split == s)[0]
    C = zn[q] @ zn[tr].T
    H = D.distancia_hamming_espejo(h[q], hf[q], h[tr], hf[tr])
    nn_c = C.max(1)
    nn_h = H.min(1)
    arg_c = C.argmax(1)
    cruces[s] = {
        "n": int(len(q)),
        "pares_cos_ge_095": int((C >= 0.95).sum()), "pares_dH_le_2": int((H <= 2).sum()),
        "max_cos_al_train": float(nn_c.max()), "min_dH_al_train": int(nn_h.min()),
        "img_nn_cos_[0.90,0.95)": int(((nn_c >= 0.90) & (nn_c < 0.95)).sum()),
        "img_nn_cos_[0.94,0.95)": int(((nn_c >= 0.94) & (nn_c < 0.95)).sum()),
        "img_nn_cos_[0.93,0.94)": int(((nn_c >= 0.93) & (nn_c < 0.94)).sum()),
        "img_nn_cos_<0.90": int((nn_c < 0.90).sum()),
        "cuantiles_nn_cos": {str(qq): float(np.quantile(nn_c, qq)) for qq in (0.05, 0.25, 0.5, 0.75, 0.95)},
        "img_nn_dH_le_4": int((nn_h <= 4).sum()), "img_nn_dH_le_6": int((nn_h <= 6).sum()),
        "img_nn_dH_le_8": int((nn_h <= 8).sum()),
        "dist_nn_dH": {str(k): int(v) for k, v in enumerate(np.bincount(nn_h)) if v and k <= 14},
        "misma_clase_del_vecino_cos": float((clase[q] == clase[tr[arg_c]]).mean()),
    }
    if s == "prueba":
        q_te, C_te, H_te, nn_c_te, arg_te = q, C, H, nn_c, arg_c
res["cruces"] = cruces
# within-train baseline: nn cosine inside train (excluding self) for comparison
Ctt = zn[tr] @ zn[tr].T
np.fill_diagonal(Ctt, -1)
nn_tt = Ctt.max(1)
res["train_interno_nn_cos_cuantiles"] = {str(qq): float(np.quantile(nn_tt, qq)) for qq in (0.05, 0.25, 0.5, 0.75, 0.95)}
del Ctt
print(json.dumps(res, indent=1))

# 2. alternative hashes (dHash, aHash, wHash, pHash of central crop) cross-split
def alt_hashes(paths):
    out = {"dhash": [], "ahash": [], "whash": [], "phash_centro": []}
    for p in paths:
        with Image.open(p) as im:
            im = im.convert("RGB")
            out["dhash"].append(imagehash.dhash(im).hash.flatten())
            out["ahash"].append(imagehash.average_hash(im).hash.flatten())
            out["whash"].append(imagehash.whash(im).hash.flatten())
            out["phash_centro"].append(imagehash.phash(im.crop((34, 34, 190, 190))).hash.flatten())
    return {k: D.empaquetar(np.array(v, dtype=bool)) for k, v in out.items()}


A = alt_hashes([proc / a for a in idx["archivo"]])
alt = {}
for k, v in A.items():
    Hq = D.hamming_matriz(v[q_te], v[tr])
    Hall = None
    nn = Hq.min(1)
    # same-split baseline: within train, nn distance
    alt[k] = {"prueba_nn_dist_conteo": {str(d): int(c) for d, c in enumerate(np.bincount(nn)) if c and d <= 8},
              "pares_cruzados_dist_0": int((Hq == 0).sum()), "pares_cruzados_dist_le_2": int((Hq <= 2).sum())}
    # for the cross pairs at distance <= 2, what is their cosine and phash distance?
    ii, jj = np.nonzero(Hq <= 2)
    if len(ii):
        alt[k]["cos_de_esos_pares_cuantiles"] = {str(qq): float(np.quantile(C_te[ii, jj], qq)) for qq in (0, 0.5, 1)}
        alt[k]["dH_phash_de_esos_pares_min"] = int(H_te[ii, jj].min())
        alt[k]["ejemplos"] = [(idx["id"][q_te[a]], idx["id"][tr[b]], int(Hq[a, b]), float(C_te[a, b]), int(H_te[a, b]))
                              for a, b in list(zip(ii, jj))[:10]]
res["hashes_alternativos_prueba_vs_train"] = alt
print(json.dumps(alt, indent=1))

# 3. calibration: recall of the criterion on synthetic augmentations described by the paper
def aug_variants(im):
    w, hh = im.size
    v = {}
    for ang in (5, 10, 15):
        v[f"rot{ang}"] = im.rotate(ang, resample=Image.Resampling.BILINEAR)
        v[f"rot{ang}_zoom"] = im.rotate(ang, resample=Image.Resampling.BILINEAR).crop(
            (int(w * .12), int(hh * .12), int(w * .88), int(hh * .88))).resize((w, hh), Image.Resampling.BILINEAR)
    for zf in (0.9, 0.8):
        m = (1 - zf) / 2
        v[f"zoom{zf}"] = im.crop((int(w * m), int(hh * m), int(w * (1 - m)), int(hh * (1 - m)))).resize((w, hh), Image.Resampling.BILINEAR)
    v["recorte_esquina"] = im.crop((0, 0, int(w * .85), int(hh * .85))).resize((w, hh), Image.Resampling.BILINEAR)
    v["brillo+40"] = Image.fromarray(np.clip(np.asarray(im).astype(int) + 40, 0, 255).astype(np.uint8))
    v["espejo"] = ImageOps.mirror(im)
    v["espejo_rot10"] = ImageOps.mirror(im).rotate(10, resample=Image.Resampling.BILINEAR)
    return v


cal_idx = rng.choice(N, 150, replace=False)
names = list(aug_variants(Image.open(proc / idx["archivo"][0]).convert("RGB")).keys())
recall = {n: {"cos": [], "dH": []} for n in names}
for i in cal_idx:
    im = Image.open(proc / idx["archivo"][i]).convert("RGB")
    vs = aug_variants(im)
    zv = D.normalizar_filas(feats(list(vs.values())))
    hv, hfv = D.hashes_de_imagenes(list(vs.values()), 8, 4, True)
    hv, hfv = D.empaquetar(hv), D.empaquetar(hfv)
    dh = D.distancia_hamming_espejo(h[[i]], hf[[i]], hv, hfv)[0]
    for k, n in enumerate(vs):
        recall[n]["cos"].append(float(zv[k] @ zn[i]))
        recall[n]["dH"].append(int(dh[k]))
cal = {}
for n, d in recall.items():
    c, dh = np.array(d["cos"]), np.array(d["dH"])
    cal[n] = {"recall_arista": float(((c >= 0.95) | (dh <= 2)).mean()), "recall_cos": float((c >= 0.95).mean()),
              "recall_dH": float((dh <= 2).mean()), "cos_mediana": float(np.median(c)), "cos_min": float(c.min()),
              "dH_mediana": float(np.median(dh))}
res["calibracion_aumentos_150_imagenes"] = cal
print(json.dumps(cal, indent=1))

# 4. TTA search: augment every test image, look for train images that match a variant much better than the original
tta_names = ["rot5", "rot10", "rot15", "rot5n", "rot10n", "rot15n", "zoom0.9", "zoom0.8", "espejo"]


def tta(im):
    w, hh = im.size
    v = []
    for ang in (5, 10, 15, -5, -10, -15):
        v.append(im.rotate(ang, resample=Image.Resampling.BILINEAR))
    for zf in (0.9, 0.8):
        m = (1 - zf) / 2
        v.append(im.crop((int(w * m), int(hh * m), int(w * (1 - m)), int(hh * (1 - m)))).resize((w, hh), Image.Resampling.BILINEAR))
    v.append(ImageOps.mirror(im))
    return v


ztr = zn[tr]
mejor_var = np.full(len(q_te), -1.0)
arg_var = np.zeros(len(q_te), dtype=int)
var_de = np.zeros(len(q_te), dtype=int)
mejor_var_h = np.full(len(q_te), 99)
lote_imgs, lote_q = [], []


def flush():
    global lote_imgs, lote_q
    if not lote_imgs:
        return
    zv = D.normalizar_filas(feats(lote_imgs))
    hv, hfv = D.hashes_de_imagenes(lote_imgs, 8, 4, True)
    hv, hfv = D.empaquetar(hv), D.empaquetar(hfv)
    Cv = zv @ ztr.T
    Hv = D.distancia_hamming_espejo(hv, hfv, h[tr], hf[tr])
    for r_, a in enumerate(lote_q):
        qi, vi = a
        m = Cv[r_].max()
        if m > mejor_var[qi]:
            mejor_var[qi], arg_var[qi], var_de[qi] = m, Cv[r_].argmax(), vi
        mejor_var_h[qi] = min(mejor_var_h[qi], Hv[r_].min())
    lote_imgs, lote_q = [], []


for qi, gi in enumerate(q_te):
    im = Image.open(proc / idx["archivo"][gi]).convert("RGB")
    for vi, v in enumerate(tta(im)):
        lote_imgs.append(v)
        lote_q.append((qi, vi))
    if len(lote_imgs) >= 576:
        flush()
flush()
gan = mejor_var - nn_c_te
res["tta_prueba"] = {
    "n": int(len(q_te)),
    "variantes_cos_ge_095_con_train": int((mejor_var >= 0.95).sum()),
    "variantes_cos_ge_097_con_train": int((mejor_var >= 0.97).sum()),
    "variantes_cos_ge_098_con_train": int((mejor_var >= 0.98).sum()),
    "variantes_dH_le_2_con_train": int((mejor_var_h <= 2).sum()),
    "max_cos_variante": float(mejor_var.max()),
    "ganancia_cos_cuantiles": {str(qq): float(np.quantile(gan, qq)) for qq in (0.5, 0.9, 0.99, 1.0)},
    "max_cos_original": float(nn_c_te.max()),
}
peores = np.argsort(-mejor_var)[:8]
res["tta_peores"] = [{"prueba": idx["id"][q_te[a]], "train": idx["id"][tr[arg_var[a]]], "variante": tta_names[var_de[a]],
                      "cos_variante": float(mejor_var[a]), "cos_original_al_mismo": float(C_te[a, arg_var[a]]),
                      "dH_original_al_mismo": int(H_te[a, arg_var[a]]), "clase_prueba": clase[q_te[a]],
                      "clase_train": clase[tr[arg_var[a]]]} for a in peores]
print(json.dumps({k: res[k] for k in ("tta_prueba", "tta_peores")}, indent=1))

# worst cross pairs by original cosine -> save side by side
orden = np.argsort(-nn_c_te)[:6]
res["pares_cruzados_mas_cercanos_coseno"] = []
for r_, a in enumerate(orden):
    b = arg_te[a]
    ia, ib = q_te[a], tr[b]
    res["pares_cruzados_mas_cercanos_coseno"].append({"prueba": idx["id"][ia], "train": idx["id"][ib], "cos": float(C_te[a, b]),
                                                     "dH": int(H_te[a, b]), "clase_prueba": clase[ia], "clase_train": clase[ib]})
    A_ = Image.open(proc / idx["archivo"][ia]).convert("RGB")
    B_ = Image.open(proc / idx["archivo"][ib]).convert("RGB")
    lienzo = Image.new("RGB", (448, 224))
    lienzo.paste(A_, (0, 0))
    lienzo.paste(B_, (224, 0))
    lienzo.save(OUT / f"cruce_coseno_{r_ + 1}_{idx['id'][ia]}_{idx['id'][ib]}.jpg", quality=90)
for r_, a in enumerate(peores[:4]):
    ia, ib = q_te[a], tr[arg_var[a]]
    lienzo = Image.new("RGB", (448, 224))
    lienzo.paste(Image.open(proc / idx["archivo"][ia]).convert("RGB"), (0, 0))
    lienzo.paste(Image.open(proc / idx["archivo"][ib]).convert("RGB"), (224, 0))
    lienzo.save(OUT / f"cruce_tta_{r_ + 1}_{idx['id'][ia]}_{idx['id'][ib]}.jpg", quality=90)
(OUT / "auditoria.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
print("pares_cruzados_mas_cercanos_coseno", json.dumps(res["pares_cruzados_mas_cercanos_coseno"], indent=1))
