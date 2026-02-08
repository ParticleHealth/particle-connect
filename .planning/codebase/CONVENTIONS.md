# Coding Conventions

**Analysis Date:** 2026-02-07

## Naming Patterns

**Files:**
- Lowercase with underscores for modules: `config.py`, `logging.py`, `exceptions.py`, `auth.py`, `http.py`
- Lowercase with underscores for packages: `core/`, `patient/`, `query/`, `document/`
- Service modules named `service.py`, model modules named `models.py`
- Workflow scripts: lowercase with underscores, e.g., `retrieve_data.py`, `submit_document.py`, `register_patient.py`

**Functions:**
- Lowercase with underscores (snake_case)
- Private functions prefixed with single underscore: `_redact_value()`, `_redact_dict()`, `_build_token_request()`, `_update_token()`
- Public methods without prefix: `needs_refresh()`, `update()`, `configure_logging()`, `get_logger()`
- Boolean methods use `needs_` or `is_` prefix: `needs_refresh()`, `is_` pattern not found but boolean convention followed

**Variables:**
- Lowercase with underscores for module-level: `REDACT_KEYS`, `PHI_PATTERNS`
- Uppercase for constants that are module-wide and immutable: `REDACT_KEYS: set[str]`, `PHI_PATTERNS: dict[str, re.Pattern[str]]`
- Lowercase snake_case for instance variables: `self._token`, `self._expiry`, `self._config`, `self._client`
- Descriptive names for function parameters: `particle_patient_id`, `purpose_of_use`, `timeout_seconds`, `json`, `params`, `headers`

**Types:**
- PascalCase for classes: `ParticleSettings`, `ParticleError`, `ParticleAuth`, `TokenManager`, `DocumentService`, `PatientService`, `QueryService`
- PascalCase for Enums: `DocumentType`, `MimeType`, `Gender`, `QueryStatus`, `PurposeOfUse`
- Exceptions follow pattern: `ParticleError`, `ParticleAuthError`, `ParticleAPIError`, `ParticleValidationError`, `ParticleRateLimitError`, `ParticleNotFoundError`, `ParticleQueryTimeoutError`, `ParticleQueryFailedError`

## Code Style

**Formatting:**
- Tool: ruff (configured in `pyproject.toml`)
- Line length: 100 characters
- Target version: Python 3.11+
- Uses `from __future__ import annotations` for forward references and modern type hint syntax

**Linting:**
- Tool: ruff with rule set E, F, I, W
  - `E`: PEP 8 errors
  - `F`: PyFlakes (undefined names, unused imports)
  - `I`: isort-compatible import sorting
  - `W`: PEP 8 warnings
- Configuration in `pyproject.toml`:
  ```toml
  [tool.ruff]
  line-length = 100
  target-version = "py311"

  [tool.ruff.lint]
  select = ["E", "F", "I", "W"]
  ```

**Quotes:**
- Double quotes preferred (seen throughout codebase): `"string"`
- Single quotes used in rare cases for pattern strings: `'ssn'` in dictionary keys

**Semicolons:**
- No semicolons used; Python convention followed

## Import Organization

**Order:**
1. `from __future__ import annotations` (always first for type hints)
2. Standard library imports: `import json`, `import sys`, `import os`, `import logging`, `import re`, `from datetime import datetime, timedelta, timezone`, `from typing import Any, Generator`
3. Third-party imports: `import httpx`, `import structlog`, `import pydantic`, `from tenacity import ...`, `import jwt`
4. Local/relative imports: `from .config import`, `from .exceptions import`, `from particle.core import`, `from particle.query import`

**Path Aliases:**
- Explicit relative imports within packages: `from .auth import ParticleAuth, TokenManager`
- Absolute imports for cross-package dependencies: `from particle.core import ParticleHTTPClient`
- Not using @ aliases or path shortcuts; all imports are explicit

**Barrel Files:**
- Each package uses `__init__.py` with explicit `__all__` export list
- Example from `particle/core/__init__.py`:
  ```python
  __all__ = [
      "ParticleSettings",
      "ParticleAuth",
      "TokenManager",
      "ParticleHTTPClient",
      "ParticleError",
      # ... etc
  ]
  ```
- Imports grouped by concern: Config, Auth, HTTP, Exceptions, Logging

## Error Handling

**Patterns:**
- Custom exception hierarchy with base class `ParticleError`
- Specific exception types for different error scenarios:
  - `ParticleAuthError`: Authentication failures (invalid credentials, 401, 403)
  - `ParticleAPIError`: API errors with status code tracking and response body
  - `ParticleValidationError`: 422 validation failures with error list
  - `ParticleRateLimitError`: 429 rate limits with optional retry_after
  - `ParticleNotFoundError`: 404 errors with resource type and ID
  - `ParticleQueryTimeoutError`: Query polling timeouts
  - `ParticleQueryFailedError`: Query processing failures on server

