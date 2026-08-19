# ═══════════════════════════════════════════════════════════════════
#  SURGEON CONSOLE — VIDEO RECEIVER SERVICE
#
#  Connects to the Robot Console's dedicated TCP video server
#  (port 5001, separate from the telemetry/control broker on 5000).
#
#  Architecture:
#    - Background receive thread: reads [4-byte length][JPEG bytes]
#    - Background decode thread:  JPEG → QImage, emits frame_received
#    - Auto-reconnect with RECONNECT_INTERVAL_S back-off
#    - Bounded decode queue (2 frames) — oldest dropped on overflow
#    - States: DISCONNECTED → CONNECTING → CONNECTED → STREAMING
#    - GUI thread is never blocked
#
#  Logged events:
#    VIDEO_CLIENT_CONNECTED    VIDEO_CLIENT_DISCONNECTED
#    VIDEO_BROADCAST_STARTED   VIDEO_BROADCAST_STOPPED
#    VIDEO_STREAM_ERROR        VIDEO_FRAME_DROPPED
# ═══════════════════════════════════════════════════════════════════

import socket
import struct
import threading
import time
import queue
import logging
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QImage

log = logging.getLogger(__name__)

# ── Config import with local fallbacks ────────────────────────────
try:
    import sys
    import os
    _proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _proj_root not in sys.path:
        sys.path.insert(0, _proj_root)
    from shared_networking.config import VIDEO_HOST, VIDEO_PORT, VIDEO_MAX_QUEUE
except ImportError:
    VIDEO_HOST      = "127.0.0.1"
    VIDEO_PORT      = 5001
    VIDEO_MAX_QUEUE = 2

RECONNECT_INTERVAL_S = 3.0    # seconds between reconnect attempts
RECV_TIMEOUT_S       = 10.0   # socket read timeout (triggers reconnect)
MAX_FRAME_BYTES      = 50 * 1024 * 1024  # 50 MB safety limit per frame


