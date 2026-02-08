# Phase 2: Local Pipeline - Research

**Researched:** 2026-02-08
**Domain:** PostgreSQL loading, Docker Compose, CLI framework, data quality reporting
**Confidence:** HIGH

## Summary

Phase 2 transforms the Phase 1 schema foundation into a working end-to-end pipeline: Docker Compose spins up PostgreSQL, a CLI command loads flat JSON data into all 21 tables with idempotent delete+insert semantics, and a data quality report gives immediate feedback. The customer experience target is "clone to first query in under 5 minutes."

The standard stack for this phase is: **psycopg 3.3.x** (modern PostgreSQL driver), **typer 0.21.x** (CLI framework replacing argparse), **python-dotenv** (already optional in Phase 1), and the **official postgres:17 Docker image** with init script mounting. The existing Phase 1 modules (parser, normalizer, schema, ddl) provide the data pipeline foundation -- Phase 2 adds a loader module, CLI entry point, and Docker infrastructure.

**Primary recommendation:** Use psycopg 3 with `executemany()` for batch loading (sufficient for the data volumes in this accelerator), typer for a polished CLI with automatic help and env var support, and Docker Compose with `/docker-entrypoint-initdb.d/` for zero-config PostgreSQL setup.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| psycopg | 3.3.2 | PostgreSQL adapter | Modern Python 3 driver, 4x faster executemany than psycopg2, server-side parameter binding, active development. psycopg2 is maintenance-only. |
| psycopg[binary] | 3.3.2 | Pre-compiled C extension | No build tools required for customers. Just `pip install "psycopg[binary]"`. |
| typer | 0.21.1 | CLI framework | Type-hint-driven, automatic `--help` generation, env var support, rich error formatting. Customer-facing accelerator benefits from polished CLI. |
| python-dotenv | 1.x | .env file loading | Already optional in Phase 1. Typer + python-dotenv is the standard pattern for CLI config from .env files. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| rich | (bundled with typer) | Formatted terminal output | Data quality report tables, progress indicators, error formatting. Comes free with typer install. |
| postgres Docker image | 17-alpine | Local database | Docker Compose service. Use 17 (latest stable LTS), alpine variant for smaller image. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| psycopg 3 | psycopg2-binary | psycopg2 is maintenance-only, no new features. psycopg 3 has better performance and modern API. Only reason to use psycopg2: legacy codebase compatibility. |
| typer | argparse (stdlib) | argparse works but requires more boilerplate, no automatic env var support, no rich error display. Phase 1 used argparse for generate_ddl because it was stdlib-only. Phase 2 already adds psycopg as a dependency, so adding typer is minimal incremental cost. |
| typer | click | typer is built on click. Same power, less boilerplate via type hints. |
| python-dotenv | pydantic-settings | Overkill for env var loading. python-dotenv is already in the codebase as optional. |

**Installation:**
```bash
pip install "psycopg[binary]" typer python-dotenv
```

**pyproject.toml dependencies:**
```toml
dependencies = [
    "psycopg[binary]>=3.3.0",
    "typer>=0.21.0",
    "python-dotenv>=1.0.0",
]
```

## Architecture Patterns

### Recommended Project Structure
```
particle-flat-observatory/
├── docker-compose.yml            # PostgreSQL service definition
├── docker/
│   └── init/
│       └── 01-create-tables.sql  # Symlink or copy of ddl/postgres/create_all.sql
├── pyproject.toml                # Updated with new dependencies + CLI entry point
├── .env.example                  # Updated with PG connection vars
├── src/
│   └── observatory/
│       ├── __init__.py
│       ├── config.py             # Extended with PG settings
│       ├── parser.py             # Unchanged from Phase 1
│       ├── normalizer.py         # Unchanged from Phase 1
│       ├── schema.py             # Unchanged from Phase 1
│       ├── ddl.py                # Unchanged from Phase 1
│       ├── generate_ddl.py       # Unchanged from Phase 1
│       ├── loader.py             # NEW: PostgreSQL loading logic
│       ├── quality.py            # NEW: Data quality report generation
│       └── cli.py                # NEW: Typer CLI entry point
├── ddl/
│   ├── postgres/create_all.sql   # From Phase 1
│   └── bigquery/create_all.sql   # From Phase 1
└── sample-data/
    └── flat_data.json            # From Phase 1
```

