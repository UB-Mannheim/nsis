# -*- coding: utf-8 -*-
# =============================================================================
# base.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Base inference functions for nsis.

Provides the core perform_inference function used by all inference modules.
"""

import asyncio
import json
import time
from typing import Optional, Any

from openai import RateLimitError

from core.clients import inference_client
from core.usage_stats_logging import usage_stats_logger
from app.utils.dev_print import DevPrint


async def perform_inference(
    system_prompt: str,
    user_prompt: str,
    model: str,
    response_format: Optional[Any] = None,
    temperature: float = 0.2,
    max_retries: int = 3,
    provider_sort: Optional[str] = None
) -> str:
    """
    Core async function for LLM inference with structured output parsing.

    Args:
        system_prompt: System prompt for the LLM
        user_prompt: User prompt/content
        model: Model identifier
        response_format: Optional Pydantic model for structured output
        temperature: Sampling temperature (default 0.2)
        max_retries: Maximum number of retry attempts (default 3)
        provider_sort: Optional sort strategy for provider routing ("price", "throughput", "latency")

    Returns:
        str: LLM response content, or empty string on failure
    """
    time_start = time.time_ns()

    for attempt in range(max_retries):
        try:
            # Build extra_body for provider routing if provided
            extra_body = None
            if provider_sort is not None:
                extra_body = {"provider": {"sort": provider_sort}}

            if response_format:
                chat_completion = await inference_client.client.chat.completions.parse(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=model,
                    response_format=response_format,
                    temperature=temperature,
                    reasoning_effort="minimal",
                    extra_body=extra_body
                )
            else:
                chat_completion = await inference_client.client.chat.completions.parse(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=model,
                    temperature=temperature,
                    reasoning_effort="minimal",
                    extra_body=extra_body
                )

            time_end = time.time_ns()
            time_total = (time_end - time_start) // 1000000

            if chat_completion.usage is not None:

                completion_tokens = getattr(chat_completion.usage, 'completion_tokens', 0)
                prompt_tokens = getattr(chat_completion.usage, 'prompt_tokens', 0)
                total_tokens = getattr(chat_completion.usage, 'total_tokens', 0)
                cost = getattr(chat_completion.usage, 'cost', 0.0)

                DevPrint.timing(f"{time_total}ms | {model} | Complete: {completion_tokens} tk | Prompt: {prompt_tokens} tk | Total: {total_tokens} tk | Cost: ${round(cost, 5)}")

                # Log performance metrics to usage stats
                usage_stats_logger.log_performance(
                    operation_type="llm_inference",
                    duration_ms=time_total,
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    cost_usd=cost
                )

            if chat_completion.choices:
                message = chat_completion.choices[0].message
                # Handle structured output (Pydantic models) - use .parsed to get the model instance
                if response_format and hasattr(message, 'parsed') and message.parsed is not None:
                    parsed = message.parsed
                    # Return proper JSON for all structured output schemas
                    if hasattr(parsed, 'model_dump_json'):
                        return parsed.model_dump_json(by_alias=True)
                    else:
                        return json.dumps(parsed)
                elif message.content is not None:
                    return message.content
                else:
                    DevPrint.error("Failed to get response from inference server: message content is None.")
                    return ""
            else:
                DevPrint.error("Failed to get response from inference server.")
                return ""

        except (RateLimitError, Exception) as e:
            if attempt < max_retries - 1:

                wait_time = (attempt + 1) * 2  # Exponential backoff: 2, 4, 6 seconds

                DevPrint.warning(f"Retry {attempt + 1}/{max_retries}: {e}")
                DevPrint.info(f"Waiting {wait_time}s before retry...")

                await asyncio.sleep(wait_time)
            else:
                DevPrint.error(f"Failed after {max_retries} attempts: {e}")

    return ""


def is_well_formed_json(json_string: str) -> bool:
    """Check if a string is valid JSON."""
    try:
        json.loads(json_string)
        return True
    except json.JSONDecodeError:
        return False


def create_numbered_list(items) -> str:
    """Create a numbered list string from items (0-indexed)."""
    return '\n'.join(f"{i}. {item}" for i, item in enumerate(items, start=0))
