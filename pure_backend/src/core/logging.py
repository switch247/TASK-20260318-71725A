import logging
import sys
from typing import Any


def configure_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Specific loggers for domains
    loggers = [
        "auth",
        "governance",
        "process",
        "security",
        "analytics",
        "operation_logger",
    ]
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.addHandler(console_handler)
        logger.propagate = False  # Prevent duplicate logs


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific domain."""
    return logging.getLogger(name)
