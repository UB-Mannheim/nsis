# BK (Basisklassifikation)

## Running the Script

```bash
uv run python metadata/BK/FULL_FLOW_bk.py
```

The script is interactive and will prompt you at each step. Press Enter to continue or 's' to skip a step.

## Data Flow

### Downloads
- **bk__default.jskos.jsonld** — BK classification data from dante.gbv.de

### Created Files
- **bk_parsed_records.json** — Intermediate parsed records (JSON)
- **bk.csv** — Final converted BK classification data

### Processing Steps
1. Download BK JSON-LD data
2. Parse JSON-LD and extract valid records (notation, label, scopeNote)
3. Generate LLM descriptions for each record
4. Export to CSV