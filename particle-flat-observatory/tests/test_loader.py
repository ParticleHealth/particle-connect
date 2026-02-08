"""Unit tests for the PostgreSQL loader module.

All tests use mocked connections -- no running PostgreSQL required.
"""

from unittest.mock import MagicMock, call

import pytest

from observatory.loader import get_connection_string, load_all, load_resource
from observatory.schema import ResourceSchema


# ---------------------------------------------------------------------------
# get_connection_string tests
# ---------------------------------------------------------------------------

class TestGetConnectionString:
    """Tests for get_connection_string()."""

    def test_defaults(self, monkeypatch):
        """Default env vars produce the compose.yaml connection string."""
        # Clear any PG_* env vars that might be set
        for var in ("PG_HOST", "PG_PORT", "PG_USER", "PG_PASSWORD", "PG_DATABASE"):
            monkeypatch.delenv(var, raising=False)

        result = get_connection_string()
        assert result == "postgresql://observatory:observatory@localhost:5432/observatory"

    def test_custom_host(self, monkeypatch):
        """PG_HOST env var overrides the default host."""
        monkeypatch.setenv("PG_HOST", "db.example.com")
        monkeypatch.delenv("PG_PORT", raising=False)
        monkeypatch.delenv("PG_USER", raising=False)
        monkeypatch.delenv("PG_PASSWORD", raising=False)
        monkeypatch.delenv("PG_DATABASE", raising=False)

        result = get_connection_string()
        assert "db.example.com" in result
        assert result == "postgresql://observatory:observatory@db.example.com:5432/observatory"

    def test_all_custom_vars(self, monkeypatch):
        """All PG_* env vars are reflected in the connection string."""
        monkeypatch.setenv("PG_HOST", "myhost")
        monkeypatch.setenv("PG_PORT", "9999")
        monkeypatch.setenv("PG_USER", "admin")
        monkeypatch.setenv("PG_PASSWORD", "secret")
        monkeypatch.setenv("PG_DATABASE", "mydb")

        result = get_connection_string()
        assert result == "postgresql://admin:secret@myhost:9999/mydb"


# ---------------------------------------------------------------------------
# load_resource tests
# ---------------------------------------------------------------------------

class TestLoadResource:
    """Tests for load_resource()."""

    def test_empty_records_returns_zero(self):
        """Empty records list returns 0 and does not touch the database."""
        conn = MagicMock()
        result = load_resource(conn, "labs", ["patient_id", "lab_name"], [], "p1")
        assert result == 0
        conn.execute.assert_not_called()
        conn.executemany.assert_not_called()

    def test_inserts_records(self):
        """Non-empty records trigger DELETE + INSERT in a transaction."""
        conn = MagicMock()
        # transaction() returns a context manager
        tx = MagicMock()
        conn.transaction.return_value = tx
        tx.__enter__ = MagicMock(return_value=tx)
        tx.__exit__ = MagicMock(return_value=False)

        records = [
            {"patient_id": "p1", "lab_name": "CBC"},
            {"patient_id": "p1", "lab_name": "BMP"},
        ]

        result = load_resource(conn, "labs", ["patient_id", "lab_name"], records, "p1")

        assert result == 2
        conn.transaction.assert_called_once()
        # DELETE is called via conn.execute
        conn.execute.assert_called_once()
        # INSERT is called via conn.executemany
        conn.executemany.assert_called_once()

    def test_returns_correct_count(self):
        """Return value matches the number of records inserted."""
        conn = MagicMock()
        tx = MagicMock()
        conn.transaction.return_value = tx
        tx.__enter__ = MagicMock(return_value=tx)
        tx.__exit__ = MagicMock(return_value=False)

        records = [{"patient_id": "p1", "col_a": "x"} for _ in range(5)]
        result = load_resource(conn, "test_table", ["patient_id", "col_a"], records, "p1")
        assert result == 5

    def test_missing_columns_become_none(self):
        """Records missing some columns get None for those columns."""
        conn = MagicMock()
        tx = MagicMock()
        conn.transaction.return_value = tx
        tx.__enter__ = MagicMock(return_value=tx)
        tx.__exit__ = MagicMock(return_value=False)

        # Record is missing "lab_value" column
        records = [{"patient_id": "p1", "lab_name": "CBC"}]
        columns = ["patient_id", "lab_name", "lab_value"]

        load_resource(conn, "labs", columns, records, "p1")

        # Check the rows passed to executemany -- the third column should be None
        executemany_call = conn.executemany.call_args
        rows = executemany_call[0][1]  # second positional arg is the rows
        assert rows == [("p1", "CBC", None)]

    def test_transaction_used_as_context_manager(self):
        """conn.transaction() is used as a context manager (with block)."""
        conn = MagicMock()
        tx = MagicMock()
        conn.transaction.return_value = tx
        tx.__enter__ = MagicMock(return_value=tx)
        tx.__exit__ = MagicMock(return_value=False)

        records = [{"patient_id": "p1", "name": "test"}]
        load_resource(conn, "patients", ["patient_id", "name"], records, "p1")

        # Verify transaction context manager was entered and exited
        tx.__enter__.assert_called_once()
        tx.__exit__.assert_called_once()


