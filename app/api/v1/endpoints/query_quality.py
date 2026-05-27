# -*- coding: utf-8 -*-
# =============================================================================
# query_quality.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Query quality endpoint for nsis API v1.
"""

from fastapi import APIRouter, Depends, Request
from app.api.v1.schemas.requests import QueryQualityRequest
from app.api.v1.schemas.responses import QueryQualityResponse, VuFindTitle
from app.dependencies import get_vufind_service
from app.rate_limit import limiter, get_rate_limit
from app.utils.abort import check_disconnected
from app.utils.dev_print_api import api_call_start, api_call_end
from core.usage_stats_logging import usage_stats_logger
from core.inference import assess_query_quality

router = APIRouter()


@router.post("/query-judge-quality", response_model=QueryQualityResponse)
@limiter.limit(get_rate_limit("query-judge-quality"))
async def query_judge_quality(
    request: Request,
    api_request: QueryQualityRequest,
    vufind_service = Depends(get_vufind_service)
):
    """
    Perform a search in the catalog to retrieve first 10 results.

    Judge the fit of the resulting titles in relation to the original natural language search query.

    Returns quality of query in relation to original search query (0.0 - 1.0).

    If titles are provided in the request (pre-fetched by client), uses those instead of
    making another VuFind request to avoid redundant API calls.
    """
    import time
    endpoint = "/api/v1/query-judge-quality"
    api_call_start(endpoint, "POST", {"query": api_request.query})
    start_time = time.time()

    # Check if client disconnected before starting
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    # Use provided titles if available, otherwise fetch from VuFind
    if api_request.titles is not None:
        titles = [
            VuFindTitle(
                title=t.title or "",
                authors=t.authors or [],
                subjects=t.subjects or [],
                year=t.year or "",
                format=t.format or "",
                url=t.url or "",
                summary=t.summary or [],
                toc=t.toc or []
            )
            for t in api_request.titles
        ]
    else:
        # Fetch titles from VuFind (legacy behavior)
        result = await vufind_service.get_vufind_data(
            api_request.url,
            get_count=False,
            get_results=True,
            max_results=10
        )

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

    # Check if client disconnected after VuFind call
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    # Assess query quality
    title_strings = [t.title for t in titles]
    subject_strings = [t.subjects for t in titles]
    author_strings = [t.authors for t in titles]
    assessment_result = await assess_query_quality(
        api_request.query, title_strings, subject_strings, author_strings, api_request.output_language
    )

    # Check again after LLM call
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    duration_ms = (time.time() - start_time) * 1000
    api_call_end(endpoint, 200, duration_ms)

    # Log business metrics for usage statistics
    request_id = getattr(request.state, 'request_id', None)
    client_ip = request.client.host if request.client else None
    quality_score = assessment_result.get("qualityScore", 0.5)
    usage_stats_logger.log_business(
        endpoint="/api/v1/query-judge-quality",
        search_term=api_request.query,
        result_count=len(titles),
        query_quality_score=quality_score,
        request_id=request_id,
        client_ip=client_ip
    )

    # Log to dedicated query log
    usage_stats_logger.log_query(
        query=api_request.query,
        result_count=len(titles),
        query_quality_score=quality_score,
        request_id=request_id,
    )

    return QueryQualityResponse(
        qualityScore=assessment_result.get("qualityScore", 0.5),
        originalQuery=api_request.query,
        assessment=assessment_result.get("assessment", "Quality assessment completed"),
        relevantIndices=assessment_result.get("relevantIndices", [])
    )
