"""
ThemeManager — Singleton that owns the current theme and broadcasts changes.

Usage:
    from theme_manager import ThemeManager
    tm = ThemeManager.instance()
    tm.theme_changed.connect(my_widget.on_theme_changed)
    color = tm.color("accent_blue")
"""
import os
from PyQt6.QtCore import QObject, pyqtSignal, QSettings
from PyQt6.QtWidgets import QApplication


# ── Color Palettes ─────────────────────────────────────────────────────────

_DARK_PALETTE = {
    # Backgrounds
    "bg_base":      "#0D1117",
    "bg_surface":   "#0F1419",
    "bg_card":      "#171C22",
    "bg_header":    "#131820",
    "bg_panel":     "#131820",
    "bg_input":     "#161B22",
    "bg_chip":      "#161B22",
    # Borders
    "border":       "#1C2333",
    "border_heavy": "#2D3748",
    # Foregrounds
    "fg_primary":   "#F5F7FA",
    "fg_secondary": "#E6EDF3",
    "fg_muted":     "#6B7B8D",
    "fg_dim":       "#4A5568",
    # Accents
    "accent_blue":   "#0095FF",
    "accent_green":  "#10B981",
    "accent_amber":  "#F59E0B",
    "accent_red":    "#EF4444",
    "accent_purple": "#8B5CF6",
    # Semantic
    "status_good":     "#10B981",
    "status_caution":  "#F59E0B",
    "status_critical": "#EF4444",
    # Robot sim
    "robot_bg":    "#0F1419",
    "robot_link":  "#0095FF",
    "robot_joint": "#10B981",
    "robot_tip":   "#F59E0B",
    "robot_text":  "#B5BEC8",
    "robot_grid":  "#1C2333",
}

_LIGHT_PALETTE = {
    # Backgrounds
    "bg_base":      "#F0F4F8",
    "bg_surface":   "#F8FAFC",
    "bg_card":      "#FFFFFF",
    "bg_header":    "#FFFFFF",
    "bg_panel":     "#F8FAFC",
    "bg_input":     "#EEF2F7",
    "bg_chip":      "#EEF2F7",
    # Borders
    "border":       "#E2E8F0",
    "border_heavy": "#CBD5E1",
    # Foregrounds
    "fg_primary":   "#0F172A",
    "fg_secondary": "#1E293B",
    "fg_muted":     "#64748B",
    "fg_dim":       "#94A3B8",
    # Accents
    "accent_blue":   "#0077CC",
    "accent_green":  "#059669",
    "accent_amber":  "#D97706",
    "accent_red":    "#DC2626",
    "accent_purple": "#7C3AED",
    # Semantic
    "status_good":     "#059669",
    "status_caution":  "#D97706",
    "status_critical": "#DC2626",
    # Robot sim
    "robot_bg":    "#F0F4F8",
    "robot_link":  "#0077CC",
    "robot_joint": "#059669",
    "robot_tip":   "#D97706",
    "robot_text":  "#475569",
    "robot_grid":  "#E2E8F0",
}


class ThemeManager(QObject):
    """Application-wide theme singleton."""

    theme_changed = pyqtSignal(str)   # emits "dark" or "light"

    _instance = None

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    def __init__(self):
        super().__init__()
        self._settings = QSettings("AetherSurgical", "AetherConsole")
        saved = self._settings.value("theme", "dark")
        self._theme = saved if saved in ("dark", "light") else "dark"

    # ── Public API ────────────────────────────────────────────────────────

    @property
    def current(self) -> str:
        return self._theme

    def is_dark(self) -> bool:
        return self._theme == "dark"

    def toggle(self):
        self._theme = "light" if self._theme == "dark" else "dark"
        self._settings.setValue("theme", self._theme)
        self._apply_qss()
        self.theme_changed.emit(self._theme)

    def apply_initial(self):
        """Call once at startup to apply the saved theme."""
        self._apply_qss()

    def color(self, name: str) -> str:
        """Return a hex color string for the current theme."""
        palette = _DARK_PALETTE if self._theme == "dark" else _LIGHT_PALETTE
        return palette.get(name, "#FF00FF")   # magenta = missing key

    # ── Internal ──────────────────────────────────────────────────────────

    def _apply_qss(self):
        app = QApplication.instance()
        if app is None:
            return
        filename = "theme_light.qss" if self._theme == "light" else "theme.qss"
        qss_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "styles", filename
        )
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        except FileNotFoundError:
            pass
