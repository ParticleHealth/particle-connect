"""JWT authentication with proactive token refresh for Particle Health API.

Particle uses a custom auth flow (NOT standard OAuth2):
- GET /auth with custom headers (client-id, client-secret, scope)
- Returns JWT token as plain text
- Token TTL is 1 hour
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Generator

import httpx
import jwt

from .config import ParticleSettings
from .exceptions import ParticleAuthError


class TokenManager:
    """Manages JWT token state and determines when refresh is needed."""

    def __init__(self) -> None:
        self._token: str | None = None
        self._expiry: datetime | None = None

    def update(self, token: str, expires_at: datetime | None = None) -> None:
        """Update token and expiry.

        Args:
            token: The JWT token string.
            expires_at: Token expiration time. If not provided, will be
                       extracted from the JWT 'exp' claim.
        """
        self._token = token

        if expires_at:
            self._expiry = expires_at
        else:
            # Extract expiry from JWT
            self._expiry = self._get_expiry_from_jwt(token)

    def _get_expiry_from_jwt(self, token: str) -> datetime | None:
        """Extract expiry time from JWT without verification.

        We decode without signature verification because we just need
        the expiry time for refresh logic, not security validation.
        """
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            if "exp" in payload:
                return datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            return None
        except jwt.DecodeError:
            return None

    def needs_refresh(self, buffer_seconds: int = 600) -> bool:
        """Check if token needs proactive refresh.

        Args:
            buffer_seconds: Seconds before expiry to trigger refresh.
                           Default is 600 (10 minutes) for 1-hour tokens.

        Returns:
            True if token is missing, expired, or within buffer of expiry.
        """
        if not self._token or not self._expiry:
            return True

        buffer = timedelta(seconds=buffer_seconds)
        return datetime.now(tz=timezone.utc) >= self._expiry - buffer

    @property
    def token(self) -> str | None:
        """Get the current token."""
        return self._token

    def clear(self) -> None:
        """Clear token state."""
        self._token = None
        self._expiry = None


class ParticleAuth(httpx.Auth):
    """HTTPX Auth class with automatic token refresh for Particle Health API.

    Particle uses a custom auth flow:
    - GET /auth with headers: client-id, client-secret, scope
    - Returns JWT as plain text
    - Token valid for 1 hour

    This class handles:
    - Initial token acquisition
    - Proactive refresh before expiry (at ~50 minutes)
    - Automatic retry on 401 responses
    """

    requires_response_body = True  # Need to read 401 responses

    def __init__(self, config: ParticleSettings) -> None:
        self._config = config
        self._token_manager = TokenManager()

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        """HTTPX auth flow with automatic token management.

        Yields requests and receives responses to handle:
        1. Initial token acquisition
        2. Proactive refresh before expiry
        3. Retry on 401 responses
        """
        # Ensure we have a valid token before the request
        if self._token_manager.needs_refresh(self._config.token_refresh_buffer_seconds):
            token_request = self._build_token_request()
            token_response = yield token_request
            self._update_token(token_response)

        # Add token to original request
        request.headers["Authorization"] = f"Bearer {self._token_manager.token}"
        response = yield request

        # Handle token expiration mid-request (401)
        if response.status_code == 401:
            # Token might have expired, try to refresh
            token_request = self._build_token_request()
            token_response = yield token_request
            self._update_token(token_response)

            # Retry original request with new token
            request.headers["Authorization"] = f"Bearer {self._token_manager.token}"
            yield request

    def _build_token_request(self) -> httpx.Request:
        """Build Particle auth request with custom headers.

        Particle uses GET /auth with custom headers instead of
        standard OAuth2 client credentials POST.
        """
        return httpx.Request(
            method="GET",
            url=f"{self._config.base_url}/auth",
            headers={
                "client-id": self._config.client_id,
                "client-secret": self._config.client_secret.get_secret_value(),
                "scope": self._config.scope_id,
                "accept": "text/plain",
            },
        )

    def _update_token(self, response: httpx.Response) -> None:
        """Parse token response and update internal state.

        Particle returns JWT as plain text, not JSON.
        """
        if response.status_code != 200:
            raise ParticleAuthError(
                f"Token request failed: {response.status_code} - {response.text}"
            )

        # Particle returns JWT as plain text
        token = response.text.strip()
        if not token:
            raise ParticleAuthError("Empty token received from auth endpoint")

        self._token_manager.update(token)

    def get_token(self) -> str | None:
        """Get the current token (for debugging/testing)."""
        return self._token_manager.token
