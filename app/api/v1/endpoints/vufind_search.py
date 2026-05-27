# -*- coding: utf-8 -*-
# =============================================================================
# vufind_search.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
VuFind search endpoint for nsis API v1.
Combines result count and first titles into a single endpoint.
"""

from fastapi import APIRouter, Depends, Request
from app.api.v1.schemas.requests import PerformVuFindSearchRequest
from app.api.v1.schemas.responses import PerformVuFindSearchResponse, VuFindTitle
from app.dependencies import get_vufind_service
from app.rate_limit import limiter, get_rate_limit
from app.utils.abort import check_disconnected
from app.utils.dev_print_api import api_call_start, api_call_end
from core.usage_stats_logging import usage_stats_logger

router = APIRouter()


@router.post("/perform-vufind-search", response_model=PerformVuFindSearchResponse)
@limiter.limit(get_rate_limit("perform-vufind-search"))
async def perform_vufind_search(
    request: Request,
    api_request: PerformVuFindSearchRequest,
    vufind_service = Depends(get_vufind_service)
):
    """
    Perform a VuFind search and return both total result count and a list of titles.

    Returns the total number of results and a list of title objects with metadata.
    """
    import time
    endpoint = "/api/v1/perform-vufind-search"
    api_call_start(endpoint, "POST", {"url": api_request.url, "limit": api_request.limit})
    start_time = time.time()

    # Check if client disconnected before starting VuFind call
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    # Get both count and titles in a single call
    result = await vufind_service.get_vufind_data(
        api_request.url,
        get_count=True,
        get_results=True,
        max_results=api_request.limit
    )

    # Check if client disconnected again after VuFind call
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    duration_ms = (time.time() - start_time) * 1000
    api_call_end(endpoint, 200, duration_ms)

    # Convert result dictionaries to VuFindTitle objects
    titles = [
        VuFindTitle(
            title=t.get("title", ""),
            authors=t.get("authors", []),
            subjects=t.get("subjects", []),
            year=t.get("year"),
            format=t.get("format", ""),
            url=t.get("url", ""),
            summary=t.get("summary", []),
            toc=t.get("toc", [])
        )
        for t in result.get("results", [])
    ]

    # Log business metrics for usage statistics
    request_id = getattr(request.state, 'request_id', None)
    client_ip = request.client.host if request.client else None
    usage_stats_logger.log_business(
        endpoint="/api/v1/perform-vufind-search",
        search_term=api_request.url,
        result_count=result.get("count"),
        request_id=request_id,
        client_ip=client_ip
    )

    return PerformVuFindSearchResponse(
        totalResults=result.get("count"),
        titles=titles,
        retrievedCount=len(result.get("results", [])),
        url=api_request.url
    )
