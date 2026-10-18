bl_info = {
    "name": "VIN Procedural Lab",
    "author": "VIN Studio",
    "version": (0, 6, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > VIN Lab",
    "description": "Generate procedural 3D shapes, future sculptures, and Geometry Nodes animations",
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
    ("RANDOM", "Random Object", "Randomly choose an individual procedural artifact family"),
    ("TWISTED_COLUMN", "Twisted Column", "A twisted, ring-based parametric solid"),
    ("ORBIT_CAGE", "Orbital Cage", "Intersecting tubular orbit loops"),
    ("ORGANIC_BLOB", "Organic Blob", "A deformed UV-like closed surface"),
    ("CRYSTAL_CLUSTER", "Crystal Cluster", "A cluster of tapered, faceted crystals"),
    ("BRANCHING_FORM", "Branching Form", "A recursively generated tubular structure"),
    ("FUTURE_SCULPTURE", "Future Sculpture", "Layered twisted loops and organic sci-fi sculpture tubes"),
    ("CYBER_MODULE", "Cyber Module", "A stacked hard-surface artifact with colored panels and vent ribs"),
    ("FOLDED_RIBBON", "Folded Ribbon", "A broad twisting metallic ribbon with a sharp sculptural silhouette"),
    ("PRISM_REACTOR", "Prism Reactor", "An angular reactor core inside intersecting open frames"),
    ("FACETED_TOTEM", "Faceted Totem", "Layered polygonal plates, facets, fins and micro-ribs"),
    ("HEX_ARMOR", "Hex Armor", "A raised honeycomb armor shield with deep dark seams"),
    ("CIRCUIT_CORE", "Circuit Core", "A layered electronic reactor plate with physical circuit traces"),
    ("ORBITAL_PARTICLE", "Orbital Particle", "A crescent cloud of metallic pearls linked by filaments"),
    ("CELLULAR_VOID", "Cellular Void", "A porous organic-metal exoskeleton with irregular holes"),
    ("SPIKE_BLOOM", "Spike Bloom", "A dark orb with randomly tapered mechanical spines"),
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
    "FUTURE_SCULPTURE": "Future Sculpture",
    "CYBER_MODULE": "Cyber Module",
    "FOLDED_RIBBON": "Folded Ribbon",
    "PRISM_REACTOR": "Prism Reactor",
    "FACETED_TOTEM": "Faceted Totem",
    "HEX_ARMOR": "Hex Armor",
    "CIRCUIT_CORE": "Circuit Core",
    "ORBITAL_PARTICLE": "Orbital Particle",
    "CELLULAR_VOID": "Cellular Void",
    "SPIKE_BLOOM": "Spike Bloom",
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


def _build_future_sculpture(settings, rng):
    """Layer several different parametric tube families into one abstract sculpture."""
    vertices, faces = [], []
    unit = settings.size
    samples = max(64, settings.detail * 6)
    tube_sides = max(6, min(10, settings.detail // 2))
    loop_count = 3 + min(3, settings.detail // 12)
    phase = rng.uniform(0.0, math.tau)

    # 1) Main flowing spatial loop: an asymmetric Lissajous / torus-knot hybrid.
    radius = unit * rng.uniform(0.34, 0.46)
    loops = rng.choice((2, 3, 4))
    vertical_wave = rng.uniform(0.22, 0.42) * unit
    points = []
    for index in range(samples):
        t = math.tau * index / samples
        breathing = 1.0 + 0.15 * math.sin(3.0 * t + phase) + 0.06 * math.cos(5.0 * t)
        x = radius * breathing * math.cos(loops * t + phase)
        y = radius * (0.86 + 0.12 * math.cos(2.0 * t)) * math.sin((loops - 1) * t)
        z = vertical_wave * math.sin(2.0 * t + phase * 0.7) + unit * 0.08 * math.sin(5.0 * t)
        points.append(Vector((x, y, z)))
    _append_tube(vertices, faces, points, unit * 0.024, sides=tube_sides, closed=True, cap_ends=False)

    # 2) Tilted orbit rings. Each one gets a different plane and slightly lobed radius.
    for ring_index in range(loop_count):
        axis = Vector((
            rng.uniform(-1.0, 1.0),
            rng.uniform(-1.0, 1.0),
            rng.uniform(-1.0, 1.0),
        ))
        if axis.length < 1e-5:
            axis = Vector((0.0, 0.0, 1.0))
        axis.normalize()
        rotation = Vector((0.0, 0.0, 1.0)).rotation_difference(axis)
        ring_radius = unit * rng.uniform(0.24, 0.49)
        ring_phase = rng.uniform(0.0, math.tau)
        ring_points = []
        for index in range(samples):
            t = math.tau * index / samples
            r = ring_radius * (
                1.0 + 0.09 * math.cos(3.0 * t + ring_phase)
                + 0.035 * math.sin(5.0 * t)
            )
            point = Vector((
                r * math.cos(t + ring_phase),
                r * rng.uniform(0.97, 1.03) * math.sin(t + ring_phase),
                unit * 0.10 * math.sin(2.0 * t + ring_phase),
            ))
            point.rotate(rotation)
            ring_points.append(point)
        _append_tube(
            vertices, faces, ring_points,
            unit * rng.uniform(0.010, 0.019),
            sides=max(5, tube_sides - 2), closed=True, cap_ends=False,
        )

    # 3) A rising helical strand crossing the loops gives the silhouette height.
    turns = rng.uniform(1.35, 2.6)
    helix_points = []
    for index in range(samples):
        t = index / (samples - 1)
        angle = math.tau * turns * t + phase
        radius_here = unit * (0.16 + 0.16 * math.sin(math.pi * t))
        helix_points.append(Vector((
            radius_here * math.cos(angle),
            radius_here * math.sin(angle),
            unit * (t - 0.5) * 0.95,
        )))
    _append_tube(
        vertices, faces, helix_points, unit * 0.017,
        sides=max(5, tube_sides - 1), closed=False, cap_ends=True,
    )

    # 4) Add a small number of graceful off-axis tendrils, not a dense fractal.
    for tendril_index in range(max(1, settings.detail // 14)):
        start_angle = rng.uniform(0.0, math.tau)
        start = Vector((
            unit * 0.22 * math.cos(start_angle),
            unit * 0.22 * math.sin(start_angle),
            rng.uniform(-0.25, 0.25) * unit,
        ))
        length = unit * rng.uniform(0.28, 0.52)
        tendril_points = []
        tendril_samples = max(12, samples // 3)
        drift_x, drift_y = rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4)
        sway_frequency = rng.uniform(1.0, 2.0)
        for index in range(tendril_samples):
            t = index / (tendril_samples - 1)
            sway = math.sin(t * math.pi * sway_frequency + phase) * unit * 0.11
            tendril_points.append(Vector((
                start.x + drift_x * length * t + sway,
                start.y + drift_y * length * t - sway * 0.45,
                start.z + length * (t - 0.35) + unit * 0.08 * math.sin(t * math.tau + phase),
            )))
        _append_tube(
            vertices, faces, tendril_points,
            unit * rng.uniform(0.008, 0.014),
            sides=max(5, tube_sides - 2), closed=False, cap_ends=True,
        )

    return vertices, faces


def _append_block(vertices, faces, center, dimensions, rotation_z=0.0, tilt_x=0.0, tilt_y=0.0):
    """Append one independently rotated hard-surface block into a shared mesh."""
    start = len(vertices)
    half_x, half_y, half_z = (max(0.01, float(value)) * 0.5 for value in dimensions)
    local = [
        (-half_x,-half_y,-half_z),(half_x,-half_y,-half_z),
        (half_x,half_y,-half_z),(-half_x,half_y,-half_z),
        (-half_x,-half_y,half_z),(half_x,-half_y,half_z),
        (half_x,half_y,half_z),(-half_x,half_y,half_z),
    ]
    qz = Quaternion(Vector((0.0,0.0,1.0)), rotation_z)
    qx = Quaternion(Vector((1.0,0.0,0.0)), tilt_x)
    qy = Quaternion(Vector((0.0,1.0,0.0)), tilt_y)
    origin = Vector(center)
    for xyz in local:
        point = Vector(xyz)
        point.rotate(qx)
        point.rotate(qy)
        point.rotate(qz)
        vertices.append(tuple(origin + point))
    faces.extend((
        (start+0,start+3,start+2,start+1),
        (start+4,start+5,start+6,start+7),
        (start+0,start+1,start+5,start+4),
        (start+1,start+2,start+6,start+5),
        (start+2,start+3,start+7,start+6),
        (start+3,start+0,start+4,start+7),
    ))


def _transform_local_offset(offset, rotation_z=0.0, tilt_x=0.0, tilt_y=0.0):
    point = Vector(offset)
    point.rotate(Quaternion(Vector((1.0,0.0,0.0)), tilt_x))
    point.rotate(Quaternion(Vector((0.0,1.0,0.0)), tilt_y))
    point.rotate(Quaternion(Vector((0.0,0.0,1.0)), rotation_z))
    return point


def _append_recessed_box(vertices, faces, center, dimensions, inset_size, recess_depth,
                         rotation_z=0.0, tilt_x=0.0, tilt_y=0.0):
    """Append a box shell with a real rectangular cavity on its -Y face."""
    hx, hy, hz = (max(0.02, float(v))*0.5 for v in dimensions)
    inset_w = min(max(0.05, float(inset_size[0])), hx*1.52)
    inset_h = min(max(0.05, float(inset_size[1])), hz*1.52)
    iw, ih = inset_w*0.5, inset_h*0.5
    depth = min(max(0.015, float(recess_depth)), hy*0.62)
    local = [
        (-hx,-hy,-hz), (hx,-hy,-hz), (hx,-hy,hz), (-hx,-hy,hz),
        (-hx,hy,-hz), (hx,hy,-hz), (hx,hy,hz), (-hx,hy,hz),
        (-iw,-hy,-ih), (iw,-hy,-ih), (iw,-hy,ih), (-iw,-hy,ih),
        (-iw,-hy+depth,-ih), (iw,-hy+depth,-ih),
        (iw,-hy+depth,ih), (-iw,-hy+depth,ih),
    ]
    base = len(vertices)
    origin = Vector(center)
    for co in local:
        vertices.append(tuple(origin + _transform_local_offset(co, rotation_z, tilt_x, tilt_y)))
    face_defs = [
        (0,4,5,1), (3,2,6,7), (0,3,7,4), (1,5,6,2), (4,5,6,7),
        (0,1,9,8), (1,2,10,9), (2,3,11,10), (3,0,8,11),
        (8,12,13,9), (9,13,14,10), (10,14,15,11), (11,15,12,8), (12,13,14,15),
    ]
    dark_face_indices = list(range(len(faces)+9, len(faces)+14))
    faces.extend(tuple(base+index for index in face) for face in face_defs)
    return dark_face_indices


def _append_tapered_prism(vertices, faces, center, radius, height, sides, phase=0.0,
                          top_scale=0.78, top_shift=(0.0, 0.0)):
    """Append a faceted tapered prism with a shifted, rotated top ring."""
    start = len(vertices)
    cx, cy, cz = center
    for ring, scale, z, offset, turn in (
        (0, 1.0, -height*0.5, (0.0,0.0), 0.0),
        (1, top_scale, height*0.5, top_shift, phase),
    ):
        for index in range(sides):
            angle = math.tau * index / sides + turn
            vertices.append((
                cx + offset[0] + radius*scale*math.cos(angle),
                cy + offset[1] + radius*scale*math.sin(angle),
                cz + z,
            ))
    faces.append(tuple(start + index for index in range(sides - 1, -1, -1)))
    faces.append(tuple(start + sides + index for index in range(sides)))
    for index in range(sides):
        nxt = (index + 1) % sides
        faces.append((start+index, start+nxt, start+sides+nxt, start+sides+index))


def _build_cyber_module(settings, rng):
    """Stacked sci-fi housing with genuinely recessed, dark front wells."""
    vertices, faces = [], []
    dark_faces = []
    unit = settings.size
    tiers = rng.randint(3, 5)
    z = -unit * 0.56
    base_width = unit * rng.uniform(0.72, 0.98)
    base_depth = unit * rng.uniform(0.62, 0.88)
    tier_height = unit * rng.uniform(0.22, 0.31)
    yaw = rng.uniform(-0.35, 0.35)
    _append_block(vertices, faces, (0,0,z+tier_height*0.45),
                  (base_width*1.20,base_depth*1.20,tier_height*0.48), yaw)
    z += tier_height * 0.52
    for tier in range(tiers):
        width = base_width * rng.uniform(0.76, 1.12)
        depth = base_depth * rng.uniform(0.78, 1.12)
        height = tier_height * rng.uniform(0.78, 1.23)
        offset_x = rng.uniform(-0.10,0.10)*unit
        offset_y = rng.uniform(-0.08,0.08)*unit
        yaw += rng.uniform(-0.42,0.42)
        tilt_x = rng.uniform(-0.08,0.08)
        tilt_y = rng.uniform(-0.08,0.08)
        body_center = (offset_x,offset_y,z+height*0.5)
        panel_w = width*rng.uniform(0.36,0.54)
        panel_h = height*rng.uniform(0.42,0.68)
        recess = min(unit*rng.uniform(0.075,0.12),depth*0.26)
        dark_faces.extend(_append_recessed_box(
            vertices,faces,body_center,(width,depth,height),(panel_w,panel_h),recess,
            yaw,tilt_x,tilt_y
        ))

        # An inner panel sits inside the opening while leaving a dark cavity border visible.
        plate_w = panel_w*rng.uniform(0.54,0.72)
        plate_h = panel_h*rng.uniform(0.54,0.72)
        plate_depth = unit*0.018
        plate_local_y = -depth*0.5 + recess - plate_depth*0.5 - unit*0.004
        plate_offset = _transform_local_offset((0.0,plate_local_y,0.0),yaw,tilt_x,tilt_y)
        plate_center = (offset_x+plate_offset.x,offset_y+plate_offset.y,z+height*0.5+plate_offset.z)
        _append_block(vertices,faces,plate_center,(plate_w,plate_depth,plate_h),yaw,tilt_x,tilt_y)

        # Thin rails around the opening catch highlights without covering the inset.
        front_local_y = -depth*0.5-unit*0.008
        rail_t = unit*0.018
        trim_specs = (
            (-(panel_w*0.5+rail_t*0.5),front_local_y,0.0,(rail_t,unit*0.025,panel_h+rail_t*1.7)),
            ((panel_w*0.5+rail_t*0.5),front_local_y,0.0,(rail_t,unit*0.025,panel_h+rail_t*1.7)),
            (0.0,front_local_y,-panel_h*0.5-rail_t*0.5,(panel_w+rail_t*1.7,unit*0.025,rail_t)),
            (0.0,front_local_y,panel_h*0.5+rail_t*0.5,(panel_w+rail_t*1.7,unit*0.025,rail_t)),
        )
        for lx,ly,lz,dims in trim_specs:
            off = _transform_local_offset((lx,ly,lz),yaw,tilt_x,tilt_y)
            c = (offset_x+off.x,offset_y+off.y,z+height*0.5+off.z)
            _append_block(vertices,faces,c,dims,yaw,tilt_x,tilt_y)

        # Vent slats are installed down inside the pocket.
        if rng.random() < 0.9:
            rib_count = rng.randint(3,7)
            rib_span = plate_w*0.82
            rib_y = -depth*0.5 + recess - unit*0.022
            for rib in range(rib_count):
                lx = -rib_span*0.5 + rib_span*(rib+0.5)/rib_count
                off = _transform_local_offset((lx,rib_y,-plate_h*0.22),yaw,tilt_x,tilt_y)
                c = (offset_x+off.x,offset_y+off.y,z+height*0.5+off.z)
                _append_block(vertices,faces,c,
                              (max(unit*0.012,plate_w*0.024),unit*0.022,plate_h*0.42),
                              yaw,tilt_x,tilt_y)

        if rng.random() < 0.75:
            side = rng.choice((-1.0,1.0))
            local_off = (side*(width*0.5+unit*0.045),0.0,height*0.02)
            off = _transform_local_offset(local_off,yaw,tilt_x,tilt_y)
            c = (offset_x+off.x,offset_y+off.y,z+height*0.5+off.z)
            _append_block(vertices,faces,c,
                          (unit*0.10,depth*rng.uniform(0.28,0.58),height*rng.uniform(0.42,0.85)),
                          yaw+rng.uniform(-0.12,0.12),tilt_x,tilt_y)
        z += height*0.83

    top_z = z + tier_height*0.12
    crown_w = base_width*rng.uniform(0.30,0.55)
    _append_block(vertices,faces,(rng.uniform(-0.12,0.12)*unit,0,top_z),
                  (crown_w,base_depth*0.42,tier_height*0.35),yaw+rng.uniform(-0.5,0.5))
    for index in range(rng.randint(2,4)):
        side = -1.0 if index % 2 else 1.0
        _append_block(vertices,faces,
                      (side*base_width*0.43,rng.uniform(-0.12,0.12)*unit,z-tier_height*0.04),
                      (unit*0.055,unit*0.09,tier_height*rng.uniform(0.45,0.85)),
                      yaw+side*rng.uniform(-0.18,0.18))
    return vertices, faces, {"dark_faces": dark_faces}


def _build_folded_ribbon(settings, rng):
    """A twisting metal ribbon with a deep longitudinal channel and raised edge lips."""
    vertices, faces = [], []
    dark_faces = []
    unit = settings.size
    samples = max(56, settings.detail*4)
    turns = rng.uniform(1.0,1.8)
    phase = rng.uniform(0.0,math.tau)
    width_base = unit*rng.uniform(0.16,0.25)
    thickness = unit*rng.uniform(0.035,0.055)
    centers = []
    jitter = rng.uniform(-0.025,0.025)
    for index in range(samples):
        t = index/(samples-1)
        angle = math.tau*turns*t+phase
        radial = unit*(0.30+0.13*math.sin(math.pi*t+jitter))
        centers.append(Vector((
            radial*math.cos(angle)+unit*0.10*math.sin(math.tau*t),
            radial*math.sin(angle),
            unit*(t-0.5)*1.45+unit*0.16*math.sin(angle*0.72),
        )))
    section_sides = 8
    for index, center in enumerate(centers):
        if index == 0:
            tangent = (centers[1]-centers[0]).normalized()
        elif index == samples-1:
            tangent = (centers[-1]-centers[-2]).normalized()
        else:
            tangent = (centers[index+1]-centers[index-1]).normalized()
        guide = Vector((0.0,0.0,1.0))
        width_axis = tangent.cross(guide)
        if width_axis.length < 1e-6:
            width_axis = tangent.cross(Vector((1.0,0.0,0.0)))
        width_axis.normalize()
        width_axis.rotate(Quaternion(tangent, math.tau*0.95*index/(samples-1)+0.28*math.sin(index*0.08)))
        depth_axis = tangent.cross(width_axis).normalized()
        t = index/(samples-1)
        width = width_base*(0.68+0.48*math.sin(math.pi*t))
        # Cross-section includes a U-shaped channel and two raised lips.
        profile = (
            (-width,-thickness),(width,-thickness),(width,thickness),
            (width*0.76,thickness),(width*0.57,-thickness*0.12),
            (-width*0.57,-thickness*0.12),(-width*0.76,thickness),(-width,thickness),
        )
        for side_offset, depth_offset in profile:
            vertices.append(tuple(center+width_axis*side_offset+depth_axis*depth_offset))
    for index in range(samples-1):
        for side in range(section_sides):
            face_index = len(faces)
            a = index*section_sides+side
            b = index*section_sides+(side+1)%section_sides
            c = (index+1)*section_sides+(side+1)%section_sides
            d = (index+1)*section_sides+side
            faces.append((a,b,c,d))
            if side == 4:
                dark_faces.append(face_index)
    faces.append(tuple(range(section_sides-1,-1,-1)))
    end = (samples-1)*section_sides
    faces.append(tuple(end+side for side in range(section_sides)))
    return vertices, faces, {"dark_faces": dark_faces}


def _build_prism_reactor(settings, rng):
    """An angular reactor-lantern with a faceted center and intersecting open frames."""
    vertices, faces = [], []
    unit = settings.size
    sides = rng.choice((5,6,7,8))
    body_h = unit*rng.uniform(0.90,1.30)
    core_radius = unit*rng.uniform(0.24,0.34)
    _append_tapered_prism(vertices,faces,(0,0,0),core_radius,body_h,sides,
                          rng.uniform(-0.25,0.25),rng.uniform(0.62,0.86),
                          (rng.uniform(-0.06,0.06)*unit,rng.uniform(-0.06,0.06)*unit))
    # Raised top and bottom rings make it feel engineered rather than like a plain crystal.
    frame_radius = unit*rng.uniform(0.42,0.55)
    for z in (-body_h*0.45,body_h*0.45):
        points = [Vector((frame_radius*math.cos(math.tau*i/96),
                          frame_radius*math.sin(math.tau*i/96),z)) for i in range(96)]
        _append_tube(vertices,faces,points,unit*0.027,sides=6,closed=True,cap_ends=False)
    # Tall orbitals are tilted independently around the core.
    for ring_index in range(rng.randint(3,5)):
        axis = Vector((rng.uniform(-0.9,0.9),rng.uniform(-0.9,0.9),rng.uniform(-0.45,0.45)))
        if axis.length < 1e-6:
            axis = Vector((0.0,1.0,0.0))
        axis.normalize()
        rot = Vector((0.0,0.0,1.0)).rotation_difference(axis)
        radius = frame_radius*rng.uniform(0.88,1.18)
        points = []
        for i in range(96):
            t = math.tau*i/96
            p = Vector((radius*math.cos(t),radius*math.sin(t),0.0))
            p.rotate(rot)
            points.append(p)
        _append_tube(vertices,faces,points,unit*rng.uniform(0.012,0.022),sides=6,closed=True,cap_ends=False)
    # Radial braces connect the base and crown, leaving open windows between them.
    brace_count = rng.randint(5,8)
    for index in range(brace_count):
        angle = math.tau*index/brace_count
        low = Vector((frame_radius*math.cos(angle),frame_radius*math.sin(angle),-body_h*0.46))
        high = Vector((frame_radius*math.cos(angle+rng.uniform(-0.25,0.25)),
                       frame_radius*math.sin(angle+rng.uniform(-0.25,0.25)),body_h*0.46))
        _append_tube(vertices,faces,(low,high),unit*0.021,sides=6,closed=False,cap_ends=True)
    # One offset top fin adds an asymmetrical sci-fi signature.
    _append_block(vertices,faces,(unit*0.23,-unit*0.12,body_h*0.53),
                  (unit*0.30,unit*0.12,unit*0.16),rng.uniform(-0.5,0.5),
                  rng.uniform(-0.4,0.4),rng.uniform(-0.3,0.3))
    return vertices, faces


def _build_faceted_totem(settings, rng):
    """A stacked gemstone-meets-industrial artifact with slanted polygonal plates."""
    vertices, faces = [], []
    unit = settings.size
    tiers = rng.randint(3,6)
    z = -unit*0.66
    sides = rng.choice((4,5,6,7))
    yaw = rng.uniform(0.0,math.tau)
    for index in range(tiers):
        height = unit*rng.uniform(0.24,0.40)
        radius = unit*rng.uniform(0.25,0.43)*(1.10 if index in (0,tiers-1) else 1.0)
        shift = (rng.uniform(-0.10,0.10)*unit,rng.uniform(-0.09,0.09)*unit)
        _append_tapered_prism(vertices,faces,(shift[0],shift[1],z+height*0.5),
                              radius,height,sides,yaw+rng.uniform(-0.45,0.45),
                              rng.uniform(0.52,1.05),
                              (rng.uniform(-0.09,0.09)*unit,rng.uniform(-0.09,0.09)*unit))
        # Fine stacked ribs or short plates are attached to selected outward faces.
        if rng.random() < 0.85:
            face_angle = yaw + math.tau*rng.randrange(sides)/sides
            rib_count = rng.randint(3,7)
            for rib in range(rib_count):
                rz = z+height*(0.2+0.58*(rib+0.5)/rib_count)
                rx = shift[0]+math.cos(face_angle)*(radius*0.92+unit*0.018)
                ry = shift[1]+math.sin(face_angle)*(radius*0.92+unit*0.018)
                _append_block(vertices,faces,(rx,ry,rz),
                              (unit*0.035,unit*0.055,height*0.045),face_angle)
        z += height*0.84
        yaw += rng.uniform(-0.48,0.48)
    # Floating fins at different angles make each seed change the silhouette, not just its color.
    for index in range(rng.randint(2,4)):
        angle = rng.uniform(0.0,math.tau)
        radius = unit*rng.uniform(0.34,0.54)
        _append_block(vertices,faces,
                      (radius*math.cos(angle),radius*math.sin(angle),rng.uniform(-0.25,0.45)*unit),
                      (unit*rng.uniform(0.12,0.22),unit*0.07,unit*rng.uniform(0.25,0.55)),
                      angle+rng.uniform(-0.6,0.6),rng.uniform(-0.5,0.5),rng.uniform(-0.5,0.5))
    return vertices, faces


def _append_uv_sphere(vertices, faces, center, radius, segments=9, rings=6):
    """Append a low-poly UV sphere; return the face-index range for material tagging."""
    face_start = len(faces)
    cx, cy, cz = center
    top = len(vertices)
    vertices.append((cx, cy, cz + radius))
    for row in range(1, rings):
        theta = math.pi * row / rings
        for col in range(segments):
            phi = math.tau * col / segments
            vertices.append((
                cx + radius * math.sin(theta) * math.cos(phi),
                cy + radius * math.sin(theta) * math.sin(phi),
                cz + radius * math.cos(theta),
            ))
    bottom = len(vertices)
    vertices.append((cx, cy, cz - radius))
    first = top + 1
    for col in range(segments):
        faces.append((top, first + col, first + (col + 1) % segments))
    for row in range(rings - 2):
        upper = first + row * segments
        lower = upper + segments
        for col in range(segments):
            nxt = (col + 1) % segments
            faces.append((upper + col, lower + col, lower + nxt, upper + nxt))
    last = first + (rings - 2) * segments
    for col in range(segments):
        faces.append((last + col, bottom, last + (col + 1) % segments))
    return list(range(face_start, len(faces)))


def _append_hex_tile(vertices, faces, center, radius, depth, phase=0.0):
    """Add a six-sided raised armor tile, facing toward negative Y."""
    face_start = len(faces)
    cx, cy, cz = center
    for y in (cy - depth * 0.5, cy + depth * 0.5):
        for side in range(6):
            angle = math.tau * side / 6 + phase
            vertices.append((cx + radius * math.cos(angle), y, cz + radius * math.sin(angle)))
    faces.append(tuple(face_start * 0 + len(vertices) - 12 + i for i in range(6)))
    faces.append(tuple(len(vertices) - 6 + i for i in range(6)))
    base_vertex = len(vertices) - 12
    for side in range(6):
        nxt = (side + 1) % 6
        faces.append((base_vertex + side, base_vertex + nxt, base_vertex + 6 + nxt, base_vertex + 6 + side))
    # First face is the dark gap/back edge; the second is the tile's reflective front.
    return face_start, face_start + 1, list(range(face_start + 2, face_start + 8))


def _append_horizontal_cylinder(vertices, faces, center, radius, depth, sides=48):
    """Append a cylinder whose circular face lies in the XY plane."""
    face_start = len(faces)
    cx, cy, cz = center
    for z in (cz - depth * 0.5, cz + depth * 0.5):
        for side in range(sides):
            angle = math.tau * side / sides
            vertices.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle), z))
    faces.append(tuple(face_start * 0 + len(vertices) - 2 * sides + i for i in range(sides - 1, -1, -1)))
    faces.append(tuple(len(vertices) - sides + i for i in range(sides)))
    base_vertex = len(vertices) - 2 * sides
    for side in range(sides):
        nxt = (side + 1) % sides
        faces.append((base_vertex + side, base_vertex + nxt, base_vertex + sides + nxt, base_vertex + sides + side))
    return list(range(face_start, len(faces)))


def _append_cone_between(vertices, faces, start, end, radius, sides=7):
    """Append a tapered mechanical spike between two points."""
    face_start = len(faces)
    a, b = Vector(start), Vector(end)
    axis = b - a
    if axis.length < 1e-6:
        return []
    axis.normalize()
    helper = Vector((0.0, 0.0, 1.0))
    if abs(axis.dot(helper)) > 0.92:
        helper = Vector((1.0, 0.0, 0.0))
    u = axis.cross(helper).normalized()
    v = axis.cross(u).normalized()
    base = len(vertices)
    for i in range(sides):
        angle = math.tau * i / sides
        point = a + radius * (u * math.cos(angle) + v * math.sin(angle))
        vertices.append(tuple(point))
    tip = len(vertices)
    vertices.append(tuple(b))
    faces.append(tuple(base + i for i in range(sides - 1, -1, -1)))
    for i in range(sides):
        nxt = (i + 1) % sides
        faces.append((base + i, base + nxt, tip))
    return list(range(face_start, len(faces)))


def _build_hex_armor(settings, rng):
    """A curved sci-fi armor plaque with raised hex cells and dark recessed seams."""
    vertices, faces = [], []
    dark_faces, material_faces = [], []
    unit = settings.size
    width, height, backing_depth = unit * 1.58, unit * 1.18, unit * 0.16
    _append_block(vertices, faces, (0.0, 0.0, 0.0), (width * 1.08, backing_depth, height * 1.08), 0.0)
    rows = rng.randint(4, 6)
    cols = rng.randint(6, 8)
    radius = min(width / (1.5 * (cols - 1) + 2.15), height / (1.72 * (rows - 1) + 2.25))
    step_x, step_z = 1.5 * radius, 1.72 * radius
    left = -step_x * (cols - 1) * 0.5
    bottom = -step_z * (rows - 1) * 0.5
    for row in range(rows):
        for col in range(cols):
            x = left + col * step_x + (0.5 * step_x if row % 2 else 0.0)
            z = bottom + row * step_z
            if abs(x) > width * 0.49 or abs(z) > height * 0.47:
                continue
            bulge = 1.0 - 0.10 * (x / width) ** 2 - 0.12 * (z / height) ** 2
            y = -backing_depth * 0.5 - radius * 0.08 * bulge
            tile_radius = radius * rng.uniform(0.88, 0.98)
            dark_idx, front_idx, side_indices = _append_hex_tile(
                vertices, faces, (x, y, z), tile_radius, unit * rng.uniform(0.035, 0.065),
                rng.uniform(-0.08, 0.08)
            )
            dark_faces.append(dark_idx)
            material_faces.append((front_idx, rng.choices((1, 2, 3, 4), weights=(4, 3, 1, 2), k=1)[0]))
            for idx in side_indices:
                material_faces.append((idx, 0))
    # Frame rails and two asymmetric mounting lugs.
    rail = unit * 0.032
    _append_block(vertices, faces, (0.0, -backing_depth * 0.58, height * 0.53),
                  (width * 1.02, rail, rail), 0.0)
    _append_block(vertices, faces, (0.0, -backing_depth * 0.58, -height * 0.53),
                  (width * 1.02, rail, rail), 0.0)
    for sign in (-1.0, 1.0):
        _append_block(vertices, faces, (sign * width * 0.52, -backing_depth * 0.58, 0.0),
                      (rail, rail, height * 1.03), rng.uniform(-0.03, 0.03))
    for index in range(rng.randint(4, 7)):
        x = rng.uniform(-width * 0.43, width * 0.43)
        z = rng.choice((-1.0, 1.0)) * height * 0.54
        _append_uv_sphere(vertices, faces, (x, -backing_depth * 0.78, z), unit * 0.018, 7, 4)
        material_faces.extend((i, 4) for i in range(len(faces) - 14, len(faces)))
    return vertices, faces, {"dark_faces": dark_faces, "face_material_indices": material_faces}


def _build_circuit_core(settings, rng):
    """A round, multi-tier circuit device with stepped rims, grooves and radial traces."""
    vertices, faces = [], []
    dark_faces, material_faces = [], []
    unit = settings.size
    radius = unit * rng.uniform(0.48, 0.62)
    depth = unit * rng.uniform(0.18, 0.26)
    base_faces = _append_horizontal_cylinder(vertices, faces, (0, 0, -depth * 0.25), radius, depth, 64)
    dark_faces.extend(base_faces[2:])
    _append_horizontal_cylinder(vertices, faces, (0, 0, depth * 0.34), radius * 0.88, depth * 0.22, 64)
    # Concentric raised tracks, one amber/cyan ring and two dark armor rails.
    for ring_index, factor in enumerate((0.36, 0.49, 0.68, 0.82, 0.96)):
        ring_radius = radius * factor
        z = depth * (0.51 + 0.015 * (ring_index % 2))
        points = [Vector((ring_radius * math.cos(math.tau * i / 128),
                          ring_radius * math.sin(math.tau * i / 128), z)) for i in range(128)]
        start_face = len(faces)
        _append_tube(vertices, faces, points, unit * (0.013 if ring_index % 2 else 0.022),
                     sides=7, closed=True, cap_ends=False)
        ring_material = (3 if ring_index in (1, 4) else 2)
        material_faces.extend((i, ring_material) for i in range(start_face, len(faces)))
    # The raised central hub.
    _append_horizontal_cylinder(vertices, faces, (0, 0, depth * 0.55), radius * 0.22, depth * 0.32, 40)
    hub_faces = _append_uv_sphere(vertices, faces, (0, 0, depth * 0.83), radius * 0.14, 16, 8)
    material_faces.extend((i, 3) for i in hub_faces)
    # Circuit traces branch at right angles. Each route is geometry, not a painted texture.
    for index in range(rng.randint(10, 15)):
        angle = math.tau * index / rng.randint(10, 15)
        r0 = radius * rng.uniform(0.38, 0.46)
        r1 = radius * rng.uniform(0.56, 0.72)
        r2 = radius * rng.uniform(0.75, 0.91)
        p0 = Vector((r0 * math.cos(angle), r0 * math.sin(angle), depth * 0.57))
        p1 = Vector((r1 * math.cos(angle), r1 * math.sin(angle), depth * 0.57))
        turn = angle + rng.choice((-1, 1)) * math.pi * 0.5
        p2 = Vector((p1.x + radius * 0.16 * math.cos(turn), p1.y + radius * 0.16 * math.sin(turn), depth * 0.57))
        p3 = Vector((r2 * math.cos(turn), r2 * math.sin(turn), depth * 0.57))
        start_face = len(faces)
        _append_tube(vertices, faces, (p0, p1, p2, p3), unit * rng.uniform(0.007, 0.013),
                     sides=5, closed=False, cap_ends=True)
        material_faces.extend((i, 3 if index % 4 == 0 else 2) for i in range(start_face, len(faces)))
        button_faces = _append_uv_sphere(vertices, faces, tuple(p3), unit * 0.022, 7, 4)
        material_faces.extend((i, 4) for i in button_faces)
    # Recess-like square chip packages around the rim.
    for index in range(rng.randint(6, 10)):
        angle = math.tau * index / 8.0 + rng.uniform(-0.08, 0.08)
        r = radius * rng.uniform(0.63, 0.73)
        x, y = r * math.cos(angle), r * math.sin(angle)
        dims = (unit * rng.uniform(0.07, 0.12), unit * 0.045, unit * rng.uniform(0.045, 0.075))
        _append_block(vertices, faces, (x, y, depth * 0.70), dims, angle)
    return vertices, faces, {"dark_faces": dark_faces, "face_material_indices": material_faces}


def _build_orbital_particle(settings, rng):
    """A crescent-shaped swarm of metallic spheres connected by delicate filament lines."""
    vertices, faces = [], []
    dark_faces, material_faces = [], []
    unit = settings.size
    major_radius = unit * rng.uniform(0.42, 0.52)
    minor_radius = unit * rng.uniform(0.18, 0.26)
    count = max(36, min(76, settings.detail + 24))
    phase = rng.uniform(0.0, math.tau)
    anchors = []
    for index in range(count):
        t = math.tau * (index / count) + phase
        # Small gap and vertical wobble make it an asymmetric orbital cloud, not a donut.
        if 0.78 * math.pi < (t % math.tau) < 1.12 * math.pi:
            continue
        radial = major_radius * (1.0 + 0.08 * math.sin(3.0 * t + phase))
        x = radial * math.cos(t)
        y = minor_radius * math.sin(t) + unit * 0.055 * math.sin(2.0 * t + phase)
        z = unit * 0.16 * math.sin(2.0 * t + phase * 0.7)
        center = Vector((x, y, z))
        anchors.append(center)
        large_radius = unit * rng.uniform(0.035, 0.078)
        sphere_faces = _append_uv_sphere(vertices, faces, tuple(center), large_radius, 9, 6)
        material_faces.extend((i, 1 if index % 4 == 0 else 0) for i in sphere_faces)
        # Several satellite pearls cluster close to each major node.
        for pearl in range(rng.randint(1, 4)):
            offset = Vector((rng.uniform(-0.10,0.10), rng.uniform(-0.10,0.10), rng.uniform(-0.10,0.10))) * unit
            pearl_center = center + offset
            pearl_radius = unit * rng.uniform(0.008, 0.028)
            pearl_faces = _append_uv_sphere(vertices, faces, tuple(pearl_center), pearl_radius, 7, 4)
            material_faces.extend((i, rng.choice((1, 2, 3, 4))) for i in pearl_faces)
    # Sparse struts form a visible scientific network through the cloud.
    if len(anchors) > 8:
        for index in range(0, len(anchors), 2):
            end_a = anchors[index]
            end_b = anchors[(index + rng.randint(3, 7)) % len(anchors)]
            start_face = len(faces)
            _append_tube(vertices, faces, (end_a, end_b), unit * rng.uniform(0.0025, 0.006),
                         sides=4, closed=False, cap_ends=True)
            material_faces.extend((i, 3 if index % 5 == 0 else 2) for i in range(start_face, len(faces)))
    return vertices, faces, {"dark_faces": dark_faces, "face_material_indices": material_faces}


def _build_cellular_void(settings, rng):
    """A porous organic-metal exoskeleton built from irregular spherical lattice struts."""
    vertices, faces = [], []
    dark_faces, material_faces = [], []
    unit = settings.size
    latitudes = max(8, min(16, settings.detail // 3))
    longitudes = latitudes * 2
    points = {}
    base_radius = unit * rng.uniform(0.43, 0.55)
    phase = rng.uniform(0.0, math.tau)
    for row in range(1, latitudes):
        theta = math.pi * row / latitudes
        for col in range(longitudes):
            phi = math.tau * col / longitudes
            wobble = 1.0 + 0.08 * math.sin(3.0 * phi + phase) * math.sin(2.0 * theta)
            wobble += rng.uniform(-0.045, 0.045)
            radius = base_radius * wobble
            points[(row,col)] = Vector((
                radius * math.sin(theta) * math.cos(phi),
                radius * math.sin(theta) * math.sin(phi),
                radius * math.cos(theta),
            ))
    # Connect only selected grid edges, leaving irregular openings through the shell.
    def add_strut(a, b, accent=False):
        start_face = len(faces)
        _append_tube(vertices, faces, (a,b), unit * rng.uniform(0.009, 0.020), sides=5, closed=False, cap_ends=True)
        mat = 2 if accent else 0
        material_faces.extend((i, mat) for i in range(start_face, len(faces)))
    for row in range(1, latitudes):
        for col in range(longitudes):
            here = points[(row,col)]
            next_col = points[(row,(col+1)%longitudes)]
            if rng.random() < 0.78:
                add_strut(here, next_col, rng.random() < 0.09)
            if row < latitudes-1 and rng.random() < 0.80:
                add_strut(here, points[(row+1,col)], rng.random() < 0.08)
            if row < latitudes-1 and rng.random() < 0.24:
                add_strut(here, points[(row+1,(col+1)%longitudes)], rng.random() < 0.10)
    # Node beads soften the intersections and emphasize the hollow, porous construction.
    for key, point in points.items():
        if rng.random() < 0.82:
            radius = unit * rng.uniform(0.014, 0.034)
            bead_faces = _append_uv_sphere(vertices, faces, tuple(point), radius, 7, 4)
            material_faces.extend((i, 1 if rng.random() < 0.18 else 0) for i in bead_faces)
    # A few inward braces create visible depth inside the holes.
    for index in range(rng.randint(8, 14)):
        a = rng.choice(list(points.values()))
        b = rng.choice(list(points.values()))
        start_face = len(faces)
        _append_tube(vertices, faces, (a * 0.90, b * 0.90), unit * 0.007, sides=4, closed=False, cap_ends=True)
        material_faces.extend((i, 2) for i in range(start_face, len(faces)))
    return vertices, faces, {"dark_faces": dark_faces, "face_material_indices": material_faces}


def _build_spike_bloom(settings, rng):
    """A dark mechanical-organic orb with irregular tapered spikes and warm inner accents."""
    vertices, faces = [], []
    dark_faces, material_faces = [], []
    unit = settings.size
    core_radius = unit * rng.uniform(0.29, 0.38)
    core_faces = _append_uv_sphere(vertices, faces, (0,0,0), core_radius, 24, 16)
    material_faces.extend((i, 0) for i in core_faces)
    spike_count = max(28, min(68, settings.detail + 24))
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))
    for index in range(spike_count):
        z = 1.0 - 2.0 * (index + 0.5) / spike_count
        radial = math.sqrt(max(0.0, 1.0 - z*z))
        angle = index * golden_angle + rng.uniform(-0.22,0.22)
        direction = Vector((radial*math.cos(angle),radial*math.sin(angle),z)).normalized()
        start = direction * (core_radius * rng.uniform(0.82, 1.03))
        length = unit * rng.uniform(0.10, 0.30)
        tip = direction * (core_radius + length)
        spike_faces = _append_cone_between(vertices, faces, start, tip, unit*rng.uniform(0.014,0.042), sides=rng.randint(5,8))
        accent = rng.random() < 0.22
        material_faces.extend((i, 3 if accent else 1) for i in spike_faces)
    # Small embedded reactor ports and a few gold/cyan nodules.
    for index in range(rng.randint(8, 16)):
        direction = Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1))).normalized()
        center = direction * core_radius * 0.97
        port_faces = _append_uv_sphere(vertices, faces, tuple(center), unit*rng.uniform(0.014,0.032), 8, 5)
        material_faces.extend((i, 2 if index % 3 else 3) for i in port_faces)
    return vertices, faces, {"dark_faces": dark_faces, "face_material_indices": material_faces}


def _new_mesh_object(context, name, vertices, faces, seed, face_material_overrides=None):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    target_collection = context.collection or context.scene.collection
    target_collection.objects.link(obj)

    rng = random.Random(seed ^ 0x5A17)
    object_family = next((family for family in ("Cyber Module", "Folded Ribbon", "Prism Reactor", "Faceted Totem", "Hex Armor", "Circuit Core", "Orbital Particle", "Cellular Void", "Spike Bloom") if family in name), None)
    if object_family:
        palettes = {
            "Cyber Module": [
                ("Graphite", (0.018,0.035,0.065), 0.76, 0.28, None, 0.0),
                ("Ceramic blue", (0.055,0.22,0.38), 0.62, 0.25, None, 0.0),
                ("Ocean cyan", (0.01,0.42,0.78), 0.34, 0.22, (0.0,0.18,0.65), 1.4),
                ("Signal orange", (1.0,0.22,0.015), 0.28, 0.23, (1.0,0.10,0.005), 2.8),
                ("Solar yellow", (1.0,0.62,0.035), 0.22, 0.28, None, 0.0),
                ("Pale alloy", (0.72,0.80,0.88), 0.68, 0.22, None, 0.0),
            ],
            "Folded Ribbon": [
                ("Midnight alloy", (0.018,0.035,0.075), 0.82, 0.20, None, 0.0),
                ("Liquid silver", (0.72,0.82,0.91), 0.86, 0.15, None, 0.0),
                ("Ion blue", (0.012,0.28,0.90), 0.48, 0.17, (0.0,0.15,1.0), 2.1),
                ("Plasma amber", (1.0,0.20,0.012), 0.30, 0.19, (1.0,0.08,0.0), 3.0),
                ("Violet titanium", (0.22,0.08,0.44), 0.65, 0.20, None, 0.0),
            ],
            "Prism Reactor": [
                ("Reactor graphite", (0.018,0.04,0.07), 0.80, 0.22, None, 0.0),
                ("Cold titanium", (0.58,0.70,0.82), 0.76, 0.20, None, 0.0),
                ("Core cyan", (0.01,0.35,0.82), 0.25, 0.18, (0.0,0.25,1.0), 4.0),
                ("Core amber", (1.0,0.18,0.01), 0.22, 0.18, (1.0,0.08,0.0), 3.5),
            ],
            "Faceted Totem": [
                ("Deep cobalt", (0.025,0.10,0.34), 0.70, 0.22, None, 0.0),
                ("Azure", (0.02,0.42,0.76), 0.40, 0.20, None, 0.0),
                ("Tangerine", (1.0,0.20,0.025), 0.28, 0.23, None, 0.0),
                ("Golden yellow", (1.0,0.60,0.025), 0.23, 0.25, None, 0.0),
                ("Teal", (0.02,0.30,0.33), 0.54, 0.24, None, 0.0),
                ("Soft silver", (0.75,0.80,0.86), 0.68, 0.20, None, 0.0),
            ],
            "Hex Armor": [
                ("Deep black ceramic", (0.006,0.012,0.022), 0.78, 0.24, None, 0.0),
                ("Graphite titanium", (0.045,0.060,0.080), 0.88, 0.19, None, 0.0),
                ("Bright machined edge", (0.36,0.43,0.52), 0.90, 0.16, None, 0.0),
                ("Ice blue seam", (0.008,0.30,0.82), 0.45, 0.18, (0.0,0.18,1.0), 1.5),
                ("Warm metal accent", (0.96,0.24,0.035), 0.52, 0.19, (1.0,0.09,0.01), 1.8),
            ],
            "Circuit Core": [
                ("Circuit substrate", (0.008,0.018,0.032), 0.75, 0.28, None, 0.0),
                ("Dark machined steel", (0.065,0.085,0.11), 0.84, 0.22, None, 0.0),
                ("Silver traces", (0.38,0.48,0.59), 0.86, 0.18, None, 0.0),
                ("Ion blue trace", (0.006,0.32,0.95), 0.30, 0.17, (0.0,0.23,1.0), 3.0),
                ("Amber signal", (1.0,0.24,0.025), 0.30, 0.18, (1.0,0.10,0.0), 3.0),
            ],
            "Orbital Particle": [
                ("Obsidian chrome", (0.012,0.016,0.025), 0.88, 0.12, None, 0.0),
                ("Silver pearl", (0.70,0.76,0.83), 0.72, 0.12, None, 0.0),
                ("Champagne gold", (0.70,0.37,0.12), 0.82, 0.16, None, 0.0),
                ("Cool blue pin light", (0.02,0.28,0.78), 0.32, 0.16, (0.0,0.22,1.0), 2.2),
                ("Amber pin light", (0.95,0.38,0.08), 0.35, 0.16, (1.0,0.20,0.02), 2.0),
            ],
            "Cellular Void": [
                ("Void black", (0.006,0.010,0.016), 0.58, 0.27, None, 0.0),
                ("Graphite shell", (0.035,0.045,0.055), 0.72, 0.21, None, 0.0),
                ("Subsurface ember", (0.42,0.055,0.018), 0.32, 0.22, (0.85,0.045,0.008), 1.5),
                ("Hot core", (0.90,0.18,0.025), 0.22, 0.19, (1.0,0.08,0.01), 3.2),
            ],
            "Spike Bloom": [
                ("Black ceramic", (0.006,0.010,0.018), 0.76, 0.18, None, 0.0),
                ("Gunmetal spikes", (0.10,0.12,0.15), 0.90, 0.17, None, 0.0),
                ("Copper port", (0.40,0.14,0.05), 0.78, 0.17, None, 0.0),
                ("Amber plasma", (1.0,0.12,0.012), 0.26, 0.17, (1.0,0.045,0.0), 3.4),
                ("Blue micro light", (0.015,0.20,0.82), 0.30, 0.16, (0.0,0.08,1.0), 2.8),
            ],
        }
        palette = palettes[object_family]
        for label, color, metallic, roughness, emission, strength in palette:
            material = _scene_material(f"VINLAB · {object_family} · {label}", color, metallic, roughness, emission, strength)
            mesh.materials.append(material)
        weight_map = {
            "Cyber Module": [3,4,2,2,1,3],
            "Folded Ribbon": [3,5,2,2,1],
            "Prism Reactor": [4,3,2,2],
            "Faceted Totem": [2,3,2,2,2,3],
            "Hex Armor": [5,5,3,1,1],
            "Circuit Core": [6,4,4,2,1],
            "Orbital Particle": [5,4,2,1,1],
            "Cellular Void": [8,3,1,1],
            "Spike Bloom": [6,4,2,1,1],
        }
        weights = weight_map[object_family]
        for index, polygon in enumerate(mesh.polygons):
            # Broad bands of color with deterministic small interruptions, not white-noise paint.
            band = (index // max(1, len(mesh.polygons)//12)) % len(palette)
            polygon.material_index = band if rng.random() < 0.62 else rng.choices(range(len(palette)), weights=weights, k=1)[0]
        if face_material_overrides:
            for polygon_index in face_material_overrides.get("dark_faces", []):
                if 0 <= polygon_index < len(mesh.polygons):
                    mesh.polygons[polygon_index].material_index = 0
            for polygon_index, material_index in face_material_overrides.get("face_material_indices", []):
                if 0 <= polygon_index < len(mesh.polygons):
                    mesh.polygons[polygon_index].material_index = max(0, min(material_index, len(palette)-1))
        obj.color = palette[1][1] + (1.0,)
        for polygon in mesh.polygons:
            polygon.use_smooth = object_family in ("Folded Ribbon", "Prism Reactor", "Orbital Particle", "Cellular Void", "Spike Bloom")
        if hasattr(mesh, "use_auto_smooth"):
            mesh.use_auto_smooth = True
        bevel = obj.modifiers.new("Micro bevels", "BEVEL")
        bounds = [Vector(v.co) for v in mesh.vertices]
        if bounds:
            extents = [max(v[axis] for v in bounds)-min(v[axis] for v in bounds) for axis in range(3)]
            max_extent = max(extents)
            min_extent = min(value for value in extents if value > 1e-6)
            family_factor = {
                "Cyber Module": 0.020,
                "Folded Ribbon": 0.012,
                "Prism Reactor": 0.012,
                "Faceted Totem": 0.016,
                "Hex Armor": 0.014,
                "Circuit Core": 0.010,
                "Orbital Particle": 0.004,
                "Cellular Void": 0.003,
                "Spike Bloom": 0.005,
            }.get(object_family, 0.010)
            bevel.width = max(0.003, min(max_extent*family_factor, min_extent*0.12))
            bevel.segments = 3
            bevel.limit_method = "ANGLE"
            if hasattr(bevel, "harden_normals"):
                bevel.harden_normals = True
            obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
            if hasattr(mesh, "use_auto_smooth"):
                mesh.use_auto_smooth = True
    else:
        material = bpy.data.materials.new(name=f"VINLAB · {name}")
        material.diffuse_color = (
            rng.uniform(0.12, 0.85),
            rng.uniform(0.25, 0.9),
            rng.uniform(0.3, 1.0),
            1.0,
        )
        mesh.materials.append(material)
        obj.color = material.diffuse_color
        smooth_surface = any(token in name for token in ("Organic Blob", "Orbital Cage", "Branching Form", "Future Sculpture"))
        for polygon in mesh.polygons:
            polygon.use_smooth = smooth_surface

    for other in context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj
    return obj


def _scene_material(name, color, metallic=0.0, roughness=0.35, emission=None, emission_strength=0.0):
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader is not None:
        shader.inputs["Base Color"].default_value = (*color, 1.0)
        shader.inputs["Metallic"].default_value = metallic
        shader.inputs["Roughness"].default_value = roughness
        if emission is not None:
            emission_socket = shader.inputs.get("Emission Color") or shader.inputs.get("Emission")
            if emission_socket is not None:
                emission_socket.default_value = (*emission, 1.0)
            strength = shader.inputs.get("Emission Strength")
            if strength is not None:
                strength.default_value = emission_strength
    return material


def _scene_box(collection, name, location, dimensions, material, bevel=0.06):
    dx, dy, dz = (max(0.02, float(v)) * 0.5 for v in dimensions)
    verts = [(-dx,-dy,-dz),(dx,-dy,-dz),(dx,dy,-dz),(-dx,dy,-dz),
             (-dx,-dy,dz),(dx,-dy,dz),(dx,dy,dz),(-dx,dy,dz)]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    if hasattr(mesh, "use_auto_smooth"):
        mesh.use_auto_smooth = True
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = location
    if bevel > 0:
        mod = obj.modifiers.new("Machined bevels", "BEVEL")
        mod.width = min(bevel, min(dimensions) * 0.2)
        mod.segments = 3
        obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return obj


def _scene_cylinder(collection, name, location, radius, depth, material, sides=48):
    verts, faces = [], []
    for z in (-depth * 0.5, depth * 0.5):
        for i in range(sides):
            angle = math.tau * i / sides
            verts.append((radius * math.cos(angle), radius * math.sin(angle), z))
    faces.extend([tuple(range(sides - 1, -1, -1)), tuple(sides + i for i in range(sides))])
    for i in range(sides):
        j = (i + 1) % sides
        faces.append((i, j, sides + j, sides + i))
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    if hasattr(mesh, "use_auto_smooth"):
        mesh.use_auto_smooth = True
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = location
    bevel = obj.modifiers.new("Rounded machined edges", "BEVEL")
    bevel.width = min(0.06, depth * 0.18, radius * 0.08)
    bevel.segments = 2
    obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return obj


def _scene_look_at(obj, target):
    direction = Vector(target) - obj.location
    if direction.length > 1e-8:
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _build_scifi_scene(context, settings, rng):
    """Build a complete editable hard-surface sci-fi scene with lighting and camera."""
    scene = context.scene
    collection = bpy.data.collections.new("VINLAB Sci-Fi Scene · " + str(settings.seed))
    scene.collection.children.link(collection)
    shell = _scene_material("VINLAB · Ceramic titanium", (0.62, 0.70, 0.79), 0.58, 0.24)
    dark = _scene_material("VINLAB · Graphite armor", (0.018, 0.035, 0.065), 0.75, 0.28)
    steel = _scene_material("VINLAB · Blue steel", (0.07, 0.15, 0.25), 0.72, 0.30)
    amber = _scene_material("VINLAB · Amber plasma", (0.9, 0.16, 0.012), 0.25, 0.22, (1.0, 0.09, 0.005), 4.0)
    cyan = _scene_material("VINLAB · Cyan plasma", (0.015, 0.34, 0.8), 0.2, 0.2, (0.01, 0.22, 1.0), 3.0)
    floor_mat = _scene_material("VINLAB · Basalt", (0.025, 0.04, 0.065), 0.35, 0.45)
    glow = (amber, cyan)

    def box(name, loc, dims, mat, bevel=0.06):
        return _scene_box(collection, name, loc, dims, mat, bevel)

    def tower(prefix, x, y, h, w, d, hero=False):
        z0 = 0.32
        box(prefix + " foundation", (x,y,z0+0.12), (w*1.3,d*1.3,0.24), dark, 0.08)
        box(prefix + " foundation light", (x,y,z0+0.26), (w*1.18,d*1.18,0.045), amber if hero else cyan, 0.01)
        body_h = h * 0.72
        body_z = z0 + 0.28 + body_h*0.5
        main = box(prefix + " armor shell", (x,y,body_z), (w,d,body_h), shell if hero else steel, 0.12)
        band_count = rng.randint(2, 4)
        for j in range(band_count):
            z = z0 + 0.28 + body_h*(j+1)/(band_count+1)
            box(prefix + " armor band " + str(j+1), (x,y,z), (w*1.07,d*1.07,max(0.07,h*0.025)), dark, 0.025)
            if rng.random() < 0.9:
                sx = x + rng.choice((-0.34,0.34))*w
                box(prefix + " energy seam " + str(j+1), (sx,y-d*0.515,z), (w*0.035,0.035,h*0.07), rng.choice(glow), 0.008)
        fy = y - d*0.5 - 0.055
        pw, ph = w*rng.uniform(0.28,0.43), body_h*rng.uniform(0.42,0.64)
        pz = body_z + rng.uniform(-0.05,0.08)*h
        box(prefix + " recessed interface", (x,fy,pz), (pw,0.10,ph), dark, 0.045)
        box(prefix + " interface amber edge", (x-pw*0.5+0.02,fy-0.06,pz), (0.035,0.025,ph*0.85), rng.choice(glow), 0.008)
        for j in range(rng.randint(3,6)):
            sz = pz + rng.uniform(-0.36,0.36)*ph
            sw = pw*rng.uniform(0.22,0.78)
            box(prefix + " control groove " + str(j+1), (x+rng.uniform(-0.06,0.06)*w,fy-0.065,sz), (sw,0.022,0.025), shell if j%2 else cyan, 0.005)
        sx = x+w*0.5+0.045
        box(prefix + " side armor", (sx,y,body_z), (0.09,d*0.55,body_h*0.62), dark, 0.025)
        for j in range(rng.randint(3,6)):
            vz = z0+0.34+body_h*0.18+j*body_h*0.045
            box(prefix + " vent " + str(j+1), (sx+0.05,y,vz), (0.035,d*0.36,0.035), shell, 0.008)
        roof = z0 + 0.28 + body_h
        box(prefix + " rooftop cap", (x,y,roof+0.06), (w*0.78,d*0.78,0.12), dark, 0.035)
        mast = h*rng.uniform(0.07,0.16)
        box(prefix + " antenna", (x+w*0.18,y,roof+0.12+mast*0.5), (0.06,0.06,mast), shell, 0.015)
        box(prefix + " beacon", (x+w*0.18,y,roof+0.12+mast), (0.15,0.15,0.08), amber, 0.02)
        return main

    # Stage, layered reactor plaza, and runway marks.
    box("Environment ground", (0,0,-0.38), (38,38,0.6), floor_mat, 0.16)
    _scene_cylinder(collection, "Plaza lower armor", (0,0,-0.02), 7.4, 0.26, dark)
    _scene_cylinder(collection, "Plaza cyan ring", (0,0,0.13), 7.1, 0.07, cyan)
    _scene_cylinder(collection, "Plaza upper deck", (0,0,0.32), 6.85, 0.32, steel)
    _scene_cylinder(collection, "Plaza ceramic surface", (0,0,0.50), 6.55, 0.07, shell)
    for i in range(24):
        a = math.tau*i/24
        mark = box("Plaza radial marker " + str(i+1), (5.9*math.cos(a),5.9*math.sin(a),0.55), (rng.uniform(0.2,0.48),0.045,0.02), glow[i%2], 0.005)
        mark.rotation_euler[2] = a

    central_h = rng.uniform(8.4,10.4)
    hero = tower("CORE TOWER",0.0,0.65,central_h,rng.uniform(2.6,3.15),rng.uniform(2.0,2.5),True)
    tower("NORTH WING",-4.2,1.2,rng.uniform(5.0,7.0),rng.uniform(1.6,2.1),rng.uniform(1.5,1.9))
    tower("SOUTH WING",4.0,0.25,rng.uniform(5.4,7.4),rng.uniform(1.6,2.15),rng.uniform(1.5,2.0))
    for i in range(rng.randint(5,8)):
        angle = math.tau*i/7 + rng.uniform(-0.2,0.2)
        radius = rng.uniform(8.3,11.5)
        tower("Perimeter station " + str(i+1), math.cos(angle)*radius, math.sin(angle)*radius,
              rng.uniform(2.5,5.6),rng.uniform(0.95,1.7),rng.uniform(0.95,1.7))

    # Orbital rails and an elevated connector give the silhouette scale.
    for i, tilt in enumerate((0.24,-0.48,0.86)):
        points = []
        for j in range(128):
            t = math.tau*j/128
            p = Vector((3.35*math.cos(t),0.0,central_h*0.47*math.sin(t)))
            p.rotate(Quaternion(Vector((0.0,1.0,0.0)),tilt+i*0.31))
            points.append(p+Vector((0.0,0.65,central_h*0.52)))
        verts, faces = [], []
        _append_tube(verts,faces,points,0.045 if i==0 else 0.027,sides=8,closed=True,cap_ends=False)
        mesh = bpy.data.meshes.new("Orbital rail mesh")
        mesh.from_pydata(verts,[],faces)
        mesh.materials.append(cyan if i==1 else dark)
        mesh.update()
        rail = bpy.data.objects.new("Core orbital rail " + str(i+1),mesh)
        collection.objects.link(rail)
        for poly in mesh.polygons:
            poly.use_smooth = True

    bridge_z = rng.uniform(4.2,5.2)
    box("Transit bridge armor", (0,0.95,bridge_z), (7.8,0.62,0.22), dark, 0.05)
    box("Transit bridge plasma rail", (0,0.60,bridge_z+0.12), (7.4,0.045,0.03), amber, 0.008)
    for i in range(7):
        x=-3.1+i*6.2/6
        box("Bridge support " + str(i+1), (x,0.95,bridge_z-0.32), (0.07,0.08,0.62), shell, 0.015)
    for side in (-1,1):
        box("Approach lane " + str(side), (side*2.1,-7.4,-0.02), (0.7,7.5,0.08), dark, 0.02)
        for i in range(9):
            box("Lane light " + str(side) + " " + str(i+1), (side*2.1,-10.7+i*0.78,0.025), (0.42,0.045,0.02), amber if i%3==0 else cyan, 0.004)

    camera_data = bpy.data.cameras.new("VINLAB Sci-Fi Camera")
    camera = bpy.data.objects.new("VINLAB Sci-Fi Camera", camera_data)
    collection.objects.link(camera)
    camera.location = (19.5,-27.5,17.0)
    _scene_look_at(camera,(0,0,4))
    camera_data.lens = 42
    scene.camera = camera

    for name, loc, color, energy, size in (
        ("VINLAB Key Light",(3,-10,18),(0.72,0.84,1.0),2600,11),
        ("VINLAB Warm Rim",(-9,5,10),(1.0,0.28,0.08),1900,8),
        ("VINLAB Cool Rim",(8,8,12),(0.08,0.38,1.0),2100,7),
    ):
        data = bpy.data.lights.new(name,type="AREA")
        data.energy, data.color, data.shape, data.size = energy, color, "DISK", size
        lamp = bpy.data.objects.new(name,data)
        collection.objects.link(lamp)
        lamp.location = loc
        _scene_look_at(lamp,(0,0,2))

    world = scene.world
    if world is not None:
        world.color = (0.018,0.025,0.045)
        if world.use_nodes and world.node_tree:
            bg = world.node_tree.nodes.get("Background")
            if bg is not None:
                bg.inputs["Color"].default_value = (0.018,0.025,0.045,1.0)
                bg.inputs["Strength"].default_value = 0.32
    scene.render.resolution_x, scene.render.resolution_y = 1600, 900
    scene.render.resolution_percentage = 100
    for obj in context.selected_objects:
        obj.select_set(False)
    hero.select_set(True)
    context.view_layer.objects.active = hero
    if context.area is not None and context.area.type == "VIEW_3D":
        space = context.space_data
        if getattr(space, "region_3d", None) is not None:
            space.region_3d.view_location = Vector((0.0, 0.0, 4.0))
            space.region_3d.view_distance = 28.0
            space.region_3d.view_rotation = camera.rotation_euler.to_quaternion()
            space.region_3d.view_perspective = "PERSP"
    scene["vinlab_scifi_scene_seed"] = settings.seed
    scene["vinlab_scifi_scene_collection"] = collection.name
    return collection, hero


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

    tree["vinlab_version"] = "0.6.0"
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
            "FUTURE_SCULPTURE": _build_future_sculpture,
            "CYBER_MODULE": _build_cyber_module,
            "FOLDED_RIBBON": _build_folded_ribbon,
            "PRISM_REACTOR": _build_prism_reactor,
            "FACETED_TOTEM": _build_faceted_totem,
            "HEX_ARMOR": _build_hex_armor,
            "CIRCUIT_CORE": _build_circuit_core,
            "ORBITAL_PARTICLE": _build_orbital_particle,
            "CELLULAR_VOID": _build_cellular_void,
            "SPIKE_BLOOM": _build_spike_bloom,
        }
        builder = builders.get(shape_type)
        if builder is None:
            self.report({"ERROR"}, "Unknown shape family")
            return {"CANCELLED"}

        try:
            build_result = builder(settings, rng)
            if len(build_result) == 3:
                vertices, faces, face_material_overrides = build_result
            else:
                vertices, faces = build_result
                face_material_overrides = None
            if not vertices or not faces:
                self.report({"ERROR"}, "The shape generator returned empty geometry")
                return {"CANCELLED"}
            obj = _new_mesh_object(
                context, f"VINLAB · {SHAPE_NAMES[shape_type]}",
                vertices, faces, settings.seed, face_material_overrides
            )
        except Exception as exc:
            self.report({"ERROR"}, f"Shape generation failed: {exc}")
            return {"CANCELLED"}

        obj["vinlab_shape_type"] = shape_type
        obj["vinlab_seed"] = settings.seed
        obj["vinlab_version"] = "0.6.0"
        self.report(
            {"INFO"},
            f"Generated {SHAPE_NAMES[shape_type]} · {len(vertices):,} verts / {len(faces):,} faces",
        )
        return {"FINISHED"}


class VINLAB_OT_generate_scifi_scene(bpy.types.Operator):
    bl_idname = "vinlab.generate_scifi_scene"
    bl_label = "Generate Sci-Fi Scene"
    bl_description = "Generate an editable sci-fi environment with modular towers, glowing details, camera, and lights"
    bl_options = {"REGISTER", "UNDO"}

    new_variation: BoolProperty(default=False, options={"HIDDEN"})

    def execute(self, context):
        settings = context.scene.vinlab_settings
        if self.new_variation:
            settings.seed = (settings.seed + 1) % 10000000
        rng = random.Random(settings.seed ^ 0xC1F1)
        try:
            collection, hero = _build_scifi_scene(context, settings, rng)
        except Exception as exc:
            self.report({"ERROR"}, f"Sci-Fi scene generation failed: {exc}")
            return {"CANCELLED"}
        hero["vinlab_scifi_scene_seed"] = settings.seed
        hero["vinlab_version"] = "0.6.0"
        self.report({"INFO"}, f"Generated sci-fi scene with {len(collection.objects)} objects · Seed {settings.seed}")
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
        if settings.shape_type in {"RANDOM", "TWISTED_COLUMN", "FUTURE_SCULPTURE"}:
            box.prop(settings, "twist")
        if settings.shape_type in {"RANDOM", "BRANCHING_FORM"}:
            box.prop(settings, "branch_depth")
        row = box.row(align=True)
        row.operator("vinlab.generate_shape", text="Generate Shape", icon="MESH_DATA")
        row.operator("vinlab.randomize_seed", text="New Variant", icon="FILE_REFRESH")

        box = layout.box()
        box.label(text="2 · Sci-Fi Scene Builder", icon="WORLD")
        box.label(text="Generate a complete editable environment")
        row = box.row(align=True)
        row.operator("vinlab.generate_scifi_scene", text="Generate Scene", icon="SCENE")
        row.operator("vinlab.generate_scifi_scene", text="Random Scene", icon="FILE_REFRESH").new_variation = True

        box = layout.box()
        box.label(text="3 · Animation Builder", icon="NODETREE")
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
    VINLAB_OT_generate_scifi_scene,
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
