---
phase: 05-api-ingestion
verified: 2026-02-08T12:30:00Z
status: passed
score: 10/10 must-haves verified
---

# Phase 5: API Ingestion Verification Report

**Phase Goal:** Customers can pull data directly from the Particle Health API instead of loading from files, with production-grade error handling

**Verified:** 2026-02-08T12:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `particle-pipeline load --source api --target postgres --patient-id <id>` authenticates with Particle Health and loads flat data from GET Flat endpoint | ✓ VERIFIED | CLI wired at line 116-137 of cli.py, calls ParticleAPIClient.get_flat_data(), applies normalization, feeds into existing pipeline |
| 2 | API calls retry automatically with exponential backoff on 429/5xx responses, with configurable timeout | ✓ VERIFIED | Retry logic at lines 197-294 of api_client.py, RETRYABLE_STATUS_CODES={429,500,502,503,504}, exponential backoff with jitter, Retry-After header respected |
| 3 | API ingestion feeds same downstream pipeline as file ingestion — identical parsing, normalization, and loading behavior | ✓ VERIFIED | Lines 130-137 of cli.py apply normalize_resource() to API data, iterate EXPECTED_RESOURCE_TYPES, produce same dict[str, list[dict]] shape. Both paths converge at line 152 (inspect_schema) |
| 4 | ParticleAPIClient raises ValueError listing missing env vars when PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, or PARTICLE_SCOPE_ID are unset | ✓ VERIFIED | Constructor lines 79-84 check all required vars, raise ValueError with all missing listed in message |
| 5 | ParticleAPIClient.get_flat_data(patient_id) returns dict[str, list[dict]] from Particle GET Flat endpoint | ✓ VERIFIED | Method at lines 106-137 returns parsed JSON dict, validated as dict type |
| 6 | Auth endpoint is called with GET method, custom headers (client-id, client-secret, scope), and accept: text/plain | ✓ VERIFIED | _acquire_token() at lines 149-195 uses GET, adds client-id/client-secret/scope headers (lines 160-162), Accept: text/plain (line 163) |
| 7 | Requests retry automatically with exponential backoff + jitter on 429 and 5xx responses, respecting Retry-After header | ✓ VERIFIED | _calculate_backoff() at lines 296-328 implements min(1.0 * 2^attempt, 60.0) + jitter, checks Retry-After header at lines 314-326 |
| 8 | Token is refreshed proactively when within 10 minutes of JWT expiry | ✓ VERIFIED | _ensure_token() at lines 139-147 checks expiry - 600 seconds (line 31: _REFRESH_BUFFER), refreshes proactively |
| 9 | 401 during data fetch triggers one token refresh attempt before failing | ✓ VERIFIED | _request_with_retry() at lines 247-252 handles 401 with token_refreshed flag (line 216), refreshes once, updates Authorization header |
| 10 | Timeout and max_retries are configurable via PARTICLE_TIMEOUT and PARTICLE_MAX_RETRIES env vars | ✓ VERIFIED | Lines 93-94 read from env with defaults (30, 3) |

**Score:** 10/10 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `particle-flat-observatory/src/observatory/api_client.py` | ParticleAPIClient class with auth, retry, get_flat_data | ✓ VERIFIED | 328 lines, contains class ParticleAPIClient, _decode_jwt_expiry, RETRYABLE_STATUS_CODES. Stdlib-only (urllib.request, base64, json, time, random). No stubs. |
| `particle-flat-observatory/tests/test_api_client.py` | Unit tests for API client | ✓ VERIFIED | 197 lines, 18 tests across 4 classes: TestCredentialValidation (5), TestDecodeJwtExpiry (4), TestBackoffCalculation (4), TestConfigurationDefaults (5). No real API calls. |
| `particle-flat-observatory/src/observatory/cli.py` | Wired --source api with --patient-id option | ✓ VERIFIED | Lines 59-66 add --patient-id option, lines 107-137 handle source=='api', deferred import of ParticleAPIClient (line 116), normalization applied (lines 131-137). |
| `particle-flat-observatory/.env.example` | PARTICLE_* env var documentation | ✓ VERIFIED | Lines 24-31 document 7 PARTICLE_* variables (CLIENT_ID, CLIENT_SECRET, SCOPE_ID, BASE_URL, TIMEOUT, MAX_RETRIES, PATIENT_ID) with comments. |
| `particle-flat-observatory/tests/test_cli_api.py` | CLI integration tests for API source | ✓ VERIFIED | 180 lines, 5 tests: missing patient-id, missing credentials, API failure, data normalization, file mode compatibility. Mocked I/O. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|------|------|--------|---------|
| cli.py | api_client.py | deferred import inside if source=='api' | ✓ WIRED | Line 116 imports ParticleAPIClient when source=='api', instantiated at 119, called at 125 |
| cli.py | normalizer.py | normalize_resource() applied to API response | ✓ WIRED | Line 131 imports normalize_resource, line 137 applies to each resource type, identical to file mode normalization |
| cli.py | parser.py | EXPECTED_RESOURCE_TYPES used to iterate API response | ✓ WIRED | Line 132 imports EXPECTED_RESOURCE_TYPES, line 135 iterates all 21 types ensuring consistent shape |
| api_client.py | urllib.request | stdlib HTTP calls | ✓ WIRED | Line 25 imports urllib.request, lines 169 and 225 use urlopen() for auth and data requests |
| api_client.py | base64 + json | JWT payload decode for exp claim | ✓ WIRED | Line 18 imports base64, line 55 uses urlsafe_b64decode for JWT payload, line 56 parses JSON, line 58 extracts exp |

