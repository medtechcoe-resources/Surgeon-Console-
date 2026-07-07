# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — JSON MESSAGE PROTOCOL
#  Defines the wire format for TCP communication between
#  the Robot Console and the Surgeon Console.
# ═══════════════════════════════════════════════════════════════════

import json
import struct
from datetime import datetime
from typing import Optional, Tuple


# ─── Message Types ────────────────────────────────────────────────
MSG_ROBOT_TELEMETRY = "ROBOT_TELEMETRY"
MSG_VITALS_DATA     = "VITALS_DATA"
MSG_HEARTBEAT       = "HEARTBEAT"
MSG_ALERT           = "ALERT"
MSG_HANDSHAKE       = "HANDSHAKE"
MSG_ACK             = "ACK"

# ─── Header: 4-byte big-endian unsigned int (payload length) ─────
HEADER_SIZE = 4
HEADER_FORMAT = "!I"


def create_message(msg_type: str, payload: dict) -> dict:
    """Wrap a payload in a standard message envelope."""
    return {
        "type": msg_type,
        "timestamp": datetime.now().isoformat(),
        "payload": payload,
    }


def create_heartbeat() -> dict:
    """Create a heartbeat message."""
    return create_message(MSG_HEARTBEAT, {"status": "alive"})


def create_handshake(client_name: str) -> dict:
    """Create a handshake message for initial connection."""
    return create_message(MSG_HANDSHAKE, {
        "client_name": client_name,
        "version": "1.0",
    })


def encode_message(message: dict) -> bytes:
    """Encode a message dict into length-prefixed bytes for TCP transmission.

    Format: [4-byte length header][JSON payload bytes]
    """
    payload_bytes = json.dumps(message, separators=(",", ":")).encode("utf-8")
    header = struct.pack(HEADER_FORMAT, len(payload_bytes))
    return header + payload_bytes


def decode_header(header_bytes: bytes) -> int:
    """Decode the 4-byte length header to get payload size."""
    if len(header_bytes) != HEADER_SIZE:
        raise ValueError(f"Invalid header size: {len(header_bytes)}")
    return struct.unpack(HEADER_FORMAT, header_bytes)[0]


def decode_payload(payload_bytes: bytes) -> dict:
    """Decode JSON payload bytes into a message dict."""
    return json.loads(payload_bytes.decode("utf-8"))


def format_json_pretty(data: dict) -> str:
    """Format a dict as pretty-printed JSON for display."""
    return json.dumps(data, indent=2, default=str)
