import ast
from pathlib import Path


def _source() -> str:
    source_path = Path(__file__).parents[1] / "app" / "main.py"
    source = source_path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(source_path))
    return source


def test_desktop_entrypoint_is_valid_python() -> None:
    _source()


def test_reference_frame_workflow_includes_automatic_wireframe() -> None:
    source = _source()
    for component in (
        "class MeshViewport",
        "class StudioWindow",
        "def set_reference_image",
        "def auto_detect_frame",
        "self.auto_detect_frame(silent=True)",
        "Auto-generate wireframe",
        "def _draw_mode_toggled",
        "def save_frame",
        "self.auto_edges",
        "frame_strokes",
    ):
        assert component in source
