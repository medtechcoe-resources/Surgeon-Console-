"""
Reusable metric Card widget used across all screens.
A Card displays: small label, large value (+ optional unit), small sub-text.
Optional left accent border colour to denote status (green/amber/red/cyan).
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt


def _lock_vertical(widget):
    sp = widget.sizePolicy()
    sp.setVerticalPolicy(QSizePolicy.Policy.Fixed)
    widget.setSizePolicy(sp)


class MetricCard(QFrame):
    def __init__(self, label, value, unit="", sub="", accent=None, value_color=None, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        if accent:
            self.setProperty("accent", accent)
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        lbl = QLabel(label.upper())
        lbl.setObjectName("CardLabel")
        layout.addWidget(lbl)

        value_row = QHBoxLayout()
        value_row.setSpacing(6)
        val = QLabel(str(value))
        val.setObjectName("CardValue")
        if value_color:
            val.setStyleSheet(f"color: {value_color}; font-size: 28px; font-weight: 700; font-family: 'JetBrains Mono', 'Consolas', monospace;")
        value_row.addWidget(val)
        if unit:
            u = QLabel(unit)
            u.setObjectName("CardSub")
            u.setStyleSheet("color:#6B7B8D; font-size:14px; padding-top:8px;")
            value_row.addWidget(u)
        value_row.addStretch()
        layout.addLayout(value_row)

        if sub:
            sub_lbl = QLabel(sub)
            sub_lbl.setObjectName("CardSub")
            layout.addWidget(sub_lbl)

        layout.addStretch()
        self.value_label = val

    def set_value(self, value):
        self.value_label.setText(str(value))


class PanelFrame(QFrame):
    """A container card with a title header bar, used for grouping
    larger blocks of content (e.g. 'MANIPULATOR TELEMETRY', 'PIPELINE CONTROLS')."""

    def __init__(self, title, right_widget=None, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setObjectName("SectionHeaderBar")
        _lock_vertical(header)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 14, 20, 14)
        title_lbl = QLabel(title.upper())
        title_lbl.setObjectName("SectionTitle")
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        if right_widget:
            h_layout.addWidget(right_widget)
        outer.addWidget(header)

        self.body = QFrame()
        self.body.setObjectName("PanelBody")
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(20, 18, 20, 18)
        self.body_layout.setSpacing(12)
        outer.addWidget(self.body)

    def add_widget(self, w):
        self.body_layout.addWidget(w)

    def add_layout(self, lay):
        self.body_layout.addLayout(lay)

    def add_stretch(self):
        self.body_layout.addStretch()
