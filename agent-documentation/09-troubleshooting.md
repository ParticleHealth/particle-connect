# Troubleshooting

Common issues and solutions when working with Particle Health APIs.

## FHIR Endpoint Returns 404 in Sandbox

**Symptom**: `GET /api/v2/patients/{id}/fhir` returns 404.

**Cause**: FHIR is production-only. Sandbox supports only flat and CCDA.

**Fix**: Use `flat` or `ccda` format:
```bash
python workflows/retrieve_data.py <patient_id> flat
```

**Detection**: Check if `PARTICLE_BASE_URL` contains "sandbox".

## Patient Registration Fails with address_state Error

**Symptom**: 422 validation error mentioning `address_state`.

**Cause**: API requires full state names. "MA" is rejected.

**Fix**: Use full state name: `"Massachusetts"`, not `"MA"`.

**Note**: The SDK does not auto-expand abbreviations.

## Overlay Error on Re-Registration

**Symptom**: "overlay detected" error when registering a patient.

**Cause**: Reusing a `patient_id` with different demographics than original registration.

**Fix**:
1. Use same demographics as original registration (idempotent update), or
2. Use a new unique `patient_id` for the different patient

**Prevention**: Generate unique patient_id values per patient. The `hello_particle.py` demo uses a fixed ID with fixed demographics, so re-runs are safe.

## Flat Data Returns Empty in Sandbox

**Symptom**: Query completes successfully (`state: COMPLETE`) but `GET /api/v2/patients/{id}/flat` returns `{}`.

**Cause**: Sandbox only returns flat data for seeded test patients. Arbitrary demographics (e.g., "John Smith") will register and query successfully but return no clinical data.

**Fix**: Use the demo patient from `hello_particle.py` (Elvira Valadez-Nucleus) or other seeded test patients when testing in sandbox.

## Query Stays in PROCESSING for Minutes

**Symptom**: Query `state` field returns PROCESSING for 2-5 minutes. (Note: the API field is `state`, not `status`.)

**Cause**: Normal. Particle queries multiple nationwide data sources. Each responds on its own timeline.

**Fix**: Use SDK's built-in polling:
```python
result = query_svc.wait_for_query_complete(patient_id, timeout_seconds=300)
```

**Note**: SDK uses exponential backoff (start 5s, cap 30s, 1.5x multiplier). Don't poll in a tight loop.

## 404 from Query Status After Submission

**Symptom**: `GET /api/v2/patients/{id}/query` returns 404 right after POST.

**Cause**: Brief propagation delay between submission and status availability.

**Fix**: SDK handles this — `wait_for_query_complete()` catches 404 and retries with backoff.

**Manual polling**: Add 5-second initial delay before first status check.

## Management API Auth Response Format

**Symptom**: Auth parsing fails or returns empty token.

**Cause**: Management API auth may return URL-encoded form data instead of JSON.

**Fix**: The `ParticleClient` in `management-ui/backend/app/services/particle_client.py` handles both formats:
```python
try:
    data = resp.json()
except Exception:
    parsed = parse_qs(raw)
    data = {k: v[0] for k, v in parsed.items()}
```

## Credential Listing Not Supported in Sandbox

**Symptom**: `GET /v1/serviceaccounts/{id}/credentials` returns 405 or 501.

**Cause**: Sandbox Management API doesn't support listing credentials.

**Fix**: The management-ui backend returns an empty list for 405/501 responses.

## BigQuery DML Concurrency

**Symptom**: BigQuery load operations queue or fail under concurrent use.

**Cause**: BigQuery limits concurrent DML to 2 active + 20 queued per table.

**Fix**: For multi-patient production loads, batch patients per load job instead of one job per patient.

## Token Expiry During Long Operations

**Symptom**: 401 errors during query polling or data retrieval.

**Cause**: JWT expired (1 hour TTL) during a long-running operation.

**Fix**: Both the SDK (`ParticleAuth`) and management-ui (`ParticleClient`) auto-refresh tokens before expiry. If using direct API calls, re-authenticate when receiving 401.

## DuckDB Database Reset

**Symptom**: Schema mismatch or stale data after loading new data.

**Fix**: Delete the database file and reload:
```bash
rm observatory.duckdb
particle-pipeline
```

Tables are auto-created on each load.
