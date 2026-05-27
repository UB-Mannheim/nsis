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
Inference functions for nsis.

This package provides async functions for LLM-based query analysis and transformation.
Import inference functions from here, not from individual modules.
"""

from core.inference.base import perform_inference
from core.inference.search_intent import analyze_search_intent
from core.inference.expand import perform_query_expansion
from core.inference.facettes import extract_facettes
from core.inference.logical_tree import build_logical_tree
from core.inference.reranker import rerank_search_results
from core.inference.query_quality import assess_query_quality

__all__ = [
    "perform_inference",
    "analyze_search_intent",
    "perform_query_expansion",
    "extract_facettes",
    "build_logical_tree",
    "rerank_search_results",
    "assess_query_quality",
]
