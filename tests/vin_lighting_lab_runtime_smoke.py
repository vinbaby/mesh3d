"""Headless Blender smoke test for the standalone VIN Lighting Lab add-on."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import bpy


def main() -> None:
    addon_path = Path(__file__).parents[1] / "blender_addon" / "vin_lighting_lab.py"
    spec = importlib.util.spec_from_file_location("vin_lighting_lab", addon_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load VIN Lighting Lab")
    addon = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = addon
    spec.loader.exec_module(addon)
    addon.register()

    scene = bpy.context.scene
    original_world = scene.world
    if original_world is not None:
        original_world.use_nodes = True
        original_background = original_world.node_tree.nodes.get("Background")
        if original_background is not None:
            original_background.inputs["Color"].default_value = (0.12, 0.14, 0.18, 1.0)
            original_background.inputs["Strength"].default_value = 0.65

    camera_data = bpy.data.cameras.new("VIN Lighting Test Original Camera Data")
    original_camera = bpy.data.objects.new("VIN Lighting Test Original Camera", camera_data)
    scene.collection.objects.link(original_camera)
    original_camera.location = (0.0, -8.0, 3.0)
    scene.camera = original_camera

    mesh = bpy.data.meshes.new("VIN Lighting Test Subject Mesh")
    mesh.from_pydata(
        [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
         (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)],
        [],
        [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],
    )
    mesh.update()
    cube = bpy.data.objects.new("VIN Lighting Test Subject", mesh)
    scene.collection.objects.link(cube)
    cube.select_set(True)
    bpy.context.view_layer.objects.active = cube

    settings = scene.vinlight_settings
    settings.power_scale = 0.65
    settings.light_size_scale = 1.0
    settings.create_camera = True
    settings.enable_glow = True
    settings.glow_threshold = 1.2

    collection = None
    manual_object = None
    expected_presets = {
        "STUDIO_PRODUCT": 4,
        "SOFTBOX": 3,
        "GLASS": 5,
        "PORTRAIT": 3,
        "NATURE": 3,
        "SCI_FI_REACTOR": 6,
    }
    for preset, expected_lights in expected_presets.items():
        settings.preset = preset
        result = bpy.ops.vinlight.build_rig()
        if "FINISHED" not in result:
            raise AssertionError(f"Lighting preset {preset} failed to build: {result}")
        collection = bpy.data.collections.get(addon.RIG_COLLECTION_NAME)
        if collection is None:
            raise AssertionError(f"{preset}: no dedicated lighting collection")
        generated = [obj for obj in collection.objects if obj.get("vinlighting_generated", False)]
        lights = [obj for obj in generated if obj.type == "LIGHT"]
        cameras = [obj for obj in generated if obj.type == "CAMERA"]
        if len(lights) != expected_lights:
            raise AssertionError(f"{preset}: expected {expected_lights} lights, got {len(lights)}")
        if len(cameras) != 1:
            raise AssertionError(f"{preset}: expected one generated camera, got {len(cameras)}")
        if scene.camera != cameras[0]:
            raise AssertionError(f"{preset}: generated camera was not assigned to the scene")
        if scene.world is None or not scene.world.use_nodes:
            raise AssertionError(f"{preset}: world shader nodes were not configured")
        background = scene.world.node_tree.nodes.get("Background")
        if background is None:
            raise AssertionError(f"{preset}: no World Background shader")
        if scene.world.get("vinlighting_preset") != preset:
            raise AssertionError(f"{preset}: world metadata does not match the preset")
        if scene.node_tree is None or scene.node_tree.nodes.get(addon.GLARE_NODE_NAME) is None:
            raise AssertionError(f"{preset}: owned Fog Glow compositor node is missing")
        compositor = next((node for node in scene.node_tree.nodes if node.bl_idname == "CompositorNodeComposite"), None)
        if compositor is None or not compositor.inputs["Image"].is_linked:
            raise AssertionError(f"{preset}: composite output is not connected")
        if manual_object is None:
            manual_mesh = bpy.data.meshes.new("User Object in Rig Collection Mesh")
            manual_object = bpy.data.objects.new("User Object in Rig Collection", manual_mesh)
            collection.objects.link(manual_object)
        elif manual_object.name not in collection.objects:
            raise AssertionError("Rebuilding the rig deleted a user object in the lighting collection")
        print(f"[OK] Lighting preset {preset}: {len(lights)} lights, camera, world and glow")

    settings.enable_glow = False
    settings.preset = "STUDIO_PRODUCT"
    result = bpy.ops.vinlight.build_rig()
    if "FINISHED" not in result:
        raise AssertionError(f"Rebuild without glow failed: {result}")
    if scene.node_tree.nodes.get(addon.GLARE_NODE_NAME) is not None:
        raise AssertionError("Fog Glow node should be removed when disabled")

    result = bpy.ops.vinlight.remove_rig()
    if "FINISHED" not in result:
        raise AssertionError(f"Remove Lighting Rig failed: {result}")
    remaining_generated = [
        obj for obj in bpy.data.objects if obj.get("vinlighting_generated", False)
    ]
    if remaining_generated:
        raise AssertionError(f"Remove Rig left generated objects: {[obj.name for obj in remaining_generated]}")
    if scene.camera != original_camera:
        raise AssertionError("Remove Rig did not restore the original camera")
    if manual_object.name not in bpy.data.objects:
        raise AssertionError("Remove Rig deleted the manual object")
    print("[OK] Remove/Restore: user objects preserved and original camera restored")

    result = bpy.ops.vinlight.restore_scene()
    if "FINISHED" not in result:
        raise AssertionError(f"Restore World failed: {result}")
    print("VIN Lighting Lab Blender runtime smoke test passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"VIN Lighting Lab runtime smoke test failed: {exc}", file=sys.stderr)
        raise
