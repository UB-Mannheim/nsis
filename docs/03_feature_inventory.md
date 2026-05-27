## Feature Inventory

### 1. Search Intent Detection

**Purpose:** Analyze user queries to determine the search intent type.

**Supported Intents:**
- `topicSearch` - Exploratory research on a topic
- `knownItem` - Finding a specific known item (short-circuit for known-item searches)
- `searchQuestion` - Research question seeking specific answers

**Used By:**
- Query Expansion: Adapts expansion strategy based on intent
- Query Transformation: Optimizes transformation pipeline based on intent

### 2. Query Expansion

**Purpose:** Expand user queries with related keywords for improved recall.

**Features:**
- Groups related terms by semantic concepts
- Identifies negated terms (NOT clauses)
- Returns both positive and negative keyword concepts

**Input Parameters:**
- `query`: Natural language search query
- `search_intent` (optional): Pre-detected search intent (if not provided, fallback to topicSearch)

### 3. Query Transformation

**Purpose:** Transform natural language queries into structured VuFind search parameters.

**Process:**
1. Analyze search intent (topic search vs. known-item search vs. search question)
2. Extract faceted filters (media forms, genres, authors, languages, dates)
3. Identify topical concepts in original and English translation
4. Vector search across BK, GND-SAZ (subject headings), and GND-GEO (geographical entities) databases
5. LLM-based reranking of search results
6. Build logical tree with AND/OR/NOT relationships

**Input Parameters:**
- `query`: Natural language search query
- `search_intent` (optional): Pre-detected search intent (if not provided, auto-detected)

**Output Metadata:**
```json
{
  "searchIntent": "topicSearch",
  "filters": {
    "mediaForms": [...],
    "contentGenres": [...],
    "authorNames": [...],
    "languages": [...]
  },
  "gndHeadingsConcepts": {"concept_1": [...], "concept_2": [...]},
  "bkNotations": [...],
  "dateRange": {"from": 2000, "to": 2025},
  "logicalTree": {...}
}
```


### 4. Vocabulary Lookup

**Purpose:** Search authority databases for matching terms.

**Supported Vocabularies:**
- `bk` - Basisklassifikation classification codes
- `gnd-saz` - GND subject headings (searches both head and description)
- `gnd-geo` - GND Geografika (geographical entities)

**Input Parameters:**
- `term` (required): The search term
- `vocabulary` (required): The vocabulary to search in (`bk`, `gnd-saz`, or `gnd-geo`)
- `limit` (optional): Maximum number of results (default: 10, max: 50)

### 5. Query Quality Assessment

**Purpose:** Evaluate search result relevance using LLM.

**Features:**
- Configurable output language (German/English)
- Quality score (0.0 - 1.0)
- Human-readable assessment (language-aware)
- List of relevant title indices

**Input Parameters:**
- `query` (required): The original natural language search query
- `url` (required): The VuFind search URL to evaluate
- `titles` (optional): Pre-fetched VuFind titles to use instead of fetching from the URL
- `output_language` (optional): Language for assessment output (`"de"` for German, default) or `"en"` (English)

### 6. VuFind Integration

**Purpose:** Proxy searches to VuFind catalog and return results.

**Features:**
- URL conversion (web → API format)
- Result count retrieval
- Title metadata extraction
- Result preview with formatting

**Input Parameters:**
- `url` (required): The VuFind search URL
- `limit` (optional): Maximum number of titles to retrieve (default: 10, max: 50)

### 7. Research Compass UI

**Purpose:** Web-based interface for end users.

**Components:**
- Search input with debounced fetch
- Search history (localStorage persistence)
- Pipeline status indicators
- Generated URL preview with syntax highlighting
- Options panel (toggleable filters/keywords)
- Results section with quality scores
- About popup with feature descriptions
- Language toggle (DE/EN) with localStorage persistence

**i18n Features:**
- All UI strings (labels, placeholders, tooltips) support German and English
- Language preference persisted to localStorage
- Dynamic label updates for options without full page reload
- English translations for: OPTIONS_CONFIG, CATEGORY_LABELS, MEDIA_FORM_LABELS, LANGUAGE_LABELS
