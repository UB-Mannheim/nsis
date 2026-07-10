# -*- coding: utf-8 -*-
# =============================================================================
# responses.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Response schemas for nsis API v1 endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal


class SearchIntentResponse(BaseModel):
    """Response schema for search intent analysis."""

    searchIntent: str = Field(..., description="The detected search intent")


class QueryExpansionResponse(BaseModel):
    """Response schema for query expansion."""

    originalQuery: str = Field(..., description="The original query")
    positiveKeywordConcepts: Dict[str, List[str]] = Field(
        ..., description="Dict mapping each positive concept to its list of related terms"
    )
    negativeKeywordConcepts: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Dict mapping each negated concept to its list of related terms"
    )
    logicalTree: Optional[Dict[str, Any]] = Field(
        None,
        description="Logical tree structure for URL building with AND/OR/NOT relationships"
    )


class FilterValue(BaseModel):
    """Schema for a filter value with label and filter value."""

    label: str = Field(..., description="Human-readable label")
    filterValue: str = Field(..., description="Value to use in filter URL")


class QueryFacettesResponse(BaseModel):
    """Response schema for query facet extraction."""

    mediaForms: List[FilterValue] = Field(default_factory=list, description="Media type filters")
    contentGenres: List[FilterValue] = Field(default_factory=list, description="Content genre filters")
    authorNames: List[FilterValue] = Field(default_factory=list, description="Author name filters")
    languages: List[FilterValue] = Field(default_factory=list, description="Language filters")
    dateRange: Optional[Dict[str, Optional[int]]] = Field(None, description="Publication date range")
    topicsInOriginalLanguage: List[str] = Field(default_factory=list, description="Topics in original language")
    topicsInEnglish: List[str] = Field(default_factory=list, description="Topics in English")


class GNDHeading(BaseModel):
    """Schema for a GND subject heading."""

    heading: str = Field(..., description="The GND heading")
    gndId: str = Field(..., description="The GND identifier")
    conceptKey: str = Field(..., description="The concept key associated with this heading")


class BKNotation(BaseModel):
    """Schema for a BK (Basisklassifikation) notation."""

    notation: str = Field(..., description="The BK notation")
    label: str = Field(..., description="The BK label")


class QueryTransformationMetadata(BaseModel):
    """Metadata for query transformation response."""

    searchIntent: str = Field(..., description="The detected search intent")
    filters: Dict[str, List[FilterValue]] = Field(..., description="Extracted filters")
    gndHeadingsConcepts: Dict[str, List[GNDHeading]] = Field(
        default_factory=dict,
        description="GND headings grouped by concept key for efficient concept-based access"
    )
    bkNotations: List[BKNotation] = Field(default_factory=list, description="BK notations")
    dateRange: Optional[Dict[str, Optional[int]]] = Field(None, description="Publication date range")
    logicalTree: Optional[Dict[str, Any]] = Field(None, description="Logical tree structure")


class QueryTransformationResponse(BaseModel):
    """Response schema for query transformation."""

    metadata: QueryTransformationMetadata = Field(..., description="Transformation metadata")


class VuFindTitle(BaseModel):
    """Schema for a VuFind title result."""

    title: str = Field(..., description="The title")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    subjects: List[List[str]] = Field(default_factory=list, description="Subject headings as list of authority entries")
    year: Optional[str] = Field(None, description="Publication year")
    format: str = Field(..., description="Media format")
    url: str = Field(..., description="Direct URL to the record")
    summary: List[str] = Field(default_factory=list, description="Summary/abstract text")
    toc: List[str] = Field(default_factory=list, description="Table of contents")


class ResultCountResponse(BaseModel):
    """Response schema for result count."""

    totalResults: Optional[int] = Field(None, description="Total number of results")
    url: str = Field(..., description="The VuFind search URL")


class FirstTitlesResponse(BaseModel):
    """Response schema for first titles."""

    titles: List[VuFindTitle] = Field(..., description="List of retrieved titles")
    retrievedCount: int = Field(..., description="Number of titles retrieved")
    url: str = Field(..., description="The VuFind search URL")


class QueryQualityResponse(BaseModel):
    """Response schema for query quality assessment."""

    qualityScore: float = Field(..., ge=0.0, le=1.0, description="Quality score (0.0 - 1.0)")
    originalQuery: str = Field(..., description="The original natural language query")
    assessment: str = Field(..., description="Assessment of query quality")
    relevantIndices: List[int] = Field(default_factory=list, description="Indices (1-based) of relevant titles")
    answer: str = Field(default="", description="Answer to the question if the query is a question, otherwise empty string")


class VocabularyResult(BaseModel):
    """Schema for a vocabulary lookup result."""

    id: str = Field(..., description="The identifier")
    label: str = Field(..., description="The label")
    notation: Optional[str] = Field(None, description="The notation (if applicable)")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")


class VocabularyLookupResponse(BaseModel):
    """Response schema for vocabulary lookup."""

    vocabulary: str = Field(..., description="The vocabulary searched")
    query: str = Field(..., description="The search query")
    results: List[VocabularyResult] = Field(..., description="List of matching results")


class PerformVuFindSearchResponse(BaseModel):
    """Response schema for performing VuFind search."""

    totalResults: Optional[int] = Field(None, description="Total number of results")
    titles: List[VuFindTitle] = Field(..., description="List of retrieved titles")
    retrievedCount: int = Field(..., description="Number of titles retrieved")
    url: str = Field(..., description="The VuFind search URL")


class BuildLogicalTreeResponse(BaseModel):
    """Response schema for building a logical tree structure."""

    query: str = Field(..., description="The original user query")
    logicalTree: Optional[Dict[str, Any]] = Field(
        None,
        description="The logical tree structure with AND/OR/NOT relationships between topic headings"
    )


class AddKeywordToConceptsResponse(BaseModel):
    """Response schema for keyword to concept mapping."""

    keyword: str = Field(..., description="The original keyword")
    decision: Literal["sub_concept", "super_concept", "new_concept"] = Field(
        ...,
        description="'sub_concept' to use existing concept, 'super_concept' to create new and reassign others, 'new_concept' to create new concept"
    )
    conceptKey: str = Field(..., description="The concept key to use")
    isNewConcept: bool = Field(..., description="True if a new concept was created")
    updated_concepts: Dict[str, List[str]] = Field(
        ...,
        description="The complete updated concepts dictionary"
    )