bl_info = {
    "name": "VIN Material Lab",
    "author": "VIN / OpenAI",
    "version": (0, 3, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > VIN Material",
    "description": "Procedural material studio with preview, reusable materials and shader controls",
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
    "EARTH_NATURAL": {
        "dark": (0.045, 0.025, 0.014),
        "base": (0.30, 0.16, 0.075),
        "mid": (0.49, 0.32, 0.16),
        "accent": (0.74, 0.36, 0.10),
        "bright": (0.80, 0.70, 0.52),
    },
    "SOFT_PASTEL": {
        "dark": (0.16, 0.18, 0.24),
        "base": (0.58, 0.66, 0.78),
        "mid": (0.86, 0.68, 0.74),
        "accent": (0.95, 0.55, 0.40),
        "bright": (0.95, 0.91, 0.84),
    },
    "OCEAN_COAST": {
        "dark": (0.012, 0.055, 0.085),
        "base": (0.035, 0.28, 0.37),
        "mid": (0.12, 0.60, 0.68),
        "accent": (0.96, 0.55, 0.27),
        "bright": (0.78, 0.91, 0.89),
    },
    "FOREST_MOSS": {
        "dark": (0.015, 0.045, 0.029),
        "base": (0.10, 0.22, 0.12),
        "mid": (0.33, 0.43, 0.20),
        "accent": (0.70, 0.42, 0.12),
        "bright": (0.77, 0.75, 0.58),
    },
    "CANDY_POP": {
        "dark": (0.055, 0.025, 0.16),
        "base": (0.28, 0.13, 0.58),
        "mid": (0.02, 0.62, 0.76),
        "accent": (0.96, 0.09, 0.30),
        "bright": (1.0, 0.78, 0.20),
    },
    "CLAY_TERRACOTTA": {
        "dark": (0.14, 0.055, 0.033),
        "base": (0.47, 0.17, 0.095),
        "mid": (0.70, 0.32, 0.18),
        "accent": (0.88, 0.58, 0.34),
        "bright": (0.94, 0.81, 0.63),
    },
}

FINISHES = {
    "TITANIUM": (0.82, 0.23),
    "BLACK_CHROME": (0.96, 0.12),
    "PORCELAIN": (0.02, 0.22),
    "CARBON_COMPOSITE": (0.46, 0.31),
    "ALIEN_POROUS": (0.08, 0.66),
    "ENERGY_CERAMIC": (0.08, 0.18),
    "CLEAR_GLASS": (0.0, 0.025),
    "FROSTED_GLASS": (0.0, 0.24),
    "CLEAR_PLASTIC": (0.0, 0.12),
    "MATTE_PLASTIC": (0.0, 0.43),
    "RUBBER": (0.0, 0.84),
    "FABRIC": (0.0, 0.88),
    "LEATHER": (0.0, 0.48),
    "WOOD": (0.0, 0.42),
    "STONE": (0.0, 0.82),
    "PAPER": (0.0, 0.90),
}

FINISH_PHYSICS = {
    "TITANIUM": {"metallic": 0.82, "roughness": 0.23, "ior": 1.45},
    "BLACK_CHROME": {"metallic": 0.96, "roughness": 0.12, "ior": 1.48},
    "PORCELAIN": {"metallic": 0.02, "roughness": 0.22, "ior": 1.48, "coat": 0.18},
    "CARBON_COMPOSITE": {"metallic": 0.46, "roughness": 0.31, "ior": 1.50},
    "ALIEN_POROUS": {"metallic": 0.08, "roughness": 0.66, "ior": 1.42},
    "ENERGY_CERAMIC": {"metallic": 0.08, "roughness": 0.18, "ior": 1.48, "coat": 0.3},
    "CLEAR_GLASS": {"metallic": 0.0, "roughness": 0.025, "ior": 1.46, "transmission": 1.0},
    "FROSTED_GLASS": {"metallic": 0.0, "roughness": 0.24, "ior": 1.46, "transmission": 0.9},
    "CLEAR_PLASTIC": {"metallic": 0.0, "roughness": 0.12, "ior": 1.46, "transmission": 0.58, "coat": 0.22},
    "MATTE_PLASTIC": {"metallic": 0.0, "roughness": 0.43, "ior": 1.46, "coat": 0.06},
    "RUBBER": {"metallic": 0.0, "roughness": 0.84, "ior": 1.48},
    "FABRIC": {"metallic": 0.0, "roughness": 0.88, "ior": 1.46, "sheen": 0.42},
    "LEATHER": {"metallic": 0.0, "roughness": 0.48, "ior": 1.46, "sheen": 0.08, "coat": 0.12},
    "WOOD": {"metallic": 0.0, "roughness": 0.42, "ior": 1.46, "coat": 0.08},
    "STONE": {"metallic": 0.0, "roughness": 0.82, "ior": 1.46},
    "PAPER": {"metallic": 0.0, "roughness": 0.90, "ior": 1.46},
}


def _set_input(node, names, value):
    socket = _socket(node, *names) if isinstance(names, tuple) else _socket(node, names)
    if socket is not None:
        socket.default_value = value
        return True
    return False


def _apply_finish_physics(material, shader, finish):
    spec = FINISH_PHYSICS.get(finish, {})
    for key, names in (
        ("metallic", ("Metallic",)),
        ("roughness", ("Roughness",)),
        ("ior", ("IOR",)),
        ("transmission", ("Transmission Weight", "Transmission")),
        ("sheen", ("Sheen Weight", "Sheen")),
        ("coat", ("Coat Weight", "Clearcoat")),
    ):
        if key in spec:
            _set_input(shader, names, spec[key])
    if finish in {"CLEAR_GLASS", "FROSTED_GLASS", "CLEAR_PLASTIC"}:
        # Eevee transparency controls differ across Blender versions; set only properties that exist.
        if hasattr(material, "blend_method"):
            try:
                material.blend_method = "BLEND"
            except (TypeError, ValueError):
                pass
        if hasattr(material, "use_screen_refraction"):
            material.use_screen_refraction = True
        if hasattr(material, "surface_render_method"):
            try:
                material.surface_render_method = "DITHERED"
            except (TypeError, ValueError):
                pass
        if hasattr(material, "show_transparent_back"):
            material.show_transparent_back = True



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
    material["vinmat_version"] = "0.2.0"
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
    _apply_finish_physics(material, shader, settings.surface_finish)

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
        if pattern == "PITTED":
            pits = _new_node(nodes, "ShaderNodeTexVoronoi", "VINMAT · Porous Crater Field", (x0, -120))
            pits.feature = "F1"
            pits.distance = "EUCLIDEAN"
            pits.inputs["Scale"].default_value = settings.texture_scale * 1.35
            links.new(mapping.outputs["Vector"], pits.inputs["Vector"])
            # Keep broad color mottling while the cell field adds crater-like relief.
            bump_factor = pits.outputs.get("Distance") or pits.outputs.get("Color")

    elif pattern == "BRUSHED":
        wave = _new_node(nodes, "ShaderNodeTexWave", "VINMAT · Brushed Grooves", (x0, y0))
        wave.wave_type = "BANDS"
        wave.bands_direction = "X"
        wave.inputs["Scale"].default_value = settings.texture_scale * 15.0
        wave.inputs["Distortion"].default_value = 2.2
        wave.inputs["Detail"].default_value = max(1.0, float(settings.texture_detail))
        links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
        factor = wave.outputs["Fac"]
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

    elif pattern == "FABRIC_WEAVE":
        warp = _new_node(nodes, "ShaderNodeTexWave", "VINMAT · Warp Fibres", (x0, 390))
        weft = _new_node(nodes, "ShaderNodeTexWave", "VINMAT · Weft Fibres", (x0, 80))
        for wave, direction in ((warp, "X"), (weft, "Y")):
            wave.wave_type = "BANDS"
            wave.bands_direction = direction
            wave.inputs["Scale"].default_value = settings.texture_scale * 13.0
            wave.inputs["Distortion"].default_value = 0.22
            wave.inputs["Detail"].default_value = 1.0
            links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
        weave = _new_node(nodes, "ShaderNodeMath", "VINMAT · Woven Fibre Intersections", (-380, 250))
        weave.operation = "MULTIPLY"
        links.new(warp.outputs["Fac"], weave.inputs[0])
        links.new(weft.outputs["Fac"], weave.inputs[1])
        factor = weave.outputs[0]
        bump_factor = factor

    elif pattern == "WOOD_GRAIN":
        wood_noise = _new_node(nodes, "ShaderNodeTexNoise", "VINMAT · Wood Grain Distortion", (x0, 420))
        wood_noise.inputs["Scale"].default_value = settings.texture_scale * 0.75
        wood_noise.inputs["Detail"].default_value = max(2.0, float(settings.texture_detail))
        links.new(mapping.outputs["Vector"], wood_noise.inputs["Vector"])
        grain = _new_node(nodes, "ShaderNodeTexWave", "VINMAT · Flowing Wood Grain", (x0, 100))
        grain.wave_type = "BANDS"
        grain.bands_direction = "X"
        grain.inputs["Scale"].default_value = settings.texture_scale * 4.0
        grain.inputs["Distortion"].default_value = 7.0
        grain.inputs["Detail"].default_value = 4.0
        links.new(mapping.outputs["Vector"], grain.inputs["Vector"])
        links.new(wood_noise.outputs["Fac"], grain.inputs["Distortion"])
        factor = grain.outputs["Fac"]
        bump_factor = factor

    elif pattern == "SPECKLED_STONE":
        mineral = _new_node(nodes, "ShaderNodeTexVoronoi", "VINMAT · Mineral Speckles", (x0, y0))
        mineral.feature = "F1"
        mineral.distance = "EUCLIDEAN"
        mineral.inputs["Scale"].default_value = settings.texture_scale * 4.5
        links.new(mapping.outputs["Vector"], mineral.inputs["Vector"])
        mineral_noise = _new_node(nodes, "ShaderNodeTexNoise", "VINMAT · Stone Clouding", (x0, -130))
        mineral_noise.inputs["Scale"].default_value = settings.texture_scale * 0.8
        mineral_noise.inputs["Detail"].default_value = settings.texture_detail
        links.new(mapping.outputs["Vector"], mineral_noise.inputs["Vector"])
        combined = _new_node(nodes, "ShaderNodeMath", "VINMAT · Stone Flecks", (-370, 250))
        combined.operation = "MULTIPLY"
        links.new(mineral.outputs["Distance"], combined.inputs[0])
        links.new(mineral_noise.outputs["Fac"], combined.inputs[1])
        factor = combined.outputs[0]
        bump_factor = mineral.outputs["Distance"]

    elif pattern == "MICRO_SCRATCHES":
        scratch_noise = _new_node(nodes, "ShaderNodeTexNoise", "VINMAT · Scratch Breakup", (x0, 420))
        scratch_noise.inputs["Scale"].default_value = settings.texture_scale * 0.55
        scratch_noise.inputs["Detail"].default_value = 2.0
        links.new(mapping.outputs["Vector"], scratch_noise.inputs["Vector"])
        scratches = _new_node(nodes, "ShaderNodeTexWave", "VINMAT · Fine Scratch Lines", (x0, 90))
        scratches.wave_type = "BANDS"
        scratches.bands_direction = "X"
        scratches.inputs["Scale"].default_value = settings.texture_scale * 23.0
        scratches.inputs["Distortion"].default_value = 1.2
        scratches.inputs["Detail"].default_value = 2.0
        links.new(mapping.outputs["Vector"], scratches.inputs["Vector"])
        links.new(scratch_noise.outputs["Fac"], scratches.inputs["Distortion"])
        factor = scratches.outputs["Fac"]
        bump_factor = factor

    elif pattern == "WATER_DROPLETS":
        droplets = _new_node(nodes, "ShaderNodeTexVoronoi", "VINMAT · Droplet Cells", (x0, y0))
        droplets.feature = "F1"
        droplets.distance = "EUCLIDEAN"
        droplets.inputs["Scale"].default_value = settings.texture_scale * 3.0
        links.new(mapping.outputs["Vector"], droplets.inputs["Vector"])
        factor = droplets.outputs["Distance"]
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

    # Fine-grain physical response differs by finish; tweak the exposed Principled sockets when available.
    if settings.surface_finish == "PAPER":
        _set_input(shader, ("Subsurface Weight", "Subsurface"), 0.035)
    elif settings.surface_finish == "FABRIC":
        _set_input(shader, ("Sheen Tint",), _rgb(palette["bright"]))
    elif settings.surface_finish == "RUBBER":
        _set_input(shader, ("Specular IOR Level", "Specular"), 0.24)

    bump = _new_node(nodes, "ShaderNodeBump", "VINMAT · Surface Relief", (420, -160))
    bump.inputs["Strength"].default_value = settings.bump_strength
    bump.inputs["Distance"].default_value = settings.bump_distance
    links.new(bump_factor if bump_factor is not None else factor, bump.inputs["Height"])
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
            ("EARTH_NATURAL", "Earth & Natural", "Wood, leather, stone, clay and natural pigments"),
            ("SOFT_PASTEL", "Soft Pastel", "Gentle pastel colors for toys, props and interiors"),
            ("OCEAN_COAST", "Ocean & Coast", "Ocean blue, sea glass and warm sand"),
            ("FOREST_MOSS", "Forest & Moss", "Moss, leaf green and earthy amber"),
            ("CANDY_POP", "Candy Pop", "Playful saturated colors for stylized assets"),
            ("CLAY_TERRACOTTA", "Clay / Terracotta", "Warm red clay and ceramic tones"),
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
            ("CLEAR_GLASS", "Clear Glass", "Highly transmissive polished glass"),
            ("FROSTED_GLASS", "Frosted Glass", "Translucent rough glass with soft highlights"),
            ("CLEAR_PLASTIC", "Clear Plastic", "Tintable transparent plastic or acrylic"),
            ("MATTE_PLASTIC", "Matte Plastic", "Opaque soft-reflection plastic"),
            ("RUBBER", "Rubber", "Dark, matte, soft-looking rubber"),
            ("FABRIC", "Fabric / Cloth", "Textile surface with high roughness and sheen"),
            ("LEATHER", "Leather", "Semi-matte hide with a restrained sheen"),
            ("WOOD", "Wood", "Natural-looking wood with a satin finish"),
            ("STONE", "Stone / Concrete", "Rough mineral surface"),
            ("PAPER", "Paper / Card", "Dry, matte paper, cardboard or cardstock"),
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
            ("FABRIC_WEAVE", "Fabric Weave", "Crossed fibres and textile relief"),
            ("WOOD_GRAIN", "Wood Grain", "Long flowing wood grain with noisy distortion"),
            ("SPECKLED_STONE", "Speckled Stone", "Mineral flecks and rough stone relief"),
            ("MICRO_SCRATCHES", "Micro Scratches", "Fine scratch lines broken by noise"),
            ("WATER_DROPLETS", "Water Droplets", "Small rounded droplet-like surface cells"),
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
    last_material: PointerProperty(name="Last Generated Material", type=bpy.types.Material)


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
        settings.last_material = material
        self.report({"INFO"}, f"Created {material.name} with {len(material.node_tree.nodes)} nodes. Use Apply Last Material or Preview Sphere.")
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
                if obj.data.users > 1:
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


class VINMAT_OT_apply_last_material(bpy.types.Operator):
    bl_idname = "vinmat.apply_last_material"
    bl_label = "Apply Last Material"
    bl_description = "Apply the most recently created VIN material to all selected geometry objects"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        material = context.scene.vinmat_settings.last_material
        if material is None or material.name not in bpy.data.materials:
            self.report({"ERROR"}, "Create a material first")
            return {"CANCELLED"}
        targets = [o for o in context.selected_objects if o.type in {"MESH", "CURVE", "FONT", "SURFACE"}]
        if not targets:
            self.report({"ERROR"}, "Select at least one mesh/curve object in Object Mode")
            return {"CANCELLED"}
        for obj in targets:
            if hasattr(obj.data, "materials"):
                obj.data.materials.clear()
                obj.data.materials.append(material)
                obj.color = material.diffuse_color
        self.report({"INFO"}, f"Applied shared material to {len(targets)} object(s)")
        return {"FINISHED"}


class VINMAT_OT_preview_sphere(bpy.types.Operator):
    bl_idname = "vinmat.preview_sphere"
    bl_label = "Create / Update Preview Sphere"
    bl_description = "Create a dedicated preview sphere and assign the latest material"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.vinmat_settings
        material = settings.last_material
        if material is None or material.name not in bpy.data.materials:
            try:
                material = _make_material(settings, f"VIN Material · {settings.palette.title().replace('_', ' ')}", 0)
                settings.last_material = material
            except Exception as exc:
                self.report({"ERROR"}, f"Could not create preview material: {exc}")
                return {"CANCELLED"}
        obj = bpy.data.objects.get("VINMAT Preview Sphere")
        if obj is None or obj.type != "MESH":
            mesh = bpy.data.meshes.new("VINMAT Preview Sphere Mesh")
            obj = bpy.data.objects.new("VINMAT Preview Sphere", mesh)
            context.scene.collection.objects.link(obj)
            # Preview is placed beside the current selection rather than replacing it.
            if context.active_object:
                obj.location = context.active_object.location + __import__('mathutils').Vector((3.0, 0.0, 0.0))
            # Build sphere mesh without context-sensitive operators.
            import bmesh
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=1.0)
            bm.to_mesh(mesh)
            bm.free()
            for poly in mesh.polygons:
                poly.use_smooth = True
        if hasattr(obj.data, "materials"):
            obj.data.materials.clear()
            obj.data.materials.append(material)
        obj.color = material.diffuse_color
        # Avoid changing the user's selection or active mode.
        self.report({"INFO"}, "Preview sphere updated. Switch viewport to Material Preview to inspect it.")
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
        if settings.surface_finish in {"CLEAR_GLASS", "FROSTED_GLASS", "CLEAR_PLASTIC"}:
            box.label(text="Transparent materials look best in Material Preview or Rendered mode.")
        elif settings.surface_finish in {"FABRIC", "LEATHER", "RUBBER", "PAPER"}:
            box.label(text="Use Fabric Weave, Micro Scratches or Noise for surface detail.")
        elif settings.surface_finish == "WOOD":
            box.label(text="Wood Grain is the recommended texture pattern.")
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
        row.operator("vinmat.create_material", text="Create Material", icon="NODETREE")
        row.operator("vinmat.preview_sphere", text="Preview Sphere", icon="SHADING_RENDERED")
        row = layout.row(align=True)
        row.operator("vinmat.apply_last_material", text="Apply Last Material", icon="MATERIAL")
        row.operator("vinmat.apply_selected", text="Generate + Apply Unique", icon="BRUSH_MATERIAL")
        if settings.last_material and settings.last_material.name in bpy.data.materials:
            box = layout.box()
            box.label(text="Current Material", icon="CHECKMARK")
            box.label(text=settings.last_material.name)
            box.label(text=f"{len(settings.last_material.node_tree.nodes)} shader nodes")
        layout.separator()
        layout.label(text="Create Material makes a reusable datablock.")
        layout.label(text="Apply Last Material shares it across selected objects.")
        layout.label(text="Preview Sphere lets you inspect the surface quickly.")
        layout.label(text="Use Material Preview mode; inspect nodes in Shader Editor.")


CLASSES = (
    VINMAT_Settings,
    VINMAT_OT_create_material,
    VINMAT_OT_apply_selected,
    VINMAT_OT_apply_last_material,
    VINMAT_OT_preview_sphere,
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
