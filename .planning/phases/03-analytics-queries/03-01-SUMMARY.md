---
phase: 03-analytics-queries
plan: 01
subsystem: database
tags: [sql, postgresql, bigquery, clinical, loinc, analytics, cte]

# Dependency graph
requires:
  - phase: 01-schema-foundation
    provides: DDL with exact column names and all-TEXT/STRING ELT approach
provides:
  - 7 PostgreSQL clinical analytics queries (CLIN-01 through CLIN-07)
  - 7 BigQuery clinical analytics queries (CLIN-01 through CLIN-07)
  - Vital sign LOINC filtering pattern (true vitals vs lab-like observations)
  - Comma-separated field splitting pattern (string_to_array/SPLIT+UNNEST)
  - Leading comma timestamp fix pattern (LTRIM before CAST/PARSE_TIMESTAMP)
affects: [03-02 operational queries, 03-03 cross-cutting queries, 04-cloud-pipeline, queries README]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - CTE-based query structure for readability
    - Dual-dialect SQL (PostgreSQL double-quotes vs BigQuery backticks)
    - LOINC code filtering for vital sign classification
    - LTRIM leading comma fix for vital_sign_observation_time
    - string_to_array+unnest (PG) / SPLIT+UNNEST (BQ) for comma-separated fields
    - Commented reference range template for lab abnormal flagging

key-files:
  created:
    - particle-flat-observatory/queries/postgres/clinical/patient_summary.sql
    - particle-flat-observatory/queries/postgres/clinical/active_problems.sql
    - particle-flat-observatory/queries/postgres/clinical/medication_timeline.sql
    - particle-flat-observatory/queries/postgres/clinical/lab_results.sql
    - particle-flat-observatory/queries/postgres/clinical/vital_sign_trends.sql
    - particle-flat-observatory/queries/postgres/clinical/encounter_history.sql
    - particle-flat-observatory/queries/postgres/clinical/care_team.sql
    - particle-flat-observatory/queries/bigquery/clinical/patient_summary.sql
    - particle-flat-observatory/queries/bigquery/clinical/active_problems.sql
    - particle-flat-observatory/queries/bigquery/clinical/medication_timeline.sql
    - particle-flat-observatory/queries/bigquery/clinical/lab_results.sql
    - particle-flat-observatory/queries/bigquery/clinical/vital_sign_trends.sql
    - particle-flat-observatory/queries/bigquery/clinical/encounter_history.sql
    - particle-flat-observatory/queries/bigquery/clinical/care_team.sql
  modified: []

key-decisions:
  - "Hardcoded sample patient_id with replacement comments instead of parameterized queries for immediate runnability"
  - "UNION ALL pattern for care team aggregation from 3 sources (encounters, medications, procedures)"
  - "Commented-out LOINC reference range CASE block in lab_results.sql for customer customization"
  - "BigQuery uses PARSE_TIMESTAMP with %z format for +0000 timezone offsets (not SAFE_CAST)"

patterns-established:
  - "SQL file header template: Query name, Requirement ID, Dialect, Description, Parameters, Tables used"
  - "CTE structure for all multi-table queries"
  - "Dual-dialect file organization: queries/{postgres,bigquery}/clinical/"

# Metrics
duration: 3min
completed: 2026-02-08
---

# Phase 3 Plan 1: Clinical Analytics Queries Summary

**7 clinical SQL queries in PostgreSQL and BigQuery dialects covering patient summary, problems, medications, labs, vitals (LOINC-filtered), encounters, and care team with comma-separated field handling**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-08T14:13:23Z
- **Completed:** 2026-02-08T14:16:40Z
- **Tasks:** 2
- **Files created:** 14

## Accomplishments

- Created 14 production-ready SQL files (7 PostgreSQL + 7 BigQuery) covering all CLIN-01 through CLIN-07 requirements
- Vital sign query (CLIN-05) correctly filters 116 rows down to true vitals using LOINC codes, with leading comma timestamp fix
- Care team query (CLIN-07) aggregates practitioners from 3 relationship sources using UNION ALL with comma-separated field splitting
- Lab results query (CLIN-04) includes customizable reference range template for abnormal flagging

## Task Commits

Each task was committed atomically:

1. **Task 1: Create PostgreSQL clinical queries** - `8d225b1` (feat)
2. **Task 2: Create BigQuery clinical queries** - `6bfe0c9` (feat)

## Files Created

**PostgreSQL (queries/postgres/clinical/):**
- `patient_summary.sql` - CLIN-01: Demographics + active conditions + current medications via CTEs and LEFT JOINs
- `active_problems.sql` - CLIN-02: All conditions with status labels, ordered active-first then by onset date
- `medication_timeline.sql` - CLIN-03: Medication history with computed duration_days via AGE()
- `lab_results.sql` - CLIN-04: Lab observations with NUMERIC casting, interpretation column, and reference range template
- `vital_sign_trends.sql` - CLIN-05: LOINC-filtered vitals with LTRIM leading comma fix before TIMESTAMPTZ cast
- `encounter_history.sql` - CLIN-06: Encounter timeline with AGE() duration, handles NULL start/end times
- `care_team.sql` - CLIN-07: Practitioners from encounters (string_to_array+unnest), medications, procedures via UNION ALL

**BigQuery (queries/bigquery/clinical/):**
- Same 7 queries with BigQuery syntax: backtick identifiers, PARSE_TIMESTAMP, SAFE_CAST(FLOAT64), TIMESTAMP_DIFF, SPLIT+UNNEST

## Decisions Made

- **Hardcoded patient_id:** Used `6f3bc061-8515-41b9-bc26-75fc55f53284` with "Replace with your patient_id" comments and parameterized form shown in header. Makes queries immediately runnable without parameter binding setup.
- **UNION ALL for care team:** Combined practitioners from encounters, medications, and procedures with a `relationship` label column. Used DISTINCT on the final SELECT to deduplicate.
- **Commented reference ranges:** Lab results include a commented-out CASE block with common LOINC reference ranges (cholesterol, creatinine, glucose, BUN, potassium, sodium) that customers can uncomment and customize.
- **BigQuery PARSE_TIMESTAMP for +0000:** Used `PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', col)` since BigQuery's SAFE_CAST may not handle +0000 timezone offsets. The %z format handles both +0000 and +00:00.
- **BigQuery UNNEST array literal for LOINC codes:** Used `UNNEST([...]) AS loinc_code` instead of PostgreSQL's `unnest(ARRAY[...])` for the vital sign LOINC code list.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. These are static SQL files that run against existing tables from Phase 1/2.

## Next Phase Readiness

- Clinical query patterns established (CTE structure, timestamp handling, LOINC filtering, comma-separated field splitting) ready for reuse in operational (03-02) and cross-cutting (03-03) queries
- Directory structure queries/{postgres,bigquery}/clinical/ mirrors ddl/{postgres,bigquery}/ convention
- All known data quality pitfalls (vital sign leading comma, NULL lab_interpretation, missing lab-encounter FK, multi-value fields) are handled and documented in query comments

---
*Phase: 03-analytics-queries*
*Completed: 2026-02-08*
