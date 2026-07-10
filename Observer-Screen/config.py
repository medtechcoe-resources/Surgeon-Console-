# ═══════════════════════════════════════════════════════════════════
#  OBSERVER SCREEN — CONFIGURATION
#  Imports shared settings and defines observer-specific parameters.
# ═══════════════════════════════════════════════════════════════════

import sys
import os

_proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _proj_root not in sys.path:
    sys.path.insert(0, _proj_root)

from shared_networking.config import BROKER_HOST, BROKER_PORT, TOPICS

# ─── Window Configuration ────────────────────────────────────────
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
WINDOW_TITLE = "AETHER CLINICAL OBSERVER SCREEN"

# ─── Palette ─────────────────────────────────────────────────────
# Dark monitoring style
C = {
    "bg0":      "#090d16",       # Deep black/blue
    "bg1":      "#111827",       # Dark blue gray
    "bg2":      "#1f2937",       # Medium blue gray
    "bg3":      "#374151",       # Light blue gray
    "border":   "#2D3748",
    "border2":  "#4A5568",

    "cyan":     "#00b4d8",
    "green":    "#10b981",
    "amber":    "#f59e0b",
    "red":      "#ef4444",
    "violet":   "#8b5cf6",
    "teal":     "#14b8a6",
    "pink":     "#ec4899",

    "txt0":     "#f9fafb",       # White
    "txt1":     "#e5e7eb",       # Off-white
    "txt2":     "#9ca3af",       # Gray
}
