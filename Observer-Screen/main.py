# ═══════════════════════════════════════════════════════════════════
#  OBSERVER SCREEN — STANDALONE MONITORING APPLICATION
# ═══════════════════════════════════════════════════════════════════

import sys
import os

# Add parent directory of Observer-Screen to path to import shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from styles import generate_stylesheet


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Clinical Observer Screen")

    # Apply stylesheet
    app.setStyleSheet(generate_stylesheet())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
