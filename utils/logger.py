"""
ParkPilot — Centralized Logger
Provides consistent, color-coded logging across all 12 modules.
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Ensure log directory exists
os.makedirs("logs", exist_ok=True)


class ColorFormatter(logging.Formatter):
    """ANSI color codes for console output."""
    COLORS = {
        logging.DEBUG:    "\033[36m",   # Cyan
        logging.INFO:     "\033[32m",   # Green
        logging.WARNING:  "\033[33m",   # Yellow
        logging.ERROR:    "\033[31m",   # Red
        logging.CRITICAL: "\033[35m",   # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Get a configured logger for a given module name.

    Usage:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Module started")
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Avoid duplicate handlers

    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # ── Console handler ──────────────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = ColorFormatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)

    # ── File handler (rotating, max 10MB, keep 5 backups) ───────────────────
    log_file = f"logs/{name.replace('.', '_')}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# ── Module-specific loggers ──────────────────────────────────────────────────
parking_logger       = get_logger("parkpilot.module1_detection")
anpr_logger          = get_logger("parkpilot.module2_anpr")
surveillance_logger  = get_logger("parkpilot.module3_surveillance")
dashboard_logger     = get_logger("parkpilot.module4_dashboard")
ev_logger            = get_logger("parkpilot.module6_ev")
prediction_logger    = get_logger("parkpilot.module7_prediction")
qr_logger            = get_logger("parkpilot.module8_qr")
nav_logger           = get_logger("parkpilot.module9_navigation")
carbon_logger        = get_logger("parkpilot.module10_carbon")
voice_logger         = get_logger("parkpilot.module11_voice")
pricing_logger       = get_logger("parkpilot.module12_pricing")
system_logger        = get_logger("parkpilot.system")


def log_event(module: str, event_type: str, message: str, extra: dict = None):
    """
    Structured event logging — writes to both logs and audit trail.

    Args:
        module: Module name (e.g. 'ANPR', 'SURVEILLANCE')
        event_type: Type of event (e.g. 'ALERT', 'ENTRY', 'EXIT')
        message: Human-readable message
        extra: Additional key-value pairs for structured logging
    """
    logger = get_logger(f"parkpilot.events.{module.lower()}")
    structured = {
        "timestamp": datetime.utcnow().isoformat(),
        "module": module,
        "event_type": event_type,
        "message": message,
    }
    if extra:
        structured.update(extra)
    logger.info(str(structured))
