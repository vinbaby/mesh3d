bl_info = {
    "name": "VIN Motion Lab",
    "author": "VIN Studio",
    "version": (0, 3, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > VIN Motion",
    "description": "Standalone Geometry Nodes animation and noise-mask scatter tools",
    "category": "Animation",
}

import bpy
import math
import random
from mathutils import Vector, Quaternion
from bpy.props import (
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
)

ANIMATION_ITEMS = [
    ("BOB", "Bob / Float", "Move geometry up and down over time"),
    ("SPIN", "Continuous Spin", "Rotate the whole geometry over time"),
    ("PULSE", "Scale Pulse", "Scale the geometry rhythmically"),
    ("TWIST", "Animated Twist", "Twist points around the Z axis over time"),
    ("LIVING", "Living Entity", "Organic breathing and noise-driven local deformation"),
]
ANIMATION_LABELS = {identifier: label for identifier, label, _description in ANIMATION_ITEMS}

def _add_interface_socket(tree, name, in_out, socket_type, default=None, min_value=None, max_value=None):
    if hasattr(tree, "interface"):
        socket = tree.interface.new_socket(
            name=name, in_out=in_out, socket_type=socket_type
        )
    else:
        sockets = tree.inputs if in_out == "INPUT" else tree.outputs
        socket = sockets.new(socket_type, name)

    if default is not None and hasattr(socket, "default_value"):
        socket.default_value = default
    if min_value is not None and hasattr(socket, "min_value"):
        socket.min_value = min_value
    if max_value is not None and hasattr(socket, "max_value"):
        socket.max_value = max_value
    return socket


def _math_node(nodes, operation, label, location):
    node = nodes.new("ShaderNodeMath")
    node.operation = operation
    node.label = label
    node.location = location
    return node


def _find_socket(sockets, name):
    socket = sockets.get(name)
    if socket is None:
        raise RuntimeError(f"Blender node socket not found: {name}")
    return socket


def _build_animation_group(settings, animation_type):
    friendly = ANIMATION_LABELS.get(animation_type, animation_type.title())
    tree = bpy.data.node_groups.new(
        name=f"VINMOTION · {friendly}", type="GeometryNodeTree"
    )
    geo_in = _add_interface_socket(tree, "Geometry", "INPUT", "NodeSocketGeometry")
    speed_socket = _add_interface_socket(
        tree, "Speed", "INPUT", "NodeSocketFloat",
        default=settings.animation_speed, min_value=0.0, max_value=20.0,
    )
    amount_label = "Amount"
    amount_limit = 0.95 if animation_type == "PULSE" else (2.0 if animation_type == "LIVING" else 10.0)
    amount_default = min(settings.animation_amount, amount_limit)
    if animation_type == "TWIST":
        amount_label = "Twist Strength"
    elif animation_type == "LIVING":
        amount_label = "Deform Strength"
    elif animation_type == "PULSE":
        amount_label = "Pulse Amount"
    elif animation_type == "BOB":
        amount_label = "Height"
    amount_socket = _add_interface_socket(
        tree, amount_label, "INPUT", "NodeSocketFloat",
        default=amount_default, min_value=0.0, max_value=amount_limit,
    )
    phase_socket = _add_interface_socket(
        tree, "Phase", "INPUT", "NodeSocketFloat",
        default=settings.animation_phase, min_value=-100.0, max_value=100.0,
    )
    extra_sockets = {}
    if animation_type == "LIVING":
        extra_sockets["noise_scale"] = _add_interface_socket(
            tree, "Organic Noise Scale", "INPUT", "NodeSocketFloat",
            default=settings.entity_noise_scale, min_value=0.05, max_value=20.0,
        )
        extra_sockets["breathing"] = _add_interface_socket(
            tree, "Breathing", "INPUT", "NodeSocketFloat",
            default=settings.entity_breathing, min_value=0.0, max_value=0.8,
        )
        extra_sockets["threshold"] = _add_interface_socket(
            tree, "Mask Threshold", "INPUT", "NodeSocketFloat",
            default=settings.entity_mask_threshold, min_value=0.0, max_value=1.0,
        )
        extra_sockets["subdivision"] = _add_interface_socket(
            tree, "Surface Detail", "INPUT", "NodeSocketInt",
            default=settings.entity_subdivision, min_value=0, max_value=4,
        )
    geo_out = _add_interface_socket(tree, "Geometry", "OUTPUT", "NodeSocketGeometry")
    nodes, links = tree.nodes, tree.links
    nodes.clear()

    group_in = nodes.new("NodeGroupInput")
    group_in.location = (-900, 100)
    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (800, 100)
    scene_time = nodes.new("GeometryNodeInputSceneTime")
    scene_time.location = (-900, -260)
    scene_time.label = "Animation clock"

    time_mul = _math_node(nodes, "MULTIPLY", "Time × Speed", (-650, -260))
    links.new(_find_socket(scene_time.outputs, "Seconds"), time_mul.inputs[0])
    links.new(_find_socket(group_in.outputs, "Speed"), time_mul.inputs[1])
    phase_add = _math_node(nodes, "ADD", "Per-object phase offset", (-430, -470))
    links.new(time_mul.outputs[0], phase_add.inputs[0])
    links.new(_find_socket(group_in.outputs, "Phase"), phase_add.inputs[1])
    time_signal = phase_add

    if animation_type == "BOB":
        sine = _math_node(nodes, "SINE", "Smooth oscillation", (-420, -260))
        amplitude = _math_node(nodes, "MULTIPLY", "Apply height", (-190, -260))
        combine = nodes.new("ShaderNodeCombineXYZ")
        combine.location = (40, -160)
        set_position = nodes.new("GeometryNodeSetPosition")
        set_position.location = (360, 100)
        set_position.label = "Move entire geometry"
        links.new(time_signal.outputs[0], sine.inputs[0])
        links.new(sine.outputs[0], amplitude.inputs[0])
        links.new(_find_socket(group_in.outputs, amount_label), amplitude.inputs[1])
        links.new(amplitude.outputs[0], combine.inputs["Z"])
        links.new(_find_socket(group_in.outputs, "Geometry"), set_position.inputs["Geometry"])
        links.new(combine.outputs["Vector"], set_position.inputs["Offset"])
        links.new(set_position.outputs["Geometry"], _find_socket(group_out.inputs, "Geometry"))

    elif animation_type == "SPIN":
        combine = nodes.new("ShaderNodeCombineXYZ")
        combine.location = (-180, -120)
        transform = nodes.new("GeometryNodeTransform")
        transform.location = (360, 100)
        transform.label = "Continuous rotation"
        links.new(time_signal.outputs[0], combine.inputs["Z"])
        links.new(_find_socket(group_in.outputs, "Geometry"), transform.inputs["Geometry"])
        links.new(combine.outputs["Vector"], transform.inputs["Rotation"])
        links.new(transform.outputs["Geometry"], _find_socket(group_out.inputs, "Geometry"))

    elif animation_type == "PULSE":
        sine = _math_node(nodes, "SINE", "Pulse wave", (-430, -260))
        amplitude = _math_node(nodes, "MULTIPLY", "Pulse amplitude", (-220, -260))
        add_one = _math_node(nodes, "ADD", "Scale around 1.0", (0, -260))
        combine = nodes.new("ShaderNodeCombineXYZ")
        combine.location = (180, -150)
        transform = nodes.new("GeometryNodeTransform")
        transform.location = (470, 100)
        transform.label = "Uniform scale pulse"
        links.new(time_signal.outputs[0], sine.inputs[0])
        links.new(sine.outputs[0], amplitude.inputs[0])
        links.new(_find_socket(group_in.outputs, amount_label), amplitude.inputs[1])
        links.new(amplitude.outputs[0], add_one.inputs[0])
        add_one.inputs[1].default_value = 1.0
        for axis in ("X", "Y", "Z"):
            links.new(add_one.outputs[0], combine.inputs[axis])
        links.new(_find_socket(group_in.outputs, "Geometry"), transform.inputs["Geometry"])
        links.new(combine.outputs["Vector"], transform.inputs["Scale"])
        links.new(transform.outputs["Geometry"], _find_socket(group_out.inputs, "Geometry"))

    elif animation_type == "TWIST":
        position = nodes.new("GeometryNodeInputPosition")
        position.location = (-900, 380)
        separate = nodes.new("ShaderNodeSeparateXYZ")
        separate.location = (-680, 380)
        links.new(position.outputs["Position"], separate.inputs["Vector"])

        vertical_twist = _math_node(nodes, "MULTIPLY", "Height × Twist Strength", (-450, 430))
        angle_add = _math_node(nodes, "ADD", "Spatial twist + time", (-230, 300))
        links.new(separate.outputs["Z"], vertical_twist.inputs[0])
        links.new(_find_socket(group_in.outputs, amount_label), vertical_twist.inputs[1])
        links.new(vertical_twist.outputs[0], angle_add.inputs[0])
        links.new(time_signal.outputs[0], angle_add.inputs[1])

        cosine = _math_node(nodes, "COSINE", "Cos(angle)", (0, 430))
        sine = _math_node(nodes, "SINE", "Sin(angle)", (0, 200))
        links.new(angle_add.outputs[0], cosine.inputs[0])
        links.new(angle_add.outputs[0], sine.inputs[0])

        x_cos = _math_node(nodes, "MULTIPLY", "X × cos", (200, 520))
        y_sin = _math_node(nodes, "MULTIPLY", "Y × sin", (200, 350))
        x_sin = _math_node(nodes, "MULTIPLY", "X × sin", (200, 170))
        y_cos = _math_node(nodes, "MULTIPLY", "Y × cos", (200, 0))
        links.new(separate.outputs["X"], x_cos.inputs[0])
        links.new(cosine.outputs[0], x_cos.inputs[1])
        links.new(separate.outputs["Y"], y_sin.inputs[0])
        links.new(sine.outputs[0], y_sin.inputs[1])
        links.new(separate.outputs["X"], x_sin.inputs[0])
        links.new(sine.outputs[0], x_sin.inputs[1])
        links.new(separate.outputs["Y"], y_cos.inputs[0])
        links.new(cosine.outputs[0], y_cos.inputs[1])

        x_sub = _math_node(nodes, "SUBTRACT", "Twisted X", (410, 430))
        y_add = _math_node(nodes, "ADD", "Twisted Y", (410, 170))
        links.new(x_cos.outputs[0], x_sub.inputs[0])
        links.new(y_sin.outputs[0], x_sub.inputs[1])
        links.new(x_sin.outputs[0], y_add.inputs[0])
        links.new(y_cos.outputs[0], y_add.inputs[1])

        combine = nodes.new("ShaderNodeCombineXYZ")
        combine.location = (580, 320)
        set_position = nodes.new("GeometryNodeSetPosition")
        set_position.location = (650, 80)
        set_position.label = "Deform points around Z"
        links.new(x_sub.outputs[0], combine.inputs["X"])
        links.new(y_add.outputs[0], combine.inputs["Y"])
        links.new(separate.outputs["Z"], combine.inputs["Z"])
        links.new(_find_socket(group_in.outputs, "Geometry"), set_position.inputs["Geometry"])
        links.new(combine.outputs["Vector"], set_position.inputs["Position"])
        links.new(set_position.outputs["Geometry"], _find_socket(group_out.inputs, "Geometry"))

    elif animation_type == "LIVING":
        # Subdivide before displacement so low-poly input meshes gain enough control points.
        subdivide = nodes.new("GeometryNodeSubdivideMesh")
        subdivide.location = (-650, 140)
        subdivide.label = "Add surface resolution before deformation"
        links.new(_find_socket(group_in.outputs, "Geometry"), subdivide.inputs["Mesh"])
        links.new(_find_socket(group_in.outputs, "Surface Detail"), subdivide.inputs["Level"])

        position = nodes.new("GeometryNodeInputPosition")
        position.location = (-900, -80)
        normal = nodes.new("GeometryNodeInputNormal")
        normal.location = (-650, -430)

        noise = nodes.new("ShaderNodeTexNoise")
        noise.location = (-420, -100)
        noise.label = "Living surface · animated 4D Noise"
        noise.noise_dimensions = "4D"
        links.new(position.outputs["Position"], noise.inputs["Vector"])
        links.new(_find_socket(group_in.outputs, "Organic Noise Scale"), noise.inputs["Scale"])
        links.new(time_signal.outputs[0], noise.inputs["W"])

        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.location = (-170, -80)
        ramp.label = "Organic influence mask · editable Color Ramp"
        ramp.color_ramp.elements[0].position = 0.28
        ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 0.0)
        ramp.color_ramp.elements[1].position = 0.72
        ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])

        mask_test = _math_node(nodes, "GREATER_THAN", "Threshold selects the moving regions", (80, -60))
        links.new(ramp.outputs["Alpha"], mask_test.inputs[0])
        links.new(_find_socket(group_in.outputs, "Mask Threshold"), mask_test.inputs[1])

        centered_noise = nodes.new("ShaderNodeVectorMath")
        centered_noise.operation = "SUBTRACT"
        centered_noise.location = (-160, -360)
        centered_noise.label = "Center the 3D noise direction"
        links.new(noise.outputs["Color"], centered_noise.inputs[0])
        centered_noise.inputs[1].default_value = (0.5, 0.5, 0.5)

        displacement_amount = _math_node(nodes, "MULTIPLY", "Deform strength × mask weight", (100, -350))
        links.new(_find_socket(group_in.outputs, amount_label), displacement_amount.inputs[0])
        links.new(ramp.outputs["Alpha"], displacement_amount.inputs[1])

        displacement_vector = nodes.new("ShaderNodeVectorMath")
        displacement_vector.operation = "SCALE"
        displacement_vector.location = (330, -350)
        displacement_vector.label = "Noise displacement"
        links.new(centered_noise.outputs["Vector"], displacement_vector.inputs["Vector"])
        links.new(displacement_amount.outputs[0], displacement_vector.inputs["Scale"])

        # Slow radial breathing is intentionally slower than the surface-noise motion.
        breath_rate = _math_node(nodes, "MULTIPLY", "Breath rate", (-650, -700))
        breath_rate.inputs[1].default_value = 0.55
        links.new(time_signal.outputs[0], breath_rate.inputs[0])
        breath_wave = _math_node(nodes, "SINE", "Soft breathing cycle", (-420, -700))
        links.new(breath_rate.outputs[0], breath_wave.inputs[0])
        breath_amount = _math_node(nodes, "MULTIPLY", "Breathing amplitude", (-200, -700))
        links.new(breath_wave.outputs[0], breath_amount.inputs[0])
        links.new(_find_socket(group_in.outputs, "Breathing"), breath_amount.inputs[1])
        breath_scale = _math_node(nodes, "ADD", "Scale around neutral size", (30, -700))
        breath_scale.inputs[1].default_value = 1.0
        links.new(breath_amount.outputs[0], breath_scale.inputs[0])

        radial_breath = nodes.new("ShaderNodeVectorMath")
        radial_breath.operation = "SCALE"
        radial_breath.location = (100, 220)
        radial_breath.label = "Whole-body breathing"
        links.new(position.outputs["Position"], radial_breath.inputs["Vector"])
        links.new(breath_scale.outputs[0], radial_breath.inputs["Scale"])

        # Also push along the surface normal, so the silhouette swells rather than sliding like a rigid plate.
        noise_center = _math_node(nodes, "SUBTRACT", "Noise around zero", (80, -520))
        noise_center.inputs[1].default_value = 0.5
        links.new(noise.outputs["Fac"], noise_center.inputs[0])
        normal_strength = _math_node(nodes, "MULTIPLY", "Normal displacement", (310, -560))
        links.new(noise_center.outputs[0], normal_strength.inputs[0])
        links.new(displacement_amount.outputs[0], normal_strength.inputs[1])
        normal_offset = nodes.new("ShaderNodeVectorMath")
        normal_offset.operation = "SCALE"
        normal_offset.location = (520, -500)
        links.new(normal.outputs["Normal"], normal_offset.inputs["Vector"])
        links.new(normal_strength.outputs[0], normal_offset.inputs["Scale"])

        offset_sum = nodes.new("ShaderNodeVectorMath")
        offset_sum.operation = "ADD"
        offset_sum.location = (540, -180)
        links.new(displacement_vector.outputs["Vector"], offset_sum.inputs[0])
        links.new(normal_offset.outputs["Vector"], offset_sum.inputs[1])

        new_position = nodes.new("ShaderNodeVectorMath")
        new_position.operation = "ADD"
        new_position.location = (560, 180)
        new_position.label = "Breathing position + organic offset"
        links.new(radial_breath.outputs["Vector"], new_position.inputs[0])
        links.new(offset_sum.outputs["Vector"], new_position.inputs[1])

        set_position = nodes.new("GeometryNodeSetPosition")
        set_position.location = (850, 140)
        set_position.label = "Only noise-mask-selected regions deform"
        links.new(subdivide.outputs["Mesh"], set_position.inputs["Geometry"])
        links.new(mask_test.outputs[0], set_position.inputs["Selection"])
        links.new(new_position.outputs["Vector"], set_position.inputs["Position"])
        links.new(set_position.outputs["Geometry"], _find_socket(group_out.inputs, "Geometry"))

    else:
        bpy.data.node_groups.remove(tree)
        raise ValueError(f"Unsupported animation type: {animation_type}")

    tree["vinmotion_version"] = "0.2.0"
    tree["vinmotion_animation_type"] = animation_type
    tree["vinmotion_speed_socket"] = getattr(speed_socket, "identifier", "Speed")
    tree["vinmotion_amount_socket"] = getattr(amount_socket, "identifier", amount_label)
    tree["vinmotion_geometry_input"] = getattr(geo_in, "identifier", "Geometry")
    tree["vinmotion_geometry_output"] = getattr(geo_out, "identifier", "Geometry")
    return tree, speed_socket, amount_socket, extra_sockets, phase_socket



