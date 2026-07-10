# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — DASHBOARD TAB
#  Displays an overview of robot status, connection status,
#  TCP statistics, and procedure information.
# ═══════════════════════════════════════════════════════════════════

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
)

from constants import C
from ui.widgets import (
    CardFrame, SectionHeader, StatusBadge, StatusIndicator,
    MetricCard, KeyValueRow,
)


class DashboardTab(QWidget):
    """Dashboard tab showing robot status, connection, TCP stats,
    and current procedure information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {C['bg0']};")
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        # ── Section: Status Overview ──────────────────────────────
        main_layout.addWidget(SectionHeader(
            "STATUS OVERVIEW", C["cyan"]))

        status_grid = QGridLayout()
        status_grid.setSpacing(10)

        # Robot Status Card
        self._robot_status_card = self._build_status_card(
            "ROBOT STATUS", "IDLE", C["txt2"],
            [("Calibration", "✔ VERIFIED", C["green"]),
             ("Safety System", "✔ ARMED", C["green"]),
             ("Servo Power", "✔ ON", C["green"])])
        status_grid.addWidget(self._robot_status_card, 0, 0)

        # Connection Status Card
        self._conn_status_card = self._build_status_card(
            "CONNECTION STATUS", "DISCONNECTED", C["red"],
            [("Server", "127.0.0.1:5000", C["txt1"]),
             ("Protocol", "TCP/JSON", C["txt1"]),
             ("Heartbeat", "---", C["txt2"])])
        status_grid.addWidget(self._conn_status_card, 0, 1)

        # TCP Status Card
        self._tcp_status_card = self._build_status_card(
            "TCP STATUS", "CLOSED", C["red"],
            [("Socket State", "CLOSED", C["red"]),
             ("Latency", "--- ms", C["txt2"]),
             ("Reconnects", "0", C["txt1"])])
        status_grid.addWidget(self._tcp_status_card, 0, 2)

        # Procedure Status Card
        self._procedure_card = self._build_status_card(
            "CURRENT PROCEDURE", "STANDBY", C["amber"],
            [("Procedure", "Laparoscopic Cholecystectomy", C["violet"]),
             ("Phase", "INTRA-OP", C["cyan"]),
             ("Duration", "---", C["txt1"])])
        status_grid.addWidget(self._procedure_card, 0, 3)

        main_layout.addLayout(status_grid)

        # ── Section: Data Transfer ────────────────────────────────
        main_layout.addWidget(SectionHeader(
            "DATA TRANSFER", C["teal"]))

        transfer_grid = QGridLayout()
        transfer_grid.setSpacing(10)

        # Data Transfer Rate Card
        self._rate_card = MetricCard(
            "DATA TRANSFER RATE", "0.0", "bytes/sec", C["teal"])
        transfer_grid.addWidget(self._rate_card, 0, 0)

        # Packet Count Card
        self._packet_card_sent = MetricCard(
            "PACKETS SENT", "0", "packets", C["cyan"])
        transfer_grid.addWidget(self._packet_card_sent, 0, 1)

        self._packet_card_recv = MetricCard(
            "PACKETS RECEIVED", "0", "packets", C["green"])
        transfer_grid.addWidget(self._packet_card_recv, 0, 2)

        self._error_card = MetricCard(
            "ERRORS", "0", "total", C["red"])
        transfer_grid.addWidget(self._error_card, 0, 3)

        main_layout.addLayout(transfer_grid)

        # ── Section: Timing ───────────────────────────────────────
        main_layout.addWidget(SectionHeader(
            "TIMING", C["amber"]))

        timing_grid = QGridLayout()
        timing_grid.setSpacing(10)

        self._last_sent_card = MetricCard(
            "LAST SENT", "---", "", C["amber"])
        timing_grid.addWidget(self._last_sent_card, 0, 0)

        self._last_recv_card = MetricCard(
            "LAST RECEIVED", "---", "", C["amber"])
        timing_grid.addWidget(self._last_recv_card, 0, 1)

        self._rate_in_card = MetricCard(
            "THROUGHPUT IN", "0.0", "bytes/sec", C["green"])
        timing_grid.addWidget(self._rate_in_card, 0, 2)

        self._rate_out_card = MetricCard(
            "THROUGHPUT OUT", "0.0", "bytes/sec", C["cyan"])
        timing_grid.addWidget(self._rate_out_card, 0, 3)

        main_layout.addLayout(timing_grid)

        main_layout.addStretch()

    def _build_status_card(self, title: str, status: str,
                           status_color: str,
                           rows: list) -> CardFrame:
        """Build a status card with a title badge and key-value rows."""
        card = CardFrame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Title bar
        title_bar = QWidget()
        title_bar.setStyleSheet(f"background-color: {C['bg3']};")
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(16, 12, 16, 12)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Consolas", 20, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {C['cyan']};")
        tb_layout.addWidget(title_lbl)

        tb_layout.addStretch()

        self_badge = StatusBadge(status, status_color)
        tb_layout.addWidget(self_badge)

        layout.addWidget(title_bar)

        # Store reference to the badge for updates
        card._status_badge = self_badge

        # Key-value rows
        card._kv_rows = {}
        for key, value, color in rows:
            kv = KeyValueRow(key, value, color)
            layout.addWidget(kv)
            card._kv_rows[key] = kv

        return card

    # ─── Public Update Methods ────────────────────────────────────

    def update_connection_stats(self, stats: dict):
        """Update all dashboard cards from connection statistics."""
        is_connected = stats.get("is_connected", False)

        # Robot Status
        if is_connected:
            self._robot_status_card._status_badge.set_text_and_color(
                "ACTIVE", C["green"])
        else:
            self._robot_status_card._status_badge.set_text_and_color(
                "IDLE", C["txt2"])

        # Connection Status
        if is_connected:
            self._conn_status_card._status_badge.set_text_and_color(
                "CONNECTED", C["green"])
            self._conn_status_card._kv_rows["Heartbeat"].set_value(
                "✔ ALIVE", C["green"])
        else:
            self._conn_status_card._status_badge.set_text_and_color(
                "DISCONNECTED", C["red"])
            self._conn_status_card._kv_rows["Heartbeat"].set_value(
                "---", C["txt2"])

        addr = stats.get("remote_address", "---")
        self._conn_status_card._kv_rows["Server"].set_value(addr)

        # TCP Status
        if is_connected:
            self._tcp_status_card._status_badge.set_text_and_color(
                "ESTABLISHED", C["green"])
            self._tcp_status_card._kv_rows["Socket State"].set_value(
                "ESTABLISHED", C["green"])
        else:
            self._tcp_status_card._status_badge.set_text_and_color(
                "CLOSED", C["red"])
            self._tcp_status_card._kv_rows["Socket State"].set_value(
                "CLOSED", C["red"])

        rc = stats.get("reconnect_count", 0)
        self._tcp_status_card._kv_rows["Reconnects"].set_value(str(rc))

        # Packet counts
        sent = stats.get("packets_sent", 0)
        recv = stats.get("packets_received", 0)
        errors = stats.get("errors", 0)

        self._packet_card_sent.set_value(str(sent))
        self._packet_card_recv.set_value(str(recv))
        self._error_card.set_value(str(errors))
        if errors > 0:
            self._error_card.set_color(C["red"])

        # Timing
        self._last_sent_card.set_value(
            stats.get("last_sent_time", "---"))
        self._last_recv_card.set_value(
            stats.get("last_received_time", "---"))

        # Data rates
        rate_in = stats.get("data_rate_in", 0.0)
        rate_out = stats.get("data_rate_out", 0.0)
        self._rate_in_card.set_value(f"{rate_in:.1f}")
        self._rate_out_card.set_value(f"{rate_out:.1f}")

        total_rate = rate_in + rate_out
        self._rate_card.set_value(f"{total_rate:.1f}")
