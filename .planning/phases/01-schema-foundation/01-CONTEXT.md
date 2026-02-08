# Phase 1: Schema Foundation - Context

**Gathered:** 2026-02-07
**Status:** Ready for planning

<domain>
## Phase Boundary

DDL generation, data normalization, and project scaffolding for all 21 Particle flat resource types. This phase creates the schema definitions, type mappings, and normalization layer that every subsequent phase builds on. No database loading happens here — just the foundation.

</domain>

<decisions>
## Implementation Decisions

### Project Structure
- Directory name: `particle-flat-observatory` (new folder at repo root)
- Internal code layout: Claude's discretion — pick based on project size and complexity
- SQL query files: Claude's discretion on location
- Terraform files: Claude's discretion on location

### Type Mapping Strategy (ELT Approach)
- **ELT, not ETL** — load raw, transform in queries
- All ID fields: TEXT (some Particle IDs are 20-digit numbers that overflow INT64)
- All timestamp fields: TEXT (store as-is, parse/cast in SQL queries)
- All numeric fields: TEXT (store as-is, cast in SQL queries)
- This means virtually all columns are TEXT/STRING — the SQL queries handle type casting
- The value is in getting data loaded reliably, not in pre-typing columns

### Normalization Behavior
- Empty strings ("") from Particle → convert to NULL on load (only transformation at load time)
- Extra fields in data not in DDL → log warning, skip the field, load the rest
- Missing fields in data that DDL expects → insert NULL for that column
- Logging: summary per resource type + warnings for skipped fields, empty types, and conversion issues

### DDL Output Format
- One combined .sql file per dialect (e.g., `create_all.sql` with all 21 CREATE TABLEs)
- Separate directories for PostgreSQL and BigQuery DDL variants (ddl/postgres/, ddl/bigquery/)
- Generated from sample data via a script, then committed as static files that can be hand-edited
- Column order follows JSON key order from Particle API response (not alphabetical)

### Claude's Discretion
- Internal package structure (flat modules vs subpackages)
- SQL query file organization
- Terraform file organization
- DDL generation script design
- Exact logging format and library choice

</decisions>

<specifics>
## Specific Ideas

- User emphasized ELT approach: "not an ETL approach" — load data as close to raw as possible, do transformations in SQL
- Column types should be mixed approach: mostly TEXT for safety, with the understanding that SQL queries provide the typed access layer
- The pipeline directory is named `particle-flat-observatory` — distinctive name chosen by user

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-schema-foundation*
*Context gathered: 2026-02-07*
