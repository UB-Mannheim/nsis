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
Schema for logical tree keyword mapping decision.

Used by core.inference.logical_tree module.
"""

from typing import Literal, List, Optional
from pydantic import BaseModel, Field


class KeywordMappingDecision(BaseModel):
    """Structured output for keyword-to-concept mapping decision."""
    decision: Literal["sub_concept", "super_concept", "new_concept"] = Field(
        ...,
        description="'sub_concept' to use existing concept, 'super_concept' to create new and reassign others, 'new_concept' to create new concept"
    )
    concept_key: str = Field(
        ...,
        description="Existing concept key if decision='sub_concept', or keyword itself if decision='new_concept' or 'super_concept'"
    )
    absorbed_concepts: Optional[List[str]] = Field(
        default=None,
        description="List of concept keys to absorb for super_concept decisions"
    )