def _build_field_scatter_group(settings):
    """Scatter a source collection on the active mesh, with animated Noise/Color Ramp point selection."""
    collection = settings.scatter_collection
    if collection is None:
        raise ValueError("Choose a Source Collection first")
    source_objects = [obj for obj in collection.objects if obj.type in {"MESH", "CURVE", "FONT", "SURFACE"}]
    if not source_objects:
        raise ValueError("The Source Collection must contain at least one mesh or curve object")

    tree = bpy.data.node_groups.new(name="VINMOTION · Noise Color Ramp Scatter", type="GeometryNodeTree")
    sockets = {}
    sockets["geometry_in"] = _add_interface_socket(tree, "Geometry", "INPUT", "NodeSocketGeometry")
    sockets["density"] = _add_interface_socket(tree, "Density", "INPUT", "NodeSocketFloat",
                                                default=settings.scatter_density, min_value=0.01, max_value=100.0)
    sockets["noise_scale"] = _add_interface_socket(tree, "Noise Scale", "INPUT", "NodeSocketFloat",
                                                    default=settings.scatter_noise_scale, min_value=0.01, max_value=50.0)
    sockets["field_strength"] = _add_interface_socket(tree, "Field Motion", "INPUT", "NodeSocketFloat",
                                                        default=settings.scatter_field_strength, min_value=0.0, max_value=10.0)
    sockets["speed"] = _add_interface_socket(tree, "Field Speed", "INPUT", "NodeSocketFloat",
                                              default=settings.scatter_speed, min_value=0.0, max_value=20.0)
    sockets["threshold"] = _add_interface_socket(tree, "Mask Threshold", "INPUT", "NodeSocketFloat",
                                                  default=settings.scatter_threshold, min_value=0.0, max_value=1.0)
    sockets["seed"] = _add_interface_socket(tree, "Seed", "INPUT", "NodeSocketInt",
                                             default=settings.scatter_seed, min_value=0, max_value=9999999)
    sockets["min_scale"] = _add_interface_socket(tree, "Min Scale", "INPUT", "NodeSocketFloat",
                                                  default=settings.scatter_min_scale, min_value=0.01, max_value=10.0)
    sockets["max_scale"] = _add_interface_socket(tree, "Max Scale", "INPUT", "NodeSocketFloat",
                                                  default=max(settings.scatter_min_scale, settings.scatter_max_scale),
                                                  min_value=0.01, max_value=10.0)
    sockets["geometry_out"] = _add_interface_socket(tree, "Geometry", "OUTPUT", "NodeSocketGeometry")
    nodes, links = tree.nodes, tree.links
    nodes.clear()

    group_in = nodes.new("NodeGroupInput")
    group_in.location = (-1120, 220)
    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (1250, 240)

    distribute = nodes.new("GeometryNodeDistributePointsOnFaces")
    distribute.location = (-840, 350)
    distribute.label = "Scatter over the active Plane"
    links.new(group_in.outputs["Geometry"], distribute.inputs["Mesh"])
    links.new(group_in.outputs["Density"], distribute.inputs["Density"])
    links.new(group_in.outputs["Seed"], distribute.inputs["Seed"])

    position = nodes.new("GeometryNodeInputPosition")
    position.location = (-1090, -230)
    scene_time = nodes.new("GeometryNodeInputSceneTime")
    scene_time.location = (-1090, -540)
    time_speed = _math_node(nodes, "MULTIPLY", "Time × Field Speed", (-850, -520))
    links.new(scene_time.outputs["Seconds"], time_speed.inputs[0])
    links.new(group_in.outputs["Field Speed"], time_speed.inputs[1])

    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-620, -200)
    noise.label = "Animated 4D Noise field"
    noise.noise_dimensions = "4D"
    links.new(position.outputs["Position"], noise.inputs["Vector"])
    links.new(group_in.outputs["Noise Scale"], noise.inputs["Scale"])
    if noise.inputs.get("W") is not None:
        links.new(time_speed.outputs[0], noise.inputs["W"])

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-370, -160)
    ramp.label = "Editable influence Color Ramp"
    ramp.color_ramp.elements[0].position = 0.38
    ramp.color_ramp.elements[0].color = (0.015, 0.015, 0.02, 0.0)
    ramp.color_ramp.elements[1].position = 0.64
    ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])

    # Alpha is a scalar 0–1 field, so it can drive the mask without an unsupported RGB-to-BW node.
    compare = _math_node(nodes, "GREATER_THAN", "Mask threshold selects affected points", (-40, -130))
    links.new(ramp.outputs["Alpha"], compare.inputs[0])
    links.new(group_in.outputs["Mask Threshold"], compare.inputs[1])

    sine = _math_node(nodes, "SINE", "Oscillating field motion", (-620, -540))
    links.new(time_speed.outputs[0], sine.inputs[0])
    amount = _math_node(nodes, "MULTIPLY", "Motion amount", (-370, -500))
    links.new(sine.outputs[0], amount.inputs[0])
    links.new(group_in.outputs["Field Motion"], amount.inputs[1])

    center_color = nodes.new("ShaderNodeVectorMath")
    center_color.operation = "SUBTRACT"
    center_color.location = (-100, -430)
    center_color.label = "Center vector around zero"
    links.new(noise.outputs["Color"], center_color.inputs[0])
    center_color.inputs[1].default_value = (0.5, 0.5, 0.5)

    motion_vector = nodes.new("ShaderNodeVectorMath")
    motion_vector.operation = "SCALE"
    motion_vector.location = (150, -410)
    motion_vector.label = "Noise direction × animated strength"
    links.new(center_color.outputs["Vector"], motion_vector.inputs["Vector"])
    links.new(amount.outputs[0], motion_vector.inputs["Scale"])

    set_position = nodes.new("GeometryNodeSetPosition")
    set_position.location = (390, 350)
    set_position.label = "Only ramp-selected scatter points move"
    links.new(distribute.outputs["Points"], set_position.inputs["Geometry"])
    links.new(compare.outputs[0], set_position.inputs["Selection"])
    links.new(motion_vector.outputs["Vector"], set_position.inputs["Offset"])

    source = nodes.new("GeometryNodeCollectionInfo")
    source.location = (100, 670)
    source.label = "Separate source objects from collection"
    source.inputs["Collection"].default_value = collection
    if source.inputs.get("Separate Children") is not None:
        source.inputs["Separate Children"].default_value = True
    if source.inputs.get("Reset Children") is not None:
        source.inputs["Reset Children"].default_value = True
    source_instances = source.outputs.get("Instances") or source.outputs.get("Geometry")
    if source_instances is None:
        bpy.data.node_groups.remove(tree)
        raise RuntimeError("Blender Collection Info node has no Instances/Geometry output")

    point_index = nodes.new("GeometryNodeInputIndex")
    point_index.location = (100, -740)

    pick_index = nodes.new("FunctionNodeRandomValue")
    pick_index.data_type = "INT"
    pick_index.location = (340, -700)
    pick_index.label = "Random source object per point"
    pick_index.inputs["Min"].default_value = 0
    pick_index.inputs["Max"].default_value = max(0, len(source_objects)-1)
    links.new(point_index.outputs["Index"], pick_index.inputs["ID"])
    links.new(group_in.outputs["Seed"], pick_index.inputs["Seed"])

    rotation = nodes.new("FunctionNodeRandomValue")
    rotation.data_type = "FLOAT_VECTOR"
    rotation.location = (340, -930)
    rotation.label = "Random rotation"
    rotation.inputs["Min"].default_value = (0.0, 0.0, 0.0)
    rotation.inputs["Max"].default_value = (0.0, 0.0, math.tau)
    links.new(point_index.outputs["Index"], rotation.inputs["ID"])
    links.new(group_in.outputs["Seed"], rotation.inputs["Seed"])

    scale = nodes.new("FunctionNodeRandomValue")
    scale.data_type = "FLOAT"
    scale.location = (340, -1160)
    scale.label = "Random size"
    links.new(point_index.outputs["Index"], scale.inputs["ID"])
    links.new(group_in.outputs["Seed"], scale.inputs["Seed"])
    links.new(group_in.outputs["Min Scale"], scale.inputs["Min"])
    links.new(group_in.outputs["Max Scale"], scale.inputs["Max"])

    uniform_scale = nodes.new("ShaderNodeCombineXYZ")
    uniform_scale.location = (590, -1050)
    for axis in ("X", "Y", "Z"):
        links.new(scale.outputs["Value"], uniform_scale.inputs[axis])

    instance = nodes.new("GeometryNodeInstanceOnPoints")
    instance.location = (850, 350)
    instance.label = "Instance the selected source object"
    links.new(set_position.outputs["Geometry"], instance.inputs["Points"])
    links.new(source_instances, instance.inputs["Instance"])
    links.new(pick_index.outputs["Value"], instance.inputs["Instance Index"])
    if instance.inputs.get("Pick Instance") is not None:
        instance.inputs["Pick Instance"].default_value = True
    links.new(rotation.outputs["Value"], instance.inputs["Rotation"])
    links.new(uniform_scale.outputs["Vector"], instance.inputs["Scale"])
    links.new(instance.outputs["Instances"], group_out.inputs["Geometry"])

    tree["vinmotion_version"] = "0.2.0"
    tree["vinmotion_feature"] = "noise_color_ramp_scatter"
    tree["vinmotion_source_collection"] = collection.name
    return tree, sockets


