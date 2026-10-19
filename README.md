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


---

## New tool: VIN Procedural Lab (Blender add-on)

The separate Blender add-on is in [`blender_addon/vin_procedural_lab.py`](blender_addon/vin_procedural_lab.py), with install/use instructions in [`blender_addon/README.md`](blender_addon/README.md).

It provides a procedural 3D shape generator and an Animation Builder that creates editable Geometry Nodes groups. It does not use an AI API and does not replace the existing desktop app.

## Separate add-on: VIN Motion Lab

Animation is being kept in its own add-on so it does not interfere with the procedural shape generator. Download [`blender_addon/vin_motion_lab.py`](blender_addon/vin_motion_lab.py) and follow [`blender_addon/VIN_MOTION_LAB_README.md`](blender_addon/VIN_MOTION_LAB_README.md).

VIN Motion Lab uses its own **VIN Motion** sidebar tab and provides Bob/Float, Spin, Pulse, Twist, plus a Noise/Color Ramp Geometry Nodes scatter tool for a Plane. It can be installed alongside VIN Procedural Lab.


Alien Lattice was added to the procedural generator: a 3-layer organic shell / triangular space-frame / metal-bead sculpture. VIN Motion Lab v0.7.0 adds Lattice Pulse to deform each layer independently with a Noise/Color Ramp mask. See the add-on READMEs for use and installation.


VIN Motion Lab v0.8.1 adds eight transform-keyframed Object Motion Actions (Wobble/Tumble, Shockwave Reaction, Orbit/Revolve, Magnet Pull/Repel, Glitch/Teleport, Fold/Unfold, Dissolve/Assemble and Wave Cascade) in the separate VIN Actions sidebar tab. Geometry Nodes motion presets remain in VIN Animate.


## Separate add-on: VIN Material Lab

Color palettes and procedural surface textures are kept in a standalone shader-node add-on so material work stays separate from shape generation and motion. Download [vin_material_lab.py](blender_addon/vin_material_lab.py) and follow [VIN_MATERIAL_LAB_README.md](blender_addon/VIN_MATERIAL_LAB_README.md). It includes Cyber Amber, Monochrome + Gold, Neon Prism, Titanium Sunset, Porcelain Champagne and Void Ember palettes, plus Noise/Color Ramp, Brushed Metal, Carbon Fiber, Hex Cells, Pitted/Porous and Circuit Line node patterns.
