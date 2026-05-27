#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# initialize_databases.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

# Standalone script to initialize/create all Milvus databases.
# Run this script when the server is OFF to create missing databases or rebuild indexes.
# Usage: uv run python scripts/initialize_databases.py [--bk] [--gnd-saz-head] [--gnd-saz-desc] [--gnd-geo] [--all] [--rebuild-index]

import asyncio
import sys
import os
import argparse
from pathlib import Path

# Add project root to path to enable imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings  # noqa: E402
import core.milvus_search as milvus_search  # noqa: E402

# Define all available databases
AVAILABLE_DATABASES = {
    "bk": {
        "name": "BK (Basisklassifikation)",
        "data_type": "bk",
        "db_path": settings.milvus_bk_db_path,
        "csv_path": settings.milvus_bk_csv_path,
        "collection_name": "bk_alle_klassen",
    },
    "gnd-saz-head": {
        "name": "GND Sachbegriffe (head)",
        "data_type": "gnd_saz",
        "db_path": settings.milvus_gnd_saz_head_db_path,
        "csv_path": settings.milvus_gnd_saz_head_csv_path,
        "collection_name": "gnd_sachbegriffe_head",
    },
    "gnd-saz-desc": {
        "name": "GND Sachbegriffe (desc)",
        "data_type": "gnd_saz",
        "db_path": settings.milvus_gnd_saz_desc_db_path,
        "csv_path": settings.milvus_gnd_saz_desc_csv_path,
        "collection_name": "gnd_sachbegriffe_desc",
    },
    "gnd-geo": {
        "name": "GND Geografika",
        "data_type": "gnd_geo",
        "db_path": settings.milvus_gnd_geo_db_path,
        "csv_path": settings.milvus_gnd_geo_csv_path,
        "collection_name": "gnd_geografika",
    },
}


def initialize_database(db_key: str):
    """Initialize a database"""
    db_config = AVAILABLE_DATABASES[db_key]
    device = settings.milvus_device

    print(f"=== Initializing {db_config['name']} ===")
    print(f"    DB path: {db_config['db_path']}")
    print(f"    CSV path: {db_config['csv_path']}")
    print(f"    Collection: {db_config['collection_name']}")

    # Check if database already exists
    if os.path.exists(db_config["db_path"]):
        print("    Database exists, loading...")
        # Use load_db for existing databases
        db = milvus_search.Milvus_Search(db_config["data_type"], device)
        db.load_db(db_config["db_path"], db_config["collection_name"])
    else:
        print("    Database does not exist, creating from CSV...")
        # Create Milvus_Search instance and initialize database
        db = milvus_search.Milvus_Search(db_config["data_type"], device)
        # Run async init_db in its own event loop
        asyncio.run(db.init_db(db_config["db_path"], db_config["csv_path"], db_config["collection_name"]))

    print("    Done.")
    print()


async def rebuild_index_database(db_key: str):
    """Rebuild index on an existing database without reloading data."""
    db_config = AVAILABLE_DATABASES[db_key]
    device = settings.milvus_device

    print(f"=== Rebuilding index for {db_config['name']} ===")
    print(f"    DB path: {db_config['db_path']}")
    print(f"    Collection: {db_config['collection_name']}")

    if not os.path.exists(db_config["db_path"]):
        print("    ERROR: Database does not exist. Run without --rebuild-index first.")
        return

    # Create Milvus_Search instance (don't reinitialize, just rebuild index)
    db = milvus_search.Milvus_Search(db_config["data_type"], device)
    db.db_path = db_config["db_path"]
    db.collection_name = db_config["collection_name"]
    db.rebuild_index()

    print("    Done.")
    print()


async def main():
    parser = argparse.ArgumentParser(
        description="Initialize Milvus databases. Run when server is OFF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python scripts/initialize_databases.py --all                           # Initialize all databases
  uv run python scripts/initialize_databases.py --bk                            # Initialize only BK database
  uv run python scripts/initialize_databases.py --gnd-saz-head --gnd-saz-desc   # Initialize GND-SAZ databases
  uv run python scripts/initialize_databases.py --gnd-geo                       # Initialize GND database
  uv run python scripts/initialize_databases.py --all --rebuild-index           # Rebuild indexes on existing databases
        """
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Initialize all databases (default if no specific DB is selected)"
    )
    parser.add_argument(
        "--bk",
        action="store_true",
        help="Initialize BK (Basisklassifikation) database"
    )
    parser.add_argument(
        "--gnd-saz-head",
        action="store_true",
        help="Initialize GND Sachbegriffe (head) database"
    )
    parser.add_argument(
        "--gnd-saz-desc",
        action="store_true",
        help="Initialize GND Sachbegriffe (desc) database"
    )
    parser.add_argument(
        "--gnd-geo",
        action="store_true",
        help="Initialize GND Geografika database"
    )
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Rebuild index on existing databases (use after --all, --bk, etc.)"
    )

    args = parser.parse_args()

    print(f"Project root: {PROJECT_ROOT}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Milvus device: {settings.milvus_device}")
    print()

    # Determine which databases to initialize
    if args.bk or args.gnd_saz_head or args.gnd_saz_desc or args.gnd_geo:
        # Specific databases selected
        selected = []
        if args.bk:
            selected.append("bk")
        if args.gnd_saz_head:
            selected.append("gnd-saz-head")
        if args.gnd_saz_desc:
            selected.append("gnd-saz-desc")
        if args.gnd_geo:
            selected.append("gnd-geo")
    elif args.all or not any([args.bk, args.gnd_saz_head, args.gnd_saz_desc]):
        # --all flag or no flags provided, initialize all
        selected = list(AVAILABLE_DATABASES.keys())
    else:
        selected = []

    if not selected:
        print("No databases selected. Use --help for usage information.")
        return

    print(f"Processing {len(selected)} database(s): {selected}")
    if args.rebuild_index:
        print("Mode: REBUILD INDEX ONLY (data will not be reloaded)")
    else:
        print("Mode: INITIALIZE (data will be loaded/reloaded from CSV)")
    print()

    # Process databases sequentially in thread pool
    if args.rebuild_index:
        for db_key in selected:
            await asyncio.to_thread(rebuild_index_database, db_key)
    else:
        for db_key in selected:
            await asyncio.to_thread(initialize_database, db_key)

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
