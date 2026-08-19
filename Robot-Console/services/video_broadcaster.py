# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — VIDEO BROADCAST SERVICE  (TCP Server)
#
#  Architecture:
#    - Listens on VIDEO_PORT (default 5001) — plain TCP, no TLS (POC)
#    - Accepts multiple Surgeon Console clients simultaneously
#    - broadcast_qimage(QImage) is called each frame from live_video._on_frame()
#    - Encoder thread: JPEG-encodes frames, sends to all connected clients
#    - Frame format: [4-byte big-endian length][JPEG binary bytes]
#    - Old frames are DROPPED when the queue is full (latency stays low)
#    - Clean shutdown: stops encoder, closes all client sockets
#
#  Transport is completely separate from the pub-sub broker (port 5000).
#  TLS can be added later by wrapping the sockets without changing the UI
#  or the broadcast_qimage() interface.
#
#  Logged events:
#    VIDEO_SERVER_STARTED    VIDEO_BROADCAST_STOPPED
#    VIDEO_CLIENT_CONNECTED  VIDEO_CLIENT_DISCONNECTED
#    VIDEO_STREAM_ERROR      VIDEO_FRAME_DROPPED
# ═══════════════════════════════════════════════════════════════════

import socket
import struct
import threading
import time
import queue
import logging
from typing import Optional, List

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QByteArray, QBuffer, QIODevice
from PyQt6.QtGui import QImage

log = logging.getLogger(__name__)

# ── Config import with local fallbacks ────────────────────────────
try:
    import sys
    import os
    _proj_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    if _proj_root not in sys.path:
        sys.path.insert(0, _proj_root)
    from shared_networking.config import (
        VIDEO_PORT, VIDEO_JPEG_QUALITY, VIDEO_FPS_TARGET, VIDEO_MAX_QUEUE,
    )
except ImportError:
    VIDEO_PORT         = 5001
    VIDEO_JPEG_QUALITY = 75
    VIDEO_FPS_TARGET   = 25
    VIDEO_MAX_QUEUE    = 2


