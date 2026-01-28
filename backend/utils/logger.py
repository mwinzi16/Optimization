"""
Logging configuration for Portfolio Optimizer.
Enterprise-grade logging with structured output.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "ils_optimizer",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """
    Set up a logger with console and optional file output.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional path to log file
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Format: timestamp - level - module - message
    console_format = logging.Formatter(
        fmt="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger


# Create default logger instance
logger = setup_logger()


def _mask_value(key: str, value: str, redact_keys=None) -> str:
    """Mask sensitive values for logging."""
    try:
        lk = key.lower()
        if redact_keys and lk in redact_keys:
            return "[REDACTED]"
        # mask long values
        s = str(value)
        if len(s) > 100:
            return s[:50] + "...[TRUNCATED]"
        return s
    except Exception:
        return "[REDACTED]"


def safe_log_dict(logger: logging.Logger, data: dict, redact_keys=None, level=logging.INFO):
    """Log a dict while redacting common sensitive keys and truncating large values."""
    try:
        redact = set([k.lower() for k in (redact_keys or [])])
        safe_items = {k: _mask_value(k, v, redact) for k, v in data.items()}
        logger.log(level, "%s", safe_items)
    except Exception:
        logger.exception("Failed to safe-log dict")


class RequestTimer:
    """Context manager for timing API requests."""
    
    def __init__(self, operation: str, logger: logging.Logger = logger):
        self.operation = operation
        self.logger = logger
        self.start_time: Optional[datetime] = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        if exc_type:
            self.logger.error(f"Failed: {self.operation} ({duration:.3f}s) - {exc_val}")
        else:
            self.logger.info(f"Completed: {self.operation} ({duration:.3f}s)")
        return False
