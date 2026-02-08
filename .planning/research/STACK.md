# Stack Research

**Domain:** Healthcare data pipeline (Particle Health flat JSON to PostgreSQL/BigQuery)
**Researched:** 2026-02-07
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | >=3.12 | Runtime | Project already uses 3.12. LTS-supported, broad library compatibility. 3.11+ for `tomllib` stdlib, 3.12+ for better error messages and f-string improvements. Do not go below 3.11 (existing `pyproject.toml` constraint). |
| psycopg | 3.3.2 | PostgreSQL driver | Modern successor to psycopg2. Native COPY protocol support for bulk loading (critical for 21 resource tables). Sync and async in one package. `write_row()` method enables streaming inserts without holding full dataset in memory. Binary format option for max throughput. |
| psycopg[binary] | 3.3.2 | C speedup for psycopg | Optional C acceleration. Unlike psycopg2-binary, this is a speedup module, not a replacement -- no segfault/libssl conflicts. Safe for both dev and production. |
| google-cloud-bigquery | 3.40.0 | BigQuery client | Official Google client. `load_table_from_json()` for batch loads, `insert_rows_json()` for streaming. `schema_from_json()` for schema management. Actively maintained (Jan 2026 release). |
| pydantic | >=2.12.5 | Schema validation / config | Already in the project (`pydantic-settings`). Use for validating Particle API JSON shapes before DB insertion. `model_validator` for cross-field checks on healthcare data. Type coercion handles string/number mismatches from API. |
| pydantic-settings | >=2.0.0 | Configuration management | Already in the project. Loads from env vars and `.env` files. Single config model for DB credentials, API keys, target selection (pg vs bq). |
| httpx | >=0.28.1 | HTTP client | Already in the project. Used by `ParticleHTTPClient`. Sync client is fine for this pipeline (not a web server). |
| structlog | >=25.5.0 | Structured logging | Already in the project. JSON-formatted logs for pipeline observability. Bind context (patient_id, resource_type, row_count) per operation. |
| tenacity | >=9.1.4 | Retry logic | Already in the project. Wrap API calls and DB writes with exponential backoff. |
| typer | 0.21.1 | CLI framework | Type-hint-driven CLI. Generates help docs automatically. Subcommands map cleanly to pipeline operations: `ingest`, `ddl`, `query`. Built on Click, so composable. Low overhead for a customer-facing accelerator -- customers understand `python main.py ingest --source file --target postgres`. |
| rich | 14.3.2 | Terminal output | Progress bars for multi-table loads, colored status output, table formatting for dry-run DDL preview. Typer integrates with Rich natively. |

### Database & Infrastructure

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| PostgreSQL | 17 (Docker: `postgres:17-alpine`) | Local database target | Current stable major version. Alpine variant keeps image small (~80MB vs ~400MB). Pin to `17` tag (not `latest`) for reproducibility. Health checks via `pg_isready`. |
| Docker Compose | v2 (file format) | Local infrastructure | Single `docker-compose.yml` for PostgreSQL + optional pgAdmin. Named volumes for data persistence. Health check with `service_healthy` condition. |
| Terraform | >=1.14 | Cloud infrastructure | IaC for BigQuery dataset, tables, IAM. Use `hashicorp/google` provider. State management via local backend for accelerator simplicity (customers can switch to GCS backend). |
| Terraform Google Provider | ~>7.0 | GCP resource management | Current major version (7.18.0 as of Feb 2026). Supports `google_bigquery_dataset`, `google_bigquery_table` with JSON schema definitions. Pin to `~>7.0` to allow minor updates while preventing breaking changes. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| google-cloud-bigquery-storage | latest | BigQuery Storage API | Only if needing to READ large result sets from BigQuery. Not needed for write-only pipeline. Add later if analytics queries return >10MB. |
| google-auth | latest | GCP authentication | Transitive dependency of google-cloud-bigquery. Application Default Credentials (ADC) for local dev, service account for production. |
| python-dotenv | latest | .env file loading | Backup for pydantic-settings `.env` loading. Already handled by pydantic-settings, so likely not needed separately. |
| pytest | >=8.0.0 | Testing | Already in the project. Test DDL generation, schema mapping, data transformations. |
| ruff | >=0.1.0 | Linting/formatting | Already in the project. Fast, opinionated. Replaces black + isort + flake8. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Docker Desktop | Run PostgreSQL locally | Required for local mode. Customers need Docker installed. |
| gcloud CLI | GCP authentication | `gcloud auth application-default login` for local BigQuery development. Not a Python dependency. |
| pgAdmin 4 (optional) | PostgreSQL GUI | Add as optional service in `docker-compose.yml`. Image: `dpage/pgadmin4`. Helpful for customers exploring loaded data. |
| psql | PostgreSQL CLI | Ships with PostgreSQL Docker image. Useful for running pre-built SQL queries. |

## Installation

