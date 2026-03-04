"""Unit tests for the Particle Health API client module.

Tests cover credential validation, JWT decode, backoff calculation,
and configuration defaults. All tests use mocked I/O -- no real API
calls are made.
"""

import base64
import json
import os
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from observatory.api_client import ParticleAPIClient, _decode_jwt_expiry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQUIRED_ENV = {
    "PARTICLE_CLIENT_ID": "test-client-id",
    "PARTICLE_CLIENT_SECRET": "test-client-secret",
    "PARTICLE_SCOPE_ID": "test-scope-id",
}


def _make_jwt(payload: dict) -> str:
    """Build a fake JWT (header.payload.signature) with the given payload dict."""
    header_b64 = base64.urlsafe_b64encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).rstrip(b"=").decode()
    signature_b64 = base64.urlsafe_b64encode(b"fakesignature").rstrip(b"=").decode()
    return f"{header_b64}.{payload_b64}.{signature_b64}"


# ---------------------------------------------------------------------------
# Credential validation tests
# ---------------------------------------------------------------------------

class TestCredentialValidation:
    """ParticleAPIClient constructor validates required environment variables."""

    def test_missing_client_id_raises_value_error(self):
        env = {
            "PARTICLE_CLIENT_SECRET": "secret",
            "PARTICLE_SCOPE_ID": "scope",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="PARTICLE_CLIENT_ID"):
                ParticleAPIClient()

    def test_missing_client_secret_raises_value_error(self):
        env = {
            "PARTICLE_CLIENT_ID": "client-id",
            "PARTICLE_SCOPE_ID": "scope",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="PARTICLE_CLIENT_SECRET"):
                ParticleAPIClient()

    def test_missing_scope_id_raises_value_error(self):
        env = {
            "PARTICLE_CLIENT_ID": "client-id",
            "PARTICLE_CLIENT_SECRET": "secret",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="PARTICLE_SCOPE_ID"):
                ParticleAPIClient()

    def test_missing_multiple_vars_lists_all(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                ParticleAPIClient()
            msg = str(exc_info.value)
            assert "PARTICLE_CLIENT_ID" in msg
            assert "PARTICLE_CLIENT_SECRET" in msg
            assert "PARTICLE_SCOPE_ID" in msg

    def test_valid_credentials_constructs_ok(self):
        with patch.dict(os.environ, REQUIRED_ENV, clear=True):
            client = ParticleAPIClient()
            assert client is not None


# ---------------------------------------------------------------------------
# JWT decode tests
# ---------------------------------------------------------------------------

class TestDecodeJwtExpiry:
    """_decode_jwt_expiry extracts the exp claim from a JWT payload."""

    def test_decode_jwt_expiry_valid_token(self):
        exp_ts = 1700000000
        token = _make_jwt({"exp": exp_ts, "sub": "user123"})
        result = _decode_jwt_expiry(token)
        expected = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
        assert result == expected

    def test_decode_jwt_expiry_no_exp_claim(self):
        token = _make_jwt({"sub": "user123", "iat": 1699999000})
        result = _decode_jwt_expiry(token)
        assert result is None

    def test_decode_jwt_expiry_malformed_token(self):
        result = _decode_jwt_expiry("not-a-jwt")
        assert result is None

    def test_decode_jwt_expiry_invalid_base64(self):
        # Three parts but the middle part is not valid base64
        result = _decode_jwt_expiry("header.!!!invalid!!!.signature")
        assert result is None


# ---------------------------------------------------------------------------
# Backoff calculation tests
# ---------------------------------------------------------------------------

class TestBackoffCalculation:
    """_calculate_backoff produces correct exponential backoff with jitter."""

    def test_backoff_attempt_0(self):
        """First attempt: base 1.0 * 2^0 = 1.0, plus jitter 0.5 = 1.5."""
        with patch.dict(os.environ, REQUIRED_ENV, clear=True):
            client = ParticleAPIClient()
        with patch("random.uniform", return_value=0.5):
            result = client._calculate_backoff(0)
        assert result == pytest.approx(1.5)

    def test_backoff_attempt_2(self):
        """Third attempt: base 1.0 * 2^2 = 4.0, plus jitter 0.5 = 4.5."""
        with patch.dict(os.environ, REQUIRED_ENV, clear=True):
            client = ParticleAPIClient()
        with patch("random.uniform", return_value=0.5):
            result = client._calculate_backoff(2)
        assert result == pytest.approx(4.5)

    def test_backoff_respects_max(self):
        """Attempt 10: base would be 1024.0 but capped at 60.0 + jitter 0.5 = 60.5."""
        with patch.dict(os.environ, REQUIRED_ENV, clear=True):
            client = ParticleAPIClient()
        with patch("random.uniform", return_value=0.5):
            result = client._calculate_backoff(10)
        assert result == pytest.approx(60.5)

    def test_backoff_respects_retry_after_header(self):
        """429 with Retry-After: 30 produces backoff >= 30.0."""
        with patch.dict(os.environ, REQUIRED_ENV, clear=True):
            client = ParticleAPIClient()
        # Simulate an HTTPError with a Retry-After header
        from unittest.mock import MagicMock
        http_error = MagicMock()
        http_error.headers = {"Retry-After": "30"}
        with patch("random.uniform", return_value=0.5):
            result = client._calculate_backoff(0, http_error=http_error)
        # base 1.0 + jitter 0.5 = 1.5, but Retry-After 30 wins: max(1.5, 30.0) = 30.0
        assert result >= 30.0


# ---------------------------------------------------------------------------
# Configuration defaults tests
# ---------------------------------------------------------------------------

class TestConfigurationDefaults:
    """ParticleAPIClient reads optional config from environment variables."""

    def test_default_base_url(self):
        with patch.dict(os.environ, REQUIRED_ENV, clear=True):
            client = ParticleAPIClient()
        assert client.base_url == "https://sandbox.particlehealth.com"

    def test_default_timeout(self):
        with patch.dict(os.environ, REQUIRED_ENV, clear=True):
            client = ParticleAPIClient()
        assert client.timeout == 30.0

    def test_default_max_retries(self):
        with patch.dict(os.environ, REQUIRED_ENV, clear=True):
            client = ParticleAPIClient()
        assert client.max_retries == 3

    def test_custom_timeout_from_env(self):
        env = {**REQUIRED_ENV, "PARTICLE_TIMEOUT": "60"}
        with patch.dict(os.environ, env, clear=True):
            client = ParticleAPIClient()
        assert client.timeout == 60.0

    def test_custom_max_retries_from_env(self):
        env = {**REQUIRED_ENV, "PARTICLE_MAX_RETRIES": "5"}
        with patch.dict(os.environ, env, clear=True):
            client = ParticleAPIClient()
        assert client.max_retries == 5
