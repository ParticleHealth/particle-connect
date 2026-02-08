# Particle Flat Data Pipeline

## What This Is

A customer-facing data pipeline accelerator that ingests Particle Health's GET Flat response data, stores it in structured database tables, and provides pre-built SQL queries for clinical and operational analytics. Ships with two deployment modes: local (Docker + PostgreSQL) for development/testing, and cloud (Terraform + BigQuery) for production.

## Core Value

Customers can go from raw Particle flat data to queryable, structured tables with useful analytics queries — working from a clean checkout with zero code changes beyond configuration.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Python-based pipeline that parses Particle GET Flat JSON response into per-resource-type records
- [ ] Dual ingestion modes: call Particle API directly (live) or load from file/stdin
- [ ] DDL statements for all 21 flat resource types (aICitations, aIOutputs, allergies, coverages, documentReferences, encounters, familyMemberHistories, immunizations, labs, locations, medications, organizations, patients, practitioners, problems, procedures, recordSources, socialHistories, sources, transitions, vitalSigns)
- [ ] Schema resilience — handles missing/extra fields, empty resource arrays, varying data shapes across customers
- [ ] Idempotent loads — safe to re-run without duplicating data
- [ ] Local mode: Docker Compose spins up PostgreSQL, creates tables, loads data
- [ ] Cloud mode: Terraform provisions BigQuery dataset, tables, and service account
- [ ] Pre-built clinical SQL queries (patient summaries, encounter timelines, lab trends, medication lists)
- [ ] Pre-built operational SQL queries (data completeness, source breakdowns, patient counts, resource coverage)
- [ ] SQL queries work on both PostgreSQL and BigQuery with minimal dialect differences
- [ ] Configuration via environment variables / .env — no code changes needed per customer
- [ ] Works from clean checkout: clone, configure, run
- [ ] Sample data included for local testing (from existing flat_data.json)
- [ ] Clear README with setup steps for both local and cloud modes

### Out of Scope

- FHIR data handling — this is exclusively for Particle's flat format
- Real-time streaming / CDC — this is batch ingestion
- Data transformation / dbt models — raw tables only, customers build their own transforms
- Multi-cloud — BigQuery only for cloud mode
- Orchestration tooling (Airflow, Dagster) — customers handle scheduling
- UI / dashboards — SQL queries only

## Context

- Lives as a new directory within the particle-connect repository
- Existing `particle-health-starters/sample-data/flat_data.json` provides sample data (21 resource types, ~880KB)
- Flat data structure: top-level dict with resource type keys, each containing an array of flat records with snake_case columns
- Some resource types will be empty for certain customers (allergies, coverages, familyMemberHistories, immunizations, socialHistories were empty in sample)
- Customers range from data/analytics engineers building warehouses to app developers needing queryable data
- Must be reliable across diverse customer environments (different OS, Python versions, Docker versions)

## Constraints

- **Language**: Python — consistent with existing particle-health-starters toolkit
- **Local DB**: PostgreSQL in Docker — closest SQL dialect to BigQuery, widely known
- **Cloud DB**: BigQuery — Terraform provisioned (minimal: dataset + tables + service account)
- **Config**: Environment variables / .env files — no hardcoded credentials
- **Security**: No real credentials, tokens, or patient data in repo. Sample data only.
- **Reliability**: Must handle empty resource types, missing fields, and varying data shapes without failure

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python for pipeline | Matches existing particle-health-starters, customers already set up | — Pending |
| PostgreSQL for local | Closest BigQuery SQL dialect, most universal | — Pending |
| All 21 resource types | Full coverage, no customer left wondering why their data type is missing | — Pending |
| Dual ingestion (API + file) | Flexibility: test with files, run live in production | — Pending |
| Minimal Terraform scope | Dataset + tables + SA only, customer handles scheduling | — Pending |
| Both clinical + operational queries | Covers analytics engineers and ops teams | — Pending |

---
*Last updated: 2026-02-07 after initialization*
