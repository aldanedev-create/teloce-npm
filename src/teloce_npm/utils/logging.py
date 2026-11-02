"""
Consistent logging for Teloce-NPM.
"""

import logging
import sys

# ANSI color codes for terminal output
COLORS = {
    "DEBUG": "\033[90m",  # Gray
    "INFO": "\033[0m",  # Default
    "SUCCESS": "\033[92m",  # Green
    "WARNING": "\033[93m",  # Yellow
    "ERROR": "\033[91m",  # Red
    "RESET": "\033[0m",
}


class TeloceFormatter(logging.Formatter):
    """Custom formatter to add colors and clean formatting."""

    def format(self, record):
        color = COLORS.get(record.levelname, COLORS["RESET"])
        reset = COLORS["RESET"]

        # Format: [INFO] Message
        return f"{color}[{record.levelname}]{reset} {record.getMessage()}"


def get_logger(verbose: bool = False) -> logging.Logger:
    """
    Get the Teloce-NPM logger.

    Args:
        verbose: If True, sets the level to DEBUG and shows timestamps.
    """
    logger = logging.getLogger("teloce_npm")

    # Prevent duplicate handlers if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    if verbose:
        # Detailed format for debugging
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    else:
        # Clean format for normal use
        formatter = TeloceFormatter()

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Default logger instance
logger = get_logger()
