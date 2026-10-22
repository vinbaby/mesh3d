# VIN Procedural Lab — Blender Add-on v0.8.1

A separate Blender add-on. It does not replace VIN 3D Studio and does not require an AI API.

## 1. Random Object / Procedural Shape Generator
Generates one editable procedural artifact at a time. Random Object chooses a family by Seed; New Variant increments the seed and generates another form. **Auto Separate Components** is enabled by default: disconnected islands created inside the generated mesh are split into individual selectable Blender objects and each part gets an origin centered on its own bounds. The Separate Existing Mesh button can split an older combined object.

Shape families include Twisted Column, Orbital Cage, Organic Blob, Crystal Cluster, Branching Form, Future Sculpture, Cyber Module, Folded Ribbon, Prism Reactor, Faceted Totem, Hex Armor, Circuit Core, Orbital Particle, Cellular Void, Spike Bloom and Alien Lattice.

### Alien Lattice — 3 editable layers

Choose **Alien Lattice** and click **Generate Object**. It creates a seeded organic C-loop with three selectable objects:
- **Shell** — broken porcelain-like surface patches with an seed-driven distribution of holes and shell thickness.
- **Triangular Frame** — dark space-frame struts, circumferential supports and alternating diagonal braces.
- **Metal Beads** — randomized metallic bead clusters concentrated around several seed-selected hotspots.

The generator intentionally keeps three organized layers instead of auto-separating every strut and pearl into hundreds of tiny Outliner objects. Select all three layers and use VIN Motion Lab's **Lattice Pulse** or apply different motion presets to each layer. New Seed values alter the loop shape, shell gaps, lattice omissions/brace directions and bead clusters.

## 2. Noise / Color Ramp Scatter
1. Generate your artifact(s) with Auto Separate Components enabled.
2. Put the source objects you want to scatter into a dedicated Blender Collection. Keep the active Plane out of this source collection.
3. Select a mesh Plane, choose that collection in the Source Collection field, then click **Scatter + Animate**.
4. The Geometry Nodes graph uses Distribute Points on Faces, Collection Info and Instance on Points. An animated 4D Noise Texture feeds an editable Color Ramp and a Mask Threshold; only selected scatter points are moved by the animated field. The Color Ramp remains editable in the Geometry Node Editor.

Controls include Density, Noise Scale, Mask Threshold, Field Motion, Field Speed, Min/Max Scale and Scatter Seed. Lower/higher the threshold to change how many points are affected; edit the Color Ramp to shape the affected zones. Play the timeline to see the noise field animate.

Note: scattered items are Geometry Nodes instances, so the procedural result is controlled through the active Plane and its node group. To move a source asset globally, edit the source object in the chosen collection. Auto Separate Components is for selecting/editing the generated source parts before scattering.

## 3. Sci-Fi Scene Builder
An optional whole-environment generator separate from Random Object. It creates a layered reactor plaza, several towers, hard-surface panels, glowing trims, orbital rails, a camera and lights. Use Generate Scene or Random Scene when a whole environment is wanted.

## Animation and noise-mask nodes moved to VIN Motion Lab
Object motion presets and Noise/Color Ramp scatter now have a dedicated, independent add-on: `vin_motion_lab.py`. See [VIN Motion Lab instructions](VIN_MOTION_LAB_README.md). The original VIN Procedural Lab panel stays focused on procedural objects and optional sci-fi scenes.

## Install / update
1. Open the add-on source file on GitHub and use **Download raw file** to get `vin_procedural_lab.py`.
2. In Blender, go to Edit → Preferences → Add-ons, choose Install from Disk, select the Python file, and enable VIN Procedural Lab.
3. Press N in the 3D Viewport and open the VIN Lab tab.
4. For an existing install, disable/remove the older add-on version before installing this one to avoid duplicate registrations. This does not change VIN 3D Studio.

## Notes
- Geometry and node graphs are procedural and editable in Blender; no AI image-generation API is used.
- Blender 3.6+ is targeted, but Geometry Nodes APIs may vary between Blender versions.
- The CI runtime test exercises all shape builders, component separation, the Noise/Color Ramp Scatter graph and the scene generator. Review visual motion/shading in your own Blender session as well.


## Separate material and texture tool

Color palettes, material finishes and shader texture nodes live in the independent VIN Material Lab add-on: see [VIN_MATERIAL_LAB_README.md](VIN_MATERIAL_LAB_README.md) and [vin_material_lab.py](vin_material_lab.py). They are intentionally not embedded in the procedural shape generator.


## Separate general-purpose materials and textures

VIN Material Lab v0.3.0 is a standalone add-on for material work: 12 color palettes, 16 surface finishes (including glass, clear/matte plastic, rubber, fabric, leather, wood, stone and paper), and 12 procedural texture node patterns. It remains separate from the shape generator. See [VIN_MATERIAL_LAB_README.md](VIN_MATERIAL_LAB_README.md) and [vin_material_lab.py](vin_material_lab.py).
