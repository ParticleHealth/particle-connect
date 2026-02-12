# Analytics Query Library

Ready-to-run SQL queries for Particle flat data. Each query is available in both PostgreSQL and BigQuery dialects.

## Quick Start

1. Load sample data into DuckDB (see main [README](../README.md))
2. Open any query file from `postgres/` or `bigquery/`
3. Replace the sample `patient_id` with your own (for patient-scoped queries)
4. Run in the DuckDB CLI or your SQL client

The `postgres/` queries work directly in DuckDB -- DuckDB is PostgreSQL-compatible with double-quoted identifiers, TEXT type, CAST, and string_agg.

```bash
# Run a query in DuckDB
duckdb observatory.duckdb < queries/postgres/clinical/patient_summary.sql
```

## Dialect Differences

Queries are provided in two dialects:
- **`postgres/`** -- Uses double-quoted identifiers, `CAST(col AS TIMESTAMPTZ)` casting, `string_to_array` + `unnest`. Also works in DuckDB.
- **`bigquery/`** -- Uses backtick identifiers, `SAFE_CAST`/`PARSE_TIMESTAMP`, `SPLIT` + `UNNEST`

Business logic is identical across dialects. Only SQL syntax differs.

## Clinical Queries

| File | Requirement | Description | Scope |
|------|-------------|-------------|-------|
| `clinical/patient_summary.sql` | CLIN-01 | Demographics, active conditions, and current medications for a patient | Patient |
| `clinical/active_problems.sql` | CLIN-02 | Current conditions with onset dates and clinical status | Patient |
| `clinical/medication_timeline.sql` | CLIN-03 | Medications with start/end dates, dosage, and status | Patient |
| `clinical/lab_results.sql` | CLIN-04 | Lab values trended by date with interpretation column | Patient |
| `clinical/vital_sign_trends.sql` | CLIN-05 | Blood pressure, heart rate, respiratory rate, O2 sat over time | Patient |
| `clinical/encounter_history.sql` | CLIN-06 | Chronological encounters with type, location, duration | Patient |
| `clinical/care_team.sql` | CLIN-07 | Practitioners involved in care with roles and specialties | Patient |

## Operational Queries

| File | Requirement | Description | Scope |
|------|-------------|-------------|-------|
| `operational/data_completeness.sql` | OPS-01 | Record counts and field population percentages per resource type | Global |
| `operational/source_coverage.sql` | OPS-02 | Which data sources contributed records, by resource type | Global |
| `operational/record_freshness.sql` | OPS-03 | Most recent record timestamp per resource type | Global |
| `operational/data_provenance.sql` | OPS-04 | Trace clinical records back to originating source documents | Patient |
| `operational/ai_output_summary.sql` | OPS-05 | AI-generated insights with citation counts and source documents | Global |

## Cross-Cutting Queries

| File | Requirement | Description | Scope |
|------|-------------|-------------|-------|
| `cross-cutting/labs_by_encounter.sql` | CROSS-01 | Labs ordered during specific encounters (temporal join) | Patient |
| `cross-cutting/medications_by_problem.sql` | CROSS-02 | Medications mapped to conditions via encounter linkage | Patient |
| `cross-cutting/procedures_by_encounter.sql` | CROSS-03 | Procedures performed during encounters with practitioners | Patient |

## Sample Data Notes

Queries are designed to work with the included sample data (`sample-data/flat_data.json`). Key characteristics:

- **1 patient** (Elvira Valadez): `6f3bc061-8515-41b9-bc26-75fc55f53284`
- **111 lab results** from a single timestamp, no interpretation values populated
- **116 vital sign observations** including lab-like observations; queries filter to true vitals via LOINC codes
- **5 encounters**, 1 with no start/end time
- **All columns are TEXT/STRING** -- queries CAST to appropriate types for comparisons and math
- **Vital sign timestamps** have a leading comma prefix that queries strip before parsing

## Known Limitations

- `lab_interpretation` is NULL for all records in sample data. The lab results query includes the column but cannot flag abnormals without source-provided interpretation codes.
- `encounter_reference_id` on procedures is NULL for all records. The procedures-by-encounter query uses a direct FK join that will work when populated; a temporal join alternative is provided in comments.
- Labs have no encounter foreign key. The labs-by-encounter query uses timestamp overlap to associate labs with encounters.
- Vital signs table contains lab-like observations (CBC, urinalysis panels). The vital sign trends query filters to true vitals using LOINC codes.
