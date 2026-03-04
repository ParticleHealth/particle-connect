"""Unit tests for the DuckDB loader module.

All tests use mocked connections -- no running DuckDB required.
"""

from unittest.mock import MagicMock, call, patch

import pytest

from observatory.loader import ensure_table, get_connection, load_all, load_resource
from observatory.schema import ResourceSchema


# ---------------------------------------------------------------------------
# get_connection tests
# ---------------------------------------------------------------------------

class TestGetConnection:
    """Tests for get_connection()."""

    def test_default_path(self, monkeypatch):
        """Default path is observatory.duckdb when DUCKDB_PATH is not set."""
        monkeypatch.delenv("DUCKDB_PATH", raising=False)

        with patch("observatory.loader.duckdb") as mock_duckdb:
            get_connection()
            mock_duckdb.connect.assert_called_once_with("observatory.duckdb")

    def test_env_var_path(self, monkeypatch):
        """DUCKDB_PATH env var overrides the default path."""
        monkeypatch.setenv("DUCKDB_PATH", "/tmp/custom.duckdb")

        with patch("observatory.loader.duckdb") as mock_duckdb:
            get_connection()
            mock_duckdb.connect.assert_called_once_with("/tmp/custom.duckdb")

    def test_explicit_path(self, monkeypatch):
        """Explicit path argument overrides env var and default."""
        monkeypatch.setenv("DUCKDB_PATH", "/tmp/env.duckdb")

        with patch("observatory.loader.duckdb") as mock_duckdb:
            get_connection("/tmp/explicit.duckdb")
            mock_duckdb.connect.assert_called_once_with("/tmp/explicit.duckdb")


# ---------------------------------------------------------------------------
# ensure_table tests
# ---------------------------------------------------------------------------

class TestEnsureTable:
    """Tests for ensure_table()."""

    def test_creates_table_with_columns(self):
        """ensure_table executes CREATE TABLE IF NOT EXISTS with quoted columns."""
        conn = MagicMock()
        schema = ResourceSchema(
            resource_type="labs",
            table_name="labs",
            columns=["patient_id", "lab_name", "lab_value"],
            record_count=5,
            is_empty=False,
        )

        ensure_table(conn, schema)

        sql = conn.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS labs" in sql
        assert '"patient_id" TEXT' in sql
        assert '"lab_name" TEXT' in sql
        assert '"lab_value" TEXT' in sql


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
        records = [
            {"patient_id": "p1", "lab_name": "CBC"},
            {"patient_id": "p1", "lab_name": "BMP"},
        ]

        result = load_resource(conn, "labs", ["patient_id", "lab_name"], records, "p1")

        assert result == 2
        conn.begin.assert_called_once()
        conn.commit.assert_called_once()
        # DELETE then INSERT
        assert conn.execute.call_count == 1  # DELETE
        conn.executemany.assert_called_once()  # INSERT

    def test_returns_correct_count(self):
        """Return value matches the number of records inserted."""
        conn = MagicMock()
        records = [{"patient_id": "p1", "col_a": "x"} for _ in range(5)]
        result = load_resource(conn, "test_table", ["patient_id", "col_a"], records, "p1")
        assert result == 5

    def test_missing_columns_become_none(self):
        """Records missing some columns get None for those columns."""
        conn = MagicMock()

        # Record is missing "lab_value" column
        records = [{"patient_id": "p1", "lab_name": "CBC"}]
        columns = ["patient_id", "lab_name", "lab_value"]

        load_resource(conn, "labs", columns, records, "p1")

        # Check the rows passed to executemany -- the third column should be None
        executemany_call = conn.executemany.call_args
        rows = executemany_call[0][1]  # second positional arg is the rows
        assert rows == [("p1", "CBC", None)]

    def test_rollback_on_error(self):
        """If executemany raises, the transaction is rolled back."""
        conn = MagicMock()
        conn.executemany.side_effect = Exception("insert failed")

        with pytest.raises(Exception, match="insert failed"):
            load_resource(conn, "labs", ["patient_id"], [{"patient_id": "p1"}], "p1")

        conn.begin.assert_called_once()
        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()

    def test_uses_question_mark_placeholders(self):
        """DuckDB uses ? placeholders, not psycopg's %s."""
        conn = MagicMock()
        records = [{"patient_id": "p1", "lab_name": "CBC"}]

        load_resource(conn, "labs", ["patient_id", "lab_name"], records, "p1")

        # Check the INSERT SQL uses ? placeholders
        insert_sql = conn.executemany.call_args[0][0]
        assert "?" in insert_sql
        assert "%s" not in insert_sql

        # Check the DELETE SQL uses ? placeholder
        delete_sql = conn.execute.call_args[0][0]
        assert "?" in delete_sql


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
        # Two patients = two begin/commit cycles
        assert conn.begin.call_count == 2

    def test_correct_return_mapping(self):
        """Return dict maps table_name -> total records loaded."""
        conn = MagicMock()

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

    def test_ensure_table_called(self):
        """ensure_table is called before loading records."""
        conn = MagicMock()

        schemas = [
            self._make_schema("patients", "patients", ["patient_id", "name"], record_count=1),
        ]
        data = {
            "patients": [{"patient_id": "p1", "name": "Jane"}],
        }

        load_all(conn, data, schemas)

        # First execute call should be the CREATE TABLE from ensure_table
        first_sql = conn.execute.call_args_list[0][0][0]
        assert "CREATE TABLE IF NOT EXISTS" in first_sql
