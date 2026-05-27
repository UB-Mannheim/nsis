# -*- coding: utf-8 -*-
# =============================================================================
# facettes.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Facet extraction inference for nsis.

Extracts faceted search parameters from user query.
"""

import json
from typing import Dict

from core.inference.base import perform_inference, is_well_formed_json
from core.models_config import MODEL_EXTRACT_FACETTES, TEMP_EXTRACT_FACETTES, MODEL_PROVIDER_SORT
from core.read_prompt import read_prompt
from core.schemas import NsisQtSchemaFacettes


async def extract_facettes(user_request: str) -> Dict:
    """
    Extract faceted search parameters from user query.

    First generates a description of the request, then extracts facets.

    Args:
        user_request: User search query

    Returns:
        dict: Contains extracted facet categories and values
    """

    system_prompt_extract = read_prompt("system_prompt_extract_facettes")
    user_prompt_extract = "## USER REQUEST\n\n" + user_request

    result = await perform_inference(
        system_prompt=system_prompt_extract,
        user_prompt=user_prompt_extract,
        model=MODEL_EXTRACT_FACETTES,
        response_format=NsisQtSchemaFacettes,
        temperature=TEMP_EXTRACT_FACETTES,
        provider_sort=MODEL_PROVIDER_SORT
    )

    if is_well_formed_json(result):
        generated_json = json.loads(result)
        return generated_json
    else:
        return json.loads("{}")
