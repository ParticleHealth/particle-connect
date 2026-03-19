# Troubleshooting

Common issues and solutions when working with Particle Health APIs.

## Error Quick Reference

HTTP status code to exception mapping. Use this table to identify the error class before reading the detailed section below.

| HTTP Code | SDK Exception | Retry Safe | Action |
|---|---|---|---|
| 401 | `ParticleAuthError` | No | Check credentials. SDK auto-refreshes tokens; if this still fires, client_id/client_secret are wrong |
| 403 | `ParticleAuthError` | No | Scope or permission issue. Verify `scope_id` matches the operation |
| 404 | `ParticleNotFoundError` | Depends | Check resource ID. Exception: 404 right after query submission is transient — retry |
| 422 | `ParticleValidationError` | No | Fix request payload. Check `error.errors` list for field-level details |
| 429 | `ParticleRateLimitError` | Yes | Wait `error.retry_after` seconds, then retry. SDK does NOT auto-retry 429s |
| 500/502/503 | `ParticleAPIError` | Yes | Transient server error. SDK auto-retries with exponential backoff (3 attempts) |
| N/A | `ParticleQueryTimeoutError` | Yes | Polling exceeded `timeout_seconds`. Increase timeout or check if patient has data |
| N/A | `ParticleQueryFailedError` | No | Query failed server-side. Check `error.error_message` for details |

## Exception Handling Pattern

Catch exceptions from most specific to least specific. All exceptions inherit from `ParticleError`.

```python
from particle.core.exceptions import (
    ParticleAuthError,
    ParticleValidationError,
    ParticleRateLimitError,
    ParticleNotFoundError,
    ParticleQueryTimeoutError,
    ParticleQueryFailedError,
    ParticleAPIError,
    ParticleError,
)

try:
    result = query_svc.wait_for_query_complete(patient_id)
except ParticleAuthError:
    # 401/403 — credentials or permissions. Do not retry.
    pass
except ParticleValidationError as e:
    # 422 — bad input. Read e.errors for field details. Do not retry.
    pass
except ParticleRateLimitError as e:
    # 429 — wait e.retry_after seconds, then retry.
    pass
except ParticleNotFoundError:
    # 404 — resource doesn't exist. Check IDs.
    pass
except ParticleQueryTimeoutError:
    # Polling exceeded timeout. Retry with longer timeout or check patient.
    pass
except ParticleQueryFailedError as e:
    # Server rejected query. Read e.error_message. Do not retry same input.
    pass
except ParticleAPIError as e:
    # Other HTTP errors. Check e.status_code.
    pass
except ParticleError:
    # Catch-all for any Particle SDK error.
    pass
```

## Retry Classification

**SDK auto-retries (no action needed):** Connection errors (`httpx.ConnectError`), read/write/pool timeouts, 5xx server errors. Retries 3 times with exponential backoff + jitter.

**You must retry manually:** 429 rate limits (wait `retry_after` seconds), `ParticleQueryTimeoutError` (increase `timeout_seconds`).

**Never retry — fix the input:** 401, 403, 404 (except post-submission), 422, `ParticleQueryFailedError`.

---

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

**Cause**: API requires two-letter state abbreviations. Full state names like "Massachusetts" are rejected.

**Fix**: Use the two-letter abbreviation: `"MA"`, not `"Massachusetts"`.

**Note**: The SDK does not auto-abbreviate state names.

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

## Signal Subscribe Returns 400

**Symptom**: `POST /api/v1/patients/{id}/subscriptions` returns 400.

**Cause**: Patient is already subscribed to monitoring.

**Fix**: Treat 400 as success. The SDK `SignalService.subscribe()` handles this automatically and returns an empty subscription list.

## Signal Trigger Returns Plain Text

**Symptom**: `trigger_sandbox_workflow()` fails to parse response as JSON.

**Cause**: The endpoint returns raw text `"success"`, not a JSON object.

**Fix**: The SDK handles this. If using raw httpx, check `response.text` instead of `response.json()`.

## Signal Flat Transitions Returns 404

**Symptom**: `GET /api/v2/patients/{id}/flat?TRANSITIONS` returns 404 after triggering a workflow.

**Cause**: Transition data may not be available immediately after workflow trigger.

**Fix**: The SDK `get_flat_transitions()` returns `{}` on 404. Retry after a short delay if needed.

## DuckDB Database Reset

**Symptom**: Schema mismatch or stale data after loading new data.

**Fix**: Delete the database file and reload:
```bash
rm observatory.duckdb
particle-pipeline
```

Tables are auto-created on each load.

## Rate Limit Exceeded (429)

**Symptom**: `ParticleRateLimitError` raised. HTTP 429 response.

**Cause**: Too many requests in a short window.

**Fix**: Wait `error.retry_after` seconds before retrying. The SDK parses the `Retry-After` header but does NOT auto-retry 429s.

```python
except ParticleRateLimitError as e:
    time.sleep(e.retry_after or 60)
    # retry the operation
```

**Note**: Unlike 5xx errors, 429s are not in the SDK's automatic retry set. You must handle them in your code.

## Persistent 5xx Server Errors

**Symptom**: `ParticleAPIError` with `status_code` 500, 502, or 503 after all retries exhausted.

