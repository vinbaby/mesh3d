bl_info = {
    "name": "VIN Material Lab",
    "author": "VIN / OpenAI",
    "version": (0, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > VIN Material",
    "description": "Standalone shader-node builder for curated sci-fi colors and surface textures",
    "category": "Material",
}

import bpy
import math
import random
from bpy.props import (
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
)


PALETTES = {
    "CYBER_AMBER": {
        "dark": (0.008, 0.016, 0.032),
        "base": (0.035, 0.105, 0.19),
        "mid": (0.035, 0.36, 0.68),
        "accent": (1.0, 0.19, 0.018),
        "bright": (0.72, 0.79, 0.86),
    },
    "MONO_GOLD": {
        "dark": (0.006, 0.008, 0.012),
        "base": (0.12, 0.15, 0.18),
        "mid": (0.46, 0.51, 0.56),
        "accent": (0.74, 0.43, 0.16),
        "bright": (0.86, 0.88, 0.90),
    },
    "NEON_PRISM": {
        "dark": (0.006, 0.008, 0.028),
        "base": (0.015, 0.12, 0.31),
        "mid": (0.0, 0.58, 0.88),
        "accent": (0.96, 0.025, 0.48),
        "bright": (0.75, 0.10, 0.88),
    },
    "TITANIUM_SUNSET": {
        "dark": (0.014, 0.027, 0.052),
        "base": (0.19, 0.28, 0.39),
        "mid": (0.58, 0.68, 0.77),
        "accent": (1.0, 0.24, 0.018),
        "bright": (0.90, 0.62, 0.35),
    },
    "PORCELAIN_CHAMPAGNE": {
        "dark": (0.075, 0.077, 0.078),
        "base": (0.56, 0.60, 0.61),
        "mid": (0.84, 0.84, 0.79),
        "accent": (0.72, 0.47, 0.24),
        "bright": (0.97, 0.93, 0.84),
    },
    "VOID_EMBER": {
        "dark": (0.003, 0.004, 0.007),
        "base": (0.035, 0.045, 0.058),
        "mid": (0.20, 0.23, 0.26),
        "accent": (0.96, 0.085, 0.008),
        "bright": (0.68, 0.70, 0.72),
    },
}

FINISHES = {
    "TITANIUM": (0.82, 0.23),
    "BLACK_CHROME": (0.96, 0.12),
    "PORCELAIN": (0.16, 0.22),
    "CARBON_COMPOSITE": (0.46, 0.31),
    "ALIEN_POROUS": (0.38, 0.29),
    "ENERGY_CERAMIC": (0.26, 0.18),
}


def _socket(node, *names):
    for name in names:
        result = node.inputs.get(name)
        if result is not None:
            return result
    return None


def _output(node, *names):
    for name in names:
        result = node.outputs.get(name)
        if result is not None:
            return result
    return None


def _rgb(color):
    return (float(color[0]), float(color[1]), float(color[2]), 1.0)


def _new_node(nodes, node_type, name, location, label=None):
    node = nodes.new(node_type)
    node.name = name
    node.label = label or name.replace("VINMAT · ", "")
    node.location = location
    return node


def _make_material(settings, material_name, seed_offset=0):
    rng = random.Random(settings.seed + seed_offset * 7919)
    palette = PALETTES[settings.palette]
    material = bpy.data.materials.new(name=material_name)
    material.use_nodes = True
    material.diffuse_color = _rgb(palette["base"])
    material["vinmat_version"] = "0.1.0"
    material["vinmat_palette"] = settings.palette
    material["vinmat_finish"] = settings.surface_finish
    material["vinmat_texture"] = settings.texture_pattern
    material["vinmat_seed"] = int(settings.seed + seed_offset)

    tree = material.node_tree
    nodes, links = tree.nodes, tree.links
    nodes.clear()

    output = _new_node(nodes, "ShaderNodeOutputMaterial", "VINMAT · Material Output", (980, 120))
    shader = _new_node(nodes, "ShaderNodeBsdfPrincipled", "VINMAT · Principled Surface", (700, 120))
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    metallic, roughness = FINISHES[settings.surface_finish]
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness

    coords = _new_node(nodes, "ShaderNodeTexCoord", "VINMAT · Coordinates", (-1100, 180))
    mapping = _new_node(nodes, "ShaderNodeMapping", "VINMAT · Seed Mapping", (-900, 180))
    mapping.inputs["Location"].default_value = (
        rng.uniform(-20.0, 20.0),
        rng.uniform(-20.0, 20.0),
        rng.uniform(-20.0, 20.0),
    )
    variation = rng.uniform(0.88, 1.12)
    mapping.inputs["Scale"].default_value = (
        variation, variation, variation
    )
    generated = _output(coords, "Generated") or _output(coords, "Object")
    if generated is not None:
        links.new(generated, mapping.inputs["Vector"])

    pattern = settings.texture_pattern
    factor = None
    bump_factor = None
    x0, y0 = -650, 240

    if pattern in {"CLEAN", "NOISE_RAMP", "PITTED"}:
        noise = _new_node(nodes, "ShaderNodeTexNoise", "VINMAT · Macro Noise", (x0, y0))
        noise.noise_dimensions = "3D"
        noise.inputs["Scale"].default_value = settings.texture_scale * (0.65 if pattern == "CLEAN" else 1.0)
        noise.inputs["Detail"].default_value = settings.texture_detail
        noise.inputs["Roughness"].default_value = 0.72
        links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
        factor = noise.outputs["Fac"]
        bump_factor = factor

    elif pattern == "BRUSHED":
        wave = _new_node(nodes, "ShaderNodeTexWave", "VINMAT · Brushed Grooves", (x0, y0))
        wave.wave_type = "BANDS"
        wave.bands_direction = "X"
        wave.inputs["Scale"].default_value = settings.texture_scale * 15.0
        wave.inputs["Distortion"].default_value = 2.2
        wave.inputs["Detail"].default_value = max(1.0, float(settings.texture_detail))
        links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
        factor = wave.outputs["Color"]
        bump_factor = wave.outputs["Fac"]

    elif pattern == "CARBON_FIBER":
        wave_x = _new_node(nodes, "ShaderNodeTexWave", "VINMAT · Carbon Weave X", (x0, 390))
        wave_y = _new_node(nodes, "ShaderNodeTexWave", "VINMAT · Carbon Weave Y", (x0, 90))
        for wave, direction in ((wave_x, "X"), (wave_y, "Y")):
            wave.wave_type = "BANDS"
            wave.bands_direction = direction
            wave.inputs["Scale"].default_value = settings.texture_scale * 10.0
            wave.inputs["Distortion"].default_value = 0.35
            wave.inputs["Detail"].default_value = 2.0
            links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
        weave = _new_node(nodes, "ShaderNodeMath", "VINMAT · Weave Crossings", (-380, 270))
        weave.operation = "MULTIPLY"
        links.new(wave_x.outputs["Fac"], weave.inputs[0])
        links.new(wave_y.outputs["Fac"], weave.inputs[1])
        factor = weave.outputs[0]
        bump_factor = factor

    elif pattern == "HEX_CELLS":
        voronoi = _new_node(nodes, "ShaderNodeTexVoronoi", "VINMAT · Hex Cell Field", (x0, y0))
        voronoi.distance = "EUCLIDEAN"
        voronoi.inputs["Scale"].default_value = settings.texture_scale * 2.5
        try:
            voronoi.feature = "DISTANCE_TO_EDGE"
        except Exception:
            voronoi.feature = "F1"
        links.new(mapping.outputs["Vector"], voronoi.inputs["Vector"])
        factor = _output(voronoi, "Distance") or _output(voronoi, "Color")
        bump_factor = _output(voronoi, "Distance") or _output(voronoi, "Color")

    elif pattern == "CIRCUIT_LINES":
        circuit_noise = _new_node(nodes, "ShaderNodeTexNoise", "VINMAT · Circuit Distortion", (x0, 430))
        circuit_noise.inputs["Scale"].default_value = settings.texture_scale * 0.9
        circuit_noise.inputs["Detail"].default_value = 2.0
        links.new(mapping.outputs["Vector"], circuit_noise.inputs["Vector"])
        wave = _new_node(nodes, "ShaderNodeTexWave", "VINMAT · Circuit Tracks", (x0, 80))
        wave.wave_type = "BANDS"
        wave.bands_direction = "X"
        wave.inputs["Scale"].default_value = settings.texture_scale * 5.0
        wave.inputs["Distortion"].default_value = 5.0
        wave.inputs["Detail"].default_value = 3.0
        if _socket(wave, "Distortion") is not None:
            links.new(circuit_noise.outputs["Fac"], wave.inputs["Distortion"])
        links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
        factor = wave.outputs["Fac"]
        bump_factor = factor

    ramp = _new_node(nodes, "ShaderNodeValToRGB", "VINMAT · Color Ramp", (-100, 230))
    ramp.label = "VIN Material · Palette Ramp"
    elements = ramp.color_ramp.elements
    elements[0].position = 0.0
    elements[0].color = _rgb(palette["dark"])
    elements[1].position = 1.0
    elements[1].color = _rgb(palette["accent"])
    mid1 = elements.new(0.30)
    mid1.color = _rgb(palette["base"])
    mid2 = elements.new(0.63)
    mid2.color = _rgb(palette["mid"])
    ramp_elements = sorted(list(ramp.color_ramp.elements), key=lambda element: element.position)
    contrast = max(0.05, min(0.49, settings.ramp_contrast))
    strength = max(0.0, min(1.0, settings.accent_strength))
    positions = [
        0.0,
        max(0.08, 0.5 - contrast),
        min(0.92, 0.5 + contrast * 0.35),
        max(0.58, min(1.0, 1.0 - strength * 0.28)),
    ]
    # Assign monotonically increasing stops; keep the final accent stop inside [0, 1].
    positions = sorted(positions)
    colors = [palette["dark"], palette["base"], palette["mid"], palette["accent"]]
    for element, position, color in zip(ramp_elements, positions, colors):
        element.position = position
        element.color = _rgb(color)
    links.new(factor, ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])

    bump = _new_node(nodes, "ShaderNodeBump", "VINMAT · Surface Relief", (420, -160))
    bump.inputs["Strength"].default_value = settings.bump_strength
    bump.inputs["Distance"].default_value = settings.bump_distance
    links.new(bump_factor or factor, bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])

    # Use the same procedural palette as a subtle emission map. It is opt-in via Glow Strength.
    emission_color = _socket(shader, "Emission Color", "Emission")
    emission_strength = _socket(shader, "Emission Strength")
    if emission_color is not None:
        links.new(ramp.outputs["Color"], emission_color)
    if emission_strength is not None:
        emission_strength.default_value = settings.glow_strength

    material["vinmat_node_count"] = len(nodes)
    material["vinmat_link_count"] = len(tree.links)
    return material


