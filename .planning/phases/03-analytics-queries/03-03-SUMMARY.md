---
phase: 03-analytics-queries
plan: 03
subsystem: database
tags: [sql, postgresql, bigquery, cross-cutting, temporal-join, analytics]

# Dependency graph
requires:
  - phase: 01-schema-foundation
    provides: DDL with all-TEXT/STRING columns and quoted identifiers
  - phase: 03-analytics-queries (plans 01, 02)
    provides: Clinical and operational query patterns establishing header template convention
provides:
  - 3 cross-cutting SQL queries in both PostgreSQL and BigQuery dialects (6 files total)
  - Query catalog README documenting all 15 analytics queries
  - Temporal join pattern for labs-to-encounters (no FK available)
  - Comma-separated reference field exploding pattern for condition/practitioner linkage
affects: [04-cloud-deployment, 05-api-layer]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Temporal join via BETWEEN for tables lacking FK relationships"
    - "string_to_array/SPLIT + unnest/UNNEST for comma-separated multi-value fields"
    - "Bridge join through intermediate tables (encounters) to connect unrelated entities"
    - "Commented-out alternative queries for data quality edge cases"

key-files:
  created:
    - particle-flat-observatory/queries/postgres/cross-cutting/labs_by_encounter.sql
    - particle-flat-observatory/queries/postgres/cross-cutting/medications_by_problem.sql
    - particle-flat-observatory/queries/postgres/cross-cutting/procedures_by_encounter.sql
    - particle-flat-observatory/queries/bigquery/cross-cutting/labs_by_encounter.sql
    - particle-flat-observatory/queries/bigquery/cross-cutting/medications_by_problem.sql
    - particle-flat-observatory/queries/bigquery/cross-cutting/procedures_by_encounter.sql
    - particle-flat-observatory/queries/README.md
  modified: []

key-decisions:
  - "Temporal join for labs-by-encounter since labs have no encounter FK"
  - "Encounter bridge pattern for medications-by-problem via condition_id_references and practitioner_role_id_references"
  - "LEFT JOIN for procedures-by-encounter since encounter_reference_id is NULL in sample data"
  - "Alternative queries provided as commented-out blocks for data quality edge cases"
  - "README catalogs all 15 queries with requirement IDs, descriptions, scope, and known limitations"

patterns-established:
  - "Temporal join: timestamp BETWEEN start_ts AND end_ts for cross-table associations without FK"
  - "Comma-separated field explode: string_to_array/unnest (PG) vs SPLIT/UNNEST (BQ)"
  - "Bridge join: entity A -> encounters -> entity B via shared encounter context"
  - "NULL FK documentation: queries work when FK populated, with commented temporal alternative"

# Metrics
duration: 3min
completed: 2026-02-08
---

# Phase 3 Plan 3: Cross-Cutting Queries and README Catalog Summary

**3 cross-cutting analytics queries (temporal join, encounter bridge, FK join) in both PostgreSQL and BigQuery dialects, plus a README cataloging all 15 analytics queries**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-08T14:16:56Z
- **Completed:** 2026-02-08T14:20:05Z
- **Tasks:** 2
- **Files created:** 7

## Accomplishments
- Labs-by-encounter query using temporal join (BETWEEN) to associate labs with encounters -- the most valuable cross-cutting pattern since labs have no encounter FK
- Medications-by-problem query bridging through encounters via comma-separated condition_id_references and practitioner_role_id_references fields
- Procedures-by-encounter query with direct FK join (LEFT JOIN handles NULL encounter_reference_id) plus commented-out temporal join alternative
- Complete README catalog documenting all 15 queries across 3 categories with requirement IDs, descriptions, scope, sample data notes, and known limitations

## Task Commits

Each task was committed atomically:

1. **Task 1: Create cross-cutting queries (both dialects)** - `5d60422` (feat)
2. **Task 2: Create queries README catalog** - `a296035` (docs)

## Files Created
- `particle-flat-observatory/queries/postgres/cross-cutting/labs_by_encounter.sql` - CROSS-01: Labs matched to encounters via timestamp overlap
- `particle-flat-observatory/queries/postgres/cross-cutting/medications_by_problem.sql` - CROSS-02: Medications mapped to conditions via encounter bridge
- `particle-flat-observatory/queries/postgres/cross-cutting/procedures_by_encounter.sql` - CROSS-03: Procedures joined to encounters via FK + practitioner lookup
- `particle-flat-observatory/queries/bigquery/cross-cutting/labs_by_encounter.sql` - CROSS-01 BigQuery dialect
- `particle-flat-observatory/queries/bigquery/cross-cutting/medications_by_problem.sql` - CROSS-02 BigQuery dialect
- `particle-flat-observatory/queries/bigquery/cross-cutting/procedures_by_encounter.sql` - CROSS-03 BigQuery dialect
- `particle-flat-observatory/queries/README.md` - Query catalog for all 15 analytics queries

## Decisions Made
- **Temporal join for labs-by-encounter:** Labs have no encounter FK in Particle flat data. Used timestamp BETWEEN to match labs occurring within encounter time windows. This is the correct approach per research findings.
- **Encounter bridge for medications-by-problem:** No direct medication-to-condition FK exists. Bridged through encounters (which reference conditions via condition_id_references) and practitioners (shared between encounters and medications). Also provided a simpler CROSS JOIN alternative as a commented-out block.
- **LEFT JOIN for procedures-by-encounter:** encounter_reference_id exists on procedures but is NULL for all sample data. Used LEFT JOIN so query works when FK is populated while still returning results (procedure + practitioner info) when it is NULL.
- **Commented-out alternative queries:** Both medications_by_problem and procedures_by_encounter include alternative query approaches in comments, giving customers options for different data quality scenarios.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 3 (Analytics Queries) is now complete: 15 queries across 3 categories in both dialects
- All queries follow consistent header template with hardcoded sample patient_id and parameterized form
- README provides complete catalog for customer discovery
- Ready for Phase 4 (Cloud Deployment) which will use BigQuery dialect queries

---
*Phase: 03-analytics-queries*
*Plan: 03*
*Completed: 2026-02-08*
