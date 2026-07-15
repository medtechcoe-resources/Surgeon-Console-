# ═══════════════════════════════════════════════════════════════════
#  AETHER CONSOLE — LOGIN DIALOG
#  Professional medical-grade modal login screen.
#  Shared by all three applications (Surgeon, Robot, Observer).
#  No registration, sign-up, or forgot-password functionality.
# ═══════════════════════════════════════════════════════════════════

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QWidget, QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor

from shared_networking.authentication import AuthManager


class LoginDialog(QDialog):
    """Modal login dialog for Aether Console applications.

    Usage:
        dialog = LoginDialog(title="Surgeon Console — Login")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            username = dialog.username
            role = dialog.role
            session_id = dialog.session_id
    """

    def __init__(self, title: str = "Aether Console — Login",
                 auth_manager: AuthManager = None, parent=None):
        super().__init__(parent)
        self._auth = auth_manager or AuthManager()
        self._title_text = title

        # Result properties
        self.username = ""
        self.role = ""
        self.session_id = ""

        self.setWindowTitle(title)
        self.setFixedSize(480, 540)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setModal(True)

        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Background frame
        bg = QFrame()
        bg.setObjectName("LoginBackground")
        main = QVBoxLayout(bg)
        main.setContentsMargins(40, 40, 40, 40)
        main.setSpacing(0)

        # ── Top accent line ──
        accent = QFrame()
        accent.setFixedHeight(4)
        accent.setObjectName("LoginAccent")
        main.addWidget(accent)
        main.addSpacing(24)

        # ── Logo / Title area ──
        logo_label = QLabel("⬡")
        logo_label.setObjectName("LoginLogo")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(logo_label)
        main.addSpacing(8)

        system_label = QLabel("AETHER SURGICAL CONSOLE")
        system_label.setObjectName("LoginSystemName")
        system_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(system_label)
        main.addSpacing(4)

        title_label = QLabel(self._title_text.upper())
        title_label.setObjectName("LoginTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(title_label)
        main.addSpacing(6)

        # Subtitle
        sub = QLabel("Secure Authentication Required")
        sub.setObjectName("LoginSubtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(sub)
        main.addSpacing(28)

        # ── Separator ──
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setObjectName("LoginSeparator")
        main.addWidget(sep)
        main.addSpacing(24)

        # ── Username field ──
        user_label = QLabel("USERNAME")
        user_label.setObjectName("LoginFieldLabel")
        main.addWidget(user_label)
        main.addSpacing(6)

        self._username_input = QLineEdit()
        self._username_input.setObjectName("LoginInput")
        self._username_input.setPlaceholderText("Enter username")
        self._username_input.setFixedHeight(44)
        main.addWidget(self._username_input)
        main.addSpacing(16)

        # ── Password field ──
        pw_label = QLabel("PASSWORD")
        pw_label.setObjectName("LoginFieldLabel")
        main.addWidget(pw_label)
        main.addSpacing(6)

        self._password_input = QLineEdit()
        self._password_input.setObjectName("LoginInput")
        self._password_input.setPlaceholderText("Enter password")
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.setFixedHeight(44)
        self._password_input.returnPressed.connect(self._on_login)
        main.addWidget(self._password_input)
        main.addSpacing(12)

        # ── Error message ──
        self._error_label = QLabel("")
        self._error_label.setObjectName("LoginError")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setWordWrap(True)
        self._error_label.setVisible(False)
        main.addWidget(self._error_label)
        main.addSpacing(8)

        # ── Login button ──
        self._login_btn = QPushButton("LOGIN")
        self._login_btn.setObjectName("LoginButton")
        self._login_btn.setFixedHeight(46)
        self._login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._login_btn.clicked.connect(self._on_login)
        main.addWidget(self._login_btn)

        main.addStretch()

        # ── Footer ──
        footer = QLabel("Aether Surgical Robotics · Secure LAN Access")
        footer.setObjectName("LoginFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(footer)

        outer.addWidget(bg)

    def _on_login(self):
        """Handle login button click."""
        username = self._username_input.text().strip()
        password = self._password_input.text()

        # Validate inputs
        if not username:
            self._show_error("Username cannot be empty.")
            self._username_input.setFocus()
            return

        if not password:
            self._show_error("Password cannot be empty.")
            self._password_input.setFocus()
            return

        # Verify credentials
        success, role = self._auth.verify(username, password)

        if success:
            self.username = username
            self.role = role
            self.session_id = self._auth.create_session(username, role)
            self.accept()
        else:
            self._show_error("Invalid username or password.")
            self._password_input.clear()
            self._password_input.setFocus()

    def _show_error(self, message: str):
        """Display an error message."""
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    def _apply_styles(self):
        """Apply dark medical-grade styling."""
        self.setStyleSheet("""
            #LoginBackground {
                background-color: #0D1117;
            }

            #LoginAccent {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0095FF, stop:0.5 #00D4AA, stop:1 #0095FF
                );
                border-radius: 2px;
            }

            #LoginLogo {
                color: #0095FF;
                font-size: 36px;
                font-weight: bold;
            }

            #LoginSystemName {
                color: #6B7B8D;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 3px;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
            }

            #LoginTitle {
                color: #E6EDF3;
                font-size: 15px;
                font-weight: 700;
                letter-spacing: 1px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }

            #LoginSubtitle {
                color: #4A5568;
                font-size: 12px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }

            #LoginSeparator {
                background-color: #1C2333;
            }

            #LoginFieldLabel {
                color: #6B7B8D;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1.5px;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
            }

            #LoginInput {
                background-color: #161B22;
                color: #E6EDF3;
                border: 1px solid #2D3748;
                border-radius: 8px;
                padding: 0 14px;
                font-size: 14px;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
            }

            #LoginInput:focus {
                border: 1px solid #0095FF;
            }

            #LoginInput::placeholder {
                color: #4A5568;
            }

            #LoginError {
                color: #EF4444;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                background-color: rgba(239, 68, 68, 0.08);
                border: 1px solid rgba(239, 68, 68, 0.2);
                border-radius: 6px;
                padding: 8px;
            }

            #LoginButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0077CC, stop:1 #0095FF
                );
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 700;
                letter-spacing: 2px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }

            #LoginButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0095FF, stop:1 #00B4FF
                );
            }

            #LoginButton:pressed {
                background-color: #005FA3;
            }

            #LoginFooter {
                color: #3A4A5C;
                font-size: 10px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
        """)
