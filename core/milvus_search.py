# -*- coding: utf-8 -*-
# =============================================================================
# milvus_search.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Milvus vector database search for nsis.

Provides the Milvus_Search class for dense vector similarity search against:
- BK (Basisklassifikation): Library classification codes
- GND Sachbegriffe: GND subject headings (searchable by heading or description)

Uses qwen3-embedding-8b for query encoding. Features an LRU cache with disk
persistence to reduce duplicate embedding API calls.
"""

import asyncio
import atexit
import csv
import gc
import os
import pickle
import time
import warnings

from pathlib import Path
from typing import List, Optional
from cachetools import LRUCache
from pymilvus import MilvusClient, DataType

from core.inference.embeddings import EmbeddingFunction, perform_embedding_batch
from core.models_config import EMBEDDING_DIM
from core.schemas.types import MilvusHit
from core.usage_stats_logging import usage_stats_logger
from app.utils.dev_print import DevPrint

# Suppress pkg_resources deprecation warning from pymilvus dependencies
warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated.*", category=UserWarning)

# Instruction prefixes for query modification
BK_INSTRUCTION_PREFIX = "Instruct: Find library classification for bibliographic topics\nQuery: "
GND_INSTRUCTION_PREFIX = "Instruct: Find relevant keywords for bibliographic topics\nQuery: "
GEO_INSTRUCTION_PREFIX = "Instruct: Find relevant geographical locations and place names\nQuery: "

def _build_bk_query(query: str):
    """Build a BK query with instruction prefix."""
    return f"{BK_INSTRUCTION_PREFIX}{query}"


def _build_gnd_query(query: str):
    """Build a GND query with instruction prefix."""
    return f"{GND_INSTRUCTION_PREFIX}{query}"


def _build_geo_query(query: str):
    """Build a GND Geografika query with instruction prefix."""
    return f"{GEO_INSTRUCTION_PREFIX}{query}"

# Cache persistence
CACHE_PICKLE_PATH = Path(__file__).parent.parent / "databases" / "query_embedding_cache.pkl"

# Module-level LRU cache for query embeddings to avoid duplicate encoding
# Max 2^14 = 16384 entries (EMBEDDING_DIM × 4 bytes × 16384)
# Automatically evicts least recently used entries when full
_query_embedding_cache: LRUCache = LRUCache(maxsize=16384)
_query_embedding_cache_lock = asyncio.Lock()


def _save_cache():
    """Save cache to disk on server shutdown."""
    DevPrint.info(f"[CACHE] Saving {len(_query_embedding_cache)} entries to {CACHE_PICKLE_PATH}")
    with open(CACHE_PICKLE_PATH, 'wb') as f:
        pickle.dump(dict(_query_embedding_cache), f)
    DevPrint.success("[CACHE] Cache saved")


def _load_cache():
    """Load cache from disk on server startup."""
    if CACHE_PICKLE_PATH.exists():
        DevPrint.info(f"[CACHE] Loading from {CACHE_PICKLE_PATH}")
        with open(CACHE_PICKLE_PATH, 'rb') as f:
            data = pickle.load(f)
            for k, v in data.items():
                _query_embedding_cache[k] = v
        DevPrint.success(f"[CACHE] Loaded {len(_query_embedding_cache)} entries")
    else:
        DevPrint.info("[CACHE] Starting with empty cache")


# Register shutdown handler
atexit.register(_save_cache)

# Load cache on module import (at startup)
_load_cache()

async def _get_embedding(query: str):
    """
    Get embedding for a query, using cache to avoid duplicate encoding.

    When multiple searches run in parallel with the same query (e.g., searching
    both gnd_head and gnd_desc for the same topic), this ensures the embedding
    is computed only once and reused.

    Args:
        query: The query string to embed

    Returns:
        List of floats representing the embedding vector
    """
    query_part = query.split("Query: ")[-1] if "Query: " in query else query
    DevPrint.debug(f"Performing single embedding: {query_part}")

    # Check cache first (without lock for fast path)
    if query in _query_embedding_cache:
        DevPrint.debug("  [SINGLE EMBED] CACHE HIT")
        return _query_embedding_cache[query]

    # Cache miss - compute embedding with lock to prevent duplicate work
    async with _query_embedding_cache_lock:
        # Double-check after acquiring lock (another task may have computed it)
        if query in _query_embedding_cache:
            DevPrint.debug("  [SINGLE EMBED] CACHE HIT (after lock)")
            return _query_embedding_cache[query]

        # Compute embedding
        DevPrint.info("  [SINGLE EMBED] Computing embedding...")
        embeddings = await EmbeddingFunction().encode_queries([query])
        embedding = embeddings[0]

        # Store in cache
        _query_embedding_cache[query] = embedding
        DevPrint.debug(f"  [SINGLE EMBED] Stored (cache: {len(_query_embedding_cache)}/{_query_embedding_cache.maxsize})")
        return embedding


def csv_to_list_of_dicts_BK(csv_path):
    """
    Convert a CSV file containing our BK data into a list of dicts

    Args:
        csv_path (str): Path to CSV file

    Returns:
        list of dicts: for every line of the CSV file, a dict containing the columnar data
            - notation (str): The BK classification code
            - label (str): The classification name
            - scopeNote (str): Scope information
            - llmDescription (str): LLM-generated description
    """

    with open(csv_path, "r") as f:

        reader = csv.reader(f, delimiter=";") # Initialize csv reader
        header = next(reader) # Get the header to map column names to indices

        # Strip UTF-8 BOM from header columns if present
        header = [col.lstrip('\ufeff') for col in header]

        # Build column index mapping from header
        col_indices = {col: idx for idx, col in enumerate(header)}

        list_of_dicts = list()

        # Required columns - will raise KeyError if missing from header
        required_cols = ["notation", "label", "scopeNote", "llmDescription"]

        for line in reader:

            d = dict()
            for col in required_cols:
                d[col] = line[col_indices[col]]

            list_of_dicts.append(d)

    return list_of_dicts

def csv_to_list_of_dicts_GND_Sachbegriffe(csv_path):
    """
    Convert a CSV file containing our GND Sachbegriffe data into a list of dicts.

    Args:
        csv_path (str): Path to CSV file

    Returns:
        list of dicts: for every line of the CSV file, a dict containing the columnar data
            - gnd_id (str): The GND ID of the GND Sachbegriff
            - heading (str): The main heading of the GND Sachbegriff
            - heading_and_alt_term (str): The main heading and the alternative terms of the GND Sachbegriff
            - description (str): A lengthier description of the GND Sachbegriff
    """

    with open(csv_path, "r") as f:

        reader = csv.reader(f, delimiter=";") # Initialize csv reader
        header = next(reader) # Get the header to map column names to indices

        # Strip UTF-8 BOM from header columns if present
        header = [col.lstrip('\ufeff') for col in header]

        # Build column index mapping from header
        col_indices = {col: idx for idx, col in enumerate(header)}

        list_of_dicts = list()

        # Required columns - will raise KeyError if missing from header
        required_cols = ["gnd_id", "heading", "heading_and_alt_term", "description"]

        for line in reader:

            d = dict()
            for col in required_cols:
                d[col] = line[col_indices[col]]

            list_of_dicts.append(d)

    return list_of_dicts


def csv_to_list_of_dicts_GND_Geografika(csv_path):
    """
    Convert a CSV file containing our GND Geografika data into a list of dicts.

    Args:
        csv_path (str): Path to CSV file

    Returns:
        list of dicts: for every line of the CSV file, a dict containing the columnar data
            - gnd_id (str): The GND ID of the geographical entity
            - heading (str): The heading/name of the geographical entity
            - description (str): Notes/description of the geographical entity
    """

    with open(csv_path, "r") as f:

        reader = csv.reader(f, delimiter=";") # Initialize csv reader
        header = next(reader) # Get the header to map column names to indices

        # Strip UTF-8 BOM from header columns if present
        header = [col.lstrip('\ufeff') for col in header]

        # Build column index mapping from header
        col_indices = {col: idx for idx, col in enumerate(header)}

        list_of_dicts = list()

        # Required columns - will raise KeyError if missing from header
        gnd_idx = col_indices["gnd"]
        heading_idx = col_indices["heading"]
        notes_idx = col_indices["notes"]

        for line in reader:

            d = dict()
            d["gnd_id"] = line[gnd_idx]
            d["heading"] = line[heading_idx]
            d["notes"] = line[notes_idx]

            list_of_dicts.append(d)

    return list_of_dicts


class Milvus_Search:
    """
    A unified class for managing and searching different types of data (BK, GND Sachbegriffe)
    using Milvus vector database with dense embeddings.

    Attributes:
        db_path (str): Path to the Milvus Lite database file
        client (MilvusClient): Instance of Milvus client
        collection_name (str): Name of the Milvus collection
        data_type (str): Type of data being searched ("bk" or "gnd_saz")
        nprobe (int): Number of clusters to search
        nlist (int): Number of clusters in the index
        metric_type (str): Distance metric ("COSINE")
        index_type (str): Index type ("IVF_FLAT")
    """

    db_path: Optional[str] = None          # the local path of the milvus lite database (initialized in __init__)
    client: Optional[MilvusClient] = None  # the client object (initialized in init_db)
    collection_name: Optional[str] = None  # the name of the collection used in this instance
    data_type: Optional[str] = None        # type of data being searched (“bk” or “gnd_saz”)
    nprobe: Optional[int] = None           # number of clusters to search (dependent of dataset)
    nlist: Optional[int] = None
    metric_type: Optional[str] = None
    index_type: Optional[str] = None

    def __init__(self, data_type, device):
        """
        Initialize the Milvus_Search class with a data type and computation device.

        Args:
            data_type (str): Type of data to search ("bk" or "gnd_saz")
            device (str): Type of computation device to use ("cpu" or "cuda:0")
        """

        # set the data type and assert that it has a correct value
        self.data_type = data_type

        # Define valid data types and their index configurations

        # IVF_FLAT: Inverted file with flat index for dense floating-point vectors
        # L2: Euclidean distance metric
        # OSINE: Cosine similarity
        # SPARSE_INVERTED_INDEX: Inverted index for sparse vectors
        # IP: Inner product
        # HNSW: Hierarchical Navigable Small World

        DATA_TYPES_CONF = {
            "bk": {
                "nlist": 128,
                "nprobe": 4,
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
            },
            "gnd_saz": {
                "nlist": 4096,
                "nprobe": 1,
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
            },
            "gnd_geo": {
                "nlist": 4096,
                "nprobe": 1,
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
            },
        }

        assert (
            isinstance(data_type, str) and data_type in DATA_TYPES_CONF
        ), f"data_type must be one of {list(DATA_TYPES_CONF.keys())}, got '{data_type}'"

        # Apply configuration from valid types
        config = DATA_TYPES_CONF[self.data_type]
        self.nlist = config["nlist"]
        self.nprobe = config["nprobe"]
        self.metric_type = config["metric_type"]
        self.index_type = config["index_type"]

        # values selected using ./tests/test_milvus_recall_quality.py

    def load_db(self, db_path: str, collection_name: str):
        """
        Load an existing database into memory for search operations.

        Args:
            db_path: Path to database file
            collection_name: Name of the collection to load

        Returns:
            bool: True if DB was loaded, False if it doesn't exist
        """
        self.db_path = db_path
        self.collection_name = collection_name

        if not os.path.exists(self.db_path):
            return False

        self.client = MilvusClient(self.db_path)
        DevPrint.debug(f"    Loading {self.collection_name} into memory...")
        self.client.load_collection(self.collection_name)
        return True

    async def init_db(self, db_path: str, csv_path: str, collection_name: str,
                      max_concurrent_batches: int = 8):
        """
        Initialize a new database from CSV with parallel embedding generation.

        This async method is designed to be run in a thread via asyncio.to_thread()
        at the call site to avoid blocking the event loop.

        Args:
            db_path: Path to database file
            csv_path: Path to CSV file
            collection_name: Name of the collection that is being initialized
            max_concurrent_batches: Maximum number of batches to process concurrently (default 8)
        """
        # set database path and collection name
        self.db_path = db_path
        self.collection_name = collection_name

        # Guard: Check if db_path exists - should only be called for new DBs
        if os.path.exists(self.db_path):
            raise FileExistsError(f"Database {self.db_path} already exists. Use load_db() to load an existing database.")

        DevPrint.info(f"DB {collection_name} does not exist. Creating from {csv_path}...")

        # initialize Milvus client with a local database file
        self.client = MilvusClient(self.db_path)

        # create a schema for the collection
        # auto_id=False allows manual ID assignment
        # enable_dynamic_schema=True allows adding new fields later
        schema = self.client.create_schema(
            auto_id=False,
            enable_dynamic_schema=True,
        )

        # common fields for all data types
        schema.add_field(field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)

        # define data_type specific collection fields
        if self.data_type == 'bk':

            schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
            schema.add_field(field_name="notation", datatype=DataType.VARCHAR, max_length=8)
            schema.add_field(field_name="label", datatype=DataType.VARCHAR, max_length=512)
            schema.add_field(field_name="scopeNote", datatype=DataType.VARCHAR, max_length=512)
            schema.add_field(field_name="llmDescription", datatype=DataType.VARCHAR, max_length=1024)

        elif self.data_type == 'gnd_saz':

            schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
            schema.add_field(field_name="gnd_id", datatype=DataType.VARCHAR, max_length=64)
            schema.add_field(field_name="heading", datatype=DataType.VARCHAR, max_length=256)
            schema.add_field(field_name="heading_and_alt_term", datatype=DataType.VARCHAR, max_length=256)
            schema.add_field(field_name="description", datatype=DataType.VARCHAR, max_length=2048)

        elif self.data_type == 'gnd_geo':

            schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
            schema.add_field(field_name="gnd_id", datatype=DataType.VARCHAR, max_length=64)
            schema.add_field(field_name="heading", datatype=DataType.VARCHAR, max_length=256)
            schema.add_field(field_name="notes", datatype=DataType.VARCHAR, max_length=2048)

        else:

            pass # should not be reached

        # create the collection without index first (faster inserts)
        # index will be built after all data is inserted
        self.client.create_collection(collection_name=self.collection_name, schema=schema)

        # read in data from the provided csv file and extract the docs which we want to generate the embeddings for
        data_list_of_dicts = []
        docs = []
        if self.data_type == 'bk':

            data_list_of_dicts = csv_to_list_of_dicts_BK(csv_path)

            docs = [data_list_of_dicts[i]["llmDescription"] for i in range(len(data_list_of_dicts))]

        elif self.data_type == 'gnd_saz':

            data_list_of_dicts = csv_to_list_of_dicts_GND_Sachbegriffe(csv_path)

            if collection_name == 'gnd_sachbegriffe_head':

                docs = [data_list_of_dicts[i]["heading"] for i in range(len(data_list_of_dicts))]

            elif collection_name == 'gnd_sachbegriffe_desc':

                docs = [data_list_of_dicts[i]["description"] for i in range(len(data_list_of_dicts))]

            else:
                pass # should not be reached

        elif self.data_type == 'gnd_geo':

            data_list_of_dicts = csv_to_list_of_dicts_GND_Geografika(csv_path)

            docs = [data_list_of_dicts[i]["heading"] for i in range(len(data_list_of_dicts))]

        else:

            pass # should not be reached

        # generate dense vector embeddings and insert them into the database
        # process in batches for memory efficiency with parallel embedding generation

        docs_batch_size = 1024
        batch_count = (len(docs) + docs_batch_size - 1) // docs_batch_size
        DevPrint.info(f"Processing {batch_count} batches (batch_size={docs_batch_size}, max_concurrent={max_concurrent_batches})...")

        # Prepare batch texts for parallel processing
        batch_texts_list = []
        batch_bounds_list = []
        for batch_idx in range(batch_count):
            docs_batch_lower_bound = batch_idx * docs_batch_size
            docs_batch_higher_bound = min(docs_batch_lower_bound + docs_batch_size, len(docs))
            batch_texts_list.append(docs[docs_batch_lower_bound:docs_batch_higher_bound])
            batch_bounds_list.append((docs_batch_lower_bound, docs_batch_higher_bound))

        # Process batches in groups for parallel embedding generation
        # Groups are processed sequentially to avoid memory overload
        # Each group: generate embeddings -> insert -> clear memory
        total_inserted = 0
        for group_start in range(0, batch_count, max_concurrent_batches):
            group_end = min(group_start + max_concurrent_batches, batch_count)

            DevPrint.info(f"Processing group {group_start // max_concurrent_batches + 1}: batches {group_start + 1}-{group_end} concurrently...")

            # Create tasks for concurrent embedding generation within the group
            async def create_embedding_task(batch_idx: int, texts: List[str]):
                DevPrint.debug(f"  Generating embeddings for batch {batch_idx + 1}/{batch_count}...")
                embeddings = await perform_embedding_batch(texts)
                return batch_idx, embeddings

            tasks = [create_embedding_task(batch_idx, batch_texts_list[batch_idx])
                     for batch_idx in range(group_start, group_end)]

            # Execute all tasks in the group concurrently
            results = await asyncio.gather(*tasks)

            # Insert each batch and clear memory immediately after
            for batch_idx, docs_embeddings in results:
                docs_batch_lower_bound, docs_batch_higher_bound = batch_bounds_list[batch_idx]

                DevPrint.debug(f"Inserting batch {batch_idx + 1}/{batch_count} ({docs_batch_lower_bound}:{docs_batch_higher_bound})")

                # prepare data for insertion by combining document properties
                data: List[dict] = []
                if self.data_type == 'bk':

                    data = [{
                        "id": docs_batch_lower_bound+i,
                        "dense_vector": docs_embeddings[i],
                        "notation": data_list_of_dicts[docs_batch_lower_bound+i]["notation"],
                        "label": data_list_of_dicts[docs_batch_lower_bound+i]["label"],
                        "scopeNote": data_list_of_dicts[docs_batch_lower_bound+i]["scopeNote"],
                        "llmDescription": data_list_of_dicts[docs_batch_lower_bound+i]["llmDescription"]
                    } for i in range(len(docs_embeddings))]

                elif self.data_type == 'gnd_saz':

                    data = [{
                        "id": docs_batch_lower_bound+i,
                        "dense_vector": docs_embeddings[i],
                        "gnd_id": data_list_of_dicts[docs_batch_lower_bound+i]["gnd_id"],
                        "heading": data_list_of_dicts[docs_batch_lower_bound+i]["heading"],
                        "heading_and_alt_term": data_list_of_dicts[docs_batch_lower_bound+i]["heading_and_alt_term"],
                        "description": data_list_of_dicts[docs_batch_lower_bound+i]["description"]
                    } for i in range(len(docs_embeddings))]

                elif self.data_type == 'gnd_geo':

                    data = [{
                        "id": docs_batch_lower_bound+i,
                        "dense_vector": docs_embeddings[i],
                        "gnd_id": data_list_of_dicts[docs_batch_lower_bound+i]["gnd_id"],
                        "heading": data_list_of_dicts[docs_batch_lower_bound+i]["heading"],
                        "notes": data_list_of_dicts[docs_batch_lower_bound+i]["notes"]
                    } for i in range(len(docs_embeddings))]

                else:

                    pass # should not be reached

                # insert the prepared data into the collection in batches
                insert_batch_size = docs_batch_size
                batch_inserted = 0
                for insert_i in range(0, len(data), insert_batch_size):

                    # calculate lower and higher bound for the batch
                    insert_batch_lower_bound = insert_i
                    insert_batch_higher_bound = min(insert_i+insert_batch_size,len(data)) # last batch can be smaller

                    res = self.client.insert(
                        collection_name=self.collection_name,
                        data=data[insert_batch_lower_bound:insert_batch_higher_bound]
                    )

                    batch_inserted += res["insert_count"]

                total_inserted += batch_inserted

                # Clean up data immediately to free RAM
                del docs_embeddings, data
                gc.collect()

        # total_inserted and row_cound should be equal in number
        DevPrint.success(f"Inserted {total_inserted} rows in total.")
        DevPrint.info(f"Collection has {self.client.get_collection_stats(self.collection_name)['row_count']} rows in total.")

        # Build index after all data is inserted

        # Type assertions for type checker
        assert self.collection_name is not None, "collection_name must be set"
        assert self.index_type is not None, "index_type must be set"
        assert self.metric_type is not None, "metric_type must be set"
        assert self.nlist is not None, "nlist must be set"

        DevPrint.info(f"Building index ({self.index_type})...")

        # Prepare index params
        index_params = self.client.prepare_index_params()
        index_params.add_index(field_name="dense_vector", index_type=self.index_type, metric_type=self.metric_type, params={"nlist": self.nlist})

        # Create the index
        self.client.create_index(collection_name=self.collection_name, index_params=index_params)

        DevPrint.success("Index built successfully.")

    def rebuild_index(self):
        """
        Rebuild the index on an existing collection.
        Useful when the collection was created without an index or the index is missing.
        """
        # Type assertions for type checker
        assert self.collection_name is not None, "collection_name must be set"
        assert self.db_path is not None, "db_path must be set"
        assert self.index_type is not None, "index_type must be set"
        assert self.metric_type is not None, "metric_type must be set"
        assert self.nlist is not None, "nlist must be set"

        DevPrint.info(f"Rebuilding index for {self.collection_name}...")

        # Initialize client if not already done
        if self.client is None:
            self.client = MilvusClient(self.db_path)

        # Prepare index params
        index_params = self.client.prepare_index_params()
        index_params.add_index(field_name="dense_vector", index_type=self.index_type, metric_type=self.metric_type, params={"nlist": self.nlist})

        # Create the index
        DevPrint.debug(f"    Creating {self.index_type} index on dense_vector field...")
        self.client.create_index(collection_name=self.collection_name, index_params=index_params)
        DevPrint.success("    Index created successfully.")

        # Reload collection to ensure index is available for search
        DevPrint.debug("    Reloading collection into memory...")
        self.client.load_collection(self.collection_name)
        DevPrint.success("    Done.")

    async def search(self, query, top_k, query_embedding: Optional[List[float]] = None) -> List[MilvusHit]:
        """
        Perform a search with a given query and modality.

        Args:
            query (str): Search query
            top_k (int): Specify how many results are retrieved
            query_embedding (Optional[List[float]]): Pre-computed embedding vector.
                If provided, skips embedding computation (for batch optimization).

        Returns:
            List[MilvusHit]: Top n results for the given query and modality
        """
        # Type assertions for type checker
        assert self.client is not None, "client must be set (call load_db first)"
        assert self.collection_name is not None, "collection_name must be set"
        assert self.metric_type is not None, "metric_type must be set"
        assert self.nprobe is not None, "nprobe must be set"

        # specify search parameters for dense vector search
        search_params_dense = {
            "metric_type": self.metric_type,                # search_metric
            "params": {"nprobe": self.nprobe}   # number of clusters to search
        }

        # define output fields based on data type
        output_fields: List[str] = []
        if self.data_type == 'bk':
            output_fields = ["notation", "label"]
        elif self.data_type == 'gnd_saz':
            output_fields = ["gnd_id", "heading"]
        elif self.data_type == 'gnd_geo':
            output_fields = ["gnd_id", "heading"]
        else:
            pass # should not be reached

        # check if query is a warmup query
        if query == "__warmup__":
            DevPrint.debug(f"    Warming up {self.data_type}...")
            res = self.client.search(
                collection_name=self.collection_name,
                data=[[0 for i in range(EMBEDDING_DIM)]],
                anns_field="dense_vector", # field to search on
                search_params=search_params_dense,
                limit=top_k, # return top k matches
                output_fields=output_fields,
            )
            return res[0]

        # modify the query so that it is more accurate on our search data
        if self.data_type == 'bk':
            query = _build_bk_query(query)
        elif self.data_type == 'gnd_saz':
            query = _build_gnd_query(query)
        elif self.data_type == 'gnd_geo':
            query = _build_geo_query(query)
        else:
            pass # should not be reached

        # Use provided embedding or compute it (with caching)
        if query_embedding is not None:
            query_vector_dense = query_embedding
        else:
            # get embedding vector for the search query (use running event loop)
            # Use cached embedding to avoid duplicate encoding when same query
            # is searched against multiple databases (e.g., gnd_head and gnd_desc)
            query_vector_dense = await _get_embedding(query)

        # perform dense vector search with timing
        time_start = time.time_ns()
        res = self.client.search(
            collection_name=self.collection_name,
            data=[query_vector_dense],
            anns_field="dense_vector", # field to search on
            search_params=search_params_dense,
            limit=top_k, # return top k matches
            output_fields=output_fields,
        )
        time_end = time.time_ns()
        duration_ms = (time_end - time_start) / 1_000_000

        # Log performance metrics
        usage_stats_logger.log_performance(
            operation_type="milvus_search",
            duration_ms=duration_ms,
            data_type=self.data_type,
            top_k=top_k,
            result_count=len(res[0]) if res else 0
        )

        return res[0]