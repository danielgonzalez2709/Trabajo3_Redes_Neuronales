Actualiza /home/jose-miguel-pulgarin/Documents/projects/Trabajo3_Redes_Neuronales/docs/MEMORIA.md por el cierre de JO-3 (José,
28-nov). Reglas: ≤ 150 líneas en total (condensa entradas viejas si hace falta, sin borrar información de otros integrantes ni
decisiones vigentes); español neutro; no inventes nada fuera de lo que sigue. Edita solo MEMORIA.md.

1. «Estado»: agrega tras la entrada de JO-1 una de JO-3: terminado en `dev/jose` el sáb 28, pendiente de PR (junto con JO-1).
   `run.py m2-datos --config configs/m2/particion.yaml` llena `grupo_duplicado` y `split` (train/validacion/prueba) de
   `data/processed/m2/indice.csv` y escribe `results/data/m2/particion/{resumen.json,pares_cercanos.csv,frontera.csv}` y la figura
   `blog/docs/figures/m2/frontera_duplicados.png`. Método: pHash 64 bits con espejo (d_H ≤ 2) o coseno ResNet-18 ImageNet congelada
   (≥ 0,95) o marca de tiempo de cámara del nombre original ≤ 10 s (598 fotos, 3 formatos) → 341 grupos (mayor 444, 6,1 %);
   5 095 / 1 091 / 1 090, cada clase en 70/15/15; 0 pares que crucen splits; huella `e0a6b55a…747370`. Pesos: `scripts/descargar_pesos_m2.py`
   a `data/raw/m2/pesos/` (no versionado); caché de características en `data/processed/m2/cache/` (no versionada; JO-4 la reutiliza;
   extracción sin caché ~3 min en CPU). Fuga residual declarada con cifras en `resumen.json` (`fuga_residual`): ~94 % de validación y
   prueba tiene en train un vecino con coseno 0,90–0,95 (mismo conductor, D5) y 75 fotos de prueba tienen una de train a ≤ 60 s.
   Pruebas `tests/test_fuga_m2.py`, `tests/test_fuga_m2_auditoria.py`, `tests/test_descargar_pesos_m2.py` (112). Revisado por
   revisor-spec (aprobado con observaciones), revisor-calidad (3 vueltas; aprobado con observaciones, aplicadas) y auditor-fugas
   (fuga residual declarada; encontró las ráfagas → D9).
2. «Decisiones vigentes»: agrega M2 [DECIDIDO, José, 27–28-nov; `jose.md` §3.2] D1–D9 de JO-3 en 2–3 líneas (hash con espejo,
   ResNet-18 congelada, umbrales 2 / 0,95 = los más permisivos bajo la guarda del 15 %, estratificación por conteo de clases del
   grupo, semilla 2026, pares entre clases = misma escena otra acción, arista por marca de tiempo ≤ 10 s, fuga por conductor
   declarada).
3. «Avisos para el equipo»: (a) Daniel: `tests/test_no_network.py` corre `run.py figures` en la raíz del repo y reescribe las figuras
   versionadas (las de M3 de Juan José); debería escribir en un directorio temporal. Tras correr la suite, `git checkout --
   blog/docs/figures/m3/`. (b) M2: si se vuelve a correr `m2-datos` con `datos.yaml`, se vacían `grupo_duplicado` y `split`; correr
   después la partición con `particion.yaml`. (c) M2: el PR de JO-3 debe incluir `results/data/m2/particion/` y
   `configs/m2/particion.yaml` (las pruebas los leen).
4. «Pendientes» punto 5 (José): agrega JO-2 (descriptivo) como siguiente tarea y que el blog de M2 debe reportar la fuga residual
   con las cifras de `fuga_residual`.
5. «Cacería»: agrega 3 candidatos de M2 de JO-3 (sin número): «la partición elimina las ráfagas casi iguales» (Datos del mundo
   real; implementador-experto Opus; lo detectó auditor-fugas), «2 / 0,95 son los más estrictos» (Conceptos, menor; orquestador
   Opus, sin prompt literal) y «el auditor no encontró aumentos cruzando splits» (Datos del mundo real, menor; orquestador Opus →
   implementador); evidencia en `alucinaciones/evidencias/JO-3/`; ver `alucinaciones/registro.md`.
6. «Bitácora»: línea nueva arriba: `2026-11-28 · José · JO-3 ✅: partición sin fuga de M2 (341 grupos, 70/15/15 por clase, huella
   e0a6b55a…, 0 pares cruzados), D1–D9 en jose.md §3.2; fuga residual por conductor declarada; 3 candidatos a la cacería.`
