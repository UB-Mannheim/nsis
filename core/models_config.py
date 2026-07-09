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
#MODEL_EMBEDDING = "qwen/qwen3-embedding-8b"
#MODEL_EMBEDDING = "text-embedding-3-small"
#MODEL_EMBEDDING = "qwen3-embedding-8b"
MODEL_EMBEDDING = "jina-embeddings-v2-base-de"  # works in maKI
#MODEL_EMBEDDING = "nvidia/llama-nemotron-embed-vl-1b-v2:free"  # test in openrouter
#MODEL_EMBEDDING = "text-embedding-3-small"  # test via openAI

# Milvus vector dimension must match the active embedding model output size.
EMBEDDING_DIMS = {
    "qwen/qwen3-embedding-8b": 4096,
    "qwen3-embedding-8b": 4096,
    "text-embedding-3-small": 1536,
    "jina-embeddings-v2-base-de": 768,
    "nvidia/llama-nemotron-embed-vl-1b-v2:free": 2048,
}
EMBEDDING_DIM = EMBEDDING_DIMS[MODEL_EMBEDDING]

#MODEL_LOCAL="gemma3:1b"
MODEL_LOCAL="gemma4-26b"  # works in maKI
#MODEL_LOCAL="qwen3.6-36b"

MODEL_QWEN235 = "qwen/qwen3-235b-a22b-2507"
MODEL_QWEN235_THINK = "qwen/qwen3-235b-a22b-thinking-2507"
MODEL_CHATGPT4O = "openai/gpt-4o"
MODEL_CHATGPT4O_MINI = "openai/gpt-4o-mini"
MODEL_CHATGPT5_MINI = "openai/gpt-5-mini"
MODEL_CHATGPT_5_4_MINI = "gpt-5.4-mini"
MODEL_CHATGPT_5_4_NANO = "gpt-5.4-nano"
MODEL_GPT_OSS_120B = "openai/gpt-oss-120b"
MODEL_GPT_OSS_20B = "openai/gpt-oss-20b"
MODEL_GEMINI_3_1_FLASH_LITE = "google/gemini-3.1-flash-lite"
MODEL_GEMINI_2_5_FLASH = "google/gemini-2.5-flash"
MODEL_GEMINI_2_5_PRO = "google/gemini-3-pro"
MODEL_KIMI_K2_5 = "moonshotai/kimi-k2.5"
MODEL_QWEN_3_6 = "qwen/qwen3.6-plus"
MODEL_GEMMA_4_26B = "google/gemma-4-26b-a4b-it:free"

# Default task models
#MODEL_SEARCH_INTENT = MODEL_CHATGPT_5_4_NANO
#MODEL_EXTRACT_FACETTES = MODEL_CHATGPT_5_4_MINI
#MODEL_RERANKER = MODEL_CHATGPT_5_4_NANO
#MODEL_LOGICAL_TREE = MODEL_CHATGPT_5_4_NANO
#MODEL_EXPAND = MODEL_CHATGPT_5_4_NANO
#MODEL_QUERY_QUALITY = MODEL_CHATGPT_5_4_NANO

# Models for maKI
MODEL_SEARCH_INTENT = MODEL_LOCAL
MODEL_EXTRACT_FACETTES = MODEL_LOCAL
MODEL_RERANKER = MODEL_LOCAL
MODEL_LOGICAL_TREE = MODEL_LOCAL
MODEL_EXPAND = MODEL_LOCAL
MODEL_QUERY_QUALITY = MODEL_LOCAL

# Openrouter models
#MODEL_SEARCH_INTENT = MODEL_GEMMA_4_26B
#MODEL_EXTRACT_FACETTES = MODEL_GEMMA_4_26B
#MODEL_RERANKER = MODEL_GEMMA_4_26B
#MODEL_LOGICAL_TREE = MODEL_GEMMA_4_26B
#MODEL_EXPAND = MODEL_GEMMA_4_26B
#MODEL_QUERY_QUALITY = MODEL_GEMMA_4_26B


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
