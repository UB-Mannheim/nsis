# -*- coding: utf-8 -*-
# =============================================================================
# query_expansion.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Query expansion endpoint for nsis API v1.
"""

from fastapi import APIRouter, Request
from app.api.v1.schemas.requests import QueryExpansionRequest
from app.api.v1.schemas.responses import QueryExpansionResponse
from app.rate_limit import limiter, get_rate_limit
from app.utils.abort import check_disconnected
from app.utils.dev_print_api import api_call_start, api_call_end
from core.usage_stats_logging import usage_stats_logger
from core.inference import perform_query_expansion
from core.inference.logical_tree import build_logical_tree

router = APIRouter()


@router.post("/query-expansion", response_model=QueryExpansionResponse)
@limiter.limit(get_rate_limit("query-expansion"))
async def query_expansion(
    request: Request,
    api_request: QueryExpansionRequest,
):
    """
    Expand/rewrite the search query with possible similar or related search terms using an LLM.

    Relies on the LLM's world knowledge to find related terms.
    """
    import time
    endpoint = "/api/v1/query-expansion"
    api_call_start(endpoint, "POST", {"query": api_request.query, "search_intent": api_request.search_intent})
    start_time = time.time()

    # Check if client disconnected before starting expensive operation
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    result = await perform_query_expansion(api_request.query, api_request.search_intent)

    # Check if client disconnected after first LLM call
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    positive_concepts = result.get("positiveConcepts", {})
    negative_concepts = result.get("negativeConcepts", {})

    # Build logical tree from concepts for URL building
    logical_tree = None
    if positive_concepts or negative_concepts:
        logical_tree = build_logical_tree(positive_concepts, negative_concepts)

    # Check if client disconnected after logical tree building
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    duration_ms = (time.time() - start_time) * 1000
    api_call_end(endpoint, 200, duration_ms)

    # Log business metrics for usage statistics
    request_id = getattr(request.state, 'request_id', None)
    client_ip = request.client.host if request.client else None
    total_concepts = sum(len(v) for v in positive_concepts.values()) + sum(len(v) for v in negative_concepts.values())
    usage_stats_logger.log_business(
        endpoint="/api/v1/query-expansion",
        search_term=api_request.query,
        result_count=total_concepts,
        request_id=request_id,
        client_ip=client_ip
    )

    return QueryExpansionResponse(
        originalQuery=api_request.query,
        positiveKeywordConcepts=positive_concepts,
        negativeKeywordConcepts=negative_concepts,
        logicalTree=logical_tree if logical_tree else None
    )