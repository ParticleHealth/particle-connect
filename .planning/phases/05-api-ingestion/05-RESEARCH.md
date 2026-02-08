# Phase 5: API Ingestion - Research

**Researched:** 2026-02-08
**Domain:** HTTP API client (stdlib), authentication, retry with exponential backoff, Particle Health API integration
**Confidence:** HIGH

## Summary

Phase 5 replaces the stubbed `--source api` CLI path with a working Particle Health API client that authenticates, calls GET Flat, handles errors with retries, and feeds the resulting JSON into the same parser/schema/loader pipeline already built in Phases 1-4. The critical design constraint is that the observatory package uses **stdlib-only dependencies** (no httpx, no tenacity, no pydantic) -- all networking must use `urllib.request` from the standard library.

The existing `particle-health-starters` codebase provides a reference implementation using httpx + tenacity + pydantic with full auth flow, retry, and error handling. Phase 5 must replicate this capability using only stdlib + the existing observatory dependencies (psycopg, typer, python-dotenv, rich). The Particle API auth flow is non-standard (GET /auth with custom headers returning plain-text JWT), and the GET Flat endpoint returns the same JSON dict structure that `load_flat_data()` already parses from files.

The integration point is clean: the API client returns a `dict[str, list[dict]]` that feeds directly into `inspect_schema()` and `load_all()` -- no changes needed to the downstream pipeline. The main new code is: (1) an API client module with auth + retries + timeout, and (2) a thin adapter in `cli.py` that calls the API client instead of reading a file when `--source api` is selected.

**Primary recommendation:** Build a single `api_client.py` module using `urllib.request` with manual retry loop (exponential backoff + jitter), JWT token management via stdlib `json` module (no PyJWT needed -- just decode the base64 payload for expiry), and configurable timeout. Wire it into `cli.py` by replacing the stub with a call that returns the same dict shape as `load_flat_data()`.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| urllib.request | stdlib (Python 3.11+) | HTTP client for API calls | Project constraint: stdlib-only dependencies. urllib.request handles HTTPS, custom headers, timeouts natively. |
| json | stdlib | JSON parsing of API responses | Already used throughout the project for flat data parsing. |
| time | stdlib | Sleep for retry backoff delays | Standard approach for retry timing. |
| random | stdlib | Jitter for backoff calculations | Prevents retry storms when multiple clients hit rate limits simultaneously. |
| base64 | stdlib | JWT payload decoding (for token expiry) | Decodes JWT middle segment to extract `exp` claim. Avoids PyJWT dependency. |
| logging | stdlib | Structured operational logging | Already used throughout the project. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | >=1.0.0 | .env loading for API credentials | Already a required dependency. Loads PARTICLE_* env vars from .env file. |
| typer | >=0.21.0 | CLI integration | Already a required dependency. Existing `--source api` option needs wiring. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| urllib.request (stdlib) | httpx | httpx is the existing choice in particle-health-starters with superior DX (auth flow, retry via tenacity). However, observatory has a strict stdlib-only policy for HTTP. Adding httpx would pull in httpcore, anyio, sniffio, certifi, h11 -- 6+ transitive dependencies. |
| Manual retry loop | tenacity | tenacity provides clean decorator-based retry with exponential backoff. However, the retry logic here is straightforward (3-5 retries, backoff on 429/5xx) and easily implemented in ~30 lines of stdlib code. |
| base64 JWT decoding | PyJWT | PyJWT provides full JWT decode with signature verification. We only need the `exp` claim for proactive refresh timing -- no signature verification needed (same approach as particle-health-starters). base64 + json is sufficient. |
| os.environ for config | pydantic-settings | pydantic-settings provides validated, typed configuration. Observatory uses raw os.environ.get() throughout -- matching that pattern is more consistent. |

**No new dependencies required.** Everything needed is stdlib or already in pyproject.toml.

## Architecture Patterns

### Recommended Module Structure

```
src/observatory/
    api_client.py     # NEW: Particle API client (auth, retries, GET Flat)
    cli.py            # MODIFIED: Wire --source api to api_client
    config.py         # MODIFIED: Add PARTICLE_* env var loading
    parser.py         # UNCHANGED: load_flat_data() still used for file mode
    schema.py         # UNCHANGED
    loader.py         # UNCHANGED
    bq_loader.py      # UNCHANGED
    normalizer.py     # UNCHANGED
    quality.py        # UNCHANGED
```

