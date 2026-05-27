# -*- coding: utf-8 -*-
# =============================================================================
# search_intent.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Search intent endpoint for nsis API v1.
"""

from fastapi import APIRouter, Request
from app.api.v1.schemas.requests import SearchIntentRequest
from app.api.v1.schemas.responses import SearchIntentResponse
from app.rate_limit import limiter, get_rate_limit
from app.utils.abort import check_disconnected
from app.utils.dev_print_api import api_call_start, api_call_end
from core.usage_stats_logging import usage_stats_logger
from core.inference import analyze_search_intent

router = APIRouter()


@router.post("/search-intent", response_model=SearchIntentResponse)
@limiter.limit(get_rate_limit("search-intent"))
async def search_intent(
    request: Request,
    api_request: SearchIntentRequest,
):
    """
    Analyze search input to figure out the search intent of the user.

    Returns analysis result, e.g. knownItem or topicSearch
    """
    import time
    endpoint = "/api/v1/search-intent"
    api_call_start(endpoint, "POST", {"query": api_request.query})
    start_time = time.time()

    # Check if client disconnected before starting expensive operation
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    result = await analyze_search_intent(api_request.query)

    # Check if client disconnected after LLM call
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    duration_ms = (time.time() - start_time) * 1000
    api_call_end(endpoint, 200, duration_ms)

    # Log business metrics for usage statistics
    request_id = getattr(request.state, "request_id", None)
    client_ip = request.client.host if request.client else None
    usage_stats_logger.log_business(
        endpoint="/api/v1/search-intent",
        search_term=api_request.query,
        request_id=request_id,
        client_ip=client_ip,
    )

    return SearchIntentResponse(
        searchIntent=result.get("searchIntent", "topicSearch"),
    )
