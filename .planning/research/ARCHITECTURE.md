# Architecture Research

**Domain:** Healthcare data pipeline (JSON-to-database ETL with dual targets)
**Researched:** 2026-02-07
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Ingestion Layer                              │
│  ┌──────────────┐  ┌──────────────┐                                 │
│  │  API Client   │  │  File Reader  │                                │
│  │  (live mode)  │  │  (file mode)  │                                │
│  └──────┬───────┘  └──────┬───────┘                                 │
│         └────────┬────────┘                                         │
├──────────────────┼──────────────────────────────────────────────────┤
│                  ▼          Processing Layer                        │
│  ┌──────────────────────────┐                                       │
│  │       JSON Parser        │  Splits flat response into            │
│  │   (resource splitter)    │  21 per-resource-type arrays          │
│  └────────────┬─────────────┘                                       │
│               ▼                                                     │
│  ┌──────────────────────────┐                                       │
│  │    Schema Inspector      │  Infers column names + types          │
│  │   (type inference)       │  from JSON values                     │
│  └────────────┬─────────────┘                                       │
│               ▼                                                     │
│  ┌──────────────────────────┐                                       │
│  │     DDL Generator        │  Produces CREATE TABLE for            │
│  │  (dialect-aware)         │  PostgreSQL or BigQuery               │
│  └────────────┬─────────────┘                                       │
├───────────────┼─────────────────────────────────────────────────────┤
│               ▼          Loading Layer                              │
│  ┌──────────────────────────┐                                       │
│  │    Loader Interface      │  Abstract: create_tables(),           │
│  │    (DatabaseLoader)      │  load_records(), upsert()             │
│  └──────┬──────────┬────────┘                                       │
│         │          │                                                │
│    ┌────▼────┐ ┌───▼──────┐                                        │
│    │ Postgres│ │ BigQuery  │                                        │
│    │ Loader  │ │ Loader    │                                        │
│    └────┬────┘ └───┬──────┘                                        │
├─────────┼──────────┼────────────────────────────────────────────────┤
│         ▼          ▼         Storage Layer                          │
│  ┌──────────┐  ┌──────────┐                                        │
│  │PostgreSQL│  │ BigQuery  │                                        │
│  │ (Docker) │  │ (GCP)    │                                        │
│  └──────────┘  └──────────┘                                        │
├─────────────────────────────────────────────────────────────────────┤
│                        Query Layer                                  │
│  ┌──────────────────────────────────────────────────┐               │
│  │            SQL Query Library                      │               │
│  │  clinical/  (patient summaries, lab trends, ...)  │               │
│  │  operational/ (coverage, completeness, ...)       │               │
│  └──────────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **API Client** | Fetches flat data from Particle Health GET Flat endpoint | Reuses existing `ParticleHTTPClient` + `QueryService.get_flat()` from `particle-health-starters` |
| **File Reader** | Reads flat JSON from local file or stdin | `json.load()` from stdlib; no external dependency needed |
| **JSON Parser** | Splits top-level dict into per-resource-type record arrays; normalizes keys | Pure Python dict iteration; handles empty arrays gracefully |
| **Schema Inspector** | Infers column names and SQL types from JSON field names and value types | Custom module; maps Python types to SQL types with dialect awareness |
| **DDL Generator** | Produces dialect-specific CREATE TABLE statements for all 21 resource types | Template-based string generation; separate type maps for PostgreSQL vs BigQuery |
| **Loader Interface** | Abstract base defining `create_tables()`, `load_records()`, `upsert()` | Python ABC or Protocol class; database-agnostic contract |
| **PostgreSQL Loader** | Implements Loader for PostgreSQL using psycopg2/psycopg | `INSERT ... ON CONFLICT DO UPDATE` for upserts; connection via env vars |
| **BigQuery Loader** | Implements Loader for BigQuery using google-cloud-bigquery | Staging table + `MERGE` statement for upserts; service account auth |
| **SQL Query Library** | Pre-built `.sql` files for clinical and operational analytics | Static SQL files organized by category; dialect-variant comments where needed |
| **CLI Entrypoint** | Orchestrates the pipeline: parse args, ingest, load, report | `argparse` (stdlib) or `click`; subcommands for `load`, `ddl`, `query` |