class VINMAT_Settings(bpy.types.PropertyGroup):
    palette: EnumProperty(
        name="Color Palette",
        items=[
            ("CYBER_AMBER", "Cyber Amber", "Graphite, titanium blue, cyan and orange"),
            ("MONO_GOLD", "Monochrome + Gold", "Black, silver and champagne gold"),
            ("NEON_PRISM", "Neon Prism", "Electric cyan, magenta and violet"),
            ("TITANIUM_SUNSET", "Titanium Sunset", "Cold titanium and orange accents"),
            ("PORCELAIN_CHAMPAGNE", "Porcelain Champagne", "Ivory ceramic with champagne metal"),
            ("VOID_EMBER", "Void Ember", "Black metal and ember-orange highlights"),
        ],
        default="CYBER_AMBER",
    )
    surface_finish: EnumProperty(
        name="Surface Finish",
        items=[
            ("TITANIUM", "Titanium", "Machined metal with a clear reflection"),
            ("BLACK_CHROME", "Black Chrome", "Very metallic, dark and glossy"),
            ("PORCELAIN", "Ceramic / Porcelain", "Smooth, low-metallic ceramic"),
            ("CARBON_COMPOSITE", "Carbon Composite", "Semi-metallic composite"),
            ("ALIEN_POROUS", "Alien Porous", "Organic-looking, irregular material"),
            ("ENERGY_CERAMIC", "Energy Ceramic", "Glossy ceramic for glowing sci-fi parts"),
        ],
        default="TITANIUM",
    )
    texture_pattern: EnumProperty(
        name="Texture Pattern",
        items=[
            ("CLEAN", "Clean Variation", "Broad subtle material variation"),
            ("BRUSHED", "Brushed Metal", "Fine directional brushed lines"),
            ("NOISE_RAMP", "Noise / Color Ramp", "Procedural noise mapped through the palette ramp"),
            ("CARBON_FIBER", "Carbon Fiber", "Crossed woven bands"),
            ("HEX_CELLS", "Hex / Cell Pattern", "Voronoi cell boundaries and surface relief"),
            ("PITTED", "Pitted / Porous", "Irregular mottling with procedural relief"),
            ("CIRCUIT_LINES", "Circuit Lines", "Distorted directional lines like etched tracks"),
        ],
        default="NOISE_RAMP",
    )
    seed: IntProperty(name="Seed", default=37, min=0, max=9999999)
    texture_scale: FloatProperty(name="Texture Scale", default=3.2, min=0.05, max=80.0, precision=2)
    texture_detail: IntProperty(name="Texture Detail", default=4, min=0, max=15)
    ramp_contrast: FloatProperty(name="Ramp Contrast", default=0.22, min=0.05, max=0.49, precision=2)
    accent_strength: FloatProperty(name="Accent Strength", default=0.55, min=0.0, max=1.0, precision=2)
    bump_strength: FloatProperty(name="Bump Strength", default=0.18, min=0.0, max=1.0, precision=2)
    bump_distance: FloatProperty(name="Bump Distance", default=0.06, min=0.001, max=1.0, precision=3)
    glow_strength: FloatProperty(name="Glow Strength", default=0.0, min=0.0, max=20.0, precision=2)


