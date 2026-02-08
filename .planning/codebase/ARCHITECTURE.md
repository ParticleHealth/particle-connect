# Architecture

**Analysis Date:** 2026-02-07

## Pattern Overview

**Overall:** Layered service architecture with HTTP adapter pattern

**Key Characteristics:**
- Clear separation between infrastructure (core) and domain services (query, patient, document)
- HTTP client abstraction at the I/O boundary with automatic token management
- Service objects expose domain operations independent of HTTP transport details
- Pydantic models for type-safe request/response validation
- Structured logging with PHI redaction for healthcare compliance

## Layers

**Infrastructure/Core Layer:**
- Purpose: Provides HTTP client, authentication, configuration, and cross-cutting concerns
- Location: `src/particle/core/`
- Contains: `config.py`, `auth.py`, `http.py`, `exceptions.py`, `logging.py`
- Depends on: External libraries (httpx, pydantic, tenacity, structlog, PyJWT)
- Used by: All service layers (query, patient, document)

**Domain Service Layer:**
- Purpose: Exposes business operations for each API domain via service classes
- Location: `src/particle/{query,patient,document}/`
- Contains: Service classes and domain models
- Depends on: Infrastructure layer (ParticleHTTPClient)
- Used by: Workflows and quick-start examples

**Application Layer:**
- Purpose: Executable workflows and quick-start demonstrations
- Location: `workflows/` (production-like patterns), `quick-starts/python/` (minimal examples)
- Contains: CLI scripts that orchestrate services
- Depends on: Service layer classes
- Used by: End customers for integration

## Data Flow

**Query Submission and Polling:**

1. Application calls `QueryService.submit_query(particle_patient_id, purpose_of_use)`
2. Service validates parameters and builds JSON payload
3. Service calls `client.request("POST", "/api/v2/patients/{id}/query", json=payload)`
4. HTTP client applies authentication (token refresh if needed), executes request with retry logic
5. Response mapped to `QuerySubmitResponse` via Pydantic validation
6. Application calls `QueryService.wait_for_query_complete(particle_patient_id, timeout_seconds, poll_interval)`
7. Service polls status endpoint with exponential backoff (1.5x multiplier, capped at max_poll_interval)
8. Polling continues until status is COMPLETE, PARTIAL, FAILED, or timeout exceeded
9. Application retrieves data via `get_ccda()`, `get_fhir()`, or `get_flat()`
10. HTTP client handles non-JSON responses (ZIP files) by returning raw bytes

**Patient Registration:**

1. Application builds `PatientRegistration` object with demographic data
2. Pydantic validates all fields before API call
3. Application calls `PatientService.register(patient)`
4. Service serializes patient object and calls `client.request("POST", "/api/v2/patients", json=payload)`
5. HTTP client executes with authentication and error handling
6. Response mapped to `PatientResponse` containing `particle_patient_id`
7. Idempotency: Same patient_id + same demographics = update (success); same patient_id + different demographics = error

**Document Submission:**

1. Application prepares document content and creates `DocumentSubmission` object
2. Service calls `client.request("POST", "/api/v1/documents", files={...})`
3. HTTP client handles multipart upload with metadata (JSON) + file content
4. Response mapped to `DocumentResponse`

**State Management:**

- **Token state:** Managed by `TokenManager` within `ParticleAuth`. Proactively refreshes 10 minutes before expiry (1-hour tokens). Stores token and expiry time internally.
- **Configuration state:** `ParticleSettings` loaded from environment variables at application startup. Immutable after initialization.
- **HTTP client state:** `ParticleHTTPClient` maintains persistent httpx.Client for connection pooling. Context manager ensures cleanup.
- **Session scope:** Each workflow creates one `ParticleHTTPClient` and reuses it across multiple service calls.

## Key Abstractions

**ParticleHTTPClient:**
- Purpose: Unified HTTP interface with authentication, retry, and error handling
- Examples: `src/particle/core/http.py`
- Pattern: Adapter + Facade. Wraps httpx.Client and ParticleAuth. Exposes a single `request()` method for all HTTP operations.

**ParticleAuth:**
- Purpose: HTTPX Auth implementation for JWT token lifecycle management
- Examples: `src/particle/core/auth.py`
- Pattern: HTTPX Auth flow handler. Implements proactive refresh (before expiry) and reactive refresh (on 401). Yields requests and processes responses in a generator-based auth flow.