## Recommended Project Structure

```
particle-flat-pipeline/
├── pyproject.toml               # Package metadata, dependencies
├── README.md                    # Setup instructions for local + cloud
├── .env.example                 # Template environment variables
├── sample-data/
│   └── flat_data.json           # Symlink or copy from particle-health-starters
├── src/
│   └── pipeline/
│       ├── __init__.py
│       ├── cli.py               # CLI entrypoint with subcommands
│       ├── config.py            # Settings from env vars (Pydantic)
│       ├── parser.py            # JSON parsing + resource splitting
│       ├── schema.py            # Schema inference + type mapping
│       ├── ddl.py               # DDL generation (dialect-aware)
│       ├── loader/
│       │   ├── __init__.py
│       │   ├── base.py          # Abstract DatabaseLoader interface
│       │   ├── postgres.py      # PostgreSQL implementation
│       │   └── bigquery.py      # BigQuery implementation
│       └── exceptions.py        # Pipeline-specific errors
├── sql/
│   ├── clinical/
│   │   ├── patient_summary.sql
│   │   ├── encounter_timeline.sql
│   │   ├── lab_trends.sql
│   │   ├── medication_list.sql
│   │   └── problem_list.sql
│   └── operational/
│       ├── data_completeness.sql
│       ├── source_breakdown.sql
│       ├── patient_counts.sql
│       └── resource_coverage.sql
├── ddl/
│   ├── postgres/                # Generated or hand-maintained DDL
│   │   └── create_tables.sql
│   └── bigquery/
│       └── create_tables.sql
├── infra/
│   ├── docker-compose.yml       # PostgreSQL + pipeline for local mode
│   ├── Dockerfile               # Pipeline container
│   └── terraform/
│       ├── main.tf              # BigQuery dataset + tables + SA
│       ├── variables.tf
│       └── outputs.tf
└── tests/
    ├── conftest.py              # Shared fixtures (sample data loading)
    ├── test_parser.py
    ├── test_schema.py
    ├── test_ddl.py
    ├── test_loader_postgres.py
    └── test_loader_bigquery.py
```

### Structure Rationale

- **`src/pipeline/`:** Single flat package because the domain is narrow. Avoid deep nesting for a pipeline with ~8 modules. Customers can read top-to-bottom without navigating layers.
- **`src/pipeline/loader/`:** Only sub-package, because PostgreSQL and BigQuery implementations share an interface but have fundamentally different mechanics. The adapter pattern demands a separate file per implementation.
- **`sql/`:** Separated from Python code because SQL files are independently useful. Customers may copy just the SQL into their own tools (dbt, BI tools, notebooks). Organized by use case (clinical vs operational), not by resource type.
- **`ddl/`:** Separated from `sql/` because DDL is one-time schema setup while `sql/` contains recurring queries. Dialect-specific subdirectories make it clear which DDL goes where.
- **`infra/`:** Docker and Terraform together because they serve the same purpose (environment provisioning) for different deployment targets. Keeps infrastructure concerns out of application code.
- **`tests/`:** Flat test directory mirroring source modules. No test subdirectories needed for a pipeline this size.

## Architectural Patterns

### Pattern 1: Adapter Pattern for Dual Database Targets

**What:** Define an abstract `DatabaseLoader` interface with methods like `create_tables()`, `load_records()`, `upsert()`, and `close()`. Implement separately for PostgreSQL and BigQuery.

**When to use:** Whenever the pipeline targets two fundamentally different databases with different SQL dialects, connection mechanisms, and bulk loading strategies.

**Trade-offs:**
- Pro: Clean separation; adding a third target (e.g., Snowflake) means adding one file
- Pro: Each loader can optimize for its database (COPY for Postgres, load_table_from_json for BigQuery)
- Con: Slight indirection; customer must understand which loader is selected
- Con: Interface must be generic enough for both targets without leaking abstractions

