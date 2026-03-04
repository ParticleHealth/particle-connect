"""Particle Health API client with authentication, retry, and JWT management.

Handles all HTTP communication with the Particle Health API using only
stdlib modules. Provides automatic token refresh, exponential backoff
with jitter on transient errors, and configurable timeouts.

Environment variables (required):
    PARTICLE_CLIENT_ID      -- Particle API client identifier
    PARTICLE_CLIENT_SECRET  -- Particle API client secret
    PARTICLE_SCOPE_ID       -- Particle scope (organization) identifier

Environment variables (optional):
    PARTICLE_BASE_URL       -- API base URL (default: https://sandbox.particlehealth.com)
    PARTICLE_TIMEOUT        -- Request timeout in seconds (default: 30)
    PARTICLE_MAX_RETRIES    -- Maximum retry attempts for transient errors (default: 3)
"""

import base64
import json
import logging
import os
import random
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_REFRESH_BUFFER = timedelta(seconds=600)

_REQUIRED_VARS = (
    "PARTICLE_CLIENT_ID",
    "PARTICLE_CLIENT_SECRET",
    "PARTICLE_SCOPE_ID",
)


def _decode_jwt_expiry(token: str) -> datetime | None:
    """Extract the exp claim from a JWT token without verifying the signature.

    Returns a timezone-aware UTC datetime, or None if the token is malformed
    or does not contain an exp claim.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload_b64 = parts[1]
        # Restore base64 padding
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


class ParticleAPIClient:
    """HTTP client for the Particle Health API.

    Reads credentials from environment variables, manages JWT token lifecycle,
    and provides automatic retry with exponential backoff on transient errors.
    """

    def __init__(self) -> None:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            logger.debug("Loaded .env file via python-dotenv")
        except ImportError:
            pass

        missing = [var for var in _REQUIRED_VARS if not os.environ.get(var)]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Set these variables or add them to a .env file."
            )

        self._client_id = os.environ["PARTICLE_CLIENT_ID"]
        self._client_secret = os.environ["PARTICLE_CLIENT_SECRET"]
        self._scope_id = os.environ["PARTICLE_SCOPE_ID"]

        self.base_url = os.environ.get(
            "PARTICLE_BASE_URL", "https://sandbox.particlehealth.com"
        )
        self.timeout = float(os.environ.get("PARTICLE_TIMEOUT", "30"))
        self.max_retries = int(os.environ.get("PARTICLE_MAX_RETRIES", "3"))

        self._token: str | None = None
        self._token_expiry: datetime | None = None

        logger.info(
            "ParticleAPIClient initialized: base_url=%s timeout=%.1f max_retries=%d",
            self.base_url,
            self.timeout,
            self.max_retries,
        )

    def get_flat_data(self, patient_id: str) -> dict[str, list[dict]]:
        """Fetch flat data for a patient from the Particle API.

        Args:
            patient_id: The Particle patient identifier.

        Returns:
            A dict mapping resource type names to lists of record dicts,
            matching the shape returned by parser.load_flat_data().

        Raises:
            ValueError: If the response is not a JSON object.
            urllib.error.URLError: If the request fails after all retries.
        """
        self._ensure_token()
        url = f"{self.base_url}/api/v2/patients/{patient_id}/flat"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }
        logger.info("Fetching flat data for patient_id=%s", patient_id)
        response_bytes = self._request_with_retry(url, headers)
        data = json.loads(response_bytes)
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected JSON object from flat data endpoint, got {type(data).__name__}"
            )
        logger.info(
            "Received flat data: %d resource types",
            len(data),
        )
        return data

    def _ensure_token(self) -> None:
        """Acquire a new token if none exists or the current one is near expiry."""
        now = datetime.now(tz=timezone.utc)
        if self._token is None:
            logger.debug("No token cached, acquiring new token")
            self._acquire_token()
        elif self._token_expiry is not None and now >= self._token_expiry - _REFRESH_BUFFER:
            logger.info("Token expires at %s, refreshing proactively", self._token_expiry)
            self._acquire_token()

    def _acquire_token(self) -> None:
        """Authenticate with the Particle API and store the JWT token.

        The auth endpoint returns a plain-text JWT (not JSON).

        Raises:
            ValueError: On 401/403 (credential errors -- not retryable).
            urllib.error.URLError: On network or server errors.
        """
        url = f"{self.base_url}/auth"
        req = urllib.request.Request(url, method="GET")
        req.add_header("client-id", self._client_id)
        req.add_header("client-secret", self._client_secret)
        req.add_header("scope", self._scope_id)
        req.add_header("Accept", "text/plain")

        logger.info("Acquiring auth token from %s", url)
        start = time.monotonic()

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                token = resp.read().decode("utf-8").strip()
        except urllib.error.HTTPError as e:
            latency_ms = (time.monotonic() - start) * 1000
            logger.error(
                "Auth failed: status=%d latency=%.0fms url=%s",
                e.code,
                latency_ms,
                url,
            )
            if e.code in (401, 403):
                raise ValueError(
                    f"Authentication failed (HTTP {e.code}). "
                    f"Check PARTICLE_CLIENT_ID, PARTICLE_CLIENT_SECRET, and "
                    f"PARTICLE_SCOPE_ID values. Verify credentials in the "
                    f"Particle Health dashboard."
                ) from e
            raise

        latency_ms = (time.monotonic() - start) * 1000
        self._token = token
        self._token_expiry = _decode_jwt_expiry(token)
        logger.info(
            "Token acquired: latency=%.0fms expires=%s",
            latency_ms,
            self._token_expiry,
        )

    def _request_with_retry(self, url: str, headers: dict[str, str]) -> bytes:
        """Execute an HTTP GET with automatic retry on transient errors.

        On 401: refreshes token once and retries (prevents infinite loop).
        On 429/5xx: backs off with exponential delay + jitter, respects
        the Retry-After header.

        Args:
            url: The full URL to request.
            headers: HTTP headers to include.

        Returns:
            The response body as bytes.

        Raises:
            urllib.error.HTTPError: If retries are exhausted.
            urllib.error.URLError: On network errors after retries.
        """
        max_attempts = self.max_retries + 1
        token_refreshed = False

        for attempt in range(max_attempts):
            req = urllib.request.Request(url, method="GET")
            for key, value in headers.items():
                req.add_header(key, value)

            start = time.monotonic()
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read()
                latency_ms = (time.monotonic() - start) * 1000
                logger.debug(
                    "Request OK: url=%s status=200 latency=%.0fms",
                    url,
                    latency_ms,
                )
                return body

            except urllib.error.HTTPError as e:
                latency_ms = (time.monotonic() - start) * 1000
                logger.warning(
                    "HTTP error: url=%s status=%d latency=%.0fms attempt=%d/%d",
                    url,
                    e.code,
                    latency_ms,
                    attempt + 1,
                    max_attempts,
                )

                # 401: refresh token once, then retry
                if e.code == 401 and not token_refreshed:
                    logger.info("Received 401, refreshing token and retrying")
                    self._acquire_token()
                    headers = {**headers, "Authorization": f"Bearer {self._token}"}
                    token_refreshed = True
                    continue

                # Retryable status codes: backoff and retry
                if e.code in RETRYABLE_STATUS_CODES and attempt < max_attempts - 1:
                    backoff = self._calculate_backoff(attempt, http_error=e)
                    logger.info(
                        "Retrying in %.1fs: url=%s status=%d attempt=%d/%d",
                        backoff,
                        url,
                        e.code,
                        attempt + 1,
                        max_attempts,
                    )
                    time.sleep(backoff)
                    continue

                # Non-retryable or retries exhausted
                raise

            except (urllib.error.URLError, TimeoutError, OSError) as e:
                latency_ms = (time.monotonic() - start) * 1000
                logger.warning(
                    "Network error: url=%s error=%s latency=%.0fms attempt=%d/%d",
                    url,
                    e,
                    latency_ms,
                    attempt + 1,
                    max_attempts,
                )
                if attempt < max_attempts - 1:
                    backoff = self._calculate_backoff(attempt)
                    logger.info(
                        "Retrying in %.1fs after network error: attempt=%d/%d",
                        backoff,
                        attempt + 1,
                        max_attempts,
                    )
                    time.sleep(backoff)
                    continue
                raise

        # Should not be reached, but satisfy type checker
        raise RuntimeError("Retry loop exited without returning or raising")

    def _calculate_backoff(self, attempt: int, http_error: object = None) -> float:
        """Calculate exponential backoff delay with jitter.

        Formula: min(1.0 * 2^attempt, 60.0) + random.uniform(0, 1.0)
        If the error has a Retry-After header, use the larger of the
        calculated backoff and the Retry-After value.

        Args:
            attempt: Zero-based attempt number.
            http_error: Optional HTTP error object with headers attribute.

        Returns:
            Backoff delay in seconds.
        """
        base = min(1.0 * (2 ** attempt), 60.0)
        jitter = random.uniform(0, 1.0)
        backoff = base + jitter

        # Respect Retry-After header if present
        if http_error is not None:
            retry_after = getattr(
                getattr(http_error, "headers", None), "__getitem__", None
            )
            if retry_after is not None:
                try:
                    headers = http_error.headers
                    retry_after_val = headers.get("Retry-After") if headers else None
                    if retry_after_val is not None:
                        backoff = max(backoff, float(retry_after_val))
                except (ValueError, TypeError, AttributeError):
                    pass

        return backoff
