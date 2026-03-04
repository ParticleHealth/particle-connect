"""HTTP client wrapper with retry logic for Particle Health API."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from .auth import ParticleAuth
from .config import ParticleSettings
from .exceptions import (
    ParticleAPIError,
    ParticleAuthError,
    ParticleNotFoundError,
    ParticleRateLimitError,
    ParticleValidationError,
)

# Transient errors that should trigger retry
RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
)


class ParticleHTTPClient:
    """HTTP client wrapper with authentication, retry, and error handling.

    Features:
    - Automatic JWT token management via ParticleAuth
    - Retry with exponential backoff and jitter for transient failures
    - Maps HTTP status codes to specific exception types
    - Context manager support for proper resource cleanup
    """

    def __init__(self, config: ParticleSettings) -> None:
        """Initialize HTTP client.

        Args:
            config: Particle settings with credentials and configuration.
        """
        self._config = config
        self._auth = ParticleAuth(config)
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=httpx.Timeout(config.timeout),
            auth=self._auth,
        )
        self._logger = structlog.get_logger(__name__)

    def request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        data: dict[str, Any] | None = None,
        files: Any | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request with retry and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., "/api/v2/patients")
            json: JSON body for POST/PUT requests
            params: Query parameters
            headers: Additional headers (Authorization added automatically)
            data: Form data for multipart uploads
            files: File uploads for multipart requests (httpx files format)

        Returns:
            Response JSON as dict, or empty dict for no-content responses.

        Raises:
            ParticleAuthError: Authentication failed
            ParticleAPIError: API returned an error
            ParticleValidationError: Request validation failed (422)
            ParticleRateLimitError: Rate limit exceeded (429)
            ParticleNotFoundError: Resource not found (404)
        """
        return self._request_with_retry(
            method, path, json=json, params=params, headers=headers,
            data=data, files=files,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=60, jitter=5),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        reraise=True,
    )
    def _request_with_retry(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Internal method with retry decorator for transient failures."""
        self._logger.debug("request", method=method, path=path)

        # Merge default headers with any provided
        request_headers = {"accept": "application/json"}
        if kwargs.get("json") is not None:
            request_headers["content-type"] = "application/json"
        # Don't set content-type for multipart - httpx sets it with boundary
        # Always pop headers from kwargs to avoid duplicate argument error
        extra_headers = kwargs.pop("headers", None)
        if extra_headers:
            request_headers.update(extra_headers)

        response = self._client.request(method, path, headers=request_headers, **kwargs)
        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Map HTTP response to result or exception.

        Args:
            response: HTTPX response object

        Returns:
            Response JSON for successful requests

        Raises:
            Appropriate ParticleError subclass for error responses
        """
        # Success - return JSON or empty dict
        if 200 <= response.status_code < 300:
            if response.content:
                # Handle both JSON and non-JSON responses
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    try:
                        return response.json()
                    except (ValueError, UnicodeDecodeError):
                        # Server claimed JSON but body is binary (e.g., CCDA ZIP)
                        return {"_raw_content": response.content, "_content_type": content_type}
                else:
                    # Return raw content for non-JSON (e.g., CCDA ZIP)
                    return {"_raw_content": response.content, "_content_type": content_type}
            return {}

        # Auth errors
        if response.status_code == 401:
            raise ParticleAuthError("Invalid or expired credentials")
        if response.status_code == 403:
            raise ParticleAuthError("Not authorized for this operation")

        # Not found
        if response.status_code == 404:
            detail = ""
            if response.content:
                try:
                    body = response.json()
                    detail = body.get("message", str(body))
                except Exception:
                    detail = response.text
            raise ParticleNotFoundError("Resource", detail or "unknown")

        # Validation error
        if response.status_code == 422:
            body = response.json() if response.content else {}
            raise ParticleValidationError(
                "Validation failed", errors=body.get("errors", [])
            )

        # Rate limit
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise ParticleRateLimitError(
                retry_after=int(retry_after) if retry_after else None
            )

        # Server errors (5xx) - these should have been retried
        if response.status_code >= 500:
            body = response.json() if response.content else {}
            raise ParticleAPIError(
                f"Server error: {response.status_code}",
                status_code=response.status_code,
                response_body=body,
            )

        # Other client errors (4xx)
        body = response.json() if response.content else {}
        raise ParticleAPIError(
            f"API error: {response.status_code}",
            status_code=response.status_code,
            response_body=body,
        )

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        self._client.close()

    def __enter__(self) -> "ParticleHTTPClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit - ensures client is closed."""
        self.close()