**Example:**
```python
from abc import ABC, abstractmethod
from typing import Any

class DatabaseLoader(ABC):
    """Abstract interface for loading flat data into a database."""

    @abstractmethod
    def connect(self) -> None:
        """Establish database connection."""
        ...

    @abstractmethod
    def create_tables(self, ddl_statements: list[str]) -> None:
        """Execute DDL to create tables. Idempotent (IF NOT EXISTS)."""
        ...

    @abstractmethod
    def load_records(self, table_name: str, records: list[dict[str, Any]]) -> int:
        """Insert records into table. Returns count of rows loaded."""
        ...

    @abstractmethod
    def upsert_records(
        self, table_name: str, records: list[dict[str, Any]], key_columns: list[str]
    ) -> int:
        """Insert or update records based on key columns. Returns count."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Clean up connections."""
        ...

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()
```

### Pattern 2: Dialect-Aware DDL Generation via Type Maps

**What:** Maintain a mapping from inferred Python/JSON types to SQL types, with separate maps per dialect. DDL generation uses the appropriate map based on target database.

**When to use:** When the same logical schema must be expressed in two SQL dialects with different type names and syntax.

**Trade-offs:**
- Pro: Single source of truth for schema; types are mapped, not duplicated
- Pro: Easy to verify correctness by inspecting the type map
- Con: Some dialect-specific features (BigQuery partitioning, PostgreSQL constraints) may not fit cleanly into a generic map

**Example:**
```python
# Type mapping from inferred Python types to SQL types
TYPE_MAPS = {
    "postgresql": {
        "string": "TEXT",
        "integer": "BIGINT",
        "float": "DOUBLE PRECISION",
        "boolean": "BOOLEAN",
        "timestamp": "TIMESTAMPTZ",
        "date": "DATE",
    },
    "bigquery": {
        "string": "STRING",
        "integer": "INT64",
        "float": "FLOAT64",
        "boolean": "BOOL",
        "timestamp": "TIMESTAMP",
        "date": "DATE",
    },
}

def generate_ddl(
    table_name: str,
    columns: dict[str, str],  # {column_name: inferred_type}
    dialect: str,
) -> str:
    """Generate CREATE TABLE statement for the given dialect."""
    type_map = TYPE_MAPS[dialect]
    col_defs = []
    for col_name, col_type in columns.items():
        sql_type = type_map.get(col_type, type_map["string"])  # default to string
        col_defs.append(f"    {col_name} {sql_type}")

    if dialect == "postgresql":
        return f"CREATE TABLE IF NOT EXISTS {table_name} (\n{',\n'.join(col_defs)}\n);"
    elif dialect == "bigquery":
        return f"CREATE TABLE IF NOT EXISTS {table_name} (\n{',\n'.join(col_defs)}\n);"
```

### Pattern 3: Delete-and-Replace Idempotency (Recommended Default)

**What:** For each load operation, delete all existing records for the given `patient_id` from the target table, then insert all new records. This avoids complex upsert key identification.

**When to use:** When natural keys are ambiguous or not guaranteed unique across all resource types. The Particle flat data has `patient_id` on every resource type, making it a reliable partition key for delete-and-replace.

**Trade-offs:**
- Pro: Simpler than upsert; no need to identify primary keys per resource type
- Pro: Handles schema changes (new/removed fields) naturally
- Pro: Works identically on both PostgreSQL and BigQuery (DELETE + INSERT vs MERGE)
- Con: Not suitable for append-only audit trails
- Con: Brief window of missing data during delete-insert (wrap in transaction for Postgres; use staging table for BigQuery)

**Why this over upsert:** The sample data analysis reveals that primary key identification is non-trivial across 21 resource types. Some resources have clear single keys (e.g., `encounter_id`, `patient_id`), but others have composite keys or ambiguous candidates. Delete-and-replace on `patient_id` is universally applicable and sidesteps key-per-table configuration.

**Example:**
```python
# PostgreSQL: wrapped in transaction
def load_patient_data(conn, table_name: str, patient_id: str, records: list[dict]):
    with conn.cursor() as cur:
        cur.execute(
            f"DELETE FROM {table_name} WHERE patient_id = %s", (patient_id,)
        )
        # Insert all records for this patient
        if records:
            columns = records[0].keys()
            placeholders = ", ".join(["%s"] * len(columns))
            col_list = ", ".join(columns)
            insert_sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})"
            for record in records:
                cur.execute(insert_sql, tuple(record[c] for c in columns))
    conn.commit()
```

