# VIN 3D Studio — Clean Start

The current prototype is a small Python/PySide6 desktop app. The v0.1.1 change is delivered as an **incremental update**, not a reinstall.

## Apply update v0.1.1
1. Close VIN 3D Studio.
2. Download `UPDATE_TO_V0.1.1.bat` from this repository.
3. Put the updater next to `run_windows.bat` in the existing Studio folder.
4. Run the updater. It downloads only the versioned `app/main.py` payload, saves a backup, and checks Python syntax. If the check fails, it restores the previous file.
5. Run `run_windows.bat` to test the app.

No dependency reinstall is required for this update.

## v0.1.1 changes
- Foreground extraction using border-connected background flood fill for plain-background images
- Surface mesh follows the detected silhouette rather than filling the whole rectangular image
- Front and back surfaces with side walls create an extruded silhouette mesh
- Wireframe edges appear only when Wireframe is enabled
- Keeps the current Studio shell, image loader, viewport controls, resolution selector and stats

## Important limitation
This is silhouette-based 2.5D extrusion, **not** AI generation of a fully shaped character. It preserves the source image's colors on the front surface but does not infer face depth, body volume, unseen anatomy or the character's back side. Plain-background reference images work best. Full image-to-3D generation and GLB export are separate future steps.

Rigging, weight paint, and animation remain out of scope for this clean-start phase.
