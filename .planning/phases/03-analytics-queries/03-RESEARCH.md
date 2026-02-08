# Phase 3: Analytics Queries - Research

**Researched:** 2026-02-08
**Domain:** SQL analytics queries, PostgreSQL/BigQuery dialect compatibility, healthcare clinical data patterns
**Confidence:** HIGH

## Summary

Phase 3 produces a library of static `.sql` files organized by category (clinical, operational, cross-cutting) that customers can run directly against their Particle flat data tables. This is NOT a code phase -- the deliverables are pure SQL files with header comments explaining what each query does and how to customize it. Every query must work against the all-TEXT/STRING schema established in Phase 1, meaning all date comparisons, numeric operations, and aggregations require explicit CAST operations within the queries themselves.

The critical technical challenge is dual-dialect compatibility (PostgreSQL and BigQuery). After thorough investigation, the two dialects are highly compatible for this use case -- both support standard SQL constructs (CASE, COALESCE, NULLIF, string_agg, CTEs, window functions) with only three areas of divergence: (1) timestamp parsing from TEXT/STRING columns, (2) identifier quoting style (double quotes vs backticks), and (3) a few function name differences. The recommended approach is to write standard ANSI SQL wherever possible and provide dialect-specific variants only for timestamp parsing and identifier quoting.

A key data quality finding is that `vital_sign_observation_time` values in the sample data have a leading comma-space prefix (e.g., `", 2011-05-28T15:19:11+0000"`), which must be stripped before timestamp parsing. Similarly, labs have no direct foreign key to encounters -- the cross-cutting join (CROSS-01) must use timestamp overlap (lab_timestamp BETWEEN encounter_start_time AND encounter_end_time). All `lab_interpretation` values are NULL in the sample data, so the "flagged abnormals" requirement for CLIN-04 must rely on LOINC code-based reference ranges rather than the interpretation field.

**Primary recommendation:** Write each query twice -- once for PostgreSQL (using `::TIMESTAMPTZ` casting and double-quoted identifiers) and once for BigQuery (using `SAFE_CAST` or `PARSE_TIMESTAMP` and backtick-quoted identifiers). Organize as `queries/postgres/` and `queries/bigquery/` mirroring the existing `ddl/postgres/` and `ddl/bigquery/` convention. Use CTEs extensively for readability since both dialects support them identically.

## Standard Stack

### Core

This phase produces SQL files, not code. No libraries are needed.

| Tool | Purpose | Why Standard |
|------|---------|--------------|
| PostgreSQL 17 | Local query execution target | Already deployed via Docker Compose in Phase 2 |
| BigQuery Standard SQL | Cloud query execution target | Planned for Phase 4; queries must be ready |
| ANSI SQL:2011 | Common subset for both dialects | CTEs, CASE, COALESCE, window functions, string_agg all work in both |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Dual dialect files | Single file with conditional comments | Too fragile; customers copy-paste queries into different tools. Separate files are clearer and safer. |
| PARSE_TIMESTAMP everywhere | CAST for PostgreSQL, PARSE_TIMESTAMP for BigQuery | CAST is simpler in PostgreSQL (native ISO 8601 support); BigQuery needs PARSE_TIMESTAMP for non-RFC3339 formats. Keep each dialect idiomatic. |
| dbt models | Raw SQL files | Explicitly out of scope (see REQUIREMENTS.md). Customers build their own transforms. |

## Architecture Patterns

### Recommended File Structure

```
particle-flat-observatory/
  queries/
    postgres/
      clinical/
        patient_summary.sql
        active_problems.sql
        medication_timeline.sql
        lab_results.sql
        vital_sign_trends.sql
        encounter_history.sql
        care_team.sql
      operational/
        data_completeness.sql
        source_coverage.sql
        record_freshness.sql
        data_provenance.sql
        ai_output_summary.sql
      cross-cutting/
        labs_by_encounter.sql
        medications_by_problem.sql
        procedures_by_encounter.sql
    bigquery/
      clinical/
        (same files as postgres/)
      operational/
        (same files as postgres/)
      cross-cutting/
        (same files as postgres/)
    README.md           # Query catalog with descriptions and expected output
```

