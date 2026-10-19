# VIN Motion Lab — Standalone Blender Add-on v0.8.1

VIN Motion Lab is a separate add-on from VIN Procedural Lab. It owns animation and Geometry Nodes workflows only; it does not replace, patch, or alter the procedural shape generator.

## Features

### Object Animation
Select one or more mesh/curve objects, choose a mode, and click **Build on Selected**. Every selected object receives its own Geometry Nodes group; phase is spread across the selection so the pieces do not move in sync. Use Reset to restore obvious starter values (Speed 1.0, Living Deform Strength 0.35, Breathing 0.18, Mask Threshold 0.30).
- Bob / Float — animated vertical offset
- Continuous Spin — rotates geometry over time
- Scale Pulse — rhythmic scaling
- Animated Twist — spatially twists mesh points over time
- **Living Entity** — subdivides the input surface, animates a 4D Noise field, maps it through an editable Color Ramp mask, displaces selected regions in noise directions and along surface normals, and adds a slower radial breathing cycle. Controls: Deform Strength, Organic Noise Scale, Breathing, Mask Threshold, and Surface Detail.
- **3D Drift** — a looping three-axis floating path; X, Y and Z use different frequencies and phase offsets.
- **Radial Pulse** — a travelling wave that moves vertices along radial directions; Wave Frequency controls ring spacing, and Wave Detail adds surface resolution.
- **Lattice Pulse** — a per-object 4D Noise / Color Ramp vibration that moves selected vertices along their surface normals; it works especially well on Alien Lattice's shell, triangular frame and bead layers.

For Living Entity, a mesh with enough geometry gives the best result. Surface Detail increases subdivision before deformation; start at 2, then try 3 for smoother motion. Very low-poly meshes otherwise cannot deform into soft shapes. The Color Ramp inside the Geometry Nodes graph can be edited to change which regions move.

The generated Geometry Nodes group is editable. Play the timeline to preview Scene Time-driven motion.

### Object Motion Actions — eight transform-keyframed presets

These presets live in the separate **VIN Actions** sidebar tab. Unlike the Geometry Nodes presets in VIN Animate, they insert regular transform keyframes on each selected object. Each object gets its own Action, with its own randomized seed/variation. Existing Geometry Nodes modifiers are left intact; existing location, rotation and scale animation channels on the assigned Action are replaced.

- **Wobble / Tumble** — smooth, uneven three-axis rotation; loops.
- **Shockwave Reaction** — each object kicks away from the center then settles at its original transform. Reaction start is staggered by distance; this is a one-shot action that holds after it finishes.
- **Orbit / Revolve** — actual object transforms follow a closed orbit around an optional anchor. If no anchor is assigned, the average position of selected objects is used.
- **Magnet Pull / Repel** — each object moves toward or away from the center, then returns; select Pull or Repel.
- **Glitch / Teleport** — discrete position/rotation jumps with constant key interpolation; loops.
- **Fold / Unfold** — parts rotate and shrink around their own origins, then open again. Use separate components/panels for the best result.
- **Dissolve / Assemble** — selected objects shrink and scatter, re-form at their original positions, then dissolve; objects are not physically fractured by this action.
- **Wave Cascade** — a looping wave phase is derived from each object's position along the selected X/Y/Z propagation axis; objects lift on Z and rock in sequence.

Controls: Motion Amount sets distance/rotation/amplitude depending on the selected preset; Speed changes cycle duration; Cycle Frames sets base timing; Motion Seed changes randomized directions/variation. Center / Anchor is available for shockwave, orbit and magnet actions. Leave it empty to use the average selected position. The operator starts from the current timeline frame.

Tips:
1. Select only the objects you want affected. For a collection of sci-fi parts, multi-select the parts in the Outliner.
2. If using Shockwave, Orbit or Magnet, optionally pick an anchor object.
3. Click **Apply to Selected** and play the timeline. Check the object's Action in the Dope Sheet to inspect keys.
4. Fold/Unfold and Dissolve/Assemble animate the selected objects themselves; they do not cut one joined mesh into separate panels or fragments.

### Surface Spawn / Individual Motion

This is separate from the quick Geometry Nodes instance scatter. It creates real, separately selectable object copies on the active mesh surface.

