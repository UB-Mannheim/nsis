# -*- coding: utf-8 -*-
# =============================================================================
# api_endpoints_test.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Integration tests for all FastAPI endpoints.
Tests run against a live instance of the API.

Usage:
    uv run tests/api_endpoints_test.py
"""

import pytest
import httpx


# Configuration - adjust these based on your environment
BASE_URL = "http://localhost:8083"
API_PREFIX = "/api"

# Timeout configuration - some endpoints may take up to 20 seconds due to LLM inference
# and external API calls
DEFAULT_TIMEOUT = 60.0  # seconds


class TestHealthEndpoints:
    """Tests for health and root endpoints."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test the root endpoint returns the Recherche-Kompass HTML interface."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(f"{BASE_URL}/")
            assert response.status_code == 200
            # Root endpoint returns HTML (Recherche-Kompass interface)
            assert response.headers.get("content-type", "").startswith("text/html")
            content = response.text
            assert len(content) > 0
            assert "html" in content.lower()

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test the health check endpoint."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(f"{BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "version" in data
            assert "supported_versions" in data


class TestSearchIntentEndpoint:
    """Tests for the search intent endpoint."""

    @pytest.mark.asyncio
    async def test_search_intent_basic_query(self):
        """Test search intent analysis with a basic query."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"query": "Bücher über Geschichte"}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/search-intent",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert "searchIntent" in data
            assert isinstance(data["searchIntent"], str)

    @pytest.mark.asyncio
    async def test_search_intent_known_item_query(self):
        """Test search intent with a known item query."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"query": "Goethe Faust"}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/search-intent",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert "searchIntent" in data

    @pytest.mark.asyncio
    async def test_search_intent_empty_query(self):
        """Test search intent with empty query (should fail validation)."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"query": ""}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/search-intent",
                json=payload
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_intent_missing_query(self):
        """Test search intent with missing query field."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/search-intent",
                json=payload
            )
            assert response.status_code == 422


class TestQueryExpansionEndpoint:
    """Tests for the query expansion endpoint."""

    @pytest.mark.asyncio
    async def test_query_expansion_basic(self):
        """Test query expansion with a basic query."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"query": "Künstliche Intelligenz"}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-expansion",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert "originalQuery" in data
            assert "positiveKeywordConcepts" in data
            assert "negativeKeywordConcepts" in data
            assert data["originalQuery"] == "Künstliche Intelligenz"
            assert isinstance(data["positiveKeywordConcepts"], dict)
            assert isinstance(data["negativeKeywordConcepts"], dict)

    @pytest.mark.asyncio
    async def test_query_expansion_english_query(self):
        """Test query expansion with an English query."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"query": "machine learning"}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-expansion",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert "positiveKeywordConcepts" in data
            assert isinstance(data["positiveKeywordConcepts"], dict)

    @pytest.mark.asyncio
    async def test_query_expansion_complex_query(self):
        """Test query expansion with a complex query."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"query": "Historische Romane aus dem 19. Jahrhundert"}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-expansion",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert "positiveKeywordConcepts" in data
            assert "negativeKeywordConcepts" in data


class TestQueryFacettesEndpoint:
    """Tests for the query facets endpoint."""

    @pytest.mark.asyncio
    async def test_query_facettes_basic(self):
        """Test facet extraction with a basic query."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"query": "Bücher von Goethe"}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-facettes",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert "mediaForms" in data
            assert "contentGenres" in data
            assert "authorNames" in data
            assert "languages" in data
            assert "dateRange" in data
            assert "topicsInOriginalLanguage" in data
            assert "topicsInEnglish" in data
            # All facet lists contain FilterValue objects with label and filterValue
            assert isinstance(data["mediaForms"], list)
            assert isinstance(data["contentGenres"], list)
            assert isinstance(data["authorNames"], list)
            assert isinstance(data["languages"], list)
            # Verify FilterValue structure if list is not empty
            for facet_list in ["mediaForms", "contentGenres", "authorNames", "languages"]:
                for item in data.get(facet_list, []):
                    assert "label" in item
                    assert "filterValue" in item

    @pytest.mark.asyncio
    async def test_query_facettes_with_media_type(self):
        """Test facet extraction with media type specified."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"query": "E-Books über Philosophie"}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-facettes",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert "mediaForms" in data
            # Verify FilterValue structure
            for item in data.get("mediaForms", []):
                assert "label" in item
                assert "filterValue" in item

    @pytest.mark.asyncio
    async def test_query_facettes_with_date_range(self):
        """Test facet extraction with date range in query."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"query": "Bücher aus den 1990er Jahren"}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-facettes",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert "dateRange" in data


