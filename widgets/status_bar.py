"""
Footer status bar — compact inline indicators with green dots.
Matches reference: MANIPULATOR · LINKED, PACS · DICOM TLS, LOOP 500 Hz, VISION · 30 FPS, LATENCY.
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor


class _StatusDot(QWidget):
    """Painted status dot."""
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(10, 10)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(self._color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(1, 1, 8, 8)
        p.end()


def _chip(dot_color, text):
    box = QHBoxLayout()
    box.setSpacing(6)
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
        self.setFixedHeight(32)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(28)

        items = [
            ("#10B981", "MANIPULATOR  \u00B7  LINKED"),
            ("#10B981", "PACS  \u00B7  DICOM TLS"),
            ("#10B981", "LOOP 500 Hz  \u00B7  0.84 ms"),
            ("#10B981", "VISION  \u00B7  30 FPS"),
            (None, "LATENCY 0.84 ms"),
        ]
        for color, text in items:
            layout.addLayout(_chip(color, text))

        layout.addStretch()

        right_items = [
            "NODE OR-03-A",
            "BUILD 4.2.118  \u00B7  STABLE",
            "OPERATOR: voss.a",
        ]
        for text in right_items:
            lbl = QLabel(text)
            lbl.setObjectName("StatusBarText")
            layout.addWidget(lbl)
