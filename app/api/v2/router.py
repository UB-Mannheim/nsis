# -*- coding: utf-8 -*-
# =============================================================================
# router.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
API router for nsis API v2 (placeholder for future versions).
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def v2_info():
    """Information about API v2."""
    return {
        "version": "v2",
        "status": "not implemented",
        "message": "API v2 is not yet implemented. Use v1 endpoints."
    }