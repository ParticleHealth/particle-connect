# Project Research Summary

**Project:** Particle Health Flat API to Database Pipeline
**Domain:** Healthcare data pipeline (ETL accelerator)
**Researched:** 2026-02-07
**Confidence:** HIGH

## Executive Summary

This project builds a healthcare data pipeline accelerator that loads Particle Health's Flat API data (21 FHIR-derived resource types) into PostgreSQL or BigQuery. The research shows this is fundamentally a JSON-to-database ETL with two critical differentiators: (1) dual-target support (local Docker PostgreSQL for demos, cloud BigQuery for production), and (2) pre-built clinical analytics queries that deliver immediate value. The recommended approach is a clean adapter pattern with database-agnostic schema generation, resilient to the data quality issues endemic to healthcare APIs (empty-string nulls, inconsistent timestamp formats, schema drift across customers).

The most significant finding is that Particle's flat format has subtle but pervasive data quality issues that will break naive implementations: empty strings where JSON nulls are expected, five different timestamp formats across resource types, and numeric ID strings that overflow standard integers. Every successful healthcare data pipeline we researched implements a normalization layer between API parsing and database insertion. The second key finding is that idempotency via delete-and-replace (per patient, per resource type) is simpler and more reliable than complex upsert logic, given the ambiguous natural keys across 21 heterogeneous tables.

The primary risk is credential exposure — this is a customer-facing accelerator handling PHI-adjacent data, requiring explicit safeguards (strict `.gitignore`, Application Default Credentials over service account keys, no logging of sensitive payloads). The second risk is schema drift between customers causing silent data loss; schema-resilient loading with explicit handling of extra/missing fields is non-negotiable for production use.

## Key Findings

### Recommended Stack

Python 3.12+ with modern database drivers: psycopg 3.3 for PostgreSQL (COPY protocol for bulk loading) and google-cloud-bigquery 3.40 for BigQuery (load jobs, not streaming inserts). The project already has the foundation (httpx, pydantic, structlog, tenacity) from particle-health-starters; add psycopg[binary], google-cloud-bigquery, typer (CLI), and rich (terminal output).

**Core technologies:**
- **psycopg 3.3**: PostgreSQL driver with native COPY protocol for bulk loading 21 resource tables efficiently
- **google-cloud-bigquery 3.40**: Official client with load_table_from_json for batch loads (free) instead of streaming inserts (costly)
- **typer 0.21 + rich 14.3**: Type-hint-driven CLI with progress bars and colored output for customer-facing UX
- **pydantic 2.12**: Schema validation for Particle API JSON before DB insertion, handles type coercion and cross-field validation
- **Docker Compose**: PostgreSQL 17 (alpine) for local mode with named volumes and health checks
- **Terraform 1.14+ with google provider ~>7.0**: BigQuery dataset and table provisioning with IaC

**Critical version notes:**
- Python 3.12 minimum (project already requires 3.12 per pyproject.toml)
- Do NOT use psycopg2-binary (libssl conflicts, maintenance mode) — use psycopg 3.3 with optional binary speedup
- Do NOT use SQLAlchemy (ORM overhead unnecessary for ETL) — raw psycopg3 is faster and more transparent
- Do NOT use pandas (300MB+ dependency, no transformation needed for pre-flattened data)

### Expected Features

**Must have (table stakes):**
- **DDL generation for all 21 resource types** — auto-generate from JSON schema, handle all types even if empty in sample data
- **Dual ingestion mode (file + API)** — file mode (flat_data.json) for zero-credential demos, API mode for production
- **Docker PostgreSQL local mode** — `docker compose up` and done, no manual setup
- **Idempotent loading** — re-run without duplicates via UPSERT or delete-and-replace per patient
- **Schema-resilient loading** — handle missing arrays, extra fields, null values without crashing
- **10-15 pre-built SQL analytics queries** — clinical (patient summaries, lab trends, medication timelines) and operational (data completeness, source coverage)
- **Sample data included** — flat_data.json (904KB, 21 types, 1,187 records) already exists
- **Clear README** — clone, configure, run instructions for both local and cloud paths

