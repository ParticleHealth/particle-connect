# Requirements: Particle Flat Data Pipeline

**Defined:** 2026-02-07
**Core Value:** Customers go from raw Particle flat data to queryable structured tables with useful analytics queries — working from a clean checkout with zero code changes beyond configuration.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Pipeline Core

- [x] **PIPE-01**: DDL statements generated for all 21 Particle flat resource types (aICitations, aIOutputs, allergies, coverages, documentReferences, encounters, familyMemberHistories, immunizations, labs, locations, medications, organizations, patients, practitioners, problems, procedures, recordSources, socialHistories, sources, transitions, vitalSigns)
- [x] **PIPE-02**: Pipeline handles empty strings from Particle API as NULLs (normalization layer)
- [x] **PIPE-03**: Pipeline handles 5+ timestamp formats present in Particle flat data
- [x] **PIPE-04**: Pipeline handles mixed int/float numeric values and large numeric string IDs
- [x] **PIPE-05**: Schema-resilient loading — handles missing fields, extra fields, and empty resource arrays without crashing
- [ ] **PIPE-06**: Idempotent loading via delete+insert per patient_id per resource type — safe to re-run
- [x] **PIPE-07**: Pipeline gracefully skips empty resource types (logs info, creates empty table, no error)

### Ingestion

- [ ] **INGEST-01**: File-based ingestion loads flat_data.json (or any Particle flat JSON file) into target database
- [ ] **INGEST-02**: Live API ingestion authenticates with Particle Health and calls GET Flat endpoint
- [ ] **INGEST-03**: API ingestion includes retries with exponential backoff for 429/5xx errors
- [ ] **INGEST-04**: API ingestion includes configurable timeout
- [ ] **INGEST-05**: Both ingestion modes feed the same downstream pipeline (parse → load)

### Local Mode

- [ ] **LOCAL-01**: Docker Compose file spins up PostgreSQL with pre-configured database and user
- [ ] **LOCAL-02**: DDL auto-runs on container startup (tables created automatically)
- [ ] **LOCAL-03**: Single command loads sample data into local PostgreSQL
- [ ] **LOCAL-04**: Docker volumes persist data across container restarts
- [ ] **LOCAL-05**: Configurable PostgreSQL port (avoids conflicts with existing local PG)

### Cloud Mode

- [ ] **CLOUD-01**: Terraform module creates BigQuery dataset
- [ ] **CLOUD-02**: Terraform creates all 21 resource type tables with correct BigQuery column types
- [ ] **CLOUD-03**: Terraform creates service account with minimum required permissions
- [ ] **CLOUD-04**: Python loader uses google-cloud-bigquery load jobs (not streaming inserts)
- [ ] **CLOUD-05**: BigQuery loader uses same idempotent delete+insert pattern as PostgreSQL
- [ ] **CLOUD-06**: Terraform uses variables for project ID, dataset name, region (customer-configurable)

### CLI

- [ ] **CLI-01**: CLI entry point with typer — `particle-pipeline load --source file --target postgres`
- [ ] **CLI-02**: CLI supports `--source file` and `--source api` modes
- [ ] **CLI-03**: CLI supports `--target postgres` and `--target bigquery` modes
- [ ] **CLI-04**: CLI reads configuration from environment variables / .env file
- [ ] **CLI-05**: CLI provides `--help` with usage examples

### Analytics Queries — Clinical

- [ ] **CLIN-01**: Patient summary query — demographics, conditions, medications, allergies for a patient
- [ ] **CLIN-02**: Active problem list — current conditions with onset dates and clinical status
- [ ] **CLIN-03**: Medication timeline — medications with start/end dates, dosage, and status
- [ ] **CLIN-04**: Lab results over time — lab values trended by date, flagged abnormals
- [ ] **CLIN-05**: Vital sign trends — blood pressure, heart rate, temperature, BMI over time
- [ ] **CLIN-06**: Encounter history — chronological encounters with type, location, duration
- [ ] **CLIN-07**: Care team — practitioners involved in care with roles and specialties

### Analytics Queries — Operational

- [ ] **OPS-01**: Data completeness scorecard — records per resource type, percentage populated
- [ ] **OPS-02**: Source coverage — which data sources contributed records, by type
- [ ] **OPS-03**: Record freshness — most recent records per resource type and source
- [ ] **OPS-04**: Data provenance — trace any clinical record back to originating source
- [ ] **OPS-05**: AI output summary — AI-generated insights with citation counts and source documents

### Analytics Queries — Cross-cutting

- [ ] **CROSS-01**: Encounter-to-labs join — labs ordered during specific encounters
- [ ] **CROSS-02**: Medication-problem correlation — medications mapped to the problems they treat
- [ ] **CROSS-03**: Procedures by encounter — procedures performed during each encounter with practitioners

### Developer Experience

- [ ] **DX-01**: Actionable error messages — tells what went wrong and how to fix it (not raw stack traces)
- [ ] **DX-02**: Data quality report after loading — records per table, null %, date ranges, issues flagged
- [ ] **DX-03**: README with setup steps for local mode (Docker)
- [ ] **DX-04**: README with setup steps for cloud mode (Terraform + BigQuery)
- [x] **DX-05**: .env.example with all required environment variables documented
- [x] **DX-06**: Sample data (flat_data.json) included in repo for immediate testing
- [ ] **DX-07**: SQL queries work on both PostgreSQL and BigQuery (standard SQL where possible, dialect variants where needed)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Schema Intelligence