### Pattern 1: Stdlib HTTP Client with Retry and Backoff

**What:** A self-contained API client class using `urllib.request` with manual retry loop implementing exponential backoff + jitter for 429 and 5xx responses, configurable timeout, and custom header support.

**When to use:** For all Particle Health API calls (auth token acquisition and GET Flat data retrieval).

**Why this pattern:** The observatory follows stdlib-only for I/O operations. urllib.request is the only stdlib HTTP client. The retry logic is simple enough (linear code path, 3-5 retries, 2 retryable conditions) that a decorator library is unnecessary.

**Example:**
```python
# Source: Python stdlib docs + AWS exponential backoff best practices
import json
import logging
import random
import time
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

# Retryable HTTP status codes
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _request_with_retry(
    url: str,
    headers: dict[str, str],
    timeout: float = 30.0,
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 60.0,
    backoff_jitter: float = 1.0,
) -> bytes:
    """Make an HTTP GET request with retry on 429/5xx."""
    req = urllib.request.Request(url, headers=headers, method="GET")

    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            if e.code not in RETRYABLE_STATUS_CODES or attempt == max_retries:
                raise
            # Calculate backoff: base * 2^attempt + jitter
            backoff = min(initial_backoff * (2 ** attempt), max_backoff)
            jitter = random.uniform(0, backoff_jitter)
            wait = backoff + jitter

            # Respect Retry-After header if present (429 responses)
            retry_after = e.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = max(wait, float(retry_after))
                except ValueError:
                    pass

            logger.warning(
                "Request failed (HTTP %d), retrying in %.1fs (attempt %d/%d)",
                e.code, wait, attempt + 1, max_retries,
            )
            time.sleep(wait)
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == max_retries:
                raise
            backoff = min(initial_backoff * (2 ** attempt), max_backoff)
            jitter = random.uniform(0, backoff_jitter)
            wait = backoff + jitter
            logger.warning(
                "Request failed (%s), retrying in %.1fs (attempt %d/%d)",
                e, wait, attempt + 1, max_retries,
            )
            time.sleep(wait)
    # Should not reach here, but satisfy type checker
    raise RuntimeError("Retry loop exhausted")
```

### Pattern 2: JWT Token Management Without PyJWT

**What:** Extract the `exp` claim from a JWT token by base64-decoding the payload segment (middle part). No signature verification needed -- we only need the expiry time for proactive refresh, matching the approach used in `particle-health-starters/src/particle/core/auth.py`.

**When to use:** After acquiring a token from GET /auth, to determine when to refresh.

**Why this pattern:** The existing starters use `jwt.decode(token, options={"verify_signature": False})` which is PyJWT just for unverified decode. The stdlib equivalent is ~10 lines of base64 + json, avoiding a new dependency.

**Example:**
```python
# Source: JWT RFC 7519 structure (header.payload.signature, base64url-encoded)
import base64
import json
from datetime import datetime, timezone


def _decode_jwt_expiry(token: str) -> datetime | None:
    """Extract expiry time from JWT without signature verification.

    JWT structure: header.payload.signature (base64url-encoded).
    We only need the payload 'exp' claim for refresh timing.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        # base64url decode the payload (second segment)
        payload_b64 = parts[1]
        # Add padding if needed (base64url omits trailing =)
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes)
        if "exp" in payload:
            return datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        return None
    except (ValueError, KeyError, json.JSONDecodeError):
        return None
```

### Pattern 3: Particle Auth Flow (Custom Non-OAuth2)

**What:** Particle uses a custom auth flow: `GET /auth` with custom headers (`client-id`, `client-secret`, `scope`) returning a plain-text JWT. This is NOT standard OAuth2 client credentials (which uses POST with form-encoded body).

**When to use:** Before making any API call. Token is valid for 1 hour; refresh proactively at ~50 minutes.

**Why this matters:** The auth flow is documented in `particle-health-starters/src/particle/core/auth.py` and confirmed by Particle's official docs. The observatory must replicate this exactly.

**Key details from existing codebase:**
- Method: `GET`
- URL: `{base_url}/auth`
- Headers: `client-id`, `client-secret`, `scope`, `accept: text/plain`
- Response: plain text JWT (not JSON)
- Token TTL: 1 hour
- Refresh buffer: 600 seconds (10 minutes before expiry)
- Sandbox URL: `https://sandbox.particlehealth.com`
- Production URL: `https://api.particlehealth.com`

