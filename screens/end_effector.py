"""
End-Effector Camera tab — Tool tip view, coordinates, tool status.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, QProgressBar, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QPen
from widgets.card import MetricCard, PanelFrame


class _ToolTipCanvas(QFrame):
    """Stylised end-effector (Maryland dissector jaws) rendered over a warm tissue glow."""

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        # Glow background
        grad = QRadialGradient(w / 2, h * 0.42, max(w, h) * 0.55)
        grad.setColorAt(0.0, QColor(70, 20, 20))
        grad.setColorAt(0.75, QColor(28, 9, 9))
        grad.setColorAt(1.0, QColor(13, 17, 23)) # Match new theme bg slightly
        p.fillRect(self.rect(), grad)

        cx = w / 2
        shaft_top = 0
        shaft_bottom = h * 0.55
        p.setPen(QPen(QColor("#2D3748"), 10, cap=Qt.PenCapStyle.RoundCap))
        p.drawLine(int(cx), int(shaft_top), int(cx), int(shaft_bottom))

        # Jaws (two angled lines forming a V opening downward)
        jaw_len = 70
        p.setPen(QPen(QColor("#4A5568"), 9, cap=Qt.PenCapStyle.RoundCap))
        p.drawLine(int(cx), int(shaft_bottom), int(cx - 26), int(shaft_bottom + jaw_len))
        p.drawLine(int(cx), int(shaft_bottom), int(cx + 26), int(shaft_bottom + jaw_len))


class _StatusDot(QWidget):
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


class CoordBox(QFrame):
    def __init__(self, label, value):
        super().__init__()
        self.setObjectName("Card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)
        l = QLabel(label)
        l.setObjectName("CardLabel")
        v = QLabel(value)
        v.setStyleSheet("color:#F5F7FA; font-size:24px; font-weight:700; font-family:'JetBrains Mono','Consolas',monospace;")
        lay.addWidget(l)
        lay.addWidget(v)


class EndEffectorScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 14, 0, 0)
        outer.setSpacing(16)

        center = QVBoxLayout()
        center.setSpacing(14)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        cards_row.addWidget(MetricCard("Active Tool", "MARYLAND", sub="Bipolar  ·  30W"))
        cards_row.addWidget(MetricCard("Grip Force", "3.54", "N", accent="cyan"))
        cards_row.addWidget(MetricCard("Tool Angle", "42.34", "\u00B0"))
        cards_row.addWidget(MetricCard("Insertion Depth", "84.2", "mm", accent="cyan"))
        cards_row.addWidget(MetricCard("Tip Temperature", "38.1", "\u00B0C", accent="green", value_color="#20C997"))
        cards_row.addWidget(MetricCard("Actuations", "148", sub="of 600 rated"))
        center.addLayout(cards_row)

        feed = QFrame()
        feed.setObjectName("Card")
        feed.setMinimumHeight(460)
        feed_layout = QVBoxLayout(feed)
        feed_layout.setContentsMargins(0, 0, 0, 0)
        feed_layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(20, 14, 20, 10)
        title = QLabel("END-EFFECTOR CAMERA  ·  TOOL TIP VIEW")
        title.setObjectName("SectionTitle")
        
        rec_dot = _StatusDot("#E5484D")
        rec = QLabel("REC")
        rec.setStyleSheet("color:#E5484D; font-size:12px; font-weight:700;")
        meta = QLabel("2560x1440  ·  60FPS")
        meta.setStyleSheet("color:#6B7B8D; font-size:12px;")
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(rec_dot)
        header.addSpacing(6)
        header.addWidget(rec)
        header.addSpacing(12)
        header.addWidget(meta)
        feed_layout.addLayout(header)

        canvas = _ToolTipCanvas()
        canvas.setMinimumHeight(390)
        c_layout = QVBoxLayout(canvas)
        c_layout.setContentsMargins(20, 16, 20, 16)

        overlay_row = QHBoxLayout()
        
        # Pose Box
        pose_box = QFrame()
        pose_box.setStyleSheet("background-color: rgba(13, 17, 23, 200); border:1px solid #2D3748; border-radius:10px;")
        pose_box.setFixedWidth(190)
        pl = QVBoxLayout(pose_box)
        pl.setContentsMargins(18, 14, 18, 14)
        pl.setSpacing(8)
        pt = QLabel("POSE")
        pt.setStyleSheet("color:#6B7B8D; font-size:12px; font-weight:700; letter-spacing:1px;")
        pl.addWidget(pt)
        for lab, val in [("X", "128.42"), ("Y", "-22.18"), ("Z", "318.04")]:
            row = QHBoxLayout()
            l = QLabel(lab)
            l.setStyleSheet("color:#B5BEC8; font-size:13px;")
            r = QLabel(val)
            r.setStyleSheet("color:#F5F7FA; font-size:15px; font-weight:700; font-family:'JetBrains Mono','Consolas',monospace;")
            row.addWidget(l)
            row.addStretch()
            row.addWidget(r)
            pl.addLayout(row)
        overlay_row.addWidget(pose_box, alignment=Qt.AlignmentFlag.AlignTop)
        overlay_row.addStretch()

        # Tool Box
        tool_box = QFrame()
        tool_box.setStyleSheet("background-color: rgba(13, 17, 23, 200); border:1px solid #0095FF; border-radius:10px;")
        tool_box.setFixedWidth(190)
        tl = QVBoxLayout(tool_box)
        tl.setContentsMargins(18, 14, 18, 14)
        tl.setSpacing(8)
        tt = QLabel("TOOL")
        tt.setStyleSheet("color:#0095FF; font-size:12px; font-weight:700; letter-spacing:1px;")
        tl.addWidget(tt)
        for lab, val in [("Grip", "3.54 N"), ("Angle", "42.34\u00B0"), ("Temp", "38.1\u00B0C")]:
            row = QHBoxLayout()
            l = QLabel(lab)
            l.setStyleSheet("color:#B5BEC8; font-size:13px;")
            r = QLabel(val)
            r.setStyleSheet("color:#F5F7FA; font-size:15px; font-weight:700;")
            row.addWidget(l)
            row.addStretch()
            row.addWidget(r)
            tl.addLayout(row)
        overlay_row.addWidget(tool_box, alignment=Qt.AlignmentFlag.AlignTop)
        c_layout.addLayout(overlay_row)
        c_layout.addStretch()

        feed_layout.addWidget(canvas, 1)

        bottom = QHBoxLayout()
        bottom.setContentsMargins(20, 10, 20, 14)
        for text in ["FRAME 0214887", "T+ 00:42:18  ·  FPS 60", "ZOOM 2.1x"]:
            l = QLabel(text)
            l.setStyleSheet("color:#6B7B8D; font-size:12px; font-family:'JetBrains Mono','Consolas',monospace;")
            bottom.addWidget(l)
            bottom.addStretch()
        feed_layout.addLayout(bottom)

        center.addWidget(feed, 1)
        outer.addLayout(center, 7)

        # ===== Right column =====
        right = QVBoxLayout()
        right.setSpacing(14)

        coords = PanelFrame("Coordinates  ·  World Frame")
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.addWidget(CoordBox("X MM", "128.42"), 0, 0)
        grid.addWidget(CoordBox("Y MM", "-22.18"), 0, 1)
        grid.addWidget(CoordBox("Z MM", "318.04"), 0, 2)
        grid.addWidget(CoordBox("RX RAD", "1.482"), 1, 0)
        grid.addWidget(CoordBox("RY RAD", "-0.215"), 1, 1)
        grid.addWidget(CoordBox("RZ RAD", "0.731"), 1, 2)
        coords.add_layout(grid)
        right.addWidget(coords)

        status = PanelFrame("Tool Status")
        for lab, val, color in [("Instrument", "Maryland Dissector", "#F5F7FA"),
                                 ("Serial", "MD-44218-A", "#E6EDF3"),
                                 ("Cycles", "148 / 600", "#E6EDF3"),
                                 ("Last Calibration", "06:18 UTC", "#E6EDF3"),
                                 ("Articulation", "7 DoF  ·  OK", "#20C997")]:
            row = QHBoxLayout()
            l = QLabel(lab)
            l.setObjectName("FieldLabel")
            v = QLabel(val)
            v.setStyleSheet(f"color:{color}; font-size:14px; font-weight:700;")
            row.addWidget(l)
            row.addStretch()
            row.addWidget(v)
            status.add_layout(row)
        bar = QProgressBar()
        bar.setRange(0, 600)
        bar.setValue(148)
        bar.setTextVisible(False)
        bar.setFixedHeight(8)
        status.add_widget(bar)
        right.addWidget(status)
        right.addStretch()

        outer.addLayout(right, 3)
