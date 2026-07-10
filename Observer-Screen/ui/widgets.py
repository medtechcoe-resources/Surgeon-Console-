# ═══════════════════════════════════════════════════════════════════
#  OBSERVER SCREEN — REUSABLE WIDGETS
# ═══════════════════════════════════════════════════════════════════

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPainterPath
from PyQt6.QtWidgets import (
    QFrame, QLabel, QHBoxLayout, QVBoxLayout, QWidget,
)

from config import C


class CardFrame(QFrame):
    """A card container matching the Observer theme."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        # Ensure styling is applied by QSS
        self.setStyleSheet(f"""
            CardFrame {{
                background-color: {C['bg1']};
                border: 1px solid {C['border']};
                border-radius: 8px;
            }}
        """)


class SectionHeader(QWidget):
    """Accent header block for panels."""

    def __init__(self, text: str, color: str = None, parent=None):
        super().__init__(parent)
        color = color or C["cyan"]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(0)

        bar = QFrame()
        bar.setFixedWidth(3)
        bar.setStyleSheet(f"background-color: {color};")
        layout.addWidget(bar)

        lbl = QLabel(f"  {text.upper()}")
        lbl.setFont(QFont("JetBrains Mono", 11, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {color};")
        layout.addWidget(lbl)

        layout.addStretch()


class StatusBadge(QLabel):
    """Colored text badge."""

    def __init__(self, text: str, color: str, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_color(color)

    def set_color(self, color: str):
        self.setStyleSheet(f"""
            padding: 3px 6px;
            background-color: {color};
            color: #ffffff;
            border-radius: 4px;
        """)

    def set_text_and_color(self, text: str, color: str):
        self.setText(text)
        self.set_color(color)


class StatusIndicator(QWidget):
    """Status dot."""

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


class MetricCard(CardFrame):
    """Simple Metric Card (label, value, unit)."""

    def __init__(self, label: str, value: str, unit: str = "",
                 color: str = None, parent=None):
        super().__init__(parent)
        color = color or C["cyan"]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        lbl = QLabel(label.upper())
        lbl.setFont(QFont("JetBrains Mono", 8, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {C['txt2']}; border: none;")
        layout.addWidget(lbl)

        val_row = QHBoxLayout()
        self._value_label = QLabel(value)
        self._value_label.setFont(QFont("JetBrains Mono", 18, QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {color}; border: none;")
        val_row.addWidget(self._value_label)

        if unit:
            unit_lbl = QLabel(unit)
            unit_lbl.setFont(QFont("JetBrains Mono", 9))
            unit_lbl.setStyleSheet(f"color: {C['txt2']}; border: none; padding-top: 6px;")
            val_row.addWidget(unit_lbl)
        val_row.addStretch()
        layout.addLayout(val_row)

    def set_value(self, value: str):
        self._value_label.setText(value)

    def set_color(self, color: str):
        self._value_label.setStyleSheet(f"color: {color}; border: none;")


class KeyValueRow(QWidget):
    """A row of key-value text."""

    def __init__(self, key: str, value: str = "---",
                 value_color: str = None, parent=None):
        super().__init__(parent)
        value_color = value_color or C["txt0"]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)

        key_lbl = QLabel(key)
        key_lbl.setFont(QFont("JetBrains Mono", 9))
        key_lbl.setStyleSheet(f"color: {C['txt2']};")
        layout.addWidget(key_lbl)

        layout.addStretch()

        self._value_label = QLabel(value)
        self._value_label.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {value_color};")
        layout.addWidget(self._value_label)

    def set_value(self, value: str, color: str = None):
        self._value_label.setText(value)
        if color:
            self._value_label.setStyleSheet(f"color: {color};")
