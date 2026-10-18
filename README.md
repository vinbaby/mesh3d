# VIN 3D Studio — Reference Frame

The desktop application is a Python/PySide6 app. Updates are incremental; do not reinstall the whole project for each UI change.

## Apply update v0.1.4
1. Close VIN 3D Studio.
2. Download `UPDATE_TO_V0.1.4.bat` from this repository.
3. Put it next to `run_windows.bat` in the folder where the Studio is already installed.
4. Run the updater. It downloads only the versioned `app/main.py` payload, backs up the current file, and runs a Python syntax check. If the check fails, it attempts to restore the previous file.
5. Run `run_windows.bat` again.

No API keys or dependency reinstall are required for this update.

## v0.1.4 — Automatic wireframe guide
- Importing an image automatically attempts foreground extraction using transparency or a locally estimated border background.
- The app samples the detected silhouette and draws a triangular 2D wireframe guide over the image.
- A button can rerun detection.
- Manual drawing remains optional.
- Undo/clear/save include automatically generated wireframe edges.
- The frame can be saved as JSON in normalized image coordinates.

## Important limitation
This creates a **2D wireframe guide overlay on the reference image**, not a true 3D reconstruction. It uses local segmentation and grid sampling; it does not use an AI model, API, or infer the hidden back side / body depth. A transparent-background image or a clear subject on a plain background works best. If it cannot isolate the main object, the app reports that and leaves manual drawing available.

The next stage is to make detected points and edges editable, then design how those guides should be projected into an actual 3D mesh. Rigging, weight paint, animation and AI 3D generation are out of scope for this update.
