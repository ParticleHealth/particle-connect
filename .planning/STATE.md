# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-07)

**Core value:** Customers go from raw Particle flat data to queryable structured tables with useful analytics queries -- working from a clean checkout with zero code changes beyond configuration.
**Current focus:** Phase 4: Cloud Deployment (in progress)

## Current Position

Phase: 4 of 5 (Cloud Mode)
Plan: 2 of 3 in current phase
Status: In progress
Last activity: 2026-02-08 -- Completed 04-02-PLAN.md (BigQuery loader module and CLI wiring)

Progress: [########..] 80% (12/15 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 12
- Average duration: 2.7min
- Total execution time: 32min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Schema Foundation | 3/3 | 8min | 2.7min |
| 2. Local Pipeline | 4/4 | 9min | 2.3min |
| 3. Analytics Queries | 3/3 | 8min | 2.7min |
| 4. Cloud Mode | 2/3 | 7min | 3.5min |

**Recent Trend:**
- Last 5 plans: 03-02 (2min), 03-03 (3min), 04-01 (2min), 04-02 (5min)
- Trend: stable (04-02 slightly longer due to optional dependency handling)

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: 5 phases derived from requirement clusters (Schema -> Local Pipeline -> Analytics -> Cloud -> API)
- Roadmap: Phase 3 (Analytics) can run in parallel with Phase 2 (Local Pipeline) after Phase 1 completes
- 01-01: Stdlib-only dependencies for maximum portability (no pydantic, no structlog)
- 01-01: python-dotenv supported as optional import, not required
- 01-01: LOG_LEVEL validation added alongside DDL_DIALECT validation
- 01-02: Schema inspector scans ALL records per resource type to discover full column set
- 01-02: Column order preserves JSON key insertion order from Particle API (not alphabetical)
- 01-02: camelCase aI prefix special-cased to produce ai_ not a_i_
- 01-03: All columns use single type per dialect (TEXT/STRING) -- ELT approach
- 01-03: All column names quoted unconditionally to handle SQL reserved words
- 01-03: Empty resource types get commented-out placeholders, not empty tables
- 01-03: DDL files committed as static reviewable artifacts, not gitignored
- 02-01: python-dotenv promoted from optional to required dependency for CLI .env loading
- 02-01: compose.yaml (Compose V2, no version key) with direct DDL bind mount
- 02-01: PG_* env vars with defaults matching compose.yaml for zero-config local dev
- 02-02: Transaction scope per-patient per-resource-type for failure isolation
- 02-02: Column ordering uses ResourceSchema.columns as single source of truth
- 02-02: All SQL identifiers quoted via psycopg.sql.Identifier for reserved word safety
- 02-03: Single-command Typer app (auto-promoted) for simpler UX
- 02-03: Deferred imports inside command functions for faster --help
- 02-03: typer.echo for user messages, logging for debug/operational output
- 02-04: Quality analysis operates on Python dicts, not database -- works even if DB write partially failed
- 02-04: rich added as explicit dependency even though typer pulls it in -- direct import requires explicit dep
- 02-04: README targets 5-minute time-to-value with numbered Quick Start steps
- 03-01: Hardcoded sample patient_id with replacement comments for immediate runnability
- 03-01: UNION ALL pattern for care team aggregation from 3 sources (encounters, medications, procedures)
- 03-01: Commented-out LOINC reference range CASE block for customer customization
- 03-01: BigQuery uses PARSE_TIMESTAMP with %z for +0000 offsets (not SAFE_CAST)
- 03-02: UNION ALL subquery pattern for data_completeness scorecard across 16 tables
- 03-02: Section-tagged UNION ALL for ai_output_summary combining detail + summary rows
- 03-02: Three PARSE_TIMESTAMP format strings for BigQuery record_freshness (%z, %E*SZ, %E*S)
- 03-02: Dual-query file pattern for data_provenance (summary + detail in one file)
- 03-03: Temporal join (BETWEEN) for labs-by-encounter since labs have no encounter FK
- 03-03: Encounter bridge pattern for medications-by-problem via condition_id_references + practitioner_role_id_references
- 03-03: LEFT JOIN for procedures-by-encounter since encounter_reference_id is NULL in sample data
- 03-03: Commented-out alternative queries for data quality edge cases
- 03-03: README catalogs all 15 queries with requirement IDs, descriptions, scope, and known limitations
- 04-01: for_each with locals map for 21 tables -- single resource block, DRY
- 04-01: All columns STRING/NULLABLE via jsonencode -- matches DDL ELT approach
- 04-01: 5 empty tables created with patient_id placeholder for future data
- 04-01: deletion_protection=false and delete_contents_on_destroy=true for accelerator use
- 04-01: dataEditor at dataset level, jobUser at project level -- minimum privilege IAM
- 04-02: google-cloud-bigquery as optional dependency (not required for postgres-only users)
- 04-02: try/except ImportError with bigquery=None fallback for testability without GCP package
- 04-02: CLI import of bq_loader wrapped in try/except Exception for graceful degradation
- 04-02: sys.modules mock approach in tests to avoid requiring google-cloud-bigquery

### Pending Todos

None.

### Blockers/Concerns

- Docker e2e verification deferred (Docker Desktop not running during 02-03 execution). Should be verified when Docker is next available.

## Session Continuity

Last session: 2026-02-08
Stopped at: Completed 04-02-PLAN.md (BigQuery loader module and CLI wiring). Phase 4 plan 2 of 3 done.
Resume file: None
