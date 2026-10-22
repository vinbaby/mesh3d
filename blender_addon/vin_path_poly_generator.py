bl_info = {
    "name": "VIN Path Poly Generator",
    "author": "VIN Studio",
    "version": (0, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > VIN Lab > Path Poly",
    "description": "Generate editable randomized low-poly solids from a closed Path curve",
    "category": "Add Mesh",
}

import bpy
import bmesh
import math
import random
from mathutils import Vector
from bpy.props import (
    IntProperty,
    FloatProperty,
    BoolProperty,
    EnumProperty,
    PointerProperty,
)


def _curve_outline(curve_obj, resolution=16):
    """Return a closed 2D outline in world XY, sampled from the active curve spline."""
    if curve_obj is None or curve_obj.type != 'CURVE':
        raise ValueError("Select a Curve object first.")
    if not curve_obj.data.splines:
        raise ValueError("The selected Curve has no spline.")

    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = curve_obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        world = evaluated.matrix_world
        # Evaluated curve mesh is used to sample Bezier/NURBS splines smoothly.
        coords = [world @ v.co for v in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()

    if len(coords) < 3:
        # Fallback for a simple Poly spline when curve evaluation gives no vertices.
        spline = curve_obj.data.splines[0]
        if spline.type != 'POLY':
            raise ValueError("Could not sample this curve. Try converting it to a Poly curve.")
        coords = [curve_obj.matrix_world @ p.co.xyz for p in spline.points]

    # The tool intentionally uses the XY projection so a front-view drawing becomes a solid.
    points = []
    for p in coords:
        q = (float(p.x), float(p.y))
        if not points or (Vector(q) - Vector(points[-1])).length > 1e-5:
            points.append(q)
    if len(points) > 2 and (Vector(points[0]) - Vector(points[-1])).length < 1e-5:
        points.pop()
    if len(points) < 3:
        raise ValueError("The Path needs at least three distinct points.")
    # Reject a degenerate outline.
    area = sum(points[i][0] * points[(i + 1) % len(points)][1] -
               points[(i + 1) % len(points)][0] * points[i][1]
               for i in range(len(points))) * 0.5
    if abs(area) < 1e-6:
        raise ValueError("The Path has almost zero area. Draw it in Front View (XY plane).")
    return points


def _point_on_segment(p, a, b, eps=1e-4):
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length2 = dx * dx + dy * dy
    if length2 < 1e-12:
        return math.hypot(px - ax, py - ay) < eps
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length2))
    qx, qy = ax + t * dx, ay + t * dy
    return math.hypot(px - qx, py - qy) < eps


def _is_boundary_point(p, outline):
    return any(_point_on_segment(p, outline[i], outline[(i + 1) % len(outline)])
               for i in range(len(outline)))


def _build_poly_solid(outline, settings, seed):
    rng = random.Random(seed)
    bm = bmesh.new()
    try:
        base = [bm.verts.new((x, y, 0.0)) for x, y in outline]
        face = bm.faces.new(base)
        bm.faces.ensure_lookup_table()
        bmesh.ops.triangulate(bm, faces=[face], quad_method='BEAUTY', ngon_method='EAR_CLIP')

        # Subdivide the triangulated surface to create a denser, varied polygon pattern.
        cuts = max(0, settings.subdivisions)
        if cuts:
            bmesh.ops.subdivide_edges(
                bm, edges=list(bm.edges), cuts=cuts,
                use_grid_fill=True, smooth=0.0,
            )

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        bm.verts.index_update()
        bm.edges.index_update()
        bm.faces.index_update()

        # Keep the drawn silhouette fixed; perturb only interior points.
        span_x = max(x for x, y in outline) - min(x for x, y in outline)
        span_y = max(y for x, y in outline) - min(y for x, y in outline)
        jitter = settings.jitter * min(max(span_x, 0.001), max(span_y, 0.001))
        depth = settings.depth
        for v in bm.verts:
            p = (v.co.x, v.co.y)
            boundary = _is_boundary_point(p, outline)
            if not boundary:
                v.co.x += rng.uniform(-jitter, jitter)
                v.co.y += rng.uniform(-jitter, jitter)
            # A little height variation creates faceted planes, while the outline remains stable.
            v.co.z = depth + (0.0 if boundary else rng.uniform(-settings.height_variation, settings.height_variation))

        # Save top surface data and boundary edges before creating the bottom.
        top_verts = list(bm.verts)
        top_faces = [tuple(v.index for v in f.verts) for f in bm.faces]
        boundary_edges = [(e.verts[0].index, e.verts[1].index)
                          for e in bm.edges if len(e.link_faces) == 1]

        top_coords = [v.co.copy() for v in top_verts]
        bottom_z = 0.0
        verts = [(c.x, c.y, c.z) for c in top_coords]
        verts.extend((c.x, c.y, bottom_z) for c in top_coords)
        n = len(top_coords)
        faces = [tuple(face_indices) for face_indices in top_faces]
        # Reverse the bottom cap normals.
        faces.extend(tuple(n + i for i in reversed(face_indices)) for face_indices in top_faces)
        for a, b in boundary_edges:
            faces.append((a, n + a, n + b, b))

        mesh = bpy.data.meshes.new("VIN_RandomPoly_Mesh")
        mesh.from_pydata(verts, [], faces)
        mesh.validate(verbose=False)
        mesh.update()
        return mesh
    finally:
        bm.free()


