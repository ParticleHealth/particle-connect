---
phase: 01-schema-foundation
plan: 03
subsystem: ddl-generation
tags: [ddl, sql, postgres, bigquery, cli, elt, code-generation]

requires:
  - phase: 01-02
    provides: "ResourceSchema objects from schema inspector, load_flat_data parser"
provides:
  - "DDL generation module (generate_ddl, DDLDialect, write_ddl)"
  - "CLI entry point for DDL generation (python -m observatory.generate_ddl)"
  - "Static PostgreSQL DDL file (ddl/postgres/create_all.sql)"
  - "Static BigQuery DDL file (ddl/bigquery/create_all.sql)"
affects:
  - "Phase 2: Local Pipeline uses ddl/postgres/create_all.sql for Docker auto-DDL"
  - "Phase 3: Analytics Queries reference table/column names from generated DDL"
  - "Phase 4: Cloud Mode uses ddl/bigquery/create_all.sql for Terraform table creation"

tech-stack:
  added: []
  patterns:
    - "ELT column typing: all columns TEXT/STRING, casting in queries"
    - "Dialect-aware quoting: double quotes for postgres, backticks for bigquery"
    - "Commented-out placeholders for empty resource types"
    - "CLI with argparse, env var defaults, CLI arg overrides"

key-files:
  created:
    - "particle-flat-observatory/src/observatory/ddl.py"
    - "particle-flat-observatory/src/observatory/generate_ddl.py"
    - "particle-flat-observatory/ddl/postgres/create_all.sql"
    - "particle-flat-observatory/ddl/bigquery/create_all.sql"
    - "particle-flat-observatory/tests/test_ddl.py"
  modified:
    - "particle-flat-observatory/src/observatory/__init__.py"
    - "particle-flat-observatory/pyproject.toml"
    - "particle-flat-observatory/.gitignore"

key-decisions:
  - "All columns use single type per dialect (TEXT/STRING) — ELT approach"
  - "All column names quoted unconditionally to handle SQL reserved words"
  - "Empty resource types get commented-out placeholders, not empty tables"
  - "DDL files committed as static reviewable artifacts, not gitignored"

duration: 3min
completed: 2026-02-08
---

# Phase 1 Plan 3: DDL Generator with CLI Summary

**DDL generator produces dialect-aware CREATE TABLE SQL for all 21 Particle resource types with CLI entry point and committed static SQL files**

## Performance
- **Duration:** 3min
- **Started:** 2026-02-08T05:38:19Z
- **Completed:** 2026-02-08T05:41:30Z
- **Tasks:** 2/2
- **Files created:** 5
- **Files modified:** 3

## Accomplishments
- DDL generation module with dialect-aware SQL output (PostgreSQL TEXT + double quotes, BigQuery STRING + backticks)
- Empty resource types produce commented-out placeholder blocks (not empty tables)
- Column order preserved from JSON key insertion order
- CLI script with argparse: supports --dialect, --data-path, --output-dir, --no-normalize
- CLI reads env vars as defaults, CLI args override
- Console entry point registered: observatory-generate-ddl
- Generated ddl/postgres/create_all.sql: 16 active tables + 5 empty placeholders = 21 resource types
- Generated ddl/bigquery/create_all.sql: 16 active tables + 5 empty placeholders = 21 resource types
- 17 unit tests covering both dialects, empty schemas, reserved words, column ordering, header content
- All 73 project tests pass, zero lint errors

## Task Commits
1. **Task 1: Create DDL generation module** - `de18b3c` (feat)
2. **Task 2: Create CLI script and generate committed DDL files** - `557fb17` (feat)

## Files Created/Modified
- `particle-flat-observatory/src/observatory/ddl.py` - DDL generation logic (DDLDialect enum, generate_create_table, generate_ddl, write_ddl)
- `particle-flat-observatory/src/observatory/generate_ddl.py` - CLI entry point with argparse and env var integration
- `particle-flat-observatory/ddl/postgres/create_all.sql` - PostgreSQL DDL for all 21 resource types (314 lines)
- `particle-flat-observatory/ddl/bigquery/create_all.sql` - BigQuery DDL for all 21 resource types (314 lines)
- `particle-flat-observatory/tests/test_ddl.py` - 17 tests for DDL generation correctness
- `particle-flat-observatory/src/observatory/__init__.py` - Added DDLDialect, generate_ddl, write_ddl exports
- `particle-flat-observatory/pyproject.toml` - Added console_scripts entry point
- `particle-flat-observatory/.gitignore` - Removed DDL files from ignore list

## Decisions Made
1. **All columns use a single type per dialect (TEXT/STRING)** - Follows the ELT approach where type casting happens in SQL queries, not during load. This was an explicit user decision from CONTEXT.md.
2. **Unconditional column name quoting** - Every column is quoted (double quotes for postgres, backticks for bigquery) since columns like "text", "type", "status" are SQL reserved words. Quoting all columns is simpler and safer than maintaining a reserved word list.
3. **Commented-out placeholders for empty resource types** - Rather than creating empty tables (which could confuse customers), empty resource types get commented-out blocks explaining why and how to add columns manually.
4. **DDL files committed as static artifacts** - Removed from .gitignore so customers can review, hand-edit, and version control the generated SQL. This aligns with the CONTEXT.md vision of "committed as static files that can be hand-edited."

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
Phase 1 is now complete. All three plans delivered:
- 01-01: Project scaffolding, configuration, sample data
- 01-02: JSON parser, schema inspector, data normalization
- 01-03: DDL generator, CLI, committed SQL files

Phase 2 (Local Pipeline) can proceed immediately:
- DDL files at ddl/postgres/create_all.sql are ready for Docker PostgreSQL auto-DDL
- Parser and schema inspector are ready for the data loading pipeline
- CLI patterns established in generate_ddl.py can be extended for the pipeline CLI

Phase 3 (Analytics Queries) can also proceed in parallel:
- Table and column names are defined in the committed DDL files
- Sample data is available for query development and testing

---
*Phase: 01-schema-foundation*
*Completed: 2026-02-08*
