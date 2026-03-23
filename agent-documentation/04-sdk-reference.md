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
    logging.py      # structlog configuration + PHI redaction
  patient/
    models.py       # PatientRegistration, PatientResponse, Gender enum
    service.py      # PatientService.register()
  query/
    models.py       # PurposeOfUse, QueryStatus, QueryRequest, QueryResponse
    service.py      # QueryService (submit, poll, retrieve flat/ccda/fhir)
  document/
    models.py       # DocumentSubmission, DocumentResponse, DocumentMetadata, MimeType enum
    service.py      # DocumentService.submit(), get(), delete(), list_by_patient()
  signal/
    models.py       # SubscriptionType, WorkflowType, ADTEventType, webhook models
    service.py      # SignalService (subscribe, trigger, referrals, transitions)
```

## Core Module

### ParticleSettings (`core/config.py:9`)
Loads configuration from environment variables or `.env` file.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| PARTICLE_CLIENT_ID | Yes | — | Client ID |
| PARTICLE_CLIENT_SECRET | Yes | — | Client secret |
| PARTICLE_SCOPE_ID | Yes | — | Scope ID (format: `projects/<id>`) |
| PARTICLE_BASE_URL | No | `https://sandbox.particlehealth.com` | API base URL |
| PARTICLE_TIMEOUT | No | 30 | Request timeout (seconds) |

### ParticleAuth (`core/auth.py:85`)
httpx.Auth subclass that handles JWT lifecycle:
- Proactive refresh 10 minutes before expiry (configurable via `token_refresh_buffer_seconds`)
- Automatic retry on 401 (re-authenticates and replays request)
- Decodes JWT expiry from `exp` claim without signature verification

### ParticleHTTPClient (`core/http.py:36`)
Wraps httpx.Client with:
- Automatic authentication via ParticleAuth
- Retry with exponential backoff + jitter (3 attempts, 1-60s wait)
- Retries on: ConnectError, ConnectTimeout, ReadTimeout, WriteTimeout, PoolTimeout
- HTTP status → exception mapping (401→AuthError, 404→NotFoundError, 422→ValidationError, 429→RateLimitError)
- Context manager support (`with ParticleHTTPClient(settings) as client:`)

### PHI/PII Redaction (`core/logging.py:88`)
structlog processor that redacts sensitive health information from all logs for HIPAA compliance. Redacts: names, SSN, DOB, addresses, phone numbers, email addresses.

### Exception Hierarchy (`core/exceptions.py:6-87`)
```
ParticleError (base)                                    :6
├── ParticleAuthError (401, 403)                        :15
├── ParticleAPIError (general, status_code + response_body) :22
│   ├── ParticleNotFoundError (404)                     :57
│   ├── ParticleValidationError (422, errors list)      :36
│   └── ParticleRateLimitError (429, retry_after)       :44
├── ParticleQueryTimeoutError (polling timeout)         :67
└── ParticleQueryFailedError (query status = FAILED)    :77
```

## Patient Module

### PatientService (`patient/service.py:33`)
Single method: `register(patient: PatientRegistration) -> PatientResponse` (`:44`)

### PatientRegistration model
Pydantic model with validators:
- SSN: XXX-XX-XXXX format
- Telephone: Normalizes any US format to XXX-XXX-XXXX (strips country code, non-digits)
- Postal code: Regex `^\d{5}(-\d{4})?$`
- Strips whitespace on all string fields

## Query Module

### QueryService (`query/service.py:37`)
- `submit_query(patient_id, purpose_of_use=TREATMENT) -> QuerySubmitResponse` (`:48`)
- `get_query_status(patient_id) -> QueryResponse` (`:70`)
- `wait_for_query_complete(patient_id, timeout=300, poll_interval=5, max_interval=30) -> QueryResponse` (`:85`)
- `get_flat(patient_id) -> dict` (`:185`)
- `get_ccda(patient_id) -> bytes` (`:139`)
- `get_fhir(patient_id) -> dict` (`:168`)

### QueryStatus enum
`PENDING → PROCESSING → COMPLETE | PARTIAL | FAILED`

### PurposeOfUse enum
`TREATMENT | PAYMENT | OPERATIONS` (required for HIPAA compliance)

## Document Module (Bi-Directionality)

### DocumentService (`document/service.py:19`)
Full document lifecycle for bi-directional data exchange:

- `submit(document: DocumentSubmission, file_content: bytes) -> DocumentResponse` (`:30`) — Upload a clinical document (multipart: metadata JSON + file bytes)
- `get(document_id: str) -> DocumentMetadata` (`:65`) — Retrieve metadata for a submitted document (verify upload)
- `delete(document_id: str) -> str` (`:85`) — Delete a document (returns "delete successful")
- `list_by_patient(patient_id: str) -> list[DocumentMetadata]` (`:106`) — List all documents for a patient

Uses `/api/v1/documents` endpoints (v1, not v2). The `patient_id` is your external ID, not the Particle UUID.

See `13-bidirectionality.md` for complete documentation including code value sets and workflow diagrams.