- **SCHEMA-01**: Schema auto-detection from JSON — infer DDL from flat data structure automatically
- **SCHEMA-02**: Schema diff utility — show what changed between Particle API versions

### Scale

- **SCALE-01**: Multi-patient batch processing with parallel workers and rate limiting
- **SCALE-02**: Progress tracking for batch loads

### Integration

- **INTEG-01**: Orchestration integration docs (how to plug into Airflow, Dagster, etc.)
- **INTEG-02**: Cron/Cloud Scheduler example for periodic refreshes

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Web UI / dashboard | Customers have their own BI tools (Metabase, Looker, Tableau). Building UI competes with their stack. |
| Real-time streaming / CDC | Particle API is request-response, not streaming. Over-engineers the problem. |
| FHIR R4 resource parsing | Flat format IS the analytics-friendly projection of FHIR. Separate code path doubles maintenance. |
| Multi-database (Snowflake, Redshift) | Each DB has different DDL, drivers, auth. Ship PG + BQ only, document extensibility. |
| Orchestration framework (Airflow, etc.) | Turns simple accelerator into infrastructure project. Customers who need it already have it. |
| dbt models / transformations | Raw tables + queries only. Customers build their own transforms. |
| HIPAA compliance features | HIPAA is organizational, not tool-level. Document security considerations instead. |
| Schema migration tooling (Alembic) | DDL regeneration + schema-resilient loading handles evolution. Migration infra is overkill for starter kit. |
| Config file support (YAML/TOML) | Env vars only, consistent with particle-health-starters. Prevents secrets in config files. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PIPE-01 | Phase 1: Schema Foundation | Complete |
| PIPE-02 | Phase 1: Schema Foundation | Complete |
| PIPE-03 | Phase 1: Schema Foundation | Complete |
| PIPE-04 | Phase 1: Schema Foundation | Complete |
| PIPE-05 | Phase 1: Schema Foundation | Complete |
| PIPE-06 | Phase 1: Schema Foundation | Pending |
| PIPE-07 | Phase 1: Schema Foundation | Complete |
| INGEST-01 | Phase 2: Local Pipeline | Pending |
| INGEST-02 | Phase 5: API Ingestion | Pending |
| INGEST-03 | Phase 5: API Ingestion | Pending |
| INGEST-04 | Phase 5: API Ingestion | Pending |
| INGEST-05 | Phase 2: Local Pipeline | Pending |
| LOCAL-01 | Phase 2: Local Pipeline | Pending |
| LOCAL-02 | Phase 2: Local Pipeline | Pending |
| LOCAL-03 | Phase 2: Local Pipeline | Pending |
| LOCAL-04 | Phase 2: Local Pipeline | Pending |
| LOCAL-05 | Phase 2: Local Pipeline | Pending |
| CLOUD-01 | Phase 4: Cloud Mode | Pending |
| CLOUD-02 | Phase 4: Cloud Mode | Pending |
| CLOUD-03 | Phase 4: Cloud Mode | Pending |
| CLOUD-04 | Phase 4: Cloud Mode | Pending |
| CLOUD-05 | Phase 4: Cloud Mode | Pending |
| CLOUD-06 | Phase 4: Cloud Mode | Pending |
| CLI-01 | Phase 2: Local Pipeline | Pending |
| CLI-02 | Phase 2: Local Pipeline | Pending |
| CLI-03 | Phase 2: Local Pipeline | Pending |
| CLI-04 | Phase 2: Local Pipeline | Pending |
| CLI-05 | Phase 2: Local Pipeline | Pending |
| CLIN-01 | Phase 3: Analytics Queries | Pending |
| CLIN-02 | Phase 3: Analytics Queries | Pending |
| CLIN-03 | Phase 3: Analytics Queries | Pending |
| CLIN-04 | Phase 3: Analytics Queries | Pending |
| CLIN-05 | Phase 3: Analytics Queries | Pending |
| CLIN-06 | Phase 3: Analytics Queries | Pending |
| CLIN-07 | Phase 3: Analytics Queries | Pending |
| OPS-01 | Phase 3: Analytics Queries | Pending |
| OPS-02 | Phase 3: Analytics Queries | Pending |
| OPS-03 | Phase 3: Analytics Queries | Pending |
| OPS-04 | Phase 3: Analytics Queries | Pending |
| OPS-05 | Phase 3: Analytics Queries | Pending |
| CROSS-01 | Phase 3: Analytics Queries | Pending |
| CROSS-02 | Phase 3: Analytics Queries | Pending |
| CROSS-03 | Phase 3: Analytics Queries | Pending |
| DX-01 | Phase 2: Local Pipeline | Pending |
| DX-02 | Phase 2: Local Pipeline | Pending |
| DX-03 | Phase 2: Local Pipeline | Pending |
| DX-04 | Phase 4: Cloud Mode | Pending |
| DX-05 | Phase 1: Schema Foundation | Complete |
| DX-06 | Phase 1: Schema Foundation | Complete |
| DX-07 | Phase 3: Analytics Queries | Pending |

**Coverage:**
- v1 requirements: 50 total
- Mapped to phases: 50
- Unmapped: 0

---
*Requirements defined: 2026-02-07*
*Last updated: 2026-02-08 after Phase 1 completion*