class VINMAT_OT_create_material(bpy.types.Operator):
    bl_idname = "vinmat.create_material"
    bl_label = "Create Node Material"
    bl_description = "Create a standalone material with an editable procedural shader-node network"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.vinmat_settings
        try:
            material = _make_material(settings, f"VIN Material · {settings.palette.title().replace('_', ' ')}", 0)
        except Exception as exc:
            self.report({"ERROR"}, f"Material node creation failed: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Created {material.name} with {len(material.node_tree.nodes)} nodes")
        return {"FINISHED"}


class VINMAT_OT_apply_selected(bpy.types.Operator):
    bl_idname = "vinmat.apply_selected"
    bl_label = "Apply Material to Selected"
    bl_description = "Create a separate editable material node tree for each selected geometry object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.vinmat_settings
        targets = [obj for obj in context.selected_objects if obj.type in {"MESH", "CURVE", "FONT", "SURFACE"}]
        if not targets:
            self.report({"ERROR"}, "Select one or more mesh or curve objects first")
            return {"CANCELLED"}
        completed = 0
        try:
            for index, obj in enumerate(targets):
                material = _make_material(
                    settings,
                    f"VIN Material · {obj.name} · {settings.palette.title().replace('_', ' ')}",
                    index,
                )
                if obj.type == "MESH" and obj.data.users > 1:
                    obj.data = obj.data.copy()
                if hasattr(obj.data, "materials"):
                    obj.data.materials.clear()
                    obj.data.materials.append(material)
                    obj.color = _rgb(PALETTES[settings.palette]["base"])
                completed += 1
        except Exception as exc:
            self.report({"ERROR"}, f"Applied to {completed}/{len(targets)} objects before error: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Created independent shader materials for {completed} selected object(s)")
        return {"FINISHED"}