## Signal Module

### SignalService (`signal/service.py:43`)
- `subscribe(particle_patient_id, subscription_type=MONITORING) -> SubscribeResponse` (`:54`) — POST /api/v1/patients/{id}/subscriptions
- `trigger_sandbox_workflow(particle_patient_id, workflow, callback_url, display_name="Test", event_type=None) -> dict` (`:89`) — POST /api/v1/patients/{id}/subscriptions/trigger-sandbox-workflow
- `register_referral_organizations(organizations: list[ReferralOrganization]) -> dict` (`:133`) — POST /api/v1/referrals/organizations/registered
- `get_hl7v2_message(message_id) -> dict` (`:160`) — GET /hl7v2/{id}
- `get_flat_transitions(particle_patient_id) -> dict` (`:174`) — GET /api/v2/patients/{id}/flat?TRANSITIONS (returns `{}` on 404)
- `parse_webhook_notification(payload) -> WebhookNotification` (`:195`) — Static method, validates CloudEvents payload

### SubscriptionType enum
`MONITORING`

### WorkflowType enum (sandbox workflow triggers)
`ADMIT_TRANSITION_ALERT | DISCHARGE_TRANSITION_ALERT | TRANSFER_TRANSITION_ALERT | NEW_ENCOUNTER_ALERT | REFERRAL_ALERT | ADT | DISCHARGE_SUMMARY_ALERT`

### ADTEventType enum (required when workflow=ADT)
`A01` (Admit) | `A02` (Transfer) | `A03` (Discharge) | `A04` (Register) | `A08` (Update Info)

### API Quirks
- `subscribe()` handles 400 "already subscribed" as success (returns empty subscription list)
- `trigger_sandbox_workflow()` handles raw text `"success"` response (not JSON)
- `get_flat_transitions()` returns `{}` on 404 (no transitions yet)
- Webhook notifications use **CloudEvents 1.0** format with `type: "com.particlehealth.api.v2.transitionalerts"`

## Usage Patterns

**End-to-end query flow** (register → query → poll → retrieve):
See `particle-api-quickstarts/workflows/hello_particle.py:105` — `main()` function

**Signal lifecycle** (register → subscribe → trigger → retrieve transitions):
See `particle-api-quickstarts/workflows/signal_end_to_end.py:91` — `main()` function

**Webhook receiver** (local HTTP server for CloudEvents):
See `particle-api-quickstarts/workflows/signal_webhook_receiver.py:30` — `WebhookHandler` class

**Document lifecycle** (submit → verify → list → delete):
See `particle-api-quickstarts/workflows/manage_documents.py`

**Minimal pattern** (no workflow scripts):
```python
from particle.core import ParticleSettings, ParticleHTTPClient
from particle.patient import PatientService, PatientRegistration, Gender
from particle.query import QueryService

settings = ParticleSettings()  # loads from .env
with ParticleHTTPClient(settings) as client:
    patient_svc = PatientService(client)
    response = patient_svc.register(PatientRegistration(
        given_name="Jane", family_name="Doe",
        date_of_birth="1980-01-15", gender=Gender.FEMALE,
        postal_code="02215", address_city="Boston",
        address_state="MA", patient_id="my-external-id",
    ))
    query_svc = QueryService(client)
    query_svc.submit_query(response.particle_patient_id)
    result = query_svc.wait_for_query_complete(response.particle_patient_id)
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
| `workflows/submit_document.py` | Submit a clinical document (CCDA or PDF) |
| `workflows/manage_documents.py` | Get, list, or delete documents |
| `workflows/signal_subscribe_patient.py` | Register patient + subscribe to MONITORING |
| `workflows/signal_trigger_alert.py` | Register → subscribe → trigger ADMIT_TRANSITION_ALERT |
| `workflows/signal_end_to_end.py` | Full lifecycle: register → subscribe → trigger → retrieve transitions |
| `workflows/signal_webhook_receiver.py` | Local HTTP server on port 8080 to receive CloudEvents webhooks |

## Quick-Start Scripts (No SDK)

Direct API calls without the SDK, useful for debugging:

| Step | cURL | Python (httpx) |
|------|------|----------------|
| Auth | `quick-starts/curl/auth.sh` | `quick-starts/python/auth.py` |
| Register | `quick-starts/curl/register_patient.sh` | `quick-starts/python/register_patient.py` |
| Query | `quick-starts/curl/submit_query.sh` | `quick-starts/python/submit_query.py` |
| Retrieve | `quick-starts/curl/retrieve_data.sh` | `quick-starts/python/retrieve_data.py` |
| Submit Document | `quick-starts/curl/submit_document.sh` | `quick-starts/python/submit_document.py` |
| Manage Documents | `quick-starts/curl/manage_documents.sh` | `quick-starts/python/manage_documents.py` |
| Signal Subscribe | — | `quick-starts/python/signal_subscribe.py` |
| Signal Trigger | — | `quick-starts/python/signal_trigger_alert.py` |
| Signal Register Org | — | `quick-starts/python/signal_register_org.py` |
