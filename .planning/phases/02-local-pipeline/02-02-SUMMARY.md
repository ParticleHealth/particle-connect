---
phase: 02-local-pipeline
plan: 02
subsystem: database
tags: [psycopg, postgres, loader, idempotent, sql-injection-safe]

# Dependency graph
requires:
  - phase: 01-schema-foundation
    provides: ResourceSchema dataclass with columns/table_name for column ordering
  - phase: 02-local-pipeline
    plan: 01
    provides: psycopg dependency, Docker Compose PostgreSQL, PG_* env var conventions
provides:
  - PostgreSQL loader with idempotent delete+insert per patient_id per resource type
  - get_connection_string() for building PostgreSQL URI from env vars
  - load_resource() for transactional per-patient loading
  - load_all() for orchestrating loading across all resource types
affects: [02-03, 02-04]

# Tech tracking
tech-stack:
  added: []
  patterns: [psycopg.sql for safe dynamic SQL, conn.transaction() for transactional semantics, delete+insert idempotency pattern]

key-files:
  created: [particle-flat-observatory/src/observatory/loader.py, particle-flat-observatory/tests/test_loader.py]
  modified: [particle-flat-observatory/src/observatory/__init__.py]

key-decisions:
  - "Transaction scope is per-patient per-resource-type, not per-entire-load -- failure isolation"
  - "Column ordering uses ResourceSchema.columns as single source of truth (matches DDL)"
  - "All SQL identifiers (table names, column names) quoted via psycopg.sql.Identifier -- handles reserved words"
  - "Records with missing columns get None via dict.get() -- graceful handling of sparse data"

patterns-established:
  - "Idempotent loading: DELETE WHERE patient_id = %s then INSERT within single transaction"
  - "Safe dynamic SQL: psycopg.sql.Identifier for identifiers, sql.Placeholder for values"
  - "Per-patient grouping: load_all groups records by patient_id before calling load_resource"

# Metrics
duration: 2min
completed: 2026-02-08
---

# Phase 2 Plan 2: PostgreSQL Loader Summary

**Idempotent delete+insert loader using psycopg 3 with safe dynamic SQL, per-patient transactions, and 13 unit tests**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-08T12:48:34Z
- **Completed:** 2026-02-08T12:50:27Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- PostgreSQL loader with idempotent delete+insert per patient_id per resource type
- All SQL uses psycopg.sql.Identifier for safe dynamic identifier quoting (handles SQL reserved words like "type", "text", "status")
- 13 unit tests verify loader behavior without requiring a running PostgreSQL instance
- Zero regressions: all 86 tests pass (73 existing + 13 new)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create PostgreSQL loader module** - `a068ba9` (feat)
2. **Task 2: Create loader unit tests** - `0436f24` (test)

## Files Created/Modified
- `particle-flat-observatory/src/observatory/loader.py` - PostgreSQL loader with get_connection_string(), load_resource(), load_all()
- `particle-flat-observatory/tests/test_loader.py` - 13 unit tests for loader module using mocked connections
- `particle-flat-observatory/src/observatory/__init__.py` - Added loader exports (get_connection_string, load_resource, load_all)

## Decisions Made
- Transaction scope is per-patient per-resource-type (not per-entire-load) for failure isolation -- a failure loading one resource type does not roll back others
- Column ordering uses ResourceSchema.columns as single source of truth, matching DDL column order
- All SQL identifiers quoted via psycopg.sql.Identifier to handle reserved words safely
- Records missing columns get None via dict.get() for graceful sparse data handling

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Loader module ready for CLI integration in Plan 02-03
- load_all() accepts connection + data + schemas, ready to be wired into CLI pipeline
- get_connection_string() uses same PG_* env vars as compose.yaml for zero-config local dev

---
*Phase: 02-local-pipeline*
*Completed: 2026-02-08*
