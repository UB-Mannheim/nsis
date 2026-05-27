#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# merge_gnd_saz.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Merge GND Sachbegriffe with Classification Labels

Enriches gnd-sachbegriffe.csv with German/English labels from gnd-sc.csv
by joining on subject codes.
"""

import csv
import unicodedata
from pathlib import Path


def normalize(text: str) -> str:
    """Normalize text to NFC form."""
    if text is None:
        return ""
    return unicodedata.normalize("NFC", text)


def main():
    base_dir = Path(__file__).parent
    gnd_sc_path = base_dir / "gnd-sachgruppen.csv"
    gnd_sachbegriffe_path = base_dir / "gnd-sachbegriffe.csv"
    output_path = base_dir / "gnd-sachbegriffe-systematik.csv"

    # Step 1: Read gnd-sc.csv into a lookup dict
    lookup: dict[str, dict[str, str]] = {}
    with open(gnd_sc_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            notation = normalize(row["notation"])
            lookup[notation] = {
                "en": normalize(row["prefLabel@en"]),
                "de": normalize(row["prefLabel@de"]),
            }

    print(f"Loaded {len(lookup)} classification codes from gnd-sc.csv")

    # Step 2 & 3: Read gnd-sachbegriffe.csv and process each row
    output_columns = [
        "gnd_id",
        "subject_code",
        "subject_label_en",
        "subject_label_de",
        "heading",
        "alt_term",
        "heading_and_alt_term",
        "definition",
        "description",
    ]

    processed = 0
    skipped = 0

    with open(gnd_sachbegriffe_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8", newline="") as outfile:

        reader = csv.DictReader(infile, delimiter=";")
        writer = csv.DictWriter(outfile, fieldnames=output_columns, delimiter=";")
        writer.writeheader()

        for row in reader:
            subject = normalize(row.get("subject", ""))

            # Skip rows where subject is empty
            if not subject:
                skipped += 1
                continue

            # Split subject by comma and take only the first code
            codes = [code.strip() for code in subject.split(",")]
            first_code = codes[0] if codes else ""

            if not first_code:
                skipped += 1
                continue

            # Lookup labels for the first code
            labels = lookup.get(first_code, {"en": "", "de": ""})

            # Take only the first GND ID (strip everything after comma if present)
            gnd_raw = row.get("gnd", "").split(",")[0].strip()
            gnd = normalize(gnd_raw)

            heading = normalize(row.get("heading", ""))
            alt_term = normalize(row.get("alt_term", ""))
            definition = normalize(row.get("definition", ""))
            subject_label_en = labels["en"]
            subject_label_de = labels["de"]

            # Compute heading_and_alt_term
            if alt_term:
                heading_and_alt_term = f"{heading}, {alt_term}"
            else:
                heading_and_alt_term = heading

            # Write description
            parts = [f"{heading}. {heading}. {heading}.", f"Begriff: {heading}"]
            if alt_term:
                parts.append(f"Synonyme: {alt_term}")
            if subject_label_de:
                parts.append(f"Kontext: {subject_label_de}")
            description = "\n".join(parts)

            writer.writerow({
                "gnd_id": gnd,
                "subject_code": first_code,
                "subject_label_en": subject_label_en,
                "subject_label_de": subject_label_de,
                "heading": heading,
                "alt_term": alt_term,
                "heading_and_alt_term": heading_and_alt_term,
                "definition": definition,
                "description": description,
            })
            processed += 1

    print(f"Processed {processed} rows, skipped {skipped} rows")
    print(f"Output written to {output_path}")


if __name__ == "__main__":
    main()
