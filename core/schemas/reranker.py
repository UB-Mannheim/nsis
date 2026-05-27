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
LLM output schema for search result reranking.

Used by core.inference.reranker module.
"""

from pydantic import BaseModel, Field
from typing import List


class NsisQtSchemaReranker(BaseModel):
    """
    Structured output for search result reranking.

    The LLM returns a JSON object containing:
    - indicesOfRelevantTopics: Indices of the relevant topics from the provided list.
    """
    indices_of_relevant_topics: List[int] = Field(
        default_factory=list,
        alias="indicesOfRelevantTopics",
        description="The indices of the relevant topics in relation to the USER REQUEST."
    )

    class Config:
        populate_by_name = True
