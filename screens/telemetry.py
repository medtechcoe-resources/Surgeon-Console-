"""
Telemetry tab — System resources, network latency, and detailed logs.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from widgets.card import MetricCard, PanelFrame

class GaugeWidget(QFrame):
    def __init__(self, label, value, unit, level="good"):
        super().__init__()
        self.setObjectName("Card")
        color = {"good": "#20C997", "caution": "#F4B740", "critical": "#E5484D"}[level]
        self.setProperty("accent", "cyan" if level == "good" else level)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(6)
        
        l = QLabel(label.upper())
        l.setObjectName("CardLabel")
        
        row = QHBoxLayout()
        v = QLabel(str(value))
        v.setStyleSheet(f"color:{color}; font-size:28px; font-weight:700; font-family:'JetBrains Mono','Consolas',monospace;")
        u = QLabel(unit)
        u.setStyleSheet("color:#6B7B8D; font-size:14px; padding-top:8px;")
        
        row.addWidget(v)
        row.addWidget(u)
        row.addStretch()
        
        lay.addWidget(l)
        lay.addLayout(row)
        lay.addStretch()

def text_row(time, msg, color="#B5BEC8"):
    row = QHBoxLayout()
    row.setContentsMargins(0, 4, 0, 4)
    t = QLabel(time)
    t.setStyleSheet("color:#6B7B8D; font-size:13px; font-family:'JetBrains Mono','Consolas',monospace; width:80px;")
    m = QLabel(msg)
    m.setStyleSheet(f"color:{color}; font-size:13px; font-family:'JetBrains Mono','Consolas',monospace;")
    row.addWidget(t)
    row.addWidget(m, 1)
    return row

class TelemetryScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 14, 0, 0)
        outer.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(14)
        
        gauges = QGridLayout()
        gauges.setSpacing(12)
        gauges.addWidget(GaugeWidget("CPU Usage", "38", "%"), 0, 0)
        gauges.addWidget(GaugeWidget("GPU Usage", "42", "%"), 0, 1)
        gauges.addWidget(GaugeWidget("RAM Usage", "14.2", "GB"), 0, 2)
        gauges.addWidget(GaugeWidget("Thermal Core", "51", "\u00B0C"), 1, 0)
        gauges.addWidget(GaugeWidget("Storage I/O", "184", "MB/s"), 1, 1)
        gauges.addWidget(GaugeWidget("Network Latency", "0.84", "ms", "good"), 1, 2)
        
        left.addLayout(gauges)
        
        network = PanelFrame("Network & Loop Diagnostics")
        for lab, val, color in [("Control Loop Frequency", "500.02 Hz", "#20C997"),
                                 ("Jitter", "0.01 ms", "#20C997"),
                                 ("Packet Loss (1hr)", "0.0001%", "#20C997"),
                                 ("Bandwidth Utilization", "42.8 Mbps", "#E6EDF3"),
                                 ("PACS Server", "Connected (TLS 1.3)", "#20C997")]:
            row = QHBoxLayout()
            l = QLabel(lab)
            l.setObjectName("FieldLabel")
            v = QLabel(val)
            v.setStyleSheet(f"color:{color}; font-size:14px; font-weight:700;")
            row.addWidget(l)
            row.addStretch()
            row.addWidget(v)
            network.add_layout(row)
        network.add_stretch()
        left.addWidget(network, 1)
        
        outer.addLayout(left, 1)
        
        right = QVBoxLayout()
        right.setSpacing(14)
        
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
        
        right.addWidget(events, 1)
        outer.addLayout(right, 1)
