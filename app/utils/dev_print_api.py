# -*- coding: utf-8 -*-
# =============================================================================
# dev_print_api.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================
"""
API endpoint call tracking for development.

Provides visual output hooks for API calls with request/response tracking.
Use these functions to add consistent visual logging for API endpoints.

Example:
    api_call_start("/api/v1/expand-search-question", "POST", {"query": "..."})
    api_call_end("/api/v1/expand-search-question", 200, 234.5)
    api_call_result("/api/v1/expand-search-question", "42 results, 3 GND headings")
"""
from typing import Optional

from app.utils.dev_print import DevPrint, DevLevel


def api_call_start(endpoint: str, method: str = "POST", args: Optional[dict] = None) -> None:
    """
    Print when an API call starts with request arguments.

    Args:
        endpoint: API endpoint path (e.g., "/api/v1/expand-search-question")
        method: HTTP method (default "POST")
        args: Optional dict of request arguments to display
    """
    DevPrint.start(f"→ {method} {endpoint}")
    if args:
        DevPrint.debug(f"   Args: {args}")


def api_call_end(endpoint: str, status: int, duration_ms: float) -> None:
    """
    Print when an API call ends with status and duration.

    Args:
        endpoint: API endpoint path
        status: HTTP status code
        duration_ms: Request duration in milliseconds
    """
    level = DevLevel.COMPLETE if status < 400 else DevLevel.ERROR
    DevPrint._print(level, f"← {endpoint} → {status} ({duration_ms:.1f}ms)")


def api_call_result(endpoint: str, summary: str) -> None:
    """
    Print a single summary line for API response results.

    Note: Use this ONLY once per API call to summarize results,
    not for individual items within the response.

    Args:
        endpoint: API endpoint path
        summary: One-line summary (e.g., "42 results, 3 GND headings")
    """
    DevPrint.result(f"{endpoint}: {summary}")