### Pattern 1: Idempotent Delete+Insert per Patient per Resource Type

**What:** Within a single transaction per resource type, DELETE all rows matching the patient_id being loaded, then INSERT the new rows. This ensures re-running the pipeline produces identical results with no duplicates.

**When to use:** Every load operation. This is the core idempotency pattern.

**Why not UPSERT/ON CONFLICT:** The tables have no primary key or unique constraints (all TEXT columns, ELT approach). Delete+insert is simpler, requires no schema changes, and handles the case where columns change between loads.

**Example:**
```python
# Source: psycopg3 official docs + project requirements
import psycopg

def load_resource(
    conn: psycopg.Connection,
    table_name: str,
    columns: list[str],
    records: list[dict],
    patient_id: str,
) -> int:
    """Load records for one resource type, one patient. Idempotent."""
    if not records:
        return 0

    with conn.transaction():
        # Delete existing records for this patient in this table
        conn.execute(
            psycopg.sql.SQL("DELETE FROM {} WHERE \"patient_id\" = %s").format(
                psycopg.sql.Identifier(table_name)
            ),
            (patient_id,),
        )

        # Build INSERT with quoted column names
        col_ids = psycopg.sql.SQL(", ").join(
            psycopg.sql.Identifier(c) for c in columns
        )
        placeholders = psycopg.sql.SQL(", ").join(
            psycopg.sql.Placeholder() for _ in columns
        )
        insert_query = psycopg.sql.SQL(
            "INSERT INTO {} ({}) VALUES ({})"
        ).format(
            psycopg.sql.Identifier(table_name),
            col_ids,
            placeholders,
        )

        # Extract values in column order, defaulting missing keys to None
        rows = [
            tuple(record.get(col) for col in columns)
            for record in records
        ]
        conn.executemany(insert_query, rows)

    return len(records)
```

### Pattern 2: Typer CLI with Subcommands and Env Var Defaults

**What:** Use typer with `typer.Option(envvar="...")` for all configuration parameters. The CLI reads from .env via python-dotenv at startup, then allows command-line flags to override.

**When to use:** The main CLI entry point.

**Example:**
```python
# Source: Typer official docs (envvar support)
from typing import Annotated
import typer

app = typer.Typer(
    name="particle-pipeline",
    help="Particle Health flat data pipeline - load data into PostgreSQL or BigQuery",
    no_args_is_help=True,
)

@app.command()
def load(
    source: Annotated[str, typer.Option(
        help="Data source: 'file' or 'api'",
        envvar="PIPELINE_SOURCE",
    )] = "file",
    target: Annotated[str, typer.Option(
        help="Target database: 'postgres' or 'bigquery'",
        envvar="PIPELINE_TARGET",
    )] = "postgres",
    data_path: Annotated[str, typer.Option(
        help="Path to flat_data.json",
        envvar="FLAT_DATA_PATH",
    )] = "sample-data/flat_data.json",
):
    """Load Particle flat data into a target database."""
    ...
```

**Entry point in pyproject.toml:**
```toml
[project.scripts]
particle-pipeline = "observatory.cli:app"
```

### Pattern 3: Docker Compose PostgreSQL with Init Scripts

**What:** Mount the existing DDL SQL file into `/docker-entrypoint-initdb.d/` so tables are created on first startup. Use a named volume for persistence.

**When to use:** Local development setup.

**Example (compose.yaml):**
```yaml
services:
  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: observatory
      POSTGRES_PASSWORD: observatory
      POSTGRES_DB: observatory
    ports:
      - "${PG_PORT:-5432}:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./ddl/postgres/create_all.sql:/docker-entrypoint-initdb.d/01-create-tables.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U observatory -d observatory"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 10s

volumes:
  pgdata:
```

