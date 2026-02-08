# Particle Flat Data Observatory

Load Particle Health flat data into a local PostgreSQL database and explore it with SQL.

Takes a `flat_data.json` response from the Particle Health API, normalizes it into relational tables, and loads everything into PostgreSQL. You get structured, queryable data in a single command.

## Quick Start

### Prerequisites

- Docker (for PostgreSQL)
- Python 3.11+
- pip

### 1. Install the package

```bash
cd particle-flat-observatory
pip install -e .
```

### 2. Start PostgreSQL

```bash
docker compose up -d
```

Tables are created automatically on first startup from `ddl/postgres/create_all.sql`.

Wait for the database to be healthy:

```bash
docker compose ps
```

### 3. Load sample data

```bash
particle-pipeline load
```

This loads the included sample data (`sample-data/flat_data.json`) into PostgreSQL. After loading, a data quality report shows record counts, null percentages, and date ranges per table.

### 4. Query your data

Connect to PostgreSQL:

```bash
docker compose exec postgres psql -U observatory -d observatory
```

Run some queries:

```sql
SELECT given_name, family_name, date_of_birth, gender FROM patients;

SELECT lab_name, lab_value, lab_unit, lab_timestamp FROM labs LIMIT 10;

SELECT condition_name, condition_clinical_status FROM problems;

SELECT encounter_type_name, encounter_start_time, encounter_end_time FROM encounters;

SELECT medication_name, medication_statement_status FROM medications;
```

Exit psql with `\q`.

## Configuration

Copy `.env.example` to `.env` to customize settings. CLI flags override environment variables.

| Variable | Default | Description |
|---|---|---|
| `FLAT_DATA_PATH` | `sample-data/flat_data.json` | Path to Particle flat data JSON file |
| `PG_HOST` | `localhost` | PostgreSQL host |
| `PG_PORT` | `5432` | PostgreSQL port |
| `PG_USER` | `observatory` | PostgreSQL user |
| `PG_PASSWORD` | `observatory` | PostgreSQL password |
| `PG_DATABASE` | `observatory` | PostgreSQL database name |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

If you already have PostgreSQL running on port 5432, set `PG_PORT` to another value (e.g., `5433`) in both `.env` and when starting Docker:

```bash
PG_PORT=5433 docker compose up -d
```

## Loading Your Own Data

Replace the sample data file or point to a different path:

```bash
particle-pipeline load --data-path /path/to/your/flat_data.json
```

Or set the environment variable:

```bash
export FLAT_DATA_PATH=/path/to/your/flat_data.json
particle-pipeline load
```

Data is loaded idempotently: re-running the command replaces existing records per patient. It is safe to run multiple times.

## CLI Reference

```
particle-pipeline load                                    # Load flat data into PostgreSQL
particle-pipeline load --help                             # Show all options
particle-pipeline load --source file --target postgres    # Explicit mode (default)
particle-pipeline load --data-path /path/to/data.json     # Custom data file
particle-pipeline load --verbose                          # Enable debug logging
```

## Resetting the Database

To destroy all data and recreate tables from scratch:

```bash
docker compose down -v && docker compose up -d
```

The `-v` flag removes the PostgreSQL data volume. On next startup, the init script (`create_all.sql`) runs again because the data directory is empty.

When to reset:
- After changing DDL files in `ddl/postgres/`
- To start fresh with no loaded data
- To recover from a corrupted database state

## Project Structure

```
particle-flat-observatory/
  compose.yaml              # PostgreSQL Docker service
  pyproject.toml            # Python package config and dependencies
  .env.example              # Environment variable template
  ddl/
    postgres/
      create_all.sql        # Table definitions (auto-loaded by Docker)
  sample-data/
    flat_data.json          # Sample Particle flat data response
  src/observatory/
    cli.py                  # Typer CLI entry point (particle-pipeline command)
    parser.py               # JSON parser for flat_data.json
    normalizer.py           # Empty string -> None normalization
    schema.py               # Schema inspector (discovers columns per resource)
    ddl.py                  # DDL generator (PostgreSQL and BigQuery)
    loader.py               # PostgreSQL loader (idempotent per-patient writes)
    quality.py              # Data quality analysis and Rich table report
    config.py               # Settings and environment variable loading
  tests/                    # Unit tests (no database required)
```

## What Gets Loaded

The sample data contains 1,187 records across 16 resource types:

| Resource Type | Table Name | Records | Columns |
|---|---|---|---|
| aICitations | ai_citations | 542 | 7 |
| recordSources | record_sources | 307 | 5 |
| vitalSigns | vital_signs | 116 | 12 |
| labs | labs | 111 | 22 |
| documentReferences | document_references | 51 | 10 |
| aIOutputs | ai_outputs | 22 | 6 |
| medications | medications | 6 | 18 |
| sources | sources | 6 | 3 |
| encounters | encounters | 5 | 13 |
| problems | problems | 5 | 14 |
| organizations | organizations | 4 | 12 |
| practitioners | practitioners | 4 | 20 |
| procedures | procedures | 4 | 14 |
| transitions | transitions | 2 | 36 |
| locations | locations | 1 | 11 |
| patients | patients | 1 | 15 |

Five resource types are empty in the sample data (no records): allergies, coverages, familyMemberHistories, immunizations, and socialHistories. Their tables are not created until data is available.
