# VIN Material Lab — Standalone Blender Add-on v0.1.0

VIN Material Lab is a separate Blender add-on for **shader materials, color palettes, and procedural surface textures**. It does not modify the shape generator or the motion tools. It supports Blender 3.6+ and uses Blender's built-in Shader Editor nodes; no external services or libraries are required.

## Install

1. Download the file named vin_material_lab.py from this folder.
2. In Blender, open Edit → Preferences → Add-ons → Install (or Get Extensions / Install from Disk, depending on Blender version) and choose the downloaded file.
3. Enable **VIN Material Lab**.
4. In the 3D Viewport, press N and open the **VIN Material** tab.

Install it alongside VIN Procedural Lab and VIN Motion Lab. Each add-on has its own file and sidebar tab.

## Use

1. Select one or more mesh, curve, font, or surface objects.
2. Choose a **Color Palette**, **Surface Finish**, and **Texture Pattern**.
3. Tune Seed, Texture Scale, Texture Detail, Ramp Contrast, Accent Strength, Bump Strength, Bump Distance, and optional Glow Strength.
4. Click **Apply to Selected**. The add-on creates a separate material and editable shader-node graph for each selected object.
5. Click **Create Nodes** to create a standalone material datablock without assigning it to an object.
6. Open the **Shader Editor** and inspect the VINMAT nodes to edit the graph manually.

Applying a material replaces the selected objects' active material-slot assignments with the new material. Old material datablocks remain in the .blend unless the user removes them. Mesh data is copied before material assignment if it is shared between objects.

## Color palettes

- **Cyber Amber** — graphite, titanium blue/cyan, orange signal accents.
- **Monochrome + Gold** — black, silver, and champagne gold.
- **Neon Prism** — deep navy, cyan, magenta, and violet.
- **Titanium Sunset** — cold metallic blue and orange highlights.
- **Porcelain Champagne** — ivory ceramic with warm champagne metal.
- **Void Ember** — black/graphite with ember-orange highlights.

## Surface finish presets

- **Titanium** — machined metallic finish.
- **Black Chrome** — very metallic and glossy.
- **Ceramic / Porcelain** — low metallic, smooth surface.
- **Carbon Composite** — semi-metallic dark composite.
- **Alien Porous** — softer organic-looking surface.
- **Energy Ceramic** — glossy finish for sci-fi energy parts.

## Texture node patterns

| Pattern | Nodes/effect |
|---|---|
| Clean Variation | Broad noise variation with restrained bump |
| Brushed Metal | Directional Wave Texture lines with fine relief |
| Noise / Color Ramp | Noise Texture → Color Ramp, with Bump |
| Carbon Fiber | Crossed Wave Texture bands combined into a woven pattern |
| Hex / Cell Pattern | Voronoi cell borders and relief |
| Pitted / Porous | Mottled noise texture with relief |
| Circuit Lines | Distorted Wave Texture tracks driven by Noise |

All patterns use native shader nodes and remain editable. Texture Scale changes the size of the pattern; Texture Detail affects noise detail; Ramp Contrast changes how abruptly colors transition; Accent Strength controls how far the accent stop moves into the ramp; Bump parameters control the perceived relief. Glow Strength is optional and defaults to 0.

### Suggested starting combinations

- **Dark cyberpunk armor:** Cyber Amber + Black Chrome + Brushed Metal or Circuit Lines.
- **White ceramic alien sculpture:** Porcelain Champagne + Ceramic / Porcelain + Pitted / Porous.
- **Neon geometric sculpture:** Neon Prism + Energy Ceramic + Noise / Color Ramp; set Glow Strength between 0.2 and 1.0.
- **Black and gold lattice:** Monochrome + Gold + Titanium + Hex / Cell Pattern.
- **Carbon sci-fi shell:** Void Ember + Carbon Composite + Carbon Fiber.

## Notes

This add-on creates procedural shader materials, not a baked texture image. The appearance is evaluated by Blender's material/render system; use Material Preview or Rendered viewport shading to see the full shader result. Geometry is not modified. Motion modifiers and transform keyframes are not changed.
