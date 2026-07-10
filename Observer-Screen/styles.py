# ═══════════════════════════════════════════════════════════════════
#  OBSERVER SCREEN — STYLESHEET
#  Defines QSS styling for the dark monitoring theme.
# ═══════════════════════════════════════════════════════════════════

from config import C


def generate_stylesheet() -> str:
    """Generate a clean dark theme QSS for the Observer Screen."""
    return f"""
    QMainWindow {{
        background-color: {C['bg0']};
    }}
    QWidget {{
        font-family: "JetBrains Mono", "Consolas", monospace;
        color: {C['txt0']};
        background-color: transparent;
    }}
    QFrame#Card {{
        background-color: {C['bg1']};
        border: 1px solid {C['border']};
        border-radius: 8px;
    }}
    QTableWidget {{
        background-color: {C['bg1']};
        border: 1px solid {C['border']};
        gridline-color: {C['bg2']};
        font-size: 11px;
    }}
    QTableWidget::item {{
        padding: 4px 6px;
        border-bottom: 1px solid {C['bg2']};
    }}
    QHeaderView::section {{
        background-color: {C['bg2']};
        color: {C['cyan']};
        font-weight: bold;
        font-size: 11px;
        padding: 6px;
        border: none;
        border-right: 1px solid {C['border']};
        border-bottom: 1px solid {C['border']};
    }}
    QTextEdit {{
        background-color: {C['bg1']};
        color: {C['txt1']};
        border: 1px solid {C['border']};
        font-size: 11px;
        padding: 6px;
    }}
    QScrollBar:vertical {{
        background: {C['bg1']};
        width: 8px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {C['border']};
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {C['border2']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    """
