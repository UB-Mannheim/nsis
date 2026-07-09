## Configuration and Running the API

### Configuration Requirements

To run the application, configure the following files:

#### 1. Environment Variables (`.env`)

Copy from `.env.sample` and configure:

```bash
cp .env.sample .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `INFERENCE_PROVIDER_BASE_URL` | OpenRouter API endpoint | `https://openrouter.ai/api/v1` |
| `INFERENCE_PROVIDER_API_KEY` | Your OpenRouter API key | `<your-api-key-here>` |
| `VUFIND_BASE_URL` | Public VuFind instance URL | - |
| `VUFIND_API_BASE_URL` | VuFind API endpoint | - |
| `VUFIND_API_TOKEN` | Token sent with outbound VuFind API requests | (empty) |
| `VUFIND_API_TOKEN_HEADER` | Header name for the VuFind API token | `X-API-KEY` |
| `HOST` | Server bind IP | - |
| `PORT` | Server bind port | - |
| `DOMAIN` | Public domain (e.g., `https://kompass.vufind.de`) | - |

**Optional IP Blocking Configuration:**

| Variable | Description | Default |
|----------|-------------|---------|
| `BLOCKED_IPS` | Comma-separated IPs to block | (empty) |
| `BLOCKED_IP_RANGES` | Comma-separated CIDR ranges | (empty) |
| `SAFE_HOSTS` | Comma-separated hostnames where auto blocking is disabled | (empty) |
| `SAFE_IP_RANGES` | Comma-separated CIDR ranges of safe IPs that should never be auto-blocked | (empty) |
| `AUTO_BLOCK_ENABLED` | Enable automatic bot detection | `true` |
| `AUTO_BLOCK_THRESHOLD` | Violation score to trigger block | `10.0` |
| `AUTO_BLOCK_WINDOW_MINUTES` | Time window for tracking violations | `60` |
| `AUTO_BLOCK_RATE_VIOLATIONS_WEIGHT` | Weight for rate limit violations | `5` |
| `AUTO_BLOCK_ERRORS_WEIGHT` | Weight for error responses (4xx/5xx) | `2` |
| `AUTO_BLOCK_REQUEST_VOLUME_WEIGHT` | Weight for excessive request volume | `500` |

**Note:** Block duration uses tiered (exponential backoff) blocking: 1min → 2min → 4min → 8min... based on block count.

#### 2. Application Settings (`app/config.py`)

Copy from `app/config.py.sample` and configure:

```bash
cp app/config.py.sample app/config.py
```

**API Configuration:**
| Setting | Description | Default |
|---------|-------------|---------|
| `api_title` | API title | `API_TITLE` |
| `api_version` | API version | `1.0.0` |
| `api_description` | API description | `API_DESCRIPTION` |
| `api_prefix` | API URL prefix | `/api` |
| `root_path` | Nginx proxy prefix | `/nsis` |
| `supported_versions` | Supported API versions | `["v1"]` |

**CORS Configuration:**
| Setting | Description | Default |
|---------|-------------|---------|
| `cors_origins` | Allowed CORS origins | `["*"]` |

**Server Configuration:**
| Setting | Description | Default |
|---------|-------------|---------|
| `host` | Server bind IP (from .env) | (empty) |
| `port` | Server bind port (from .env) | `8000` |
| `domain` | Public domain (from .env) | (empty) |

**Inference Provider:**
| Setting | Description | Default |
|---------|-------------|---------|
| `inference_provider_base_url` | OpenRouter API URL (from .env) | (empty) |
| `inference_provider_api_key` | API key (from .env) | (empty) |

**Milvus Configuration:**
| Setting | Description | Default |
|---------|-------------|---------|
| `milvus_device` | Device for embeddings | `cpu` |
| `milvus_bk_csv_path` | BK database CSV path | `./metadata/BK/bk.csv` |
| `milvus_bk_db_path` | BK vector database path | `./databases/bk.db` |
| `milvus_gnd_saz_head_csv_path` | GND-SAZ-HEAD CSV path | `./metadata/GND/Sachbegriffe/gnd-sachbegriffe-systematik.csv` |
| `milvus_gnd_saz_head_db_path` | GND-SAZ-HEAD database path | `./databases/gnd_saz_head.db` |
| `milvus_gnd_saz_desc_csv_path` | GND-SAZ-DESC CSV path | `./metadata/GND/Sachbegriffe/gnd-sachbegriffe-systematik.csv` |
| `milvus_gnd_saz_desc_db_path` | GND-SAZ-DESC database path | `./databases/gnd_saz_desc.db` |
| `milvus_gnd_geo_csv_path` | GND-GEO CSV path | `./metadata/GND/Geografika/gnd-geografika.csv` |
| `milvus_gnd_geo_db_path` | GND-GEO database path | `./databases/gnd_geo.db` |

**VuFind Configuration:**
| Setting | Description | Default |
|---------|-------------|---------|
| `vufind_base_url` | Public VuFind URL | (empty) |
| `vufind_api_base_url` | VuFind API URL | (empty) |
| `vufind_api_token` | Token sent to VuFind API from `.env` as `VUFIND_API_TOKEN`; empty sends no auth header | (empty) |
| `vufind_api_token_header` | Header name used for the VuFind API token | `X-API-KEY` |

**Content Security Policy:**
| Setting | Description | Default |
|---------|-------------|---------|
| `csp_fonts_domain` | Font CDN domain | `https://fonts.bunny.net` |
| `csp_icons_domain` | Icon CDN domain | `https://unpkg.com` |
| `csp_vufind_domain` | VuFind domain | (empty) |
| `csp_institution_domain` | Institution domain | (empty) |

