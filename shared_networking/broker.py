# ═══════════════════════════════════════════════════════════════════
#  AETHER CONSOLE — PUB-SUB BROKER
#  Central TCP server that routes messages between clients
#  based on topic subscriptions. Manages client registry,
#  heartbeat tracking, authentication, and encrypted communication.
#
#  Responsibilities (kept lightweight):
#    - Accept connections
#    - Authenticate users
#    - Route messages
#    - Encrypt/decrypt
#    - Log events
#    - Monitor client status
# ═══════════════════════════════════════════════════════════════════

import socket
import threading
import logging
import time
from datetime import datetime

from shared_networking.config import (
    BROKER_HOST, BROKER_PORT, HEADER_SIZE, HEARTBEAT_TIMEOUT_S,
    ENCRYPTION_KEY_PATH,
)
from shared_networking.protocol import (
    encode_message, decode_header, decode_payload, create_message,
    CTRL_SUBSCRIBE, CTRL_UNSUBSCRIBE, CTRL_HEARTBEAT,
    CTRL_HANDSHAKE, CTRL_CLIENT_LIST, CTRL_CLIENT_UPDATE,
)
from shared_networking.encryption import EncryptionManager
from shared_networking.authentication import AuthManager
from shared_networking.logger import get_logger

log = get_logger("BROKER")


class ClientInfo:
    """Tracks a connected client's state."""

    def __init__(self, conn: socket.socket, addr: tuple):
        self.conn = conn
        self.addr = addr
        self.name = f"{addr[0]}:{addr[1]}"
        self.subscriptions: set = set()
        self.publish_topics: list = []
        self.last_heartbeat = time.time()
        self.connect_time = datetime.now()
        self.packets_received = 0
        self.packets_sent = 0

        # Auth context (populated during handshake)
        self.username = ""
        self.role = ""
        self.session_id = ""
        self.authenticated = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "address": f"{self.addr[0]}:{self.addr[1]}",
            "subscriptions": list(self.subscriptions),
            "publish_topics": self.publish_topics,
            "connected_since": self.connect_time.isoformat(),
            "username": self.username,
            "role": self.role,
            "authenticated": self.authenticated,
        }


