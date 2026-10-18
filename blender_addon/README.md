# VIN Procedural Lab — Blender Add-on v0.6.0

A separate Blender add-on. It does not replace VIN 3D Studio and does not require an AI API.

## 1. Random Object / Procedural Shape Generator
Generates one editable procedural artifact at a time as a Blender mesh object. Random Object selects a family by Seed; New Variant increments the seed and generates another form.

### Hard-surface / cyberpunk families
- **Cyber Module** — stacked housings, inset front wells, dark cavity floors, perimeter rails, and grille slats.
- **Folded Ribbon** — twisting formed-metal ribbon with a grooved cross-section and raised edge lips.
- **Prism Reactor** — faceted core inside intersecting metal frames.
- **Faceted Totem** — stacked polygonal plates, angled fins, and micro-ribs.
- **Hex Armor** — a sci-fi shield/panel with dozens of raised hexagonal tiles, dark seams, a rigid perimeter, and metallic accents.
- **Circuit Core** — a layered circular electronic artifact with actual tube geometry for circuit traces, concentric raised rails, chips, and signal nodes.

### Abstract / organic families
- **Orbital Particle** — a crescent swarm of reflective spheres and tiny pearls, tied together by delicate filament struts.
- **Cellular Void** — a porous spherical exoskeleton with irregular openings, crossing struts, and bead-like joints.
- **Spike Bloom** — a dark mechanical-organic orb with many independent tapered spines and small reactor ports.
- **Future Sculpture**, **Orbital Cage**, **Organic Blob**, **Branching Form**, **Crystal Cluster**, and **Twisted Column** remain available.

The newer families have their own editable multi-material palettes. The geometry is generated algorithmically, so different seeds affect shape, spacing, density, proportions, and details instead of only changing the color. Some parts overlap in one mesh object as a procedural assembly; this is a starting point for art direction rather than guaranteed watertight manufacturing topology.

## 2. Sci-Fi Scene Builder
An optional environment generator separate from Random Object. It creates a layered reactor plaza, several towers, hard-surface panels, glowing trims, orbital rails, a camera, and lights. Use Generate Scene or Random Scene when a whole environment is wanted.

## 3. Animation Builder
Builds editable Geometry Nodes for Bob / Float, Continuous Spin, Scale Pulse, or Animated Twist. Preview by playing the timeline and inspect the generated graph in the Geometry Node Editor.

## Install / update
1. Open the add-on source file on GitHub and use Download raw file to get the Python file.
2. In Blender, go to Edit → Preferences → Add-ons, choose Install from Disk, select the Python file, and enable VIN Procedural Lab.
3. Press N in the 3D Viewport and open the VIN Lab tab.
4. For an existing install, disable/remove the previous add-on version before installing this one to avoid duplicate registrations. This does not change VIN 3D Studio.

## Notes
- This add-on uses procedural math and randomness, not an AI image-generation API.
- Meshes, materials, and modifiers remain editable in Blender.
- CI compiles the add-on and exercises each shape family, the scene generator, and the Geometry Nodes builders in background Blender. Visual styling should also be reviewed in the user's Blender session.
- Targets Blender 3.6+; some APIs vary by Blender version.