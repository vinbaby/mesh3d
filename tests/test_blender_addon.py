import ast
from pathlib import Path


def _addon_source() -> str:
    source_path = Path(__file__).parents[1] / "blender_addon" / "vin_procedural_lab.py"
    source = source_path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(source_path))
    return source


def _motion_addon_source() -> str:
    source_path = Path(__file__).parents[1] / "blender_addon" / "vin_motion_lab.py"
    source = source_path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(source_path))
    return source


def _material_addon_source() -> str:
    source_path = Path(__file__).parents[1] / "blender_addon" / "vin_material_lab.py"
    source = source_path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(source_path))
    return source


def test_standalone_material_lab_has_independent_color_and_texture_nodes() -> None:
    source = _material_addon_source()
    assert '"name": "VIN Material Lab"' in source
    assert '"version": (0, 1, 0)' in source
    assert 'bl_category = "VIN Material"' in source
    assert "class VINMAT_OT_apply_selected" in source
    assert "class VINMAT_OT_create_material" in source
    assert "class VINMAT_PT_main" in source
    for palette in (
        "CYBER_AMBER", "MONO_GOLD", "NEON_PRISM",
        "TITANIUM_SUNSET", "PORCELAIN_CHAMPAGNE", "VOID_EMBER",
    ):
        assert palette in source
    for pattern in (
        "CLEAN", "BRUSHED", "NOISE_RAMP", "CARBON_FIBER",
        "HEX_CELLS", "PITTED", "CIRCUIT_LINES",
    ):
        assert pattern in source
    for node_type in (
        "ShaderNodeBsdfPrincipled", "ShaderNodeValToRGB",
        "ShaderNodeTexNoise", "ShaderNodeTexWave",
        "ShaderNodeTexVoronoi", "ShaderNodeBump",
        "ShaderNodeMapping", "ShaderNodeTexCoord",
    ):
        assert node_type in source
    assert "VIN Material Lab" not in _addon_source()
    assert "VINLAB_PT_color" not in _addon_source()
    assert "color_style: EnumProperty" not in _addon_source()


def test_standalone_motion_addon_is_valid_and_independent() -> None:
    source = _motion_addon_source()
    assert '"name": "VIN Motion Lab"' in source
    assert 'bl_category = "VIN Animate"' in source
    assert "class VINMOTION_OT_build_animation" in source
    assert "class VINMOTION_OT_apply_object_motion" in source
    assert "class VINMOTION_PT_actions" in source
    assert 'bl_category = "VIN Actions"' in source
    assert "OBJECT_MOTION_LABELS" in source
    assert '("WOBBLE", "Wobble / Tumble"' in source
    assert '("SHOCKWAVE", "Shockwave Reaction"' in source
    assert '("ORBIT", "Orbit / Revolve"' in source
    assert '("MAGNET", "Magnet Pull / Repel"' in source
    assert '("GLITCH", "Glitch / Teleport"' in source
    assert '("FOLD", "Fold / Unfold"' in source
    assert '("DISSOLVE", "Dissolve / Assemble"' in source
    assert '("CASCADE", "Wave Cascade"' in source
    assert '("DRIFT", "3D Drift"' in source
    assert '("RADIAL", "Radial Pulse"' in source
    assert '("LATTICE_PULSE", "Lattice Pulse"' in source
    assert 'elif animation_type == "LATTICE_PULSE"' in source
    assert 'elif animation_type == "DRIFT"' in source
    assert 'elif animation_type == "RADIAL"' in source
    assert "class VINMOTION_OT_reset_motion" in source
    assert "animation_phase_spread: FloatProperty" in source
    assert "for index, obj in enumerate(targets)" in source
    assert "class VINMOTION_OT_surface_spawn" in source
    assert "class VINMOTION_OT_surface_crawl" in source
    assert "def _build_surface_bvh" in source
    assert "def _projected_random_walk" in source
    assert "def _animate_object_crawl" in source
    assert "Animate Selected Along Surface" in source
    assert "class VINMOTION_OT_build_scatter" in source
    assert "def _surface_triangles" in source
    assert "def _insert_growth_keys" in source
    assert 'name="Phase"' in source
    assert "Spawn Separate Objects" in source
    assert "spawn.animation_type" not in source
    assert "class VINMOTION_PT_animation" in source
    assert 'bl_category = "VIN Animate"' in source
    assert 'bl_category = "VIN Scatter"' in source
    assert 'bl_category = "VIN Spawn"' in source
    assert 'bl_category = "VIN Crawl"' in source
    assert "class VINMOTION_PT_main" not in source
    assert "GeometryNodeDistributePointsOnFaces" in source
    assert "ShaderNodeTexNoise" in source
    assert "ShaderNodeValToRGB" in source
    assert "class VINLAB_PT_main" not in source