def _surface_triangles(plane, depsgraph):
    """Return world-space surface triangles weighted by their area."""
    evaluated = plane.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    triangles = []
    try:
        mesh.calc_loop_triangles()
        matrix_world = evaluated.matrix_world.copy()
        total_area = 0.0
        for triangle in mesh.loop_triangles:
            a = matrix_world @ mesh.vertices[triangle.vertices[0]].co
            b = matrix_world @ mesh.vertices[triangle.vertices[1]].co
            c = matrix_world @ mesh.vertices[triangle.vertices[2]].co
            cross = (b - a).cross(c - a)
            area = cross.length * 0.5
            if area <= 1e-10:
                continue
            triangles.append((a.copy(), b.copy(), c.copy(), cross.normalized(), area, total_area))
            total_area += area
        return triangles, total_area
    finally:
        evaluated.to_mesh_clear()


def _sample_surface_triangle(triangles, total_area, rng):
    marker = rng.random() * total_area
    triangle = triangles[-1]
    for candidate in triangles:
        if marker <= candidate[5] + candidate[4]:
            triangle = candidate
            break
    a, b, c, normal, _area, _cumulative = triangle
    u = math.sqrt(rng.random())
    v = rng.random()
    point = a * (1.0 - u) + b * (u * (1.0 - v)) + c * (u * v)
    return point, normal.copy()


