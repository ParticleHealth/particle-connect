# Roadmap: Particle Flat Data Pipeline

## Overview

This roadmap delivers a customer-facing data pipeline accelerator that takes Particle Health's GET Flat response data from raw JSON to queryable structured tables with pre-built analytics queries. The journey starts with schema foundation and data normalization (the hardest part due to healthcare data quality issues), delivers a working local pipeline with Docker PostgreSQL, adds a comprehensive analytics query library, extends to cloud BigQuery with Terraform, and finishes with live Particle API ingestion. Each phase delivers a complete, verifiable capability that customers can use independently.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Schema Foundation** - DDL generation, data normalization, and project scaffolding for all 21 Particle flat resource types
- [x] **Phase 2: Local Pipeline** - End-to-end file-to-PostgreSQL pipeline with Docker, CLI, and developer experience
- [x] **Phase 3: Analytics Queries** - Pre-built clinical, operational, and cross-cutting SQL queries for both database targets
- [ ] **Phase 4: Cloud Mode** - BigQuery target with Terraform provisioning and production-ready cloud loading
- [ ] **Phase 5: API Ingestion** - Live Particle Health API integration with authentication, retries, and error handling

## Phase Details

### Phase 1: Schema Foundation
**Goal**: Customers have a validated, dialect-aware schema for all 21 Particle flat resource types with data normalization that handles real-world healthcare data quality issues
**Depends on**: Nothing (first phase)
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05, PIPE-06, PIPE-07, DX-05, DX-06
**Success Criteria** (what must be TRUE):
  1. Running DDL generation against the included sample data produces CREATE TABLE statements for all 21 resource types in both PostgreSQL and BigQuery dialects
  2. Empty strings from Particle data are normalized to NULLs for non-text columns (timestamps, numerics, booleans) without corrupting text fields
  3. All five timestamp formats found in Particle flat data parse successfully into a consistent format
  4. Schema-resilient parsing handles missing fields, extra fields, and empty resource arrays without errors -- verified against sample data
  5. Project includes .env.example with all configuration variables documented and sample flat_data.json for immediate testing
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md -- Project scaffolding, Python package, configuration, and sample data
- [x] 01-02-PLAN.md -- JSON parser, schema inspector, and data normalization layer
- [x] 01-03-PLAN.md -- DDL generator with CLI and dialect-aware SQL output for all 21 resource types

### Phase 2: Local Pipeline
**Goal**: Customers can load Particle flat data into a local PostgreSQL database from a clean checkout with a single command, getting immediate feedback on data quality
**Depends on**: Phase 1
**Requirements**: LOCAL-01, LOCAL-02, LOCAL-03, LOCAL-04, LOCAL-05, INGEST-01, INGEST-05, CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, DX-01, DX-02, DX-03, PIPE-06
**Success Criteria** (what must be TRUE):
  1. `docker compose up` starts PostgreSQL with all 21 tables created automatically, and data persists across container restarts
  2. `particle-pipeline load --source file --target postgres` loads sample data into PostgreSQL with a data quality report showing record counts per table, null percentages, and date ranges
  3. Re-running the load command produces identical results (idempotent via delete+insert per patient_id per resource type) with no duplicate records
  4. CLI provides `--help` with usage examples, reads config from .env, and displays actionable error messages when things go wrong (not raw stack traces)
  5. README documents local setup from clone to first query in under 5 minutes
**Plans**: 4 plans

Plans:
- [x] 02-01-PLAN.md -- Docker Compose PostgreSQL setup with auto-DDL, volume persistence, and pipeline dependencies
- [x] 02-02-PLAN.md -- PostgreSQL loader module with idempotent delete+insert per patient per resource type
- [x] 02-03-PLAN.md -- Typer CLI entry point with .env configuration, error handling, and end-to-end verification
- [x] 02-04-PLAN.md -- Data quality report with Rich formatting and local setup README

