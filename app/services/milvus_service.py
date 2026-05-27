# -*- coding: utf-8 -*-
# =============================================================================
# milvus_service.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Milvus service for nsis FastAPI application.
Wraps Milvus vector database operations.
"""

import asyncio
import time
from typing import List, Optional
import core.milvus_search as milvus_search
from core.schemas.types import MilvusHit
from app.utils.dev_print import DevPrint


def _run_async_search(db, query, top_k):
    """Helper to run async Milvus search in a thread pool executor.

    Used for warmup queriesm where we need to call async search() from
    a thread executor (run_in_executor) without blocking the event loop.
    """
    return asyncio.run(db.search(query, top_k))


class MilvusService:
    """Service for Milvus vector database operations."""

    def __init__(
        self,
        device: str,
        bk_db_path: str,
        bk_csv_path: str,
        gnd_saz_head_db_path: str,
        gnd_saz_head_csv_path: str,
        gnd_saz_desc_db_path: str,
        gnd_saz_desc_csv_path: str,
        gnd_geo_db_path: str,
        gnd_geo_csv_path: str,
    ):
        """
        Initialize the Milvus service.

        Args:
            device: Computation device (cpu or cuda:0)
            bk_db_path: Path to BK database
            bk_csv_path: Path to BK CSV file
            gnd_saz_head_db_path: Path to GND SAZ head database
            gnd_saz_head_csv_path: Path to GND SAZ head CSV file
            gnd_saz_desc_db_path: Path to GND SAZ description database
            gnd_saz_desc_csv_path: Path to GND SAZ description CSV file
            gnd_geo_db_path: Path to GND Geografika database
            gnd_geo_csv_path: Path to GND Geografika CSV file
        """
        self.device = device

        self.bk_db_path = bk_db_path
        self.bk_csv_path = bk_csv_path

        self.gnd_saz_head_db_path = gnd_saz_head_db_path
        self.gnd_saz_head_csv_path = gnd_saz_head_csv_path

        self.gnd_saz_desc_db_path = gnd_saz_desc_db_path
        self.gnd_saz_desc_csv_path = gnd_saz_desc_csv_path

        self.gnd_geo_db_path = gnd_geo_db_path
        self.gnd_geo_csv_path = gnd_geo_csv_path

        # Milvus database instances
        self.db_bk: Optional[milvus_search.Milvus_Search] = None
        self.db_gnd_head: Optional[milvus_search.Milvus_Search] = None
        self.db_gnd_desc: Optional[milvus_search.Milvus_Search] = None
        self.db_gnd_geo: Optional[milvus_search.Milvus_Search] = None

    async def initialize(self):
        """Initialize Milvus databases in parallel for faster startup."""
        DevPrint.info("Initializing Milvus databases...")

        # Create Milvus_Search instances
        self.db_bk = milvus_search.Milvus_Search("bk", self.device)
        self.db_gnd_head = milvus_search.Milvus_Search("gnd_saz", self.device)
        self.db_gnd_desc = milvus_search.Milvus_Search("gnd_saz", self.device)
        self.db_gnd_geo = milvus_search.Milvus_Search("gnd_geo", self.device)

        # Load databases in batches of 2 to avoid OOM
        # Database creation is done via ./scripts/initialize_databases.py
        start_time = time.time()

        # Batch 1: GND-SAZ-HEAD and GND-SAZ-DESC
        DevPrint.info("    Loading batch 1: GND-SAZ-HEAD and GND-SAZ-DESC...")
        await asyncio.gather(
            asyncio.to_thread(self.db_gnd_head.load_db, self.gnd_saz_head_db_path, "gnd_sachbegriffe_head"),
            asyncio.to_thread(self.db_gnd_desc.load_db, self.gnd_saz_desc_db_path, "gnd_sachbegriffe_desc"),
        )

        # Batch 2: BK and GND-GEO
        DevPrint.info("    Loading batch 2: BK and GND-GEO...")
        await asyncio.gather(
            asyncio.to_thread(self.db_bk.load_db, self.bk_db_path, "bk_alle_klassen"),
            asyncio.to_thread(self.db_gnd_geo.load_db, self.gnd_geo_db_path, "gnd_geografika"),
        )

        init_elapsed = time.time() - start_time
        DevPrint.success(f"    Databases loaded in {init_elapsed:.2f}s")

        # Warm up databases in parallel - create threads to run async search functions
        DevPrint.info("Warming up databases...")
        warmup_start = time.time()

        # Run each async search in a separate thread to avoid blocking the event loop
        # We use run_in_executor to properly run async code in thread pool
        loop = asyncio.get_running_loop()
        warmup_tasks = [
            loop.run_in_executor(None, _run_async_search, self.db_bk, "__warmup__", 1),
            loop.run_in_executor(None, _run_async_search, self.db_gnd_head, "__warmup__", 1),
            loop.run_in_executor(None, _run_async_search, self.db_gnd_desc, "__warmup__", 1),
            loop.run_in_executor(None, _run_async_search, self.db_gnd_geo, "__warmup__", 1),
        ]
        await asyncio.gather(*warmup_tasks)
        warmup_elapsed = time.time() - warmup_start

        DevPrint.success(f"Milvus databases initialized (init: {init_elapsed:.2f}s, warmup: {warmup_elapsed:.2f}s).")

    async def shutdown(self):
        """Shutdown Milvus databases."""
        # Close database connections if needed
        self.db_bk = None
        self.db_gnd_head = None
        self.db_gnd_desc = None
        self.db_gnd_geo = None

    async def search_bk(self, query: str, top_k: int = 8, query_embedding: Optional[List[float]] = None) -> List[MilvusHit]:
        """
        Search in BK (Basisklassifikation) database.

        Args:
            query: Search query
            top_k: Number of results to return
            query_embedding: Optional pre-computed embedding for batch optimization

        Returns:
            List of search results
        """
        if self.db_bk is None:
            return []
        return await self.db_bk.search(query, top_k, query_embedding=query_embedding)

    async def search_gnd_head(self, query: str, top_k: int = 8, query_embedding: Optional[List[float]] = None) -> List[MilvusHit]:
        """
        Search in GND heading database.

        Args:
            query: Search query
            top_k: Number of results to return
            query_embedding: Optional pre-computed embedding for batch optimization

        Returns:
            List of search results
        """
        if self.db_gnd_head is None:
            return []
        return await self.db_gnd_head.search(query, top_k, query_embedding=query_embedding)

    async def search_gnd_desc(self, query: str, top_k: int = 8, query_embedding: Optional[List[float]] = None) -> List[MilvusHit]:
        """
        Search in GND description database.

        Args:
            query: Search query
            top_k: Number of results to return
            query_embedding: Optional pre-computed embedding for batch optimization

        Returns:
            List of search results
        """
        if self.db_gnd_desc is None:
            return []
        return await self.db_gnd_desc.search(query, top_k, query_embedding=query_embedding)

    async def search_gnd_geo(self, query: str, top_k: int = 8, query_embedding: Optional[List[float]] = None) -> List[MilvusHit]:
        """
        Search in GND Geografika database.

        Args:
            query: Search query
            top_k: Number of results to return
            query_embedding: Optional pre-computed embedding for batch optimization

        Returns:
            List of search results
        """
        if self.db_gnd_geo is None:
            return []
        return await self.db_gnd_geo.search(query, top_k, query_embedding=query_embedding)

    async def search_vocabulary(self, term: str, vocabulary: str, limit: int = 10):
        """
        Search in a specific vocabulary.

        Args:
            term: Search term
            vocabulary: Vocabulary type (gnd-saz, gnd-geo, bk)
            limit: Number of results to return

        Returns:
            List of search results with scores
        """
        results = []

        if vocabulary == "bk":

            hits = await self.search_bk(term, top_k=limit)
            for hit in hits:
                results.append({
                    "id": hit["entity"]["notation"],
                    "label": hit["entity"]["label"],
                    "notation": hit["entity"]["notation"],
                    "score": 1.0 - hit["distance"],
                })

        elif vocabulary == "gnd-saz":

            # Search both head and description databases in parallel
            hits_head, hits_desc = await asyncio.gather(
                self.search_gnd_head(term, top_k=limit),
                self.search_gnd_desc(term, top_k=limit),
            )

            # Combine results
            for hit in hits_head:
                results.append({
                    "id": hit["entity"]["gnd_id"],
                    "label": hit["entity"]["heading"],
                    "notation": None,
                    "score": 1.0 - hit["distance"],
                })
            for hit in hits_desc:
                results.append({
                    "id": hit["entity"]["gnd_id"],
                    "label": hit["entity"]["heading"],
                    "notation": None,
                    "score": 1.0 - hit["distance"],
                })

        elif vocabulary == "gnd-geo":

            hits = await self.search_gnd_geo(term, top_k=limit)
            for hit in hits:
                results.append({
                    "id": hit["entity"]["gnd_id"],
                    "label": hit["entity"]["heading"],
                    "notation": None,
                    "score": 1.0 - hit["distance"],
                })

        return results

    async def search_all(self, query: str, top_k: int = 8):
        """
        Search all databases in parallel (BK, GND head, GND desc, GND geo).

        Args:
            query: Search query
            top_k: Number of results to return per database

        Returns:
            Dictionary with results from each database
        """
        bk_results, gnd_head_results, gnd_desc_results, gnd_geo_results = await asyncio.gather(
            self.search_bk(query, top_k),
            self.search_gnd_head(query, top_k),
            self.search_gnd_desc(query, top_k),
            self.search_gnd_geo(query, top_k),
        )
        return {
            "bk": bk_results,
            "gnd_head": gnd_head_results,
            "gnd_desc": gnd_desc_results,
            "gnd_geo": gnd_geo_results,
        }
