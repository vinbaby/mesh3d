import ast
from pathlib import Path


def _addon_source() -> str:
    source_path = Path(__file__).parents[1] / "blender_addon" / "vin_procedural_lab.py"
    source = source_path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(source_path))
    return source


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
    ):
        assert f"def {builder}" in source
    assert "class VINLAB_OT_generate_shape" in source
    assert "random.Random(settings.seed)" in source


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
