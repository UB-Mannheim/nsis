# -*- coding: utf-8 -*-
# =============================================================================
# abort.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Client disconnection detection utilities for nsis API.

Provides utilities to detect client disconnections and abort
expensive operations early to save resources.
"""

import logging

from fastapi import Request

logger = logging.getLogger("nsis")


async def check_disconnected(request: Request) -> bool:
    """
    Check if the client has disconnected from the request.

    Args:
        request: The FastAPI Request object

    Returns:
        True if the client has disconnected, False otherwise
    """
    try:
        return await request.is_disconnected()
    except Exception as e:
        logger.warning(f"Error checking client disconnection: {e}")
        return False