```bash
# Core pipeline dependencies
pip install \
  "psycopg[binary]>=3.3.0" \
  "google-cloud-bigquery>=3.40.0" \
  "pydantic>=2.12.0" \
  "pydantic-settings>=2.0.0" \
  "httpx>=0.28.0" \
  "structlog>=25.0.0" \
  "tenacity>=9.0.0" \
  "typer>=0.21.0" \
  "rich>=14.0.0" \
  "PyJWT>=2.0.0"

# Dev dependencies
pip install -D \
  "pytest>=8.0.0" \
  "ruff>=0.1.0"
```

Or add to `pyproject.toml`:

```toml
[project]
dependencies = [
    "httpx>=0.28.0",
    "pydantic>=2.12.0",
    "pydantic-settings>=2.0.0",
    "structlog>=25.0.0",
    "tenacity>=9.0.0",
    "PyJWT>=2.0.0",
    "psycopg[binary]>=3.3.0",
    "google-cloud-bigquery>=3.40.0",
    "typer>=0.21.0",
    "rich>=14.0.0",
]
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| psycopg 3.3 | psycopg2-binary 2.9.11 | Only if deploying to environments where psycopg3 has compatibility issues (very rare). psycopg2 is maintenance-mode; psycopg3 is the active development target. |
| psycopg 3.3 | asyncpg | Only if building a high-concurrency async web server. asyncpg is ~5x faster for raw queries but async-only, no COPY protocol via `write_row()`, and adds asyncio complexity customers don't need for a batch pipeline. |
| psycopg 3.3 (raw) | SQLAlchemy 2.x | Only if building an ORM-heavy application with complex relationships. For ETL/bulk loading, raw psycopg3 with COPY protocol is faster and simpler. SQLAlchemy adds abstraction overhead that doesn't pay off when you're generating DDL and doing bulk inserts. |
| typer | click 8.3.1 | Only if customers already use Click and want consistency. Typer wraps Click, so they're compatible. Typer is less boilerplate for the simple subcommand pattern this pipeline needs. |
| typer | argparse (stdlib) | Never for this project. argparse requires manual help text, no type validation, no rich output integration. |
| rich | no terminal formatting | Only if targeting non-interactive (cron/CI) environments exclusively. But rich degrades gracefully when stdout is not a TTY, so it's safe to include always. |
| JSON dict manipulation | pandas / polars | Only if doing complex transformations (pivots, aggregations, joins) on the flat data before loading. Particle's flat API returns pre-flattened JSON arrays -- each resource type maps 1:1 to a table. No transformation needed beyond type mapping. Adding pandas (or polars) would add a heavy dependency for no benefit. |
| Terraform | Pulumi / CDK | Only if the customer's org is standardized on Pulumi/CDK. Terraform is the most widely adopted IaC tool and what most GCP customers expect. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| psycopg2 (source build) | Requires `libpq-dev` and C compiler on customer machines. Friction for "run from clean checkout" goal. Maintenance-mode, no new features. | psycopg[binary] 3.3 -- pure Python with optional C speedup, no system deps. |
| psycopg2-binary | Bundles its own libssl, can cause segfaults under concurrency. Officially discouraged for production by maintainers. Legacy API. | psycopg[binary] 3.3 -- the binary speedup is an optional addon, not a library replacement, so no libssl conflicts. |
| SQLAlchemy | Overkill for this use case. Adds ORM abstraction layer over what is fundamentally "generate DDL + COPY data". Customers would need to learn SQLAlchemy to understand/modify the accelerator. | Raw psycopg3 with COPY protocol. Simpler, faster, more transparent for customers. |
| pandas | 300MB+ dependency for reading JSON arrays that Python's `json` module handles natively. No transformation needed on pre-flattened data. Slow for large datasets vs. psycopg3 COPY. | Python stdlib `json` module + psycopg3 COPY. |
| Apache Airflow / Luigi / Prefect | Workflow orchestrators are for scheduling recurring pipelines with many steps. This is a single-shot or on-demand ingestion tool. Adding Airflow would require customers to run its scheduler, metadata DB, and web UI. | Simple CLI via typer. Customers run it when they need it. |
| JSONB columns in PostgreSQL | Storing Particle flat data as JSONB defeats the purpose. Customers want typed, queryable columns with proper indexes for analytics. JSONB queries are slower and harder to write than typed column queries. | Typed columns derived from JSON schema. One column per field. |
| google-cloud-bigquery-storage (for writes) | The Storage Write API is for high-throughput streaming scenarios (>10K rows/sec continuous). Particle flat data is batch-oriented with bounded size per patient. Adds complexity and a separate dependency. | `load_table_from_json()` from google-cloud-bigquery. Handles batch loads up to table size limits. |

## Stack Patterns by Variant

**If target is PostgreSQL (local/Docker):**
- Use psycopg3 with COPY protocol for bulk loading
- Generate DDL with `CREATE TABLE IF NOT EXISTS` for idempotency
- Use `ON CONFLICT DO UPDATE` (upsert) for re-runs on the same patient data
- Docker Compose with `postgres:17-alpine` + named volume
- Connection string from pydantic-settings: `POSTGRES_DSN=postgresql://user:pass@localhost:5432/particle`

