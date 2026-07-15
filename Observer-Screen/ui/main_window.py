# ═══════════════════════════════════════════════════════════════════
#  OBSERVER SCREEN — MAIN WINDOW
#  Subscribes to all topics and renders an 8-panel real-time grid.
# ═══════════════════════════════════════════════════════════════════

import sys
import os
import json
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QTextEdit,
)

# Ensure project root is in path for shared_networking
_proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _proj_root not in sys.path:
    sys.path.insert(0, _proj_root)

from shared_networking.connection_manager import ConnectionManager
from config import C, WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT
from ui.widgets import (
    CardFrame, SectionHeader, StatusBadge, StatusIndicator,
    MetricCard, KeyValueRow,
)


class MainWindow(QMainWindow):
    """Observer Screen Main Window — 8-panel grid dashboard."""

    def __init__(self, username: str = "", role: str = "user",
                 session_id: str = ""):
        super().__init__()
        self._username = username
        self._role = role
        self._session_id = session_id

        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # Initialize shared networking
        self._conn_mgr = ConnectionManager(
            client_name="observer_screen",
            publish_topics=[],
            subscribe_topics=[
                "patient_vitals",
                "robot_telemetry",
                "alerts",
                "system_status",
                "connection_status",
            ],
            username=username,
            role=role,
            session_id=session_id,
            parent=self,
        )
        self._conn_mgr.enable_auto_reconnect(True)

        # Wire signals
        self._conn_mgr.connected.connect(self._on_connected)
        self._conn_mgr.disconnected.connect(self._on_disconnected)
        self._conn_mgr.error_occurred.connect(self._on_error)
        self._conn_mgr.stats_updated.connect(self._on_stats_updated)
        self._conn_mgr.message_received.connect(self._on_message_received)
        self._conn_mgr.client_list_received.connect(self._on_client_list)

        # Topic tracking stats
        self._topic_counts = {
            "patient_vitals": 0,
            "robot_telemetry": 0,
            "alerts": 0,
            "system_status": 0,
            "connection_status": 0,
        }
        self._topic_last_times = {}

        self._build_ui()

        # Auto-connect to broker
        self._conn_mgr.connect_to_broker()

        # Request client list periodically
        self._list_timer = QTimer(self)
        self._list_timer.setInterval(3000)
        self._list_timer.timeout.connect(self._conn_mgr.request_client_list)
        self._list_timer.start()

    # ══════════════════════════════════════════════════════════════
    #  UI BUILD
    # ══════════════════════════════════════════════════════════════

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Header Bar
        self._build_header(main_layout)

        # 8-Panel Grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)

        # Col 0 (Left): Patient Vitals & Robot Telemetry
        grid_layout.addWidget(self._build_vitals_panel(), 0, 0)
        grid_layout.addWidget(self._build_telemetry_panel(), 1, 0)

        # Col 1 (Middle): Active Alerts & Live Message Log
        grid_layout.addWidget(self._build_alerts_panel(), 0, 1)
        grid_layout.addWidget(self._build_message_log_panel(), 1, 1)

        # Col 2 (Right): Connected Clients, Topic Monitor, Health/Stats
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        right_layout.addWidget(self._build_clients_panel(), 1)
        right_layout.addWidget(self._build_topic_monitor_panel(), 1)

        # Stats and Health split
        stats_health = QHBoxLayout()
        stats_health.setSpacing(10)
        stats_health.addWidget(self._build_stats_panel(), 1)
        stats_health.addWidget(self._build_health_panel(), 1)
        right_layout.addLayout(stats_health)

        grid_layout.addWidget(right_panel, 0, 2, 2, 1)

        # Set column stretch factors for balanced layout
        grid_layout.setColumnStretch(0, 3)  # Vitals & Telemetry
        grid_layout.setColumnStretch(1, 4)  # Alerts & Messages
        grid_layout.setColumnStretch(2, 3)  # Info lists

        # Set row stretches
        grid_layout.setRowStretch(0, 1)
        grid_layout.setRowStretch(1, 1)

        main_layout.addLayout(grid_layout, 1)

    def _build_header(self, layout: QVBoxLayout):
        """Top bar displaying title, status, and clock."""
        header = QWidget()
        header.setFixedHeight(50)
        header.setStyleSheet(f"background-color: {C['bg1']}; border-bottom: 2px solid {C['cyan']};")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)

        title = QLabel("AETHER CLINICAL OBSERVER SCREEN")
        title.setFont(QFont("JetBrains Mono", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C['cyan']};")
        h_layout.addWidget(title)

        h_layout.addStretch()

        self._header_conn_indicator = StatusIndicator(C["red"], size=12)
        h_layout.addWidget(self._header_conn_indicator)
        h_layout.addSpacing(6)

        self._header_conn_label = QLabel("DISCONNECTED FROM BROKER")
        self._header_conn_label.setFont(QFont("JetBrains Mono", 10, QFont.Weight.Bold))
        self._header_conn_label.setStyleSheet(f"color: {C['red']};")
        h_layout.addWidget(self._header_conn_label)
        h_layout.addSpacing(30)

        self._clock_label = QLabel("--:--:--")
        self._clock_label.setFont(QFont("JetBrains Mono", 12, QFont.Weight.Bold))
        self._clock_label.setStyleSheet(f"color: {C['txt1']};")
        h_layout.addWidget(self._clock_label)

        # Timer for clock
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(
            lambda: self._clock_label.setText(datetime.now().strftime("%H:%M:%S")))
        self._clock_timer.start()

        layout.addWidget(header)

    # ── Panel 1: Patient Vitals ───────────────────────────────────

    def _build_vitals_panel(self) -> QWidget:
        card = CardFrame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        layout.addWidget(SectionHeader("Patient Vitals (From Surgeon Console)", C["green"]))

        # ICU Vitals Grid
        grid = QGridLayout()
        grid.setSpacing(8)

        self._vital_widgets = {}
        vitals_cfg = [
            ("HR", "bpm", C["pink"]),
            ("SpO₂", "%", C["cyan"]),
            ("BP", "mmHg", C["violet"]),
            ("RR", "br/m", C["amber"]),
            ("Temp", "°C", C["green"]),
        ]

        for i, (name, unit, color) in enumerate(vitals_cfg):
            vc = CardFrame()
            vcl = QVBoxLayout(vc)
            vcl.setContentsMargins(8, 6, 8, 6)
            vcl.setSpacing(2)

            lbl = QLabel(name)
            lbl.setFont(QFont("JetBrains Mono", 10, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color: {C['txt2']};")
            vcl.addWidget(lbl)

            val = QLabel("---")
            val.setFont(QFont("JetBrains Mono", 24, QFont.Weight.Bold))
            val.setStyleSheet(f"color: {color};")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vcl.addWidget(val)

            unit_lbl = QLabel(unit)
            unit_lbl.setFont(QFont("JetBrains Mono", 8))
            unit_lbl.setStyleSheet(f"color: {C['txt2']};")
            unit_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vcl.addWidget(unit_lbl)

            grid.addWidget(vc, 0, i)
            self._vital_widgets[name] = val

        layout.addLayout(grid)

        # ECG block
        ecg_card = CardFrame()
        el = QHBoxLayout(ecg_card)
        el.setContentsMargins(12, 6, 12, 6)
        el.addWidget(QLabel("ECG WAVEFORM STATUS: "))
        self._ecg_status = QLabel("WAITING FOR DATA")
        self._ecg_status.setFont(QFont("JetBrains Mono", 10, QFont.Weight.Bold))
        self._ecg_status.setStyleSheet(f"color: {C['txt2']};")
        el.addWidget(self._ecg_status)
        el.addStretch()
        layout.addWidget(ecg_card)

        return card

    # ── Panel 2: Robot Telemetry ──────────────────────────────────

    def _build_telemetry_panel(self) -> QWidget:
        card = CardFrame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        layout.addWidget(SectionHeader("Robot Telemetry & DOF State", C["violet"]))

        cols = QHBoxLayout()
        cols.setSpacing(10)

        # Joint angles (Left col)
        left = QVBoxLayout()
        left.addWidget(QLabel("JOINT ANGLES:"))
        self._joint_labels = []
        for i in range(6):
            row = KeyValueRow(f"Joint {i+1}", "0.00°")
            left.addWidget(row)
            self._joint_labels.append(row)
        cols.addLayout(left, 1)

        # Position/EE details (Right col)
        right = QVBoxLayout()
        right.addWidget(QLabel("END EFFECTOR STATE:"))
        self._telem_pos_x = KeyValueRow("Tool Position X", "---", C["cyan"])
        self._telem_pos_y = KeyValueRow("Tool Position Y", "---", C["cyan"])
        self._telem_pos_z = KeyValueRow("Tool Position Z", "---", C["cyan"])
        self._telem_rot = KeyValueRow("EE Rotation", "---", C["green"])
        self._telem_force = KeyValueRow("Contact Force", "---", C["pink"])
        self._telem_cpu = KeyValueRow("CPU Usage", "---", C["amber"])

        for w in (self._telem_pos_x, self._telem_pos_y, self._telem_pos_z,
                  self._telem_rot, self._telem_force, self._telem_cpu):
            right.addWidget(w)
        cols.addLayout(right, 1)

        layout.addLayout(cols)
        return card

    # ── Panel 3: Active Alerts ────────────────────────────────────

    def _build_alerts_panel(self) -> QWidget:
        card = CardFrame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        layout.addWidget(SectionHeader("System Safety & Active Alerts", C["red"]))

        self._alerts_table = QTableWidget()
        self._alerts_table.setColumnCount(4)
        self._alerts_table.setHorizontalHeaderLabels(
            ["TIME", "SEVERITY", "SOURCE", "MESSAGE"])
        self._alerts_table.verticalHeader().setVisible(False)
        self._alerts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._alerts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._alerts_table.setAlternatingRowColors(True)

        self._alerts_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        for col in range(3):
            self._alerts_table.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._alerts_table)
        return card

    # ── Panel 4: Connected Clients ────────────────────────────────

    def _build_clients_panel(self) -> QWidget:
        card = CardFrame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        layout.addWidget(SectionHeader("Connected Pub-Sub Clients", C["cyan"]))

        self._clients_table = QTableWidget()
        self._clients_table.setColumnCount(3)
        self._clients_table.setHorizontalHeaderLabels(["CLIENT", "PUBLISHES", "SUBSCRIBES"])
        self._clients_table.verticalHeader().setVisible(False)
        self._clients_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._clients_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._clients_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._clients_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._clients_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self._clients_table)
        return card

    # ── Panel 5: Topic Monitor ────────────────────────────────────

    def _build_topic_monitor_panel(self) -> QWidget:
        card = CardFrame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        layout.addWidget(SectionHeader("Topic & Broadcast Traffic Monitor", C["teal"]))

        self._topic_table = QTableWidget()
        self._topic_table.setColumnCount(3)
        self._topic_table.setHorizontalHeaderLabels(["TOPIC", "MESSAGES", "LAST ACTIVE"])
        self._topic_table.verticalHeader().setVisible(False)
        self._topic_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._topic_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._topic_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._topic_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._topic_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._topic_table)
        self._refresh_topic_table()
        return card

    # ── Panel 6: Packet Statistics ────────────────────────────────

    def _build_stats_panel(self) -> QWidget:
        card = CardFrame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        layout.addWidget(SectionHeader("Network Traffic Stats", C["cyan"]))

        self._stat_packets = KeyValueRow("Packets Recv", "0", C["cyan"])
        self._stat_bytes = KeyValueRow("Bytes Recv", "0", C["cyan"])
        self._stat_rate = KeyValueRow("Throughput In", "0.0 B/s", C["green"])
        self._stat_errors = KeyValueRow("Errors Count", "0", C["red"])

        for w in (self._stat_packets, self._stat_bytes, self._stat_rate, self._stat_errors):
            layout.addWidget(w)

        layout.addStretch()
        return card

    # ── Panel 7: Connection Health ────────────────────────────────

    def _build_health_panel(self) -> QWidget:
        card = CardFrame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        layout.addWidget(SectionHeader("Broker Connection Health", C["green"]))

        self._health_latency = KeyValueRow("Ping Latency", "--- ms", C["green"])
        self._health_reconnects = KeyValueRow("Reconnects", "0", C["amber"])
        self._health_heartbeat = KeyValueRow("Heartbeat", "---", C["green"])
        self._health_uptime = KeyValueRow("Client Uptime", "---", C["cyan"])

        for w in (self._health_latency, self._health_reconnects, self._health_heartbeat, self._health_uptime):
            layout.addWidget(w)

        layout.addStretch()
        return card

    # ── Panel 8: Live Message Log ─────────────────────────────────

    def _build_message_log_panel(self) -> QWidget:
        card = CardFrame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        layout.addWidget(SectionHeader("Live Pub-Sub Message Payload Log", C["pink"]))

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setStyleSheet(
            f"background-color: {C['bg1']}; color: #8495a6; "
            f"border: 1px solid {C['border']}; font-size: 11px;"
        )

        layout.addWidget(self._log_text)
        return card

    # ══════════════════════════════════════════════════════════════
    #  SIGNAL HANDLERS
    # ══════════════════════════════════════════════════════════════

    def _on_connected(self):
        self._header_conn_indicator.set_color(C["green"])
        self._header_conn_label.setText("CONNECTED TO BROKER")
        self._header_conn_label.setStyleSheet(f"color: {C['green']};")
        self._health_heartbeat.set_value("✔ NOMINAL", C["green"])

    def _on_disconnected(self):
        self._header_conn_indicator.set_color(C["red"])
        self._header_conn_label.setText("DISCONNECTED FROM BROKER")
        self._header_conn_label.setStyleSheet(f"color: {C['red']};")
        self._health_heartbeat.set_value("---", C["txt2"])

    def _on_error(self, err: str):
        pass

    def _on_stats_updated(self, stats: dict):
        self._stat_packets.set_value(str(stats.get("packets_received", 0)))
        self._stat_bytes.set_value(str(stats.get("bytes_received", 0)))
        self._stat_rate.set_value(f"{stats.get('data_rate_in', 0.0):.1f} B/s")
        self._stat_errors.set_value(str(stats.get("errors", 0)))

        self._health_reconnects.set_value(str(stats.get("reconnect_count", 0)))
        self._health_uptime.set_value(stats.get("uptime", "---"))

    def _on_message_received(self, topic: str, message: dict):
        """Route incoming messages to update fields in real-time."""
        payload = message.get("payload", {})
        source = message.get("source", "---")
        ts = message.get("timestamp", "")

        # 1. Update Topic monitor
        if topic in self._topic_counts:
            self._topic_counts[topic] += 1
            self._topic_last_times[topic] = datetime.now().strftime("%H:%M:%S")
            self._refresh_topic_table()

        # 2. Append to payload log
        pretty_payload = json.dumps(payload, separators=(",", ":"))
        self._log_text.append(
            f'<span style="color:{C["txt2"]};">[{ts[-12:-4]}]</span> '
            f'<span style="color:{C["cyan"]};">{topic}</span> '
            f'<span style="color:#ffffff;">({source}):</span> '
            f'<span style="color:#a7f3d0;">{pretty_payload[:120]}</span>'
        )
        if self._log_text.document().blockCount() > 500:
            cursor = self._log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 50)
            cursor.removeSelectedText()

        # 3. Route specific topics to UI panels
        if topic == "patient_vitals":
            self._update_vitals(payload)
        elif topic == "robot_telemetry":
            self._update_telemetry(payload)
        elif topic == "alerts":
            self._add_alert_row(ts, payload)

    def _on_client_list(self, clients: list):
        """Update clients list table."""
        self._clients_table.setRowCount(0)
        for c in clients:
            row = self._clients_table.rowCount()
            self._clients_table.insertRow(row)

            name_item = QTableWidgetItem(c.get("name", "---"))
            name_item.setForeground(QColor(C["txt0"]))
            self._clients_table.setItem(row, 0, name_item)

            pub_item = QTableWidgetItem(", ".join(c.get("publish_topics", [])))
            pub_item.setForeground(QColor(C["cyan"]))
            self._clients_table.setItem(row, 1, pub_item)

            sub_item = QTableWidgetItem(", ".join(c.get("subscriptions", [])))
            sub_item.setForeground(QColor(C["green"]))
            self._clients_table.setItem(row, 2, sub_item)

    # ══════════════════════════════════════════════════════════════
    #  PANEL CONTENT UPDATERS
    # ══════════════════════════════════════════════════════════════

    def _update_vitals(self, payload: dict):
        """Update Patient Vitals panel."""
        for name, key in [("HR", "heart_rate"), ("SpO₂", "spo2"),
                          ("BP", "blood_pressure"), ("RR", "respiration"),
                          ("Temp", "temperature")]:
            val = payload.get(key, "---")
            if val != "---" and key in ("heart_rate", "respiration"):
                val = f"{int(val)}"
            self._vital_widgets[name].setText(str(val))

        ecg = payload.get("ecg_status", "---")
        self._ecg_status.setText(ecg)
        if "normal" in ecg.lower():
            self._ecg_status.setStyleSheet(f"color: {C['green']}; font-weight: bold;")
        else:
            self._ecg_status.setStyleSheet(f"color: {C['red']}; font-weight: bold;")

    def _update_telemetry(self, payload: dict):
        """Update Robot Telemetry panel."""
        # Joint angles
        ja = payload.get("joint_angles", {})
        for i in range(6):
            val = ja.get(f"j{i+1}", 0.0)
            self._joint_labels[i].set_value(f"{val:.2f}°")

        # End Effector state
        tp = payload.get("tool_position", {})
        self._telem_pos_x.set_value(f"{tp.get('x', 0.0):.2f} mm")
        self._telem_pos_y.set_value(f"{tp.get('y', 0.0):.2f} mm")
        self._telem_pos_z.set_value(f"{tp.get('z', 0.0):.2f} mm")

        self._telem_rot.set_value(f"{payload.get('end_effector_rotation', 0.0):.2f}°")
        self._telem_force.set_value(f"{payload.get('force', 0.0):.2f} N")
        self._telem_cpu.set_value(f"{payload.get('cpu_usage', 0.0):.1f}%")

        # Network latency
        lat = payload.get("latency", 0.0)
        self._health_latency.set_value(f"{lat:.2f} ms")

    def _add_alert_row(self, timestamp: str, alert: dict):
        """Add safety alert to alerts panel."""
        row = 0
        self._alerts_table.insertRow(row)

        ts_item = QTableWidgetItem(timestamp[-12:-4])
        ts_item.setForeground(QColor(C["txt2"]))
        self._alerts_table.setItem(row, 0, ts_item)

        sev = alert.get("severity", "INFO")
        sev_colors = {"CRITICAL": C["red"], "WARNING": C["amber"], "INFO": C["cyan"]}
        color = sev_colors.get(sev, C["txt1"])

        sev_item = QTableWidgetItem(sev)
        sev_item.setForeground(QColor(color))
        sev_item.setFont(QFont("JetBrains Mono", 9, QFont.Weight.Bold))
        self._alerts_table.setItem(row, 1, sev_item)

        src_item = QTableWidgetItem(alert.get("source", "---"))
        src_item.setForeground(QColor(C["txt1"]))
        self._alerts_table.setItem(row, 2, src_item)

        msg_item = QTableWidgetItem(alert.get("message", "---"))
        msg_item.setForeground(QColor(C["txt0"]))
        self._alerts_table.setItem(row, 3, msg_item)

        # Keep max 50 rows
        while self._alerts_table.rowCount() > 50:
            self._alerts_table.removeRow(self._alerts_table.rowCount() - 1)

    # ── Refresh Topic Table ───────────────────────────────────────

    def _refresh_topic_table(self):
        """Re-render the topic traffic monitor table."""
        self._topic_table.setRowCount(0)
        for topic, count in self._topic_counts.items():
            row = self._topic_table.rowCount()
            self._topic_table.insertRow(row)

            topic_item = QTableWidgetItem(topic)
            topic_item.setForeground(QColor(C["cyan"]))
            self._topic_table.setItem(row, 0, topic_item)

            count_item = QTableWidgetItem(str(count))
            count_item.setForeground(QColor(C["txt0"]))
            self._topic_table.setItem(row, 1, count_item)

            last_time = self._topic_last_times.get(topic, "---")
            time_item = QTableWidgetItem(last_time)
            time_item.setForeground(QColor(C["txt2"]))
            self._topic_table.setItem(row, 2, time_item)

    # ══════════════════════════════════════════════════════════════
    #  CLEANUP
    # ══════════════════════════════════════════════════════════════

    def closeEvent(self, event):
        self._list_timer.stop()
        self._clock_timer.stop()
        self._conn_mgr.cleanup()
        event.accept()
