# VIN 3D Studio — Clean Start

This repository currently contains the first small desktop prototype for rebuilding VIN 3D Studio.

## Run on Windows
1. Install Python 3.10 or newer.
2. Run `install_windows.bat` to create the virtual environment and install dependencies from `pyproject.toml`.
3. Run `run_windows.bat`.

The desktop entry point is `app/main.py`.

## Phase 1 includes
- A simple dark Studio window with side panels
- Load PNG, JPG, or WebP reference images
- A rotatable and zoomable viewport
- A brightness-based 2.5D relief mesh preview
- Adjustable relief depth and a conservative mesh resolution range
- Vertex/triangle counters and a wireframe toggle

## Important limitation
This is a basic relief-mesh prototype, **not** AI image-to-complete-3D generation. It does not infer hidden geometry or a character's back side. The goal of this phase is to validate the app shell and keep viewport interactions responsive before integrating a real image-to-3D backend.

Rigging, weight paint, animation, and GLB export are not included in this clean-start phase.
