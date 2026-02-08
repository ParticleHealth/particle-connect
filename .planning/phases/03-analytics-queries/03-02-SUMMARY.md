---
phase: 03-analytics-queries
plan: 02
subsystem: database
tags: [sql, postgresql, bigquery, analytics, operational, data-quality, provenance]

# Dependency graph
requires:
  - phase: 01-schema-foundation
    provides: DDL definitions for all 16 resource types (TEXT/STRING columns)
provides:
  - 5 operational analytics queries in PostgreSQL dialect (OPS-01 through OPS-05)
  - 5 operational analytics queries in BigQuery dialect (OPS-01 through OPS-05)
  - Data completeness scorecard across all 16 resource types
  - Source coverage breakdown via record_sources + sources join
  - Record freshness reporting with dialect-specific timestamp parsing
  - Data provenance tracing (summary + detail) per patient
  - AI output summary with citation counts
affects: [04-cloud-deployment, queries-README]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "UNION ALL for multi-table aggregation (data_completeness, record_freshness)"
    - "CTE for resource_type_totals with percentage calculation (source_coverage)"
    - "LTRIM for vital_sign_observation_time leading comma before timestamp parse"
    - "PARSE_TIMESTAMP with format strings for BigQuery timestamp handling"
    - "Dual-query file pattern: summary + detail in one file (data_provenance)"
    - "UNION ALL of detail + summary CTEs in single result set (ai_output_summary)"

key-files:
  created:
    - particle-flat-observatory/queries/postgres/operational/data_completeness.sql
    - particle-flat-observatory/queries/postgres/operational/source_coverage.sql
    - particle-flat-observatory/queries/postgres/operational/record_freshness.sql
    - particle-flat-observatory/queries/postgres/operational/data_provenance.sql
    - particle-flat-observatory/queries/postgres/operational/ai_output_summary.sql
    - particle-flat-observatory/queries/bigquery/operational/data_completeness.sql
    - particle-flat-observatory/queries/bigquery/operational/source_coverage.sql
    - particle-flat-observatory/queries/bigquery/operational/record_freshness.sql
    - particle-flat-observatory/queries/bigquery/operational/data_provenance.sql
    - particle-flat-observatory/queries/bigquery/operational/ai_output_summary.sql
  modified: []

key-decisions:
  - "UNION ALL with subquery wrapper for data_completeness -- avoids 16 separate CTEs, keeps column alignment clean"
  - "ai_output_summary uses section column ('detail'/'summary') to combine per-output and type-level rows in one result"
  - "data_provenance structured as two separate queries in one file -- summary first, detail second -- for different use cases"
  - "BigQuery record_freshness uses three PARSE_TIMESTAMP format strings: %z for offsets, %E*SZ for fractional+Z, %E*S for microseconds"

patterns-established:
  - "Standardized SQL file header: Query name, Requirement ID, Dialect, Description, Parameters, Tables"
  - "PostgreSQL: double-quoted identifiers, CAST AS TIMESTAMPTZ for timestamps"
  - "BigQuery: backtick identifiers, PARSE_TIMESTAMP with format strings for timestamps"
  - "Operational queries are global (no patient_id) except data_provenance which is patient-scoped"

# Metrics
duration: 2min
completed: 2026-02-08
---

# Phase 3 Plan 02: Operational Analytics Queries Summary

**10 SQL files (5 PostgreSQL + 5 BigQuery) covering data completeness, source coverage, record freshness, data provenance, and AI output summaries with correct timestamp handling per dialect**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-08T14:14:57Z
- **Completed:** 2026-02-08T14:17:30Z
- **Tasks:** 2
- **Files created:** 10

## Accomplishments

- OPS-01: Data completeness scorecard reporting record counts and key field population percentages for all 16 resource types
- OPS-02: Source coverage breakdown showing which of 6 data sources contributed to which resource types via record_sources + sources join
- OPS-03: Record freshness showing most recent timestamp per resource type, with LTRIM handling for vital_sign_observation_time leading comma
- OPS-04: Data provenance tracing clinical records back to originating sources (summary + detail views)
- OPS-05: AI output summary showing 22 outputs (21 DISCHARGE_SUMMARY, 1 PATIENT_HISTORY) with citation counts from ai_citations
- All queries available in both PostgreSQL and BigQuery dialects with correct syntax differences

## Task Commits

Each task was committed atomically:

1. **Task 1: Create PostgreSQL operational queries** - `a09199c` (feat)
2. **Task 2: Create BigQuery operational queries** - `e848da2` (feat)

## Files Created

- `particle-flat-observatory/queries/postgres/operational/data_completeness.sql` - OPS-01: Record counts and key field percentages for 16 resource types
- `particle-flat-observatory/queries/postgres/operational/source_coverage.sql` - OPS-02: Source-to-resource-type coverage with percentage of type
- `particle-flat-observatory/queries/postgres/operational/record_freshness.sql` - OPS-03: Most recent timestamp per resource type
- `particle-flat-observatory/queries/postgres/operational/data_provenance.sql` - OPS-04: Trace records to sources (summary + detail)
- `particle-flat-observatory/queries/postgres/operational/ai_output_summary.sql` - OPS-05: AI outputs with citation counts
- `particle-flat-observatory/queries/bigquery/operational/data_completeness.sql` - OPS-01 BigQuery dialect
- `particle-flat-observatory/queries/bigquery/operational/source_coverage.sql` - OPS-02 BigQuery dialect
- `particle-flat-observatory/queries/bigquery/operational/record_freshness.sql` - OPS-03 BigQuery dialect with PARSE_TIMESTAMP
- `particle-flat-observatory/queries/bigquery/operational/data_provenance.sql` - OPS-04 BigQuery dialect with @patient_id parameterization comment
- `particle-flat-observatory/queries/bigquery/operational/ai_output_summary.sql` - OPS-05 BigQuery dialect

## Decisions Made

- **UNION ALL subquery pattern for data_completeness:** Wrapped 16 UNION ALL segments in a subquery with computed percentage column, avoiding 16 separate CTEs while keeping the column alignment clean.
- **Section-tagged UNION ALL for ai_output_summary:** Used a `section` column with values 'detail' and 'summary' to combine per-output detail rows with type-level summary rows in one result set. Allows customers to filter by section or view all together.
- **Two separate queries for data_provenance:** Rather than one complex query, the file contains a summary query (resource_type counts) and a detail query (full provenance trace), separated by clear comment blocks. This is more practical for customer use -- they pick the view they need.
- **Three PARSE_TIMESTAMP format strings for BigQuery record_freshness:** `%z` for timezone offset timestamps (encounters, problems, medications, labs, vital_signs, procedures), `%E*SZ` for fractional seconds + Z (ai_outputs), and `%E*S` for microsecond precision without Z (transitions).

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None -- no external service configuration required. These are static SQL files that can be run against any Particle flat data tables created by Phase 1 DDL.

## Next Phase Readiness

- Operational query directory structure established for both dialects
- Ready for Phase 3 Plan 03 (cross-cutting queries) to add queries in the cross-cutting/ subdirectories
- Query file header template and dialect conventions established for consistency across remaining query plans

---
*Phase: 03-analytics-queries*
*Completed: 2026-02-08*
