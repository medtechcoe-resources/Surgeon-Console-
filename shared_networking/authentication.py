# ═══════════════════════════════════════════════════════════════════
#  AETHER CONSOLE — AUTHENTICATION MODULE
#  Local credential management using bcrypt + encrypted JSON file.
#  Designed for exactly 2 accounts (admin + user) on a private LAN.
#  No JWT, no tokens, no expiry, no registration, no password recovery.
# ═══════════════════════════════════════════════════════════════════

import json
import os
import uuid
import logging
from typing import Optional, Tuple

import bcrypt

from shared_networking.config import CREDENTIALS_PATH

log = logging.getLogger(__name__)

# Minimum password length
MIN_PASSWORD_LENGTH = 6

# Default accounts (created on first run)
_DEFAULT_ACCOUNTS = {
    "admin": {"role": "admin"},
    "user":  {"role": "user"},
}
_DEFAULT_PASSWORDS = {
    "admin": "admin123",
    "user":  "user123",
}


class AuthManager:
    """Manages local authentication for all Aether Console applications.

    Credentials are stored in a JSON file with bcrypt-hashed passwords.
    Only two accounts exist: admin and user. No registration is supported.

    Usage:
        auth = AuthManager()
        success, role = auth.verify("admin", "admin123")
        if success:
            session_id = auth.create_session("admin", role)
    """

    def __init__(self, credentials_path: str = None):
        self._path = credentials_path or CREDENTIALS_PATH
        self._credentials: dict = {}
        self._sessions: dict = {}  # session_id -> {username, role}

        self._load_or_create()

    # ─── Public API ───────────────────────────────────────────────

    def verify(self, username: str, password: str) -> Tuple[bool, str]:
        """Verify a username/password combination.

        Returns:
            (True, role) on success
            (False, "") on failure
        """
        if not username or not password:
            log.warning("[AUTH] Empty username or password")
            return False, ""

        user = self._credentials.get(username)
        if user is None:
            log.warning(f"[AUTH] Login failed — unknown user: {username}")
            return False, ""

        stored_hash = user.get("password_hash", "")
        if not stored_hash:
            log.error(f"[AUTH] No password hash for user: {username}")
            return False, ""

        try:
            if bcrypt.checkpw(password.encode("utf-8"),
                              stored_hash.encode("utf-8")):
                role = user.get("role", "user")
                log.info(f"[AUTH] Login successful: {username} (role={role})")
                return True, role
            else:
                log.warning(f"[AUTH] Login failed — wrong password: {username}")
                return False, ""
        except Exception as e:
            log.error(f"[AUTH] Password verification error: {e}")
            return False, ""

    def change_password(self, username: str, current_password: str,
                        new_password: str, requesting_role: str) -> Tuple[bool, str]:
        """Change a user's password.

        Rules:
            - Only admin role can change passwords
            - Admin can only change their own password
            - New password must meet minimum length requirement

        Returns:
            (True, "Password changed successfully") on success
            (False, "Error message") on failure
        """
        # Rule: only admin can change passwords
        if requesting_role != "admin":
            log.warning(f"[AUTH] Password change denied — user role cannot change passwords")
            return False, "Only administrators can change passwords."

        # Rule: admin can only change their own password
        if username != "admin":
            log.warning(f"[AUTH] Password change denied — admin can only change own password")
            return False, "You can only change your own password."

        # Verify current password first
        success, _ = self.verify(username, current_password)
        if not success:
            return False, "Current password is incorrect."

        # Validate new password strength
        if len(new_password) < MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."

        # Hash and save
        new_hash = self._hash_password(new_password)
        self._credentials[username]["password_hash"] = new_hash
        self._save()

        log.info(f"[AUTH] Password changed for: {username}")
        return True, "Password changed successfully."

    def create_session(self, username: str, role: str) -> str:
        """Create a new in-memory session.

        Returns a session_id string (UUID).
        """
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "username": username,
            "role": role,
        }
        log.info(f"[AUTH] Session created for {username}: {session_id[:8]}...")
        return session_id

    def validate_session(self, session_id: str) -> Tuple[bool, str, str]:
        """Validate a session ID.

        Returns:
            (True, username, role) if valid
            (False, "", "") if invalid
        """
        session = self._sessions.get(session_id)
        if session:
            return True, session["username"], session["role"]
        return False, "", ""

    def remove_session(self, session_id: str):
        """Remove a session (logout)."""
        if session_id in self._sessions:
            info = self._sessions.pop(session_id)
            log.info(f"[AUTH] Session removed for {info['username']}")

    # ─── Internal ─────────────────────────────────────────────────

    def _load_or_create(self):
        """Load credentials from file, or create defaults if missing."""
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._credentials = json.load(f)
                log.info(f"[AUTH] Credentials loaded from {self._path}")
                return
            except Exception as e:
                log.error(f"[AUTH] Failed to load credentials: {e}")

        # Create default accounts
        log.info("[AUTH] Creating default credentials file")
        self._credentials = {}
        for username, info in _DEFAULT_ACCOUNTS.items():
            default_pw = _DEFAULT_PASSWORDS[username]
            self._credentials[username] = {
                "password_hash": self._hash_password(default_pw),
                "role": info["role"],
            }
        self._save()

    def _save(self):
        """Save credentials to the JSON file."""
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._credentials, f, indent=2)
            log.info(f"[AUTH] Credentials saved to {self._path}")
        except Exception as e:
            log.error(f"[AUTH] Failed to save credentials: {e}")

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