def _insert_growth_keys(obj, final_scale, start_frame, growth_frames, rng):
    """Animate scale from nearly zero to full size with a restrained spring overshoot."""
    final_values = tuple(max(1e-4, float(abs(value))) for value in final_scale)
    obj.scale = (0.0001, 0.0001, 0.0001)
    obj.keyframe_insert(data_path="scale", frame=start_frame)
    overshoot_frame = start_frame + max(1, int(round(growth_frames * 0.72)))
    overshoot = rng.uniform(1.02, 1.10)
    obj.scale = tuple(value * overshoot for value in final_values)
    obj.keyframe_insert(data_path="scale", frame=overshoot_frame)
    obj.scale = final_values
    obj.keyframe_insert(data_path="scale", frame=start_frame + growth_frames)
    if obj.animation_data and obj.animation_data.action:
        action = obj.animation_data.action
        curves = getattr(action, "fcurves", [])
        for curve in curves:
            for key in curve.keyframe_points:
                key.interpolation = "BEZIER"
                key.handle_left_type = "AUTO_CLAMPED"
                key.handle_right_type = "AUTO_CLAMPED"


class VINMOTION_Settings(bpy.types.PropertyGroup):
    animation_type: EnumProperty(name="Animation", items=ANIMATION_ITEMS, default="BOB")
    animation_speed: FloatProperty(name="Speed", default=1.0, min=0.0, max=20.0, precision=2)
    animation_amount: FloatProperty(name="Amount", description="Height, pulse intensity, twist strength, or living surface deformation", default=0.5, min=0.0, max=10.0, precision=2)
    animation_phase: FloatProperty(name="Phase", description="Offset the animation clock to desynchronize this object", default=0.0, min=-100.0, max=100.0, precision=2)
    entity_noise_scale: FloatProperty(name="Organic Noise Scale", default=1.6, min=0.05, max=20.0, precision=2)
    entity_breathing: FloatProperty(name="Breathing", default=0.18, min=0.0, max=0.8, precision=2)
    entity_mask_threshold: FloatProperty(name="Mask Threshold", default=0.30, min=0.0, max=1.0, precision=2)
    entity_subdivision: IntProperty(name="Surface Detail", default=2, min=0, max=4)

    scatter_collection: PointerProperty(
        name="Source Collection",
        description="Separate source objects to instance over the active Plane",
        type=bpy.types.Collection,
    )
    spawn_source_collection: PointerProperty(
        name="Spawn Source Collection",
        description="Collection of separate source objects to copy onto the Plane",
        type=bpy.types.Collection,
    )
    spawn_count: IntProperty(name="Spawn Count", default=24, min=1, max=300)
    spawn_seed: IntProperty(name="Spawn Seed", default=71, min=0, max=9999999)
    spawn_min_scale: FloatProperty(name="Min Scale", default=0.55, min=0.01, max=10.0, precision=2)
    spawn_max_scale: FloatProperty(name="Max Scale", default=1.15, min=0.01, max=10.0, precision=2)
    spawn_surface_offset: FloatProperty(name="Surface Offset", default=0.02, min=0.0, max=10.0, precision=3)
    spawn_align_normal: BoolProperty(name="Align to Surface", default=True)
    spawn_animation_mode: EnumProperty(
        name="Motion Assignment",
        items=[
            ("RANDOM", "Random per Object", "Give each object its own random motion preset"),
            ("CURRENT", "Use Selected Motion", "Use the selected animation preset on each object"),
        ],
        default="RANDOM",
    )
    spawn_speed_variance: FloatProperty(name="Speed Variation", default=0.35, min=0.0, max=1.0, precision=2)
    spawn_amount_variance: FloatProperty(name="Amount Variation", default=0.25, min=0.0, max=1.0, precision=2)
    spawn_phase_range: FloatProperty(name="Phase Spread", default=6.283, min=0.0, max=50.0, precision=2)
    spawn_start_frame: IntProperty(name="First Spawn Frame", default=1, min=1, max=100000)
    spawn_stagger_frames: IntProperty(name="Spawn Stagger", default=72, min=0, max=100000)
    spawn_growth_frames: IntProperty(name="Growth Frames", default=16, min=1, max=1000)

    scatter_density: FloatProperty(name="Density", default=2.0, min=0.01, max=100.0, precision=2)
    scatter_noise_scale: FloatProperty(name="Noise Scale", default=1.4, min=0.01, max=50.0, precision=2)
    scatter_field_strength: FloatProperty(name="Field Motion", default=0.35, min=0.0, max=10.0, precision=2)
    scatter_speed: FloatProperty(name="Field Speed", default=1.0, min=0.0, max=20.0, precision=2)
    scatter_threshold: FloatProperty(name="Mask Threshold", default=0.52, min=0.0, max=1.0, precision=2)
    scatter_min_scale: FloatProperty(name="Min Scale", default=0.65, min=0.01, max=10.0, precision=2)
    scatter_max_scale: FloatProperty(name="Max Scale", default=1.25, min=0.01, max=10.0, precision=2)
    scatter_seed: IntProperty(name="Scatter Seed", default=17, min=0, max=9999999)


