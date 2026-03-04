# AGENTS.md — Particle Connect

Universal instructions for AI agents working in this repository.

## Project Summary

This is a monorepo with three sub-projects for integrating with the Particle Health Platform (nationwide health data network). All projects are Python or TypeScript, intended for local development and learning — not production use.

## Repository Structure

```
particle-connect-private/
  particle-api-quickstarts/     # Python SDK + workflows for Query Flow API
  particle-analytics-quickstarts/  # DuckDB/BigQuery pipeline for flat data
  management-ui/                # React + FastAPI admin UI for Management API
  agent-documentation/          # AI agent-optimized docs (this folder)
```

## Build and Test Commands

### particle-api-quickstarts (Python SDK)
```bash
cd particle-api-quickstarts
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -v                    # Run tests
python workflows/check_setup.py  # Validate credentials
```

### particle-analytics-quickstarts (Pipeline)
```bash
cd particle-analytics-quickstarts
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
particle-pipeline            # Load sample data into DuckDB
```

### management-ui (Docker)
```bash
cd management-ui
docker compose up --build    # Starts frontend (:3000) + backend (:8000)
```

### management-ui (without Docker)
```bash
# Backend
cd management-ui/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd management-ui/frontend
npm install && npm run dev   # Runs on :5173
```

## Code Style

- Python: Type hints, Pydantic models, httpx for HTTP, structlog for logging
- TypeScript: React 19, Vite, CSS modules
- All strings: Double quotes in Python, match existing style in TypeScript
- Imports: Standard library first, then third-party, then local
- Error handling: Custom exception hierarchy (ParticleAuthError, ParticleAPIError, etc.)

## Key Conventions

- **State names**: Particle API requires two-letter state abbreviations ("MA", not "Massachusetts") for patient registration
- **Auth**: Custom flow — GET /auth with custom headers, returns JWT as plain text (NOT OAuth2)
- **Environments**: Sandbox (sandbox.particlehealth.com) and Production (api.particlehealth.com)
- **FHIR**: Not available in sandbox — only flat and CCDA formats work in sandbox
- **Query timing**: Queries take 2-5 minutes (nationwide network). Use exponential backoff polling.
- **Idempotency**: Patient registration is idempotent if same patient_id + same demographics. Different demographics = overlay error.

## Do Not

- Do not commit .env files, secrets, or credentials
- Do not edit files outside the agent-documentation/ folder when working on documentation tasks
- Do not hardcode patient IDs or API credentials in source code
- Do not use tight polling loops for query status — use exponential backoff
