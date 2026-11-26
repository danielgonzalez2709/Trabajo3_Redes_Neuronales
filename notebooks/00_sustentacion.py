# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
# ---

# %% [markdown]
# # 00 · Sustentación
# Una celda por módulo: el profesor escoge el módulo y pide cambios de hiperparámetros en vivo.
# Se edita el dict `SET_Mx` de la celda de parámetros, se escribe la predicción y se ejecuta la celda del módulo.
# Cero lógica aquí: todo corre con `src/` a través de `run.py`.

# %%
CONFIG = "configs/notebooks/00_sustentacion.yaml"

# Un SET por módulo; mismas claves que `--set` en la terminal (clave inexistente = error).
SET_M1 = {}  # ajustar cuando exista la config de demo de Andrés. Ejemplo: {"entrenamiento.lr": 5e-4}
SET_M2 = {}  # ajustar cuando exista la config de demo de José. Ejemplo: {"entrenamiento.lr": 5e-4}
SET_M3 = {}  # ajustar cuando exista la config de demo de Juan José. Ejemplo: {"evaluacion.k": 10}

# %%
from src.comun.notebooks import config_notebook, correr_demo

cfg = config_notebook(CONFIG)

# %% [markdown]
# ## M1 · Demanda de pasajeros (series de tiempo)
# Demuestra el pronóstico de demanda con referencias y redes en modo demo (dueño de la demo: Andrés).
# Equivalente en terminal: `python run.py m1 --config configs/m1/demo.yaml`

# %% [markdown]
# ### Predicción antes de ejecutar
# - Cambio que hago (`SET_M1`):
# - Qué espero que pase con la métrica y por qué:
# - Qué contrastaré con la corrida de referencia:

# %%
res_m1 = correr_demo(cfg, "m1", SET_M1)
print("Estado M1:", res_m1["estado"])

# %% [markdown]
# ## M2 · Conducción distractiva (imágenes)
# Demuestra la clasificación de imágenes con referencias y redes en modo demo (dueño de la demo: José).
# Equivalente en terminal: `python run.py m2 --config configs/m2/demo.yaml`

# %% [markdown]
# ### Predicción antes de ejecutar
# - Cambio que hago (`SET_M2`):
# - Qué espero que pase con la métrica y por qué:
# - Qué contrastaré con la corrida de referencia:

# %%
res_m2 = correr_demo(cfg, "m2", SET_M2)
print("Estado M2:", res_m2["estado"])

# %% [markdown]
# ## M3 · Recomendación de destinos
# Demuestra el recomendador con referencias y red en modo demo (dueño de la demo: Juan José).
# Equivalente en terminal: `python run.py m3 --config configs/m3/demo.yaml`

# %% [markdown]
# ### Predicción antes de ejecutar
# - Cambio que hago (`SET_M3`):
# - Qué espero que pase con la métrica y por qué:
# - Qué contrastaré con la corrida de referencia:

# %%
res_m3 = correr_demo(cfg, "m3", SET_M3)
print("Estado M3:", res_m3["estado"])
