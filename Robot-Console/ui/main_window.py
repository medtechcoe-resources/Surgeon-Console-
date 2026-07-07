# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — MAIN WINDOW
#  The central QMainWindow that assembles the top bar, tab widget,
#  and wires all services together.
# ═══════════════════════════════════════════════════════════════════

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTabWidget, QApplication,
)

from constants import C, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE
from styles import generate_stylesheet
from networking.tcp_client import TCPClient
from networking.protocol import MSG_ROBOT_TELEMETRY, MSG_VITALS_DATA, MSG_ALERT
from services.telemetry_generator import TelemetryGenerator
from services.alert_generator import AlertGenerator
from services.connection_monitor import ConnectionMonitor
from ui.tab_dashboard import DashboardTab
from ui.tab_patient_vitals import PatientVitalsTab
from ui.tab_robot_telemetry import RobotTelemetryTab
from ui.tab_communication import CommunicationTab
from ui.tab_alerts import AlertsTab
from ui.widgets import StatusBadge, StatusIndicator


class MainWindow(QMainWindow):
    """Robot Console main window — assembles the top bar, 5 tabs,
    and connects all background services."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(1280, 720)

        # Apply global stylesheet
        self.setStyleSheet(generate_stylesheet())

        # ── Initialise Services ───────────────────────────────────
        self._tcp_client = TCPClient(self)
        self._telemetry_gen = TelemetryGenerator(self)
        self._alert_gen = AlertGenerator(self)
        self._conn_monitor = ConnectionMonitor(self)
        self._conn_monitor.set_client(self._tcp_client)

        # ── Build UI ──────────────────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        self._main_layout = QVBoxLayout(central)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self._build_topbar()
        self._build_tabs()

        # ── Wire Signals ──────────────────────────────────────────
        self._connect_signals()

        # ── Start Services ────────────────────────────────────────
        self._start_services()

        # ── Clock ─────────────────────────────────────────────────
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start()
        self._update_clock()

    # ══════════════════════════════════════════════════════════════
    #  TOP BAR
    # ══════════════════════════════════════════════════════════════

    def _build_topbar(self):
        """Build the top bar matching the Surgeon Console design."""
        topbar = QWidget()
        topbar.setFixedHeight(56)
        topbar.setStyleSheet(f"background-color: {C['bg2']};")

        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(16, 0, 16, 0)
        tb_layout.setSpacing(0)

        # Title
        title = QLabel("  ROBOT CONSOLE")
        title.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C['txt0']};")
        tb_layout.addWidget(title)

        version = QLabel("  MEDROBOT OS v4.2")
        version.setFont(QFont("Consolas", 9))
        version.setStyleSheet(f"color: {C['txt2']};")
        tb_layout.addWidget(version)

        tb_layout.addStretch()

        # Connection status indicator
        self._topbar_conn_indicator = StatusIndicator(C["red"], size=10)
        tb_layout.addWidget(self._topbar_conn_indicator)
        tb_layout.addSpacing(4)

        self._topbar_conn_label = QLabel("DISCONNECTED")
        self._topbar_conn_label.setFont(
            QFont("Consolas", 8, QFont.Weight.Bold))
        self._topbar_conn_label.setStyleSheet(f"color: {C['red']};")
        tb_layout.addWidget(self._topbar_conn_label)
        tb_layout.addSpacing(16)

        # Robot status badge
        self._topbar_robot_badge = StatusBadge("IDLE", C["txt2"])
        tb_layout.addWidget(self._topbar_robot_badge)
        tb_layout.addSpacing(16)

        # Alert badge
        self._topbar_alert_badge = StatusBadge("0", C["txt2"])
        self._topbar_alert_badge.setVisible(False)
        tb_layout.addWidget(self._topbar_alert_badge)
        tb_layout.addSpacing(16)

        # Clock
        clock_frame = QWidget()
        clock_frame.setStyleSheet(
            f"background-color: {C['cyan']}; padding: 4px 10px;")
        cf_layout = QHBoxLayout(clock_frame)
        cf_layout.setContentsMargins(10, 4, 10, 4)

        self._clock_label = QLabel("--:--:--")
        self._clock_label.setFont(QFont("Consolas", 13, QFont.Weight.Bold))
        self._clock_label.setStyleSheet("color: white;")
        cf_layout.addWidget(self._clock_label)

        tb_layout.addWidget(clock_frame)

        self._main_layout.addWidget(topbar)

        # Cyan accent line (matches Surgeon Console)
        accent = QFrame()
        accent.setFixedHeight(3)
        accent.setStyleSheet(f"background-color: {C['cyan']};")
        self._main_layout.addWidget(accent)

        border = QFrame()
        border.setFixedHeight(1)
        border.setStyleSheet(f"background-color: {C['border']};")
        self._main_layout.addWidget(border)

    # ══════════════════════════════════════════════════════════════
    #  TABS
    # ══════════════════════════════════════════════════════════════

    def _build_tabs(self):
        """Build the 5 main tabs."""
        self._tab_widget = QTabWidget()
        self._tab_widget.setDocumentMode(True)

        # Create tab instances
        self._dashboard_tab = DashboardTab()
        self._vitals_tab = PatientVitalsTab()
        self._telemetry_tab = RobotTelemetryTab()
        self._comm_tab = CommunicationTab()
        self._alerts_tab = AlertsTab()

        # Wire comm tab buttons
        self._comm_tab.on_connect = self._on_connect
        self._comm_tab.on_disconnect = self._on_disconnect

        # Add tabs
        self._tab_widget.addTab(self._dashboard_tab, "  DASHBOARD  ")
        self._tab_widget.addTab(self._vitals_tab, "  PATIENT VITALS  ")
        self._tab_widget.addTab(self._telemetry_tab, "  ROBOT TELEMETRY  ")
        self._tab_widget.addTab(self._comm_tab, "  COMMUNICATION CENTER  ")
        self._tab_widget.addTab(self._alerts_tab, "  ALERTS  ")

        self._main_layout.addWidget(self._tab_widget)

    # ══════════════════════════════════════════════════════════════
    #  SIGNAL WIRING
    # ══════════════════════════════════════════════════════════════

    def _connect_signals(self):
        """Connect all service signals to UI update slots."""

        # TCP Client signals
        self._tcp_client.connected.connect(self._on_connected)
        self._tcp_client.disconnected.connect(self._on_disconnected)
        self._tcp_client.data_received.connect(self._on_data_received)
        self._tcp_client.data_sent.connect(self._on_data_sent)
        self._tcp_client.error_occurred.connect(self._on_tcp_error)
        self._tcp_client.log_message.connect(self._on_log_message)
        self._tcp_client.stats_updated.connect(self._on_stats_updated)

        # Telemetry generator signals
        self._telemetry_gen.telemetry_updated.connect(
            self._on_telemetry_updated)

        # Alert generator signals
        self._alert_gen.alert_generated.connect(self._on_alert_generated)

        # Connection monitor signals
        self._conn_monitor.stats_updated.connect(self._on_stats_updated)

    # ══════════════════════════════════════════════════════════════
    #  SERVICE MANAGEMENT
    # ══════════════════════════════════════════════════════════════

    def _start_services(self):
        """Start background services."""
        self._telemetry_gen.start()
        self._alert_gen.start()
        self._conn_monitor.start()

    def _stop_services(self):
        """Stop all background services."""
        self._telemetry_gen.stop()
        self._alert_gen.stop()
        self._conn_monitor.stop()
        self._tcp_client.disconnect_from_server()

    # ══════════════════════════════════════════════════════════════
    #  CONNECTION HANDLERS
    # ══════════════════════════════════════════════════════════════

    def _on_connect(self, host: str, port: int):
        """Handle connect button click from Communication tab."""
        self._tcp_client.connect_to_server(host, port)

    def _on_disconnect(self):
        """Handle disconnect button click."""
        self._tcp_client.disconnect_from_server()

    def _on_connected(self):
        """TCP connection established."""
        self._comm_tab.set_connected(True)
        self._topbar_conn_indicator.set_color(C["green"])
        self._topbar_conn_label.setText("CONNECTED")
        self._topbar_conn_label.setStyleSheet(f"color: {C['green']};")
        self._topbar_robot_badge.set_text_and_color("ACTIVE", C["green"])

    def _on_disconnected(self):
        """TCP connection lost."""
        self._comm_tab.set_connected(False)
        self._topbar_conn_indicator.set_color(C["red"])
        self._topbar_conn_label.setText("DISCONNECTED")
        self._topbar_conn_label.setStyleSheet(f"color: {C['red']};")

    # ══════════════════════════════════════════════════════════════
    #  DATA HANDLERS
    # ══════════════════════════════════════════════════════════════

    def _on_data_received(self, message: dict):
        """Handle data received from the Surgeon Console."""
        msg_type = message.get("type", "")

        # Update JSON viewer
        self._comm_tab.update_received_json(message)

        # Route by message type
        if msg_type == MSG_VITALS_DATA:
            self._vitals_tab.update_vitals(message)

        # Log the receive
        self._comm_tab.add_log_entry(
            "INFO", f"Received {msg_type} packet")

    def _on_data_sent(self, message: dict):
        """Handle data sent confirmation."""
        msg_type = message.get("type", "")
        self._comm_tab.update_sent_json(message)
        self._comm_tab.add_log_entry(
            "INFO", f"Sent {msg_type} packet")

    def _on_tcp_error(self, error: str):
        """Handle TCP error."""
        self._comm_tab.add_log_entry("ERROR", error)

    def _on_log_message(self, level: str, message: str):
        """Handle log message from TCP client."""
        self._comm_tab.add_log_entry(level, message)

    def _on_stats_updated(self, stats: dict):
        """Handle updated connection statistics."""
        self._dashboard_tab.update_connection_stats(stats)
        self._comm_tab.update_stats(stats)

    # ══════════════════════════════════════════════════════════════
    #  TELEMETRY HANDLER
    # ══════════════════════════════════════════════════════════════

    def _on_telemetry_updated(self, telemetry):
        """Handle new telemetry data from the generator."""
        # Update telemetry tab
        self._telemetry_tab.update_telemetry(
            telemetry, self._telemetry_gen.joint_history)

        # Send over TCP if connected
        if self._tcp_client.is_connected:
            self._tcp_client.send_data(
                MSG_ROBOT_TELEMETRY, telemetry.to_dict())

    # ══════════════════════════════════════════════════════════════
    #  ALERT HANDLER
    # ══════════════════════════════════════════════════════════════

    def _on_alert_generated(self, alert):
        """Handle new alert from the generator."""
        # Update alerts tab
        self._alerts_tab.add_alert(alert)

        # Update topbar badge
        total = len(self._alert_gen.alerts)
        critical = sum(1 for a in self._alert_gen.alerts
                      if a.severity == "CRITICAL")
        if critical > 0:
            self._topbar_alert_badge.set_text_and_color(
                f" {total} ", C["red"])
        elif total > 0:
            self._topbar_alert_badge.set_text_and_color(
                f" {total} ", C["amber"])
        self._topbar_alert_badge.setVisible(total > 0)

        # Send alert over TCP if connected
        if self._tcp_client.is_connected:
            self._tcp_client.send_data(MSG_ALERT, alert.to_dict())

    # ══════════════════════════════════════════════════════════════
    #  CLOCK
    # ══════════════════════════════════════════════════════════════

    def _update_clock(self):
        """Update the topbar clock."""
        self._clock_label.setText(
            datetime.now().strftime("%H:%M:%S"))

    # ══════════════════════════════════════════════════════════════
    #  CLEANUP
    # ══════════════════════════════════════════════════════════════

    def closeEvent(self, event):
        """Clean up services on window close."""
        self._stop_services()
        event.accept()
