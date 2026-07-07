# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — CONNECTION MONITOR
#  Tracks connection health, data rates, and latency.
# ═══════════════════════════════════════════════════════════════════

import time
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class ConnectionMonitor(QObject):
    """Monitors TCP connection health and computes throughput statistics.

    Tracks bytes transferred over sliding windows to calculate
    real-time data rates for both inbound and outbound traffic.
    """

    stats_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Snapshot values for rate calculation
        self._prev_bytes_sent = 0
        self._prev_bytes_received = 0
        self._prev_time = time.time()

        self._data_rate_in = 0.0
        self._data_rate_out = 0.0

        # Polling timer
        self._timer = QTimer(self)
        self._timer.setInterval(1000)    # Calculate rates every 1s
        self._timer.timeout.connect(self._calculate_rates)

        self._tcp_client = None

    # ─── Public API ───────────────────────────────────────────────

    def set_client(self, tcp_client):
        """Attach the TCP client to monitor."""
        self._tcp_client = tcp_client

    def start(self):
        """Start monitoring."""
        self._prev_time = time.time()
        self._timer.start()

    def stop(self):
        """Stop monitoring."""
        self._timer.stop()

    @property
    def data_rate_in(self) -> float:
        return self._data_rate_in

    @property
    def data_rate_out(self) -> float:
        return self._data_rate_out

    # ─── Internal ─────────────────────────────────────────────────

    def _calculate_rates(self):
        """Calculate bytes/sec rates from the TCP client stats."""
        if not self._tcp_client:
            return

        stats = self._tcp_client.get_stats()
        now = time.time()
        elapsed = now - self._prev_time
        if elapsed <= 0:
            return

        bytes_sent = stats.get("bytes_sent", 0)
        bytes_recv = stats.get("bytes_received", 0)

        self._data_rate_out = (bytes_sent - self._prev_bytes_sent) / elapsed
        self._data_rate_in = (bytes_recv - self._prev_bytes_received) / elapsed

        self._prev_bytes_sent = bytes_sent
        self._prev_bytes_received = bytes_recv
        self._prev_time = now

        # Augment stats with computed rates
        stats["data_rate_in"] = round(self._data_rate_in, 1)
        stats["data_rate_out"] = round(self._data_rate_out, 1)

        self.stats_updated.emit(stats)