This mirrors the existing `ddl/postgres/` and `ddl/bigquery/` convention from Phase 1.

### Pattern 1: Standard Query File Format

Every SQL file should follow this template for customer readability:

```sql
-- =============================================================================
-- Query: [Human-readable name]
-- Requirement: [CLIN-XX / OPS-XX / CROSS-XX]
-- Dialect: PostgreSQL (or BigQuery)
-- Description: [What this query answers in plain English]
-- Parameters: [patient_id = UUID of target patient, or "none" if query is global]
-- Tables used: [list of tables]
-- =============================================================================

-- [The actual query]
```

### Pattern 2: CTE-Based Query Structure

Use CTEs to break complex queries into readable named stages. Both PostgreSQL and BigQuery support CTEs identically.

```sql
WITH
  -- Stage 1: Filter and transform raw data
  base_data AS (
    SELECT ...
    FROM ...
    WHERE ...
  ),
  -- Stage 2: Aggregate or join
  aggregated AS (
    SELECT ...
    FROM base_data
    ...
  )
-- Final output
SELECT * FROM aggregated
ORDER BY ...;
```

### Pattern 3: Timestamp Parsing (Dialect-Specific)

The most significant dialect difference. All timestamps are stored as TEXT/STRING and must be parsed for comparisons, ordering, and date math.

**PostgreSQL:**
```sql
-- Direct cast works for ISO 8601 with timezone (e.g., "2011-05-28T15:19:11+0000")
CAST("lab_timestamp" AS TIMESTAMPTZ)
-- or shorthand
"lab_timestamp"::TIMESTAMPTZ

-- For dates without timezone (e.g., "1970-12-26T00:00:00")
CAST("date_of_birth" AS TIMESTAMP)

-- For timestamps with fractional seconds (e.g., "2026-02-06T02:41:44.378318936Z")
CAST("created" AS TIMESTAMPTZ)
```

**BigQuery:**
```sql
-- For ISO 8601 with timezone offset +0000 (no colon)
-- SAFE_CAST may not handle +0000 directly; use PARSE_TIMESTAMP
PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `lab_timestamp`)

-- For dates without timezone (e.g., "1970-12-26T00:00:00")
SAFE_CAST(`date_of_birth` AS TIMESTAMP)

-- For timestamps with fractional seconds and Z suffix
PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*SZ', `created`)

-- Always prefer SAFE_CAST or SAFE-prefixed functions to avoid query failures on bad data
```

### Pattern 4: Numeric Parsing from TEXT/STRING

All numeric values are stored as TEXT/STRING. Queries that need numeric comparisons or aggregations must CAST.

```sql
-- PostgreSQL
CAST("lab_value_quantity" AS NUMERIC)
-- or shorthand
"lab_value_quantity"::NUMERIC

-- BigQuery
SAFE_CAST(`lab_value_quantity` AS FLOAT64)
```

Use `SAFE_CAST` in BigQuery to avoid query failures on non-numeric values. In PostgreSQL, wrap in a CASE or use TRY_CAST (PG 17+ does not have TRY_CAST natively, so use CASE with regex).

### Pattern 5: NULL-Safe Comparisons

All empty strings from Particle API have been normalized to NULL by the loader. Queries should use COALESCE for display and IS NOT NULL for filtering.

```sql
-- Works identically in both dialects
COALESCE("condition_clinical_status", 'unknown') AS clinical_status
WHERE "condition_onset_date" IS NOT NULL
```

### Pattern 6: Handling Multi-Value Comma-Separated Fields

