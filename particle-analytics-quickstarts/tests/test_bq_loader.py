"""Unit tests for the BigQuery loader module.

All tests use mocked BigQuery client -- no running BigQuery or
google-cloud-bigquery installation required.
"""

import os
import sys
from unittest.mock import MagicMock, call, patch

import pytest

# Mock the google.cloud.bigquery module before importing bq_loader,
# so the import succeeds even without google-cloud-bigquery installed.
_mock_bigquery = MagicMock()
sys.modules["google.cloud.bigquery"] = _mock_bigquery
sys.modules["google.cloud"] = MagicMock(bigquery=_mock_bigquery)
sys.modules["google"] = MagicMock()

# Now import bq_loader -- it will use our mocked bigquery
from observatory.bq_loader import get_bq_client, load_all_bq, load_resource_bq
from observatory.schema import ResourceSchema


# ---------------------------------------------------------------------------
# get_bq_client tests
# ---------------------------------------------------------------------------

class TestGetBqClient:
    """Tests for get_bq_client()."""

    def test_missing_project_id(self, monkeypatch):
        """Calling get_bq_client without BQ_PROJECT_ID raises ValueError."""
        monkeypatch.delenv("BQ_PROJECT_ID", raising=False)
        monkeypatch.delenv("BQ_DATASET", raising=False)

        with pytest.raises(ValueError, match="BQ_PROJECT_ID not set"):
            get_bq_client()

    @patch("observatory.bq_loader.bigquery")
    def test_with_env_vars(self, mock_bq, monkeypatch):
        """With BQ_PROJECT_ID set, returns client and dataset_id."""
        monkeypatch.setenv("BQ_PROJECT_ID", "my-project")
        monkeypatch.setenv("BQ_DATASET", "my_dataset")

        client, dataset_id = get_bq_client()

        mock_bq.Client.assert_called_once_with(project="my-project")
        assert dataset_id == "my_dataset"

    @patch("observatory.bq_loader.bigquery")
    def test_default_dataset(self, mock_bq, monkeypatch):
        """Without BQ_DATASET set, defaults to 'particle_observatory'."""
        monkeypatch.setenv("BQ_PROJECT_ID", "my-project")
        monkeypatch.delenv("BQ_DATASET", raising=False)

        _, dataset_id = get_bq_client()

        assert dataset_id == "particle_observatory"

    @patch("observatory.bq_loader.bigquery")
    def test_custom_dataset(self, mock_bq, monkeypatch):
        """With BQ_DATASET='custom', returns 'custom' as dataset_id."""
        monkeypatch.setenv("BQ_PROJECT_ID", "my-project")
        monkeypatch.setenv("BQ_DATASET", "custom")

        _, dataset_id = get_bq_client()

        assert dataset_id == "custom"


# ---------------------------------------------------------------------------
# load_resource_bq tests
# ---------------------------------------------------------------------------

class TestLoadResourceBq:
    """Tests for load_resource_bq()."""

    def test_empty_records_returns_zero(self):
        """Returns 0 and makes no client calls when records is empty."""
        client = MagicMock()

        result = load_resource_bq(client, "my_dataset", "labs", ["patient_id", "lab_name"], [], "p1")

        assert result == 0
        client.query.assert_not_called()
        client.load_table_from_json.assert_not_called()

    @patch("observatory.bq_loader.bigquery")
    def test_calls_delete_then_load(self, mock_bq):
        """Verifies client.query (DELETE) is called, then client.load_table_from_json (INSERT)."""
        client = MagicMock()
        client.project = "my-project"

        records = [
            {"patient_id": "p1", "lab_name": "CBC"},
            {"patient_id": "p1", "lab_name": "BMP"},
        ]

        result = load_resource_bq(
            client, "my_dataset", "labs", ["patient_id", "lab_name"], records, "p1"
        )

        assert result == 2

        # DELETE was called via client.query
        client.query.assert_called_once()
        delete_call = client.query.call_args
        assert "DELETE FROM" in delete_call[0][0]
        assert "patient_id" in delete_call[0][0]

        # INSERT was called via client.load_table_from_json
        client.load_table_from_json.assert_called_once()

    @patch("observatory.bq_loader.bigquery")
    def test_uses_explicit_schema(self, mock_bq):
        """Verifies LoadJobConfig is created with SchemaField objects."""
        client = MagicMock()
        client.project = "my-project"

        records = [{"patient_id": "p1", "lab_name": "CBC"}]

        load_resource_bq(
            client, "my_dataset", "labs", ["patient_id", "lab_name"], records, "p1"
        )

        # LoadJobConfig was called with schema containing SchemaField objects
        mock_bq.LoadJobConfig.assert_called_once()
        load_config_call = mock_bq.LoadJobConfig.call_args
        schema = load_config_call[1]["schema"]
        assert len(schema) == 2
        # SchemaField was called for each column
        assert mock_bq.SchemaField.call_count == 2
        mock_bq.SchemaField.assert_any_call("patient_id", "STRING", mode="NULLABLE")
        mock_bq.SchemaField.assert_any_call("lab_name", "STRING", mode="NULLABLE")

    @patch("observatory.bq_loader.bigquery")
    def test_uses_parameterized_delete(self, mock_bq):
        """Verifies QueryJobConfig has ScalarQueryParameter with patient_id."""
        client = MagicMock()
        client.project = "my-project"

        records = [{"patient_id": "p1", "lab_name": "CBC"}]

        load_resource_bq(
            client, "my_dataset", "labs", ["patient_id", "lab_name"], records, "p1"
        )

        # QueryJobConfig was created with ScalarQueryParameter
        mock_bq.QueryJobConfig.assert_called_once()
        config_call = mock_bq.QueryJobConfig.call_args
        query_params = config_call[1]["query_parameters"]
        assert len(query_params) == 1
        mock_bq.ScalarQueryParameter.assert_called_once_with(
            "patient_id", "STRING", "p1"
        )


# ---------------------------------------------------------------------------
# load_all_bq tests
# ---------------------------------------------------------------------------

class TestLoadAllBq:
    """Tests for load_all_bq()."""

    def _make_schema(self, resource_type, table_name, columns, record_count=1, is_empty=False):
        """Helper to create a ResourceSchema for testing."""
        return ResourceSchema(
            resource_type=resource_type,
            table_name=table_name,
            columns=columns,
            record_count=record_count,
            is_empty=is_empty,
        )

    def test_skips_empty_schemas(self):
        """Empty schemas are skipped entirely."""
        client = MagicMock()
        schemas = [
            self._make_schema("allergies", "allergies", [], record_count=0, is_empty=True),
        ]
        data = {"allergies": []}

        result = load_all_bq(client, "my_dataset", data, schemas)

        assert result == {}
        client.query.assert_not_called()
        client.load_table_from_json.assert_not_called()

    @patch("observatory.bq_loader.bigquery")
    def test_groups_by_patient(self, mock_bq):
        """Multiple patients' records are loaded separately."""
        client = MagicMock()
        client.project = "my-project"

        schemas = [
            self._make_schema("labs", "labs", ["patient_id", "lab_name"], record_count=3),
        ]
        data = {
            "labs": [
                {"patient_id": "p1", "lab_name": "CBC"},
                {"patient_id": "p2", "lab_name": "BMP"},
                {"patient_id": "p1", "lab_name": "CMP"},
            ],
        }

        result = load_all_bq(client, "my_dataset", data, schemas)

        assert result == {"labs": 3}
        # Two patients = two DELETE queries + two load_table_from_json calls
        assert client.query.call_count == 2
        assert client.load_table_from_json.call_count == 2
