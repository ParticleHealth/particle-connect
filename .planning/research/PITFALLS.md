# Pitfalls Research

**Domain:** Healthcare flat-data pipeline (JSON to PostgreSQL/BigQuery)
**Researched:** 2026-02-07
**Confidence:** HIGH (verified against actual sample data + official docs + multiple sources)

## Critical Pitfalls

### Pitfall 1: Empty Strings Masquerading as NULLs

**What goes wrong:**
The Particle GET Flat API returns empty strings (`""`) for missing/absent data instead of JSON `null`. Every single nullable field in the sample data uses empty string -- zero actual NULL values exist across all 21 resource types (verified against `flat_data.json`). If the DDL uses typed columns (DATE, TIMESTAMP, INTEGER, FLOAT) and the pipeline inserts empty strings, PostgreSQL will throw type-cast errors (`invalid input syntax for type timestamp: ""`), and BigQuery will reject the load or silently store incorrect values.

**Why it happens:**
Developers assume JSON APIs return `null` for absent data. Particle's flat format is an opinionated denormalization that uses empty strings universally. Building DDL with strict types and then inserting raw API values without coercion causes immediate failures.

**How to avoid:**
- Implement a normalization layer between API response parsing and database insertion that converts empty strings to `None`/`NULL` for non-TEXT columns.
- For each field, define an explicit type mapping: `{field: "TEXT"}` gets empty string as-is; `{field: "TIMESTAMP"}` converts `""` to `NULL`.
- Test the normalization against the actual sample data before writing any DDL.
- Use `NULLIF(value, '')` in SQL views as a safety net for downstream queries.

**Warning signs:**
- `INSERT` statements failing with `invalid input syntax for type` errors.
- Date/timestamp columns containing `1970-01-01` or epoch-zero values (from empty-string-to-default coercion).
- BigQuery load jobs failing with `Could not parse '' as TIMESTAMP`.

**Phase to address:**
Phase 1 (DDL + Schema Design). This must be solved before any data loading code is written. The normalization function is a prerequisite for every downstream phase.

---

### Pitfall 2: Timestamp Format Inconsistency Across Resource Types

**What goes wrong:**
Particle's flat data uses at least five different timestamp formats across resource types, verified in `flat_data.json`:

| Format | Example | Found In |
|--------|---------|----------|
| ISO 8601 + Z (nanosecond) | `2026-02-06T02:41:44.378318936Z` | `aIOutputs.created` |
| ISO 8601 + offset (no colon) | `2025-11-01T23:30:00+0000` | `encounters`, `labs`, `medications`, `problems`, `procedures` |
| ISO 8601 no timezone | `1970-12-26T00:00:00` | `patients.date_of_birth` |
| Space-separated + microsecond | `1970-12-26 00:00:00.000000+00:00` | `transitions.dob`, `transitions.visit_*` |
| ISO 8601 + microsecond + colon offset | `2026-01-13T16:57:10.003238+00:00` | `transitions.status_date_time` |

A naive `CAST(value AS TIMESTAMP)` or a single `strptime` format string will work for some records and fail for others, often silently within the same table (e.g., `transitions` has both space-separated and T-separated formats).

**Why it happens:**
Different data sources feeding into Particle use different timestamp serialization. The flat format preserves source variation rather than normalizing. Developers test with one resource type and assume consistency.

**How to avoid:**
- Use Python's `dateutil.parser.isoparse()` or `datetime.fromisoformat()` (Python 3.11+ handles most ISO 8601 variants) for all timestamp parsing before insertion.
- Normalize all timestamps to a single format (ISO 8601 with T separator and UTC timezone) before insertion.
- For PostgreSQL, use `TIMESTAMPTZ` for all timestamp columns -- it accepts the broadest range of input formats.
- For BigQuery, use `TIMESTAMP` type (always UTC-normalized) and parse via `PARSE_TIMESTAMP()` with explicit format strings as a fallback.
- Build a per-field format detection test that runs against sample data during development.

