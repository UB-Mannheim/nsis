# -*- coding: utf-8 -*-
# =============================================================================
# query_facettes.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Query facets endpoint for nsis API v1.
"""

from fastapi import APIRouter, Request
from app.api.v1.schemas.requests import QueryFacettesRequest
from app.api.v1.schemas.responses import QueryFacettesResponse, FilterValue
from app.rate_limit import limiter, get_rate_limit
from app.utils.abort import check_disconnected
from app.utils.dev_print_api import api_call_start, api_call_end
from core.usage_stats_logging import usage_stats_logger
from core.inference import extract_facettes
from app.services.transformation_service import _normalize_author_name, _extract_german_author_patterns

router = APIRouter()


@router.post("/query-facettes", response_model=QueryFacettesResponse)
@limiter.limit(get_rate_limit("query-facettes"))
async def query_facettes(
    request: Request,
    api_request: QueryFacettesRequest,
):
    """
    Analyze the user query in relation to catalog filters and facettes.

    Returns filters and facettes with values as detected for:
    - mediaType
    - contentGenre
    - author
    - dateRange
    - languages
    """
    import time
    endpoint = "/api/v1/query-facettes"
    api_call_start(endpoint, "POST", {"query": api_request.query})
    start_time = time.time()

    # Check if client disconnected before starting expensive operation
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    result = await extract_facettes(api_request.query)

    # Extract author names from LLM response
    author_names_llm = result.get("authorNames", []) or []

    # Supplement with German author patterns (e.g., "von Sabine Gehrlein")
    author_names = list(author_names_llm)
    german_authors = _extract_german_author_patterns(api_request.query)
    for ga in german_authors:
        if ga not in author_names:
            author_names.append(ga)

    # Check if client disconnected after LLM call
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    duration_ms = (time.time() - start_time) * 1000
    api_call_end(endpoint, 200, duration_ms)

    # Convert media forms
    media_forms = [
        FilterValue(label=mf, filterValue=mf)
        for mf in result.get("mediaForms", [])
    ]

    # Convert content genres
    content_genres = [
        FilterValue(label=cg, filterValue=cg)
        for cg in result.get("contentGenres", [])
    ]

    # Convert author names
    author_filters = [
        FilterValue(label=_normalize_author_name(an), filterValue=_normalize_author_name(an))
        for an in author_names
    ]

    # Convert languages
    languages = [
        FilterValue(label=lang, filterValue=lang)
        for lang in result.get("languages", [])
    ]

    # Get date range
    date_range = result.get("dateRange", {})

    # Log business metrics for usage statistics
    request_id = getattr(request.state, 'request_id', None)
    client_ip = request.client.host if request.client else None
    usage_stats_logger.log_business(
        endpoint="/api/v1/query-facettes",
        search_term=api_request.query,
        facets_extracted={
            "mediaForms": len(media_forms),
            "contentGenres": len(content_genres),
            "authorNames": len(author_names),
            "languages": len(languages),
            "topicsInOriginalLanguage": len(result.get("topicsInOriginalLanguage", [])),
            "topicsInEnglish": len(result.get("topicsInEnglish", []))
        },
        request_id=request_id,
        client_ip=client_ip
    )

    return QueryFacettesResponse(
        mediaForms=media_forms,
        contentGenres=content_genres,
        authorNames=author_filters,
        languages=languages,
        dateRange=date_range,
        topicsInOriginalLanguage=result.get("topicsInOriginalLanguage", []),
        topicsInEnglish=result.get("topicsInEnglish", [])
    )