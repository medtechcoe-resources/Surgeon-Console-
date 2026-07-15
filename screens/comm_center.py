"""
Comm Center tab — Surgeon Console communication hub.
Provides connection status, data-source status, subscribe status,
live message monitor, packet statistics, connection info, and comm log.

All data (patient_vitals, robot_telemetry, alerts) is now produced
by the standalone Data Generator backend console.
This console subscribes to: robot_telemetry, alerts, connection_status, system_status
"""
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QPushButton, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from widgets.card import MetricCard, PanelFrame
from theme_manager import ThemeManager


class CommCenterScreen(QWidget):
    """Communication Center screen for the Surgeon Console."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._conn_manager = None
        self._message_count = 0

        # Stats tracking
        self._topic_stats = {}
        self._log_entries = []

        self._build_ui()

    # ══════════════════════════════════════════════════════════════
    #  UI BUILD
    # ══════════════════════════════════════════════════════════════

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        main = QVBoxLayout(container)
        main.setContentsMargins(0, 14, 0, 14)
        main.setSpacing(16)

        # ── Row 1: Connection + Publish + Subscribe ───────────────
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        row1.addWidget(self._build_connection_panel(), 1)
        row1.addWidget(self._build_publish_panel(), 1)
        row1.addWidget(self._build_subscribe_panel(), 1)

        main.addLayout(row1)

        # ── Row 2: Packet Stats + Connection Info ─────────────────
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        row2.addWidget(self._build_packet_stats_panel(), 2)
        row2.addWidget(self._build_connection_info_panel(), 1)

        main.addLayout(row2)

        # ── Row 3: Live Message Monitor ───────────────────────────
        main.addWidget(self._build_message_monitor_panel(), 1)

        # ── Row 4: Communication Log ──────────────────────────────
        main.addWidget(self._build_comm_log_panel(), 1)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── Connection Panel ──────────────────────────────────────────

    def _build_connection_panel(self) -> QWidget:
        panel = PanelFrame("Connection Status")

        # Status indicator
        status_row = QHBoxLayout()
        self._conn_dot = QFrame()
        self._conn_dot.setFixedSize(14, 14)
        self._conn_dot.setStyleSheet(
            "background-color: #EF4444; border-radius: 7px;")
        status_row.addWidget(self._conn_dot)

        self._conn_label = QLabel("DISCONNECTED")
        self._conn_label.setObjectName("CardValue")
        self._conn_label.setStyleSheet(
            "color: #EF4444; font-size: 18px; font-weight: 700;")
        status_row.addWidget(self._conn_label)
        status_row.addStretch()
        panel.add_layout(status_row)

        # Host/Port inputs
        host_row = QHBoxLayout()
        host_lbl = QLabel("BROKER HOST")
        host_lbl.setObjectName("FieldLabel")
        host_lbl.setFixedWidth(120)
        self._host_input = QLineEdit("127.0.0.1")
        self._host_input.setStyleSheet(
            "background-color: #161B22; color: #E6EDF3; "
            "border: 1px solid #2D3748; padding: 8px; border-radius: 6px; "
            "font-size: 14px;")
        host_row.addWidget(host_lbl)
        host_row.addWidget(self._host_input)
        panel.add_layout(host_row)

        port_row = QHBoxLayout()
        port_lbl = QLabel("PORT")
        port_lbl.setObjectName("FieldLabel")
        port_lbl.setFixedWidth(120)
        self._port_input = QLineEdit("5000")
        self._port_input.setFixedWidth(100)
        self._port_input.setStyleSheet(
            "background-color: #161B22; color: #E6EDF3; "
            "border: 1px solid #2D3748; padding: 8px; border-radius: 6px; "
            "font-size: 14px;")
        port_row.addWidget(port_lbl)
        port_row.addWidget(self._port_input)
        port_row.addStretch()
        panel.add_layout(port_row)

        # Buttons
        btn_row = QHBoxLayout()
        self._connect_btn = QPushButton("CONNECT")
        self._connect_btn.setProperty("class", "PrimaryButton")
        self._connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._connect_btn.clicked.connect(self._on_connect)
        btn_row.addWidget(self._connect_btn)

        self._disconnect_btn = QPushButton("DISCONNECT")
        self._disconnect_btn.setProperty("class", "DangerButton")
        self._disconnect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._disconnect_btn.setEnabled(False)
        self._disconnect_btn.clicked.connect(self._on_disconnect)
        btn_row.addWidget(self._disconnect_btn)
        panel.add_layout(btn_row)

        return panel

    # ── Data Source Panel ─────────────────────────────────────────

    def _build_publish_panel(self) -> QWidget:
        """Shows Data Generator backend status (replaces the old publish panel)."""
        panel = PanelFrame("Data Source — Data Generator")

        # Source label
        src_row = QHBoxLayout()
        src_lbl = QLabel("SOURCE")
        src_lbl.setObjectName("FieldLabel")
        src_val = QLabel("Data Generator Backend")
        src_val.setObjectName("FieldValueBold")
        src_val.setStyleSheet("color: #0095FF; font-size: 14px;")
        src_row.addWidget(src_lbl)
        src_row.addStretch()
        src_row.addWidget(src_val)
        panel.add_layout(src_row)

        # Topics row
        topics_row = QHBoxLayout()
        topics_lbl = QLabel("PUBLISHES")
        topics_lbl.setObjectName("FieldLabel")
        topics_val = QLabel("patient_vitals · robot_telemetry · alerts")
        topics_val.setObjectName("FieldValue")
        topics_val.setStyleSheet("color: #10B981; font-size: 12px;")
        topics_val.setWordWrap(True)
        topics_row.addWidget(topics_lbl)
        topics_row.addSpacing(8)
        topics_row.addWidget(topics_val)
        panel.add_layout(topics_row)

        # Status row
        status_row = QHBoxLayout()
        stat_lbl = QLabel("STATUS")
        stat_lbl.setObjectName("FieldLabel")
        self._datagen_status = QLabel("WAITING FOR BROKER")
        self._datagen_status.setObjectName("FieldValueBold")
        self._datagen_status.setStyleSheet("color: #F59E0B; font-size: 13px;")
        status_row.addWidget(stat_lbl)
        status_row.addStretch()
        status_row.addWidget(self._datagen_status)
        panel.add_layout(status_row)

        # Info note
        note = QLabel(
            "All simulation data is generated by the separate\n"
            "Data Generator backend process.")
        note.setObjectName("CardSub")
        note.setWordWrap(True)
        note.setStyleSheet(
            "color: #6B7B8D; font-size: 12px; "
            "font-family: 'JetBrains Mono', monospace;")
        panel.add_widget(note)

        return panel

    # ── Subscribe Panel ───────────────────────────────────────────

    def _build_subscribe_panel(self) -> QWidget:
        panel = PanelFrame("Subscribe Status")

        topics = [
            ("robot_telemetry", "#8B5CF6"),
            ("alerts", "#EF4444"),
            ("connection_status", "#10B981"),
            ("system_status", "#F59E0B"),
        ]

        self._sub_status_labels = {}
        self._sub_count_labels = {}
        self._sub_time_labels = {}

        for topic, color in topics:
            row = QHBoxLayout()
            row.setContentsMargins(0, 4, 0, 4)

            dot = QFrame()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(
                f"background-color: {color}; border-radius: 5px;")
            row.addWidget(dot)

            name = QLabel(topic)
            name.setObjectName("FieldLabel")
            name.setStyleSheet(f"color: {color}; font-size: 13px;")
            row.addWidget(name)

            row.addStretch()

            count = QLabel("0")
            count.setStyleSheet(
                "color: #E6EDF3; font-size: 13px; font-weight: 600; "
                "font-family: 'JetBrains Mono', monospace;")
            row.addWidget(count)
            self._sub_count_labels[topic] = count

            status = QLabel("WAITING")
            status.setStyleSheet("color: #6B7B8D; font-size: 11px;")
            status.setFixedWidth(80)
            row.addWidget(status)
            self._sub_status_labels[topic] = status

            panel.add_layout(row)
            self._topic_stats[topic] = {"count": 0, "last_time": "---"}

        return panel

    # ── Packet Statistics ─────────────────────────────────────────

    def _build_packet_stats_panel(self) -> QWidget:
        panel = PanelFrame("Packet Statistics")

        grid = QGridLayout()
        grid.setSpacing(12)

        self._stat_sent = MetricCard("PACKETS SENT", "0", "packets",
                                     accent="cyan")
        grid.addWidget(self._stat_sent, 0, 0)

        self._stat_recv = MetricCard("PACKETS RECEIVED", "0", "packets",
                                     accent="green")
        grid.addWidget(self._stat_recv, 0, 1)

        self._stat_bytes_out = MetricCard("BYTES SENT", "0", "bytes")
        grid.addWidget(self._stat_bytes_out, 0, 2)

        self._stat_bytes_in = MetricCard("BYTES RECEIVED", "0", "bytes")
        grid.addWidget(self._stat_bytes_in, 0, 3)

        self._stat_rate_out = MetricCard("THROUGHPUT OUT", "0.0",
                                         "bytes/sec", accent="cyan")
        grid.addWidget(self._stat_rate_out, 1, 0)

        self._stat_rate_in = MetricCard("THROUGHPUT IN", "0.0",
                                        "bytes/sec", accent="green")
        grid.addWidget(self._stat_rate_in, 1, 1)

        self._stat_errors = MetricCard("ERRORS", "0", "total",
                                       accent="red")
        grid.addWidget(self._stat_errors, 1, 2)

        self._stat_reconnects = MetricCard("RECONNECTS", "0", "total")
        grid.addWidget(self._stat_reconnects, 1, 3)

        panel.add_layout(grid)
        return panel

    # ── Connection Info ───────────────────────────────────────────

    def _build_connection_info_panel(self) -> QWidget:
        panel = PanelFrame("Connection Information")

        info_items = [
            ("Client Name", "surgeon_console"),
            ("Broker", "---"),
            ("Protocol", "TCP / JSON"),
            ("Heartbeat", "2 sec"),
            ("Uptime", "---"),
            ("Last Sent", "---"),
            ("Last Received", "---"),
        ]

        self._info_labels = {}
        for label, value in info_items:
            row = QHBoxLayout()
            row.setContentsMargins(0, 3, 0, 3)
            lbl = QLabel(label)
            lbl.setObjectName("FieldLabel")
            val = QLabel(value)
            val.setObjectName("FieldValue")
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            panel.add_layout(row)
            self._info_labels[label] = val

        return panel

    # ── Live Message Monitor ──────────────────────────────────────

    def _build_message_monitor_panel(self) -> QWidget:
        panel = PanelFrame("Live Message Monitor")

        self._msg_table = QTableWidget()
        self._msg_table.setColumnCount(5)
        self._msg_table.setHorizontalHeaderLabels(
            ["TIME", "DIRECTION", "TOPIC", "SOURCE", "PREVIEW"])
        self._msg_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch)
        for col in range(4):
            self._msg_table.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeMode.ResizeToContents)
        self._msg_table.verticalHeader().setVisible(False)
        self._msg_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self._msg_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self._msg_table.setAlternatingRowColors(True)
        self._msg_table.setMaximumHeight(250)

        panel.add_widget(self._msg_table)
        return panel

    # ── Communication Log ─────────────────────────────────────────

    def _build_comm_log_panel(self) -> QWidget:
        panel = PanelFrame("Communication Log")

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(200)
        self._log_text.setStyleSheet(
            "background-color: #131820; color: #B5BEC8; "
            "border: 1px solid #1C2333; border-radius: 8px; "
            "padding: 10px; font-size: 12px; "
            "font-family: 'JetBrains Mono', 'Consolas', monospace;")
        self._log_text.setPlaceholderText(
            "Communication events will appear here...")

        panel.add_widget(self._log_text)
        return panel

    # ══════════════════════════════════════════════════════════════
    #  PUBLIC API — Called by main.py
    # ══════════════════════════════════════════════════════════════

    def set_connection_manager(self, conn_mgr):
        """Attach the shared ConnectionManager instance."""
        self._conn_manager = conn_mgr

        # Wire signals
        conn_mgr.connected.connect(self._on_connected)
        conn_mgr.disconnected.connect(self._on_disconnected)
        conn_mgr.error_occurred.connect(self._on_error)
        conn_mgr.log_message.connect(self._on_log)
        conn_mgr.stats_updated.connect(self._on_stats_updated)
        conn_mgr.message_received.connect(self._on_message_received)

    def _update_datagen_status(self, connected: bool):
        """Update the Data Generator status indicator in the publish panel."""
        if connected:
            self._datagen_status.setText("DATA FLOWING")
            self._datagen_status.setStyleSheet("color: #10B981; font-size: 13px;")
        else:
            self._datagen_status.setText("WAITING FOR DATA GEN")
            self._datagen_status.setStyleSheet("color: #F59E0B; font-size: 13px;")

    # ══════════════════════════════════════════════════════════════
    #  BUTTON HANDLERS
    # ══════════════════════════════════════════════════════════════

    def _on_connect(self):
        if not self._conn_manager:
            return
        host = self._host_input.text().strip()
        port = int(self._port_input.text().strip())
        self._conn_manager.connect_to_broker(host, port)

    def _on_disconnect(self):
        if not self._conn_manager:
            return
        self._conn_manager.disconnect_from_broker()

    # ══════════════════════════════════════════════════════════════
    #  SIGNAL HANDLERS
    # ══════════════════════════════════════════════════════════════

    def _on_connected(self):
        self._conn_dot.setStyleSheet(
            "background-color: #10B981; border-radius: 7px;")
        self._conn_label.setText("CONNECTED")
        self._conn_label.setStyleSheet(
            "color: #10B981; font-size: 18px; font-weight: 700;")
        self._connect_btn.setEnabled(False)
        self._disconnect_btn.setEnabled(True)
        self._host_input.setEnabled(False)
        self._port_input.setEnabled(False)
        self._update_datagen_status(False)

    def _on_disconnected(self):
        self._conn_dot.setStyleSheet(
            "background-color: #EF4444; border-radius: 7px;")
        self._conn_label.setText("DISCONNECTED")
        self._conn_label.setStyleSheet(
            "color: #EF4444; font-size: 18px; font-weight: 700;")
        self._connect_btn.setEnabled(True)
        self._disconnect_btn.setEnabled(False)
        self._host_input.setEnabled(True)
        self._port_input.setEnabled(True)
        self._update_datagen_status(False)

    def _on_error(self, error: str):
        self._add_log("ERROR", error)

    def _on_log(self, level: str, message: str):
        self._add_log(level, message)

    def _on_stats_updated(self, stats: dict):
        self._stat_sent.set_value(str(stats.get("packets_sent", 0)))
        self._stat_recv.set_value(str(stats.get("packets_received", 0)))
        self._stat_bytes_out.set_value(str(stats.get("bytes_sent", 0)))
        self._stat_bytes_in.set_value(str(stats.get("bytes_received", 0)))
        self._stat_rate_out.set_value(
            f"{stats.get('data_rate_out', 0.0):.1f}")
        self._stat_rate_in.set_value(
            f"{stats.get('data_rate_in', 0.0):.1f}")
        self._stat_errors.set_value(str(stats.get("errors", 0)))
        self._stat_reconnects.set_value(
            str(stats.get("reconnect_count", 0)))

        # Connection info
        self._info_labels["Broker"].setText(
            stats.get("remote_address", "---"))
        self._info_labels["Uptime"].setText(stats.get("uptime", "---"))
        self._info_labels["Last Sent"].setText(
            stats.get("last_sent_time", "---"))
        self._info_labels["Last Received"].setText(
            stats.get("last_received_time", "---"))

    def _on_message_received(self, topic: str, message: dict):
        """Handle incoming pub-sub messages."""
        # Update topic stats
        if topic in self._topic_stats:
            self._topic_stats[topic]["count"] += 1
            self._topic_stats[topic]["last_time"] = (
                datetime.now().strftime("%H:%M:%S"))

            if topic in self._sub_count_labels:
                self._sub_count_labels[topic].setText(
                    str(self._topic_stats[topic]["count"]))
            if topic in self._sub_status_labels:
                self._sub_status_labels[topic].setText("ACTIVE")
                self._sub_status_labels[topic].setStyleSheet(
                    "color: #10B981; font-size: 11px;")

        # If we see data from the Data Generator, update status panel
        if topic in ("robot_telemetry", "alerts"):
            self._update_datagen_status(True)

        # Add to message monitor
        self._add_message_row("← IN", topic,
                              message.get("source", "---"),
                              str(message.get("payload", {}))[:100])



    # ══════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════

    def _add_log(self, level: str, message: str):
        """Add a timestamped entry to the communication log."""
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        colors = {"INFO": "#0095FF", "WARNING": "#F59E0B",
                  "ERROR": "#EF4444"}
        color = colors.get(level, "#B5BEC8")
        self._log_text.append(
            f'<span style="color:#6B7B8D;">{ts}</span> '
            f'<span style="color:{color}; font-weight:bold;">'
            f'[{level}]</span> '
            f'<span style="color:#B5BEC8;">{message}</span>')

        # Keep reasonable size
        if self._log_text.document().blockCount() > 500:
            cursor = self._log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down,
                                cursor.MoveMode.KeepAnchor, 100)
            cursor.removeSelectedText()

    def _add_message_row(self, direction: str, topic: str,
                         source: str, preview: str):
        """Add a row to the live message monitor table."""
        row = 0
        self._msg_table.insertRow(row)

        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        items = [ts, direction, topic, source, preview]
        colors = ["#6B7B8D", "#B5BEC8", "#0095FF", "#E6EDF3", "#6B7B8D"]

        for col, (text, color) in enumerate(zip(items, colors)):
            item = QTableWidgetItem(text)
            item.setForeground(QColor(color))
            self._msg_table.setItem(row, col, item)

        # Keep max 200 rows
        while self._msg_table.rowCount() > 200:
            self._msg_table.removeRow(self._msg_table.rowCount() - 1)
