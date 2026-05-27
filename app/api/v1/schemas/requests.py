# -*- coding: utf-8 -*-
# =============================================================================
# requests.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Request schemas for nsis API v1 endpoints.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum


class SearchIntentEnum(str, Enum):
    """Enumeration of possible search intents."""
    KNOWN_ITEM = "knownItem"
    TOPIC_SEARCH = "topicSearch"
    SEARCH_QUESTION = "searchQuestion"


class SearchIntentRequest(BaseModel):
    """Request schema for search intent analysis."""

    query: str = Field(..., description="The search query to analyze", min_length=1, max_length=500)


class QueryExpansionRequest(BaseModel):
    """Request schema for query expansion."""

    query: str = Field(..., description="The query to expand", min_length=1, max_length=500)
    search_intent: Optional[str] = Field(
        default=None,
        description="Optional search intent to adapt query expansion strategy (e.g., 'searchQuestion')"
    )


class QueryFacettesRequest(BaseModel):
    """Request schema for query facet extraction."""

    query: str = Field(..., description="The query to analyze for facets", min_length=1, max_length=500)


class QueryTransformationRequest(BaseModel):
    """Request schema for query transformation."""

    query: str = Field(..., description="The natural language query to transform", min_length=1, max_length=500)
    search_intent: Optional[str] = Field(
        default=None,
        description="Optional search intent. If not provided, will be detected automatically."
    )


class ResultCountRequest(BaseModel):
    """Request schema for getting result count from VuFind URL."""

    url: str = Field(..., description="The VuFind search URL", min_length=1, max_length=2000)


class FirstTitlesRequest(BaseModel):
    """Request schema for getting first titles from VuFind URL."""

    url: str = Field(..., description="The VuFind search URL", min_length=1, max_length=2000)
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of titles to retrieve")


class VuFindTitleInput(BaseModel):
    """Input schema for VuFind title data passed from client."""

    title: str = Field(default="", description="Title of the work")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    subjects: List[List[str]] = Field(default_factory=list, description="Subject headings as list of authority entries")
    year: Optional[str] = Field(default=None, description="Publication year")
    format: Optional[str] = Field(default=None, description="Format/medium")
    url: Optional[str] = Field(default=None, description="URL to the record")
    summary: List[str] = Field(default_factory=list, description="Summary/abstract text")
    toc: List[str] = Field(default_factory=list, description="Table of contents")


class QueryQualityRequest(BaseModel):
    """Request schema for query quality assessment."""

    query: str = Field(..., description="The original natural language query", min_length=1, max_length=500)
    url: str = Field(..., description="The VuFind search URL to evaluate", min_length=1, max_length=2000)
    titles: Optional[List[VuFindTitleInput]] = Field(
        default=None,
        description="Optional pre-fetched VuFind titles to use instead of fetching again"
    )
    output_language: str = Field(
        default="de",
        description="Language for assessment output ('de' for German, 'en' for English)"
    )


class VocabularyLookupRequest(BaseModel):
    """Request schema for vocabulary lookup."""

    term: str = Field(..., description="The search term", min_length=1, max_length=500)
    vocabulary: str = Field(..., description="The vocabulary to search in (gnd-saz, bk)")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")


class PerformVuFindSearchRequest(BaseModel):
    """Request schema for performing VuFind search."""

    url: str = Field(..., description="The VuFind search URL", min_length=1, max_length=2000)
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of titles to retrieve")


class BuildLogicalTreeRequest(BaseModel):
    """Request schema for building a logical tree structure."""

    query: str = Field(..., description="The user search query", min_length=1, max_length=500)
    positive_keywords: Dict[str, List[str]] = Field(
        ...,
        description="Dict mapping positive concept keys to their related terms",
        min_length=1
    )
    negative_keywords: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Dict mapping negated concept keys to their related terms"
    )


class AddKeywordToConceptsRequest(BaseModel):
    """Request schema for mapping a keyword to concepts."""

    keyword: str = Field(..., description="The keyword to map", min_length=1, max_length=200)
    existing_concepts: Dict[str, List[str]] = Field(
        ...,
        description="Dict mapping concept keys to their related terms"
    )