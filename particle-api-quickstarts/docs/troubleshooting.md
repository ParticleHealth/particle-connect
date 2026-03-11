# Troubleshooting

Common issues when working with the Particle Health API, especially in the sandbox environment.

## Error quick reference

HTTP status code to SDK exception mapping. Check this table first to classify the error, then find the detailed section below.

| HTTP Code | SDK Exception | Retry Safe | What To Do |
|---|---|---|---|
| 401 | `ParticleAuthError` | No | Bad credentials. SDK auto-refreshes tokens; if this fires, `client_id`/`client_secret` are wrong |
| 403 | `ParticleAuthError` | No | Valid credentials, wrong permissions. Check `scope_id` |
| 404 | `ParticleNotFoundError` | Depends | Bad resource ID. Exception: 404 right after query submission is transient — retry |
| 422 | `ParticleValidationError` | No | Bad request payload. Check `error.errors` for field-level details |
| 429 | `ParticleRateLimitError` | Yes | Wait `error.retry_after` seconds, then retry. SDK does NOT auto-retry 429s |
| 500/502/503 | `ParticleAPIError` | Yes | Server error. SDK auto-retries 3 times with backoff |
| N/A | `ParticleQueryTimeoutError` | Yes | Polling exceeded `timeout_seconds`. Increase timeout or check patient data |
| N/A | `ParticleQueryFailedError` | No | Server rejected query. Check `error.error_message` |

## Exception handling pattern

Catch from most specific to least specific. All exceptions inherit from `ParticleError`.

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

## Retry classification

**SDK auto-retries (no action needed):** Connection errors (`httpx.ConnectError`), read/write/pool timeouts, 5xx server errors. 3 retries with exponential backoff + jitter.

**You must retry manually:** 429 rate limits (wait `retry_after` seconds), `ParticleQueryTimeoutError` (increase `timeout_seconds`).

**Never retry — fix the input:** 401, 403, 404 (except post-submission), 422, `ParticleQueryFailedError`.

---

## FHIR endpoint returns 404 in sandbox

**Symptom:** `GET /api/v2/patients/{id}/fhir` returns 404.

**Cause:** The FHIR endpoint is not available in the sandbox environment. Sandbox only supports flat JSON and CCDA formats.

**Fix:** Use `flat` or `ccda` format instead:

```bash
python workflows/retrieve_data.py <patient_id> flat
python workflows/retrieve_data.py <patient_id> ccda
```

**Prevention:** Check `PARTICLE_BASE_URL` — if it contains `sandbox`, use flat or CCDA.

## Patient registration fails with "address_state" error

**Symptom:** 422 validation error on patient registration mentioning `address_state`.

**Cause:** The API requires two-letter state abbreviations. Full state names like `"Massachusetts"` are rejected; `"MA"` is accepted.

**Fix:** Use the two-letter abbreviation:

```python
PatientRegistration(
    address_state="MA",  # not "Massachusetts"
    ...
)
```

**Prevention:** The SDK does not auto-abbreviate state names. Always pass the two-letter abbreviation in your patient data.

## Overlay error on re-registration

**Symptom:** API returns an error like "overlay detected" when registering a patient.

**Cause:** You're re-using a `patient_id` that was previously registered with different demographics (name, DOB, etc.). Particle treats this as a conflict.

**Fix:** Either:
1. Use the same demographics as the original registration (idempotent update), or
2. Use a new unique `patient_id` for the different patient.

**Prevention:** Generate unique `patient_id` values per patient. Don't reuse IDs across different people. The `hello_particle.py` demo uses a fixed ID with fixed demographics, so re-runs are safe.

## Flat data returns empty in sandbox

**Symptom:** Query completes successfully but `GET /api/v2/patients/{id}/flat` returns `{}`.

**Cause:** Sandbox only returns flat data for seeded test patients. Arbitrary demographics (e.g., "John Smith") will register and query successfully but return no clinical data.

**Fix:** Use the demo patient from `hello_particle.py` (Elvira Valadez-Nucleus) or other seeded test patients when testing in sandbox.

## Query stays in PROCESSING for several minutes

**Symptom:** Query status returns `PROCESSING` for 2-5 minutes before completing.

**Cause:** This is normal. Particle queries multiple data sources across a nationwide network. Each source responds on its own timeline.

**Fix:** Use the SDK's built-in polling with `wait_for_query_complete()`:

```python
result = query_svc.wait_for_query_complete(
    particle_patient_id=patient_id,
    timeout_seconds=300,  # 5 minutes
)
```

**Prevention:** Set a reasonable timeout (300s is the default). The SDK uses exponential backoff to avoid hammering the API. Don't poll manually in a tight loop.

## 404 from query status immediately after submission

**Symptom:** `GET /api/v2/patients/{id}/query` returns 404 right after `POST` to submit the query.

**Cause:** There's a brief propagation delay between query submission and status availability. The status endpoint may not recognize the query for a few seconds.

