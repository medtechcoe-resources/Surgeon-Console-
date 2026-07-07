# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — CONSTANTS
#  Matches the Surgeon Console clinical design language exactly.
# ═══════════════════════════════════════════════════════════════════

# ─── COLOR SYSTEM — Light Cool Clinical Theme ────────────────────
C = {
    "bg0":      "#eef2f7",
    "bg1":      "#f7f9fc",
    "bg2":      "#ffffff",
    "bg3":      "#dde6f0",

    "border":   "#c8d8e8",
    "border2":  "#a0bcd4",

    "cyan":     "#0077b6",
    "green":    "#0a9e6a",
    "amber":    "#d4860a",
    "red":      "#d63031",
    "violet":   "#6c5ce7",
    "teal":     "#00897b",
    "pink":     "#e84393",

    "txt0":     "#0d1b2a",
    "txt1":     "#3a5068",
    "txt2":     "#7a97b0",

    "link1":    "#0077b6",
    "link2":    "#d4860a",
    "link3":    "#6c5ce7",
    "ee":       "#0a9e6a",
    "grid":     "#d0dce8",

    "red_bg":   "#fff0f0",
    "amber_bg": "#fffbf0",
    "green_bg": "#f0faf6",
    "cyan_bg":  "#f0f8ff",
}

# ─── NETWORK CONFIGURATION ───────────────────────────────────────
TCP_HOST = "127.0.0.1"
TCP_PORT = 5000
HEARTBEAT_INTERVAL_MS = 3000       # Send heartbeat every 3s
RECONNECT_DELAY_MS = 5000          # Wait 5s before reconnect attempt
MAX_RECONNECT_ATTEMPTS = 10

# ─── TELEMETRY CONFIGURATION ─────────────────────────────────────
TELEMETRY_UPDATE_INTERVAL_MS = 600   # 100 updates/min ≈ 600ms
NUM_JOINTS = 6

# Joint angle limits (degrees)
JOINT_LIMITS = [
    (-170, 170),   # J1
    (-120, 120),   # J2
    (-170, 170),   # J3
    (-120, 120),   # J4
    (-170, 170),   # J5
    (-120, 120),   # J6
]

# ─── ALERT CONFIGURATION ─────────────────────────────────────────
ALERT_INTERVAL_MS = 60000            # 1 alert per minute

ALERT_TEMPLATES = [
    {"severity": "WARNING",  "source": "Joint Controller",  "message": "Joint Torque High"},
    {"severity": "WARNING",  "source": "Thermal Monitor",   "message": "Servo Temperature High"},
    {"severity": "INFO",     "source": "Calibration Sys.",   "message": "Calibration Required"},
    {"severity": "WARNING",  "source": "Network Monitor",   "message": "Network Delay Warning"},
    {"severity": "WARNING",  "source": "Motion Planner",    "message": "Motion Limit Approaching"},
    {"severity": "CRITICAL", "source": "Safety System",     "message": "Emergency Stop Triggered"},
    {"severity": "WARNING",  "source": "Sensor Array",      "message": "Sensor Validation Warning"},
    {"severity": "INFO",     "source": "System Controller",  "message": "System Health Check OK"},
    {"severity": "WARNING",  "source": "Force Sensor",      "message": "End Effector Force Spike"},
    {"severity": "INFO",     "source": "Motion Planner",    "message": "Trajectory Replanned"},
]

# ─── WINDOW CONFIGURATION ────────────────────────────────────────
WINDOW_WIDTH = 2560
WINDOW_HEIGHT = 1080
WINDOW_TITLE = "ROBOT CONSOLE  //  MEDROBOT OS v4.2"
