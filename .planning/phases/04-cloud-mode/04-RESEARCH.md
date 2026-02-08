# Phase 4: Cloud Mode - Research

**Researched:** 2026-02-08
**Domain:** BigQuery data loading, Terraform GCP provisioning, Python google-cloud-bigquery
**Confidence:** HIGH

## Summary

Phase 4 adds BigQuery as a cloud target for the existing Particle flat data pipeline. The work divides into three areas: (1) Terraform HCL to provision a BigQuery dataset, 21 tables with all-STRING schemas, and a service account with minimum IAM permissions; (2) a Python BigQuery loader module using `google-cloud-bigquery` that mirrors the existing PostgreSQL loader's idempotent delete+insert pattern; and (3) CLI integration wiring `--target bigquery` into the existing Typer app.

The existing codebase already has BigQuery DDL (all STRING columns), BigQuery-dialect analytics queries (30 SQL files), and a CLI stub that returns "BigQuery target not yet implemented." The loader must use batch load jobs (`load_table_from_json`), not streaming inserts, and must provide the same per-patient per-resource-type delete+insert idempotency as the PostgreSQL loader. BigQuery supports multi-statement transactions via `BEGIN TRANSACTION / COMMIT TRANSACTION` which enables the atomic delete+insert pattern.

**Primary recommendation:** Use `google-cloud-bigquery>=3.40.0` with explicit `SchemaField` definitions (all STRING, NULLABLE) to avoid type auto-detection issues, execute DELETE via `client.query()` with parameterized DML, then load via `load_table_from_json()` per patient per resource type. Use Terraform `hashicorp/google` provider `~> 7.0` with `google_bigquery_dataset`, `google_bigquery_table` (jsonencode schema), `google_service_account`, and dataset-level + project-level IAM bindings.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| google-cloud-bigquery | >=3.40.0 | Python BigQuery client (load jobs, DML queries) | Official Google client, supports load_table_from_json and client.query for DML |
| hashicorp/google (Terraform) | ~> 7.0 | GCP Terraform provider | Current major version, GA since 2025 |
| Terraform | >= 1.0 | Infrastructure as code | Industry standard for GCP provisioning |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| google-auth | (transitive) | ADC authentication | Pulled in by google-cloud-bigquery; no direct dependency needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| load_table_from_json | load_table_from_file (JSONL) | load_table_from_json is simpler for in-memory dicts; avoids JSONL serialization step |
| load_table_from_json | insert_rows_json (streaming) | Streaming has cost, quota, and latency implications; requirement explicitly says batch load jobs |
| Individual google_bigquery_table resources | terraform-google-modules/bigquery module | Module adds abstraction layer; raw resources are simpler for 21 identical STRING-only tables |
| google_project_iam_member | google_bigquery_dataset_iam_member only | jobUser role must be project-level; cannot be dataset-scoped |

**Installation:**
```bash
# Python dependency (add to pyproject.toml)
pip install "google-cloud-bigquery>=3.40.0"

# Terraform (customer runs in terraform/ directory)
terraform init
```

## Architecture Patterns

### Recommended Project Structure
```
particle-flat-observatory/
  src/observatory/
    loader.py            # Existing PostgreSQL loader (unchanged)
    bq_loader.py         # NEW: BigQuery loader module
    cli.py               # Modified: wire --target bigquery
    config.py            # Modified: add BQ_* env vars
  terraform/
    main.tf              # Provider config + dataset + tables
    variables.tf         # project_id, dataset_name, region
    outputs.tf           # dataset_id, service_account_email
    tables.tf            # All 21 table resources (or use for_each in main.tf)
    iam.tf               # Service account + role bindings
    terraform.tfvars.example  # Example variable values
```

