# -*- coding: utf-8 -*-
# =============================================================================
# __init__.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
LLM output schemas for nsis inference.

These schemas define the expected structure of LLM responses for each inference task.
Used for structured output parsing and validation with jsonschema.

Import schemas from here, not from individual files.
"""

from core.schemas.search_intent import NsisQtSchemaSearchIntent, SearchIntent
from core.schemas.expand import QueryExpansion
from core.schemas.facettes import NsisQtSchemaFacettes, MediaForms, ContentGenre, Language
from core.schemas.logical_tree import KeywordMappingDecision
from core.schemas.reranker import NsisQtSchemaReranker
from core.schemas.query_quality import QueryQualityAssessment

__all__ = [
    "NsisQtSchemaSearchIntent",
    "SearchIntent",
    "QueryExpansion",
    "NsisQtSchemaFacettes",
    "MediaForms",
    "ContentGenre",
    "Language",
    "KeywordMappingDecision",
    "NsisQtSchemaReranker",
    "QueryQualityAssessment",
]
