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
Search intent inference for nsis.

Analyzes user search query to determine search intent.
"""

import json
from typing import Dict

from core.inference.base import perform_inference, is_well_formed_json
from core.models_config import MODEL_SEARCH_INTENT, TEMP_SEARCH_INTENT, MODEL_PROVIDER_SORT
from core.read_prompt import read_prompt
from core.schemas import NsisQtSchemaSearchIntent
from app.utils.dev_print import DevPrint


async def analyze_search_intent(user_request: str) -> Dict:
    """
    Analyze user search query to determine search intent.

    Args:
        user_request: Natural language search query

    Returns:
        dict: Contains searchIntent
    """
    system_prompt = read_prompt("system_prompt_search_intent")
    user_prompt = f"## USER REQUEST\n\n{user_request}"

    result = await perform_inference(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=MODEL_SEARCH_INTENT,
        response_format=NsisQtSchemaSearchIntent,
        temperature=TEMP_SEARCH_INTENT,
        #provider_sort=MODEL_PROVIDER_SORT
    )

    if is_well_formed_json(result):
        generated_json = json.loads(result)
        DevPrint.result(f"Intent: {generated_json.get('searchIntent', 'unknown')}")
        return generated_json
    else:
        return json.loads("{}")
