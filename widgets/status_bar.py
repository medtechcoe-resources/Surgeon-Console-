from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor


class _StatusDot(QWidget):
    """Painted status dot."""
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(12, 12)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(self._color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(1, 1, 10, 10)
        p.end()


def _chip(dot_color, text):
    box = QHBoxLayout()
    box.setSpacing(8)
    if dot_color:
        dot = _StatusDot(dot_color)
        box.addWidget(dot)
    lbl = QLabel(text)
    lbl.setObjectName("StatusBarText")
    box.addWidget(lbl)
    return box


class StatusBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatusBar")
        self.setFixedHeight(38)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(32)

        items = [
            ("#20C997", "MANIPULATOR  ·  LINKED"),
            ("#20C997", "PACS  ·  DICOM TLS"),
            ("#20C997", "LOOP 500 Hz  ·  0.84 ms"),
            (None, "VISION  ·  28 FPS"),
        ]
        for color, text in items:
            layout.addLayout(_chip(color, text))

        layout.addStretch()

        right_items = [
            "NODE OR-03-A",
            "BUILD 4.2.118  ·  STABLE",
            "OPERATOR: voss.a",
        ]
        for text in right_items:
            lbl = QLabel(text)
            lbl.setObjectName("StatusBarText")
            layout.addWidget(lbl)
