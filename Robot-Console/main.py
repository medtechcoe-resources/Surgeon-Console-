# ═══════════════════════════════════════════════════════════════════
#  ROBOT CONSOLE — APPLICATION ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

import sys
import os

# Ensure project root is on sys.path for the shared networking package
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

from shared_networking.encryption import EncryptionManager
from shared_networking.authentication import AuthManager
from shared_networking.login_dialog import LoginDialog
from shared_networking.config import ENCRYPTION_KEY_PATH


def main():
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Robot Console")
    app.setOrganizationName("MedRobot")
    app.setApplicationVersion("1.0")

    # ── Initialize Encryption ─────────────────────────────────
    em = EncryptionManager.instance()
    if not em.load_key(ENCRYPTION_KEY_PATH):
        EncryptionManager.generate_key(ENCRYPTION_KEY_PATH)
        em.load_key(ENCRYPTION_KEY_PATH)

    # ── Initialize Authentication ─────────────────────────────
    auth = AuthManager()

    # ── Show Login Dialog ─────────────────────────────────────
    login = LoginDialog(
        title="Robot Console — Login",
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
