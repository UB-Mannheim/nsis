# -*- coding: utf-8 -*-
# =============================================================================
# transformation_service.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Transformation service for nsis FastAPI application.
Orchestrates the complete query transformation pipeline.
"""

import asyncio
import time
from typing import Dict, List, Optional
from app.services.milvus_service import MilvusService
from core.inference import (
    analyze_search_intent,
    extract_facettes,
    rerank_search_results,
    build_logical_tree,
)
from core.inference.embeddings import EmbeddingFunction
from core import milvus_search
from app.utils.dev_print import DevPrint


def _normalize_author_name(name: str) -> str:
    """
    Normalize author name to 'Surname, Given name' format.

    Handles names in natural language format like 'Sabine Gehrlein' and
    converts them to catalog format 'Gehrlein, Sabine'. Names already in
    the correct format (containing a comma) are returned unchanged.

    Args:
        name: Author name in any format

    Returns:
        Author name in 'Surname, Given name' format
    """
    name = name.strip()
    if "," in name:
        return name
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[-1]}, {' '.join(parts[:-1])}"
    return name


def _extract_german_author_patterns(query: str) -> List[str]:
    """
    Extract potential author names from German query patterns.

    In German, "von [Name]" often indicates authorship (e.g., "von Sabine Gehrlein").
    This function extracts names following such patterns as potential authors.

    Args:
        query: The user query string

    Returns:
        List of potential author names found in the query
    """
    import re
    authors = []

    # Pattern: "von [Name]" - captures names after "von" indicating authorship
    # Matches: "von Sabine Gehrlein", "von Prof. Dr. Müller", "von 'Name'"
    von_pattern = re.compile(
        r'\bvon\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)',
        re.UNICODE
    )
    for match in von_pattern.finditer(query):
        name = match.group(1).strip()
        # Validate: should have at least 2 words (typical name)
        if len(name.split()) >= 2:
            authors.append(name)

    return authors


class TransformationService:
    """Service for query transformation operations."""

    def __init__(self, milvus_service: MilvusService):
        """
        Initialize the transformation service.

        Args:
            milvus_service: Milvus service instance
        """
        self.milvus_service = milvus_service

    async def transform_query(self, user_request: str, search_intent: Optional[str] = None) -> Dict:
        """
        Transform a natural language query into structured search metadata.

        This is the main transformation pipeline that:
        1. Analyzes search intent (if not provided)
        2. Extracts facets
        3. Performs vector search
        4. Reranks results
        5. Analyzes logical tree
        6. Builds metadata

        Args:
            user_request: The natural language query
            search_intent: Optional pre-detected search intent

        Returns:
            Dictionary containing metadata
        """
        DevPrint.info(f"User request: {user_request}")

        # 1) Search-intent analysis (only if not provided)
        if search_intent is None:
            DevPrint.debug("Search intent was not passed, analyzing")
            intent_json = await analyze_search_intent(user_request)
            search_intent = intent_json.get("searchIntent", "topicSearch")  # topicSearch as fallback

        # Known-item short-circuit
        if search_intent == "knownItem":
            DevPrint.info("Performing known-item search")
            return {
                "metadata": {
                    "searchIntent": "knownItem",
                    "filters": {
                        "mediaForms": [],
                        "contentGenres": [],
                        "authorNames": [],
                        "languages": [],
                    },
                    "gndHeadings": [],
                    "bkNotations": [],
                    "dateRange": {"from": None, "to": None},
                    "logicalTree": None,
                },
            }

        # 2) Facette extraction
        facettes = await extract_facettes(user_request)

        media_forms = facettes.get("mediaForms", []) or []
        content_genres = facettes.get("contentGenres", []) or []
        author_names = facettes.get("authorNames", []) or []
        languages = facettes.get("languages", []) or []

        # Supplement with German author patterns (e.g., "von Sabine Gehrlein")
        german_authors = _extract_german_author_patterns(user_request)
        author_names_normalized = set(_normalize_author_name(a).lower() for a in author_names)
        for ga in german_authors:
            ga_normalized = _normalize_author_name(ga)
            if ga_normalized.lower() not in author_names_normalized:
                author_names.append(ga)
                author_names_normalized.add(ga_normalized.lower())
                DevPrint.debug(f"Added author from German pattern: {ga}")
        date_range = facettes.get("dateRange", {}) or {}
        start_year = date_range.get("startYear")
        end_year = date_range.get("endYear")
        topics_orig = facettes.get("topicsInOriginalLanguage", []) or []
        topics_en = facettes.get("topicsInEnglish", []) or []

        # Remove author names from topics to avoid duplicate search
        # (author names should only be used as facets, not search terms)
        topics_orig = [t for t in topics_orig if t.lower() not in author_names_normalized]
        topics_en = [t for t in topics_en if t.lower() not in author_names_normalized]

        DevPrint.debug(f"searchIntent: {search_intent}")
        DevPrint.debug(f"mediaForms: {media_forms}")
        DevPrint.debug(f"contentGenres: {content_genres}")
        DevPrint.debug(f"authorNames: {author_names}")
        DevPrint.debug(f"languages: {languages}")
        DevPrint.debug(f"startYear: {start_year}")
        DevPrint.debug(f"endYear: {end_year}")
        DevPrint.debug(f"topicsOrig: {topics_orig}")
        DevPrint.debug(f"topicsEn: {topics_en}")

        # 3) Vector search - parallel across all topics and databases
        # Using a batch mechanism for embedding queries to reduce API calls
        DevPrint.info(f"Performing batch embedding: {topics_orig}")

        no_of_topics = len(topics_orig)
        top_k = 8 if no_of_topics > 0 else 0

        search_results_bk = []
        search_results_gnd = []

        if no_of_topics > 0:
            # Step 1: Build "Pool of Pools" - collect all queries with prefixes
            bk_queries = [milvus_search._build_bk_query(topic) for topic in topics_en]
            gnd_saz_queries = [milvus_search._build_gnd_query(topic) for topic in topics_orig]
            gnd_geo_queries = [milvus_search._build_geo_query(topic) for topic in topics_orig]

            # Combine into single list for batch embedding
            all_queries = bk_queries + gnd_saz_queries + gnd_geo_queries
            bk_count = len(bk_queries)  # used to split BK embeddings later
            gnd_count = len(gnd_saz_queries)  # used to split GND embeddings later

            # Step 2: Check cache for each query (fast, no lock needed for reads)
            # We use the module-level cache from milvus_search
            all_embeddings_list: List[Optional[List[float]]] = [None] * len(all_queries)
            missing_indices = []
            missing_queries = []

            for i, q in enumerate(all_queries):
                if q in milvus_search._query_embedding_cache:
                    all_embeddings_list[i] = milvus_search._query_embedding_cache[q]
                else:
                    missing_indices.append(i)
                    missing_queries.append(q)

            cache_hits = len(all_queries) - len(missing_queries)
            if cache_hits > 0:
                DevPrint.debug(f"  [BATCH EMBED] Cache hits: {cache_hits}/{len(all_queries)}")

            # Step 3: Batch-embed ONLY missing queries (1 API call for all missing queries)
            if missing_queries:
                DevPrint.info(f"  [BATCH EMBED] Computing embeddings for {len(missing_queries)} missing queries...")
                new_embeddings = await EmbeddingFunction().encode_queries(missing_queries)

                # Write newly computed embeddings to cache
                async with milvus_search._query_embedding_cache_lock:
                    for idx, emb in zip(missing_indices, new_embeddings):
                        all_embeddings_list[idx] = emb
                        q = all_queries[idx]
                        milvus_search._query_embedding_cache[q] = emb

                DevPrint.info(f"  [BATCH EMBED] Cached {len(missing_queries)} new embeddings (cache size: {len(milvus_search._query_embedding_cache)})")

            # Step 4: Split embeddings by index
            bk_embeddings = all_embeddings_list[:bk_count]
            gnd_saz_embeddings = all_embeddings_list[bk_count:bk_count + gnd_count]
            gnd_geo_embeddings = all_embeddings_list[bk_count + gnd_count:]

            # Step 5: Run parallel searches with pre-computed embeddings

            # Build search tasks with pre-computed embeddings
            bk_tasks = []
            for i in range(bk_count):
                topic = topics_en[i]
                embedding = bk_embeddings[i]
                bk_tasks.append((topic, embedding, self.milvus_service.search_bk(topic, top_k, query_embedding=embedding)))

            gnd_saz_tasks = []
            for i, topic in enumerate(topics_orig):
                emb = gnd_saz_embeddings[i]
                gnd_saz_tasks.append((topic, "head", emb, self.milvus_service.search_gnd_head(topic, top_k, query_embedding=emb)))
                gnd_saz_tasks.append((topic, "desc", emb, self.milvus_service.search_gnd_desc(topic, top_k, query_embedding=emb)))

            gnd_geo_tasks = []
            for i, topic in enumerate(topics_orig):
                emb = gnd_geo_embeddings[i]
                gnd_geo_tasks.append((topic, emb, self.milvus_service.search_gnd_geo(topic, top_k, query_embedding=emb)))

            # Run all searches in parallel
            # item at index -1 (last element) is the milvus_service.search_ task
            all_tasks = [task[-1] for task in bk_tasks] + [task[-1] for task in gnd_saz_tasks] + [task[-1] for task in gnd_geo_tasks]
            all_results = await asyncio.gather(*all_tasks)

            # Split results back into BK, GND-SAZ, and GND-GEO
            all_bk_results = all_results[:len(bk_tasks)]
            all_gnd_saz_results = all_results[len(bk_tasks):len(bk_tasks) + len(gnd_saz_tasks)]
            all_gnd_geo_results = all_results[len(bk_tasks) + len(gnd_saz_tasks):]
        else:
            all_bk_results = []
            all_gnd_saz_results = []
            all_gnd_geo_results = []
            bk_tasks = []
            gnd_saz_tasks = []
            gnd_geo_tasks = []

        # Process BK results
        for idx, (topic, _, _) in enumerate(bk_tasks):
            hits = all_bk_results[idx]
            DevPrint.debug(f'Top {top_k} BK for "{topic}":')
            for i, r in enumerate(hits, 1):
                DevPrint.result(f'    {i}. {r["entity"]["notation"]} {r["entity"]["label"]} (d={r["distance"]:.3f})')
            search_results_bk += hits

        # Process GND-SAZ results (interleaved head/desc per topic)
        gnd_saz_idx = 0
        topic_gnd_head = {}
        topic_gnd_desc = {}
        for topic, db_type, _, _ in gnd_saz_tasks:
            hits = all_gnd_saz_results[gnd_saz_idx]
            if db_type == "head":
                topic_gnd_head[topic] = hits
            else:
                topic_gnd_desc[topic] = hits
            gnd_saz_idx += 1

        # Process GND-GEO results
        topic_gnd_geo = {}
        for i, topic in enumerate(topics_orig):
            hits = all_gnd_geo_results[i] if i < len(all_gnd_geo_results) else []
            topic_gnd_geo[topic] = hits

        # Print GND results in topic order
        for topic in topics_orig:
            hits_head = topic_gnd_head.get(topic, [])
            hits_desc = topic_gnd_desc.get(topic, [])
            hits_geo = topic_gnd_geo.get(topic, [])
            DevPrint.debug(f'Top {top_k} GND HEAD for "{topic}":')
            for i, r in enumerate(hits_head, 1):
                DevPrint.result(f'    {i}. {r["entity"]["gnd_id"]} {r["entity"]["heading"]} (d={r["distance"]:.3f})')
            search_results_gnd += hits_head

            DevPrint.debug(f'Top {top_k} GND DESC for "{topic}":')
            for i, r in enumerate(hits_desc, 1):
                DevPrint.result(f'    {i}. {r["entity"]["gnd_id"]} {r["entity"]["heading"]} (d={r["distance"]:.3f})')
            search_results_gnd += hits_desc

            DevPrint.debug(f'Top {top_k} GND GEO for "{topic}":')
            for i, r in enumerate(hits_geo, 1):
                DevPrint.result(f'    {i}. {r["entity"]["gnd_id"]} {r["entity"]["heading"]} (d={r["distance"]:.3f})')
            search_results_gnd += hits_geo

        # 4) LLM-based reranking (parallel for independent BK and GND)
        rr_bk_task = None
        rr_gnd_saz_task = None

        if search_results_bk:
            labels = [b["entity"]["label"] for b in search_results_bk]
            rr_bk_task = rerank_search_results(user_request, labels, "BK")

        if search_results_gnd:
            headings = [g["entity"]["heading"] for g in search_results_gnd]
            rr_gnd_saz_task = rerank_search_results(user_request, headings, "GND-SAZ")

        # Run both rerankings in parallel
        rerank_start = time.time()
        rr_bk_result, rr_gnd_result = await asyncio.gather(
            rr_bk_task if rr_bk_task else asyncio.sleep(0),
            rr_gnd_saz_task if rr_gnd_saz_task else asyncio.sleep(0),
        )
        rerank_elapsed = time.time() - rerank_start

        if search_results_bk and rr_bk_result:
            search_results_bk = [search_results_bk[i] for i in rr_bk_result.get("indicesOfRelevantTopics", [])]

        if search_results_gnd and rr_gnd_result:
            search_results_gnd = [search_results_gnd[i] for i in rr_gnd_result.get("indicesOfRelevantTopics", [])]

        # Deduplicate selected results
        seen_gnd = set()
        search_results_gnd = [r for r in search_results_gnd if r["entity"]["heading"] not in seen_gnd and not seen_gnd.add(r["entity"]["heading"])]

        seen_bk = set()
        search_results_bk = [r for r in search_results_bk if r["entity"]["notation"] not in seen_bk and not seen_bk.add(r["entity"]["notation"])]

        DevPrint.timing(f"Reranking completed in {rerank_elapsed:.2f}s")

        # 5) Logical tree - build from reranked results per topic
        # Extract heading strings from result lists for proper membership testing
        topic_headings_head = {
            topic: {r["entity"]["heading"] for r in hits}
            for topic, hits in topic_gnd_head.items() if hits
        }
        topic_headings_desc = {
            topic: {r["entity"]["heading"] for r in hits}
            for topic, hits in topic_gnd_desc.items() if hits
        }
        topic_headings_geo = {
            topic: {r["entity"]["heading"] for r in hits}
            for topic, hits in topic_gnd_geo.items() if hits
        }

        concepts_gnd = {}
        for topic in topics_orig:
            topic_headings = []
            for result in search_results_gnd:
                heading = result["entity"]["heading"]
                if (heading in topic_headings_head.get(topic, set()) or
                    heading in topic_headings_desc.get(topic, set()) or
                    heading in topic_headings_geo.get(topic, set())):
                    topic_headings.append(heading)
            if topic_headings:
                concepts_gnd[topic] = topic_headings

        DevPrint.debug(f"Headings grouped by topic ({len(concepts_gnd)}):")
        for topic, headings in concepts_gnd.items():
            DevPrint.debug(f"  {topic}: {headings}")

        logical_tree = build_logical_tree(concepts_gnd, {}) if concepts_gnd else {}

        # 6) Build metadata

        meta_media_forms = []
        for mf in media_forms:
            meta_media_forms.append({"label": mf, "filterValue": mf})

        meta_genres = []
        for cg in content_genres:
            meta_genres.append({"label": cg, "filterValue": cg})

        meta_languages = []
        for lang in languages:
            meta_languages.append({"label": lang, "filterValue": lang})

        meta_authors = []
        for a in author_names:
            normalized = _normalize_author_name(a)
            meta_authors.append({"label": normalized, "filterValue": normalized})

        meta_bk = [
            {"notation": bk["entity"]["notation"], "label": str(bk["entity"].get("label", bk["entity"]["notation"]))}
            for bk in search_results_bk
        ]

        # Build gndHeadingsConcepts dict directly from search_results_gnd and concepts_gnd
        meta_gnd_concepts: Dict[str, List[Dict]] = {}
        for g in search_results_gnd:
            heading = str(g["entity"]["heading"])
            # Find which topic/concept this heading belongs to
            concept_key = None
            for topic, headings in concepts_gnd.items():
                if heading in headings:
                    concept_key = topic
                    break
            if concept_key:
                if concept_key not in meta_gnd_concepts:
                    meta_gnd_concepts[concept_key] = []
                meta_gnd_concepts[concept_key].append({
                    "heading": heading,
                    "gnd_id": str(g["entity"].get("gnd_id", "")),
                    "conceptKey": concept_key
                })

        metadata = {
            "searchIntent": search_intent,
            "filters": {
                "mediaForms": meta_media_forms,
                "contentGenres": meta_genres,
                "authorNames": meta_authors,
                "languages": meta_languages,
            },
            "gndHeadingsConcepts": meta_gnd_concepts,
            "bkNotations": meta_bk,
            "dateRange": {
                "from": start_year,
                "to": end_year,
            },
            "logicalTree": logical_tree,
        }

        return {"metadata": metadata}