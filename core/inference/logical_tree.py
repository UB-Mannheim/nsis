# -*- coding: utf-8 -*-
# =============================================================================
# logical_tree.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Logical tree inference for nsis.

Analyzes query and creates a logical tree structure with topic headings.
"""

import json
from typing import Dict, List, Union

from core.inference.base import perform_inference, is_well_formed_json
from core.models_config import MODEL_LOGICAL_TREE, TEMP_LOGICAL_TREE, MODEL_PROVIDER_SORT
from core.read_prompt import read_prompt
from core.schemas import KeywordMappingDecision
from app.utils.dev_print import DevPrint


def _format_tree_compact(tree: Union[Dict, List], depth: int = 0) -> str:
    """Format logical tree with newlines and indentation, without type labels. Used for printing out."""
    indent = "  " * depth
    if isinstance(tree, dict):
        if tree.get("type") == "term":
            return f'{indent}"{tree["value"]}"'
        elif tree.get("type") == "group":
            op = tree.get("operator", "?")
            items = tree.get("items", [])
            if not items:
                return f'{indent}{op}()'
            if len(items) == 1:
                return f'{indent}{op}({_format_tree_compact(items[0], depth + 1)})'
            inner = "\n" + ",\n".join(_format_tree_compact(i, depth + 1) for i in items)
            return f'{indent}{op}({inner}\n{indent})'
    elif isinstance(tree, list):
        return ",\n".join(_format_tree_compact(i, depth) for i in tree)
    return str(tree)


def build_logical_tree(
    positive_concepts: Dict[str, List[str]],
    negative_concepts: Dict[str, List[str]]
) -> Dict:
    """
    Build a deterministic search query tree from positive and negative concepts.

    This function replaces the LLM-based analyze_logical_tree for cases where
    concepts have already been extracted (e.g., from query expansion).

    Args:
        positive_concepts: Dict mapping concept keys to their related terms
        negative_concepts: Dict mapping negated concept keys to their related terms

    Returns:
        dict: Search query tree with root AND group containing OR/NOT groups
    """
    items = []

    # Add positive concept groups
    for concept_key, terms in positive_concepts.items():
        if len(terms) == 1:
            # Single term: no need for OR wrapper
            items.append({"type": "term", "value": terms[0]})
        else:
            # Multiple terms: create OR group
            or_group = {
                "type": "group",
                "operator": "OR",
                "items": [{"type": "term", "value": term} for term in terms]
            }
            items.append(or_group)

    # Add negative concept groups (NOT)
    for concept_key, terms in negative_concepts.items():
        if len(terms) == 1:
            # Single term: no need for OR wrapper
            not_group = {
                "type": "group",
                "operator": "NOT",
                "items": [{"type": "term", "value": terms[0]}]
            }
        else:
            # Multiple terms: wrap in OR subgroup first, then negate
            # This produces "NOT (term1 OR term2)" instead of "term1 NOT term2"
            not_group = {
                "type": "group",
                "operator": "NOT",
                "items": [{
                    "type": "group",
                    "operator": "OR",
                    "items": [{"type": "term", "value": term} for term in terms]
                }]
            }
        items.append(not_group)

    logical_tree = {
        "type": "group",
        "operator": "AND",
        "items": items
    }
    DevPrint.debug(f"Generated logical tree:\n{_format_tree_compact(logical_tree)}")
    return logical_tree


async def add_keyword_to_concepts(
    keyword: str,
    existing_concepts: Dict[str, List[str]]
) -> Dict:
    """
    Analyze a keyword and decide whether to map it to an existing concept
    or create a new concept.

    Args:
        keyword: The keyword to analyze
        existing_concepts: Dict mapping concept keys to their related terms

    Returns:
        dict: {
            "decision": "sub_concept", "super_concept", or "new_concept",
            "concept_key": str,
            "absorbed_concepts": list or None
        }
    """
    # If no existing concepts, always create new
    if not existing_concepts:
        return {
            "decision": "new_concept",
            "concept_key": keyword,
            "absorbed_concepts": None
        }

    # Format existing concepts for prompt
    concepts_lines = []
    for concept_key, related_terms in existing_concepts.items():
        if related_terms:
            terms_str = ", ".join(related_terms)
            concepts_lines.append(f"- {concept_key}: {terms_str}")
        else:
            concepts_lines.append(f"- {concept_key}")
    formatted_concepts = "\n".join(concepts_lines)

    system_prompt = read_prompt("system_prompt_map_keyword")

    result = await perform_inference(
        system_prompt=system_prompt,
        user_prompt=f"## KEYWORD\n`{keyword}`\n\n## EXISTING CONCEPTS\n{formatted_concepts}",
        model=MODEL_LOGICAL_TREE,
        response_format=KeywordMappingDecision,
        temperature=TEMP_LOGICAL_TREE,
        provider_sort=MODEL_PROVIDER_SORT
    )

    if is_well_formed_json(result):
        generated_json = json.loads(result)
        decision = generated_json.get("decision", "new_concept")
        concept_key = generated_json.get("concept_key", keyword)
        absorbed_concepts = generated_json.get("absorbed_concepts")

        if decision == "super_concept":
            DevPrint.debug(f"SUPER_CONCEPT: '{keyword}' absorbing {absorbed_concepts}")
        elif decision == "sub_concept":
            DevPrint.debug(f"SUB_CONCEPT: '{keyword}' -> '{concept_key}'")
        elif decision == "new_concept":
            DevPrint.debug(f"NEW_CONCEPT: '{keyword}'")
        else:
            DevPrint.warning(f"UNKNOWN decision: '{keyword}' -> {decision}")

        return {
            "decision": decision,
            "concept_key": concept_key,
            "absorbed_concepts": absorbed_concepts
        }

    # Fallback: create new concept
    DevPrint.warning(f"FALLBACK: '{keyword}' -> LLM response malformed, creating new concept")
    return {
        "decision": "new_concept",
        "concept_key": keyword,
        "absorbed_concepts": None
    }