class VINMOTION_OT_build_animation(bpy.types.Operator):
    bl_idname = "vinmotion.build_animation"
    bl_label = "Build Animation Nodes"
    bl_description = "Create an editable Geometry Nodes animation graph on the active object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type not in {"MESH", "CURVE", "FONT", "SURFACE"}:
            self.report({"ERROR"}, "Select a mesh or curve object first")
            return {"CANCELLED"}
        settings = context.scene.vinmotion_settings
        try:
            tree, speed_socket, amount_socket, extra_sockets, phase_socket = _build_animation_group(settings, settings.animation_type)
            modifier = obj.modifiers.get("VIN Motion · Animation")
            if modifier is None or modifier.type != "NODES":
                modifier = obj.modifiers.new(name="VIN Motion · Animation", type="NODES")
            modifier.node_group = tree
            speed_id = getattr(speed_socket, "identifier", None)
            amount_id = getattr(amount_socket, "identifier", None)
            if speed_id:
                modifier[speed_id] = settings.animation_speed
            if amount_id:
                amount_limit = 0.95 if settings.animation_type == "PULSE" else (2.0 if settings.animation_type == "LIVING" else 10.0)
                modifier[amount_id] = min(settings.animation_amount, amount_limit)
            phase_id = getattr(phase_socket, "identifier", None)
            if phase_id:
                modifier[phase_id] = settings.animation_phase
            extra_values = {
                "noise_scale": settings.entity_noise_scale,
                "breathing": settings.entity_breathing,
                "threshold": settings.entity_mask_threshold,
                "subdivision": settings.entity_subdivision,
            }
            for key, socket in extra_sockets.items():
                identifier = getattr(socket, "identifier", None)
                if identifier:
                    modifier[identifier] = extra_values[key]
            obj["vinmotion_animation_type"] = settings.animation_type
            obj["vinmotion_animation_group"] = tree.name
            context.view_layer.update()
        except Exception as exc:
            self.report({"ERROR"}, f"Animation node creation failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Built {ANIMATION_LABELS[settings.animation_type]} nodes on {obj.name}")
        return {"FINISHED"}