Several fields contain comma-separated values (e.g., `condition_id_references`, `encounter_type_code`, `encounter_type_name`, `practitioner_role_id_references`). These cannot be reliably joined without splitting.

```sql
-- PostgreSQL: Use string_to_array + unnest
SELECT unnest(string_to_array("condition_id_references", ', ')) AS condition_id
FROM encounters
WHERE "condition_id_references" IS NOT NULL

-- BigQuery: Use SPLIT + UNNEST
SELECT condition_id
FROM encounters, UNNEST(SPLIT(`condition_id_references`, ', ')) AS condition_id
WHERE `condition_id_references` IS NOT NULL
```

This is one of the most significant dialect differences and applies to cross-cutting joins that reference these multi-value fields.

### Anti-Patterns to Avoid

- **Casting without NULL check:** Always guard CAST with `WHERE col IS NOT NULL` or `CASE WHEN col IS NOT NULL THEN CAST(col AS ...) END`. NULL casts are safe, but empty strings would have been normalized to NULL already.
- **Assuming encounter_reference_id exists on labs:** Labs do NOT have an encounter reference column. Use timestamp overlap for CROSS-01 (labs by encounter).
- **Trusting lab_interpretation for abnormal flags:** All values are NULL in sample data. Use LOINC code-based reference ranges or note the limitation.
- **Ignoring the leading comma in vital_sign_observation_time:** Values are `", 2011-05-28T15:19:11+0000"` -- must LTRIM before parsing.
- **Using PostgreSQL :: cast syntax in BigQuery queries:** BigQuery uses CAST() or SAFE_CAST(), not the :: shorthand.
- **Using backticks in PostgreSQL or double quotes in BigQuery:** Each dialect has its own identifier quoting convention.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Timestamp parsing across formats | Custom regex timestamp parser | `::TIMESTAMPTZ` (PG) / `PARSE_TIMESTAMP` (BQ) | Both databases handle ISO 8601 natively with proper format strings |
| Numeric validation before CAST | Manual regex check for every numeric column | `CASE WHEN ... THEN CAST ... END` (PG) / `SAFE_CAST` (BQ) | SAFE_CAST returns NULL on failure; PG requires a CASE guard but this is straightforward |
| Comma-separated value splitting | Custom string splitting logic | `string_to_array` + `unnest` (PG) / `SPLIT` + `UNNEST` (BQ) | Both databases have built-in array splitting |
| Date difference calculations | Manual epoch arithmetic | `AGE()` / date subtraction (PG) / `TIMESTAMP_DIFF` (BQ) | Native functions handle edge cases (leap years, DST) |
| Result pivoting for vital signs | CASE-based manual pivoting | CTE + FILTER/conditional aggregation | Standard pattern, no need for CROSSTAB extension |

## Common Pitfalls

### Pitfall 1: Vital Sign Observation Time Has Leading Comma

**What goes wrong:** `vital_sign_observation_time` values in the sample data are `", 2011-05-28T15:19:11+0000"` (note leading comma-space). Direct CAST to timestamp fails.
**Why it happens:** Particle API returns this format for some vital sign observations -- it appears to be a multi-value field where the first value is empty.
**How to avoid:** Always strip leading comma and space before parsing:
```sql
-- PostgreSQL
CAST(LTRIM("vital_sign_observation_time", ', ') AS TIMESTAMPTZ)

-- BigQuery
PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', LTRIM(`vital_sign_observation_time`, ', '))
```
**Warning signs:** Timestamp CAST failures only in vital_signs queries, not in labs or encounters.

### Pitfall 2: Labs Have No Direct Encounter Foreign Key

**What goes wrong:** Attempting to JOIN labs to encounters via a foreign key column that does not exist.
**Why it happens:** The labs table schema does not include `encounter_reference_id` or any encounter FK. The join must use temporal overlap.
**How to avoid:** For CROSS-01 (labs by encounter), use timestamp-based join:
```sql
-- Labs that occurred during an encounter's time window
WHERE lab_timestamp_parsed BETWEEN encounter_start_parsed AND encounter_end_parsed
  AND labs.patient_id = encounters.patient_id
```
**Warning signs:** Empty results or join key column not found errors.

