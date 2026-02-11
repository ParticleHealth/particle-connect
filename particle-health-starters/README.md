# Particle Starter

A Python toolkit for connecting to the [Particle Health](https://www.particlehealth.com/) API — the nationwide health data network that pulls clinical records from thousands of sources with a single query. Register patients, submit queries, and retrieve data in FHIR, Flat JSON, or CCDA format. Comes with workflow scripts that use the SDK and quick-start scripts that hit the API directly, so you can go from zero to patient data in minutes.

## Setup

### 1. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -e ".[dev]"
```

### 3. Set environment variables

```bash
cp .env.example .env
# Edit .env with your Particle Health credentials
```

Or export directly:

```bash
export PARTICLE_CLIENT_ID="your-client-id"
export PARTICLE_CLIENT_SECRET="your-client-secret"
export PARTICLE_SCOPE_ID="projects/your-scope-id"
```

### 4. Validate setup

```bash
python workflows/check_setup.py
```

## Quick Start

The fastest way to see data: run the end-to-end demo (register, query, poll, retrieve, summarize):

```bash
python workflows/hello_particle.py
```

Or run each step individually:

### 1. Register a patient

```bash
python workflows/register_patient.py
```

This returns a `particle_patient_id` needed for subsequent operations.

### 2. Submit a query

```bash
python workflows/submit_query.py <particle_patient_id>
```

### 3. Retrieve data

```bash
# Flat JSON format (default)
python workflows/retrieve_data.py <particle_patient_id> flat

# CCDA format (ZIP)
python workflows/retrieve_data.py <particle_patient_id> ccda

# FHIR format (production only — not available in sandbox)
# python workflows/retrieve_data.py <particle_patient_id> fhir
```

## Workflow Scripts

| Script | Description |
|--------|-------------|
| `workflows/hello_particle.py` | End-to-end demo: register, query, retrieve, summarize |
| `workflows/check_setup.py` | Validate environment variables and credentials |
| `workflows/register_patient.py` | Register a new patient |
| `workflows/submit_query.py` | Submit a clinical data query |
| `workflows/retrieve_data.py` | Retrieve data in FHIR, Flat, or CCDA format |
| `workflows/submit_document.py` | Submit a clinical document |

## Quick Starts

Standalone scripts that call the Particle API directly — no SDK required. Good for testing endpoints or as copy-paste references.

### cURL

```bash
# 1. Get auth token
source quick-starts/curl/auth.sh

# 2. Register a patient
bash quick-starts/curl/register_patient.sh

# 3. Submit a query
bash quick-starts/curl/submit_query.sh <particle_patient_id>

# 4. Retrieve data (flat, fhir, or ccda)
bash quick-starts/curl/retrieve_data.sh <particle_patient_id> flat
```

### Python (httpx)

```bash
# 1. Get auth token
python quick-starts/python/auth.py

# 2. Register a patient
python quick-starts/python/register_patient.py

# 3. Submit a query (includes polling)
python quick-starts/python/submit_query.py <particle_patient_id>

# 4. Retrieve data (flat, fhir, or ccda)
python quick-starts/python/retrieve_data.py <particle_patient_id> flat
```

| Script | cURL | Python |
|--------|------|--------|
| Auth | `quick-starts/curl/auth.sh` | `quick-starts/python/auth.py` |
| Register patient | `quick-starts/curl/register_patient.sh` | `quick-starts/python/register_patient.py` |
| Submit query | `quick-starts/curl/submit_query.sh` | `quick-starts/python/submit_query.py` |
| Retrieve data | `quick-starts/curl/retrieve_data.sh` | `quick-starts/python/retrieve_data.py` |

## API Reference

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth` | GET | Get JWT token (custom headers) |
| `/api/v2/patients` | POST | Register a patient |
| `/api/v2/patients/{id}/query` | POST | Submit a query |
| `/api/v2/patients/{id}/query` | GET | Check query status |
| `/api/v2/patients/{id}/flat` | GET | Get flat JSON data |
| `/api/v2/patients/{id}/fhir` | GET | Get FHIR Bundle (production only) |
| `/api/v2/patients/{id}/ccda` | GET | Get CCDA ZIP |
| `/api/v1/documents` | POST | Submit a clinical document (multipart) |

### Base URLs

- Sandbox: `https://sandbox.particlehealth.com`
- Production: `https://api.particlehealth.com`

> **Note:** The sandbox environment does not support the FHIR endpoint (`/fhir`). Use flat or CCDA format for sandbox testing.

### Patient Fields

| Field | Required | Format |
|-------|----------|--------|
| `given_name` | Yes | String |
| `family_name` | Yes | String |
| `date_of_birth` | Yes | YYYY-MM-DD |
| `gender` | Yes | MALE or FEMALE |
| `postal_code` | Yes | 5 or 9 digit ZIP |
| `address_city` | Yes | String |
| `address_state` | Yes | Full state name |
| `address_lines` | No | Array of strings |
| `ssn` | No | XXX-XX-XXXX |
| `telephone` | No | XXX-XXX-XXXX |
| `patient_id` | No | Your external ID |
| `email` | No | String |

## Notebooks

| Notebook | Description |
|----------|-------------|
| `notebooks/explore_flat_data.ipynb` | Explore flat JSON data with no credentials required |

## Troubleshooting

See [docs/troubleshooting.md](docs/troubleshooting.md) for common sandbox issues including FHIR 404s, address_state formatting, overlay errors, and query timing.

## Running Tests

```bash
pytest -v
```

## Configuration

Set `PARTICLE_BASE_URL` for production:

```bash
export PARTICLE_BASE_URL="https://api.particlehealth.com"
```
