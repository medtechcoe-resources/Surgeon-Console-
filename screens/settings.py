"""
Settings tab — Comprehensive multi-section layout.
Absorbs telemetry content (CPU/GPU/RAM gauges, network diagnostics, event log).
Sections: Display, Vision, Network, System, Telemetry, Event Log.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QFrame, QPushButton, QComboBox, QSlider,
                             QScrollArea)
from PyQt6.QtCore import Qt
from widgets.card import PanelFrame


def setting_row(label, widget):
    row = QHBoxLayout()
    row.setContentsMargins(0, 8, 0, 8)
    l = QLabel(label)
    l.setObjectName("FieldLabel")
    l.setFixedWidth(200)
    row.addWidget(l)
    from PyQt6.QtWidgets import QLayout
    if isinstance(widget, QLayout):
        row.addLayout(widget)
    else:
        row.addWidget(widget)
    row.addStretch()
    return row


def _combo(items, width=200):
    c = QComboBox()
    c.addItems(items)
    c.setFixedWidth(width)
    c.setStyleSheet(
        "background-color:#1C2333; color:#E6EDF3; "
        "border:1px solid #2D3748; padding:6px; border-radius:4px;"
    )
    return c


class GaugeWidget(QFrame):
    def __init__(self, label, value, unit, level="good"):
        super().__init__()
        self.setObjectName("Card")
        color = {"good": "#20C997", "caution": "#F4B740", "critical": "#E5484D"}[level]
        self.setProperty("accent", "cyan" if level == "good" else level)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)

        l = QLabel(label.upper())
        l.setObjectName("CardLabel")

        row = QHBoxLayout()
        v = QLabel(str(value))
        v.setStyleSheet(
            f"color:{color}; font-size:24px; font-weight:700; "
            f"font-family:'JetBrains Mono','Consolas',monospace;"
        )
        u = QLabel(unit)
        u.setStyleSheet("color:#6B7B8D; font-size:13px; padding-top:6px;")

        row.addWidget(v)
        row.addWidget(u)
        row.addStretch()

        lay.addWidget(l)
        lay.addLayout(row)
        lay.addStretch()


def text_row(time, msg, color="#B5BEC8"):
    row = QHBoxLayout()
    row.setContentsMargins(0, 3, 0, 3)
    t = QLabel(time)
    t.setStyleSheet(
        "color:#6B7B8D; font-size:12px; "
        "font-family:'JetBrains Mono','Consolas',monospace; width:70px;"
    )
    m = QLabel(msg)
    m.setStyleSheet(
        f"color:{color}; font-size:12px; "
        f"font-family:'JetBrains Mono','Consolas',monospace;"
    )
    m.setWordWrap(True)
    row.addWidget(t)
    row.addWidget(m, 1)
    return row


class SettingsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        outer = QHBoxLayout(container)
        outer.setContentsMargins(0, 14, 0, 0)
        outer.setSpacing(16)

        # ═══ Column 1: Display + Vision + Camera ═══
        col1 = QVBoxLayout()
        col1.setSpacing(14)

        display = PanelFrame("Display & Interface")

        theme_combo = _combo(["Dark (Default)", "Light"])
        display.add_layout(setting_row("Application Theme", theme_combo))

        res_combo = _combo(["3440 x 1440 (Native)", "2560 x 1440", "1920 x 1080"])
        display.add_layout(setting_row("Default Resolution", res_combo))

        display.add_stretch()
        col1.addWidget(display)

        vision = PanelFrame("Vision & YOLO Pipeline")

        model_combo = _combo(
            ["yolov8x.pt (High Accuracy)", "yolov8m.pt (Balanced)", "yolov8n.pt (Fastest)"],
            250
        )
        vision.add_layout(setting_row("Detection Model", model_combo))

        conf_slider = QSlider(Qt.Orientation.Horizontal)
        conf_slider.setRange(10, 95)
        conf_slider.setValue(70)
        conf_slider.setFixedWidth(200)
        conf_val = QLabel("70%")
        conf_val.setStyleSheet("color:#F5F7FA; font-size:14px; margin-left:12px;")
        conf_slider.valueChanged.connect(lambda v: conf_val.setText(f"{v}%"))

        conf_row = QHBoxLayout()
        conf_row.addWidget(conf_slider)
        conf_row.addWidget(conf_val)
        vision.add_layout(setting_row("Confidence Threshold", conf_row))

        hw_combo = _combo(
            ["Auto (TensorRT > CUDA > CPU)", "CUDA Only", "CPU Only"],
            250
        )
        vision.add_layout(setting_row("Hardware Acceleration", hw_combo))

        vision.add_stretch()
        col1.addWidget(vision)

        camera = PanelFrame("Camera Calibration")
        for lab, val in [
            ("Lens Profile", "12mm F/1.8"),
            ("White Balance", "Auto  \u00B7  5500K"),
            ("Exposure", "Auto  \u00B7  1/60"),
            ("Focus Mode", "Continuous AF"),
        ]:
            row = QHBoxLayout()
            l = QLabel(lab)
            l.setObjectName("FieldLabel")
            v = QLabel(val)
            v.setStyleSheet("color:#E6EDF3; font-size:14px; font-weight:600;")
            row.addWidget(l)
            row.addStretch()
            row.addWidget(v)
            camera.add_layout(row)
        camera.add_stretch()
        col1.addWidget(camera)

        col1.addStretch()
        outer.addLayout(col1, 1)

        # ═══ Column 2: Network + System + Safety ═══
        col2 = QVBoxLayout()
        col2.setSpacing(14)

        network = PanelFrame("Network & Communication")

        pacs_btn = QPushButton("Configure PACS Server")
        pacs_btn.setProperty("class", "SecondaryButton")
        pacs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        network.add_layout(setting_row("DICOM Integration", pacs_btn))

        stream_combo = _combo(
            ["H.265 (High Efficiency)", "H.264 (Maximum Compatibility)", "Uncompressed (Diagnostics)"],
            250
        )
        network.add_layout(setting_row("Stream Codec", stream_combo))

        network.add_stretch()
        col2.addWidget(network)

        system = PanelFrame("System Maintenance")

        calib_btn = QPushButton("Run Full Calibration")
        calib_btn.setProperty("class", "PrimaryButton")
        calib_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        system.add_layout(setting_row("Kinematics", calib_btn))

        log_btn = QPushButton("Export System Logs")
        log_btn.setProperty("class", "SecondaryButton")
        log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        system.add_layout(setting_row("Diagnostics", log_btn))

        reset_btn = QPushButton("Factory Reset")
        reset_btn.setProperty("class", "DangerButton")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        system.add_layout(setting_row("Danger Zone", reset_btn))

        system.add_stretch()
        col2.addWidget(system)

        safety = PanelFrame("Safety Configuration")
        for lab, val, color in [
            ("Force Limit", "8.0 N", "#F5F7FA"),
            ("Velocity Cap", "0.5 m/s", "#F5F7FA"),
            ("Workspace Boundary", "Sphere 400mm", "#F5F7FA"),
            ("Tremor Filter", "ON  \u00B7  12 Hz", "#10B981"),
            ("Motion Scaling", "3:1 Default", "#F5F7FA"),
        ]:
            row = QHBoxLayout()
            l = QLabel(lab)
            l.setObjectName("FieldLabel")
            v = QLabel(val)
            v.setStyleSheet(f"color:{color}; font-size:14px; font-weight:700;")
            row.addWidget(l)
            row.addStretch()
            row.addWidget(v)
            safety.add_layout(row)
        safety.add_stretch()
        col2.addWidget(safety)

        col2.addStretch()
        outer.addLayout(col2, 1)

        # ═══ Column 3: Telemetry (absorbed from telemetry tab) + Event Log ═══
        col3 = QVBoxLayout()
        col3.setSpacing(14)

        # ─ System Telemetry Gauges ─
        telem_title = QLabel("SYSTEM TELEMETRY")
        telem_title.setObjectName("SectionTitle")
        col3.addWidget(telem_title)

        gauges = QGridLayout()
        gauges.setSpacing(10)
        gauges.addWidget(GaugeWidget("CPU Usage", "38", "%"), 0, 0)
        gauges.addWidget(GaugeWidget("GPU Usage", "42", "%"), 0, 1)
        gauges.addWidget(GaugeWidget("RAM Usage", "14.2", "GB"), 0, 2)
        gauges.addWidget(GaugeWidget("Thermal Core", "51", "\u00B0C"), 1, 0)
        gauges.addWidget(GaugeWidget("Storage I/O", "184", "MB/s"), 1, 1)
        gauges.addWidget(GaugeWidget("Network Latency", "0.84", "ms", "good"), 1, 2)
        col3.addLayout(gauges)

        # ─ Network & Loop Diagnostics ─
        net_diag = PanelFrame("Network & Loop Diagnostics")
        for lab, val, color in [
            ("Control Loop Frequency", "500.02 Hz", "#20C997"),
            ("Jitter", "0.01 ms", "#20C997"),
            ("Packet Loss (1hr)", "0.0001%", "#20C997"),
            ("Bandwidth Utilization", "42.8 Mbps", "#E6EDF3"),
            ("PACS Server", "Connected (TLS 1.3)", "#20C997"),
        ]:
            row = QHBoxLayout()
            l = QLabel(lab)
            l.setObjectName("FieldLabel")
            v = QLabel(val)
            v.setStyleSheet(f"color:{color}; font-size:14px; font-weight:700;")
            row.addWidget(l)
            row.addStretch()
            row.addWidget(v)
            net_diag.add_layout(row)
        net_diag.add_stretch()
        col3.addWidget(net_diag)

        # ─ System Event Log ─
        events = PanelFrame("System Event Log")
        logs = [
            ("08:42:11", "System initialized. OR-03 active.", "#F5F7FA"),
            ("08:42:15", "EtherCAT master link established at 1000Hz.", "#20C997"),
            ("08:43:02", "Kinematics calibrated. RMS error 0.42mm.", "#20C997"),
            ("08:45:10", "End-effector connected: Maryland Dissector.", "#F5F7FA"),
            ("08:50:22", "YOLOv8x vision pipeline loaded. GPU active.", "#F5F7FA"),
            ("09:12:05", "Warning: J3 approaching soft limit.", "#F4B740"),
            ("09:12:48", "Tool change verified.", "#20C997"),
            ("09:15:00", "Phase advanced: Dissection.", "#0095FF"),
            ("09:22:18", "Telemetry synced to console.", "#F5F7FA"),
            ("09:24:33", "Vital signs stable.", "#20C997"),
        ]
        for t, m, c in logs:
            events.add_layout(text_row(t, m, c))
        events.add_stretch()
        col3.addWidget(events, 1)

        col3.addStretch()
        outer.addLayout(col3, 1)

        scroll.setWidget(container)
        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)
