# -*- coding: utf-8 -*-
# =============================================================================
# models_config.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Model configuration constants for nsis inference.

This module is the single source of truth for all model names and temperatures and routing decisions.
Import model constants from here instead of duplicating them.
"""

# Short-list of available models (see https://openrouter.ai/models)
MODEL_EMBEDDING = "qwen/qwen3-embedding-8b"

MODEL_QWEN235 = "qwen/qwen3-235b-a22b-2507"
MODEL_QWEN235_THINK = "qwen/qwen3-235b-a22b-thinking-2507"
MODEL_CHATGPT4O = "openai/gpt-4o"
MODEL_CHATGPT4O_MINI = "openai/gpt-4o-mini"
MODEL_CHATGPT5_MINI = "openai/gpt-5-mini"
MODEL_CHATGPT_5_4_MINI = "openai/gpt-5.4-mini"
MODEL_CHATGPT_5_4_NANO = "openai/gpt-5.4-nano"
MODEL_GPT_OSS_120B = "openai/gpt-oss-120b"
MODEL_GPT_OSS_20B = "openai/gpt-oss-20b"
MODEL_GEMINI_3_1_FLASH_LITE = "google/gemini-3.1-flash-lite"
MODEL_GEMINI_2_5_FLASH = "google/gemini-2.5-flash"
MODEL_GEMINI_2_5_PRO = "google/gemini-3-pro"
MODEL_KIMI_K2_5 = "moonshotai/kimi-k2.5"
MODEL_QWEN_3_6 = "qwen/qwen3.6-plus"

# Default task models
MODEL_SEARCH_INTENT = MODEL_GEMINI_3_1_FLASH_LITE
MODEL_EXTRACT_FACETTES = MODEL_CHATGPT_5_4_MINI
MODEL_RERANKER = MODEL_GEMINI_3_1_FLASH_LITE
MODEL_LOGICAL_TREE = MODEL_GEMINI_3_1_FLASH_LITE
MODEL_EXPAND = MODEL_GEMINI_3_1_FLASH_LITE
MODEL_QUERY_QUALITY = MODEL_GEMINI_3_1_FLASH_LITE

# Settings for OpenRouter provider routing
# Source: https://openrouter.ai/docs/guides/routing/provider-selection
#
# "price": prioritize lowest price
# "throughput": prioritize highest throughput
# "latency": prioritize lowest latency

# OpenRouter provider routing for embeddings
EMBEDDING_PROVIDER_SORT = "price"

# OpenRouter provider routing for general LLM inference
MODEL_PROVIDER_SORT = "latency"

# Task temperatures
TEMP_SEARCH_INTENT = 0.2
TEMP_EXTRACT_FACETTES = 0
TEMP_RERANKER = 0.2
TEMP_LOGICAL_TREE = 0.2
TEMP_EXPAND = 0.1
TEMP_QUERY_QUALITY = 0
