# nsis - Natürlichsprachige Suche im StabiKat

## System Overview

**Version:** 1.0.0
**Last Updated:** May 18, 2026
**Repository:** nsis (Natürlichsprachige Suche im StabiKat)

---

## Table of Contents

1. [Short Summary](#short-summary)
2. [System Architecture](01_system_architecture.md#system-architecture)
3. [Software Architecture Analysis](01_system_architecture.md#software-architecture-analysis)
4. [Codebase Structure](02_codebase_structure.md#codebase-structure)
5. [Feature Inventory](03_feature_inventory.md#feature-inventory)
6. [API Endpoints Reference](04_api_endpoints.md#api-endpoints-reference)
7. [Technical Insights](05_technical_details.md#technical-details)
8. [User Workflows](06_user_workflows.md#user-workflows)
9. [Configuration and Running the API](07_config_and_running.md#configuration-and-running-the-api)

---

## Modular Documentation

This overview has been split into modular documentation files for easier maintenance and context management. Each file contains a complete section and can be read independently.

| Section | File | Description |
|---------|------|-------------|
| Executive Summary | [00_overview.md](00_overview.md) | Project purpose and capabilities |
| System Architecture | [01_system_architecture.md](01_system_architecture.md) | High-level architecture, flows, diagrams |
| Software Architecture | [01_system_architecture.md](01_system_architecture.md) | Design patterns, service dependencies |
| Codebase Structure | [02_codebase_structure.md](02_codebase_structure.md) | Directory organization and module responsibilities |
| Feature Inventory | [03_feature_inventory.md](03_feature_inventory.md) | All system features and their details |
| API Endpoints | [04_api_endpoints.md](04_api_endpoints.md) | Complete API endpoint reference |
| Technical Details | [05_technical_details.md](05_technical_details.md) | Model config, caching, rate limits |
| User Workflows | [06_user_workflows.md](06_user_workflows.md) | Main search and keyword addition workflows |
| Configuration Guide | [07_config_and_running.md](07_config_and_running.md) | Environment, app, and frontend configuration |

---

## Short Summary

### Project Purpose

nsis (Natürlichsprachige Suche im StabiKat) is a FastAPI-based natural language search enhancement system designed to improve discovery in VuFind library catalogs, specifically integrating with StabiKat, the VuFind catalog used by the Staatsbibliothek zu Berlin.

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Natural Language Processing** | Transforms user queries in natural language into structured search parameters |
| **Multi-Vocabulary Search** | Searches across BK (Basisklassifikation), GND-SAZ (GND Sachbegriffe), and GND-GEO (GND Geografika) authority databases |
| **Faceted Search** | Extracts and applies filters (media types, genres, languages, authors, date ranges) |
| **Intelligent Expansion** | Expands queries with related terms for improved recall |
| **Quality Assessment** | Evaluates search result relevance and provides feedback |
| **Logical Tree Building** | Constructs boolean search trees (AND/OR/NOT) from concepts |

### Key Technologies

- **Framework:** FastAPI 0.104+ with Uvicorn
- **Vector Database:** Milvus Lite (local SQLite-based)
- **LLM Provider:** OpenRouter API (20+ model support)
- **Embedding Model:** Qwen/Qwen3-Embedding-8B
- **Frontend:** Vanilla JavaScript SPA (Recherche-Kompass)
- **Python Version:** 3.14+

---