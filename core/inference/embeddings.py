# -*- coding: utf-8 -*-
# =============================================================================
# embeddings.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Embedding functions for nsis.

Provides asynchronous embedding functions for Milvus vector search.
"""

import asyncio
import logging
import time
from typing import List

from openai import RateLimitError

from core.clients import inference_client
from core.models_config import MODEL_EMBEDDING, EMBEDDING_PROVIDER_SORT

# Import usage stats logger
from core.usage_stats_logging import usage_stats_logger

logger = logging.getLogger(__name__)


async def perform_embedding_batch(texts: List[str], max_retries: int = 3) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts using the async OpenAI embeddings API.

    Args:
        texts: List of text strings to embed
        max_retries: Maximum number of retry attempts (default 3)

    Returns:
        List of embedding vectors
    """
    time_start = time.time_ns()

    for attempt in range(max_retries):
        try:
            response = await inference_client.client.embeddings.create(
                input=texts,
                model=MODEL_EMBEDDING,
                extra_body={
                    "provider": {
                        "sort": EMBEDDING_PROVIDER_SORT
                    }
                }
            )
            embeddings = [item.embedding for item in response.data]

            time_end = time.time_ns()
            duration_ms = (time_end - time_start) / 1_000_000

            # Log performance metrics
            usage_stats_logger.log_performance(
                operation_type="embedding",
                duration_ms=duration_ms,
                model=MODEL_EMBEDDING,
                batch_size=len(texts)
            )

            return embeddings

        except (RateLimitError, Exception) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Embedding attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All embedding attempts failed. Final error: {e}")

    # Return empty list if all retries failed
    return []


class EmbeddingFunction:
    """
    Wrapper class for Milvus-compatible embedding generation.

    Used by milvus_search.py for vector search operations.
    """

    async def encode_queries(self, queries: List[str]):
        """Encode search queries for similarity search."""
        return await perform_embedding_batch(queries)

    async def encode_documents(self, docs: List[str]):
        """Encode documents for indexing in Milvus."""
        return await perform_embedding_batch(docs)
