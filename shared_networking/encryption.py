# ═══════════════════════════════════════════════════════════════════
#  AETHER CONSOLE — ENCRYPTION MODULE
#  Centralized Fernet (AES-128-CBC + HMAC) encryption/decryption.
#  All wire-level encryption passes through this single module.
#  No encryption logic should exist elsewhere in the application.
# ═══════════════════════════════════════════════════════════════════

import os
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

log = logging.getLogger(__name__)


class EncryptionManager:
    """Singleton that manages Fernet encryption for all network messages.

    Usage:
        em = EncryptionManager.instance()
        em.load_key("path/to/aether.key")

        ciphertext = em.encrypt(plaintext_bytes)
        plaintext  = em.decrypt(ciphertext)
    """

    _instance: Optional["EncryptionManager"] = None

    @classmethod
    def instance(cls) -> "EncryptionManager":
        if cls._instance is None:
            cls._instance = EncryptionManager()
        return cls._instance

    def __init__(self):
        self._fernet: Optional[Fernet] = None
        self._key_loaded = False

        # Diagnostics counters
        self.encryption_errors = 0
        self.decryption_errors = 0

    # ─── Key Management ───────────────────────────────────────────

    def load_key(self, path: str) -> bool:
        """Load a Fernet key from the given file path.

        Returns True on success, False on failure.
        """
        try:
            with open(path, "rb") as f:
                key = f.read().strip()
            self._fernet = Fernet(key)
            self._key_loaded = True
            log.info(f"Encryption key loaded from {path}")
            return True
        except FileNotFoundError:
            log.error(f"Encryption key file not found: {path}")
            return False
        except Exception as e:
            log.error(f"Failed to load encryption key: {e}")
            return False

    @staticmethod
    def generate_key(path: str) -> bool:
        """Generate a new Fernet key and save it to the given path.

        Creates parent directories if they don't exist.
        Returns True on success.
        """
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            key = Fernet.generate_key()
            with open(path, "wb") as f:
                f.write(key)
            log.info(f"New encryption key generated: {path}")
            return True
        except Exception as e:
            log.error(f"Failed to generate encryption key: {e}")
            return False

    @property
    def is_ready(self) -> bool:
        """True if a valid key has been loaded."""
        return self._key_loaded and self._fernet is not None

    @property
    def algorithm(self) -> str:
        """Human-readable algorithm description."""
        return "Fernet (AES-128-CBC + HMAC-SHA256)"

    # ─── Encrypt / Decrypt ────────────────────────────────────────

    def encrypt(self, plaintext: bytes) -> Optional[bytes]:
        """Encrypt plaintext bytes using Fernet.

        Returns ciphertext bytes, or None on failure.
        """
        if not self.is_ready:
            log.warning("Encryption attempted without a loaded key")
            self.encryption_errors += 1
            return None

        try:
            return self._fernet.encrypt(plaintext)
        except Exception as e:
            self.encryption_errors += 1
            log.error(f"Encryption failed: {e}")
            return None

    def decrypt(self, ciphertext: bytes) -> Optional[bytes]:
        """Decrypt Fernet ciphertext back to plaintext bytes.

        Returns plaintext bytes, or None on failure (invalid token,
        corrupted data, wrong key, etc.).
        """
        if not self.is_ready:
            log.warning("Decryption attempted without a loaded key")
            self.decryption_errors += 1
            return None

        try:
            return self._fernet.decrypt(ciphertext)
        except InvalidToken:
            self.decryption_errors += 1
            log.error("Decryption failed: invalid token (wrong key or corrupted data)")
            return None
        except Exception as e:
            self.decryption_errors += 1
            log.error(f"Decryption failed: {e}")
            return None

    def get_stats(self) -> dict:
        """Return encryption diagnostics."""
        return {
            "encryption_enabled": self.is_ready,
            "algorithm": self.algorithm,
            "encryption_errors": self.encryption_errors,
            "decryption_errors": self.decryption_errors,
        }
