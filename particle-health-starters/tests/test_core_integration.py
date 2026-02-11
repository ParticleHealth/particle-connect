"""Integration tests for core infrastructure components."""

from unittest.mock import patch

import pytest
from pydantic import ValidationError

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
from particle.patient import Gender, PatientRegistration
from particle.query import QueryResponse, QueryStatus


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


class TestPatientRegistrationValidators:
    """Tests for PatientRegistration field validators."""

    def test_ssn_valid_format(self):
        """Verify SSN in XXX-XX-XXXX format is accepted."""
        patient = PatientRegistration(
            given_name="Test", family_name="User", date_of_birth="1990-01-01",
            gender=Gender.MALE, postal_code="12345", address_city="Boston",
            address_state="Massachusetts", ssn="123-45-6789",
        )
        assert patient.ssn == "123-45-6789"

    def test_ssn_invalid_no_dashes(self):
        """Verify SSN without dashes is rejected."""
        with pytest.raises(ValidationError, match="SSN must be in format"):
            PatientRegistration(
                given_name="Test", family_name="User", date_of_birth="1990-01-01",
                gender=Gender.MALE, postal_code="12345", address_city="Boston",
                address_state="Massachusetts", ssn="123456789",
            )

    def test_ssn_none_allowed(self):
        """Verify SSN can be omitted."""
        patient = PatientRegistration(
            given_name="Test", family_name="User", date_of_birth="1990-01-01",
            gender=Gender.MALE, postal_code="12345", address_city="Boston",
            address_state="Massachusetts",
        )
        assert patient.ssn is None

    def test_telephone_standard_format(self):
        """Verify XXX-XXX-XXXX telephone format."""
        patient = PatientRegistration(
            given_name="Test", family_name="User", date_of_birth="1990-01-01",
            gender=Gender.MALE, postal_code="12345", address_city="Boston",
            address_state="Massachusetts", telephone="234-567-8910",
        )
        assert patient.telephone == "234-567-8910"

    def test_telephone_parentheses_format(self):
        """Verify (XXX) XXX-XXXX is normalized."""
        patient = PatientRegistration(
            given_name="Test", family_name="User", date_of_birth="1990-01-01",
            gender=Gender.MALE, postal_code="12345", address_city="Boston",
            address_state="Massachusetts", telephone="(234) 567-8910",
        )
        assert patient.telephone == "234-567-8910"

    def test_telephone_dots_format(self):
        """Verify XXX.XXX.XXXX is normalized."""
        patient = PatientRegistration(
            given_name="Test", family_name="User", date_of_birth="1990-01-01",
            gender=Gender.MALE, postal_code="12345", address_city="Boston",
            address_state="Massachusetts", telephone="234.567.8910",
        )
        assert patient.telephone == "234-567-8910"

    def test_telephone_digits_only(self):
        """Verify 10 bare digits are normalized."""
        patient = PatientRegistration(
            given_name="Test", family_name="User", date_of_birth="1990-01-01",
            gender=Gender.MALE, postal_code="12345", address_city="Boston",
            address_state="Massachusetts", telephone="2345678910",
        )
        assert patient.telephone == "234-567-8910"

    def test_telephone_country_code(self):
        """Verify 1-XXX-XXX-XXXX drops country code."""
        patient = PatientRegistration(
            given_name="Test", family_name="User", date_of_birth="1990-01-01",
            gender=Gender.MALE, postal_code="12345", address_city="Boston",
            address_state="Massachusetts", telephone="1-234-567-8910",
        )
        assert patient.telephone == "234-567-8910"

    def test_telephone_plus_country_code(self):
        """Verify +1 XXX XXX XXXX drops country code."""
        patient = PatientRegistration(
            given_name="Test", family_name="User", date_of_birth="1990-01-01",
            gender=Gender.MALE, postal_code="12345", address_city="Boston",
            address_state="Massachusetts", telephone="+1 234 567 8910",
        )
        assert patient.telephone == "234-567-8910"

    def test_telephone_invalid_digit_count(self):
        """Verify too few digits is rejected."""
        with pytest.raises(ValidationError, match="10 digits"):
            PatientRegistration(
                given_name="Test", family_name="User", date_of_birth="1990-01-01",
                gender=Gender.MALE, postal_code="12345", address_city="Boston",
                address_state="Massachusetts", telephone="234-567",
            )

    def test_telephone_none_allowed(self):
        """Verify telephone can be omitted."""
        patient = PatientRegistration(
            given_name="Test", family_name="User", date_of_birth="1990-01-01",
            gender=Gender.MALE, postal_code="12345", address_city="Boston",
            address_state="Massachusetts",
        )
        assert patient.telephone is None

    def test_postal_code_5_digit(self):
        """Verify 5-digit postal code."""
        patient = PatientRegistration(
            given_name="Test", family_name="User", date_of_birth="1990-01-01",
            gender=Gender.MALE, postal_code="02215", address_city="Boston",
            address_state="Massachusetts",
        )
        assert patient.postal_code == "02215"

    def test_postal_code_9_digit_with_dash(self):
        """Verify 9-digit postal code with dash."""
        patient = PatientRegistration(
            given_name="Test", family_name="User", date_of_birth="1990-01-01",
            gender=Gender.MALE, postal_code="02215-1234", address_city="Boston",
            address_state="Massachusetts",
        )
        assert patient.postal_code == "02215-1234"

    def test_postal_code_invalid_4_digits(self):
        """Verify 4-digit postal code is rejected."""
        with pytest.raises(ValidationError):
            PatientRegistration(
                given_name="Test", family_name="User", date_of_birth="1990-01-01",
                gender=Gender.MALE, postal_code="0221", address_city="Boston",
                address_state="Massachusetts",
            )

    def test_gender_only_male_female(self):
        """Verify Gender enum has exactly MALE and FEMALE."""
        assert set(Gender) == {Gender.MALE, Gender.FEMALE}
        assert len(Gender) == 2

    def test_missing_given_name_raises(self):
        """Verify missing required field raises ValidationError."""
        with pytest.raises(ValidationError):
            PatientRegistration(
                family_name="User", date_of_birth="1990-01-01",
                gender=Gender.MALE, postal_code="12345", address_city="Boston",
                address_state="Massachusetts",
            )