**Warning signs:**
- Partial load failures where some rows in a batch succeed and others fail.
- Timestamp columns showing `NULL` for rows where the API clearly returned a date string.
- Off-by-hours errors from timezone offset misinterpretation.

**Phase to address:**
Phase 1 (Schema + Type Mapping). The timestamp normalization function must handle all five formats and be tested against every resource type's date fields.

---

### Pitfall 3: Schema Drift Between Customers

**What goes wrong:**
Particle's flat response includes fields that vary across customers. Some customers may have additional fields not present in the sample data, or fields may be absent entirely. If the DDL is generated from a single sample's field set, customer data with extra fields will fail on strict-schema inserts, and customers with fewer fields will have NULL columns they never expected.

BigQuery enforces column schemas: inserting data with extra fields causes load job failure unless `--schema_update_option=ALLOW_FIELD_ADDITION` is set. PostgreSQL `INSERT` statements with explicit column lists will fail if the data has columns not in the DDL.

**Why it happens:**
The flat format is a denormalization of FHIR resources from multiple health data networks. Different provider networks return different fields. The sample data represents one patient's data shape, not the universe of possible shapes.

**How to avoid:**
- Design the insertion logic to be schema-resilient: introspect incoming JSON keys, compare against known DDL columns, and insert only matching fields.
- For unknown/extra fields, either (a) store them in a `_extra_fields JSONB` column (PostgreSQL) / `_extra_fields JSON` column (BigQuery), or (b) skip them with a warning log.
- For missing fields, insert `NULL` explicitly.
- Make the DDL comprehensive (all known fields from the Particle API documentation, not just sample data).
- Add a `--schema-update` mode that can ALTER TABLE ADD COLUMN for new fields.

**Warning signs:**
- Pipeline works perfectly with sample data but fails on first real customer data.
- BigQuery load jobs failing with `no such field` errors.
- Customers reporting "missing data" because their extra fields were silently dropped.

**Phase to address:**
Phase 1 (DDL Design) for the base schema, Phase 2 (Ingestion Logic) for the resilient insertion code. This is the single most important pitfall for a customer-facing accelerator -- it determines whether the tool works on first try or requires debugging.

---

### Pitfall 4: Idempotency Without Natural Keys

**What goes wrong:**
Not all 21 resource types have obvious unique identifiers. While some have clear IDs (`encounter_id`, `procedure_id`, `lab_observation_id`), others lack a single unique key:
- `recordSources` has `resource_id` + `source_id` as a composite key.
- `aICitations` has `citation_id` but also `ai_output_id` + `resource_reference_id` combinations.
- Empty resource types (`allergies`, `coverages`, etc.) may gain records for other customers with unknown key structure.

If the pipeline uses `INSERT ... ON CONFLICT DO NOTHING` (PostgreSQL) or `MERGE` (BigQuery) with the wrong conflict target, re-runs will either duplicate data or silently skip updates.

In PostgreSQL, NULL values in composite unique keys are a known gotcha: `NULL != NULL`, so each insert with a NULL key component creates a new row instead of triggering a conflict. The Particle data uses empty strings (not NULL), but if the normalization layer (Pitfall 1) converts those to NULL, the upsert logic breaks.

**Why it happens:**
Developers define a primary key from one sample dataset without considering that the same field might be NULL or non-unique across different customers. The PostgreSQL `ON CONFLICT` clause requires exact unique constraint matching.

**How to avoid:**
- Audit every resource type's sample data and API documentation to identify the correct natural key for each table.
- For resource types without clear natural keys, add a deterministic surrogate key: hash of all field values or a `(patient_id, resource_type_id, field_hash)` composite.
- Keep the normalization layer aware of key columns: never convert key field empty strings to NULL.
- For PostgreSQL, ensure all columns in the `ON CONFLICT` target are `NOT NULL` or use a partial unique index.
- For BigQuery, use `MERGE` with explicit match conditions, and always include a `WHEN NOT MATCHED` clause.
- Use `DELETE + INSERT` (truncate-and-reload per patient per resource type) as the simplest idempotency strategy for batch loads. This avoids complex upsert logic entirely.

