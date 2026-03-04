# SDK Reference — Python SDK

The Python SDK in `particle-api-quickstarts/` provides a typed, validated interface to the Particle Health Query Flow API.

## Architecture

```
src/particle/
  __init__.py
  core/
    auth.py         # TokenManager + ParticleAuth (httpx.Auth subclass)
    config.py       # ParticleSettings (Pydantic BaseSettings, loads .env)
    http.py         # ParticleHTTPClient (retry, error mapping)
    exceptions.py   # Exception hierarchy
    logging.py      # structlog configuration
  patient/
    models.py       # PatientRegistration, PatientResponse, Gender enum
    service.py      # PatientService.register()
  query/
    models.py       # PurposeOfUse, QueryStatus, QueryRequest, QueryResponse
    service.py      # QueryService (submit, poll, retrieve flat/ccda/fhir)
  document/
    models.py       # DocumentSubmission, DocumentResponse, MimeType enum
    service.py      # DocumentService.submit()
```

## Core Module

### ParticleSettings (`core/config.py`)
Loads configuration from environment variables or `.env` file.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| PARTICLE_CLIENT_ID | Yes | — | Client ID |
| PARTICLE_CLIENT_SECRET | Yes | — | Client secret |
| PARTICLE_SCOPE_ID | Yes | — | Scope ID (format: `projects/<id>`) |
| PARTICLE_BASE_URL | No | `https://sandbox.particlehealth.com` | API base URL |
| PARTICLE_TIMEOUT | No | 30 | Request timeout (seconds) |

### ParticleAuth (`core/auth.py`)
httpx.Auth subclass that handles JWT lifecycle:
- Proactive refresh 10 minutes before expiry (configurable via `token_refresh_buffer_seconds`)
- Automatic retry on 401 (re-authenticates and replays request)
- Decodes JWT expiry from `exp` claim without signature verification

### ParticleHTTPClient (`core/http.py`)
Wraps httpx.Client with:
- Automatic authentication via ParticleAuth
- Retry with exponential backoff + jitter (3 attempts, 1-60s wait)
- Retries on: ConnectError, ConnectTimeout, ReadTimeout, WriteTimeout, PoolTimeout
- HTTP status → exception mapping (401→AuthError, 404→NotFoundError, 422→ValidationError, 429→RateLimitError)
- Context manager support (`with ParticleHTTPClient(settings) as client:`)

### PHI/PII Redaction (`core/logging.py`)
structlog processor that redacts sensitive health information from all logs for HIPAA compliance. Redacts: names, SSN, DOB, addresses, phone numbers, email addresses.

### Exception Hierarchy (`core/exceptions.py`)
```
ParticleError (base)
├── ParticleAuthError (401, 403)
├── ParticleAPIError (general, includes status_code + response_body)
│   ├── ParticleNotFoundError (404)
│   ├── ParticleValidationError (422, includes errors list)
│   └── ParticleRateLimitError (429, includes retry_after)
├── ParticleQueryTimeoutError (polling timeout)
└── ParticleQueryFailedError (query status = FAILED)
```

## Patient Module

### PatientService (`patient/service.py`)
Single method: `register(patient: PatientRegistration) -> PatientResponse`

### PatientRegistration model
Pydantic model with validators:
- SSN: XXX-XX-XXXX format
- Telephone: Normalizes any US format to XXX-XXX-XXXX (strips country code, non-digits)
- Postal code: Regex `^\d{5}(-\d{4})?$`
- Strips whitespace on all string fields

## Query Module

### QueryService (`query/service.py`)
- `submit_query(patient_id, purpose_of_use=TREATMENT) -> QuerySubmitResponse`
- `get_query_status(patient_id) -> QueryResponse`
- `wait_for_query_complete(patient_id, timeout=300, poll_interval=5, max_interval=30) -> QueryResponse`
- `get_flat(patient_id) -> dict`
- `get_ccda(patient_id) -> bytes`
- `get_fhir(patient_id) -> dict`

### QueryStatus enum
`PENDING → PROCESSING → COMPLETE | PARTIAL | FAILED`

### PurposeOfUse enum
`TREATMENT | PAYMENT | OPERATIONS` (required for HIPAA compliance)

## Document Module

### DocumentService (`document/service.py`)
Single method: `submit(document: DocumentSubmission, file_content: bytes) -> DocumentResponse`

Sends multipart form with:
- `metadata` field: JSON string of document metadata
- `file` field: Binary file content with filename and MIME type

## Usage Pattern

```python
from particle.core import ParticleSettings, ParticleHTTPClient
from particle.patient import PatientService, PatientRegistration, Gender
from particle.query import QueryService

settings = ParticleSettings()  # loads from .env

with ParticleHTTPClient(settings) as client:
    # Register patient
    patient_svc = PatientService(client)
    response = patient_svc.register(PatientRegistration(
        given_name="Kam", family_name="Quark",
        date_of_birth="1954-12-01", gender=Gender.MALE,
        postal_code="11111", address_city="Brooklyn",
        address_state="New York",
    ))

    # Query clinical data
    query_svc = QueryService(client)
    query_svc.submit_query(response.particle_patient_id)
    result = query_svc.wait_for_query_complete(response.particle_patient_id)

    # Retrieve data
    flat_data = query_svc.get_flat(response.particle_patient_id)
```

## Workflow Scripts

| Script | Purpose |
|--------|---------|
| `workflows/hello_particle.py` | End-to-end demo: register → query → retrieve |
| `workflows/check_setup.py` | Validate credentials and connectivity |
| `workflows/register_patient.py` | Register a single patient |
| `workflows/submit_query.py` | Submit query + poll for completion |
| `workflows/retrieve_data.py` | Retrieve flat/ccda data |
| `workflows/submit_document.py` | Submit a clinical document |

## Quick-Start Scripts (No SDK)

Direct API calls without the SDK, useful for debugging:

| Step | cURL | Python (httpx) |
|------|------|----------------|
| Auth | `quick-starts/curl/auth.sh` | `quick-starts/python/auth.py` |
| Register | `quick-starts/curl/register_patient.sh` | `quick-starts/python/register_patient.py` |
| Query | `quick-starts/curl/submit_query.sh` | `quick-starts/python/submit_query.py` |
| Retrieve | `quick-starts/curl/retrieve_data.sh` | `quick-starts/python/retrieve_data.py` |
