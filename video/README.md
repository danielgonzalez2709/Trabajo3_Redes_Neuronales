# Video promocional (Remotion)

Guion: [`guion.md`](guion.md). Duración objetivo: 2:30, 1920×1080, 30 fps. Se arma como el del Trabajo 2: composición
principal `Promocional` en Remotion, con cada escena registrada también por separado en la carpeta *Escenas* del Studio.

## Estado
Solo existe el guion. **Falta crear:**
- [ ] Proyecto Remotion (`video/package.json`, `video/src/`, `video/public/clips/`).
- [ ] Composición `Promocional` y una escena por fila del guion.
- [ ] Verificar la licencia de Remotion para este uso (se revisó en el Trabajo 2; confirmar de nuevo en su LICENSE.md oficial).
- [ ] Clips y grabaciones de pantalla (sáb 28), música con licencia verificada, URL y QR finales.

## Ver y editar (cuando exista el proyecto)
```bash
npm --prefix video install
npm --prefix video run dev
```
Abre el Studio en http://localhost:3000.

## Agregar los clips grabados (sáb 28)
1. Copiar cada toma a `video/public/clips/` (nombres según el guion: `daniel.mp4`, `andres.mp4`, `equipo.mp4`, `app-demanda.mp4`, etc.).
2. En `src/Promocional.tsx`, poner el nombre del archivo en cada escena. Mientras esté vacío, la escena muestra un aviso con
   quién habla y qué dice.
3. Cifras `[CIFRA: …]`: se leen de `results/data/`, no se escriben a mano.

## Exportar el MP4 (al final)
```bash
cd video
npx remotion render Promocional out/promocional.mp4
```
Subir a YouTube (no listado) el lun 30 y poner el enlace en la app (`URL_VIDEO_PROMOCIONAL`) y en el blog.
