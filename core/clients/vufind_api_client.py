# -*- coding: utf-8 -*-
# =============================================================================
# vufind_api_client.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
VuFind REST API client for nsis FastAPI application.
"""

import requests
from urllib.parse import urlparse
from typing import Optional, List, Dict, Any
from app.config import settings


# HTTP Headers for API requests
BASE_HEADERS = {
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
}


class VuFindAPIError(Exception):
    """Base exception for VuFind API errors."""
    pass


class VuFindAPIClientError(VuFindAPIError):
    """Exception raised when the VuFind API returns an error response."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


class VuFindAPITimeoutError(VuFindAPIError):
    """Exception raised when the VuFind API request times out."""
    pass


class VuFindAPIClientSSRFError(VuFindAPIError):
    """Exception raised when a URL fails SSRF validation."""
    pass


class VuFindAPIClient:
    """
    Client for interacting with the VuFind REST API.

    This is a low-level client that handles:
    1. HTTP communication with the VuFind API
    2. URL conversion between web and API formats
    3. Basic error handling
    4. SSRF protection through URL validation
    """

    def __init__(self, base_url: str, web_url: str, timeout: int = 30):
        """
        Initialize the VuFind API client.

        Args:
            base_url: Base URL for the VuFind API
            web_url: Web interface base URL for URL conversion
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip('/')
        self.web_url = settings.vufind_base_url
        self.timeout = timeout
        self._allowed_domains = self._extract_allowed_domains()

    def _extract_allowed_domains(self) -> set:
        """
        Extract allowed domains from configured VuFind URLs.

        This is used for SSRF protection to ensure requests only go to trusted domains.

        Returns:
            Set of allowed domain strings (without protocol)
        """
        domains = set()

        # Add domains from configured URLs
        for url in [self.base_url, self.web_url]:
            if url:
                parsed = urlparse(url)
                if parsed.netloc:
                    domains.add(parsed.netloc.lower())

        return domains

    def _validate_url_for_ssr(self, url: str) -> None:
        """
        Validate that a URL is safe for SSRF protection.

        This method ensures the URL belongs to one of the allowed VuFind domains,
        preventing attacks where an attacker supplies internal URLs or cloud metadata endpoints.

        Args:
            url: The URL to validate

        Raises:
            VuFindAPIClientSSRFError: If the URL is not allowed
        """

        # Basic URL validation
        if not url or not isinstance(url, str):
            raise VuFindAPIClientSSRFError("Invalid URL: empty or not a string")

        # Check for schemes other than http/https
        parsed = urlparse(url)
        if parsed.scheme and parsed.scheme not in ('http', 'https'):
            raise VuFindAPIClientSSRFError(
                f"URL scheme '{parsed.scheme}' is not allowed. Only http and https are permitted."
            )

        # Check if the URL has a netloc (absolute URL check)
        if not parsed.netloc and not url.startswith('/'):
            raise VuFindAPIClientSSRFError(
                "URL must be either an absolute URL with domain or start with '/'"
            )

        # Skip validation for relative URLs (internal paths)
        if not parsed.netloc:
            return

        # Validate against allowed domains
        netloc = parsed.netloc.lower()
        is_allowed = any(
            netloc == domain or netloc.endswith('.' + domain)
            for domain in self._allowed_domains
        )

        if not is_allowed:
            raise VuFindAPIClientSSRFError(
                f"URL domain '{netloc}' is not in the allowed list: {self._allowed_domains}"
            )

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        headers = BASE_HEADERS.copy()
        headers["User-Agent"] = f"{settings.api_title}/{settings.api_version}"

        token = settings.vufind_api_token.strip()
        token_header = settings.vufind_api_token_header.strip()
        if token and token_header:
            headers[token_header] = token

        return headers

    def replace_url_prefix(self, url: str) -> str:
        """
        Convert a VuFind web URL to an API URL.

        Replaces the web interface prefix with the API prefix.
        Example:
            https://stabikat.de/Search/Results?lookfor=berlin
            → http://vufind-api.stabikat.de/api/v1/search?lookfor=berlin

        The query parameters are preserved as-is since the API handles them correctly.

        Args:
            url: The original VuFind web URL

        Returns:
            The converted API URL
        """
        # Define the prefix to replace
        web_prefix = f"{self.web_url}/Search/Results"
        api_prefix = f"{self.base_url}/search"

        if url.startswith(web_prefix):
            return url.replace(web_prefix, api_prefix, 1)

        # If URL doesn't have the standard prefix, try to construct API URL
        if "/Search/Results" in url:
            return url.replace(self.web_url, self.base_url)

        # Fallback: just prepend the API base URL if URL starts with /
        if url.startswith('/'):
            return f"{self.base_url}{url}"

        # Return as-is if we can't determine how to convert it
        return url

    def _prepare_request_kwargs(self) -> Dict[str, Any]:
        """Prepare keyword arguments for requests."""
        return {
            "headers": self._get_headers(),
            "timeout": self.timeout,
        }

    def reconstruct_full_title(self, record: Dict[str, Any]) -> str:
        """
        Reconstruct the full title from shortTitle and subTitle fields.

        The VuFind API returns 'title' without the subtitle delimiter,
        but provides 'shortTitle' and 'subTitle' separately.

        Args:
            record: A record dict from the VuFind API

        Returns:
            The full title with subtitle properly separated by ' : '
        """
        short_title = record.get('shortTitle', '')
        sub_title = record.get('subTitle', '')

        if short_title and sub_title:
            return f"{short_title} : {sub_title}"
        elif short_title:
            return short_title
        else:
            return record.get('title', '')

    def perform_search_request(self, api_url: str, fields: Optional[List[str]] = None, limit: int = 10) -> Dict[str, Any]:
        """
        Perform a search request to the VuFind API.

        This is a low-level method that handles the actual HTTP request to the VuFind API.
        It does not perform any business logic transformations on the response.

        Args:
            api_url: The API URL to request (should be converted using replace_url_prefix)
            fields: List of fields to request from the API
            limit: Maximum number of results to retrieve

        Returns:
            Raw API response as a dictionary

        Raises:
            VuFindAPIClientError: If the API returns an error response
            VuFindAPITimeoutError: If the request times out
        """
        from urllib.parse import urlparse, parse_qs

        parsed = urlparse(api_url)
        params = parse_qs(parsed.query)

        # Add fields if not already in the URL
        if fields and 'field[]' not in params and 'field' not in params:
            for field in fields:
                api_url += f"&field[]={field}"

        # Add limit if not already in the URL
        if limit and 'limit' not in params:
            api_url += f"&limit={limit}"

        # Prepare request kwargs (headers, timeout, proxies)
        kwargs = self._prepare_request_kwargs()

        # SSRF protection: validate URL before making request
        self._validate_url_for_ssr(api_url)

        try:
            # Perform the request
            response = requests.get(api_url, **kwargs)

            # Check for HTTP errors
            if response.status_code != 200:
                raise VuFindAPIClientError(
                    f"API returned status {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text
                )

            # Parse JSON response
            try:
                return response.json()
            except ValueError:
                raise VuFindAPIClientError(
                    "API returned invalid JSON",
                    status_code=response.status_code,
                    response_body=response.text
                )

        except requests.Timeout:
            raise VuFindAPITimeoutError(f"Request to {api_url} timed out after {self.timeout} seconds")
        except requests.RequestException as e:
            raise VuFindAPIClientError(f"Request failed: {str(e)}")

