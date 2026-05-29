# About the nsis API

A FastAPI-based API that transforms natural language queries into structured search parameters for VuFind library catalogs. It uses BK (Basisklassifikation), GND-SAZ (GND Sachbegriffe), and GND-GEO (GND Geografika) authority databases combined with LLM-powered query expansion, facet extraction, and search result reranking to improve media discovery and provide an automatic research consultation for library catalogs. The frontend ("Research Compass") is served as a Single-Page-Application (HTML+JS+CSS) by the API.

# Live Instance

Navigate to this link to test the live instance: [https://kompass.stabikat.de](https://kompass.stabikat.de)

# Docs

Detailed documentation of the nsis API lives in the `docs/` folder. Start with reading the [overview](docs/00_overview.md).

# How to run

Run command: `uv run python -m app.main`

# Setup

1. Setup the `uv` toolchain and perform `uv sync` to download the libraries the project depends on
2. Create .env from .env.sample
3. Create app/config.py from app/config.py.sample
4. Edit app/static/research-compass-settings.js to adapt the API to your specific VuFind configuration
    - Edit these constants to match your specific VuFind configuration: `CONFIG, UI_STRINGS, UI_ELEMENTS, OPTIONS_CONFIG, VUFIND_PARAMS, OPTIONS_ORDER, CATEGORY_LABELS, MEDIA_FORM_LABELS, LANGUAGE_LABELS` (and their _EN equivalents)
    - This step involves detailed knowledge about how your specific VuFind instance works
5. Execute `uv run metadata/BK/FULL_FLOW_bk.py` to build BK Database CSV
    - This step involves OpenRouter API costs, as content is generated for CSV construction
6. Execute `uv run metadata/GND/Sachbegriffe/FULL_FLOW_gnd_sachbegriffe.py` to build GND-SAZ Database CSVs
6. Execute `uv run metadata/GND/Geografika/FULL_FLOW_gnd_geografika.py` to build GND-GEO Database CSV
7. Initialize / build databases with `uv run python scripts/initialize_databases.py --all`
    - This step involves OpenRouter API costs, as the embeddings are generated for database construction
    - This step generates `databases/bk.db`, `databases/gnd-saz-head.db`, `databases/gnd-saz-desc.db` and `databases/gnd-geo.db`
    - This step can take some time, as we are processing ~ 700.000 items in total
8. Run FastAPI server with run command `uv run python -m app.main`
9. Edit and execute the API access test script with `uv run python tests/access_test.py` to test the API locally
    - The access test script simulates parallel accesses / research consultations in the frontend and outputs performance and cost statistics
10. Navigate to the public endpoint of the API and open "http(s)://API_DOMAIN/" to test the system for yourself
    - The exact URL depends on your (nginx) configuration