### Pattern 4: Connection String from Environment Variables

**What:** Build PostgreSQL connection from individual env vars (host, port, user, password, dbname) rather than a single DSN string. This matches the Docker Compose env var pattern and is more explicit for customers.

**Example:**
```python
def get_connection_string() -> str:
    """Build PostgreSQL connection string from environment variables."""
    host = os.environ.get("PG_HOST", "localhost")
    port = os.environ.get("PG_PORT", "5432")
    user = os.environ.get("PG_USER", "observatory")
    password = os.environ.get("PG_PASSWORD", "observatory")
    dbname = os.environ.get("PG_DATABASE", "observatory")
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
```

### Anti-Patterns to Avoid

- **Global autocommit mode:** Do not set `conn.autocommit = True` for loading operations. The delete+insert pattern MUST run within a transaction to prevent data loss if the insert fails after the delete.
- **Building SQL with string concatenation:** Always use `psycopg.sql` module for dynamic table/column names. Never use f-strings or .format() for SQL.
- **Single large transaction for all tables:** Commit per resource type, not per entire load. This way a failure in one resource type does not roll back all others.
- **Using COPY for this use case:** COPY cannot perform the delete+insert pattern within a single operation. executemany is sufficient for the data volumes here (hundreds to low thousands of records) and supports the transactional pattern.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI argument parsing with env var fallback | Custom argparse + os.environ wiring | typer with `envvar` parameter | Typer handles precedence (CLI > env > default) automatically, shows env vars in --help |
| SQL identifier quoting | f-string quoting with double quotes | `psycopg.sql.Identifier()` | Handles edge cases (reserved words, special chars) and prevents SQL injection |
| Terminal tables/formatting | print() with manual spacing | `rich.table.Table` (comes with typer) | Rich is already installed as a typer dependency. Professional output for data quality reports |
| Docker PostgreSQL init | Custom entrypoint script | `/docker-entrypoint-initdb.d/` mounting | Official postgres image handles init script execution, ordering, and idempotency (only runs on empty data dir) |
| Connection string building | Manual string formatting | `psycopg.conninfo.make_conninfo()` or simple f-string with env vars | psycopg provides conninfo utilities, but for this simple case env var assembly is acceptable |

**Key insight:** Phase 2 introduces the first external dependencies (psycopg, typer). This is justified because: (1) psycopg is the ONLY way to talk to PostgreSQL from Python, and (2) typer gives customer-facing polish (auto-help, env var support, rich errors) that would take hundreds of lines to replicate with argparse.

## Common Pitfalls

### Pitfall 1: Init Scripts Not Re-running After Volume Exists

**What goes wrong:** Customer runs `docker compose up`, stops the container, modifies the DDL, runs `docker compose up` again -- but tables are NOT recreated because the data volume already exists.

**Why it happens:** PostgreSQL Docker init scripts (`/docker-entrypoint-initdb.d/`) only run when the data directory is empty (first startup).

**How to avoid:** Document this clearly in README. Provide a reset command: `docker compose down -v && docker compose up -d` to destroy the volume and re-initialize. Consider adding a `--reset-db` CLI flag that drops and recreates tables.

**Warning signs:** Customer reports "my schema changes aren't taking effect" after modifying DDL.

### Pitfall 2: Missing patient_id in Some Resource Types

**What goes wrong:** The delete+insert pattern uses `WHERE patient_id = %s` but some resource types may not have a `patient_id` column (or it may be named differently, like `particle_patient_id`).

**Why it happens:** Particle flat data uses `patient_id` in most resource types but some use variations.

**How to avoid:** Check the DDL/schema to confirm which column name to use for each resource type. The sample data shows that all 16 non-empty resource types DO have a `patient_id` column. The `aICitations` table also has `particle_patient_id`. Use `patient_id` as the standard delete key for all tables.

**Warning signs:** DELETE statement affects 0 rows when it should have matched records.

### Pitfall 3: Transaction Isolation and Connection Behavior in psycopg 3

