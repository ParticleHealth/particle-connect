"""Data normalization for Particle flat data.

The only load-time transformation in this ELT pipeline: empty strings -> None.
All other transformations happen in SQL queries downstream.
"""

from typing import Any


def normalize_value(value: Any) -> Any:
    """Convert empty strings to None; return all other values unchanged.

    This is the single transformation applied at load time. Particle returns ""
    instead of null for missing values, and NULL is more useful in SQL queries.
    """
    if value == "" and isinstance(value, str):
        return None
    return value


def normalize_record(record: dict) -> dict:
    """Apply normalize_value to every value in a record dict.

    Returns a new dict (does not mutate input). Preserves key order.
    """
    return {k: normalize_value(v) for k, v in record.items()}


def normalize_resource(records: list[dict]) -> list[dict]:
    """Apply normalize_record to every record in a resource list.

    Returns a new list (does not mutate input).
    """
    return [normalize_record(r) for r in records]
