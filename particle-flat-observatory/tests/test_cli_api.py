"""CLI integration tests for the --source api path.

Tests verify that the CLI correctly handles:
- Missing --patient-id with --source api
- Missing API credentials
- API request failures
- Normalization of API data before the pipeline
- Silent --patient-id in file mode (no regression)

All tests use mocked I/O -- no real API calls or database connections.
"""

import os
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from observatory.cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PARTICLE_ENV = {
    "PARTICLE_CLIENT_ID": "test-client-id",
    "PARTICLE_CLIENT_SECRET": "test-client-secret",
    "PARTICLE_SCOPE_ID": "test-scope-id",
}


def _make_api_response(**resource_overrides: list[dict]) -> dict[str, list[dict]]:
    """Build a minimal API response dict with empty defaults for all 21 types."""
    from observatory.parser import EXPECTED_RESOURCE_TYPES

    data = {key: [] for key in EXPECTED_RESOURCE_TYPES}
    data.update(resource_overrides)
    return data


# ---------------------------------------------------------------------------
# Test: missing --patient-id
# ---------------------------------------------------------------------------


class TestApiSourceMissingPatientId:
    """--source api without --patient-id produces actionable error."""

    def test_api_source_missing_patient_id(self):
        result = runner.invoke(app, ["--source", "api"])
        assert result.exit_code == 1
        assert "--patient-id is required" in result.output


# ---------------------------------------------------------------------------
# Test: missing credentials
# ---------------------------------------------------------------------------


class TestApiSourceMissingCredentials:
    """--source api with missing env vars surfaces the ValueError message."""

    def test_api_source_missing_credentials(self):
        with patch.dict(os.environ, {}, clear=False):
            # Remove PARTICLE_* vars if they happen to exist
            for var in ("PARTICLE_CLIENT_ID", "PARTICLE_CLIENT_SECRET", "PARTICLE_SCOPE_ID"):
                os.environ.pop(var, None)

            result = runner.invoke(app, ["--source", "api", "--patient-id", "test-123"])

        assert result.exit_code == 1
        assert "Missing required environment variables" in result.output
        assert "PARTICLE_CLIENT_ID" in result.output


# ---------------------------------------------------------------------------
# Test: API request failure
# ---------------------------------------------------------------------------


class TestApiSourceRequestFailure:
    """API errors are caught and displayed with 'API request failed' prefix."""

    def test_api_source_api_request_failure(self):
        mock_client = MagicMock()
        mock_client.get_flat_data.side_effect = Exception("Connection timeout")

        with patch("observatory.api_client.ParticleAPIClient", return_value=mock_client):
            result = runner.invoke(app, ["--source", "api", "--patient-id", "test-123"])

        assert result.exit_code == 1
        assert "API request failed" in result.output
        assert "Connection timeout" in result.output


# ---------------------------------------------------------------------------
# Test: normalization of API data
# ---------------------------------------------------------------------------


class TestApiSourceNormalizesData:
    """API data goes through normalize_resource() before the pipeline."""

    def test_api_source_normalizes_data(self):
        # API returns records with empty strings (Particle convention)
        raw_response = _make_api_response(
            patients=[
                {"id": "p1", "first_name": "Jane", "middle_name": ""},
            ],
        )

        mock_client = MagicMock()
        mock_client.get_flat_data.return_value = raw_response

        captured_data = {}

        def fake_load_all(conn, data, schemas):
            captured_data.update(data)
            return {"patients": 1}

        mock_conn = MagicMock()
        with (
            patch("observatory.api_client.ParticleAPIClient", return_value=mock_client),
            patch("observatory.loader.get_connection", return_value=mock_conn),
            patch("observatory.loader.load_all", fake_load_all),
        ):
            result = runner.invoke(
                app, ["--source", "api", "--patient-id", "test-123", "--target", "duckdb"]
            )

        # Verify normalization: empty string -> None
        assert "patients" in captured_data
        patient = captured_data["patients"][0]
        assert patient["first_name"] == "Jane"
        assert patient["middle_name"] is None, (
            "Empty string should be normalized to None"
        )


# ---------------------------------------------------------------------------
# Test: file source ignores --patient-id
# ---------------------------------------------------------------------------


class TestFileSourceIgnoresPatientId:
    """--patient-id is silently ignored when --source file (no regression)."""

    def test_file_source_ignores_patient_id(self):
        test_data = _make_api_response(
            patients=[{"id": "p1", "first_name": "Jane"}],
        )

        def fake_load_all(conn, data, schemas):
            return {"patients": 1}

        mock_conn = MagicMock()
        with (
            patch("observatory.parser.load_flat_data", return_value=test_data),
            patch("observatory.loader.get_connection", return_value=mock_conn),
            patch("observatory.loader.load_all", fake_load_all),
        ):
            result = runner.invoke(
                app,
                [
                    "--source", "file",
                    "--patient-id", "test-123",
                    "--data-path", "sample-data/flat_data.json",
                ],
            )

        assert result.exit_code == 0
        assert "Done." in result.output
