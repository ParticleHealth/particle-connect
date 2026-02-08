# External Integrations

**Analysis Date:** 2026-02-07

## APIs & External Services

**Particle Health API:**
- Service: Nationwide health data network API for clinical records retrieval
- What it's used for: Register patients, submit queries for clinical data, retrieve data in multiple formats (FHIR, Flat JSON, CCDA), submit documents
- SDK/Client: Custom httpx wrapper (`ParticleHTTPClient`) in `src/particle/core/http.py`
- Auth: Custom JWT-based authentication (not standard OAuth2)
  - Method: GET `/auth` with custom headers
  - Env vars: `PARTICLE_CLIENT_ID`, `PARTICLE_CLIENT_SECRET`, `PARTICLE_SCOPE_ID`
  - Token TTL: 1 hour with proactive refresh at 10-minute buffer
  - Location: `src/particle/core/auth.py` - `ParticleAuth` class

**Endpoints:**
- `/auth` - GET - Token acquisition (custom headers, returns JWT as plain text)
- `/api/v2/patients` - POST - Register a patient
- `/api/v2/patients/{id}/query` - POST - Submit query for clinical data
- `/api/v2/patients/{id}/query` - GET - Check query status
- `/api/v2/patients/{id}/flat` - GET - Retrieve flat JSON clinical data
- `/api/v2/patients/{id}/fhir` - GET - Retrieve FHIR Bundle (production only)
- `/api/v2/patients/{id}/ccda` - GET - Retrieve CCDA ZIP file
- `/api/v1/documents` - POST - Submit clinical document (multipart upload)

**Base URLs:**
- Sandbox: `https://sandbox.particlehealth.com` (default)
- Production: `https://api.particlehealth.com` (requires explicit override via `PARTICLE_BASE_URL`)

## Data Storage

**Databases:**
- None - This is a client library, not a backend service
- No persistent data storage in this codebase
- Query results are downloaded to memory/disk by consuming scripts

**File Storage:**
- Local filesystem only - Downloaded CCDA ZIP files or data exports
- No cloud storage integration
- Example: `workflows/retrieve_data.py` writes CCDA data to local files

**Caching:**
- Token caching: In-memory token storage with proactive refresh
  - Location: `src/particle/core/auth.py` - `TokenManager` class
  - Mechanism: Extracts expiry from JWT `exp` claim, refreshes 10 minutes before expiry
- No response caching

## Authentication & Identity

**Auth Provider:**
- Custom Particle Health auth flow (proprietary, not standard OAuth2)
  - Implementation: `src/particle/core/auth.py` - `ParticleAuth` class
  - Flow: GET `/auth` with headers instead of POST with JSON body
  - Token format: JWT as plain text (not JSON)
  - Token TTL: 1 hour
  - Auto-refresh: Proactive refresh before expiry + reactive refresh on 401 responses

**Credential Management:**
- SecretStr type used for `client_secret` to prevent accidental logging
- Location: `src/particle/core/config.py`
- Never logged or exposed in debug output

## Monitoring & Observability

**Error Tracking:**
- None - No integration with external error tracking service (Sentry, etc.)
- Errors are raised as custom exceptions and must be handled by consuming code
- Exception hierarchy in `src/particle/core/exceptions.py`

**Logs:**
- Structured logging with structlog
  - Location: `src/particle/core/logging.py`
  - Format: JSON (production) or console (development)
  - PHI/PII redaction: Automatic via processor, redacts known sensitive keys and patterns
  - Redacted fields: `first_name`, `last_name`, `ssn`, `mrn`, `dob`, `phone`, `email`, `address`, postal codes, etc.
  - Patterns: SSN (XXX-XX-XXXX), DOB (YYYY-MM-DD), phone (XXX-XXX-XXXX), email, MRN
  - Log level configurable, defaults to INFO
  - No credentials logged (SecretStr prevents exposure)

