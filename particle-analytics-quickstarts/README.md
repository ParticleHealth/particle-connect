# Particle Flat Data Observatory

Load Particle Health flat data into a local DuckDB database and explore it with SQL.

Takes a `flat_data.json` response from the Particle Health API, normalizes it into relational tables, and loads everything into DuckDB. You get structured, queryable data in a single command. No Docker, no server, no connection config.

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### 1. Install the package

```bash
cd particle-flat-observatory
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Load sample data

```bash
particle-pipeline
```

This loads the included sample data (`sample-data/flat_data.json`) into a local DuckDB file (`observatory.duckdb`). Tables are created automatically. After loading, a data quality report shows record counts, null percentages, and date ranges per table.

### 3. Query your data

Run queries using the Python `duckdb` module (already installed):

```bash
python3 -c "import duckdb; conn = duckdb.connect('observatory.duckdb'); conn.sql('SELECT given_name, family_name, date_of_birth, gender FROM patients').show()"
```

More examples:

```bash
python3 -c "import duckdb; conn = duckdb.connect('observatory.duckdb'); conn.sql('SELECT lab_name, lab_value, lab_unit FROM labs LIMIT 10').show()"

python3 -c "import duckdb; conn = duckdb.connect('observatory.duckdb'); conn.sql('SELECT condition_name, condition_clinical_status FROM problems').show()"

python3 -c "import duckdb; conn = duckdb.connect('observatory.duckdb'); conn.sql('SELECT medication_name, medication_statement_status FROM medications').show()"
```

**Optional: DuckDB CLI.** For an interactive SQL shell, install the [DuckDB CLI](https://duckdb.org/docs/installation/) separately (it is not included in the pip package):

```bash
# macOS
brew install duckdb

# or any platform
curl https://install.duckdb.org | sh
```

Then connect directly:

```bash
duckdb observatory.duckdb
```

## Configuration

Copy `.env.example` to `.env` to customize settings. CLI flags override environment variables.

| Variable | Default | Description |
|---|---|---|
| `FLAT_DATA_PATH` | `sample-data/flat_data.json` | Path to Particle flat data JSON file |
| `DUCKDB_PATH` | `observatory.duckdb` | Path to DuckDB database file |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Loading Your Own Data

Replace the sample data file or point to a different path:

```bash
particle-pipeline --data-path /path/to/your/flat_data.json
```

Or set the environment variable:

```bash
export FLAT_DATA_PATH=/path/to/your/flat_data.json
particle-pipeline
```

Data is loaded idempotently: re-running the command replaces existing records per patient. It is safe to run multiple times.

## CLI Reference

```
particle-pipeline                                    # Load flat data into DuckDB
particle-pipeline --help                             # Show all options
particle-pipeline --source file --target duckdb      # Explicit mode (default)
particle-pipeline --data-path /path/to/data.json     # Custom data file
particle-pipeline --verbose                          # Enable debug logging
```

## Resetting the Database

To start fresh, delete the DuckDB file:

```bash
rm observatory.duckdb
particle-pipeline
```

Tables are auto-created on each load, so no init script is needed.

## Project Structure

```
particle-flat-observatory/
  pyproject.toml            # Python package config and dependencies
  .env.example              # Environment variable template
  ddl/
    duckdb/
      create_all.sql        # Table definitions (reference artifact)
    postgres/
      create_all.sql        # Table definitions (PostgreSQL dialect)
  sample-data/
    flat_data.json          # Sample Particle flat data response
  src/observatory/
    cli.py                  # Typer CLI entry point (particle-pipeline command)
    parser.py               # JSON parser for flat_data.json
    normalizer.py           # Empty string -> None normalization
    schema.py               # Schema inspector (discovers columns per resource)
    ddl.py                  # DDL generator (DuckDB, PostgreSQL, and BigQuery)
    loader.py               # DuckDB loader (idempotent per-patient writes)
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

## Analytics Queries

The `queries/` directory contains 15 pre-built analytics queries:

```bash
python3 -c "import duckdb; conn = duckdb.connect('observatory.duckdb'); conn.sql(open('queries/duckdb/clinical/patient_summary.sql').read()).show()"
```

With the DuckDB CLI installed, the same query is shorter:

```bash
duckdb observatory.duckdb < queries/duckdb/clinical/patient_summary.sql
```

See [queries/README.md](queries/README.md) for the full query catalog.

## Cloud Mode (BigQuery)

Load the same flat data into Google BigQuery for cloud-scale analytics. Terraform provisions the dataset and tables. The same CLI loads data into BigQuery instead of DuckDB.

### Prerequisites

- Everything from the local Quick Start (Python 3.11+, pip)
- Google Cloud account with a project and billing enabled
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.0
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed

### 1. Install BigQuery support

The BigQuery dependency is optional. The base install works without it for local-only (DuckDB) users.

```bash
cd particle-flat-observatory
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
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

For production, `terraform/iam.tf` can create a dedicated service account (`observatory-pipeline`) with minimum permissions. Set `create_service_account = true` in `terraform.tfvars` (requires IAM admin permissions on the project).

### 3. Provision infrastructure with Terraform

Terraform creates 1 BigQuery dataset and 21 tables.

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
terraform plan    # Review: 1 dataset, 21 tables
terraform apply
```

Type `yes` when prompted. Terraform creates all resources and outputs the dataset ID.

**Terraform variables:**

| Variable | Default | Description |
|---|---|---|
| `project_id` | (required) | GCP project ID |
| `dataset_name` | `particle_observatory` | BigQuery dataset name |
| `region` | `US` | Dataset location (multi-region `US`/`EU` or single-region e.g. `us-central1`) |
| `create_service_account` | `false` | Create a dedicated service account (requires IAM admin) |

### 4. Configure environment

Uncomment and set the BigQuery variables in your `.env` file (or copy from `.env.example`):

```bash
BQ_PROJECT_ID=your-gcp-project-id
BQ_DATASET=particle_observatory
```

`BQ_PROJECT_ID` is required. `BQ_DATASET` defaults to `particle_observatory` if not set.

### 5. Load data

```bash
particle-pipeline --source file --target bigquery
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