**What goes wrong:** Developer uses `with psycopg.connect(...) as conn:` expecting it to commit on exit (like psycopg2), but psycopg 3's `with` block CLOSES the connection on exit, and an uncommitted transaction is rolled back.

**Why it happens:** Breaking change from psycopg2. In psycopg 3, `with connection` = close connection, not commit transaction. Use `with conn.transaction()` for transaction scope.

**How to avoid:** Always use explicit `conn.transaction()` blocks for transactional work. The connection context manager is for cleanup, not transaction management.

**Warning signs:** Data appears to load (no errors) but the tables are empty after the script exits.

### Pitfall 4: Port Conflicts with Local PostgreSQL

**What goes wrong:** Customer already has PostgreSQL running on port 5432. Docker Compose fails with "port already in use."

**Why it happens:** Default PostgreSQL port is 5432, commonly already in use on developer machines.

**How to avoid:** Make the port configurable via `PG_PORT` env var in docker-compose.yml using `${PG_PORT:-5432}:5432` syntax. Document in .env.example.

**Warning signs:** Docker Compose error: "Bind for 0.0.0.0:5432 failed: port is already allocated."

### Pitfall 5: Empty Resource Type Tables with No Columns

**What goes wrong:** Phase 1 DDL has 5 empty resource types (allergies, coverages, familyMemberHistories, immunizations, socialHistories) with commented-out CREATE TABLE statements. If the loader tries to insert into these tables, it fails because they do not exist.

**Why it happens:** Empty resource types have no columns in sample data, so no CREATE TABLE was generated.

**How to avoid:** The loader should skip resource types with 0 records (already handled by parser returning empty lists). The DDL init script should be the committed `create_all.sql` which only creates tables that have columns. Empty resource types simply have no table -- this is correct behavior.

**Warning signs:** "relation does not exist" error for allergies, coverages, etc.

### Pitfall 6: Column Order Mismatch Between Schema and INSERT

**What goes wrong:** The INSERT statement columns don't match the order of values being inserted, causing data to land in wrong columns.

**Why it happens:** Relying on dict key ordering or column ordering that differs between schema inspection and INSERT construction.

**How to avoid:** Use the `ResourceSchema.columns` list as the single source of truth for column ordering. Both the DDL and the INSERT must use this exact order. Extract values from each record dict using the same column list.

**Warning signs:** Data loads but column values are swapped (e.g., patient_id contains a medication name).

## Code Examples

Verified patterns from official sources:

### psycopg 3 Connection and Transaction

```python
# Source: https://www.psycopg.org/psycopg3/docs/basic/usage.html
import psycopg

# Connection as context manager (closes on exit)
with psycopg.connect("postgresql://observatory:observatory@localhost:5432/observatory") as conn:
    # Transaction block (commits on success, rolls back on exception)
    with conn.transaction():
        conn.execute("DELETE FROM patients WHERE \"patient_id\" = %s", ("abc-123",))
        conn.execute(
            "INSERT INTO patients (\"patient_id\", \"given_name\") VALUES (%s, %s)",
            ("abc-123", "Jane"),
        )
    # Transaction is committed here

# Connection is closed here
```

### psycopg 3 Dynamic SQL with sql Module

```python
# Source: https://www.psycopg.org/psycopg3/docs/basic/from_pg2.html
from psycopg import sql

# Safe dynamic table/column names
query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
    sql.Identifier("patients"),
    sql.SQL(", ").join(sql.Identifier(c) for c in ["patient_id", "given_name"]),
    sql.SQL(", ").join(sql.Placeholder() for _ in ["patient_id", "given_name"]),
)
conn.execute(query, ("abc-123", "Jane"))
```

### psycopg 3 executemany for Batch Insert

```python
# Source: https://www.psycopg.org/psycopg3/docs/basic/usage.html
records = [
    ("abc-123", "Jane"),
    ("def-456", "John"),
]

query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
    sql.Identifier("patients"),
    sql.SQL(", ").join(sql.Identifier(c) for c in ["patient_id", "given_name"]),
    sql.SQL(", ").join(sql.Placeholder() for _ in ["patient_id", "given_name"]),
)

with conn.transaction():
    conn.executemany(query, records)
```