def test_blender_addon_is_valid_python() -> None:
    source = _addon_source()
    assert "bl_info" in source
    assert "def register()" in source
    assert "def unregister()" in source


def test_procedural_shape_generators_are_present() -> None:
    source = _addon_source()
    for builder in (
        "_build_twisted_column",
        "_build_orbit_cage",
        "_build_organic_blob",
        "_build_crystal_cluster",
        "_build_branching_form",
        "_build_future_sculpture",
        "_build_cyber_module",
        "_build_folded_ribbon",
        "_build_prism_reactor",
        "_build_faceted_totem",
        "_build_hex_armor",
        "_build_circuit_core",
        "_build_orbital_particle",
        "_build_cellular_void",
        "_build_spike_bloom",
        "_build_alien_lattice_parts",
    ):
        assert f"def {builder}" in source
    assert "class VINLAB_OT_generate_shape" in source
    assert "Random Object" in source
    assert "Cyber Module" in source
    assert "Folded Ribbon" in source
    assert "Prism Reactor" in source
    assert "Faceted Totem" in source
    assert "Hex Armor" in source
    assert "Circuit Core" in source
    assert "Orbital Particle" in source
    assert "Cellular Void" in source
    assert "Spike Bloom" in source
    assert "Alien Lattice" in source
    assert "Triangular Frame" in source
    assert "Damaged shell" in source or "damaged ceramic shell" in source
    assert "def _append_hex_tile" in source
    assert "def _append_uv_sphere" in source
    assert "random.Random(settings.seed)" in source


def test_separate_components_and_noise_scatter_are_available() -> None:
    source = _addon_source()
    assert 'name="Auto Separate Components"' in source
    assert "def _separate_loose_parts" in source
    assert 'bpy.ops.mesh.separate(type="LOOSE")' in source
    assert "class VINLAB_OT_separate_loose_parts" in source
    assert "class VINLAB_OT_build_field_scatter" in source
    assert "def _build_field_scatter_group" in source
    panel = source[source.index("class VINLAB_PT_main"):source.index("\n\nCLASSES =")]
    assert 'box.label(text="2 · Sci-Fi Scene Builder"' in panel
    assert "Animation and Noise/Color Ramp tools are in the separate VIN Motion add-on." in panel
    assert 'box.label(text="2 · Noise / Color Ramp Scatter"' not in panel
    assert "ShaderNodeTexNoise" in source
    assert "ShaderNodeValToRGB" in source
    assert "GeometryNodeDistributePointsOnFaces" in source
    assert "Noise Texture" in source and "Color Ramp" in source


def test_scifi_scene_builder_creates_environment_assets() -> None:
    source = _addon_source()
    assert "class VINLAB_OT_generate_scifi_scene" in source
    assert "def _build_scifi_scene" in source
    assert "VINLAB Sci-Fi Camera" in source
    assert "VINLAB Warm Rim" in source
    assert 'scene["vinlab_scifi_scene_seed"]' in source


def test_animation_builder_creates_real_geometry_nodes() -> None:
    source = _addon_source()
    assert "class VINLAB_OT_build_animation" in source
    assert 'bpy.data.node_groups.new(' in source
    for node_type in (
        "GeometryNodeInputSceneTime",
        "GeometryNodeSetPosition",
        "GeometryNodeTransform",
        "ShaderNodeCombineXYZ",
    ):
        assert node_type in source
    for animation in ('"BOB"', '"SPIN"', '"PULSE"', '"TWIST"'):
        assert animation in source
    assert "dict(ANIMATION_ITEMS)" not in source
