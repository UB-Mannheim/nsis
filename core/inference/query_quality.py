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
Query quality assessment inference for nsis.

Assesses quality of search results by evaluating title relevance.
"""

import json
from typing import Dict, List, Optional

from core.inference.base import perform_inference, is_well_formed_json, create_numbered_list
from core.models_config import MODEL_QUERY_QUALITY, TEMP_QUERY_QUALITY, MODEL_PROVIDER_SORT
from core.read_prompt import read_prompt
from core.schemas import QueryQualityAssessment
from app.utils.dev_print import DevPrint


# Mapping of language codes to display names
LANGUAGE_NAMES = {
    "de": "German",
    "en": "English",
}


async def assess_query_quality(user_request: str, titles: List[str], subjects: Optional[List[List[List[str]]]] = None, authors: Optional[List[List[str]]] = None, output_language: str = "de") -> Dict:
    """
    Assess quality of search results by evaluating title relevance.

    Args:
        user_request: Original search query
        titles: List of retrieved result titles
        subjects: List of subject heading lists for each title
        authors: List of author lists for each title
        output_language: Language for assessment output (default: "de" for German)

    Returns:
        dict: Contains assessment, qualityScore (0.0-1.0), and relevantTitles
    """
    system_prompt = read_prompt("system_prompt_query_quality")
    language_name = LANGUAGE_NAMES.get(output_language, "German")
    system_prompt = system_prompt.replace("{{LANGUAGE}}", language_name)
    numbered_titles = create_numbered_list(titles)

    # Build titles_with_metadata string if subjects and/or authors are provided
    if subjects or authors:
        titles_with_metadata = []
        for i, (title, title_subjects, title_authors) in enumerate(zip(titles, subjects or [[] for _ in titles], authors or [[] for _ in titles]), 1):
            parts = [f"{i}. {title}"]
            if title_authors:
                authors_str = ", ".join(title_authors)
                parts.append(f"Authors: {authors_str}")
            if title_subjects:
                subjects_str = ", ".join([", ".join(s) for s in title_subjects]) if title_subjects else "No subjects"
                parts.append(f"Subjects: {subjects_str}")
            titles_with_metadata.append(" | ".join(parts))
        user_prompt = f"## USER REQUEST\n\n{user_request}\n\n## RETRIEVED TITLES WITH METADATA\n\n{chr(10).join(titles_with_metadata)}"
    else:
        user_prompt = f"## USER REQUEST\n\n{user_request}\n\n## RETRIEVED TITLES\n\n{numbered_titles}"

    result = await perform_inference(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=MODEL_QUERY_QUALITY,
        response_format=QueryQualityAssessment,
        temperature=TEMP_QUERY_QUALITY,
        #provider_sort=MODEL_PROVIDER_SORT
    )

    if is_well_formed_json(result):
        generated_json = json.loads(result)
        DevPrint.success(f"Quality score: {generated_json.get('qualityScore', 0)} | Relevant: {generated_json.get('relevantIndices', [])}")
        return generated_json
    else:
        return {"assessment": "Failed to assess query quality", "qualityScore": 0.0, "relevantIndices": []}
