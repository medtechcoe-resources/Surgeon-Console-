# ═══════════════════════════════════════════════════════════════════
#  DATA GENERATOR — ALERT GENERATOR
#  Generates random robot/system safety alerts drawn from a template
#  pool.  Interval: every 60 000 ms (1 per minute).
# ═══════════════════════════════════════════════════════════════════

import random
from datetime import datetime

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


# ── Alert template pool ───────────────────────────────────────────
ALERT_TEMPLATES = [
    {"severity": "WARNING",  "source": "Joint Controller",  "message": "Joint Torque High"},
    {"severity": "WARNING",  "source": "Thermal Monitor",   "message": "Servo Temperature High"},
    {"severity": "INFO",     "source": "Calibration Sys.",  "message": "Calibration Required"},
    {"severity": "WARNING",  "source": "Network Monitor",   "message": "Network Delay Warning"},
    {"severity": "WARNING",  "source": "Motion Planner",    "message": "Motion Limit Approaching"},
    {"severity": "CRITICAL", "source": "Safety System",     "message": "Emergency Stop Triggered"},
    {"severity": "WARNING",  "source": "Sensor Array",      "message": "Sensor Validation Warning"},
    {"severity": "INFO",     "source": "System Controller", "message": "System Health Check OK"},
    {"severity": "WARNING",  "source": "Force Sensor",      "message": "End Effector Force Spike"},
    {"severity": "INFO",     "source": "Motion Planner",    "message": "Trajectory Replanned"},
    {"severity": "WARNING",  "source": "Power Monitor",     "message": "Battery Below 25%"},
    {"severity": "INFO",     "source": "Vision System",     "message": "Camera Feed Stable"},
    {"severity": "CRITICAL", "source": "Joint Controller",  "message": "Overcurrent on J3"},
    {"severity": "WARNING",  "source": "Collision Detect",  "message": "Workspace Boundary Near"},
    {"severity": "INFO",     "source": "Telemetry Sys.",    "message": "Telemetry Link OK"},
]

INTERVAL_MS = 60_000   # 1 alert per minute


class AlertGenerator(QObject):
    """Generates random robot/system safety alerts at a fixed interval.

    Draws from a curated template pool and emits ``alert_ready`` each
    time a new alert is produced.  Maintains a rolling list of the
    last 200 alerts for display by the console UI.
    """

    alert_ready = pyqtSignal(dict)   # emits the alert dict

    def __init__(self, parent=None):
        super().__init__(parent)

        self._timer = QTimer(self)
        self._timer.setInterval(INTERVAL_MS)
        self._timer.timeout.connect(self._generate)

        self._running = False
        self._msg_count = 0

        # Rolling alert log (newest first)
        self.alerts: list[dict] = []

        # Latest generated alert — readable by console UI
        self.latest: dict = {}

    # ── Public API ────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def message_count(self) -> int:
        return self._msg_count

    def start(self):
        """Start generating alerts."""
        if self._running:
            return
        self._running = True
        self._timer.start()

    def stop(self):
        """Stop generating alerts."""
        self._running = False
        self._timer.stop()

    def pause(self):
        """Pause without clearing state."""
        if self._running:
            self._timer.stop()
            self._running = False

    def resume(self):
        """Resume from paused state."""
        if not self._running:
            self._running = True
            self._timer.start()

    def inject(self, severity: str, source: str, message: str):
        """Manually inject a custom alert (useful for testing)."""
        alert = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "severity":  severity,
            "source":    source,
            "message":   message,
        }
        self._store_and_emit(alert)

    # ── Internal ──────────────────────────────────────────────────

    def _generate(self):
        """Generate a single random alert from the template pool."""
        template = random.choice(ALERT_TEMPLATES)
        alert = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "severity":  template["severity"],
            "source":    template["source"],
            "message":   template["message"],
        }
        self._store_and_emit(alert)

    def _store_and_emit(self, alert: dict):
        """Store alert in rolling log and emit signal."""
        self.alerts.insert(0, alert)
        if len(self.alerts) > 200:
            self.alerts = self.alerts[:200]

        self.latest = alert
        self._msg_count += 1
        self.alert_ready.emit(alert)