class TestQueryTransformationEndpoint:
    """Tests for the query transformation endpoint."""

    @pytest.mark.asyncio
    async def test_query_transformation_basic(self):
        """Test query transformation with a basic query."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"query": "Bücher über Geschichte"}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-transformation",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert "metadata" in data
            assert isinstance(data["metadata"], dict)
            # Check metadata structure
            metadata = data["metadata"]
            assert "searchIntent" in metadata
            assert "filters" in metadata
            assert "gndHeadingsConcepts" in metadata
            assert "bkNotations" in metadata
            assert "dateRange" in metadata
            assert "logicalTree" in metadata
            # gndHeadingsConcepts is a dict mapping conceptKey to list of GNDHeading objects
            gndHeadingsConcepts = metadata.get("gndHeadingsConcepts", {})
            assert isinstance(gndHeadingsConcepts, dict)
            for conceptKey, headings in gndHeadingsConcepts.items():
                assert isinstance(headings, list)
                for heading in headings:
                    assert "heading" in heading
                    assert "gndId" in heading
            # bkNotations contains BKNotation objects with notation and label
            for notation in metadata.get("bkNotations", []):
                assert "notation" in notation
                assert "label" in notation

    @pytest.mark.asyncio
    async def test_query_transformation_complex(self):
        """Test query transformation with a complex query."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"query": "Deutsche Romane aus dem 20. Jahrhundert"}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-transformation",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert "metadata" in data
            metadata = data["metadata"]
            assert "gndHeadingsConcepts" in metadata
            assert "bkNotations" in metadata

    @pytest.mark.asyncio
    async def test_query_transformation_with_author(self):
        """Test query transformation with author specified."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"query": "Werke von Thomas Mann"}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-transformation",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert "metadata" in data


class TestPerformVuFindSearchEndpoint:
    """Tests for the perform VuFind search endpoint.

    These tests validate the perform-vufind-search endpoint which uses
    the VuFindAPIClient from core/vufind_api_client.py via
    VuFindService from app/services/vufind_service.py.
    """

    @pytest.mark.asyncio
    async def test_perform_vufind_search_valid_url(self):
        """Test performing VuFind search with a valid VuFind URL."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            # Use a sample VuFind URL - the API client converts web URLs to API URLs
            payload = {
                "url": "https://stabikat.de/Search/Results?lookfor=test&type=AllFields"
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/perform-vufind-search",
                json=payload
            )
            # May succeed or fail depending on actual VuFind API availability
            assert response.status_code in [200, 500, 503]
            if response.status_code == 200:
                data = response.json()
                assert "totalResults" in data
                assert "titles" in data
                assert "retrievedCount" in data
                assert "url" in data
                assert isinstance(data["titles"], list)
                # totalResults can be int or None depending on API response
                assert isinstance(data["totalResults"], (int, type(None)))
                # Verify title structure includes all VuFindTitle fields
                for title in data.get("titles", []):
                    assert "title" in title
                    assert "authors" in title
                    assert "subjects" in title
                    assert "format" in title
                    assert "url" in title
                    assert isinstance(title["authors"], list)
                    # subjects is List[List[str]] in the schema (list of authority entries)
                    assert isinstance(title["subjects"], list)
                    assert all(isinstance(s, list) for s in title["subjects"])

    @pytest.mark.asyncio
    async def test_perform_vufind_search_invalid_url(self):
        """Test performing VuFind search with an invalid URL."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"url": "not-a-valid-url"}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/perform-vufind-search",
                json=payload
            )
            # The API client may still return 200 with error info in results
            # or return an error status depending on how URL validation works
            assert response.status_code in [200, 400, 500]
            if response.status_code == 200:
                data = response.json()
                assert "titles" in data
                # Error handling returns empty results or None count
                assert isinstance(data["totalResults"], (int, type(None)))
                assert isinstance(data["titles"], list)
                # Verify title structure if any titles returned
                for title in data.get("titles", []):
                    assert "title" in title
                    assert "authors" in title
                    assert "subjects" in title
                    assert "format" in title
                    assert "url" in title

    @pytest.mark.asyncio
    async def test_perform_vufind_search_missing_url(self):
        """Test performing VuFind search with missing URL field."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/perform-vufind-search",
                json=payload
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_perform_vufind_search_default_limit(self):
        """Test performing VuFind search with default limit."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "url": "https://stabikat.de/Search/Results?lookfor=test&type=AllFields"
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/perform-vufind-search",
                json=payload
            )
            # May succeed or fail depending on actual VuFind API availability
            assert response.status_code in [200, 500, 503]
            if response.status_code == 200:
                data = response.json()
                assert "titles" in data
                assert "retrievedCount" in data
                assert isinstance(data["titles"], list)

    @pytest.mark.asyncio
    async def test_perform_vufind_search_custom_limit(self):
        """Test performing VuFind search with custom limit."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "url": "https://stabikat.de/Search/Results?lookfor=test&type=AllFields",
                "limit": 5
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/perform-vufind-search",
                json=payload
            )
            assert response.status_code in [200, 500, 503]
            if response.status_code == 200:
                data = response.json()
                assert "titles" in data
                assert len(data["titles"]) <= 5

    @pytest.mark.asyncio
    async def test_perform_vufind_search_limit_too_high(self):
        """Test performing VuFind search with limit exceeding maximum."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "url": "https://stabikat.de/Search/Results?lookfor=test&type=AllFields",
                "limit": 100  # Exceeds max of 50
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/perform-vufind-search",
                json=payload
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_perform_vufind_search_limit_too_low(self):
        """Test performing VuFind search with limit below minimum."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "url": "https://stabikat.de/Search/Results?lookfor=test&type=AllFields",
                "limit": 0  # Below min of 1
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/perform-vufind-search",
                json=payload
            )
            assert response.status_code == 422


