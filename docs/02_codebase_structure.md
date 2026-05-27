## Codebase Structure

### Directory Organization

```
nsis/
├── .env                                                      # Environment variables (gitignored)
├── .env.sample                                               # Environment variables template
├── .gitignore                                                # Git ignore rules
├── .python-version                                           # Python version specification
├── README.md                                                 # Project readme
├── pyproject.toml                                            # Python project configuration
│
├── app/                                                      # FastAPI application
│   ├── __init__.py
│   ├── main.py                                               # Entry point, middleware, exception handlers
│   ├── dependencies.py                                       # Service container and DI
│   ├── config.py                                             # Application configuration
│   ├── config.py.sample                                      # Configuration template
│   ├── rate_limit.py                                         # Rate limiting configuration
│   ├── ip_blocklist.py                                       # IP blocking management
│   ├── ip_tracker.py                                         # IP tracking for bot detection
│   │
│   ├── api/                                                  # API routers
│   │   ├── __init__.py
│   │   ├── v1/                                               # API v1 router and endpoints
│   │   │   ├── __init__.py
│   │   │   ├── router.py                                     # Main router
│   │   │   ├── endpoints/                                    # Individual endpoint modules
│   │   │   │   ├── __init__.py
│   │   │   │   ├── keyword_mapping.py                        # Map keywords to concepts
│   │   │   │   ├── logical_tree.py                           # Build boolean search trees
│   │   │   │   ├── query_expansion.py                        # Expand queries with keywords
│   │   │   │   ├── query_facettes.py                         # Extract faceted filters
│   │   │   │   ├── query_quality.py                          # Assess search result quality
│   │   │   │   ├── query_transformation.py                   # Complete transformation pipeline
│   │   │   │   ├── search_intent.py                          # Analyze search intent
│   │   │   │   ├── vocabulary_lookup.py                      # Search authority databases
│   │   │   │   └── vufind_search.py                          # Proxy to VuFind catalog
│   │   │   └── schemas/                                      # Pydantic request/response schemas
│   │   │       ├── __init__.py
│   │   │       ├── requests.py                               # Request schemas
│   │   │       └── responses.py                              # Response schemas
│   │   └── v2/                                               # API v2 router (placeholder)
│   │       ├── __init__.py
│   │       └── router.py
│   │
│   ├── services/                                             # Business logic services
│   │   ├── __init__.py
│   │   ├── milvus_service.py                                 # Milvus vector database operations
│   │   ├── transformation_service.py                         # Query transformation pipeline
│   │   └── vufind_service.py                                 # VuFind integration service
│   │
│   ├── static/                                               # Frontend assets for Research Compass UI
│   │   ├── research-compass.html                             # Main HTML interface
│   │   ├── research-compass.css                              # UI styles
│   │   ├── research-compass.js                               # Client-side JavaScript
│   │   └── research-compass-settings.js                      # Configuration and i18n
│   │
│   └── utils/                                                # Utility functions
│       ├── __init__.py
│       ├── abort.py                                          # Abort request helpers
│       ├── dev_print.py                                      # DevPrint colored output utility
│       ├── dev_print_api.py                                  # API call tracking helpers
│       └── logging.py                                        # Logging utilities
│
├── core/                                                     # Core inference and search logic
│   ├── __init__.py
│   ├── milvus_search.py                                      # Milvus vector search operations
│   ├── models_config.py                                      # LLM model configuration
│   ├── read_prompt.py                                        # Prompt template loading
│   ├── usage_stats_logging.py                                # Usage statistics logging
│   │
│   ├── clients/                                              # External API clients
│   │   ├── __init__.py
│   │   ├── inference_api_client.py                           # OpenRouter API client
│   │   └── vufind_api_client.py                              # VuFind API client
│   │
│   ├── inference/                                            # LLM inference modules
│   │   ├── __init__.py
│   │   ├── base.py                                           # Core perform_inference function
│   │   ├── embeddings.py                                     # Embedding generation
│   │   ├── search_intent.py                                  # Search intent analysis
│   │   ├── facettes.py                                       # Facet extraction
│   │   ├── expand.py                                         # Query expansion
│   │   ├── reranker.py                                       # Result reranking
│   │   ├── query_quality.py                                  # Quality assessment
│   │   └── logical_tree.py                                   # Boolean tree building
│   │
│   ├── prompts/                                              # System prompts for LLM tasks
│   │   ├── system_prompt_expand.md                           # Query expansion prompt
│   │   ├── system_prompt_extract_facettes.md                 # Facet extraction prompt
│   │   ├── system_prompt_map_keyword.md                      # Keyword mapping prompt
│   │   ├── system_prompt_query_quality.md                    # Quality assessment prompt
│   │   ├── system_prompt_reranker_search.md                  # Search reranking prompt
│   │   ├── system_prompt_reranker_vocabulary.md              # Vocabulary reranking prompt
│   │   ├── system_prompt_search_intent.md                    # Search intent prompt
│   │   └── user_prompt_expand_search_question.md             # Search question user prompt
│   │
│   └── schemas/                                              # Inference response schemas
│       ├── __init__.py
│       ├── types.py                                          # Shared type definitions
│       ├── expand.py                                         # Query expansion schemas
│       ├── facettes.py                                       # Facet extraction schemas
│       ├── logical_tree.py                                   # Boolean tree schemas
│       ├── query_quality.py                                  # Quality assessment schemas
│       ├── reranker.py                                       # Reranking schemas
│       └── search_intent.py                                  # Search intent schemas
│
├── metadata/                                                 # Authority data processing
│   ├── BK/                                                   # Basisklassifikation data
│   │   ├── bk__default.jskos.jsonld                          # BK JSKOS format
│   │   ├── bk_parsed_records.json                            # Parsed BK records
│   │   ├── bk.csv                                            # BK CSV export
│   │   ├── FULL_FLOW_bk.py                                   # BK data processing pipeline
│   │   └── README_bk.md                                      # BK data documentation
│   └── GND/                                                  # GND authority data
│       ├── Geografika/                                       # GND geographical entities
│       │   ├── authorities-gnd-geografika_dnbmarc.mrc.xml    # Source MARC data
│       │   ├── convert_gnd_geografika_to_csv.sh              # CSV conversion script
│       │   ├── FULL_FLOW_gnd_geografika.py                   # GND Geografika pipeline
│       │   ├── gnd-geografika.csv                            # GND Geografika CSV
│       │   └── README_gnd_geografika.md                      # GND Geografika documentation
│       └── Sachbegriffe/                                     # GND subject headings
│           ├── authorities-gnd-sachbegriff_dnbmarc.mrc.xml   # Source MARC data
│           ├── convert_gnd_sachbegriffe_to_csv.sh            # CSV conversion script
│           ├── convert_gnd_sachgruppen_to_csv.py             # Sachgruppen conversion
│           ├── FULL_FLOW_gnd_sachbegriffe.py                 # GND processing pipeline
│           ├── gnd-sachbegriffe.csv                          # GND subject headings CSV
│           ├── gnd-sachbegriffe-systematik.csv               # GND systematics CSV
│           ├── gnd-sachgruppen.csv                           # GND groups CSV
│           ├── gnd-sachgruppen.ttl                           # GND groups TTL format
│           ├── merge_gnd_saz.py                              # Merge SAZ data
│           └── README_gnd_sachbegriffe.md                    # GND data documentation
│
├── scripts/                                                  # Utility scripts
│   └── initialize_databases.py                               # Initialize Milvus databases
│
├── tests/                                                    # Test suite
│   ├── access_test.py                                        # API access test
│   ├── api_endpoints_test.py                                 # API endpoints test
│   ├── milvus_recall_quality_test.py                         # Milvus recall quality test
│   ├── test_auto_block_safe_ips.py                           # Auto IP blocking test
│   ├── test_corpus_qe.py                                     # Query expansion corpus test
│   ├── vufind_api_proxy_test.py                              # VuFind proxy test
│   ├── access_tests/                                         # Access test results
│   └── milvus_tests/                                         # Milvus test data
│
├── databases/                                                # Generated Milvus databases
│   ├── bk.db                                                 # BK vector database
│   ├── gnd_saz_head.db                                       # GND-SAZ head database
│   ├── gnd_saz_desc.db                                       # GND-SAZ description database
│   ├── gnd_geo.db                                            # GND-GEO vector database
│   └── query_embedding_cache.pkl                             # Query embedding cache
│
└── docs/                                                     # Documentation
    ├── 00_overview.md                                        # Project overview
    ├── 01_system_architecture.md                             # System architecture
    ├── 02_codebase_structure.md                              # Codebase structure
    ├── 03_feature_inventory.md                               # Feature inventory
    ├── 04_api_endpoints.md                                   # API endpoints reference
    ├── 05_technical_details.md                               # Technical details
    ├── 06_user_workflows.md                                  # User workflows
    └── 07_config_and_running.md                              # Configuration guide
```

### Module Responsibilities

| Module | Responsibility | Public API |
|--------|---------------|-----------|
| `app/main.py` | HTTP server, middleware, routing | FastAPI app instance |
| `app/dependencies.py` | Service instantiation and access | `get_milvus_service()`, etc. |
| `app/services/transformation_service.py` | Orchestrates query transformation pipeline | `transform_query()` |
| `app/services/milvus_service.py` | Vector database operations | `search_bk()`, `search_gnd_*()` |
| `core/milvus_search.py` | Low-level Milvus operations | `Milvus_Search` class |
| `core/inference/base.py` | LLM inference abstraction | `perform_inference()` |
| `core/inference/embeddings.py` | Embedding generation | `EmbeddingFunction` class |