### Typer CLI with Env Var Support

```python
# Source: https://typer.tiangolo.com/tutorial/arguments/envvar/
from typing import Annotated
import typer

app = typer.Typer(
    name="particle-pipeline",
    help="Load Particle Health flat data into PostgreSQL or BigQuery.",
    no_args_is_help=True,
)

@app.command()
def load(
    source: Annotated[str, typer.Option(
        "--source", help="Data source: 'file' or 'api'",
    )] = "file",
    target: Annotated[str, typer.Option(
        "--target", help="Target database: 'postgres' or 'bigquery'",
    )] = "postgres",
    data_path: Annotated[str, typer.Option(
        "--data-path", help="Path to flat_data.json file",
        envvar="FLAT_DATA_PATH",
    )] = "sample-data/flat_data.json",
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output",
    )] = False,
):
    """Load Particle flat data into a target database.

    Examples:
        particle-pipeline load --source file --target postgres
        particle-pipeline load --data-path /path/to/data.json
    """
    ...

if __name__ == "__main__":
    app()
```

### Docker Compose with Init Script and Healthcheck

```yaml
# Source: Official postgres Docker image docs + Docker Compose docs
services:
  postgres:
    image: postgres:17-alpine
    container_name: observatory-postgres
    environment:
      POSTGRES_USER: observatory
      POSTGRES_PASSWORD: observatory
      POSTGRES_DB: observatory
    ports:
      - "${PG_PORT:-5432}:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./ddl/postgres/create_all.sql:/docker-entrypoint-initdb.d/01-create-tables.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U observatory -d observatory"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 10s
    restart: unless-stopped

volumes:
  pgdata:
```

### Data Quality Report with Rich Tables

