"""Integration tests for core infrastructure components."""

import pytest

from particle.core import (
    ParticleAPIError,
    ParticleAuth,
    ParticleAuthError,
    ParticleError,
    ParticleHTTPClient,
    ParticleNotFoundError,
    ParticleRateLimitError,
    ParticleSettings,
    ParticleValidationError,
    TokenManager,
    configure_logging,
    get_logger,
    redact_phi,
)


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    """Set up environment variables for all tests."""
    monkeypatch.setenv("PARTICLE_CLIENT_ID", "test-client")
    monkeypatch.setenv("PARTICLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("PARTICLE_SCOPE_ID", "test-scope")


class TestConfig:
    """Tests for ParticleSettings configuration."""

    def test_config_loads_from_env(self):
        """Verify config loads from PARTICLE_* env vars."""
        config = ParticleSettings()
        assert config.client_id == "test-client"
        assert config.client_secret.get_secret_value() == "test-secret"
        assert config.scope_id == "test-scope"

    def test_config_defaults(self):
        """Verify sensible defaults are set."""
        config = ParticleSettings()
        assert config.base_url == "https://sandbox.particlehealth.com"
        assert config.timeout == 30.0
        assert config.token_refresh_buffer_seconds == 600

    def test_secret_str_protects_secret(self):
        """Verify SecretStr doesn't expose secret in repr."""
        config = ParticleSettings()
        repr_str = repr(config.client_secret)
        assert "test-secret" not in repr_str
        assert "**********" in repr_str


class TestExceptions:
    """Tests for custom exception hierarchy."""

    def test_all_exceptions_inherit_from_base(self):
        """Verify all exceptions inherit from ParticleError."""
        exceptions = [
            ParticleAuthError(),
            ParticleAPIError("test", 500),
            ParticleValidationError("test"),
            ParticleRateLimitError(),
            ParticleNotFoundError("Patient", "123"),
        ]
        for exc in exceptions:
            assert isinstance(exc, ParticleError)

    def test_api_error_has_status_code(self):
        """Verify ParticleAPIError includes status code."""
        exc = ParticleAPIError("Server error", 500, {"error": "details"})
        assert exc.status_code == 500
        assert exc.response_body == {"error": "details"}
        assert exc.code == "api_error"

    def test_rate_limit_error_has_retry_after(self):
        """Verify ParticleRateLimitError includes retry_after."""
        exc = ParticleRateLimitError(retry_after=60)
        assert exc.retry_after == 60
        assert "60" in exc.message

    def test_not_found_error_has_resource_info(self):
        """Verify ParticleNotFoundError includes resource details."""
        exc = ParticleNotFoundError("Patient", "abc-123")
        assert exc.resource_type == "Patient"
        assert exc.resource_id == "abc-123"
        assert "Patient" in exc.message


class TestLogging:
    """Tests for structured logging with PHI redaction."""

    def test_redact_phi_by_key(self):
        """Verify PHI is redacted by key name."""
        event_dict = {
            "first_name": "John",
            "last_name": "Doe",
            "ssn": "123-45-6789",
            "event": "test",
        }
        result = redact_phi(None, "info", event_dict)
        assert result["first_name"] == "[REDACTED]"
        assert result["last_name"] == "[REDACTED]"
        assert result["ssn"] == "[REDACTED]"
        assert result["event"] == "test"  # Non-PHI preserved

    def test_redact_phi_by_pattern(self):
        """Verify PHI is redacted by pattern matching."""
        event_dict = {
            "message": "Patient SSN is 123-45-6789 and phone is 555-123-4567",
        }
        result = redact_phi(None, "info", event_dict)
        assert "123-45-6789" not in result["message"]
        assert "555-123-4567" not in result["message"]
        assert "REDACTED" in result["message"]

    def test_redact_nested_dicts(self):
        """Verify PHI redaction works on nested structures."""
        event_dict = {
            "patient": {
                "first_name": "Jane",
                "email": "jane@example.com",
            }
        }
        result = redact_phi(None, "info", event_dict)
        assert result["patient"]["first_name"] == "[REDACTED]"
        assert result["patient"]["email"] == "[REDACTED]"

    def test_configure_logging_runs(self):
        """Verify configure_logging doesn't raise."""
        configure_logging()
        logger = get_logger("test")
        assert logger is not None


class TestAuth:
    """Tests for authentication components."""

    def test_token_manager_needs_refresh_when_empty(self):
        """Verify TokenManager needs refresh when no token."""
        tm = TokenManager()
        assert tm.needs_refresh() is True

    def test_token_manager_tracks_token(self):
        """Verify TokenManager stores and returns token."""
        tm = TokenManager()
        # Simulate token with 1 hour expiry
        from datetime import datetime, timedelta, timezone
        expiry = datetime.now(tz=timezone.utc) + timedelta(hours=1)
        tm.update("test-token", expires_at=expiry)
        assert tm.token == "test-token"
        assert tm.needs_refresh() is False

    def test_particle_auth_builds_correct_request(self):
        """Verify ParticleAuth builds request with custom headers."""
        config = ParticleSettings()
        auth = ParticleAuth(config)
        req = auth._build_token_request()

        assert req.method == "GET"
        assert "/auth" in str(req.url)
        assert req.headers["client-id"] == "test-client"
        assert req.headers["client-secret"] == "test-secret"
        assert req.headers["scope"] == "test-scope"


class TestHTTPClient:
    """Tests for HTTP client."""

    def test_http_client_creation(self):
        """Verify ParticleHTTPClient creates without error."""
        config = ParticleSettings()
        client = ParticleHTTPClient(config)
        assert client is not None
        client.close()

    def test_http_client_context_manager(self):
        """Verify ParticleHTTPClient works as context manager."""
        config = ParticleSettings()
        with ParticleHTTPClient(config) as client:
            assert client is not None


class TestExports:
    """Tests for package exports."""

    def test_all_exports_available(self):
        """Verify all expected symbols are in particle.core.__all__."""
        from particle import core

        expected = [
            "ParticleSettings",
            "ParticleAuth",
            "TokenManager",
            "ParticleHTTPClient",
            "ParticleError",
            "ParticleAuthError",
            "ParticleAPIError",
            "ParticleValidationError",
            "ParticleRateLimitError",
            "ParticleNotFoundError",
            "configure_logging",
            "get_logger",
            "redact_phi",
        ]
        for name in expected:
            assert name in core.__all__, f"Missing export: {name}"
            assert hasattr(core, name), f"Export not accessible: {name}"