class TestQueryQualityEndpoint:
    """Tests for the query quality endpoint.

    The query quality endpoint uses VuFindAPIClient via VuFindService to fetch
    titles, then uses inference service to assess query quality.
    VuFindTitle response includes: title, authors, subjects, year, format, url,
    summary, toc.
    """

    @pytest.mark.asyncio
    async def test_query_judge_quality_basic(self):
        """Test query judge quality with basic query and URL."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "query": "Bücher über Geschichte",
                "url": "https://stabikat.de/Search/Results?lookfor=geschichte&type=AllFields"
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-judge-quality",
                json=payload
            )
            # May succeed or fail depending on actual VuFind API availability
            assert response.status_code in [200, 500, 503]
            if response.status_code == 200:
                data = response.json()
                assert "qualityScore" in data
                assert "originalQuery" in data
                assert "relevantIndices" in data
                assert "assessment" in data
                assert isinstance(data["qualityScore"], float)
                assert 0.0 <= data["qualityScore"] <= 1.0
                # Verify relevantIndices is a list of integers
                assert isinstance(data["relevantIndices"], list)
                for idx in data.get("relevantIndices", []):
                    assert isinstance(idx, int)

    @pytest.mark.asyncio
    async def test_query_judge_quality_missing_query(self):
        """Test query judge quality with missing query field."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "url": "https://stabikat.de/Search/Results?lookfor=test&type=AllFields"
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-judge-quality",
                json=payload
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_query_judge_quality_missing_url(self):
        """Test query judge quality with missing URL field."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"query": "test query"}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-judge-quality",
                json=payload
            )
            assert response.status_code == 422


class TestVocabularyLookupEndpoint:
    """Tests for the vocabulary lookup endpoint."""

    @pytest.mark.asyncio
    async def test_vocabulary_lookup_gnd_saz(self):
        """Test vocabulary lookup for GND SAZ."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "term": "Geschichte",
                "vocabulary": "gnd-saz",
                "limit": 10
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/lookup-vocabulary",
                json=payload
            )
            # May succeed or fail depending on Milvus availability
            assert response.status_code in [200, 500, 503]
            if response.status_code == 200:
                data = response.json()
                assert "vocabulary" in data
                assert "query" in data
                assert "results" in data
                assert data["vocabulary"] == "gnd-saz"
                assert data["query"] == "Geschichte"
                assert isinstance(data["results"], list)

    @pytest.mark.asyncio
    async def test_vocabulary_lookup_bk(self):
        """Test vocabulary lookup for BK (Basisklassifikation)."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "term": "Geschichte",
                "vocabulary": "bk",
                "limit": 10
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/lookup-vocabulary",
                json=payload
            )
            assert response.status_code in [200, 500, 503]
            if response.status_code == 200:
                data = response.json()
                assert "vocabulary" in data
                assert "query" in data
                assert "results" in data
                assert data["vocabulary"] == "bk"
                assert isinstance(data["results"], list)

    @pytest.mark.asyncio
    async def test_vocabulary_lookup_gnd_geo(self):
        """Test vocabulary lookup for GND Geografika."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "term": "Berlin",
                "vocabulary": "gnd-geo",
                "limit": 10
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/lookup-vocabulary",
                json=payload
            )
            # May succeed or fail depending on Milvus availability
            assert response.status_code in [200, 500, 503]
            if response.status_code == 200:
                data = response.json()
                assert "vocabulary" in data
                assert "query" in data
                assert "results" in data
                assert data["vocabulary"] == "gnd-geo"
                assert data["query"] == "Berlin"
                assert isinstance(data["results"], list)

    @pytest.mark.asyncio
    async def test_vocabulary_lookup_invalid_vocabulary(self):
        """Test vocabulary lookup with invalid vocabulary."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "term": "test",
                "vocabulary": "invalid-vocab",
                "limit": 10
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/lookup-vocabulary",
                json=payload
            )
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_vocabulary_lookup_custom_limit(self):
        """Test vocabulary lookup with custom limit."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "term": "Philosophie",
                "vocabulary": "gnd-saz",
                "limit": 5
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/lookup-vocabulary",
                json=payload
            )
            assert response.status_code in [200, 500, 503]
            if response.status_code == 200:
                data = response.json()
                assert len(data["results"]) <= 5

    @pytest.mark.asyncio
    async def test_vocabulary_lookup_missing_term(self):
        """Test vocabulary lookup with missing term."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "vocabulary": "gnd-saz",
                "limit": 10
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/lookup-vocabulary",
                json=payload
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_vocabulary_lookup_missing_vocabulary(self):
        """Test vocabulary lookup with missing vocabulary."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "term": "test",
                "limit": 10
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/lookup-vocabulary",
                json=payload
            )
            assert response.status_code == 422