**Fix:** The SDK handles this automatically — `wait_for_query_complete()` catches 404 responses during polling and retries with backoff.

**Prevention:** Always use `wait_for_query_complete()` instead of manually checking status. If you must poll manually, add a short initial delay (5 seconds) before the first status check.

## Rate limit exceeded (429)

**Symptom:** `ParticleRateLimitError` raised. HTTP 429 response.

**Cause:** Too many requests in a short window.

**Fix:** Wait `error.retry_after` seconds before retrying:

```python
except ParticleRateLimitError as e:
    time.sleep(e.retry_after or 60)
    # retry the operation
```

**Prevention:** The SDK parses the `Retry-After` header but does NOT auto-retry 429s. Unlike 5xx errors, you must handle these in your code.

## Persistent 5xx server errors

**Symptom:** `ParticleAPIError` with `status_code` 500, 502, or 503 after all retries exhausted.

**Cause:** Particle API is experiencing an outage or degraded service. The SDK already retried 3 times with exponential backoff.

**Fix:**
1. Wait 5-10 minutes and retry
2. Check Particle status page or support channels
3. Do not retry in a tight loop — this will worsen the issue

## Forbidden (403)

**Symptom:** `ParticleAuthError` with message "Not authorized for this operation".

**Cause:** Valid credentials but insufficient permissions. Common when `scope_id` doesn't grant access to the requested resource or operation.

**Fix:**
1. Verify `PARTICLE_SCOPE_ID` is correct for the target project
2. Confirm the service account has the required IAM role
3. Management API operations require org-level credentials, not project-level

**Prevention:** 403 is distinct from 401. A 401 means bad credentials; 403 means valid credentials but wrong permissions.

## Validation error (422) — general

**Symptom:** `ParticleValidationError` raised. The `errors` attribute contains field-level details.

**Cause:** Request payload failed server-side validation. Common triggers beyond `address_state`:
- Missing required fields (`given_name`, `family_name`, `date_of_birth`, `gender`, `postal_code`, `address_city`, `address_state`, `patient_id`)
- Invalid `date_of_birth` format (must be YYYY-MM-DD)
- Invalid `gender` value (must be MALE or FEMALE)
- Invalid `postal_code` (must be 5 or 9 digits)
- Invalid `ssn` format (must be XXX-XX-XXXX)

**Fix:** Read `error.errors` for the specific field and reason:

```python
except ParticleValidationError as e:
    for field_error in e.errors:
        print(field_error)  # {"field": "date_of_birth", "message": "..."}
```

**Prevention:** Pydantic validation in the SDK catches some of these before the API call. If you bypass the SDK models, you'll get 422s from the server instead.

## Query polling timeout

**Symptom:** `ParticleQueryTimeoutError` raised after `timeout_seconds` elapsed.

**Cause:** Query did not reach COMPLETE or FAILED state within the timeout window. Default is 300 seconds (5 minutes).

**Fix:**
1. Increase timeout: `wait_for_query_complete(patient_id, timeout_seconds=600)`
2. Check if the patient has data — sandbox only returns data for seeded test patients
3. A timed-out query may still complete server-side. Check status later with `get_query_status()`

**Prevention:** This is a client-side timeout, not a server error. The query continues processing on Particle's side.

## Query failed on server

**Symptom:** `ParticleQueryFailedError` raised. Query `state` is FAILED.

**Cause:** Particle's backend rejected or could not process the query. The `error.error_message` field contains details.

**Fix:** Read the error message. Common causes:
1. Patient demographics don't match any records in the network
2. Server-side processing error (retry with a new query submission)
3. Invalid patient registration data that passed client validation but failed downstream

**Prevention:** Do not retry the same query without reviewing the error message. If the error is transient, submit a new query rather than re-polling the failed one.

## Document submission errors

**Symptom:** `ParticleValidationError` or `ParticleAPIError` from `DocumentService.submit()`.

**Cause:** Document upload rejected. Common triggers:
- Unsupported document type (only CCDA XML and PDF are accepted)
- File too large
- Patient ID not found (must use your external `patient_id`, not the Particle UUID)
- Missing or malformed multipart form data

**Fix:** Verify:
1. Document type is `"ccda"` or `"pdf"`
2. Patient was registered with the `patient_id` you're using
3. File content is valid (well-formed XML for CCDA, valid PDF)

## Connection and timeout errors

**Symptom:** `httpx.ConnectError`, `httpx.ReadTimeout`, `httpx.WriteTimeout`, or `httpx.PoolTimeout` after all retries exhausted.

**Cause:** Network-level failure. Cannot reach Particle API endpoint. The SDK already retried 3 times.

**Fix:**
1. Verify `PARTICLE_BASE_URL` is correct (`https://sandbox.particlehealth.com` or `https://api.particlehealth.com`)
2. Check network/firewall/proxy settings
3. Increase `PARTICLE_TIMEOUT` if responses are slow (default 30s)