### Requirements Coverage

Phase 5 requirements from REQUIREMENTS.md:

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| INGEST-02: Live API ingestion authenticates with Particle Health and calls GET Flat endpoint | ✓ SATISFIED | None — CLI calls ParticleAPIClient.get_flat_data(), which calls /api/v2/patients/{id}/flat with Bearer token |
| INGEST-03: API ingestion includes retries with exponential backoff for 429/5xx errors | ✓ SATISFIED | None — _request_with_retry() retries on {429,500,502,503,504}, exponential backoff with jitter and Retry-After support |
| INGEST-04: API ingestion includes configurable timeout | ✓ SATISFIED | None — PARTICLE_TIMEOUT env var (default 30s), applied to all urlopen() calls |

### Anti-Patterns Found

None detected.

**Scan performed on:**
- `particle-flat-observatory/src/observatory/api_client.py` — no TODO/FIXME/placeholder/stub patterns
- `particle-flat-observatory/src/observatory/cli.py` — no TODO/FIXME/placeholder/stub patterns
- `particle-flat-observatory/tests/test_api_client.py` — test file (expected patterns OK)
- `particle-flat-observatory/tests/test_cli_api.py` — test file (expected patterns OK)

### Implementation Quality Assessment

**Strengths:**

1. **Production-grade error handling:**
   - Actionable error messages for missing credentials (lists all missing vars)
   - 401/403 auth failures provide fix steps (check dashboard)
   - API request failures caught and reported with context
   - Connection failures provide troubleshooting steps

2. **Robust retry logic:**
   - Exponential backoff with jitter prevents thundering herd
   - Retry-After header respected (RFC 7231 compliant)
   - 401 recovery with single token refresh (prevents infinite loops)
   - Capped at 60s max backoff
   - Configurable max_retries

3. **Token lifecycle management:**
   - Proactive refresh at 10-minute buffer
   - JWT exp claim extracted without third-party library
   - Token refresh on 401 during data fetch
   - Expiry stored as timezone-aware datetime

4. **Consistent pipeline integration:**
   - API data normalized identically to file data
   - Both paths produce dict[str, list[dict]] with all 21 resource types
   - Downstream pipeline (schema, loader, quality) unchanged
   - Works with both --target postgres and --target bigquery

5. **Minimal dependencies:**
   - Stdlib-only HTTP (urllib.request)
   - No httpx, requests, tenacity, or jwt libraries
   - Matches project philosophy of minimal dependencies

6. **Comprehensive testing:**
   - 18 unit tests for API client (credential validation, JWT decode, backoff math, config)
   - 5 CLI integration tests (missing patient-id, missing creds, API failures, normalization, file mode compat)
   - All tests use mocked I/O (no real API calls or DB connections)
   - Deterministic backoff tests via random.uniform mock

**Observations:**

- Deferred import pattern in cli.py (line 116) keeps api_client.py from loading in file mode — good separation
- CLI help includes API source example (line 85)
- .env.example documents all PARTICLE_* vars with defaults
- --patient-id silently ignored in file mode (no warning) — consistent with CLI design philosophy

### Human Verification Required

None. All success criteria are programmatically verifiable and passed.

### Gaps Summary

No gaps found. All must-haves verified.

---

_Verified: 2026-02-08T12:30:00Z_
_Verifier: Claude (gsd-verifier)_