**Warning signs:**
- Row counts growing on each re-run of the pipeline.
- `ON CONFLICT` silently doing nothing when it should update.
- BigQuery `MERGE` statement scanning the entire table (cost explosion on large tables).

**Phase to address:**
Phase 2 (Ingestion Logic). Must be designed before the first INSERT statement is written. The `DELETE + INSERT` per-patient-per-resource-type pattern is strongly recommended as the initial approach.

---

### Pitfall 5: Mixed Numeric Types (int/float) Breaking DDL

**What goes wrong:**
Verified in `flat_data.json`: `medications.medication_statement_dose_value` contains both `int` and `float` values, and `vitalSigns.vital_sign_observation_value` contains both `int` and `float` values. If the DDL generator infers types from the first record (or a subset), it may create an `INTEGER` column that later rejects `float` values, or vice versa.

Additionally, some fields that look numeric are actually strings (e.g., `transition_id: "18229980713577542496"` is a 20-digit numeric string that overflows a 64-bit integer).

**Why it happens:**
JSON does not distinguish between integer and float types at the format level. Python's `json.load()` does distinguish (`int` vs `float`), but this is an implementation detail. DDL generators that use Python type introspection will get inconsistent results depending on which records they sample.

**How to avoid:**
- Default all numeric-looking fields to `NUMERIC`/`DECIMAL` (PostgreSQL) or `FLOAT64` (BigQuery) unless explicitly known to be integer-only.
- For ID fields that are numeric strings (e.g., `transition_id`, `citation_id`, `ai_output_id`), always use `TEXT`/`STRING` -- never integer types, regardless of content.
- Build the type inference to scan ALL records for a field, not just the first record. If any value is a float, the column must be float-capable.
- Document the type mapping decision for each field explicitly.

**Warning signs:**
- `INSERT` failing with `integer out of range` or `invalid input syntax for type integer`.
- Numeric IDs being silently truncated (e.g., `18229980713577542496` becoming `9223372036854775807` due to INT8 overflow).
- Loss of decimal precision in lab values.

**Phase to address:**
Phase 1 (DDL + Schema Design). The type mapping table must be finalized before DDL is generated.

---

### Pitfall 6: Credential and Service Account Key Exposure

**What goes wrong:**
The pipeline requires credentials for both Particle Health API (client_id, client_secret, scope_id) and BigQuery (GCP service account key). Customers copy-paste setup instructions and accidentally commit `.env` files or service account JSON keys to their repositories. For a healthcare pipeline handling PHI-adjacent data, this is a compliance incident, not just a security bug.

**Why it happens:**
The accelerator ships as a clone-and-run tool. Customers configure credentials in `.env` files or download service account keys to the project directory. Without explicit `.gitignore` entries and prominent warnings, credentials leak.

**How to avoid:**
- Ship a `.gitignore` that explicitly excludes: `.env`, `*.json` (service account keys), `*.key`, `credentials/`.
- Include a `.env.example` with placeholder values and comments explaining each variable.
- For BigQuery, recommend Application Default Credentials (`gcloud auth application-default login`) over service account key files. Document both paths but emphasize ADC.
- Add a pre-flight check in the pipeline script that warns if `.env` or service account key files are tracked by git.
- For Terraform, use a `backend` block that stores state remotely (GCS bucket) so `terraform.tfstate` (which contains credentials) is never local.
- Never log credential values -- use `SecretStr` pattern from the existing `particle-health-starters` codebase.

**Warning signs:**
- `git status` showing `.env` or `*.json` as tracked files.
- Service account key files in the project directory without `.gitignore` coverage.
- Terraform state files (`*.tfstate`) committed to the repository.
- Log output containing `client_secret` or service account private keys.