**Cause**: Particle API is experiencing an outage or degraded service.

**Fix**: The SDK already retried 3 times with exponential backoff. If you still get this error:
1. Wait 5-10 minutes and retry
2. Check Particle status page or support channels
3. Do not retry in a tight loop — this will worsen the issue

**Note**: 5xx errors are transient. If persistent across minutes, the issue is on Particle's side.

## Forbidden (403)

**Symptom**: `ParticleAuthError` with message "Not authorized for this operation".

**Cause**: Valid credentials but insufficient permissions. Common when `scope_id` doesn't grant access to the requested resource or operation.

**Fix**:
1. Verify `PARTICLE_SCOPE_ID` is correct for the target project
2. Confirm the service account has the required IAM role
3. Management API operations require org-level credentials, not project-level

**Note**: 403 is distinct from 401. A 401 means bad credentials; 403 means valid credentials but wrong permissions.

## Validation Error (422) — General

**Symptom**: `ParticleValidationError` raised. The `errors` attribute contains field-level details.

**Cause**: Request payload failed server-side validation. Common triggers beyond `address_state`:
- Missing required fields (`given_name`, `family_name`, `date_of_birth`, `gender`, `postal_code`, `address_city`, `address_state`, `patient_id`)
- Invalid `date_of_birth` format (must be YYYY-MM-DD)
- Invalid `gender` value (must be MALE or FEMALE)
- Invalid `postal_code` (must be 5 or 9 digits)
- Invalid `ssn` format (must be XXX-XX-XXXX)

**Fix**: Read `error.errors` for the specific field and reason:
```python
except ParticleValidationError as e:
    for field_error in e.errors:
        print(field_error)  # {"field": "date_of_birth", "message": "..."}
```

**Note**: Pydantic validation in the SDK catches some of these before the API call. If you bypass the SDK models, you'll get 422s from the server instead.

## Query Polling Timeout

**Symptom**: `ParticleQueryTimeoutError` raised after `timeout_seconds` elapsed.

**Cause**: Query did not reach COMPLETE or FAILED state within the timeout window. Default is 300 seconds (5 minutes).

**Fix**:
1. Increase timeout: `wait_for_query_complete(patient_id, timeout_seconds=600)`
2. Check if the patient has data — sandbox only returns data for seeded test patients
3. A timed-out query may still complete server-side. You can check status later with `get_query_status()`

**Note**: This is a client-side timeout, not a server error. The query continues processing on Particle's side.

## Query Failed on Server

**Symptom**: `ParticleQueryFailedError` raised. Query `state` is FAILED.

**Cause**: Particle's backend rejected or could not process the query. The `error.error_message` field contains details.

**Fix**: Read the error message. Common causes:
1. Patient demographics don't match any records in the network
2. Server-side processing error (retry with a new query submission)
3. Invalid patient registration data that passed client validation but failed downstream

**Note**: Do not retry the same query without reviewing the error message. If the error is transient, submit a new query rather than re-polling the failed one.

## Document Submission Errors

**Symptom**: `ParticleValidationError` or `ParticleAPIError` from `DocumentService.submit()`.

**Cause**: Document upload rejected. Common triggers:
- Unsupported document type (only CCDA XML and PDF are accepted)
- File too large
- Patient ID not found (must use your external `patient_id`, not the Particle UUID)
- Missing or malformed multipart form data

**Fix**: Verify:
1. Document type is `"ccda"` or `"pdf"`
2. Patient was registered with the `patient_id` you're using
3. File content is valid (well-formed XML for CCDA, valid PDF)

## Document List Returns Null After Deletion

**Symptom**: `GET /api/v1/documents/patient/{patient_id}` returns `null` instead of `[]` when a patient has no documents.

**Cause**: The API returns a JSON `null` (not an empty array) when all documents for a patient have been deleted or none have been submitted.

**Fix**: Always null-check the response before iterating or calling `len()`:
```python
documents = response.json()
if documents is None:
    documents = []
```

The SDK `DocumentService.list_by_patient()` handles this automatically.

## Document Delete Response Is JSON, Not Plain Text

**Symptom**: Parsing `DELETE /api/v1/documents/{document_id}` response as a plain string gives `{"message":"delete successful"}` instead of just `"delete successful"`.

**Cause**: The API returns a JSON object `{"message": "delete successful"}`, not a raw text string as some documentation suggests.

**Fix**: Parse the response as JSON if you need the message:
```python
result = response.json()  # {"message": "delete successful"}
```

Or just check the HTTP status code — a 200 means the delete succeeded regardless of body format.

## Connection and Timeout Errors

**Symptom**: `httpx.ConnectError`, `httpx.ReadTimeout`, `httpx.WriteTimeout`, or `httpx.PoolTimeout` after all retries exhausted.

**Cause**: Network-level failure. Cannot reach Particle API endpoint.

**Fix**:
1. Verify `PARTICLE_BASE_URL` is correct (`https://sandbox.particlehealth.com` or `https://api.particlehealth.com`)
2. Check network/firewall/proxy settings
3. Increase `PARTICLE_TIMEOUT` if responses are slow (default 30s)

**Note**: SDK auto-retries all connection/timeout errors 3 times. If you see this error, all retries failed.