**Exception constructor pattern:**
```python
class ParticleError(Exception):
    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code
        super().__init__(message)
```

**Error context preservation:**
- All custom exceptions store relevant context (status code, response body, resource ID, retry_after)
- HTTP client maps status codes to specific exceptions in `_handle_response()`
- Retry decorator in `_request_with_retry()` only retries on `RETRYABLE_EXCEPTIONS` (timeouts and connection errors)

## Logging

**Framework:** structlog with PHI redaction processor

**Configuration:**
- Function: `configure_logging(json_output=False, enable_redaction=True, log_level=logging.INFO)`
- Processors ordered: contextvars → add_log_level → TimeStamper → redact_phi → JSONRenderer or ConsoleRenderer
- Default: Console output with human-readable format, production should use `json_output=True`

**PHI Redaction:**
- Processor function: `redact_phi(logger, method_name, event_dict)` must run before rendering
- Key-based redaction: Any value with key in `REDACT_KEYS` becomes `[REDACTED]`
  - Includes: first_name, last_name, ssn, mrn, patient_id, date_of_birth, address fields, phone, email
- Pattern-based redaction: Strings matching PHI_PATTERNS redacted with type-specific replacement
  - Patterns: SSN (XXX-XX-XXXX), DOB (YYYY-MM-DD), phone, email, MRN
- Recursive redaction: Processes nested dicts and lists

**Patterns:**
- All loggers obtained via `structlog.get_logger(__name__)` or `get_logger()` wrapper
- Logging only endpoint, status, latency, method in HTTP client: `self._logger.debug("request", method=method, path=path)`
- No sensitive data logged by design (secrets/tokens/PHI redacted automatically)

## Comments

**When to Comment:**
- Non-obvious algorithms or complex logic paths
- API-specific quirks and authentication flows (e.g., Particle's custom GET /auth instead of OAuth2)
- HIPAA compliance requirements and security decisions
- Future improvements marked with `# Future:` prefix

**Examples from codebase:**
```python
# Particle uses a custom auth flow (NOT standard OAuth2):
# - GET /auth with custom headers (client-id, client-secret, scope)
# - Returns JWT token as plain text
# - Token TTL is 1 hour

# We decode without signature verification because we just need
# the expiry time for refresh logic, not security validation.

# Server claimed JSON but body is binary (e.g., CCDA ZIP)

# Future: This could be replaced by webhook-based notification.
```

**JSDoc/Docstring Pattern:**
- Google-style docstrings with triple quotes
- Format:
  ```python
  """One-line summary.

  Optional longer description explaining context and behavior.

  Args:
      param_name: Description and type hints (types in signature)

  Returns:
      Type and description

  Raises:
      ExceptionType: When/why this is raised
  """
  ```

**Examples:**
- `ParticleSettings` class docstring explains config via env vars with PARTICLE_ prefix
- `ParticleAuth.auth_flow()` explains generator-based HTTPX flow and retry strategy
- Service methods include Args, Returns, Raises sections

## Function Design

**Size:**
- Methods focused on single responsibility: registration, query submission, status polling, data retrieval
- Longest method is `wait_for_query_complete()` at ~50 lines with exponential backoff logic

**Parameters:**
- Explicit over implicit: `particle_patient_id`, `timeout_seconds`, `poll_interval`, `max_poll_interval`
- Optional parameters with sensible defaults: `purpose_of_use: PurposeOfUse = PurposeOfUse.TREATMENT`
- `**kwargs` used sparingly: `_request_with_retry(**kwargs)` for flexible HTTP method args

**Return Values:**
- Pydantic models for structured responses: `QueryResponse.model_validate(response)`
- Dict for unstructured data: `dict[str, Any]` for JSON responses
- Bytes for binary: `bytes` for CCDA ZIP files
- None for side-effect only operations: `close()`, `clear()`

## Module Design

**Exports:**
- Each package uses explicit `__all__` list in `__init__.py`
- All public APIs documented and exported
- Private modules (starting with _) not used; internal functions use `_` prefix instead

**Barrel Files:**
- `particle/core/__init__.py`: Exports config, auth, HTTP, exceptions, logging utilities
- `particle/patient/__init__.py`: Exports PatientService, PatientRegistration, Gender, PatientResponse
- `particle/query/__init__.py`: Exports QueryService, QueryStatus, PurposeOfUse, query models
- `particle/document/__init__.py`: Exports DocumentService, document models

**Service Layer Pattern:**
- Each service (`PatientService`, `QueryService`, `DocumentService`) wraps `ParticleHTTPClient`
- Services validate inputs via Pydantic models before HTTP calls
- Services map HTTP responses to response models
- Services convert low-level HTTP errors to domain-specific exceptions

---

*Convention analysis: 2026-02-07*
