# -*- coding: utf-8 -*-
# =============================================================================
# expand.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Query expansion inference for nsis.

Expands user query with related keywords for better search recall.
"""

import json
from typing import Dict, Optional

from core.inference.base import perform_inference, is_well_formed_json
from core.models_config import MODEL_EXPAND, TEMP_EXPAND, MODEL_PROVIDER_SORT
from core.read_prompt import read_prompt
from core.schemas import QueryExpansion
from app.utils.dev_print import DevPrint


async def perform_query_expansion(user_request: str, search_intent: Optional[str] = None) -> Dict:
    """
    Expand user query with related keywords for better search recall.

    Args:
        user_request: Original search query
        search_intent: Optional search intent to adapt expansion strategy

    Returns:
        dict: Contains 'positiveConcepts' and 'negativeConcepts' dicts mapping concepts to related terms
    """
    system_prompt = read_prompt("system_prompt_expand")

    # Build user prompt with optional context about search intent
    user_prompt = "## USER REQUEST\n\n" + user_request
    if search_intent == "searchQuestion":
        search_question_context = read_prompt("user_prompt_expand_search_question")
        user_prompt += "\n\n## CONTEXT\n" + search_question_context

    result = await perform_inference(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=MODEL_EXPAND,
        response_format=QueryExpansion,
        temperature=TEMP_EXPAND,
        provider_sort=MODEL_PROVIDER_SORT
    )

    if is_well_formed_json(result):
        generated_json = json.loads(result)
        positive_concepts = generated_json.get("positiveConcepts", {})
        negative_concepts = generated_json.get("negativeConcepts", {})

        DevPrint.info("Query Expansion:")
        DevPrint.debug(f"   Positive Concepts: {positive_concepts}")
        DevPrint.debug(f"   Negative Concepts: {negative_concepts}")
        return {
            "positiveConcepts": positive_concepts,
            "negativeConcepts": negative_concepts
        }
    else:
        return {"positiveConcepts": {}, "negativeConcepts": {}}