### Pitfall 3: All Lab Interpretations Are NULL

**What goes wrong:** CLIN-04 requires "flagged abnormals" but `lab_interpretation` is NULL for all 111 lab records in sample data.
**Why it happens:** Not all data sources provide interpretation codes. This is a common healthcare data quality issue.
**How to avoid:** Design the query to show the interpretation column (for when data is available) but also include reference range annotations based on well-known LOINC codes. Document that "abnormal" flags depend on data source quality.
**Warning signs:** No abnormal labs appearing in query results even when values are clearly out of range.

### Pitfall 4: Comma-Separated Multi-Value Fields

**What goes wrong:** Fields like `condition_id_references`, `encounter_type_code`, `practitioner_role_id_references` contain comma-separated lists that look like single values. JOINs against these fields match nothing.
**Why it happens:** Particle flat format stores multi-value FHIR references as comma-separated strings.
**How to avoid:** Use `unnest(string_to_array(...))` (PG) or `UNNEST(SPLIT(...))` (BQ) to explode multi-value fields before joining.
**Warning signs:** Unexpectedly empty join results, or partial matches that only work for single-value records.

### Pitfall 5: BigQuery Timezone Offset Format (+0000 vs +00:00)

**What goes wrong:** `SAFE_CAST('2011-05-28T15:19:11+0000' AS TIMESTAMP)` may fail in BigQuery because it expects RFC 3339 format with colon in timezone offset (+00:00).
**Why it happens:** BigQuery's CAST follows RFC 3339 strictly; the Particle data uses ISO 8601 without colon in offset.
**How to avoid:** Use `PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', col)` in BigQuery -- the `%z` format element handles offsets both with and without colons.
**Warning signs:** NULL results from SAFE_CAST on timestamp columns that have timezone offsets.

### Pitfall 6: Empty Encounter Start/End Times

**What goes wrong:** Some encounters have NULL start/end times (one encounter in sample data: `2bcc07b5f4ebf469...`). Timestamp-based joins produce NULLs.
**Why it happens:** Not all data sources provide complete encounter metadata.
**How to avoid:** Use `WHERE encounter_start_time IS NOT NULL` filters in temporal join conditions, and note incomplete encounters in results.
**Warning signs:** NULL timestamps in encounter timeline queries.

### Pitfall 7: Vital Signs Table Contains Lab-Like Observations

**What goes wrong:** CLIN-05 (vital sign trends for BP, HR, temperature, BMI) returns 116 rows including CBC, urinalysis, and chemistry panel results mixed in.
**Why it happens:** The `vital_signs` table contains ALL observations categorized as "vital-signs" by the source system, which includes lab panels that were clinically classified alongside true vitals.
**How to avoid:** Filter on `vital_sign_observation_name` or `vital_sign_observation_code` (LOINC codes) for true vital signs:
- Systolic BP: code `8480-6`
- Diastolic BP: code `8462-4`
- Heart Rate: code `8867-4`
- Respiratory Rate: code `9279-1`
- O2 Saturation: codes `2708-6`, `59408-5`
- Body Temperature: code `8310-5` (not in sample data)
- BMI: code `39156-5` (not in sample data)
**Warning signs:** Unexpectedly high row counts in vital sign trends query.

## Code Examples

### CLIN-01: Patient Summary (PostgreSQL)