**Phase to address:**
Phase 0 (Project Scaffolding). The `.gitignore`, `.env.example`, and credential documentation must be in place before any code is written. This is a non-negotiable for healthcare tooling.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Store all fields as TEXT/STRING | Avoids all type-casting issues | Every downstream query needs CAST(); BigQuery scans full column width; no date range queries | Never for a production accelerator. Acceptable only as a debug/landing table. |
| Hardcode DDL for all 21 tables | Fast to write, no inference logic | Breaks when Particle adds fields or resource types; customer data with extra fields fails silently | Only if paired with a `_extra_fields` JSON overflow column. |
| Use `DELETE FROM table; INSERT...` for idempotency | Simple, always correct | Full table scans on every load; BigQuery DML costs per bytes scanned; slow for large tables | Acceptable for per-patient loading (small row counts). Never for full-dataset reloads. |
| Single timestamp format parser | Works for first resource type tested | Fails on transitions, aIOutputs, or any resource with different format | Never. Must handle all five observed formats from day one. |
| Skip empty resource types in DDL | Fewer tables to create, simpler code | Customer's first non-empty load fails because table doesn't exist | Never. All 21 tables must be created regardless of sample data emptiness. |
| Pin to specific Docker Postgres version tag | Reproducible builds | Misses security patches; customer on different architecture (ARM vs x86) may have issues | Acceptable if using multi-arch image tags like `postgres:16-alpine`. |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Particle Health API | Assuming flat response shape is stable across patients/customers | Build schema-resilient insertion that handles extra/missing fields gracefully |
| Particle Health API | Not handling rate limits (429) during batch retrieval for multiple patients | Use existing `tenacity` retry with backoff from `particle-health-starters`; add per-request delay |
| PostgreSQL (Docker) | Using `localhost` for host when running pipeline outside container | Use `host.docker.internal` (Mac/Windows) or container network name; document both scenarios |
| PostgreSQL (Docker) | Binding to port 5432 when customer already has PostgreSQL running locally | Use a non-standard port (e.g., `5433:5432` mapping) and make it configurable via `.env` |
| BigQuery | Using streaming inserts (`insertAll`) for batch data | Use load jobs (free) instead of streaming inserts ($0.05/GB). Batch pipeline does not need real-time availability. |
| BigQuery | Not setting `deletion_protection = false` in Terraform before destroy | Customers cannot `terraform destroy` to clean up; add explicit flag with comment explaining why |
| BigQuery | Assuming DDL column additions are free of constraints | New columns on existing BigQuery tables MUST be `NULLABLE` -- cannot add `REQUIRED` columns after table creation |
| Terraform | Storing state locally in repo directory | State contains service account credentials and resource IDs; use remote backend (GCS bucket) or at minimum `.gitignore` the `*.tfstate` files |
| Terraform | Not handling BigQuery dataset/table state drift | After manual BigQuery console edits, `terraform plan` shows drift; document that Terraform is source of truth |
| Docker Compose | Using bind mounts for PostgreSQL data directory | Volume permissions differ across Mac/Linux/Windows; use Docker-managed named volumes instead |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Single-row INSERT in a loop | Slow ingestion, high latency | Use batch INSERT with `executemany()` or `COPY` for PostgreSQL; use load jobs for BigQuery | > 1,000 records per resource type |
| BigQuery MERGE for upsert on large tables | Full table scan per MERGE; slot consumption; high cost | Use DELETE + INSERT per patient_id partition, or use BigQuery load jobs with WRITE_TRUNCATE disposition per partition | > 100K rows in target table |
| Loading all 21 resource types sequentially | Total pipeline time = sum of all resource type load times | Parallelize independent resource type loads (they share no foreign keys in flat format) | > 5 resource types with > 100 records each |
| VARCHAR(255) for all string columns in PostgreSQL | Wastes memory in query plans; `document_reference_content_data` can be 18K+ chars | Use `TEXT` for PostgreSQL (no length limit, same performance); use `STRING` for BigQuery (also no practical limit) | When `aIOutputs.text` (5K+ chars) or `documentReferences.document_reference_content_data` (18K+ chars) arrives |
| Not using BigQuery table partitioning/clustering | Full table scans for every query; high cost at scale | Partition by `patient_id` or ingestion date; cluster by resource type | > 1M rows across patients |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Including real patient data in sample files | PHI exposure; HIPAA violation | Use only synthetic/sandbox data; verify sample data provenance; add header comment to sample files stating "SYNTHETIC DATA ONLY" |
| Logging full API response bodies during debugging | PHI in clinical data appears in log files | Use the existing `structlog` PHI redaction processor from `particle-health-starters`; never log raw response bodies |
| Storing BigQuery service account key as JSON file in project | Key leak via git, backup, or file sharing | Prefer Application Default Credentials; if key file needed, store outside project directory and reference via env var path |
| Using Terraform with local state containing SA credentials | `terraform.tfstate` contains plaintext service account details | Use remote state backend (GCS); add `*.tfstate` and `*.tfstate.backup` to `.gitignore` |
| Not encrypting PostgreSQL connections in Docker | Data in transit is plaintext on the Docker network | For local dev this is acceptable; for any non-local deployment, enable SSL in PostgreSQL config |
| Committing `.env` file with Particle API credentials | Credential exposure via git history | Ship `.env.example` only; add `.env` to `.gitignore`; add pre-commit check |

