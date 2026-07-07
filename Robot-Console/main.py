# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — APPLICATION ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Robot Console")
    app.setOrganizationName("MedRobot")
    app.setApplicationVersion("1.0")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