class TestEndpointIntegration:
    """Integration tests combining multiple endpoints."""

    @pytest.mark.asyncio
    async def test_full_search_workflow(self):
        """Test a complete search workflow using multiple endpoints."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            query = "Bücher über deutsche Geschichte"

            # Step 1: Analyze search intent
            intent_payload = {"query": query}
            intent_response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/search-intent",
                json=intent_payload
            )
            assert intent_response.status_code == 200
            intent_data = intent_response.json()
            assert "searchIntent" in intent_data

            # Step 2: Expand the query
            expansion_payload = {"query": query}
            expansion_response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-expansion",
                json=expansion_payload
            )
            assert expansion_response.status_code == 200
            expansion_data = expansion_response.json()
            assert "originalQuery" in expansion_data
            assert "positiveKeywordConcepts" in expansion_data
            assert "negativeKeywordConcepts" in expansion_data

            # Step 3: Extract facets
            facets_payload = {"query": query}
            facets_response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-facettes",
                json=facets_payload
            )
            assert facets_response.status_code == 200
            facets_data = facets_response.json()
            assert "mediaForms" in facets_data

            # Step 4: Transform query to URL
            transform_payload = {"query": query}
            transform_response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-transformation",
                json=transform_payload
            )
            assert transform_response.status_code == 200
            transform_data = transform_response.json()
            # query-transformation returns QueryTransformationResponse with metadata
            assert "metadata" in transform_data
            metadata = transform_data["metadata"]
            assert "searchIntent" in metadata
            assert "filters" in metadata

    @pytest.mark.asyncio
    async def test_vocabulary_search_workflow(self):
        """Test vocabulary lookup workflow."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            term = "Philosophie"

            # Search in GND SAZ
            gnd_payload = {
                "term": term,
                "vocabulary": "gnd-saz",
                "limit": 5
            }
            gnd_response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/lookup-vocabulary",
                json=gnd_payload
            )
            assert gnd_response.status_code in [200, 500, 503]

            # Search in BK
            bk_payload = {
                "term": term,
                "vocabulary": "bk",
                "limit": 5
            }
            bk_response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/lookup-vocabulary",
                json=bk_payload
            )
            assert bk_response.status_code in [200, 500, 503]


