# ═══════════════════════════════════════════════════════════════════
#  AETHER CONSOLE — PUB-SUB WIRE PROTOCOL
#  Defines the message envelope format and encoding/decoding for
#  TCP communication between broker and clients.
#  Reuses the length-prefixed JSON approach from Robot-Console.
# ═══════════════════════════════════════════════════════════════════

import json
import struct
from datetime import datetime
from typing import Optional

from shared_networking.config import HEADER_SIZE, HEADER_FORMAT, MAX_PAYLOAD_SIZE


# ─── Internal Control Topics ─────────────────────────────────────
CTRL_SUBSCRIBE = "_subscribe"
CTRL_UNSUBSCRIBE = "_unsubscribe"
CTRL_HEARTBEAT = "_heartbeat"
CTRL_HANDSHAKE = "_handshake"
CTRL_CLIENT_LIST = "_client_list"
CTRL_CLIENT_UPDATE = "_client_update"


def create_message(topic: str, source: str, payload: dict) -> dict:
    """Create a standard pub-sub message envelope."""
    return {
        "topic": topic,
        "source": source,
        "timestamp": datetime.now().isoformat(),
        "payload": payload,
    }


def create_heartbeat(source: str) -> dict:
    """Create a heartbeat control message."""
    return create_message(CTRL_HEARTBEAT, source, {"status": "alive"})


def create_handshake(client_name: str, publish_topics: list = None,
                     subscribe_topics: list = None) -> dict:
    """Create a handshake message for initial broker registration."""
    return create_message(CTRL_HANDSHAKE, client_name, {
        "client_name": client_name,
        "version": "1.0",
        "publish_topics": publish_topics or [],
        "subscribe_topics": subscribe_topics or [],
    })


def create_subscribe(source: str, topics: list) -> dict:
    """Create a subscription request message."""
    return create_message(CTRL_SUBSCRIBE, source, {"topics": topics})


def create_unsubscribe(source: str, topics: list) -> dict:
    """Create an unsubscription request message."""
    return create_message(CTRL_UNSUBSCRIBE, source, {"topics": topics})


def create_client_list_request(source: str) -> dict:
    """Create a request for the list of connected clients."""
    return create_message(CTRL_CLIENT_LIST, source, {})


# ─── Encoding / Decoding ─────────────────────────────────────────

def encode_message(message: dict) -> bytes:
    """Encode a message dict into length-prefixed bytes for TCP.

    Format: [4-byte length header][JSON payload bytes]
    """
    payload_bytes = json.dumps(message, separators=(",", ":"),
                               default=str).encode("utf-8")
    header = struct.pack(HEADER_FORMAT, len(payload_bytes))
    return header + payload_bytes


def decode_header(header_bytes: bytes) -> int:
    """Decode the 4-byte length header to get payload size."""
    if len(header_bytes) != HEADER_SIZE:
        raise ValueError(f"Invalid header size: {len(header_bytes)}")
    length = struct.unpack(HEADER_FORMAT, header_bytes)[0]
    if length > MAX_PAYLOAD_SIZE:
        raise ValueError(f"Payload too large: {length} bytes")
    return length


def decode_payload(payload_bytes: bytes) -> dict:
    """Decode JSON payload bytes into a message dict."""
    return json.loads(payload_bytes.decode("utf-8"))


def format_json_pretty(data: dict) -> str:
    """Format a dict as pretty-printed JSON for display."""
    return json.dumps(data, indent=2, default=str)


def is_control_message(message: dict) -> bool:
    """Check if a message is an internal control message."""
    topic = message.get("topic", "")
    return topic.startswith("_")