## Data Flow

### Primary Pipeline Flow

```
[Input Source]
    │
    ├── API Mode: ParticleHTTPClient → GET /api/v2/patients/{id}/flat → JSON response
    │
    └── File Mode: Read flat_data.json from path or stdin → JSON dict
    │
    ▼
[JSON Parser]
    │  Input: Single JSON dict with 21 top-level keys
    │  Output: Dict[str, list[dict]] — resource_type → list of flat records
    │  Handles: Empty arrays (skip), missing keys (skip), extra keys (pass through)
    │
    ▼
[Schema Inspector]
    │  Input: Dict[str, list[dict]]
    │  Output: Dict[str, Dict[str, str]] — resource_type → {column → inferred_type}
    │  Logic: Scan all records per type to infer types (string, integer, float, boolean)
    │  Note: 19 of 21 types are all-string; only medications.dose_value and
    │        vitalSigns.observation_value have numeric values (int/float)
    │
    ▼
[DDL Generator]
    │  Input: Schema dict + target dialect (postgresql | bigquery)
    │  Output: List of CREATE TABLE SQL strings
    │  Adds: Pipeline metadata columns (_loaded_at TIMESTAMP, _patient_id TEXT)
    │
    ▼
[Loader]
    │  Input: DDL statements + parsed records + target config
    │  Steps:
    │    1. Connect to target database
    │    2. Execute CREATE TABLE IF NOT EXISTS (idempotent)
    │    3. For each resource type with data:
    │       a. Delete existing records for patient_id (idempotent)
    │       b. Insert new records
    │    4. Report: tables created, rows loaded per type, errors
    │
    ▼
[Result]
    Structured tables in PostgreSQL or BigQuery
    Ready for SQL queries from sql/ directory
```

### Key Data Characteristics (from sample data analysis)

| Characteristic | Finding | Implication |
|----------------|---------|-------------|
| Total resource types | 21 | DDL generator must handle all 21; 5 will be empty for some customers |
| Records per patient | ~1,187 across 16 types | Small per-patient; batch loading is fine, no streaming needed |
| File size per patient | ~880KB JSON | Fits in memory easily; no need for streaming JSON parsers |
| Value types | 99% strings, 2 fields have int/float | Default all columns to TEXT/STRING, override only `medication_statement_dose_value` and `vital_sign_observation_value` |
| Date formats | Mixed: `2011-05-28T16:41:11+0000`, `1970-12-26T00:00:00`, `2025-11-01 18:30:00.000000+00:00` | Store as TEXT/STRING, not TIMESTAMP; customers parse downstream |
| ID fields | Every resource has `patient_id`; most have a resource-specific `*_id` | `patient_id` is universal partition key for delete-and-replace |
| Empty types | allergies, coverages, familyMemberHistories, immunizations, socialHistories | Create tables even for empty types (schema readiness); skip data load |
| Comma-separated IDs | `encounter_type_code`, `condition_id_references`, etc. contain comma-delimited values | Store as TEXT; do NOT try to normalize into arrays at pipeline level |

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-100 patients | Current design is fine. Single-threaded sequential loading. ~100K records total. Completes in seconds. |
| 100-10K patients | Add batch inserts (execute_values for Postgres, load_table_from_json for BigQuery). Consider parallel loading by patient. Connection pooling. |
| 10K+ patients | Out of scope per PROJECT.md. Would need: orchestration (Airflow), chunked file processing, BigQuery load jobs instead of streaming inserts. |

### Scaling Priorities

1. **First bottleneck:** Individual INSERT statements per record. Fix with batch inserts (`execute_values` for PostgreSQL, `load_table_from_json` for BigQuery). Implement from the start.
2. **Second bottleneck:** Sequential patient processing. Fix with concurrent loading (threading or asyncio). Defer until customer need is demonstrated.

## Anti-Patterns

### Anti-Pattern 1: SQLAlchemy ORM for Simple Pipeline Loading

