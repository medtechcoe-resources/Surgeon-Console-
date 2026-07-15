# ═══════════════════════════════════════════════════════════════════
#  AETHER CONSOLE — STRUCTURED LOGGER
#  Single structured application log with category prefixes.
#  Categories: [COMM] [AUTH] [SYSTEM] [BROKER]
# ═══════════════════════════════════════════════════════════════════

import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

_LOG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG_FILE = os.path.join(_LOG_DIR, "aether.log")
_MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 3

# Valid categories
CATEGORIES = ("COMM", "AUTH", "SYSTEM", "BROKER")

_root_configured = False


def _ensure_root_configured():
    """Configure the root logger once with console + file handlers."""
    global _root_configured
    if _root_configured:
        return

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # Rotating file handler
    try:
        fh = RotatingFileHandler(
            _LOG_FILE, maxBytes=_MAX_LOG_SIZE,
            backupCount=_BACKUP_COUNT, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except Exception:
        pass  # Don't crash if log file can't be created

    _root_configured = True


def get_logger(category: str) -> logging.Logger:
    """Return a logger that auto-prefixes messages with the category.

    Usage:
        log = get_logger("COMM")
        log.info("Connected to broker")
        # Output: 2026-07-10 12:30:00 INFO    [COMM] Connected to broker
    """
    _ensure_root_configured()

    category = category.upper()
    logger = logging.getLogger(f"aether.{category.lower()}")

    # Use a custom adapter to prefix the category tag
    return _CategoryLogger(logger, category)


class _CategoryLogger:
    """Wraps a standard Logger to auto-prefix [CATEGORY] to messages."""

    def __init__(self, logger: logging.Logger, category: str):
        self._logger = logger
        self._prefix = f"[{category}]"

    def debug(self, msg: str, *args, **kwargs):
        self._logger.debug(f"{self._prefix} {msg}", *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        self._logger.info(f"{self._prefix} {msg}", *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self._logger.warning(f"{self._prefix} {msg}", *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self._logger.error(f"{self._prefix} {msg}", *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        self._logger.critical(f"{self._prefix} {msg}", *args, **kwargs)
