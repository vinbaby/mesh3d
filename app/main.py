from __future__ import annotations

import json
import math
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
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
    """2D reference-image viewport with manually drawn frame strokes."""

    frame_changed = Signal(int, int)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(360, 320)
        self.setMouseTracking(True)
        self.reference_image: QImage | None = None
        # Stroke points are normalized to the image rectangle (0..1), so the
        # overlay remains attached to the reference if the viewport is resized.
        self.frame_strokes: list[list[QPointF]] = []
        self._active_stroke: list[QPointF] | None = None
        self.draw_mode = False
        self.line_width = 2.0
        self.image_zoom = 1.0
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_reference_image(self, image: QImage | None) -> None:
        self.reference_image = image
        self.frame_strokes.clear()
        self._active_stroke = None
        self.image_zoom = 1.0
        self.frame_changed.emit(0, 0)
        self.update()

    def set_draw_mode(self, enabled: bool) -> None:
        self.draw_mode = enabled
        self.setCursor(Qt.CursorShape.CrossCursor if enabled else Qt.CursorShape.ArrowCursor)
        self.update()

    def undo_stroke(self) -> None:
        if self._active_stroke is not None:
            self._active_stroke = None
        elif self.frame_strokes:
            self.frame_strokes.pop()
        self._emit_frame_changed()
        self.update()

    def clear_frame(self) -> None:
        self.frame_strokes.clear()
        self._active_stroke = None
        self._emit_frame_changed()
        self.update()

    def fit_image(self) -> None:
        self.image_zoom = 1.0
        self.update()

    def _fit_rect(self) -> QRectF:
        if self.reference_image is None or self.reference_image.isNull():
            return QRectF()
        iw, ih = self.reference_image.width(), self.reference_image.height()
        scale = min(self.width() / max(1, iw), self.height() / max(1, ih)) * self.image_zoom
        width, height = iw * scale, ih * scale
        return QRectF((self.width() - width) / 2, (self.height() - height) / 2, width, height)

    def _normalized_point(self, pos: QPointF) -> QPointF | None:
        rect = self._fit_rect()
        if rect.isNull() or rect.width() <= 0 or rect.height() <= 0 or not rect.contains(pos):
            return None
        return QPointF(
            max(0.0, min(1.0, (pos.x() - rect.left()) / rect.width())),
            max(0.0, min(1.0, (pos.y() - rect.top()) / rect.height())),
        )

    def _to_view(self, point: QPointF) -> QPointF:
        rect = self._fit_rect()
        return QPointF(rect.left() + point.x() * rect.width(),
                       rect.top() + point.y() * rect.height())

    def _emit_frame_changed(self) -> None:
        strokes = list(self.frame_strokes)
        if self._active_stroke:
            strokes.append(self._active_stroke)
        self.frame_changed.emit(len(strokes), sum(len(stroke) for stroke in strokes))

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#282e37"))
        if self.reference_image is None or self.reference_image.isNull():
            painter.setPen(QColor("#b7c1d0"))
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter,
                "VIN 3D STUDIO\n\nImport a reference image, then draw frame lines over it",
            )
            painter.end()
            return

        image_rect = self._fit_rect()
        painter.drawImage(image_rect, self.reference_image)
        painter.setPen(QPen(QColor(8, 12, 18, 180), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(image_rect)

        all_strokes = list(self.frame_strokes)
        if self._active_stroke:
            all_strokes.append(self._active_stroke)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for stroke in all_strokes:
            view_points = [self._to_view(point) for point in stroke]
            if len(view_points) >= 2:
                painter.setPen(QPen(QColor("#72efb5"), self.line_width,
                                    Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                                    Qt.PenJoinStyle.RoundJoin))
                painter.drawPolyline(QPolygonF(view_points))
            if view_points:
                painter.setPen(QPen(QColor("#10251c"), 1))
                painter.setBrush(QColor("#a5ffd5"))
                stride = max(1, len(view_points) // 35)
                for point in view_points[::stride]:
                    painter.drawEllipse(point, 2.3, 2.3)
                painter.setBrush(Qt.BrushStyle.NoBrush)

        if self.draw_mode:
            painter.fillRect(QRectF(12, 12, 180, 27), QColor(20, 29, 35, 215))
            painter.setPen(QColor("#a5ffd5"))
            painter.drawText(QRectF(21, 12, 170, 27),
                             Qt.AlignmentFlag.AlignVCenter, "FRAME DRAW MODE · DRAG")
        painter.end()

    def mousePressEvent(self, event) -> None:
        if (event.button() == Qt.MouseButton.LeftButton
                and self.draw_mode and self.reference_image is not None):
            point = self._normalized_point(event.position())
            if point is not None:
                self._active_stroke = [point]
                self._emit_frame_changed()
                self.update()
                event.accept()
                return
        event.ignore()

    def mouseMoveEvent(self, event) -> None:
        if self._active_stroke is None:
            return
        point = self._normalized_point(event.position())
        if point is None:
            return
        last = self._active_stroke[-1]
        rect = self._fit_rect()
        dx = (point.x() - last.x()) * rect.width()
        dy = (point.y() - last.y()) * rect.height()
        # Sampling every few screen pixels avoids millions of points on long drags.
        if dx * dx + dy * dy >= 9.0:
            self._active_stroke.append(point)
            self._emit_frame_changed()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._active_stroke is not None:
            if self._active_stroke:
                self.frame_strokes.append(self._active_stroke)
            self._active_stroke = None
            self._emit_frame_changed()
            self.update()
            event.accept()
            return
        event.ignore()

    def wheelEvent(self, event) -> None:
        if self.reference_image is None:
            return
        factor = 1.12 if event.angleDelta().y() > 0 else 0.89
        self.image_zoom = max(1.0, min(4.0, self.image_zoom * factor))
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
            QPushButton:checked { color: #102019; background: #78e2b2; border-color: #78e2b2; font-weight: 700; }
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
        version = QLabel("REFERENCE FRAME · v0.1.2")
        version.setObjectName("muted")
        header.addWidget(version)
        header.addStretch(1)
        header.addWidget(QLabel("Draw wireframe over image"))
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
        left_layout.addWidget(self._section("REFERENCE IMAGE"))
        left_layout.addWidget(QLabel("Import a picture, then trace frame lines directly on top."))
        browse = QPushButton("Import image…")
        browse.setObjectName("primary")
        browse.clicked.connect(self.load_image)
        left_layout.addWidget(browse)
        self.file_label = QLabel("No image selected")
        self.file_label.setObjectName("muted")
        self.file_label.setWordWrap(True)
        left_layout.addWidget(self.file_label)

        left_layout.addSpacing(10)
        left_layout.addWidget(self._section("FRAME DRAWING"))
        self.draw_button = QPushButton("Draw frame: OFF")
        self.draw_button.setCheckable(True)
        self.draw_button.setEnabled(False)
        self.draw_button.toggled.connect(self._draw_mode_toggled)
        left_layout.addWidget(self.draw_button)

        self.undo_button = QPushButton("Undo last stroke")
        self.undo_button.setEnabled(False)
        self.undo_button.clicked.connect(self.undo_stroke)
        left_layout.addWidget(self.undo_button)

        self.clear_button = QPushButton("Clear frame")
        self.clear_button.setEnabled(False)
        self.clear_button.clicked.connect(self.clear_frame)
        left_layout.addWidget(self.clear_button)

        left_layout.addWidget(self._section("LINE WIDTH"))
        width_row = QHBoxLayout()
        self.line_slider = QSlider(Qt.Orientation.Horizontal)
        self.line_slider.setRange(1, 6)
        self.line_slider.setValue(2)
        self.line_value = QLabel("2 px")
        self.line_slider.valueChanged.connect(self._line_width_changed)
        width_row.addWidget(self.line_slider, 1)
        width_row.addWidget(self.line_value)
        left_layout.addLayout(width_row)

        self.save_button = QPushButton("Save frame data…")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_frame)
        left_layout.addWidget(self.save_button)
        fit_button = QPushButton("Fit image")
        left_layout.addWidget(fit_button)

        note = QLabel(
            "Turn on Draw frame, then left-click and drag to draw strokes over the reference. "
            "Mouse wheel zooms the image. This tool records 2D guide strokes; it does not "
            "generate a 3D model automatically."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        left_layout.addSpacing(8)
        left_layout.addWidget(note)
        left_layout.addStretch(1)
        body.addWidget(left)

        self.viewport = MeshViewport()
        fit_button.clicked.connect(self.viewport.fit_image)
        self.viewport.setStyleSheet("background:#282e37;")
        self.viewport.frame_changed.connect(self.update_frame_stats)
        body.addWidget(self.viewport, 1)

        right = QFrame()
        right.setObjectName("side")
        right.setFixedWidth(220)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(8)
        right_layout.addWidget(self._section("REFERENCE"))
        self.object_value = self._stat(right_layout, "Active image", "None")
        self.strokes_value = self._stat(right_layout, "Strokes", "0")
        self.points_value = self._stat(right_layout, "Frame points", "0")
        self.mode_value = self._stat(right_layout, "Mode", "Image view")
        right_layout.addSpacing(14)
        right_layout.addWidget(self._section("WORKFLOW"))
        right_layout.addWidget(QLabel("1. Import image\n2. Enable Draw frame\n3. Trace contours / edges\n4. Undo or clear as needed\n5. Save frame JSON"))
        right_layout.addSpacing(14)
        right_layout.addWidget(self._section("NEXT STEP"))
        export_note = QLabel("Next: turn the drawn guides into editable vertices and edges for a real mesh workflow.")
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
        self.image = img.convertToFormat(QImage.Format.Format_ARGB32)
        self.image_path = Path(filename)
        self.file_label.setText(self.image_path.name)
        self.object_value.setText(self.image_path.name)
        self.viewport.set_reference_image(self.image)
        self.draw_button.setEnabled(True)
        self.draw_button.setChecked(False)
        # Undo, clear and save stay disabled until at least one stroke exists.
        self.undo_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.mode_value.setText("Image view")
        self.statusBar().showMessage("Image loaded · Enable Draw frame to trace lines")

    def _draw_mode_toggled(self, enabled: bool) -> None:
        self.viewport.set_draw_mode(enabled)
        self.draw_button.setText(f"Draw frame: {'ON' if enabled else 'OFF'}")
        self.mode_value.setText("Drawing frame" if enabled else "Image view")
        self.statusBar().showMessage(
            "Draw mode on · left-drag on the image to add frame strokes"
            if enabled else "Draw mode off · image navigation"
        )

    def _line_width_changed(self, value: int) -> None:
        self.line_value.setText(f"{value} px")
        self.viewport.line_width = float(value)
        self.viewport.update()

    def update_frame_stats(self, stroke_count: int, point_count: int) -> None:
        self.strokes_value.setText(str(stroke_count))
        self.points_value.setText(f"{point_count:,}")
        self.undo_button.setEnabled(self.image is not None and stroke_count > 0)
        self.clear_button.setEnabled(self.image is not None and stroke_count > 0)
        self.save_button.setEnabled(self.image is not None and stroke_count > 0)

    def undo_stroke(self) -> None:
        self.viewport.undo_stroke()
        self.statusBar().showMessage("Last stroke undone")

    def clear_frame(self) -> None:
        if not self.viewport.frame_strokes and self.viewport._active_stroke is None:
            return
        answer = QMessageBox.question(
            self, "Clear frame", "Remove all frame strokes from this image?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.viewport.clear_frame()
        self.statusBar().showMessage("Frame cleared")

    def save_frame(self) -> None:
        strokes = self.viewport.frame_strokes
        if not strokes:
            QMessageBox.information(self, "No frame", "Draw at least one stroke before saving.")
            return
        default_name = (
            f"{self.image_path.stem}_frame.json" if self.image_path
            else "reference_frame.json"
        )
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save frame data", default_name, "Frame data (*.json)"
        )
        if not filename:
            return
        data = {
            "format": "vin-3d-studio-reference-frame",
            "version": 1,
            "source_image": self.image_path.name if self.image_path else None,
            "image_size": [self.image.width(), self.image.height()] if self.image else None,
            "coordinate_space": "normalized_image_0_to_1",
            "line_width_px": self.viewport.line_width,
            "strokes": [
                [{"u": round(point.x(), 6), "v": round(point.y(), 6)} for point in stroke]
                for stroke in strokes
            ],
        }
        try:
            Path(filename).write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self, "Save failed", f"Could not save frame data:\n{exc}")
            return
        self.statusBar().showMessage(f"Frame data saved · {Path(filename).name}")

    def reset_scene(self) -> None:
        self.image = None
        self.image_path = None
        self.file_label.setText("No image selected")
        self.draw_button.setChecked(False)
        self.draw_button.setEnabled(False)
        self.undo_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.object_value.setText("None")
        self.mode_value.setText("Image view")
        self.viewport.set_reference_image(None)
        self.statusBar().showMessage("Scene reset · No image loaded")


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("VIN 3D Studio")
    window = StudioWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
