# Codebase Concerns

**Analysis Date:** 2026-02-07

## Tech Debt

**Bare Exception Handler in HTTP Response Processing:**
- Issue: `except Exception:` swallows all exceptions without logging, making debugging difficult
- Files: `src/particle/core/http.py:166`
- Impact: JSON decode failures or other unexpected errors in response handling are silently converted to empty strings in error details
- Fix approach: Replace with specific exception types (ValueError, UnicodeDecodeError) and log the original error before handling

**Query Polling via Polling Instead of Webhooks:**
- Issue: Long-polling with exponential backoff is the current pattern; webhooks would reduce latency and API calls
- Files: `src/particle/query/service.py:96-137`
- Impact: Higher latency for query completion detection, unnecessary API calls during polling intervals
- Fix approach: Add webhook-based notification support as alternative to polling; maintain polling as fallback
- Priority: Medium (impacts real-time responsiveness)

**Hard-coded Default Patient Data in Workflow Example:**
- Issue: Contains real-looking SSN (123-45-6789) and phone number in default demo data
- Files: `workflows/register_patient.py:53-65`
- Impact: While data is clearly demo data, this could be copy-pasted into production code accidentally
- Fix approach: Use obviously fake/redacted demo data (e.g., "123-45-6789" → "[DEMO-SSN]" or use actual non-sensitive test data)

## Known Limitations

**Sandbox Environment Limitations:**
- Issue: FHIR endpoint (`/api/v2/patients/{id}/fhir`) is not available in sandbox, only in production
- Files: `README.md:128`, `workflows/retrieve_data.py:30`
- Impact: Cannot fully test FHIR workflows without production access
- Mitigation: Documentation clearly notes this limitation; flat and CCDA formats work in both environments

**Narrow Validation for Phone and SSN Formats:**
- Issue: Validation allows only US formats (10-digit phone, XXX-XX-XXXX SSN)
- Files: `src/particle/patient/models.py:75-106`
- Impact: Non-US patients or international phone numbers cannot be registered; extension handling not supported
- Fix approach: Add optional country_code field to support international formats, document US-only current state

## Security Considerations

**PHI Redaction in Logging:**
- Risk: Without careful logging discipline, sensitive data could leak into logs
- Files: `src/particle/core/logging.py:1-150`
- Current mitigation: Comprehensive redaction processor with pattern matching and key-based filtering; redaction is enabled by default
- Recommendations:
  - Continue mandatory redaction in production (redaction enforced at processor level, happens before rendering)
  - Add structured tests for new PHI fields if patient schema expands
  - Document disable_redaction=True warnings in code comments (currently line 112)

**Credentials in Environment Variables:**
- Risk: PARTICLE_CLIENT_SECRET and PARTICLE_SCOPE_ID passed via env vars; could appear in logs or process listings
- Files: `src/particle/core/config.py:1-42`
- Current mitigation: SecretStr field prevents exposure in repr(); config not logged
- Recommendations:
  - Document that client_secret should never be logged (already followed)
  - Consider adding a check to raise error if credentials are passed via .env file in production (currently allows env file loading)

**Token Exposure Risk:**
- Risk: JWT tokens could leak in exception messages or logs
- Files: `src/particle/core/auth.py:155-166`, `src/particle/core/http.py:122`
- Current mitigation: Tokens are not logged; only endpoints/status codes are logged
- Recommendations:
  - Verify that httpx auth flow logging is disabled (check httpx configuration)
  - Consider masking tokens in auth error messages (currently shows "Token request failed" without token details)

**Multipart File Upload Error Handling:**
- Risk: File submission with potentially large binary files could fail without retry
- Files: `src/particle/document/service.py:19-52`
- Current mitigation: HTTP client has retry logic for transient errors (ConnectError, timeout, etc.)
- Issue: 429 (rate limit) is retried by client, but 422 (validation) raises immediately without retry
- Recommendations:
  - Document that document submission should validate file size/format before API call
  - Consider adding configurable retry for validation errors in document service if Particle API has transient validation issues

