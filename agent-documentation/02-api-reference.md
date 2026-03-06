# API Reference — Query Flow

The Particle Health Query Flow API enables patient registration, clinical data queries, and data retrieval.

## Base URLs

| Environment | URL |
|-------------|-----|
| Sandbox | `https://sandbox.particlehealth.com` |
| Production | `https://api.particlehealth.com` |

## Authentication

All endpoints (except `/auth`) require a Bearer JWT token in the `Authorization` header.

```
GET /auth
Headers:
  client-id: <your-client-id>
  client-secret: <your-client-secret>
  scope: projects/<your-project-id>
  accept: text/plain

Response: JWT token as plain text (1 hour TTL)
```

This is NOT standard OAuth2. See `08-authentication.md` for details.

## Endpoints

### Register Patient
```
POST /api/v2/patients
Content-Type: application/json

Body:
{
  "given_name": "string (required)",
  "family_name": "string (required)",
  "date_of_birth": "YYYY-MM-DD (required)",
  "gender": "MALE | FEMALE (required)",
  "postal_code": "5 or 9 digit ZIP (required)",
  "address_city": "string (required)",
  "address_state": "Two-letter state abbreviation, e.g. 'MA' (required)",
  "patient_id": "your external ID (required, enables idempotency)",
  "address_lines": ["string array (optional)"],
  "ssn": "XXX-XX-XXXX (optional)",
  "telephone": "XXX-XXX-XXXX (optional)",
  "email": "string (optional)"
}

Response 200:
{
  "particle_patient_id": "uuid",
  "given_name": "...",
  ...echoed demographics
}
```

**Gotcha**: `address_state` MUST be a two-letter state abbreviation. "Massachusetts" is rejected; "MA" is accepted.

**Idempotency**: Same `patient_id` + same demographics = updates existing. Same `patient_id` + different demographics = overlay error.

### Submit Query
```
POST /api/v2/patients/{particle_patient_id}/query
Content-Type: application/json

Body:
{
  "purpose_of_use": "TREATMENT | PAYMENT | OPERATIONS"
}

Response 200:
{
  "particle_patient_id": "uuid",
  "external_patient_id": "your patient_id",
  "purpose_of_use": "TREATMENT",
  "query_id": "uuid"
}
```

### Check Query Status
```
GET /api/v2/patients/{particle_patient_id}/query

Response 200:
{
  "state": "PENDING | PROCESSING | COMPLETE | PARTIAL | FAILED",
  "files_available": 0,
  "files_downloaded": 0,
  "error_message": null
}
```

**State progression**: PENDING → PROCESSING → COMPLETE | PARTIAL | FAILED (note: the API field is `state`, not `status`)

**Timing**: Queries take 2-5 minutes. Use exponential backoff (SDK default: start at 5s, cap at 30s, 1.5x multiplier).

**Note**: Status endpoint may return 404 briefly after submission (propagation delay). The SDK handles this automatically.

### Retrieve Flat Data
```
GET /api/v2/patients/{particle_patient_id}/flat
Accept: application/json

Response 200: JSON object with resource type arrays
```

Particle's denormalized JSON format. Each resource type is a flat list of records with string values. Easiest to parse and load into databases.

**Sandbox limitation**: Flat data only returns results for seeded test patients (e.g., Elvira Valadez-Nucleus from `hello_particle.py`). Arbitrary patient demographics will query successfully but return empty data (`{}`).

### Retrieve CCDA
```
GET /api/v2/patients/{particle_patient_id}/ccda

Response 200: ZIP file containing CCDA XML documents
```

Standard C-CDA XML clinical documents. Available in both sandbox and production.

### Retrieve FHIR
```
GET /api/v2/patients/{particle_patient_id}/fhir
Accept: application/json

Response 200: FHIR R4 Bundle (JSON)
```

**Sandbox limitation**: Returns 404. FHIR is production-only.

### Submit Document
```
POST /api/v1/documents
Content-Type: multipart/form-data

Fields:
  metadata: JSON string with document metadata
  file: document file content (XML or PDF)

Metadata fields:
{
  "patient_id": "your external patient ID (required)",
  "document_id": "your document ID (required)",
  "type": "CLINICAL",
  "title": "filename.xml",
  "mime_type": "application/xml | application/pdf",
  "creation_time": "ISO8601 datetime",
  "format_code": "IHE format code",
  "class_code": "LOINC class code",
  "type_code": "LOINC type code",
  "confidentiality_code": "N (Normal, default)",
  "healthcare_facility_type_code": "SNOMED code",
  "practice_setting_code": "SNOMED code"
}

Response 200:
{
  "document_id": "...",
  "patient_id": "...",
  "status": "..."
}
```

