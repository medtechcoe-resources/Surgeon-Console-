# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — REUSABLE WIDGETS
#  Qt equivalents of the Surgeon Console's tkinter widget helpers:
#  CardFrame, SectionHeader, StatusBadge, SparklineWidget, etc.
# ═══════════════════════════════════════════════════════════════════

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPainterPath
from PyQt6.QtWidgets import (
    QFrame, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QSizePolicy,
)

from constants import C


# ═══════════════════════════════════════════════════════════════════
#  CARD FRAME — White bordered card (matches tkinter `card()`)
# ═══════════════════════════════════════════════════════════════════

class CardFrame(QFrame):
    """A white card with a 1px border, matching the Surgeon Console style."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            CardFrame {{
                background-color: {C['bg2']};
                border: 1px solid {C['border']};
            }}
        """)


# ═══════════════════════════════════════════════════════════════════
#  SECTION HEADER — Colored bar + bold label (matches `sec_header()`)
# ═══════════════════════════════════════════════════════════════════

class SectionHeader(QWidget):
    """A section header with a colored left accent bar and bold label."""

    def __init__(self, text: str, color: str = None, parent=None):
        super().__init__(parent)
        color = color or C["cyan"]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 4)
        layout.setSpacing(0)

        self.setStyleSheet(f"background-color: {C['bg0']};")

        # Colored accent bar
        bar = QFrame()
        bar.setFixedWidth(3)
        bar.setStyleSheet(f"background-color: {color};")
        layout.addWidget(bar)

        # Label
        lbl = QLabel(f"  {text}")
        lbl.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {color}; background-color: {C['bg0']};")
        layout.addWidget(lbl)

        layout.addStretch()


# ═══════════════════════════════════════════════════════════════════
#  STATUS BADGE — Colored background + white text
# ═══════════════════════════════════════════════════════════════════

class StatusBadge(QLabel):
    """A colored badge label with white text, matching `status_badge()`."""

    def __init__(self, text: str, color: str, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_color(color)

    def set_color(self, color: str):
        self.setStyleSheet(f"""
            padding: 4px 8px;
            background-color: {color};
            color: white;
        """)

    def set_text_and_color(self, text: str, color: str):
        self.setText(text)
        self.set_color(color)


# ═══════════════════════════════════════════════════════════════════
#  STATUS INDICATOR — Small colored dot
# ═══════════════════════════════════════════════════════════════════

class StatusIndicator(QWidget):
    """A small colored dot indicator (green / amber / red)."""

    def __init__(self, color: str = None, size: int = 10, parent=None):
        super().__init__(parent)
        self._color = QColor(color or C["green"])
        self._size = size
        self.setFixedSize(size, size)

    def set_color(self, color: str):
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self._color)
        painter.setPen(Qt.PenStyle.NoPen)
        margin = 1
        painter.drawEllipse(margin, margin,
                            self._size - 2 * margin,
                            self._size - 2 * margin)
        painter.end()


# ═══════════════════════════════════════════════════════════════════
#  SPARKLINE WIDGET — Mini scrolling line chart (matches `Sparkline`)
# ═══════════════════════════════════════════════════════════════════

