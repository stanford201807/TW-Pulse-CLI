"""Logging configuration for Pulse CLI."""

import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler


def get_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Path | None = None,
) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)
        level: Logging level
        log_file: Optional file path for file logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    # Rich console handler for beautiful terminal output
    console_handler = RichHandler(
        console=Console(stderr=True),
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
    )
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    # Automatically add file logging if DEFAULT_LOG_FILE is defined or log_file is passed
    target_log_file = log_file or Path("logs/pulse.log")
    try:
        target_log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(target_log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)
    except Exception as e:
        # Fallback to console if file logging fails
        print(f"Failed to setup file logging: {e}")

    return logger


# Default application logger
log = get_logger("pulse", level=logging.DEBUG)