class VINMOTION_OT_surface_spawn(bpy.types.Operator):
    bl_idname = "vinmotion.surface_spawn"
    bl_label = "Spawn Separate Objects"
    bl_description = "Create individually selectable copies across the active surface with independent motion and growth"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        plane = context.object
        settings = context.scene.vinmotion_settings
        source_collection = settings.spawn_source_collection
        if plane is None or plane.type != "MESH":
            self.report({"ERROR"}, "Select a target Plane or mesh surface first")
            return {"CANCELLED"}
        if source_collection is None:
            self.report({"ERROR"}, "Choose a Spawn Source Collection")
            return {"CANCELLED"}
        if plane.name in {item.name for item in source_collection.objects}:
            self.report({"ERROR"}, "Keep the target surface outside the Spawn Source Collection")
            return {"CANCELLED"}
        sources = [
            item for item in source_collection.objects
            if item.type in {"MESH", "CURVE", "FONT", "SURFACE"} and item.data is not None
        ]
        if not sources:
            self.report({"ERROR"}, "The Spawn Source Collection has no mesh or curve objects")
            return {"CANCELLED"}
        triangles, total_area = _surface_triangles(plane, context.evaluated_depsgraph_get())
        if not triangles or total_area <= 1e-10:
            self.report({"ERROR"}, "The target surface has no non-zero-area faces")
            return {"CANCELLED"}

        rng = random.Random(settings.spawn_seed)
        safe_min = max(0.01, min(settings.spawn_min_scale, settings.spawn_max_scale))
        safe_max = max(safe_min, settings.spawn_max_scale)
        result_collection = bpy.data.collections.new("VIN Motion · Surface Spawn")
        context.scene.collection.children.link(result_collection)
        animation_types = ("BOB", "SPIN", "PULSE", "TWIST", "LIVING")
        spawned = []
        failure = None
        try:
            for index in range(settings.spawn_count):
                source = rng.choice(sources)
                point, normal = _sample_surface_triangle(triangles, total_area, rng)
                spawn_obj = source.copy()
                spawn_obj.data = source.data.copy()
                spawn_obj.animation_data_clear()
                spawn_obj.parent = None
                for old_collection in list(spawn_obj.users_collection):
                    old_collection.objects.unlink(spawn_obj)
                result_collection.objects.link(spawn_obj)
                spawned.append(spawn_obj)

                _source_location, source_rotation, source_scale = source.matrix_world.decompose()
                scale_factor = rng.uniform(safe_min, safe_max)
                final_scale = tuple(abs(value) * scale_factor for value in source_scale)
                if settings.spawn_align_normal:
                    align_rotation = normal.to_track_quat("Z", "Y")
                    twist = Quaternion(normal, rng.uniform(0.0, math.tau))
                    spawn_obj.rotation_mode = "QUATERNION"
                    spawn_obj.rotation_quaternion = twist @ align_rotation @ source_rotation
                else:
                    spawn_obj.rotation_mode = "QUATERNION"
                    spawn_obj.rotation_quaternion = source_rotation
                spawn_obj.location = point + normal * settings.spawn_surface_offset
                spawn_obj.scale = final_scale
                spawn_obj.name = f"VIN Spawn · {source.name} · {index + 1:03d}"
                if spawn_obj.data is not None:
                    spawn_obj.data.name = spawn_obj.name + " Mesh"

                animation_type = (
                    rng.choice(animation_types)
                    if settings.spawn_animation_mode == "RANDOM"
                    else settings.animation_type
                )
                tree, speed_socket, amount_socket, extra_sockets, phase_socket = _build_animation_group(settings, animation_type)
                modifier = spawn_obj.modifiers.get("VIN Motion · Animation")
                if modifier is None or modifier.type != "NODES":
                    modifier = spawn_obj.modifiers.new(name="VIN Motion · Animation", type="NODES")
                modifier.node_group = tree

                speed_identifier = getattr(speed_socket, "identifier", None)
                amount_identifier = getattr(amount_socket, "identifier", None)
                phase_identifier = getattr(phase_socket, "identifier", None)
                speed_variance = rng.uniform(1.0-settings.spawn_speed_variance, 1.0+settings.spawn_speed_variance)
                amount_variance = rng.uniform(1.0-settings.spawn_amount_variance, 1.0+settings.spawn_amount_variance)
                speed_value = max(0.0, min(20.0, settings.animation_speed * speed_variance))
                amount_limit = 0.95 if animation_type == "PULSE" else (2.0 if animation_type == "LIVING" else 10.0)
                amount_value = max(0.0, min(amount_limit, settings.animation_amount * amount_variance))
                phase_value = rng.uniform(-settings.spawn_phase_range, settings.spawn_phase_range)
                if speed_identifier:
                    modifier[speed_identifier] = speed_value
                if amount_identifier:
                    modifier[amount_identifier] = amount_value
                if phase_identifier:
                    modifier[phase_identifier] = phase_value
                extra_values = {
                    "noise_scale": settings.entity_noise_scale,
                    "breathing": settings.entity_breathing,
                    "threshold": settings.entity_mask_threshold,
                    "subdivision": settings.entity_subdivision,
                }
                for key, socket in extra_sockets.items():
                    identifier = getattr(socket, "identifier", None)
                    if identifier:
                        modifier[identifier] = extra_values[key]

                start_frame = settings.spawn_start_frame
                if settings.spawn_stagger_frames:
                    start_frame += rng.randint(0, settings.spawn_stagger_frames)
                _insert_growth_keys(spawn_obj, final_scale, start_frame, settings.spawn_growth_frames, rng)
                spawn_obj["vinmotion_spawn_index"] = index + 1
                spawn_obj["vinmotion_animation_type"] = animation_type
                spawn_obj["vinmotion_speed"] = speed_value
                spawn_obj["vinmotion_phase"] = phase_value
                spawn_obj["vinmotion_source_object"] = source.name
                spawn_obj["vinmotion_spawn_collection"] = result_collection.name
        except Exception as exc:
            failure = exc

        if failure is not None:
            for item in spawned:
                if item.name in bpy.data.objects:
                    bpy.data.objects.remove(item, do_unlink=True)
            if result_collection.name in bpy.data.collections:
                bpy.data.collections.remove(result_collection)
            self.report({"ERROR"}, f"Surface Spawn failed: {failure}")
            return {"CANCELLED"}

        bpy.ops.object.select_all(action="DESELECT")
        for item in spawned:
            item.select_set(True)
        if spawned:
            context.view_layer.objects.active = spawned[0]
        context.scene.frame_set(context.scene.frame_current)
        self.report({"INFO"}, f"Spawned {len(spawned)} separate objects; each has its own animation modifier")
        return {"FINISHED"}


