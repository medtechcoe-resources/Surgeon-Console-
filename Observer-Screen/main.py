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

from shared_networking.encryption import EncryptionManager
from shared_networking.authentication import AuthManager
from shared_networking.login_dialog import LoginDialog
from shared_networking.config import ENCRYPTION_KEY_PATH


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Clinical Observer Screen")

    # Apply stylesheet
    app.setStyleSheet(generate_stylesheet())

    # ── Initialize Encryption ─────────────────────────────────
    em = EncryptionManager.instance()
    if not em.load_key(ENCRYPTION_KEY_PATH):
        EncryptionManager.generate_key(ENCRYPTION_KEY_PATH)
        em.load_key(ENCRYPTION_KEY_PATH)

    # ── Initialize Authentication ─────────────────────────────
    auth = AuthManager()

    # ── Show Login Dialog ─────────────────────────────────────
    login = LoginDialog(
        title="Observer Screen — Login",
        auth_manager=auth,
    )
    if login.exec() != LoginDialog.DialogCode.Accepted:
        sys.exit(0)

    # ── Launch Main Window ────────────────────────────────────
    window = MainWindow(
        username=login.username,
        role=login.role,
        session_id=login.session_id,
    )
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
