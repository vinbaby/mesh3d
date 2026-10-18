import ast
from pathlib import Path


def test_desktop_entrypoint_is_valid_python() -> None:
    source_path = Path(__file__).parents[1] / "app" / "main.py"
    source = source_path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(source_path))


def test_clean_start_contains_core_studio_components() -> None:
    source_path = Path(__file__).parents[1] / "app" / "main.py"
    source = source_path.read_text(encoding="utf-8")
    for component in ("class MeshViewport", "class StudioWindow", "def build_mesh", "def main"):
        assert component in source
