"""
Centralized logging configuration utilities.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

_LEVEL_MAP = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def _level_from_env(default: int = logging.INFO) -> int:
    value = os.getenv("LOG_LEVEL", "").strip().upper()
    return _LEVEL_MAP.get(value, default)


def setup_logging(level: Optional[int] = None) -> None:
    """
    Configure root logging once with a reasonable format.
    Subsequent calls are no-ops if handlers already exist.
    """
    root = logging.getLogger()
    if root.handlers:
        return

    resolved = level if level is not None else _level_from_env()
    logging.basicConfig(
        level=resolved,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