**What people do:** Import SQLAlchemy, define ORM models for all 21 resource types, use session.add() to insert records.
**Why it's wrong:** Massive overhead for a pipeline that does flat INSERT/DELETE operations. ORM models add ~500 lines of boilerplate for 21 tables with no behavioral benefit. SQLAlchemy's connection pooling and query building add complexity the customer must understand. The schema is derived from JSON, not defined in Python classes.
**Do this instead:** Use psycopg2/psycopg directly for PostgreSQL and google-cloud-bigquery client for BigQuery. Build SQL strings from the inferred schema. Keep it transparent and debuggable.

### Anti-Pattern 2: Normalizing Comma-Separated Values into Arrays or Join Tables

**What people do:** See fields like `encounter_type_code: "185347001, 185347001"` and create normalized junction tables or PostgreSQL arrays.
**Why it's wrong:** The flat format is intentionally denormalized by Particle. Normalizing it reintroduces complexity that customers must understand. Different customers have different normalization needs. The pipeline scope is "raw tables only" per PROJECT.md.
**Do this instead:** Store as TEXT/STRING exactly as received. Document the comma-separated pattern. Let customers normalize downstream in their own dbt models or views.

### Anti-Pattern 3: Storing Dates as TIMESTAMP/DATE Types

**What people do:** Parse date strings like `2011-05-28T16:41:11+0000` into TIMESTAMP columns, assuming consistent formatting.
**Why it's wrong:** Sample data shows at least 3 date formats across resource types. Some "date" fields contain empty strings. Parsing failures would block the entire pipeline. Type coercion belongs downstream, not in the ingestion layer.
**Do this instead:** Store all date-like fields as TEXT/STRING. Include comments in DDL noting which fields contain date values. Provide example CAST expressions in the SQL query library.

### Anti-Pattern 4: Dynamic Schema Detection on Every Load

**What people do:** Inspect every batch of JSON to dynamically detect schema changes and ALTER TABLE accordingly.
**Why it's wrong:** Adds complexity and unpredictability. ALTER TABLE on BigQuery has limitations (cannot change column types, cannot remove columns). Schema drift across customers is a support nightmare.
**Do this instead:** Define schemas statically from the known 21 resource types. Use the sample data to establish the baseline. Add a `--strict` flag that warns on unexpected fields rather than silently adding columns. Extra fields go into a catch-all `_extra_fields` JSON/TEXT column if needed.

### Anti-Pattern 5: Using dlt, Airbyte, or Other Pipeline Frameworks

**What people do:** Reach for dlt, Airbyte, Singer, or Meltano to handle the PostgreSQL/BigQuery loading.
**Why it's wrong for this use case:** This is a customer-facing accelerator, not an internal data team tool. Adding a framework dependency means: (a) customers must learn the framework, (b) framework version conflicts with customer environments, (c) framework abstractions hide what the pipeline actually does, (d) debugging requires framework knowledge. The total data volume (21 tables, ~1K records per patient) does not justify framework overhead.
**Do this instead:** Use the database client libraries directly (psycopg2 + google-cloud-bigquery). Keep the total dependency count minimal. Customers can see exactly what SQL is being executed.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **Particle Health API** | Reuse existing `ParticleHTTPClient` from `particle-health-starters/src/particle/` | Import as dependency or copy the core module. API client is already production-quality with auth, retry, PHI redaction. |
| **PostgreSQL** | `psycopg2-binary` (or `psycopg[binary]`) | Use `psycopg2` for maximum compatibility across customer environments. Connection via standard `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` env vars. |
| **BigQuery** | `google-cloud-bigquery` Python client | Service account JSON key or Application Default Credentials. Project ID and dataset via env vars. |
| **Docker** | Docker Compose for local PostgreSQL | Simple `docker-compose.yml` with postgres:16 image, health check, volume mount for DDL. |
| **Terraform** | HCL for BigQuery provisioning | Minimal: `google_bigquery_dataset` + `google_bigquery_table` resources. Service account with `bigquery.dataEditor` role. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **CLI -> Parser** | Function call: `parse_flat_data(json_data: dict) -> dict[str, list[dict]]` | Synchronous, in-memory. Parser is pure function, no side effects. |
| **Parser -> Schema** | Function call: `infer_schema(parsed: dict[str, list[dict]]) -> dict[str, dict[str, str]]` | Synchronous, pure function. Returns column->type mapping per table. |
| **Schema -> DDL** | Function call: `generate_ddl(schema: dict, dialect: str) -> list[str]` | Synchronous, pure function. Returns SQL strings. |
| **DDL -> Loader** | Method call: `loader.create_tables(ddl_statements)` | Side effect: executes DDL against database. |
| **Parser -> Loader** | Method call: `loader.load_records(table_name, records)` | Side effect: inserts/upserts records into database. |
| **CLI -> Loader** | Factory: `create_loader(config) -> DatabaseLoader` | Returns PostgresLoader or BigQueryLoader based on config. |