**Example:**
```python
def _acquire_token(self) -> str:
    """Acquire JWT from Particle auth endpoint."""
    headers = {
        "client-id": self._client_id,
        "client-secret": self._client_secret,
        "scope": self._scope_id,
        "accept": "text/plain",
    }
    req = urllib.request.Request(
        f"{self._base_url}/auth",
        headers=headers,
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=self._timeout) as response:
        token = response.read().decode("utf-8").strip()
    if not token:
        raise ValueError("Empty token received from auth endpoint")
    self._token = token
    self._token_expiry = _decode_jwt_expiry(token)
    logger.info("Token acquired, expires at %s", self._token_expiry)
    return token
```

### Pattern 4: API-to-Pipeline Adapter (Same Dict Shape)

**What:** The API client's `get_flat_data()` method returns a `dict[str, list[dict]]` -- the exact same shape that `load_flat_data()` returns from file. This means the downstream pipeline (inspect_schema, normalizer, loader) needs zero changes.

**When to use:** In `cli.py` when `--source api` is selected.

**Why this matters:** INGEST-05 (both ingestion modes feed the same downstream pipeline) is already marked complete because the architecture was designed for this. The integration point is in `cli.py` at line 86-88 where the stub currently exits.

**Example (cli.py integration):**
```python
if source == "api":
    from observatory.api_client import ParticleAPIClient

    try:
        client = ParticleAPIClient()  # reads PARTICLE_* from env
    except ValueError as e:
        typer.echo(str(e))
        raise typer.Exit(code=1)

    try:
        raw_data = client.get_flat_data(patient_id)
    except Exception as e:
        typer.echo(f"API request failed: {e}")
        raise typer.Exit(code=1)

    # Apply same normalization as file mode
    from observatory.normalizer import normalize_resource
    data = {}
    for key in EXPECTED_RESOURCE_TYPES:
        records = raw_data.get(key, [])
        data[key] = normalize_resource(records)
else:
    data = load_flat_data(data_path)
```

### Pattern 5: CLI Extension for API Mode

**What:** The `--source api` mode needs a `--patient-id` option to specify which patient's flat data to retrieve. File mode uses `--data-path`; API mode uses `--patient-id`. These are mutually exclusive by mode.

**When to use:** CLI argument design for Phase 5.

**Example:**
```python
@app.command()
def load(
    source: Annotated[str, typer.Option("--source")] = "file",
    target: Annotated[str, typer.Option("--target")] = "postgres",
    data_path: Annotated[str, typer.Option("--data-path", envvar="FLAT_DATA_PATH")] = "sample-data/flat_data.json",
    patient_id: Annotated[str | None, typer.Option("--patient-id", envvar="PARTICLE_PATIENT_ID")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
):
    if source == "api" and not patient_id:
        typer.echo("--patient-id is required when --source api")
        raise typer.Exit(code=1)
```

### Anti-Patterns to Avoid

- **Importing httpx or tenacity in the observatory package:** The stdlib-only constraint is a project decision. Adding httpx would pull in 6+ transitive dependencies and break the dependency philosophy.
- **Coupling the API client to the parser module:** The API client should return raw JSON dict, not call `load_flat_data()`. The normalization step should happen in cli.py (or a shared pipeline function), keeping the API client focused on HTTP.
- **Verifying JWT signatures:** Unnecessary -- we only need the `exp` claim for refresh timing, same as the starters codebase. Signature verification would require PyJWT or cryptography, adding heavyweight dependencies.
- **Storing tokens in files or config:** Tokens are ephemeral (1 hour TTL). Keep them in-memory only. Never log the token value.
- **Retrying auth failures (401/403):** These indicate bad credentials, not transient errors. Retry only 429 and 5xx. The auth endpoint itself should not be retried on 401 (that means wrong credentials).

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT expiry extraction | Full JWT library | base64 + json stdlib decode | We only need the `exp` claim, not validation. 10 lines vs a new dependency. |
| Exponential backoff formula | Custom math | Standard formula: `min(initial * 2^attempt, max) + random(0, jitter)` | AWS and Google both recommend this exact formula. No need to invent. |
| Retry-After header parsing | Custom parser | `float(e.headers.get("Retry-After", "0"))` | RFC 7231 defines Retry-After as seconds (integer) or HTTP-date. Particle uses seconds. |
| Environment variable config | Custom config class | `os.environ.get()` with defaults | Matches existing observatory pattern (config.py, loader.py, bq_loader.py all use this). |
| URL construction | String formatting | `f"{base_url}/api/v2/patients/{patient_id}/flat"` | Simple path concatenation is correct for REST APIs with known path structure. |