class VINMOTION_OT_build_scatter(bpy.types.Operator):
    bl_idname = "vinmotion.build_scatter"
    bl_label = "Build Noise Scatter"
    bl_description = "Scatter separate source objects on the active Plane using an animated Noise and Color Ramp mask"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != "MESH":
            self.report({"ERROR"}, "Select the mesh Plane first")
            return {"CANCELLED"}
        settings = context.scene.vinmotion_settings
        collection = settings.scatter_collection
        valid_types = {"MESH", "CURVE", "FONT", "SURFACE"}
        if collection is None or not any(source.type in valid_types for source in collection.objects):
            self.report({"ERROR"}, "Choose a Source Collection with separate mesh or curve objects")
            return {"CANCELLED"}
        if obj.name in {source.name for source in collection.objects}:
            self.report({"ERROR"}, "Keep the active Plane out of the Source Collection to avoid recursive scatter")
            return {"CANCELLED"}
        try:
            tree, sockets = _build_field_scatter_group(settings)
            modifier = obj.modifiers.get("VIN Motion · Noise Scatter")
            if modifier is None or modifier.type != "NODES":
                modifier = obj.modifiers.new(name="VIN Motion · Noise Scatter", type="NODES")
            modifier.node_group = tree
            values = {
                "density": settings.scatter_density,
                "noise_scale": settings.scatter_noise_scale,
                "field_strength": settings.scatter_field_strength,
                "speed": settings.scatter_speed,
                "threshold": settings.scatter_threshold,
                "seed": settings.scatter_seed,
                "min_scale": settings.scatter_min_scale,
                "max_scale": max(settings.scatter_min_scale, settings.scatter_max_scale),
            }
            for key, value in values.items():
                socket = sockets.get(key)
                identifier = getattr(socket, "identifier", None) if socket else None
                if identifier:
                    modifier[identifier] = value
            obj["vinmotion_source_collection"] = collection.name
            obj["vinmotion_mask"] = "Noise 4D -> Color Ramp Alpha -> Threshold -> Set Position Selection"
            context.view_layer.update()
        except Exception as exc:
            self.report({"ERROR"}, f"Noise Scatter creation failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Built Noise / Color Ramp Scatter on {obj.name}")
        return {"FINISHED"}