class VideoBroadcastService(QObject):
    """TCP server that broadcasts live video frames to Surgeon Console clients.

    Usage (called by Robot Console MainWindow):
        svc = VideoBroadcastService(parent)
        svc.start_server()           # start listening on VIDEO_PORT
        # Then pass svc to LiveVideoScreen.set_broadcaster(svc)
        # live_video._on_frame() calls svc.broadcast_qimage(qimage) each frame
        svc.stop_server()            # clean shutdown

    Signals:
        status_changed(str)        — human-readable status
        fps_updated(float)         — transmit FPS (emitted every second)
        frame_sent(int)            — cumulative frames sent
        client_connected(str)      — new Surgeon Console address
        client_disconnected(str)   — Surgeon Console address
        error_occurred(str)        — error description
    """

    status_changed      = pyqtSignal(str)
    fps_updated         = pyqtSignal(float)
    frame_sent          = pyqtSignal(int)
    client_connected    = pyqtSignal(str)
    client_disconnected = pyqtSignal(str)
    error_occurred      = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._port          = VIDEO_PORT
        self._jpeg_quality  = VIDEO_JPEG_QUALITY

        self._server_sock: Optional[socket.socket] = None
        self._clients: List[socket.socket] = []
        self._clients_lock  = threading.Lock()

        self._running        = False
        self._server_thread: Optional[threading.Thread] = None
        self._encoder_thread: Optional[threading.Thread] = None

        # Bounded queue: hold QImage objects; oldest dropped when full
        self._frame_queue: queue.Queue = queue.Queue(maxsize=VIDEO_MAX_QUEUE)

        self._frames_sent  = 0
        self._fps_counter  = 0
        self._fps          = 0.0

        self._fps_timer = QTimer(self)
        self._fps_timer.setInterval(1000)
        self._fps_timer.timeout.connect(self._update_fps)

    # ── Properties ────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def client_count(self) -> int:
        with self._clients_lock:
            return len(self._clients)

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def frames_sent(self) -> int:
        return self._frames_sent

    # ── Public API ────────────────────────────────────────────────

    def start_server(self):
        """Start the TCP video server.  Idempotent — safe to call twice."""
        if self._running:
            return
        try:
            self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Bind to all interfaces so both localhost and LAN clients can connect
            self._server_sock.bind(("0.0.0.0", self._port))
            self._server_sock.listen(5)
            self._running = True

            self._server_thread = threading.Thread(
                target=self._accept_loop,
                daemon=True,
                name="VideoServer-Accept",
            )
            self._server_thread.start()

            self._encoder_thread = threading.Thread(
                target=self._encoder_loop,
                daemon=True,
                name="VideoServer-Encoder",
            )
            self._encoder_thread.start()

            self._fps_timer.start()
            msg = f"Video server started on port {self._port}"
            self.status_changed.emit(msg)
            log.info(f"VIDEO_SERVER_STARTED port={self._port}")

        except Exception as e:
            err = f"Failed to start video server: {e}"
            self.error_occurred.emit(err)
            log.error(f"VIDEO_STREAM_ERROR {err}")
            self._running = False
            if self._server_sock:
                try:
                    self._server_sock.close()
                except Exception:
                    pass
                self._server_sock = None

    def stop_server(self):
        """Stop the TCP video server and release all resources."""
        if not self._running:
            return

        self._running = False
        self._fps_timer.stop()

        # Close server socket to unblock accept()
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass
            self._server_sock = None

        # Close all connected clients
        with self._clients_lock:
            for sock in list(self._clients):
                try:
                    sock.close()
                except Exception:
                    pass
            self._clients.clear()

        # Send sentinel to unblock encoder queue
        try:
            self._frame_queue.put_nowait(None)
        except queue.Full:
            pass

        # Wait for threads (bounded)
        for t in (self._server_thread, self._encoder_thread):
            if t and t.is_alive():
                t.join(timeout=2.0)

        self.status_changed.emit("Video server stopped")
        self.fps_updated.emit(0.0)
        log.info("VIDEO_BROADCAST_STOPPED")

    def broadcast_qimage(self, qimage: QImage):
        """Feed a processed frame into the broadcast pipeline.

        Called from the Qt GUI thread (_on_frame in live_video.py).
        The actual JPEG encoding and network sending happen in the
        background encoder thread — the GUI thread is never blocked.

        If the queue is full (Surgeon Console is slower than source),
        the OLDEST frame is dropped to keep latency minimal.
        """
        if not self._running:
            return
        # Non-blocking put — drop oldest on overflow to prefer newest frame
        try:
            self._frame_queue.put_nowait(qimage)
        except queue.Full:
            try:
                self._frame_queue.get_nowait()   # discard oldest
            except queue.Empty:
                pass
            try:
                self._frame_queue.put_nowait(qimage)
            except queue.Full:
                log.debug("VIDEO_FRAME_DROPPED encoder queue full")

    # ── Background Threads ────────────────────────────────────────

    def _accept_loop(self):
        """Accept incoming Surgeon Console client connections."""
        log.info(f"Video server accepting connections on 0.0.0.0:{self._port}")
        while self._running and self._server_sock:
            try:
                self._server_sock.settimeout(1.0)
                try:
                    conn, addr = self._server_sock.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break  # server socket closed by stop_server()

                addr_str = f"{addr[0]}:{addr[1]}"
                # Disable Nagle — we send frames one at a time and want low latency
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                with self._clients_lock:
                    self._clients.append(conn)

                self.client_connected.emit(addr_str)
                self.status_changed.emit(f"Surgeon Console connected: {addr_str}")
                log.info(f"VIDEO_CLIENT_CONNECTED {addr_str}")

            except Exception as e:
                if self._running:
                    log.warning(f"Video accept error: {e}")

        log.info("Video accept loop ended")

    def _encoder_loop(self):
        """Encode QImage frames to JPEG and send to all connected clients."""
        frame_interval = 1.0 / VIDEO_FPS_TARGET

        while self._running:
            try:
                t0 = time.perf_counter()

                # Block until a frame (or sentinel None) arrives
                try:
                    qimage = self._frame_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                if qimage is None:
                    break  # sentinel from stop_server()

                # JPEG encode using Qt's built-in encoder
                ba = QByteArray()
                buf = QBuffer(ba)
                buf.open(QIODevice.OpenModeFlag.WriteOnly)
                qimage.save(buf, "JPG", self._jpeg_quality)
                buf.close()
                jpeg_bytes = ba.data()

                if not jpeg_bytes:
                    continue

                # Frame format: [4-byte big-endian length][JPEG bytes]
                header  = struct.pack("!I", len(jpeg_bytes))
                payload = header + jpeg_bytes

                # Send to all clients; collect dead ones
                dead: List[socket.socket] = []
                with self._clients_lock:
                    clients_snapshot = list(self._clients)

                for sock in clients_snapshot:
                    try:
                        sock.sendall(payload)
                    except Exception as send_err:
                        dead.append(sock)
                        log.info(f"VIDEO_CLIENT_DISCONNECTED send failed: {send_err}")

                # Remove and close dead clients
                if dead:
                    with self._clients_lock:
                        for s in dead:
                            if s in self._clients:
                                self._clients.remove(s)
                    for s in dead:
                        try:
                            addr = s.getpeername()
                            self.client_disconnected.emit(f"{addr[0]}:{addr[1]}")
                        except Exception:
                            self.client_disconnected.emit("unknown")
                        try:
                            s.close()
                        except Exception:
                            pass

                self._frames_sent += 1
                self._fps_counter += 1

                # Rate-limit to VIDEO_FPS_TARGET — sleep remaining time in interval
                elapsed  = time.perf_counter() - t0
                sleep_t  = frame_interval - elapsed
                if sleep_t > 0.001:
                    time.sleep(sleep_t)

            except Exception as e:
                if self._running:
                    log.warning(f"VIDEO_STREAM_ERROR encoder: {e}")

        log.info("Video encoder loop ended")

    def _update_fps(self):
        """Emit FPS and frame count every second (called on Qt timer)."""
        self._fps = float(self._fps_counter)
        self._fps_counter = 0
        self.fps_updated.emit(self._fps)
        self.frame_sent.emit(self._frames_sent)

    # ── Aliases for backward compatibility ────────────────────────
    # These no-ops exist so that any older call sites do not crash
    # while the migration from the broker-based implementation is
    # completed.  They will be removed in a future cleanup pass.

    def start_broadcast(self):
        """Legacy alias for start_server()."""
        if not self._running:
            self.start_server()

    def stop(self):
        """Legacy alias for stop_server()."""
        self.stop_server()

    def load_video(self, path: str):
        """No-op.  VideoBroadcastService no longer manages video sources;
        source management is handled by YoloPipeline in live_video.py."""

    def start_camera(self, index: int = 0):
        """No-op.  Camera management is handled by YoloPipeline."""