**Logging Configuration:**
| Setting | Description | Default |
|---------|-------------|---------|
| `log_level` | Log level | `INFO` |
| `log_dir` | Log directory | (empty) |
| `logger_name` | Logger name | (empty) |

#### 3. Frontend Settings (`app/static/research-compass-settings.js`)

Configure the following configuration objects:

**CONFIG** - Application settings:
```javascript
const CONFIG = {
    // API_BASE_URL is derived from current website location
    API_BASE_URL: (window.location.origin) + '/nsis/api/v1',
    VUFIND_BASE_URL: '<your-vufind-url>',
    MAX_HISTORY: 5,
    FETCH_DEBOUNCE_MS: 800,
    LOCAL_STORAGE_KEY: 'research-compass-history',
    LOCAL_STORAGE_KEY_SETTINGS: 'research-compass-settings',
    SHOW_DEBUG_PANEL: false,
    UI_LANGUAGE: 'de'
};
```

**VUFIND_PARAMS** - VuFind-specific URL parameters and search constants:
```javascript
const VUFIND_PARAMS = {
    // URL Configuration
    SEARCH_PATH: '/Search/Results',

    // Search Type Constants
    SEARCH_TYPE_ALL_FIELDS: 'AllFields',
    SEARCH_TYPE_SUBJECT: 'Subject',

    // Filter Field Prefixes (for ~field:"value" syntax)
    FILTER_FORMAT: '~format',
    FILTER_FORMAT_DETAILS: '~format_details_str_mv',
    FILTER_LANGUAGE: '~language',
    FILTER_AUTHOR: '~author_facet',
    FILTER_BK: '~bklnumber',

    // URL Parameter Names
    PARAM_LOOKFOR: 'lookfor',
    PARAM_TYPE: 'type',
    PARAM_BOOL: 'bool',
    PARAM_JOIN: 'join',
    PARAM_FILTER_ARRAY: 'filter[]',
    PARAM_DATERANGE_ARRAY: 'daterange[]',
    PARAM_PUBLISH_DATE: 'publishDate',
    PARAM_PUBLISH_DATE_FROM: 'publishDatefrom',
    PARAM_PUBLISH_DATE_TO: 'publishDateto',

    // Boolean Operators
    BOOL_AND: 'AND',
    BOOL_OR: 'OR',
};
```

**UI_STRINGS** / **UI_STRINGS_EN** - All UI labels and messages (i18n)
- `UI_STRINGS`: German translations
- `UI_STRINGS_EN`: English translations
- `getStrings()`: Returns current language strings based on `CONFIG.UI_LANGUAGE`

**UI_ELEMENTS** - Image URLs, external resources, and links:
- `logoSrc`, `footerLogoSrc`, `faviconSrc`
- `fontsUrl`, `iconsUrl`
- `institutionUrl`, `privacyUrl`, `imprintUrl`
- Search example icons and option icons

**OPTIONS_CONFIG** / **OPTIONS_CONFIG_EN** - Search option category configuration:
- `keyword`: Suchbegriffe / Keywords
- `topic_facet`: Themen / Topics
- `bklnumber`: Themenbereiche / Subject Areas
- `format`: Medientyp / Media Type
- `format_details`: Inhaltsgenre / Content Genre
- `language`: Sprache / Language
- `author_facet`: Autor / Author
- `date`: Erscheinungsdatum / Publication Date

**OPTIONS_ORDER** - Display order of option categories

**CATEGORY_LABELS** / **CATEGORY_LABELS_EN** - Display labels for option badges

**MEDIA_FORM_LABELS** / **MEDIA_FORM_LABELS_EN** - Labels for media form values (Article, Book, eBook, etc.)

**LANGUAGE_LABELS** / **LANGUAGE_LABELS_EN** - Labels for language codes

**Language Toggle:**
- Users can switch between German (DE) and English (EN) via header links
- Language preference is persisted to localStorage
- `getLanguage()` reads preference; `saveLanguage()` persists it

### Quick Start Commands

#### 1. Setup
```bash
uv sync
cp .env.sample .env
cp app/config.py.sample app/config.py
```

#### 2. Configure settings
Edit the following files:
- `.env` - Your API key + host, port and domain
- `app/config.py` - API title/version and CSP domains
- `app/static/research-compass-settings.js` - VuFind and UI Settings

#### 3. Build BK Database CSV
```bash
uv run python metadata/BK/FULL_FLOW_bk.py
```

#### 4. Build GND-SAZ Database CSVs
```bash
uv run python metadata/GND/Sachbegriffe/FULL_FLOW_gnd_sachbegriffe.py
```

#### 5. Build GND-Geografika Database CSV
```bash
uv run python metadata/GND/Geografika/FULL_FLOW_gnd_geografika.py
```

#### 6. Build vector databases (requires OpenRouter API key)
```bash
uv run python scripts/initialize_databases.py --all
```

#### 7. Run server
```bash
uv run python -m app.main
```

#### 8. Test API locally against the running server (optional)
```bash
uv run python tests/access_test.py
```

#### Access (after deployment)

Assuming .env has HOST=0.0.0.0, PORT=8000, DOMAIN=your-domain set:
- API docs: http://localhost:8000/api (or http://localhost:8000/docs for Swagger UI)
- UI: http://localhost:8000/ (Recherche-Kompass is now the default landing page)
- Production: http://your-domain/