## Performance Bottlenecks

**Query Polling Efficiency:**
- Problem: Default polling interval starts at 5s and caps at 30s; for queries taking 5+ minutes, this wastes API quota
- Files: `src/particle/query/service.py:85-137`
- Cause: Fixed multiplier (1.5x) and max cap (30s) not configurable per use case
- Improvement path:
  1. Add timeout_strategy parameter to allow different polling curves (conservative, moderate, aggressive)
  2. Add jitter to avoid thundering herd if multiple clients poll simultaneously
  3. Implement webhook fallback to eliminate polling entirely

**Token Refresh Proactive Buffer:**
- Problem: Default 600-second (10-minute) refresh buffer means frequent token requests for long-running operations
- Files: `src/particle/core/auth.py:58-72`, `src/particle/core/config.py:32-35`
- Cause: Conservative buffer chosen for reliability, but increases HTTP calls
- Improvement path:
  - Document actual token lifetime behavior from Particle API
  - Consider shorter buffer (5 minutes) if tokens are truly 1 hour
  - Add metric collection to measure how often refresh actually needed vs. preemptive

## Fragile Areas

**Patient Registration Idempotency Unclear:**
- Files: `workflows/register_patient.py:33-36`
- Why fragile: Documentation says idempotent re-registration works with same patient_id + demographics, but error handling only catches ParticleAPIError
  - If API returns 409 Conflict (not documented), it will propagate to caller
  - Overlay detection (duplicate with different data) behavior not explicitly tested
- Safe modification:
  - Add specific test for 409/conflict scenarios
  - Document expected status codes from re-registration endpoint
  - Add defensive check for ParticleAPIError with status_code==409

**Response Parsing for Binary CCDA:**
- Files: `src/particle/core/http.py:138-151`, `src/particle/query/service.py:139-166`
- Why fragile:
  - Assumes non-JSON responses always return `{"_raw_content": bytes}` structure
  - If API changes content-type header or response format changes, binary extraction fails
  - No validation that returned content is actually valid ZIP
- Safe modification:
  - Add CCDA validation after retrieval (attempt to open as ZIP before returning)
  - Document expected response structure in docstrings
  - Add specific test with mock CCDA response

**Query Status Field Parsing:**
- Files: `src/particle/query/models.py`, `src/particle/query/service.py:70-83`
- Why fragile: Relies on exact enum values (PENDING, IN_PROGRESS, COMPLETE, PARTIAL, FAILED)
  - If Particle API introduces new status (e.g., EXPIRED, CANCELLED), code silently continues
  - error_message field may be missing when status is not FAILED (nullable but not always present)
- Safe modification:
  - Add validation to reject unknown status values
  - Add tests for edge cases (missing error_message on FAILED, extra fields in response)
  - Document status lifecycle and when error_message is populated

**Test Coverage Gaps:**

**Missing Integration Tests:**
- What's not tested: Actual network interactions (tests use fixtures and mocks)
- Files: `tests/test_core_integration.py:1-210`
- Risk: Auth flow failures, rate limiting, server errors not tested end-to-end
- Priority: High (auth and retry logic are critical)
- Mitigation: Document that integration tests against sandbox require credentials and network access; recommend running against mock server

**Missing Endpoint-Specific Tests:**
- What's not tested: Document submission multipart form handling, CCDA binary response parsing
- Files: `src/particle/document/service.py`, CCDA retrieval in `src/particle/query/service.py`
- Risk: Silent failures if API changes multipart field names or response format
- Priority: High (document and CCDA handling are error-prone)

**Missing Error Scenario Tests:**
- What's not tested: 401 token refresh retry, 429 rate limit with Retry-After header, 422 validation with detailed errors
- Files: `src/particle/core/http.py:_handle_response`, `src/particle/core/auth.py:auth_flow`
- Risk: Error paths may fail undetected when actually called
- Priority: High (these are the exception paths that fail in production)