## Build Order (Dependency Chain)

The architecture has a clear left-to-right dependency chain. Build in this order:

```
Phase 1: Foundation (no external dependencies)
  ├── config.py        (env var loading)
  ├── parser.py        (JSON splitting)
  ├── schema.py        (type inference)
  └── exceptions.py    (error types)

Phase 2: DDL Generation (depends on Phase 1)
  ├── ddl.py           (generates SQL from schema)
  └── ddl/ files       (static DDL output for both dialects)

Phase 3: PostgreSQL Loading (depends on Phase 1 + 2)
  ├── loader/base.py   (abstract interface)
  ├── loader/postgres.py (PostgreSQL implementation)
  └── docker-compose.yml (local PostgreSQL)

Phase 4: BigQuery Loading (depends on Phase 1 + 2)
  ├── loader/bigquery.py (BigQuery implementation)
  └── terraform/        (BigQuery provisioning)

Phase 5: SQL Query Library (independent, can parallel with 3/4)
  ├── sql/clinical/    (patient summaries, lab trends, ...)
  └── sql/operational/ (coverage, completeness, ...)

Phase 6: CLI + Integration (depends on all above)
  ├── cli.py           (orchestrates everything)
  └── README.md        (customer documentation)
```

**Key insight:** Phases 1-2 are pure Python with zero external dependencies. They can be built and tested with just the sample data JSON file. Phase 3 needs Docker. Phase 4 needs a GCP project. Phase 5 is SQL-only and can be written in parallel. This ordering minimizes blocked work and lets early phases validate the data model before committing to database-specific implementations.

## Sources

- Particle Health sample data analysis: `/Users/sangyetsakorshika/Documents/GitHub/particle-connect/particle-health-starters/sample-data/flat_data.json` (21 resource types, 1,187 records, ~880KB) [HIGH confidence - direct observation]
- Existing codebase architecture: `/Users/sangyetsakorshika/Documents/GitHub/particle-connect/.planning/codebase/ARCHITECTURE.md` [HIGH confidence - direct observation]
- [PostgreSQL ON CONFLICT upsert](https://www.prisma.io/dataguide/postgresql/inserting-and-modifying-data/insert-on-conflict) [MEDIUM confidence - official Prisma docs]
- [BigQuery MERGE statement for upserts](https://hevodata.com/learn/bigquery-upsert/) [MEDIUM confidence - multiple sources agree]
- [BigQuery DDL reference](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language) [HIGH confidence - Google official docs]
- [Idempotent data pipeline patterns](https://www.startdataengineering.com/post/why-how-idempotent-data-pipeline/) [MEDIUM confidence - well-regarded data engineering source]
- [ETL pipeline project structure best practices](https://medium.com/@aliakbarhosseinzadeh/structuring-an-etl-pipeline-project-best-practices-5ed1e4d5a601) [LOW confidence - single blog post, but patterns verified against multiple sources]
- [Python CLI tools: Click, Typer, argparse](https://inventivehq.com/blog/python-cli-tools-guide) [MEDIUM confidence - multiple sources agree]
- [Psycopg2 vs psycopg3 benchmark](https://www.spherex.dev/psycopg-2-vs-psycopg3/) [MEDIUM confidence - independent benchmark]
- [PostgreSQL type mapping to BigQuery](https://blog.panoply.io/convert-postgresql-queries-into-bigquery-sql) [MEDIUM confidence - verified against BigQuery docs]
- [bigquery-schema-generator on PyPI](https://pypi.org/project/bigquery-schema-generator/) [HIGH confidence - PyPI official]

---
*Architecture research for: Particle Flat Data Pipeline*
*Researched: 2026-02-07*
