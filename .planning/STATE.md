# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-07)

**Core value:** Customers go from raw Particle flat data to queryable structured tables with useful analytics queries -- working from a clean checkout with zero code changes beyond configuration.
**Current focus:** Phase 3: Analytics Queries (in progress)

## Current Position

Phase: 3 of 5 (Analytics Queries)
Plan: 1 of 3 in current phase
Status: In progress
Last activity: 2026-02-08 -- Completed 03-01-PLAN.md (clinical analytics queries)

Progress: [#####.....] 53% (8/15 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 8
- Average duration: 2.5min
- Total execution time: 20min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Schema Foundation | 3/3 | 8min | 2.7min |
| 2. Local Pipeline | 4/4 | 9min | 2.3min |
| 3. Analytics Queries | 1/3 | 3min | 3.0min |

**Recent Trend:**
- Last 5 plans: 02-02 (2min), 02-03 (3min), 02-04 (3min), 03-01 (3min)
- Trend: stable

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

### Pending Todos

None.

### Blockers/Concerns

- Docker e2e verification deferred (Docker Desktop not running during 02-03 execution). Should be verified when Docker is next available.

## Session Continuity

Last session: 2026-02-08
Stopped at: Completed 03-01-PLAN.md (clinical analytics queries)
Resume file: None
