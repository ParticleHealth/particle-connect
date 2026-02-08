---
phase: 01-schema-foundation
plan: 02
subsystem: data-processing
tags: [python, json-parser, schema-inspection, normalization, elt]

requires:
  - phase: 01-01
    provides: pip-installable Python package, config module, sample flat_data.json
provides:
  - JSON parser loading all 21 Particle resource types with normalization
  - Schema inspector discovering columns per resource type from data
  - Data normalizer converting empty strings to None (only ELT transformation)
  - camelCase to snake_case table name conversion
affects:
  - 01-03 (DDL generator consumes ResourceSchema objects to produce CREATE TABLE statements)
  - 02-02 (PostgreSQL loader uses parser and normalizer for data ingestion)
  - all subsequent phases (parser and schema are the core data processing modules)

tech-stack:
  added: []
  patterns: [dataclass-schema, scan-all-records, insertion-order-columns, normalize-on-load]

key-files:
  created:
    - particle-flat-observatory/src/observatory/normalizer.py
    - particle-flat-observatory/src/observatory/parser.py
    - particle-flat-observatory/src/observatory/schema.py
    - particle-flat-observatory/tests/__init__.py
    - particle-flat-observatory/tests/test_normalizer.py
    - particle-flat-observatory/tests/test_parser.py
  modified:
    - particle-flat-observatory/src/observatory/__init__.py

key-decisions:
  - "Schema inspector scans ALL records per resource type to discover full column set (not just first record)"
  - "Column order preserves JSON key insertion order from Particle API (not alphabetical)"
  - "camelCase aI prefix special-cased to produce ai_ not a_i_ in snake_case conversion"

duration: 3min
completed: 2026-02-08
---

# Phase 1 Plan 2: JSON Parser, Schema Inspector, and Data Normalization Summary

**JSON parser for 21 Particle resource types with empty-string-to-None normalization and schema inspector that discovers columns by scanning all records in insertion order.**

## Performance
- **Duration:** 3 minutes
- **Started:** 2026-02-08T05:31:51Z
- **Completed:** 2026-02-08T05:34:57Z
- **Tasks:** 2/2
- **Files created:** 6
- **Files modified:** 1

## Accomplishments
- Created normalizer with single ELT transformation: empty strings to None (Particle returns "" instead of null)
- Created parser that loads flat_data.json, validates structure, normalizes data, and returns all 21 resource types (missing types get empty lists, unknown types are warned and skipped)
- Created schema inspector that discovers all column names per resource type by scanning every record (not just the first), preserving JSON key insertion order
- Created camel_to_snake converter handling all 21 Particle resource type names including the tricky aICitations/aIOutputs prefix
- 56 tests covering normalizer edge cases, parser loading/error handling, camel_to_snake for all 21 types, and schema inspection against real sample data
- Zero external dependencies (stdlib only) as established in Plan 01

## Task Commits
1. **Task 1: Create JSON parser and data normalizer** - `444416c` (feat)
2. **Task 2: Create schema inspector with tests** - `9087072` (feat)

## Files Created/Modified
- `particle-flat-observatory/src/observatory/normalizer.py` - normalize_value, normalize_record, normalize_resource functions
- `particle-flat-observatory/src/observatory/parser.py` - EXPECTED_RESOURCE_TYPES list, load_flat_data with validation and logging
- `particle-flat-observatory/src/observatory/schema.py` - ResourceSchema dataclass, camel_to_snake, inspect_schema
- `particle-flat-observatory/src/observatory/__init__.py` - Updated exports for all new public APIs
- `particle-flat-observatory/tests/__init__.py` - Test package init
- `particle-flat-observatory/tests/test_normalizer.py` - 17 tests for normalizer behavior
- `particle-flat-observatory/tests/test_parser.py` - 39 tests for parser, camel_to_snake, and schema inspection

## Decisions Made
1. **Scan all records for schema discovery** - The schema inspector iterates every record in a resource type to build the column set, not just the first record. This handles cases where different records have different fields.
2. **Preserve insertion order** - Column order follows the order keys are first encountered across records (matching Particle API JSON key order), using dict.fromkeys() for deduplication.
3. **Special-case aI prefix** - The camelCase converter special-cases the "aI" prefix (aICitations, aIOutputs) to produce "ai_" rather than the naive "a_i_" that a generic regex would produce.

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
Plan 01-03 (DDL generator) can proceed immediately. The `inspect_schema()` function returns `ResourceSchema` objects with `table_name`, `columns`, `record_count`, and `is_empty` -- everything the DDL generator needs to produce CREATE TABLE statements. The sample data produces 16 non-empty resource types with column counts ranging from 3 (sources) to 36 (transitions), and 5 empty types (allergies, coverages, familyMemberHistories, immunizations, socialHistories) that will need special handling in DDL generation.

---
*Phase: 01-schema-foundation*
*Completed: 2026-02-08*
