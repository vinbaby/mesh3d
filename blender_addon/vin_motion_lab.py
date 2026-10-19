bl_info = {
    "name": "VIN Motion Lab",
    "author": "VIN Studio",
    "version": (0, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > VIN Motion",
    "description": "Standalone Geometry Nodes animation and noise-mask scatter tools",
    "category": "Animation",
}

import bpy
import math
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
    amount_limit = 0.95 if animation_type == "PULSE" else 10.0
    amount_default = min(settings.animation_amount, amount_limit)
    if animation_type == "TWIST":
        amount_label = "Twist Strength"
    elif animation_type == "PULSE":
        amount_label = "Pulse Amount"
    elif animation_type == "BOB":
        amount_label = "Height"
    amount_socket = _add_interface_socket(
        tree, amount_label, "INPUT", "NodeSocketFloat",
        default=amount_default, min_value=0.0, max_value=amount_limit,
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

    if animation_type == "BOB":
        sine = _math_node(nodes, "SINE", "Smooth oscillation", (-420, -260))
        amplitude = _math_node(nodes, "MULTIPLY", "Apply height", (-190, -260))
        combine = nodes.new("ShaderNodeCombineXYZ")
        combine.location = (40, -160)
        set_position = nodes.new("GeometryNodeSetPosition")
        set_position.location = (360, 100)
        set_position.label = "Move entire geometry"
        links.new(time_mul.outputs[0], sine.inputs[0])
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
        links.new(time_mul.outputs[0], combine.inputs["Z"])
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
        links.new(time_mul.outputs[0], sine.inputs[0])
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
        links.new(time_mul.outputs[0], angle_add.inputs[1])

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

    else:
        bpy.data.node_groups.remove(tree)
        raise ValueError(f"Unsupported animation type: {animation_type}")

    tree["vinmotion_version"] = "0.1.0"
    tree["vinmotion_animation_type"] = animation_type
    tree["vinmotion_speed_socket"] = getattr(speed_socket, "identifier", "Speed")
    tree["vinmotion_amount_socket"] = getattr(amount_socket, "identifier", amount_label)
    tree["vinmotion_geometry_input"] = getattr(geo_in, "identifier", "Geometry")
    tree["vinmotion_geometry_output"] = getattr(geo_out, "identifier", "Geometry")
    return tree, speed_socket, amount_socket



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

    tree["vinmotion_version"] = "0.1.0"
    tree["vinmotion_feature"] = "noise_color_ramp_scatter"
    tree["vinmotion_source_collection"] = collection.name
    return tree, sockets


class VINMOTION_Settings(bpy.types.PropertyGroup):
    animation_type: EnumProperty(name="Animation", items=ANIMATION_ITEMS, default="BOB")
    animation_speed: FloatProperty(name="Speed", default=1.0, min=0.0, max=20.0, precision=2)
    animation_amount: FloatProperty(name="Amount", description="Height, pulse intensity, or twist strength", default=0.5, min=0.0, max=10.0, precision=2)

    scatter_collection: PointerProperty(
        name="Source Collection",
        description="Separate source objects to instance over the active Plane",
        type=bpy.types.Collection,
    )
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
            tree, speed_socket, amount_socket = _build_animation_group(settings, settings.animation_type)
            modifier = obj.modifiers.get("VIN Motion · Animation")
            if modifier is None or modifier.type != "NODES":
                modifier = obj.modifiers.new(name="VIN Motion · Animation", type="NODES")
            modifier.node_group = tree
            speed_id = getattr(speed_socket, "identifier", None)
            amount_id = getattr(amount_socket, "identifier", None)
            if speed_id:
                modifier[speed_id] = settings.animation_speed
            if amount_id:
                modifier[amount_id] = min(settings.animation_amount, 0.95 if settings.animation_type == "PULSE" else 10.0)
            obj["vinmotion_animation_type"] = settings.animation_type
            obj["vinmotion_animation_group"] = tree.name
            context.view_layer.update()
        except Exception as exc:
            self.report({"ERROR"}, f"Animation node creation failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Built {ANIMATION_LABELS[settings.animation_type]} nodes on {obj.name}")
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
        if settings.animation_type == "BOB":
            amount_label = "Height"
        elif settings.animation_type == "PULSE":
            amount_label = "Pulse Amount"
        elif settings.animation_type == "TWIST":
            amount_label = "Twist Strength"
        else:
            amount_label = "Amount"
        box.prop(settings, "animation_amount", text=amount_label)
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
        box.operator("vinmotion.build_scatter", text="Build Scatter Nodes", icon="NODETREE")
        layout.separator()
        layout.label(text="Standalone add-on — no effect on VIN Procedural Lab.")


CLASSES = (
    VINMOTION_Settings,
    VINMOTION_OT_build_animation,
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