**Note**: Uses v1 endpoint (not v2). The `patient_id` is your external ID, not the Particle UUID.

## Signal Endpoints

### Subscribe Patient to Monitoring
```
POST /api/v1/patients/{particle_patient_id}/subscriptions
Content-Type: application/json

Body:
{
  "type": "MONITORING"
}

Response 200:
{
  "subscriptions": [
    { "id": "uuid", "type": "MONITORING" }
  ]
}
```

**Gotcha**: Returns 400 if patient is already subscribed. Treat 400 as success (already subscribed).

**Gotcha**: Sandbox may return empty response body. Parse defensively.

### Trigger Sandbox Workflow
```
POST /api/v1/patients/{particle_patient_id}/subscriptions/trigger-sandbox-workflow
Content-Type: application/json

Body:
{
  "workflow": "ADMIT_TRANSITION_ALERT | DISCHARGE_TRANSITION_ALERT | TRANSFER_TRANSITION_ALERT | NEW_ENCOUNTER_ALERT | REFERRAL_ALERT | ADT | DISCHARGE_SUMMARY_ALERT",
  "callback_url": "https://your-webhook-url.example.com/webhook",
  "display_name": "Test",
  "event_type": "A01 | A02 | A03 | A04 | A08 (required only for ADT workflow)"
}

Response 200: "success" (plain text, NOT JSON)
```

**Gotcha**: Response is raw text `"success"`, not a JSON object.

### Register Referral Organizations
```
POST /api/v1/referrals/organizations/registered
Content-Type: application/json

Body:
[
  { "oid": "2.16.840.1.113883.3.8391.5.710576" }
]
```

### Get HL7v2 Message
```
GET /hl7v2/{message_id}

Response 200: HL7v2 message object (JSON)
```

**Note**: No `/api/v2` prefix — this endpoint is at the root path.

### Retrieve Flat Transitions
```
GET /api/v2/patients/{particle_patient_id}/flat?TRANSITIONS

Response 200: JSON object with transition resource arrays
Response 404: No transitions available yet (returns empty dict in SDK)
```

### Webhook Notification Format (CloudEvents 1.0)
```json
{
  "specversion": "1.0",
  "type": "com.particlehealth.api.v2.transitionalerts",
  "subject": "patient-id",
  "source": "particle-health",
  "id": "notification-uuid",
  "time": "2026-03-06T12:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "particle_patient_id": "uuid",
    "event_type": "A01",
    "event_sequence": 1,
    "is_final_event": false,
    "resources": [
      { "file_id": "uuid", "resource_ids": ["path/to/resource"] }
    ]
  }
}
```

## Data Formats Summary

| Format | Sandbox | Production | Best For |
|--------|---------|------------|----------|
| Flat | Yes | Yes | Data analysis, database loading, pipeline work |
| CCDA | Yes | Yes | Original clinical documents, EHR interoperability |
| FHIR | No | Yes | Standard interoperability, rich clinical semantics |

## Error Responses

| Status | Exception | Meaning |
|--------|-----------|---------|
| 401 | ParticleAuthError | Invalid or expired credentials |
| 403 | ParticleAuthError | Not authorized for this operation |
| 404 | ParticleNotFoundError | Resource not found |
| 422 | ParticleValidationError | Request validation failed |
| 429 | ParticleRateLimitError | Rate limit exceeded (check Retry-After header) |
| 5xx | ParticleAPIError | Server error (retried automatically by SDK) |

## SDK Implementation

Source: `particle-api-quickstarts/src/particle/`
- Auth: `core/auth.py` — ParticleAuth (httpx.Auth subclass with auto-refresh)
- HTTP: `core/http.py` — ParticleHTTPClient (retry with tenacity)
- Patient: `patient/service.py` — PatientService.register()
- Query: `query/service.py` — QueryService.submit_query(), wait_for_query_complete(), get_flat(), get_ccda(), get_fhir()
- Document: `document/service.py` — DocumentService.submit()
- Signal: `signal/service.py` — SignalService.subscribe(), trigger_sandbox_workflow(), register_referral_organizations(), get_hl7v2_message(), get_flat_transitions()
