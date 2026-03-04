"""Unit tests for the data quality analysis module.

All tests use synthetic data -- no database or file I/O needed.
"""

import pytest

from observatory.quality import analyze_quality, print_quality_report
from observatory.schema import ResourceSchema


def _make_schema(resource_type, table_name, columns, record_count=1, is_empty=False):
    """Helper to create a ResourceSchema for testing."""
    return ResourceSchema(
        resource_type=resource_type,
        table_name=table_name,
        columns=columns,
        record_count=record_count,
        is_empty=is_empty,
    )


# ---------------------------------------------------------------------------
# analyze_quality tests
# ---------------------------------------------------------------------------

class TestAnalyzeQuality:
    """Tests for analyze_quality()."""

    def test_all_fields_populated_near_zero_null_pct(self):
        """Resource with all fields populated has null_pct near 0%."""
        schemas = [_make_schema("labs", "labs", ["patient_id", "lab_name"], record_count=2)]
        data = {
            "labs": [
                {"patient_id": "p1", "lab_name": "CBC"},
                {"patient_id": "p2", "lab_name": "BMP"},
            ]
        }

        results = analyze_quality(data, schemas)

        assert len(results) == 1
        assert results[0]["null_pct"] == 0.0
        assert results[0]["record_count"] == 2
        assert results[0]["column_count"] == 2

    def test_half_none_values_near_fifty_pct(self):
        """Resource with half None values has null_pct near 50%."""
        schemas = [_make_schema("labs", "labs", ["patient_id", "lab_name"], record_count=2)]
        data = {
            "labs": [
                {"patient_id": "p1", "lab_name": "CBC"},
                {"patient_id": "p2", "lab_name": None},
            ]
        }

        results = analyze_quality(data, schemas)

        assert len(results) == 1
        assert results[0]["null_pct"] == 25.0  # 1 null out of 4 fields

    def test_missing_keys_counted_as_none(self):
        """Records missing a key are counted as None for that field."""
        schemas = [_make_schema("labs", "labs", ["patient_id", "lab_name", "lab_value"], record_count=1)]
        data = {
            "labs": [
                {"patient_id": "p1", "lab_name": "CBC"},  # missing lab_value
            ]
        }

        results = analyze_quality(data, schemas)

        # 1 null out of 3 fields = 33.3%
        assert abs(results[0]["null_pct"] - 33.33) < 0.1

    def test_date_range_with_timestamps(self):
        """Resource with date-like values shows min/max date range."""
        schemas = [_make_schema("labs", "labs", ["patient_id", "lab_timestamp"], record_count=3)]
        data = {
            "labs": [
                {"patient_id": "p1", "lab_timestamp": "2024-01-15T10:30:00Z"},
                {"patient_id": "p1", "lab_timestamp": "2024-03-20T14:00:00Z"},
                {"patient_id": "p1", "lab_timestamp": "2024-02-10T08:15:00Z"},
            ]
        }

        results = analyze_quality(data, schemas)

        assert results[0]["date_range"] == "2024-01-15 to 2024-03-20"

    def test_date_range_no_dates(self):
        """Resource with no date-like values has date_range 'n/a'."""
        schemas = [_make_schema("patients", "patients", ["patient_id", "given_name"], record_count=1)]
        data = {
            "patients": [
                {"patient_id": "p1", "given_name": "Jane"},
            ]
        }

        results = analyze_quality(data, schemas)

        assert results[0]["date_range"] == "n/a"

    def test_empty_columns_counted(self):
        """Column where ALL values are None is counted as empty."""
        schemas = [_make_schema("labs", "labs", ["patient_id", "lab_name", "lab_value"], record_count=2)]
        data = {
            "labs": [
                {"patient_id": "p1", "lab_name": "CBC", "lab_value": None},
                {"patient_id": "p2", "lab_name": "BMP", "lab_value": None},
            ]
        }

        results = analyze_quality(data, schemas)

        assert results[0]["empty_columns"] == 1

    def test_partially_null_column_not_empty(self):
        """Column with some None and some values is NOT counted as empty."""
        schemas = [_make_schema("labs", "labs", ["patient_id", "lab_value"], record_count=2)]
        data = {
            "labs": [
                {"patient_id": "p1", "lab_value": "42"},
                {"patient_id": "p2", "lab_value": None},
            ]
        }

        results = analyze_quality(data, schemas)

        assert results[0]["empty_columns"] == 0

    def test_empty_schemas_skipped(self):
        """Schemas with is_empty=True are skipped."""
        schemas = [
            _make_schema("allergies", "allergies", [], record_count=0, is_empty=True),
            _make_schema("labs", "labs", ["patient_id"], record_count=1),
        ]
        data = {
            "allergies": [],
            "labs": [{"patient_id": "p1"}],
        }

        results = analyze_quality(data, schemas)

        assert len(results) == 1
        assert results[0]["table_name"] == "labs"

    def test_no_records_in_data_skipped(self):
        """Schemas with no matching records in data are skipped."""
        schemas = [_make_schema("labs", "labs", ["patient_id"], record_count=5)]
        data = {"labs": []}

        results = analyze_quality(data, schemas)

        assert len(results) == 0

    def test_sorted_by_record_count_descending(self):
        """Results are sorted by record_count descending."""
        schemas = [
            _make_schema("patients", "patients", ["patient_id"], record_count=1),
            _make_schema("labs", "labs", ["patient_id"], record_count=100),
            _make_schema("sources", "sources", ["patient_id"], record_count=10),
        ]
        data = {
            "patients": [{"patient_id": "p1"}],
            "labs": [{"patient_id": f"p{i}"} for i in range(100)],
            "sources": [{"patient_id": f"p{i}"} for i in range(10)],
        }

        results = analyze_quality(data, schemas)

        counts = [r["record_count"] for r in results]
        assert counts == [100, 10, 1]


# ---------------------------------------------------------------------------
# print_quality_report tests
# ---------------------------------------------------------------------------

class TestPrintQualityReport:
    """Tests for print_quality_report()."""

    def test_prints_without_error(self, capsys):
        """print_quality_report does not raise with valid results."""
        results = [
            {
                "table_name": "labs",
                "record_count": 111,
                "column_count": 22,
                "null_pct": 45.2,
                "date_range": "2024-01-01 to 2024-12-31",
                "empty_columns": 0,
            }
        ]

        # Should not raise
        print_quality_report(results)

    def test_prints_empty_results(self, capsys):
        """print_quality_report handles empty results list."""
        print_quality_report([])

    def test_prints_summary_line(self, capsys):
        """Output includes the summary line with record and table counts."""
        results = [
            {
                "table_name": "labs",
                "record_count": 50,
                "column_count": 10,
                "null_pct": 10.0,
                "date_range": "n/a",
                "empty_columns": 0,
            },
            {
                "table_name": "patients",
                "record_count": 5,
                "column_count": 15,
                "null_pct": 5.0,
                "date_range": "n/a",
                "empty_columns": 0,
            },
        ]

        print_quality_report(results)

        captured = capsys.readouterr()
        assert "55 records" in captured.out
        assert "2 tables" in captured.out
