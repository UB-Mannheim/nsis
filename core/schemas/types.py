# -*- coding: utf-8 -*-
# =============================================================================
# types.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Shared type definitions for the nsis codebase.

This module centralizes type aliases used across multiple modules
to avoid duplication and ensure consistency.
"""

from typing import Any, Dict

# Type alias for Milvus search results
MilvusHit = Dict[str, Any]