class VINMAT_PT_main(bpy.types.Panel):
    bl_label = "VIN Material Lab"
    bl_idname = "VINMAT_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VIN Material"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.vinmat_settings
        box = layout.box()
        box.label(text="1 · Art-Directed Color", icon="MATERIAL")
        box.prop(settings, "palette")
        box.prop(settings, "surface_finish")
        box.prop(settings, "seed")
        box.label(text="A new Seed offsets the procedural pattern.")
        box = layout.box()
        box.label(text="2 · Surface Texture Nodes", icon="NODETREE")
        box.prop(settings, "texture_pattern")
        box.prop(settings, "texture_scale")
        box.prop(settings, "texture_detail")
        box.prop(settings, "ramp_contrast")
        box.prop(settings, "accent_strength")
        box.prop(settings, "bump_strength")
        box.prop(settings, "bump_distance")
        box.prop(settings, "glow_strength")
        row = layout.row(align=True)
        row.operator("vinmat.apply_selected", text="Apply to Selected", icon="MATERIAL")
        row.operator("vinmat.create_material", text="Create Nodes", icon="NODETREE")
        layout.separator()
        layout.label(text="Each object gets its own material/node tree.")
        layout.label(text="Use the Shader Editor to inspect or edit the generated nodes.")


CLASSES = (
    VINMAT_Settings,
    VINMAT_OT_create_material,
    VINMAT_OT_apply_selected,
    VINMAT_PT_main,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.vinmat_settings = PointerProperty(type=VINMAT_Settings)


def unregister():
    if hasattr(bpy.types.Scene, "vinmat_settings"):
        del bpy.types.Scene.vinmat_settings
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass


if __name__ == "__main__":
    register()