# ---------------------------------------------------------------------------
# load_all tests
# ---------------------------------------------------------------------------

class TestLoadAll:
    """Tests for load_all()."""

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
        """Schemas with is_empty=True are skipped entirely."""
        conn = MagicMock()
        schemas = [
            self._make_schema("allergies", "allergies", [], record_count=0, is_empty=True),
        ]
        data = {"allergies": []}

        result = load_all(conn, data, schemas)

        assert result == {}
        conn.execute.assert_not_called()

    def test_skips_no_records_in_data(self):
        """Schemas with no matching records in data dict are skipped."""
        conn = MagicMock()
        schemas = [
            self._make_schema("labs", "labs", ["patient_id", "lab_name"], record_count=5),
        ]
        # Data has empty list for labs
        data = {"labs": []}

        result = load_all(conn, data, schemas)

        assert result == {}
        conn.execute.assert_not_called()

    def test_loads_records_per_patient(self):
        """Records are grouped by patient_id and loaded per-patient."""
        conn = MagicMock()
        tx = MagicMock()
        conn.transaction.return_value = tx
        tx.__enter__ = MagicMock(return_value=tx)
        tx.__exit__ = MagicMock(return_value=False)

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

        result = load_all(conn, data, schemas)

        assert result == {"labs": 3}
        # Two patients = two transaction blocks (two load_resource calls)
        assert conn.transaction.call_count == 2

    def test_correct_return_mapping(self):
        """Return dict maps table_name -> total records loaded."""
        conn = MagicMock()
        tx = MagicMock()
        conn.transaction.return_value = tx
        tx.__enter__ = MagicMock(return_value=tx)
        tx.__exit__ = MagicMock(return_value=False)

        schemas = [
            self._make_schema("labs", "labs", ["patient_id", "lab_name"], record_count=2),
            self._make_schema("patients", "patients", ["patient_id", "given_name"], record_count=1),
            self._make_schema("allergies", "allergies", [], record_count=0, is_empty=True),
        ]
        data = {
            "labs": [
                {"patient_id": "p1", "lab_name": "CBC"},
                {"patient_id": "p1", "lab_name": "BMP"},
            ],
            "patients": [
                {"patient_id": "p1", "given_name": "Jane"},
            ],
            "allergies": [],
        }

        result = load_all(conn, data, schemas)

        assert "labs" in result
        assert "patients" in result
        assert "allergies" not in result  # empty schema skipped
        assert result["labs"] == 2
        assert result["patients"] == 1

    def test_missing_resource_type_in_data(self):
        """Schema for a resource type not present in data dict is skipped."""
        conn = MagicMock()
        schemas = [
            self._make_schema("labs", "labs", ["patient_id"], record_count=5),
        ]
        # data does not contain "labs" at all
        data = {}

        result = load_all(conn, data, schemas)

        assert result == {}
        conn.execute.assert_not_called()
