# -*- coding: utf-8 -*-
# =============================================================================
# router.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
API router for nsis API v1.
Aggregates all v1 endpoints.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    search_intent,
    query_expansion,
    query_facettes,
    query_transformation,
    vufind_search,
    query_quality,
    vocabulary_lookup,
    logical_tree,
    keyword_mapping,
)

router = APIRouter()

# Include all endpoint routers
router.include_router(search_intent.router)
router.include_router(query_expansion.router)
router.include_router(query_facettes.router)
router.include_router(query_transformation.router)
router.include_router(vufind_search.router)
router.include_router(query_quality.router)
router.include_router(vocabulary_lookup.router)
router.include_router(logical_tree.router)
router.include_router(keyword_mapping.router)