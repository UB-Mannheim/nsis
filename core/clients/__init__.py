# -*- coding: utf-8 -*-
# =============================================================================
# __init__.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Clients package for nsis.

Provides API clients for:
- LLM inference (AsyncOpenAI)
- VuFind API
"""

from core.clients.inference_api_client import AsyncInferenceClient, inference_client
from core.clients.vufind_api_client import (
    VuFindAPIClient,
    VuFindAPIClientError,
    VuFindAPITimeoutError,
)

__all__ = [
    "AsyncInferenceClient",
    "inference_client",
    "VuFindAPIClient",
    "VuFindAPIClientError",
    "VuFindAPITimeoutError",
]