class TestQueryResponseAliasMapping:
    """Tests for QueryResponse alias mapping (state -> query_status)."""

    def test_state_alias_maps_to_query_status(self):
        """Verify 'state' field maps to query_status via alias."""
        resp = QueryResponse.model_validate({"state": "COMPLETE"})
        assert resp.query_status == QueryStatus.COMPLETE

    def test_all_query_status_values_parse(self):
        """Verify all 5 QueryStatus values parse from API alias."""
        for status in QueryStatus:
            resp = QueryResponse.model_validate({"state": status.value})
            assert resp.query_status == status

    def test_files_available_defaults_to_zero(self):
        """Verify files_available defaults to 0."""
        resp = QueryResponse.model_validate({"state": "PROCESSING"})
        assert resp.files_available == 0

    def test_error_message_optional(self):
        """Verify error_message is None by default."""
        resp = QueryResponse.model_validate({"state": "COMPLETE"})
        assert resp.error_message is None


class TestMockIntegrationFlow:
    """Mock integration test for register -> query -> poll -> retrieve flow."""

    def test_full_flow_with_mocked_http(self):
        """Exercise full register -> query -> poll -> retrieve with mocked responses."""
        register_body = {
            "particle_patient_id": "pid-12345",
            "given_name": "Test",
            "family_name": "User",
            "date_of_birth": "1990-01-01",
            "gender": "MALE",
            "postal_code": "12345",
            "address_city": "Boston",
            "address_state": "Massachusetts",
        }
        submit_body = {"particle_patient_id": "pid-12345"}
        status_body = {"state": "COMPLETE", "files_available": 3}
        flat_body = {"medications": [{"medication_name": "Aspirin"}], "problems": []}

        # Mock at the HTTP client request level (bypasses auth + retry internals)
        responses = [register_body, submit_body, status_body, flat_body]
        call_index = 0

        def mock_request(method, path, **kwargs):
            nonlocal call_index
            resp = responses[call_index]
            call_index += 1
            return resp

        settings = ParticleSettings()
        client = ParticleHTTPClient(settings)

        with patch.object(client, "request", side_effect=mock_request):
            from particle.patient import PatientService
            from particle.query import PurposeOfUse, QueryService

            # Register
            patient_svc = PatientService(client)
            patient = PatientRegistration(
                given_name="Test", family_name="User", date_of_birth="1990-01-01",
                gender=Gender.MALE, postal_code="12345", address_city="Boston",
                address_state="Massachusetts",
            )
            reg_resp = patient_svc.register(patient)
            assert reg_resp.particle_patient_id == "pid-12345"

            # Submit query
            query_svc = QueryService(client)
            sub_resp = query_svc.submit_query("pid-12345", PurposeOfUse.TREATMENT)
            assert sub_resp.particle_patient_id == "pid-12345"

            # Check status
            status_resp = query_svc.get_query_status("pid-12345")
            assert status_resp.query_status == QueryStatus.COMPLETE
            assert status_resp.files_available == 3

            # Get flat data
            flat_data = query_svc.get_flat("pid-12345")
            assert "medications" in flat_data
            assert flat_data["medications"][0]["medication_name"] == "Aspirin"

        client.close()
