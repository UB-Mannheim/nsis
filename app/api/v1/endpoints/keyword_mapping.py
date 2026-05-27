# -*- coding: utf-8 -*-
# =============================================================================
# keyword_mapping.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Keyword mapping endpoint for nsis API v1.

Maps custom keywords to existing concepts or creates new concepts using LLM.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Request
from app.api.v1.schemas.requests import AddKeywordToConceptsRequest
from app.api.v1.schemas.responses import AddKeywordToConceptsResponse
from app.rate_limit import limiter, get_rate_limit
from app.utils.abort import check_disconnected
from app.utils.dev_print_api import api_call_start, api_call_end
from core.inference.logical_tree import add_keyword_to_concepts
from core.usage_stats_logging import usage_stats_logger

router = APIRouter()


def apply_concept_decision(
    existing_concepts: Dict[str, List[str]],
    keyword: str,
    decision: str,
    concept_key: str,
    absorbed_concepts: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """
    Apply the LLM decision to produce the updated concepts dictionary.

    This is done in Python to ensure consistency and prevent frontend/backend divergence.

    Args:
        existing_concepts: The current concepts dictionary
        keyword: The keyword being mapped
        decision: 'sub_concept', 'super_concept', or 'new_concept'
        concept_key: The target concept key
        absorbed_concepts: List of concept keys to absorb for super_concept decisions

    Returns:
        The updated concepts dictionary
    """
    # Deep copy to avoid mutating input
    updated = {k: list(v) for k, v in existing_concepts.items()}

    if decision == "sub_concept":
        # Map keyword to existing concept
        if concept_key not in updated:
            updated[concept_key] = []
        if keyword not in updated[concept_key]:
            updated[concept_key].append(keyword)

    elif decision == "super_concept":
        # Create new supercategory and reassign existing terms
        if concept_key not in updated:
            updated[concept_key] = []
        if keyword not in updated[concept_key]:
            updated[concept_key].append(keyword)

        # Python computes absorption from existing_concepts
        if absorbed_concepts:
            for from_concept in absorbed_concepts:
                if from_concept not in updated:
                    continue
                # terms come from existing_concepts - Python has the data!
                terms = list(existing_concepts[from_concept])
                for term in terms:
                    if term in updated[from_concept]:
                        updated[from_concept].remove(term)
                    if term not in updated[concept_key]:
                        updated[concept_key].append(term)
                if len(updated[from_concept]) == 0:
                    del updated[from_concept]

    elif decision == "new_concept":
        # Create new concept with keyword
        if concept_key not in updated:
            updated[concept_key] = []
        if keyword not in updated[concept_key]:
            updated[concept_key].append(keyword)

    return updated


@router.post("/add-keyword-to-concepts", response_model=AddKeywordToConceptsResponse)
@limiter.limit(get_rate_limit("add-keyword-to-concepts"))
async def add_keyword_to_concepts_endpoint(
    request: Request,
    api_request: AddKeywordToConceptsRequest,
):
    """
    Map a keyword to an existing concept or create a new concept.

    Uses LLM to analyze the keyword against existing concepts and decide
    whether to:
    - Map the keyword to an existing concept (if semantically related)
    - Create a new concept for the keyword (if distinct topic)
    - Create a new supercategory and reassign existing concepts (if keyword is a supertopic)
    """
    import time
    endpoint = "/api/v1/add-keyword-to-concepts"
    api_call_start(endpoint, "POST", {"keyword": api_request.keyword})
    start_time = time.time()

    # Check if client disconnected before starting LLM operation
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    result = await add_keyword_to_concepts(
        keyword=api_request.keyword,
        existing_concepts=api_request.existing_concepts
    )

    # Check if client disconnected after LLM call
    if await check_disconnected(request):
        api_call_end(endpoint, 499, (time.time() - start_time) * 1000)
        return

    duration_ms = (time.time() - start_time) * 1000
    api_call_end(endpoint, 200, duration_ms)

    # Apply decision in Python to produce updated concepts
    updated_concepts = apply_concept_decision(
        existing_concepts=api_request.existing_concepts,
        keyword=api_request.keyword,
        decision=result["decision"],
        concept_key=result["concept_key"],
        absorbed_concepts=result.get("absorbed_concepts")
    )

    # Log business metrics for usage statistics
    request_id = getattr(request.state, 'request_id', None)
    client_ip = request.client.host if request.client else None
    usage_stats_logger.log_business(
        endpoint="/api/v1/add-keyword-to-concepts",
        search_term=api_request.keyword,
        result_count=1,
        request_id=request_id,
        client_ip=client_ip
    )

    return AddKeywordToConceptsResponse(
        keyword=api_request.keyword,
        decision=result["decision"],
        conceptKey=result["concept_key"],
        isNewConcept=(result["decision"] in ["new_concept", "super_concept"]),
        updated_concepts=updated_concepts
    )
