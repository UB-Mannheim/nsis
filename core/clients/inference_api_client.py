# -*- coding: utf-8 -*-
# =============================================================================
# inference_api_client.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Inference API client for nsis inference.

This module provides:
- AsyncOpenAI client ..
    - for LLM inference
    - for embeddings (used by Milvus vector search)
"""

from openai import AsyncOpenAI

# Import settings from app config
from app.config import settings


class AsyncInferenceClient:
    """Async client for concurrent LLM inference requests (FastAPI compatible)."""

    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=settings.inference_provider_api_key,
            base_url=settings.inference_provider_base_url,
        )

    @property
    def client(self) -> AsyncOpenAI:
        """Get the underlying AsyncOpenAI client."""
        return self._client


# Singleton instance
inference_client = AsyncInferenceClient()