class VideoReceiver(QObject):
    """Receives live video frames from Robot Console over plain TCP.

    Typical usage (Surgeon Console main.py):
        receiver = VideoReceiver(parent=self)
        receiver.frame_received.connect(self.live_video.update_frame)
        receiver.status_changed.connect(self.status_bar_widget.set_video_status)
        receiver.start()
        # On close:
        receiver.stop()

    Signals:
        frame_received(QImage)  — decoded frame ready for display
        status_changed(str)     — human-readable status for UI
        error_occurred(str)     — error description
        connected()             — TCP connection established
        disconnected()          — TCP connection lost / before reconnect
        fps_updated(float)      — receive FPS (emitted every second)
    """

    frame_received  = pyqtSignal(QImage)
    status_changed  = pyqtSignal(str)
    error_occurred  = pyqtSignal(str)
    connected       = pyqtSignal()
    disconnected    = pyqtSignal()
    fps_updated     = pyqtSignal(float)

    def __init__(self, host: str = None, port: int = None, parent=None):
        super().__init__(parent)
        self._host = host or VIDEO_HOST
        self._port = port or VIDEO_PORT

        self._running        = False
        self._is_streaming   = False

        self._recv_thread:   Optional[threading.Thread] = None
        self._decode_thread: Optional[threading.Thread] = None

        # Bounded queue for raw JPEG bytes (max VIDEO_MAX_QUEUE frames)
        self._decode_queue: queue.Queue = queue.Queue(maxsize=VIDEO_MAX_QUEUE)

        self._frames_received = 0
        self._fps_counter     = 0
        self._fps             = 0.0

        self._fps_timer = QTimer(self)
        self._fps_timer.setInterval(1000)
        self._fps_timer.timeout.connect(self._update_fps)

    # ── Properties ────────────────────────────────────────────────

    @property
    def is_streaming(self) -> bool:
        return self._is_streaming

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def frames_received(self) -> int:
        return self._frames_received

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    # ── Public API ────────────────────────────────────────────────

    def start(self):
        """Begin connecting to Robot Console video server.  Idempotent."""
        if self._running:
            return
        self._running = True

        self._recv_thread = threading.Thread(
            target=self._recv_loop, daemon=True, name="VideoRecv")
        self._recv_thread.start()

        self._decode_thread = threading.Thread(
            target=self._decode_loop, daemon=True, name="VideoDecode")
        self._decode_thread.start()

        self._fps_timer.start()
        log.info(f"VIDEO_BROADCAST_STARTED receiver connecting to {self._host}:{self._port}")

    def stop(self):
        """Stop receiving video and release all resources."""
        if not self._running:
            return
        self._running      = False
        self._is_streaming = False
        self._fps_timer.stop()

        # Unblock the decode thread
        try:
            self._decode_queue.put_nowait(None)  # sentinel
        except queue.Full:
            pass

        for t in (self._recv_thread, self._decode_thread):
            if t and t.is_alive():
                t.join(timeout=2.0)

        self._recv_thread   = None
        self._decode_thread = None
        self.status_changed.emit("Video receiver stopped")
        log.info("VIDEO_BROADCAST_STOPPED receiver")

    # ── Background: Receive Loop ──────────────────────────────────

    def _recv_loop(self):
        """Background thread: connect to Robot Console, read frames.

        Runs continuously while self._running is True.
        On disconnect or error, waits RECONNECT_INTERVAL_S then retries.
        """
        while self._running:
            sock: Optional[socket.socket] = None
            try:
                self.status_changed.emit(
                    f"Connecting to Robot Console video ({self._host}:{self._port})...")
                log.info(f"VideoReceiver connecting to {self._host}:{self._port}")

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                sock.connect((self._host, self._port))
                sock.settimeout(RECV_TIMEOUT_S)  # per-chunk timeout while streaming

                self._is_streaming = True
                self.connected.emit()
                self.status_changed.emit("Video stream connected — receiving")
                log.info("VIDEO_CLIENT_CONNECTED to Robot Console video server")

                while self._running:
                    # Read the 4-byte frame-length header
                    header = self._recv_exact(sock, 4)
                    if header is None:
                        break   # connection closed cleanly

                    frame_len = struct.unpack("!I", header)[0]

                    if frame_len == 0 or frame_len > MAX_FRAME_BYTES:
                        log.warning(
                            f"VIDEO_STREAM_ERROR invalid frame length: {frame_len}")
                        break

                    # Read JPEG payload
                    jpeg_bytes = self._recv_exact(sock, frame_len)
                    if jpeg_bytes is None:
                        break

                    self._frames_received += 1
                    self._fps_counter     += 1

                    # Non-blocking push to decode queue.
                    # If the decoder is running behind, drop the oldest frame
                    # to prevent latency from accumulating.
                    try:
                        self._decode_queue.put_nowait(jpeg_bytes)
                    except queue.Full:
                        try:
                            self._decode_queue.get_nowait()  # drop oldest
                        except queue.Empty:
                            pass
                        try:
                            self._decode_queue.put_nowait(jpeg_bytes)
                        except queue.Full:
                            log.debug("VIDEO_FRAME_DROPPED decode queue full")

            except (ConnectionRefusedError, TimeoutError) as e:
                if self._running:
                    log.debug(f"Video connect failed ({type(e).__name__}): {e}")
                    self.status_changed.emit(
                        f"Video: Robot Console unavailable — retrying in "
                        f"{RECONNECT_INTERVAL_S:.0f}s")
            except OSError as e:
                if self._running:
                    log.warning(f"VIDEO_STREAM_ERROR OSError: {e}")
            except Exception as e:
                if self._running:
                    log.warning(f"VIDEO_STREAM_ERROR unexpected: {e}")
                    self.error_occurred.emit(str(e))
            finally:
                self._is_streaming = False
                if sock:
                    try:
                        sock.close()
                    except Exception:
                        pass

            if not self._running:
                break

            # Announce disconnect and wait before retrying
            self.disconnected.emit()
            self.status_changed.emit(
                f"Video stream disconnected — reconnecting in "
                f"{RECONNECT_INTERVAL_S:.0f}s")
            log.info("VIDEO_CLIENT_DISCONNECTED from Robot Console")
            time.sleep(RECONNECT_INTERVAL_S)

        log.info("VideoReceiver receive loop ended")

    # ── Background: Decode Loop ───────────────────────────────────

    def _decode_loop(self):
        """Background thread: decode JPEG bytes → QImage and emit signal.

        Runs continuously while self._running is True.
        Emitting the signal is safe across threads — Qt queues the call
        to the main thread automatically.
        """
        while self._running:
            try:
                jpeg_bytes = self._decode_queue.get(timeout=0.5)
                if jpeg_bytes is None:
                    break  # sentinel from stop()

                img = QImage.fromData(bytes(jpeg_bytes))
                if not img.isNull():
                    self.frame_received.emit(img)
                else:
                    log.debug("VIDEO_STREAM_ERROR QImage.fromData returned null image")

            except queue.Empty:
                continue
            except Exception as e:
                if self._running:
                    log.warning(f"VIDEO_STREAM_ERROR decode: {e}")

        log.info("VideoReceiver decode loop ended")

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _recv_exact(sock: socket.socket, n: int) -> Optional[bytes]:
        """Read exactly n bytes from socket using a pre-allocated buffer.

        Returns bytes on success, None if the connection was closed
        or a network error occurred.  Never raises.
        """
        if n == 0:
            return b""
        buf      = bytearray(n)
        view     = memoryview(buf)
        received = 0
        while received < n:
            try:
                chunk = sock.recv_into(view[received:], n - received)
                if not chunk:
                    return None   # connection closed cleanly
                received += chunk
            except (ConnectionResetError, ConnectionAbortedError, OSError,
                    socket.timeout, TimeoutError):
                return None
        return bytes(buf)

    def _update_fps(self):
        """Emit FPS estimate once per second (runs on Qt GUI timer)."""
        self._fps         = float(self._fps_counter)
        self._fps_counter = 0
        self.fps_updated.emit(self._fps)
