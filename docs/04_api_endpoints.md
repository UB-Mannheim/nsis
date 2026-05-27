## API Endpoints Reference

### Query Processing Endpoints

| Method | Endpoint | Rate Limit | Purpose |
|--------|----------|-----------|---------|
| POST | `/api/v1/search-intent` | 20/min | Analyze search intent |
| POST | `/api/v1/query-expansion` | 20/min | Expand query with keywords |
| POST | `/api/v1/query-facettes` | 20/min | Extract faceted filters |
| POST | `/api/v1/query-transformation` | 20/min | Complete transformation pipeline |

### VuFind Integration Endpoints

| Method | Endpoint | Rate Limit | Purpose |
|--------|----------|-----------|---------|
| POST | `/api/v1/perform-vufind-search` | 30/min | Search VuFind catalog |
| POST | `/api/v1/query-judge-quality` | 30/min | Assess result quality |

### Vocabulary Endpoints

| Method | Endpoint | Rate Limit | Purpose |
|--------|----------|-----------|---------|
| POST | `/api/v1/lookup-vocabulary` | 50/min | Search authority databases |
| POST | `/api/v1/build-logical-tree` | 50/min | Build boolean search tree |
| POST | `/api/v1/add-keyword-to-concepts` | 50/min | Map keyword to concepts |

### Information Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Research Compass HTML interface (default landing page) |
| GET | `/api` | API root with version info |
| GET | `/research-compass` | Redirects to root (/) |
| GET | `/health` | Service health status with individual service checks |
| GET | `/docs` | Swagger UI documentation |

