# VIN Lighting Lab — Standalone Blender Add-on v0.1.0

VIN Lighting Lab creates real Blender Light objects and an optional camera in its own collection. It is separate from VIN Procedural Lab, VIN Motion Lab, and VIN Material Lab.

## Install

1. Download the file named vin_lighting_lab.py from this folder.
2. In Blender 3.6, open Edit → Preferences → Add-ons → Install and choose the .py file.
3. Enable VIN Lighting Lab.
4. In the 3D Viewport, press N and open VIN Lighting.

## Basic workflow

1. Select the mesh object or collection of parts to light. If several pieces belong to one assembly, select all of them together.
2. Choose a Lighting Preset.
3. Adjust Light Power and Light Size. Background Tint and World Strength update with the selected preset and remain editable.
4. Keep Create / Aim Camera enabled for a ready-to-render camera, or turn it off if you already have your own camera.
5. Keep Enable Fog Glow on to insert the add-on's named Fog Glow node in the Compositor, or turn it off for a clean render.
6. Click Build Lighting Rig.
7. Use Rendered viewport shading or press F12 to evaluate the scene lighting. Material Preview can use its own studio HDRI unless Scene Lights and Scene World are enabled in the viewport shading popover.

The rig objects are grouped in the VIN Lighting Rig collection. Rebuilding replaces only objects tagged as created by VIN Lighting Lab; untagged user objects inside that collection are preserved. Existing Geometry Nodes, meshes, and material node trees are not changed.

## Presets

- Studio Product — key, fill, rim and top sources for hard-surface product renders.
- Softbox / Soft Light — larger sources with gentler gradients and shadows.
- Glass / Crystal — slim strip lights and edge highlights that reveal transparent, reflective surfaces.
- Portrait / Character — beauty key, soft fill and a warm rim.
- Nature / Organic — warm key light, green fill and organic color separation.
- Sci-Fi Reactor — cold key, cyan fill, red rim, amber top light and red/amber point lights for a glowing core.

## Controls

- Light Power scales energy for all generated lights.
- Light Size scales Area light sizes and Point light softness.
- Background Tint / World Strength set the world shader background.
- Create / Aim Camera creates a camera looking at the selected subject's bounding center and assigns it as the scene camera.
- Camera Lens controls the new camera's focal length.
- Enable Fog Glow / Glow Threshold inserts an optional Fog Glow node in the compositor.
- Remove Rig removes only generated rig objects and removes the add-on-owned Fog Glow node.
- Restore World restores world background values and the camera recorded before the first VIN rig was built, when still available.

## Practical notes

- Clear glass needs appropriate material settings and strong environment/reflection shapes. A light rig helps reveal its edges, but lighting alone does not turn an opaque material into glass.
- Emission materials often need scene lights nearby to illuminate surrounding objects; emission color by itself is not a substitute for a complete lighting setup.
- Fog Glow is a compositor post effect, best evaluated in Rendered mode or a final render. It does not add physical light energy to the scene.
- The add-on keeps the current render engine and output settings; it does not switch the file between Eevee and Cycles.
- For a fast first look, try Studio Product on a metallic object, Glass / Crystal on a clear material, and Sci-Fi Reactor on a red or cyan emissive core.