**Logging Locations:**
- HTTP client: Debug logs for method, path in `src/particle/core/http.py`
- Auth: Token management implicit in flow
- Structured logging configured with `configure_logging()` in `src/particle/core/logging.py`

## CI/CD & Deployment

**Hosting:**
- Not applicable - This is a client library/toolkit, not a hosted service
- Customers run code locally or in their own infrastructure

**CI Pipeline:**
- None detected - No GitHub Actions, GitLab CI, or other CI/CD configuration in codebase
- Tests can be run with `pytest -v` (see `pyproject.toml`)

## Environment Configuration

**Required env vars:**
- `PARTICLE_CLIENT_ID` - API client identifier
- `PARTICLE_CLIENT_SECRET` - API credential
- `PARTICLE_SCOPE_ID` - Project/scope identifier

**Optional env vars:**
- `PARTICLE_BASE_URL` - API base URL (defaults to sandbox)
- `PARTICLE_TIMEOUT` - Request timeout in seconds (defaults to 30.0)

**Secrets location:**
- Environment variables (no secrets checked into repo)
- `.env` file support (not committed)
- SecretStr prevents exposure in logs and repr

## Webhooks & Callbacks

**Incoming:**
- None currently implemented
- Particle API supports webhook-based query completion notification (future feature noted in `src/particle/query/service.py` line 96-98)

**Outgoing:**
- None

**Query Status Polling:**
- Manual polling required: `QueryService.wait_for_query_complete()` in `src/particle/query/service.py`
- Exponential backoff: Initial 5s, max 30s, 1.5x multiplier
- Default timeout: 300 seconds (5 minutes)
- Handles transient 404s (resource briefly unavailable after submission)

## Error Handling & Retry Strategy

**Transient Errors (Retried):**
- Connection errors: `httpx.ConnectError`, `httpx.ConnectTimeout`
- Read/Write timeouts: `httpx.ReadTimeout`, `httpx.WriteTimeout`
- Pool timeouts: `httpx.PoolTimeout`
- Retry policy: Up to 3 attempts with exponential backoff + jitter (initial 1s, max 60s)
- Location: `src/particle/core/http.py` - `@retry` decorator on `_request_with_retry()`

**Non-Retried Errors:**
- 401/403: Authentication/authorization failed → `ParticleAuthError`
- 404: Resource not found → `ParticleNotFoundError`
- 422: Validation failed → `ParticleValidationError`
- 429: Rate limited → `ParticleRateLimitError` (includes `Retry-After` header if present)
- 5xx: Server errors (already retried) → `ParticleAPIError`
- 4xx: Other client errors → `ParticleAPIError`

**Exception Hierarchy:**
- Base: `ParticleError`
- Specific: `ParticleAuthError`, `ParticleAPIError`, `ParticleValidationError`, `ParticleRateLimitError`, `ParticleNotFoundError`, `ParticleQueryTimeoutError`, `ParticleQueryFailedError`
- Location: `src/particle/core/exceptions.py`

## Request Patterns

**Authentication:**
- All requests go through `ParticleAuth` (httpx Auth class)
- Token automatically included in `Authorization: Bearer {token}` header
- Auto-refresh on token expiry (proactive at 10-min buffer, reactive on 401)

**Headers:**
- Default: `accept: application/json`
- Automatic `content-type: application/json` for POST/PUT with JSON body
- No `content-type` set for multipart (httpx sets with boundary)
- Custom headers can be passed and merged

**Timeouts:**
- Global timeout: 30 seconds (configurable via `PARTICLE_TIMEOUT`)
- Applies to all HTTP operations including token refresh

**Content Handling:**
- JSON responses parsed and returned as dict
- Non-JSON responses (CCDA ZIP): returned as `{"_raw_content": bytes, "_content_type": string}`
- Empty responses (204 No Content): returned as empty dict `{}`
- Graceful degradation when server claims JSON but body is binary

---

*Integration audit: 2026-02-07*
