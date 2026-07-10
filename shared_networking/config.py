# ═══════════════════════════════════════════════════════════════════
#  AETHER CONSOLE — NETWORKING CONFIGURATION
#  Single source of truth for all networking parameters.
#  Import from here instead of hardcoding values.
# ═══════════════════════════════════════════════════════════════════

# ─── Broker / Server ─────────────────────────────────────────────
BROKER_HOST = "127.0.0.1"
BROKER_PORT = 5000

# ─── Heartbeat ───────────────────────────────────────────────────
HEARTBEAT_INTERVAL_S = 2          # Send heartbeat every 2 seconds
HEARTBEAT_TIMEOUT_S = 6           # Consider dead after 3 missed heartbeats

# ─── Reconnection ────────────────────────────────────────────────
RECONNECT_INTERVAL_S = 3          # Wait 3 seconds before reconnect attempt
MAX_RECONNECT_ATTEMPTS = 0        # 0 = unlimited

# ─── Topics ──────────────────────────────────────────────────────
TOPICS = [
    "patient_vitals",
    "robot_telemetry",
    "alerts",
    "system_status",
    "connection_status",
]

# ─── Wire Protocol ───────────────────────────────────────────────
HEADER_SIZE = 4                   # 4-byte big-endian unsigned int
HEADER_FORMAT = "!I"              # struct format
MAX_PAYLOAD_SIZE = 10 * 1024 * 1024   # 10 MB safety limit

# ─── Publish Intervals ──────────────────────────────────────────
VITALS_PUBLISH_INTERVAL_S = 1.0   # Surgeon Console publishes vitals every 1s
TELEMETRY_PUBLISH_INTERVAL_S = 1.0  # Robot Console publishes telemetry every 1s