class VINMOTION_PT_main(bpy.types.Panel):
    bl_label = "VIN Motion Lab"
    bl_idname = "VINMOTION_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VIN Motion"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.vinmotion_settings

        box = layout.box()
        box.label(text="1 · Object Animation", icon="NODETREE")
        box.prop(settings, "animation_type")
        box.prop(settings, "animation_speed")
        box.prop(settings, "animation_phase")
        if settings.animation_type == "BOB":
            amount_label = "Height"
        elif settings.animation_type == "PULSE":
            amount_label = "Pulse Amount"
        elif settings.animation_type == "TWIST":
            amount_label = "Twist Strength"
        elif settings.animation_type == "LIVING":
            amount_label = "Deform Strength"
        else:
            amount_label = "Amount"
        box.prop(settings, "animation_amount", text=amount_label)
        if settings.animation_type == "LIVING":
            box.prop(settings, "entity_noise_scale")
            box.prop(settings, "entity_breathing")
            box.prop(settings, "entity_mask_threshold")
            box.prop(settings, "entity_subdivision")
            box.label(text="Needs mesh vertices to deform; higher Detail adds resolution.")
        box.operator("vinmotion.build_animation", text="Build Animation Nodes", icon="ACTION")

        box = layout.box()
        box.label(text="2 · Noise / Color Ramp Scatter", icon="FORCE_NOISE")
        box.label(text="Select a Plane, then choose a source collection")
        box.prop(settings, "scatter_collection")
        box.prop(settings, "scatter_density")
        box.prop(settings, "scatter_noise_scale")
        box.prop(settings, "scatter_threshold")
        box.prop(settings, "scatter_field_strength")
        box.prop(settings, "scatter_speed")
        row = box.row(align=True)
        row.prop(settings, "scatter_min_scale")
        row.prop(settings, "scatter_max_scale")
        box.prop(settings, "scatter_seed")
        box.operator("vinmotion.build_scatter", text="Build Scatter Nodes (Instances)", icon="NODETREE")

        box = layout.box()
        box.label(text="3 · Surface Spawn / Individual Motion", icon="PARTICLES")
        box.label(text="Creates separate objects, not shared instances")
        box.prop(settings, "spawn_source_collection")
        box.prop(settings, "spawn_count")
        box.prop(settings, "spawn_seed")
        box.prop(settings, "spawn_animation_mode")
        box.prop(settings, "spawn_align_normal")
        row = box.row(align=True)
        row.prop(settings, "spawn_min_scale")
        row.prop(settings, "spawn_max_scale")
        row = box.row(align=True)
        row.prop(settings, "spawn_speed_variance")
        row.prop(settings, "spawn_amount_variance")
        box.prop(settings, "spawn_phase_range")
        box.prop(settings, "spawn_surface_offset")
        row = box.row(align=True)
        row.prop(settings, "spawn_start_frame")
        row.prop(settings, "spawn_stagger_frames")
        box.prop(settings, "spawn_growth_frames")
        box.operator("vinmotion.surface_spawn", text="Spawn Separate Objects", icon="OUTLINER_OB_GROUP_INSTANCE")
        layout.separator()
        layout.label(text="Standalone add-on — no effect on VIN Procedural Lab.")


CLASSES = (
    VINMOTION_Settings,
    VINMOTION_OT_build_animation,
    VINMOTION_OT_surface_spawn,
    VINMOTION_OT_build_scatter,
    VINMOTION_PT_main,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.vinmotion_settings = PointerProperty(type=VINMOTION_Settings)


def unregister():
    if hasattr(bpy.types.Scene, "vinmotion_settings"):
        del bpy.types.Scene.vinmotion_settings
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass


if __name__ == "__main__":
    register()