### Pattern 1: BigQuery Idempotent Delete+Insert via DML + Load Job
**What:** Mirror PostgreSQL's per-patient per-resource-type atomic delete+insert using BigQuery DML for DELETE and load job for INSERT.
**When to use:** Every load operation.
**Why not a single transaction:** BigQuery multi-statement transactions (`BEGIN TRANSACTION ... COMMIT TRANSACTION`) support DELETE and INSERT DML, but `load_table_from_json` is a load job, not DML. The delete+insert must therefore be: (1) DELETE via `client.query()`, (2) INSERT via `load_table_from_json()`. These are not atomic in a single transaction. However, since data is scoped per-patient per-resource-type and idempotent (safe to re-run), eventual consistency is acceptable.
**Alternative:** Use DML INSERT instead of load job for atomicity, but this has row-level quotas and is slower for batch data.
**Example:**
```python
from google.cloud import bigquery

def load_resource_bq(client, dataset_id, table_name, columns, records, patient_id):
    """Idempotent delete+insert for BigQuery."""
    if not records:
        return 0

    table_ref = f"{client.project}.{dataset_id}.{table_name}"

    # Step 1: DELETE existing rows for this patient
    delete_query = f"DELETE FROM `{table_ref}` WHERE `patient_id` = @patient_id"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("patient_id", "STRING", patient_id)
        ]
    )
    client.query(delete_query, job_config=job_config).result()

    # Step 2: INSERT via batch load job
    schema = [bigquery.SchemaField(col, "STRING", mode="NULLABLE") for col in columns]
    load_config = bigquery.LoadJobConfig(schema=schema)
    # Filter records to only include known columns
    rows = [{col: record.get(col) for col in columns} for record in records]
    load_job = client.load_table_from_json(rows, table_ref, job_config=load_config)
    load_job.result()

    return len(records)
```

### Pattern 2: Terraform for_each for 21 Tables
**What:** Use `for_each` with a local map to create all 21 BigQuery tables from a single resource block.
**When to use:** When all tables share the same pattern (all STRING columns, same options).
**Example:**
```hcl
locals {
  # Table schemas derived from existing DDL -- table_name -> list of column names
  tables = {
    "ai_citations" = ["ai_output_id", "citation_id", "particle_patient_id", ...]
    "ai_outputs"   = ["ai_output_id", "created", "patient_id", ...]
    # ... all 21 tables
  }
}

resource "google_bigquery_table" "tables" {
  for_each   = local.tables
  dataset_id = google_bigquery_dataset.observatory.dataset_id
  table_id   = each.key

  deletion_protection = false  # Accelerator/demo context

  schema = jsonencode([
    for col in each.value : {
      name = col
      type = "STRING"
      mode = "NULLABLE"
    }
  ])
}
```

### Pattern 3: ADC Authentication (No Explicit Credentials in Code)
**What:** Use Application Default Credentials so the BigQuery client auto-discovers credentials from the environment.
**When to use:** Always. Never embed credentials in code.
**Example:**
```python
# Client auto-discovers credentials from:
# 1. GOOGLE_APPLICATION_CREDENTIALS env var (service account JSON key)
# 2. gcloud auth application-default login (user credentials)
# 3. GCE/Cloud Run metadata server (when running on GCP)
client = bigquery.Client(project=project_id)
```

### Anti-Patterns to Avoid
- **Streaming inserts instead of batch load:** Requirement CLOUD-04 explicitly requires load jobs. Streaming has per-row costs and different quotas.
- **Auto-detect schema:** Must use explicit SchemaField with STRING type. Auto-detect will interpret numeric-looking strings ("123") as INTEGER, causing type mismatch errors.
- **Hardcoded project/dataset in Python:** Use environment variables (BQ_PROJECT_ID, BQ_DATASET) matching the existing config pattern.
- **Full-table TRUNCATE instead of per-patient DELETE:** Breaks multi-patient idempotency. Must scope DELETE to patient_id, matching PostgreSQL behavior.
- **Embedding service account keys in repo:** Use ADC. Document `gcloud auth application-default login` for local dev, service account key file via env var for CI/production.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| BigQuery schema definition | Manual JSON string building | `bigquery.SchemaField` objects | Handles escaping, validation, mode defaults |
| Parameterized DML queries | f-string SQL interpolation | `bigquery.ScalarQueryParameter` | Prevents SQL injection, handles type coercion |
| GCP authentication | Custom credential loading | ADC via `bigquery.Client()` | Handles all auth flows (user, SA, metadata) |
| Table reference formatting | Manual `project.dataset.table` strings | `client.project` + config-driven dataset | Consistent, testable, no typos |
| Terraform table schemas | 21 separate resource blocks | `for_each` with locals map | DRY, maintainable, single pattern |
| IAM role assignment | Manual gcloud commands | Terraform `google_project_iam_member` + `google_bigquery_dataset_iam_member` | Reproducible, declarative, auditable |

