# VIN Procedural Lab — Blender Add-on v0.1.0

This is a separate Blender add-on. It does not replace VIN 3D Studio and does not require an AI API.

## Modules

### 1. Procedural Shape Generator
Creates real editable Blender mesh objects using deterministic math and seeded randomness:
- Random Shape
- Twisted Column
- Orbital Cage
- Organic Blob
- Crystal Cluster
- Branching Form

Controls: seed, detail, size, twist, and branch depth. Use the same seed and settings to reproduce a shape; choose **New Variant** to change the seed.

### 2. Animation Builder
Builds an editable Geometry Nodes node group and adds it as a Geometry Nodes modifier to the active object:
- **Bob / Float** — Scene Time drives a sine wave connected to Set Position offset
- **Continuous Spin** — Scene Time drives Transform Geometry rotation
- **Scale Pulse** — Scene Time drives a uniform scale pulse
- **Animated Twist** — position fields and trigonometric nodes twist points around Z over time

The generated groups remain editable in Blender's Geometry Node Editor. Speed and mode-relevant amount controls are exposed on the modifier.

## Install
1. Download `vin_procedural_lab.py` from this folder using GitHub's **Download raw file** action.
2. Open Blender and go to **Edit → Preferences → Add-ons** (wording may vary by Blender version).
3. Choose **Install from Disk**, select the downloaded `.py` file, then enable **VIN Procedural Lab**.
4. In the 3D Viewport, press **N** to open the sidebar and choose the **VIN Lab** tab.

## Use
1. In **Procedural Shape Generator**, choose a family or leave Random Shape selected, adjust parameters, and click **Generate Shape**.
2. Select the generated object (or any supported object) that should animate.
3. In **Animation Builder**, choose the motion, adjust Speed and the relevant Amount, then click **Build Geometry Nodes**.
4. Open the Geometry Node Editor to inspect and further edit the generated graph. Use the timeline/play controls to see the animation.

## Notes and limitations
- Shapes are algorithmic procedural geometry, not AI-generated interpretations of a prompt.
- Animation uses Scene Time, so preview it by playing the timeline.
- The first version intentionally includes five shape families and four animation templates. It does not promise production-ready topology for every downstream use.
- This repository's CI checks Python syntax and structural smoke tests. A Blender GUI/runtime test still needs to be performed in Blender; no claim of direct GUI testing is made here.
- Requires Blender 3.6 or newer in principle; Geometry Nodes interface APIs vary across Blender versions, so report the exact Blender version if runtime node creation fails.
