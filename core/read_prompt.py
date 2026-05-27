# -*- coding: utf-8 -*-
# =============================================================================
# read_prompt.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Prompt loading utilities for nsis inference.

Loads system prompts from the core/prompts directory.
"""

from pathlib import Path

from app.utils.dev_print import DevPrint

# Base directory for prompts
PROMPTS_DIR = Path(__file__).parent / "prompts"


def read_prompt(prompt_name: str) -> str:
    """
    Read a system prompt file by name.

    Args:
        prompt_name: Name of the prompt file (without .md extension)
                    e.g., "system_prompt_search_intent"

    Returns:
        The prompt content as a string, or empty string if file not found.
    """
    prompt_path = PROMPTS_DIR / f"{prompt_name}.md"
    try:
        with open(prompt_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        DevPrint.warning(f"Prompt file not found: {prompt_path}")
        return ""