**Key insight:** The entire API client is ~150-200 lines of code. The stdlib provides everything needed. The complexity is in the retry logic and auth flow, not in the HTTP mechanics.

## Common Pitfalls

### Pitfall 1: Auth Endpoint Returning Non-JSON (Plain Text JWT)

**What goes wrong:** Developer assumes API returns JSON and calls `json.loads()` on the auth response, getting a decode error because the response is plain-text JWT.

**Why it happens:** Almost all REST APIs return JSON. Particle's auth endpoint is an exception -- it returns the JWT as a plain text string.

**How to avoid:** Read the response as text (`response.read().decode("utf-8").strip()`), not JSON. The Accept header should be `text/plain`, not `application/json`. This is documented in the existing starters code (`auth.py` line 148-149: `"accept": "text/plain"`) and confirmed in the Particle docs.

**Warning signs:** `json.JSONDecodeError` when calling the auth endpoint.

### Pitfall 2: Missing Retry-After Header Handling for 429

**What goes wrong:** The retry logic uses only calculated backoff, ignoring the server's `Retry-After` header. This can lead to retrying too quickly (server says "wait 30s" but backoff calculates 2s) or too slowly.

**Why it happens:** Developers implement generic exponential backoff without checking for the rate-limit-specific header.

**How to avoid:** Check `e.headers.get("Retry-After")` on 429 responses. Use `max(calculated_backoff, retry_after_value)` to respect the server's guidance. The existing starters codebase captures Retry-After in `ParticleRateLimitError.retry_after` (http.py line 179-182).

**Warning signs:** Continued 429 responses despite retries, or unnecessarily long waits when the server allows shorter retry windows.

### Pitfall 3: urllib.request Timeout Scope

**What goes wrong:** Developer sets `timeout=30` expecting it to cover the entire request lifecycle, but `urllib.request.urlopen(timeout=...)` only sets the socket timeout -- it does not cover DNS resolution or the total response read time for large responses.

**Why it happens:** The `timeout` parameter in urlopen is a socket-level timeout, not a request-level timeout. Python's DNS resolver does not obey the socket timeout.

**How to avoid:** Set a reasonable timeout (30s default, matching starters), but document that this is a socket timeout. For extremely large flat data responses, consider that the response read will succeed in chunks without hitting the socket timeout (each chunk read resets the timer). Add logging of request duration for operational visibility.

**Warning signs:** Requests appearing to hang despite timeout being set (stuck in DNS resolution, or socket timeout not triggering during slow response streaming).

### Pitfall 4: Token Refresh Race During Long Pipeline Runs

**What goes wrong:** For a customer loading multiple patients in sequence, the API client acquires a token at the start, but by the time it processes the 50th patient (hours later), the token has expired. The next API call fails with 401.

**Why it happens:** The token is acquired once and never refreshed. With 1-hour TTL and multiple patients, the pipeline can outlive the token.

**How to avoid:** Check `needs_refresh()` before every API call, not just at startup. Use the same proactive refresh buffer (600 seconds = 10 minutes before expiry) as the starters codebase. The `_acquire_token()` method should be called transparently when the token is stale.

**Warning signs:** Pipeline works for the first patient but fails with 401 on subsequent patients after ~50 minutes.

### Pitfall 5: Confusing API Flat Response with File Flat Data

**What goes wrong:** The API GET Flat response and the file `flat_data.json` have the same structure but may differ in: (a) which resource types are present, (b) which fields exist per resource type, and (c) whether empty types are present as empty arrays or absent entirely.

**Why it happens:** The file was saved from a specific API call at a specific time. A live API call may return different data.

**How to avoid:** The existing parser already handles this gracefully: it iterates over `EXPECTED_RESOURCE_TYPES` and treats missing keys as empty lists. The API client should return the raw API response dict, and the same parser logic handles both. No special handling needed, but this should be tested.

