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
LLM output schema for search intent analysis.

Used by core.inference.search_intent module.
"""

from pydantic import BaseModel, Field
from enum import Enum


class SearchIntent(str, Enum):
    """
    Enumeration of possible search intents.
    """
    KNOWN_ITEM = "knownItem"
    TOPIC_SEARCH = "topicSearch"
    SEARCH_QUESTION = "searchQuestion"


class NsisQtSchemaSearchIntent(BaseModel):
    """
    Structured output for search intent analysis.

    The LLM returns a JSON object with:
    - searchIntent: The determined intent (knownItem, topicSearch or searchQuestion)
    """
    search_intent: SearchIntent = Field(
        default_factory=lambda: SearchIntent.TOPIC_SEARCH,
        alias="searchIntent",
        description="The search intent of the user request."
    )

    class Config:
        populate_by_name = True
