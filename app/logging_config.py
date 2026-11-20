# app/logging_config.py
from __future__ import annotations

import logging
from logging import Logger
from pathlib import Path

from app.config import Settings


def _get_log_level(level_name: str) -> int:
    """
    Resolve a logging level name (e.g., "DEBUG" or "INFO") to its numeric value.

    Fall back to logging.INFO when the name is unrecognized.
    """
    level_name = (level_name or "").upper()
    level = getattr(logging, level_name, None)
    if isinstance(level, int):
        return level
    return logging.INFO


def setup_logging(settings: Settings) -> Logger:
    """
    Configure application-wide logging.

    Create the log directory, configure the root logger, and add file and
    console handlers. Return this module's logger.
    """
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "bot.log"
    log_level = _get_log_level(settings.log_level)

    # Use the same format for file and console messages.
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] " "%(message)s"
    )

    # Clear existing root handlers to avoid duplicate log messages.
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    # Write logs to a file.
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Also write logs to the console.
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Return this module's logger after initializing logging.
    logger = logging.getLogger(__name__)
    logger.debug(
        "Logging initialized. level=%s, log_file=%s",
        settings.log_level,
        log_file,
    )
    return logger