**Should have (competitive advantage):**
- **BigQuery cloud mode with Terraform** — production-ready IaC, not just local-only demo tool
- **Pre-built clinical analytics** — medication adherence gaps, lab trend analysis, encounter utilization — immediate "so what?" value
- **AI citations as queryable data** — Particle's aICitations and aIOutputs are unique resources not in FHIR; making them SQL-queryable is differentiated value
- **Data quality report** — post-load summary of record counts, null percentages, date ranges, potential issues
- **Schema auto-detection** — generate DDL from JSON introspection, handles Particle schema evolution

**Defer (v2+):**
- Web UI/dashboard (customers have their own BI tools)
- Real-time streaming/CDC (batch-oriented source)
- FHIR R4 parsing (Flat IS the FHIR projection)
- Multi-database support beyond PG/BQ (extensible but defer actual implementations)
- Orchestration framework integration (customers who need it already have it)

### Architecture Approach

Four-layer architecture: Ingestion (API client + file reader), Processing (JSON parser, schema inspector, DDL generator), Loading (adapter pattern with PostgresLoader and BigQueryLoader implementations), and Query (static SQL library organized by clinical/operational use case). The adapter pattern enables dual-target support without leaking database-specific logic into shared components. Schema generation is dialect-aware via type maps (Python types → PostgreSQL types vs BigQuery types).

**Major components:**
1. **JSON Parser + Schema Inspector** — splits flat response into per-resource-type arrays, infers column types from values across all records (not just first record)
2. **DDL Generator** — dialect-aware CREATE TABLE generation from inferred schema, uses type maps to translate logical types to database-specific SQL types
3. **DatabaseLoader interface + implementations** — abstract base with create_tables(), load_records(), upsert_records(); PostgresLoader uses psycopg COPY protocol; BigQueryLoader uses load_table_from_json batch jobs
4. **SQL Query Library** — pre-built analytics queries in sql/clinical/ and sql/operational/, written using standard SQL subset compatible with both PostgreSQL and BigQuery

**Key patterns:**
- **Delete-and-replace idempotency** — for each patient_id, DELETE existing records then INSERT new, simpler than per-table natural key identification
- **Schema-resilient insertion** — introspect incoming JSON keys, match against known DDL columns, capture extra fields in _extra_fields JSON column or log and skip
- **Empty-string normalization** — convert `""` to NULL only for non-TEXT columns (timestamp, numeric, boolean), preserve empty strings for TEXT columns

### Critical Pitfalls

1. **Empty strings masquerading as NULLs** — Particle returns `""` instead of JSON `null` for all missing data; inserting `""` into TIMESTAMP/INTEGER columns causes type-cast errors. Fix: implement normalization layer that converts `""` to NULL only for non-TEXT columns, test against all 21 resource types before writing DDL.

2. **Timestamp format inconsistency** — Five different timestamp formats across resource types: `2026-02-06T02:41:44.378318936Z`, `2025-11-01T23:30:00+0000`, `1970-12-26T00:00:00`, `1970-12-26 00:00:00.000000+00:00`, `2026-01-13T16:57:10.003238+00:00`. A single `strptime` format fails. Fix: use `dateutil.parser` or Python 3.11+ `fromisoformat` with fallback parsing, normalize all timestamps to single format before insertion.

3. **Schema drift between customers** — Different customers have different fields based on their data sources; extra fields cause BigQuery load job failures, missing fields leave unexpected nulls. Fix: schema-resilient insertion that matches incoming keys against DDL columns, stores unknowns in _extra_fields JSON column or logs warning and skips, comprehensive DDL from API docs not just sample data.

