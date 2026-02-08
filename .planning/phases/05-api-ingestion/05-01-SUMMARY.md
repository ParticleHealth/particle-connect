---
phase: 05-api-ingestion
plan: 01
subsystem: api-client
tags: [http, auth, jwt, retry, backoff, stdlib]
dependency-graph:
  requires: []
  provides: [ParticleAPIClient, _decode_jwt_expiry, RETRYABLE_STATUS_CODES]
  affects: [05-02]
tech-stack:
  added: []
  patterns: [exponential-backoff-with-jitter, jwt-decode-without-library, retry-with-token-refresh]
file-tracking:
  key-files:
    created:
      - particle-flat-observatory/src/observatory/api_client.py
      - particle-flat-observatory/tests/test_api_client.py
    modified: []
decisions:
  - id: 05-01-01
    summary: "Stdlib-only HTTP via urllib.request -- no httpx, tenacity, or jwt libraries"
  - id: 05-01-02
    summary: "JWT exp claim decoded via base64url without signature verification (sufficient for TTL check)"
  - id: 05-01-03
    summary: "Retry-After header respected via max(calculated_backoff, retry_after) on 429 responses"
  - id: 05-01-04
    summary: "401 during data fetch triggers single token refresh, not infinite retry loop"
  - id: 05-01-05
    summary: "python-dotenv loaded in constructor (same pattern as config.py) for .env credential loading"
metrics:
  duration: 2min
  completed: 2026-02-08
---

# Phase 5 Plan 1: Particle API Client Summary

Stdlib-only HTTP client for Particle Health API with JWT auth, exponential backoff (jitter + Retry-After), proactive token refresh at 10min buffer, and configurable timeout/retries.

## What Was Built

### ParticleAPIClient (`api_client.py`)

Production-grade HTTP client for Particle Health API using only Python stdlib (`urllib.request`, `base64`, `json`, `time`, `random`).

**Key capabilities:**
- **Credential validation** -- Constructor reads `PARTICLE_CLIENT_ID`, `PARTICLE_CLIENT_SECRET`, `PARTICLE_SCOPE_ID` from env; raises `ValueError` listing ALL missing vars (not just the first)
- **Auth flow** -- GET `{base_url}/auth` with `client-id`, `client-secret`, `scope` headers; `Accept: text/plain`; response is raw JWT string
- **JWT decode** -- `_decode_jwt_expiry()` extracts `exp` claim via base64url decode (no third-party JWT library)
- **Proactive token refresh** -- Token refreshed when within 600 seconds (10 min) of expiry
- **Exponential backoff** -- Formula: `min(1.0 * 2^attempt, 60.0) + random.uniform(0, 1.0)` with 60s cap
- **Retry-After respect** -- On 429, uses `max(calculated_backoff, Retry-After)`
- **401 recovery** -- Single token refresh attempt on 401 during data fetch (prevents infinite loop)
- **get_flat_data(patient_id)** -- Returns `dict[str, list[dict]]` matching the shape from `parser.load_flat_data()`
- **Configurable** -- `PARTICLE_TIMEOUT` (default 30s), `PARTICLE_MAX_RETRIES` (default 3), `PARTICLE_BASE_URL` (default sandbox)

### Unit Tests (`test_api_client.py`)

18 tests across 4 test classes:

| Class | Tests | Coverage |
|-------|-------|----------|
| TestCredentialValidation | 5 | Missing single var, multiple vars, valid construction |
| TestDecodeJwtExpiry | 4 | Valid token, no exp, malformed, invalid base64 |
| TestBackoffCalculation | 4 | Attempt 0/2/10, Retry-After header |
| TestConfigurationDefaults | 5 | base_url, timeout, max_retries, custom env overrides |

All tests use mocked I/O -- no real API calls. Deterministic backoff tests via `random.uniform` mock.

## Decisions Made

1. **Stdlib-only HTTP** -- `urllib.request` instead of httpx/requests. Matches project convention of minimal dependencies.
2. **JWT decode without library** -- base64url decode of payload segment to extract `exp` claim. No signature verification needed since we only need the TTL for refresh scheduling.
3. **Retry-After via max()** -- When 429 includes `Retry-After`, the backoff is `max(calculated, retry_after)` so we never sleep less than the server requests.
4. **Single 401 refresh** -- Boolean flag `token_refreshed` prevents infinite token-refresh loops if credentials are revoked mid-session.
5. **python-dotenv in constructor** -- Same `try/except ImportError` pattern as `config.py` for .env file loading.

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

1. `python -m pytest tests/test_api_client.py -v` -- 18/18 passed
2. `from observatory.api_client import ParticleAPIClient, _decode_jwt_expiry` -- importable
3. stdlib-only check -- no httpx, tenacity, or jwt imports found in source
4. `python -m pytest tests/ -v` -- 127/127 passed (zero regressions)

## Task Commits

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Write failing tests (RED) | 8b89631 | tests/test_api_client.py |
| 2 | Implement ParticleAPIClient (GREEN) | ad0ffe2 | src/observatory/api_client.py |

## Next Phase Readiness

Plan 05-02 can proceed. It will wire `ParticleAPIClient.get_flat_data()` into the CLI as a `--source api` option alongside the existing `--source file` path. The client is ready to be instantiated and called from a CLI command handler.