```sql
-- Patient summary with demographics, active conditions, and current medications
WITH
  demographics AS (
    SELECT
      "patient_id",
      "given_name" || ' ' || "family_name" AS full_name,
      "date_of_birth",
      "gender",
      "race",
      "address_line",
      "address_city",
      "address_state",
      "address_postal_code",
      "telephone",
      "language"
    FROM patients
    WHERE "patient_id" = :patient_id   -- parameterized
  ),
  active_conditions AS (
    SELECT
      "patient_id",
      string_agg("condition_name", '; ' ORDER BY "condition_onset_date") AS conditions
    FROM problems
    WHERE "patient_id" = :patient_id
      AND "condition_clinical_status" = 'active'
    GROUP BY "patient_id"
  ),
  current_medications AS (
    SELECT
      "patient_id",
      string_agg("medication_name", '; ' ORDER BY "medication_name") AS medications
    FROM medications
    WHERE "patient_id" = :patient_id
      AND "medication_statement_status" IN ('active', 'completed')
    GROUP BY "patient_id"
  )
SELECT
  d.*,
  COALESCE(ac.conditions, 'None documented') AS active_conditions,
  COALESCE(cm.medications, 'None documented') AS current_medications
FROM demographics d
LEFT JOIN active_conditions ac ON d."patient_id" = ac."patient_id"
LEFT JOIN current_medications cm ON d."patient_id" = cm."patient_id";
```

### OPS-01: Data Completeness Scorecard (PostgreSQL)

```sql
-- Data completeness scorecard across all resource types
SELECT
  'patients' AS resource_type,
  COUNT(*) AS record_count,
  COUNT("given_name") AS given_name_populated,
  ROUND(100.0 * COUNT("given_name") / NULLIF(COUNT(*), 0), 1) AS given_name_pct
FROM patients
UNION ALL
SELECT
  'problems',
  COUNT(*),
  COUNT("condition_name"),
  ROUND(100.0 * COUNT("condition_name") / NULLIF(COUNT(*), 0), 1)
FROM problems
UNION ALL
SELECT
  'medications',
  COUNT(*),
  COUNT("medication_name"),
  ROUND(100.0 * COUNT("medication_name") / NULLIF(COUNT(*), 0), 1)
FROM medications
-- ... etc for each resource type
ORDER BY resource_type;
```

### CROSS-01: Labs by Encounter (PostgreSQL)

```sql
-- Labs ordered during specific encounters (temporal join)
WITH
  parsed_encounters AS (
    SELECT
      "encounter_id",
      "encounter_type_name",
      CAST("encounter_start_time" AS TIMESTAMPTZ) AS start_ts,
      CAST("encounter_end_time" AS TIMESTAMPTZ) AS end_ts,
      "patient_id"
    FROM encounters
    WHERE "encounter_start_time" IS NOT NULL
      AND "encounter_end_time" IS NOT NULL
  ),
  parsed_labs AS (
    SELECT
      "lab_observation_id",
      "lab_name",
      "lab_value_quantity",
      "lab_unit",
      CAST("lab_timestamp" AS TIMESTAMPTZ) AS lab_ts,
      "patient_id"
    FROM labs
    WHERE "lab_timestamp" IS NOT NULL
  )
SELECT
  pe."encounter_id",
  pe."encounter_type_name",
  pe.start_ts,
  pe.end_ts,
  pl."lab_name",
  pl."lab_value_quantity",
  pl."lab_unit",
  pl.lab_ts
FROM parsed_encounters pe
INNER JOIN parsed_labs pl
  ON pe."patient_id" = pl."patient_id"
  AND pl.lab_ts >= pe.start_ts
  AND pl.lab_ts <= pe.end_ts
ORDER BY pe.start_ts, pl.lab_ts;
```

### Timestamp Parsing Comparison

**PostgreSQL:**
```sql
-- All these work via direct cast
CAST("lab_timestamp" AS TIMESTAMPTZ)                    -- "2011-05-28T15:19:11+0000"
CAST("date_of_birth" AS TIMESTAMP)                      -- "1970-12-26T00:00:00"
CAST("created" AS TIMESTAMPTZ)                          -- "2026-02-06T02:41:44.378318936Z"
CAST(LTRIM("vital_sign_observation_time", ', ') AS TIMESTAMPTZ)  -- ", 2011-05-28T15:19:11+0000"
```

