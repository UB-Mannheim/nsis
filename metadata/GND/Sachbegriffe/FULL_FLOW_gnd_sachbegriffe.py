#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# FULL_FLOW_gnd_sachbegriffe.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Flow script for GND Sachbegriffe processing.

This script:
1. Moves to metadata/GND/ directory
2. Downloads and unpacks GND authority data
3. Downloads GND subject categories
4. Runs conversion scripts
"""

import os
import sys
import urllib.request
import gzip
import shutil
import subprocess
from pathlib import Path


def download_and_extract_gz(url: str, output_filename: str) -> None:
    """Download a gzipped file and extract it."""
    gz_filename = output_filename + ".gz"

    if os.path.exists(output_filename):
        print(f"  File {output_filename} already exists, skipping download.")
        return

    print(f"  Downloading {url} ...")
    urllib.request.urlretrieve(url, gz_filename)
    print(f"  Downloaded to {gz_filename}")

    print(f"  Extracting to {output_filename} ...")
    with gzip.open(gz_filename, 'rb') as f_in:
        with open(output_filename, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print(f"  Extracted to {output_filename}")

    # Remove the .gz file
    os.remove(gz_filename)
    print(f"  Removed {gz_filename}")


def download_file(url: str, output_filename: str) -> None:
    """Download a file."""
    if os.path.exists(output_filename):
        print(f"  File {output_filename} already exists, skipping download.")
        return

    print(f"  Downloading {url} ...")
    urllib.request.urlretrieve(url, output_filename)
    print(f"  Downloaded to {output_filename}")


def run_script(script_path: str, description: str) -> None:
    """Run a bash script and display its output."""
    print(f"  Running {description} ...")
    result = subprocess.run(["bash", script_path], capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"{description} failed with exit code {result.returncode}")
    print(f"  {description} completed")


def run_python_script(script_path: str, description: str) -> None:
    """Run a Python script using uv and display its output."""
    print(f"  Running {description} ...")
    result = subprocess.run(["uv", "run", "python", script_path], capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"{description} failed with exit code {result.returncode}")
    print(f"  {description} completed")


def prompt_continue(current_step: int, current_description: str, next_step: int, next_description: str) -> bool:
    """Prompt user to continue to next step.

    Returns:
        True if user wants to skip the next step, False otherwise.
    """
    response = input(f"Step {current_step} ({current_description}) completed.\n\nPress Enter to continue to step {next_step} ({next_description}), or 's' to skip: ")
    return response.strip().lower() == 's'


def main():
    script_dir = Path(__file__).parent.resolve()
    skip_next = False

    print("=" * 60)
    print("GND Sachbegriffe Flow Script")
    print("=" * 60)

    # Step 0: Move to metadata/GND/ directory
    print("\n[Step 0] Moving to metadata/GND/ directory...")
    gnd_dir = script_dir
    os.chdir(gnd_dir)
    print(f"  Current directory: {os.getcwd()}")

    # Step 1: Download and extract GND Sachbegriffe data
    skip_next = prompt_continue(0, "Change directory", 1, "Download GND Sachbegriffe")
    if skip_next:
        print("\n[Step 1] Skipping Download GND Sachbegriffe...")
    else:
        print("\n[Step 1] Downloading GND Sachbegriffe data...")
        download_and_extract_gz(
            "https://data.dnb.de/GND/authorities-gnd-sachbegriff_dnbmarc.mrc.xml.gz",
            "authorities-gnd-sachbegriffe_dnbmarc.mrc.xml"
        )
    skip_next = prompt_continue(1, "Download GND Sachbegriffe", 2, "Download GND Sachgruppen")

    # Step 2: Download GND Sachgruppen TTL
    if skip_next:
        print("\n[Step 2] Skipping Download GND Sachgruppen...")
    else:
        print("\n[Step 2] Downloading GND Sachgruppen TTL...")
        download_file(
            "https://d-nb.info/standards/vocab/gnd/gnd-sc.ttl",
            "gnd-sachgruppen.ttl"
        )
    skip_next = prompt_continue(2, "Download GND Sachgruppen", 3, "convert_gnd_sachbegriffe_to_csv.sh")

    # Step 3: Run convert_gnd_sachbegriffe_to_csv.sh
    if skip_next:
        print("\n[Step 3] Skipping convert_gnd_sachbegriffe_to_csv.sh...")
    else:
        print("\n[Step 3] Running convert_gnd_sachbegriffe_to_csv.sh...")
        run_script("convert_gnd_sachbegriffe_to_csv.sh", "convert_gnd_sachbegriffe_to_csv.sh")
    skip_next = prompt_continue(3, "convert_gnd_sachbegriffe_to_csv.sh", 4, "convert_gnd_sachgruppen_to_csv.py")

    # Step 4: Run convert_gnd_sc_to_csv.py
    if skip_next:
        print("\n[Step 4] Skipping convert_gnd_sachgruppen_to_csv.py...")
    else:
        print("\n[Step 4] Running convert_gnd_sachgruppen_to_csv.py...")
        run_python_script("convert_gnd_sachgruppen_to_csv.py", "convert_gnd_sachgruppen_to_csv.py")
    skip_next = prompt_continue(4, "convert_gnd_sachgruppen_to_csv.py", 5, "merge_gnd_saz.py")

    # Step 5: Run merge_gnd_saz.py
    if skip_next:
        print("\n[Step 5] Skipping merge_gnd_saz.py...")
    else:
        print("\n[Step 5] Running merge_gnd_saz.py...")
        run_python_script("merge_gnd_saz.py", "merge_gnd_saz.py")
    prompt_continue(5, "merge_gnd_saz.py", 6, "Done")

    print("\n" + "=" * 60)
    print("All steps completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