## Dependencies at Risk

**tenacity for Retry Logic:**
- Risk: Custom retry configuration could diverge from Particle API's recommended patterns
- Current state: Fixed 3 attempts, exponential backoff (initial=1s, max=60s)
- Impact: May retry too few times for intermittent failures, or too many times for non-transient errors
- Migration plan: Document retry configuration; if Particle publishes recommended retry strategy, align with it

**PyJWT for Token Decoding:**
- Risk: Decoding without signature verification for expiry extraction
- Current state: `jwt.decode(token, options={"verify_signature": False})` in `src/particle/core/auth.py:51`
- Impact: Tokens are verified on backend, not locally; this is correct for extracting expiry but could be confusing
- Recommendations:
  - Add comment explaining why signature verification is skipped (expiry extraction only, not validation)
  - Document that token freshness is enforced by Particle API 401 responses, not by client verification

**pydantic and pydantic-settings Lock-in:**
- Risk: Heavy reliance on Pydantic v2 features; migration to other validation frameworks would be large
- Current state: BaseModel subclasses with field_validator, SecretStr, ConfigDict
- Impact: High switching cost if Pydantic major version breaks compatibility
- Mitigation: Use only stable Pydantic v2 APIs; avoid experimental features

## Missing Critical Features

**No Request/Response Logging for Debugging:**
- Problem: Errors include response status and body, but request details (headers, params) not logged
- Blocks: Diagnosing issues like missing required headers or incorrect endpoint versions
- Workaround: Enable httpx debug logging, but not integrated with particle logging
- Fix: Add debug-level logging of request/response details (request_id, endpoint, response time)

**No Distributed Tracing / Correlation ID Support:**
- Problem: No way to trace a request through logs across client and server
- Blocks: Multi-step workflows (register → query → retrieve) hard to debug when any step fails
- Workaround: Wrap operations in application-level tracing, but not built into SDK
- Fix: Add optional correlation_id parameter, pass through headers and logs

**No Async Support:**
- Problem: All APIs are synchronous; blocking I/O limits concurrent operations
- Blocks: Batch processing (register multiple patients, submit queries in parallel) requires manual threading
- Workaround: Use ProcessPoolExecutor or threads, manage token refresh across workers manually
- Priority: Low (most customer use cases are single-threaded, but batch processing would benefit)

## Scaling Limits

**Token Refresh Thread Safety:**
- Current capacity: Single-threaded token manager; multiple threads could trigger simultaneous refresh
- Limit: Breaks when clients spawn multiple threads/processes
- Scaling path:
  1. Add thread-safe locking in TokenManager.update() and auth_flow()
  2. Document that HTTP client is not thread-safe (httpx.Client is thread-safe but httpx.Auth is not)
  3. Consider process-safe token caching if multiprocessing is needed

**Polling Timeout Accuracy:**
- Current capacity: Deadline calculation uses time.time(); accurate to ~1 second
- Limit: For timeouts < 10 seconds, jitter from time.sleep() could exceed requested timeout
- Scaling path:
  - Switch to time.monotonic() for deadline calculation (immune to system clock adjustments)
  - Add explicit deadline check before each sleep (currently only checked at loop start)

## Documentation Gaps

**Particle API Behavior Not Documented:**
- Missing: Expected retry behavior (does Particle API use exponential backoff recommendation?)
- Missing: Rate limit headers (what is X-RateLimit-Remaining format?)
- Missing: Query completion webhook support (if available)
- Impact: Conservative defaults chosen without certainty of API behavior
- Fix: Add `/docs/api-behavior.md` with collected knowledge from support interactions

**Configuration Migration Guide Missing:**
- Missing: How to switch from sandbox to production
- Missing: What credentials are needed vs. optional
- Missing: How scope_id relates to customer tenants
- Impact: Customers may misconfigure environment
- Fix: Add clear setup instructions per environment (sandbox vs production)

---

*Concerns audit: 2026-02-07*
