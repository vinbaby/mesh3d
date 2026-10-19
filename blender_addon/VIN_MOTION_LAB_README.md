# VIN Motion Lab — Standalone Blender Add-on v0.3.0

VIN Motion Lab is a separate add-on from VIN Procedural Lab. It owns animation and Geometry Nodes workflows only; it does not replace, patch, or alter the procedural shape generator.

## Features

### Object Animation
Select any mesh or curve object, choose one mode, and click Build Animation Nodes:
- Bob / Float — animated vertical offset
- Continuous Spin — rotates geometry over time
- Scale Pulse — rhythmic scaling
- Animated Twist — spatially twists mesh points over time
- **Living Entity** — subdivides the input surface, animates a 4D Noise field, maps it through an editable Color Ramp mask, displaces selected regions in noise directions and along surface normals, and adds a slower radial breathing cycle. Controls: Deform Strength, Organic Noise Scale, Breathing, Mask Threshold, and Surface Detail.

For Living Entity, a mesh with enough geometry gives the best result. Surface Detail increases subdivision before deformation; start at 2, then try 3 for smoother motion. Very low-poly meshes otherwise cannot deform into soft shapes. The Color Ramp inside the Geometry Nodes graph can be edited to change which regions move.

The generated Geometry Nodes group is editable. Play the timeline to preview Scene Time-driven motion.

### Surface Spawn / Individual Motion

This is separate from the quick Geometry Nodes instance scatter. It creates real, separately selectable object copies on the active mesh surface.

1. Put the source meshes in a dedicated collection. Each source should already be a separate object, not a single joined mesh containing disconnected pieces.
2. Select the target Plane/surface, choose the collection in **Spawn Source Collection**, then click **Spawn Separate Objects**.
3. The new objects appear in a collection named **VIN Motion · Surface Spawn**. Each spawned copy gets its own mesh datablock, animation modifier, Geometry Nodes group, random phase, speed and amount, plus staggered growth keyframes.
4. Choose **Random per Object** for mixed motion types or **Use Selected Motion** to use the current Animation preset for each copy.

Controls: Spawn Count, Seed, Min/Max Scale, Align to Surface, Speed/Amount Variation, Phase Spread, First Spawn Frame, Spawn Stagger and Growth Frames. To control one item, select it in the Outliner and adjust its **VIN Motion · Animation** modifier inputs, or edit its dedicated node group. Rerunning creates a new output collection rather than joining objects together.

The quick Scatter tool below remains available for lighter-weight instance-based layouts when individual object control is not needed.

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
Targets Blender 3.6+. Geometry Nodes APIs vary somewhat between Blender releases. The repository runtime test exercises five animation graphs, including Living Entity, the instance-based scatter graph, and Surface Spawn's separate objects, unique per-object node groups and growth keyframes.
