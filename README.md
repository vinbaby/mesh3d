# VIN 3D Studio — Clean Start

The current prototype is a small Python/PySide6 desktop app. Updates are provided incrementally; there is no need to reinstall the project for each UI change.

## Apply update v0.1.3 (startup fix)
1. Close VIN 3D Studio.
2. Download `UPDATE_TO_V0.1.3.bat` from this repository.
3. Place it next to `run_windows.bat` in the existing Studio folder.
4. Run the updater. It downloads only the versioned `app/main.py` payload, creates a backup, and checks Python syntax. If the check fails, it attempts to restore the previous file.
5. Run `run_windows.bat` to verify startup.

No dependency reinstall is required.

## v0.1.3 — Startup fix
- Fixes the crash `StudioWindow object has no attribute 'viewport'` by connecting the Fit Image button only after the viewport has been created.

## Apply update v0.1.2 (reference drawing)
The manual frame drawing feature is already in v0.1.3. Existing installations should use v0.1.3 rather than v0.1.2.

## v0.1.2 — Reference frame drawing
- Import a reference image and show it flat in the viewport
- Toggle manual frame drawing
- Left-click and drag to trace strokes/edges directly on the image
- Undo the last stroke or clear the frame
- Adjust line width and zoom the image for closer tracing
- Save stroke points as JSON in normalized image coordinates
- Smoke tests cover syntax and the presence of the new workflow

## Important scope
The app records **2D guide strokes over the reference image**. It does not create a complete 3D model automatically and does not require an AI API. This stage is for manually constructing visual frame guides; the next step can turn these guides into editable mesh vertices and edges, then connect them to a 3D workflow.