4. **Idempotency without natural keys** — Not all resource types have obvious unique identifiers (recordSources has composite key, empty types have unknown structure); wrong conflict target causes duplicates or silent skip. Fix: use delete-and-replace per patient_id instead of complex per-table upsert logic; patient_id is universal partition key present in all resource types.

5. **Credential and service account key exposure** — Customers copy-paste setup and commit `.env` files or GCP SA keys to repos; PHI-adjacent data makes this a compliance incident. Fix: strict `.gitignore` covering `.env`, `*.tfstate`, `*-key.json`; use Application Default Credentials; pre-flight check warning if credentials tracked by git; never log credential values.

6. **Mixed numeric types breaking DDL** — `medications.medication_statement_dose_value` and `vitalSigns.vital_sign_observation_value` contain both int and float; numeric ID strings like `transition_id: "18229980713577542496"` overflow INT64. Fix: default all numeric-looking fields to NUMERIC/FLOAT64, store all ID fields as TEXT/STRING regardless of content, scan ALL records for type inference not just first record.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 0: Project Scaffolding
**Rationale:** Credential safety is non-negotiable for healthcare tooling; must be in place before any code is written to prevent inadvertent PHI-adjacent data exposure.
**Delivers:** `.gitignore` covering `.env`, `*.tfstate`, `*-key.json`; `.env.example` with placeholders; `pyproject.toml` with dependencies; `docker-compose.yml` skeleton; README structure
**Addresses:** Pitfall 5 (credential exposure), project structure from ARCHITECTURE.md
**Avoids:** Committing sensitive configuration before gitignore exists

### Phase 1: Schema Foundation (DDL Generation)
**Rationale:** Everything depends on tables existing; DDL generation validates the data model before database-specific implementations are built. This phase has zero external dependencies (pure Python + sample JSON).
**Delivers:** JSON parser, schema inspector (type inference from all records), DDL generator (dialect-aware with type maps), DDL files for all 21 resource types (PostgreSQL and BigQuery variants), empty-string normalization function, timestamp parsing with all five format variants
**Addresses:** Must-have features (DDL generation, schema-resilient loading), Pitfalls 1-3, 6 (empty strings, timestamps, schema drift, numeric types)
**Avoids:** Building database loaders before data model is validated; type-casting errors on first real data

### Phase 2: Local Mode (PostgreSQL + File Ingestion)
**Rationale:** Local mode proves the pipeline end-to-end without credentials or cloud dependencies; fastest iteration path. File ingestion (flat_data.json) enables "works from clean checkout" promise.
**Delivers:** Docker Compose PostgreSQL setup, PostgresLoader with COPY protocol or batch inserts, delete-and-replace idempotency per patient_id, file-based ingestion, CLI with `load` command, data quality validation
**Uses:** psycopg[binary] 3.3, Docker postgres:17-alpine
**Implements:** DatabaseLoader interface (adapter pattern), idempotent loading strategy
**Addresses:** Must-have features (Docker local mode, file ingestion, idempotent loading), Pitfall 4 (idempotency)
**Avoids:** Building cloud mode before local pipeline is proven

### Phase 3: Analytics Query Library
**Rationale:** Independent of database implementation (static SQL files); can be built in parallel with Phase 2. Queries deliver immediate proof-of-value and validate that DDL is analytics-ready.
**Delivers:** 10-15 SQL queries in sql/clinical/ (patient summaries, encounter timelines, lab trends, medication lists, vital sign trends, problem lists) and sql/operational/ (data completeness, source coverage, record freshness, provenance), queries tested on both PostgreSQL and BigQuery (standard SQL subset)
**Addresses:** Must-have feature (pre-built analytics queries), should-have (clinical analytics, AI citations, transition-of-care analytics)
**Validates:** DDL is fit for purpose; column names and types support real queries