1. Put the source meshes in a dedicated collection. Each source should already be a separate object, not a single joined mesh containing disconnected pieces.
2. Select the target Plane/surface, choose the collection in **Spawn Source Collection**, then click **Spawn Separate Objects**.
3. The new objects appear in a collection named **VIN Motion · Surface Spawn**. Each spawned copy gets its own mesh datablock, animation modifier, Geometry Nodes group, random phase, speed and amount, plus staggered growth keyframes.
4. Choose **Random per Object** for mixed motion types or **Use Selected Motion** to use the current Animation preset for each copy.

Controls: Spawn Count, Seed, Min/Max Scale, Align to Surface, Speed/Amount Variation, Phase Spread, First Spawn Frame, Spawn Stagger and Growth Frames. To control one item, select it in the Outliner and adjust its **VIN Motion · Animation** modifier inputs, or edit its dedicated node group. Rerunning creates a new output collection rather than joining objects together.

The quick Scatter tool below remains available for lighter-weight instance-based layouts when individual object control is not needed.

### Surface Crawl / Per-Object Path

This creates ordinary transform keyframes on each selected object, not one shared Geometry Nodes animation. Each object gets a separately seeded random-walk route projected onto a target mesh using a BVH nearest-surface query.

1. Keep the target mesh (usually a Plane) separate from the moving objects.
2. Select the objects that should crawl, then set **Crawl Surface** to the target mesh.
3. Choose Path Steps, Frames per Step, Step Distance, Surface Offset, First Crawl Frame and Start Stagger.
4. Click **Animate Selected Along Surface** and play the timeline.

Each object's route uses its own random seed, has its own keyframes, and loops with a Cycles modifier. Optional Align to Surface aligns local Z to the sampled surface normal. Targets must be unparented in this version; the active target surface is not animated or modified. This is a procedural projected walk rather than a physics-based crawler, so sharp edges or disconnected surface islands can result in short pauses or jumps.

### Noise / Color Ramp Scatter
1. Keep the objects you want to scatter in a dedicated Blender Collection. Use the original generated source parts; they remain separate objects.
2. Add or select a mesh Plane and keep that Plane outside the source collection.
3. In the VIN Motion sidebar tab, choose the source collection and click Build Scatter Nodes.
4. Play the timeline. The graph uses Distribute Points on Faces, Collection Info, Instance on Points, 4D Noise, Color Ramp Alpha, a threshold comparison, and Set Position. It instances source objects with randomized orientation and scale; only the masked points move with the animated field.

Controls include Density, Noise Scale, Mask Threshold, Field Motion, Field Speed, Min/Max Scale, and Scatter Seed. Adjust the Color Ramp in the Geometry Node Editor to change the affected zones.

Note: scatter output uses Geometry Nodes instances, not separate scene objects. To edit source geometry, edit objects in the selected source collection. The original Plane and source objects are not destructively joined.

## Install
1. Download vin_motion_lab.py from this folder using GitHub's Download raw file action.
2. In Blender, open Edit → Preferences → Add-ons, choose Install from Disk, select vin_motion_lab.py, then enable VIN Motion Lab.
3. In the 3D Viewport, press N and select the VIN Motion tab.

Leave VIN Procedural Lab installed if you still use its shape generator. The two add-ons use different panel tabs, scene settings, operators, and modifier names.

## Compatibility
Targets Blender 3.6+. Geometry Nodes APIs vary somewhat between Blender releases. The repository runtime test exercises five animation graphs, including Living Entity, the instance-based scatter graph, Surface Spawn's separate objects and unique per-object node groups, and Surface Crawl's independent looping paths.


## Sidebar layout v0.5.0

The panel is split into four separate Viewport Sidebar tabs: VIN Animate, VIN Scatter, VIN Spawn and VIN Crawl. Use one tab at a time; each contains only its own controls.


### Lattice Pulse controls

Select one or more Alien Lattice layers or other meshes, choose **Lattice Pulse**, then use Strength, Lattice Noise Scale, Lattice Wave Frequency and Lattice Mask Threshold. Click **Build on Selected** to assign a separate Geometry Nodes graph and phase per object. Keep Strength modest (around 0.05–0.18 for thin lattice struts) to preserve the structural silhouette.


### Sidebar tabs v0.8.1

The Viewport Sidebar uses VIN Animate (Geometry Nodes motion), VIN Actions (real transform keyframes), VIN Scatter, VIN Spawn and VIN Crawl. Each Object Motion Action creates one independent Action per selected object.
