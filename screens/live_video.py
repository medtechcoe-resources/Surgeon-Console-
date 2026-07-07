"""
Live Video Tab — Redesigned for 3440×1440 ultrawide.
Layout: Left panel 18% | Center video 62% | Right panel 20%

Left panel:
  - Detection Summary (6 info rows: Instrument, Confidence, Tracking ID,
    Detection Status, Frame Count, Detection Time)
  - Instrument Controls (4 sliders: Jaw / Pitch / Yaw / Roll for Maryland Bipolar)
  - Pipeline Controls (Load Video, YOLO Detection, Vitals Overlay)

Center: Endoscopic video feed with zoom controls

Right panel:
  - Instruments list (name + arm + stats)
  - Arm diagram
  - Action buttons (CLUTCH / COAG / CUT) — compact, color-coded
"""
import math
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QPushButton, QSlider, QSizePolicy,
                             QFileDialog, QScrollArea, QSpacerItem)
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import (QPainter, QColor, QRadialGradient, QPen, QFont,
                          QPixmap, QImage, QPolygonF)
from widgets.card import MetricCard, PanelFrame
from theme_manager import ThemeManager
from yolo_pipeline import YoloPipeline


INSTRUMENT_COLORS = {1: "#0095FF", 2: "#10B981", 3: "#8B5CF6", 4: "#F59E0B"}


# ═══════════════════════════════════════════════════════════════════
#  DETECTION INFO ROW
# ═══════════════════════════════════════════════════════════════════

