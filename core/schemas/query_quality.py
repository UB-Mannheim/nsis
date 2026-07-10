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
LLM output schema for query quality assessment.

Used by core.inference.query_quality module.
"""

from pydantic import BaseModel, Field
from typing import List


class QueryQualityAssessment(BaseModel):
    """
    Structured output for query quality assessment.

    The LLM returns a JSON object containing:
    - assessment: Brief explanation of the quality score
    - qualityScore: Score from 0.0 (poor) to 1.0 (excellent)
    - relevantTitles: List of titles from the results that are relevant
    - answer: Answer to the question if the query is a question, otherwise empty string
    """
    assessment: str = Field(
        ...,
        description="Brief explanation of the quality score, describing how well the titles match the query."
    )

    quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        alias="qualityScore",
        description="Quality score from 0.0 (poor) to 1.0 (excellent) indicating how well the retrieved titles match the query intent."
    )

    relevant_indices: List[int] = Field(
        default_factory=list,
        alias="relevantIndices",
        description="List of indices (1-based) of titles from the retrieved results that are relevant to the query."
    )

    answer: str = Field(
        default="",
        description="Answer to the question if the query is a question, otherwise empty string."
    )

    class Config:
        populate_by_name = True