**BigQuery:**
```sql
-- Use PARSE_TIMESTAMP for +0000 timezone format
PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', `lab_timestamp`)
-- Use SAFE_CAST for simple formats
SAFE_CAST(`date_of_birth` AS TIMESTAMP)
-- Use PARSE_TIMESTAMP for fractional seconds + Z
PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*SZ', `created`)
-- Strip leading comma first for vital signs
PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', LTRIM(`vital_sign_observation_time`, ', '))
```

## Data Model Reference

### Table Relationships (Join Keys)

This is critical for writing correct cross-cutting queries.

```
patients.patient_id  ----+---- (all tables).patient_id     [universal join key]
                         |
encounters.encounter_id -+---- problems.encounter_id       [direct FK, may be NULL]
                         |---- document_references.encounter_reference_id [direct FK, many NULL]
                         |---- procedures.encounter_reference_id [direct FK, all NULL in sample]
                         |---- labs (NO FK -- use temporal join via timestamps)
                         |
practitioners.practitioner_role_id --- encounters.practitioner_role_id_references [comma-separated!]
                                   --- medications.practitioner_role_id            [direct FK]
                                   --- procedures.performer_practitioner_role_reference_id [direct FK]
                                   --- document_references.practitioner_role_reference_id  [direct FK]
                         |
record_sources.resource_id -------- (any table's primary ID column)  [provenance link]
record_sources.source_id ---------- sources.source_id                [source name lookup]
record_sources.resource_type ------ identifies which table the resource_id belongs to
record_sources.resource_id_name --- identifies which column name holds the ID
                         |
ai_citations.ai_output_id -------- ai_outputs.ai_output_id           [direct FK]
ai_citations.resource_reference_id -- (any table's primary ID)       [cited resource]
```

### Resource ID Column Names by Table

For record_sources/provenance joins, each table's primary ID column:

| Table | Primary ID Column | resource_type in record_sources | resource_id_name in record_sources |
|-------|-------------------|--------------------------------|-----------------------------------|
| document_references | document_reference_id | document_reference | document_reference_id |
| encounters | encounter_id | encounter | encounter_id |
| labs | lab_observation_id | lab | lab_observation_id |
| locations | location_id | location | location_id |
| medications | medication_id | medication | medication_id |
| organizations | organization_id | organization | organization_id |
| practitioners | practitioner_id | practitioner | practitioner_id |
| problems | condition_id | problem | condition_id |
| procedures | procedure_id | procedure | procedure_id |
| vital_signs | vital_sign_observation_id | vital_sign | vital_sign_observation_id |

### Sample Data Volumes

| Table | Records | Key Observations |
|-------|---------|-----------------|
| patients | 1 | Single patient (Elvira Valadez) |
| encounters | 5 | 1 has no start/end time; 1 is Emergency type |
| problems | 5 | 4 active, 1 resolved; some have encounter_id |
| medications | 6 | 4 completed, 2 active; all have dose info |
| labs | 111 | All from one timestamp; no interpretation values |
| vital_signs | 116 | Mix of true vitals (5) and lab-like observations (111) |
| procedures | 4 | All have procedure_code; none have encounter_reference_id |
| practitioners | 4 | Most fields sparse; 1 has specialty |
| organizations | 4 | Full address info |
| locations | 1 | Full address info |
| document_references | 51 | 11 linked to encounters, 40 not |
| sources | 6 | Named source documents (XML files) |
| record_sources | 307 | Links every resource to its source(s) |
| ai_outputs | 22 | 21 DISCHARGE_SUMMARY, 1 PATIENT_HISTORY |
| ai_citations | 542 | All reference DocumentReferences |
| transitions | 2 | ADT-style records with diagnosis info |

### Timestamp Formats in Sample Data