def _make_generated(context, settings, replace_existing=False):
    source = settings.path_object or context.active_object
    outline = _curve_outline(source)
    seed = settings.seed
    mesh = _build_poly_solid(outline, settings, seed)
    obj_name = "VIN_Poly_" + str(seed)
    obj = bpy.data.objects.new(obj_name, mesh)
    context.collection.objects.link(obj)
    obj["vin_generator"] = "VIN Path Poly Generator"
    obj["vin_seed"] = seed
    obj["vin_source_path"] = source.name
    obj["vin_path_poly_version"] = "0.1.0"

    # Keep generated object at world origin because outline coordinates are sampled in world space.
    obj.matrix_world.identity()
    if settings.bevel > 0:
        mod = obj.modifiers.new("Soft Poly Edges", 'BEVEL')
        mod.width = settings.bevel
        mod.segments = 1
        if hasattr(mod, "affect"):
            mod.affect = 'EDGES'
    if settings.weighted_normals:
        try:
            mod = obj.modifiers.new("Weighted Normals", 'WEIGHTED_NORMAL')
            mod.keep_sharp = True
        except Exception:
            pass

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    context.view_layer.objects.active = obj
    return obj


class VINPPG_Settings(bpy.types.PropertyGroup):
    path_object: PointerProperty(
        name="Path Curve", type=bpy.types.Object,
        description="Closed Curve object used as the 2D silhouette",
        poll=lambda self, obj: obj.type == 'CURVE',
    )
    depth: FloatProperty(name="Depth", default=0.8, min=0.01, max=20.0, subtype='DISTANCE')
    subdivisions: IntProperty(name="Facet Density", default=2, min=0, max=4,
                               description="More subdivisions create smaller polygon facets")
    jitter: FloatProperty(name="Organic Randomness", default=0.12, min=0.0, max=0.45)
    height_variation: FloatProperty(name="Facet Height", default=0.12, min=0.0, max=2.0)
    bevel: FloatProperty(name="Edge Bevel", default=0.015, min=0.0, max=0.25)
    seed: IntProperty(name="Random Seed", default=1, min=0, max=999999)
    weighted_normals: BoolProperty(name="Weighted Normals", default=True)
    replace_last: BoolProperty(name="Delete Previous Generated", default=False)


class VINPPG_OT_generate(bpy.types.Operator):
    bl_idname = "vin_ppg.generate"
    bl_label = "Generate Poly"
    bl_description = "Create a real editable low-poly solid from the selected closed Path curve"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.vin_ppg_settings
        try:
            source = settings.path_object or context.active_object
            if source is None or source.type != 'CURVE':
                self.report({'ERROR'}, "Select a closed Curve Path first.")
                return {'CANCELLED'}
            if settings.replace_last:
                for obj in list(context.scene.objects):
                    if obj.get("vin_generator") == "VIN Path Poly Generator":
                        bpy.data.objects.remove(obj, do_unlink=True)
            obj = _make_generated(context, settings)
            self.report({'INFO'}, "Generated " + obj.name + ". Mesh is editable in Edit Mode.")
            return {'FINISHED'}
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}


class VINPPG_OT_randomize(bpy.types.Operator):
    bl_idname = "vin_ppg.randomize"
    bl_label = "Randomize"
    bl_description = "Generate a new variant from the same Path using a new random seed"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.vin_ppg_settings
        settings.seed = (settings.seed + 1) % 1000000
        try:
            obj = _make_generated(context, settings)
            self.report({'INFO'}, "New variant generated with seed " + str(settings.seed))
            return {'FINISHED'}
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}


class VINPPG_PT_panel(bpy.types.Panel):
    bl_label = "Path Poly Generator"
    bl_idname = "VINPPG_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VIN Lab"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.vin_ppg_settings
        layout.label(text="1. Select a closed Curve Path", icon='CURVE_PATH')
        layout.prop(settings, "path_object")
        layout.label(text="2. Generate a randomized solid")
        layout.prop(settings, "depth")
        layout.prop(settings, "subdivisions")
        layout.prop(settings, "jitter")
        layout.prop(settings, "height_variation")
        layout.prop(settings, "bevel")
        layout.separator()
        layout.prop(settings, "seed")
        row = layout.row(align=True)
        row.operator("vin_ppg.generate", icon='MESH_ICOSPHERE')
        row.operator("vin_ppg.randomize", icon='FILE_REFRESH')
        layout.prop(settings, "replace_last")
        layout.prop(settings, "weighted_normals")
        layout.separator()
        layout.label(text="Tip: draw the Path in Front View (XY).", icon='INFO')
        layout.label(text="Generated result is a real mesh.")


classes = (
    VINPPG_Settings,
    VINPPG_OT_generate,
    VINPPG_OT_randomize,
    VINPPG_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.vin_ppg_settings = PointerProperty(type=VINPPG_Settings)


def unregister():
    del bpy.types.Scene.vin_ppg_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
