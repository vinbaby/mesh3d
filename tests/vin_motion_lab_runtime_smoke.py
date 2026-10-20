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

    for animation_type in ("BOB", "SPIN", "PULSE", "TWIST", "LIVING", "DRIFT", "RADIAL", "LATTICE_PULSE"):
        settings.animation_type = animation_type
        result = bpy.ops.vinmotion.build_animation()
        if "FINISHED" not in result:
            raise AssertionError(f"Animation builder failed for {animation_type}: {result}")
        modifier = target.modifiers.get("VIN Motion · Animation")
        if modifier is None or modifier.type != "NODES" or modifier.node_group is None:
            raise AssertionError(f"{animation_type} did not create a Geometry Nodes modifier")
        if len(modifier.node_group.nodes) < 4 or len(modifier.node_group.links) < 3:
            raise AssertionError(f"{animation_type} created an incomplete node graph")
        if animation_type == "DRIFT":
            node_types = {node.bl_idname for node in modifier.node_group.nodes}
            if "ShaderNodeCombineXYZ" not in node_types or "GeometryNodeSetPosition" not in node_types:
                raise AssertionError("3D Drift graph is missing Combine XYZ or Set Position")
            sine_nodes = [node for node in modifier.node_group.nodes if node.bl_idname == "ShaderNodeMath" and node.operation == "SINE"]
            if len(sine_nodes) < 3:
                raise AssertionError("3D Drift needs independent X/Y/Z sinusoidal paths")
        if animation_type == "LATTICE_PULSE":
            node_types = {node.bl_idname for node in modifier.node_group.nodes}
            required_lattice_nodes = {
                "GeometryNodeInputPosition",
                "GeometryNodeInputNormal",
                "ShaderNodeTexNoise",
                "ShaderNodeValToRGB",
                "GeometryNodeSetPosition",
            }
            if not required_lattice_nodes.issubset(node_types):
                raise AssertionError(f"Lattice Pulse graph missing nodes: {required_lattice_nodes - node_types}")
            sine_nodes = [node for node in modifier.node_group.nodes if node.bl_idname == "ShaderNodeMath" and node.operation == "SINE"]
            if len(sine_nodes) != 1:
                raise AssertionError("Lattice Pulse should create one travelling-wave sine")
            if len(modifier.node_group.links) < 14:
                raise AssertionError("Lattice Pulse graph does not contain enough links")
        if animation_type == "RADIAL":
            node_types = {node.bl_idname for node in modifier.node_group.nodes}
            required_radial_nodes = {
                "GeometryNodeSubdivideMesh",
                "GeometryNodeInputPosition",
                "ShaderNodeVectorMath",
                "GeometryNodeSetPosition",
            }
            if not required_radial_nodes.issubset(node_types):
                raise AssertionError(f"Radial Pulse graph missing nodes: {required_radial_nodes - node_types}")
            if len(modifier.node_group.links) < 12:
                raise AssertionError("Radial Pulse does not have enough field links")
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

    # Build a motion on several selected objects and prove each receives a unique graph/phase.
    settings.animation_type = "LIVING"
    settings.animation_speed = 1.0
    settings.animation_amount = 0.35
    settings.entity_noise_scale = 1.6
    settings.entity_breathing = 0.18
    settings.entity_mask_threshold = 0.30
    settings.entity_subdivision = 2
    settings.animation_phase_spread = 6.283
    multi_targets = [target]
    for index in range(2):
        dup = target.copy()
        dup.data = target.data.copy()
        dup.animation_data_clear()
        bpy.context.scene.collection.objects.link(dup)
        dup.location.x = (index + 1) * 3.0
        multi_targets.append(dup)
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in multi_targets:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = multi_targets[0]
    result = bpy.ops.vinmotion.build_animation()
    if "FINISHED" not in result:
        raise AssertionError(f"Multi-object animation builder failed: {result}")
    graph_ids = set()
    phases = set()
    for obj in multi_targets:
        mod = obj.modifiers.get("VIN Motion · Animation")
        if mod is None or mod.node_group is None:
            raise AssertionError(f"{obj.name} has no independently assigned node graph")
        graph_ids.add(mod.node_group.as_pointer())
        phases.add(round(float(obj.get("vinmotion_phase", 0.0)), 4))
    if len(graph_ids) != len(multi_targets):
        raise AssertionError("Selected objects are sharing one node group")
    if len(phases) != len(multi_targets):
        raise AssertionError("Selected objects did not receive distinct animation phases")
    print(f"[OK] Multi-object motion: {len(multi_targets)} separate node graphs and phases")

    reset_result = bpy.ops.vinmotion.reset_motion()
    if "FINISHED" not in reset_result:
        raise AssertionError("Reset Motion Defaults operator failed")
    if abs(settings.animation_speed - 1.0) > 1e-5 or abs(settings.animation_amount - 0.35) > 1e-5:
        raise AssertionError("Reset Motion Defaults did not restore visible starter values")
    if abs(settings.entity_mask_threshold - 0.30) > 1e-5:
        raise AssertionError("Reset Motion Defaults did not reset Living Entity mask threshold")
    print("[OK] Reset Motion Defaults: visible Living Entity starter settings")

    # Real transform-keyframed Object Motion Actions, each with an independent Action.
    action_targets = []
    for index, location in enumerate(((-2.0, 0.0, 0.4), (1.5, 1.0, 0.7), (0.5, -2.0, 1.0))):
        action_obj = bpy.data.objects.new(f"VIN Object Action Target {index}", target.data.copy())
        action_obj.location = location
        bpy.context.scene.collection.objects.link(action_obj)
        action_targets.append(action_obj)

    settings.object_motion_speed = 1.0
    settings.object_motion_amount = 0.55
    settings.object_motion_duration = 48
    settings.object_motion_stagger = 9
    settings.object_motion_seed = 812
    settings.object_motion_anchor = None
    settings.object_motion_axis = "Z"
    for mode in ("WOBBLE", "SHOCKWAVE", "ORBIT", "MAGNET", "GLITCH", "FOLD", "DISSOLVE", "CASCADE"):
        settings.object_motion_type = mode
        settings.object_magnet_mode = "PULL"
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in action_targets:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = action_targets[0]
        action_result = bpy.ops.vinmotion.apply_object_motion()
        if "FINISHED" not in action_result:
            raise AssertionError(f"Object Motion Action failed for {mode}: {action_result}")
        action_ids = set()
        for obj in action_targets:
            action = obj.animation_data.action if obj.animation_data else None
            if action is None:
                raise AssertionError(f"{mode}: {obj.name} has no transform Action")
            action_ids.add(action.as_pointer())
            location_curves = [fc for fc in action.fcurves if fc.data_path == "location"]
            rotation_curves = [fc for fc in action.fcurves if fc.data_path == "rotation_euler"]
            scale_curves = [fc for fc in action.fcurves if fc.data_path == "scale"]
            if len(location_curves) != 3 or len(rotation_curves) != 3 or len(scale_curves) != 3:
                raise AssertionError(f"{mode}: {obj.name} is missing independent transform channels")
            if any(len(fc.keyframe_points) < 5 for fc in location_curves):
                raise AssertionError(f"{mode}: {obj.name} has too few transform keys")
            if obj.get("vinmotion_object_motion") != mode:
                raise AssertionError(f"{mode}: metadata was not written on {obj.name}")
        if len(action_ids) != len(action_targets):
            raise AssertionError(f"{mode}: object targets share an Action instead of using independent Actions")
        if mode == "MAGNET":
            settings.object_magnet_mode = "REPEL"
            result = bpy.ops.vinmotion.apply_object_motion()
            if "FINISHED" not in result:
                raise AssertionError("Magnet Repel action failed")
        print(f"[OK] Object Motion Action {mode}: {len(action_targets)} independent Actions")

    # VIN Force Lab: one-shot, independent transform-keyframed responses.
    settings.force_anchor = None
    settings.force_strength = 1.25
    settings.force_radius = 10.0
    settings.force_falloff = 1.35
    settings.force_duration = 32
    settings.force_stagger = 4
    settings.force_seed = 173
    settings.force_direction = (0.0, 0.0, 1.0)
    settings.force_vortex_turns = 1.25
    for mode in ("IMPULSE_BURST", "RADIAL_PUSH", "RADIAL_PULL", "DIRECTIONAL_BLAST", "SHOCKWAVE_RING", "VORTEX", "TURBULENCE"):
        settings.force_mode = mode
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in action_targets:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = action_targets[0]
        force_result = bpy.ops.vinmotion.apply_force_action()
        if "FINISHED" not in force_result:
            raise AssertionError(f"Force action failed for {mode}: {force_result}")
        force_action_ids = set()
        for obj in action_targets:
            action = obj.animation_data.action if obj.animation_data else None
            if action is None:
                raise AssertionError(f"{mode}: {obj.name} has no force Action")
            force_action_ids.add(action.as_pointer())
            loc_curves = [fc for fc in action.fcurves if fc.data_path == "location"]
            rot_curves = [fc for fc in action.fcurves if fc.data_path == "rotation_euler"]
            scale_curves = [fc for fc in action.fcurves if fc.data_path == "scale"]
            if len(loc_curves) != 3 or len(rot_curves) != 3 or len(scale_curves) != 3:
                raise AssertionError(f"{mode}: missing separate transform channels")
            if any(len(fc.keyframe_points) < 4 for fc in loc_curves):
                raise AssertionError(f"{mode}: expected multiple one-shot transform keys")
            if any(any(mod.type == "CYCLES" for mod in fc.modifiers) for fc in loc_curves):
                raise AssertionError(f"{mode}: force response should be one-shot, not looping")
            if obj.get("vinmotion_force_mode") != mode:
                raise AssertionError(f"{mode}: force metadata is missing")
        if len(force_action_ids) != len(action_targets):
            raise AssertionError(f"{mode}: selected objects share Actions")
        print(f"[OK] VIN Force {mode}: {len(action_targets)} separate one-shot Actions")

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
    settings.spawn_growth_mode = "RISE_TWIST"
    settings.spawn_growth_height = 1.25
    settings.spawn_growth_twist = 0.45

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
        action = obj.animation_data.action
        location_curves = [fc for fc in action.fcurves if fc.data_path == "location"]
        rotation_curves = [fc for fc in action.fcurves if fc.data_path == "rotation_quaternion"]
        if obj.get("vinmotion_spawn_growth_mode") != "RISE_TWIST":
            raise AssertionError(f"{obj.name} has incorrect growth mode metadata")
        if len(location_curves) != 3 or len(rotation_curves) != 4:
            raise AssertionError(f"{obj.name} is missing rise/twist keyframe channels")
        if any(len(fc.keyframe_points) < 3 for fc in location_curves):
            raise AssertionError(f"{obj.name} has too few rise keyframes")
    if len(node_group_ids) != len(spawned):
        raise AssertionError("Spawned objects are sharing animation node groups instead of receiving individual graphs")
    if len(assigned_types) < 2:
        raise AssertionError("Random-per-object mode did not vary the assigned motion presets")
    print(f"[OK] Surface Spawn / Rise + Twist: {len(spawned)} separate animated objects, {len(node_group_ids)} unique node groups, types={sorted(assigned_types)}")

    # Surface Crawl: each target gets its own loop of projected location keys on a target mesh.
    crawl_surface_mesh = bpy.data.meshes.new("VIN Motion Crawl Surface Mesh")
    crawl_surface_mesh.from_pydata([(-5,-5,0),(5,-5,0),(5,5,0),(-5,5,0)], [], [(0,1,2,3)])
    crawl_surface_mesh.update()
    crawl_surface = bpy.data.objects.new("VIN Motion Crawl Surface", crawl_surface_mesh)
    bpy.context.scene.collection.objects.link(crawl_surface)

    crawl_targets = []
    for index, location in enumerate(((0.0,0.0,0.3),(1.0,1.0,0.3),(-1.0,0.5,0.3))):
        crawl_mesh = bpy.data.meshes.new(f"VIN Motion Crawler Mesh {index}")
        crawl_mesh.from_pydata(
            [(-0.2,-0.2,0),(0.2,-0.2,0),(0.2,0.2,0),(-0.2,0.2,0)],
            [], [(0,1,2,3)]
        )
        crawl_mesh.update()
        crawler = bpy.data.objects.new(f"VIN Motion Crawler {index}", crawl_mesh)
        crawler.location = location
        bpy.context.scene.collection.objects.link(crawler)
        crawl_targets.append(crawler)

    settings.crawl_surface = crawl_surface
    settings.crawl_seed = 93
    settings.crawl_steps = 4
    settings.crawl_step_frames = 6
    settings.crawl_step_distance = 0.35
    settings.crawl_surface_offset = 0.025
    settings.crawl_stagger_frames = 12
    settings.crawl_start_frame = 1
    settings.crawl_align_normal = False
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in crawl_targets:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = crawl_targets[0]
    crawl_result = bpy.ops.vinmotion.surface_crawl()
    if "FINISHED" not in crawl_result:
        raise AssertionError(f"Surface Crawl failed: {crawl_result}")
    for crawler in crawl_targets:
        action = crawler.animation_data.action if crawler.animation_data else None
        if action is None:
            raise AssertionError(f"{crawler.name} has no location animation")
        location_curves = [fc for fc in action.fcurves if fc.data_path == "location"]
        if len(location_curves) != 3:
            raise AssertionError(f"{crawler.name} does not have 3 location curves")
        if any(len(fc.keyframe_points) < settings.crawl_steps + 2 for fc in location_curves):
            raise AssertionError(f"{crawler.name} path has too few keys")
        if not all(any(mod.type == "CYCLES" for mod in fc.modifiers) for fc in location_curves):
            raise AssertionError(f"{crawler.name} path does not loop")
        if not crawler.get("vinmotion_surface_crawl", False):
            raise AssertionError(f"{crawler.name} is missing Surface Crawl metadata")
    print(f"[OK] Surface Crawl: {len(crawl_targets)} independent looping paths with location keyframes")
    print("VIN Motion Lab runtime smoke test passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"VIN Motion Lab runtime smoke test failed: {exc}", file=sys.stderr)
        raise
