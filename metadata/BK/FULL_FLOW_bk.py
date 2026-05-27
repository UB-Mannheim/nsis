#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# FULL_FLOW_bk.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Flow script for BK (Basisklassifikation) processing.

This script:
1. Moves to metadata/BK/ directory
2. Downloads BK JSON-LD data
3. Parses JSON-LD and extracts fields (notation, label, scopeNote)
4. Generates llmDescription via LLM calls
5. Exports to CSV
"""

import asyncio
import json
import os
import re
import sys
import urllib.request
import pandas as pd

from pathlib import Path
from pydantic import BaseModel

# Add project root to path for imports (must be before other project imports)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.inference.base import perform_inference  # noqa: E402
from core.models_config import MODEL_GEMINI_3_1_FLASH_LITE, MODEL_PROVIDER_SORT  # noqa: E402

# Pydantic response schema for LLM output
class BKDescriptionResponse(BaseModel):
    llmDescription: str

SYSTEM_PROMPT = """Generate short descriptions for library classification entries. Rules: repeat the classification name, include examples of subjects, plain text only. Output valid JSON with field "llmDescription"."""


def download_file(url: str, output_filename: str) -> None:
    """Download a file, skipping if it already exists."""
    if os.path.exists(output_filename):
        print(f"  File {output_filename} already exists, skipping download.")
        return

    print(f"  Downloading {url} ...")
    urllib.request.urlretrieve(url, output_filename)
    print(f"  Downloaded to {output_filename}")


def check_format_bk_regex(s: str) -> bool:
    """
    Validate if a string matches the BK notation format (xx.xx).

    Args:
        s: String to validate

    Returns:
        True if string matches format, False otherwise
    """
    pattern = r'^\d{2}\.\d{2}$'
    return bool(re.match(pattern, s))


def parse_jsonld_to_records(jsonld_path: str) -> list[dict]:
    """
    Parse JSON-LD file and extract all BK records.

    Args:
        jsonld_path: Path to the JSON-LD file

    Returns:
        List of dictionaries with notation, label, and scopeNote
    """
    import json

    with open(jsonld_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    records = []

    for item in data:
        record = {}

        # Process notation field (format: xx.xx)
        notation = item.get('notation', [])
        if notation is not None:
            notation_str = notation[0] if isinstance(notation, list) else str(notation)
            # Skip entries that don't match BK Unterklassen format
            if not check_format_bk_regex(notation_str):
                continue
            record['notation'] = notation_str
        else:
            continue

        # Process preferred label (German)
        preflabel = item.get('prefLabel', {})
        if preflabel is not None:
            if isinstance(preflabel, dict):
                record['label'] = preflabel.get('de', '')
            else:
                record['label'] = str(preflabel)

        # Process alternative labels (extend label)
        altlabel = item.get('altLabel', {})
        if altlabel is not None:
            if altlabel:
                record['label'] += ', ' + ', '.join(altlabel["de"])
            else:
                record['label'] += ""

        # Process scope notes (German)
        scopenote = item.get('scopeNote', {})
        if scopenote is not None:
            if scopenote:
                record['scopeNote'] = ', '.join(scopenote["de"])
            else:
                record['scopeNote'] = ""

        records.append(record)

    return records


async def generate_llm_description_async(
    label: str,
    scopeNote: str,
    notation: str
) -> str:
    """
    Generate LLM description for a BK classification entry.

    Args:
        label: The classification label
        scopeNote: The scope note

    Returns:
        Generated description or empty string on failure
    """
    user_prompt = f"""Generate a description for library classification "{label}". Include examples of subjects. Max 2 sentences."""

    response = await perform_inference(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=MODEL_GEMINI_3_1_FLASH_LITE,
        response_format=BKDescriptionResponse,
        temperature=0.2,
        provider_sort=MODEL_PROVIDER_SORT
    )

    # Parse JSON response and extract llmDescription
    try:
        parsed = json.loads(response)
        if isinstance(parsed, dict) and 'llmDescription' in parsed:
            return parsed['llmDescription']
    except (json.JSONDecodeError, TypeError):
        pass
    return ""


def generate_llm_description(
    label: str,
    scopeNote: str,
    notation: str
) -> str:
    """
    Synchronous wrapper for LLM description generation.

    Args:
        label: The classification label
        scopeNote: The scope note
        notation: The notation code

    Returns:
        Generated description or empty string on failure
    """
    return asyncio.run(generate_llm_description_async(label, scopeNote, notation))


def save_records_to_json(records: list, output_path: str) -> None:
    """Save records to JSON file for later use."""
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"  Saved {len(records)} records to {output_path}")


def load_records_from_json(json_path: str) -> list[dict]:
    """Load records from JSON file."""
    import json
    with open(json_path, 'r', encoding='utf-8') as f:
        records = json.load(f)
    print(f"  Loaded {len(records)} records from {json_path}")
    return records


def export_to_csv(records: list, output_path: str) -> None:
    """
    Export records to CSV file.

    Args:
        records: List of record dictionaries
        output_path: Path for output CSV file
    """
    df = pd.DataFrame(records)
    # Use semicolon as delimiter and UTF-8-sig for Excel compatibility
    df.to_csv(output_path, sep=';', index=False, encoding='utf-8-sig')
    print(f"  Exported {len(records)} records to {output_path}")


def prompt_continue(
    current_step: int,
    current_description: str,
    next_step: int,
    next_description: str
) -> bool:
    """
    Prompt user to continue to next step.

    Returns:
        True if user wants to skip the next step, False otherwise.
    """
    response = input(
        f"Step {current_step} ({current_description}) completed.\n\n"
        f"Press Enter to continue to step {next_step} ({next_description}), "
        f"or 's' to skip: "
    )
    return response.strip().lower() == 's'


async def process_record_with_semaphore(
    record: dict,
    semaphore: asyncio.Semaphore,
    progress: list[int],
    total: int,
    lock: asyncio.Lock
) -> dict:
    """
    Process a single record with semaphore-controlled concurrency.

    Args:
        record: Record dictionary
        semaphore: Semaphore to limit concurrent requests
        progress: Shared progress counter [completed]
        total: Total number of records
        lock: Lock for progress updates

    Returns:
        Record with llmDescription field added
    """
    async with semaphore:
        llm_description = await generate_llm_description_async(
            label=record['label'],
            scopeNote=record['scopeNote'],
            notation=record['notation']
        )
        record['llmDescription'] = llm_description

        async with lock:
            progress[0] += 1
            print(f"  Processed {progress[0]}/{total}: {record['notation']} - {record['label'][:50]}...")

        return record


async def process_records_async(
    records: list[dict],
    max_concurrent: int = 10
) -> list[dict]:
    """
    Process records and generate LLM descriptions in parallel.

    Args:
        records: List of parsed records
        max_concurrent: Maximum number of concurrent LLM calls (default: 10)

    Returns:
        Records with llmDescription field added
    """
    total = len(records)
    semaphore = asyncio.Semaphore(max_concurrent)
    progress = [0]  # Use list for mutable counter
    lock = asyncio.Lock()

    tasks = [
        process_record_with_semaphore(record, semaphore, progress, total, lock)
        for record in records
    ]

    print(f"  Processing {total} records with up to {max_concurrent} concurrent LLM calls...")
    results = await asyncio.gather(*tasks)

    return results


def main():
    script_dir = Path(__file__).parent.resolve()
    skip_next = False

    print("=" * 60)
    print("BK (Basisklassifikation) Flow Script")
    print("=" * 60)

    # Step 0: Move to metadata/BK/ directory
    print("\n[Step 0] Moving to metadata/BK/ directory...")
    bk_dir = script_dir
    os.chdir(bk_dir)
    print(f"  Current directory: {os.getcwd()}")

    jsonld_file = "bk__default.jskos.jsonld"
    parsed_json_file = "bk_parsed_records.json"
    csv_file = "bk.csv"
    records: list[dict] = []

    # Step 1: Download BK JSON-LD
    skip_next = prompt_continue(
        0, "Change directory",
        1, "Download BK JSON-LD"
    )
    if skip_next:
        print("\n[Step 1] Skipping Download BK JSON-LD...")
    else:
        print("\n[Step 1] Downloading BK JSON-LD data...")
        download_file(
            "https://api.dante.gbv.de/export/download/bk/default/bk__default.jskos.jsonld",
            jsonld_file
        )
    skip_next = prompt_continue(
        1, "Download BK JSON-LD",
        2, "Parse JSON-LD"
    )

    # Step 2: Parse JSON-LD
    if skip_next:
        print("\n[Step 2] Skipping Parse JSON-LD...")
    else:
        print("\n[Step 2] Parsing JSON-LD file...")
        records = parse_jsonld_to_records(jsonld_file)
        print(f"  Parsed {len(records)} valid records")
        save_records_to_json(records, parsed_json_file)
    skip_next = prompt_continue(
        2, "Parse JSON-LD",
        3, "Generate LLM descriptions"
    )

    # Step 3: Generate LLM descriptions
    if skip_next:
        print("\n[Step 3] Skipping Generate LLM descriptions...")
    else:
        print("\n[Step 3] Loading parsed records and generating LLM descriptions...")
        if os.path.exists(parsed_json_file):
            records = load_records_from_json(parsed_json_file)
        else:
            print("  Error: Parsed records file not found. Run Step 2 first.")
            return
        print("  This may take a while depending on the number of records...")
        records = asyncio.run(process_records_async(records))
        print(f"  Generated descriptions for {len(records)} records")
    skip_next = prompt_continue(
        3, "Generate LLM descriptions",
        4, "Export to CSV"
    )

    # Step 4: Export to CSV
    if skip_next:
        print("\n[Step 4] Skipping Export to CSV...")
    else:
        print("\n[Step 4] Exporting to CSV...")
        export_to_csv(records, csv_file)

    prompt_continue(4, "Export to CSV", 5, "Done")

    print("\n" + "=" * 60)
    print("All steps completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()