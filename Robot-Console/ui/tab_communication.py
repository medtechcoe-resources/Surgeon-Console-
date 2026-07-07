# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — COMMUNICATION CENTER TAB
#  The most complex tab: connection controls, data transmission,
#  JSON viewer, and timestamped communication log.
# ═══════════════════════════════════════════════════════════════════

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QTextCharFormat
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QPushButton, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QSizePolicy, QAbstractItemView,
)

from constants import C, TCP_HOST, TCP_PORT
from ui.widgets import (
    CardFrame, SectionHeader, StatusBadge, StatusIndicator, MetricCard,
)
from networking.protocol import format_json_pretty


class CommunicationTab(QWidget):
    """Communication Center — connection controls, data transmission
    stats, JSON viewer, and full communication log."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {C['bg0']};")

        # Callbacks set by main_window
        self.on_connect = None
        self.on_disconnect = None

        self._log_entries = []

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # ── TOP ROW: Connection Panel + Data Transmission ─────────
        top_layout = QHBoxLayout()
        top_layout.setSpacing(6)

        # Connection Panel
        conn_widget = QWidget()
        conn_layout = QVBoxLayout(conn_widget)
        conn_layout.setContentsMargins(0, 0, 0, 0)
        conn_layout.setSpacing(4)

        conn_layout.addWidget(SectionHeader(
            "CONNECTION PANEL", C["cyan"]))

        conn_card = CardFrame()
        cc_layout = QVBoxLayout(conn_card)
        cc_layout.setContentsMargins(12, 10, 12, 10)
        cc_layout.setSpacing(8)

        # Status indicator row
        status_row = QHBoxLayout()
        self._conn_indicator = StatusIndicator(C["red"], size=12)
        status_row.addWidget(self._conn_indicator)

        self._conn_status_label = QLabel("DISCONNECTED")
        self._conn_status_label.setFont(
            QFont("Consolas", 11, QFont.Weight.Bold))
        self._conn_status_label.setStyleSheet(
            f"color: {C['red']}; border: none;")
        status_row.addWidget(self._conn_status_label)
        status_row.addStretch()
        cc_layout.addLayout(status_row)

        # Host input
        host_row = QHBoxLayout()
        host_lbl = QLabel("HOST :")
        host_lbl.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        host_lbl.setStyleSheet(f"color: {C['txt1']};")
        host_row.addWidget(host_lbl)

        self._host_input = QLineEdit(TCP_HOST)
        self._host_input.setFont(QFont("Consolas", 10))
        host_row.addWidget(self._host_input)
        cc_layout.addLayout(host_row)

        # Port input
        port_row = QHBoxLayout()
        port_lbl = QLabel("PORT :")
        port_lbl.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        port_lbl.setStyleSheet(f"color: {C['txt1']};")
        port_row.addWidget(port_lbl)

        self._port_input = QLineEdit(str(TCP_PORT))
        self._port_input.setFont(QFont("Consolas", 10))
        self._port_input.setFixedWidth(80)
        port_row.addWidget(self._port_input)
        port_row.addStretch()
        cc_layout.addLayout(port_row)

        # Connect / Disconnect buttons
        btn_row = QHBoxLayout()

        self._connect_btn = QPushButton("▶  CONNECT")
        self._connect_btn.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        self._connect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['green']};
                color: white;
                padding: 10px 16px;
            }}
            QPushButton:hover {{
                background-color: {C['teal']};
            }}
        """)
        self._connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._connect_btn.clicked.connect(self._on_connect_clicked)
        btn_row.addWidget(self._connect_btn)

        self._disconnect_btn = QPushButton("⏹  DISCONNECT")
        self._disconnect_btn.setFont(
            QFont("Consolas", 9, QFont.Weight.Bold))
        self._disconnect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['red']};
                color: white;
                padding: 10px 16px;
            }}
            QPushButton:hover {{
                background-color: #c0392b;
            }}
        """)
        self._disconnect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._disconnect_btn.setEnabled(False)
        self._disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        btn_row.addWidget(self._disconnect_btn)

        cc_layout.addLayout(btn_row)

        # Reconnect button
        self._reconnect_btn = QPushButton("↻  RECONNECT")
        self._reconnect_btn.setFont(
            QFont("Consolas", 9, QFont.Weight.Bold))
        self._reconnect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['amber']};
                color: white;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #b8740a;
            }}
        """)
        self._reconnect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reconnect_btn.setEnabled(False)
        self._reconnect_btn.clicked.connect(self._on_reconnect_clicked)
        cc_layout.addWidget(self._reconnect_btn)

        conn_layout.addWidget(conn_card)
        top_layout.addWidget(conn_widget, stretch=1)

        # Data Transmission Panel
        data_widget = QWidget()
        data_layout = QVBoxLayout(data_widget)
        data_layout.setContentsMargins(0, 0, 0, 0)
        data_layout.setSpacing(4)

        data_layout.addWidget(SectionHeader(
            "DATA TRANSMISSION", C["teal"]))

        data_grid = QGridLayout()
        data_grid.setSpacing(4)

        self._sent_count = MetricCard(
            "SENT MESSAGES", "0", "packets", C["cyan"])
        data_grid.addWidget(self._sent_count, 0, 0)

        self._recv_count = MetricCard(
            "RECEIVED MESSAGES", "0", "packets", C["green"])
        data_grid.addWidget(self._recv_count, 0, 1)

        self._throughput_in = MetricCard(
            "THROUGHPUT IN", "0.0", "bytes/sec", C["green"])
        data_grid.addWidget(self._throughput_in, 1, 0)

        self._throughput_out = MetricCard(
            "THROUGHPUT OUT", "0.0", "bytes/sec", C["cyan"])
        data_grid.addWidget(self._throughput_out, 1, 1)

        data_layout.addLayout(data_grid)
        top_layout.addWidget(data_widget, stretch=1)

        main_layout.addLayout(top_layout)

        # ── MIDDLE: JSON Viewer ───────────────────────────────────
        main_layout.addWidget(SectionHeader(
            "JSON VIEWER", C["violet"]))

        json_layout = QHBoxLayout()
        json_layout.setSpacing(6)

        # Last Sent JSON
        sent_widget = QWidget()
        sw_layout = QVBoxLayout(sent_widget)
        sw_layout.setContentsMargins(0, 0, 0, 0)
        sw_layout.setSpacing(2)

        sent_hdr = QLabel("  LAST SENT JSON")
        sent_hdr.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        sent_hdr.setStyleSheet(
            f"color: {C['cyan']}; background-color: {C['bg3']};"
            f" padding: 4px;")
        sw_layout.addWidget(sent_hdr)

        self._sent_json = QTextEdit()
        self._sent_json.setReadOnly(True)
        self._sent_json.setFont(QFont("Consolas", 9))
        self._sent_json.setPlaceholderText("No data sent yet...")
        self._sent_json.setMaximumHeight(200)
        sw_layout.addWidget(self._sent_json)

        json_layout.addWidget(sent_widget, stretch=1)

        # Last Received JSON
        recv_widget = QWidget()
        rw_layout = QVBoxLayout(recv_widget)
        rw_layout.setContentsMargins(0, 0, 0, 0)
        rw_layout.setSpacing(2)

        recv_hdr = QLabel("  LAST RECEIVED JSON")
        recv_hdr.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        recv_hdr.setStyleSheet(
            f"color: {C['green']}; background-color: {C['bg3']};"
            f" padding: 4px;")
        rw_layout.addWidget(recv_hdr)

        self._recv_json = QTextEdit()
        self._recv_json.setReadOnly(True)
        self._recv_json.setFont(QFont("Consolas", 9))
        self._recv_json.setPlaceholderText("No data received yet...")
        self._recv_json.setMaximumHeight(200)
        rw_layout.addWidget(self._recv_json)

        json_layout.addWidget(recv_widget, stretch=1)

        main_layout.addLayout(json_layout)

        # ── BOTTOM: Communication Log ─────────────────────────────
        main_layout.addWidget(SectionHeader(
            "COMMUNICATION LOG", C["amber"]))

        self._log_table = QTableWidget()
        self._log_table.setColumnCount(4)
        self._log_table.setHorizontalHeaderLabels(
            ["TIMESTAMP", "TYPE", "DIRECTION", "DETAILS"])
        self._log_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch)
        self._log_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        self._log_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)
        self._log_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents)
        self._log_table.verticalHeader().setVisible(False)
        self._log_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self._log_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self._log_table.setAlternatingRowColors(True)
        self._log_table.setStyleSheet(f"""
            QTableWidget {{
                alternate-background-color: {C['bg1']};
            }}
        """)

        main_layout.addWidget(self._log_table, stretch=1)

    # ─── Button Handlers ──────────────────────────────────────────

    def _on_connect_clicked(self):
        if self.on_connect:
            host = self._host_input.text().strip()
            port = int(self._port_input.text().strip())
            self.on_connect(host, port)

    def _on_disconnect_clicked(self):
        if self.on_disconnect:
            self.on_disconnect()

    def _on_reconnect_clicked(self):
        if self.on_disconnect and self.on_connect:
            self.on_disconnect()
            host = self._host_input.text().strip()
            port = int(self._port_input.text().strip())
            self.on_connect(host, port)

    # ─── Public Update Methods ────────────────────────────────────

    def set_connected(self, connected: bool):
        """Update UI for connection state change."""
        if connected:
            self._conn_indicator.set_color(C["green"])
            self._conn_status_label.setText("CONNECTED")
            self._conn_status_label.setStyleSheet(
                f"color: {C['green']}; border: none;")
            self._connect_btn.setEnabled(False)
            self._disconnect_btn.setEnabled(True)
            self._reconnect_btn.setEnabled(True)
            self._host_input.setEnabled(False)
            self._port_input.setEnabled(False)
        else:
            self._conn_indicator.set_color(C["red"])
            self._conn_status_label.setText("DISCONNECTED")
            self._conn_status_label.setStyleSheet(
                f"color: {C['red']}; border: none;")
            self._connect_btn.setEnabled(True)
            self._disconnect_btn.setEnabled(False)
            self._reconnect_btn.setEnabled(False)
            self._host_input.setEnabled(True)
            self._port_input.setEnabled(True)

    def update_sent_json(self, message: dict):
        """Update the last-sent JSON viewer."""
        self._sent_json.setPlainText(format_json_pretty(message))

    def update_received_json(self, message: dict):
        """Update the last-received JSON viewer."""
        self._recv_json.setPlainText(format_json_pretty(message))

    def update_stats(self, stats: dict):
        """Update data transmission statistics."""
        self._sent_count.set_value(
            str(stats.get("packets_sent", 0)))
        self._recv_count.set_value(
            str(stats.get("packets_received", 0)))
        self._throughput_in.set_value(
            f"{stats.get('data_rate_in', 0.0):.1f}")
        self._throughput_out.set_value(
            f"{stats.get('data_rate_out', 0.0):.1f}")

    def add_log_entry(self, level: str, message: str):
        """Add a timestamped log entry to the table."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Determine direction and colour
        if "sent" in message.lower() or "send" in message.lower():
            direction = "OUT →"
        elif "received" in message.lower() or "recv" in message.lower():
            direction = "← IN"
        elif "connect" in message.lower():
            direction = "SYS"
        else:
            direction = "SYS"

        level_colors = {
            "INFO": C["cyan"],
            "WARNING": C["amber"],
            "ERROR": C["red"],
        }
        color = level_colors.get(level, C["txt1"])

        row = self._log_table.rowCount()
        self._log_table.insertRow(row)

        ts_item = QTableWidgetItem(timestamp)
        ts_item.setForeground(QColor(C["txt2"]))
        self._log_table.setItem(row, 0, ts_item)

        type_item = QTableWidgetItem(level)
        type_item.setForeground(QColor(color))
        type_item.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        self._log_table.setItem(row, 1, type_item)

        dir_item = QTableWidgetItem(direction)
        dir_item.setForeground(QColor(C["txt1"]))
        self._log_table.setItem(row, 2, dir_item)

        msg_item = QTableWidgetItem(message)
        msg_item.setForeground(QColor(C["txt0"]))
        self._log_table.setItem(row, 3, msg_item)

        # Auto-scroll to bottom
        self._log_table.scrollToBottom()

        # Keep max 500 rows
        while self._log_table.rowCount() > 500:
            self._log_table.removeRow(0)