**Warning signs:** Missing resource types in API mode that were present in file mode (or vice versa).

### Pitfall 6: Not Validating PARTICLE_* Env Vars Before API Call

**What goes wrong:** User runs `particle-pipeline load --source api --target postgres` without setting PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, or PARTICLE_SCOPE_ID. The error is a cryptic urllib.error.HTTPError from the auth endpoint instead of an actionable message.

**Why it happens:** The API client attempts the auth request without checking that required env vars are present.

**How to avoid:** Validate that all required env vars (PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, PARTICLE_SCOPE_ID) are non-empty at client construction time, before making any HTTP requests. Raise a `ValueError` with an actionable message listing which vars are missing and pointing to .env.example.

**Warning signs:** Raw HTTP error stack traces when API credentials are missing.

## Code Examples

Verified patterns from existing codebase and official sources:

### Complete API Client Class Structure

```python
# Source: Particle starters auth.py + query/service.py, adapted for stdlib
import json
import logging
import os
import random
import time
import base64
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class ParticleAPIClient:
    """Stdlib-based Particle Health API client with auth and retry.

    Reads configuration from environment variables:
        PARTICLE_CLIENT_ID (required)
        PARTICLE_CLIENT_SECRET (required)
        PARTICLE_SCOPE_ID (required)
        PARTICLE_BASE_URL (default: https://sandbox.particlehealth.com)
        PARTICLE_TIMEOUT (default: 30)
        PARTICLE_MAX_RETRIES (default: 3)
    """

    def __init__(self) -> None:
        self._client_id = os.environ.get("PARTICLE_CLIENT_ID", "")
        self._client_secret = os.environ.get("PARTICLE_CLIENT_SECRET", "")
        self._scope_id = os.environ.get("PARTICLE_SCOPE_ID", "")
        self._base_url = os.environ.get(
            "PARTICLE_BASE_URL", "https://sandbox.particlehealth.com"
        )
        self._timeout = float(os.environ.get("PARTICLE_TIMEOUT", "30"))
        self._max_retries = int(os.environ.get("PARTICLE_MAX_RETRIES", "3"))
        self._token: str | None = None
        self._token_expiry: datetime | None = None
        self._refresh_buffer = timedelta(seconds=600)  # 10 min before expiry

        # Validate required settings
        missing = []
        if not self._client_id:
            missing.append("PARTICLE_CLIENT_ID")
        if not self._client_secret:
            missing.append("PARTICLE_CLIENT_SECRET")
        if not self._scope_id:
            missing.append("PARTICLE_SCOPE_ID")
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n\n"
                "To fix: set these in .env or environment. See .env.example."
            )

    def get_flat_data(self, patient_id: str) -> dict[str, list[dict]]:
        """Fetch flat data for a patient from the Particle API.

        Returns the same dict shape as load_flat_data(): resource_type -> records.
        """
        self._ensure_token()
        url = f"{self._base_url}/api/v2/patients/{patient_id}/flat"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "accept": "application/json",
        }
        response_bytes = self._request_with_retry(url, headers)
        data = json.loads(response_bytes.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected JSON object from API, got {type(data).__name__}"
            )
        return data
```

### Auth Token Acquisition

```python
# Source: particle-health-starters/src/particle/core/auth.py lines 136-168
def _ensure_token(self) -> None:
    """Acquire or refresh token if needed."""
    if self._token and self._token_expiry:
        if datetime.now(tz=timezone.utc) < self._token_expiry - self._refresh_buffer:
            return  # Token still valid
    self._acquire_token()

def _acquire_token(self) -> None:
    """Acquire JWT from Particle auth endpoint."""
    headers = {
        "client-id": self._client_id,
        "client-secret": self._client_secret,
        "scope": self._scope_id,
        "accept": "text/plain",
    }
    req = urllib.request.Request(
        f"{self._base_url}/auth",
        headers=headers,
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=self._timeout) as response:
            token = response.read().decode("utf-8").strip()
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise ValueError(
                f"Authentication failed (HTTP {e.code}).\n\n"
                "To fix:\n"
                "  1. Check PARTICLE_CLIENT_ID and PARTICLE_CLIENT_SECRET in .env\n"
                "  2. Verify credentials in the Particle Developer Portal\n"
                "  3. Check PARTICLE_SCOPE_ID matches your project scope"
            ) from e
        raise
    if not token:
        raise ValueError("Empty token received from auth endpoint")
    self._token = token
    self._token_expiry = _decode_jwt_expiry(token)
    logger.info("Token acquired, expires at %s", self._token_expiry)
```

