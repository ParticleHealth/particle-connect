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
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
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

## Cloud Mode (BigQuery)

Load the same flat data into Google BigQuery for cloud-scale analytics. Terraform provisions the dataset and tables. The same CLI loads data into BigQuery instead of PostgreSQL.

### Prerequisites

- Everything from the local Quick Start (Python 3.11+, pip)
- Google Cloud account with a project and billing enabled
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.0
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed

### 1. Install BigQuery support

The BigQuery dependency is optional. The base install works without it for local-only (PostgreSQL) users.

```bash
cd particle-flat-observatory
pip install -e ".[bigquery]"
```

This adds `google-cloud-bigquery` to your environment. Verify:

```bash
python -c "from google.cloud import bigquery; print('OK')"
```

### 2. Authenticate

The BigQuery client uses [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/application-default-credentials). For local development:

```bash
gcloud auth application-default login
```

This opens a browser to authenticate and stores credentials locally. The BigQuery client discovers them automatically -- no key files or environment variables needed.

For CI or production, set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of a service account key file:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

The `terraform/iam.tf` file creates a dedicated service account (`observatory-pipeline`) with minimum permissions (dataEditor on the dataset, jobUser on the project). You can create a key for this service account in the GCP Console.

### 3. Provision infrastructure with Terraform

Terraform creates 1 BigQuery dataset, 21 tables, 1 service account, and 2 IAM bindings.

```bash
cd terraform/
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set `project_id` to your GCP project:

```hcl
project_id   = "your-gcp-project-id"
dataset_name = "particle_observatory"
region       = "US"
```

Then initialize and apply:

```bash
terraform init
terraform plan    # Review: 1 dataset, 21 tables, 1 service account, 2 IAM bindings
terraform apply
```

Type `yes` when prompted. Terraform creates all resources and outputs the dataset ID and service account email.

**Terraform variables:**

| Variable | Default | Description |
|---|---|---|
| `project_id` | (required) | GCP project ID |
| `dataset_name` | `particle_observatory` | BigQuery dataset name |
| `region` | `US` | Dataset location |

### 4. Configure environment

Uncomment and set the BigQuery variables in your `.env` file (or copy from `.env.example`):

```bash
BQ_PROJECT_ID=your-gcp-project-id
BQ_DATASET=particle_observatory
```

`BQ_PROJECT_ID` is required. `BQ_DATASET` defaults to `particle_observatory` if not set.

### 5. Load data

```bash
particle-pipeline load --source file --target bigquery
```

Expected output is similar to local mode: record counts per table and a data quality report. The loader uses the same flat data file (`sample-data/flat_data.json` by default, or the path in `FLAT_DATA_PATH`).

Loading is idempotent: each run deletes existing rows for the patient and reinserts. Safe to re-run.

### 6. Run analytics queries

The `queries/bigquery/` directory contains 15 pre-built analytics queries organized by category:

- **clinical/** -- patient summary, active problems, medication timeline, lab results, vital sign trends, encounter history, care team
- **operational/** -- data completeness, source coverage, record freshness, data provenance, AI output summary
- **cross-cutting/** -- labs by encounter, medications by problem, procedures by encounter

**Important: default dataset for unqualified table names.** The analytics queries use unqualified table names (e.g., `FROM patients` not `FROM your-project.particle_observatory.patients`). You must set a default dataset before running them.

**Option A: BigQuery Console**

1. Navigate to your project in the [BigQuery Console](https://console.cloud.google.com/bigquery)
2. In the query editor, click **More > Query settings > Additional settings**
3. Set **Default dataset** to `particle_observatory`
4. Paste a query from `queries/bigquery/` and run it

Try the patient summary first:

```sql
-- queries/bigquery/clinical/patient_summary.sql
-- Replace the patient_id with one from your data
SELECT * FROM patients LIMIT 5;
```

**Option B: bq CLI**

Use `--dataset_id` to set the default dataset:

```bash
bq query --use_legacy_sql=false \
  --dataset_id=particle_observatory \
  < queries/bigquery/clinical/patient_summary.sql
```

Other examples:

```bash
# Active problems list
bq query --use_legacy_sql=false \
  --dataset_id=particle_observatory \
  < queries/bigquery/clinical/active_problems.sql

# Data completeness scorecard
bq query --use_legacy_sql=false \
  --dataset_id=particle_observatory \
  < queries/bigquery/operational/data_completeness.sql

# Labs correlated with encounters
bq query --use_legacy_sql=false \
  --dataset_id=particle_observatory \
  < queries/bigquery/cross-cutting/labs_by_encounter.sql
```

### 7. Tear down (optional)

To remove all BigQuery resources:

```bash
cd terraform/
terraform destroy
```

Type `yes` when prompted. This deletes the dataset, all tables, and the service account.

Tables have `deletion_protection` disabled for this accelerator. Production deployments should set `deletion_protection = true` in `main.tf`.

### Cloud Mode known limitations

- **Load job quota:** BigQuery allows 1,500 load jobs per table per day. For production with many patients, batch multiple patients per load job instead of one load job per patient.
- **Non-atomic delete+insert:** The DELETE runs as a DML query and the INSERT runs as a load job. These are not in a single transaction. Loading is idempotent (safe to re-run) but not atomic -- a failure between DELETE and INSERT leaves the patient with no rows until re-run.
- **DML concurrency:** BigQuery limits concurrent DML to 2 active + 20 queued operations per table. This is not a concern for single-user accelerator use but matters for parallel multi-patient production loads.
