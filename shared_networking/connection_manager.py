# ═══════════════════════════════════════════════════════════════════
#  AETHER CONSOLE — CONNECTION MANAGER
#  Manages the TCP socket lifecycle for pub-sub clients.
#  Handles connect, disconnect, auto-reconnect, heartbeat,
#  background receive thread, and packet statistics.
# ═══════════════════════════════════════════════════════════════════

import socket
import time
import threading
import logging
from datetime import datetime

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from shared_networking.config import (
    BROKER_HOST, BROKER_PORT,
    HEARTBEAT_INTERVAL_S, RECONNECT_INTERVAL_S, MAX_RECONNECT_ATTEMPTS,
    HEADER_SIZE,
)
from shared_networking.protocol import (
    encode_message, decode_header, decode_payload,
    create_heartbeat, create_handshake, create_subscribe,
    create_unsubscribe, create_client_list_request,
    CTRL_HEARTBEAT, CTRL_CLIENT_UPDATE, CTRL_CLIENT_LIST,
    is_control_message,
)

log = logging.getLogger(__name__)


class ConnectionManager(QObject):
    """Manages TCP connection to the pub-sub broker.

    Provides publish/subscribe functionality with automatic reconnect,
    heartbeat, and packet statistics. All UI-relevant events are
    emitted as Qt signals for thread-safe updates.
    """

    # ─── Signals ──────────────────────────────────────────────────
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error_occurred = pyqtSignal(str)
    log_message = pyqtSignal(str, str)          # (level, message)
    stats_updated = pyqtSignal(dict)
    message_received = pyqtSignal(str, dict)    # (topic, full_message)
    client_list_received = pyqtSignal(list)     # list of client dicts

    # Private signals for thread safety
    _start_timers_sig = pyqtSignal()
    _stop_timers_sig = pyqtSignal()
    _start_reconnect_sig = pyqtSignal()

    def __init__(self, client_name: str, publish_topics: list = None,
                 subscribe_topics: list = None, parent=None):
        super().__init__(parent)
        self._client_name = client_name
        self._publish_topics = publish_topics or []
        self._subscribe_topics = subscribe_topics or []

        self._socket: socket.socket = None
        self._is_connected = False
        self._host = BROKER_HOST
        self._port = BROKER_PORT
        self._lock = threading.Lock()

        # Statistics
        self._packets_sent = 0
        self._packets_received = 0
        self._bytes_sent = 0
        self._bytes_received = 0
        self._errors = 0
        self._last_sent_time = "---"
        self._last_received_time = "---"
        self._reconnect_count = 0
        self._connect_time = None

        # Background threads
        self._receive_thread: threading.Thread = None
        self._running = False

        # Heartbeat timer
        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.setInterval(int(HEARTBEAT_INTERVAL_S * 1000))
        self._heartbeat_timer.timeout.connect(self._send_heartbeat)

        # Auto-reconnect timer
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setSingleShot(True)
        self._reconnect_timer.setInterval(int(RECONNECT_INTERVAL_S * 1000))
        self._reconnect_timer.timeout.connect(self._auto_reconnect)
        self._auto_reconnect_enabled = True

        # Data rate tracking
        self._prev_bytes_sent = 0
        self._prev_bytes_received = 0
        self._prev_rate_time = time.time()
        self._data_rate_in = 0.0
        self._data_rate_out = 0.0

        self._rate_timer = QTimer(self)
        self._rate_timer.setInterval(1000)
        self._rate_timer.timeout.connect(self._calculate_rates)

        # Connect private signals
        self._start_timers_sig.connect(self._on_start_timers)
        self._stop_timers_sig.connect(self._on_stop_timers)
        self._start_reconnect_sig.connect(self._on_start_reconnect)

    def _on_start_timers(self):
        self._heartbeat_timer.start()
        self._rate_timer.start()

    def _on_stop_timers(self):
        self._heartbeat_timer.stop()
        self._rate_timer.stop()

    def _on_start_reconnect(self):
        self._reconnect_timer.start()

    # ─── Properties ───────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def client_name(self) -> str:
        return self._client_name

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    # ─── Public API ───────────────────────────────────────────────

    def connect_to_broker(self, host: str = None, port: int = None):
        """Connect to the pub-sub broker."""
        if self._is_connected:
            self.log_message.emit("WARNING", "Already connected")
            return

        if host:
            self._host = host
        if port:
            self._port = port

        self.log_message.emit("INFO",
                              f"Connecting to broker {self._host}:{self._port}...")

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(5.0)
            self._socket.connect((self._host, self._port))
            self._socket.settimeout(None)

            self._is_connected = True
            self._running = True
            self._connect_time = datetime.now()

            # Send handshake
            handshake = create_handshake(
                self._client_name,
                self._publish_topics,
                self._subscribe_topics,
            )
            self._send_raw(handshake)

            # Subscribe to topics
            if self._subscribe_topics:
                sub_msg = create_subscribe(
                    self._client_name, self._subscribe_topics)
                self._send_raw(sub_msg)

            # Start receive thread
            self._receive_thread = threading.Thread(
                target=self._receive_loop, daemon=True,
                name=f"PubSub-Recv-{self._client_name}")
            self._receive_thread.start()

            # Start heartbeat and rate timers (thread-safe)
            self._start_timers_sig.emit()

            self.connected.emit()
            self.log_message.emit("INFO",
                                  f"Connected to broker {self._host}:{self._port}")
            self._emit_stats()

        except Exception as e:
            self._is_connected = False
            err = f"Connection failed: {e}"
            self.error_occurred.emit(err)
            self.log_message.emit("ERROR", err)
            self._errors += 1
            if self._socket:
                try:
                    self._socket.close()
                except Exception:
                    pass
                self._socket = None

            # Schedule auto-reconnect
            if self._auto_reconnect_enabled:
                self._schedule_reconnect()

    def disconnect_from_broker(self):
        """Gracefully disconnect from the broker."""
        self._auto_reconnect_enabled = False
        self._reconnect_timer.stop()
        self._do_disconnect()
        self.log_message.emit("INFO", "Disconnected from broker")

    def publish(self, topic: str, payload: dict):
        """Publish a message to a topic."""
        if not self._is_connected:
            return
        from shared_networking.protocol import create_message
        message = create_message(topic, self._client_name, payload)
        self._send_raw(message)

    def subscribe(self, topics: list):
        """Subscribe to additional topics."""
        new_topics = [t for t in topics if t not in self._subscribe_topics]
        if not new_topics:
            return
        self._subscribe_topics.extend(new_topics)
        if self._is_connected:
            msg = create_subscribe(self._client_name, new_topics)
            self._send_raw(msg)

    def unsubscribe(self, topics: list):
        """Unsubscribe from topics."""
        for t in topics:
            if t in self._subscribe_topics:
                self._subscribe_topics.remove(t)
        if self._is_connected:
            msg = create_unsubscribe(self._client_name, topics)
            self._send_raw(msg)

    def request_client_list(self):
        """Request the list of connected clients from the broker."""
        if self._is_connected:
            self._send_raw(create_client_list_request(self._client_name))

    def enable_auto_reconnect(self, enabled: bool = True):
        """Enable or disable auto-reconnect."""
        self._auto_reconnect_enabled = enabled

    def get_stats(self) -> dict:
        """Return current connection statistics."""
        uptime = "---"
        if self._connect_time and self._is_connected:
            delta = datetime.now() - self._connect_time
            mins, secs = divmod(int(delta.total_seconds()), 60)
            hours, mins = divmod(mins, 60)
            uptime = f"{hours:02d}:{mins:02d}:{secs:02d}"

        return {
            "is_connected": self._is_connected,
            "client_name": self._client_name,
            "remote_address": f"{self._host}:{self._port}",
            "packets_sent": self._packets_sent,
            "packets_received": self._packets_received,
            "bytes_sent": self._bytes_sent,
            "bytes_received": self._bytes_received,
            "errors": self._errors,
            "last_sent_time": self._last_sent_time,
            "last_received_time": self._last_received_time,
            "reconnect_count": self._reconnect_count,
            "data_rate_in": round(self._data_rate_in, 1),
            "data_rate_out": round(self._data_rate_out, 1),
            "uptime": uptime,
            "publish_topics": self._publish_topics,
            "subscribe_topics": self._subscribe_topics,
        }

    def cleanup(self):
        """Stop all timers and disconnect. Call on application shutdown."""
        self._auto_reconnect_enabled = False
        self._reconnect_timer.stop()
        self._heartbeat_timer.stop()
        self._rate_timer.stop()
        self._do_disconnect()

    # ─── Internal: Send ───────────────────────────────────────────

    def _send_raw(self, message: dict):
        """Encode and send a message over the socket."""
        if not self._socket or not self._is_connected:
            return

        try:
            data = encode_message(message)
            with self._lock:
                self._socket.sendall(data)

            self._packets_sent += 1
            self._bytes_sent += len(data)
            self._last_sent_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        except Exception as e:
            self._errors += 1
            err = f"Send error: {e}"
            self.error_occurred.emit(err)
            self.log_message.emit("ERROR", err)
            self._handle_connection_lost()

    def _send_heartbeat(self):
        """Send a periodic heartbeat to the broker."""
        if self._is_connected:
            self._send_raw(create_heartbeat(self._client_name))

    # ─── Internal: Receive Loop ───────────────────────────────────

    def _receive_loop(self):
        """Background thread: continuously receive data from broker."""
        while self._running and self._socket:
            try:
                header = self._recv_exact(HEADER_SIZE)
                if header is None:
                    break

                payload_len = decode_header(header)
                payload_bytes = self._recv_exact(payload_len)
                if payload_bytes is None:
                    break

                message = decode_payload(payload_bytes)
                self._packets_received += 1
                self._bytes_received += HEADER_SIZE + payload_len
                self._last_received_time = (
                    datetime.now().strftime("%H:%M:%S.%f")[:-3])

                topic = message.get("topic", "")

                # Route control messages
                if topic == CTRL_HEARTBEAT:
                    continue
                elif topic == CTRL_CLIENT_LIST or topic == CTRL_CLIENT_UPDATE:
                    clients = message.get("payload", {}).get("clients", [])
                    self.client_list_received.emit(clients)
                    continue

                # Emit data message
                self.message_received.emit(topic, message)

            except Exception as e:
                if self._running:
                    self._errors += 1
                    self.error_occurred.emit(f"Receive error: {e}")
                    self.log_message.emit("ERROR", f"Receive error: {e}")
                break

        if self._running:
            self._handle_connection_lost()

    def _recv_exact(self, num_bytes: int):
        """Read exactly num_bytes from the socket."""
        data = b""
        while len(data) < num_bytes:
            try:
                chunk = self._socket.recv(num_bytes - len(data))
                if not chunk:
                    return None
                data += chunk
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                return None
        return data

    # ─── Internal: Connection Management ──────────────────────────

    def _do_disconnect(self):
        """Internal disconnect without logging or auto-reconnect logic."""
        was_connected = self._is_connected
        self._running = False
        self._is_connected = False
        self._stop_timers_sig.emit()

        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

        if was_connected:
            self.disconnected.emit()
            self._emit_stats()

    def _handle_connection_lost(self):
        """Handle unexpected connection loss."""
        if not self._is_connected:
            return

        self._do_disconnect()
        self.log_message.emit("WARNING", "Connection lost")

        if self._auto_reconnect_enabled:
            self._schedule_reconnect()

    def _schedule_reconnect(self):
        """Schedule an auto-reconnect attempt."""
        if MAX_RECONNECT_ATTEMPTS > 0 and \
                self._reconnect_count >= MAX_RECONNECT_ATTEMPTS:
            self.log_message.emit("ERROR",
                                  "Max reconnect attempts reached")
            return
        self.log_message.emit("INFO",
                              f"Reconnecting in {RECONNECT_INTERVAL_S}s...")
        self._start_reconnect_sig.emit()

    def _auto_reconnect(self):
        """Auto-reconnect attempt."""
        self._reconnect_count += 1
        self.log_message.emit("INFO",
                              f"Reconnect attempt #{self._reconnect_count}")
        self.connect_to_broker()

    def _calculate_rates(self):
        """Calculate data rates."""
        now = time.time()
        elapsed = now - self._prev_rate_time
        if elapsed <= 0:
            return

        self._data_rate_out = (
            self._bytes_sent - self._prev_bytes_sent) / elapsed
        self._data_rate_in = (
            self._bytes_received - self._prev_bytes_received) / elapsed

        self._prev_bytes_sent = self._bytes_sent
        self._prev_bytes_received = self._bytes_received
        self._prev_rate_time = now

        self._emit_stats()

    def _emit_stats(self):
        """Emit current stats to the UI."""
        self.stats_updated.emit(self.get_stats())