**Key insight:** The BigQuery Python client has sharp edges around type auto-detection. Always provide explicit schemas with `SchemaField` objects and never rely on auto-detect when all columns are STRING.

## Common Pitfalls

### Pitfall 1: load_table_from_json Type Auto-Detection
**What goes wrong:** When loading data with `load_table_from_json`, BigQuery auto-detects schema by default. Values like `"123"` get interpreted as INTEGER instead of STRING, causing `Field X has changed type from STRING to INTEGER` errors.
**Why it happens:** The library sets `autodetect=True` by default when no schema is provided.
**How to avoid:** Always provide explicit `LoadJobConfig(schema=[SchemaField(...)])` with all fields as STRING, NULLABLE.
**Warning signs:** Type mismatch errors during load, especially for columns containing numeric-looking string values (IDs, codes).

### Pitfall 2: None/Null Values in load_table_from_json
**What goes wrong:** Records with `None` values for some columns can cause issues if schema is not explicit.
**Why it happens:** JSON null values can confuse auto-detection.
**How to avoid:** Explicit schema with `mode="NULLABLE"` on all fields. The existing normalizer already converts empty strings to None, which BigQuery handles correctly as NULL when schema is explicit.
**Warning signs:** Errors about null values in REQUIRED fields.

### Pitfall 3: DELETE DML Without WHERE Clause Scope
**What goes wrong:** A DELETE without proper scoping removes all rows from the table instead of just the target patient's data.
**Why it happens:** Copy-paste error or forgetting the patient_id filter.
**How to avoid:** Always use parameterized queries with `@patient_id` parameter. Never use f-string interpolation for the WHERE clause.
**Warning signs:** Table becomes empty after loading a single patient.

### Pitfall 4: BigQuery Quotas for Load Jobs
**What goes wrong:** Exceeding 1,500 load jobs per table per day.
**Why it happens:** Each patient + resource type combination creates one load job. With many patients, this adds up fast.
**How to avoid:** For the accelerator scope (sample data, small number of patients), this is not an issue. For production scale, batch multiple patients into a single load job. Document this limitation in README.
**Warning signs:** 429 errors from BigQuery API with quota exceeded messages.

### Pitfall 5: Terraform deletion_protection Default
**What goes wrong:** `terraform destroy` fails because `deletion_protection` defaults to `true` on newer provider versions.
**Why it happens:** Provider v6+ changed the default to protect against accidental deletion.
**How to avoid:** Explicitly set `deletion_protection = false` on tables in the accelerator context. Document that production deployments should set this to `true`.
**Warning signs:** `terraform destroy` errors saying table is protected.

### Pitfall 6: Unqualified Table Names in BigQuery Queries
**What goes wrong:** Existing BigQuery analytics queries use unqualified table names (e.g., `FROM patients` not `FROM project.dataset.patients`). These fail unless a default dataset is configured.
**Why it happens:** Queries were written for portability and simplicity.
**How to avoid:** When running queries programmatically, set `default_dataset` on `QueryJobConfig`. In the BigQuery console, users must select the dataset. Document this in README.
**Warning signs:** "Table not found" errors when running analytics queries.

### Pitfall 7: BigQuery DML Concurrency
**What goes wrong:** Multiple concurrent DML operations on the same table can queue or fail.
**Why it happens:** BigQuery limits concurrent mutating DML to 2 active + 20 queued per table.
**How to avoid:** For the accelerator (single-user, small data), this is not a concern. For production, batch operations. Document the limitation.
**Warning signs:** Slow load times, queued job status.

## Code Examples

Verified patterns from official sources:

