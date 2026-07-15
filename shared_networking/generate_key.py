#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════
#  AETHER CONSOLE — ENCRYPTION KEY GENERATOR
#  Run this script once to generate the pre-shared Fernet key.
#
#  Usage:  python shared_networking/generate_key.py
# ═══════════════════════════════════════════════════════════════════

import os
import sys

# Ensure parent package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_networking.encryption import EncryptionManager
from shared_networking.config import ENCRYPTION_KEY_PATH


def main():
    if os.path.exists(ENCRYPTION_KEY_PATH):
        print(f"  Key already exists: {ENCRYPTION_KEY_PATH}")
        answer = input("  Overwrite? (y/N): ").strip().lower()
        if answer != "y":
            print("  Aborted.")
            return

    ok = EncryptionManager.generate_key(ENCRYPTION_KEY_PATH)
    if ok:
        print(f"  ✔ Encryption key generated: {ENCRYPTION_KEY_PATH}")
        print("  Keep this file safe. All apps and the broker must share it.")
    else:
        print("  ✖ Failed to generate key.")
        sys.exit(1)


if __name__ == "__main__":
    main()
