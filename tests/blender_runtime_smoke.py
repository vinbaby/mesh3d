"""Executed inside Blender with: blender --background --factory-startup --python tests/blender_runtime_smoke.py"""

import importlib.util
import sys
from pathlib import Path

import bpy


def main() -> None:
    addon_path = Path(__file__).parents[1] / "blender_addon" / "vin_procedural_lab.py"
    spec = importlib.util.spec_from_file_location("vin_procedural_lab", addon_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load VIN Procedural Lab add-on")
    addon = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = addon
    spec.loader.exec_module(addon)
    addon.register()

    settings = bpy.context.scene.vinlab_settings
    settings.seed = 12345
    settings.detail = 12
    settings.size = 1.5
    settings.branch_depth = 2
    settings.twist = 2.6

    generated = []
    shape_types = (
        "TWISTED_COLUMN",
        "ORBIT_CAGE",
        "ORGANIC_BLOB",
        "CRYSTAL_CLUSTER",
        "BRANCHING_FORM",
        "FUTURE_SCULPTURE",
    )
    for shape_type in shape_types:
        settings.shape_type = shape_type
        result = bpy.ops.vinlab.generate_shape()
        if "FINISHED" not in result:
            raise AssertionError(f"Shape generator failed for {shape_type}: {result}")
        obj = bpy.context.view_layer.objects.active
        if obj is None or obj.type != "MESH":
            raise AssertionError(f"{shape_type} did not create an active mesh object")
        if len(obj.data.vertices) == 0 or len(obj.data.polygons) == 0:
            raise AssertionError(f"{shape_type} created an empty mesh")
        generated.append(obj)
        print(f"[OK] {shape_type}: {len(obj.data.vertices)} vertices, {len(obj.data.polygons)} polygons")

    target = generated[0]
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target

    for animation_type in ("BOB", "SPIN", "PULSE", "TWIST"):
        settings.animation_type = animation_type
        settings.animation_speed = 1.25
        settings.animation_amount = 0.35
        result = bpy.ops.vinlab.build_animation()
        if "FINISHED" not in result:
            raise AssertionError(f"Node builder failed for {animation_type}: {result}")
        modifier = target.modifiers.get("VINLAB Animation")
        if modifier is None or modifier.type != "NODES" or modifier.node_group is None:
            raise AssertionError(f"{animation_type} did not create a Geometry Nodes modifier")
        node_group = modifier.node_group
        if len(node_group.nodes) < 4 or len(node_group.links) < 3:
            raise AssertionError(f"{animation_type} generated an incomplete node graph")
        bpy.context.view_layer.update()
        print(f"[OK] {animation_type}: {len(node_group.nodes)} nodes, {len(node_group.links)} links")

    print("VIN Procedural Lab Blender runtime smoke test passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"VIN Procedural Lab Blender runtime smoke test failed: {exc}", file=sys.stderr)
        raise