| Format | Example | Found In |
|--------|---------|----------|
| ISO 8601 + TZ offset | `2011-05-28T15:19:11+0000` | labs, encounters, problems, procedures, vital_signs |
| ISO 8601 no TZ | `1970-12-26T00:00:00` | patients (date_of_birth) |
| ISO 8601 + fractional + Z | `2026-02-06T02:41:44.378318936Z` | ai_outputs (created) |
| ISO 8601 + fractional microsec | `2026-01-13T16:57:10.00323` | transitions (status_date_time) |
| Space-separated + fractional | `2025-11-01 15:30:00.00000` | transitions (visit dates) |
| Leading comma prefix | `, 2011-05-28T15:19:11+0000` | vital_signs (observation_time) |

## Dialect Compatibility Matrix

Functions and syntax that work the same vs differently across PostgreSQL and BigQuery.

### Identical (Standard SQL)

| Feature | Syntax | Notes |
|---------|--------|-------|
| Common Table Expressions | `WITH cte AS (...)` | Identical syntax |
| CASE expressions | `CASE WHEN ... THEN ... END` | Identical |
| COALESCE | `COALESCE(a, b, c)` | Identical |
| NULLIF | `NULLIF(a, b)` | Identical |
| COUNT/SUM/AVG/MIN/MAX | Same syntax | Identical |
| WHERE / GROUP BY / HAVING | Same syntax | Identical |
| LEFT/RIGHT/INNER JOIN | Same syntax | Identical |
| UNION ALL | Same syntax | Identical |
| ROUND | `ROUND(x, n)` | Identical |
| LIKE / IN / BETWEEN | Same syntax | Identical |
| IS NULL / IS NOT NULL | Same syntax | Identical |
| ORDER BY ... NULLS LAST | Same syntax | Both support NULLS FIRST/LAST |
| Window functions | `ROW_NUMBER() OVER(...)` | Identical |
| STRING_AGG | `STRING_AGG(expr, delim)` | Both support it |

### Different (Dialect-Specific)

| Feature | PostgreSQL | BigQuery |
|---------|-----------|----------|
| Identifier quoting | Double quotes: `"column_name"` | Backticks: `` `column_name` `` |
| Timestamp cast | `col::TIMESTAMPTZ` or `CAST(col AS TIMESTAMPTZ)` | `SAFE_CAST(col AS TIMESTAMP)` or `PARSE_TIMESTAMP(fmt, col)` |
| Safe cast | Not built-in (use CASE) | `SAFE_CAST(expr AS type)` |
| Numeric cast | `col::NUMERIC` | `SAFE_CAST(col AS FLOAT64)` or `SAFE_CAST(col AS NUMERIC)` |
| Date extraction | `EXTRACT(YEAR FROM ts)` | `EXTRACT(YEAR FROM ts)` (same!) |
| Date truncation | `DATE_TRUNC('month', ts)` | `TIMESTAMP_TRUNC(ts, MONTH)` |
| Array from string | `string_to_array(col, ', ')` | `SPLIT(col, ', ')` |
| Unnest array | `unnest(array)` | `UNNEST(array)` (same keyword, different context) |
| Age calculation | `AGE(ts1, ts2)` | `TIMESTAMP_DIFF(ts1, ts2, DAY)` |
| String concatenation | `\|\|` operator | `CONCAT()` or `\|\|` (both work in both) |
| Boolean display | `TRUE`/`FALSE` | `TRUE`/`FALSE` (same) |
| Parameter placeholder | `:param_name` or `$1` | `@param_name` |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PostgreSQL `::` cast only | `CAST()` syntax available in both dialects | Always available | Use `CAST()` for clarity in cross-dialect documentation, `::` for PostgreSQL-specific files |
| Manual NULL coalescing | `COALESCE()` standard SQL | Always available | Both dialects support it identically |
| Subqueries for complex logic | CTEs (`WITH` clause) | Widely available since PG 8.4 / BQ inception | Use CTEs for all multi-stage queries -- more readable for customers |
| ARRAY_AGG for list building | STRING_AGG for comma-separated lists | Both available | STRING_AGG is simpler for display-ready output |