## UX Pitfalls

Common user experience mistakes in this domain (UX = customer/developer experience for this accelerator).

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Requiring manual DDL execution before pipeline runs | Extra step customers forget; "table does not exist" error | Auto-create tables on first run; make DDL execution part of the pipeline's `--init` or `--setup` command |
| Showing raw Python tracebacks on pipeline failure | Customers cannot diagnose the issue; creates support tickets | Catch known errors and print actionable messages: "Port 5432 is in use. Set POSTGRES_PORT in .env to use a different port." |
| Silent success with no summary output | Customer does not know if data loaded correctly | Print a summary table after load: resource type, row count, any warnings (empty types, skipped fields) |
| Requiring separate Terraform and pipeline steps with no coordination | Customer runs pipeline before Terraform; BigQuery tables don't exist | Either (a) pipeline checks for table existence and runs DDL if needed, or (b) clear error message: "Run `make setup-cloud` first" |
| Different SQL query files for PostgreSQL vs BigQuery | Maintenance burden; customers confused about which to use | Write SQL queries using the common subset of GoogleSQL and PostgreSQL syntax; use COALESCE, TIMESTAMP functions, and standard aggregations that work on both |
| No way to validate setup before running the full pipeline | Customer discovers misconfiguration after 5 minutes of waiting | Add a `--check` or `--validate` command that tests connectivity, credentials, and table existence without loading data |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **DDL for all 21 resource types:** Often missing the 5 empty types (allergies, coverages, familyMemberHistories, immunizations, socialHistories) because the sample data has 0 records for them -- verify DDL exists for ALL 21 types regardless of sample emptiness
- [ ] **Timestamp parsing:** Often works for the main ISO 8601 format but fails on the space-separated `transitions` format -- verify parsing against ALL five timestamp format variations found in sample data
- [ ] **Empty string handling:** Often converts `""` to `NULL` globally, breaking TEXT fields that legitimately use empty strings -- verify the normalization is column-type-aware (only convert `""` to `NULL` for non-TEXT columns)
- [ ] **Idempotent re-runs:** Often tested with `INSERT` on empty table, never tested with duplicate data -- verify running the pipeline twice produces the same row count
- [ ] **Cross-platform Docker:** Often works on the developer's Mac but fails on Linux or Windows -- verify `docker compose up` works with Docker-managed volumes, non-default ports, and no pre-existing PostgreSQL
- [ ] **BigQuery load jobs:** Often tested with small data; never tested with 1000+ records -- verify load job handles the BigQuery 1000-load-jobs-per-day limit and uses batching appropriately
- [ ] **Large string fields:** Often uses VARCHAR(255) or assumes short strings -- verify `aIOutputs.text` (5K+ chars), `aIOutputs.resource_reference_ids` (6K+ chars), and `documentReferences.document_reference_content_data` (18K+ chars) load without truncation
- [ ] **SQL query compatibility:** Often tested on one database only -- verify every shipped SQL query runs on BOTH PostgreSQL and BigQuery without modification
- [ ] **Numeric ID overflow:** Often treated as INTEGER -- verify `transition_id` (20-digit numeric string: `18229980713577542496`) and `citation_id` are stored as TEXT/STRING, not INTEGER
- [ ] **Credential safety:** Often `.gitignore` covers `.env` but misses Terraform state and GCP service account keys -- verify `*.tfstate`, `*.tfstate.backup`, and `*-key.json` are in `.gitignore`

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Empty strings not normalized (type errors on insert) | LOW | Add normalization function; re-run pipeline (idempotent design handles re-runs) |
| Timestamp parsing failure (partial data load) | LOW | Fix parser; truncate affected table; re-run pipeline |
| Schema drift (customer has extra fields) | MEDIUM | Add `_extra_fields` JSON column via ALTER TABLE; update insertion logic to capture unknowns; re-run |
| Wrong natural key (duplicate rows) | MEDIUM | Identify correct key; deduplicate existing data with `DELETE` + subquery keeping latest; update upsert logic |
| Numeric ID overflow (data truncation/corruption) | HIGH | ALTER column type from INTEGER to TEXT; re-load all affected data; audit downstream queries for numeric comparisons |
| Credential exposure (committed to git) | HIGH | Rotate ALL exposed credentials immediately; use `git filter-branch` or BFG to scrub history; notify customer's security team |
| Terraform state drift (manual BigQuery edits) | MEDIUM | Run `terraform import` for manually-created resources; or `terraform state rm` and re-create |
| BigQuery cost spike (streaming inserts instead of load jobs) | MEDIUM | Switch to load jobs; costs stop immediately but already-incurred charges remain |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Empty strings as NULLs | Phase 1: Schema + Type Mapping | Unit test: normalize(`""`, `TIMESTAMP`) returns `None`; normalize(`""`, `TEXT`) returns `""` |
| Timestamp format inconsistency | Phase 1: Schema + Type Mapping | Test: parse all date fields from sample data across all 21 resource types without error |
| Schema drift between customers | Phase 2: Ingestion Logic | Test: insert a record with an extra field not in DDL -- should log warning, not crash |
| Idempotency without natural keys | Phase 2: Ingestion Logic | Test: run pipeline twice with same data -- row counts match after both runs |
| Mixed numeric types (int/float) | Phase 1: Schema + Type Mapping | Review: no INTEGER columns for fields where floats appear; no INTEGER for large numeric string IDs |
| Credential exposure | Phase 0: Project Scaffolding | Verify: `.gitignore` covers `.env`, `*.tfstate`, `*-key.json`; `.env.example` has no real values |
| Docker cross-platform issues | Phase 3: Local Mode (Docker + PG) | Test: `docker compose up` on Mac and Linux with and without existing port 5432 listener |
| BigQuery cost traps | Phase 4: Cloud Mode (Terraform + BQ) | Review: no streaming inserts in code; load jobs used; partitioning documented for scale |
| SQL dialect differences | Phase 5: Analytics Queries | Test: every shipped SQL query runs on both PostgreSQL and BigQuery and returns results |
| Terraform state management | Phase 4: Cloud Mode (Terraform + BQ) | Verify: `.gitignore` includes state files; remote backend documented; `deletion_protection` handled |