**If target is BigQuery (cloud/Terraform):**
- Use `google-cloud-bigquery` client with `load_table_from_json()`
- Generate schemas as JSON files consumed by both Terraform (table creation) and Python (load job config)
- Use `WRITE_TRUNCATE` or `WRITE_APPEND` disposition based on idempotency strategy
- Terraform manages dataset + table lifecycle; Python manages data loading
- Authentication via Application Default Credentials (ADC)

**If target is both (dual-mode):**
- Abstract the "loader" behind a simple interface: `load(table_name, rows, schema)`
- PostgreSQL loader uses psycopg3 COPY
- BigQuery loader uses `load_table_from_json()`
- CLI flag: `--target postgres` or `--target bigquery`
- Schema definition is the single source of truth for both DDL generation and load job config

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| psycopg[binary] 3.3.x | Python >=3.10 | Requires Python 3.10+. Our project targets 3.12, so compatible. |
| google-cloud-bigquery 3.40.x | Python >=3.9 | Broad Python support. No conflicts with psycopg3. |
| typer 0.21.x | Python >=3.9, click >=8.0 | Typer depends on Click. If project uses Click elsewhere, versions must align. |
| pydantic 2.12.x | Python >=3.8 | Existing project dependency. No version conflicts. |
| structlog 25.x | Python >=3.8 | Existing project dependency. No version conflicts. |
| httpx 0.28.x | Python >=3.8 | Note: httpx 1.0 is in dev preview. Stay on 0.28.x for stability. |
| Terraform 1.14.x | Google provider ~>7.0 | Use `required_providers` block to pin. |
| postgres:17-alpine | psycopg 3.3.x | PostgreSQL 17 wire protocol fully supported by psycopg3. |

## Docker Compose Reference

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: particle
      POSTGRES_USER: particle
      POSTGRES_PASSWORD: particle_dev
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U particle"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Optional: pgAdmin for data exploration
  pgadmin:
    image: dpage/pgadmin4
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@local.dev
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "8080:80"
    depends_on:
      postgres:
        condition: service_healthy
    profiles:
      - tools

volumes:
  pgdata:
```

## Terraform Reference

```hcl
# providers.tf
terraform {
  required_version = ">= 1.14"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# bigquery.tf
resource "google_bigquery_dataset" "particle" {
  dataset_id = "particle_health"
  location   = var.region

  labels = {
    env     = var.environment
    managed = "terraform"
  }
}
```

## Sources

- [PyPI: psycopg 3.3.2](https://pypi.org/project/psycopg/) -- verified version and Python support (HIGH confidence)
- [PyPI: psycopg-binary 3.3.2](https://pypi.org/project/psycopg-binary/) -- verified version (HIGH confidence)
- [PyPI: psycopg2-binary 2.9.11](https://pypi.org/project/psycopg2-binary/) -- verified version (HIGH confidence)
- [PyPI: google-cloud-bigquery 3.40.0](https://pypi.org/project/google-cloud-bigquery/) -- verified version and Python support (HIGH confidence)
- [PyPI: pydantic 2.12.5](https://pypi.org/project/pydantic/) -- verified version (HIGH confidence)
- [PyPI: typer 0.21.1](https://pypi.org/project/typer/) -- verified version (HIGH confidence)
- [PyPI: click 8.3.1](https://pypi.org/project/click/) -- verified version (HIGH confidence)
- [PyPI: rich 14.3.2](https://pypi.org/project/rich/) -- verified version (HIGH confidence)
- [PyPI: structlog 25.5.0](https://pypi.org/project/structlog/) -- verified version (HIGH confidence)
- [PyPI: httpx 0.28.1](https://pypi.org/project/httpx/) -- verified version (HIGH confidence)
- [PyPI: tenacity 9.1.4](https://pypi.org/project/tenacity/) -- verified version (HIGH confidence)
- [Psycopg3 COPY docs](https://www.psycopg.org/psycopg3/docs/basic/copy.html) -- COPY protocol patterns (HIGH confidence)
- [psycopg2-binary production warning](https://github.com/psycopg/psycopg2/issues/674) -- libssl conflict documentation (HIGH confidence)
- [psycopg3 binary discussion](https://github.com/psycopg/psycopg/discussions/1057) -- binary addon is safe unlike psycopg2-binary (HIGH confidence)
- [Tiger Data: psycopg2 vs psycopg3 benchmark](https://www.tigerdata.com/blog/psycopg2-vs-psycopg3-performance-benchmark) -- performance comparison (MEDIUM confidence)
- [Terraform Google Provider releases](https://github.com/hashicorp/terraform-provider-google/releases) -- v7.18.0 verified (HIGH confidence)
- [Docker Hub: postgres](https://hub.docker.com/_/postgres) -- image tags and versions (HIGH confidence)
- [Google BigQuery Python client docs](https://cloud.google.com/python/docs/reference/bigquery/latest) -- API reference (HIGH confidence)
- [Google BigQuery schema docs](https://cloud.google.com/bigquery/docs/schemas) -- schema management patterns (HIGH confidence)
- [BigQuery JSON loading docs](https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-json) -- load job configuration (HIGH confidence)

---
*Stack research for: Healthcare data pipeline (Particle Health flat JSON to PostgreSQL/BigQuery)*
*Researched: 2026-02-07*
