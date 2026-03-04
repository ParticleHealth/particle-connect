# Analytics Pipeline

The `particle-analytics-quickstarts/` project loads Particle Health flat data into DuckDB (local) or BigQuery (cloud) for SQL analytics.

## Architecture

```
flat_data.json → parser → normalizer → schema discovery → DDL generation → loader → DuckDB/BigQuery
                                                                                 → quality report
```

### Source Modules (`src/observatory/`)

| Module | Purpose |
|--------|---------|
| `cli.py` | Typer CLI entry point — `particle-pipeline` command |
| `parser.py` | Parses flat_data.json into resource-type groups |
| `normalizer.py` | Converts empty strings to None |
| `schema.py` | Discovers columns per resource type from data |
| `ddl.py` | Generates CREATE TABLE DDL (DuckDB, PostgreSQL, BigQuery) |
| `loader.py` | DuckDB loader — idempotent per-patient (DELETE + INSERT) |
| `bq_loader.py` | BigQuery loader — idempotent per-patient |
| `quality.py` | Data quality analysis with Rich table output |
| `config.py` | Settings from .env (FLAT_DATA_PATH, DUCKDB_PATH, BQ_*) |
| `api_client.py` | HTTP client for fetching data from Particle API |

## CLI Commands

```bash
particle-pipeline                                  # Load file → DuckDB (default)
particle-pipeline --source file --target duckdb    # Explicit default mode
particle-pipeline --source file --target bigquery  # Load file → BigQuery
particle-pipeline --data-path /path/to/data.json   # Custom data file
particle-pipeline --verbose                        # Debug logging
particle-pipeline --help                           # Show all options
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| FLAT_DATA_PATH | `sample-data/flat_data.json` | Input data file path |
| DUCKDB_PATH | `observatory.duckdb` | DuckDB database file path |
| LOG_LEVEL | `INFO` | Logging level |
| BQ_PROJECT_ID | (required for BigQuery) | GCP project ID |
| BQ_DATASET | `particle_observatory` | BigQuery dataset name |

## Sample Data

The included `sample-data/flat_data.json` contains 1,187 records across 16 resource types:

| Resource Type | Table Name | Records | Columns |
|---------------|------------|---------|---------|
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

Empty in sample: allergies, coverages, familyMemberHistories, immunizations, socialHistories.

All columns are TEXT/STRING. Queries CAST to appropriate types.

## Pre-Built Queries (15 total)

Available in both `queries/duckdb/` and `queries/bigquery/` dialects.

### Clinical (7 queries)
| Query | Description |
|-------|-------------|
| patient_summary.sql | Demographics, active conditions, current medications |
| active_problems.sql | Current conditions with onset dates and clinical status |
| medication_timeline.sql | Medications with start/end dates, dosage, status |
| lab_results.sql | Lab values trended by date with interpretation |
| vital_sign_trends.sql | BP, heart rate, respiratory rate, O2 sat over time |
| encounter_history.sql | Chronological encounters with type, location, duration |
| care_team.sql | Practitioners with roles and specialties |

### Operational (5 queries)
| Query | Description |
|-------|-------------|
| data_completeness.sql | Record counts and field population percentages |
| source_coverage.sql | Data sources by resource type |
| record_freshness.sql | Most recent record timestamp per resource type |
| data_provenance.sql | Trace records to source documents |
| ai_output_summary.sql | AI insights with citation counts |

### Cross-Cutting (3 queries)
| Query | Description |
|-------|-------------|
| labs_by_encounter.sql | Labs ordered during encounters (temporal join) |
| medications_by_problem.sql | Medications mapped to conditions via encounters |
| procedures_by_encounter.sql | Procedures with practitioners per encounter |

## BigQuery Mode

Requires: GCP project, Terraform, gcloud CLI, `pip install -e ".[bigquery]"`

```bash
cd terraform/
cp terraform.tfvars.example terraform.tfvars  # Set project_id
terraform init && terraform apply              # Creates 1 dataset, 21 tables
particle-pipeline --source file --target bigquery
```

### Known Limitations
- 1,500 load jobs per table per day (BigQuery quota)
- DELETE + INSERT is not atomic (safe to re-run but not transactional)
- 2 concurrent + 20 queued DML operations per table