### Retry Loop with Exponential Backoff + Jitter

```python
# Source: AWS Architecture Blog exponential backoff + Python stdlib
def _request_with_retry(self, url: str, headers: dict[str, str]) -> bytes:
    """Make GET request with retry on 429/5xx."""
    req = urllib.request.Request(url, headers=headers, method="GET")

    for attempt in range(self._max_retries + 1):
        try:
            logger.debug("GET %s (attempt %d)", url, attempt + 1)
            start = time.monotonic()
            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                data = response.read()
            elapsed = time.monotonic() - start
            logger.info("GET %s -> %d (%.1fs)", url, response.status, elapsed)
            return data

        except urllib.error.HTTPError as e:
            if e.code == 401:
                # Token may have expired mid-pipeline; try refresh once
                logger.warning("Got 401, refreshing token")
                self._acquire_token()
                req.remove_header("Authorization")
                req.add_header("Authorization", f"Bearer {self._token}")
                continue

            if e.code not in RETRYABLE_STATUS_CODES or attempt == self._max_retries:
                raise

            wait = self._calculate_backoff(attempt, e)
            logger.warning(
                "GET %s -> %d, retrying in %.1fs (attempt %d/%d)",
                url, e.code, wait, attempt + 1, self._max_retries,
            )
            time.sleep(wait)

        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt == self._max_retries:
                raise
            wait = self._calculate_backoff(attempt)
            logger.warning(
                "GET %s failed (%s), retrying in %.1fs (attempt %d/%d)",
                url, e, wait, attempt + 1, self._max_retries,
            )
            time.sleep(wait)

    raise RuntimeError("Retry loop exhausted")


def _calculate_backoff(
    self, attempt: int, http_error: urllib.error.HTTPError | None = None
) -> float:
    """Calculate backoff with jitter, respecting Retry-After header."""
    backoff = min(1.0 * (2 ** attempt), 60.0)
    jitter = random.uniform(0, 1.0)
    wait = backoff + jitter

    if http_error and http_error.code == 429:
        retry_after = http_error.headers.get("Retry-After")
        if retry_after:
            try:
                wait = max(wait, float(retry_after))
            except ValueError:
                pass

    return wait
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| requests + urllib3 retry | httpx + tenacity (async-capable) | httpx stable since 2023 | Better async support, typed API. But observatory uses stdlib. |
| PyJWT for token decode | base64 + json (when only `exp` needed) | Always valid for unverified decode | Avoids dependency when full JWT validation isn't needed |
| Global retry decorator | Context-aware retry with Retry-After | Growing adoption since 2024 | Respects server guidance, avoids ban from aggressive retry |
| Single timeout value | Connect + read separate timeouts | httpx/urllib3 support this | urllib.request only supports socket timeout; document limitation |

**Deprecated/outdated:**
- **requests library**: Not deprecated, but httpx is the modern replacement. Neither is used here (stdlib-only).
- **urllib2**: Replaced by `urllib.request` in Python 3. Do not reference urllib2 patterns.

## Open Questions

Things that could not be fully resolved:

1. **Does the GET Flat endpoint paginate for large responses?**
   - What we know: The Particle docs mention "continuation tokens" for pagination in general, but the GET Flat endpoint documentation does not explicitly discuss pagination. The sample flat data for one patient is ~880KB -- well within a single HTTP response.
   - What's unclear: Whether multi-source patients with very large clinical histories could exceed response size limits.
   - Recommendation: Implement single-request retrieval for Phase 5. If pagination is needed, it will manifest as truncated data and can be addressed as a follow-up. Log the response size for monitoring.

2. **Exact rate limits for the Particle API**
   - What we know: Particle docs say "standard bucket/TTL middleware is enforced. Limits vary by tenant." The starters codebase retries on 429 with Retry-After header. Webhook retry uses exponential backoff: 0s, 30s, 2m, 10m, 1h.
   - What's unclear: Exact requests-per-second or requests-per-minute limits. Whether sandbox and production have different limits.
   - Recommendation: Implement retry with exponential backoff (handles any rate limit transparently). Log all 429 responses with Retry-After values so customers can understand their limits. Default max retries to 3, configurable via PARTICLE_MAX_RETRIES.

3. **Should the API client handle the full query flow (submit + poll + get flat)?**
   - What we know: Getting flat data requires a completed query. The starters have `QueryService.submit_query()` + `wait_for_query_complete()` + `get_flat()` as a 3-step flow.
   - What's unclear: Whether Phase 5 should implement only `get_flat()` (assuming query is already complete) or the full submit-poll-retrieve flow.
   - Recommendation: Start with `get_flat()` only for Phase 5 -- this is what the requirements specify (INGEST-02: "authenticates with Particle Health and calls GET Flat endpoint"). The patient_id passed via `--patient-id` is assumed to have a completed query. Document this assumption. Full query orchestration can be a future enhancement.

4. **How should the client secret be protected in logging?**
   - What we know: The starters use `pydantic.SecretStr` to prevent secrets from appearing in repr/str output. Observatory uses raw `os.environ.get()`.
   - What's unclear: Whether the stdlib approach needs explicit protection.
   - Recommendation: Never log the client_secret value. The `_acquire_token()` method should log "Authenticating with Particle API at {base_url}" but never include credentials. The `__repr__` of the client class should redact the secret.

## Sources

### Primary (HIGH confidence)
- `particle-health-starters/src/particle/core/auth.py` -- Particle auth flow implementation: GET /auth, custom headers, plain-text JWT response, TokenManager with proactive refresh
- `particle-health-starters/src/particle/core/http.py` -- HTTP client with retry (tenacity), error mapping (429, 5xx), Retry-After handling
- `particle-health-starters/src/particle/core/config.py` -- PARTICLE_* env vars, sandbox URL default, 30s timeout, 600s refresh buffer
- `particle-health-starters/src/particle/query/service.py` -- GET Flat endpoint: `GET /api/v2/patients/{id}/flat`, returns JSON dict
- `particle-health-starters/src/particle/core/exceptions.py` -- Error hierarchy for auth, rate limit, API, validation errors
- `particle-flat-observatory/src/observatory/cli.py` -- Current --source api stub (line 86-88), CLI structure, deferred imports pattern
- `particle-flat-observatory/src/observatory/parser.py` -- load_flat_data() returns dict[str, list[dict]], the target output shape for API client
- [Python urllib.request official docs](https://docs.python.org/3/library/urllib.request.html) -- Request class, urlopen(), HTTPError, timeout parameter

### Secondary (MEDIUM confidence)
- [Particle Health Authentication docs](https://docs.particlehealth.com/reference/authentication) -- OAuth2 client credentials flow, JWT, 1-hour TTL
- [Particle Health Data Retrieval APIs](https://docs.particlehealth.com/docs/data-retrieval-apis) -- GET Flat endpoint, _since parameter, dataset filters, response format
- [Particle Health Patient Data APIs](https://docs.particlehealth.com/docs/patient-data-apis) -- Query flow: register -> query -> poll -> retrieve
- [AWS Architecture Blog: Exponential Backoff and Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) -- Full jitter algorithm: `sleep = random_between(0, min(cap, base * 2 ^ attempt))`
- `.planning/codebase/STACK.md` -- Sandbox URL: sandbox.particlehealth.com, Production URL: api.particlehealth.com

### Tertiary (LOW confidence)
- [Particle Health API Postman collection](https://www.postman.com/particlehealth/particle-health-api/overview) -- API endpoint verification (not fetched, referenced for completeness)
- Rate limit specifics ("limits vary by tenant") -- could not find exact numbers in public docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All stdlib, verified against Python 3.11+ docs, no new dependencies needed
- Architecture: HIGH - Integration points verified by reading existing cli.py (stub at line 86-88) and parser.py (dict shape matches API response)
- Auth flow: HIGH - Fully documented in existing starters codebase auth.py, verified against Particle official docs
- Retry patterns: HIGH - Exponential backoff + jitter is well-established (AWS blog, multiple sources), urllib.request error handling verified in Python docs
- Pitfalls: MEDIUM - Some pitfalls (timeout scope, pagination) are based on general urllib.request behavior, not Particle-specific testing

**Research date:** 2026-02-08
**Valid until:** 2026-03-08 (30 days -- stdlib is stable, Particle API is versioned v2)
