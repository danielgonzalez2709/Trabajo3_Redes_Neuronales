# JJ-3 — 3.ª vuelta del orquestador (Opus 5.5) al revisor-calidad (Haiku), 2026-11-26

Por tu N1, la sesión principal cambió el paso 2 de `asignar_split` en `src/m3_recomendacion/particion.py` (líneas ~125-127):
en lugar de `canonico.sort_values(["usuario_id", "xi"])` con un comentario que prometía estabilidad no documentada, ahora usa
`canonico.iloc[np.lexsort((np.arange(n), xi, usuario_id))]`, con desempate explícito por la posición canónica. Revisa SOLO ese
cambio: ¿es correcto (np.lexsort ordena por la última clave como primaria), legible para explicarlo en vivo y equivalente al
anterior? Comprobado por la sesión principal: `run.py m3-datos` da el mismo SHA-256 del parquet (`4e143626…5e315e`), la misma
huella (`b35cd70b…58e8b8`) y el mismo `resumen.json`; `tests/test_fuga_m3.py` 53 passed. Solo lectura. Si quieres, verifica que
el mutante «sin orden canónico» (quitar el `sort_values(CLAVE, …)` del paso 1) sigue haciendo fallar
`test_independiente_del_orden_de_entrada`, sobre una copia en el scratchpad (no edites el repositorio). N2 y N3 no se aplican.

Entrega: APROBADO / CAMBIOS NECESARIOS.