class SparklineWidget(QWidget):
    """A mini scrolling line chart for real-time data visualisation."""

    def __init__(self, color: str, width: int = 120, height: int = 30,
                 parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._data: list[float] = []
        self.setFixedHeight(height)
        self.setMinimumWidth(width)
        self.setStyleSheet(f"background-color: {C['bg3']};")

    def update_data(self, data: list):
        """Replace sparkline data with the latest values."""
        self._data = list(data[-50:])
        self.update()

    def paintEvent(self, event):
        if not self._data or len(self._data) < 2:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        mn = min(self._data)
        mx = max(self._data)
        rng = mx - mn or 1

        pen = QPen(self._color, 2)
        painter.setPen(pen)

        path = QPainterPath()
        for i, v in enumerate(self._data):
            x = i / max(len(self._data) - 1, 1) * w
            y = h - (v - mn) / rng * (h - 4) - 2
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        painter.drawPath(path)
        painter.end()


# ═══════════════════════════════════════════════════════════════════
#  METRIC CARD — Label + large value + unit (for dashboards)
# ═══════════════════════════════════════════════════════════════════

class MetricCard(CardFrame):
    """A card displaying a labelled metric with large value and unit."""

    def __init__(self, label: str, value: str, unit: str = "",
                 color: str = None, parent=None):
        super().__init__(parent)
        color = color or C["cyan"]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        # Label
        lbl = QLabel(label)
        lbl.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {C['txt1']}; border: none;")
        layout.addWidget(lbl)

        # Value
        self._value_label = QLabel(value)
        self._value_label.setFont(QFont("Consolas", 22, QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {color}; border: none;")
        layout.addWidget(self._value_label)

        # Unit
        if unit:
            unit_lbl = QLabel(unit)
            unit_lbl.setFont(QFont("Consolas", 8))
            unit_lbl.setStyleSheet(f"color: {C['txt2']}; border: none;")
            layout.addWidget(unit_lbl)

        self._color = color

    def set_value(self, value: str):
        self._value_label.setText(value)

    def set_color(self, color: str):
        self._color = color
        self._value_label.setStyleSheet(f"color: {color}; border: none;")


# ═══════════════════════════════════════════════════════════════════
#  VITAL CARD — Large monitor-style vital sign card
# ═══════════════════════════════════════════════════════════════════

class VitalCard(CardFrame):
    """An ICU-style vital sign monitor card with label, value, unit,
    status indicator, and optional sparkline."""

    def __init__(self, label: str, unit: str, color: str,
                 show_sparkline: bool = False, parent=None):
        super().__init__(parent)
        self._color = color

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        # Label
        lbl = QLabel(label)
        lbl.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {C['txt1']}; border: none;")
        layout.addWidget(lbl)

        # Value
        self._value_label = QLabel("---")
        self._value_label.setFont(QFont("Consolas", 32, QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {color}; border: none;")
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._value_label)

        # Unit
        unit_lbl = QLabel(unit)
        unit_lbl.setFont(QFont("Consolas", 9))
        unit_lbl.setStyleSheet(f"color: {C['txt2']}; border: none;")
        unit_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(unit_lbl)

        # Status
        self._status_label = QLabel("")
        self._status_label.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        self._status_label.setStyleSheet(
            f"color: {C['green']}; border: none;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)

        # Optional sparkline
        self._sparkline = None
        if show_sparkline:
            self._sparkline = SparklineWidget(color=color, width=200,
                                              height=36)
            layout.addWidget(self._sparkline)

    def set_value(self, value: str):
        self._value_label.setText(value)

    def set_status(self, text: str, color: str = None):
        self._status_label.setText(text)
        if color:
            self._status_label.setStyleSheet(
                f"color: {color}; border: none;")

    def update_sparkline(self, data: list):
        if self._sparkline:
            self._sparkline.update_data(data)


# ═══════════════════════════════════════════════════════════════════
#  KEY-VALUE ROW — Simple label : value pair
# ═══════════════════════════════════════════════════════════════════

class KeyValueRow(QWidget):
    """A horizontal label-value pair row for cards and sidebars."""

    def __init__(self, key: str, value: str = "---",
                 value_color: str = None, parent=None):
        super().__init__(parent)
        value_color = value_color or C["txt0"]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 3, 10, 3)
        layout.setSpacing(4)

        self.setStyleSheet(f"background-color: {C['bg2']};")

        key_lbl = QLabel(key)
        key_lbl.setFont(QFont("Consolas", 8))
        key_lbl.setStyleSheet(f"color: {C['txt2']};")
        layout.addWidget(key_lbl)

        layout.addStretch()

        self._value_label = QLabel(value)
        self._value_label.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {value_color};")
        layout.addWidget(self._value_label)

    def set_value(self, value: str, color: str = None):
        self._value_label.setText(value)
        if color:
            self._value_label.setStyleSheet(f"color: {color};")
