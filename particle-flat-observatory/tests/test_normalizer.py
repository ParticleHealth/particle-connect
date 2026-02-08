"""Tests for the data normalizer module."""

from observatory.normalizer import normalize_record, normalize_resource, normalize_value


class TestNormalizeValue:
    def test_empty_string_becomes_none(self):
        assert normalize_value("") is None

    def test_non_empty_string_unchanged(self):
        assert normalize_value("hello") == "hello"

    def test_whitespace_string_unchanged(self):
        assert normalize_value(" ") == " "
        assert normalize_value("  ") == "  "

    def test_numeric_unchanged(self):
        assert normalize_value(42) == 42
        assert normalize_value(0) == 0
        assert normalize_value(3.14) == 3.14

    def test_none_unchanged(self):
        assert normalize_value(None) is None

    def test_boolean_unchanged(self):
        assert normalize_value(True) is True
        assert normalize_value(False) is False

    def test_list_unchanged(self):
        val = [1, 2, 3]
        assert normalize_value(val) == [1, 2, 3]

    def test_dict_unchanged(self):
        val = {"nested": "value"}
        assert normalize_value(val) == {"nested": "value"}


class TestNormalizeRecord:
    def test_normalize_record(self):
        record = {"a": "", "b": "val", "c": ""}
        result = normalize_record(record)
        assert result == {"a": None, "b": "val", "c": None}

    def test_normalize_record_preserves_key_order(self):
        record = {"zebra": "", "alpha": "keep", "middle": ""}
        result = normalize_record(record)
        assert list(result.keys()) == ["zebra", "alpha", "middle"]

    def test_normalize_record_does_not_mutate_input(self):
        record = {"a": "", "b": "val"}
        result = normalize_record(record)
        assert record["a"] == ""  # original unchanged
        assert result["a"] is None  # new dict has None

    def test_normalize_record_all_empty(self):
        record = {"x": "", "y": "", "z": ""}
        result = normalize_record(record)
        assert result == {"x": None, "y": None, "z": None}

    def test_normalize_record_no_empty(self):
        record = {"a": "hello", "b": 42, "c": True}
        result = normalize_record(record)
        assert result == {"a": "hello", "b": 42, "c": True}

    def test_normalize_record_empty_dict(self):
        result = normalize_record({})
        assert result == {}


class TestNormalizeResource:
    def test_normalize_resource(self):
        records = [
            {"name": "Alice", "phone": ""},
            {"name": "", "phone": "555-0100"},
        ]
        result = normalize_resource(records)
        assert result == [
            {"name": "Alice", "phone": None},
            {"name": None, "phone": "555-0100"},
        ]

    def test_normalize_resource_does_not_mutate_input(self):
        records = [{"a": ""}]
        result = normalize_resource(records)
        assert records[0]["a"] == ""  # original unchanged
        assert result[0]["a"] is None  # new list has None

    def test_normalize_resource_empty_list(self):
        result = normalize_resource([])
        assert result == []
