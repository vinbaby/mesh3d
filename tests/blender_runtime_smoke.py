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
        "CYBER_MODULE",
        "FOLDED_RIBBON",
        "PRISM_REACTOR",
        "FACETED_TOTEM",
        "HEX_ARMOR",
        "CIRCUIT_CORE",
        "ORBITAL_PARTICLE",
        "CELLULAR_VOID",
        "SPIKE_BLOOM",
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
        selected_parts = [
            part for part in bpy.context.selected_objects
            if part.type == "MESH" and part.get("vinlab_shape_type") == shape_type
        ]
        if settings.separate_parts and shape_type in ("HEX_ARMOR", "CIRCUIT_CORE", "ORBITAL_PARTICLE", "CELLULAR_VOID", "SPIKE_BLOOM") and len(selected_parts) < 2:
            raise AssertionError(f"{shape_type} was not split into independently selectable components")
        print(f"[OK] {shape_type}: {len(obj.data.vertices)} vertices, {len(obj.data.polygons)} polygons, {len(selected_parts) or 1} selected part(s)")

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


    # Exercise the Plane scatter graph using a dedicated source collection.
    source_collection = bpy.data.collections.new("VINLAB Test Scatter Sources")
    bpy.context.scene.collection.children.link(source_collection)
    cube_mesh = bpy.data.meshes.new("Scatter Test Cube Mesh")
    cube_mesh.from_pydata(
        [(-0.5,-0.5,-0.5),(0.5,-0.5,-0.5),(0.5,0.5,-0.5),(-0.5,0.5,-0.5),
         (-0.5,-0.5,0.5),(0.5,-0.5,0.5),(0.5,0.5,0.5),(-0.5,0.5,0.5)],
        [],
        [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],
    )
    cube_mesh.update()
    source_cube = bpy.data.objects.new("Scatter Test Cube", cube_mesh)
    source_collection.objects.link(source_cube)
    sphere_mesh = bpy.data.meshes.new("Scatter Test Sphere Mesh")
    sphere_mesh.from_pydata(
        [(0,0,1),(1,0,0),(0,1,0),(-1,0,0),(0,-1,0),(0,0,-1)],
        [],
        [(0,2,1),(0,3,2),(0,4,3),(0,1,4),(5,1,2),(5,2,3),(5,3,4),(5,4,1)],
    )
    sphere_mesh.update()
    source_sphere = bpy.data.objects.new("Scatter Test Sphere", sphere_mesh)
    source_collection.objects.link(source_sphere)

    plane_mesh = bpy.data.meshes.new("Scatter Test Plane Mesh")
    plane_mesh.from_pydata([(-5,-5,0),(5,-5,0),(5,5,0),(-5,5,0)], [], [(0,1,2,3)])
    plane_mesh.update()
    plane = bpy.data.objects.new("Scatter Test Plane", plane_mesh)
    bpy.context.scene.collection.objects.link(plane)
    settings.scatter_collection = source_collection
    settings.scatter_density = 1.5
    settings.scatter_noise_scale = 1.4
    settings.scatter_field_strength = 0.4
    settings.scatter_speed = 1.1
    settings.scatter_threshold = 0.52
    settings.scatter_min_scale = 0.6
    settings.scatter_max_scale = 1.3
    settings.scatter_seed = 37
    for selected in bpy.context.selected_objects:
        selected.select_set(False)
    plane.select_set(True)
    bpy.context.view_layer.objects.active = plane
    scatter_result = bpy.ops.vinlab.build_field_scatter()
    if "FINISHED" not in scatter_result:
        raise AssertionError(f"Noise/Color Ramp scatter builder failed: {scatter_result}")
    scatter_modifier = plane.modifiers.get("VINLAB Noise Scatter")
    if scatter_modifier is None or scatter_modifier.node_group is None:
        raise AssertionError("Plane does not have a Noise Scatter Geometry Nodes modifier")
    scatter_nodes = {node.bl_idname for node in scatter_modifier.node_group.nodes}
    required_nodes = {
        "GeometryNodeDistributePointsOnFaces",
        "GeometryNodeCollectionInfo",
        "GeometryNodeInstanceOnPoints",
        "GeometryNodeSetPosition",
        "ShaderNodeTexNoise",
        "ShaderNodeValToRGB",
    }
    if not required_nodes.issubset(scatter_nodes):
        raise AssertionError(f"Noise Scatter node graph is missing required nodes: {required_nodes - scatter_nodes}")
    if len(scatter_modifier.node_group.links) < 16:
        raise AssertionError("Noise Scatter node graph is missing required links")
    print(f"[OK] Noise / Color Ramp Scatter: {len(scatter_nodes)} node types, {len(scatter_modifier.node_group.links)} links")

    settings.seed = 24680
    scene_result = bpy.ops.vinlab.generate_scifi_scene()
    if "FINISHED" not in scene_result:
        raise AssertionError(f"Sci-Fi scene builder failed: {scene_result}")
    collection_name = bpy.context.scene.get("vinlab_scifi_scene_collection")
    scene_collection = bpy.data.collections.get(collection_name) if collection_name else None
    if scene_collection is None:
        raise AssertionError("Sci-Fi scene collection was not registered on the scene")
    if len(scene_collection.objects) < 50:
        raise AssertionError(f"Sci-Fi scene has too few generated objects: {len(scene_collection.objects)}")
    if bpy.context.scene.camera is None:
        raise AssertionError("Sci-Fi scene did not create a camera")
    if not any(obj.type == "LIGHT" for obj in scene_collection.objects):
        raise AssertionError("Sci-Fi scene did not create any lights")
    if not any(obj.type == "MESH" for obj in scene_collection.objects):
        raise AssertionError("Sci-Fi scene did not create any mesh assets")
    print(f"[OK] Sci-Fi scene: {len(scene_collection.objects)} objects, camera and lights created")

    print("VIN Procedural Lab Blender runtime smoke test passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"VIN Procedural Lab Blender runtime smoke test failed: {exc}", file=sys.stderr)
        raise
