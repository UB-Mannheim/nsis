# -*- coding: utf-8 -*-
# =============================================================================
# vocabulary_lookup.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Vocabulary lookup endpoint for nsis API v1.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from app.api.v1.schemas.requests import VocabularyLookupRequest
from app.api.v1.schemas.responses import VocabularyLookupResponse, VocabularyResult
from app.dependencies import get_milvus_service
from app.rate_limit import limiter, get_rate_limit
from app.utils.abort import check_disconnected
from app.utils.dev_print import DevPrint
from core.inference.reranker import rerank_vocabulary_lookup
from core.usage_stats_logging import usage_stats_logger

router = APIRouter()


@router.post("/lookup-vocabulary", response_model=VocabularyLookupResponse)
@limiter.limit(get_rate_limit("lookup-vocabulary"))
async def lookup_vocabulary(
    request: Request,
    api_request: VocabularyLookupRequest,
    milvus_service = Depends(get_milvus_service)
):
    """
    Perform semantic search on controlled vocabularies for specific search terms.

    Finds related or better matches, performing LLM-based reranking.

    Supported vocabularies:
    - gnd-saz: GND Sachschlagwörter
    - gnd-geo: GND Geografika
    - bk: Basisklassifikation
    """
    # Validate vocabulary
    if api_request.vocabulary not in ["gnd-saz", "gnd-geo", "bk"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported vocabulary: {api_request.vocabulary}. Supported: gnd-saz, gnd-geo, bk"
        )

    # Check if client disconnected before starting search
    if await check_disconnected(request):
        return

    DevPrint.start("Vocabulary lookup started")
    results = await milvus_service.search_vocabulary(
        term=api_request.term,
        vocabulary=api_request.vocabulary,
        limit=api_request.limit
    )
    DevPrint.debug(f"Found {len(results)} results before reranking")

    # Check if client disconnected after Milvus service completes
    if await check_disconnected(request):
        return

    # Rerank results using LLM-based reranking
    if results:
        result_labels = [r["label"] for r in results]
        reranked = await rerank_vocabulary_lookup(
            user_request=api_request.term,
            results=result_labels,
            type="vocabulary"
        )
        indices = reranked.get("indicesOfRelevantTopics", [])
        # Reorder results based on reranked indices
        if indices:
            results = [results[i] for i in indices if i < len(results)]

    # Deduplicate results by id (case-insensitive label deduplication as fallback)
    seen_ids = set()
    seen_labels = set()
    unique_results = []
    for r in results:
        result_id = r.get("id")
        label = r.get("label", "").lower()
        if result_id is not None and result_id in seen_ids:
            continue
        if label in seen_labels:
            continue
        seen_ids.add(result_id)
        seen_labels.add(label)
        unique_results.append(r)
    results = unique_results

    # Convert to response format
    vocabulary_results = [
        VocabularyResult(
            id=r["id"],
            label=r["label"],
            notation=r.get("notation"),
            score=r["score"]
        )
        for r in results
    ]

    # Log business metrics for usage statistics
    request_id = getattr(request.state, 'request_id', None)
    client_ip = request.client.host if request.client else None
    usage_stats_logger.log_business(
        endpoint="/api/v1/lookup-vocabulary",
        search_term=api_request.term,
        result_count=len(vocabulary_results),
        request_id=request_id,
        client_ip=client_ip
    )

    return VocabularyLookupResponse(
        vocabulary=api_request.vocabulary,
        query=api_request.term,
        results=vocabulary_results
    )