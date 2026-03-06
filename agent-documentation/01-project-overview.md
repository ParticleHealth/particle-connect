# Project Overview

Particle Connect is a monorepo of tools for integrating with the Particle Health Platform — a nationwide health data network that pulls clinical records from thousands of sources with a single API query.

## Sub-Projects

### 1. particle-api-quickstarts (Python SDK)
**Purpose**: Python toolkit for the Particle Health Query Flow API. Register patients, submit queries, retrieve clinical data in Flat JSON, CCDA, or FHIR format. Subscribe to Signal ADT event notifications via webhooks.

**Key paths**:
- `src/particle/core/` — Auth, HTTP client, config, exceptions
- `src/particle/patient/` — Patient registration models and service
- `src/particle/query/` — Query submission, polling, data retrieval
- `src/particle/document/` — Clinical document submission
- `src/particle/signal/` — Signal subscriptions, ADT events, webhook parsing
- `workflows/` — Runnable scripts (hello_particle.py, register_patient.py, signal_*.py, etc.)
- `quick-starts/curl/` — cURL scripts for direct API calls
- `quick-starts/python/` — httpx scripts (no SDK dependency)
- `notebooks/` — Jupyter notebook for exploring flat data
- `sample-data/` — Sample flat_data.json and CCDA ZIP
- `tests/` — Unit tests (pytest)

**Tech stack**: Python 3.11+, httpx, Pydantic, PyJWT, structlog, tenacity

### 2. particle-analytics-quickstarts (Data Pipeline)
**Purpose**: Load Particle flat data into DuckDB (local) or BigQuery (cloud) for SQL analytics.

**Key paths**:
- `src/observatory/cli.py` — CLI entry point (`particle-pipeline` command)
- `src/observatory/parser.py` — JSON parser for flat_data.json
- `src/observatory/normalizer.py` — Empty string to None normalization
- `src/observatory/schema.py` — Dynamic schema discovery from data
- `src/observatory/ddl.py` — DDL generation (DuckDB, PostgreSQL, BigQuery)
- `src/observatory/loader.py` — DuckDB loader (idempotent per-patient)
- `src/observatory/bq_loader.py` — BigQuery loader
- `src/observatory/quality.py` — Data quality report
- `queries/duckdb/` — 15 DuckDB analytics queries
- `queries/bigquery/` — 15 BigQuery analytics queries (same logic, different dialect)
- `terraform/` — BigQuery infrastructure provisioning
- `sample-data/flat_data.json` — Sample data (1,187 records, 16 resource types)

**Tech stack**: Python 3.11+, DuckDB, Typer, Rich, google-cloud-bigquery (optional), Terraform

### 3. management-ui (Admin Interface)
**Purpose**: Dockerized admin UI for the Particle Health Management API. Create projects, manage service accounts, rotate credentials.

**Key paths**:
- `backend/app/main.py` — FastAPI app with CORS, lifespan, routers
- `backend/app/services/particle_client.py` — Async HTTP client for Management API
- `backend/app/routers/auth.py` — Auth connect/status/switch endpoints
- `backend/app/routers/projects.py` — Project CRUD
- `backend/app/routers/service_accounts.py` — Service account management
- `backend/app/routers/credentials.py` — Credential create/list/delete
- `frontend/src/` — React 19 + TypeScript app (Vite)
- `docker-compose.yml` — Two-container setup (nginx:3000, uvicorn:8000)

**Tech stack**: FastAPI, httpx (async), React 19, TypeScript, Vite, Docker Compose, nginx

## How the Sub-Projects Relate

```
                    Particle Health Platform
                    ┌─────────────────────┐
                    │                     │
        Query Flow API            Management API
        (v2 endpoints)            (v1 endpoints)
              │                         │
              ├─────────┐               │
              │         │               │
    particle-api-   particle-      management-ui
    quickstarts     analytics-     (React + FastAPI)
    (Python SDK)    quickstarts
                    (DuckDB/BQ)
```

- **particle-api-quickstarts** calls the Query Flow API to register patients and retrieve clinical data
- **particle-analytics-quickstarts** takes the flat JSON output from the Query Flow API and loads it into a database for analysis
- **management-ui** calls the Management API (different base URL) to manage organizational resources like projects and service accounts

## CI/CD

A single GitHub Actions workflow (`.github/workflows/sync-to-public.yml`) syncs this private repo to the public `ParticleHealth/particle-connect` repo. It:
- Triggers on push to main
- Checks for sensitive files (.env, credentials, tfstate)
- Strips private directories (.planning, .claude, _private, .github) and files (CLAUDE.md)
- Force-pushes the sanitized content to the public repo via deploy key