### BigQuery Client Initialization with ADC
```python
# Source: Google Cloud BigQuery Python client documentation
from google.cloud import bigquery
import os

def get_bq_client():
    """Create a BigQuery client using Application Default Credentials."""
    project_id = os.environ.get("BQ_PROJECT_ID")
    if not project_id:
        raise ValueError(
            "BQ_PROJECT_ID not set. "
            "Set BQ_PROJECT_ID in .env or environment to your GCP project ID."
        )
    return bigquery.Client(project=project_id)
```

### BigQuery Load Job with Explicit Schema
```python
# Source: Google Cloud BigQuery Python client docs + issue #1228 workaround
from google.cloud import bigquery

def load_records_to_bq(client, dataset_id, table_name, columns, records):
    """Load records into BigQuery using a batch load job with explicit schema."""
    table_ref = f"{client.project}.{dataset_id}.{table_name}"

    schema = [
        bigquery.SchemaField(col, "STRING", mode="NULLABLE")
        for col in columns
    ]
    job_config = bigquery.LoadJobConfig(schema=schema)

    # Build row dicts with only known columns
    rows = [{col: record.get(col) for col in columns} for record in records]

    load_job = client.load_table_from_json(rows, table_ref, job_config=job_config)
    load_job.result()  # Wait for completion

    return len(records)
```

### BigQuery Parameterized DELETE
```python
# Source: Google Cloud BigQuery DML documentation
from google.cloud import bigquery

def delete_patient_records(client, dataset_id, table_name, patient_id):
    """Delete all records for a patient from a BigQuery table."""
    table_ref = f"`{client.project}.{dataset_id}.{table_name}`"
    query = f"DELETE FROM {table_ref} WHERE `patient_id` = @patient_id"

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("patient_id", "STRING", patient_id)
        ]
    )
    query_job = client.query(query, job_config=job_config)
    query_job.result()  # Wait for completion
```

### Terraform BigQuery Dataset
```hcl
# Source: hashicorp/google provider documentation
resource "google_bigquery_dataset" "observatory" {
  dataset_id    = var.dataset_name
  project       = var.project_id
  location      = var.region
  friendly_name = "Particle Flat Data Observatory"
  description   = "Structured tables for Particle Health flat data analytics"

  # Allow terraform destroy for accelerator use
  delete_contents_on_destroy = true
}
```

### Terraform BigQuery Table with jsonencode Schema
```hcl
# Source: hashicorp/google provider documentation + community patterns
resource "google_bigquery_table" "tables" {
  for_each   = local.tables
  dataset_id = google_bigquery_dataset.observatory.dataset_id
  project    = var.project_id
  table_id   = each.key

  deletion_protection = false

  schema = jsonencode([
    for col in each.value : {
      name = col
      type = "STRING"
      mode = "NULLABLE"
    }
  ])
}
```

### Terraform Service Account with Minimum Permissions
```hcl
# Source: BigQuery IAM documentation + Terraform provider docs
resource "google_service_account" "observatory" {
  account_id   = "observatory-pipeline"
  display_name = "Observatory Pipeline Service Account"
  project      = var.project_id
}

# Dataset-level: data editor (read/write data)
resource "google_bigquery_dataset_iam_member" "data_editor" {
  dataset_id = google_bigquery_dataset.observatory.dataset_id
  project    = var.project_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.observatory.email}"
}

# Project-level: job user (create load/query jobs)
resource "google_project_iam_member" "job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.observatory.email}"
}
```

