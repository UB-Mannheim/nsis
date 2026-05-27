## Technical Details

### Model Configuration

All LLM models are configured in `core/models_config.py`:

| Task | Default Model | Temperature |
|------|--------------|-------------|
| Search Intent | `google/gemini-3.1-flash-lite` | 0.2 |
| Facet Extraction | `openai/gpt-5.4-mini` | 0.0 |
| Query Expansion | `google/gemini-3.1-flash-lite` | 0.1 |
| Reranking | `google/gemini-3.1-flash-lite` | 0.2 |
| Logical Tree | `google/gemini-3.1-flash-lite` | 0.2 |
| Query Quality | `google/gemini-3.1-flash-lite` | 0.0 |
| Embeddings | `qwen/qwen3-embedding-8b` | - |

**Provider Routing:**
- Embeddings: `price` (lowest cost)
- General LLM: `latency` (fastest response)

### Caching Strategy

| Cache | Location | Size | Purpose |
|-------|----------|------|---------|
| Query Embeddings | `databases/query_embedding_cache.pkl` | 16,384 entries | Avoid duplicate encoding |
| Milvus Collections | Memory | N/A | Loaded on startup, warmed up |

**Embeddings Cache Features:**
- LRU eviction policy
- Persisted to disk on shutdown
- Loaded on startup
- Thread-safe with asyncio locks

### Rate Limiting Configuration

| Endpoint Type | Limit | Rationale |
|--------------|-------|-----------|
| Vocabulary/Structuring | 50/min | Light operations |
| Query Processing | 20/min | LLM inference heavy |
| VuFind Search | 30/min | External API dependency |
| Quality Assessment | 30/min | LLM inference heavy |

### Auto IP Blocking Configuration

The system includes automatic bot detection and blocking based on IP behavior with tiered (exponential backoff) blocking durations:

| Configuration | Default | Description |
|--------------|--------|-------------|
| `auto_block_enabled` | `true` | Enable/disable auto blocking |
| `auto_block_threshold` | `10.0` | Violation score threshold to trigger block |
| `auto_block_window_minutes` | `60` | Time window for tracking violations |
| `auto_block_rate_violations_weight` | `5` | Weight for rate limit violations |
| `auto_block_errors_weight` | `2` | Weight for error responses (4xx/5xx) |
| `auto_block_request_volume_weight` | `500` | Weight for excessive request volume |

**Tiered Blocking Durations:**
| Block Count | Duration |
|-------------|----------|
| 1st | 1 minute |
| 2nd | 2 minutes |
| 3rd | 4 minutes |
| 4th | 8 minutes |
| ... | (doubles each time) |

If an IP gets new offenses during a block, it gets re-blocked with an incremented block count. Block count resets to 0 after `auto_block_window_minutes` (60 minutes) of no new offenses.

**Violation Score Calculation:**
```
score = rate_violations × 5 + error_count × 2 + volume_penalties × 500
```
When the score reaches `auto_block_threshold`, the IP is automatically blocked.

**Safe IP Ranges:**
Use `SAFE_IP_RANGES` to whitelist IP ranges that should never be auto-blocked:
```
SAFE_IP_RANGES=192.168.0.0/24,13.13.13.13/0
```
Supports both IPv4 and IPv6 in CIDR notation (comma-separated).

### Security Configuration

#### SSRF Protection

The VuFind API client implements Server-Side Request Forgery (SSRF) protection:

| Feature | Description |
|---------|-------------|
| Domain Allowlist | Extracted from `settings.vufind_api_base_url` and `settings.vufind_base_url` |
| Subdomain Matching | Allows subdomains of configured domains |
| Scheme Validation | Only `http://` and `https://` permitted |
| Relative Paths | Allowed for internal routing |

**Protected Endpoints:**
- `/api/v1/perform-vufind-search`
- `/api/v1/query-transformation` (via VuFind)
- `/api/v1/query-quality` (via VuFind)

### Vector Database Configuration

| Database | Collection | nlist | nprobe | Metric |
|----------|------------|-------|--------|--------|
| BK | bk_alle_klassen | 128 | 4 | COSINE |
| GND-SAZ-HEAD | gnd_sachbegriffe_head | 4096 | 1 | COSINE |
| GND-SAZ-DESC | gnd_sachbegriffe_desc | 4096 | 1 | COSINE |
| GND-GEO | gnd_geografika | 4096 | 1 | COSINE |
