# -*- coding: utf-8 -*-
# =============================================================================
# rate_limit.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Rate limiting configuration for nsis API.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter instance with IP-based key function
limiter = Limiter(key_func=get_remote_address)


# =============================================================================
# API Endpoint Rate Limits
# =============================================================================
# Centralized configuration for all API endpoint rate limits.
# Format: "requests / period" (e.g., "200/minute")
# =============================================================================

RATE_LIMITS = {
    # Vocabulary & structuring endpoints
    "lookup-vocabulary": "50/minute",
    "build-logical-tree": "50/minute",
    "add-keyword-to-concepts": "50/minute",

    # VuFind search & quality assessment endpoints
    "perform-vufind-search": "30/minute",
    "query-judge-quality": "30/minute",

    # Query processing endpoints
    "search-intent": "20/minute",
    "query-expansion": "20/minute",
    "query-facettes": "20/minute",
    "query-transformation": "20/minute",
}


def get_rate_limit(endpoint_name: str) -> str:
    """
    Get the rate limit string for a given endpoint.

    Args:
        endpoint_name: Name of the endpoint (must match keys in RATE_LIMITS)

    Returns:
        Rate limit string in format "requests / period"

    Raises:
        KeyError: If endpoint_name is not found in RATE_LIMITS
    """
    return RATE_LIMITS[endpoint_name]
