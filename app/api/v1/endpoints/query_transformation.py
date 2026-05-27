# -*- coding: utf-8 -*-
# =============================================================================
# query_transformation.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Query transformation endpoint for nsis API v1.
"""

from typing import Dict, List

from fastapi import APIRouter, Depends, Request
from app.api.v1.schemas.requests import QueryTransformationRequest
from app.api.v1.schemas.responses import (
    QueryTransformationResponse,
    QueryTransformationMetadata,
    GNDHeading,
    BKNotation,
    FilterValue
)
from app.dependencies import get_transformation_service
from app.rate_limit import limiter, get_rate_limit
from app.utils.abort import check_disconnected
from app.utils.dev_print_api import api_call_start, api_call_end
from core.usage_stats_logging import usage_stats_logger

router = APIRouter()


@router.post("/query-transformation", response_model=QueryTransformationResponse)
@limiter.limit(get_rate_limit("query-transformation"))
async def query_transformation(
    request: Request,
    api_request: QueryTransformationRequest,
    transformation_service = Depends(get_transformation_service)
):
    """
    Perform a complete transformation of the query.

    Includes analysis of catalog filters and facettes (mediaType, contentGenre, author, etc.)
    and semantic search terms.

    Returns search query ready to perform on the catalog.
    """
    import time
    endpoint = "/api/v1/query-transformation"
    api_call_start(endpoint, "POST", {"query": api_request.query, "search_intent": api_request.search_intent})
    start_time = time.time()

    # Check if client disconnected before starting expensive operation
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    result = await transformation_service.transform_query(api_request.query, api_request.search_intent)

    # Check if client disconnected after transformation service completes
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    duration_ms = (time.time() - start_time) * 1000
    api_call_end(endpoint, 200, duration_ms)

    # Convert metadata to response format
    metadata = result["metadata"]

    # Convert filters
    filters = {}
    for key, values in metadata["filters"].items():
        filters[key] = [
            FilterValue(label=v["label"], filterValue=v["filterValue"])
            for v in values
        ]

    # Convert GND headings grouped by concept key
    gnd_headings_concepts: Dict[str, List[GNDHeading]] = {}
    for concept_key, headings_list in metadata.get("gndHeadingsConcepts", {}).items():
        gnd_headings_concepts[concept_key] = [
            GNDHeading(heading=h["heading"], gndId=h["gnd_id"], conceptKey=h["conceptKey"])
            for h in headings_list
        ]

    # Convert BK notations
    bk_notations = [
        BKNotation(notation=b["notation"], label=b["label"])
        for b in metadata["bkNotations"]
    ]

    # Transfer logical tree
    logical_tree = metadata["logicalTree"]

    # Log business metrics for usage statistics
    request_id = getattr(request.state, 'request_id', None)
    client_ip = request.client.host if request.client else None
    usage_stats_logger.log_business(
        endpoint="/api/v1/query-transformation",
        search_term=api_request.query,
        result_count=sum(len(headings) for headings in gnd_headings_concepts.values()) + len(bk_notations),
        facets_extracted=metadata,
        request_id=request_id,
        client_ip=client_ip
    )

    return QueryTransformationResponse(
        metadata=QueryTransformationMetadata(
            searchIntent=metadata["searchIntent"],
            filters=filters,
            gndHeadingsConcepts=gnd_headings_concepts,
            bkNotations=bk_notations,
            dateRange=metadata["dateRange"],
            logicalTree=logical_tree
        )
    )