### Phase 4: Cloud Mode (BigQuery + Terraform)
**Rationale:** Builds on proven local pipeline; BigQuery adds production-ready cloud target with IaC for reproducibility. This phase requires GCP project and adds Terraform complexity.
**Delivers:** Terraform module (google_bigquery_dataset, google_bigquery_table, IAM), BigQueryLoader using load_table_from_json (batch jobs not streaming), Application Default Credentials setup, BigQuery-specific DDL adjustments (partitioning recommendations), CLI flag `--target bigquery`
**Uses:** google-cloud-bigquery 3.40, Terraform google provider ~>7.0
**Implements:** BigQuery adapter in DatabaseLoader pattern
**Addresses:** Should-have feature (BigQuery cloud mode with Terraform), Pitfall 5 (credential safety via ADC)
**Avoids:** Streaming inserts (costly); hardcoded service account keys

### Phase 5: API Ingestion Mode
**Rationale:** Deferred until local file mode is fully validated; adds Particle API authentication, rate limiting, and error handling from particle-health-starters.
**Delivers:** API client integration (reuse ParticleHTTPClient from particle-health-starters), CLI flag `--source api`, patient ID input, retry logic with tenacity, PHI redaction in logs
**Uses:** Existing httpx, tenacity, structlog from particle-health-starters
**Addresses:** Must-have feature (dual ingestion mode - API path)
**Depends on:** Phases 1-2 complete (ingestion pipeline must work with file data first)

### Phase 6: Production Hardening
**Rationale:** After core functionality proven, add operational features for production use.
**Delivers:** Schema auto-detection from JSON, data quality report post-load, multi-patient batch wrapper (optional), pre-flight validation (--check command), error messages with actionable fixes, comprehensive README with both paths
**Addresses:** Should-have features (schema auto-detection, data quality report), anti-features documented (what NOT to add)

### Phase Ordering Rationale

- **Phase 0 first:** Healthcare data + customer-facing tool = credential safety is non-negotiable from day one
- **Phase 1 before database work:** Schema validation with zero dependencies prevents building on wrong data model
- **Local before cloud:** Docker PostgreSQL is simpler, faster iteration, proves pipeline before adding Terraform/GCP complexity
- **File before API:** File ingestion enables zero-credential demos and validates pipeline without rate limiting / auth complications
- **Analytics in parallel:** SQL queries are independent and validate DDL fitness for actual use cases
- **API mode deferred:** Reuses existing particle-health-starters client; only makes sense after file mode proven
- **Production features last:** Operational nice-to-haves after core value delivered

This ordering minimizes blocked work (Phase 1 builds foundation for both Phase 2 and 4 in parallel), de-risks early (local file mode is simplest path), and enables customer validation before cloud investment (Docker demo first, GCP billing second).

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 4 (Cloud Mode):** BigQuery partitioning strategies for healthcare data access patterns (by patient_id vs ingestion date vs resource type), IAM roles and healthcare-specific GCP security considerations, Terraform state management for customer deployments
- **Phase 5 (API Ingestion):** Particle Health API rate limits and batch retrieval patterns for multiple patients, pagination handling if flat response exceeds limits, error codes and retry strategies specific to healthcare APIs

**Phases with standard patterns (skip research-phase):**
- **Phase 0-1:** Project scaffolding and JSON parsing are well-documented patterns, no healthcare-specific complexity
- **Phase 2:** PostgreSQL bulk loading via COPY/execute_values is standard ETL, Docker Compose patterns well-established
- **Phase 3:** SQL query writing is implementation work, not research (validate syntax compatibility via testing)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified on PyPI, Docker Hub, Terraform registry; existing project dependencies confirmed in pyproject.toml |
| Features | HIGH | Based on actual flat_data.json structure (904KB, 21 types, 1,187 records), Particle Health API documentation, competitor analysis (Redox+Databricks, Google HDE, Microsoft HDF) |
| Architecture | HIGH | Adapter pattern is standard for dual-target ETL; component responsibilities validated against healthcare pipeline patterns; build order has clear dependency chain |
| Pitfalls | HIGH | All six critical pitfalls verified against actual sample data (empty strings, timestamp formats, numeric types, schema drift patterns confirmed); credential exposure risks standard for healthcare tooling |

