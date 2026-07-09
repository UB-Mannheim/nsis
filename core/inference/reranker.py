# -*- coding: utf-8 -*-
# =============================================================================
# reranker.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Search result reranking inference for nsis.

Reranks search results based on relevance to user query.
"""

import json
from typing import Dict, List

from core.inference.base import perform_inference, is_well_formed_json, create_numbered_list
from core.models_config import MODEL_RERANKER, TEMP_RERANKER, MODEL_PROVIDER_SORT
from core.read_prompt import read_prompt
from core.schemas import NsisQtSchemaReranker
from app.utils.dev_print import DevPrint


async def rerank_search_results(user_request: str, results: List[str], type: str) -> Dict:
    """
    Rerank search results based on relevance to user query.

    Args:
        user_request: Original search query
        results: List of search result topics

    Returns:
        dict: Contains indicesOfRelevantTopics list
    """
    system_prompt = read_prompt("system_prompt_reranker_search")
    numbered_results = create_numbered_list(results)
    user_prompt = f"## USER REQUEST\n\n{user_request}\n\n## TOPICS\n\n{numbered_results}"

    DevPrint.debug(f"Reranking {type} topics:\n{numbered_results}")

    result = await perform_inference(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=MODEL_RERANKER,
        response_format=NsisQtSchemaReranker,
        temperature=TEMP_RERANKER,
        #provider_sort=MODEL_PROVIDER_SORT
    )

    if is_well_formed_json(result):
        generated_json = json.loads(result)
        DevPrint.result(f"Selected {type} (indices): {generated_json['indicesOfRelevantTopics']}")
        return generated_json
    else:
        return json.loads("{}")


async def rerank_vocabulary_lookup(user_request: str, results: List[str], type: str) -> Dict:
    """
    Rerank vocabulary lookup results based on relevance to user search term.

    Uses a less restrictive prompt than rerank_search_results to select
    more topics for vocabulary discovery purposes.

    Args:
        user_request: Original search term
        results: List of search result topics

    Returns:
        dict: Contains indicesOfRelevantTopics list
    """
    system_prompt = read_prompt("system_prompt_reranker_vocabulary")
    numbered_results = create_numbered_list(results)
    user_prompt = f"## USER REQUEST\n\n{user_request}\n\n## TOPICS\n\n{numbered_results}"

    DevPrint.debug(f"Reranking {type} topics:\n{numbered_results}")

    result = await perform_inference(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=MODEL_RERANKER,
        response_format=NsisQtSchemaReranker,
        temperature=TEMP_RERANKER,
        #provider_sort=MODEL_PROVIDER_SORT
    )

    if is_well_formed_json(result):
        generated_json = json.loads(result)
        DevPrint.result(f"Selected {type} (indices): {generated_json['indicesOfRelevantTopics']}")
        return generated_json
    else:
        return json.loads("{}")
