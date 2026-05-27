## System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph Frontend["Frontend Layer"]
        UI[Recherche-Kompass UI]
        JS[JavaScript Client]
    end

    subgraph API["API Layer"]
        FE[FastAPI Entry Point]
        MW[Middleware Stack]
        RT[API Router v1]
    end

    subgraph Services["Service Layer"]
        TS[Transformation Service]
        MS[Milvus Service]
        VS[VuFind Service]
    end

    subgraph Inference["Inference Layer"]
        SI[Search Intent Analysis]
        FE2[Facet Extraction]
        QE[Query Expansion]
        RR[Reranking]
        QA[Quality Assessment]
        LT[Logical Tree Builder]
    end

    subgraph Data["Data Layer"]
        BK[BK Database]
        GND_HEAD[GND-SAZ-HEAD Database]
        GND_DESC[GND-SAZ-DESC Database]
        GND_GEO[GND-GEO Database]
        VF[VuFind Catalog API]
        OC[OpenRouter API]
    end

    UI --> JS
    JS --> FE
    FE --> MW
    MW --> RT
    RT --> TS
    RT --> VS
    TS --> MS
    TS --> SI
    TS --> FE2
    TS --> QE
    TS --> RR
    TS --> LT
    MS --> BK
    MS --> GND_HEAD
    MS --> GND_DESC
    MS --> GND_GEO
    VS --> VF
    SI --> OC
    FE2 --> OC
    QE --> OC
    RR --> OC
    QA --> OC
```

### Request Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as Recherche-Kompass
    participant API as FastAPI Transformation Service
    participant LLM as OpenRouter LLMs
    participant MS as FastAPI Milvus Service
    participant VF as VuFind API

    User->>UI: Enter natural language query

    UI->>API: POST /search-intent
    API->>LLM: Analyze search intent (topicSearch/knownItem/searchQuestion)
    LLM->>API:
    API->>UI: searchIntent result

    par Parallel Processing
        UI->>API: POST /query-expansion
        API->>LLM: Expand user query (intent-aware)
        LLM->>API:
        API->>API: Build logical tree
        API->>UI: Query Expansion results

        UI->>API: POST /query-transformation (intent-aware)
            API->>LLM: Extract facettes
            LLM->>API:
            API->>MS: Perform vector search in BK & GND databases
            MS->>API:
            API->>LLM: Rerank results
            LLM->>API:
            API->>API: Build logical tree
        API->>UI: Query Transformation results
    end

    UI->>API: POST /perform-vufind-search
    API->>VF: Perform VuFind Search
    VF->>API:
    API->>UI: Search results

    UI->>API: POST /query-judge-quality
    API->>LLM: Assess result quality
    LLM->>API:
    API->>UI: Quality score & assessment
```

### Query Expansion Pipeline

```mermaid
flowchart LR
    A[User Query] --> B[Generate complementary search terms]

    B --> C[Group by Semantic Concepts]
    C --> D[Positive Concepts]
    C --> E[Negative Concepts]

    D --> F[Logical Tree]
    E --> F

    F --> G[Expanded Keywords]
```

### Query Transformation Pipeline

```mermaid
flowchart LR
    A[User Query] --> C[Search Intent?]
    C -->|Known Item | Z[Short-circuit]
    C -->|Topic Search | D[Facet Extraction]
    C -->|Search Question | D

    D --> E[Media Forms]
    D --> F[Content Genres]
    D --> G[Authors]
    D --> H[Languages]
    D --> I[Date Range]
    D --> J[Topics]

    J --> K[Batch Embedding]
    K --> L[Parallel Vector Search for every topic]
    L --> M[BK Results]
    L --> N[GND Results]

    M --> O[Reranking]
    N --> O

    O --> P[Logical Tree]
    P --> Q[Final Metadata]
    Z --> Q
```

---

## Software Architecture

### Design Patterns

| Pattern | Implementation | Purpose |
|---------|----------------|---------|
| **Service Container** | `app/dependencies.py` | Dependency injection for lazy-initialized services |
| **Repository Pattern** | `core/milvus_search.py` | Abstracts database operations |
| **Pipeline Pattern** | `research-compass.js` | Sequential step execution with independent UI updates |
| **Strategy Pattern** | `core/inference/*.py` | Interchangeable inference modules |
| **Middleware Pattern** | `app/main.py` | Cross-cutting concerns (logging, CORS, IP blocking) |

### Service Dependencies

```mermaid
graph TD
    subgraph App
        Main[app/main.py]
        Deps[app/dependencies.py]
    end

    subgraph Services
        MS[MilvusService]
        VS[VuFindService]
        TS[TransformationService]
    end

    subgraph Core
        MSearch[milvus_search.py]
        Embed[embeddings.py]
        Base[inference/base.py]
        Client[InferenceAPIClient]
    end

    Main --> Deps
    Deps --> MS
    Deps --> VS
    Deps --> TS
    TS --> MS
    TS --> Base
    MS --> MSearch
    MSearch --> Embed
    Base --> Client
    Embed --> Client
```

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Request Lifecycle                            │
├─────────────────────────────────────────────────────────────────────┤
│  1. HTTP Request                                                    │
│     ↓                                                               │
│  2. Middleware Stack                                                │
│     ├── Trusted Host Validation                                     │
│     ├── IP Blocking                                                 │
│     ├── Request ID Injection                                        │
│     ├── JSON Error Catching                                         │
│     └── API Request Logging                                         │
│     ↓                                                               │
│  3. Rate Limiting (SlowAPI)                                         │
│     ↓                                                               │
│  4. Endpoint Handler                                                │
│     ↓                                                               │
│  5. Service Layer                                                   │
│     ↓                                                               │
│  6. Core Inference / Search Layer                                   │
│     ↓                                                               │
│  7. External APIs (OpenRouter, VuFind, Milvus)                      │
│     ↓                                                               │
│  8. Response Building                                               │
│     ↓                                                               │
│  9. Pydantic Validation                                             │
│     ↓                                                               │
│ 10. HTTP Response                                                   │
└─────────────────────────────────────────────────────────────────────┘
```
