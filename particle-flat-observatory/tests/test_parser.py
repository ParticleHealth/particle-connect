"""Tests for the parser and schema inspector modules."""

import json
import tempfile
from pathlib import Path

import pytest

from observatory.parser import EXPECTED_RESOURCE_TYPES, load_flat_data
from observatory.schema import ResourceSchema, camel_to_snake, inspect_schema

SAMPLE_DATA = Path(__file__).resolve().parent.parent / "sample-data" / "flat_data.json"


class TestLoadFlatData:
    def test_load_sample_data(self):
        data = load_flat_data(SAMPLE_DATA)
        assert len(data) == 21
        assert set(data.keys()) == set(EXPECTED_RESOURCE_TYPES)

    def test_load_normalizes_empty_strings(self):
        data = load_flat_data(SAMPLE_DATA, normalize=True)
        for rtype, records in data.items():
            for rec in records:
                for k, v in rec.items():
                    assert v != "", f"Empty string found in {rtype}.{k} after normalization"

    def test_load_without_normalize(self):
        data = load_flat_data(SAMPLE_DATA, normalize=False)
        # At least some resource types should have empty strings in raw data
        has_empty = False
        for records in data.values():
            for rec in records:
                for v in rec.values():
                    if v == "":
                        has_empty = True
                        break
        assert has_empty, "Expected empty strings in raw (non-normalized) data"

    def test_load_missing_file(self):
        with pytest.raises(FileNotFoundError, match="Flat data file not found"):
            load_flat_data("/nonexistent/path/flat_data.json")

    def test_load_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{invalid json content")
            f.flush()
            with pytest.raises(json.JSONDecodeError):
                load_flat_data(f.name)

    def test_load_non_dict_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([1, 2, 3], f)
            f.flush()
            with pytest.raises(ValueError, match="Expected top-level JSON object"):
                load_flat_data(f.name)

    def test_load_handles_missing_resource_types(self):
        """If a resource type is missing from the file, it is included with an empty list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"patients": [{"patient_id": "1"}]}, f)
            f.flush()
            data = load_flat_data(f.name)
            assert len(data) == 21
            assert data["patients"] == [{"patient_id": "1"}]
            assert data["allergies"] == []

    def test_load_handles_extra_resource_types(self):
        """Unknown resource types are skipped (not included in result)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"unknownType": [{"id": "1"}], "patients": []}, f)
            f.flush()
            data = load_flat_data(f.name)
            assert len(data) == 21
            assert "unknownType" not in data

    def test_expected_resource_types_count(self):
        assert len(EXPECTED_RESOURCE_TYPES) == 21

    def test_empty_resource_types_in_sample(self):
        """Known empty resource types in sample data should have 0 records."""
        data = load_flat_data(SAMPLE_DATA)
        expected_empty = ["allergies", "coverages", "familyMemberHistories",
                          "immunizations", "socialHistories"]
        for rtype in expected_empty:
            assert len(data[rtype]) == 0, f"{rtype} should be empty in sample data"


class TestCamelToSnake:
    @pytest.mark.parametrize(
        "camel,expected",
        [
            ("aICitations", "ai_citations"),
            ("aIOutputs", "ai_outputs"),
            ("allergies", "allergies"),
            ("coverages", "coverages"),
            ("documentReferences", "document_references"),
            ("encounters", "encounters"),
            ("familyMemberHistories", "family_member_histories"),
            ("immunizations", "immunizations"),
            ("labs", "labs"),
            ("locations", "locations"),
            ("medications", "medications"),
            ("organizations", "organizations"),
            ("patients", "patients"),
            ("practitioners", "practitioners"),
            ("problems", "problems"),
            ("procedures", "procedures"),
            ("recordSources", "record_sources"),
            ("socialHistories", "social_histories"),
            ("sources", "sources"),
            ("transitions", "transitions"),
            ("vitalSigns", "vital_signs"),
        ],
    )
    def test_camel_to_snake(self, camel, expected):
        assert camel_to_snake(camel) == expected

    def test_all_21_resource_types(self):
        """Every expected resource type converts without error."""
        for rtype in EXPECTED_RESOURCE_TYPES:
            result = camel_to_snake(rtype)
            assert result == result.lower(), f"{rtype} -> {result} should be all lowercase"
            assert "--" not in result, f"{rtype} -> {result} should not have double dashes"


class TestInspectSchema:
    def test_inspect_schema_sample_data(self):
        data = load_flat_data(SAMPLE_DATA)
        schemas = inspect_schema(data)
        assert len(schemas) == 21
        # All schemas should be ResourceSchema instances
        for s in schemas:
            assert isinstance(s, ResourceSchema)

    def test_inspect_schema_column_counts(self):
        data = load_flat_data(SAMPLE_DATA)
        schemas = inspect_schema(data)
        non_empty = [s for s in schemas if not s.is_empty]
        for s in non_empty:
            assert len(s.columns) > 0, f"{s.resource_type} has data but no columns"

    def test_inspect_schema_empty_types(self):
        data = load_flat_data(SAMPLE_DATA)
        schemas = inspect_schema(data)
        empty = [s for s in schemas if s.is_empty]
        for s in empty:
            assert s.columns == [], f"{s.resource_type} is empty but has columns: {s.columns}"
            assert s.record_count == 0

    def test_inspect_schema_discovers_all_columns(self):
        """When different records have different keys, all columns are discovered."""
        data = {
            "patients": [
                {"id": "1", "name": "Alice"},
                {"id": "2", "phone": "555-0100"},
                {"id": "3", "name": "Charlie", "email": "c@example.com"},
            ]
        }
        schemas = inspect_schema(data)
        patient_schema = schemas[0]
        assert patient_schema.columns == ["id", "name", "phone", "email"]
        assert patient_schema.record_count == 3
        assert patient_schema.is_empty is False

    def test_inspect_schema_preserves_key_order(self):
        """Column order matches first-seen insertion order, not alphabetical."""
        data = {
            "patients": [
                {"zebra": "1", "alpha": "2", "middle": "3"},
            ]
        }
        schemas = inspect_schema(data)
        assert schemas[0].columns == ["zebra", "alpha", "middle"]

    def test_inspect_schema_order_matches_expected(self):
        """Schemas are returned in EXPECTED_RESOURCE_TYPES order."""
        data = load_flat_data(SAMPLE_DATA)
        schemas = inspect_schema(data)
        schema_types = [s.resource_type for s in schemas]
        assert schema_types == EXPECTED_RESOURCE_TYPES

    def test_inspect_schema_table_names(self):
        data = load_flat_data(SAMPLE_DATA)
        schemas = inspect_schema(data)
        table_names = {s.resource_type: s.table_name for s in schemas}
        assert table_names["aICitations"] == "ai_citations"
        assert table_names["vitalSigns"] == "vital_signs"
        assert table_names["documentReferences"] == "document_references"
