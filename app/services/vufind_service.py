# -*- coding: utf-8 -*-
# =============================================================================
# vufind_service.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
VuFind service for nsis FastAPI application.
Uses VuFind REST API for catalog operations.
"""

from typing import Dict, Any
import asyncio
from app.config import settings
from app.utils.dev_print import DevPrint
from core.clients.vufind_api_client import VuFindAPIClient, VuFindAPIClientError, VuFindAPITimeoutError, VuFindAPIClientSSRFError


class VuFindService:
    """
    Service for VuFind catalog operations using the REST API.

    This service is responsible for:
    1. High-level search operations
    2. Mapping API responses to application models
    3. Business logic transformations
    4. Error handling and recovery

    It delegates low-level HTTP communication to the VuFindAPIClient.
    """

    def __init__(self):
        """Initialize the VuFind service with an API client."""
        self.api_client = VuFindAPIClient(
            base_url=settings.vufind_api_base_url,
            web_url=settings.vufind_base_url,
            timeout=45
        )

    def _map_record_to_result(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map an API record to the internal result format.

        This method is responsible for transforming the raw API response format
        into the application's internal data model. It handles:
        1. Flattening complex nested structures (like authors)
        2. Normalizing fields to consistent formats
        3. Extracting primary values from arrays
        4. Reconstructing the full title with proper formatting

        Args:
            record: Raw record from VuFind API

        Returns:
            Mapped record with flattened authors, normalized fields, and full title
        """
        # Extract and flatten authors from nested structure
        authors_list = []
        authors_data = record.get("authors", {})
        if isinstance(authors_data, dict):
            for author_type in ['primary', 'secondary', 'corporate']:
                author_group = authors_data.get(author_type, {})
                if isinstance(author_group, dict):
                    authors_list.extend(author_group.keys())

        # Extract primary values from arrays
        primary_author = authors_list[0] if authors_list else None
        formats = record.get("formats", [])
        format_str = formats[0] if formats else "Unknown"
        publication_dates = record.get("publicationDates", [])
        year = publication_dates[0] if publication_dates else None
        url = record.get("recordPage", "")
        subjects = record.get("subjects", [])
        summary = record.get("summary", [])
        toc = record.get("toc", [])

        # Reconstruct full title from shortTitle and subTitle
        full_title = self.api_client.reconstruct_full_title(record)

        # Return the mapped record in the application's format
        return {
            "title": full_title,
            "authors": authors_list,
            "author": primary_author,
            "year": year,
            "format": format_str,
            "url": url,
            "subjects": subjects,
            "summary": summary,
            "toc": toc,
        }

    async def get_vufind_data(
        self,
        url: str,
        get_count: bool = True,
        get_results: bool = False,
        max_results: int = 10
    ) -> Dict:
        """
        Get VuFind data via the REST API with flexible options.

        This is a high-level method that:
        1. Converts the web URL to an API URL
        2. Makes the API request using the client
        3. Processes the response data
        4. Maps records to the application's format

        Args:
            url: The VuFind search URL
            get_count: Whether to get result count
            get_results: Whether to get results
            max_results: Maximum number of results to retrieve

        Returns:
            Dictionary containing:
                - count: Total result count (int)
                - results: List of mapped result dictionaries
                - success: Whether the request succeeded
                - error: Error message if failed
        """
        def _make_request():
            # Convert web URL to API URL
            api_url = self.api_client.replace_url_prefix(url)

            # Define fields to request from the API
            all_fields = [
                "authors", "formats", "id", "languages", "series", "subjects", "title", "urls",
                "publicationDates", "recordPage",
                "shortTitle", "subTitle", "summary", "toc"
            ]

            try:
                # Use the client to make the API request
                data = self.api_client.perform_search_request(
                    api_url=api_url,
                    fields=all_fields,
                    limit=max_results
                )

                # Process the response data
                result_count = 0
                if get_count and data.get("resultCount"):
                    result_count = int(data.get("resultCount", 0))

                results = []
                if get_results:
                    records = data.get("records", [])

                    DevPrint.debug(f"VuFind API: url={api_url}, max_results={max_results}, records_returned={len(records)}, result_count={result_count}")

                    # Map records to application format
                    for record in records[:max_results]:
                        mapped = self._map_record_to_result(record)
                        results.append(mapped)

                return {
                    "success": True,
                    "error": None,
                    "count": result_count,
                    "results": results
                }

            except VuFindAPIClientError as e:
                return {
                    "success": False,
                    "error": f"API error: {str(e)}",
                    "count": 0,
                    "results": []
                }
            except VuFindAPITimeoutError as e:
                return {
                    "success": False,
                    "error": f"API timeout: {str(e)}",
                    "count": 0,
                    "results": []
                }
            except VuFindAPIClientSSRFError as e:
                return {
                    "success": False,
                    "error": f"Invalid URL: the requested URL {str(e)} is not allowed. Only valid VuFind URLs are permitted.",
                    "count": 0,
                    "results": []
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Unexpected error: {str(e)}",
                    "count": 0,
                    "results": []
                }

        return await asyncio.to_thread(_make_request)