**Service Layer:**
- Purpose: Domain-specific operations (QueryService, PatientService, DocumentService)
- Examples: `src/particle/query/service.py`, `src/particle/patient/service.py`, `src/particle/document/service.py`
- Pattern: Service locator. Encapsulates API endpoint knowledge and business logic (e.g., polling with exponential backoff in `wait_for_query_complete`).

**Pydantic Models:**
- Purpose: Request/response validation and serialization
- Examples: `src/particle/query/models.py`, `src/particle/patient/models.py`, `src/particle/document/models.py`
- Pattern: Data Transfer Objects (DTOs) with validation. Enums for fixed-value fields (QueryStatus, PurposeOfUse, Gender, DocumentType, MimeType). Mapping aliases handle API field name differences (e.g., API returns `state`, model field is `query_status`).

**Exception Hierarchy:**
- Purpose: Type-safe error handling with context-specific information
- Examples: `src/particle/core/exceptions.py`
- Pattern: Inheritance tree rooted at `ParticleError`. Specific subclasses capture status codes, retry info, resource identifiers, and domain context.

## Entry Points

**Workflow Scripts:**
- Location: `workflows/register_patient.py`, `workflows/submit_query.py`, `workflows/submit_document.py`, `workflows/retrieve_data.py`
- Triggers: Command-line invocation with arguments
- Responsibilities: Parse CLI args, load config, instantiate services, orchestrate business operations, handle errors, print results

**Quick-Start Scripts:**
- Location: `quick-starts/python/submit_query.py`, `quick-starts/python/register_patient.py`, `quick-starts/python/retrieve_data.py`
- Triggers: Command-line invocation
- Responsibilities: Minimal, dependency-free examples. Demonstrate core flows using only httpx + stdlib. No service layer abstraction.

**Python Library API:**
- Location: `src/particle/__init__.py` (package entry point)
- Triggers: `from particle import ...`
- Responsibilities: Export service classes and models for customer code to import and use programmatically

## Error Handling

**Strategy:** Exceptions propagate from HTTP layer → service layer → application layer. Applications catch specific exception types and handle accordingly.

**Patterns:**
- **Authentication errors (401/403):** `ParticleAuthError` raised by `ParticleHTTPClient`. Handled in workflows with explicit message.
- **Validation errors (422):** `ParticleValidationError` contains field-level errors from API. Application iterates over `exc.errors` list for detail.
- **Rate limiting (429):** `ParticleRateLimitError` includes `retry_after` seconds from header. Application can sleep and retry.
- **Transient failures (timeouts, connection errors):** Retried automatically by tenacity decorator in `_request_with_retry`. Max 3 attempts with exponential backoff (1s initial, 60s max, ±5s jitter).
- **Query-specific timeouts:** `ParticleQueryTimeoutError` raised by polling loop if deadline exceeded. Application exits or retries later.
- **Query failures:** `ParticleQueryFailedError` raised when API returns FAILED status with error_message.

## Cross-Cutting Concerns

**Logging:** Structured logging via `structlog`. Call `configure_logging()` at application startup. Logs are emitted via `logger.debug()`, `logger.info()` calls in HTTP client and services. PHI redaction enabled by default.

**Validation:** Pydantic models validate at construction time. Request models validated before serialization. Response models validated after deserialization. API payloads validated server-side; 422 errors returned to client.

**Authentication:** JWT token lifecycle managed by `ParticleAuth` (proactive refresh at 600s buffer) and `TokenManager`. All requests automatically include `Authorization: Bearer {token}` header. Token acquisition uses custom Particle header auth (not standard OAuth2).

**Retry Logic:** Transient errors (connection timeouts, read timeouts, pool timeouts) retried with exponential backoff via tenacity. Max 3 attempts, 1s initial wait, 60s max, ±5s jitter. Non-transient errors (4xx except retry-able ones) not retried.

**PHI Redaction:** Automatic redaction of sensitive fields (ssn, date_of_birth, phone, email, names) in all logs. Pattern-based redaction for PHI format strings. Processor runs before log rendering to ensure no exposure.

---

*Architecture analysis: 2026-02-07*
