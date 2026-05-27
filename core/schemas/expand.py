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
LLM output schema for query expansion.

Used by core.inference.expand module.
"""

from typing import Dict, List

from pydantic import BaseModel, Field


class QueryExpansion(BaseModel):
    """
    Structured output for query expansion.

    The LLM returns a JSON object with:
    - positiveConcepts: Dict mapping each positive concept/phrase to its list of related terms.
    - negativeConcepts: Dict mapping each negated concept/phrase to its list of related terms.
    """
    positive_concepts: Dict[str, List[str]] = Field(
        alias="positiveConcepts",
        description="Dict mapping each positive concept/phrase (from the user's query) to its list of related terms (including the original).",
        default_factory=dict
    )
    negative_concepts: Dict[str, List[str]] = Field(
        alias="negativeConcepts",
        description="Dict mapping each negated concept/phrase to its list of related terms (for exclusions like 'aber keine', 'nicht', 'ohne').",
        default_factory=dict
    )
