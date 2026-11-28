# JJ-5 — evidencia de los candidatos sobre los diagnósticos de la red de dos torres (M3), 2026-11-27

Encontrados por el `verificador-matematico` (Opus) en R1 de JJ-5 (vueltas 1, 2 y 3). Los scripts de esta carpeta son copia de los
que corrió el verificador en el scratchpad de la sesión (fuera del repositorio): se conservan como evidencia, con las rutas absolutas
de esa máquina. `S0.npz` (puntajes de la semilla 0, 606 usuarios de prueba × 1 000 destinos, 5,3 MB) no se versiona: se regenera con
`v3_colapso.py`. Prompts literales: `alucinaciones/prompts/JJ-5-*.md`.

## C1. «personalización = media sobre destinos de la desviación entre usuarios de s_ui (b_i no aporta)»
- **Origen:** `JJ-5-implementador-experto.md` (orquestador Opus 5.5 → implementador-experto Opus): «una medida de personalización,
  p. ej. la media sobre destinos de la desviación entre usuarios de s_ui». El implementador la escribió tal cual en `red.py`.
- **Por qué es falso:** s_ui = ⟨u, v̄⟩ + ⟨u, v_i − v̄⟩ + b_i. El término ⟨u, v̄⟩ es un desplazamiento propio de cada usuario que infla
  la desviación entre usuarios y no cambia ningún orden. Lo que cambia el orden es la interacción doble centrada
  E = S − media de filas − media de columnas + media.
- **Evidencia (`v5_semilla8.py`, `v3_colapso.py`):** la semilla 8, reentrenada, reproduce la medida del JSON (0,242023, la más alta
  de las 30) y, sin embargo, el efecto de usuario explica el 74,0 % de la varianza de S y la interacción el 1,8 %; hay 6 listas
  top-10 distintas y los 606 usuarios tienen el mismo top-1. Sin el efecto de usuario la medida baja de 0,238 a 0,030.
- **Corrección:** `medidas_personalizacion` con E doble centrada y tres diagnósticos más (`fraccion_varianza_interaccion`,
  `listas_top10_distintas`, `fraccion_mismo_top1`); `JJ-5-implementador-experto-2.md`.

## C2. «(0 si S es constante)» y luego «∈ [0, 1]» para `fraccion_varianza_interaccion`
- **Origen:** el implementador-experto (Opus) escribió «0 si S es constante» con la guarda `total > 0` (2.ª vuelta); el
  orquestador (Opus 5.5) lo «corrigió» con `np.ptp(S) == 0` y escribió en el docstring «∈ [0, 1]» como garantía (3.ª vuelta).
- **Por qué es falso:** en punto flotante ‖S − μ‖² de una S constante no es 0 (≈ 1e-30 a 1e-27), y con S casi constante el
  cociente ‖E‖²/‖S − μ‖² lo dominan los errores de redondeo de las medias.
- **Evidencia (`w1_funcion.py`, `x1_frac.py`):** `np.full((5, 20), 0.7)` da 2,25; `np.full((606, 1000), −0.2513)` da 1 089; una sola
  celda en `nextafter(0.7)` en 606 × 1 000 da 2 720 334 135,0; 66 de 75 casos casi constantes salen de [0, 1].
- **Corrección (`x2_arreglo.py`, `y1_vuelta4.py`):** denominador = ‖E‖² + n_destinos·‖α‖² + n_usuarios·‖β‖² (descomposición
  ortogonal) y guarda `ptp == 0`; 0 de 75 casos fuera de [0, 1]; mismo valor en S genérica (diferencia relativa 2,2e-16) y en S0.
  Pruebas `test_personalizacion_con_puntajes_constantes_da_fraccion_cero` y `..._casi_constantes_queda_en_cero_uno`.

## C3. «En la práctica quedan por debajo de los destinos con train» / «no [superan] a los mejor puntuados de cada usuario»
- **Origen:** el orquestador (Opus 5.5) en `JJ-5-implementador-experto-2.md`, punto 2 («en la práctica quedan por debajo de los
  destinos con train»), copiado por el implementador en `descripcion_frios`; y de nuevo el orquestador en su corrección de la 2.ª
  vuelta («pueden superar a destinos con train, pero no a los mejor puntuados de cada usuario»).
- **Por qué es falso / impreciso:** la primera frase, leída literal, es falsa; la segunda presenta un resultado empírico de esta
  corrida como propiedad del modelo (nada en la arquitectura impide que un frío entre al top-K).
- **Evidencia (`x3_frios.py`, semilla 0):** en los 606 usuarios algún frío supera a algún destino con train; el mejor frío supera
  entre el 62,3 % y el 88,7 % de los 655 destinos con train (mediana 77,2 %) y su mejor posición es la 75 (mediana 150). Lo que sí
  vale es empírico: `frios_por_lista` = 0 en las 30 semillas para K ≤ 10.
- **Corrección:** «Pueden superar a destinos con train; si entran o no al top-K depende del entrenamiento, así que se MIDE en
  `frios_por_lista`.»
