# -*- coding: utf-8 -*-
# =============================================================================
# dev_print.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================
"""
Development print utilities with colored output.

Provides consistent visual styling for development/debug print output
across the codebase. Use DevPrint.* methods instead of plain print()
for better visual output during development.

Example:
    DevPrint.info("Starting search")
    DevPrint.timing("Query took: 1.23s")
    DevPrint.result("Found 42 items")
    DevPrint.warning("Cache miss for key")
    DevPrint.error("Connection failed")
"""
import sys
from enum import Enum

# ANSI color codes for terminal output
ANSI_RESET = "\033[0m"
ANSI_BLUE = "\033[94m"
ANSI_BRIGHT_CYAN = "\033[96m"
ANSI_BRIGHT_GREEN = "\033[92m\033[1m"
ANSI_GRAY = "\033[37m"
ANSI_GREEN = "\033[92m"
ANSI_PINK = "\033[95m"
ANSI_YELLOW = "\033[93m"
ANSI_RED = "\033[91m"


class DevLevel(Enum):
    """Output levels with ANSI color codes and prefixes (all 9 chars for alignment)."""
    INFO = ("[INFO]    ", ANSI_BLUE)
    START = ("[START]   ", ANSI_BRIGHT_CYAN)
    DEBUG = ("[DEBUG]   ", ANSI_GRAY)
    RESULT = ("[RESULT]  ", ANSI_GREEN)
    TIMING = ("[TIMING]  ", ANSI_PINK)
    SUCCESS = ("[SUCCESS] ", ANSI_GREEN)
    COMPLETE = ("[COMPLETE]", ANSI_BRIGHT_GREEN)
    WARNING = ("[WARNING] ", ANSI_YELLOW)
    ERROR = ("[ERROR]   ", ANSI_RED)


class DevPrint:
    """
    Colored development print utility.

    Provides methods for visually consistent debug output with
    color-coded prefixes based on message severity/type.

    Class-level enable/disable:
        DevPrint.enable()   # Enable colored output
        DevPrint.disable()  # Disable (for log files)
    """

    _enabled: bool = True  # Class variable for enable/disable
    RESET = ANSI_RESET

    @classmethod
    def enable(cls) -> None:
        """Enable colored output (auto-enabled if stdout is a TTY)."""
        cls._enabled = True

    @classmethod
    def disable(cls) -> None:
        """Disable colored output (e.g., for log files)."""
        cls._enabled = False

    @classmethod
    def _print(cls, level: DevLevel, msg: str, **kwargs) -> None:
        """Internal print method with color support."""
        # Strip leading/trailing whitespace from message
        msg = msg.strip()
        prefix = level.value[0]
        color = level.value[1]

        if cls._enabled and sys.stdout.isatty():
            print(f"{color}{prefix} {msg}{cls.RESET}", **kwargs)
        else:
            # Strip color codes for non-TTY output
            print(f"{prefix} {msg}", **kwargs)

    @classmethod
    def info(cls, msg: str, **kwargs) -> None:
        """Print info message (blue)."""
        cls._print(DevLevel.INFO, msg, **kwargs)

    @classmethod
    def debug(cls, msg: str, **kwargs) -> None:
        """Print debug message (gray/dim)."""
        cls._print(DevLevel.DEBUG, msg, **kwargs)

    @classmethod
    def result(cls, msg: str, **kwargs) -> None:
        """
        Print result message (green).

        Used for search results, list items, and API response summaries.
        For API results, consider using api_call_result() instead.
        """
        cls._print(DevLevel.RESULT, msg, **kwargs)

    @classmethod
    def timing(cls, msg: str, **kwargs) -> None:
        """Print timing/duration message (pink/magenta)."""
        cls._print(DevLevel.TIMING, msg, **kwargs)

    @classmethod
    def success(cls, msg: str, **kwargs) -> None:
        """Print success message (green)."""
        cls._print(DevLevel.SUCCESS, msg, **kwargs)

    @classmethod
    def warning(cls, msg: str, **kwargs) -> None:
        """Print warning message (yellow)."""
        cls._print(DevLevel.WARNING, msg, **kwargs)

    @classmethod
    def start(cls, msg: str, **kwargs) -> None:
        """Print start message (bright cyan)."""
        cls._print(DevLevel.START, msg, **kwargs)

    @classmethod
    def error(cls, msg: str, **kwargs) -> None:
        """Print error message (red)."""
        cls._print(DevLevel.ERROR, msg, **kwargs)
