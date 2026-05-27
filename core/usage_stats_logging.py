# -*- coding: utf-8 -*-
# =============================================================================
# usage_stats_logging.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Usage statistics logging for nsis core components.

Provides structured logging for:
- Basic metrics: endpoint hits, request/response sizes, latency, client IPs
- Business metrics: search terms, result counts, facets extracted, query quality scores
- Performance metrics: per-operation latency breakdowns (embedding, LLM calls, Milvus search, etc.)
- Query metrics: dedicated log for /query-judge-quality endpoint (query, result_count, quality_score)
"""

import inspect
import json
import logging
import logging.handlers
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _get_caller_function_name() -> str:
    """
    Get the name of the calling function using the inspect module.

    Returns:
        str: The function name of the grandparent (the function that called the function
             that called this helper), or "unknown" if unable to determine.
    """
    try:
        # Get the caller's frame
        # Call stack: this function -> logger method -> perform_inference -> expand_facettes (grandparent)
        frame = inspect.currentframe()
        if frame is None:
            return "unknown"
        # Go back 3 frames: current function -> logger method -> calling function -> grandparent
        f_back_1 = frame.f_back
        if f_back_1 is None:
            return "unknown"
        f_back_2 = f_back_1.f_back
        if f_back_2 is None:
            return "unknown"
        grandparent_frame = f_back_2.f_back
        if grandparent_frame is None:
            return "unknown"
        return grandparent_frame.f_code.co_name
    except Exception:
        return "unknown"


class UsageStatsLogger:
    """
    Centralized usage statistics logger with separate loggers for
    basic, business, and performance metrics.
    """

    def __init__(self):
        self._basic_logger: Optional[logging.Logger] = None
        self._business_logger: Optional[logging.Logger] = None
        self._performance_logger: Optional[logging.Logger] = None
        self._query_logger: Optional[logging.Logger] = None

    def setup(self, log_dir: str) -> None:
        """
        Set up the three usage statistics loggers.

        Args:
            log_dir: Directory to store log files
        """
        os.makedirs(log_dir, exist_ok=True)

        # Basic metrics logger
        self._basic_logger = self._create_logger(
            "nsis.stats.basic",
            os.path.join(log_dir, "nsis_stats_basic.log")
        )

        # Business metrics logger
        self._business_logger = self._create_logger(
            "nsis.stats.business",
            os.path.join(log_dir, "nsis_stats_business.log")
        )

        # Performance metrics logger
        self._performance_logger = self._create_logger(
            "nsis.stats.performance",
            os.path.join(log_dir, "nsis_stats_performance.log")
        )

        # Query metrics logger (dedicated log for /query-judge-quality endpoint)
        self._query_logger = self._create_logger(
            "nsis.stats.query",
            os.path.join(log_dir, "nsis_stats_query.log")
        )

    def _create_logger(self, name: str, log_file: str) -> logging.Logger:
        """Create a logger with rotating file handler for JSON output."""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        logger.propagate = False

        # Clear existing handlers
        logger.handlers.clear()

        # Add rotating file handler
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        return logger

    def _format_log_entry(self, log_type: str, data: Dict[str, Any]) -> str:
        """Format a log entry as JSON."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": log_type,
            **data
        }
        return json.dumps(entry, default=str, ensure_ascii=False)

    def log_basic(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        client_ip: Optional[str] = None,
        latency_ms: Optional[float] = None,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None,
        request_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        **extra: Any
    ) -> None:
        """
        Log basic API metrics.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: Response status code
            client_ip: Client IP address
            latency_ms: Request latency in milliseconds
            request_size_bytes: Request body size in bytes
            response_size_bytes: Response body size in bytes
            request_id: Request tracking ID
            user_agent: Client user agent string
            **extra: Additional fields to include
        """
        if not self._basic_logger:
            return

        data = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            **({k: v for k, v in {
                "client_ip": client_ip,
                "latency_ms": round(latency_ms, 2) if latency_ms is not None else None,
                "request_size_bytes": request_size_bytes,
                "response_size_bytes": response_size_bytes,
                "request_id": request_id,
                "user_agent": user_agent,
            }.items() if v is not None}),
            **extra
        }

        self._basic_logger.info(self._format_log_entry("basic", data))

    def log_business(
        self,
        endpoint: str,
        search_term: Optional[str] = None,
        result_count: Optional[int] = None,
        facets_extracted: Optional[Dict[str, Any]] = None,
        query_quality_score: Optional[float] = None,
        request_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        **extra: Any
    ) -> None:
        """
        Log business-related metrics.

        Args:
            endpoint: API endpoint path
            search_term: The user's search query
            result_count: Number of results returned
            facets_extracted: Dictionary of extracted facets (e.g., {"mediaForms": 2, "authorNames": 1})
            query_quality_score: Quality score (0.0 - 1.0) if applicable
            request_id: Request tracking ID
            client_ip: Client IP address
            **extra: Additional fields to include
        """
        if not self._business_logger:
            return

        data = {
            "endpoint": endpoint,
            **({k: v for k, v in {
                "search_term": search_term,
                "result_count": result_count,
                "facets_extracted": facets_extracted,
                "query_quality_score": round(query_quality_score, 3) if query_quality_score is not None else None,
                "request_id": request_id,
                "client_ip": client_ip,
            }.items() if v is not None}),
            **extra
        }

        self._business_logger.info(self._format_log_entry("business", data))

    def log_performance(
        self,
        operation_type: str,
        duration_ms: float,
        model: Optional[str] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        cost_usd: Optional[float] = None,
        batch_size: Optional[int] = None,
        request_id: Optional[str] = None,
        **extra: Any
    ) -> None:
        """
        Log performance metrics for internal operations.

        Args:
            operation_type: Type of operation (e.g., "llm_inference", "embedding", "milvus_search")
            duration_ms: Operation duration in milliseconds
            model: Model name (for LLM operations)
            prompt_tokens: Number of prompt tokens (for LLM operations)
            completion_tokens: Number of completion tokens (for LLM operations)
            total_tokens: Total tokens used (for LLM operations)
            cost_usd: Cost in USD (for LLM operations)
            batch_size: Batch size (for embedding operations)
            request_id: Request tracking ID
            **extra: Additional fields to include
        """
        if not self._performance_logger:
            return

        # Auto-detect function name using inspect
        function_name = _get_caller_function_name()

        data = {
            "operation_type": operation_type,
            "function_name": function_name,
            "duration_ms": round(duration_ms, 2),
            **({k: v for k, v in {
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost_usd": round(cost_usd, 6) if cost_usd is not None else None,
                "batch_size": batch_size,
                "request_id": request_id,
            }.items() if v is not None}),
            **extra
        }

        self._performance_logger.info(self._format_log_entry("performance", data))

    def log_query(
        self,
        query: str,
        result_count: int,
        query_quality_score: float,
        request_id: Optional[str] = None,
        **extra: Any
    ) -> None:
        """
        Log query-quality-specific metrics. Only called from /query-judge-quality endpoint.

        Args:
            query: The user's search query
            result_count: Number of results returned
            query_quality_score: Quality score (0.0 - 1.0)
            request_id: Request tracking ID
            **extra: Additional fields to include
        """
        if not self._query_logger:
            return

        data = {
            "query": query,
            "result_count": result_count,
            "query_quality_score": round(query_quality_score, 3),
            **({k: v for k, v in {
                "request_id": request_id,
            }.items() if v is not None}),
            **extra
        }

        self._query_logger.info(self._format_log_entry("query", data))


# Global instance
usage_stats_logger = UsageStatsLogger()


def setup_usage_stats_loggers(log_dir: str) -> UsageStatsLogger:
    """
    Set up usage statistics loggers.

    Args:
        log_dir: Directory to store log files

    Returns:
        The configured UsageStatsLogger instance
    """
    usage_stats_logger.setup(log_dir)
    return usage_stats_logger

