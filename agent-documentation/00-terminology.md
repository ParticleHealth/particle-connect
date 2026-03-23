# Terminology

Key terms that are easily confused. Read this before working with any Particle API.

## Patient Identifiers

| Term | Format | Who Creates It | Where Used | Example |
|------|--------|---------------|------------|---------|
| `patient_id` | Any string | You (the integrator) | Patient registration, document submission, idempotency key | `"my-system-patient-42"` |
| `particle_patient_id` | UUID | Particle (returned in response) | Query submission, status polling, data retrieval, Signal subscriptions | `"a1b2c3d4-e5f6-..."` |
| `external_patient_id` | Same as `patient_id` | You | Returned in query responses as echo of your `patient_id` | `"my-system-patient-42"` |
| `person_id` | UUID | Particle (legacy) | Query completion webhook notifications only — same as `particle_patient_id` in most cases | `"a1b2c3d4-e5f6-..."` |

**Critical rule**: Use `particle_patient_id` (UUID from Particle) for all Query Flow API calls after registration. Use `patient_id` (your external ID) for Document API calls. Mixing them up causes 404 or mismatched data.

## API Field Names That Confuse LLMs

| Field | Appears In | Actual Meaning | Common Mistake |
|-------|-----------|----------------|----------------|
| `state` | Query status response | Query processing state: PENDING/PROCESSING/COMPLETE/PARTIAL/FAILED | Confused with US state or project state |
| `address_state` | Patient registration | US state abbreviation: "MA", "NY", "CA" | Using full name "Massachusetts" (causes 422) |
| `state` | Project model | Project lifecycle: STATE_ACTIVE/STATE_INACTIVE | Confused with query state or US state |
| `status` | Credential model | Credential status | Confused with query state (the query field is `state`, NOT `status`) |
| `type` | Multiple models | Varies: SubscriptionType, DocumentType, notification_type | Overloaded — always check which model |

## Environment Terms

| Term | Meaning |
|------|---------|
| Sandbox | `sandbox.particlehealth.com` — test environment, seeded patients, FHIR unavailable |
| Production | `api.particlehealth.com` — real patient data, all formats available |
| Management API | `management.{env}.particlehealth.com` — separate subdomain for org/project management |
| Query Flow API | Same host as auth — patient registration, queries, data retrieval |

## Credential Levels

| Level | Used For | Auth Method | Scope Header |
|-------|----------|-------------|-------------|
| Project-level | Query Flow API (patient data) | GET /auth with `scope` header | Required: `projects/{id}` |
| Org-level | Management API (projects, service accounts) | POST /auth, no scope | Not used |

## Data Format Terms

| Term | Meaning | Sandbox | Production |
|------|---------|---------|------------|
| Flat | Particle's denormalized JSON — 21 resource types, all string values | Yes | Yes |
| CCDA | C-CDA XML clinical documents in a ZIP file | Yes | Yes |
| FHIR | FHIR R4 Bundle (JSON) | No (returns 404) | Yes |
| Transitions | ADT event data from Signal subscriptions, accessed via flat endpoint with `?TRANSITIONS` | Yes (via sandbox trigger) | Yes |
