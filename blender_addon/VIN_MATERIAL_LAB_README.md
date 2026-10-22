# VIN Material Lab — Standalone Blender Add-on v0.3.0

VIN Material Lab is a separate Blender add-on for **shader materials, color palettes, and procedural surface textures**. It does not modify the shape generator or the motion tools. It supports Blender 3.6+ and uses Blender's built-in Shader Editor nodes; no external services or libraries are required.

## Install

1. Download the file named vin_material_lab.py from this folder.
2. In Blender, open Edit → Preferences → Add-ons → Install (or Get Extensions / Install from Disk, depending on Blender version) and choose the downloaded file.
3. Enable **VIN Material Lab**.
4. In the 3D Viewport, press N and open the **VIN Material** tab.

Install it alongside VIN Procedural Lab and VIN Motion Lab. Each add-on has its own file and sidebar tab.

## Use

1. Choose a **Color Palette**, **Surface Finish**, and **Texture Pattern**.
2. Tune Seed, Texture Scale, Texture Detail, Ramp Contrast, Accent Strength, Bump Strength, Bump Distance, and optional Glow Strength.
3. Click **Create Material** to create a reusable material datablock and editable shader-node graph.
4. Click **Preview Sphere** to create or update the dedicated preview sphere with the most recently generated material. Switch the viewport to **Material Preview** to inspect it.
5. Select one or more mesh, curve, font, or surface objects and click **Apply Last Material** to share the same material across them.
6. Use **Generate + Apply Unique** when each selected object should get its own independent shader material.
7. Open the **Shader Editor** and inspect or edit the VINMAT nodes manually.

Applying a shared material replaces selected objects' active material-slot assignments with that material. The preview sphere is a separate object named **VINMAT Preview Sphere** and is not merged with your target model.

Applying a material replaces the selected objects' active material-slot assignments with the new material. Old material datablocks remain in the .blend unless the user removes them. Mesh data is copied before material assignment if it is shared between objects.

## Color palettes

- **Cyber Amber** — graphite, titanium blue/cyan, orange signal accents.
- **Monochrome + Gold** — black, silver, and champagne gold.
- **Neon Prism** — deep navy, cyan, magenta, and violet.
- **Titanium Sunset** — cold metallic blue and orange highlights.
- **Porcelain Champagne** — ivory ceramic with warm champagne metal.
- **Void Ember** — black/graphite with ember-orange highlights.
- **Earth & Natural** — wood, leather, clay, sand and natural pigments.
- **Soft Pastel** — gentle colors for toys, characters, props and interiors.
- **Ocean & Coast** — ocean blue, sea-glass turquoise, foam and warm sand.
- **Forest & Moss** — greens, moss and natural amber.
- **Candy Pop** — playful saturated colors for stylized assets.
- **Clay / Terracotta** — warm clay, brick, fired ceramic and earthy orange.

## Surface finish presets

- **Titanium / Black Chrome / Carbon Composite** — metal and engineered surfaces.
- **Ceramic / Porcelain / Energy Ceramic** — glazed, satin or glossy ceramic.
- **Clear Glass** — high transmission and sharp reflections.
- **Frosted Glass** — translucent rough glass with soft highlights.
- **Clear Plastic** — tinted acrylic/polycarbonate with transmission and a little coat.
- **Matte Plastic** — opaque, non-metallic plastic with broad highlights.
- **Rubber** — very rough, low-reflection surface.
- **Fabric / Cloth** — high roughness and a sheen response.
- **Leather** — semi-matte hide with modest sheen.
- **Wood** — non-metallic satin finish intended for wood-grain texture.
- **Stone / Concrete** — rough mineral surface.
- **Paper / Card** — dry matte paper, cardboard or cardstock.
- **Alien Porous** — rough organic finish for experimental materials.

Transparent finishes configure transmission and available viewport transparency properties. For physically convincing glass, use **Cycles** or configure the lighting/refraction in Eevee for your Blender version. The shader alone cannot create solid thickness, convincing refraction detail or a background to reflect.

## Texture node patterns

| Pattern | Nodes/effect |
|---|---|
| Clean Variation | Broad noise variation with restrained bump |
| Brushed Metal | Directional Wave Texture lines with fine relief |
| Noise / Color Ramp | Noise Texture to Color Ramp, with Bump |
| Carbon Fiber | Crossed Wave bands combined into a woven pattern |
| Hex / Cell Pattern | Voronoi cell boundaries and surface relief |
| Pitted / Porous | Mottled noise plus Voronoi crater-like relief |
| Circuit Lines | Distorted directional tracks driven by Noise |
| Fabric Weave | Two crossed Wave fields for fibre crossings |
| Wood Grain | Distorted Wave bands guided by Noise for flowing grain |
| Speckled Stone | Voronoi mineral flecks blended with broad Noise |
| Micro Scratches | Fine directional lines broken up by Noise |
| Water Droplets | Voronoi cell field for droplet-like relief |

All patterns use native shader nodes and remain editable. Texture Scale changes pattern size; Texture Detail controls noise detail where applicable; Ramp Contrast changes how abruptly colors transition; Accent Strength affects the accent portion of the ramp; Bump Strength and Distance control perceived relief. Glow Strength is optional and defaults to 0.

### Suggested starting combinations

- **Dark cyberpunk armor:** Cyber Amber + Black Chrome + Brushed Metal or Circuit Lines.
- **White ceramic alien sculpture:** Porcelain Champagne + Ceramic / Porcelain + Pitted / Porous.
- **Neon geometric sculpture:** Neon Prism + Energy Ceramic + Noise / Color Ramp; set Glow Strength between 0.2 and 1.0.
- **Black and gold lattice:** Monochrome + Gold + Titanium + Hex / Cell Pattern.
- **Clear glass object:** Ocean & Coast + Clear Glass + Clean Variation; use a lit environment and inspect in Cycles.
- **Soft toy or stylized prop:** Soft Pastel + Matte Plastic + Clean Variation.
- **Cloth or fabric accessory:** Earth & Natural + Fabric / Cloth + Fabric Weave.
- **Wooden prop or furniture:** Earth & Natural + Wood + Wood Grain.
- **Stone, concrete or rock:** Forest & Moss or Earth & Natural + Stone + Speckled Stone.
- **Leather gear:** Earth & Natural + Leather + Micro Scratches.
- **Water droplets on a surface:** Ocean & Coast + Clear Glass or Clear Plastic + Water Droplets.

## Notes

This add-on creates procedural shader materials, not a baked texture image. The appearance is evaluated by Blender's material/render system; use Material Preview or Rendered viewport shading to see the full shader result. Geometry is not modified. Motion modifiers and transform keyframes are not changed.