## Open Questions

### 1. BigQuery %z Format Element Precision

- **What we know:** BigQuery's `PARSE_TIMESTAMP` supports `%z` for timezone offsets. PostgreSQL's `::TIMESTAMPTZ` cast handles `+0000` natively.
- **What is unclear:** Whether BigQuery's `%z` handles `+0000` (without colon) or requires `+00:00`. The documentation mentions `%Ez` for colon-separated offsets.
- **Recommendation:** Use `PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%z', col)` in BigQuery. If this fails for `+0000`, fall back to string manipulation: `REGEXP_REPLACE(col, r'(\+\d{2})(\d{2})$', r'\1:\2')` to insert the colon before parsing. Validate during implementation with actual BigQuery execution if possible. **Confidence: MEDIUM**

### 2. Lab Abnormal Flagging Without Interpretation Data

- **What we know:** All `lab_interpretation` values are NULL in sample data. The requirement CLIN-04 asks for "flagged abnormals."
- **What is unclear:** Whether real customer data will have non-NULL interpretation values.
- **Recommendation:** Include the `lab_interpretation` column in output (it will show data when available). Additionally, add a comment block with common LOINC reference ranges that customers can uncomment and customize. Document this as a data-quality-dependent feature. **Confidence: HIGH** (the approach is sound; the limitation is inherent in the data)

### 3. Parameter Syntax Convention

- **What we know:** PostgreSQL uses `:param` or `$1`; BigQuery uses `@param`.
- **What is unclear:** Whether to use parameterized queries or hardcode a sample patient_id for immediate runnability.
- **Recommendation:** Use a hardcoded sample patient_id (the one from sample data: `6f3bc061-8515-41b9-bc26-75fc55f53284`) with a clear comment saying "Replace with your patient_id". This makes queries immediately runnable from any SQL client without parameter binding setup. Add a comment showing the parameterized form for production use. **Confidence: HIGH**

## Sources

### Primary (HIGH confidence)

- PostgreSQL DDL: `particle-flat-observatory/ddl/postgres/create_all.sql` -- exact column names and types
- BigQuery DDL: `particle-flat-observatory/ddl/bigquery/create_all.sql` -- exact column names and types
- Sample data: `particle-flat-observatory/sample-data/flat_data.json` -- actual data values, formats, and volumes
- Normalizer: `particle-flat-observatory/src/observatory/normalizer.py` -- confirms only empty-string-to-NULL transformation
- Phase 1 decisions in STATE.md: all-TEXT/STRING ELT approach, quoted identifiers

### Secondary (MEDIUM confidence)

- [PostgreSQL timestamp documentation](https://www.postgresql.org/docs/current/datatype-datetime.html) -- ISO 8601 cast support
- [BigQuery conversion functions](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/conversion_functions) -- SAFE_CAST, PARSE_TIMESTAMP
- [BigQuery aggregate functions](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/aggregate_functions) -- STRING_AGG compatibility
- [BigQuery format elements](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/format-elements) -- %z timezone format

### Tertiary (LOW confidence)

- BigQuery `%z` format element handling of `+0000` without colon -- could not verify definitively; needs runtime validation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- this is pure SQL, no library uncertainty
- Architecture (file organization): HIGH -- follows existing ddl/ convention from Phase 1
- Dialect compatibility: HIGH for most features, MEDIUM for BigQuery timezone parsing
- Data model / join keys: HIGH -- verified against actual sample data
- Pitfalls: HIGH -- all discovered through direct data inspection

**Research date:** 2026-02-08
**Valid until:** Indefinite for SQL patterns; revalidate if Particle API changes field formats