class TestErrorHandling:
    """Tests for error handling across endpoints."""

    @pytest.mark.asyncio
    async def test_invalid_json(self):
        """Test sending invalid JSON to endpoints."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/search-intent",
                content="invalid json"
            )
            # FastAPI returns 422 for JSON decode errors
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_nonexistent_endpoint(self):
        """Test accessing a nonexistent endpoint."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(
                f"{BASE_URL}{API_PREFIX}/v1/nonexistent"
            )
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_wrong_method(self):
        """Test using wrong HTTP method for endpoints."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            # Try GET on POST endpoint
            response = await client.get(
                f"{BASE_URL}{API_PREFIX}/v1/search-intent"
            )
            assert response.status_code == 405  # Method Not Allowed


class TestVuFindEndpoints:
    """Tests for VuFind API endpoints (stabikat.de).

    These tests use the VuFind REST API via VuFindAPIClient
    (core/vufind_api_client.py) and VuFindService
    (app/services/vufind_service.py).

    The VuFindTitle response structure includes:
    - title: str
    - authors: List[str]
    - subjects: List[List[str]] (list of authority entries)
    - year: Optional[str]
    - format: str
    - url: str
    - summary: List[str]
    - toc: List[str]

    totalResults can be int or None depending on API response.
    """

    # Example VuFind URLs for stabikat.de
    STABIKAT_SEARCH_URL = "https://stabikat.de/Search/Results?lookfor0=%22R%C3%B6misches+Reich%22&type0=Subject&join=AND&lookfor1=Geschichte&type1=AllFields"
    STABIKAT_SIMPLE_SEARCH = "https://stabikat.de/Search/Results?lookfor=Goethe&type=AllFields"

    @pytest.mark.asyncio
    async def test_perform_vufind_search_basic(self):
        """Test performing a VuFind search with basic URL."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "url": self.STABIKAT_SEARCH_URL,
                "limit": 10
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/perform-vufind-search",
                json=payload
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            assert "totalResults" in data
            assert "titles" in data
            assert "retrievedCount" in data
            assert "url" in data
            assert data["url"] == self.STABIKAT_SEARCH_URL
            assert isinstance(data["titles"], list)
            # totalResults can be int or None (API may return None for errors)
            assert isinstance(data["totalResults"], (int, type(None)))
            assert data["retrievedCount"] <= 10

    @pytest.mark.asyncio
    async def test_perform_vufind_search_simple_query(self):
        """Test performing a VuFind search with a simple query."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "url": self.STABIKAT_SIMPLE_SEARCH,
                "limit": 5
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/perform-vufind-search",
                json=payload
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            assert "totalResults" in data
            assert isinstance(data["totalResults"], (int, type(None)))
            assert "titles" in data
            assert data["retrievedCount"] <= 5

    @pytest.mark.asyncio
    async def test_perform_vufind_search_titles_structure(self):
        """Test that returned titles have correct VuFindTitle structure."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "url": self.STABIKAT_SIMPLE_SEARCH,
                "limit": 3
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/perform-vufind-search",
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                for title in data.get("titles", []):
                    # Verify core VuFindTitle fields are present
                    assert "title" in title
                    assert "authors" in title
                    assert "subjects" in title
                    assert "format" in title
                    assert "url" in title
                    assert isinstance(title["authors"], list)
                    assert isinstance(title["subjects"], list)
                    # year is optional, may or may not be present
                    if "year" in title:
                        assert isinstance(title["year"], (str, type(None)))

    @pytest.mark.asyncio
    async def test_perform_vufind_search_missing_url(self):
        """Test perform-vufind-search with missing URL field."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"limit": 10}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/perform-vufind-search",
                json=payload
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_perform_vufind_search_empty_url(self):
        """Test perform-vufind-search with empty URL."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"url": "", "limit": 10}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/perform-vufind-search",
                json=payload
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_perform_vufind_search_limit_bounds(self):
        """Test perform-vufind-search with limit at boundaries."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            # Test minimum limit (1)
            payload_min = {"url": self.STABIKAT_SIMPLE_SEARCH, "limit": 1}
            response_min = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/perform-vufind-search",
                json=payload_min
            )
            if response_min.status_code == 200:
                data_min = response_min.json()
                assert data_min["retrievedCount"] <= 1

            # Test maximum limit (50)
            payload_max = {"url": self.STABIKAT_SIMPLE_SEARCH, "limit": 50}
            response_max = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/perform-vufind-search",
                json=payload_max
            )
            if response_max.status_code == 200:
                data_max = response_max.json()
                assert data_max["retrievedCount"] <= 50

    @pytest.mark.asyncio
    async def test_query_judge_quality_basic(self):
        """Test query judge quality with a basic query and URL."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "query": "Bücher über Römisches Reich",
                "url": self.STABIKAT_SEARCH_URL
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-judge-quality",
                json=payload
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            assert "qualityScore" in data
            assert "originalQuery" in data
            assert "relevantIndices" in data
            assert "assessment" in data
            assert data["originalQuery"] == "Bücher über Römisches Reich"
            assert 0.0 <= data["qualityScore"] <= 1.0
            assert isinstance(data["relevantIndices"], list)

    @pytest.mark.asyncio
    async def test_query_judge_quality_goethe_query(self):
        """Test query judge quality with Goethe search query."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "query": "Faust von Goethe",
                "url": self.STABIKAT_SIMPLE_SEARCH
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-judge-quality",
                json=payload
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            assert "qualityScore" in data
            assert 0.0 <= data["qualityScore"] <= 1.0
            assert isinstance(data["relevantIndices"], list)

    @pytest.mark.asyncio
    async def test_query_judge_quality_titles_structure(self):
        """Test that query judge quality returns correct structure with relevantIndices."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {
                "query": "Philosophie",
                "url": "https://stabikat.de/Search/Results?lookfor=Philosophie&type=AllFields"
            }
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-judge-quality",
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                # QueryQualityResponse contains qualityScore, originalQuery, assessment, relevantIndices
                assert "qualityScore" in data
                assert "originalQuery" in data
                assert "assessment" in data
                assert "relevantIndices" in data
                assert isinstance(data["relevantIndices"], list)
                for idx in data.get("relevantIndices", []):
                    assert isinstance(idx, int)

    @pytest.mark.asyncio
    async def test_query_judge_quality_missing_query(self):
        """Test query-judge-quality with missing query field."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"url": self.STABIKAT_SEARCH_URL}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-judge-quality",
                json=payload
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_query_judge_quality_missing_url(self):
        """Test query-judge-quality with missing URL field."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"query": "Test query"}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-judge-quality",
                json=payload
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_query_judge_quality_empty_query(self):
        """Test query-judge-quality with empty query."""
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            payload = {"query": "", "url": self.STABIKAT_SEARCH_URL}
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/v1/query-judge-quality",
                json=payload
            )
            assert response.status_code == 422


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


if __name__ == "__main__":
    # Run tests with: pytest tests/test_api_endpoints.py -v
    # Or with custom base URL: API_BASE_URL=http://localhost:8000 pytest tests/test_api_endpoints.py -v
    pytest.main([__file__, "-v"])