**Overall confidence:** HIGH

Research is grounded in direct observation of actual Particle Health flat data (flat_data.json), official vendor documentation (Particle Health, Google Cloud, PostgreSQL, BigQuery), and established healthcare data pipeline patterns. All recommended technologies have verified versions and Python compatibility. All identified pitfalls have reproduction cases in sample data and documented prevention strategies.

### Gaps to Address

**Schema evolution handling:** Research identified that Particle may add new resource types or fields over time, but sample data represents single point in time. During Phase 1 (DDL generation), build in explicit versioning or change detection to alert when sample data diverges from DDL. During Phase 2 (ingestion), schema-resilient insertion handles new fields via _extra_fields column, but should be tested with synthetic "future schema" test cases.

**BigQuery cost optimization at scale:** Research covered standard patterns (load jobs vs streaming, partitioning), but actual access patterns determine optimal partitioning strategy. During Phase 4 (BigQuery mode), document that partitioning choice (by patient_id, by date, by resource type, or combination) should be revisited once customer query patterns are known. Defer implementation of specific partitioning to customer needs rather than guessing.

**Multi-patient batch processing:** Deferred to v2+ per anti-features analysis, but actual customer scale needs are unknown. During Phase 5 (API ingestion), implement single-patient-at-a-time cleanly with extension points for future parallelization. Document scaling considerations (parallel workers, rate limiting, progress tracking) without implementing them.

**SQL dialect compatibility edge cases:** Research verified that standard SQL subset works for common operations, but edge cases (window functions, JSON operators, regex) differ between PostgreSQL and BigQuery. During Phase 3 (analytics queries), test every shipped query on both databases and document any dialect-specific variants needed. May need sql/clinical/postgres/ and sql/clinical/bigquery/ subdirectories if divergence is significant.

## Sources

### Primary (HIGH confidence)
- Sample data analysis: flat_data.json (904KB, 21 resource types, 1,187 records, verified structures and formats)
- Existing codebase: particle-health-starters pyproject.toml, ParticleHTTPClient implementation, structlog configuration
- PyPI version verification: psycopg 3.3.2, google-cloud-bigquery 3.40.0, pydantic 2.12.5, typer 0.21.1, rich 14.3.2, structlog 25.5.0, httpx 0.28.1, tenacity 9.1.4
- Official documentation: Google BigQuery DDL reference, PostgreSQL ON CONFLICT upsert, BigQuery schema management, Terraform google provider 7.18.0
- Docker Hub: postgres:17-alpine image verification

### Secondary (MEDIUM confidence)
- Healthcare pipeline patterns: Integrate.io healthcare ETL guide, Start Data Engineering idempotency patterns, Areca data engineering core concepts
- Competitor analysis: Google Healthcare Data Engine accelerators, Microsoft Healthcare Data Foundations, Databricks + Redox partnership
- Database best practices: Prisma PostgreSQL upsert guide, Hevo BigQuery MERGE patterns, Panoply PostgreSQL to BigQuery migration, Airbyte BigQuery pricing analysis
- Pitfall documentation: PostgreSQL NULL in unique constraints (mailing list + blog), Docker PostgreSQL volume permissions (GitHub issues), BigQuery DML limits (Google Cloud Blog), Terraform BigQuery schema drift (GitHub issues + blog posts)

### Tertiary (LOW confidence)
- Schema drift general patterns: Estuary schema drift management (not healthcare-specific, needs validation)
- SQL dialect differences: Data With Sarah SQL dialects guide, Daasity BigQuery syntax differences (general advice, test all queries)
- ETL project structure: Medium blog post on ETL best practices (single source, patterns verified against other references)

---
*Research completed: 2026-02-07*
*Ready for roadmap: yes*
