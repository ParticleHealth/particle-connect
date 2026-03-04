# Particle Starter

A Python toolkit for the [Particle Health](https://www.particlehealth.com/) API — the nationwide health data network that pulls clinical records from thousands of sources with a single query. Register patients, submit queries, and retrieve data in Flat JSON, CCDA, or FHIR format.

## Prerequisites

- **Python 3.11+**
- **Particle Health credentials** — you need a `client_id`, `client_secret`, and `scope_id` from your [Particle Health dashboard](https://www.particlehealth.com/)

## Getting Started

1. **Clone and set up a virtual environment**

   ```bash
   git clone <repo-url> && cd particle-health-starters
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -e ".[dev]"
   ```

3. **Configure credentials**

   ```bash
   cp .env.example .env
   # Edit .env with your Particle Health credentials
   ```

   Your `.env` should look like:

   ```
   PARTICLE_CLIENT_ID=your-client-id
   PARTICLE_CLIENT_SECRET=your-client-secret
   PARTICLE_SCOPE_ID=projects/your-scope-id
   ```

4. **Validate setup**

   ```bash
   python workflows/check_setup.py
   ```

   Expected output:

   ```
   Checking Particle Health API setup...

   1. Checking environment variables...
      OK: All required variables found
   2. Testing authentication...
      OK: Authentication successful

   --- Setup OK ---
   Environment: sandbox
   ```

5. **Run the demo**

   ```bash
   python workflows/hello_particle.py
   ```

   This registers a demo patient, submits a query, polls for completion (2-5 minutes), and prints a summary of the clinical data returned. Expected output:

   ```
   === Hello Particle ===

   1. Registering demo patient...
      Patient ID: ...
   2. Submitting clinical data query...
   3. Waiting for query to complete (this may take 2-5 minutes)...
      Status: COMPLETE
   4. Retrieving flat data...

   === Data Summary ===
   Resource types returned:
     allergies: 4 records
     encounters: 12 records
     medications: 8 records
     ...
   ```

## Explore the Data (No Credentials Needed)

If you want to see what Particle flat data looks like before setting up credentials, open the notebook:

```
notebooks/explore_flat_data.ipynb
```

It loads `sample-data/flat_data.json` (included in this repo) and walks through resource types, medications, problems, vital signs, and common transformations. No API calls, no credentials — just a JSON file and Python.

## Step-by-Step Workflow

For users who want to run each step individually instead of `hello_particle.py`:

**Register a patient**

```bash
python workflows/register_patient.py
```

Returns a `particle_patient_id` you'll need for the next steps. Example output:

```
Patient registered successfully!
  Particle Patient ID: 12345678-1234-1234-1234-123456789012
  Your Patient ID: test-elvira-valadez
```

You can also pass a JSON file or inline JSON:

```bash
python workflows/register_patient.py patient.json
python workflows/register_patient.py '{"given_name": "John", ...}'
```

**Submit a query**

```bash
python workflows/submit_query.py <particle_patient_id>
```

Submits the query and polls until completion (up to 5 minutes). Example output:

```
Query completed!
  Status: COMPLETE
  Files available: ['flat', 'ccda']
```

**Retrieve data**

```bash
python workflows/retrieve_data.py <particle_patient_id> flat
python workflows/retrieve_data.py <particle_patient_id> ccda
```

Flat and CCDA are the two formats available in the sandbox. FHIR is production-only (see [Data Formats](#data-formats)).

## Submit a Document

Document submission is a separate flow from query/retrieval. It uploads a clinical document for a patient:

```bash
# Submit a CCDA (XML) document
python workflows/submit_document.py <patient_id>

# Submit a PDF document
python workflows/submit_document.py <patient_id> pdf
```

The `<patient_id>` here is your external patient ID (assigned during registration), not the Particle patient UUID.

## Quick-Start Scripts (No SDK)

These scripts call the Particle API directly with `curl` or `httpx` — no SDK required. Useful for debugging, testing endpoints, or as copy-paste references for your own integration.

### cURL

```bash
source quick-starts/curl/auth.sh           # sets $TOKEN
bash quick-starts/curl/register_patient.sh
bash quick-starts/curl/submit_query.sh <particle_patient_id>
bash quick-starts/curl/retrieve_data.sh <particle_patient_id> flat
```

### Python (httpx)

```bash
python quick-starts/python/auth.py
python quick-starts/python/register_patient.py
python quick-starts/python/submit_query.py <particle_patient_id>
python quick-starts/python/retrieve_data.py <particle_patient_id> flat
```

| Step | cURL | Python |
|------|------|--------|
| Auth | `quick-starts/curl/auth.sh` | `quick-starts/python/auth.py` |
| Register | `quick-starts/curl/register_patient.sh` | `quick-starts/python/register_patient.py` |
| Query | `quick-starts/curl/submit_query.sh` | `quick-starts/python/submit_query.py` |
| Retrieve | `quick-starts/curl/retrieve_data.sh` | `quick-starts/python/retrieve_data.py` |

## Data Formats

| Format | Sandbox | Production | Description |
|--------|---------|------------|-------------|
| **Flat** | Yes | Yes | Particle's denormalized JSON — each resource type is a flat list of records with string values. Easiest to parse and load into a database. |
| **CCDA** | Yes | Yes | C-CDA XML documents in a ZIP file. Standard clinical document format used across EHRs. |
| **FHIR** | No | Yes | FHIR R4 Bundle (JSON). Richest clinical semantics, but not available in sandbox. |

**Recommendation:** Start with **flat** for data analysis and pipeline work. Use **CCDA** when you need the original clinical documents. Use **FHIR** in production when you need standard interoperability.

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

- **Sandbox:** `https://sandbox.particlehealth.com`
- **Production:** `https://api.particlehealth.com`

### Patient Fields

| Field | Required | Format |
|-------|----------|--------|
| `given_name` | Yes | String |
| `family_name` | Yes | String |
| `date_of_birth` | Yes | YYYY-MM-DD |
| `gender` | Yes | MALE or FEMALE |
| `postal_code` | Yes | 5 or 9 digit ZIP |
| `address_city` | Yes | String |
| `address_state` | Yes | **Full state name** (e.g., "Massachusetts", not "MA") |
| `address_lines` | No | Array of strings |
| `ssn` | No | XXX-XX-XXXX |
| `telephone` | No | XXX-XXX-XXXX |
| `patient_id` | Yes | Your external ID |
| `email` | No | String |

## Troubleshooting

**`address_state` must be the full state name.** The API rejects abbreviations — use `"Massachusetts"`, not `"MA"`.

**FHIR endpoint returns 404 in sandbox.** The `/fhir` endpoint is production-only. Use `flat` or `ccda` in sandbox.

**Query takes 2-5 minutes.** This is normal — Particle queries a nationwide network. The SDK polls with exponential backoff automatically.

**Flat data returns empty in sandbox.** Sandbox only returns data for seeded test patients (e.g., Elvira Valadez-Nucleus). Arbitrary demographics will query successfully but return `{}`.

For more issues (overlay errors, 404 after query submission, timeout tuning), see [docs/troubleshooting.md](docs/troubleshooting.md).

## Running Tests

```bash
pytest -v
```

## Configuration

The `.env` file (or environment variables) supports these settings:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PARTICLE_CLIENT_ID` | Yes | — | Your Particle client ID |
| `PARTICLE_CLIENT_SECRET` | Yes | — | Your Particle client secret |
| `PARTICLE_SCOPE_ID` | Yes | — | Your Particle scope ID |
| `PARTICLE_BASE_URL` | No | `https://sandbox.particlehealth.com` | API base URL |
| `PARTICLE_TIMEOUT` | No | `30` | Request timeout in seconds |

To switch to production:

```bash
export PARTICLE_BASE_URL="https://api.particlehealth.com"
```

## What's in This Repo

```
particle-health-starters/
  workflows/                  # SDK-based workflow scripts
    hello_particle.py           # End-to-end demo (start here)
    check_setup.py              # Validate credentials
    register_patient.py         # Register a patient
    submit_query.py             # Submit + poll a query
    retrieve_data.py            # Retrieve flat/ccda/fhir data
    submit_document.py          # Submit a clinical document
  quick-starts/               # No-SDK scripts (direct API calls)
    curl/                       # cURL scripts
    python/                     # httpx scripts
  notebooks/
    explore_flat_data.ipynb     # Explore flat data (no credentials needed)
  sample-data/
    flat_data.json              # Sample flat JSON response
    ccda_data.zip               # Sample CCDA ZIP
    ccda_data/                  # Extracted CCDA XML files
  src/particle/               # SDK source code
    core/                       # Auth, HTTP client, settings, errors
    patient/                    # Patient registration
    query/                      # Query submission + retrieval
    document/                   # Document submission
  tests/                      # Test suite
  docs/
    troubleshooting.md          # Full troubleshooting guide
```
