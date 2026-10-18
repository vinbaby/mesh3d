bl_info = {
    "name": "VIN Procedural Lab",
    "author": "VIN Studio",
    "version": (0, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > VIN Lab",
    "description": "Generate procedural 3D shapes and build animated Geometry Nodes setups",
    "category": "Add Mesh",
}

import bpy
import math
import random
from mathutils import Vector, Quaternion
from bpy.props import (
    EnumProperty,
    IntProperty,
    FloatProperty,
    BoolProperty,
)


SHAPE_ITEMS = [
    ("RANDOM", "Random Shape", "Pick a shape family from the current seed"),
    ("TWISTED_COLUMN", "Twisted Column", "A twisted, ring-based parametric solid"),
    ("ORBIT_CAGE", "Orbital Cage", "Intersecting tubular orbit loops"),
    ("ORGANIC_BLOB", "Organic Blob", "A deformed UV-like closed surface"),
    ("CRYSTAL_CLUSTER", "Crystal Cluster", "A cluster of tapered, faceted crystals"),
    ("BRANCHING_FORM", "Branching Form", "A recursively generated tubular structure"),
]

ANIMATION_ITEMS = [
    ("BOB", "Bob / Float", "Move geometry up and down over time"),
    ("SPIN", "Continuous Spin", "Rotate the whole geometry over time"),
    ("PULSE", "Scale Pulse", "Scale the geometry rhythmically"),
    ("TWIST", "Animated Twist", "Twist points around the Z axis over time"),
]
ANIMATION_LABELS = {identifier: label for identifier, label, _description in ANIMATION_ITEMS}

SHAPE_NAMES = {
    "TWISTED_COLUMN": "Twisted Column",
    "ORBIT_CAGE": "Orbital Cage",
    "ORGANIC_BLOB": "Organic Blob",
    "CRYSTAL_CLUSTER": "Crystal Cluster",
    "BRANCHING_FORM": "Branching Form",
}


def _append_tube(
    vertices,
    faces,
    points,
    radius,
    sides=6,
    closed=False,
    cap_ends=True,
):
    """Append a tube around a polyline. Points are mathutils.Vector instances."""
    points = [Vector(point) for point in points]
    count = len(points)
    if count < 2 or radius <= 0:
        return

    first_ring = len(vertices)
    z_axis = Vector((0.0, 0.0, 1.0))
    x_axis = Vector((1.0, 0.0, 0.0))
    ring_count = count

    for i, point in enumerate(points):
        if closed:
            tangent = (points[(i + 1) % count] - points[(i - 1) % count]).normalized()
        elif i == 0:
            tangent = (points[1] - points[0]).normalized()
        elif i == count - 1:
            tangent = (points[-1] - points[-2]).normalized()
        else:
            tangent = (points[i + 1] - points[i - 1]).normalized()

        helper = z_axis if abs(tangent.dot(z_axis)) < 0.88 else x_axis
        normal = tangent.cross(helper)
        if normal.length < 1e-8:
            normal = tangent.cross(x_axis)
        normal.normalize()
        binormal = tangent.cross(normal).normalized()

        for j in range(sides):
            angle = math.tau * j / sides
            offset = radius * (normal * math.cos(angle) + binormal * math.sin(angle))
            vertices.append(tuple(point + offset))

    span_count = ring_count if closed else ring_count - 1
    for i in range(span_count):
        next_i = (i + 1) % ring_count
        for j in range(sides):
            next_j = (j + 1) % sides
            a = first_ring + i * sides + j
            b = first_ring + i * sides + next_j
            c = first_ring + next_i * sides + next_j
            d = first_ring + next_i * sides + j
            faces.append((a, b, c, d))

    if cap_ends and not closed:
        faces.append(tuple(first_ring + j for j in range(sides - 1, -1, -1)))
        last_start = first_ring + (ring_count - 1) * sides
        faces.append(tuple(last_start + j for j in range(sides)))


def _build_twisted_column(settings, rng):
    vertices, faces = [], []
    rings = max(12, settings.detail * 2)
    sides = max(8, settings.detail)
    radius = settings.size * 0.34
    height = settings.size * 1.5
    phase = rng.random() * math.tau

    for row in range(rings + 1):
        t = row / rings
        z = -height * 0.5 + height * t
        local_radius = radius * (
            1.0 + 0.16 * math.sin(t * math.tau * 2.0 + phase)
            + 0.05 * math.sin(t * math.tau * 4.0)
        )
        turn = settings.twist * (t - 0.5)
        for col in range(sides):
            a = math.tau * col / sides + turn
            r = local_radius * (1.0 + 0.035 * math.cos(3.0 * a + phase))
            vertices.append((r * math.cos(a), r * math.sin(a), z))

    for row in range(rings):
        for col in range(sides):
            a = row * sides + col
            b = row * sides + (col + 1) % sides
            c = (row + 1) * sides + (col + 1) % sides
            d = (row + 1) * sides + col
            faces.append((a, b, c, d))

    faces.append(tuple(range(sides - 1, -1, -1)))
    faces.append(tuple(rings * sides + col for col in range(sides)))
    return vertices, faces


def _build_organic_blob(settings, rng):
    vertices, faces = [], []
    rings = max(8, settings.detail)
    sides = max(16, settings.detail * 2)
    radius = settings.size * 0.5
    phase = [rng.random() * math.tau for _ in range(4)]

    vertices.append((0.0, 0.0, radius * (1.0 + 0.08 * math.sin(phase[0]))))
    for row in range(1, rings):
        theta = math.pi * row / rings
        for col in range(sides):
            phi = math.tau * col / sides
            wave = (
                0.11 * math.sin(3.0 * phi + phase[0]) * math.sin(2.0 * theta + phase[1])
                + 0.07 * math.cos(5.0 * phi + phase[2]) * math.sin(3.0 * theta)
                + 0.035 * math.sin(7.0 * phi + theta + phase[3])
            )
            local_radius = radius * (1.0 + wave)
            x = local_radius * math.sin(theta) * math.cos(phi)
            y = local_radius * math.sin(theta) * math.sin(phi)
            z = local_radius * math.cos(theta)
            vertices.append((x, y, z))

    bottom_index = len(vertices)
    vertices.append((0.0, 0.0, -radius * (1.0 + 0.08 * math.sin(phase[1]))))

    first_ring = 1
    for col in range(sides):
        faces.append((0, first_ring + col, first_ring + (col + 1) % sides))

    for row in range(rings - 2):
        upper = 1 + row * sides
        lower = upper + sides
        for col in range(sides):
            nxt = (col + 1) % sides
            faces.append((upper + col, lower + col, lower + nxt, upper + nxt))

    last_ring = 1 + (rings - 2) * sides
    for col in range(sides):
        faces.append((last_ring + col, bottom_index, last_ring + (col + 1) % sides))
    return vertices, faces


def _build_crystal_cluster(settings, rng):
    vertices, faces = [], []
    count = max(3, settings.detail // 2)
    scale = settings.size
    sides = max(5, min(9, settings.detail // 3))
    for index in range(count):
        angle = (index / count) * math.tau + rng.uniform(-0.28, 0.28)
        distance = 0.0 if index == 0 else scale * rng.uniform(0.08, 0.32)
        cx = math.cos(angle) * distance
        cy = math.sin(angle) * distance
        height = scale * rng.uniform(0.48, 1.05)
        base_radius = scale * rng.uniform(0.075, 0.17)
        lean_x = rng.uniform(-0.15, 0.15) * scale
        lean_y = rng.uniform(-0.15, 0.15) * scale
        twist = rng.uniform(0.0, math.tau)
        start = len(vertices)

        for z_factor, radius_factor, shift_x, shift_y in (
            (0.0, 1.0, 0.0, 0.0),
            (0.62, 0.66, lean_x * 0.55, lean_y * 0.55),
        ):
            for side in range(sides):
                a = math.tau * side / sides + twist
                vertices.append((
                    cx + shift_x + base_radius * radius_factor * math.cos(a),
                    cy + shift_y + base_radius * radius_factor * math.sin(a),
                    -height * 0.32 + height * z_factor,
                ))

        tip_index = len(vertices)
        vertices.append((cx + lean_x, cy + lean_y, height * 0.68))
        faces.append(tuple(start + side for side in range(sides - 1, -1, -1)))
        for side in range(sides):
            nxt = (side + 1) % sides
            a, b = start + side, start + nxt
            c, d = start + sides + nxt, start + sides + side
            faces.append((a, b, c, d))
            faces.append((d, c, tip_index))
    return vertices, faces


def _build_orbit_cage(settings, rng):
    vertices, faces = [], []
    radius = settings.size * 0.43
    samples = max(32, settings.detail * 2)
    tube_radius = settings.size * 0.012
    base_normals = [
        Vector((0.0, 0.0, 1.0)),
        Vector((1.0, 0.0, 0.0)),
        Vector((0.0, 1.0, 0.0)),
    ]
    base_normals.extend(
        Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized()
        for _ in range(max(2, settings.detail // 8))
    )

    for normal in base_normals:
        normal.normalize()
        rotation = Vector((0.0, 0.0, 1.0)).rotation_difference(normal)
        loop_radius = radius * rng.uniform(0.72, 1.08)
        ellipse_y = loop_radius * rng.uniform(0.94, 1.06)
        phase = rng.uniform(0.0, math.tau)
        points = []
        for index in range(samples):
            angle = math.tau * index / samples + phase
            p = Vector((
                loop_radius * math.cos(angle),
                ellipse_y * math.sin(angle),
                0.0,
            ))
            p.rotate(rotation)
            points.append(p)
        _append_tube(vertices, faces, points, tube_radius, sides=5, closed=True, cap_ends=False)
    return vertices, faces


def _build_branching_form(settings, rng):
    vertices, faces = [], []
    unit = settings.size
    max_depth = max(1, min(4, settings.branch_depth))
    segments = 5
    tube_sides = max(5, min(8, settings.detail // 3))

    def grow(start, direction, length, depth, radius):
        points = [Vector(start)]
        current = Vector(start)
        travel = Vector(direction).normalized()
        for _ in range(segments):
            jitter = Vector((
                rng.uniform(-0.22, 0.22),
                rng.uniform(-0.22, 0.22),
                rng.uniform(-0.10, 0.20),
            ))
            travel = (travel + jitter).normalized()
            current = current + travel * (length / segments)
            points.append(current.copy())
        _append_tube(
            vertices, faces, points, radius, sides=tube_sides, closed=False, cap_ends=True
        )
        if depth <= 0:
            return

        end = points[-1]
        axis = travel.cross(Vector((0.0, 0.0, 1.0)))
        if axis.length < 1e-6:
            axis = travel.cross(Vector((1.0, 0.0, 0.0)))
        axis.normalize()
        angle = math.radians(rng.uniform(22.0, 42.0))
        for sign in (-1, 1):
            child_dir = travel.copy()
            child_dir.rotate(Quaternion(axis, angle * sign))
            child_dir.rotate(Quaternion(travel, rng.uniform(-0.25, 0.25)))
            grow(end, child_dir, length * rng.uniform(0.62, 0.78), depth - 1, radius * 0.68)

    grow(
        Vector((0.0, 0.0, -unit * 0.55)),
        Vector((0.0, 0.0, 1.0)),
        unit * 0.88,
        max_depth,
        unit * 0.035,
    )
    return vertices, faces


def _new_mesh_object(context, name, vertices, faces, seed):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    context.collection.objects.link(obj)

    rng = random.Random(seed ^ 0x5A17)
    material = bpy.data.materials.new(name=f"VINLAB · {name}")
    material.diffuse_color = (
        rng.uniform(0.12, 0.85),
        rng.uniform(0.25, 0.9),
        rng.uniform(0.3, 1.0),
        1.0,
    )
    mesh.materials.append(material)
    obj.color = material.diffuse_color
    for polygon in mesh.polygons:
        polygon.use_smooth = False

    for other in context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj
    return obj


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
        name=f"VINLAB · {friendly}", type="GeometryNodeTree"
    )
    if hasattr(tree, "is_modifier"):
        tree.is_modifier = True

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

    tree["vinlab_version"] = "0.1.0"
    tree["vinlab_animation_type"] = animation_type
    tree["vinlab_speed_socket"] = getattr(speed_socket, "identifier", "Speed")
    tree["vinlab_amount_socket"] = getattr(amount_socket, "identifier", amount_label)
    tree["vinlab_geometry_input"] = getattr(geo_in, "identifier", "Geometry")
    tree["vinlab_geometry_output"] = getattr(geo_out, "identifier", "Geometry")
    return tree, speed_socket, amount_socket


class VINLAB_Settings(bpy.types.PropertyGroup):
    shape_type: EnumProperty(
        name="Shape Family", items=SHAPE_ITEMS, default="RANDOM"
    )
    seed: IntProperty(name="Seed", default=17, min=0, max=9999999)
    detail: IntProperty(name="Detail", description="Higher values add more geometry", default=18, min=6, max=48)
    size: FloatProperty(name="Size", default=2.0, min=0.2, max=20.0, precision=2)
    twist: FloatProperty(name="Twist", description="Twist strength for twisted columns", default=2.6, min=-12.0, max=12.0, precision=2)
    branch_depth: IntProperty(name="Branch Depth", default=3, min=1, max=4)
    animation_type: EnumProperty(
        name="Animation", items=ANIMATION_ITEMS, default="BOB"
    )
    animation_speed: FloatProperty(name="Speed", default=1.0, min=0.0, max=20.0, precision=2)
    animation_amount: FloatProperty(name="Amount", description="Height, pulse intensity, or twist strength", default=0.5, min=0.0, max=10.0, precision=2)


class VINLAB_OT_generate_shape(bpy.types.Operator):
    bl_idname = "vinlab.generate_shape"
    bl_label = "Generate Shape"
    bl_description = "Generate a new procedural 3D mesh from the current parameters"
    bl_options = {"REGISTER", "UNDO"}

    new_variation: BoolProperty(default=False, options={"HIDDEN"})

    def execute(self, context):
        settings = context.scene.vinlab_settings
        if self.new_variation:
            settings.seed = (settings.seed + 1) % 10000000
        rng = random.Random(settings.seed)

        shape_type = settings.shape_type
        if shape_type == "RANDOM":
            shape_type = rng.choice(list(SHAPE_NAMES.keys()))

        builders = {
            "TWISTED_COLUMN": _build_twisted_column,
            "ORBIT_CAGE": _build_orbit_cage,
            "ORGANIC_BLOB": _build_organic_blob,
            "CRYSTAL_CLUSTER": _build_crystal_cluster,
            "BRANCHING_FORM": _build_branching_form,
        }
        builder = builders.get(shape_type)
        if builder is None:
            self.report({"ERROR"}, "Unknown shape family")
            return {"CANCELLED"}

        try:
            vertices, faces = builder(settings, rng)
            if not vertices or not faces:
                self.report({"ERROR"}, "The shape generator returned empty geometry")
                return {"CANCELLED"}
            obj = _new_mesh_object(
                context, f"VINLAB · {SHAPE_NAMES[shape_type]}", vertices, faces, settings.seed
            )
        except Exception as exc:
            self.report({"ERROR"}, f"Shape generation failed: {exc}")
            return {"CANCELLED"}

        obj["vinlab_shape_type"] = shape_type
        obj["vinlab_seed"] = settings.seed
        obj["vinlab_version"] = "0.1.0"
        self.report(
            {"INFO"},
            f"Generated {SHAPE_NAMES[shape_type]} · {len(vertices):,} verts / {len(faces):,} faces",
        )
        return {"FINISHED"}


class VINLAB_OT_build_animation(bpy.types.Operator):
    bl_idname = "vinlab.build_animation"
    bl_label = "Build Geometry Nodes"
    bl_description = "Create a real Geometry Nodes graph for the selected animation on the active object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.object
        if obj is None:
            self.report({"ERROR"}, "Select a mesh or curve object first")
            return {"CANCELLED"}

        settings = context.scene.vinlab_settings
        try:
            tree, speed_socket, amount_socket = _build_animation_group(
                settings, settings.animation_type
            )
            modifier = obj.modifiers.get("VINLAB Animation")
            if modifier is None or modifier.type != "NODES":
                modifier = obj.modifiers.new(name="VINLAB Animation", type="NODES")
            modifier.node_group = tree

            speed_id = getattr(speed_socket, "identifier", None)
            amount_id = getattr(amount_socket, "identifier", None)
            if speed_id:
                modifier[speed_id] = settings.animation_speed
            if amount_id:
                modifier[amount_id] = min(
                    settings.animation_amount,
                    0.95 if settings.animation_type == "PULSE" else 10.0,
                )

            obj["vinlab_animation_type"] = settings.animation_type
            obj["vinlab_animation_node_group"] = tree.name
            context.view_layer.update()
        except Exception as exc:
            self.report({"ERROR"}, f"Geometry Nodes creation failed: {exc}")
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            f"Created {ANIMATION_LABELS[settings.animation_type]} nodes on {obj.name}",
        )
        return {"FINISHED"}


class VINLAB_OT_randomize_seed(bpy.types.Operator):
    bl_idname = "vinlab.randomize_seed"
    bl_label = "New Random Variation"
    bl_description = "Change the seed and generate another procedural shape"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        result = bpy.ops.vinlab.generate_shape(new_variation=True)
        return result


class VINLAB_PT_main(bpy.types.Panel):
    bl_label = "VIN Procedural Lab"
    bl_idname = "VINLAB_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VIN Lab"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.vinlab_settings

        box = layout.box()
        box.label(text="1 · Procedural Shape Generator", icon="MESH_ICOSPHERE")
        box.prop(settings, "shape_type")
        box.prop(settings, "seed")
        box.prop(settings, "detail")
        box.prop(settings, "size")
        if settings.shape_type in {"RANDOM", "TWISTED_COLUMN"}:
            box.prop(settings, "twist")
        if settings.shape_type in {"RANDOM", "BRANCHING_FORM"}:
            box.prop(settings, "branch_depth")
        row = box.row(align=True)
        row.operator("vinlab.generate_shape", text="Generate Shape", icon="MESH_DATA")
        row.operator("vinlab.randomize_seed", text="New Variant", icon="FILE_REFRESH")

        box = layout.box()
        box.label(text="2 · Animation Builder", icon="NODETREE")
        box.prop(settings, "animation_type")
        box.prop(settings, "animation_speed")
        if settings.animation_type == "BOB":
            amount_caption = "Height"
        elif settings.animation_type == "PULSE":
            amount_caption = "Pulse Amount"
        elif settings.animation_type == "TWIST":
            amount_caption = "Twist Strength"
        else:
            amount_caption = None
        if amount_caption:
            box.prop(settings, "animation_amount", text=amount_caption)
        box.operator("vinlab.build_animation", text="Build Geometry Nodes", icon="NODETREE")
        box.label(text="Applies to the active object", icon="INFO")

        layout.separator()
        layout.label(text="Generated node groups stay editable.")
        layout.label(text="Scene Time drives the animation.")


CLASSES = (
    VINLAB_Settings,
    VINLAB_OT_generate_shape,
    VINLAB_OT_build_animation,
    VINLAB_OT_randomize_seed,
    VINLAB_PT_main,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.vinlab_settings = bpy.props.PointerProperty(type=VINLAB_Settings)


def unregister():
    if hasattr(bpy.types.Scene, "vinlab_settings"):
        del bpy.types.Scene.vinlab_settings
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