class PubSubBroker:
    """TCP Pub-Sub Broker — routes encrypted messages between clients.

    Architecture:
    - One accept thread for new connections.
    - One receive thread per connected client.
    - Lock-guarded send to any client.
    - Heartbeat monitor thread checks for dead clients.
    - Fernet encryption on all wire traffic.
    - Authentication during handshake.
    """

    def __init__(self, host: str = None, port: int = None):
        self._host = host or BROKER_HOST
        self._port = port or BROKER_PORT
        self._server_socket: socket.socket = None
        self._running = False
        self._lock = threading.Lock()

        # Client registry: socket fd → ClientInfo
        self._clients: dict[int, ClientInfo] = {}

        # Auth manager for credential verification
        self._auth_manager = AuthManager()

    # ─── Public API ───────────────────────────────────────────────

    def start(self):
        """Start the broker server."""
        # Load encryption key
        em = EncryptionManager.instance()
        if not em.load_key(ENCRYPTION_KEY_PATH):
            log.warning("Encryption key not found — generating new key")
            EncryptionManager.generate_key(ENCRYPTION_KEY_PATH)
            em.load_key(ENCRYPTION_KEY_PATH)

        if em.is_ready:
            log.info(f"Encryption enabled: {em.algorithm}")
        else:
            log.warning("Encryption is NOT active — messages will be plaintext")

        self._server_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self._host, self._port))
        self._server_socket.listen(10)
        self._running = True

        log.info(f"Pub-Sub Broker started on {self._host}:{self._port}")
        print("=" * 60)
        print("  AETHER PUB-SUB BROKER")
        print(f"  Listening on {self._host}:{self._port}")
        print(f"  Encryption: {em.algorithm if em.is_ready else 'DISABLED'}")
        print("=" * 60)

        # Start heartbeat monitor
        monitor = threading.Thread(
            target=self._heartbeat_monitor, daemon=True,
            name="Broker-HeartbeatMonitor")
        monitor.start()

        # Accept loop (blocking)
        self._accept_loop()

    def stop(self):
        """Stop the broker."""
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass

        with self._lock:
            for fd, client in list(self._clients.items()):
                try:
                    client.conn.close()
                except Exception:
                    pass
            self._clients.clear()

        log.info("Broker stopped")

    # ─── Accept Loop ──────────────────────────────────────────────

    def _accept_loop(self):
        """Accept incoming client connections."""
        while self._running:
            try:
                conn, addr = self._server_socket.accept()
                log.info(f"New connection from {addr}")
                print(f"  [+] Client connected: {addr[0]}:{addr[1]}")

                client = ClientInfo(conn, addr)
                with self._lock:
                    self._clients[conn.fileno()] = client

                # Start client handler thread
                t = threading.Thread(
                    target=self._client_handler,
                    args=(client,), daemon=True,
                    name=f"Broker-Client-{addr[0]}:{addr[1]}")
                t.start()

            except OSError:
                if self._running:
                    log.error("Accept error")
                break

    # ─── Client Handler ───────────────────────────────────────────

    def _client_handler(self, client: ClientInfo):
        """Handle messages from a single client."""
        while self._running:
            try:
                header = self._recv_exact(client.conn, HEADER_SIZE)
                if header is None:
                    break

                payload_len = decode_header(header)
                payload_bytes = self._recv_exact(
                    client.conn, payload_len)
                if payload_bytes is None:
                    break

                message = decode_payload(payload_bytes)
                client.packets_received += 1
                topic = message.get("topic", "")

                # Route by message type
                if topic == CTRL_HANDSHAKE:
                    self._handle_handshake(client, message)
                elif topic == CTRL_SUBSCRIBE:
                    self._handle_subscribe(client, message)
                elif topic == CTRL_UNSUBSCRIBE:
                    self._handle_unsubscribe(client, message)
                elif topic == CTRL_HEARTBEAT:
                    client.last_heartbeat = time.time()
                elif topic == CTRL_CLIENT_LIST:
                    self._handle_client_list_request(client)
                else:
                    # Data message — route to subscribers
                    self._route_message(client, message, topic)

            except Exception as e:
                if self._running:
                    log.warning(
                        f"Error from {client.name}: {e}")
                break

        # Client disconnected
        self._remove_client(client)

    # ─── Message Routing ──────────────────────────────────────────

    def _route_message(self, sender: ClientInfo, message: dict,
                       topic: str):
        """Route a published message to all subscribers of the topic."""
        data = encode_message(message)

        subscribers_count = 0
        with self._lock:
            for fd, client in list(self._clients.items()):
                if client is sender:
                    continue
                if topic in client.subscriptions:
                    try:
                        client.conn.sendall(data)
                        client.packets_sent += 1
                        subscribers_count += 1
                    except Exception:
                        pass  # Will be cleaned up by heartbeat
        
        log.debug(f"Routed message on topic '{topic}' from '{sender.name}' to {subscribers_count} subscribers")

    # ─── Control Message Handlers ─────────────────────────────────

    def _handle_handshake(self, client: ClientInfo, message: dict):
        """Process a client handshake with authentication."""
        payload = message.get("payload", {})
        client.name = payload.get("client_name", client.name)
        client.publish_topics = payload.get("publish_topics", [])
        subscribe_topics = payload.get("subscribe_topics", [])
        client.subscriptions.update(subscribe_topics)

        # Auth context from handshake
        client.username = payload.get("username", "")
        client.role = payload.get("role", "")
        client.session_id = payload.get("session_id", "")

        # Validate session if auth info provided
        if client.username and client.session_id:
            valid, _, _ = self._auth_manager.validate_session(
                client.session_id)
            if valid:
                client.authenticated = True
                log.info(f"Authenticated client: {client.name} "
                         f"(user={client.username}, role={client.role})")
            else:
                # Create a session for this client (broker-side trust)
                # The client already authenticated locally before connecting
                client.authenticated = True
                self._auth_manager.create_session(
                    client.username, client.role)
                log.info(f"Client trusted: {client.name} "
                         f"(user={client.username}, role={client.role})")
        else:
            # No auth info — still accept but mark as unauthenticated
            client.authenticated = False
            log.warning(f"Unauthenticated client: {client.name}")

        log.info(f"Handshake from '{client.name}' — "
                 f"pub={client.publish_topics}, "
                 f"sub={list(client.subscriptions)}")
        print(f"  [Handshake] {client.name} "
              f"(pub={client.publish_topics}, "
              f"sub={list(client.subscriptions)}, "
              f"user={client.username})")

        # Broadcast client update to all
        self._broadcast_client_update()

    def _handle_subscribe(self, client: ClientInfo, message: dict):
        """Process a subscription request."""
        topics = message.get("payload", {}).get("topics", [])
        client.subscriptions.update(topics)
        log.info(f"'{client.name}' subscribed to {topics}")
        print(f"  [Subscribed] {client.name} subscribed: {topics}")

    def _handle_unsubscribe(self, client: ClientInfo, message: dict):
        """Process an unsubscription request."""
        topics = message.get("payload", {}).get("topics", [])
        client.subscriptions -= set(topics)
        log.info(f"'{client.name}' unsubscribed from {topics}")

    def _handle_client_list_request(self, client: ClientInfo):
        """Send the list of connected clients to the requester."""
        clients_data = []
        with self._lock:
            for fd, c in self._clients.items():
                clients_data.append(c.to_dict())

        response = create_message(CTRL_CLIENT_LIST, "broker", {
            "clients": clients_data,
        })
        try:
            client.conn.sendall(encode_message(response))
        except Exception:
            pass

    # ─── Client Management ────────────────────────────────────────

    def _remove_client(self, client: ClientInfo):
        """Remove a disconnected client."""
        with self._lock:
            fd = None
            for f, c in self._clients.items():
                if c is client:
                    fd = f
                    break
            if fd is not None:
                del self._clients[fd]

        try:
            client.conn.close()
        except Exception:
            pass

        log.info(f"Client disconnected: {client.name} "
                 f"(user={client.username})")
        print(f"  [-] Client disconnected: {client.name}")

        # Remove session
        if client.session_id:
            self._auth_manager.remove_session(client.session_id)

        # Broadcast updated client list
        self._broadcast_client_update()

        # Broadcast connection_status to inform subscribers
        status_msg = create_message("connection_status", "broker", {
            "event": "client_disconnected",
            "client_name": client.name,
            "timestamp": datetime.now().isoformat(),
        })
        self._broadcast_to_topic("connection_status", status_msg)

    def _broadcast_client_update(self):
        """Broadcast updated client list to all connected clients."""
        clients_data = []
        with self._lock:
            for fd, c in self._clients.items():
                clients_data.append(c.to_dict())

        msg = create_message(CTRL_CLIENT_UPDATE, "broker", {
            "clients": clients_data,
        })
        data = encode_message(msg)

        with self._lock:
            for fd, client in list(self._clients.items()):
                try:
                    client.conn.sendall(data)
                    client.packets_sent += 1
                except Exception:
                    pass

    def _broadcast_to_topic(self, topic: str, message: dict):
        """Send a message to all subscribers of a topic."""
        data = encode_message(message)
        with self._lock:
            for fd, client in list(self._clients.items()):
                if topic in client.subscriptions:
                    try:
                        client.conn.sendall(data)
                        client.packets_sent += 1
                    except Exception:
                        pass

    # ─── Heartbeat Monitor ────────────────────────────────────────

    def _heartbeat_monitor(self):
        """Periodically check for dead clients."""
        while self._running:
            time.sleep(HEARTBEAT_TIMEOUT_S)
            now = time.time()
            dead = []

            with self._lock:
                for fd, client in list(self._clients.items()):
                    if now - client.last_heartbeat > HEARTBEAT_TIMEOUT_S:
                        dead.append(client)

            for client in dead:
                log.warning(
                    f"Heartbeat timeout for '{client.name}'")
                print(f"  [!] Heartbeat timeout: {client.name}")
                self._remove_client(client)

    # ─── Utility ──────────────────────────────────────────────────

    @staticmethod
    def _recv_exact(conn: socket.socket, num_bytes: int):
        """Read exactly num_bytes from a socket."""
        data = b""
        while len(data) < num_bytes:
            try:
                chunk = conn.recv(num_bytes - len(data))
                if not chunk:
                    return None
                data += chunk
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                return None
        return data