class _DetectRow(QWidget):
    """Single label + value row for the Detection Summary panel."""

    def __init__(self, label: str, value: str = "--", parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(8)

        self._lbl = QLabel(label.upper())
        self._lbl.setObjectName("DetectRowLabel")
        self._lbl.setMinimumWidth(120)

        self._val = QLabel(value)
        self._val.setObjectName("DetectRowValue")
        self._val.setAlignment(Qt.AlignmentFlag.AlignRight)

        lay.addWidget(self._lbl)
        lay.addStretch()
        lay.addWidget(self._val)

    def set_value(self, v: str):
        self._val.setText(v)

    def set_color(self, hex_color: str):
        self._val.setStyleSheet(
            f"color:{hex_color}; font-size:14px; font-weight:700; "
            f"font-family:'JetBrains Mono','Consolas',monospace;"
        )

    def reset_color(self):
        self._val.setStyleSheet("")


# ═══════════════════════════════════════════════════════════════════
#  INSTRUMENT SLIDER ROW
# ═══════════════════════════════════════════════════════════════════

class _SliderRow(QWidget):
    """Label + QSlider + live value display."""

    def __init__(self, label: str, min_val: int, max_val: int, default: int = 0,
                 unit: str = "°", parent=None):
        super().__init__(parent)
        self._unit = unit

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(4)

        header = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setObjectName("SliderLabel")
        self._val_lbl = QLabel(f"{default}{unit}")
        self._val_lbl.setObjectName("SliderValue")
        self._val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(self._val_lbl)
        lay.addLayout(header)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(default)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider.valueChanged.connect(self._on_change)
        lay.addWidget(self.slider)

    def _on_change(self, v: int):
        self._val_lbl.setText(f"{v}{self._unit}")

    def set_enabled(self, enabled: bool):
        self.slider.setEnabled(enabled)

    def reset(self):
        self.slider.setValue(0)


# ═══════════════════════════════════════════════════════════════════
#  COMPACT INSTRUMENT CARD (Right Panel)
# ═══════════════════════════════════════════════════════════════════

class _InstrumentCard(QFrame):
    def __init__(self, number, name, arm, stat_label="", stat_val="", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        color = INSTRUMENT_COLORS.get(number, "#0095FF")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(12)

        badge = QLabel(str(number))
        badge.setFixedSize(28, 28)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background-color:{color}; color:#0D1117; border-radius:14px; "
            f"font-size:13px; font-weight:800;"
        )
        lay.addWidget(badge)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        n = QLabel(name)
        n.setStyleSheet(
            "color:#F5F7FA; font-size:13px; font-weight:700;"
        )
        n.setWordWrap(True)
        a = QLabel(arm)
        a.setStyleSheet(
            f"color:{color}; font-size:11px; font-weight:700; letter-spacing:0.5px;"
        )
        text_box.addWidget(n)
        text_box.addWidget(a)
        lay.addLayout(text_box, 1)

        if stat_label:
            stat = QVBoxLayout()
            stat.setSpacing(2)
            sl = QLabel(stat_label)
            sl.setObjectName("DetectRowLabel")
            sv = QLabel(stat_val)
            sv.setStyleSheet(
                f"color:{color}; font-size:14px; font-weight:700; "
                f"font-family:'JetBrains Mono','Consolas',monospace;"
            )
            stat.addWidget(sl)
            stat.addWidget(sv)
            lay.addLayout(stat)


# ═══════════════════════════════════════════════════════════════════
#  ROBOTIC ARM DIAGRAM
# ═══════════════════════════════════════════════════════════════════

class _ArmDiagram(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setFixedHeight(160)
        tm = ThemeManager.instance()
        tm.theme_changed.connect(lambda _: self.update())

    def paintEvent(self, event):
        tm = ThemeManager.instance()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        # Console body
        p.setBrush(QColor(tm.color("bg_header")))
        p.setPen(QPen(QColor(tm.color("border_heavy")), 2))
        p.drawRoundedRect(int(cx - 18), int(cy - 40), 36, 80, 8, 8)

        colors = ["#0095FF", "#10B981", "#8B5CF6", "#F59E0B"]
        positions = [
            (cx - 70, cy - 25),
            (cx + 44, cy - 25),
            (cx - 70, cy + 10),
            (cx + 44, cy + 10),
        ]
        for i, ((ax, ay), color) in enumerate(zip(positions, colors)):
            arm_cx = cx - 18 if ax < cx else cx + 18
            arm_cy = ay + 12
            p.setPen(QPen(QColor(color), 2.5, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap))
            p.drawLine(int(arm_cx), int(arm_cy), int(ax + 12), int(arm_cy))
            p.setBrush(QColor(tm.color("bg_card")))
            p.setPen(QPen(QColor(color), 2))
            p.drawEllipse(int(ax), int(ay), 24, 24)
            p.setPen(QColor(color))
            f = QFont("Inter", 10, QFont.Weight.Bold)
            p.setFont(f)
            p.drawText(int(ax), int(ay), 24, 24,
                       Qt.AlignmentFlag.AlignCenter, str(i + 1))
        p.end()


# ═══════════════════════════════════════════════════════════════════
#  VIDEO FEED CANVAS
# ═══════════════════════════════════════════════════════════════════

class _FeedCanvas(QFrame):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(640, 360)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._pixmap = None
        tm = ThemeManager.instance()
        tm.theme_changed.connect(lambda _: self.update())

    def set_frame(self, qimage):
        self._pixmap = QPixmap.fromImage(qimage)
        self.update()

    def clear_frame(self):
        self._pixmap = None
        self.update()

    def paintEvent(self, event):
        tm = ThemeManager.instance()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                w, h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            sx = (scaled.width() - w) // 2
            sy = (scaled.height() - h) // 2
            p.drawPixmap(0, 0, scaled, sx, sy, w, h)
        else:
            if tm.is_dark():
                grad = QRadialGradient(w / 2, h / 2, max(w, h) * 0.7)
                grad.setColorAt(0.0, QColor(50, 18, 18))
                grad.setColorAt(0.7, QColor(22, 8, 8))
                grad.setColorAt(1.0, QColor(10, 5, 5))
            else:
                grad = QRadialGradient(w / 2, h / 2, max(w, h) * 0.7)
                grad.setColorAt(0.0, QColor(220, 230, 240))
                grad.setColorAt(1.0, QColor(200, 215, 230))
            p.fillRect(self.rect(), grad)

            muted = QColor(tm.color("fg_muted"))
            p.setPen(muted)
            font = QFont("Inter", 16, QFont.Weight.DemiBold)
            p.setFont(font)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "NO VIDEO SOURCE")

        p.end()


# ═══════════════════════════════════════════════════════════════════
#  PAINTED DOT
# ═══════════════════════════════════════════════════════════════════

class _PaintedDot(QWidget):
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


# ═══════════════════════════════════════════════════════════════════
#  SECTION SEPARATOR
# ═══════════════════════════════════════════════════════════════════

def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("SectionTitle")
    return lbl


def _divider() -> QFrame:
    f = QFrame()
    f.setObjectName("HLine")
    f.setFrameShape(QFrame.Shape.HLine)
    return f


# ═══════════════════════════════════════════════════════════════════
#  MAIN LIVE VIDEO SCREEN
# ═══════════════════════════════════════════════════════════════════

class LiveVideoScreen(QWidget):
    ZOOM_MIN = 1.0
    ZOOM_MAX = 3.0
    ZOOM_STEP = 0.2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom = self.ZOOM_MIN

        # YOLO Pipeline
        self.pipeline = YoloPipeline(self)
        self.pipeline.frame_ready.connect(self._on_frame)
        self.pipeline.stats_updated.connect(self._on_stats)
        self.pipeline.status_changed.connect(self._on_status)

        self._yolo_enabled = False
        self._vitals_enabled = False
        self._frame_count = 0
        self._detect_time_ms = 0.0

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 14, 0, 0)
        outer.setSpacing(14)

        # ══════════════════════════════════════════
        #  LEFT PANEL (~18%)
        # ══════════════════════════════════════════
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setMinimumWidth(280)
        left_scroll.setMaximumWidth(320)

        left_widget = QWidget()
        left = QVBoxLayout(left_widget)
        left.setContentsMargins(0, 0, 8, 0)
        left.setSpacing(10)

        # ─ Detection Summary ─
        left.addWidget(_section_label("DETECTION SUMMARY"))

        detect_card = QFrame()
        detect_card.setObjectName("Card")
        detect_layout = QVBoxLayout(detect_card)
        detect_layout.setContentsMargins(16, 14, 16, 14)
        detect_layout.setSpacing(2)

        self._d_name   = _DetectRow("Instrument Name", "--")
        self._d_conf   = _DetectRow("Confidence", "--")
        self._d_tid    = _DetectRow("Tracking ID", "--")
        self._d_status = _DetectRow("Detection Status", "IDLE")
        self._d_frames = _DetectRow("Frame Count", "0")
        self._d_time   = _DetectRow("Detection Time", "--")

        for row in (self._d_name, self._d_conf, self._d_tid,
                    self._d_status, self._d_frames, self._d_time):
            detect_layout.addWidget(row)
            detect_layout.addWidget(_divider())

        left.addWidget(detect_card)
        left.addSpacing(4)

        # ─ Maryland Bipolar Controls ─
        left.addWidget(_section_label("MARYLAND BIPOLAR CONTROLS"))

        slider_card = QFrame()
        slider_card.setObjectName("Card")
        slider_layout = QVBoxLayout(slider_card)
        slider_layout.setContentsMargins(16, 14, 16, 14)
        slider_layout.setSpacing(6)

        self._s_jaw   = _SliderRow("Jaw",   0,    100,   0, "°")
        self._s_pitch = _SliderRow("Pitch", -45,  45,    0, "°")
        self._s_yaw   = _SliderRow("Yaw",   -45,  45,    0, "°")
        self._s_roll  = _SliderRow("Roll",  -180, 180,   0, "°")

        for sr in (self._s_jaw, self._s_pitch, self._s_yaw, self._s_roll):
            slider_layout.addWidget(sr)

        left.addWidget(slider_card)
        left.addSpacing(4)

        # ─ Pipeline Controls ─
        left.addWidget(_section_label("PIPELINE CONTROLS"))

        self.btn_load_video = QPushButton("Load Video")
        self.btn_load_video.setProperty("class", "PrimaryButton")
        self.btn_load_video.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_load_video.clicked.connect(self._load_video)
        left.addWidget(self.btn_load_video)

        self.btn_yolo = QPushButton("YOLO Detection")
        self.btn_yolo.setProperty("class", "ToggleButton")
        self.btn_yolo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_yolo.clicked.connect(self._toggle_yolo)
        left.addWidget(self.btn_yolo)

        self.btn_vitals = QPushButton("Vitals Overlay")
        self.btn_vitals.setProperty("class", "ToggleButton")
        self.btn_vitals.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_vitals.clicked.connect(self._toggle_vitals)
        left.addWidget(self.btn_vitals)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("DetectRowLabel")
        self.status_label.setWordWrap(True)
        left.addWidget(self.status_label)

        left.addStretch()
        left_scroll.setWidget(left_widget)
        outer.addWidget(left_scroll, 18)

        # ══════════════════════════════════════════
        #  CENTER PANEL (~62%) — Video Feed
        # ══════════════════════════════════════════
        center = QVBoxLayout()
        center.setSpacing(0)
        center.setContentsMargins(0, 0, 0, 0)

        # Header bar
        header_bar = QFrame()
        header_bar.setObjectName("SectionHeaderBar")
        hb_lay = QHBoxLayout(header_bar)
        hb_lay.setContentsMargins(20, 10, 20, 10)
        hb_lay.setSpacing(16)

        feed_title = QLabel("ENDOSCOPIC FEED  ·  CH-01")
        feed_title.setObjectName("PanelTitle")
        feed_title.setStyleSheet("font-size:16px;")

        self.rec_dot = _PaintedDot("#EF4444")
        self.rec_label = QLabel("REC")
        self.rec_label.setStyleSheet(
            "color:#EF4444; font-size:11px; font-weight:700;"
        )
        self.meta_label = QLabel("1920×1080  ·  H.265")
        self.meta_label.setObjectName("DetectRowLabel")

        hb_lay.addWidget(feed_title)
        hb_lay.addStretch()
        hb_lay.addWidget(self.rec_dot)
        hb_lay.addSpacing(4)
        hb_lay.addWidget(self.rec_label)
        hb_lay.addSpacing(16)
        hb_lay.addWidget(self.meta_label)
        center.addWidget(header_bar)

        # Video canvas
        self.canvas = _FeedCanvas()
        self.canvas.setMinimumHeight(480)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        center.addWidget(self.canvas, 1)

        # Camera control bar
        ctrl_bar = QHBoxLayout()
        ctrl_bar.setContentsMargins(20, 10, 20, 10)
        ctrl_bar.setSpacing(16)

        self.btn_focus = QPushButton("Focus")
        self.btn_focus.setProperty("class", "GridButton")
        self.btn_focus.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_focus.setFixedSize(72, 34)
        ctrl_bar.addWidget(self.btn_focus)

        ctrl_bar.addStretch()

        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setProperty("class", "GridButton")
        self.btn_zoom_out.setFixedSize(34, 34)
        self.btn_zoom_out.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_zoom_out.clicked.connect(self._zoom_out)

        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 30)
        self.zoom_slider.setValue(10)
        self.zoom_slider.setFixedWidth(180)
        self.zoom_slider.valueChanged.connect(self._on_zoom_slider)

        self.zoom_value_lbl = QLabel("1.0×")
        self.zoom_value_lbl.setObjectName("SliderValue")
        self.zoom_value_lbl.setFixedWidth(48)
        self.zoom_value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setProperty("class", "GridButton")
        self.btn_zoom_in.setFixedSize(34, 34)
        self.btn_zoom_in.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_zoom_in.clicked.connect(self._zoom_in)

        ctrl_bar.addWidget(self.btn_zoom_out)
        ctrl_bar.addWidget(self.zoom_slider)
        ctrl_bar.addWidget(self.zoom_value_lbl)
        ctrl_bar.addWidget(self.btn_zoom_in)
        ctrl_bar.addStretch()

        self.btn_home_cam = QPushButton("Home")
        self.btn_home_cam.setProperty("class", "GridButton")
        self.btn_home_cam.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_home_cam.setFixedSize(72, 34)
        self.btn_home_cam.clicked.connect(self._zoom_home)
        ctrl_bar.addWidget(self.btn_home_cam)
        center.addLayout(ctrl_bar)

        # Bottom info bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(20, 0, 20, 10)
        self.frame_lbl = QLabel("FRAME 0000000")
        self.time_lbl = QLabel("T+ 00:00:00")
        self.roi_lbl = QLabel("ZOOM 1.0×  ·  ROI 100%")
        for lbl in (self.frame_lbl, self.time_lbl, self.roi_lbl):
            lbl.setObjectName("DetectRowLabel")
            lbl.setStyleSheet(
                "font-family:'JetBrains Mono','Consolas',monospace; font-size:11px;"
            )
            bottom_bar.addWidget(lbl)
            bottom_bar.addStretch()
        center.addLayout(bottom_bar)

        center_widget = QWidget()
        center_widget.setLayout(center)
        center_widget.setObjectName("Card")
        outer.addWidget(center_widget, 62)

        # ══════════════════════════════════════════
        #  RIGHT PANEL (~20%)
        # ══════════════════════════════════════════
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_scroll.setMinimumWidth(260)
        right_scroll.setMaximumWidth(340)

        right_widget = QWidget()
        right = QVBoxLayout(right_widget)
        right.setContentsMargins(8, 0, 0, 0)
        right.setSpacing(10)

        right.addWidget(_section_label("INSTRUMENTS"))

        right.addWidget(_InstrumentCard(
            1, "Maryland Bipolar Curved Scissors", "Arm 1", "Coag", "40 W"
        ))
        right.addWidget(_InstrumentCard(
            2, "Monopolar Curved Scissors", "Arm 2", "Cut", "30 W"
        ))
        right.addWidget(_InstrumentCard(
            3, "Prograsp Forceps", "Arm 3"
        ))
        right.addWidget(_InstrumentCard(
            4, "Cadiere Forceps", "Arm 4"
        ))

        right.addWidget(_ArmDiagram())

        # ─ Action Buttons ─
        right.addWidget(_section_label("FOOT PEDAL CONTROLS"))

        action_card = QFrame()
        action_card.setObjectName("Card")
        ac_lay = QVBoxLayout(action_card)
        ac_lay.setContentsMargins(14, 14, 14, 14)
        ac_lay.setSpacing(8)

        self.btn_clutch = QPushButton("⬛  CLUTCH")
        self.btn_clutch.setProperty("class", "ClutchButton")
        self.btn_clutch.setProperty("active", "true")
        self.btn_clutch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clutch.clicked.connect(lambda: self._toggle_action(self.btn_clutch))
        ac_lay.addWidget(self.btn_clutch)

        coag_cut = QHBoxLayout()
        coag_cut.setSpacing(8)

        self.btn_coag = QPushButton("🔥  COAG")
        self.btn_coag.setProperty("class", "CoagButton")
        self.btn_coag.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_coag.clicked.connect(lambda: self._toggle_action(self.btn_coag))

        self.btn_cut = QPushButton("✂  CUT")
        self.btn_cut.setProperty("class", "CutButton")
        self.btn_cut.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cut.clicked.connect(lambda: self._toggle_action(self.btn_cut))

        coag_cut.addWidget(self.btn_coag)
        coag_cut.addWidget(self.btn_cut)
        ac_lay.addLayout(coag_cut)

        right.addWidget(action_card)
        right.addStretch()

        right_scroll.setWidget(right_widget)
        outer.addWidget(right_scroll, 20)

        # REC blink
        self._rec_visible = True
        self._rec_timer = QTimer(self)
        self._rec_timer.timeout.connect(self._blink_rec)
        self._rec_timer.start(800)

    # ── Frame / Stats Callbacks ────────────────────────────────────────

    def _on_frame(self, qimage):
        self.canvas.set_frame(qimage)
        info = self.pipeline.get_video_info()
        self._frame_count = info.get("current_frame", self._frame_count)
        self.frame_lbl.setText(f"FRAME {self._frame_count:07d}")
        if info.get("width", 0) > 0:
            self.meta_label.setText(
                f"{info['width']}×{info['height']}  ·  H.265"
            )

    def _on_stats(self, stats):
        # Detection summary rows
        if stats.objects_detected > 0:
            self._d_name.set_value("Instrument")
            self._d_name.set_color("#10B981")
            self._d_status.set_value("DETECTED")
            self._d_status.set_color("#10B981")
        else:
            self._d_name.set_value("--")
            self._d_name.reset_color()
            self._d_status.set_value("IDLE")
            self._d_status.reset_color()

        conf = stats.mean_confidence
        self._d_conf.set_value(f"{conf:.0f}%" if conf > 0 else "--")
        self._d_tid.set_value(
            str(stats.objects_detected) if stats.objects_detected > 0 else "--"
        )
        self._d_frames.set_value(str(self._frame_count))
        self._d_time.set_value(
            f"{stats.inference_ms:.1f} ms" if stats.inference_ms > 0 else "--"
        )

    def _on_status(self, msg):
        self.status_label.setText(msg)

    # ── Button Handlers ───────────────────────────────────────────────

    def _load_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Video", "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv);;All Files (*)"
        )
        if path:
            self.pipeline.load_video(path)

    def _toggle_yolo(self):
        self._yolo_enabled = not self._yolo_enabled
        self.pipeline.set_detection(self._yolo_enabled)
        self.btn_yolo.setProperty(
            "active", "true" if self._yolo_enabled else "false"
        )
        self.btn_yolo.style().unpolish(self.btn_yolo)
        self.btn_yolo.style().polish(self.btn_yolo)

    def _toggle_vitals(self):
        self._vitals_enabled = not self._vitals_enabled
        self.pipeline.set_vitals_overlay(self._vitals_enabled)
        self.btn_vitals.setProperty(
            "active", "true" if self._vitals_enabled else "false"
        )
        self.btn_vitals.setProperty(
            "accent", "blue" if self._vitals_enabled else ""
        )
        self.btn_vitals.style().unpolish(self.btn_vitals)
        self.btn_vitals.style().polish(self.btn_vitals)

    def _toggle_action(self, btn):
        current = btn.property("active") == "true"
        btn.setProperty("active", "false" if current else "true")
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    # ── Zoom ──────────────────────────────────────────────────────────

    def _zoom_in(self):
        self.zoom = min(self.ZOOM_MAX, round(self.zoom + self.ZOOM_STEP, 2))
        self._apply_zoom()

    def _zoom_out(self):
        self.zoom = max(self.ZOOM_MIN, round(self.zoom - self.ZOOM_STEP, 2))
        self._apply_zoom()

    def _zoom_home(self):
        self.zoom = 1.0
        self._apply_zoom()

    def _on_zoom_slider(self, value):
        self.zoom = value / 10.0
        self._update_zoom_ui()

    def _apply_zoom(self):
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(self.zoom * 10))
        self.zoom_slider.blockSignals(False)
        self._update_zoom_ui()

    def _update_zoom_ui(self):
        self.zoom_value_lbl.setText(f"{self.zoom:.1f}×")
        roi = round(100 / self.zoom)
        self.roi_lbl.setText(f"ZOOM {self.zoom:.1f}×  ·  ROI {roi}%")
        self.btn_zoom_out.setEnabled(self.zoom > self.ZOOM_MIN)
        self.btn_zoom_in.setEnabled(self.zoom < self.ZOOM_MAX)

    # ── REC Blink ─────────────────────────────────────────────────────

    def _blink_rec(self):
        self._rec_visible = not self._rec_visible
        self.rec_dot.setVisible(self._rec_visible)
        self.rec_label.setVisible(self._rec_visible)
