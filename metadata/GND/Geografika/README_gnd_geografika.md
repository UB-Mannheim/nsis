# GND Geografika

## Running the Script

```bash
uv run python metadata/GND/Geografika/FULL_FLOW_gnd_geografika.py
```

The script is interactive and will prompt you at each step. Press Enter to continue or 's' to skip a step.

## Data Flow

### Downloads
- **authorities-gnd-geografika_dnbmarc.mrc.xml** — GND authority data (Geografika) from dnb.de

### Created Files
- **gnd-geografika.csv** — Converted GND Geografika data

### Processing Steps
1. Move to metadata/GND/Geografika directory
2. Download and extract GND Geografika authority data
3. Convert Geografika MARC data to CSV
