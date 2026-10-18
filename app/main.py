from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


@dataclass
class ReliefMesh:
    resolution: int
    vertices: list[tuple[float, float, float]]
    colors: list[tuple[int, int, int]]
    triangles: list[tuple[int, int, int]]


class MeshViewport(QWidget):
    """Small software-rendered relief viewport; no heavy 3D engine required."""

    mesh_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(360, 320)
        self.setMouseTracking(True)
        self.mesh: ReliefMesh | None = None
        self.rot_x = -0.25
        self.rot_y = 0.45
        self.zoom = 1.0
        self.wireframe = False
        self._last_mouse = None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_mesh(self, mesh: ReliefMesh | None) -> None:
        self.mesh = mesh
        self.mesh_changed.emit(mesh)
        self.update()

    def reset_view(self) -> None:
        self.rot_x, self.rot_y, self.zoom = -0.25, 0.45, 1.0
        self.update()

    def front_view(self) -> None:
        self.rot_x, self.rot_y, self.zoom = 0.0, 0.0, 1.0
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#282e37"))
        self._draw_grid(painter)
        if not self.mesh:
            painter.setPen(QColor("#b7c1d0"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "VIN 3D STUDIO\n\nLoad an image to start",
            )
            painter.end()
            return

        points = [self._project(v) for v in self.mesh.vertices]
        # Painter's algorithm: far faces first. The first phase intentionally
        # keeps resolution modest to avoid blocking the UI on large meshes.
        ordered = sorted(
            self.mesh.triangles,
            key=lambda face: (
                points[face[0]][2] + points[face[1]][2] + points[face[2]][2]
            ) / 3.0,
        )
        for face in ordered:
            p0, p1, p2 = (points[face[0]], points[face[1]], points[face[2]])
            polygon = QPolygonF(
                [QPointF(p0[0], p0[1]), QPointF(p1[0], p1[1]), QPointF(p2[0], p2[1])]
            )
            c0, c1, c2 = (self.mesh.colors[index] for index in face)
            depth_shade = max(0.55, min(1.18, 0.92 + (p0[2] + p1[2] + p2[2]) / 18.0))
            red = max(0, min(255, int((c0[0] + c1[0] + c2[0]) / 3 * depth_shade)))
            green = max(0, min(255, int((c0[1] + c1[1] + c2[1]) / 3 * depth_shade)))
            blue = max(0, min(255, int((c0[2] + c1[2] + c2[2]) / 3 * depth_shade)))
            if self.wireframe:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(120, 226, 178, 130), 0.45))
            else:
                painter.setBrush(QColor(red, green, blue))
                painter.setPen(QPen(QColor(12, 17, 23, 55), 0.35))
            painter.drawPolygon(polygon)
        painter.end()

    def _draw_grid(self, painter: QPainter) -> None:
        w, h = self.width(), self.height()
        base = int(h * 0.72)
        painter.setPen(QPen(QColor(160, 175, 195, 26), 1))
        for i in range(-10, 11):
            x = w // 2 + i * 30
            painter.drawLine(x, base, w // 2 + i * 65, h)
        for row in range(8):
            y = base + row * row * 4
            painter.drawLine(0, y, w, y)

    def _project(self, vertex: tuple[float, float, float]) -> tuple[float, float, float]:
        x, y, z = vertex
        cy, sy = math.cos(self.rot_y), math.sin(self.rot_y)
        cx, sx = math.cos(self.rot_x), math.sin(self.rot_x)
        xx = x * cy - z * sy
        zz = x * sy + z * cy
        yy = y * cx - zz * sx
        zz = y * sx + zz * cx
        scale = min(self.width(), self.height()) * 0.43 * self.zoom
        return self.width() / 2 + xx * scale, self.height() / 2 - yy * scale, zz

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_mouse = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event) -> None:
        if self._last_mouse is None:
            return
        current = event.position()
        delta = current - self._last_mouse
        self.rot_y += delta.x() * 0.008
        self.rot_x += delta.y() * 0.008
        self._last_mouse = current
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        self._last_mouse = None
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def wheelEvent(self, event) -> None:
        factor = 1.08 if event.angleDelta().y() > 0 else 0.92
        self.zoom = max(0.35, min(2.5, self.zoom * factor))
        self.update()


class StudioWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VIN 3D Studio — Clean Start")
        self.resize(1280, 800)
        self.image: QImage | None = None
        self.image_path: Path | None = None
        self._build_ui()
        self.statusBar().showMessage("Ready · No image loaded")

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #20242c; color: #edf1f8; }
            QLabel#section { color: #bdc7d6; font-size: 12px; font-weight: 700; }
            QLabel#muted { color: #9aa6b7; font-size: 11px; }
            QPushButton { background: #2b313b; border: 1px solid #485363; border-radius: 6px; padding: 8px 10px; }
            QPushButton:hover { border-color: #78e2b2; }
            QPushButton#primary { color: #102019; background: #78e2b2; border-color: #78e2b2; font-weight: 700; }
            QSlider { accent-color: #78e2b2; }
            QFrame#side { background: #20242c; }
            QStatusBar { background: #171a20; color: #a5afbe; }
            """
        )
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(16, 12, 16, 12)
        title = QLabel('<span style="font-weight:800">VIN <span style="color:#78e2b2">3D</span> STUDIO</span>')
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setStyleSheet("font-size:16px")
        header.addWidget(title)
        header.addSpacing(8)
        version = QLabel("CLEAN START · PHASE 1")
        version.setObjectName("muted")
        header.addWidget(version)
        header.addStretch(1)
        header.addWidget(QLabel("Image-to-Mesh prototype"))
        outer.addLayout(header)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(1)
        outer.addLayout(body, 1)

        left = QFrame()
        left.setObjectName("side")
        left.setFixedWidth(250)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(10)
        left_layout.addWidget(self._section("IMAGE INPUT"))
        left_layout.addWidget(QLabel("Load a reference image to build a relief preview."))
        browse = QPushButton("Browse image…")
        browse.setObjectName("primary")
        browse.clicked.connect(self.load_image)
        left_layout.addWidget(browse)
        self.file_label = QLabel("No image selected")
        self.file_label.setObjectName("muted")
        self.file_label.setWordWrap(True)
        left_layout.addWidget(self.file_label)

        left_layout.addSpacing(8)
        left_layout.addWidget(self._section("RELIEF DEPTH"))
        self.depth_value = QLabel("0.35")
        self.depth_slider = QSlider(Qt.Orientation.Horizontal)
        self.depth_slider.setRange(0, 100)
        self.depth_slider.setValue(35)
        self.depth_slider.valueChanged.connect(self._depth_changed)
        depth_row = QHBoxLayout()
        depth_row.addWidget(self.depth_slider, 1)
        depth_row.addWidget(self.depth_value)
        left_layout.addLayout(depth_row)

        left_layout.addWidget(self._section("GRID RESOLUTION"))
        self.res_combo = QComboBox()
        for value in (32, 48, 64, 80, 96, 112, 128):
            self.res_combo.addItem(f"{value} × {value}", value)
        self.res_combo.setCurrentIndex(2)
        left_layout.addWidget(self.res_combo)

        self.build_button = QPushButton("Build mesh preview")
        self.build_button.setObjectName("primary")
        self.build_button.setEnabled(False)
        self.build_button.clicked.connect(self.build_mesh)
        left_layout.addWidget(self.build_button)
        reset = QPushButton("Reset scene")
        reset.clicked.connect(self.reset_scene)
        left_layout.addWidget(reset)

        note = QLabel(
            "This first phase creates a brightness-based 2.5D relief. "
            "It does not yet infer a complete AI-generated model or hidden back side."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        left_layout.addSpacing(10)
        left_layout.addWidget(note)
        left_layout.addStretch(1)
        body.addWidget(left)

        self.viewport = MeshViewport()
        self.viewport.setStyleSheet("background:#282e37;")
        self.viewport.mesh_changed.connect(self.update_stats)
        body.addWidget(self.viewport, 1)

        right = QFrame()
        right.setObjectName("side")
        right.setFixedWidth(220)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(8)
        right_layout.addWidget(self._section("SCENE"))
        self.object_value = self._stat(right_layout, "Active object", "None")
        self.vertices_value = self._stat(right_layout, "Vertices", "0")
        self.triangles_value = self._stat(right_layout, "Triangles", "0")
        self.mode_value = self._stat(right_layout, "Mode", "Empty")
        right_layout.addSpacing(14)
        right_layout.addWidget(self._section("VIEW"))
        front = QPushButton("Front view")
        front.clicked.connect(self.viewport.front_view)
        right_layout.addWidget(front)
        self.wire_button = QPushButton("Wireframe: off")
        self.wire_button.clicked.connect(self.toggle_wireframe)
        right_layout.addWidget(self.wire_button)
        right_layout.addSpacing(14)
        right_layout.addWidget(self._section("NEXT PHASE"))
        export_note = QLabel("GLB export and full AI image-to-3D generation are not included yet.")
        export_note.setObjectName("muted")
        export_note.setWordWrap(True)
        right_layout.addWidget(export_note)
        right_layout.addStretch(1)
        body.addWidget(right)

    @staticmethod
    def _section(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("section")
        return label

    @staticmethod
    def _stat(layout: QVBoxLayout, title: str, value: str) -> QLabel:
        row = QHBoxLayout()
        name = QLabel(title)
        name.setObjectName("muted")
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(name, 1)
        row.addWidget(value_label)
        layout.addLayout(row)
        return value_label

    def load_image(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Choose reference image", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if not filename:
            return
        img = QImage(filename)
        if img.isNull():
            QMessageBox.warning(self, "Image error", "The selected image could not be opened.")
            return
        self.image = img.convertToFormat(QImage.Format.Format_RGB32)
        self.image_path = Path(filename)
        self.file_label.setText(self.image_path.name)
        self.object_value.setText(self.image_path.name)
        self.mode_value.setText("Image loaded")
        self.build_button.setEnabled(True)
        self.statusBar().showMessage("Image loaded · Build a mesh preview")

    def build_mesh(self) -> None:
        if self.image is None:
            return
        n = int(self.res_combo.currentData())
        # Sample to a square canvas while preserving the image aspect ratio.
        sample = QImage(n, n, QImage.Format.Format_RGB32)
        sample.fill(QColor(119, 119, 119))
        scaled = self.image.scaled(
            n, n, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        from PySide6.QtGui import QPainter as ImagePainter

        ip = ImagePainter(sample)
        ip.drawImage((n - scaled.width()) // 2, (n - scaled.height()) // 2, scaled)
        ip.end()

        depth = self.depth_slider.value() / 100.0
        vertices: list[tuple[float, float, float]] = []
        colors: list[tuple[int, int, int]] = []
        for y in range(n):
            for x in range(n):
                color = sample.pixelColor(x, y)
                luminance = (
                    0.2126 * color.red() + 0.7152 * color.green() + 0.0722 * color.blue()
                ) / 255.0
                vertices.append(
                    ((x / (n - 1) - 0.5) * 2.0, (0.5 - y / (n - 1)) * 2.0,
                     (luminance - 0.5) * depth)
                )
                colors.append((color.red(), color.green(), color.blue()))

        triangles: list[tuple[int, int, int]] = []
        for y in range(n - 1):
            for x in range(n - 1):
                a = y * n + x
                b = a + 1
                c = a + n
                d = c + 1
                triangles.append((a, c, b))
                triangles.append((b, c, d))

        mesh = ReliefMesh(n, vertices, colors, triangles)
        self.viewport.set_mesh(mesh)
        self.mode_value.setText("Relief preview")
        self.statusBar().showMessage(
            f"Preview generated · {len(vertices):,} vertices · {len(triangles):,} triangles"
        )

    def _depth_changed(self, value: int) -> None:
        self.depth_value.setText(f"{value / 100.0:.2f}")
        # Rebuild only when a mesh already exists; the user controls when this happens.
        if self.viewport.mesh is not None:
            self.build_mesh()

    def update_stats(self, mesh: ReliefMesh | None) -> None:
        if mesh is None:
            self.vertices_value.setText("0")
            self.triangles_value.setText("0")
        else:
            self.vertices_value.setText(f"{len(mesh.vertices):,}")
            self.triangles_value.setText(f"{len(mesh.triangles):,}")

    def toggle_wireframe(self) -> None:
        self.viewport.wireframe = not self.viewport.wireframe
        self.wire_button.setText(f"Wireframe: {'on' if self.viewport.wireframe else 'off'}")
        self.viewport.update()

    def reset_scene(self) -> None:
        self.image = None
        self.image_path = None
        self.file_label.setText("No image selected")
        self.build_button.setEnabled(False)
        self.object_value.setText("None")
        self.mode_value.setText("Empty")
        self.viewport.set_mesh(None)
        self.viewport.reset_view()
        self.statusBar().showMessage("Scene reset · No image loaded")


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("VIN 3D Studio")
    window = StudioWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