## Sources

- Sample data analysis: `/Users/sangyetsakorshika/Documents/GitHub/particle-connect/particle-health-starters/sample-data/flat_data.json` (direct inspection, HIGH confidence)
- BigQuery schema modification rules: [Managing table schemas (Google Cloud)](https://docs.cloud.google.com/bigquery/docs/managing-table-schemas) (MEDIUM confidence -- redirected fetch, partial content)
- BigQuery DML limits: [DML without limits (Google Cloud Blog)](https://cloud.google.com/blog/products/data-analytics/dml-without-limits-now-in-bigquery) (MEDIUM confidence -- WebSearch verified)
- BigQuery pricing -- streaming vs load: [BigQuery Pricing Guide (Airbyte)](https://airbyte.com/data-engineering-resources/bigquery-pricing), [Cutting 95% costs with file loads (Medium)](https://medium.com/google-developer-experts/trimming-down-over-95-of-your-bigquery-costs-using-file-loads-d08dd3d8b2fd) (MEDIUM confidence -- multiple sources agree)
- PostgreSQL ON CONFLICT NULL gotcha: [PostgreSQL mailing list re: upsert with nulls](https://www.postgresql.org/message-id/20161004205648.GV4498@aart.rice.edu), [Atomic UPSERT with nullable columns](https://blag.nullteilerfrei.de/2018/08/26/atomic-upsert-with-unique-constraint-on-null-able-column-in-postgresql/) (HIGH confidence -- PostgreSQL official + verified pattern)
- Docker PostgreSQL volume permissions: [moby/moby #22075](https://github.com/moby/moby/issues/22075), [docker-library/postgres #346](https://github.com/docker-library/postgres/issues/346) (HIGH confidence -- GitHub issues with reproduction steps)
- Docker PostgreSQL collation issue: [postgres Docker image Debian upgrade](https://vonng.com/en/db/no-docker-pg/) (MEDIUM confidence -- single detailed source)
- Terraform BigQuery state issues: [BigQuery schema state pain (Medium)](https://medium.com/@upadhyayankit403/if-only-terraform-used-maps-fixing-bigquery-schema-state-pain-112f3e869f8e), [terraform-provider-google #11604](https://github.com/hashicorp/terraform-provider-google/issues/11604) (MEDIUM confidence -- GitHub issue + blog post)
- Schema drift general patterns: [Managing Schema Drift (Estuary)](https://estuary.dev/blog/schema-drift/) (LOW confidence -- general advice, not healthcare-specific)
- Idempotent pipeline patterns: [Core Data Engineering: Idempotency (Areca)](https://www.arecadata.com/core-data-engineering-concepts-idempotency/), [How to make data pipelines idempotent (Start Data Engineering)](https://www.startdataengineering.com/post/why-how-idempotent-data-pipeline/) (MEDIUM confidence -- multiple sources agree on patterns)
- SQL dialect differences: [SQL Dialects Explained (Data With Sarah)](https://datawithsarah.com/post/sql-dialects-explained-translating-between-databases-without-losing-your-mind/), [BigQuery SQL Syntax Differences (Daasity)](https://www.daasity.com/post/bigquery-sql-syntax) (MEDIUM confidence -- multiple sources)
- HIPAA credential management: [HIPAA Compliance for Healthcare Database Management (Liquibase)](https://www.liquibase.com/resources/guides/hipaa-compliance-for-healthcare-database-management-best-practices) (MEDIUM confidence -- vendor documentation)
- psycopg2 JSON NULL handling: [psycopg/psycopg2 Discussion #1433](https://github.com/psycopg/psycopg2/discussions/1433) (HIGH confidence -- library maintainer discussion)

---
*Pitfalls research for: Healthcare flat-data pipeline (Particle Health GET Flat to PostgreSQL/BigQuery)*
*Researched: 2026-02-07*
