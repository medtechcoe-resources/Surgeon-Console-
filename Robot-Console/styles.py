# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — QSS STYLESHEET GENERATOR
#  Translates the clinical color system into Qt stylesheets.
#  Scaled for 3440×1440 ultrawide display.
# ═══════════════════════════════════════════════════════════════════

from constants import C


def generate_stylesheet() -> str:
    """Generate a complete QSS stylesheet matching the Surgeon Console design.
    Font sizes and paddings scaled for 3440×1440."""
    return f"""
    /* ── Global ───────────────────────────────────────────────── */
    QMainWindow {{
        background-color: {C['bg0']};
    }}
    QWidget {{
        font-family: "Consolas", "Courier New", monospace;
        color: {C['txt0']};
    }}

    /* ── Tab Widget ───────────────────────────────────────────── */
    QTabWidget::pane {{
        border: none;
        background-color: {C['bg0']};
    }}
    QTabBar {{
        background-color: {C['bg1']};
        border: none;
    }}
    QTabBar::tab {{
        background-color: {C['bg2']};
        color: {C['txt2']};
        font-family: "Consolas";
        font-size: 18px;
        font-weight: bold;
        padding: 16px 32px;
        margin-right: 2px;
        border: none;
        border-bottom: 3px solid transparent;
    }}
    QTabBar::tab:selected {{
        background-color: {C['cyan_bg']};
        color: {C['cyan']};
        border-bottom: 3px solid {C['cyan']};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {C['bg3']};
        color: {C['txt1']};
    }}

    /* ── Scroll Bars ──────────────────────────────────────────── */
    QScrollBar:vertical {{
        background: {C['bg1']};
        width: 14px;
        border: none;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {C['border']};
        border-radius: 6px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {C['border2']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {C['bg1']};
        height: 14px;
        border: none;
    }}
    QScrollBar::handle:horizontal {{
        background: {C['border']};
        border-radius: 6px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {C['border2']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* ── Table Widget ─────────────────────────────────────────── */
    QTableWidget {{
        background-color: {C['bg2']};
        border: 1px solid {C['border']};
        gridline-color: {C['bg3']};
        font-family: "Consolas";
        font-size: 18px;
        selection-background-color: {C['cyan_bg']};
        selection-color: {C['cyan']};
    }}
    QTableWidget::item {{
        padding: 10px 14px;
        border-bottom: 1px solid {C['bg3']};
    }}
    QHeaderView::section {{
        background-color: {C['bg3']};
        color: {C['cyan']};
        font-family: "Consolas";
        font-size: 18px;
        font-weight: bold;
        padding: 10px 14px;
        border: none;
        border-right: 1px solid {C['border']};
        border-bottom: 1px solid {C['border']};
    }}

    /* ── Text Edit / Plain Text ───────────────────────────────── */
    QTextEdit, QPlainTextEdit {{
        background-color: {C['bg2']};
        color: {C['txt0']};
        border: 1px solid {C['border']};
        font-family: "Consolas";
        font-size: 18px;
        padding: 10px;
        selection-background-color: {C['cyan_bg']};
        selection-color: {C['cyan']};
    }}

    /* ── Line Edit ────────────────────────────────────────────── */
    QLineEdit {{
        background-color: {C['bg3']};
        color: {C['txt0']};
        border: 1px solid {C['border']};
        font-family: "Consolas";
        font-size: 20px;
        padding: 10px 14px;
    }}
    QLineEdit:focus {{
        border: 1px solid {C['cyan']};
    }}

    /* ── Push Buttons ─────────────────────────────────────────── */
    QPushButton {{
        font-family: "Consolas";
        font-size: 20px;
        font-weight: bold;
        padding: 14px 24px;
        border: none;
        border-radius: 0px;
    }}
    QPushButton:hover {{
        opacity: 0.9;
    }}

    /* ── Tooltips ──────────────────────────────────────────────── */
    QToolTip {{
        background-color: {C['txt0']};
        color: white;
        font-family: "Consolas";
        font-size: 16px;
        padding: 8px 12px;
        border: none;
    }}

    /* ── Splitter ──────────────────────────────────────────────── */
    QSplitter::handle {{
        background-color: {C['border']};
    }}
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    QSplitter::handle:vertical {{
        height: 2px;
    }}
    """