```python
# Source: Rich library docs (bundled with typer)
from rich.console import Console
from rich.table import Table

def print_quality_report(results: dict) -> None:
    """Print a formatted data quality report to the terminal."""
    console = Console()
    table = Table(title="Data Quality Report")
    table.add_column("Table", style="cyan")
    table.add_column("Records", justify="right", style="green")
    table.add_column("Null %", justify="right")
    table.add_column("Date Range", style="dim")

    for name, stats in results.items():
        table.add_row(
            name,
            str(stats["count"]),
            f"{stats['null_pct']:.1f}%",
            stats.get("date_range", "n/a"),
        )

    console.print(table)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| psycopg2 / psycopg2-binary | psycopg (v3) with `psycopg[binary]` | Stable since 2023, recommended for new projects | 4x faster executemany, modern API, async support |
| docker-compose.yml (v2 syntax) | compose.yaml (Compose V2, no version: field) | Docker Compose V2 became default in 2023 | Use `compose.yaml` filename, no `version:` key at top |
| argparse for CLI | typer with type hints | typer 0.x series, stable since 2022 | Automatic help, env var support, rich error formatting |
| psycopg2 execute_values / execute_batch | psycopg 3 executemany (optimized internally) | psycopg 3 | No need for helpers -- native executemany is fast enough |

**Deprecated/outdated:**
- **psycopg2**: Maintenance-only, no new features. Use psycopg 3 for new projects.
- **docker-compose (v1 CLI)**: Replaced by `docker compose` (v2, integrated into Docker CLI). The `docker-compose` binary is deprecated.
- **version: "3.x" in compose files**: The `version` key is obsolete in Compose V2. Omit it entirely.

## Open Questions

Things that could not be fully resolved:

1. **Should the CLI command be `particle-pipeline load` (subcommand) or `particle-pipeline` (single command)?**
   - What we know: The requirements say `particle-pipeline load --source file --target postgres`. This implies a subcommand model, which leaves room for future commands (e.g., `particle-pipeline schema`, `particle-pipeline query`).
   - What's unclear: Whether future phases will add more CLI commands.
   - Recommendation: Use typer's subcommand pattern (`app.command()`) with `load` as the primary command. This is extensible and matches the requirement exactly. If only one command exists, typer still works fine -- it just shows `load` in the help text.

2. **Should the loader use COPY or executemany for INSERT?**
   - What we know: COPY is fastest (protocol-level bulk loading), but cannot be combined with DELETE in a single transaction easily. executemany in psycopg 3 is 4x faster than psycopg2 and handles hundreds/thousands of records efficiently.
   - What's unclear: Whether customer data volumes will be large enough to need COPY performance.
   - Recommendation: Use `executemany` for Phase 2. The sample data has ~1,200 total records across 16 tables. executemany handles this in milliseconds. COPY optimization can be added in Phase 5 (API ingestion) if needed for larger datasets.

3. **How to handle schema discovery at load time vs using committed DDL?**
   - What we know: Phase 1 generates DDL from sample data and commits it. At load time, we need column lists to build INSERT statements.
   - What's unclear: Should we re-run schema inspection on each load, or read the DDL, or hardcode column lists?
   - Recommendation: Re-run `inspect_schema()` from the parser output at load time. This is fast, always matches the actual data being loaded, and handles any column differences between the DDL and the data file. The DDL is the source of truth for table CREATION, but `inspect_schema()` is the source of truth for what columns exist in the data being loaded.

## Sources

### Primary (HIGH confidence)
- [psycopg 3 official docs - Usage](https://www.psycopg.org/psycopg3/docs/basic/usage.html) - Connection, cursor, transaction, executemany patterns
- [psycopg 3 official docs - Migration from pg2](https://www.psycopg.org/psycopg3/docs/basic/from_pg2.html) - Breaking changes, API differences
- [psycopg 3 official docs - COPY](https://www.psycopg.org/psycopg3/docs/basic/copy.html) - COPY protocol API
- [psycopg 3 official docs - Installation](https://www.psycopg.org/psycopg3/docs/basic/install.html) - Installation options, platform support
- [psycopg PyPI](https://pypi.org/project/psycopg/) - Version 3.3.2, Dec 2025
- [Typer official docs](https://typer.tiangolo.com/) - CLI framework features, env var support
- [Typer official docs - Environment Variables](https://typer.tiangolo.com/tutorial/arguments/envvar/) - envvar parameter for Options/Arguments
- [Typer official docs - Subcommands](https://typer.tiangolo.com/tutorial/subcommands/add-typer/) - add_typer pattern
- [Typer official docs - Packaging](https://typer.tiangolo.com/tutorial/package/) - pyproject.toml entry point
- [Typer PyPI](https://pypi.org/project/typer/) - Version 0.21.1, Jan 2026
- [PostgreSQL Docker image docs](https://github.com/docker-library/docs/blob/master/postgres/README.md) - Environment variables, init scripts, volumes
- [Docker Compose healthcheck patterns](https://github.com/peter-evans/docker-compose-healthcheck) - pg_isready healthcheck

### Secondary (MEDIUM confidence)
- [Tiger Data - psycopg2 vs psycopg3 benchmark](https://www.tigerdata.com/blog/psycopg2-vs-psycopg3-performance-benchmark) - 4x executemany improvement verified
- [Start Data Engineering - Idempotent pipelines](https://www.startdataengineering.com/post/why-how-idempotent-data-pipeline/) - Delete-write idempotency pattern
- [Docker docs - Pre-seeding databases](https://docs.docker.com/guides/pre-seeding/) - Official Docker guidance on init scripts

### Tertiary (LOW confidence)
- None -- all claims verified with primary or secondary sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All library versions verified on PyPI, APIs verified in official docs
- Architecture: HIGH - Patterns verified against official documentation for psycopg 3, typer, and Docker postgres image
- Pitfalls: HIGH - psycopg 3 transaction behavior verified in migration docs; Docker init script behavior verified in official image README
- Data quality report: MEDIUM - Healthcare data quality dimensions are well-established, but specific metrics for Particle flat data need to be defined during implementation based on available columns

**Research date:** 2026-02-08
**Valid until:** 2026-03-08 (30 days -- all technologies are stable)