### Terraform Variables
```hcl
# Source: Terraform best practices for customer-configurable modules
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "dataset_name" {
  description = "BigQuery dataset name"
  type        = string
  default     = "particle_observatory"
}

variable "region" {
  description = "GCP region for dataset location"
  type        = string
  default     = "US"
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Streaming inserts (insertAll) | Batch load jobs (load_table_from_json) | Ongoing best practice | Free vs. per-row cost; better for batch ETL |
| google provider v5/v6 | google provider v7 (GA) | 2025 | deletion_protection defaults changed; new resource attributes |
| Manual BigQuery table creation | Terraform for_each with jsonencode | Terraform 0.12+ | DRY, maintainable, handles 21 identical tables |
| Service account key files | Application Default Credentials | Ongoing best practice | Simpler setup, works across environments |

**Deprecated/outdated:**
- `google.cloud.bigquery.Table.insert_data()` -- replaced by `client.insert_rows_json()` and `client.load_table_from_json()`
- Terraform `google` provider v5 -- v7 is current GA, v6+ changed deletion_protection defaults

## Open Questions

Things that could not be fully resolved:

1. **Atomicity of DELETE + Load Job**
   - What we know: BigQuery multi-statement transactions support DML (DELETE, INSERT) but load jobs are not DML statements. A load job and a DML DELETE cannot be combined in a single BEGIN/COMMIT transaction.
   - What's unclear: Whether there is a way to make delete+load_job atomic without using DML INSERT (which has different quotas).
   - Recommendation: Accept non-atomic delete+insert for the accelerator. The pattern is still idempotent -- re-running is safe. Document that for production, consider using DML INSERT within a transaction for atomicity at the cost of DML quotas (free tier: 1,500 DML per table/day). For sample data scale, this is a non-issue.

2. **Empty Table Handling in Terraform**
   - What we know: 5 of the 21 resource types have no sample data (allergies, coverages, familyMemberHistories, immunizations, socialHistories). The existing BigQuery DDL comments these out.
   - What's unclear: Whether Terraform should create empty tables for these or skip them.
   - Recommendation: Create all 21 tables in Terraform (even empty ones) with placeholder columns (just `patient_id STRING`). This ensures tables exist when data becomes available. The Python loader already handles empty resource types by skipping them.

3. **Load Job Quota at Scale**
   - What we know: BigQuery allows 1,500 load jobs per table per day. Each patient + resource type = 1 load job.
   - What's unclear: Whether customers will hit this with production data volumes.
   - Recommendation: For the accelerator scope, this is fine. Document the limitation and suggest batching multiple patients per load job for production use.

## Sources

### Primary (HIGH confidence)
- [google-cloud-bigquery PyPI](https://pypi.org/project/google-cloud-bigquery/) - version 3.40.0 confirmed (Jan 2026)
- [BigQuery Batch Loading Docs](https://docs.cloud.google.com/bigquery/docs/batch-loading-data) - load job patterns
- [BigQuery Multi-Statement Transactions](https://docs.cloud.google.com/bigquery/docs/transactions) - BEGIN/COMMIT/ROLLBACK syntax and limitations
- [BigQuery DML Syntax](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax) - DELETE, INSERT statements
- [BigQuery IAM Roles](https://cloud.google.com/bigquery/docs/access-control) - minimum permissions (dataEditor + jobUser)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs) - v7.18.0 current
- [google_bigquery_dataset resource](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigquery_dataset)
- [google_bigquery_table resource](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigquery_table)
- [python-bigquery issue #1228](https://github.com/googleapis/python-bigquery/issues/1228) - load_table_from_json STRING type auto-detection bug and workaround

### Secondary (MEDIUM confidence)
- [BigQuery ADC Setup](https://cloud.google.com/bigquery/docs/authentication/getting-started) - authentication patterns
- [Terraform BigQuery IAM](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigquery_dataset_iam) - dataset-level IAM bindings
- [Terraform BigQuery Module](https://github.com/terraform-google-modules/terraform-google-bigquery) - community patterns (used for reference, not direct dependency)

### Tertiary (LOW confidence)
- Community blog posts on BigQuery idempotent patterns -- patterns verified against official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official Google Cloud libraries and Terraform provider, versions verified on PyPI and Terraform Registry
- Architecture: HIGH - Patterns derived from existing codebase (PostgreSQL loader) mapped to verified BigQuery API capabilities
- Pitfalls: HIGH - Type auto-detection issue verified via GitHub issue #1228; quota limits from official docs; deletion_protection from provider changelog

**Research date:** 2026-02-08
**Valid until:** 2026-03-08 (30 days -- stable ecosystem, major versions unlikely to change)
