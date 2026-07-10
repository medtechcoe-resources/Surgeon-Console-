# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — PUB-SUB BRIDGE SERVICE
#  Adapts the existing Robot Console services to the shared
#  pub-sub networking system. Publishes robot_telemetry, alerts,
#  and connection_status. Subscribes to patient_vitals.
# ═══════════════════════════════════════════════════════════════════

import sys
import os
from datetime import datetime

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

# Ensure the project root is on sys.path for the shared networking package
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from shared_networking.connection_manager import ConnectionManager
from shared_networking.config import BROKER_HOST, BROKER_PORT


class PubSubBridge(QObject):
    """Bridge between Robot Console services and the pub-sub broker.

    Publishes:
        - robot_telemetry (every 1 second)
        - alerts (on generation)
        - connection_status (on connect/disconnect)

    Subscribes:
        - patient_vitals

    Emits Qt signals for received data so existing tabs can
    consume it without modification.
    """

    # Signals for UI tabs to consume
    vitals_received = pyqtSignal(dict)        # patient vitals data
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error_occurred = pyqtSignal(str)
    log_message = pyqtSignal(str, str)        # (level, message)
    stats_updated = pyqtSignal(dict)
    data_received = pyqtSignal(dict)          # raw message for comm tab
    data_sent = pyqtSignal(dict)              # raw message for comm tab

    def __init__(self, parent=None):
        super().__init__(parent)

        self._conn_manager = ConnectionManager(
            client_name="robot_console",
            publish_topics=["robot_telemetry", "alerts", "connection_status"],
            subscribe_topics=["patient_vitals"],
            parent=self,
        )
        self._conn_manager.enable_auto_reconnect(True)

        # Wire connection manager signals
        self._conn_manager.connected.connect(self._on_connected)
        self._conn_manager.disconnected.connect(self._on_disconnected)
        self._conn_manager.error_occurred.connect(self.error_occurred)
        self._conn_manager.log_message.connect(self.log_message)
        self._conn_manager.stats_updated.connect(self.stats_updated)
        self._conn_manager.message_received.connect(self._on_message)

        # Telemetry publish timer (1 second)
        self._telemetry_timer = QTimer(self)
        self._telemetry_timer.setInterval(1000)
        self._telemetry_timer.timeout.connect(self._publish_telemetry)

        # Cached data from generators
        self._current_telemetry = None
        self._telemetry_publish_count = 0

    # ─── Properties ───────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        return self._conn_manager.is_connected

    @property
    def host(self) -> str:
        return self._conn_manager.host

    @property
    def port(self) -> int:
        return self._conn_manager.port

    # ─── Public API ───────────────────────────────────────────────

    def start(self):
        """Connect to broker and start publishing."""
        self._conn_manager.connect_to_broker()

    def stop(self):
        """Stop publishing and disconnect."""
        self._telemetry_timer.stop()
        self._conn_manager.cleanup()

    def connect_to_server(self, host: str = None, port: int = None):
        """Connect to broker (compatible with comm tab interface)."""
        self._conn_manager.connect_to_broker(host, port)

    def disconnect_from_server(self):
        """Disconnect from broker (compatible with comm tab interface)."""
        self._telemetry_timer.stop()
        self._conn_manager.disconnect_from_broker()

    def reconnect(self):
        """Reconnect to broker."""
        self.disconnect_from_server()
        QTimer.singleShot(2000, lambda: self.connect_to_server())

    def update_telemetry(self, telemetry):
        """Cache the latest telemetry data for periodic publishing."""
        self._current_telemetry = telemetry

    def publish_alert(self, alert):
        """Publish an alert to the broker."""
        if not self._conn_manager.is_connected:
            return
        self._conn_manager.publish("alerts", alert.to_dict())

    def get_stats(self) -> dict:
        """Return current connection statistics."""
        return self._conn_manager.get_stats()

    # ─── Signal Handlers ──────────────────────────────────────────

    def _on_connected(self):
        self.connected.emit()
        self._telemetry_timer.start()

        # Publish connection status
        self._conn_manager.publish("connection_status", {
            "event": "robot_console_connected",
            "client_name": "robot_console",
            "timestamp": datetime.now().isoformat(),
        })

    def _on_disconnected(self):
        self._telemetry_timer.stop()
        self.disconnected.emit()

    def _on_message(self, topic: str, message: dict):
        """Route incoming pub-sub messages to the appropriate handler."""
        if topic == "patient_vitals":
            # Convert to the format expected by the existing PatientVitalsTab
            payload = message.get("payload", {})
            vitals_msg = {
                "type": "VITALS_DATA",
                "timestamp": message.get("timestamp", ""),
                "payload": {
                    "hr": payload.get("heart_rate", 0),
                    "spo2": payload.get("spo2", 0),
                    "nibp_s": self._parse_bp(payload.get(
                        "blood_pressure", "0/0"), 0),
                    "nibp_d": self._parse_bp(payload.get(
                        "blood_pressure", "0/0"), 1),
                    "etco2": 38.0,  # Default EtCO2
                    "rr": payload.get("respiration", 0),
                    "temp": payload.get("temperature", 0),
                    "ecg_status": payload.get("ecg_status", "---"),
                },
            }
            self.vitals_received.emit(vitals_msg)
            self.data_received.emit(vitals_msg)

    def _publish_telemetry(self):
        """Publish cached telemetry data to the broker."""
        if not self._conn_manager.is_connected or \
                self._current_telemetry is None:
            return

        telemetry = self._current_telemetry
        payload = telemetry.to_dict()

        # Add extra fields required by the spec
        import psutil
        try:
            cpu = psutil.cpu_percent(interval=None)
        except Exception:
            cpu = 0.0

        payload["velocity"] = 0.0
        payload["force"] = 0.0
        payload["motion_enabled"] = telemetry.motion_state != "IDLE"
        payload["emergency_status"] = "CLEAR"
        payload["cpu_usage"] = cpu
        payload["latency"] = 0.84

        self._conn_manager.publish("robot_telemetry", payload)
        self._telemetry_publish_count += 1

        # Emit for comm tab
        self.data_sent.emit({
            "type": "ROBOT_TELEMETRY",
            "timestamp": payload.get("timestamp", ""),
            "payload": payload,
        })

    @staticmethod
    def _parse_bp(bp_str: str, index: int) -> float:
        """Parse blood pressure string 'sys/dia' into components."""
        try:
            parts = str(bp_str).split("/")
            return float(parts[index])
        except (IndexError, ValueError):
            return 0.0
