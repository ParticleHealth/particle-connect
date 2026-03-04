import logging
import time
from dataclasses import dataclass, field
from urllib.parse import parse_qs

import httpx

from app.config import ENVIRONMENTS, settings

logger = logging.getLogger(__name__)


class ParticleAuthError(Exception):
    """Raised when authentication with Particle fails."""


class ParticleAPIError(Exception):
    """Raised when a Particle API call fails."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


# JWT expires after 60 minutes; refresh if within this buffer
_REFRESH_BUFFER_SECONDS = 5 * 60


@dataclass
class _TokenState:
    access_token: str = ""
    obtained_at: float = 0.0
    expires_in: int = 3600

    @property
    def is_valid(self) -> bool:
        if not self.access_token:
            return False
        elapsed = time.time() - self.obtained_at
        return elapsed < (self.expires_in - _REFRESH_BUFFER_SECONDS)


@dataclass
class ParticleClient:
    """Shared HTTP client for all Particle Management API calls.

    Stores JWT in-memory and auto-refreshes when close to expiry.
    """

    _token: _TokenState = field(default_factory=_TokenState)
    _client_id: str = ""
    _client_secret: str = ""
    _environment: str = "sandbox"
    _http: httpx.AsyncClient = field(init=False)
    _auth_http: httpx.AsyncClient = field(init=False)

    def __post_init__(self):
        self._environment = settings.particle_env
        self._http = httpx.AsyncClient(
            base_url=settings.particle_base_url,
            timeout=httpx.Timeout(settings.particle_timeout),
        )
        self._auth_http = httpx.AsyncClient(
            base_url=settings.particle_auth_url,
            timeout=httpx.Timeout(settings.particle_timeout),
        )

    @property
    def is_authenticated(self) -> bool:
        return self._token.is_valid

    @property
    def environment(self) -> str:
        return self._environment

    async def authenticate(self, client_id: str, client_secret: str) -> dict:
        """Authenticate with Particle and cache the JWT."""
        logger.info("Authenticating with Particle API at %s", self._auth_http.base_url)
        resp = await self._auth_http.post(
            "/auth",
            headers={"client-id": client_id, "client-secret": client_secret},
        )
        if resp.status_code != 200:
            body = resp.text
            logger.warning(
                "Authentication failed: status=%d body=%s", resp.status_code, body
            )
            raise ParticleAuthError(
                f"Authentication failed ({resp.status_code}): {body}"
            )

        # Particle returns URL-encoded form data, not JSON
        raw = resp.text
        try:
            data = resp.json()
        except Exception:
            parsed = parse_qs(raw)
            data = {k: v[0] for k, v in parsed.items()}

        access_token = data.get("access_token", "")
        expires_in = int(data.get("expires_in", 3600))

        self._client_id = client_id
        self._client_secret = client_secret
        self._token = _TokenState(
            access_token=access_token,
            obtained_at=time.time(),
            expires_in=expires_in,
        )
        logger.info("Authenticated successfully, token expires_in=%d", self._token.expires_in)
        return {"access_token": access_token, "expires_in": expires_in}

    async def connect(self) -> dict:
        """Authenticate using credentials from environment variables."""
        if not settings.particle_client_id or not settings.particle_client_secret:
            raise ParticleAuthError(
                "PARTICLE_CLIENT_ID and PARTICLE_CLIENT_SECRET must be set in .env"
            )
        return await self.authenticate(
            settings.particle_client_id, settings.particle_client_secret
        )

    async def switch_environment(self, env: str) -> dict:
        """Switch between sandbox and production, then re-authenticate."""
        if env not in ENVIRONMENTS:
            raise ValueError(f"Unknown environment: {env}. Must be 'sandbox' or 'production'.")

        urls = ENVIRONMENTS[env]
        self._environment = env

        # Close old clients and create new ones with updated base URLs
        await self._http.aclose()
        await self._auth_http.aclose()
        self._http = httpx.AsyncClient(
            base_url=urls["base_url"],
            timeout=httpx.Timeout(settings.particle_timeout),
        )
        self._auth_http = httpx.AsyncClient(
            base_url=urls["auth_url"],
            timeout=httpx.Timeout(settings.particle_timeout),
        )

        # Clear existing token and re-authenticate
        self._token = _TokenState()
        return await self.connect()

    async def _ensure_token(self):
        """Re-authenticate if the token is expired or close to expiry."""
        if self._token.is_valid:
            return
        if not self._client_id:
            raise ParticleAuthError(
                "Not authenticated. Call POST /api/auth/connect first."
            )
        logger.info("Token expired or near expiry, re-authenticating")
        await self.authenticate(self._client_id, self._client_secret)

    async def request(
        self, method: str, path: str, *, json: dict | None = None
    ) -> dict | list:
        """Make an authenticated request to the Particle Management API."""
        await self._ensure_token()

        headers = {"Authorization": f"Bearer {self._token.access_token}"}
        logger.info("Particle API %s %s", method.upper(), path)
        start = time.time()

        resp = await self._http.request(method, path, headers=headers, json=json)
        latency_ms = (time.time() - start) * 1000
        logger.info(
            "Particle API response: status=%d latency=%.0fms path=%s",
            resp.status_code,
            latency_ms,
            path,
        )

        if resp.status_code >= 400:
            detail = resp.text
            try:
                err_body = resp.json()
                detail = err_body.get("message", err_body.get("error", detail))
            except Exception:
                pass
            raise ParticleAPIError(status_code=resp.status_code, detail=detail)

        if resp.status_code == 204:
            return {}
        return resp.json()

    async def close(self):
        await self._http.aclose()
        await self._auth_http.aclose()

    def clear_auth(self):
        """Clear cached credentials and token."""
        self._token = _TokenState()
        self._client_id = ""
        self._client_secret = ""


# Module-level singleton shared across the app
particle_client = ParticleClient()
