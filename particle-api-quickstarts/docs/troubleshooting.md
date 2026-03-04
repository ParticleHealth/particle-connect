# Troubleshooting

Common issues when working with the Particle Health API, especially in the sandbox environment.

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
