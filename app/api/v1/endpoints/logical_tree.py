# -*- coding: utf-8 -*-
# =============================================================================
# logical_tree.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Logical tree analysis endpoint for nsis API v1.
"""

from fastapi import APIRouter, Request
from app.api.v1.schemas.requests import BuildLogicalTreeRequest
from app.api.v1.schemas.responses import BuildLogicalTreeResponse
from app.rate_limit import limiter, get_rate_limit
from app.utils.abort import check_disconnected
from app.utils.dev_print_api import api_call_start, api_call_end
from core.usage_stats_logging import usage_stats_logger
from core.inference.logical_tree import build_logical_tree

router = APIRouter()


@router.post("/build-logical-tree", response_model=BuildLogicalTreeResponse)
@limiter.limit(get_rate_limit("build-logical-tree"))
async def build_logical_tree_endpoint(
    request: Request,
    api_request: BuildLogicalTreeRequest,
):
    """
    Build a logical tree structure from positive and negative concepts.

    The logical tree groups topic headings with AND/OR/NOT operators to build
    structured search queries suitable for building VuFind search URLs.
    The root operator is always AND.
    """
    import time
    endpoint = "/api/v1/build-logical-tree"
    api_call_start(endpoint, "POST", {"query": api_request.query})
    start_time = time.time()

    # Check if client disconnected before starting LLM operation
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    # Build logical tree from positive and negative concepts
    positive_concepts = api_request.positive_keywords
    negative_concepts = api_request.negative_keywords
    result = build_logical_tree(positive_concepts, negative_concepts)

    # Check if client disconnected after tree building
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
        endpoint="/api/v1/build-logical-tree",
        search_term=api_request.query,
        result_count=total_concepts,
        request_id=request_id,
        client_ip=client_ip
    )

    return BuildLogicalTreeResponse(
        query=api_request.query,
        logicalTree=result
    )