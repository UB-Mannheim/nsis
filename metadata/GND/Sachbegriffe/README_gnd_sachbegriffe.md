# GND Sachbegriffe

## Running the Script

```bash
uv run python metadata/GND/Sachbegriffe/FULL_FLOW_gnd_sachbegriffe.py
```

The script is interactive and will prompt you at each step. Press Enter to continue or 's' to skip a step.

## Data Flow

### Downloads
- **authorities-gnd-sachbegriff_dnbmarc.mrc.xml** — GND authority data (Sachbegriffe) from dnb.de
- **gnd-sachgruppen.ttl** — GND subject categories vocabulary from d-nb.info

### Created Files
- **gnd-sachbegriffe.csv** — Converted GND Sachbegriffe data
- **gnd-sachgruppen.csv** — Converted GND subject categories

### Processing Steps
1. Download and extract GND Sachbegriffe authority data
2. Download GND Sachgruppen TTL vocabulary
3. Convert Sachbegriffe MARC data to CSV
4. Convert Sachgruppen TTL to CSV
5. Merge GND data into final output