# -*- coding: utf-8 -*-
# =============================================================================
# logging.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Logging utilities for nsis FastAPI application.
"""

import logging
import logging.handlers
import sys
import os
from typing import Optional


class HttpStreamFilter(logging.Filter):
    """
    Filter that suppresses HTTP Request log messages from httpx and similar libraries
    when outputting to stdout, but allows them through to file handlers.
    """

    def filter(self, record):
        # Suppress httpx HTTP Request logs (e.g., "HTTP Request: POST ... 200 OK")
        if record.name == "httpx" and "HTTP Request" in record.getMessage():
            return False
        # Also suppress any other noisy HTTP client libraries with similar patterns
        if record.name in ("httpx", "httpcore", "urllib3") and "HTTP" in record.getMessage():
            return False
        return True


def setup_logging(log_level: str, log_dir: str):
    """
    Set up logging configuration for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Configure handlers
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.addFilter(HttpStreamFilter())
    handlers = [
        stream_handler,
    ]

    # Add file handler for permanent logging
    log_file = os.path.join(log_dir, "nsis.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.WARNING),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )

    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)


def log_error(endpoint: str, error: Exception):
    """
    Log an error.

    Args:
        endpoint: The endpoint where the error occurred
        error: The exception that was raised
    """
    logger = logging.getLogger("nsis.api")
    logger.error(f"Error in {endpoint}: {str(error)}", exc_info=True)


def setup_api_calls_logger(log_dir: str):
    """
    Set up a dedicated logger for API calls that writes to a separate file.

    Args:
        log_dir: Directory to store log files
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Create API calls logger
    api_logger = logging.getLogger("nsis.api_calls")
    api_logger.setLevel(logging.INFO)
    api_logger.propagate = False  # Don't propagate to root logger

    # Add file handler for API calls
    api_log_file = os.path.join(log_dir, "nsis_api_calls.log")
    file_handler = logging.handlers.RotatingFileHandler(
        api_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))

    # Clear existing handlers and add the file handler
    api_logger.handlers.clear()
    api_logger.addHandler(file_handler)

    return api_logger


def log_api_call(method: str, path: str, status_code: int, client_ip: Optional[str] = None,
                 query_params: Optional[str] = None, body: Optional[str] = None,
                 duration_ms: Optional[float] = None):
    """
    Log an API call to the dedicated API calls log file.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        client_ip: Client IP address (optional)
        query_params: Query parameters (optional)
        body: Request body (optional)
        duration_ms: Request duration in milliseconds (optional)
    """
    logger = logging.getLogger("nsis.api_calls")

    log_parts = [
        f"{method} {path}",
        f"Status: {status_code}"
    ]

    if client_ip:
        log_parts.append(f"Client: {client_ip}")
    if query_params:
        log_parts.append(f"Query: {query_params}")
    if body:
        log_parts.append(f"Body: {body}")
    if duration_ms is not None:
        log_parts.append(f"Duration: {duration_ms:.2f}ms")

    logger.info(" | ".join(log_parts))


