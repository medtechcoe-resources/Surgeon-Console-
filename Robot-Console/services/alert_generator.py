# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — ALERT GENERATOR
#  Generates random system alerts at a rate of 1 per minute.
# ═══════════════════════════════════════════════════════════════════

import random
from datetime import datetime

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from models.data_models import AlertEntry
from constants import ALERT_INTERVAL_MS, ALERT_TEMPLATES


class AlertGenerator(QObject):
    """Generates random robot system alerts at configurable intervals.

    Each alert has a severity (CRITICAL/WARNING/INFO), a source
    subsystem, and a descriptive message drawn from the template pool.
    """

    alert_generated = pyqtSignal(AlertEntry)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(ALERT_INTERVAL_MS)
        self._timer.timeout.connect(self._generate)
        self._running = False

        # Store all alerts for the table
        self.alerts: list[AlertEntry] = []

    # ─── Public API ───────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self):
        """Start automatic alert generation."""
        if self._running:
            return
        self._running = True
        self._timer.start()

    def stop(self):
        """Stop alert generation."""
        self._running = False
        self._timer.stop()

    def add_alert(self, severity: str, source: str, message: str):
        """Manually add an alert entry."""
        entry = AlertEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            severity=severity,
            source=source,
            message=message,
        )
        self.alerts.insert(0, entry)
        self.alert_generated.emit(entry)

    # ─── Internal ─────────────────────────────────────────────────

    def _generate(self):
        """Generate a single random alert from the template pool."""
        template = random.choice(ALERT_TEMPLATES)
        entry = AlertEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            severity=template["severity"],
            source=template["source"],
            message=template["message"],
        )
        self.alerts.insert(0, entry)

        # Keep at most 200 alerts
        if len(self.alerts) > 200:
            self.alerts = self.alerts[:200]

        self.alert_generated.emit(entry)