### Phase 3: Analytics Queries
**Goal**: Customers have a library of ready-to-run SQL queries that answer common clinical and operational questions about their Particle data
**Depends on**: Phase 1 (uses DDL schema; can proceed in parallel with Phase 2)
**Requirements**: CLIN-01, CLIN-02, CLIN-03, CLIN-04, CLIN-05, CLIN-06, CLIN-07, OPS-01, OPS-02, OPS-03, OPS-04, OPS-05, CROSS-01, CROSS-02, CROSS-03, DX-07
**Success Criteria** (what must be TRUE):
  1. Clinical queries return meaningful results against sample data: patient summaries with demographics/conditions/medications, active problem lists, medication timelines, lab trends with abnormal flags, vital sign trends, encounter history, and care team information
  2. Operational queries return meaningful results: data completeness scorecard, source coverage breakdown, record freshness per resource type, data provenance tracing, and AI output summaries with citation counts
  3. Cross-cutting queries join across resource types: labs-by-encounter, medications-by-problem, and procedures-by-encounter all return results from sample data
  4. Every query runs successfully on both PostgreSQL and BigQuery with documented dialect variants where standard SQL is insufficient
**Plans**: 3 plans

Plans:
- [x] 03-01-PLAN.md -- Clinical analytics queries (patient summary, problems, medications, labs, vitals, encounters, care team) for PostgreSQL and BigQuery
- [x] 03-02-PLAN.md -- Operational analytics queries (completeness, sources, freshness, provenance, AI outputs) for PostgreSQL and BigQuery
- [x] 03-03-PLAN.md -- Cross-cutting queries (labs-by-encounter, medications-by-problem, procedures-by-encounter) and query catalog README

### Phase 4: Cloud Mode
**Goal**: Customers can provision BigQuery infrastructure with Terraform and load Particle flat data into a production-ready cloud warehouse
**Depends on**: Phase 1, Phase 2 (reuses loader interface and idempotency pattern)
**Requirements**: CLOUD-01, CLOUD-02, CLOUD-03, CLOUD-04, CLOUD-05, CLOUD-06, DX-04
**Success Criteria** (what must be TRUE):
  1. `terraform apply` creates a BigQuery dataset, all 21 resource type tables with correct column types, and a service account with minimum required permissions -- all configurable via variables (project ID, dataset name, region)
  2. `particle-pipeline load --source file --target bigquery` loads sample data into BigQuery using batch load jobs (not streaming inserts) with the same idempotent delete+insert pattern as PostgreSQL
  3. All analytics queries from Phase 3 run successfully against the BigQuery tables
  4. README documents cloud setup including Terraform variables, authentication via Application Default Credentials, and first query walkthrough
**Plans**: 3 plans

Plans:
- [ ] 04-01-PLAN.md -- Terraform module for BigQuery dataset, 21 tables (for_each), service account, and IAM bindings
- [ ] 04-02-PLAN.md -- BigQuery loader module with batch load jobs, idempotent delete+insert, and CLI wiring
- [ ] 04-03-PLAN.md -- Cloud Mode README section with Terraform setup, ADC auth, and query walkthrough

### Phase 5: API Ingestion
**Goal**: Customers can pull data directly from the Particle Health API instead of loading from files, with production-grade error handling
**Depends on**: Phase 2 (reuses pipeline and CLI infrastructure)
**Requirements**: INGEST-02, INGEST-03, INGEST-04
**Success Criteria** (what must be TRUE):
  1. `particle-pipeline load --source api --target postgres` authenticates with Particle Health and loads flat data from the GET Flat endpoint into the target database
  2. API calls retry automatically with exponential backoff on 429 (rate limit) and 5xx (server error) responses, with configurable timeout
  3. API ingestion feeds the same downstream pipeline as file ingestion -- identical parsing, normalization, and loading behavior
**Plans**: TBD

Plans:
- [ ] 05-01: Particle API client with authentication, retries, and timeout
- [ ] 05-02: API ingestion integration with existing pipeline and CLI

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5
Note: Phase 3 can proceed in parallel with Phase 2 after Phase 1 completes.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Schema Foundation | 3/3 | Complete | 2026-02-08 |
| 2. Local Pipeline | 4/4 | Complete | 2026-02-08 |
| 3. Analytics Queries | 3/3 | Complete | 2026-02-08 |
| 4. Cloud Mode | 0/3 | Not started | - |
| 5. API Ingestion | 0/2 | Not started | - |
