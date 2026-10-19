"""Runtime smoke test for standalone VIN Motion Lab, run inside Blender."""
import importlib.util
import sys
from pathlib import Path

import bpy


def main() -> None:
    addon_path = Path(__file__).parents[1] / "blender_addon" / "vin_motion_lab.py"
    spec = importlib.util.spec_from_file_location("vin_motion_lab", addon_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load standalone VIN Motion Lab add-on")
    addon = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = addon
    spec.loader.exec_module(addon)
    addon.register()

    settings = bpy.context.scene.vinmotion_settings
    settings.animation_speed = 1.15
    settings.animation_amount = 0.35

    mesh = bpy.data.meshes.new("VIN Motion Test Cube Mesh")
    mesh.from_pydata(
        [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
         (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)],
        [],
        [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],
    )
    mesh.update()
    target = bpy.data.objects.new("VIN Motion Test Object", mesh)
    bpy.context.scene.collection.objects.link(target)
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target

    for animation_type in ("BOB", "SPIN", "PULSE", "TWIST", "LIVING"):
        settings.animation_type = animation_type
        result = bpy.ops.vinmotion.build_animation()
        if "FINISHED" not in result:
            raise AssertionError(f"Animation builder failed for {animation_type}: {result}")
        modifier = target.modifiers.get("VIN Motion · Animation")
        if modifier is None or modifier.type != "NODES" or modifier.node_group is None:
            raise AssertionError(f"{animation_type} did not create a Geometry Nodes modifier")
        if len(modifier.node_group.nodes) < 4 or len(modifier.node_group.links) < 3:
            raise AssertionError(f"{animation_type} created an incomplete node graph")
        if animation_type == "LIVING":
            node_types = {node.bl_idname for node in modifier.node_group.nodes}
            required_living_nodes = {
                "GeometryNodeSubdivideMesh",
                "GeometryNodeInputPosition",
                "GeometryNodeInputNormal",
                "ShaderNodeTexNoise",
                "ShaderNodeValToRGB",
                "GeometryNodeSetPosition",
            }
            if not required_living_nodes.issubset(node_types):
                raise AssertionError(f"Living Entity graph missing nodes: {required_living_nodes - node_types}")
            if len(modifier.node_group.links) < 22:
                raise AssertionError("Living Entity graph does not contain enough field links")
        print(f"[OK] VIN Motion {animation_type}: {len(modifier.node_group.nodes)} nodes, {len(modifier.node_group.links)} links")

    # Create an independent source collection with two object choices and an unrelated Plane.
    source_collection = bpy.data.collections.new("VIN Motion Test Sources")
    bpy.context.scene.collection.children.link(source_collection)
    cube_mesh = bpy.data.meshes.new("VIN Motion Scatter Cube Mesh")
    cube_mesh.from_pydata(
        [(-0.5,-0.5,-0.5),(0.5,-0.5,-0.5),(0.5,0.5,-0.5),(-0.5,0.5,-0.5),
         (-0.5,-0.5,0.5),(0.5,-0.5,0.5),(0.5,0.5,0.5),(-0.5,0.5,0.5)],
        [],
        [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],
    )
    cube_mesh.update()
    source_cube = bpy.data.objects.new("VIN Motion Scatter Cube", cube_mesh)
    source_collection.objects.link(source_cube)

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.5, location=(20, 0, 0))
    ico = bpy.context.object
    ico.name = "VIN Motion Scatter Icosphere"
    for col in list(ico.users_collection):
        col.objects.unlink(ico)
    source_collection.objects.link(ico)

    plane_mesh = bpy.data.meshes.new("VIN Motion Test Plane Mesh")
    plane_mesh.from_pydata([(-5,-5,0),(5,-5,0),(5,5,0),(-5,5,0)], [], [(0,1,2,3)])
    plane_mesh.update()
    plane = bpy.data.objects.new("VIN Motion Test Plane", plane_mesh)
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

    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    plane.select_set(True)
    bpy.context.view_layer.objects.active = plane
    result = bpy.ops.vinmotion.build_scatter()
    if "FINISHED" not in result:
        raise AssertionError(f"VIN Motion scatter builder failed: {result}")
    modifier = plane.modifiers.get("VIN Motion · Noise Scatter")
    if modifier is None or modifier.node_group is None:
        raise AssertionError("Plane does not have the VIN Motion scatter modifier")
    node_types = {node.bl_idname for node in modifier.node_group.nodes}
    required = {
        "GeometryNodeDistributePointsOnFaces",
        "GeometryNodeCollectionInfo",
        "GeometryNodeInstanceOnPoints",
        "GeometryNodeSetPosition",
        "ShaderNodeTexNoise",
        "ShaderNodeValToRGB",
    }
    if not required.issubset(node_types):
        raise AssertionError(f"Scatter graph missing node types: {required - node_types}")
    if len(modifier.node_group.links) < 30:
        raise AssertionError("Scatter graph does not contain the expected node links")

    print(f"[OK] VIN Motion Noise / Color Ramp Scatter: {len(node_types)} node types, {len(modifier.node_group.links)} links")

    # Surface Spawn must create real, individually selectable objects, each with its own node group.
    spawn_plane_mesh = bpy.data.meshes.new("VIN Motion Spawn Plane Mesh")
    spawn_plane_mesh.from_pydata([(-4,-4,0),(4,-4,0),(4,4,0),(-4,4,0)], [], [(0,1,2,3)])
    spawn_plane_mesh.update()
    spawn_plane = bpy.data.objects.new("VIN Motion Spawn Plane", spawn_plane_mesh)
    bpy.context.scene.collection.objects.link(spawn_plane)

    settings.spawn_source_collection = source_collection
    settings.spawn_count = 12
    settings.spawn_seed = 2026
    settings.spawn_min_scale = 0.5
    settings.spawn_max_scale = 1.0
    settings.spawn_surface_offset = 0.02
    settings.spawn_align_normal = True
    settings.spawn_animation_mode = "RANDOM"
    settings.spawn_speed_variance = 0.3
    settings.spawn_amount_variance = 0.2
    settings.spawn_phase_range = 6.283
    settings.spawn_start_frame = 1
    settings.spawn_stagger_frames = 30
    settings.spawn_growth_frames = 10

    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    spawn_plane.select_set(True)
    bpy.context.view_layer.objects.active = spawn_plane
    spawn_result = bpy.ops.vinmotion.surface_spawn()
    if "FINISHED" not in spawn_result:
        raise AssertionError(f"Surface Spawn failed: {spawn_result}")
    spawn_collection = bpy.data.collections.get("VIN Motion · Surface Spawn")
    if spawn_collection is None:
        raise AssertionError("Surface Spawn did not create an output collection")
    spawned = [obj for obj in spawn_collection.objects if obj.type == "MESH"]
    if len(spawned) != settings.spawn_count:
        raise AssertionError(f"Expected {settings.spawn_count} separate objects, got {len(spawned)}")
    node_group_ids = set()
    assigned_types = set()
    for obj in spawned:
        mod = obj.modifiers.get("VIN Motion · Animation")
        if mod is None or mod.type != "NODES" or mod.node_group is None:
            raise AssertionError(f"{obj.name} has no independent animation modifier")
        node_group_ids.add(mod.node_group.as_pointer())
        assigned_types.add(obj.get("vinmotion_animation_type"))
        if obj.animation_data is None or obj.animation_data.action is None:
            raise AssertionError(f"{obj.name} has no growth keyframes")
    if len(node_group_ids) != len(spawned):
        raise AssertionError("Spawned objects are sharing animation node groups instead of receiving individual graphs")
    if len(assigned_types) < 2:
        raise AssertionError("Random-per-object mode did not vary the assigned motion presets")
    print(f"[OK] Surface Spawn: {len(spawned)} separate animated objects, {len(node_group_ids)} unique node groups, types={sorted(assigned_types)}")
    print("VIN Motion Lab runtime smoke test passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"VIN Motion Lab runtime smoke test failed: {exc}", file=sys.stderr)
        raise
